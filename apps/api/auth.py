"""
Auth endpoints for public web clients (magic links, etc.).
"""

from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from shared.config import Settings, settings_dependency
from shared.logging_config import get_logger
from shared.repo_root import find_repo_root

from shared.metrics import RateLimiter, incr

logger = get_logger("sorce.api.auth")


def _mask_email(email: str) -> str:
    """Mask email for logging to avoid PII exposure."""
    parts = email.split("@")
    if len(parts) != 2:
        return "***"
    local = parts[0]
    masked_local = local[:2] + "***" if len(local) > 2 else "***"
    return f"{masked_local}@{parts[1]}"


router = APIRouter(prefix="/auth", tags=["auth"])


_template_path = (
    find_repo_root(Path(__file__)) / "templates" / "emails" / "magic_link.html"
)
try:
    MAGIC_LINK_TEMPLATE = _template_path.read_text(encoding="utf-8")
except FileNotFoundError:
    MAGIC_LINK_TEMPLATE = (
        """<p>Use this link to sign in: <a href=\"$action_link\">$action_link</a></p>"""
    )
    logger.warning(
        "Magic link template not found at %s; falling back to plain text HTML",
        _template_path,
    )

# TTL-evicting cache for per-email rate limiters.
# Entries are (limiter, last_access_time). Eviction runs on access.
_magic_link_limiters: dict[str, tuple[RateLimiter, float]] = {}
_LIMITER_CACHE_MAX_SIZE = 10_000
_LIMITER_CACHE_TTL = 7200  # 2 hours

# Consumed magic link tokens (jti values) to prevent replay.
# In production, use Redis instead of in-memory set.
_consumed_tokens: dict[str, float] = {}
_CONSUMED_TOKEN_TTL = 3700  # slightly longer than magic link TTL


def _mark_token_consumed(jti: str) -> bool:
    """Mark a token as consumed. Returns False if already consumed."""
    now = time.monotonic()
    # Evict expired entries
    expired = [k for k, ts in _consumed_tokens.items() if now - ts > _CONSUMED_TOKEN_TTL]
    for k in expired:
        _consumed_tokens.pop(k, None)
    if jti in _consumed_tokens:
        return False
    _consumed_tokens[jti] = now
    return True


class MagicLinkRequest(BaseModel):
    email: EmailStr
    return_to: str | None = None


class MagicLinkResponse(BaseModel):
    status: str = "sent"


def _sanitize_return_to(value: str | None) -> str | None:
    """Whitelist-only sanitizer for return_to paths to prevent open redirects."""
    if not value:
        return None

    trimmed = value.strip()

    # Reject absolute URLs / dangerous schemes / protocol-relative
    lower = trimmed.lower()
    if (
        lower.startswith("http:")
        or lower.startswith("https:")
        or lower.startswith("javascript:")
        or lower.startswith("data:")
    ):
        return None
    if not trimmed.startswith("/") or trimmed.startswith("//"):
        return None

    # Separate path from query/hash for whitelist check, but preserve query
    parts = trimmed.split("?", 1)
    path_only = parts[0].split("#")[0]
    query = parts[1].split("#")[0] if len(parts) > 1 else None

    # Block traversal
    if "../" in path_only or "..\\" in path_only:
        return None

    allowed = {
        "/app/onboarding",
        "/app/dashboard",
        "/app/jobs",
        "/app/applications",
        "/app/holds",
        "/app/billing",
        "/app/settings",
        "/app/team",
    }

    if path_only not in allowed:
        return None

    # Re-append query string if present (safe: path is whitelisted)
    return f"{path_only}?{query}" if query else path_only


def _build_redirect_url(settings: Settings, return_to: str | None) -> str:
    base = settings.app_base_url.rstrip("/")
    if not base or base == "http://localhost:5173":
        logger.warning(
            "[MAGIC_LINK] APP_BASE_URL not configured properly, magic links may not work in production. "
            "Set APP_BASE_URL environment variable to your production URL (e.g., https://jobhuntin.com)"
        )
    if not base:
        base = "http://localhost:5173"
    redirect = f"{base}/login"
    safe_return = _sanitize_return_to(return_to)
    if safe_return:
        redirect = f"{redirect}?returnTo={quote(safe_return, safe='')}"
    return redirect


