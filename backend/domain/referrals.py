"""Referral program logic.

Each user gets a unique referral code. When a new user signs up with
a referral code, both the referrer and referee get bonus application
credits (default: 5 each).
"""

from __future__ import annotations

import hashlib
from typing import Any

import asyncpg

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.referrals")


def generate_referral_code(user_id: str) -> str:
    """Generate a short, unique referral code from user_id."""
    hash_hex = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    return f"SORCE-{hash_hex.upper()}"


async def get_or_create_referral_code(
    conn: asyncpg.Connection,
    user_id: str,
) -> str:
    """Get existing referral code or create a new one."""
    # Check if user already has a referral code stored
    code = await conn.fetchval(
        "SELECT referral_code FROM public.users WHERE id = $1",
        user_id,
    )
    if code:
        return str(code)

    code = generate_referral_code(user_id)

    # Store on user row
    await conn.execute(
        "UPDATE public.users SET referral_code = $2 WHERE id = $1",
        user_id,
        code,
    )

    # Create pending referral row (no referee yet)
    await conn.execute(
        """
        INSERT INTO public.referrals (referrer_id, referral_code, status)
        VALUES ($1, $2, 'pending')
        ON CONFLICT (referral_code) DO NOTHING
        """,
        user_id,
        code,
    )

    return code


async def redeem_referral_code(
    conn: asyncpg.Connection,
    referee_id: str,
    referral_code: str,
) -> dict[str, Any] | None:
    """Redeem a referral code for a new user.

    Returns the referral row if successful, None if code invalid or already used.
    """
    s = get_settings()
    reward = s.referral_reward_apps

    # Find the referral
    row = await conn.fetchrow(
        """
        SELECT id, referrer_id, status FROM public.referrals
        WHERE referral_code = $1 AND status = 'pending'
        """,
        referral_code,
    )
    if not row:
        return None

    referrer_id = str(row["referrer_id"])

    # Can't refer yourself
    if referrer_id == referee_id:
        return None

    # Update referral status
    await conn.execute(
        """
        UPDATE public.referrals
        SET referee_id = $2, status = 'rewarded', redeemed_at = now()
        WHERE id = $1
        """,
        row["id"],
        referee_id,
    )

    # Grant bonus credits to referrer's tenant
    await conn.execute(
        """
        UPDATE public.tenants
        SET bonus_app_credits = bonus_app_credits + $2
        WHERE id = (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = $1 AND role = 'OWNER' LIMIT 1
        )
        """,
        referrer_id,
        reward,
    )

    # Grant bonus credits to referee's tenant
    await conn.execute(
        """
        UPDATE public.tenants
        SET bonus_app_credits = bonus_app_credits + $2
        WHERE id = (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = $1 AND role = 'OWNER' LIMIT 1
        )
        """,
        referee_id,
        reward,
    )

    # Create a new pending referral for future use by the referrer
    new_code = generate_referral_code(referrer_id + referral_code)
    await conn.execute(
        """
        INSERT INTO public.referrals (referrer_id, referral_code, status)
        VALUES ($1, $2, 'pending')
        ON CONFLICT (referral_code) DO NOTHING
        """,
        referrer_id,
        new_code,
    )

    logger.info(
        "Referral redeemed: referrer=%s, referee=%s, code=%s, reward=%d",
        referrer_id,
        referee_id,
        referral_code,
        reward,
    )

    return {
        "referral_id": str(row["id"]),
        "referrer_id": referrer_id,
        "referee_id": referee_id,
        "reward_amount": reward,
    }


async def get_referral_stats(
    conn: asyncpg.Connection,
    user_id: str,
) -> dict[str, Any]:
    """Get referral stats for a user."""
    code = await get_or_create_referral_code(conn, user_id)

    total = await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.referrals WHERE referrer_id = $1 AND status = 'rewarded'",
        user_id,
    )

    bonus = await conn.fetchval(
        """
        SELECT COALESCE(t.bonus_app_credits, 0)
        FROM public.tenants t
        JOIN public.tenant_members tm ON tm.tenant_id = t.id
        WHERE tm.user_id = $1 AND tm.role = 'OWNER'
        LIMIT 1
        """,
        user_id,
    )

    return {
        "referral_code": code,
        "total_referrals": total or 0,
        "bonus_credits": bonus or 0,
    }
