"""
Revenue Analytics Dashboard — track MRR, churn, and revenue metrics.

Provides insights for subscription-based business tracking.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.revenue_analytics")


async def get_mrr_breakdown(conn: asyncpg.Connection) -> dict[str, Any]:
    rows = await conn.fetch(
        """
        WITH active_subscriptions AS (
            SELECT
                t.plan,
                t.stripe_price_id,
                COUNT(*) AS subscriber_count,
                SUM(
                    CASE
                        WHEN t.stripe_price_id LIKE '%annual%' THEN
                            (COALESCE(t.monthly_price_cents, 0) / 12.0)
                        ELSE COALESCE(t.monthly_price_cents, 0)
                    END
                ) AS monthly_revenue_cents
            FROM public.tenants t
            WHERE t.plan IN ('PRO', 'TEAM', 'ENTERPRISE')
              AND t.stripe_subscription_status = 'active'
            GROUP BY t.plan, t.stripe_price_id
        )
        SELECT
            plan,
            subscriber_count,
            monthly_revenue_cents,
            SUM(monthly_revenue_cents) OVER () AS total_mrr_cents
        FROM active_subscriptions
        ORDER BY
            CASE plan
                WHEN 'ENTERPRISE' THEN 1
                WHEN 'TEAM' THEN 2
                WHEN 'PRO' THEN 3
            END
        """
    )

    plans = []
    total_mrr = 0

    for r in rows:
        plans.append(
            {
                "plan": r["plan"],
                "subscribers": r["subscriber_count"],
                "mrr_cents": int(r["monthly_revenue_cents"] or 0),
            }
        )
        total_mrr = int(r["total_mrr_cents"] or 0)

    return {
        "total_mrr_cents": total_mrr,
        "total_mrr_dollars": round(total_mrr / 100, 2),
        "breakdown": plans,
        "currency": "USD",
    }


async def get_revenue_trend(
    conn: asyncpg.Connection,
    months: int = 12,
) -> dict[str, Any]:
    rows = await conn.fetch(
        f"""
        SELECT
            DATE_TRUNC('month', created_at) AS month,
            SUM(amount_cents) AS total_cents,
            COUNT(*) AS transaction_count,
            COUNT(DISTINCT tenant_id) AS paying_tenants
        FROM public.stripe_invoice_log
        WHERE status = 'paid'
          AND created_at >= NOW() - INTERVAL '{months} months'
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY month
        """
    )

    return {
        "months": [
            {
                "month": r["month"].isoformat() if r["month"] else None,
                "revenue_cents": int(r["total_cents"] or 0),
                "transactions": r["transaction_count"],
                "paying_tenants": r["paying_tenants"],
            }
            for r in rows
        ]
    }


async def get_churn_metrics(conn: asyncpg.Connection) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        WITH monthly_churn AS (
            SELECT
                DATE_TRUNC('month', updated_at) AS month,
                COUNT(*) AS churned
            FROM public.tenants
            WHERE stripe_subscription_status = 'canceled'
              AND updated_at >= NOW() - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', updated_at)
        ),
        monthly_start AS (
            SELECT
                DATE_TRUNC('month', created_at) AS month,
                COUNT(*) AS started
            FROM public.tenants
            WHERE created_at >= NOW() - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', created_at)
        )
        SELECT
            COALESCE(SUM(mc.churned), 0) AS total_churned,
            COALESCE(SUM(ms.started), 0) AS total_started,
            (SELECT COUNT(*) FROM public.tenants WHERE stripe_subscription_status = 'active') AS current_active
        FROM monthly_churn mc
        FULL OUTER JOIN monthly_start ms ON ms.month = mc.month
        """
    )

    total_churned = row["total_churned"] if row else 0
    total_started = row["total_started"] if row else 0
    current_active = row["current_active"] if row else 0

    churn_rate = (
        (total_churned / (total_churned + current_active) * 100)
        if (total_churned + current_active) > 0
        else 0
    )

    return {
        "total_churned_12m": total_churned,
        "total_started_12m": total_started,
        "current_active": current_active,
        "churn_rate_pct": round(churn_rate, 1),
        "net_growth": total_started - total_churned,
    }


async def get_arpu(conn: asyncpg.Connection) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        WITH revenue AS (
            SELECT
                tenant_id,
                SUM(amount_cents) AS total_cents
            FROM public.stripe_invoice_log
            WHERE status = 'paid'
              AND created_at >= NOW() - INTERVAL '1 month'
            GROUP BY tenant_id
        ),
        users AS (
            SELECT
                t.id AS tenant_id,
                COUNT(DISTINCT tm.user_id) AS user_count
            FROM public.tenants t
            LEFT JOIN public.team_members tm ON tm.tenant_id = t.id
            WHERE t.stripe_subscription_status = 'active'
            GROUP BY t.id
        )
        SELECT
            COALESCE(SUM(r.total_cents), 0) AS total_revenue_cents,
            COALESCE(SUM(u.user_count), 0) AS total_users,
            COALESCE(COUNT(DISTINCT r.tenant_id), 0) AS paying_tenants
        FROM revenue r
        FULL OUTER JOIN users u ON u.tenant_id = r.tenant_id
        """
    )

    total_revenue = int(row["total_revenue_cents"] or 0) if row else 0
    total_users = int(row["total_users"] or 0) if row else 0
    paying_tenants = int(row["paying_tenants"] or 0) if row else 0

    arpu = (total_revenue / total_users / 100) if total_users > 0 else 0
    arppu = (total_revenue / paying_tenants / 100) if paying_tenants > 0 else 0

    return {
        "arpu_dollars": round(arpu, 2),
        "arppu_dollars": round(arppu, 2),
        "total_users": total_users,
        "paying_tenants": paying_tenants,
        "total_revenue_cents": total_revenue,
    }


async def get_conversion_funnel(conn: asyncpg.Connection) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        WITH funnel AS (
            SELECT
                (SELECT COUNT(*) FROM auth.users) AS total_signups,
                (SELECT COUNT(*) FROM auth.users WHERE id IN (SELECT DISTINCT user_id FROM public.applications)) AS activated,
                (SELECT COUNT(*) FROM public.tenants WHERE plan != 'FREE') AS converted,
                (SELECT COUNT(*) FROM public.tenants WHERE plan IN ('PRO', 'TEAM', 'ENTERPRISE') AND stripe_subscription_status = 'active') AS active_paid
        )
        SELECT * FROM funnel
        """
    )

    total = row["total_signups"] if row else 0
    activated = row["activated"] if row else 0
    converted = row["converted"] if row else 0
    active = row["active_paid"] if row else 0

    return {
        "total_signups": total,
        "activated": activated,
        "converted": converted,
        "active_paid": active,
        "activation_rate": round(activated / total * 100, 1) if total > 0 else 0,
        "conversion_rate": round(converted / total * 100, 1) if total > 0 else 0,
        "paid_retention_rate": round(active / converted * 100, 1)
        if converted > 0
        else 0,
    }


async def get_revenue_dashboard(conn: asyncpg.Connection) -> dict[str, Any]:
    mrr = await get_mrr_breakdown(conn)
    churn = await get_churn_metrics(conn)
    arpu = await get_arpu(conn)
    funnel = await get_conversion_funnel(conn)
    trend = await get_revenue_trend(conn, months=6)

    incr("revenue_analytics.dashboard_viewed")

    return {
        "mrr": mrr,
        "churn": churn,
        "arpu": arpu,
        "funnel": funnel,
        "trend": trend,
        "updated_at": datetime.now(UTC).isoformat(),
    }
