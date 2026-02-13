"""
Data Retention Policy — automated data archiving and cleanup.

Implements configurable retention periods for different data types:
- Application data: 2 years (configurable)
- Event logs: 90 days
- Session data: 30 days
- Analytics events: 1 year
- Background job logs: 30 days
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import asyncpg

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.retention")


class RetentionPolicy:
    APPLICATIONS_DAYS = 730  # 2 years
    APPLICATION_EVENTS_DAYS = 90
    ANALYTICS_EVENTS_DAYS = 365
    BACKGROUND_JOBS_DAYS = 30
    EMAIL_DIGEST_LOG_DAYS = 90
    JOB_ALERT_LOG_DAYS = 90
    SESSION_DATA_DAYS = 30
    AUDIT_LOG_DAYS = 365


async def get_retention_stats(conn: asyncpg.Connection) -> dict[str, Any]:
    stats = {}

    stats["applications"] = await conn.fetchrow(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE created_at < NOW() - INTERVAL '730 days') AS older_than_2_years,
            MIN(created_at) AS oldest_record
        FROM public.applications
        """
    )

    stats["application_events"] = await conn.fetchrow(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE created_at < NOW() - INTERVAL '90 days') AS older_than_90_days
        FROM public.application_events
        """
    )

    stats["analytics_events"] = await conn.fetchrow(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE created_at < NOW() - INTERVAL '365 days') AS older_than_1_year
        FROM public.analytics_events
        """
    )

    stats["background_jobs"] = await conn.fetchrow(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE created_at < NOW() - INTERVAL '30 days') AS older_than_30_days
        FROM public.background_jobs
        WHERE status IN ('completed', 'failed', 'cancelled')
        """
    )

    return {
        "applications": dict(stats["applications"]) if stats["applications"] else {},
        "application_events": dict(stats["application_events"])
        if stats["application_events"]
        else {},
        "analytics_events": dict(stats["analytics_events"])
        if stats["analytics_events"]
        else {},
        "background_jobs": dict(stats["background_jobs"])
        if stats["background_jobs"]
        else {},
    }


async def archive_old_applications(
    conn: asyncpg.Connection,
    days_old: int = RetentionPolicy.APPLICATIONS_DAYS,
    batch_size: int = 1000,
) -> int:
    total_archived = 0

    while True:
        result = await conn.execute(
            f"""
            WITH to_archive AS (
                SELECT id FROM public.applications
                WHERE created_at < NOW() - INTERVAL '{days_old} days'
                LIMIT {batch_size}
                FOR UPDATE SKIP LOCKED
            )
            DELETE FROM public.applications
            WHERE id IN (SELECT id FROM to_archive)
            """
        )

        archived = int(result.split()[-1]) if "DELETE" in result else 0
        total_archived += archived

        if archived == 0:
            break

        logger.info("Archived %d applications (total: %d)", archived, total_archived)

    if total_archived > 0:
        incr("retention.applications_archived", value=total_archived)

    return total_archived


async def cleanup_application_events(
    conn: asyncpg.Connection,
    days_old: int = RetentionPolicy.APPLICATION_EVENTS_DAYS,
) -> int:
    result = await conn.execute(
        f"""
        DELETE FROM public.application_events
        WHERE created_at < NOW() - INTERVAL '{days_old} days'
        """
    )
    deleted = int(result.split()[-1]) if "DELETE" in result else 0
    if deleted > 0:
        logger.info(
            "Cleaned up %d application events older than %d days", deleted, days_old
        )
        incr("retention.events_cleaned", value=deleted)
    return deleted


async def cleanup_analytics_events(
    conn: asyncpg.Connection,
    days_old: int = RetentionPolicy.ANALYTICS_EVENTS_DAYS,
) -> int:
    result = await conn.execute(
        f"""
        DELETE FROM public.analytics_events
        WHERE created_at < NOW() - INTERVAL '{days_old} days'
        """
    )
    deleted = int(result.split()[-1]) if "DELETE" in result else 0
    if deleted > 0:
        logger.info(
            "Cleaned up %d analytics events older than %d days", deleted, days_old
        )
        incr("retention.analytics_cleaned", value=deleted)
    return deleted


async def cleanup_email_digest_logs(
    conn: asyncpg.Connection,
    days_old: int = RetentionPolicy.EMAIL_DIGEST_LOG_DAYS,
) -> int:
    result = await conn.execute(
        f"""
        DELETE FROM public.email_digest_log
        WHERE sent_at < NOW() - INTERVAL '{days_old} days'
        """
    )
    deleted = int(result.split()[-1]) if "DELETE" in result else 0
    if deleted > 0:
        logger.info(
            "Cleaned up %d email digest logs older than %d days", deleted, days_old
        )
    return deleted


async def cleanup_job_alert_logs(
    conn: asyncpg.Connection,
    days_old: int = RetentionPolicy.JOB_ALERT_LOG_DAYS,
) -> int:
    result = await conn.execute(
        f"""
        DELETE FROM public.job_alert_log
        WHERE sent_at < NOW() - INTERVAL '{days_old} days'
        """
    )
    deleted = int(result.split()[-1]) if "DELETE" in result else 0
    if deleted > 0:
        logger.info(
            "Cleaned up %d job alert logs older than %d days", deleted, days_old
        )
    return deleted


async def run_retention_cleanup(pool: asyncpg.Pool) -> dict[str, int]:
    results = {}

    async with pool.acquire() as conn:
        results["applications_archived"] = await archive_old_applications(conn)
        results["events_cleaned"] = await cleanup_application_events(conn)
        results["analytics_cleaned"] = await cleanup_analytics_events(conn)
        results["email_logs_cleaned"] = await cleanup_email_digest_logs(conn)
        results["alert_logs_cleaned"] = await cleanup_job_alert_logs(conn)

    total = sum(results.values())
    logger.info("Retention cleanup complete: %d total records processed", total)
    incr("retention.cleanup_total", value=total)

    return results


async def get_retention_policy_config() -> dict[str, Any]:
    return {
        "applications_days": RetentionPolicy.APPLICATIONS_DAYS,
        "application_events_days": RetentionPolicy.APPLICATION_EVENTS_DAYS,
        "analytics_events_days": RetentionPolicy.ANALYTICS_EVENTS_DAYS,
        "background_jobs_days": RetentionPolicy.BACKGROUND_JOBS_DAYS,
        "email_digest_log_days": RetentionPolicy.EMAIL_DIGEST_LOG_DAYS,
        "job_alert_log_days": RetentionPolicy.JOB_ALERT_LOG_DAYS,
        "session_data_days": RetentionPolicy.SESSION_DATA_DAYS,
        "audit_log_days": RetentionPolicy.AUDIT_LOG_DAYS,
    }
