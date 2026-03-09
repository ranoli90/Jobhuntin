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
from shared.config import get_settings  # noqa: E402
from shared.logging_config import get_logger  # noqa: E402

logger = get_logger("sorce.follow_up_reminders_worker")

_shutdown = False
POLL_INTERVAL_SEC = 15 * 60  # 15 minutes


def handle_shutdown(signum, frame):  # noqa: ARG001
    global _shutdown
    logger.info("Received signal %s, shutting down...", signum)
    _shutdown = True


async def create_db_pool() -> asyncpg.Pool:
    settings = get_settings()
    return await asyncpg.create_pool(
        settings.database_url,
        min_size=1,
        max_size=3,
    )


async def run_reminders_loop() -> None:
    db_pool = await create_db_pool()
    manager = create_follow_up_manager(db_pool)

    logger.info("Follow-up reminders worker started (poll every %d min)", POLL_INTERVAL_SEC // 60)

    while not _shutdown:
        try:
            pending = await manager.get_pending_reminders(limit=50)
            if pending:
                logger.info("Processing %d pending reminders", len(pending))
                sent = 0
                for reminder in pending:
                    try:
                        ok = await manager.send_reminder(reminder.id)
                        if ok:
                            sent += 1
                    except Exception as e:
                        logger.error("Failed to send reminder %s: %s", reminder.id, e)
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
