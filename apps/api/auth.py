"""Auth endpoints for public web clients (magic links, etc.)."""

from __future__ import annotations

import asyncio
import math
import time
from datetime import timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote

import httpx
import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr

from backend.domain.session_manager import SessionManager
from shared.config import Settings, settings_dependency
from shared.logging_config import get_logger
from shared.metrics import RateLimiter, get_rate_limiter, incr
from shared.middleware import get_client_ip
from shared.repo_root import find_repo_root

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


# Load email templates
templates_dir = find_repo_root(Path(__file__)) / "templates" / "emails"

_template_path_html = templates_dir / "magic_link.html"
_template_path_txt = templates_dir / "magic_link.txt"

try:
    MAGIC_LINK_TEMPLATE_HTML = _template_path_html.read_text(encoding="utf-8")
except FileNotFoundError:
    MAGIC_LINK_TEMPLATE_HTML = (
        """<p>Use this link to sign in: <a href=\"$action_link\">$action_link</a></p>"""
    )
    logger.warning(
        "Magic link HTML template not found at %s; falling back to plain text HTML",
        _template_path_html,
    )

try:
    MAGIC_LINK_TEMPLATE_TXT = _template_path_txt.read_text(encoding="utf-8")
except FileNotFoundError:
    MAGIC_LINK_TEMPLATE_TXT = """Hey there!

Here's your sign-in link for $app_name:

$action_link

You'll be taken to: $destination

This link expires in $expires_minutes minutes.

If you didn't ask for this, no worries — just ignore it.

---
$app_name — $app_tagline
$app_base_url
"""
    logger.warning(
        "Magic link text template not found at %s; using fallback",
        _template_path_txt,
    )

# TTL-evicting cache for per-email rate limiters.
# Entries are (limiter, last_access_time). Eviction runs on access.
_magic_link_limiters: dict[str, tuple[RateLimiter, float]] = {}
_LIMITER_CACHE_MAX_SIZE = 10_000
_LIMITER_CACHE_TTL = 7200  # 2 hours

# Consumed magic link tokens (jti values) to prevent replay.
# Uses Redis when available (multi-worker safe); falls back to in-memory for local dev.
_consumed_tokens: dict[str, float] = {}
_CONSUMED_TOKEN_TTL = 3700  # slightly longer than magic link TTL
_REDIS_KEY_PREFIX = "auth:consumed_jti:"


async def _mark_token_consumed(jti: str, settings: Settings) -> bool:
    """Mark a token as consumed. Returns False if already consumed. Uses Redis when available."""
    if settings.redis_url:
        try:
            from shared.redis_client import get_redis

            r = await get_redis()
            key = f"{_REDIS_KEY_PREFIX}{jti}"
            # SET NX with TTL: only set if not exists, return True; if exists return False
            ok = await r.set(key, "1", nx=True, ex=_CONSUMED_TOKEN_TTL)
            return bool(ok)
        except Exception as e:
            logger.warning(
                "Redis consumed-token check failed, falling back to in-memory: %s", e
            )

    # In-memory fallback (single-instance only) - NOT safe for multi-worker deployments
    if settings.env.value == "prod":
        # CRITICAL: Fail fast in production without Redis to prevent security vulnerability
        logger.critical(
            "Redis not available in production - magic link token replay protection disabled. "
            "Set REDIS_URL for multi-instance deployments. This is a security risk."
        )
        raise RuntimeError(
            "Redis required for production token replay protection. "
            "Set REDIS_URL environment variable."
        )

    if not hasattr(_mark_token_consumed, "_warned_no_redis"):
        logger.warning(
            "Redis not available - magic link token replay prevention uses in-memory store. "
            "Set REDIS_URL for multi-instance deployments."
        )
        _mark_token_consumed._warned_no_redis = True  # type: ignore

    now = time.monotonic()
    expired = [
        k for k, ts in _consumed_tokens.items() if now - ts > _CONSUMED_TOKEN_TTL
    ]
    for k in expired:
        _consumed_tokens.pop(k, None)
    if jti in _consumed_tokens:
        return False
    _consumed_tokens[jti] = now
    return True


async def _revoke_session_token(jti: str, settings: Settings) -> None:
    """Revoke a session token by adding jti to Redis blacklist."""
    from shared.session_revocation import revoke_jti_in_redis

    await revoke_jti_in_redis(jti, settings.redis_url, settings.env.value)


async def _is_session_token_revoked(jti: str, settings: Settings) -> bool:
    """Check if a session token has been revoked.

    Args:
        jti: JWT ID claim from the session token
        settings: Application settings

    Returns:
        True if token is revoked, False otherwise
    """
    if not settings.redis_url:
        # In production, require Redis for revocation checks
        if settings.env.value == "prod":
            logger.warning(
                "Redis not available - cannot check session token revocation. "
                "Assuming token is valid (security risk)."
            )
        return False

    try:
        from shared.redis_client import get_redis

        r = await get_redis()
        key = f"auth:revoked_jti:{jti}"
        exists = await r.exists(key)
        return bool(exists)
    except Exception as e:
        logger.warning("Failed to check session token revocation: %s", e)
        # Fail open in case of Redis errors (don't block legitimate users)
        # But log the error for monitoring
        return False


