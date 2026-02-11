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
    
    Only enabled if a secret is provided (required in prod).
    """
    if not secret:
        logger.warning(
            "CSRF protection DISABLED - set CSRF_SECRET env var for production"
        )
        return
    
    try:
        from starlette_csrf import CSRFMiddleware as StarletteCSRF
        
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
