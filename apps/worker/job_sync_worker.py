"""Background worker for scheduled job synchronization.
Runs every 4 hours to fetch fresh jobs from all sources.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import time

# Add project paths before imports (E402: import not at top - required for worker)
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "packages"))

import asyncpg  # noqa: E402

from packages.backend.domain.job_sync_service import JobSyncService  # noqa: E402
from shared.config import get_settings  # noqa: E402
from shared.logging_config import get_logger  # noqa: E402

logger = get_logger("sorce.job_sync_worker")

_shutdown = False


def handle_shutdown(signum, _frame):
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


async def ensure_job_sync_tables(db_pool):
    """Create job sync tables if they don't exist, and add missing columns to existing tables."""
    async with db_pool.acquire() as conn:
        # Create popular_searches table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.popular_searches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                search_term TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT 'Remote',
                search_count INTEGER NOT NULL DEFAULT 1,
                last_searched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE(search_term, location)
            )
        """)
        
        # Add missing columns to job_sync_runs if they exist
        try:
            await conn.execute("""
                ALTER TABLE public.job_sync_runs ADD COLUMN IF NOT EXISTS search_term TEXT
            """)
            await conn.execute("""
                ALTER TABLE public.job_sync_runs ADD COLUMN IF NOT EXISTS location TEXT
            """)
        except Exception as e:
            logger.debug("Columns may already exist: %s", e)
        
        # Add missing columns to job_sync_config if they exist
        try:
            await conn.execute("""
                ALTER TABLE public.job_sync_config ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN DEFAULT TRUE
            """)
            await conn.execute("""
                ALTER TABLE public.job_sync_config ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid()
            """)
        except Exception as e:
            logger.debug("Columns may already exist: %s", e)
        
        # Create job_sync_runs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.job_sync_runs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                completed_at TIMESTAMPTZ,
                jobs_fetched INTEGER NOT NULL DEFAULT 0,
                jobs_new INTEGER NOT NULL DEFAULT 0,
                jobs_updated INTEGER NOT NULL DEFAULT 0,
                jobs_skipped INTEGER NOT NULL DEFAULT 0,
                errors JSONB NOT NULL DEFAULT '[]'::jsonb,
                duration_ms INTEGER,
                search_term TEXT,
                location TEXT
            )
        """)
        
        # Create job_sync_config table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.job_sync_config (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source TEXT UNIQUE NOT NULL,
                is_enabled BOOLEAN DEFAULT TRUE,
                enabled BOOLEAN DEFAULT TRUE,
                last_synced_at TIMESTAMPTZ,
                sync_interval_hours INTEGER DEFAULT 4,
                max_results INTEGER DEFAULT 50,
                search_queries JSONB DEFAULT '[]',
                config JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        
        # Create job_source_stats table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.job_source_stats (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source TEXT UNIQUE NOT NULL,
                total_jobs INTEGER NOT NULL DEFAULT 0,
                new_jobs_24h INTEGER NOT NULL DEFAULT 0,
                updated_jobs_24h INTEGER NOT NULL DEFAULT 0,
                avg_quality_score REAL,
                last_updated TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        
        # Insert default sync sources
        await conn.execute("""
            INSERT INTO public.job_sync_config (source, is_enabled, enabled, config)
            VALUES 
                ('indeed', true, true, '{"rate_limit": 100, "priority": 1}'::jsonb),
                ('linkedin', true, true, '{"rate_limit": 50, "priority": 2}'::jsonb),
                ('zip_recruiter', true, true, '{"rate_limit": 100, "priority": 3}'::jsonb),
                ('glassdoor', true, true, '{"rate_limit": 50, "priority": 4}'::jsonb)
            ON CONFLICT (source) DO NOTHING
        """)
        
        logger.info("Job sync tables created/verified")


async def run_sync_loop():
    """Main sync loop - runs every 4 hours."""
    settings = get_settings()
    db_pool = await create_db_pool()
    
    # Ensure tables exist before starting
    await ensure_job_sync_tables(db_pool)
    
    sync_service = JobSyncService(db_pool, settings)

    logger.info("Job sync worker started")
    logger.info(f"Sources: {sync_service.jobspy.sources}")
    logger.info(
        f"Sync interval: {getattr(settings, 'jobspy_sync_interval_hours', 3)} hours"
    )

    # Run initial sync on startup
    try:
        logger.info("Running initial sync...")
        await sync_service.sync_all_sources(max_concurrent=2)
    except Exception as e:
        logger.error(f"Initial sync failed: {e}")

    while not _shutdown:
        try:
            # Calculate sleep time (4 hours default)
            interval_hours = getattr(settings, "jobspy_sync_interval_hours", 3)
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
            logger.info(
                f"Sync completed in {duration:.1f}s with {len(results)} results"
            )

        except Exception as e:
            logger.error(f"Sync loop error: {e}")
            # Sleep 5 minutes on error before retrying, but check for shutdown periodically
            for _ in range(300):
                if _shutdown:
                    break
                await asyncio.sleep(1)

    await db_pool.close()
    logger.info("Job sync worker stopped")


def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    asyncio.run(run_sync_loop())


if __name__ == "__main__":
    main()
