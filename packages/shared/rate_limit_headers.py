"""
Rate limit headers middleware.

Adds X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers
to all responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.logging_config import get_logger

logger = get_logger("sorce.rate_limit_headers")


@dataclass
class RateLimitInfo:
    """Rate limit information for a client."""
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: int | None = None


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds rate limit headers to responses."""

    def __init__(
        self,
        app,
        default_limit: int = 100,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._limits: dict[str, RateLimitInfo] = {}

    def _get_client_key(self, request: Request) -> str:
        """Get unique key for client (IP or user ID)."""
        # Use user ID if authenticated
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        return f"ip:{request.client.host if request.client else 'unknown'}"

    def _get_tier_limit(self, request: Request) -> int:
        """Get rate limit based on user tier."""
        tier = getattr(request.state, "tier", "free")

        tier_limits = {
            "free": 100,
            "pro": 500,
            "enterprise": 5000,
        }

        return tier_limits.get(tier, self.default_limit)

    def check_rate_limit(self, request: Request) -> RateLimitInfo:
        """Check rate limit for client and return info."""
        key = self._get_client_key(request)
        limit = self._get_tier_limit(request)
        now = datetime.now()

        if key not in self._limits:
            # First request
            info = RateLimitInfo(
                limit=limit,
                remaining=limit - 1,
                reset_at=now + timedelta(seconds=self.window_seconds),
            )
            self._limits[key] = info
            return info

        info = self._limits[key]

        # Check if window has reset
        if now >= info.reset_at:
            info = RateLimitInfo(
                limit=limit,
                remaining=limit - 1,
                reset_at=now + timedelta(seconds=self.window_seconds),
            )
            self._limits[key] = info
            return info

        # Decrement remaining
        if info.remaining > 0:
            info.remaining -= 1
        else:
            # Rate limited
            retry_after = int((info.reset_at - now).total_seconds())
            info.retry_after = retry_after

        return info

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add rate limit headers."""
        info = self.check_rate_limit(request)

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info.limit)
        response.headers["X-RateLimit-Remaining"] = str(info.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(info.reset_at.timestamp()))

        if info.retry_after:
            response.headers["Retry-After"] = str(info.retry_after)

        return response


def setup_rate_limit_headers(app, default_limit: int = 100, window_seconds: int = 60):
    """Add rate limit headers middleware to app."""
    app.add_middleware(
        RateLimitHeadersMiddleware,
        default_limit=default_limit,
        window_seconds=window_seconds,
    )
    logger.info(
        "Rate limit headers middleware enabled",
        extra={"default_limit": default_limit, "window_seconds": window_seconds},
    )
