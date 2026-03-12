"""Billing domain functions (no FastAPI dependencies to avoid circular imports)."""

import asyncpg


async def ensure_stripe_customer(
    conn: asyncpg.Connection, tenant_id: str, user_email: str | None
) -> str:
    """Ensure a Stripe customer exists for the tenant."""
    from packages.backend.domain.stripe_client import get_stripe

    stripe = get_stripe()

    row = await conn.fetchrow(
        "SELECT provider_customer_id FROM public.billing_customers WHERE tenant_id = $1",
        tenant_id,
    )

    if row and row["provider_customer_id"]:
        return row["provider_customer_id"]

    # Create new customer - handle None email gracefully
    customer_params = {"metadata": {"tenant_id": tenant_id}}

    # Only add email if it's provided (Stripe doesn't accept None)
    if user_email:
        customer_params["email"] = user_email

    customer = stripe.Customer.create(**customer_params)

    await conn.execute(
        """INSERT INTO public.billing_customers (tenant_id, provider, provider_customer_id)
            VALUES ($1, 'STRIPE', $2)
            ON CONFLICT (tenant_id) DO UPDATE SET
            provider = 'STRIPE',
            provider_customer_id = $2""",
        tenant_id,
        customer.id,
    )

    return customer.id


async def update_subscription_state(
    conn: asyncpg.Connection,
    customer_id: str,
    status: str,
    subscription_id: str | None = None,
):
    """Update subscription state in database."""
    await conn.execute(
        """UPDATE public.billing_customers
            SET current_subscription_status = $1,
                current_subscription_id = COALESCE($2, current_subscription_id)
            WHERE provider_customer_id = $3""",
        status,
        subscription_id,
        customer_id,
    )
