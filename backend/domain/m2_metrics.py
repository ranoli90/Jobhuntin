"""M2 open-beta metrics — conversion funnel, cohort retention, referral
performance, and UTM source attribution.

Queries the materialized views from migration 011.
"""

from __future__ import annotations

from typing import Any

import asyncpg


async def get_conversion_funnel(conn: asyncpg.Connection) -> dict[str, Any]:
    """Return the 30-day signup → activation → conversion funnel."""
    row = await conn.fetchrow("SELECT * FROM public.mv_conversion_funnel")
    if not row:
        return {
            "total_signups": 0,
            "onboarded": 0,
            "uploaded_resume": 0,
            "first_application": 0,
            "converted_pro": 0,
            "onboarding_rate": 0,
            "activation_rate": 0,
            "conversion_rate": 0,
        }
    return dict(row)


async def get_weekly_cohorts(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Return weekly cohort retention table (last 12 weeks)."""
    rows = await conn.fetch(
        "SELECT * FROM public.mv_weekly_cohorts ORDER BY cohort_week DESC LIMIT 12"
    )
    result = []
    for r in rows:
        d = dict(r)
        size = d.get("cohort_size", 1) or 1
        d["retention_w1"] = round((d.get("week_1", 0) / size) * 100, 1)
        d["retention_w2"] = round((d.get("week_2", 0) / size) * 100, 1)
        d["retention_w3"] = round((d.get("week_3", 0) / size) * 100, 1)
        d["retention_w4"] = round((d.get("week_4", 0) / size) * 100, 1)
        result.append(d)
    return result


async def get_referral_performance(conn: asyncpg.Connection) -> dict[str, Any]:
    """Return aggregated referral program stats."""
    row = await conn.fetchrow("SELECT * FROM public.mv_referral_stats")
    if not row:
        return {
            "total_referrals": 0,
            "successful": 0,
            "pending": 0,
            "total_bonus_apps_granted": 0,
            "unique_referrers": 0,
        }
    return dict(row)


async def get_signup_sources(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Return signup source attribution (UTM-based)."""
    rows = await conn.fetch(
        "SELECT * FROM public.mv_signup_sources ORDER BY signups DESC LIMIT 20"
    )
    return [dict(r) for r in rows]


async def get_m2_dashboard(conn: asyncpg.Connection) -> dict[str, Any]:
    """Return the complete M2 dashboard payload."""
    # Import M1 dashboard for base metrics
    from backend.domain.m1_metrics import get_m1_dashboard

    m1 = await get_m1_dashboard(conn)
    funnel = await get_conversion_funnel(conn)
    cohorts = await get_weekly_cohorts(conn)
    referrals = await get_referral_performance(conn)
    sources = await get_signup_sources(conn)

    # Live push notification stats
    push_stats = await conn.fetchrow(
        """
        SELECT
            COUNT(DISTINCT user_id)::int AS users_with_push,
            COUNT(*)::int AS total_tokens
        FROM public.push_tokens WHERE is_active = true
    """
    )

    # Live digest stats
    digest_stats = await conn.fetchrow(
        """
        SELECT
            COUNT(*)::int AS digests_sent_this_week
        FROM public.email_digest_log
        WHERE sent_at >= now() - interval '7 days'
    """
    )

    # M2 targets
    m2_targets = {
        "mau_target": 3000,
        "mau_current": m1["active_users"]["mau"],
        "mau_pct": round(m1["active_users"]["mau"] / 30, 1),
        "pro_target": 100,
        "pro_current": m1["m1_targets"]["pro_subscribers"],
        "pro_pct": round(m1["m1_targets"]["pro_subscribers"], 1),
        "mrr_target": 2900,
        "mrr_current": m1["m1_targets"]["mrr"],
        "conversion_target": 5.0,
        "conversion_current": float(funnel.get("conversion_rate") or 0),
    }

    return {
        **m1,
        "conversion_funnel": funnel,
        "weekly_cohorts": cohorts,
        "referral_performance": referrals,
        "signup_sources": sources,
        "push_stats": (
            dict(push_stats)
            if push_stats
            else {"users_with_push": 0, "total_tokens": 0}
        ),
        "digest_stats": (
            dict(digest_stats) if digest_stats else {"digests_sent_this_week": 0}
        ),
        "m2_targets": m2_targets,
    }


async def refresh_m2_views(conn: asyncpg.Connection) -> None:
    """Refresh all M2 materialized views (plus M1)."""
    await conn.execute("SELECT public.refresh_m1_dashboard()")
    await conn.execute("SELECT public.refresh_m2_views()")
