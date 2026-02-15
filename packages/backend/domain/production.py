"""
Production hardening module for AI endpoints.

Provides:
- Comprehensive error handling middleware
- Multi-tenant rate limiting
- Structured logging with context
- Metrics for match success rates
- Request/response validation
"""

from __future__ import annotations

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import HTTPException, Request, Response
from shared.logging_config import get_logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from shared.metrics import incr, observe

logger = get_logger("sorce.production")

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_ctx: ContextVar[str] = ContextVar("tenant_id", default="")


@dataclass
class RequestContext:
    """Context for a single request."""

    request_id: str
    tenant_id: str | None = None
    user_id: str | None = None
    endpoint: str = ""
    method: str = ""
    start_time: float = field(default_factory=time.monotonic)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProductionMiddleware(BaseHTTPMiddleware):
    """
    Production-hardening middleware for all API endpoints.

    Features:
    - Request ID tracking
    - Structured logging with context
    - Error handling with proper HTTP codes
    - Request timing metrics
    - Tenant context extraction
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._error_counts: dict[str, int] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(request_id)

        tenant_id = request.headers.get("X-Tenant-ID", "")
        tenant_id_ctx.set(tenant_id)

        ctx = RequestContext(
            request_id=request_id,
            tenant_id=tenant_id or None,
            endpoint=request.url.path,
            method=request.method,
        )

        log_context = {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "method": request.method,
            "path": request.url.path,
        }

        try:
            response = await call_next(request)

            duration = time.monotonic() - ctx.start_time
            observe(
                "api.request_duration_seconds", duration, {"endpoint": ctx.endpoint}
            )

            response.headers["X-Request-ID"] = request_id

            if ctx.tenant_id:
                incr(
                    "api.requests",
                    {"tenant_id": ctx.tenant_id, "endpoint": ctx.endpoint},
                )

            logger.info(
                "Request completed",
                extra={
                    **log_context,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
            )

            return response

        except HTTPException as e:
            duration = time.monotonic() - ctx.start_time
            self._record_error(ctx.endpoint, e.status_code)

            logger.warning(
                "HTTP exception",
                extra={
                    **log_context,
                    "status_code": e.status_code,
                    "detail": str(e.detail),
                },
            )

            incr(
                "api.errors",
                {"endpoint": ctx.endpoint, "status_code": str(e.status_code)},
            )

            raise

        except Exception as e:
            duration = time.monotonic() - ctx.start_time
            self._record_error(ctx.endpoint, 500)

            logger.error(
                "Unhandled exception",
                extra={**log_context, "error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )

            incr("api.errors", {"endpoint": ctx.endpoint, "status_code": "500"})

            raise HTTPException(status_code=500, detail="Internal server error") from e

    def _record_error(self, endpoint: str, status_code: int) -> None:
        key = f"{endpoint}:{status_code}"
        self._error_counts[key] = self._error_counts.get(key, 0) + 1


class AIEndpointError(Exception):
    """Base exception for AI endpoint errors."""

    def __init__(self, message: str, error_code: str, http_status: int = 500) -> None:
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        super().__init__(message)


class LLMError(AIEndpointError):
    """LLM-related errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "LLM_ERROR", 502)


class EmbeddingError(AIEndpointError):
    """Embedding service errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "EMBEDDING_ERROR", 502)


class RateLimitError(AIEndpointError):
    """Rate limit exceeded errors."""

    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message, "RATE_LIMIT", 429)
        self.retry_after = retry_after


class TenantIsolationError(AIEndpointError):
    """Tenant isolation violation errors."""

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message, "TENANT_ISOLATION", 403)


class ValidationError(AIEndpointError):
    """Validation errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR", 400)


def handle_ai_error(error: Exception) -> HTTPException:
    """Convert AI endpoint errors to HTTP exceptions with proper logging."""
    if isinstance(error, AIEndpointError):
        logger.warning(
            "AI endpoint error",
            extra={
                "error_code": error.error_code,
                "error_msg": error.message,
                "http_status": error.http_status,
                "request_id": request_id_ctx.get(),
                "tenant_id": tenant_id_ctx.get(),
            },
        )
        return HTTPException(
            status_code=error.http_status,
            detail={"error": error.error_code, "message": error.message},
        )

    logger.error(
        "Unexpected error in AI endpoint",
        extra={
            "error_str": str(error),
            "error_type": type(error).__name__,
            "request_id": request_id_ctx.get(),
        },
        exc_info=True,
    )
    return HTTPException(
        status_code=500,
        detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )


