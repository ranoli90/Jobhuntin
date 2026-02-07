"""
M5 Revenue Intelligence — P&L, LTV:CAC, cohort retention,
marketplace revenue, agent performance, and Series A metrics.

Queries materialized views from migration 018.
"""

from __future__ import annotations

from typing import Any

import asyncpg


async def get_pnl(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT * FROM public.mv_m5_pnl ORDER BY month")
    return [dict(r) for r in rows]


async def get_marketplace_revenue(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT * FROM public.mv_marketplace_revenue ORDER BY month")
    return [dict(r) for r in rows]


async def get_cohort_retention(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT * FROM public.mv_cohort_retention ORDER BY cohort_month, month_number")
    return [dict(r) for r in rows]


async def get_agent_performance_weekly(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch("SELECT * FROM public.mv_agent_performance_m5 ORDER BY week DESC, blueprint_key LIMIT 100")
    return [dict(r) for r in rows]


async def get_subscriber_counts(conn: asyncpg.Connection) -> dict[str, int]:
    row = await conn.fetchrow("""
        SELECT
            COUNT(*) FILTER (WHERE plan != 'FREE')::int AS paying,
            COUNT(*) FILTER (WHERE plan = 'PRO')::int AS pro,
            COUNT(*) FILTER (WHERE plan = 'TEAM')::int AS team,
            COUNT(*) FILTER (WHERE plan = 'ENTERPRISE')::int AS enterprise,
            COUNT(*)::int AS total
        FROM public.tenants
    """)
    return dict(row)


async def get_churn_rate(conn: asyncpg.Connection, days: int = 30) -> dict[str, Any]:
    """Monthly churn rate: tenants that downgraded to FREE in last N days / total paying."""
    churned = await conn.fetchval("""
        SELECT COUNT(*)::int FROM public.audit_log
        WHERE action = 'billing.changed' AND details->>'new_plan' = 'FREE'
          AND created_at >= now() - ($1 || ' days')::interval
    """, str(days)) or 0

    paying = await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.tenants WHERE plan != 'FREE'"
    ) or 1

    rate = round(churned / max(paying, 1) * 100, 2)
    return {"churned": churned, "paying": paying, "churn_rate_pct": rate, "period_days": days}


async def get_ltv_cac_detailed(conn: asyncpg.Connection) -> dict[str, Any]:
    """Detailed LTV:CAC with per-plan breakdown."""
    from backend.domain.m4_metrics import get_ltv_cac_estimate
    base = await get_ltv_cac_estimate(conn)

    # Per-plan ARPU
    plan_arpu = await conn.fetch("""
        SELECT plan::text,
               COUNT(*)::int AS count,
               AVG(CASE
                   WHEN plan = 'PRO' THEN 29
                   WHEN plan = 'TEAM' THEN 199 + GREATEST(seat_count - 3, 0) * 49
                   WHEN plan = 'ENTERPRISE' THEN COALESCE(contract_value_cents / 100, 999)
                   ELSE 0
               END)::numeric AS arpu
        FROM public.tenants WHERE plan != 'FREE'
        GROUP BY plan
    """)

    base["per_plan"] = [dict(r) for r in plan_arpu]
    return base


async def get_gross_margin(conn: asyncpg.Connection) -> dict[str, Any]:
    """Compute gross margin from P&L data."""
    pnl = await get_pnl(conn)
    if not pnl:
        return {"total_mrr": 0, "total_cogs": 0, "gross_margin_pct": 0}

    latest = pnl[-1]
    total_mrr = latest.get("total_mrr", 0)
    cogs = latest.get("estimated_cogs", 0)
    margin = round((total_mrr - cogs) / max(total_mrr, 1) * 100, 1) if total_mrr > 0 else 0

    return {
        "month": str(latest.get("month", "")),
        "total_mrr": total_mrr,
        "estimated_cogs": cogs,
        "gross_profit": total_mrr - cogs,
        "gross_margin_pct": margin,
    }


async def get_m5_dashboard(conn: asyncpg.Connection) -> dict[str, Any]:
    """Complete M5 revenue intelligence dashboard."""
    from backend.domain.m4_metrics import get_m4_dashboard

    m4 = await get_m4_dashboard(conn)
    pnl = await get_pnl(conn)
    marketplace_rev = await get_marketplace_revenue(conn)
    cohort_ret = await get_cohort_retention(conn)
    agent_perf = await get_agent_performance_weekly(conn)
    subs = await get_subscriber_counts(conn)
    churn = await get_churn_rate(conn)
    ltv_cac = await get_ltv_cac_detailed(conn)
    margin = await get_gross_margin(conn)

    # M5 success criteria
    total_mrr = m4.get("ltv_cac", {}).get("total_mrr", 0)
    m5_targets = {
        "mrr_target": 83_000,
        "mrr_current": total_mrr,
        "mrr_on_track": total_mrr >= 83_000,
        "subscribers_target": 5_000,
        "subscribers_current": subs.get("paying", 0),
        "team_accounts_target": 100,
        "team_accounts_current": subs.get("team", 0),
        "enterprise_target": 5,
        "enterprise_current": subs.get("enterprise", 0),
        "ltv_cac_target": 3.0,
        "ltv_cac_current": ltv_cac.get("ltv_cac_ratio", 0),
        "churn_target_pct": 4.0,
        "churn_current_pct": churn.get("churn_rate_pct", 0),
        "agent_success_target": 90,
        "agent_success_current": agent_perf[0].get("success_rate", 0) if agent_perf else 0,
    }

    return {
        **m4,
        "pnl": pnl,
        "marketplace_revenue": marketplace_rev,
        "cohort_retention": cohort_ret,
        "agent_performance_weekly": agent_perf,
        "subscriber_counts": subs,
        "churn": churn,
        "ltv_cac_detailed": ltv_cac,
        "gross_margin": margin,
        "m5_targets": m5_targets,
    }


async def get_investor_metrics(conn: asyncpg.Connection) -> dict[str, Any]:
    """
    Series A metrics export — clean JSON for pitch deck.
    Covers: MRR, ARR, growth, churn, LTV:CAC, NRR, gross margin,
    subscriber counts, agent performance, marketplace traction.
    """
    subs = await get_subscriber_counts(conn)
    churn = await get_churn_rate(conn)
    ltv_cac = await get_ltv_cac_detailed(conn)
    margin = await get_gross_margin(conn)
    pnl = await get_pnl(conn)
    marketplace_rev = await get_marketplace_revenue(conn)
    agent_perf = await get_agent_performance_weekly(conn)

    total_mrr = ltv_cac.get("total_mrr", 0)
    arr = total_mrr * 12

    # MRR growth (latest 2 months)
    mrr_growth = 0
    if len(pnl) >= 2:
        prev = pnl[-2].get("total_mrr", 0)
        curr = pnl[-1].get("total_mrr", 0)
        if prev > 0:
            mrr_growth = round((curr - prev) / prev * 100, 1)

    return {
        "company": "Sorce",
        "period": "M5 — Series A Metrics",
        "generated_at": None,  # set by endpoint
        "financials": {
            "mrr": total_mrr,
            "arr": arr,
            "mrr_growth_mom_pct": mrr_growth,
            "gross_margin_pct": margin.get("gross_margin_pct", 0),
            "estimated_cogs": margin.get("estimated_cogs", 0),
            "net_revenue_retention_pct": None,  # from M4 NRR view
        },
        "customers": {
            "total_tenants": subs.get("total", 0),
            "paying_subscribers": subs.get("paying", 0),
            "pro": subs.get("pro", 0),
            "team": subs.get("team", 0),
            "enterprise": subs.get("enterprise", 0),
        },
        "unit_economics": {
            "arpu": ltv_cac.get("arpu", 0),
            "ltv": ltv_cac.get("estimated_ltv", 0),
            "cac": ltv_cac.get("estimated_cac", 0),
            "ltv_cac_ratio": ltv_cac.get("ltv_cac_ratio", 0),
            "monthly_churn_pct": churn.get("churn_rate_pct", 0),
            "payback_months": round(ltv_cac.get("estimated_cac", 0) / max(ltv_cac.get("arpu", 1), 1), 1),
        },
        "product": {
            "agent_success_rate_pct": agent_perf[0].get("success_rate", 0) if agent_perf else 0,
            "total_applications_processed": sum(r.get("total", 0) for r in agent_perf),
            "marketplace_blueprints": None,  # filled by endpoint
            "marketplace_platform_revenue": sum(r.get("platform_fee_cents", 0) for r in marketplace_rev),
        },
        "mrr_history": [
            {"month": str(p.get("month", "")), "mrr": p.get("total_mrr", 0)}
            for p in pnl[-12:]
        ],
    }


async def refresh_m5_views(conn: asyncpg.Connection) -> None:
    """Refresh all M1–M5 materialized views."""
    from backend.domain.m4_metrics import refresh_m4_views
    await refresh_m4_views(conn)
    await conn.execute("SELECT public.refresh_m5_views()")
