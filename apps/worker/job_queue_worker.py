"""Background job queue worker.
Polls public.background_jobs and processes jobs with registered handlers.
Runs every 5 seconds.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "packages"))

import asyncpg  # noqa: E402

from packages.backend.domain.job_queue import BackgroundJobQueue, JobResult  # noqa: E402
from shared.config import get_settings  # noqa: E402
from shared.logging_config import get_logger  # noqa: E402

logger = get_logger("sorce.job_queue_worker")

_shutdown = False
POLL_INTERVAL_SEC = 5


def handle_shutdown(signum, _frame):
    global _shutdown
    logger.info("Received signal %s, shutting down...", signum)
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


async def create_db_pool() -> asyncpg.Pool:
    settings = get_settings()
    from shared.db import resolve_dsn_ipv4

    dsn = resolve_dsn_ipv4(settings.database_url)
    ssl_arg = _get_ssl_config(settings)
    return await asyncpg.create_pool(
        dsn,
        min_size=1,
        max_size=3,
        statement_cache_size=0,
        ssl=ssl_arg,
        timeout=30.0,
        command_timeout=60.0,
    )


async def run_queue_loop() -> None:
    db_pool = await create_db_pool()

    # Create tables if they don't exist
    async with db_pool.acquire() as conn:
        from packages.backend.domain.job_queue import (
            create_follow_up_reminders_table,
            create_job_queue_tables,
        )
        await create_job_queue_tables(conn)
        await create_follow_up_reminders_table(conn)

    queue = BackgroundJobQueue(db_pool)

    # LOW: Register match score pre-computation job handler
    try:
        from packages.backend.domain.match_score_precompute import register_match_score_job_handler

        register_match_score_job_handler(queue)
    except Exception as e:
        logger.warning("Failed to register match score pre-computation handler: %s", e)

    # Placeholder handlers: fail until real implementations are added for each job type
    async def not_implemented_handler(payload: dict) -> JobResult:
        logger.warning(
            "Handler not implemented for job payload: %s", list(payload.keys())
        )
        return JobResult(
            success=False, result={"error": "handler_not_implemented"}, retry=False
        )

    queue.register_handler("email_send", not_implemented_handler)
    queue.register_handler("notification", not_implemented_handler)
    queue.register_handler("digest", not_implemented_handler)

    logger.info("Job queue worker started (poll every %ds)", POLL_INTERVAL_SEC)

    consecutive_errors = 0
    while not _shutdown:
        try:
            processed = await queue.process_jobs(batch_size=5)
            if processed:
                logger.info("Processed %d jobs", processed)
                consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            logger.error("Job queue loop error: %s", e)
            # WORK-004: Backoff on repeated failure (e.g. external API down)
            backoff = min(60, 5 * (2 ** min(consecutive_errors - 1, 4)))
            logger.info("Backing off %ds before next poll", backoff)
            for _ in range(backoff):
                if _shutdown:
                    break
                await asyncio.sleep(1)
            continue

        for _ in range(POLL_INTERVAL_SEC):
            if _shutdown:
                break
            await asyncio.sleep(1)

    await db_pool.close()
    logger.info("Job queue worker stopped")


def main() -> None:
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    asyncio.run(run_queue_loop())


if __name__ == "__main__":
    main()
