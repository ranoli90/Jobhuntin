"""Tests for production hardening module.

Validates error handling, rate limiting, and metrics.
"""

from __future__ import annotations

import pytest

from backend.domain.production import (
    AIEndpointError,
    EmbeddingError,
    LLMError,
    MatchMetrics,
    RateLimitError,
    TenantIsolationError,
    TenantRateLimiter,
    ValidationError,
    handle_ai_error,
)


class TestAIEndpointErrors:
    """Tests for AI endpoint error types."""

    def test_base_error_attributes(self) -> None:
        """Base error should have all required attributes."""
        error = AIEndpointError("Test error", "TEST_ERROR", 400)
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.http_status == 400

    def test_llm_error(self) -> None:
        """LLM error should have correct defaults."""
        error = LLMError("LLM failed")
        assert error.message == "LLM failed"
        assert error.error_code == "LLM_ERROR"
        assert error.http_status == 502

    def test_embedding_error(self) -> None:
        """Embedding error should have correct defaults."""
        error = EmbeddingError("Embedding service unavailable")
        assert error.error_code == "EMBEDDING_ERROR"
        assert error.http_status == 502

    def test_rate_limit_error(self) -> None:
        """Rate limit error should have retry_after."""
        error = RateLimitError("Too many requests", retry_after=30)
        assert error.error_code == "RATE_LIMIT"
        assert error.http_status == 429
        assert error.retry_after == 30

    def test_tenant_isolation_error(self) -> None:
        """Tenant isolation error should have correct defaults."""
        error = TenantIsolationError()
        assert error.error_code == "TENANT_ISOLATION"
        assert error.http_status == 403

    def test_validation_error(self) -> None:
        """Validation error should have correct defaults."""
        error = ValidationError("Invalid input")
        assert error.error_code == "VALIDATION_ERROR"
        assert error.http_status == 400


class TestHandleAIError:
    """Tests for error handler function."""

    def test_handle_ai_endpoint_error(self) -> None:
        """AI endpoint errors should convert to HTTPException."""
        error = LLMError("LLM timeout")
        http_exc = handle_ai_error(error)
        assert http_exc.status_code == 502
        assert "LLM_ERROR" in str(http_exc.detail)

    def test_handle_rate_limit_error(self) -> None:
        """Rate limit errors should have correct status."""
        error = RateLimitError("Rate limited", retry_after=60)
        http_exc = handle_ai_error(error)
        assert http_exc.status_code == 429

    def test_handle_validation_error(self) -> None:
        """Validation errors should have 400 status."""
        error = ValidationError("Missing required field")
        http_exc = handle_ai_error(error)
        assert http_exc.status_code == 400

    def test_handle_unknown_error(self) -> None:
        """Unknown errors should result in 500."""
        error = RuntimeError("Something went wrong")
        http_exc = handle_ai_error(error)
        assert http_exc.status_code == 500
        assert "INTERNAL_ERROR" in str(http_exc.detail)


class TestTenantRateLimiter:
    """Tests for tenant rate limiter."""

    @pytest.fixture
    def limiter(self) -> TenantRateLimiter:
        return TenantRateLimiter()

    def test_tier_limits_defined(self, limiter: TenantRateLimiter) -> None:
        """All tier limits should be defined."""
        assert "free" in limiter.TIER_LIMITS
        assert "pro" in limiter.TIER_LIMITS
        assert "team" in limiter.TIER_LIMITS
        assert "enterprise" in limiter.TIER_LIMITS

    def test_free_tier_lowest_limit(self, limiter: TenantRateLimiter) -> None:
        """Free tier should have lowest limit."""
        assert limiter.TIER_LIMITS["free"] < limiter.TIER_LIMITS["pro"]
        assert limiter.TIER_LIMITS["pro"] < limiter.TIER_LIMITS["team"]
        assert limiter.TIER_LIMITS["team"] < limiter.TIER_LIMITS["enterprise"]

    def test_get_tier_from_subscription(self, limiter: TenantRateLimiter) -> None:
        """Should map subscription tiers correctly."""
        assert limiter.get_tier_from_subscription("PRO") == "pro"
        assert limiter.get_tier_from_subscription("team") == "team"
        assert limiter.get_tier_from_subscription("ENTERPRISE") == "enterprise"
        assert limiter.get_tier_from_subscription(None) == "free"
        assert limiter.get_tier_from_subscription("unknown") == "free"


class TestMatchMetrics:
    """Tests for match metrics recording."""

    def test_record_match_values(self) -> None:
        """record_match should accept all required values."""
        MatchMetrics.record_match(
            tenant_id="test-tenant",
            job_id="test-job",
            score=0.85,
            passed_dealbreakers=True,
            confidence="high",
            duration_ms=150.5,
        )

    def test_record_batch_match_values(self) -> None:
        """record_batch_match should accept all required values."""
        MatchMetrics.record_batch_match(
            tenant_id="test-tenant",
            job_count=20,
            success_count=18,
            duration_ms=500.0,
        )

    def test_record_tailoring_values(self) -> None:
        """record_tailoring should accept all required values."""
        MatchMetrics.record_tailoring(
            tenant_id="test-tenant",
            job_id="test-job",
            ats_score=0.75,
            duration_ms=200.0,
        )

    def test_record_match_low_score(self) -> None:
        """record_match should handle low scores."""
        MatchMetrics.record_match(
            tenant_id="test-tenant",
            job_id="test-job",
            score=0.3,
            passed_dealbreakers=False,
            confidence="low",
            duration_ms=50.0,
        )

    def test_record_batch_match_zero_jobs(self) -> None:
        """record_batch_match should handle zero jobs."""
        MatchMetrics.record_batch_match(
            tenant_id="test-tenant",
            job_count=0,
            success_count=0,
            duration_ms=10.0,
        )
