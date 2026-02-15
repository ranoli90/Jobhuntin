"""
Push notification sender — uses Expo Push Notifications API.

Handles:
  - Sending push notifications to individual users
  - Batch sending to multiple tokens
  - Logging all sent notifications to notification_log
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.notifications")

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

async def register_push_token(
    conn: asyncpg.Connection,
    user_id: str,
    token: str,
    platform: str = "expo",
    tenant_id: str | None = None,
) -> None:
    """Register or reactivate a push token for a user."""
    await conn.execute(
        """
        INSERT INTO public.push_tokens (user_id, token, platform, tenant_id, is_active)
        VALUES ($1, $2, $3, $4, true)
        ON CONFLICT (user_id, token) DO UPDATE
            SET is_active = true, platform = $3, updated_at = now()
        """,
        user_id, token, platform, tenant_id,
    )


async def deactivate_push_token(
    conn: asyncpg.Connection,
    user_id: str,
    token: str,
) -> None:
    """Deactivate a push token (e.g., on logout)."""
    await conn.execute(
        """
        UPDATE public.push_tokens SET is_active = false, updated_at = now()
        WHERE user_id = $1 AND token = $2
        """,
        user_id, token,
    )


async def get_active_tokens(
    conn: asyncpg.Connection,
    user_id: str,
) -> list[str]:
    """Get all active push tokens for a user."""
    rows = await conn.fetch(
        "SELECT token FROM public.push_tokens WHERE user_id = $1 AND is_active = true",
        user_id,
    )
    return [r["token"] for r in rows]


# ---------------------------------------------------------------------------
# Send push notification
# ---------------------------------------------------------------------------

async def send_push_to_user(
    conn: asyncpg.Connection,
    user_id: str,
    title: str,
    body: str,
    notification_type: str,
    data: dict[str, Any] | None = None,
    tenant_id: str | None = None,
) -> int:
    """
    Send a push notification to all active tokens for a user.

    Returns the number of tokens sent to.
    """
    tokens = await get_active_tokens(conn, user_id)
    if not tokens:
        return 0

    s = get_settings()
    sent = await _send_expo_push(
        tokens=tokens,
        title=title,
        body=body,
        data=data or {},
        access_token=s.expo_push_access_token,
    )

    # Log the notification
    await conn.execute(
        """
        INSERT INTO public.notification_log
            (user_id, tenant_id, channel, notification_type, title, body, metadata)
        VALUES ($1, $2, 'push', $3, $4, $5, $6::jsonb)
        """,
        user_id, tenant_id, notification_type, title, body,
        json.dumps(data or {}),
    )

    return sent


async def _send_expo_push(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, Any],
    access_token: str = "",
) -> int:
    """Send push via Expo Push API. Returns count of messages sent."""
    import httpx

    messages = [
        {
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "data": data,
        }
        for token in tokens
    ]

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                EXPO_PUSH_URL,
                json=messages,
                headers=headers,
            )
            if resp.status_code == 200:
                result = resp.json()
                # Check for individual ticket errors
                tickets = result.get("data", [])
                ok_count = sum(1 for t in tickets if t.get("status") == "ok")
                err_count = len(tickets) - ok_count
                if err_count:
                    logger.warning("Push send: %d ok, %d errors", ok_count, err_count)
                return ok_count
            else:
                logger.error("Expo push API error: %d %s", resp.status_code, resp.text[:200])
                return 0
    except Exception as exc:
        logger.error("Expo push send failed: %s", exc)
        return 0


# ---------------------------------------------------------------------------
# Pre-built notification templates
# ---------------------------------------------------------------------------

async def notify_application_submitted(
    conn: asyncpg.Connection,
    user_id: str,
    company: str,
    job_title: str,
    application_id: str,
    tenant_id: str | None = None,
) -> int:
    """Notify user that their application was submitted successfully."""
    return await send_push_to_user(
        conn, user_id,
        title="Application Submitted!",
        body=f"Your application to {company} for {job_title} was submitted.",
        notification_type="application_submitted",
        data={"application_id": application_id, "screen": "application_detail"},
        tenant_id=tenant_id,
    )


async def notify_hold_questions(
    conn: asyncpg.Connection,
    user_id: str,
    company: str,
    question_count: int,
    application_id: str,
    tenant_id: str | None = None,
) -> int:
    """Notify user that the agent needs their input."""
    return await send_push_to_user(
        conn, user_id,
        title="Input Needed",
        body=f"Your {company} application has {question_count} question(s) that need your answer.",
        notification_type="hold_questions",
        data={"application_id": application_id, "screen": "hold_questions"},
        tenant_id=tenant_id,
    )


async def notify_referral_reward(
    conn: asyncpg.Connection,
    user_id: str,
    bonus_apps: int,
    tenant_id: str | None = None,
) -> int:
    """Notify user they received referral bonus credits."""
    return await send_push_to_user(
        conn, user_id,
        title="Referral Reward!",
        body=f"You earned {bonus_apps} bonus applications from a referral!",
        notification_type="referral_reward",
        data={"screen": "referral"},
        tenant_id=tenant_id,
    )
