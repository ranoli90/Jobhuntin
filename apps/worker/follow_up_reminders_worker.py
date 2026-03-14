"""Background worker for follow-up reminders.
Polls pending reminders and sends them (email or in-app).
Runs every 15 minutes.
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

from packages.backend.domain.follow_up_reminders import (
    create_follow_up_manager,  # noqa: E402
)
from packages.backend.domain.job_queue import (
    create_follow_up_reminders_table,  # noqa: E402
)
from shared.config import get_settings  # noqa: E402
from shared.logging_config import get_logger  # noqa: E402

logger = get_logger("sorce.follow_up_reminders_worker")

_shutdown = False
POLL_INTERVAL_SEC = 15 * 60  # 15 minutes


def handle_shutdown(signum, _frame):
    global _shutdown
    logger.info("Received signal %s, shutting down...", signum)
    _shutdown = True


async def create_db_pool() -> asyncpg.Pool:
    import ssl

    settings = get_settings()
    from shared.db import resolve_dsn_ipv4

    dsn = resolve_dsn_ipv4(settings.database_url)
    # Use SSL but don't verify certificate for self-signed certs on Render
    # The connection is still encrypted, just not verified against a CA
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return await asyncpg.create_pool(
        dsn,
        min_size=1,
        max_size=3,
        statement_cache_size=0,
        ssl=ctx,
        timeout=30.0,
        command_timeout=60.0,
    )


async def run_reminders_loop() -> None:
    db_pool = await create_db_pool()

    # Create tables if they don't exist
    async with db_pool.acquire() as conn:
        await create_follow_up_reminders_table(conn)

    manager = create_follow_up_manager(db_pool)

    logger.info(
        "Follow-up reminders worker started (poll every %d min)",
        POLL_INTERVAL_SEC // 60,
    )

    while not _shutdown:
        try:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    # WORK-001: Atomic claim with FOR UPDATE SKIP LOCKED
                    pending = await manager.claim_pending_reminders(conn, limit=50)
                    if pending:
                        logger.info("Processing %d pending reminders", len(pending))
                        # WORK-006: Send in parallel (batches of 5) so one slow send doesn't block others
                        batch_size = 5
                        sent = 0
                        for i in range(0, len(pending), batch_size):
                            batch = pending[i : i + batch_size]
                            results = await asyncio.gather(
                                *[manager.send_reminder(r.id, conn=conn) for r in batch],
                                return_exceptions=True,
                            )
                            for j, res in enumerate(results):
                                if res is True:
                                    sent += 1
                                elif isinstance(res, Exception):
                                    logger.error("Failed to send reminder %s: %s", batch[j].id, res)
                        if sent:
                            logger.info("Sent %d reminders", sent)
        except Exception as e:
            logger.error("Reminders loop error: %s", e)

        for _ in range(int(POLL_INTERVAL_SEC / 60)):
            if _shutdown:
                break
            await asyncio.sleep(60)

    await db_pool.close()
    logger.info("Follow-up reminders worker stopped")


def main() -> None:
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    asyncio.run(run_reminders_loop())


if __name__ == "__main__":
    main()
