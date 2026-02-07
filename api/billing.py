"""
Billing API — Stripe integration for M1 closed beta.

Provides:
  - POST /billing/webhook         – Stripe webhook (signature-verified)
  - POST /billing/checkout        – Create Stripe Checkout Session for FREE→PRO
  - POST /billing/portal          – Create Stripe Customer Portal session
  - GET  /billing/status          – Current billing status for the tenant
  - GET  /billing/usage           – Current quota usage for the tenant

Stripe flow:
  1. User taps "Upgrade to PRO" in mobile app.
  2. App calls POST /billing/checkout → receives Stripe Checkout URL.
  3. User completes payment in browser.
  4. Stripe sends webhook → we update billing_customers + tenants.plan.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.domain.repositories import TenantRepo, db_transaction
from backend.domain.plans import plan_config_for
from backend.domain.tenant import TenantContext, TenantScopeError, require_role
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.billing")

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Stripe SDK (lazy import so app starts even without stripe installed)
# ---------------------------------------------------------------------------

def _get_stripe():
    """Lazy-import stripe and configure API key."""
    import stripe
    s = get_settings()
    stripe.api_key = s.stripe_secret_key
    return stripe


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class CheckoutRequest(BaseModel):
    success_url: str = "sorce://billing/success"
    cancel_url: str = "sorce://billing/cancel"


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    portal_url: str


class BillingStatusResponse(BaseModel):
    tenant_id: str
    plan: str
    provider: str | None = None
    provider_customer_id: str | None = None
    subscription_status: str = "none"
    current_period_end: str | None = None


class UsageResponse(BaseModel):
    tenant_id: str
    plan: str
    monthly_limit: int
    monthly_used: int
    monthly_remaining: int
    concurrent_limit: int
    concurrent_used: int
    percentage_used: float


# ---------------------------------------------------------------------------
# Dependency stubs (injected by main app at mount time)
# ---------------------------------------------------------------------------

def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    raise NotImplementedError("Tenant context dependency not injected")


# ---------------------------------------------------------------------------
# Stripe event → plan mapping
# ---------------------------------------------------------------------------

SUBSCRIPTION_STATUS_MAP: dict[str, str] = {
    "active": "PRO",
    "trialing": "PRO",
    "past_due": "PRO",
    "canceled": "FREE",
    "unpaid": "FREE",
    "incomplete_expired": "FREE",
}

# Plans that map to TEAM based on the price ID (resolved at webhook time)
_TEAM_PLAN_OVERRIDE: str = "TEAM"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _ensure_stripe_customer(
    conn: asyncpg.Connection,
    tenant_id: str,
    user_email: str | None = None,
) -> str:
    """Get or create a Stripe customer for this tenant. Returns customer ID."""
    row = await conn.fetchrow(
        "SELECT provider_customer_id FROM public.billing_customers WHERE tenant_id = $1",
        tenant_id,
    )
    if row and row["provider_customer_id"]:
        return row["provider_customer_id"]

    stripe = _get_stripe()
    customer = stripe.Customer.create(
        metadata={"tenant_id": tenant_id},
        email=user_email,
    )

    await conn.execute(
        """
        INSERT INTO public.billing_customers (tenant_id, provider, provider_customer_id)
        VALUES ($1, 'STRIPE', $2)
        ON CONFLICT (tenant_id) DO UPDATE
            SET provider_customer_id = $2, updated_at = now()
        """,
        tenant_id,
        customer.id,
    )
    return customer.id


async def _update_subscription_state(
    conn: asyncpg.Connection,
    stripe_customer_id: str,
    subscription_status: str,
    subscription_id: str | None = None,
    current_period_end: datetime | None = None,
) -> None:
    """Update billing_customers and tenants.plan based on subscription state."""
    new_plan = SUBSCRIPTION_STATUS_MAP.get(subscription_status, "FREE")

    await conn.execute(
        """
        UPDATE public.billing_customers
        SET current_subscription_status = $2,
            current_subscription_id = COALESCE($3, current_subscription_id),
            current_period_end = COALESCE($4, current_period_end),
            updated_at = now()
        WHERE provider_customer_id = $1
        """,
        stripe_customer_id,
        subscription_status,
        subscription_id,
        current_period_end,
    )

    await conn.execute(
        """
        UPDATE public.tenants
        SET plan = $2::public.tenant_plan, updated_at = now()
        WHERE id = (
            SELECT tenant_id FROM public.billing_customers
            WHERE provider_customer_id = $1
        )
        """,
        stripe_customer_id,
        new_plan,
    )
    logger.info("Updated tenant plan to %s for Stripe customer %s", new_plan, stripe_customer_id)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/webhook")
async def billing_webhook(
    request: Request,
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """
    Stripe webhook handler with signature verification.

    Handles:
      - customer.subscription.created / updated / deleted
      - invoice.payment_failed
      - checkout.session.completed
    """
    incr("billing.webhook.received")

    raw_body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    s = get_settings()
    stripe = _get_stripe()

    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            raw_body, sig_header, s.stripe_webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as exc:
        logger.warning("Webhook parse error: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]
    event_id = event["id"]
    data_object = event["data"]["object"]

    logger.info("Stripe webhook: type=%s id=%s", event_type, event_id)

    async with db_transaction(db) as conn:
        if event_type in (
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ):
            customer_id = data_object.get("customer", "")
            status = data_object.get("status", "canceled")
            sub_id = data_object.get("id")
            period_end_ts = data_object.get("current_period_end")
            period_end = (
                datetime.fromtimestamp(period_end_ts, tz=timezone.utc)
                if period_end_ts else None
            )
            await _update_subscription_state(
                conn, customer_id, status, sub_id, period_end,
            )

        elif event_type == "invoice.payment_failed":
            customer_id = data_object.get("customer", "")
            await _update_subscription_state(conn, customer_id, "past_due")

        elif event_type == "checkout.session.completed":
            customer_id = data_object.get("customer", "")
            sub_id = data_object.get("subscription")
            metadata = data_object.get("metadata", {})

            if sub_id:
                await _update_subscription_state(
                    conn, customer_id, "active", sub_id,
                )

            # M3: Handle TEAM plan checkout metadata
            if metadata.get("plan") == "TEAM":
                seats = int(metadata.get("seats", "3"))
                team_name = metadata.get("team_name", "")

                # Override plan to TEAM (default map sets PRO for active)
                await conn.execute(
                    """
                    UPDATE public.tenants
                    SET plan = 'TEAM'::public.tenant_plan,
                        max_seats = $2,
                        team_name = NULLIF($3, ''),
                        updated_at = now()
                    WHERE id = (
                        SELECT tenant_id FROM public.billing_customers
                        WHERE provider_customer_id = $1
                    )
                    """,
                    customer_id, seats, team_name,
                )

                # Store the seat subscription_item_id for future quantity updates
                if sub_id:
                    try:
                        stripe = _get_stripe()
                        s = get_settings()
                        subscription = stripe.Subscription.retrieve(sub_id)
                        for item in subscription.get("items", {}).get("data", []):
                            if item.get("price", {}).get("id") == s.stripe_team_seat_price_id:
                                await conn.execute(
                                    """
                                    UPDATE public.billing_customers
                                    SET stripe_subscription_item_id = $2
                                    WHERE provider_customer_id = $1
                                    """,
                                    customer_id, item["id"],
                                )
                                break
                    except Exception as seat_exc:
                        logger.warning("Failed to store seat subscription item: %s", seat_exc)

                logger.info("TEAM checkout completed: customer=%s seats=%d", customer_id, seats)

            # M4: Handle ENTERPRISE plan checkout metadata
            elif metadata.get("plan") == "ENTERPRISE":
                seats = int(metadata.get("seats", "10"))
                team_name = metadata.get("team_name", "")
                sla_tier = metadata.get("sla_tier", "standard")

                tenant_row = await conn.fetchrow(
                    """
                    UPDATE public.tenants
                    SET plan = 'ENTERPRISE'::public.tenant_plan,
                        max_seats = $2,
                        team_name = NULLIF($3, ''),
                        updated_at = now()
                    WHERE id = (
                        SELECT tenant_id FROM public.billing_customers
                        WHERE provider_customer_id = $1
                    )
                    RETURNING id
                    """,
                    customer_id, seats, team_name,
                )

                if tenant_row:
                    t_id = str(tenant_row["id"])
                    # Create enterprise_settings row
                    await conn.execute(
                        """
                        INSERT INTO public.enterprise_settings (tenant_id, sla_tier)
                        VALUES ($1, $2)
                        ON CONFLICT (tenant_id) DO UPDATE SET sla_tier = $2, updated_at = now()
                        """,
                        t_id, sla_tier,
                    )

                    # Audit log
                    from backend.domain.audit import record_audit_event
                    await record_audit_event(
                        conn, t_id, None,
                        action="billing.enterprise_activated",
                        resource="tenant",
                        resource_id=t_id,
                        details={"seats": seats, "sla_tier": sla_tier},
                    )

                logger.info("ENTERPRISE checkout completed: customer=%s seats=%d sla=%s", customer_id, seats, sla_tier)

    incr("billing.webhook.processed", tags={"event_type": event_type})
    return {"status": "received", "event_id": event_id}


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> CheckoutResponse:
    """
    Create a Stripe Checkout Session for upgrading FREE → PRO.

    Returns a checkout URL the mobile app opens in a WebView or browser.
    """
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can manage billing")

    if ctx.plan == "PRO":
        raise HTTPException(status_code=409, detail="Already on PRO plan")

    s = get_settings()
    if not s.stripe_secret_key or not s.stripe_pro_price_id:
        raise HTTPException(status_code=503, detail="Billing not configured")

    stripe = _get_stripe()

    async with db.acquire() as conn:
        customer_id = await _ensure_stripe_customer(conn, ctx.tenant_id)

    checkout_params: dict[str, Any] = {
        "customer": customer_id,
        "mode": "subscription",
        "line_items": [{"price": s.stripe_pro_price_id, "quantity": 1}],
        "success_url": body.success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": body.cancel_url,
        "metadata": {"tenant_id": ctx.tenant_id},
    }
    if s.stripe_free_trial_days > 0:
        checkout_params["subscription_data"] = {
            "trial_period_days": s.stripe_free_trial_days,
        }

    session = stripe.checkout.Session.create(**checkout_params)

    incr("billing.checkout.created", tags={"tenant_id": ctx.tenant_id})
    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> PortalResponse:
    """Create a Stripe Customer Portal session for managing subscription."""
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can manage billing")

    stripe = _get_stripe()

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT provider_customer_id FROM public.billing_customers WHERE tenant_id = $1",
            ctx.tenant_id,
        )
    if not row or not row["provider_customer_id"]:
        raise HTTPException(status_code=404, detail="No billing account found. Please upgrade first.")

    portal = stripe.billing_portal.Session.create(
        customer=row["provider_customer_id"],
        return_url="sorce://billing/portal-return",
    )
    return PortalResponse(portal_url=portal.url)


@router.get("/status", response_model=BillingStatusResponse)
async def billing_status(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> BillingStatusResponse:
    """Return current billing status for the tenant."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM public.billing_customers WHERE tenant_id = $1",
            ctx.tenant_id,
        )

    if row is None:
        return BillingStatusResponse(
            tenant_id=ctx.tenant_id,
            plan=ctx.plan,
        )

    return BillingStatusResponse(
        tenant_id=ctx.tenant_id,
        plan=ctx.plan,
        provider=row["provider"],
        provider_customer_id=row["provider_customer_id"],
        subscription_status=row["current_subscription_status"],
        current_period_end=row["current_period_end"].isoformat() if row["current_period_end"] else None,
    )


