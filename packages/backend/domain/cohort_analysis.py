"""
Cohort Analysis — track user retention and engagement over time.

Cohorts are groups of users who signed up in the same time period.
This module analyzes their behavior over subsequent periods.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.cohort_analysis")


class CohortPeriod:
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


async def get_cohort_data(
    conn: asyncpg.Connection,
    period: str = CohortPeriod.WEEKLY,
    num_periods: int = 12,
) -> dict[str, Any]:
    if period == CohortPeriod.DAILY:
        interval = "1 day"
        date_trunc = "day"
    elif period == CohortPeriod.MONTHLY:
        interval = "1 month"
        date_trunc = "month"
    else:
        interval = "1 week"
        date_trunc = "week"

    cohorts = await conn.fetch(
        f"""
        WITH user_cohorts AS (
            SELECT
                u.id AS user_id,
                DATE_TRUNC('{date_trunc}', u.created_at) AS cohort_date
            FROM auth.users u
            WHERE u.created_at >= NOW() - INTERVAL '{num_periods} {interval.replace("1 ", "")}'
        ),
        activity AS (
            SELECT DISTINCT
                a.user_id,
                DATE_TRUNC('{date_trunc}', a.created_at) AS activity_date
            FROM public.applications a
            WHERE a.created_at >= NOW() - INTERVAL '{num_periods} {interval.replace("1 ", "")}'
        )
        SELECT
            uc.cohort_date,
            a.activity_date,
            COUNT(DISTINCT uc.user_id) AS active_users,
            (SELECT COUNT(*) FROM user_cohorts uc2 WHERE uc2.cohort_date = uc.cohort_date) AS cohort_size
        FROM user_cohorts uc
        LEFT JOIN activity a ON a.user_id = uc.user_id
        GROUP BY uc.cohort_date, a.activity_date
        ORDER BY uc.cohort_date, a.activity_date
        """
    )

    cohort_map: dict[str, dict[str, Any]] = {}
    for row in cohorts:
        cohort_date = row["cohort_date"]
        if cohort_date is None:
            continue
        cohort_key = cohort_date.isoformat() if cohort_date else "unknown"

        if cohort_key not in cohort_map:
            cohort_map[cohort_key] = {
                "cohort_date": cohort_key,
                "cohort_size": row["cohort_size"] or 0,
                "retention": {},
            }

        activity_date = row["activity_date"]
        if activity_date:
            period_num = _calculate_period_number(cohort_date, activity_date, period)
            retention_pct = (
                (row["active_users"] / row["cohort_size"] * 100)
                if row["cohort_size"] and row["cohort_size"] > 0
                else 0
            )
            cohort_map[cohort_key]["retention"][str(period_num)] = round(
                retention_pct, 1
            )

    return {
        "period": period,
        "cohorts": list(cohort_map.values()),
    }


def _calculate_period_number(
    cohort_date: datetime, activity_date: datetime, period: str
) -> int:
    delta = activity_date - cohort_date
    if period == CohortPeriod.DAILY:
        return delta.days
    elif period == CohortPeriod.MONTHLY:
        return delta.days // 30
    else:
        return delta.days // 7


async def get_retention_metrics(
    conn: asyncpg.Connection,
) -> dict[str, Any]:
    d7 = await conn.fetchrow(
        """
        WITH cohort AS (
            SELECT COUNT(DISTINCT id) AS total
            FROM auth.users
            WHERE created_at >= NOW() - INTERVAL '14 days'
              AND created_at < NOW() - INTERVAL '7 days'
        ),
        retained AS (
            SELECT COUNT(DISTINCT u.id) AS count
            FROM auth.users u
            JOIN public.applications a ON a.user_id = u.id
            WHERE u.created_at >= NOW() - INTERVAL '14 days'
              AND u.created_at < NOW() - INTERVAL '7 days'
              AND a.created_at >= u.created_at + INTERVAL '7 days'
        )
        SELECT cohort.total AS cohort_size, retained.count AS retained_count
        FROM cohort, retained
        """
    )

    d30 = await conn.fetchrow(
        """
        WITH cohort AS (
            SELECT COUNT(DISTINCT id) AS total
            FROM auth.users
            WHERE created_at >= NOW() - INTERVAL '60 days'
              AND created_at < NOW() - INTERVAL '30 days'
        ),
        retained AS (
            SELECT COUNT(DISTINCT u.id) AS count
            FROM auth.users u
            JOIN public.applications a ON a.user_id = u.id
            WHERE u.created_at >= NOW() - INTERVAL '60 days'
              AND u.created_at < NOW() - INTERVAL '30 days'
              AND a.created_at >= u.created_at + INTERVAL '30 days'
        )
        SELECT cohort.total AS cohort_size, retained.count AS retained_count
        FROM cohort, retained
        """
    )

    return {
        "d7_retention": round(
            (d7["retained_count"] / d7["cohort_size"] * 100)
            if d7 and d7["cohort_size"]
            else 0,
            1,
        ),
        "d7_cohort_size": d7["cohort_size"] if d7 else 0,
        "d30_retention": round(
            (d30["retained_count"] / d30["cohort_size"] * 100)
            if d30 and d30["cohort_size"]
            else 0,
            1,
        ),
        "d30_cohort_size": d30["cohort_size"] if d30 else 0,
    }


async def get_engagement_metrics(
    conn: asyncpg.Connection,
    period_days: int = 7,
) -> dict[str, Any]:
    rows = await conn.fetch(
        f"""
        WITH user_activity AS (
            SELECT
                u.id AS user_id,
                COUNT(a.id) AS application_count,
                COUNT(DISTINCT DATE(a.created_at)) AS active_days
            FROM auth.users u
            LEFT JOIN public.applications a ON a.user_id = u.id
                AND a.created_at >= NOW() - INTERVAL '{period_days} days'
            GROUP BY u.id
        )
        SELECT
            COUNT(*) FILTER (WHERE application_count > 0) AS active_users,
            COUNT(*) FILTER (WHERE application_count = 0) AS inactive_users,
            AVG(application_count) FILTER (WHERE application_count > 0) AS avg_apps_per_active,
            AVG(active_days) FILTER (WHERE active_days > 0) AS avg_active_days
        FROM user_activity
        """
    )

    if rows:
        r = rows[0]
        return {
            "period_days": period_days,
            "active_users": r["active_users"] or 0,
            "inactive_users": r["inactive_users"] or 0,
            "avg_apps_per_active": round(float(r["avg_apps_per_active"] or 0), 1),
            "avg_active_days": round(float(r["avg_active_days"] or 0), 1),
        }

    return {
        "period_days": period_days,
        "active_users": 0,
        "inactive_users": 0,
        "avg_apps_per_active": 0,
        "avg_active_days": 0,
    }