async def _get_pool():
    """Database pool dependency - overridden at app startup."""
    raise NotImplementedError("Pool dependency not injected")


async def _generate_magic_link(
    settings: Settings, email: str, redirect_to: str, db: Any
) -> str:
    """Generate a magic link with a signed JWT."""
    import uuid
    from datetime import datetime, timedelta, timezone

    import jwt

    logger.info(
        "[MAGIC_LINK] Starting generation",
        extra={"email": _mask_email(email), "redirect_to": redirect_to},
    )

    # Find or create user
    async with db.acquire() as conn:
        # First try to find existing user by email
        user_id = await conn.fetchval(
            "SELECT id FROM public.users WHERE email = $1", email
        )
        if not user_id:
            # Create new user
            logger.info("[MAGIC_LINK] Creating new user", extra={"email": _mask_email(email)})
            user_id = await conn.fetchval(
                """
                INSERT INTO public.users (id, email, created_at, updated_at)
                VALUES ($1, $2, now(), now())
                RETURNING id
            """,
                str(uuid.uuid4()),
                email,
            )
            logger.info(
                "[MAGIC_LINK] User created",
                extra={"user_id": str(user_id), "email": email},
            )
        else:
            logger.info(
                "[MAGIC_LINK] Found existing user",
                extra={"user_id": str(user_id), "email": email},
            )

        # Create empty profile if not exists
        await conn.execute(
            """
            INSERT INTO public.profiles (user_id, resume_url, profile_data)
            VALUES ($1, '', '{}')
            ON CONFLICT (user_id) DO NOTHING
        """,
            user_id,
        )
        logger.debug("[MAGIC_LINK] Profile ensured", extra={"user_id": str(user_id)})

    # Generate token
    ttl_seconds = getattr(settings, "magic_link_token_ttl_seconds", 3600)
    token_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "jti": token_id,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }

    if not settings.jwt_secret:
        logger.error("[MAGIC_LINK] JWT_SECRET not set - cannot sign magic link")
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: JWT_SECRET missing"
        )

    secret = settings.jwt_secret

    token = jwt.encode(payload, secret, algorithm="HS256")
    logger.info(
        "[MAGIC_LINK] Token generated",
        extra={"user_id": str(user_id), "email": email, "token_length": len(token)},
    )

    # Append token to redirect URL
    separator = "&" if "?" in redirect_to else "?"
    magic_link = f"{redirect_to}{separator}token={token}"
    logger.info(
        "[MAGIC_LINK] Magic link generated successfully",
        extra={"user_id": str(user_id), "email": email},
    )
    return magic_link