@router.get("/usage", response_model=UsageResponse)
async def billing_usage(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> UsageResponse:
    """Return current quota usage for the tenant (used by mobile upgrade prompts)."""
    config = plan_config_for(ctx.plan)

    async with db.acquire() as conn:
        monthly_used = await TenantRepo.count_monthly_applications(conn, ctx.tenant_id)
        concurrent_used = await TenantRepo.count_concurrent_processing(conn, ctx.tenant_id)

    monthly_limit = config["max_monthly_applications"]
    return UsageResponse(
        tenant_id=ctx.tenant_id,
        plan=ctx.plan,
        monthly_limit=monthly_limit,
        monthly_used=monthly_used,
        monthly_remaining=max(0, monthly_limit - monthly_used),
        concurrent_limit=config["max_concurrent_applications"],
        concurrent_used=concurrent_used,
        percentage_used=round(monthly_used / max(monthly_limit, 1) * 100, 1),
    )


# ===================================================================
# M3: Team Billing Endpoints
# ===================================================================

class TeamCheckoutRequest(BaseModel):
    seats: int = 3  # minimum 3
    team_name: str = "My Team"
    success_url: str = "https://admin.sorce.app/billing/success"
    cancel_url: str = "https://admin.sorce.app/billing/cancel"


class TeamCheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class AddSeatsRequest(BaseModel):
    new_total_seats: int


class InviteRequest(BaseModel):
    email: str
    role: str = "MEMBER"


class AcceptInviteRequest(BaseModel):
    token: str


@router.post("/team-checkout", response_model=TeamCheckoutResponse)
async def create_team_checkout(
    body: TeamCheckoutRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> TeamCheckoutResponse:
    """
    Create a Stripe Checkout Session for TEAM plan.

    Pricing: $199/month base (includes 3 seats) + $49/seat/month for additional.
    """
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can manage billing")

    if ctx.plan == "TEAM":
        raise HTTPException(status_code=409, detail="Already on TEAM plan. Use /billing/add-seats.")

    s = get_settings()
    if not s.stripe_team_base_price_id or not s.stripe_team_seat_price_id:
        raise HTTPException(status_code=503, detail="Team billing not configured")

    seats = max(body.seats, s.team_included_seats)
    additional_seats = max(0, seats - s.team_included_seats)

    stripe = _get_stripe()

    async with db.acquire() as conn:
        customer_id = await _ensure_stripe_customer(conn, ctx.tenant_id)

    line_items: list[dict[str, Any]] = [
        {"price": s.stripe_team_base_price_id, "quantity": 1},
    ]
    if additional_seats > 0:
        line_items.append(
            {"price": s.stripe_team_seat_price_id, "quantity": additional_seats},
        )

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=line_items,
        success_url=body.success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=body.cancel_url,
        metadata={
            "tenant_id": ctx.tenant_id,
            "plan": "TEAM",
            "seats": str(seats),
            "team_name": body.team_name,
        },
    )

    incr("billing.team_checkout.created", tags={"tenant_id": ctx.tenant_id})
    return TeamCheckoutResponse(checkout_url=session.url, session_id=session.id)


@router.post("/add-seats")
async def add_seats(
    body: AddSeatsRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Add seats to an existing TEAM subscription (prorated)."""
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can manage billing")

    if ctx.plan not in ("TEAM", "ENTERPRISE"):
        raise HTTPException(status_code=409, detail="Must be on TEAM plan to add seats")

    s = get_settings()
    if body.new_total_seats < s.team_included_seats:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum seats: {s.team_included_seats}",
        )

    from backend.domain.teams import update_stripe_seat_quantity

    async with db.acquire() as conn:
        await update_stripe_seat_quantity(conn, ctx.tenant_id, body.new_total_seats)

    incr("billing.seats.updated", tags={"tenant_id": ctx.tenant_id})
    return {"status": "updated", "new_total_seats": body.new_total_seats}


@router.post("/invite")
async def invite_member(
    body: InviteRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Send a team invite to an email address."""
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can invite")

    from backend.domain.teams import create_invite

    try:
        async with db.acquire() as conn:
            invite = await create_invite(
                conn, ctx.tenant_id, ctx.user_id, body.email, body.role,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    incr("billing.invite.created")
    return {"status": "invited", "invite": invite}


@router.post("/invite/accept")
async def accept_invite_endpoint(
    body: AcceptInviteRequest,
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Accept a team invite by token. No auth required (token is the auth)."""
    from backend.domain.teams import accept_invite
    from backend.domain.repositories import db_transaction as txn

    try:
        async with txn(db) as conn:
            result = await accept_invite(conn, body.token, "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    incr("billing.invite.accepted")
    return {"status": "accepted", **result}


@router.get("/team")
async def team_overview(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get team overview: members, usage, invites."""
    from backend.domain.teams import get_team_overview

    async with db.acquire() as conn:
        return await get_team_overview(conn, ctx.tenant_id)


@router.get("/team/members")
async def team_members(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """List all team members with usage stats."""
    from backend.domain.teams import list_members

    async with db.acquire() as conn:
        return await list_members(conn, ctx.tenant_id)


@router.get("/team/invites")
async def team_invites(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """List all team invites."""
    from backend.domain.teams import list_invites

    async with db.acquire() as conn:
        return await list_invites(conn, ctx.tenant_id)


@router.delete("/team/members/{user_id}")
async def remove_team_member(
    user_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Remove a member from the team."""
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can remove members")

    from backend.domain.teams import remove_member

    try:
        async with db.acquire() as conn:
            removed = await remove_member(conn, ctx.tenant_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"status": "removed"}


# ===================================================================
# M4: Enterprise Billing Endpoints
# ===================================================================

class EnterpriseCheckoutRequest(BaseModel):
    seats: int = 10
    team_name: str = ""
    sla_tier: str = "standard"  # standard, premium, dedicated
    success_url: str = "https://admin.sorce.app/billing/success"
    cancel_url: str = "https://admin.sorce.app/billing/cancel"


@router.post("/enterprise-checkout")
async def create_enterprise_checkout(
    body: EnterpriseCheckoutRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """
    Create a Stripe Checkout Session for ENTERPRISE plan ($999+/month).

    Enterprise pricing is custom — this creates the base subscription.
    Custom pricing adjustments are handled via Stripe dashboard or API.
    """
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can manage billing")

    s = get_settings()
    if not s.stripe_enterprise_price_id:
        raise HTTPException(status_code=503, detail="Enterprise billing not configured")

    stripe = _get_stripe()

    async with db.acquire() as conn:
        customer_id = await _ensure_stripe_customer(conn, ctx.tenant_id)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": s.stripe_enterprise_price_id, "quantity": 1}],
        success_url=body.success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=body.cancel_url,
        metadata={
            "tenant_id": ctx.tenant_id,
            "plan": "ENTERPRISE",
            "seats": str(body.seats),
            "team_name": body.team_name,
            "sla_tier": body.sla_tier,
        },
    )

    incr("billing.enterprise_checkout.created", tags={"tenant_id": ctx.tenant_id})
    return {"checkout_url": session.url, "session_id": session.id}


@router.get("/audit-log")
async def get_audit_log_endpoint(
    limit: int = 50,
    offset: int = 0,
    action: str | None = None,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get audit log for current tenant (ENTERPRISE/TEAM)."""
    if ctx.plan not in ("TEAM", "ENTERPRISE"):
        raise HTTPException(status_code=403, detail="Audit log requires TEAM or ENTERPRISE plan")

    from backend.domain.audit import get_audit_log, get_audit_log_count

    async with db.acquire() as conn:
        logs = await get_audit_log(conn, ctx.tenant_id, limit, offset, action)
        total = await get_audit_log_count(conn, ctx.tenant_id)

    return {"logs": logs, "total": total, "limit": limit, "offset": offset}


@router.get("/audit-log/export")
async def export_audit_log_endpoint(
    days: int = 90,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
):  # returns Response
    """Export audit log as CSV (SOC 2 compliance)."""
    if ctx.plan != "ENTERPRISE":
        raise HTTPException(status_code=403, detail="Audit export requires ENTERPRISE plan")

    from backend.domain.audit import export_audit_log_csv

    async with db.acquire() as conn:
        csv_content = await export_audit_log_csv(conn, ctx.tenant_id, days)

    from fastapi.responses import Response as FastAPIResponse
    return FastAPIResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_log_{ctx.tenant_id}_{days}d.csv"},
    )


# ===================================================================
# M5: Annual Billing + Self-Serve Enterprise
# ===================================================================

class AnnualCheckoutRequest(BaseModel):
    plan: str  # PRO, TEAM, ENTERPRISE
    seats: int = 1
    team_name: str = ""
    success_url: str = "https://admin.sorce.app/billing/success"
    cancel_url: str = "https://admin.sorce.app/billing/cancel"


@router.post("/annual-checkout")
async def create_annual_checkout(
    body: AnnualCheckoutRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Create a Stripe Checkout for annual billing (20% discount)."""
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can manage billing")

    from backend.domain.contracts import get_annual_price_id
    price_id = get_annual_price_id(body.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"No annual price for plan: {body.plan}")

    stripe = _get_stripe()
    async with db.acquire() as conn:
        customer_id = await _ensure_stripe_customer(conn, ctx.tenant_id)

    line_items = [{"price": price_id, "quantity": 1}]
    # For TEAM, add seat line items
    s = get_settings()
    if body.plan == "TEAM" and body.seats > s.team_included_seats:
        extra = body.seats - s.team_included_seats
        if s.stripe_team_seat_price_id:
            line_items.append({"price": s.stripe_team_seat_price_id, "quantity": extra})

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=line_items,
        success_url=body.success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=body.cancel_url,
        metadata={
            "tenant_id": ctx.tenant_id,
            "plan": body.plan,
            "billing_interval": "annual",
            "seats": str(body.seats),
            "team_name": body.team_name,
        },
    )

    incr("billing.annual_checkout.created", tags={"plan": body.plan})
    return {"checkout_url": session.url, "session_id": session.id}


class SelfServeEnterpriseRequest(BaseModel):
    company_name: str
    custom_domain: str = ""
    seats: int = 10
    billing_interval: str = "monthly"  # monthly or annual


@router.post("/enterprise-self-serve")
async def enterprise_self_serve(
    body: SelfServeEnterpriseRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """
    Start self-serve enterprise signup.
    Creates onboarding record → returns checkout URL + onboarding status.
    """
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only owners/admins can upgrade")

    from backend.domain.contracts import start_enterprise_onboarding

    s = get_settings()
    stripe = _get_stripe()

    async with db.acquire() as conn:
        # Start onboarding
        onboarding = await start_enterprise_onboarding(conn, ctx.tenant_id, body.custom_domain)

        # Update tenant name
        await conn.execute(
            "UPDATE public.tenants SET team_name = $2 WHERE id = $1",
            ctx.tenant_id, body.company_name,
        )

        customer_id = await _ensure_stripe_customer(conn, ctx.tenant_id)

    # Determine price
    if body.billing_interval == "annual" and s.stripe_enterprise_annual_price_id:
        price_id = s.stripe_enterprise_annual_price_id
    elif s.stripe_enterprise_price_id:
        price_id = s.stripe_enterprise_price_id
    else:
        raise HTTPException(status_code=503, detail="Enterprise billing not configured")

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"https://admin.sorce.app/onboarding/sso?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"https://admin.sorce.app/enterprise",
        metadata={
            "tenant_id": ctx.tenant_id,
            "plan": "ENTERPRISE",
            "billing_interval": body.billing_interval,
            "seats": str(body.seats),
            "team_name": body.company_name,
            "sla_tier": "standard",
        },
    )

    incr("billing.enterprise_self_serve.created")
    return {
        "checkout_url": session.url,
        "onboarding": onboarding,
    }


@router.get("/onboarding")
async def get_onboarding(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get current enterprise onboarding status."""
    from backend.domain.contracts import get_onboarding_status
    async with db.acquire() as conn:
        status = await get_onboarding_status(conn, ctx.tenant_id)
    if not status:
        return {"step": "not_started"}
    return status