class TenantRateLimiter:
    """
    Multi-tenant rate limiter with per-tenant quotas.

    Supports different rate limits based on tenant tier:
    - FREE: 20 AI requests per minute
    - PRO: 100 AI requests per minute
    - TEAM: 500 AI requests per minute
    - ENTERPRISE: Unlimited (within platform limits)
    """

    TIER_LIMITS = {
        "free": 20,
        "pro": 100,
        "team": 500,
        "enterprise": 2000,
    }

    def __init__(self) -> None:
        self._limiters: dict[str, Any] = {}

    async def check_rate_limit(
        self,
        tenant_id: str,
        tier: str = "free",
        endpoint: str = "default",
    ) -> tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.

        Returns:
            Tuple of (allowed, remaining, reset_after_seconds)
        """
        from shared.metrics import get_rate_limiter

        limit = self.TIER_LIMITS.get(tier.lower(), self.TIER_LIMITS["free"])
        limiter_name = f"tenant:{tenant_id}:{endpoint}"
        limiter = get_rate_limiter(limiter_name, max_calls=limit, window_seconds=60)

        allowed = await limiter.acquire()
        remaining = max(0, limit - limiter.current_count())
        reset_after = limiter.next_available_in()

        if not allowed:
            incr("api.rate_limited", {"tenant_id": tenant_id, "endpoint": endpoint})
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "tenant_id": tenant_id,
                    "tier": tier,
                    "endpoint": endpoint,
                    "limit": limit,
                },
            )

        return allowed, remaining, int(reset_after)

    def get_tier_from_subscription(self, subscription_tier: str | None) -> str:
        """Map subscription tier to rate limit tier."""
        if not subscription_tier:
            return "free"

        tier_map = {
            "free": "free",
            "pro": "pro",
            "team": "team",
            "enterprise": "enterprise",
        }
        return tier_map.get(subscription_tier.lower(), "free")


tenant_rate_limiter = TenantRateLimiter()


class MatchMetrics:
    """Metrics for semantic matching operations."""

    @staticmethod
    def record_match(
        tenant_id: str,
        job_id: str,
        score: float,
        passed_dealbreakers: bool,
        confidence: str,
        duration_ms: float,
    ) -> None:
        """Record a semantic match operation."""
        incr("semantic_match.requests", {"tenant_id": tenant_id})

        score_bucket = "high" if score >= 0.8 else "medium" if score >= 0.6 else "low"
        incr("semantic_match.scores", {"tenant_id": tenant_id, "bucket": score_bucket})

        if passed_dealbreakers:
            incr("semantic_match.passed", {"tenant_id": tenant_id})
        else:
            incr("semantic_match.filtered", {"tenant_id": tenant_id})

        incr("semantic_match.confidence", {"tenant_id": tenant_id, "level": confidence})

        observe("semantic_match.duration_ms", duration_ms, {"tenant_id": tenant_id})

        logger.info(
            "Semantic match completed",
            extra={
                "tenant_id": tenant_id,
                "job_id": job_id,
                "score": score,
                "passed": passed_dealbreakers,
                "confidence": confidence,
                "duration_ms": duration_ms,
            },
        )

    @staticmethod
    def record_batch_match(
        tenant_id: str,
        job_count: int,
        success_count: int,
        duration_ms: float,
    ) -> None:
        """Record a batch match operation."""
        incr("semantic_match.batch_requests", {"tenant_id": tenant_id})
        observe("semantic_match.batch_size", job_count, {"tenant_id": tenant_id})
        observe(
            "semantic_match.batch_duration_ms", duration_ms, {"tenant_id": tenant_id}
        )

        success_rate = success_count / job_count if job_count > 0 else 0
        observe(
            "semantic_match.batch_success_rate", success_rate, {"tenant_id": tenant_id}
        )

        logger.info(
            "Batch semantic match completed",
            extra={
                "tenant_id": tenant_id,
                "job_count": job_count,
                "success_count": success_count,
                "duration_ms": duration_ms,
            },
        )

    @staticmethod
    def record_tailoring(
        tenant_id: str,
        job_id: str,
        ats_score: float,
        duration_ms: float,
    ) -> None:
        """Record a resume tailoring operation."""
        incr("resume_tailoring.requests", {"tenant_id": tenant_id})

        ats_bucket = (
            "high" if ats_score >= 0.8 else "medium" if ats_score >= 0.6 else "low"
        )
        incr(
            "resume_tailoring.ats_scores",
            {"tenant_id": tenant_id, "bucket": ats_bucket},
        )

        observe("resume_tailoring.duration_ms", duration_ms, {"tenant_id": tenant_id})

        logger.info(
            "Resume tailoring completed",
            extra={
                "tenant_id": tenant_id,
                "job_id": job_id,
                "ats_score": ats_score,
                "duration_ms": duration_ms,
            },
        )


def validate_tenant_access(tenant_id: str | None, resource_tenant_id: str) -> None:
    """Validate that tenant has access to the requested resource."""
    if not tenant_id:
        raise TenantIsolationError("No tenant context provided")

    if tenant_id != resource_tenant_id:
        logger.warning(
            "Tenant isolation violation attempt",
            extra={
                "requesting_tenant": tenant_id,
                "resource_tenant": resource_tenant_id,
            },
        )
        raise TenantIsolationError()


def get_request_context() -> dict[str, Any]:
    """Get the current request context for logging."""
    return {
        "request_id": request_id_ctx.get(),
        "tenant_id": tenant_id_ctx.get(),
    }
