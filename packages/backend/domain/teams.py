"""
Team management — invites, seat allocation, member management.

Handles the lifecycle of team invites and per-seat Stripe quantity updates.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

import asyncpg
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.teams")


# ---------------------------------------------------------------------------
# Invite token generation
# ---------------------------------------------------------------------------

def generate_invite_token() -> str:
    """Generate a URL-safe invite token."""
    return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# Invite management
# ---------------------------------------------------------------------------

async def create_invite(
    conn: asyncpg.Connection,
    tenant_id: str,
    invited_by: str,
    email: str,
    role: str = "MEMBER",
) -> dict[str, Any]:
    """Create a team invite. Returns the invite row."""
    # Check seat capacity
    tenant = await conn.fetchrow(
        "SELECT seat_count, max_seats, plan FROM public.tenants WHERE id = $1",
        tenant_id,
    )
    if not tenant:
        raise ValueError("Tenant not found")
    if tenant["plan"] not in ("TEAM", "ENTERPRISE"):
        raise ValueError("Team invites require TEAM or ENTERPRISE plan")

    # Count existing pending invites + current members
    member_count = await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.tenant_members WHERE tenant_id = $1",
        tenant_id,
    )
    pending_count = await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.team_invites WHERE tenant_id = $1 AND status = 'pending'",
        tenant_id,
    )
    if (member_count + pending_count) >= tenant["max_seats"]:
        raise ValueError(
            f"Seat limit reached ({tenant['max_seats']}). "
            "Add more seats before inviting."
        )

    # Check for duplicate pending invite
    existing = await conn.fetchval(
        """SELECT id FROM public.team_invites
           WHERE tenant_id = $1 AND email = $2 AND status = 'pending'""",
        tenant_id, email,
    )
    if existing:
        raise ValueError(f"Pending invite already exists for {email}")

    token = generate_invite_token()
    row = await conn.fetchrow(
        """
        INSERT INTO public.team_invites (tenant_id, invited_by, email, role, token)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, tenant_id, email, role, token, status, created_at, expires_at
        """,
        tenant_id, invited_by, email, role, token,
    )
    return dict(row)


async def accept_invite(
    conn: asyncpg.Connection,
    token: str,
    user_id: str,
) -> dict[str, Any]:
    """Accept a team invite by token. Adds user as tenant member."""
    invite = await conn.fetchrow(
        """
        SELECT id, tenant_id, email, role, status, expires_at
        FROM public.team_invites WHERE token = $1
        """,
        token,
    )
    if not invite:
        raise ValueError("Invalid invite token")
    if invite["status"] != "pending":
        raise ValueError(f"Invite is {invite['status']}")
    if invite["expires_at"] < datetime.now(UTC):
        await conn.execute(
            "UPDATE public.team_invites SET status = 'expired' WHERE id = $1",
            invite["id"],
        )
        raise ValueError("Invite has expired")

    tenant_id = str(invite["tenant_id"])
    role = invite["role"]

    # Lock tenant row to prevent race condition on seat count
    tenant = await conn.fetchrow(
        "SELECT seat_count, max_seats FROM public.tenants WHERE id = $1 FOR UPDATE",
        tenant_id,
    )

    # Check not already a member
    already = await conn.fetchval(
        "SELECT COUNT(*) FROM public.tenant_members WHERE tenant_id = $1 AND user_id = $2",
        tenant_id, user_id,
    )
    if already and already > 0:
        # Just mark invite accepted
        await conn.execute(
            "UPDATE public.team_invites SET status = 'accepted', accepted_at = now() WHERE id = $1",
            invite["id"],
        )
        return {"tenant_id": tenant_id, "already_member": True}

    # Add as member
    await conn.execute(
        """
        INSERT INTO public.tenant_members (tenant_id, user_id, role)
        VALUES ($1, $2, $3)
        ON CONFLICT (tenant_id, user_id) DO UPDATE SET role = $3
        """,
        tenant_id, user_id, role,
    )

    # Update seat count
    new_seat_count_row = await conn.fetchrow(
        "UPDATE public.tenants SET seat_count = seat_count + 1 WHERE id = $1 RETURNING seat_count",
        tenant_id,
    )
    new_seat_count = new_seat_count_row["seat_count"] if new_seat_count_row else None

    # Sync seat count with Stripe billing
    try:
        if new_seat_count is not None:
            await update_stripe_seat_quantity(conn, tenant_id, new_seat_count)
    except Exception as e:
        logger.warning("Failed to sync seat count with Stripe: %s", e)

    # Mark invite accepted
    await conn.execute(
        "UPDATE public.team_invites SET status = 'accepted', accepted_at = now() WHERE id = $1",
        invite["id"],
    )

    logger.info("User %s joined tenant %s as %s via invite", user_id, tenant_id, role)
    return {"tenant_id": tenant_id, "role": role, "already_member": False}


async def revoke_invite(
    conn: asyncpg.Connection,
    invite_id: str,
    tenant_id: str,
) -> bool:
    """Revoke a pending invite."""
    result = await conn.execute(
        """
        UPDATE public.team_invites SET status = 'revoked'
        WHERE id = $1 AND tenant_id = $2 AND status = 'pending'
        """,
        invite_id, tenant_id,
    )
    return "UPDATE 1" in result


async def list_invites(
    conn: asyncpg.Connection,
    tenant_id: str,
) -> list[dict[str, Any]]:
    """List all invites for a tenant."""
    rows = await conn.fetch(
        """
        SELECT id, email, role, status, created_at, expires_at, accepted_at
        FROM public.team_invites
        WHERE tenant_id = $1
        ORDER BY created_at DESC
        """,
        tenant_id,
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------

async def list_members(
    conn: asyncpg.Connection,
    tenant_id: str,
) -> list[dict[str, Any]]:
    """List all members of a tenant with usage stats."""
    rows = await conn.fetch(
        """
        SELECT
            tm.user_id,
            tm.role,
            u.email,
            u.raw_user_meta_data->>'full_name' AS name,
            (SELECT COUNT(*)::int FROM public.applications a
             WHERE a.user_id = tm.user_id
               AND a.created_at >= date_trunc('month', now())
            ) AS apps_this_month,
            (SELECT COUNT(*)::int FROM public.applications a
             WHERE a.user_id = tm.user_id
            ) AS apps_total
        FROM public.tenant_members tm
        JOIN auth.users u ON u.id = tm.user_id
        WHERE tm.tenant_id = $1
        ORDER BY tm.role DESC, u.email
        """,
        tenant_id,
    )
    return [dict(r) for r in rows]


async def remove_member(
    conn: asyncpg.Connection,
    tenant_id: str,
    user_id: str,
) -> bool:
    """Remove a member from a tenant (cannot remove OWNER)."""
    role = await conn.fetchval(
        "SELECT role FROM public.tenant_members WHERE tenant_id = $1 AND user_id = $2",
        tenant_id, user_id,
    )
    if not role:
        return False
    if role == "OWNER":
        raise ValueError("Cannot remove the tenant owner")

    await conn.execute(
        "DELETE FROM public.tenant_members WHERE tenant_id = $1 AND user_id = $2",
        tenant_id, user_id,
    )
    new_seat_count_row = await conn.fetchrow(
        "UPDATE public.tenants SET seat_count = GREATEST(seat_count - 1, 1) WHERE id = $1 RETURNING seat_count",
        tenant_id,
    )
    new_seat_count = new_seat_count_row["seat_count"] if new_seat_count_row else None

    # Sync seat count with Stripe billing
    try:
        if new_seat_count is not None:
            await update_stripe_seat_quantity(conn, tenant_id, new_seat_count)
    except Exception as e:
        logger.warning("Failed to sync seat count with Stripe: %s", e)

    return True


async def update_member_role(
    conn: asyncpg.Connection,
    tenant_id: str,
    user_id: str,
    new_role: str,
) -> bool:
    """Update a member's role."""
    if new_role not in ("MEMBER", "ADMIN"):
        raise ValueError("Invalid role; must be MEMBER or ADMIN")
    result = await conn.execute(
        "UPDATE public.tenant_members SET role = $3 WHERE tenant_id = $1 AND user_id = $2",
        tenant_id, user_id, new_role,
    )
    return "UPDATE 1" in result


