"""
Worker horizontal scaling — manages multiple concurrent Playwright instances
with connection pooling, read replicas, and enterprise-dedicated pools.

Usage:
    python -m worker.scaling --instances 10
"""

from __future__ import annotations

import asyncio
import contextlib
import signal
import sys
from typing import Any

import asyncpg

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.worker.scaling")


async def create_primary_pool() -> asyncpg.Pool:
    """Create the primary write DB pool."""
    s = get_settings()
    from shared.db import resolve_dsn_ipv4
    return await asyncpg.create_pool(
        resolve_dsn_ipv4(s.database_url),
        min_size=s.db_pool_min,
        max_size=s.db_pool_max,
        command_timeout=60,
    )


async def create_read_replica_pool() -> asyncpg.Pool | None:
    """Create a read replica pool if configured."""
    s = get_settings()
    if not s.read_replica_url:
        logger.info("No read replica configured; using primary for reads")
        return None
    from shared.db import resolve_dsn_ipv4
    return await asyncpg.create_pool(
        resolve_dsn_ipv4(s.read_replica_url),
        min_size=2,
        max_size=s.db_pool_max,
        command_timeout=60,
    )


async def create_enterprise_pool() -> asyncpg.Pool | None:
    """Create a dedicated pool for enterprise tenants."""
    s = get_settings()
    if not s.enterprise_db_pool_min:
        return None
    from shared.db import resolve_dsn_ipv4
    return await asyncpg.create_pool(
        resolve_dsn_ipv4(s.database_url),
        min_size=s.enterprise_db_pool_min,
        max_size=s.enterprise_db_pool_max,
        command_timeout=120,  # longer timeout for enterprise
    )


class WorkerScaler:
    """Manages N concurrent worker instances sharing a pool."""

    def __init__(self, instance_count: int = 1):
        self.instance_count = instance_count
        self.primary_pool: asyncpg.Pool | None = None
        self.read_pool: asyncpg.Pool | None = None
        self.enterprise_pool: asyncpg.Pool | None = None
        self._shutdown = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Initialize pools and launch worker instances."""
        logger.info("Starting %d worker instances...", self.instance_count)

        self.primary_pool = await create_primary_pool()
        self.read_pool = await create_read_replica_pool()
        self.enterprise_pool = await create_enterprise_pool()

        # Import here to avoid circular deps
        from worker.agent import run_once

        for i in range(self.instance_count):
            task = asyncio.create_task(
                self._worker_loop(i, run_once),
                name=f"worker-{i}",
            )
            self._tasks.append(task)

        logger.info(
            "All %d workers started (primary_pool=%d/%d, read_replica=%s, enterprise_pool=%s)",
            self.instance_count,
            self.primary_pool.get_min_size(),
            self.primary_pool.get_max_size(),
            "yes" if self.read_pool else "no",
            "yes" if self.enterprise_pool else "no",
        )

    async def _worker_loop(self, instance_id: int, run_once_fn: Any) -> None:
        """Single worker loop — claims and processes tasks."""
        s = get_settings()
        while not self._shutdown.is_set():
            try:
                pool = self.primary_pool
                if pool is None:
                    break
                processed = await run_once_fn(pool)
                if not processed:
                    # No task available — back off
                    await asyncio.sleep(s.poll_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Worker-%d error: %s", instance_id, exc, exc_info=True)
                await asyncio.sleep(5)

    async def shutdown(self) -> None:
        """Gracefully shutdown all workers and pools."""
        logger.info("Shutting down %d workers...", self.instance_count)
        self._shutdown.set()

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        if self.primary_pool:
            await self.primary_pool.close()
        if self.read_pool:
            await self.read_pool.close()
        if self.enterprise_pool:
            await self.enterprise_pool.close()

        logger.info("All workers shut down.")

    def get_pool_stats(self) -> dict[str, Any]:
        """Return connection pool statistics."""
        stats: dict[str, Any] = {}
        if self.primary_pool:
            stats["primary"] = {
                "size": self.primary_pool.get_size(),
                "free": self.primary_pool.get_idle_size(),
                "min": self.primary_pool.get_min_size(),
                "max": self.primary_pool.get_max_size(),
            }
        if self.read_pool:
            stats["read_replica"] = {
                "size": self.read_pool.get_size(),
                "free": self.read_pool.get_idle_size(),
            }
        if self.enterprise_pool:
            stats["enterprise"] = {
                "size": self.enterprise_pool.get_size(),
                "free": self.enterprise_pool.get_idle_size(),
            }
        return stats


async def main() -> None:
    """Entry point for scaled worker."""
    s = get_settings()
    count = s.worker_instance_count

    # Parse CLI override
    if "--instances" in sys.argv:
        idx = sys.argv.index("--instances")
        if idx + 1 < len(sys.argv):
            count = int(sys.argv[idx + 1])

    scaler = WorkerScaler(instance_count=count)

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(scaler.shutdown()))

    await scaler.start()

    # Wait for shutdown
    await scaler._shutdown.wait()
    await scaler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
