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

# Cookie used for httpOnly session auth (magic link flow). CSRF is only enforced
# when this cookie is present. Bearer-only requests skip CSRF per OWASP.
AUTH_COOKIE_NAME = "jobhuntin_auth"

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
        "/auth/dev-login",
        "/auth/logout",
        "/auth/webhooks/resend",
        "/billing/webhook",
        "/sso/saml/acs",
        "/og/",
        "/webhook/resume_parse",  # Resume parse webhook (user-initiated but from same origin)
        "/contact",  # Public contact form (rate-limited by IP)
    ]

    @classmethod
    def exempt_urls(cls, env: str | None = None) -> list[str]:
        """Return list of URL patterns to exempt from CSRF."""
        return list(cls.EXEMPT_PATHS)


def _get_csrf_cookie_domain(
    *,
    is_prod: bool,
    api_host: str,
    app_host: str,
    api_url: str,
    app_url: str,
) -> str | None:
    """Derive cookie domain for CSRF so frontend and API can share the cookie.

    - Local (localhost/127.0.0.1): use "localhost" for cross-port (5173/8000).
    - Prod cross-origin (app.jobhuntin.com + api.jobhuntin.com): use parent "jobhuntin.com".
    - Same host or *.onrender.com: no shared parent, return None.
    """
    if not is_prod and api_host in ("localhost", "127.0.0.1") and app_host in ("localhost", "127.0.0.1"):
        return "localhost" if api_host == "localhost" else None

    if not is_prod or api_host == app_host:
        return None

    # Cross-origin production: derive parent domain from api or app URL
    for url in (api_url, app_url):
        if not url or "[REDACTED]" in url:
            continue
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or parsed.path).split(":")[0] or ""
            if not host:
                continue
            # Skip IPs and single-label (e.g. "localhost")
            if "." not in host or host.replace(".", "").isdigit():
                continue
            # Skip *.onrender.com (no shared parent we control)
            if host.endswith(".onrender.com") or host == "onrender.com":
                continue
            parts = host.split(".")
            if len(parts) >= 2:
                return ".".join(parts[-2:])
        except Exception:
            continue
    return None


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

    s = get_settings()
    exempt_patterns = [re.compile(p) for p in CSRFMiddleware.exempt_urls()]
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
            if origin and cors_origins and origin in cors_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

    is_prod = s.env.value in ("prod", "staging")
    # Secure=True is ONLY allowed over HTTPS. In local dev, it must be False.
    cookie_secure = is_prod or (s.app_base_url and s.app_base_url.startswith("https"))

    # sensitive_cookies: Only enforce CSRF when cookie-based auth is present.
    # Bearer-only requests skip CSRF per OWASP (browser cannot auto-send Authorization header).
    # Scales to 1 or 500 users: stateless, no server-side session lookup.
    sensitive_cookies: frozenset[str] = frozenset({AUTH_COOKIE_NAME})

    # cookie_domain: Enables cross-subdomain CSRF cookie when app and API differ.
    # Local: localhost for ports 5173/8000. Prod: parent domain (e.g. .jobhuntin.com).
    cookie_domain = _get_csrf_cookie_domain(
        is_prod=is_prod,
        api_host=api_host,
        app_host=app_host,
        api_url=s.api_public_url or "",
        app_url=s.app_base_url or "",
    )

    # cookie_httponly=False: double-submit pattern requires JS to read token for header
    app.add_middleware(
        CSRFForCORSMiddleware,
        secret=secret,
        cookie_name="csrftoken",
        cookie_secure=cookie_secure,
        cookie_httponly=False,
        cookie_samesite="none" if is_cross_origin else "lax",
        cookie_path="/",
        cookie_domain=cookie_domain,
        sensitive_cookies=sensitive_cookies,
        exempt_urls=exempt_patterns,
    )
    logger.info(
        f"CSRF protection enabled (SameSite={'none' if is_cross_origin else 'lax'}, "
        f"sensitive_cookies={list(sensitive_cookies)})"
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
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
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

        # CSP connect-src: must include API URL if cross-origin, and analytics
        connect_src = "'self' https://www.google-analytics.com https://www.googletagmanager.com https://api.resend.com"
        for url in (s.api_public_url, s.app_base_url):
            if url and url.startswith(("http://", "https://")) and "[REDACTED]" not in url:
                connect_src += f" {url.rstrip('/')}"

        # img-src: avoid 'https:' (allows any HTTPS); use specific domains
        img_src = "'self' data: blob: https://www.google-analytics.com https://www.googletagmanager.com"

        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"script-src {csp_script_src}; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            f"img-src {img_src}; "
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
