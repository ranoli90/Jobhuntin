"""Billing API routes for Stripe checkout and subscription management."""

from __future__ import annotations

import os
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.domain.billing import ensure_stripe_customer, update_subscription_state
from backend.domain.stripe_client import get_stripe, protected_stripe_call
from backend.domain.tenant import TenantContext
from shared.config import Settings, settings_dependency
from shared.logging_config import get_logger

logger = get_logger("sorce.api.billing")

router = APIRouter(prefix="/billing", tags=["billing"])

# #24: Canonical billing tiers - single source of truth for API and frontend
BILLING_TIERS = [
    {
        "name": "FREE",
        "price": "$0",
        "features": ["10 applications", "Basic tailoring", "Standard support"],
        "actionKey": None,
        "recommended": False,
    },
    {
        "name": "PRO",
        "price": "$19",
        "features": ["Unlimited apps", "Priority queue", "Interview coach"],
        "recommended": True,
        "actionKey": "upgrade",
    },
    {
        "name": "TEAM",
        "price": "$49",
        "features": ["10 team seats", "API access", "White-label reports"],
        "actionKey": "addSeats",
        "recommended": False,
    },
]


# Dependencies (to be overridden at app startup)
async def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_tenant_ctx() -> TenantContext:
    raise NotImplementedError("Tenant context dependency not injected")


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str
    billing_period: str = "monthly"  # monthly or annual


class PortalRequest(BaseModel):
    return_url: str


@router.get("/tiers")
async def billing_tiers(
    tenant_ctx: Any = Depends(_get_tenant_ctx),
) -> list[dict[str, Any]]:
    """#24: Get billing tiers. Single source of truth for plan display."""
    return BILLING_TIERS


@router.get("/status")
async def billing_status(
    request: Request,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
    tenant_ctx: Any = Depends(_get_tenant_ctx),
):
    """Get current billing status for the tenant."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT bc.provider_customer_id, bc.current_subscription_status,
                   bc.current_subscription_id, bc.current_period_end,
                   t.plan
            FROM public.billing_customers bc
            JOIN public.tenants t ON t.id = bc.tenant_id
            WHERE bc.tenant_id = $1
            """,
            tenant_ctx.tenant_id,
        )

        if not row:
            # No billing record yet - return FREE plan
            return {
                "tenant_id": tenant_ctx.tenant_id,
                "plan": "FREE",
                "provider": None,
                "provider_customer_id": None,
                "subscription_status": "none",
                "current_period_end": None,
            }

        return {
            "tenant_id": tenant_ctx.tenant_id,
            "plan": row["plan"],
            "provider": "STRIPE" if row["provider_customer_id"] else None,
            "provider_customer_id": row["provider_customer_id"],
            "subscription_status": row["current_subscription_status"] or "none",
            "current_period_end": (
                row["current_period_end"].isoformat()
                if row["current_period_end"]
                else None
            ),
        }


@router.get("/usage")
async def billing_usage(
    request: Request,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
    tenant_ctx: Any = Depends(_get_tenant_ctx),
):
    """Get current billing usage for the tenant."""
    async with db.acquire() as conn:
        # Get tenant plan
        tenant_row = await conn.fetchrow(
            "SELECT plan FROM public.tenants WHERE id = $1",
            tenant_ctx.tenant_id,
        )
        plan = tenant_row["plan"] if tenant_row else "FREE"

        # Count applications this month
        usage_row = await conn.fetchrow(
            """
            SELECT COUNT(*) as count
            FROM public.applications
            WHERE tenant_id = $1
            AND created_at >= date_trunc('month', now())
            """,
            tenant_ctx.tenant_id,
        )
        monthly_used = usage_row["count"] if usage_row else 0

        # Set limits based on plan - using canonical values from plans.py
        if plan == "FREE":
            monthly_limit = 25  # Match plans.py FREE tier limit
        elif plan == "PRO":
            monthly_limit = None  # Unlimited
        elif plan == "TEAM":
            monthly_limit = None  # Unlimited
        else:
            monthly_limit = None

        monthly_remaining = monthly_limit - monthly_used if monthly_limit else None
        percentage_used = (monthly_used / monthly_limit * 100) if monthly_limit else 0

        return {
            "tenant_id": tenant_ctx.tenant_id,
            "plan": plan,
            "monthly_limit": monthly_limit,
            "monthly_used": monthly_used,
            "monthly_remaining": monthly_remaining,
            "percentage_used": min(percentage_used, 100),
            "concurrent_limit": 2
            if plan == "FREE"
            else None,  # Match plans.py FREE tier concurrent limit
            "concurrent_used": 0,  # TODO: Track concurrent usage
        }


