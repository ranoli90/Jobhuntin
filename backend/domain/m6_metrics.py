"""
M6 Platform Metrics — ARR by vertical, API usage, integrator stats,
staffing performance, university ROI, and full investor data room.

Queries materialized views from migration 020.
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

import asyncpg


async def get_arr_by_vertical(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Get ARR breakdown by vertical."""
    rows = await conn.fetch("SELECT * FROM public.mv_arr_by_vertical ORDER BY total_mrr DESC")
    return [dict(r) for r in rows]


async def get_api_v2_usage(conn: asyncpg.Connection, days: int = 30) -> list[dict[str, Any]]:
    """Get API usage metrics for the last N days."""
    rows = await conn.fetch(
        "SELECT * FROM public.mv_api_v2_usage WHERE day >= CURRENT_DATE - $1 ORDER BY day DESC, calls DESC",
        days,
    )
    return [dict(r) for r in rows]


async def get_blueprint_heatmap(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Get blueprint installation heatmap data."""
    rows = await conn.fetch("SELECT * FROM public.mv_blueprint_heatmap ORDER BY week DESC, installs DESC LIMIT 200")
    return [dict(r) for r in rows]


async def get_revenue_per_blueprint(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Get revenue generated per blueprint."""
    rows = await conn.fetch("SELECT * FROM public.mv_revenue_per_blueprint ORDER BY gross_revenue_cents DESC")
    return [dict(r) for r in rows]


async def get_staffing_performance(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Get staffing agency performance metrics."""
    rows = await conn.fetch("SELECT * FROM public.mv_staffing_performance ORDER BY week DESC LIMIT 52")
    return [dict(r) for r in rows]


async def get_university_roi(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Get university partner ROI metrics."""
    rows = await conn.fetch("SELECT * FROM public.mv_university_roi")
    return [dict(r) for r in rows]


async def get_integrator_stats(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Get statistics for API integrators."""
    rows = await conn.fetch("SELECT * FROM public.mv_integrator_stats ORDER BY total_calls DESC")
    return [dict(r) for r in rows]


async def get_contract_renewals(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Get upcoming contract renewals."""
    rows = await conn.fetch("""
        SELECT cr.*, t.name AS tenant_name, t.plan::text AS plan
        FROM public.contract_renewals cr
        JOIN public.tenants t ON t.id = cr.tenant_id
        WHERE cr.status NOT IN ('renewed', 'churned')
        ORDER BY cr.renewal_date ASC
    """)
    return [dict(r) for r in rows]


async def get_platform_summary(conn: asyncpg.Connection) -> dict[str, Any]:
    """High-level platform summary for M6 dashboard header."""
    row = await conn.fetchrow("""
        SELECT
            (SELECT COUNT(*)::int FROM public.tenants WHERE plan != 'FREE') AS paying_tenants,
            (SELECT COUNT(*)::int FROM public.api_keys WHERE is_active = true) AS active_api_keys,
            (SELECT COUNT(DISTINCT tenant_id)::int FROM public.api_usage
             WHERE created_at >= now() - interval '30 days') AS api_active_tenants,
            (SELECT COUNT(*)::int FROM public.marketplace_blueprints
             WHERE approval_status = 'approved') AS marketplace_blueprints,
            (SELECT COUNT(*)::int FROM public.blueprint_installations
             WHERE is_active = true) AS active_installations,
            (SELECT COUNT(*)::int FROM public.university_partners
             WHERE is_active = true) AS university_partners,
            (SELECT SUM(total_students)::int FROM public.university_partners) AS total_students,
            (SELECT COUNT(*)::int FROM public.staffing_batches
             WHERE created_at >= now() - interval '30 days') AS staffing_batches_30d,
            (SELECT COUNT(*)::int FROM public.webhook_endpoints
             WHERE is_active = true) AS active_webhooks
    """)
    return dict(row) if row else {}


async def get_m6_dashboard(conn: asyncpg.Connection) -> dict[str, Any]:
    """Complete M6 platform dashboard."""
    from backend.domain.m5_metrics import get_m5_dashboard

    m5 = await get_m5_dashboard(conn)
    summary = await get_platform_summary(conn)
    arr_vertical = await get_arr_by_vertical(conn)
    api_usage = await get_api_v2_usage(conn, 30)
    bp_heatmap = await get_blueprint_heatmap(conn)
    bp_revenue = await get_revenue_per_blueprint(conn)
    staffing = await get_staffing_performance(conn)
    uni_roi = await get_university_roi(conn)
    integrators = await get_integrator_stats(conn)
    renewals = await get_contract_renewals(conn)

    # M6 target tracking
    total_arr = sum(v.get("total_arr", 0) for v in arr_vertical)
    enterprise_count = sum(v.get("enterprise_count", 0) for v in arr_vertical)
    integrator_count = len([i for i in integrators if i.get("total_calls", 0) > 0])
    staffing_mrr = sum(s.get("revenue_cents", 0) for s in staffing[:4]) // 100  # last month

    m6_targets = {
        "enterprise_contract_target": 50000,
        "enterprise_max_acv": max(
            (r.get("contract_value", 0) for r in renewals), default=0
        ),
        "enterprise_count": enterprise_count,
        "adjacent_vertical_mrr_target": 10000,
        "staffing_mrr_current": staffing_mrr,
        "integrators_target": 3,
        "integrators_current": integrator_count,
        "arr_target": 2000000,
        "arr_current": total_arr,
        "arr_on_track": total_arr >= 2000000,
    }

    return {
        **m5,
        "platform_summary": summary,
        "arr_by_vertical": arr_vertical,
        "api_v2_usage": api_usage,
        "blueprint_heatmap": bp_heatmap,
        "revenue_per_blueprint": bp_revenue,
        "staffing_performance": staffing,
        "university_roi": uni_roi,
        "integrator_stats": integrators,
        "contract_renewals": renewals,
        "m6_targets": m6_targets,
    }


async def get_full_investor_metrics(conn: asyncpg.Connection) -> dict[str, Any]:
    """
    Full Series A data room — comprehensive diligence package.
    Extends M5 investor metrics with platform-level data.
    """
    from datetime import datetime

    from backend.domain.m5_metrics import get_investor_metrics

    base = await get_investor_metrics(conn)
    arr_vertical = await get_arr_by_vertical(conn)
    integrators = await get_integrator_stats(conn)
    staffing = await get_staffing_performance(conn)
    uni_roi = await get_university_roi(conn)
    bp_revenue = await get_revenue_per_blueprint(conn)
    summary = await get_platform_summary(conn)

    base["generated_at"] = datetime.now(UTC).isoformat()

    # Platform data
    base["platform"] = {
        "active_api_keys": summary.get("active_api_keys", 0),
        "api_active_tenants_30d": summary.get("api_active_tenants", 0),
        "marketplace_blueprints": summary.get("marketplace_blueprints", 0),
        "active_installations": summary.get("active_installations", 0),
        "active_webhooks": summary.get("active_webhooks", 0),
        "integrators": len([i for i in integrators if i.get("total_calls", 0) > 0]),
    }

    # Vertical breakdown
    base["verticals"] = [
        {
            "vertical": v.get("vertical", ""),
            "tenant_count": v.get("tenant_count", 0),
            "mrr": v.get("total_mrr", 0),
            "arr": v.get("total_arr", 0),
            "enterprise_count": v.get("enterprise_count", 0),
        }
        for v in arr_vertical
    ]

    # Staffing agency vertical
    staffing_revenue = sum(s.get("revenue_cents", 0) for s in staffing) // 100
    base["staffing_vertical"] = {
        "total_batches": sum(s.get("total_batches", 0) for s in staffing),
        "total_candidates_submitted": sum(s.get("total_candidates", 0) for s in staffing),
        "success_rate_pct": staffing[0].get("success_rate", 0) if staffing else 0,
        "revenue": staffing_revenue,
        "unique_agencies": max((s.get("unique_agencies", 0) for s in staffing), default=0),
    }

    # University partnerships
    base["university_partnerships"] = {
        "partner_count": summary.get("university_partners", 0),
        "total_students": summary.get("total_students", 0),
        "partners": [
            {"name": u.get("name", ""), "students": u.get("total_students", 0), "pro_upgrades": u.get("pro_upgrades", 0)}
            for u in uni_roi
        ],
    }

    # Marketplace economics
    total_platform_rev = sum(b.get("platform_revenue_cents", 0) for b in bp_revenue) // 100
    base["marketplace_economics"] = {
        "total_paid_blueprints": len(bp_revenue),
        "gross_revenue": sum(b.get("gross_revenue_cents", 0) for b in bp_revenue) // 100,
        "platform_revenue": total_platform_rev,
        "author_revenue": sum(b.get("author_revenue_cents", 0) for b in bp_revenue) // 100,
        "top_blueprints": [
            {"name": b.get("name", ""), "installs": b.get("install_count", 0), "revenue": b.get("gross_revenue_cents", 0) // 100}
            for b in bp_revenue[:5]
        ],
    }

    return base


async def refresh_m6_views(conn: asyncpg.Connection) -> None:
    """Refresh all M1–M6 materialized views."""
    from backend.domain.m5_metrics import refresh_m5_views
    await refresh_m5_views(conn)
    await conn.execute("SELECT public.refresh_m6_views()")
