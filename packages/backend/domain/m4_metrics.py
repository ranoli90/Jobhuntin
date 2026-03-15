"""M4 enterprise analytics — scale to $100k MRR.

Queries materialized views from migration 016 for:
  - MRR cohort analysis
  - Expansion revenue tracking
  - Churn prediction with risk levels
  - Net revenue retention (NRR)
  - Enterprise pipeline
  - LTV:CAC ratio estimation
"""

from __future__ import annotations

from typing import Any

import asyncpg


async def get_mrr_cohorts(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT * FROM public.mv_mrr_cohorts ORDER BY cohort_month")
    return [dict(r) for r in rows]


async def get_expansion_revenue(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT * FROM public.mv_expansion_revenue ORDER BY month")
    return [dict(r) for r in rows]


async def get_churn_prediction(
    conn: asyncpg.Connection, limit: int = 30
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        "SELECT * FROM public.mv_churn_prediction ORDER BY churn_risk_level DESC, "
        "days_since_last_activity DESC LIMIT $1",
        limit,
    )
    return [dict(r) for r in rows]


async def get_nrr_monthly(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT * FROM public.mv_nrr_monthly ORDER BY month")
    return [dict(r) for r in rows]


async def get_enterprise_pipeline(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT * FROM public.mv_enterprise_pipeline")
    return [dict(r) for r in rows]


async def get_ltv_cac_estimate(conn: asyncpg.Connection) -> dict[str, Any]:
    """Estimate LTV:CAC ratio from available data.

    LTV = ARPU × gross margin / monthly churn rate
    CAC approximated from marketing spend (stub: hardcoded placeholder).
    """
    # Current ARPU
    arpu_row = await conn.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE plan != 'FREE')::int AS paying_tenants,
            SUM(CASE
                WHEN plan = 'PRO' THEN 29
                WHEN plan = 'TEAM' THEN 199 + GREATEST(seat_count - 3, 0) * 49
                WHEN plan = 'ENTERPRISE' THEN 999
                ELSE 0
            END)::int AS total_mrr
        FROM public.tenants
        WHERE plan != 'FREE'
    """
    )

    paying = arpu_row["paying_tenants"] or 1
    total_mrr = arpu_row["total_mrr"] or 0
    arpu = round(total_mrr / max(paying, 1), 2)

    # Churn rate approximation (tenants that went FREE in last 30 days / total paying)
    churned = (
        await conn.fetchval(
            """
        SELECT COUNT(*)::int FROM public.audit_log
        WHERE action = 'billing.changed'
          AND details->>'new_plan' = 'FREE'
          AND created_at >= now() - interval '30 days'
    """
        )
        or 0
    )
    monthly_churn_rate = round(churned / max(paying, 1), 4)

    gross_margin = 0.85  # 85% assumed
    ltv = round(arpu * gross_margin / max(monthly_churn_rate, 0.01), 2)
    cac = 150  # Stub: would come from marketing spend tracking
    ltv_cac_ratio = round(ltv / max(cac, 1), 2)

    return {
        "arpu": arpu,
        "paying_tenants": paying,
        "total_mrr": total_mrr,
        "monthly_churn_rate": monthly_churn_rate,
        "churned_last_30d": churned,
        "estimated_ltv": ltv,
        "estimated_cac": cac,
        "ltv_cac_ratio": ltv_cac_ratio,
        "gross_margin": gross_margin,
    }


async def get_m4_dashboard(conn: asyncpg.Connection) -> dict[str, Any]:
    """Return the complete M4 enterprise analytics dashboard."""
    # Import M3 for base metrics
    from packages.backend.domain.m3_metrics import get_m3_dashboard

    m3 = await get_m3_dashboard(conn)
    cohorts = await get_mrr_cohorts(conn)
    expansion = await get_expansion_revenue(conn)
    churn = await get_churn_prediction(conn)
    nrr = await get_nrr_monthly(conn)
    pipeline = await get_enterprise_pipeline(conn)
    ltv_cac = await get_ltv_cac_estimate(conn)

    # M4 targets
    m4_targets = {
        "mau_target": 30_000,
        "mau_current": m3.get("active_users", {}).get("mau", 0),
        "mrr_target": 100_000,
        "mrr_current": m3.get("total_mrr", 0),
        "subscribers_target": 2_000,
        "subscribers_current": sum(
            r.get("tenant_count", 0)
            for r in m3.get("mrr_by_plan", [])
            if r.get("plan") != "FREE"
        ),
        "team_accounts_target": 50,
        "team_accounts_current": m3.get("team_metrics", {}).get("total_teams", 0),
        "enterprise_pilots_target": 3,
        "enterprise_pilots_current": len(
            [p for p in pipeline if p.get("plan") == "ENTERPRISE"]
        ),
        "nrr_target": 110,
        "nrr_current": nrr[-1]["nrr_pct"] if nrr and nrr[-1].get("nrr_pct") else 0,
    }

    # Churn risk summary
    churn_summary = {
        "high_risk": len([c for c in churn if c.get("churn_risk_level") == "high"]),
        "medium_risk": len([c for c in churn if c.get("churn_risk_level") == "medium"]),
        "low_risk": len([c for c in churn if c.get("churn_risk_level") == "low"]),
        "total_mrr_at_risk": sum(
            c.get("mrr_at_risk", 0)
            for c in churn
            if c.get("churn_risk_level") in ("high", "medium")
        ),
    }

    return {
        **m3,
        "mrr_cohorts": cohorts,
        "expansion_revenue": expansion,
        "churn_prediction": churn,
        "churn_summary": churn_summary,
        "nrr_monthly": nrr,
        "enterprise_pipeline": pipeline,
        "ltv_cac": ltv_cac,
        "m4_targets": m4_targets,
    }


async def refresh_m4_views(conn: asyncpg.Connection) -> None:
    """Refresh all M1–M4 materialized views."""
    await conn.execute("SELECT public.refresh_m1_dashboard()")
    await conn.execute("SELECT public.refresh_m2_views()")
    await conn.execute("SELECT public.refresh_m3_views()")
    await conn.execute("SELECT public.refresh_m4_views()")