def _validate_redirect_url(url: str, param_name: str, settings: Settings) -> None:
    """Validate that redirect URL starts with an allowed origin."""
    app_url = getattr(settings, "app_base_url", None) or os.getenv(
        "APP_PUBLIC_URL", "https://jobhuntin.com"
    )
    if app_url and app_url != "[REDACTED]":
        allowed_origins = [app_url.rstrip("/"), "http://localhost:5173"]
    else:
        allowed_origins = ["https://jobhuntin.com", "http://localhost:5173"]
    if not any(url.startswith(origin) for origin in allowed_origins):
        raise HTTPException(status_code=400, detail=f"Invalid {param_name}")


def _handle_stripe_error(e: Exception) -> None:
    """Re-raise Stripe 4xx as HTTPException for better UX (BILL-006)."""
    stripe_mod = get_stripe()
    if hasattr(stripe_mod, "error") and isinstance(e, stripe_mod.error.StripeError):
        status = getattr(e, "http_status", 400)
        if 400 <= status < 500:
            msg = "Your card was declined. Please try a different payment method." if status == 402 else (getattr(e, "user_message", None) or str(e))[:200]
            raise HTTPException(status_code=status, detail=msg)


@router.post("/checkout")
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
    tenant_ctx: Any = Depends(_get_tenant_ctx),
):
    """Create a Stripe checkout session for PRO subscription."""
    _validate_redirect_url(body.success_url, "success_url", settings)
    _validate_redirect_url(body.cancel_url, "cancel_url", settings)
    stripe = get_stripe()

    try:
        async with db.acquire() as conn:
            # Ensure customer exists (user_email not available in TenantContext, will be updated after checkout)
            customer_id = await ensure_stripe_customer(conn, tenant_ctx.tenant_id, None)

            # Determine price ID based on billing period
            if body.billing_period == "annual":
                price_id = settings.stripe_pro_annual_price_id
            else:
                price_id = settings.stripe_pro_price_id

            if not price_id:
                raise HTTPException(
                    status_code=500, detail="Stripe price ID not configured"
                )

            # Create checkout session with optional first month promotion
            # Apply coupon if configured and valid
            coupon_id = getattr(settings, "first_month_coupon", None)

            # Validate coupon exists in Stripe before applying (optional but safer)
            discounts = []
            if coupon_id:
                try:
                    # Verify coupon exists before applying
                    coupon = protected_stripe_call(
                        lambda: stripe.Coupon.retrieve(coupon_id)
                    )
                    if coupon:
                        discounts = [{"coupon": coupon_id}]
                        logger.info(
                            f"Applying coupon {coupon_id} for tenant {tenant_ctx.tenant_id}"
                        )
                    else:
                        logger.warning(
                            f"Coupon {coupon_id} not found in Stripe, proceeding without discount"
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to validate coupon {coupon_id}: {e}, proceeding without discount"
                    )

            checkout_session = protected_stripe_call(
                lambda: stripe.checkout.Session.create(
                    customer=customer_id,
                    payment_method_types=["card"],
                    line_items=[
                        {
                            "price": price_id,
                            "quantity": 1,
                        }
                    ],
                    mode="subscription",
                    success_url=body.success_url,
                    cancel_url=body.cancel_url,
                    discounts=discounts,
                    subscription_data={
                        "trial_period_days": (
                            settings.stripe_free_trial_days
                            if settings.stripe_free_trial_days > 0
                            else None
                        ),
                        "metadata": {
                            "tenant_id": tenant_ctx.tenant_id,
                            "plan": "PRO",
                        },
                    },
                    metadata={
                        "tenant_id": tenant_ctx.tenant_id,
                        "plan": "PRO",
                        "billing_period": body.billing_period,
                    },
                )
            )

            if not checkout_session:
                raise HTTPException(
                    status_code=503, detail="Payment service temporarily unavailable"
                )

            logger.info(
                "Checkout session created for tenant %s: %s",
                tenant_ctx.tenant_id,
                checkout_session.id,
            )

            return {"checkout_url": checkout_session.url}
    except HTTPException:
        raise
    except Exception as e:
        _handle_stripe_error(e)
        logger.error("Checkout creation failed: %s", e)
        raise HTTPException(status_code=503, detail="Payment service temporarily unavailable")


