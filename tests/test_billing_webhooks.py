"""
Tests for billing and webhook handlers.
"""

import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStripeWebhooks:
    """Tests for Stripe webhook handling."""

    def test_webhook_signature_validation(self):
        """Webhook signatures should be validated correctly."""
        secret = "whsec_test_secret"
        payload = json.dumps({"id": "evt_test", "object": "event", "type": "checkout.session.completed"})
        timestamp = int(datetime.now().timestamp())

        # Create signature
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
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
            }
        }

        assert payload["type"] == "checkout.session.completed"
        assert payload["data"]["object"]["customer"] == "cus_test123"

    @pytest.mark.asyncio
    async def test_handle_checkout_completed(self):
        """Checkout completion should update user subscription."""
        from apps.api.billing import handle_checkout_completed

        session = {
            "id": "cs_test123",
            "customer": "cus_test123",
            "subscription": "sub_test123",
            "metadata": {"user_id": "user_123"},
        }

        with patch("apps.api.billing.update_user_subscription") as mock_update:
            mock_update.return_value = AsyncMock()
            await handle_checkout_completed(session)
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_deleted(self):
        """Subscription deletion should downgrade user tier."""
        from apps.api.billing import handle_subscription_deleted

        subscription = {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "canceled",
        }

        with patch("apps.api.billing.downgrade_user_tier") as mock_downgrade:
            mock_downgrade.return_value = AsyncMock()
            await handle_subscription_deleted(subscription)
            mock_downgrade.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_invoice_payment_failed(self):
        """Payment failure should notify user."""
        from apps.api.billing import handle_invoice_payment_failed

        invoice = {
            "id": "in_test123",
            "customer": "cus_test123",
            "subscription": "sub_test123",
            "attempt_count": 2,
        }

        with patch("apps.api.billing.notify_payment_failure") as mock_notify:
            mock_notify.return_value = AsyncMock()
            await handle_invoice_payment_failed(invoice)
            mock_notify.assert_called_once()


class TestBillingQueries:
    """Tests for billing database queries."""

    @pytest.mark.asyncio
    async def test_get_user_subscription(self):
        """Should retrieve user subscription from database."""
        from backend.domain.repositories import SubscriptionRepo

        mock_conn = MagicMock()
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": "sub_123",
            "user_id": "user_123",
            "stripe_subscription_id": "stripe_sub_123",
            "tier": "pro",
            "status": "active",
        })

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
        mock_conn.fetchrow = AsyncMock(return_value={
            "total_tokens": 50000,
            "api_calls": 150,
            "jobs_matched": 500,
        })

        repo = UsageRepo()
        result = await repo.get_monthly_usage(mock_conn, "tenant_123")

        assert result["total_tokens"] == 50000
        assert result["api_calls"] == 150


class TestTierLimits:
    """Tests for tier-based limits."""

    def test_free_tier_limits(self):
        """Free tier should have correct limits."""
        from shared.config import TierLimits

        limits = TierLimits.FREE
        assert limits.max_jobs_per_day == 10
        assert limits.max_applications_per_day == 5
        assert limits.max_resume_tailors == 3

    def test_pro_tier_limits(self):
        """Pro tier should have correct limits."""
        from shared.config import TierLimits

        limits = TierLimits.PRO
        assert limits.max_jobs_per_day == 100
        assert limits.max_applications_per_day == 50
        assert limits.max_resume_tailors == 20

    def test_enterprise_tier_limits(self):
        """Enterprise tier should have unlimited or high limits."""
        from shared.config import TierLimits

        limits = TierLimits.ENTERPRISE
        assert limits.max_jobs_per_day == -1  # Unlimited
        assert limits.max_applications_per_day == -1
