"""
Middleware implementations for security and observability.

Includes:
- CSRF Protection middleware
- Request ID middleware for distributed tracing
"""

from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds a unique request ID to each request for distributed tracing.

    - Uses existing X-Request-ID header if present (for upstream services)
    - Generates new UUID if not present
    - Adds request ID to response headers
    - Attaches to request.state for logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        s = get_settings()
        header_name = s.request_id_header

        # Use existing or generate new
        request_id = request.headers.get(header_name) or str(uuid.uuid4())

        # Attach to request state for downstream access
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers[header_name] = request_id

        return response


def get_request_id(request: Request) -> str:
    """Extract request ID from request state, or generate one."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))


class CSRFMiddleware:
    """
    CSRF protection middleware using starlette-csrf.

    Configuration:
    - Exempts safe methods (GET, HEAD, OPTIONS, TRACE)
    - Exempts API webhook endpoints
    - Uses SameSite+HttpOnly cookies

    Usage:
        from starlette_csrf import CSRFMiddleware
        app.add_middleware(CSRFMiddleware, secret=settings.csrf_secret)
    """

    # Paths exempt from CSRF protection (webhooks, public endpoints)
    EXEMPT_PATHS = [
        "/health",
        "/healthz",
        "/api/v2/webhook",
        "/billing/webhook",
        "/sso/saml/acs",
        "/og/",
    ]

    @classmethod
    def exempt_urls(cls) -> list[str]:
        """Return list of URL patterns to exempt from CSRF."""
        return cls.EXEMPT_PATHS


def setup_csrf_middleware(app, secret: str) -> None:
    """
    Configure CSRF middleware on the FastAPI app.

    Fail-closed: in staging/prod, refuse to start without a CSRF secret.
    In local/dev, warn but continue (for development convenience).
    """
    if not secret:
        s = get_settings()
        if s.env.value in ("prod", "staging"):
            raise RuntimeError(
                "CSRF_SECRET is required in production/staging. "
                "Set the CSRF_SECRET environment variable."
            )
        logger.warning(
            "CSRF protection DISABLED - set CSRF_SECRET env var for production"
        )
        return

    try:
        from starlette_csrf.middleware import CSRFMiddleware as StarletteCSRF

        app.add_middleware(
            StarletteCSRF,
            secret=secret,
            cookie_name="csrftoken",
            cookie_secure=True,  # HTTPS only
            cookie_samesite="lax",
            exempt_urls=CSRFMiddleware.exempt_urls(),
        )
        logger.info("CSRF protection enabled")
    except ImportError:
        logger.error("starlette-csrf not installed - CSRF protection disabled")


def setup_request_id_middleware(app) -> None:
    """Add RequestID middleware to the app."""
    app.add_middleware(RequestIDMiddleware)
    logger.info("Request ID middleware enabled")


# ---------------------------------------------------------------------------
# IP Extraction Helper
# ---------------------------------------------------------------------------


def get_client_ip(request: Request) -> str:
    """
    Extract real client IP, respecting proxy headers (X-Forwarded-For).

    Falls back to X-Real-IP, then request.client.host.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For: client, proxy1, proxy2
        # Leftmost is the original client
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response.

    Headers:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY (unless iframe explicitly allowed)
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Strict-Transport-Security: max-age=31536000; includeSubDomains (if HTTPS/Prod)
    - Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; object-src 'none'
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Basic CSP; can be expanded with nonces if needed for inline scripts
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; frame-ancestors 'none'; object-src 'none'",
        )

        # HSTS (Strict-Transport-Security)
        # We assume SSL is handled by termination proxy (Render/Heroku/AWS),
        # so we check X-Forwarded-Proto or just enforce if env is PROD.
        # Ideally, we should check if request.url.scheme == "https" or settings.env == "prod"
        s = get_settings()
        if s.env.value == "prod":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


def setup_security_headers(app) -> None:
    """Add SecurityHeaders middleware to the app."""
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware enabled")
