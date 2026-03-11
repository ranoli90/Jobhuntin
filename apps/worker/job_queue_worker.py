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

from packages.backend.domain.job_queue import (  # noqa: E402
    BackgroundJobQueue,
    JobResult,
)
from shared.config import get_settings  # noqa: E402
from shared.logging_config import get_logger  # noqa: E402

logger = get_logger("sorce.job_queue_worker")

_shutdown = False
POLL_INTERVAL_SEC = 5


def handle_shutdown(signum, _frame):
    global _shutdown
    logger.info("Received signal %s, shutting down...", signum)
    _shutdown = True


async def create_db_pool() -> asyncpg.Pool:
    import ssl

    settings = get_settings()
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = True
    return await asyncpg.create_pool(
        settings.database_url,
        min_size=1,
        max_size=3,
        statement_cache_size=0,
        ssl=ctx,
        timeout=30.0,
        command_timeout=60.0,
    )


async def run_queue_loop() -> None:
    db_pool = await create_db_pool()
    queue = BackgroundJobQueue(db_pool)

    # LOW: Register match score pre-computation job handler
    try:
        from packages.backend.domain.match_score_precompute import (
            register_match_score_job_handler,
        )

        register_match_score_job_handler(queue)
    except Exception as e:
        logger.warning("Failed to register match score pre-computation handler: %s", e)

    # Register placeholder handlers — extend as job types are added
    async def noop_handler(payload: dict) -> JobResult:
        logger.warning("No handler for job payload: %s", list(payload.keys()))
        return JobResult(success=True, result={"skipped": "no_handler"})

    queue.register_handler("email_send", noop_handler)
    queue.register_handler("notification", noop_handler)
    queue.register_handler("digest", noop_handler)

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