@router.post("/portal")
async def create_portal(
    request: Request,
    body: PortalRequest,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
    tenant_ctx: Any = Depends(_get_tenant_ctx),
):
    """Create a Stripe customer portal session."""
    _validate_redirect_url(body.return_url, "return_url", settings)
    stripe = get_stripe()

    async with db.acquire() as conn:
        # Get customer ID
        row = await conn.fetchrow(
            "SELECT provider_customer_id FROM public.billing_customers WHERE tenant_id = $1",
            tenant_ctx.tenant_id,
        )

        if not row or not row["provider_customer_id"]:
            raise HTTPException(
                status_code=400,
                detail="No active subscription. Please subscribe first at /billing/checkout",
            )

        customer_id = row["provider_customer_id"]

        # Create portal session
        portal_session = protected_stripe_call(
            lambda: stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=body.return_url,
            )
        )

        if not portal_session:
            raise HTTPException(
                status_code=503, detail="Payment service temporarily unavailable"
            )

        return {"portal_url": portal_session.url}


@router.get("/invoices")
async def list_invoices(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: Any = Depends(_get_pool),
    settings: Settings = Depends(settings_dependency),
) -> list[dict[str, Any]]:
    """List billing invoices for the current tenant."""
    if not settings.stripe_secret_key:
        return []

    stripe = get_stripe()
    try:
        async with db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT plan FROM public.tenants WHERE id = $1",
                ctx.tenant_id,
            )
            if not row or row["plan"] == "FREE":
                return []

            user_row = await conn.fetchrow(
                "SELECT email FROM public.users WHERE id = $1",
                ctx.user_id,
            )
            user_email = user_row["email"] if user_row else None

            customer_id = await ensure_stripe_customer(conn, ctx.tenant_id, user_email)
        invoices = protected_stripe_call(
            lambda: stripe.Invoice.list(customer=customer_id, limit=20)
        )
        return [
            {
                "id": inv.id,
                "number": inv.number,
                "amount_due": inv.amount_due,
                "amount_paid": inv.amount_paid,
                "currency": inv.currency,
                "status": inv.status,
                "created": inv.created,
                "period_start": inv.period_start,
                "period_end": inv.period_end,
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url,
            }
            for inv in invoices.auto_paging_iter()
        ][:20]
    except Exception as e:
        logger.warning("Failed to fetch invoices: %s", e)
        return []


class TeamCheckoutRequest(BaseModel):
    seats: int = 1
    success_url: str | None = None
    cancel_url: str | None = None