def _render_email_html(
    settings: Settings, action_link: str, return_to: str | None
) -> str:
    destination_path = return_to or "/app/dashboard"
    expires_minutes = max(1, settings.magic_link_token_ttl_seconds // 60)

    destination_labels = {
        "/app/onboarding": "Onboarding",
        "/app/dashboard": "Dashboard",
        "/app/jobs": "Job Feed",
        "/app/applications": "Applications",
        "/app/holds": "Hold Queue",
        "/app/billing": "Billing",
        "/app/settings": "Settings",
        "/app/team": "Team Workspace",
    }
    destination_label = destination_labels.get(
        destination_path, destination_path.replace("/app/", "").title()
    )

    html = (
        MAGIC_LINK_TEMPLATE.replace("$action_link", action_link)
        .replace("$destination", destination_label)
        .replace("$expires_minutes", str(expires_minutes))
    )
    return html


def _evict_stale_limiters() -> None:
    """Remove expired entries when cache exceeds max size."""
    if len(_magic_link_limiters) <= _LIMITER_CACHE_MAX_SIZE:
        return
    now = time.monotonic()
    expired = [
        k
        for k, (_, ts) in _magic_link_limiters.items()
        if now - ts > _LIMITER_CACHE_TTL
    ]
    for k in expired:
        _magic_link_limiters.pop(k, None)
    # If still over limit after TTL eviction, drop oldest entries
    if len(_magic_link_limiters) > _LIMITER_CACHE_MAX_SIZE:
        sorted_keys = sorted(
            _magic_link_limiters, key=lambda k: _magic_link_limiters[k][1]
        )
        for k in sorted_keys[: len(_magic_link_limiters) - _LIMITER_CACHE_MAX_SIZE]:
            _magic_link_limiters.pop(k, None)


def _get_rate_limiter(settings: Settings, email: str) -> RateLimiter:
    _evict_stale_limiters()
    entry = _magic_link_limiters.get(email)
    if (
        entry is not None
        and entry[0].max_calls == settings.magic_link_requests_per_hour
    ):
        _magic_link_limiters[email] = (entry[0], time.monotonic())
        return entry[0]
    limiter = RateLimiter(
        max_calls=settings.magic_link_requests_per_hour,
        window_seconds=float(settings.magic_link_rate_limit_window_seconds),
        name=f"magic_link:{email}",
    )
    _magic_link_limiters[email] = (limiter, time.monotonic())
    return limiter


async def _send_magic_link_email(
    settings: Settings, email: str, action_link: str, return_to: str | None
) -> None:
    if not settings.resend_api_key:
        raise HTTPException(status_code=500, detail="Email service is not configured")

    html = _render_email_html(settings, action_link, return_to)

    # Create a proper text version for better deliverability
    destination = return_to or "/app/dashboard"
    destination_name = {
        "/app/onboarding": "Onboarding",
        "/app/dashboard": "Dashboard",
        "/app/jobs": "Job Feed",
        "/app/applications": "Applications",
        "/app/holds": "Hold Queue",
        "/app/billing": "Billing",
        "/app/settings": "Settings",
        "/app/team": "Team Workspace",
    }.get(destination, destination.replace("/app/", "").title())

    text_content = f"""Hey there!

Here's your sign-in link for JobHuntin:

{action_link}

You'll be taken to: {destination_name}

This link expires in {settings.magic_link_token_ttl_seconds // 60} minutes.

If you didn't ask for this, no worries — just ignore it.

---
JobHuntin — Find your next job, faster
https://jobhuntin.com
"""

    payload = {
        "from": settings.email_from,
        "to": [email],
        "subject": "Sign in to JobHuntin",
        "html": html,
        "text": text_content,
        "headers": {
            "List-Unsubscribe": f"<{settings.app_base_url.rstrip('/')}/app/settings#notifications>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    logger.info(
        "[MAGIC_LINK] Sending email",
        extra={"email": _mask_email(email), "destination": destination_name},
    )

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.resend.com/emails", headers=headers, json=payload
        )

    if resp.status_code not in (200, 201):
        logger.error(
            "[MAGIC_LINK] Resend email failed",
            extra={
                "email": email,
                "status": resp.status_code,
                "response": resp.text[:200],
            },
        )
        raise HTTPException(status_code=502, detail="Failed to send magic link email")

    logger.info(
        "[MAGIC_LINK] Email sent successfully",
        extra={
            "email": email,
            "destination": destination_name,
            "resend_response": resp.json() if resp.text else None,
        },
    )
    # Note: Metric is incremented in request_magic_link endpoint with email_domain tag


@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    body: MagicLinkRequest,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
) -> MagicLinkResponse:
    """Generate a magic link and email it via Resend."""

    limiter = _get_rate_limiter(settings, body.email)
    if not await limiter.acquire():
        retry_after = limiter.next_available_in()
        logger.warning(
            "Magic link rate limit hit",
            extra={"email": body.email, "retry_after": retry_after},
        )
        incr(
            "auth.magic_link.rate_limited", {"email_domain": body.email.split("@")[-1]}
        )
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait before requesting another magic link.",
            headers={"Retry-After": str(int(math.ceil(retry_after)))},
        )

    redirect = _build_redirect_url(settings, body.return_to)
    action_link = await _generate_magic_link(settings, body.email, redirect, db)
    await _send_magic_link_email(settings, body.email, action_link, body.return_to)
    incr("auth.magic_link.sent", {"email_domain": body.email.split("@")[-1]})
    return MagicLinkResponse()
