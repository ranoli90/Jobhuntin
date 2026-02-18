"""
Stripe Connect payouts — revenue share for blueprint marketplace authors.

70% to authors, 30% platform fee.
Handles: Connect account onboarding, transfer creation, payout tracking.
"""

from __future__ import annotations

from typing import Any

import asyncpg
from shared.config import get_settings
from shared.logging_config import get_logger

from backend.domain.stripe_client import (
    get_protected_stripe,
    get_stripe,
    protected_stripe_call,
)

logger = get_logger("sorce.payouts")


async def get_or_create_connect_account(
    conn: asyncpg.Connection,
    tenant_id: str,
    email: str,
) -> str:
    """Get existing Stripe Connect account or create a new one."""
    row = await conn.fetchrow(
        "SELECT stripe_connect_id FROM public.tenants WHERE id = $1", tenant_id,
    )
    if row and row["stripe_connect_id"]:
        return row["stripe_connect_id"]

    s = get_settings()
    if not s.stripe_secret_key:
        raise RuntimeError("Stripe not configured")

    stripe = get_stripe()

    account = protected_stripe_call(
        lambda: stripe.Account.create(
            type="express",
            email=email,
            capabilities={"transfers": {"requested": True}},
            metadata={"tenant_id": tenant_id},
        )
    )

    if not account:
        raise RuntimeError("Failed to create Stripe Connect account (circuit open)")

    await conn.execute(
        "UPDATE public.tenants SET stripe_connect_id = $2 WHERE id = $1",
        tenant_id, account.id,
    )

    logger.info("Created Stripe Connect account %s for tenant %s", account.id, tenant_id)
    return account.id


async def create_connect_onboarding_link(
    conn: asyncpg.Connection,
    tenant_id: str,
    email: str,
    return_url: str = "https://admin.sorce.app/marketplace/author",
) -> str:
    """Create a Stripe Connect onboarding link for the author."""
    account_id = await get_or_create_connect_account(conn, tenant_id, email)

    get_settings()
    stripe = get_stripe()
    link = protected_stripe_call(
        lambda: stripe.AccountLink.create(
            account=account_id,
            refresh_url=return_url,
            return_url=return_url,
            type="account_onboarding",
        )
    )

    if not link:
        raise RuntimeError("Failed to create onboarding link (circuit open)")

    return link.url


async def process_marketplace_payouts(
    conn: asyncpg.Connection,
    period_start: str | None = None,
    period_end: str | None = None,
) -> list[dict[str, Any]]:
    """
    Process pending marketplace payouts for the current period.

    Calculates revenue share for each blueprint author based on
    installations during the period.
    """
    s = get_settings()

    # Find paid blueprints with active installations
    rows = await conn.fetch("""
        SELECT
            mb.id AS blueprint_id,
            mb.author_tenant_id,
            mb.price_cents,
            mb.revenue_share_pct,
            COUNT(bi.id)::int AS active_installs,
            t.stripe_connect_id
        FROM public.marketplace_blueprints mb
        JOIN public.blueprint_installations bi ON bi.blueprint_id = mb.id AND bi.is_active = true
        JOIN public.tenants t ON t.id = mb.author_tenant_id
        WHERE mb.price_cents > 0
          AND mb.approval_status = 'approved'
          AND t.stripe_connect_id IS NOT NULL
        GROUP BY mb.id, mb.author_tenant_id, mb.price_cents, mb.revenue_share_pct, t.stripe_connect_id
    """)

    if not rows:
        return []

    import stripe
    stripe.api_key = s.stripe_secret_key

    results = []
    stripe_cb = get_protected_stripe()

    for row in rows:
        total_revenue = row["price_cents"] * row["active_installs"]
        author_share = row.get("revenue_share_pct", 70)
        author_amount = int(total_revenue * author_share / 100)
        platform_amount = total_revenue - author_amount

        if author_amount < 100:  # minimum $1.00 payout
            continue

        try:
            # Create Stripe transfer to Connected account
            transfer = stripe_cb.call(
                lambda: stripe.Transfer.create(
                    amount=author_amount,
                    currency="usd",
                    destination=row["stripe_connect_id"],
                    description=f"Sorce marketplace payout - {row['active_installs']} installs",
                    metadata={
                        "blueprint_id": str(row["blueprint_id"]),
                        "author_tenant_id": str(row["author_tenant_id"]),
                        "period": period_end or "current",
                    },
                )
            )

            if not transfer:
                raise RuntimeError("Transfer failed (circuit open)")

            # Record payout
            await conn.execute(
                """
                INSERT INTO public.author_payouts
                    (author_tenant_id, blueprint_id, amount_cents, platform_fee_cents,
                     stripe_transfer_id, status, period_start, period_end)
                VALUES ($1, $2, $3, $4, $5, 'paid', $6::timestamptz, $7::timestamptz)
                """,
                row["author_tenant_id"], row["blueprint_id"],
                author_amount, platform_amount,
                transfer.id,
                period_start or "now()",
                period_end or "now()",
            )

            results.append({
                "blueprint_id": str(row["blueprint_id"]),
                "author_tenant_id": str(row["author_tenant_id"]),
                "installs": row["active_installs"],
                "author_amount_cents": author_amount,
                "platform_fee_cents": platform_amount,
                "transfer_id": transfer.id,
                "status": "paid",
            })

            logger.info(
                "Payout: blueprint=%s author=%s amount=$%.2f",
                row["blueprint_id"], row["author_tenant_id"], author_amount / 100,
            )

        except Exception as exc:
            logger.error("Payout failed for blueprint %s: %s", row["blueprint_id"], exc)
            await conn.execute(
                """
                INSERT INTO public.author_payouts
                    (author_tenant_id, blueprint_id, amount_cents, platform_fee_cents,
                     status, period_start, period_end)
                VALUES ($1, $2, $3, $4, 'failed', $5::timestamptz, $6::timestamptz)
                """,
                row["author_tenant_id"], row["blueprint_id"],
                author_amount, platform_amount,
                period_start or "now()",
                period_end or "now()",
            )
            results.append({
                "blueprint_id": str(row["blueprint_id"]),
                "status": "failed",
                "error": str(exc),
            })

    return results