# ---------------------------------------------------------------------------
# Seat management (Stripe integration)
# ---------------------------------------------------------------------------

async def update_stripe_seat_quantity(
    conn: asyncpg.Connection,
    tenant_id: str,
    new_seat_count: int,
) -> None:
    """
    Update Stripe subscription quantity for per-seat billing.
    Also updates tenants.max_seats.
    """
    s = get_settings()
    row = await conn.fetchrow(
        """SELECT stripe_subscription_item_id, provider_customer_id
           FROM public.billing_customers WHERE tenant_id = $1""",
        tenant_id,
    )
    if not row or not row["stripe_subscription_item_id"]:
        logger.warning("No seat subscription item for tenant %s", tenant_id)
        return

    import stripe
    stripe.api_key = s.stripe_secret_key

    # Calculate additional seats beyond included
    additional = max(0, new_seat_count - s.team_included_seats)

    stripe.SubscriptionItem.modify(
        row["stripe_subscription_item_id"],
        quantity=additional,
        proration_behavior="create_prorations",
    )

    await conn.execute(
        "UPDATE public.tenants SET max_seats = $2 WHERE id = $1",
        tenant_id, new_seat_count,
    )
    logger.info("Updated seats for tenant %s: %d (additional billable: %d)",
                tenant_id, new_seat_count, additional)


async def get_team_overview(
    conn: asyncpg.Connection,
    tenant_id: str,
) -> dict[str, Any]:
    """Get team overview stats."""
    tenant = await conn.fetchrow(
        """SELECT id, name, team_name, plan, seat_count, max_seats,
                  bonus_app_credits, created_at
           FROM public.tenants WHERE id = $1""",
        tenant_id,
    )
    if not tenant:
        return {}

    members = await list_members(conn, tenant_id)
    pending_invites = await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.team_invites WHERE tenant_id = $1 AND status = 'pending'",
        tenant_id,
    )

    total_apps_month = sum(m.get("apps_this_month", 0) for m in members)
    total_apps_all = sum(m.get("apps_total", 0) for m in members)

    return {
        "tenant": dict(tenant),
        "members": members,
        "member_count": len(members),
        "pending_invites": pending_invites or 0,
        "total_apps_this_month": total_apps_month,
        "total_apps_all_time": total_apps_all,
    }
