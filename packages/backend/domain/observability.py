"""
Observability — Sentry integration, structured error tracking, and automated alerting.

Provides:
  - Sentry SDK initialization with tenant/plan context
  - Structured error capture with tenant metadata
  - Automated alert checks: agent success rate, Stripe failures, quota spikes
"""

from __future__ import annotations

import asyncio
from typing import Any

import asyncpg
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.observability")


# ---------------------------------------------------------------------------
# Sentry initialization
# ---------------------------------------------------------------------------

_sentry_initialized = False


def init_sentry() -> None:
    """Initialize Sentry SDK if configured."""
    global _sentry_initialized
    s = get_settings()
    if not s.sentry_dsn or _sentry_initialized:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.asyncio import AsyncioIntegration

        sentry_sdk.init(
            dsn=s.sentry_dsn,
            environment=s.sentry_environment,
            traces_sample_rate=s.sentry_traces_sample_rate,
            integrations=[AsyncioIntegration()],
            send_default_pii=False,
        )
        _sentry_initialized = True
        logger.info("Sentry initialized (env=%s, sample_rate=%.2f)",
                     s.sentry_environment, s.sentry_traces_sample_rate)
    except ImportError:
        logger.warning("sentry_sdk not installed — Sentry disabled")
    except Exception as exc:
        logger.error("Failed to init Sentry: %s", exc)


def capture_error(
    error: Exception,
    tenant_id: str | None = None,
    plan: str | None = None,
    user_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> str | None:
    """
    Capture an error in Sentry with tenant context.
    Returns the Sentry event ID or None.
    """
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if tenant_id:
                scope.set_tag("tenant_id", tenant_id)
            if plan:
                scope.set_tag("plan", plan)
            if user_id:
                scope.set_user({"id": user_id})
            if extra:
                for k, v in extra.items():
                    scope.set_extra(k, v)
            event_id = sentry_sdk.capture_exception(error)
            return event_id
    except ImportError:
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Alert definitions
# ---------------------------------------------------------------------------

class AlertResult:
    """Result of an alert check."""
    def __init__(self, name: str, level: str, message: str, value: Any = None):
        self.name = name
        self.level = level  # info, warning, critical
        self.message = message
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "message": self.message,
            "value": self.value,
        }


async def get_success_metrics(
    conn: asyncpg.Connection, interval: str, min_samples: int = 10
) -> dict[str, Any] | None:
    """Calculate success rate metrics over a time interval."""
    row = await conn.fetchrow(f"""
        SELECT
            COUNT(*)::int AS total,
            COUNT(*) FILTER (WHERE status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED'))::int AS succeeded
        FROM public.applications
        WHERE created_at >= now() - interval '{interval}'
          AND status NOT IN ('QUEUED', 'PROCESSING')
    """)
    if not row or (row["total"] or 0) < min_samples:
        return None

    total = row["total"]
    succeeded = row["succeeded"] or 0
    return {
        "total": total,
        "succeeded": succeeded,
        "rate": round(succeeded / total * 100, 1),
    }


async def check_agent_success_rate(conn: asyncpg.Connection, threshold: float = 85.0) -> AlertResult | None:
    """Alert if agent success rate drops below threshold (last 24h)."""
    metrics = await get_success_metrics(conn, "24 hours")
    if not metrics:
        return None

    rate = metrics["rate"]
    if rate < threshold:
        return AlertResult(
            "agent_success_rate",
            "critical" if rate < 70 else "warning",
            f"Agent success rate is {rate}% (threshold: {threshold}%)",
            value=rate,
        )
    return None


async def check_stripe_failures(conn: asyncpg.Connection) -> AlertResult | None:
    """Alert if there are recent Stripe payment failures."""
    count = await conn.fetchval("""
        SELECT COUNT(*)::int FROM public.audit_log
        WHERE action LIKE 'billing.payment_failed%'
          AND created_at >= now() - interval '1 hour'
    """) or 0
    if count >= 3:
        return AlertResult(
            "stripe_failures",
            "critical" if count >= 10 else "warning",
            f"{count} Stripe payment failures in the last hour",
            value=count,
        )
    return None


async def check_quota_exhaustion(conn: asyncpg.Connection) -> AlertResult | None:
    """Alert if many tenants are hitting quota limits."""
    count = await conn.fetchval("""
        SELECT COUNT(DISTINCT tenant_id)::int
        FROM public.analytics_events
        WHERE event_type = 'quota_exceeded'
          AND created_at >= now() - interval '1 hour'
    """) or 0
    if count >= 5:
        return AlertResult(
            "quota_exhaustion_spike",
            "warning",
            f"{count} tenants hit quota limits in the last hour",
            value=count,
        )
    return None


async def check_queue_depth(conn: asyncpg.Connection) -> AlertResult | None:
    """Alert if task queue is growing too large."""
    count = await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.applications WHERE status = 'QUEUED'"
    ) or 0
    if count >= 100:
        return AlertResult(
            "queue_depth",
            "critical" if count >= 500 else "warning",
            f"Task queue depth: {count} pending applications",
            value=count,
        )
    return None


async def check_enterprise_sla(conn: asyncpg.Connection) -> AlertResult | None:
    """Alert if enterprise tasks are waiting too long."""
    row = await conn.fetchrow("""
        SELECT
            COUNT(*)::int AS waiting,
            MAX(EXTRACT(EPOCH FROM now() - a.created_at))::int AS max_wait_secs
        FROM public.applications a
        JOIN public.tenant_members tm ON tm.user_id = a.user_id
        JOIN public.tenants t ON t.id = tm.tenant_id
        WHERE a.status = 'QUEUED' AND t.plan = 'ENTERPRISE'
    """)
    if row and (row["waiting"] or 0) > 0 and (row["max_wait_secs"] or 0) > 300:
        return AlertResult(
            "enterprise_sla",
            "critical",
            f"{row['waiting']} enterprise tasks waiting (max wait: {row['max_wait_secs']}s)",
            value=row["max_wait_secs"],
        )
    return None


async def run_all_alerts(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Run all alert checks and return triggered alerts."""
    checks = [
        check_agent_success_rate(conn),
        check_stripe_failures(conn),
        check_quota_exhaustion(conn),
        check_queue_depth(conn),
        check_enterprise_sla(conn),
    ]
    results = await asyncio.gather(*checks, return_exceptions=True)
    alerts = []
    for r in results:
        if isinstance(r, AlertResult):
            alerts.append(r.to_dict())
        elif isinstance(r, Exception):
            logger.error("Alert check failed: %s", r)
    return alerts
