"""M5: Business Metrics Dashboard — Real-time DAU, retention, conversion tracking.

Provides comprehensive business metrics for monitoring product health and growth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import asyncpg


async def get_daily_active_users(
    conn: asyncpg.Connection, days: int = 30
) -> list[dict[str, Any]]:
    """Get daily active users for the last N days."""
    rows = await conn.fetch(
        """
        SELECT
            DATE(created_at) AS date,
            COUNT(DISTINCT user_id)::int AS dau
        FROM public.analytics_events
        WHERE created_at >= now() - interval '1 day' * $1
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """,
        days,
    )
    return [
        {"date": r["date"].isoformat() if r["date"] else None, "dau": r["dau"]}
        for r in rows
    ]


async def get_retention_cohorts(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Get user retention by signup cohort."""
    rows = await conn.fetch(
        """
        WITH user_signups AS (
            SELECT
                u.id AS user_id,
                DATE_TRUNC('month', u.created_at) AS cohort_month
            FROM public.users u
            WHERE u.created_at >= now() - interval '6 months'
        ),
        monthly_activity AS (
            SELECT
                us.cohort_month,
                DATE_TRUNC('month', ae.created_at) AS activity_month,
                COUNT(DISTINCT ae.user_id)::int AS active_users
            FROM user_signups us
            JOIN public.analytics_events ae ON ae.user_id = us.user_id
            WHERE ae.created_at >= us.cohort_month
            GROUP BY us.cohort_month, DATE_TRUNC('month', ae.created_at)
        ),
        cohort_sizes AS (
            SELECT
                cohort_month,
                COUNT(DISTINCT user_id)::int AS cohort_size
            FROM user_signups
            GROUP BY cohort_month
        )
        SELECT
            ma.cohort_month::text AS cohort_month,
            ma.activity_month::text AS activity_month,
            cs.cohort_size,
            ma.active_users,
            ROUND((ma.active_users::numeric / NULLIF(cs.cohort_size, 0)) * 100, 2) AS retention_pct
        FROM monthly_activity ma
        JOIN cohort_sizes cs ON cs.cohort_month = ma.cohort_month
        WHERE ma.activity_month >= ma.cohort_month
        ORDER BY ma.cohort_month DESC, ma.activity_month DESC
        """
    )
    return [dict(r) for r in rows]


async def get_conversion_funnel(conn: asyncpg.Connection) -> dict[str, Any]:
    """Get conversion funnel metrics (signup → onboarding → first application → paid)."""
    rows = await conn.fetchrow(
        """
        WITH signups AS (
            SELECT COUNT(*)::int AS count
            FROM public.users
            WHERE created_at >= now() - interval '30 days'
        ),
        onboarded AS (
            SELECT COUNT(DISTINCT p.user_id)::int AS count
            FROM public.profiles p
            WHERE COALESCE((p.profile_data->>'has_completed_onboarding')::boolean, false) = true
            AND p.updated_at >= now() - interval '30 days'
        ),
        first_application AS (
            SELECT COUNT(DISTINCT user_id)::int AS count
            FROM public.applications
            WHERE created_at >= now() - interval '30 days'
            AND user_id IN (
                SELECT user_id FROM public.applications
                GROUP BY user_id
                HAVING COUNT(*) = 1
            )
        ),
        paid_users AS (
            SELECT COUNT(DISTINCT tm.user_id)::int AS count
            FROM public.tenant_members tm
            JOIN public.tenants t ON t.id = tm.tenant_id
            WHERE t.plan NOT IN ('FREE', 'TRIAL')
            AND tm.created_at >= now() - interval '30 days'
        )
        SELECT
            (SELECT count FROM signups) AS signups,
            (SELECT count FROM onboarded) AS onboarded,
            (SELECT count FROM first_application) AS first_application,
            (SELECT count FROM paid_users) AS paid_users
        """
    )

    if not rows:
        return {
            "signups": 0,
            "onboarded": 0,
            "first_application": 0,
            "paid_users": 0,
            "signup_to_onboarded_pct": 0.0,
            "onboarded_to_application_pct": 0.0,
            "application_to_paid_pct": 0.0,
        }

    signups = rows["signups"] or 0
    onboarded = rows["onboarded"] or 0
    first_app = rows["first_application"] or 0
    paid = rows["paid_users"] or 0

    return {
        "signups": signups,
        "onboarded": onboarded,
        "first_application": first_app,
        "paid_users": paid,
        "signup_to_onboarded_pct": round(
            (onboarded / signups * 100) if signups > 0 else 0, 2
        ),
        "onboarded_to_application_pct": round(
            (first_app / onboarded * 100) if onboarded > 0 else 0, 2
        ),
        "application_to_paid_pct": round(
            (paid / first_app * 100) if first_app > 0 else 0, 2
        ),
    }


