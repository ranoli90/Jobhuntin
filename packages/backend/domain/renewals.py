"""
Contract Renewal Automation — 90/60/30-day Slack/email notification sequences,
auto-invoice via Stripe, churn tracking.

Designed to run daily via cron: `python -m backend.domain.renewals`
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import asyncpg

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.renewals")


async def scan_upcoming_renewals(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Find contracts approaching renewal and create/update tracking records."""
    now = datetime.now(UTC)
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
    now = datetime.now(UTC)
    notifications: list[dict[str, Any]] = []

    renewals = await conn.fetch("""
        SELECT cr.*, t.name AS tenant_name, t.plan::text AS plan
        FROM public.contract_renewals cr
        JOIN public.tenants t ON t.id = cr.tenant_id
        WHERE cr.status NOT IN ('renewed', 'churned')
        ORDER BY cr.renewal_date ASC
    """)

    for renewal in renewals:
        status_update = _determine_renewal_status(renewal, now)
        if status_update:
            days_until, new_status = status_update
            notif = await _send_renewal_notification(conn, renewal, days_until, new_status, now)
            notifications.append(notif)

    return notifications


def _determine_renewal_status(renewal: dict, now: datetime) -> tuple[int, str] | None:
    """Determine if a notification is needed and return (days_until, new_status)."""
    days_until = (renewal["renewal_date"] - now).days
    current_status = renewal["status"]

    if days_until <= 30 and current_status != "notified_30":
        return days_until, "notified_30"
    if days_until <= 60 and current_status not in ("notified_30", "notified_60"):
        return days_until, "notified_60"
    if days_until <= 90 and current_status == "upcoming":
        return days_until, "notified_90"

    return None


async def _send_renewal_notification(
    conn: asyncpg.Connection,
    renewal: asyncpg.Record,
    days_until: int,
    new_status: str,
    now: datetime,
) -> dict[str, Any]:
    """Helper to send notification and update renewal status."""
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

    logger.info("Renewal notification: %s — %d days — %s", renewal["tenant_name"], days_until, new_status)

    return {
        "tenant": renewal["tenant_name"],
        "plan": renewal["plan"],
        "days_until": days_until,
        "status": new_status,
        "value": value,
    }


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
