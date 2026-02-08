"""
Auth endpoints for public web clients (magic links, etc.).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from shared.config import Settings, settings_dependency
from shared.logging_config import get_logger

logger = get_logger("sorce.api.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


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


def _render_email_html(action_link: str, return_to: str | None) -> str:
    destination = return_to or "/app/dashboard"
    return f"""
    <table style="width:100%;background:#FFF8F1;padding:32px 0;font-family:'Baloo 2',Segoe UI,sans-serif;">
      <tr>
        <td align="center">
          <table style="max-width:520px;width:100%;background:#ffffff;border-radius:28px;padding:40px;box-shadow:0 25px 70px rgba(16,24,40,0.12);">
            <tr>
              <td style="text-align:center;">
                <div style="display:inline-flex;align-items:center;gap:12px;margin-bottom:24px;">
                  <span style="width:44px;height:44px;border-radius:14px;background:#FF9C6B;color:#fff;font-weight:700;display:grid;place-items:center;font-size:18px;">Sk</span>
                  <span style="font-size:28px;color:#101828;font-weight:700;">Skedaddle</span>
                </div>
                <h1 style="font-size:26px;color:#101828;margin:0 0 12px;">Your magic link is ready ✨</h1>
                <p style="font-size:16px;color:#475467;margin:0 0 32px;">Tap the button to hop back into your Skedaddle workspace.<br />We'll take you to <strong>{destination}</strong>.</p>
                <a href="{action_link}" style="display:inline-block;background:#17BEBB;color:#fff;font-weight:600;padding:14px 32px;border-radius:999px;text-decoration:none;box-shadow:0 18px 40px rgba(23,190,187,0.35);">Open Skedaddle</a>
                <p style="font-size:14px;color:#98A2B3;margin:32px 0 8px;">Link expires in 1 hour. Not you? Ignore this email.</p>
                <p style="font-size:13px;color:#98A2B3;margin:0;">Or copy & paste this link:<br /><a href="{action_link}" style="color:#17BEBB;word-break:break-all;">{action_link}</a></p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """


async def _send_magic_link_email(settings: Settings, email: str, action_link: str, return_to: str | None) -> None:
    if not settings.resend_api_key:
        raise HTTPException(status_code=500, detail="Email service is not configured")
    html = _render_email_html(action_link, return_to)
    payload = {
        "from": settings.email_from,
        "to": [email],
        "subject": "Sign in to Skedaddle",
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


@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    body: MagicLinkRequest,
    settings: Settings = Depends(settings_dependency),
) -> MagicLinkResponse:
    """Generate a Supabase magic link and email it via Resend."""

    redirect = _build_redirect_url(settings, body.return_to)
    action_link = await _generate_magic_link(settings, body.email, redirect)
    await _send_magic_link_email(settings, body.email, action_link, body.return_to)
    return MagicLinkResponse()
