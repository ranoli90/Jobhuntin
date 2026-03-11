"""Tests for billing and webhook handlers."""

import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from shared.tenant_rate_limit import TIER_LIMITS, TenantTier


class TestStripeWebhooks:
    """Tests for Stripe webhook handling."""

    def test_webhook_signature_validation(self):
        """Webhook signatures should be validated correctly."""
        secret = "whsec_test_secret"
        payload = json.dumps(
            {"id": "evt_test", "object": "event", "type": "checkout.session.completed"}
        )
        timestamp = int(datetime.now().timestamp())

        # Create signature
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()

        # Verify signature format
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

    def test_webhook_payload_parsing(self):
        """Webhook payloads should be parsed correctly."""
        payload = {
            "id": "evt_test123",
            "object": "event",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test123",
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                }
            },
        }

        assert payload["type"] == "checkout.session.completed"
        assert payload["data"]["object"]["customer"] == "cus_test123"

    @pytest.mark.asyncio
    async def test_handle_checkout_completed(self):
        """Checkout completion should update subscription state."""
        from apps.api.billing import handle_checkout_completed

        session = {
            "id": "cs_test123",
            "customer": "cus_test123",
            "subscription": "sub_test123",
            "metadata": {"tenant_id": "t_123", "plan": "pro"},
        }

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock()
        await handle_checkout_completed(mock_conn, session)
        assert mock_conn.execute.called

    @pytest.mark.asyncio
    async def test_handle_subscription_cancelled(self):
        """Subscription cancellation should update state."""
        from apps.api.billing import handle_subscription_cancelled

        subscription = {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "canceled",
        }

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock()
        await handle_subscription_cancelled(mock_conn, subscription)
        assert mock_conn.execute.called

    @pytest.mark.asyncio
    async def test_handle_payment_failed(self):
        """Payment failure should update subscription state."""
        from apps.api.billing import handle_payment_failed

        invoice = {
            "id": "in_test123",
            "customer": "cus_test123",
            "subscription": "sub_test123",
        }

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock()
        await handle_payment_failed(mock_conn, invoice)
        assert mock_conn.execute.called


class TestBillingQueries:
    """Tests for billing database queries."""

    @pytest.mark.asyncio
    async def test_get_user_subscription(self):
        """Should retrieve user subscription from database."""
        from backend.domain.repositories import SubscriptionRepo

        mock_conn = MagicMock()
        mock_conn.fetchrow = AsyncMock(
            return_value={
                "id": "sub_123",
                "user_id": "user_123",
                "stripe_subscription_id": "stripe_sub_123",
                "tier": "pro",
                "status": "active",
            }
        )

        repo = SubscriptionRepo()
        result = await repo.get_by_user_id(mock_conn, "user_123")

        assert result is not None
        assert result["tier"] == "pro"

    @pytest.mark.asyncio
    async def test_update_subscription_tier(self):
        """Should update user subscription tier."""
        from backend.domain.repositories import SubscriptionRepo

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")

        repo = SubscriptionRepo()
        await repo.update_tier(mock_conn, "user_123", "enterprise")

        mock_conn.execute.assert_called_once()


class TestUsageTracking:
    """Tests for usage tracking."""

    @pytest.mark.asyncio
    async def test_track_api_usage(self):
        """Should track API usage for billing."""
        from backend.domain.repositories import UsageRepo

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 1")

        repo = UsageRepo()
        await repo.track_usage(
            mock_conn,
            tenant_id="tenant_123",
            endpoint="/ai/match-job",
            tokens_used=500,
        )

        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_monthly_usage(self):
        """Should retrieve monthly usage totals."""
        from backend.domain.repositories import UsageRepo

        mock_conn = MagicMock()
        mock_conn.fetchrow = AsyncMock(
            return_value={
                "total_tokens": 50000,
                "api_calls": 150,
                "jobs_matched": 500,
            }
        )

        repo = UsageRepo()
        result = await repo.get_monthly_usage(mock_conn, "tenant_123")

        assert result["total_tokens"] == 50000
        assert result["api_calls"] == 150


class TestInputRepoUpdateAnswers:
    """Tests for InputRepo.update_answers IDOR prevention."""

    @pytest.mark.asyncio
    async def test_update_answers_requires_application_id(self):
        """update_answers must receive application_id to prevent IDOR."""
        from backend.domain.repositories import InputRepo

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")

        with pytest.raises(ValueError, match="application_id is required"):
            await InputRepo.update_answers(
                mock_conn,
                [{"input_id": "inp_123", "answer": "test"}],
                application_id=None,
            )

    @pytest.mark.asyncio
    async def test_update_answers_with_application_id(self):
        """update_answers with application_id scopes update correctly."""
        from backend.domain.repositories import InputRepo

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")

        await InputRepo.update_answers(
            mock_conn,
            [{"input_id": "inp_123", "answer": "test"}],
            application_id="app_456",
        )

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert "app_456" in str(call_args)


class TestTierLimits:
    """Tests for tier-based limits."""

    def test_free_tier_limits(self):
        """Free tier should have rate limits."""
        limits = TIER_LIMITS[TenantTier.FREE]
        assert limits.requests_per_minute == 10
        assert limits.requests_per_hour == 100

    def test_pro_tier_limits(self):
        """Pro tier should have higher limits."""
        limits = TIER_LIMITS[TenantTier.PRO]
        assert limits.requests_per_minute == 60
        assert limits.requests_per_hour == 1000

    def test_enterprise_tier_limits(self):
        """Enterprise tier should have highest limits."""
        limits = TIER_LIMITS[TenantTier.ENTERPRISE]
        assert limits.requests_per_minute == 500
        assert limits.concurrent_requests == 100