class MagicLinkRequest(BaseModel):
    email: EmailStr
    return_to: str | None = None
    captcha_token: str | None = None


class MagicLinkResponse(BaseModel):
    status: str = "sent"


# Common disposable/temporary email domains to block
_DISPOSABLE_EMAIL_DOMAINS: set[str] = {
    # Major disposable providers
    "mailinator.com",
    "guerrillamail.com",
    "tempmail.com",
    "throwawaymail.com",
    "yopmail.com",
    "sharklasers.com",
    "getairmail.com",
    "temp-mail.org",
    "fakeinbox.com",
    "tempinbox.com",
    "mailnesia.com",
    "tempmailaddress.com",
    "burnermail.io",
    "disposablemail.com",
    "emailondeck.com",
    "getnada.com",
    "inboxkitten.com",
    "maildrop.cc",
    "mailforspam.com",
    "mailsac.com",
    "mailtothis.com",
    "mytemp.email",
    "shieldemail.net",
    "tempm.com",
    "tempmails.com",
    "thistempmail.com",
    "tmpmail.org",
    "trashmail.com",
    "trash-mail.com",
    "wegwerfmail.de",
    # yandex.com removed: legitimate provider used by millions
    # Temporary mail variants
    "10minutemail.com",
    "10minutemail.net",
    "10minemail.com",
    "20minute.email",
    "20minutemail.com",
    "30minutemail.com",
    "60minutemail.com",
    "hourlymail.com",
    "minutemail.com",
    "instantemail.com",
    "quickmail.com",
    # Additional disposable providers (2025)
    "tempail.com",
    "guerrillamail.info",
    "guerrillamail.biz",
    "guerrillamail.de",
    "spam4.me",
    "mail.tm",
    "dispostable.com",
    "mailinator2.com",
    "grr.la",
    "guerrillamail.org",
    "fakeinbox.info",
    "tempmailo.com",
    "dropmail.me",
    "emailfake.com",
    "minuteinbox.com",
}


def _is_disposable_email(email: str) -> bool:
    """Check if email domain is a known disposable/temporary email provider."""
    try:
        domain = email.lower().split("@")[-1]
        return domain in _DISPOSABLE_EMAIL_DOMAINS
    except Exception:
        return False


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

    # S13: Must match magicLinkService.ts allowedPaths exactly
    allowed = {
        "/app/onboarding",
        "/app/dashboard",
        "/app/jobs",
        "/app/applications",
        "/app/holds",
        "/app/billing",
        "/app/settings",
        "/app/team",
        "/app/matches",
        "/app/tailor",
        "/app/ats-score",
        "/app/job-alerts",
        "/app/pipeline-view",
        "/app/application-export",
        "/app/follow-up-reminders",
        "/app/interview-practice",
        "/app/multi-resume",
        "/app/application-notes",
        "/app/communication-preferences",
        "/app/notification-history",
        "/app/dlq-dashboard",
        "/app/screenshot-capture",
        "/app/agent-improvements",
        "/app/admin/usage",
        "/app/admin/matches",
        "/app/admin/alerts",
        "/app/admin/sources",
    }

    if path_only not in allowed:
        return None

    # Re-append query string if present (safe: path is whitelisted)
    return f"{path_only}?{query}" if query else path_only


