"""Billing API routes for Stripe checkout and subscription management."""

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from shared.config import Settings, settings_dependency
from shared.logging_config import get_logger
from shared.middleware import get_tenant_context

from packages.backend.domain.billing import ensure_stripe_customer, update_subscription_state
from packages.backend.domain.stripe_client import get_stripe, protected_stripe_call

logger = get_logger("sorce.api.billing")

router = APIRouter(prefix="/billing", tags=["billing"])

# Dependencies (to be overridden at app startup)
async def _get_pool():
    raise NotImplementedError("Pool dependency not injected")

async def _get_tenant_ctx():
    raise NotImplementedError("Tenant context dependency not injected")


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str
    billing_period: str = "monthly"  # monthly or annual


class PortalRequest(BaseModel):
    return_url: str


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
            "current_period_end": row["current_period_end"].isoformat() if row["current_period_end"] else None,
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
        
        # Set limits based on plan
        if plan == "FREE":
            monthly_limit = 20
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
            "concurrent_limit": 5 if plan == "FREE" else None,
            "concurrent_used": 0,  # TODO: Track concurrent usage
        }


@router.post("/checkout")
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
    tenant_ctx: Any = Depends(_get_tenant_ctx),
):
    """Create a Stripe checkout session for PRO subscription."""
    stripe = get_stripe()
    
    async with db.acquire() as conn:
        # Ensure customer exists
        customer_id = await ensure_stripe_customer(conn, tenant_ctx.tenant_id, tenant_ctx.user_email)
        
        # Determine price ID based on billing period
        if body.billing_period == "annual":
            price_id = settings.stripe_pro_annual_price_id
        else:
            price_id = settings.stripe_pro_price_id
        
        if not price_id:
            raise HTTPException(status_code=500, detail="Stripe price ID not configured")
        
        # Create checkout session with $10 first month promotion
        # Apply the FIRST_MONTH_10 coupon automatically for new subscribers
        coupon_id = getattr(settings, 'first_month_coupon', 'FIRST_MONTH_10')
        
        checkout_session = protected_stripe_call(
            lambda: stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=body.success_url,
                cancel_url=body.cancel_url,
                discounts=[{"coupon": coupon_id}] if coupon_id else [],
                subscription_data={
                    "trial_period_days": settings.stripe_free_trial_days if settings.stripe_free_trial_days > 0 else None,
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
            raise HTTPException(status_code=503, detail="Payment service temporarily unavailable")
        
        logger.info(
            "Checkout session created for tenant %s: %s",
            tenant_ctx.tenant_id,
            checkout_session.id,
        )
        
        return {"checkout_url": checkout_session.url}


@router.post("/portal")
async def create_portal(
    request: Request,
    body: PortalRequest,
    settings: Settings = Depends(settings_dependency),
    db: Any = Depends(_get_pool),
    tenant_ctx: Any = Depends(_get_tenant_ctx),
):
    """Create a Stripe customer portal session."""
    stripe = get_stripe()
    
    async with db.acquire() as conn:
        # Get customer ID
        row = await conn.fetchrow(
            "SELECT provider_customer_id FROM public.billing_customers WHERE tenant_id = $1",
            tenant_ctx.tenant_id,
        )
        
        if not row or not row["provider_customer_id"]:
            # No Stripe customer yet - redirect to checkout instead
            return {"checkout_url": f"{body.return_url}/upgrade"}
        
        customer_id = row["provider_customer_id"]
        
        # Create portal session
        portal_session = protected_stripe_call(
            lambda: stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=body.return_url,
            )
        )
        
        if not portal_session:
            raise HTTPException(status_code=503, detail="Payment service temporarily unavailable")
        
        return {"portal_url": portal_session.url}


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
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    async with db.acquire() as conn:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            await handle_checkout_completed(conn, session)
        elif event["type"] == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            await handle_payment_succeeded(conn, invoice)
        elif event["type"] == "invoice.payment_failed":
            invoice = event["data"]["object"]
            await handle_payment_failed(conn, invoice)
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            await handle_subscription_cancelled(conn, subscription)
        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            await handle_subscription_updated(conn, subscription)
    
    return {"status": "ok"}


async def handle_checkout_completed(conn: asyncpg.Connection, session: dict):
    """Handle successful checkout completion."""
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    metadata = session.get("metadata", {})
    
    if subscription_id:
        await update_subscription_state(
            conn, customer_id, "active", subscription_id
        )
    
    logger.info("Checkout completed for customer %s", customer_id)


async def handle_payment_succeeded(conn: asyncpg.Connection, invoice: dict):
    """Handle successful payment."""
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")
    
    if subscription_id:
        await update_subscription_state(
            conn, customer_id, "active", subscription_id
        )
    
    logger.info("Payment succeeded for customer %s", customer_id)


async def handle_payment_failed(conn: asyncpg.Connection, invoice: dict):
    """Handle failed payment."""
    customer_id = invoice.get("customer")
    
    await update_subscription_state(conn, customer_id, "past_due")
    logger.warning("Payment failed for customer %s", customer_id)


async def handle_subscription_cancelled(conn: asyncpg.Connection, subscription: dict):
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")
    
    await update_subscription_state(conn, customer_id, "canceled")
    logger.info("Subscription cancelled for customer %s", customer_id)


async def handle_subscription_updated(conn: asyncpg.Connection, subscription: dict):
    """Handle subscription updates."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    subscription_id = subscription.get("id")
    
    await update_subscription_state(conn, customer_id, status, subscription_id)
    logger.info("Subscription updated for customer %s: %s", customer_id, status)
