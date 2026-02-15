from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from shared.config import Settings, settings_dependency
from shared.logging_config import get_logger

from backend.domain.billing import (
    ensure_stripe_customer,
    get_stripe_client,
    handle_checkout_session,
    handle_invoice_event,
    handle_subscription_event,
)
from backend.domain.plans import plan_config_for
from backend.domain.repositories import TenantRepo
from backend.domain.tenant import TenantContext

logger = get_logger("sorce.api.billing")

router = APIRouter(prefix="/billing", tags=["billing"])

# ---------------------------------------------------------------------------
# Dependencies (injected by main.py)
# ---------------------------------------------------------------------------

def _get_pool() -> asyncpg.Pool:
    raise NotImplementedError("Pool dependency not injected")

async def _get_tenant_ctx() -> TenantContext:
    raise NotImplementedError

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

class PortalResponse(BaseModel):
    portal_url: str

class BillingStatusResponse(BaseModel):
    tenant_id: str
    plan: str
    provider: str | None
    provider_customer_id: str | None
    subscription_status: str
    current_period_end: str | None

class UsageResponse(BaseModel):
    tenant_id: str
    plan: str
    monthly_limit: int | None
    monthly_used: int
    monthly_remaining: int | None
    concurrent_limit: int | None
    concurrent_used: int
    percentage_used: float

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> BillingStatusResponse:
    """Get current billing status for the tenant."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                t.plan,
                bc.provider,
                bc.provider_customer_id,
                bc.current_subscription_status,
                bc.current_period_end
            FROM public.tenants t
            LEFT JOIN public.billing_customers bc ON bc.tenant_id = t.id
            WHERE t.id = $1
            """,
            ctx.tenant_id,
        )

    if not row:
        return BillingStatusResponse(
            tenant_id=ctx.tenant_id,
            plan="FREE",
            provider=None,
            provider_customer_id=None,
            subscription_status="active",
            current_period_end=None,
        )

    return BillingStatusResponse(
        tenant_id=ctx.tenant_id,
        plan=row["plan"],
        provider=row["provider"],
        provider_customer_id=row["provider_customer_id"],
        subscription_status=row["current_subscription_status"] or "active",
        current_period_end=row["current_period_end"].isoformat() if row["current_period_end"] else None,
    )

@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> UsageResponse:
    """Get current quota usage."""
    async with db.acquire() as conn:
        # Get current usage counts
        monthly_used = await TenantRepo.count_monthly_applications(conn, ctx.tenant_id)
        concurrent_used = await TenantRepo.count_concurrent_processing(conn, ctx.tenant_id)

        # Get plan config (could fetch custom metadata from tenant row if needed)
        # For simplicity, we assume standard plan limits unless we fetch tenant row
        tenant_row = await conn.fetchrow("SELECT plan, metadata FROM public.tenants WHERE id = $1", ctx.tenant_id)
        plan = tenant_row["plan"] if tenant_row else "FREE"
        metadata = tenant_row["metadata"] if tenant_row and "metadata" in tenant_row else None  # jsonb metadata might contain plan overrides

        config = plan_config_for(plan, metadata)

        monthly_limit = config["max_monthly_applications"]
        concurrent_limit = config["max_concurrent_applications"]

        monthly_remaining = max(0, monthly_limit - monthly_used)
        percentage_used = (monthly_used / monthly_limit) * 100 if monthly_limit > 0 else 0.0

    return UsageResponse(
        tenant_id=ctx.tenant_id,
        plan=plan,
        monthly_limit=monthly_limit,
        monthly_used=monthly_used,
        monthly_remaining=monthly_remaining,
        concurrent_limit=concurrent_limit,
        concurrent_used=concurrent_used,
        percentage_used=percentage_used,
    )

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
    settings: Settings = Depends(settings_dependency),
) -> CheckoutResponse:
    """Create Stripe checkout session for PRO plan."""
    stripe = get_stripe_client()

    async with db.acquire() as conn:
        email_row = await conn.fetchrow("SELECT email FROM public.users WHERE id = $1", ctx.user_id)
        email = email_row["email"] if email_row else None

        customer_id = await ensure_stripe_customer(conn, ctx.tenant_id, email)

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": settings.stripe_pro_price_id,
                "quantity": 1,
            }],
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={
                "tenant_id": ctx.tenant_id,
                "user_id": ctx.user_id,
                "plan": "PRO",
            },
        )
        return CheckoutResponse(checkout_url=session.url, session_id=session.id)
    except Exception as e:
        logger.error("Stripe checkout failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Payment provider error: {str(e)}")

@router.post("/team-checkout", response_model=CheckoutResponse)
async def create_team_checkout_session(
    body: CheckoutRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
    settings: Settings = Depends(settings_dependency),
) -> CheckoutResponse:
    """Create Stripe checkout session for TEAM plan (per seat)."""
    stripe = get_stripe_client()

    async with db.acquire() as conn:
        email_row = await conn.fetchrow("SELECT email FROM public.users WHERE id = $1", ctx.user_id)
        email = email_row["email"] if email_row else None
        customer_id = await ensure_stripe_customer(conn, ctx.tenant_id, email)

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": settings.stripe_team_seat_price_id,
                "quantity": 3, # Default starting seats
            }],
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={
                "tenant_id": ctx.tenant_id,
                "user_id": ctx.user_id,
                "plan": "TEAM",
            },
        )
        return CheckoutResponse(checkout_url=session.url, session_id=session.id)
    except Exception as e:
        logger.error("Stripe checkout failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Payment provider error: {str(e)}")

@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
    settings: Settings = Depends(settings_dependency),
) -> PortalResponse:
    """Create Stripe billing portal session."""
    stripe = get_stripe_client()

    async with db.acquire() as conn:
        customer_id = await ensure_stripe_customer(conn, ctx.tenant_id)

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.app_base_url}/app/settings",
        )
        return PortalResponse(portal_url=session.url)
    except Exception as e:
        logger.error("Stripe portal failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Payment provider error: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: asyncpg.Pool = Depends(_get_pool),
    settings: Settings = Depends(settings_dependency),
):
    """Handle Stripe webhooks."""
    stripe = get_stripe_client()
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        # Check if it's a signature verification error (handle both stripe.error and stripe namespaces)
        if "signature" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid signature")
        raise

    data = event["data"]["object"]
    event_type = event["type"]

    logger.info("Stripe webhook: %s", event_type)

    async with db.acquire() as conn:
        if event_type in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
            await handle_subscription_event(conn, event_type, data)
        elif event_type == "invoice.payment_failed":
            await handle_invoice_event(conn, data)
        elif event_type == "checkout.session.completed":
            await handle_checkout_session(conn, data)

    return {"status": "ok"}
