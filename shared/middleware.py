"""Middleware implementations for security and observability.

Includes:
- CSRF Protection middleware
- Request ID middleware for distributed tracing
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from shared.config import get_settings
from shared.logging_config import get_logger

try:
    from starlette_csrf.middleware import CSRFMiddleware as StarletteCSRF
except ImportError:
    StarletteCSRF = None  # type: ignore[misc, assignment]

logger = get_logger("sorce.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Adds a unique request ID to each request for distributed tracing.

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

        return response  # type: ignore[no-any-return]


def get_request_id(request: Request) -> str:
    """Extract request ID from request state, or generate one."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))


class CSRFMiddleware:
    """CSRF protection middleware using starlette-csrf.

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
        "/auth/magic-link",
        "/auth/verify-magic",
        "/auth/logout",
        "/auth/webhooks/resend",
        "/api/v2/webhook",
        "/billing/webhook",
        "/sso/saml/acs",
        "/og/",
        "/webhook/resume_parse",  # Resume parse webhook (user-initiated but from same origin)
    ]

    @classmethod
    def exempt_urls(cls) -> list[str]:
        """Return list of URL patterns to exempt from CSRF."""
        return cls.EXEMPT_PATHS


def setup_csrf_middleware(app, secret: str) -> None:
    """Configure CSRF middleware on the FastAPI app.

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

    if StarletteCSRF is None:
        logger.error("starlette-csrf not installed - CSRF protection disabled")
        return

    exempt_patterns = [re.compile(p) for p in CSRFMiddleware.exempt_urls()]
    s = get_settings()
    api_host = urlparse(s.api_public_url).hostname if s.api_public_url else ""
    app_host = urlparse(s.app_base_url).hostname if s.app_base_url else ""
    is_cross_origin = api_host != app_host and api_host and app_host

    class CSRFForCORSMiddleware(StarletteCSRF):
        def _get_error_response(self, request: Request) -> Response:
            response = JSONResponse(
                {
                    "error": {
                        "code": "CSRF_FAILED",
                        "message": "CSRF validation failed",
                    }
                },
                status_code=403,
            )
            origin = request.headers.get("origin", "")
            cors_origins = getattr(app.state, "cors_origins", [])
            if origin and (origin in cors_origins or not cors_origins):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

    is_prod = s.env.value in ("prod", "staging")
    # Secure=True is ONLY allowed over HTTPS. In local dev, it must be False.
    cookie_secure = is_prod or (s.app_base_url and s.app_base_url.startswith("https"))

    app.add_middleware(
        CSRFForCORSMiddleware,
        secret=secret,
        cookie_name="csrftoken",
        cookie_secure=cookie_secure,
        cookie_samesite="none" if is_cross_origin else "lax",
        exempt_urls=exempt_patterns,
    )
    logger.info(
        f"CSRF protection enabled (SameSite={'none' if is_cross_origin else 'lax'})"
    )


def setup_request_id_middleware(app) -> None:
    """Add RequestID middleware to the app."""
    app.add_middleware(RequestIDMiddleware)
    logger.info("Request ID middleware enabled")


# ---------------------------------------------------------------------------
# IP Extraction Helper
# ---------------------------------------------------------------------------


def get_client_ip(request: Request) -> str:
    """Extract client IP, using rightmost XFF entry to prevent spoofing."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Use rightmost (most trustworthy) entry — the one added by our reverse proxy
        parts = [p.strip() for p in forwarded.split(",")]
        if parts:
            return parts[-1]
        elif request.client:
            return request.client.host or "unknown"
        else:
            return "unknown"
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response.

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
        s = get_settings()

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # S3 (Audit): Enhanced CSP with nonce support for dynamic scripts
        # Uses nonce-based approach instead of 'unsafe-inline' for better security
        csp_script_src = (
            "'self' https://www.googletagmanager.com https://www.google-analytics.com"
        )
        if hasattr(request.state, "csp_nonce"):
            csp_script_src += f" 'nonce-{request.state.csp_nonce}'"
        else:
            # Fallback to 'unsafe-inline' only when nonce not available (rare)
            csp_script_src += " 'unsafe-inline'"

        # CSP connect-src: must include API URL if it's cross-origin, and analytics
        connect_src = "'self' https://www.google-analytics.com https://www.googletagmanager.com https://api.resend.com"
        if s.api_public_url:
            connect_src += f" {s.api_public_url}"
        if s.app_base_url:
            connect_src += f" {s.app_base_url}"

        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"script-src {csp_script_src}; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https: blob:; "
            f"connect-src {connect_src}; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "object-src 'none'"
        )

        # HSTS (Strict-Transport-Security)
        # Must be set by server, not meta tag. Enforce in production.
        if s.env.value == "prod":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        elif request.url.scheme == "https":
            # For HTTPS in non-prod environments
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response  # type: ignore[no-any-return]


def setup_security_headers(app) -> None:
    """Add SecurityHeaders middleware to the app."""
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware enabled")
