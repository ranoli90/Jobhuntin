"""Background worker for data retention cleanup.

Runs periodically (daily/weekly) to clean up old data according to
retention policies defined in shared/data_retention.py.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import uuid
from datetime import datetime
from typing import Any

# Add project paths before imports (E402: import not at top - required for worker)
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "packages"))

import asyncpg  # noqa: E402

from shared.config import get_settings  # noqa: E402
from shared.data_retention import (  # noqa: E402
    DataRetentionPolicy,
    DataType,
    get_retention_policy,
)
from shared.logging_config import get_logger  # noqa: E402

logger = get_logger("sorce.data_retention_worker")

_shutdown = False
_job_id = str(uuid.uuid4())


def handle_shutdown(signum, _frame):
    """Handle shutdown signals gracefully."""
    global _shutdown
    logger.info(f"Received signal {signum}, shutting down...")
    _shutdown = True


def _get_ssl_config(settings) -> object:
    """Derive SSL configuration for the worker database pool.

    Uses secure verification when db_ssl_ca_cert_path is set,
    otherwise uses system defaults (requires valid CA-signed cert).
    """
    import ssl

    if getattr(settings, "db_ssl_ca_cert_path", None):
        ctx = ssl.create_default_context(cafile=settings.db_ssl_ca_cert_path)
        return ctx
    # Use system default SSL verification (requires valid CA-signed cert)
    return False


async def create_db_pool():
    """Create database connection pool."""
    settings = get_settings()
    from shared.db import resolve_dsn_ipv4

    dsn = resolve_dsn_ipv4(settings.database_url)
    ssl_arg = _get_ssl_config(settings)
    return await asyncpg.create_pool(
        dsn,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        statement_cache_size=0,
        ssl=ssl_arg,
        timeout=30.0,
        command_timeout=60.0,
    )


async def log_deletion(
    db_pool: asyncpg.Pool,
    data_type: str,
    deleted_count: int,
    batch_number: int,
    error: str | None = None,
) -> None:
    """Log deletion to the data_retention_logs table."""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO data_retention_logs
                (job_id, data_type, deleted_count, batch_number, error_message, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                _job_id,
                data_type,
                deleted_count,
                batch_number,
                error,
                datetime.utcnow(),
            )
    except Exception as e:
        logger.error(f"Failed to log deletion: {e}")


async def cleanup_session_logs(
    db_pool: asyncpg.Pool, policy: DataRetentionPolicy, dry_run: bool = False
) -> dict[str, Any]:
    """Clean up old session logs."""
    data_type = DataType.SESSION_LOGS
    cutoff = policy.get_cutoff_date(data_type)
    batch_size = policy.get_policy(data_type).batch_size if policy.get_policy(data_type) else 1000

    total_deleted = 0

    try:
        async with db_pool.acquire() as conn:
            # Get count of records to delete
            count_result = await conn.fetchval(
                "SELECT COUNT(*) FROM session_logs WHERE created_at < $1",
                cutoff,
            )
            logger.info(f"Found {count_result} session logs eligible for deletion")

            if dry_run:
                return {"status": "dry_run", "would_delete": count_result}

            # Delete in batches
            batch_num = 0
            while True:
                batch_num += 1
                # Get IDs to delete in this batch
                ids = await conn.fetch(
                    """
                    SELECT id FROM session_logs
                    WHERE created_at < $1
                    LIMIT $2
                    """,
                    cutoff,
                    batch_size,
                )

                if not ids:
                    break

                id_list = [r["id"] for r in ids]
                deleted = await conn.execute(
                    "DELETE FROM session_logs WHERE id = ANY($1)", id_list
                )
                count = len(id_list)
                total_deleted += count

                logger.info(f"Batch {batch_num}: deleted {count} session logs")
                await log_deletion(db_pool, data_type.value, count, batch_num)

                # Small delay to avoid overwhelming the DB
                await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error cleaning up session logs: {e}")
        await log_deletion(db_pool, data_type.value, 0, 0, str(e))
        return {"status": "error", "error": str(e)}

    return {"status": "success", "deleted": total_deleted}


async def cleanup_analytics_events(
    db_pool: asyncpg.Pool, policy: DataRetentionPolicy, dry_run: bool = False
) -> dict[str, Any]:
    """Clean up old analytics events."""
    data_type = DataType.ANALYTICS_EVENTS
    cutoff = policy.get_cutoff_date(data_type)
    batch_size = policy.get_policy(data_type).batch_size if policy.get_policy(data_type) else 10000

    total_deleted = 0

    try:
        async with db_pool.acquire() as conn:
            count_result = await conn.fetchval(
                "SELECT COUNT(*) FROM analytics_events WHERE created_at < $1",
                cutoff,
            )
            logger.info(f"Found {count_result} analytics events eligible for deletion")

            if dry_run:
                return {"status": "dry_run", "would_delete": count_result}

            batch_num = 0
            while True:
                batch_num += 1
                ids = await conn.fetch(
                    """
                    SELECT id FROM analytics_events
                    WHERE created_at < $1
                    LIMIT $2
                    """,
                    cutoff,
                    batch_size,
                )

                if not ids:
                    break

                id_list = [r["id"] for r in ids]
                deleted = await conn.execute(
                    "DELETE FROM analytics_events WHERE id = ANY($1)", id_list
                )
                count = len(id_list)
                total_deleted += count

                logger.info(f"Batch {batch_num}: deleted {count} analytics events")
                await log_deletion(db_pool, data_type.value, count, batch_num)

                await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error cleaning up analytics events: {e}")
        await log_deletion(db_pool, data_type.value, 0, 0, str(e))
        return {"status": "error", "error": str(e)}

    return {"status": "success", "deleted": total_deleted}


async def cleanup_application_data(
    db_pool: asyncpg.Pool, policy: DataRetentionPolicy, dry_run: bool = False
) -> dict[str, Any]:
    """Clean up application data for deleted accounts (after grace period)."""
    data_type = DataType.APPLICATION_DATA
    cutoff = policy.get_cutoff_date(data_type)
    batch_size = policy.get_policy(data_type).batch_size if policy.get_policy(data_type) else 1000

    total_deleted = 0

    try:
        async with db_pool.acquire() as conn:
            # Only delete applications that are soft-deleted and past the grace period
            count_result = await conn.fetchval(
                """
                SELECT COUNT(*) FROM applications
                WHERE deleted_at IS NOT NULL AND deleted_at < $1
                """,
                cutoff,
            )
            logger.info(f"Found {count_result} application records eligible for deletion")

            if dry_run:
                return {"status": "dry_run", "would_delete": count_result}

            batch_num = 0
            while True:
                batch_num += 1
                ids = await conn.fetch(
                    """
                    SELECT id FROM applications
                    WHERE deleted_at IS NOT NULL AND deleted_at < $1
                    LIMIT $2
                    """,
                    cutoff,
                    batch_size,
                )

                if not ids:
                    break

                id_list = [r["id"] for r in ids]
                deleted = await conn.execute(
                    "DELETE FROM applications WHERE id = ANY($1)", id_list
                )
                count = len(id_list)
                total_deleted += count

                logger.info(f"Batch {batch_num}: deleted {count} application records")
                await log_deletion(db_pool, data_type.value, count, batch_num)

                await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error cleaning up application data: {e}")
        await log_deletion(db_pool, data_type.value, 0, 0, str(e))
        return {"status": "error", "error": str(e)}

    return {"status": "success", "deleted": total_deleted}


async def cleanup_uploaded_resumes(
    db_pool: asyncpg.Pool, policy: DataRetentionPolicy, dry_run: bool = False
) -> dict[str, Any]:
    """Clean up uploaded resumes for deleted accounts (after grace period)."""
    data_type = DataType.UPLOADED_RESUMES
    cutoff = policy.get_cutoff_date(data_type)
    batch_size = policy.get_policy(data_type).batch_size if policy.get_policy(data_type) else 500

    total_deleted = 0

    try:
        async with db_pool.acquire() as conn:
            count_result = await conn.fetchval(
                """
                SELECT COUNT(*) FROM uploaded_resumes
                WHERE deleted_at IS NOT NULL AND deleted_at < $1
                """,
                cutoff,
            )
            logger.info(f"Found {count_result} uploaded resumes eligible for deletion")

            if dry_run:
                return {"status": "dry_run", "would_delete": count_result}

            batch_num = 0
            while True:
                batch_num += 1
                ids = await conn.fetch(
                    """
                    SELECT id FROM uploaded_resumes
                    WHERE deleted_at IS NOT NULL AND deleted_at < $1
                    LIMIT $2
                    """,
                    cutoff,
                    batch_size,
                )

                if not ids:
                    break

                id_list = [r["id"] for r in ids]
                deleted = await conn.execute(
                    "DELETE FROM uploaded_resumes WHERE id = ANY($1)", id_list
                )
                count = len(id_list)
                total_deleted += count

                logger.info(f"Batch {batch_num}: deleted {count} uploaded resumes")
                await log_deletion(db_pool, data_type.value, count, batch_num)

                await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error cleaning up uploaded resumes: {e}")
        await log_deletion(db_pool, data_type.value, 0, 0, str(e))
        return {"status": "error", "error": str(e)}

    return {"status": "success", "deleted": total_deleted}


async def cleanup_api_logs(
    db_pool: asyncpg.Pool, policy: DataRetentionPolicy, dry_run: bool = False
) -> dict[str, Any]:
    """Clean up old API logs."""
    data_type = DataType.API_LOGS
    cutoff = policy.get_cutoff_date(data_type)
    batch_size = policy.get_policy(data_type).batch_size if policy.get_policy(data_type) else 10000

    total_deleted = 0

    try:
        async with db_pool.acquire() as conn:
            count_result = await conn.fetchval(
                "SELECT COUNT(*) FROM api_logs WHERE created_at < $1",
                cutoff,
            )
            logger.info(f"Found {count_result} API logs eligible for deletion")

            if dry_run:
                return {"status": "dry_run", "would_delete": count_result}

            batch_num = 0
            while True:
                batch_num += 1
                ids = await conn.fetch(
                    """
                    SELECT id FROM api_logs
                    WHERE created_at < $1
                    LIMIT $2
                    """,
                    cutoff,
                    batch_size,
                )

                if not ids:
                    break

                id_list = [r["id"] for r in ids]
                deleted = await conn.execute(
                    "DELETE FROM api_logs WHERE id = ANY($1)", id_list
                )
                count = len(id_list)
                total_deleted += count

                logger.info(f"Batch {batch_num}: deleted {count} API logs")
                await log_deletion(db_pool, data_type.value, count, batch_num)

                await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error cleaning up API logs: {e}")
        await log_deletion(db_pool, data_type.value, 0, 0, str(e))
        return {"status": "error", "error": str(e)}

    return {"status": "success", "deleted": total_deleted}


async def run_retention_cleanup(
    db_pool: asyncpg.Pool,
    policy: DataRetentionPolicy | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run the full retention cleanup process.

    Args:
        db_pool: Database connection pool
        policy: Retention policy to use (defaults to global)
        dry_run: If True, only count records without deleting

    Returns:
        Dictionary with results for each data type
    """
    global _job_id
    _job_id = str(uuid.uuid4())  # New job ID for each run

    if policy is None:
        policy = get_retention_policy()

    logger.info(f"Starting data retention cleanup (job_id: {_job_id})")
    logger.info(f"Configuration: {policy.config}")

    results = {}

    # Run cleanup for each data type
    cleanup_tasks = [
        (DataType.SESSION_LOGS, cleanup_session_logs),
        (DataType.ANALYTICS_EVENTS, cleanup_analytics_events),
        (DataType.APPLICATION_DATA, cleanup_application_data),
        (DataType.UPLOADED_RESUMES, cleanup_uploaded_resumes),
        (DataType.API_LOGS, cleanup_api_logs),
    ]

    for data_type, cleanup_func in cleanup_tasks:
        try:
            logger.info(f"Processing {data_type.value}...")
            result = await cleanup_func(db_pool, policy, dry_run)
            results[data_type.value] = result

            # Log job start in retention_logs
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO data_retention_logs
                    (job_id, data_type, deleted_count, batch_number, error_message, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    _job_id,
                    f"{data_type.value}_started",
                    0,
                    0,
                    f"Dry run: {dry_run}",
                    datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Error processing {data_type.value}: {e}")
            results[data_type.value] = {"status": "error", "error": str(e)}

    logger.info(f"Data retention cleanup completed (job_id: {_job_id})")
    return results


async def run_cleanup_loop():
    """Main cleanup loop - runs periodically based on configuration."""
    settings = get_settings()
    policy = get_retention_policy()
    db_pool = await create_db_pool()

    # Determine if dry run from environment
    dry_run = os.environ.get("RETENTION_DRY_RUN", "false").lower() == "true"

    logger.info("Data retention worker started")
    logger.info(f"Run interval: {policy.config.run_interval_hours} hours")
    logger.info(f"Dry run mode: {dry_run}")

    # Run initial cleanup on startup
    try:
        logger.info("Running initial cleanup...")
        await run_retention_cleanup(db_pool, policy, dry_run)
    except Exception as e:
        logger.error(f"Initial cleanup failed: {e}")

    while not _shutdown:
        try:
            # Calculate sleep time based on configuration
            interval_seconds = policy.config.run_interval_hours * 3600
            logger.info(f"Sleeping for {interval_seconds / 3600} hours...")

            for _ in range(interval_seconds):
                if _shutdown:
                    break
                await asyncio.sleep(1)

            if not _shutdown:
                logger.info("Running scheduled cleanup...")
                await run_retention_cleanup(db_pool, policy, dry_run)

        except Exception as e:
            logger.error(f"Cleanup cycle failed: {e}")

    # Cleanup
    await db_pool.close()
    logger.info("Data retention worker stopped")


def main():
    """Entry point for the data retention worker."""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Run the async main
    asyncio.run(run_cleanup_loop())


if __name__ == "__main__":
    main()
