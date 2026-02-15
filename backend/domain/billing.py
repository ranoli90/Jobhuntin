"""
Billing domain logic — Stripe integration, subscription state management, and checkout handling.
"""

from __future__ import annotations

from datetime import UTC, datetime

import asyncpg
from shared.config import get_settings
from shared.logging_config import get_logger

from backend.domain.audit import record_audit_event
from backend.domain.stripe_client import get_stripe, protected_stripe_call

logger = get_logger("sorce.billing")

SUBSCRIPTION_STATUS_MAP: dict[str, str] = {
    "active": "PRO",
    "trialing": "PRO",
    "past_due": "PRO",
    "canceled": "FREE",
    "unpaid": "FREE",
    "incomplete_expired": "FREE",
}

def get_stripe_client():
    """Lazy-import stripe and configure API key. Deprecated: use get_stripe() instead."""
    return get_stripe()

async def ensure_stripe_customer(
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

    stripe = get_stripe()
    # Protected Stripe call with circuit breaker
    customer = protected_stripe_call(
        lambda: stripe.Customer.create(
            metadata={"tenant_id": tenant_id},
            email=user_email,
        )
    )

    if customer is None:
        raise Exception("Failed to create Stripe customer - circuit breaker open")

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

async def update_subscription_state(
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

async def handle_subscription_event(
    conn: asyncpg.Connection, event_type: str, data_object: dict
) -> None:
    customer_id = data_object.get("customer", "")
    status = data_object.get("status", "canceled")
    sub_id = data_object.get("id")
    period_end_ts = data_object.get("current_period_end")
    period_end = (
        datetime.fromtimestamp(period_end_ts, tz=UTC)
        if period_end_ts else None
    )
    await update_subscription_state(
        conn, customer_id, status, sub_id, period_end,
    )

async def handle_invoice_event(conn: asyncpg.Connection, data_object: dict) -> None:
    customer_id = data_object.get("customer", "")
    await update_subscription_state(conn, customer_id, "past_due")

async def handle_checkout_session(conn: asyncpg.Connection, data_object: dict) -> None:
    customer_id = data_object.get("customer", "")
    sub_id = data_object.get("subscription")
    metadata = data_object.get("metadata", {})

    if sub_id:
        await update_subscription_state(conn, customer_id, "active", sub_id)

    # Handle TEAM/ENTERPRISE metadata
    if metadata.get("plan") == "TEAM":
        await handle_team_checkout(conn, customer_id, sub_id, metadata)
    elif metadata.get("plan") == "ENTERPRISE":
        await handle_enterprise_checkout(conn, customer_id, metadata)

async def handle_team_checkout(
    conn: asyncpg.Connection, customer_id: str, sub_id: str | None, metadata: dict
) -> None:
    seats = int(metadata.get("seats", "3"))
    team_name = metadata.get("team_name", "")

    # Override plan to TEAM
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

    # Store the seat subscription_item_id
    if sub_id:
        try:
            stripe = get_stripe()
            s = get_settings()
            # Protected Stripe call
            subscription = protected_stripe_call(
                lambda: stripe.Subscription.retrieve(sub_id)
            )
            if subscription:
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

async def handle_enterprise_checkout(
    conn: asyncpg.Connection, customer_id: str, metadata: dict
) -> None:
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
        await record_audit_event(
            conn, t_id, None,
            action="billing.enterprise_activated",
            resource="tenant",
            resource_id=t_id,
            details={"seats": seats, "sla_tier": sla_tier},
        )

    logger.info("ENTERPRISE checkout completed: customer=%s seats=%d sla=%s", customer_id, seats, sla_tier)
