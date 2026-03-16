"""Redirect and URL validation for OAuth, SSO, webhooks — prevent open redirect and SSRF."""

from __future__ import annotations

import socket
from urllib.parse import urlparse

from fastapi import HTTPException

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.security_utils import is_private_ip, is_safe_redirect_url

logger = get_logger("sorce.redirect_validation")


def _get_allowed_redirect_origins() -> list[str]:
    """Get allowed origins for redirect URL validation."""
    settings = get_settings()
    app_url = (settings.app_base_url or "").strip()
    if not app_url or app_url == "[REDACTED]":
        return []
    origins = [app_url.rstrip("/")]
    if settings.env.value == "local":
        origins.extend(settings.parsed_local_redirect_origins)
    return origins


def validate_redirect_url(url: str, param_name: str = "redirect_url") -> None:
    """Validate redirect URL against allowed origins. Raises HTTPException if invalid."""
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail=f"Missing {param_name}")
    url = url.strip()
    origins = _get_allowed_redirect_origins()
    if not origins:
        raise HTTPException(
            status_code=503,
            detail="APP_BASE_URL not configured. Cannot validate redirect URL.",
        )
    # Use shared utility to validate redirect URL against allowed origins
    if not is_safe_redirect_url(url, origins):
        raise HTTPException(status_code=400, detail=f"Invalid {param_name}")


def validate_webhook_url(url: str, param_name: str = "webhook_url") -> None:
    """Validate webhook/callback URL: HTTPS only, no private/reserved IPs (SSRF prevention)."""
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail=f"Missing {param_name}")
    try:
        parsed = urlparse(url.strip())
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid {param_name}")
    if parsed.scheme != "https":
        raise HTTPException(
            status_code=400,
            detail=f"{param_name} must use HTTPS",
        )
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail=f"Invalid {param_name}")
    # Use shared utility to check for private IP addresses
    if is_private_ip(parsed.hostname):
        raise HTTPException(
            status_code=400,
            detail=f"{param_name} must point to a public address",
        )


def validate_oauth_redirect_uri(redirect_uri: str) -> None:
    """Validate OAuth redirect_uri: must be HTTPS (or localhost in dev) and not private IP."""
    if not redirect_uri or not redirect_uri.strip():
        raise HTTPException(status_code=400, detail="Missing redirect_uri")
    try:
        parsed = urlparse(redirect_uri.strip())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    if parsed.scheme not in ("https", "http"):
        raise HTTPException(
            status_code=400,
            detail="redirect_uri must use https or http (localhost only)",
        )
    if parsed.scheme == "http" and parsed.hostname not in (
        "localhost",
        "127.0.0.1",
        "::1",
    ):
        raise HTTPException(
            status_code=400,
            detail="redirect_uri must use HTTPS for non-localhost",
        )
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
        return
    # Use shared utility to check for private IP addresses
    if is_private_ip(parsed.hostname):
        raise HTTPException(
            status_code=400,
            detail="redirect_uri must point to a public address",
        )
