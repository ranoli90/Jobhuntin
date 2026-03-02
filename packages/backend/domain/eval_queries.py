"""Aggregation queries for agent performance metrics.

Provides SQL-based analytics over agent_evaluations, applications, and
application_inputs to surface success rates, failure distributions, and
hold-question frequency.
"""

from __future__ import annotations

from typing import Any

import asyncpg

# ---------------------------------------------------------------------------
# Success rate per tenant / blueprint / week
# ---------------------------------------------------------------------------

AGENT_SUCCESS_RATE_SQL = """
SELECT
    a.tenant_id,
    a.blueprint_key,
    date_trunc('week', e.created_at) AS week,
    e.label,
    COUNT(*)::int AS count
FROM public.agent_evaluations e
JOIN public.applications a ON a.id = e.application_id
WHERE e.source = 'SYSTEM'
  AND ($1::uuid IS NULL OR a.tenant_id = $1)
  AND ($2::text IS NULL OR a.blueprint_key = $2)
  AND e.created_at >= COALESCE($3::timestamptz, '2000-01-01')
  AND e.created_at < COALESCE($4::timestamptz, '2100-01-01')
GROUP BY a.tenant_id, a.blueprint_key, week, e.label
ORDER BY week DESC, a.tenant_id, a.blueprint_key, e.label
"""


async def get_success_rate_breakdown(
    conn: asyncpg.Connection,
    tenant_id: str | None = None,
    blueprint_key: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """Return success/partial/failure counts grouped by tenant, blueprint, week."""
    rows = await conn.fetch(
        AGENT_SUCCESS_RATE_SQL,
        tenant_id,
        blueprint_key,
        date_from,
        date_to,
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Average hold questions per application
# ---------------------------------------------------------------------------

AVG_HOLD_QUESTIONS_SQL = """
SELECT
    a.tenant_id,
    a.blueprint_key,
    COUNT(DISTINCT a.id)::int AS application_count,
    COUNT(i.id)::int AS total_hold_questions,
    ROUND(COUNT(i.id)::numeric / NULLIF(COUNT(DISTINCT a.id), 0), 2) AS avg_hold_questions
FROM public.applications a
LEFT JOIN public.application_inputs i ON i.application_id = a.id
WHERE ($1::uuid IS NULL OR a.tenant_id = $1)
  AND ($2::text IS NULL OR a.blueprint_key = $2)
  AND a.created_at >= COALESCE($3::timestamptz, '2000-01-01')
  AND a.created_at < COALESCE($4::timestamptz, '2100-01-01')
GROUP BY a.tenant_id, a.blueprint_key
ORDER BY a.tenant_id, a.blueprint_key
"""


async def get_avg_hold_questions(
    conn: asyncpg.Connection,
    tenant_id: str | None = None,
    blueprint_key: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """Return average hold questions per application grouped by tenant + blueprint."""
    rows = await conn.fetch(
        AVG_HOLD_QUESTIONS_SQL,
        tenant_id,
        blueprint_key,
        date_from,
        date_to,
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Failure reason distribution
# ---------------------------------------------------------------------------

FAILURE_REASONS_SQL = """
SELECT
    e.reason,
    COUNT(*)::int AS count
FROM public.agent_evaluations e
JOIN public.applications a ON a.id = e.application_id
WHERE e.source = 'SYSTEM'
  AND e.label = 'FAILURE'
  AND ($1::uuid IS NULL OR a.tenant_id = $1)
  AND ($2::text IS NULL OR a.blueprint_key = $2)
  AND e.created_at >= COALESCE($3::timestamptz, '2000-01-01')
  AND e.created_at < COALESCE($4::timestamptz, '2100-01-01')
GROUP BY e.reason
ORDER BY count DESC
LIMIT 50
"""


async def get_failure_reasons(
    conn: asyncpg.Connection,
    tenant_id: str | None = None,
    blueprint_key: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """Return top failure reasons with counts."""
    rows = await conn.fetch(
        FAILURE_REASONS_SQL,
        tenant_id,
        blueprint_key,
        date_from,
        date_to,
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Combined performance summary
# ---------------------------------------------------------------------------

async def get_agent_performance_summary(
    conn: asyncpg.Connection,
    tenant_id: str | None = None,
    blueprint_key: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """Return a combined performance summary dict."""
    success_rates = await get_success_rate_breakdown(
        conn, tenant_id, blueprint_key, date_from, date_to,
    )
    hold_questions = await get_avg_hold_questions(
        conn, tenant_id, blueprint_key, date_from, date_to,
    )
    failure_reasons = await get_failure_reasons(
        conn, tenant_id, blueprint_key, date_from, date_to,
    )
    return {
        "success_rate_breakdown": success_rates,
        "avg_hold_questions": hold_questions,
        "top_failure_reasons": failure_reasons,
    }
