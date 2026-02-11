"""
Growth sub-router — push tokens, referrals, email digest, onboarding.

Mounted via _mount_sub_routers() in api/main.py.
"""

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.domain.email_digest import run_weekly_digest
from backend.domain.notifications import (
    deactivate_push_token,
    register_push_token,
)
from backend.domain.referrals import (
    get_referral_stats,
    redeem_referral_code,
)
from backend.domain.repositories import db_transaction
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.api.growth")

router = APIRouter(tags=["growth"])

# ---------------------------------------------------------------------------
# Dependency stubs — injected by api/main.py at mount time
# ---------------------------------------------------------------------------

def _get_pool() -> asyncpg.Pool:
    return (_ for _ in ()).throw(  # type: ignore[return-value]
    NotImplementedError("Pool dependency not injected")
)

def _get_user_id() -> str:
    return (_ for _ in ()).throw(  # type: ignore[return-value]
    NotImplementedError("User ID dependency not injected")
)

def _get_admin_user_id() -> str:
    return (_ for _ in ()).throw(  # type: ignore[return-value]
    NotImplementedError("Admin user ID dependency not injected")
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class PushTokenRequest(BaseModel):
    token: str
    platform: str = "expo"  # expo, apns, fcm


class PushTokenResponse(BaseModel):
    status: str


class RedeemReferralRequest(BaseModel):
    referral_code: str


class ReferralStatsResponse(BaseModel):
    referral_code: str
    total_referrals: int
    bonus_credits: int
    share_url: str


class RedeemResponse(BaseModel):
    success: bool
    reward_amount: int = 0
    message: str


class OnboardingCompleteRequest(BaseModel):
    referral_code: str | None = None


class DigestTriggerResponse(BaseModel):
    sent: int
    skipped: int
    failed: int


# ---------------------------------------------------------------------------
# Push token endpoints
# ---------------------------------------------------------------------------

@router.post("/push/register", response_model=PushTokenResponse)
async def register_token(
    body: PushTokenRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> PushTokenResponse:
    """Register an Expo push token for the current user."""
    async with db.acquire() as conn:
        await register_push_token(conn, user_id, body.token, body.platform)
    incr("growth.push_token.registered")
    return PushTokenResponse(status="registered")


@router.post("/push/unregister", response_model=PushTokenResponse)
async def unregister_token(
    body: PushTokenRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> PushTokenResponse:
    """Deactivate a push token (e.g., on logout)."""
    async with db.acquire() as conn:
        await deactivate_push_token(conn, user_id, body.token)
    return PushTokenResponse(status="unregistered")


# ---------------------------------------------------------------------------
# Referral endpoints
# ---------------------------------------------------------------------------

@router.get("/referral", response_model=ReferralStatsResponse)
async def referral_stats(
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> ReferralStatsResponse:
    """Get the current user's referral code and stats."""
    async with db.acquire() as conn:
        stats = await get_referral_stats(conn, user_id)
    get_settings()
    share_url = f"https://jobhuntin.com/invite/{stats['referral_code']}"
    return ReferralStatsResponse(
        referral_code=stats["referral_code"],
        total_referrals=stats["total_referrals"],
        bonus_credits=stats["bonus_credits"],
        share_url=share_url,
    )


@router.post("/referral/redeem", response_model=RedeemResponse)
async def redeem_referral(
    body: RedeemReferralRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> RedeemResponse:
    """Redeem a referral code (called during onboarding)."""
    async with db_transaction(db) as conn:
        result = await redeem_referral_code(conn, user_id, body.referral_code)

    if not result:
        return RedeemResponse(success=False, message="Invalid or already used referral code.")

    # Notify referrer about the reward
    try:
        async with db.acquire() as conn:
            from backend.domain.notifications import notify_referral_reward
            await notify_referral_reward(conn, result["referrer_id"], result["reward_amount"])
    except Exception:
        pass  # Non-critical

    incr("growth.referral.redeemed")
    return RedeemResponse(
        success=True,
        reward_amount=result["reward_amount"],
        message=f"You and your friend each got {result['reward_amount']} bonus applications!",
    )


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

@router.post("/onboarding/complete")
async def onboarding_complete(
    body: OnboardingCompleteRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Mark onboarding as complete. Optionally redeem a referral code."""
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE public.users SET onboarding_completed_at = now() WHERE id = $1",
            user_id,
        )

    referral_result = None
    if body.referral_code:
        async with db_transaction(db) as conn:
            referral_result = await redeem_referral_code(conn, user_id, body.referral_code)

    incr("growth.onboarding.completed")
    return {
        "status": "completed",
        "referral_redeemed": referral_result is not None,
        "bonus_apps": referral_result["reward_amount"] if referral_result else 0,
    }


# ---------------------------------------------------------------------------
# Email digest (admin-triggered or cron)
# ---------------------------------------------------------------------------

@router.post("/admin/trigger-digest", response_model=DigestTriggerResponse)
async def trigger_digest(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> DigestTriggerResponse:
    """Trigger the weekly email digest for all active users. Admin only."""
    result = await run_weekly_digest(db)
    return DigestTriggerResponse(**result)
