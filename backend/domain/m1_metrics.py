"""M1 closed-beta dashboard metrics.

Queries the materialized views from migration 009 plus live counts
to power the admin dashboard and mobile founder view.
"""

from __future__ import annotations

from typing import Any

import asyncpg


async def get_m1_dashboard(conn: asyncpg.Connection) -> dict[str, Any]:
    """Return the complete M1 dashboard payload."""
    # 1. Active users (MAU/WAU/DAU)
    active_users = await conn.fetchrow(
        "SELECT mau, wau, dau FROM public.mv_active_users"
    )
    au = dict(active_users) if active_users else {"mau": 0, "wau": 0, "dau": 0}

    # 2. Agent success rates (7d / 30d)
    success = await conn.fetchrow("SELECT * FROM public.mv_agent_success_rates")
    sr = (
        dict(success)
        if success
        else {
            "total_7d": 0,
            "success_7d": 0,
            "partial_7d": 0,
            "failure_7d": 0,
            "success_rate_7d": 0,
            "total_30d": 0,
            "success_30d": 0,
            "partial_30d": 0,
            "failure_30d": 0,
            "success_rate_30d": 0,
        }
    )

    # 3. Total applications processed (all-time)
    total_apps = await conn.fetchval("SELECT COUNT(*)::int FROM public.applications")

    # 4. Daily stats (last 14 days)
    daily_rows = await conn.fetch(
        "SELECT * FROM public.mv_daily_app_stats ORDER BY day DESC LIMIT 14"
    )
    daily_stats = [dict(r) for r in daily_rows]

    # 5. Plan distribution
    plan_rows = await conn.fetch(
        "SELECT * FROM public.mv_plan_distribution ORDER BY plan"
    )
    plan_dist = [dict(r) for r in plan_rows]

    # 6. Live counts (not from materialized views)
    live = await conn.fetchrow(
        """
        SELECT
            COUNT(*)::int AS total_users,
            COUNT(*) FILTER (WHERE created_at >= now() - interval '24 hours')::int AS signups_today
        FROM public.users
    """
    )
    live_counts = dict(live) if live else {"total_users": 0, "signups_today": 0}

    # 7. Paying subscriber count
    pro_count = await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.tenants WHERE plan = 'PRO'"
    )

    # 8. MRR estimate (PRO × $29)
    mrr = (pro_count or 0) * 29

    # 9. Top failure reasons (last 7 days)
    failure_rows = await conn.fetch(
        """
        SELECT reason, COUNT(*)::int AS count
        FROM public.agent_evaluations
        WHERE source = 'SYSTEM' AND label = 'FAILURE'
          AND created_at >= now() - interval '7 days'
        GROUP BY reason
        ORDER BY count DESC
        LIMIT 5
    """
    )
    top_failures = [dict(r) for r in failure_rows]

    # 10. M1 target progress
    m1_targets = {
        "mau_target": 500,
        "mau_current": au["mau"],
        "mau_pct": round(au["mau"] / 5, 1),  # /500 * 100
        "apps_target": 10_000,
        "apps_current": total_apps or 0,
        "apps_pct": round((total_apps or 0) / 100, 1),  # /10000 * 100
        "success_rate_target": 75.0,
        "success_rate_current": float(sr.get("success_rate_30d") or 0),
        "pro_subscribers": pro_count or 0,
        "mrr": mrr,
    }

    return {
        "active_users": au,
        "agent_success": sr,
        "total_applications": total_apps or 0,
        "daily_stats": daily_stats,
        "plan_distribution": plan_dist,
        "live_counts": live_counts,
        "top_failures": top_failures,
        "m1_targets": m1_targets,
    }


async def refresh_dashboard_views(conn: asyncpg.Connection) -> None:
    """Refresh all materialized views. Call from a cron job or admin endpoint."""
    await conn.execute("SELECT public.refresh_m1_dashboard()")
