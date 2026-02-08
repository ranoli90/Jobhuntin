"""
Auth endpoints for public web clients (magic links, etc.).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from shared.config import Settings, settings_dependency
from shared.logging_config import get_logger
from shared.metrics import RateLimiter, incr

logger = get_logger("sorce.api.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


_template_path = Path(__file__).resolve().parent.parent / "templates" / "emails" / "magic_link.html"
try:
    MAGIC_LINK_TEMPLATE = _template_path.read_text(encoding="utf-8")
except FileNotFoundError:
    MAGIC_LINK_TEMPLATE = """<p>Use this link to sign in: <a href=\"$action_link\">$action_link</a></p>"""
    logger.warning("Magic link template not found at %s; falling back to plain text HTML", _template_path)

_magic_link_limiters: dict[str, RateLimiter] = defaultdict(lambda: RateLimiter(max_calls=5, window_seconds=3600))


class MagicLinkRequest(BaseModel):
    email: EmailStr
    return_to: str | None = None


class MagicLinkResponse(BaseModel):
    status: str = "sent"


def _sanitize_return_to(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value.startswith("/"):
        return None
    if value.startswith("//"):
        return None
    return value


def _build_redirect_url(settings: Settings, return_to: str | None) -> str:
    base = settings.app_base_url.rstrip("/") or "http://localhost:5173"
    redirect = f"{base}/login"
    safe_return = _sanitize_return_to(return_to)
    if safe_return:
        redirect = f"{redirect}?returnTo={quote(safe_return, safe='')}"
    return redirect


async def _generate_magic_link(settings: Settings, email: str, redirect_to: str) -> str:
    if not settings.supabase_url or not settings.supabase_service_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured")

    payload = {
        "type": "magiclink",
        "email": email,
        "options": {
            "redirect_to": redirect_to,
            "expires_in": settings.magic_link_token_ttl_seconds,
        },
    }
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
    }
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/generate_link"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        logger.error("Supabase generate_link failed: %s - %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=502, detail="Failed to generate magic link")
    data: dict[str, Any] = resp.json()
    action_link = data.get("action_link") or data.get("email_action_link")
    if not action_link:
        logger.error("Supabase generate_link response missing action_link: %s", data)
        raise HTTPException(status_code=502, detail="Magic link unavailable")
    return action_link


def _render_email_html(settings: Settings, action_link: str, return_to: str | None) -> str:
    destination = return_to or "/app/dashboard"
    expires_minutes = max(1, settings.magic_link_token_ttl_seconds // 60)
    html = (
        MAGIC_LINK_TEMPLATE
        .replace("$action_link", action_link)
        .replace("$destination", destination)
        .replace("$expires_minutes", str(expires_minutes))
    )
    return html


def _get_rate_limiter(settings: Settings, email: str) -> RateLimiter:
    limiter = _magic_link_limiters.get(email)
    if limiter is None or limiter.max_calls != settings.magic_link_requests_per_hour:
        limiter = RateLimiter(
            max_calls=settings.magic_link_requests_per_hour,
            window_seconds=float(settings.magic_link_rate_limit_window_seconds),
        )
        _magic_link_limiters[email] = limiter
    return limiter


async def _send_magic_link_email(settings: Settings, email: str, action_link: str, return_to: str | None) -> None:
    if not settings.resend_api_key:
        raise HTTPException(status_code=500, detail="Email service is not configured")
    html = _render_email_html(settings, action_link, return_to)
    payload = {
        "from": settings.email_from,
        "to": [email],
        "subject": "Sign in to JobHuntin",
        "html": html,
        "text": f"Use this link to sign in: {action_link}",
    }
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post("https://api.resend.com/emails", headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        logger.error("Resend email failed: %s - %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=502, detail="Failed to send magic link email")
    logger.info("Magic link email queued", extra={"email": email, "return_to": return_to or "/app/dashboard"})
    incr("auth.magic_link.sent")


@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    body: MagicLinkRequest,
    settings: Settings = Depends(settings_dependency),
) -> MagicLinkResponse:
    """Generate a Supabase magic link and email it via Resend."""

    limiter = _get_rate_limiter(settings, body.email)
    if not limiter.allow():
        logger.warning("Magic link rate limit hit", extra={"email": body.email})
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait before requesting another magic link.",
        )

    redirect = _build_redirect_url(settings, body.return_to)
    action_link = await _generate_magic_link(settings, body.email, redirect)
    await _send_magic_link_email(settings, body.email, action_link, body.return_to)
    return MagicLinkResponse()
