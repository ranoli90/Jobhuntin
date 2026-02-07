"""
Contract Renewal Automation — 90/60/30-day Slack/email notification sequences,
auto-invoice via Stripe, churn tracking.

Designed to run daily via cron: `python -m backend.domain.renewals`
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.renewals")


async def scan_upcoming_renewals(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Find contracts approaching renewal and create/update tracking records."""
    now = datetime.now(timezone.utc)
    d90 = now + timedelta(days=90)

    # Find tenants with contract_end within 90 days that don't have a renewal record
    rows = await conn.fetch("""
        SELECT t.id AS tenant_id, t.name, t.plan::text, t.contract_end,
               t.contract_value_cents, t.billing_interval
        FROM public.tenants t
        WHERE t.contract_end IS NOT NULL
          AND t.contract_end <= $1
          AND t.contract_end > now()
          AND t.plan IN ('TEAM', 'ENTERPRISE')
          AND NOT EXISTS (
              SELECT 1 FROM public.contract_renewals cr
              WHERE cr.tenant_id = t.id AND cr.renewal_date = t.contract_end
          )
    """, d90)

    created = []
    for row in rows:
        await conn.execute(
            """INSERT INTO public.contract_renewals
                   (tenant_id, renewal_date, contract_value, status)
               VALUES ($1, $2, $3, 'upcoming')""",
            row["tenant_id"], row["contract_end"], row["contract_value_cents"] or 0,
        )
        created.append(dict(row))
        logger.info("Created renewal tracking: tenant=%s date=%s", row["name"], row["contract_end"])

    return created


async def run_notification_sequence(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """
    Check all upcoming renewals and send notifications at 90/60/30 day marks.
    Updates renewal status and notification_log.
    """
    now = datetime.now(timezone.utc)
    notifications: list[dict[str, Any]] = []

    renewals = await conn.fetch("""
        SELECT cr.*, t.name AS tenant_name, t.plan::text AS plan
        FROM public.contract_renewals cr
        JOIN public.tenants t ON t.id = cr.tenant_id
        WHERE cr.status NOT IN ('renewed', 'churned')
        ORDER BY cr.renewal_date ASC
    """)

    for renewal in renewals:
        days_until = (renewal["renewal_date"] - now).days
        current_status = renewal["status"]
        new_status = current_status
        should_notify = False

        if days_until <= 30 and current_status != "notified_30":
            new_status = "notified_30"
            should_notify = True
        elif days_until <= 60 and current_status not in ("notified_30", "notified_60"):
            new_status = "notified_60"
            should_notify = True
        elif days_until <= 90 and current_status == "upcoming":
            new_status = "notified_90"
            should_notify = True

        if should_notify:
            # Build notification
            value = (renewal["contract_value"] or 0) / 100
            msg = (
                f"{'🔴' if days_until <= 30 else '🟡' if days_until <= 60 else '🟢'} "
                f"*Contract Renewal*: {renewal['tenant_name']} ({renewal['plan']}) — "
                f"${value:,.0f}/yr renews in {days_until} days "
                f"({renewal['renewal_date'].strftime('%Y-%m-%d')})"
            )

            # Send Slack notification
            from backend.domain.alerting_v2 import send_slack_message
            await send_slack_message(
                text=msg,
                channel=get_settings().slack_enterprise_channel,
            )

            # Update log
            log = json.loads(renewal["notification_log"]) if isinstance(renewal["notification_log"], str) else list(renewal["notification_log"] or [])
            log.append({
                "status": new_status,
                "days_until_renewal": days_until,
                "notified_at": now.isoformat(),
                "channel": "slack",
            })

            await conn.execute(
                """UPDATE public.contract_renewals
                   SET status = $2, notification_log = $3::jsonb
                   WHERE id = $1""",
                renewal["id"], new_status, json.dumps(log),
            )

            notifications.append({
                "tenant": renewal["tenant_name"],
                "plan": renewal["plan"],
                "days_until": days_until,
                "status": new_status,
                "value": value,
            })

            logger.info("Renewal notification: %s — %d days — %s", renewal["tenant_name"], days_until, new_status)

    return notifications


async def auto_create_renewal_invoice(
    conn: asyncpg.Connection,
    tenant_id: str,
) -> dict[str, Any] | None:
    """
    Auto-create a Stripe invoice for contract renewal.
    Called when a renewal is approved or auto-renewed.
    """
    s = get_settings()
    if not s.stripe_secret_key:
        logger.warning("Stripe not configured — skipping auto-invoice")
        return None

    tenant = await conn.fetchrow(
        """SELECT t.*, bc.stripe_customer_id
           FROM public.tenants t
           LEFT JOIN public.billing_customers bc ON bc.tenant_id = t.id
           WHERE t.id = $1""",
        tenant_id,
    )
    if not tenant or not tenant["stripe_customer_id"]:
        logger.warning("No Stripe customer for tenant %s", tenant_id)
        return None

    try:
        import stripe
        stripe.api_key = s.stripe_secret_key

        contract_value = (tenant["contract_value_cents"] or 0)
        if contract_value <= 0:
            return None

        # Create invoice
        invoice = stripe.Invoice.create(
            customer=tenant["stripe_customer_id"],
            collection_method="send_invoice",
            days_until_due=30,
            description=f"Contract Renewal — {tenant['name']} ({tenant['plan']})",
            metadata={"tenant_id": str(tenant_id), "type": "renewal"},
        )

        # Add line item
        stripe.InvoiceItem.create(
            customer=tenant["stripe_customer_id"],
            invoice=invoice.id,
            amount=contract_value,
            currency="usd",
            description=f"Annual contract renewal — {tenant['plan']} plan",
        )

        # Finalize and send
        stripe.Invoice.finalize_invoice(invoice.id)
        stripe.Invoice.send_invoice(invoice.id)

        # Update renewal status
        await conn.execute(
            """UPDATE public.contract_renewals
               SET status = 'renewed'
               WHERE tenant_id = $1 AND status != 'renewed'
               ORDER BY renewal_date ASC LIMIT 1""",
            tenant_id,
        )

        # Extend contract
        new_end = tenant["contract_end"] + timedelta(days=365) if tenant["contract_end"] else None
        if new_end:
            await conn.execute(
                "UPDATE public.tenants SET contract_start = contract_end, contract_end = $2 WHERE id = $1",
                tenant_id, new_end,
            )

        logger.info("Auto-renewal invoice created: tenant=%s invoice=%s amount=$%.2f",
                     tenant["name"], invoice.id, contract_value / 100)

        return {
            "tenant_id": str(tenant_id),
            "invoice_id": invoice.id,
            "amount_cents": contract_value,
            "status": "sent",
        }

    except Exception as exc:
        logger.error("Auto-renewal invoice failed for %s: %s", tenant_id, exc)
        return None


async def run_renewal_cycle(conn: asyncpg.Connection) -> dict[str, Any]:
    """
    Full renewal cycle — run daily via cron.
    1. Scan for upcoming renewals
    2. Send 90/60/30-day notifications
    """
    new_renewals = await scan_upcoming_renewals(conn)
    notifications = await run_notification_sequence(conn)

    return {
        "new_renewals_tracked": len(new_renewals),
        "notifications_sent": len(notifications),
        "notifications": notifications,
    }