@router.post("/team-checkout")
async def team_checkout(
    body: TeamCheckoutRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: Any = Depends(_get_pool),
    settings: Settings = Depends(settings_dependency),
) -> dict[str, Any]:
    """Create a Stripe checkout session for team plan with additional seats."""
    if body.seats < 1:
        raise HTTPException(status_code=400, detail="Seats must be at least 1")
    if body.seats > 500:
        raise HTTPException(status_code=400, detail="Maximum 500 seats")
    stripe = get_stripe()
    if not settings.stripe_team_base_price_id:
        raise HTTPException(status_code=503, detail="Team pricing not configured")

    # BILL-003/BILL-004: Use body URLs if provided, else build from app_base_url
    app_url = getattr(settings, "app_base_url", None) or os.getenv("APP_PUBLIC_URL", "https://jobhuntin.com")
    success_url = body.success_url or f"{app_url.rstrip('/')}/app/billing?success=true"
    cancel_url = body.cancel_url or f"{app_url.rstrip('/')}/app/billing?canceled=true"
    _validate_redirect_url(success_url, "success_url", settings)
    _validate_redirect_url(cancel_url, "cancel_url", settings)

    try:
        async with db.acquire() as conn:
            user_row = await conn.fetchrow(
                "SELECT email FROM public.users WHERE id = $1",
                ctx.user_id,
            )
            user_email = user_row["email"] if user_row else None
            customer_id = await ensure_stripe_customer(conn, ctx.tenant_id, user_email)

        line_items = [
            {"price": settings.stripe_team_base_price_id, "quantity": 1},
        ]
        if settings.stripe_team_seat_price_id and body.seats > 0:
            line_items.append(
                {"price": settings.stripe_team_seat_price_id, "quantity": body.seats}
            )

        session = protected_stripe_call(
            lambda: stripe.checkout.Session.create(
                customer=customer_id,
                mode="subscription",
                line_items=line_items,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "tenant_id": str(ctx.tenant_id),
                    "plan": "TEAM",
                    "seats": str(body.seats),
                },
            )
        )
        if not session or not session.url:
            raise HTTPException(
                status_code=503, detail="Payment service temporarily unavailable"
            )
        return {"checkout_url": session.url}
    except HTTPException:
        raise
    except Exception as e:
        try:
            _handle_stripe_error(e)
        except HTTPException:
            raise
        logger.error("Team checkout creation failed: %s", e)
        raise HTTPException(
            status_code=503, detail="Payment service temporarily unavailable"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
):
    """Handle Stripe webhooks for subscription events."""
    stripe = get_stripe()

    # Get the webhook payload
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    if not settings.stripe_webhook_secret:
        logger.error("Stripe webhook secret not configured")
        raise HTTPException(
            status_code=503,
            detail="Webhook not configured. Set STRIPE_WEBHOOK_SECRET.",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event.get("id")
    if not event_id:
        raise HTTPException(status_code=400, detail="Invalid event: missing id")

    async with db.acquire() as conn:
        async with conn.transaction():
            # Idempotency: INSERT first - if conflict, event already processed (atomic)
            row = await conn.fetchrow(
                """
                INSERT INTO public.processed_stripe_events (event_id) VALUES ($1)
                ON CONFLICT (event_id) DO NOTHING RETURNING event_id
                """,
                event_id,
            )
            if not row:
                return {"status": "ok"}

            data_obj = (event.get("data") or {}).get("object")
            if not isinstance(data_obj, dict):
                logger.warning("Stripe event missing data.object: type=%s", event.get("type"))
                return {"status": "ok"}

            if event["type"] == "checkout.session.completed":
                await handle_checkout_completed(conn, data_obj)
            elif event["type"] == "invoice.payment_succeeded":
                await handle_payment_succeeded(conn, data_obj)
            elif event["type"] == "invoice.payment_failed":
                await handle_payment_failed(conn, data_obj)
            elif event["type"] == "customer.subscription.deleted":
                await handle_subscription_cancelled(conn, data_obj)
            elif event["type"] == "customer.subscription.updated":
                await handle_subscription_updated(conn, data_obj)
            # BILL-005: Both handlers run in same transaction; idempotent and order-independent

    return {"status": "ok"}


def _extract_id(obj: Any, key: str) -> str | None:
    """Extract ID from Stripe object (may be string or expanded dict)."""
    if not isinstance(obj, dict):
        return None
    val = obj.get(key)
    if isinstance(val, dict):
        return val.get("id")
    return val if isinstance(val, str) else None


async def handle_checkout_completed(conn: asyncpg.Connection, session: dict):
    """Handle successful checkout completion."""
    customer_id = _extract_id(session, "customer")
    subscription_id = _extract_id(session, "subscription")
    metadata = session.get("metadata") or {}

    # Extract tenant_id and plan from metadata to update tenant record
    tenant_id = metadata.get("tenant_id")
    plan = metadata.get("plan")

    if subscription_id and customer_id:
        await update_subscription_state(conn, customer_id, "active", subscription_id)

    # Update tenant plan if metadata is available
    if tenant_id and plan:
        await conn.execute(
            "UPDATE public.tenants SET plan = $1 WHERE id = $2", plan, tenant_id
        )
        logger.info(f"Updated tenant {tenant_id} plan to {plan}")

    logger.info("Checkout completed for customer %s, tenant %s", customer_id, tenant_id)


async def handle_payment_succeeded(conn: asyncpg.Connection, invoice: dict):
    """Handle successful payment."""
    customer_id = _extract_id(invoice, "customer")
    subscription_id = _extract_id(invoice, "subscription")

    if subscription_id and customer_id:
        await update_subscription_state(conn, customer_id, "active", subscription_id)

    logger.info("Payment succeeded for customer %s", customer_id)


async def handle_payment_failed(conn: asyncpg.Connection, invoice: dict):
    """Handle failed payment."""
    customer_id = _extract_id(invoice, "customer")
    if not customer_id:
        logger.warning("Payment failed event missing customer_id")
        return
    await update_subscription_state(conn, customer_id, "past_due")
    logger.warning("Payment failed for customer %s", customer_id)


async def handle_subscription_cancelled(conn: asyncpg.Connection, subscription: dict):
    """Handle subscription cancellation."""
    customer_id = _extract_id(subscription, "customer")
    if not customer_id:
        logger.warning("Subscription cancelled event missing customer_id")
        return
    await update_subscription_state(conn, customer_id, "canceled")
    # BILL-001: Downgrade tenant plan to FREE when subscription ends
    await conn.execute(
        """UPDATE public.tenants SET plan = 'FREE'
           WHERE id = (SELECT tenant_id FROM public.billing_customers
                       WHERE provider_customer_id = $1 AND tenant_id IS NOT NULL)""",
        customer_id,
    )
    logger.info("Subscription cancelled for customer %s", customer_id)


async def handle_subscription_updated(conn: asyncpg.Connection, subscription: dict):
    """Handle subscription updates."""
    customer_id = _extract_id(subscription, "customer")
    status = subscription.get("status")
    sub_id = subscription.get("id")
    subscription_id = sub_id if isinstance(sub_id, str) else (sub_id.get("id") if isinstance(sub_id, dict) else None)
    if not customer_id:
        logger.warning("Subscription updated event missing customer_id")
        return
    await update_subscription_state(conn, customer_id, status, subscription_id)
    # BILL-001: Downgrade tenant plan to FREE when subscription is canceled/ended
    if status in ("canceled", "unpaid", "incomplete_expired"):
        await conn.execute(
            """UPDATE public.tenants SET plan = 'FREE'
               WHERE id = (SELECT tenant_id FROM public.billing_customers
                           WHERE provider_customer_id = $1 AND tenant_id IS NOT NULL)""",
            customer_id,
        )
    logger.info("Subscription updated for customer %s: %s", customer_id, status)
