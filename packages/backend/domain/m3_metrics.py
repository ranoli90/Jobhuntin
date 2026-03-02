"""M3 team + vertical expansion metrics.

Queries materialized views from migration 014 for:
  - Team metrics (seats, MRR, team count)
  - Blueprint performance (job-app vs grant success rates)
  - MRR by plan breakdown
  - Churn risk (inactive paying tenants)
  - Team vs individual usage comparison
"""

from __future__ import annotations

from typing import Any

import asyncpg


async def get_team_metrics(conn: asyncpg.Connection) -> dict[str, Any]:
    """Return aggregated team metrics."""
    row = await conn.fetchrow("SELECT * FROM public.mv_team_metrics")
    if not row:
        return {
            "total_teams": 0, "total_team_seats": 0,
            "teams_with_3_plus": 0, "avg_seats_per_team": 0, "team_mrr": 0,
        }
    return dict(row)


async def get_blueprint_performance(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Return per-blueprint performance stats (last 30 days)."""
    rows = await conn.fetch(
        "SELECT * FROM public.mv_blueprint_performance ORDER BY total DESC"
    )
    return [dict(r) for r in rows]


async def get_mrr_by_plan(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Return MRR breakdown by plan tier."""
    rows = await conn.fetch(
        "SELECT * FROM public.mv_mrr_by_plan ORDER BY plan_mrr DESC"
    )
    return [dict(r) for r in rows]


async def get_churn_risk(conn: asyncpg.Connection, limit: int = 20) -> list[dict[str, Any]]:
    """Return paying tenants at churn risk (inactive >7 days)."""
    rows = await conn.fetch(
        "SELECT * FROM public.mv_churn_risk LIMIT $1", limit
    )
    return [dict(r) for r in rows]


async def get_team_vs_individual(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Return team vs individual usage comparison."""
    rows = await conn.fetch("SELECT * FROM public.mv_team_vs_individual")
    return [dict(r) for r in rows]


async def get_plan_distribution(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Return plan distribution with user counts."""
    rows = await conn.fetch("""
        SELECT
            t.plan::text AS plan,
            COUNT(DISTINCT t.id)::int AS tenant_count,
            COUNT(DISTINCT tm.user_id)::int AS user_count
        FROM public.tenants t
        LEFT JOIN public.tenant_members tm ON tm.tenant_id = t.id
        GROUP BY t.plan
        ORDER BY tenant_count DESC
    """)
    return [dict(r) for r in rows]


async def get_m3_dashboard(conn: asyncpg.Connection) -> dict[str, Any]:
    """Return the complete M3 dashboard payload."""
    from packages.backend.domain.m2_metrics import get_conversion_funnel

    team = await get_team_metrics(conn)
    blueprints = await get_blueprint_performance(conn)
    mrr_plans = await get_mrr_by_plan(conn)
    churn = await get_churn_risk(conn)
    segments = await get_team_vs_individual(conn)
    plan_dist = await get_plan_distribution(conn)
    funnel = await get_conversion_funnel(conn)

    # Live active user counts
    active = await conn.fetchrow("""
        SELECT
            COUNT(DISTINCT user_id) FILTER (WHERE created_at >= now() - interval '30 days')::int AS mau,
            COUNT(DISTINCT user_id) FILTER (WHERE created_at >= now() - interval '7 days')::int AS wau,
            COUNT(DISTINCT user_id) FILTER (WHERE created_at >= now() - interval '1 day')::int AS dau
        FROM public.analytics_events
    """)

    # Total applications all time
    total_apps = await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.applications"
    )

    # Total MRR
    total_mrr = sum(r.get("plan_mrr", 0) or 0 for r in mrr_plans)

    # M3 targets
    m3_targets = {
        "mau_target": 10_000,
        "mau_current": active["mau"] if active else 0,
        "subscribers_target": 500,
        "subscribers_current": sum(
            r.get("tenant_count", 0) for r in mrr_plans if r.get("plan") != "FREE"
        ),
        "mrr_target": 18_000,
        "mrr_current": total_mrr,
        "team_accounts_target": 10,
        "team_accounts_current": team.get("total_teams", 0),
        "teams_3_plus_target": 10,
        "teams_3_plus_current": team.get("teams_with_3_plus", 0),
    }

    return {
        "active_users": dict(active) if active else {"mau": 0, "wau": 0, "dau": 0},
        "total_applications": total_apps or 0,
        "team_metrics": team,
        "blueprint_performance": blueprints,
        "mrr_by_plan": mrr_plans,
        "total_mrr": total_mrr,
        "churn_risk": churn,
        "team_vs_individual": segments,
        "plan_distribution": plan_dist,
        "conversion_funnel": funnel,
        "m3_targets": m3_targets,
    }


async def refresh_m3_views(conn: asyncpg.Connection) -> None:
    """Refresh all M3 materialized views (plus M1/M2)."""
    await conn.execute("SELECT public.refresh_m1_dashboard()")
    await conn.execute("SELECT public.refresh_m2_views()")
    await conn.execute("SELECT public.refresh_m3_views()")