def _build_redirect_url(settings: Settings, return_to: str | None) -> str:
    base = settings.app_base_url.rstrip("/")
    if not base or base == "http://localhost:5173":
        logger.warning(
            "[MAGIC_LINK] APP_BASE_URL not configured properly, "
            "magic links may not work in production. "
            "Set APP_BASE_URL environment variable to your "
            "production URL (e.g., https://jobhuntin.com)"
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


async def _find_or_create_user_by_email(
    conn: Any, email: str, settings: Settings
) -> tuple[str, bool]:
    """
    Find existing user or create new one on verification.

    Returns tuple of (user_id, is_new_user).
    """
    import uuid

    # Use INSERT ... ON CONFLICT to avoid race when two magic links for same new email are verified concurrently
    new_id = str(uuid.uuid4())
    row = await conn.fetchrow(
        """
        INSERT INTO public.users (id, email, created_at, updated_at)
        VALUES ($1, $2, now(), now())
        ON CONFLICT (email) DO UPDATE SET updated_at = now()
        RETURNING id
        """,
        new_id,
        email,
    )
    if not row:
        raise RuntimeError("User insert/upsert failed")
    user_id = row["id"]
    inserted = str(user_id) == new_id

    if inserted:
        logger.info("[MAGIC_LINK] Creating new user for email: %s", _mask_email(email))
        await conn.execute(
            """
            INSERT INTO public.profiles (user_id, profile_data)
            VALUES ($1, '{}')
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
        )
        logger.info(
            "[MAGIC_LINK] New user created with ID %s for email: %s",
            str(user_id),
            _mask_email(email),
        )
    else:
        logger.info("[MAGIC_LINK] Existing user found (race) for email: %s", _mask_email(email))

    return str(user_id), inserted


async def _generate_magic_link(
    settings: Settings,
    email: str,
    redirect_to: str,
    db: Any,
    return_to: str | None = None,
    client_ip: str | None = None,
) -> tuple[str, str]:
    """
    Generate a magic link with a signed JWT.

    Returns tuple of (magic_link_url, pending_user_id_or_email).
    The user_id is stored in the token for existing users, or email for new users.

    If MAGIC_LINK_BIND_TO_IP is enabled, the token will be bound to the requesting IP.
    """
    import uuid
    from datetime import datetime, timedelta

    import jwt

    logger.info(
        "[MAGIC_LINK] Starting generation for email: %s",
        _mask_email(email),
        extra={"email": _mask_email(email), "redirect_to": redirect_to},
    )

    # Find existing user (if any) - don't create yet
    async with db.acquire() as conn:
        existing_user_id = await conn.fetchval(
            "SELECT id FROM public.users WHERE email = $1", email
        )

        if existing_user_id:
            user_identifier = str(existing_user_id)
            logger.info(
                "[MAGIC_LINK] Found existing user with ID %s for email: %s",
                user_identifier,
                _mask_email(email),
            )
        else:
            # Store email in token for new user creation on verification
            user_identifier = email
            logger.info(
                "[MAGIC_LINK] No existing user for email: %s, will create on verification",
                _mask_email(email),
            )

    # Generate token
    ttl_seconds = getattr(settings, "magic_link_token_ttl_seconds", 3600)
    token_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Optional: Bind token to requesting IP for additional security
    # This prevents token theft and use from different IP addresses
    bind_to_ip = getattr(settings, "magic_link_bind_to_ip", False)
    ip_hash = None
    if bind_to_ip and client_ip:
        import hashlib

        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    payload = {
        "sub": str(user_identifier),
        "email": email,
        "aud": "authenticated",
        "jti": token_id,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(seconds=ttl_seconds),
        "new_user": existing_user_id is None,
    }

    # Add IP binding if enabled
    if ip_hash:
        payload["ip_hash"] = ip_hash

    if not settings.jwt_secret:
        logger.error("[MAGIC_LINK] JWT_SECRET not set - cannot sign magic link")
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: JWT_SECRET missing"
        )

    secret = settings.jwt_secret

    token = jwt.encode(payload, secret, algorithm="HS256")
    logger.info(
        "[MAGIC_LINK] Token generated for %s with jti %s",
        "existing user" if existing_user_id else "new user",
        token_id,
    )

    # Use frontend URL for magic link (better UX - users see branded domain)
    # Frontend will redirect to backend to verify token and set cookie
    # Ensure we use the frontend URL (jobhuntin.com), not the backend URL
    app_url = settings.app_base_url.rstrip("/")
    # Fix: If app_base_url contains backend domain (sorce, api.), use jobhuntin.com instead
    if (
        not app_url
        or "sorce" in app_url.lower()
        or "api." in app_url.lower()
        or app_url.startswith("http://localhost:8000")
    ):
        app_url = "https://jobhuntin.com"
    verify_url = f"{app_url}/login?token={quote(token, safe='')}"
    safe_return = _sanitize_return_to(return_to) if return_to else None
    if safe_return:
        verify_url += f"&returnTo={quote(safe_return, safe='')}"
    logger.info(
        "[MAGIC_LINK] Using frontend verify flow for %s",
        "existing user" if existing_user_id else "new user",
    )
    return verify_url, user_identifier


_DESTINATION_LABELS = {
    "/app/onboarding": "Onboarding",
    "/app/dashboard": "Dashboard",
    "/app/jobs": "Job Feed",
    "/app/applications": "Applications",
    "/app/holds": "Hold Queue",
    "/app/billing": "Billing",
    "/app/settings": "Settings",
    "/app/team": "Team Workspace",
    "/app/matches": "AI Matches",
    "/app/tailor": "AI Tailor",
    "/app/ats-score": "ATS Score",
    "/app/admin/usage": "Usage",
    "/app/admin/matches": "Admin Matches",
    "/app/admin/alerts": "Admin Alerts",
    "/app/admin/sources": "Admin Sources",
}


def _get_destination_label(destination_path: str) -> str:
    """Get human-readable destination label from path."""
    return _DESTINATION_LABELS.get(
        destination_path, destination_path.replace("/app/", "").title()
    )


def _get_app_branding(settings: Settings) -> dict[str, str]:
    """Get app branding values from settings or defaults."""
    base_url = settings.app_base_url.rstrip("/")
    # Fix: If app_base_url contains backend domain, use jobhuntin.com instead
    if (
        not base_url
        or "sorce" in base_url.lower()
        or "api." in base_url.lower()
        or base_url.startswith("http://localhost:8000")
    ):
        base_url = "https://jobhuntin.com"

    api_url = getattr(settings, "api_public_url", "").rstrip("/")
    domain = (
        base_url.replace("https://", "").replace("http://", "")
        if base_url
        else "jobhuntin.com"
    )

    return {
        "app_name": getattr(settings, "app_name", "JobHuntin"),
        "app_initials": getattr(settings, "app_initials", "JH"),
        "app_tagline": getattr(settings, "app_tagline", "Find your next job, faster"),
        "app_base_url": base_url or "https://jobhuntin.com",
        "api_public_url": api_url,
        "app_domain": domain,
        "support_email": getattr(settings, "support_email", "support@jobhuntin.com"),
    }


def _render_email_html(
    settings: Settings, action_link: str, return_to: str | None
) -> str:
    """Render HTML email with template variables."""
    expires_minutes = max(1, settings.magic_link_token_ttl_seconds // 60)
    branding = _get_app_branding(settings)

    # Simplify the link display to show the main domain, not the API URL
    # Extract just the domain part for cleaner display
    display_link = action_link
    if branding["app_base_url"] and branding["api_public_url"]:
        # Replace API URL with main domain for display purposes
        display_link = action_link.replace(
            branding["api_public_url"], branding["app_base_url"]
        )

    html = (
        MAGIC_LINK_TEMPLATE_HTML.replace("$action_link", action_link)
        .replace("$display_link", display_link)
        .replace("$expires_minutes", str(expires_minutes))
        .replace("$app_name", branding["app_name"])
        .replace("$app_domain", branding["app_domain"])
        .replace("$app_tagline", branding["app_tagline"])
    )
    return html


def _render_email_text(
    settings: Settings, action_link: str, return_to: str | None
) -> str:
    """Render plain text email with template variables."""
    expires_minutes = max(1, settings.magic_link_token_ttl_seconds // 60)
    branding = _get_app_branding(settings)

    # Simplify the link display to show the main domain
    display_link = action_link
    if branding["app_base_url"] and branding["api_public_url"]:
        display_link = action_link.replace(
            branding["api_public_url"], branding["app_base_url"]
        )

    destination_path = return_to or "/app/dashboard"
    destination_label = _get_destination_label(destination_path)

    text = (
        MAGIC_LINK_TEMPLATE_TXT.replace("$action_link", display_link)
        .replace("$destination", destination_label)
        .replace("$expires_minutes", str(expires_minutes))
        .replace("$app_name", branding["app_name"])
        .replace("$app_domain", branding["app_domain"])
        .replace("$app_tagline", branding["app_tagline"])
        .replace("$app_base_url", branding["app_base_url"])
    )
    return text


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
    """Send magic link email via Resend with retry logic."""
    if not settings.resend_api_key:
        # In production, email must be configured. In local/dev, log the link instead.
        if settings.env.value == "prod":
            raise HTTPException(
                status_code=500, detail="Email service is not configured"
            )
        # LOCAL DEV FALLBACK: print magic link to server logs so devs can click it
        logger.warning(
            "\n" + "=" * 70 + "\n"
            "[DEV] RESEND_API_KEY not set — magic link NOT sent by email.\n"
            "[DEV] Click this link to authenticate:\n"
            "[DEV] %s\n"
            "=" * 70,
            action_link,
        )
        return

    # Render email content using templates
    html = _render_email_html(settings, action_link, return_to)
    text_content = _render_email_text(settings, action_link, return_to)

    # Get destination for logging
    destination_path = return_to or "/app/dashboard"
    destination_label = _get_destination_label(destination_path)
    branding = _get_app_branding(settings)

    payload = {
        "from": settings.email_from,
        "to": [email],
        "subject": f"Sign in to {branding['app_name']}",
        "html": html,
        "text": text_content,
        "headers": {
            "List-Unsubscribe": f"<{branding['app_base_url']}/app/settings#notifications>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    logger.info(
        "[MAGIC_LINK] Sending email",
        extra={"email": _mask_email(email), "destination": destination_label},
    )

    # Retry logic with exponential backoff
    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            # MEDIUM: Use circuit breaker for email service calls
            from shared.circuit_breaker import get_email_breaker

            email_breaker = get_email_breaker()

            async def _send_email():
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(
                        "https://api.resend.com/emails", headers=headers, json=payload
                    )
                    return resp

            resp = await email_breaker.call(_send_email)

            if resp.status_code in (200, 201):
                # Success - log and return
                logger.info(
                    "[MAGIC_LINK] Email sent successfully",
                    extra={
                        "email": _mask_email(email),
                        "destination": destination_label,
                        "resend_response": resp.json() if resp.text else None,
                        "attempt": attempt + 1,
                    },
                )
                return

            # Check if error is retryable
            if resp.status_code >= 500 or resp.status_code == 429:
                # Server error or rate limit - retry
                if attempt < max_retries - 1:
                    delay = (
                        base_delay * (2**attempt) + (hash(email) % 100) / 100
                    )  # Add jitter
                    logger.warning(
                        f"[MAGIC_LINK] Resend returned {resp.status_code}, "
                        f"retrying in {delay:.2f}s",
                        extra={
                            "email": _mask_email(email),
                            "attempt": attempt + 1,
                            "status": resp.status_code,
                        },
                    )
                    await asyncio.sleep(delay)
                    continue

            # Non-retryable error or retries exhausted
            logger.error(
                "[MAGIC_LINK] Resend email failed",
                extra={
                    "email": _mask_email(email),
                    "status": resp.status_code,
                    "response": resp.text[:200],
                    "attempt": attempt + 1,
                },
            )
            raise HTTPException(
                status_code=502,
                detail=f"Failed to send magic link email (status {resp.status_code})",
            )

        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logger.warning(
                    f"[MAGIC_LINK] Resend timeout, retrying in {delay:.2f}s",
                    extra={"email": _mask_email(email), "attempt": attempt + 1},
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "[MAGIC_LINK] Resend timeout after all retries",
                    extra={"email": _mask_email(email)},
                )
                raise HTTPException(status_code=504, detail="Email service timeout")

        except Exception as e:
            logger.error(
                "[MAGIC_LINK] Unexpected error sending email",
                extra={"email": _mask_email(email), "error": str(e)},
            )
            raise HTTPException(
                status_code=502, detail="Failed to send magic link email"
            )


AUTH_COOKIE_NAME = "jobhuntin_auth"


@router.get("/verify-magic")
async def verify_magic_link(
    request: Request,
    token: str,
    return_to: str | None = None,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
) -> RedirectResponse:
    """S1: Verify magic link token, create user if new, set httpOnly cookie, redirect to app.
    User clicks link in email -> hits this endpoint -> [create user if new] -> set cookie -> redirect.
    """
    if not token or not settings.jwt_secret:
        redirect_url = (
            f"{settings.app_base_url.rstrip('/')}/login?error=auth_failed&hint=invalid"
        )
        if return_to:
            redirect_url += f"&returnTo={quote(return_to, safe='')}"
        return RedirectResponse(url=redirect_url, status_code=302)

    try:
        payload = pyjwt.decode(
            token, settings.jwt_secret, algorithms=["HS256"], audience="authenticated"
        )
        user_identifier = payload.get("sub")  # Can be user_id (UUID) or email
        email = payload.get("email")
        jti = payload.get("jti")
        is_new_user_flag = payload.get("new_user", False)
        ip_hash = payload.get("ip_hash")  # Optional IP binding

        if not user_identifier or not jti or not email:
            raise ValueError("Missing sub, email, or jti")
    except pyjwt.PyJWTError as exc:
        logger.warning("Verify-magic JWT invalid: %s", exc)
        hint = "expired" if "expired" in str(exc).lower() else "invalid"
        redirect_url = (
            f"{settings.app_base_url.rstrip('/')}/login?error=auth_failed&hint={hint}"
        )
        if return_to:
            redirect_url += f"&returnTo={quote(return_to, safe='')}"
        return RedirectResponse(url=redirect_url, status_code=302)

    # Verify IP binding if present
    if ip_hash:
        client_ip = get_client_ip(request)
        import hashlib

        current_ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
        if current_ip_hash != ip_hash:
            logger.warning(
                "[MAGIC_LINK] IP binding mismatch for jti: %s",
                jti,
                extra={"expected_ip_hash": ip_hash, "actual_ip_hash": current_ip_hash},
            )
            redirect_url = f"{settings.app_base_url.rstrip('/')}/login?error=auth_failed&hint=ip_mismatch"
            if return_to:
                redirect_url += f"&returnTo={quote(return_to, safe='')}"
            return RedirectResponse(url=redirect_url, status_code=302)

    if not await _mark_token_consumed(jti, settings):
        logger.warning("Verify-magic replay attempt for jti: %s", jti)
        redirect_url = (
            f"{settings.app_base_url.rstrip('/')}/login?error=auth_failed&hint=used"
        )
        if return_to:
            redirect_url += f"&returnTo={quote(return_to, safe='')}"
        return RedirectResponse(url=redirect_url, status_code=302)

    # Handle user creation for new users (user_identifier is email for new users)
    async with db.acquire() as conn:
        if is_new_user_flag or "@" in user_identifier:
            # This is a new user - create them now
            user_id, created = await _find_or_create_user_by_email(
                conn, email, settings
            )
            if created:
                logger.info(
                    "[MAGIC_LINK] New user created on verification: %s",
                    _mask_email(email),
                )
                incr("auth.magic_link.new_user_created", tags={})
            else:
                # User was created between request and verification
                logger.info(
                    "[MAGIC_LINK] User already existed on verification: %s",
                    _mask_email(email),
                )
        else:
            # Existing user - verify the user still exists
            user_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM public.users WHERE id = $1)",
                user_identifier,
            )
            if not user_exists:
                logger.warning(
                    "[MAGIC_LINK] User from token no longer exists: %s",
                    user_identifier,
                )
                redirect_url = f"{settings.app_base_url.rstrip('/')}/login?error=auth_failed&hint=invalid"
                if return_to:
                    redirect_url += f"&returnTo={quote(return_to, safe='')}"
                return RedirectResponse(url=redirect_url, status_code=302)
            user_id = user_identifier

    safe_return = _sanitize_return_to(return_to)
    dest = safe_return or "/app/dashboard"

    logger.info(
        "Successfully verified magic link for user ID: %s with jti: %s",
        user_id,
        jti,
    )

    # C4: Analytics Tracking - Track magic link verification (backend metric)
    incr(
        "auth.magic_link.verified",
        tags={
            "is_new_user": str(is_new_user_flag),
            "destination": dest,
            "email_domain": email.split("@")[-1] if "@" in email else "unknown",
        },
    )
    logger.info(
        "[MAGIC_LINK] Magic link verified successfully",
        extra={
            "user_id": user_id,
            "is_new_user": is_new_user_flag,
            "destination": dest,
            "email_domain": email.split("@")[-1] if "@" in email else "unknown",
        },
    )
    # Add magic_verified hint for frontend analytics (magic_link_verified event)
    sep = "&" if "?" in dest else "?"
    redirect_url = f"{settings.app_base_url.rstrip('/')}{dest}{sep}magic_verified=1"

    # ----------------------------------------------------------------
    # M2: Device Fingerprinting - Detect suspicious logins
    # Track device fingerprint and check for suspicious activity
    # ----------------------------------------------------------------
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")

    # Get tenant_id if available
    tenant_id = None
    async with db.acquire() as conn:
        tenant_row = await conn.fetchrow(
            "SELECT tenant_id FROM public.tenant_members WHERE user_id = $1 LIMIT 1",
            user_id,
        )
        if tenant_row and tenant_row.get("tenant_id"):
            tenant_id = (
                str(tenant_row["tenant_id"]) if tenant_row["tenant_id"] else None
            )

    # Create session with device fingerprinting
    session_manager = SessionManager(db)
    try:
        session_info = await session_manager.create_session(
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={"source": "magic_link", "is_new_user": is_new_user_flag},
        )

        # Check for suspicious activity
        suspicious_check = await session_manager.detect_suspicious_activity(
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except Exception as exc:
        # If session creation fails, log but continue with authentication
        # This allows login to work even if session tracking is broken
        logger.error(
            "[MAGIC_LINK] Session creation failed, continuing without session tracking: %s",
            exc,
            exc_info=True,
        )
        # Create a minimal session_info for the JWT
        import uuid as _uuid_mod

        session_info = type("SessionInfo", (), {"session_id": str(_uuid_mod.uuid4())})()
        suspicious_check = {"suspicious": False, "reasons": []}

    if suspicious_check["suspicious"]:
        logger.warning(
            "[M2] Suspicious login detected for user=%s",
            user_id,
            extra={
                "user_id": user_id,
                "reasons": suspicious_check["reasons"],
                "ip_address": client_ip,
                "user_agent": user_agent,
                "active_sessions": suspicious_check["active_sessions"],
                "known_ips": suspicious_check["known_ips"],
            },
        )
        incr(
            "auth.suspicious_login",
            tags={
                "reason": ",".join(suspicious_check["reasons"]),
                "is_new_user": str(is_new_user_flag),
            },
        )
        # Log security event but don't block login (user may be legitimate)
        # In production, consider sending alert to security team

    # ----------------------------------------------------------------
    # CRITICAL FIX: Issue a fresh SESSION JWT with sub=user_id (UUID).
    # The original magic-link JWT may have sub=email for new users.
    # All downstream API dependencies (get_current_user_id) expect sub
    # to be a UUID. The session cookie must use the resolved UUID.
    # Session TTL is 7 days (separate from the 1h magic link TTL).
    # Store session_id in JWT for session tracking.
    # ----------------------------------------------------------------
    SESSION_TTL_SECONDS = 7 * 24 * 3600  # 7 days
    import uuid as _uuid_mod
    from datetime import datetime as _dt
    from datetime import timedelta as _td

    import jwt as _jwt

    _now = _dt.now(timezone.utc)
    jti = str(_uuid_mod.uuid4())
    session_payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "jti": jti,
        "session_id": session_info.session_id,  # M2: Store session_id for tracking
        "iat": _now,
        "nbf": _now,
        "exp": _now + _td(seconds=SESSION_TTL_SECONDS),
    }
    session_token = _jwt.encode(session_payload, settings.jwt_secret, algorithm="HS256")

    # Store jti in session metadata so revoke can blacklist the JWT in Redis
    try:
        await session_manager.update_session_jti(session_info.session_id, jti)
    except Exception as e:
        logger.warning("Failed to store jti in session metadata: %s", e)

    # Revoke any previous session tokens for this user (optional - for session rotation)
    # This ensures only one active session per user at a time
    # Note: We don't have the old jti here, so this is a placeholder for future enhancement
    # For now, we'll revoke on explicit logout only

    is_prod = settings.env.value in ("prod", "staging")
    response = RedirectResponse(url=redirect_url, status_code=302)
    cookie_kwargs = dict(
        key=AUTH_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
        path="/",
    )
    # Add partitioned attribute for CHIPS (Cookies Having Independent Partitioned State)
    # This provides security benefits of SameSite=None while limiting cross-site tracking
    if is_prod:
        cookie_kwargs["partitioned"] = True  # type: ignore[arg-type]
    response.set_cookie(**cookie_kwargs)
    return response


@router.api_route("/logout", methods=["GET", "POST"])
async def logout(
    request: Request,
    settings: Settings = Depends(settings_dependency),
) -> RedirectResponse:
    """Clear auth cookie, revoke session token, and redirect to login.
    Supports GET for redirect-based logout.

    SECURITY: Revokes the session token to prevent replay attacks.
    """
    # Extract and revoke the session token before clearing the cookie
    jobhuntin_auth = request.cookies.get(AUTH_COOKIE_NAME)
    if jobhuntin_auth:
        try:
            import jwt as pyjwt

            payload = pyjwt.decode(
                jobhuntin_auth,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": False},  # Allow expired tokens for revocation
            )
            jti = payload.get("jti")
            if jti:
                await _revoke_session_token(jti, settings)
                logger.info("Session token revoked on logout: jti=%s", jti)
        except Exception as e:
            # Log but don't fail logout if revocation fails
            logger.warning("Failed to revoke session token on logout: %s", e)

    is_prod = settings.env.value in ("prod", "staging")
    redirect_url = f"{settings.app_base_url.rstrip('/')}/login"
    response = RedirectResponse(url=redirect_url, status_code=302)
    # SECURITY: Use same partitioned attribute as set_cookie for proper deletion
    cookie_kwargs: Dict[str, Any] = dict(
        key=AUTH_COOKIE_NAME,
        path="/",
        samesite="none" if is_prod else "lax",
        secure=is_prod,
    )
    if is_prod:
        cookie_kwargs["partitioned"] = True
    response.delete_cookie(**cookie_kwargs)
    return response


async def _verify_captcha(settings: Settings, token: str, client_ip: str) -> bool:
    """Verify a reCAPTCHA v3 token."""
    if not settings.recaptcha_secret_key:
        # In production, CAPTCHA is mandatory. Fail closed for security.
        if settings.env.value == "prod":
            logger.error(
                "RECAPTCHA_SECRET_KEY not set in production - rejecting request"
            )
            return False
        logger.warning("RECAPTCHA_SECRET_KEY not set, skipping verification.")
        return True

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": settings.recaptcha_secret_key,
                    "response": token,
                    "remoteip": client_ip,
                },
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success") and result.get("score", 0.0) >= 0.5:
                logger.info(
                    "reCAPTCHA verification successful with score: %s",
                    result.get("score"),
                )
                return True
            else:
                logger.warning(
                    "reCAPTCHA verification failed: %s",
                    result.get("error-codes", "No error codes"),
                )
                return False
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error while verifying reCAPTCHA token: %s", e)
            return False
        except Exception as e:
            logger.error(
                "An unexpected error occurred during reCAPTCHA verification: %s", e
            )
            return False


@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    request: Request,
    body: MagicLinkRequest,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
) -> MagicLinkResponse:
    """Generate a magic link and email it via Resend."""
    # S6: Global IP rate limit to prevent mass enumeration from a single IP
    client_ip = get_client_ip(request)

    # Check for disposable email domains
    if _is_disposable_email(body.email):
        logger.warning(
            "Disposable email blocked",
            extra={"email": _mask_email(body.email), "ip": client_ip},
        )
        incr("auth.magic_link.disposable_email_blocked", tags={})
        # Return generic error to avoid revealing our detection
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait before requesting another magic link.",
        )

    # H1: Rate Limiting Hardening - Enforce CAPTCHA for high-risk scenarios
    # P1: Tighter limits to reduce enumeration risk (20/hr per IP, CAPTCHA after 3)
    ip_limiter = get_rate_limiter(
        f"magic_link_ip:{client_ip}",
        max_calls=20,  # 20 per hour per IP (enumeration protection)
        window_seconds=3600,
    )
    ip_request_count = ip_limiter.current_count()
    requires_captcha = (
        ip_request_count >= 3
    )  # Require CAPTCHA after 3 requests from same IP

    # Also require CAPTCHA if email has hit 40% of its limit (earlier than 50%)
    email_limiter = _get_rate_limiter(settings, body.email)
    email_request_count = email_limiter.current_count()
    if email_request_count >= settings.magic_link_requests_per_hour * 0.4:
        requires_captcha = True

    if requires_captcha and not body.captcha_token:
        logger.warning(
            "CAPTCHA required but not provided",
            extra={
                "email": _mask_email(body.email),
                "ip": client_ip,
                "ip_count": ip_request_count,
                "email_count": email_request_count,
            },
        )
        raise HTTPException(
            status_code=400,
            detail="CAPTCHA verification required. Please complete the CAPTCHA and try again.",
        )

    if body.captcha_token:
        if not await _verify_captcha(settings, body.captcha_token, client_ip):
            raise HTTPException(status_code=400, detail="Invalid CAPTCHA token")

    # H1: Rate Limiting Hardening - Check IP rate limit
    if not await ip_limiter.acquire():
        retry_after = ip_limiter.next_available_in()
        logger.warning(
            "Magic link IP rate limit hit",
            extra={"retry_after": retry_after, "ip": client_ip},
        )
        incr("auth.magic_link.ip_rate_limited", tags={"ip": client_ip})
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait before requesting another magic link.",
            headers={"Retry-After": str(int(math.ceil(retry_after)))},
        )

    limiter = _get_rate_limiter(settings, body.email)
    if not await limiter.acquire():
        retry_after = limiter.next_available_in()
        logger.warning(
            "Magic link rate limit hit",
            extra={"email": body.email, "retry_after": retry_after},
        )
        incr(
            "auth.magic_link.rate_limited",
            tags={"email_domain": body.email.split("@")[-1]},
            value=1,
        )
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait before requesting another magic link.",
            headers={"Retry-After": str(int(math.ceil(retry_after)))},
        )

    redirect = _build_redirect_url(settings, body.return_to)
    action_link, _ = await _generate_magic_link(
        settings, body.email, redirect, db, body.return_to, client_ip
    )
    try:
        await _send_magic_link_email(settings, body.email, action_link, body.return_to)
    except HTTPException:
        incr(
            "auth.magic_link.failed",
            tags={"reason": "email_send", "email_domain": body.email.split("@")[-1]},
        )
        raise
    # C4: Analytics Tracking - Track magic link sent (backend metric)
    incr("auth.magic_link.sent", tags={"email_domain": body.email.split("@")[-1]})
    logger.info(
        "[MAGIC_LINK] Magic link sent successfully",
        extra={
            "email": _mask_email(body.email),
            "email_domain": body.email.split("@")[-1],
            "return_to": body.return_to,
        },
    )
    return MagicLinkResponse()


# ---------------------------------------------------------------------------
# Email Delivery Webhook (Resend)
# ---------------------------------------------------------------------------


class ResendWebhookPayload(BaseModel):
    type: str
    data: dict[str, Any]


@router.post("/webhooks/resend")
async def resend_webhook(
    request: Request,
    payload: ResendWebhookPayload,
    settings: Settings = Depends(settings_dependency),
) -> JSONResponse:
    """
    Handle Resend email delivery webhooks.

    Tracks: delivered, bounced, complained, opened, clicked
    Resend docs: https://resend.com/docs/dashboard/webhooks
    """
    # Verify webhook signature if configured (#1: Email delivery confirmation)
    # Resend signs webhooks with RESEND_WEBHOOK_SECRET when configured in dashboard
    webhook_secret = settings.resend_webhook_secret
    if webhook_secret:
        signature = request.headers.get("resend-signature")
        if not signature:
            logger.warning("Resend webhook missing signature")
            raise HTTPException(status_code=401, detail="Missing signature")

        # Verify the signature using HMAC-SHA256
        # Resend signs the request body with the webhook secret
        import hashlib
        import hmac

        # Get the raw request body for verification
        body = await request.body()
        expected_signature = hmac.new(
            webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Resend webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = payload.type
    data = payload.data

    # Extract email info (guard against empty list)
    to_val = data.get("to", ["unknown"])
    if isinstance(to_val, list):
        email_to = to_val[0] if to_val else "unknown"
    else:
        email_to = to_val if to_val else "unknown"
    email_id = data.get("email_id") or data.get("id", "unknown")

    # Log the event
    logger.info(
        f"Resend webhook: {event_type}",
        extra={
            "event_type": event_type,
            "email_id": email_id,
            "email": _mask_email(email_to),
        },
    )

    # C8: Email Delivery Tracking - Track all email events for delivery confirmation
    if event_type == "email.delivered":
        incr("email.delivered", tags={"provider": "resend", "email_type": "magic_link"})
        # Track delivery rate for magic links specifically
        if (
            "magic" in str(data.get("subject", "")).lower()
            or "sign in" in str(data.get("subject", "")).lower()
        ):
            incr(
                "auth.magic_link.delivered",
                tags={
                    "email_domain": email_to.split("@")[-1]
                    if "@" in email_to
                    else "unknown"
                },
            )
        logger.info(
            f"Email delivered: {_mask_email(email_to)}",
            extra={"email_id": email_id, "email_type": "magic_link"},
        )
    elif event_type == "email.bounced":
        incr("email.bounced", tags={"provider": "resend", "email_type": "magic_link"})
        if (
            "magic" in str(data.get("subject", "")).lower()
            or "sign in" in str(data.get("subject", "")).lower()
        ):
            incr(
                "auth.magic_link.bounced",
                tags={
                    "email_domain": email_to.split("@")[-1]
                    if "@" in email_to
                    else "unknown"
                },
            )
        logger.warning(
            f"Email bounced: {_mask_email(email_to)}",
            extra={"bounce_reason": data.get("bounce_type"), "email_id": email_id},
        )
    elif event_type == "email.complained":
        incr(
            "email.complained", tags={"provider": "resend", "email_type": "magic_link"}
        )
        logger.warning(
            f"Email complaint: {_mask_email(email_to)}", extra={"email_id": email_id}
        )
    elif event_type == "email.opened":
        incr("email.opened", tags={"provider": "resend", "email_type": "magic_link"})
        if (
            "magic" in str(data.get("subject", "")).lower()
            or "sign in" in str(data.get("subject", "")).lower()
        ):
            incr("auth.magic_link.opened", tags={})
    elif event_type == "email.clicked":
        incr("email.clicked", tags={"provider": "resend", "email_type": "magic_link"})
        if (
            "magic" in str(data.get("subject", "")).lower()
            or "sign in" in str(data.get("subject", "")).lower()
        ):
            incr("auth.magic_link.clicked", tags={})
    elif event_type == "email.sent":
        incr("email.sent", tags={"provider": "resend", "email_type": "magic_link"})
    elif event_type == "email.delivery_delayed":
        incr(
            "email.delivery_delayed",
            tags={"provider": "resend", "email_type": "magic_link"},
        )
        logger.warning(
            f"Email delivery delayed: {_mask_email(email_to)}",
            extra={"email_id": email_id, "delay_reason": data.get("reason")},
        )
    else:
        logger.info(f"Unknown Resend event type: {event_type}")

    return JSONResponse({"status": "ok"})