async def get_revenue_metrics(conn: asyncpg.Connection) -> dict[str, Any]:
    """Get revenue metrics (MRR, ARR, growth rate)."""
    rows = await conn.fetchrow(
        """
        WITH current_mrr AS (
            SELECT
                SUM(
                    CASE t.plan
                        WHEN 'PRO' THEN 99
                        WHEN 'TEAM' THEN 299
                        WHEN 'ENTERPRISE' THEN 999
                        ELSE 0
                    END
                )::int AS mrr
            FROM public.tenants t
            WHERE t.plan NOT IN ('FREE', 'TRIAL')
            AND t.created_at <= now()
        ),
        previous_mrr AS (
            SELECT
                SUM(
                    CASE t.plan
                        WHEN 'PRO' THEN 99
                        WHEN 'TEAM' THEN 299
                        WHEN 'ENTERPRISE' THEN 999
                        ELSE 0
                    END
                )::int AS mrr
            FROM public.tenants t
            WHERE t.plan NOT IN ('FREE', 'TRIAL')
            AND t.created_at <= now() - interval '1 month'
        )
        SELECT
            (SELECT mrr FROM current_mrr) AS current_mrr,
            (SELECT mrr FROM previous_mrr) AS previous_mrr
        """
    )

    if not rows:
        return {
            "mrr": 0,
            "arr": 0,
            "mrr_growth_pct": 0.0,
        }

    current_mrr = rows["current_mrr"] or 0
    previous_mrr = rows["previous_mrr"] or 0

    growth_pct = round(
        ((current_mrr - previous_mrr) / previous_mrr * 100) if previous_mrr > 0 else 0,
        2,
    )

    return {
        "mrr": current_mrr,
        "arr": current_mrr * 12,
        "mrr_growth_pct": growth_pct,
    }


async def get_active_user_metrics(conn: asyncpg.Connection) -> dict[str, Any]:
    """Get active user metrics (DAU, WAU, MAU)."""
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(DISTINCT user_id) FILTER (
                WHERE created_at >= now() - interval '1 day'
            )::int AS dau,
            COUNT(DISTINCT user_id) FILTER (
                WHERE created_at >= now() - interval '7 days'
            )::int AS wau,
            COUNT(DISTINCT user_id) FILTER (
                WHERE created_at >= now() - interval '30 days'
            )::int AS mau
        FROM public.analytics_events
        """
    )

    if not row:
        return {"dau": 0, "wau": 0, "mau": 0}

    return {
        "dau": row["dau"] or 0,
        "wau": row["wau"] or 0,
        "mau": row["mau"] or 0,
    }


async def get_business_metrics_dashboard(conn: asyncpg.Connection) -> dict[str, Any]:
    """M5: Return comprehensive business metrics dashboard.

    Includes:
    - Real-time DAU/WAU/MAU
    - Daily active users trend (30 days)
    - User retention by cohort
    - Conversion funnel (signup → paid)
    - Revenue metrics (MRR, ARR, growth)
    """
    dau_trend = await get_daily_active_users(conn, days=30)
    retention = await get_retention_cohorts(conn)
    conversion = await get_conversion_funnel(conn)
    revenue = await get_revenue_metrics(conn)
    active_users = await get_active_user_metrics(conn)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_users": active_users,
        "dau_trend": dau_trend,
        "retention_cohorts": retention,
        "conversion_funnel": conversion,
        "revenue": revenue,
    }
