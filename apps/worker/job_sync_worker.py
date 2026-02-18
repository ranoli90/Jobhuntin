"""
Background worker for scheduled job synchronization.
Runs every 4 hours to fetch fresh jobs from all sources.
"""
from __future__ import annotations

import asyncio
import os
import signal
import sys
import time

# Add project paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "packages"))

import asyncpg
from shared.config import get_settings
from shared.logging_config import get_logger

from backend.domain.job_sync_service import JobSyncService

logger = get_logger("sorce.job_sync_worker")

_shutdown = False


def handle_shutdown(signum, frame):
    global _shutdown
    logger.info(f"Received signal {signum}, shutting down...")
    _shutdown = True


async def create_db_pool():
    """Create database connection pool."""
    settings = get_settings()
    return await asyncpg.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        min_size=2,
        max_size=10,
    )


async def run_sync_loop():
    """Main sync loop - runs every 4 hours."""
    global _shutdown

    settings = get_settings()
    db_pool = await create_db_pool()
    sync_service = JobSyncService(db_pool, settings)

    logger.info("Job sync worker started")
    logger.info(f"Sources: {sync_service.jobspy.sources}")
    logger.info(f"Sync interval: {getattr(settings, 'jobspy_sync_interval_hours', 4)} hours")

    # Run initial sync on startup
    try:
        logger.info("Running initial sync...")
        await sync_service.sync_all_sources(max_concurrent=2)
    except Exception as e:
        logger.error(f"Initial sync failed: {e}")

    while not _shutdown:
        try:
            # Calculate sleep time (4 hours default)
            interval_hours = getattr(settings, 'jobspy_sync_interval_hours', 4)
            sleep_seconds = interval_hours * 60 * 60

            logger.info(f"Sleeping for {interval_hours} hours until next sync...")

            # Sleep in 60-second intervals to check for shutdown
            for _ in range(int(sleep_seconds / 60)):
                if _shutdown:
                    break
                await asyncio.sleep(60)

            if _shutdown:
                break

            logger.info("Starting scheduled job sync...")
            start_time = time.time()

            results = await sync_service.sync_all_sources(max_concurrent=2)

            duration = time.time() - start_time
            logger.info(f"Sync completed in {duration:.1f}s with {len(results)} results")

        except Exception as e:
            logger.error(f"Sync loop error: {e}")
            # Sleep 5 minutes on error before retrying
            await asyncio.sleep(300)

    await db_pool.close()
    logger.info("Job sync worker stopped")


def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    asyncio.run(run_sync_loop())


if __name__ == "__main__":
    main()
