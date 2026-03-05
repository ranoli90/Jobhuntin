"""Worker horizontal scaling — manages multiple concurrent Playwright instances
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
from shared.metrics import incr, observe

logger = get_logger("sorce.worker.scaling")


def _get_ssl_config() -> Any:
    """Get SSL configuration for database connections."""
    # Render databases use SSL by default; our DSN resolver enforces sslmode=require
    # No special SSL context needed; asyncpg handles it when sslmode is in DSN
    return None  # pylint: disable=useless-return


async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool with robust retries and Render-compatible settings."""
    s = get_settings()
    from shared.db import resolve_dsn_ipv4

    ssl = _get_ssl_config()  # pylint: disable=assignment-from-none
    kwargs: dict[str, Any] = {
        "min_size": s.db_pool_min,
        "max_size": s.db_pool_max,
        "command_timeout": 60,
        "statement_cache_size": 0,  # Critical for PGBouncer/Render
    }
    if ssl:
        kwargs["ssl"] = ssl

    for attempt in range(1, 4):
        try:
            dsn = resolve_dsn_ipv4(s.database_url)
            return await asyncpg.create_pool(dsn, **kwargs)
        except asyncpg.PostgresError as exc:
            error_msg = str(exc)
            if "password authentication failed" in error_msg.lower():
                logger.warning(
                    "Primary DB pool attempt %d/3 failed: %s. "
                    "Check your DATABASE_URL credentials.",
                    attempt,
                    exc,
                )
            elif (
                "connection refused" in error_msg.lower()
                or "could not connect" in error_msg.lower()
            ):
                logger.warning(
                    "Primary DB pool attempt %d/3 failed: %s. "
                    "Check that the database host is accessible.",
                    attempt,
                    exc,
                )
            else:
                logger.warning("Primary DB pool attempt %d/3 failed: %s", attempt, exc)
            if attempt < 3:
                await asyncio.sleep(3 * attempt)
        except Exception as exc:
            logger.error("Unexpected error creating primary DB pool: %s", exc)
            raise

    raise RuntimeError("Could not create primary DB pool after 3 attempts")


async def create_read_replica_pool() -> asyncpg.Pool | None:
    """Create a read replica pool if configured."""
    s = get_settings()
    if not s.read_replica_url:
        logger.info("No read replica configured; using primary for reads")
        return None
    from shared.db import resolve_dsn_ipv4

    ssl = _get_ssl_config()  # pylint: disable=assignment-from-none
    kwargs: dict[str, Any] = {
        "min_size": 2,
        "max_size": s.db_pool_max,
        "command_timeout": 60,
        "statement_cache_size": 0,  # Critical for PGBouncer/Render
    }
    if ssl:
        kwargs["ssl"] = ssl

    for attempt in range(1, 4):
        try:
            return await asyncpg.create_pool(
                resolve_dsn_ipv4(s.read_replica_url), **kwargs
            )
        except asyncpg.PostgresError as exc:
            error_msg = str(exc)
            if (
                "Tenant or user not found" in error_msg
                or "password authentication failed" in error_msg
            ):
                logger.warning(
                    "Read replica DB pool attempt %d/3 failed: %s. "
                    "This usually means READ_REPLICA_URL credentials are incorrect. "
                    "Check that the read replica credentials match your Render PostgreSQL database.",
                    attempt,
                    exc,
                )
            elif (
                "connection refused" in error_msg.lower()
                or "could not connect" in error_msg.lower()
            ):
                logger.warning(
                    "Read replica DB pool attempt %d/3 failed: %s. "
                    "Check that the read replica host is accessible and the port is correct.",
                    attempt,
                    exc,
                )
            else:
                logger.warning(
                    "Read replica DB pool attempt %d/3 failed: %s", attempt, exc
                )
            if attempt < 3:
                await asyncio.sleep(3 * attempt)
        except Exception as exc:
            logger.error("Unexpected error creating read replica DB pool: %s", exc)
            raise

    logger.warning(
        "Could not create read replica DB pool after 3 attempts; using primary for reads"
    )
    return None


async def create_enterprise_pool() -> asyncpg.Pool | None:
    """Create a dedicated pool for enterprise tenants."""
    s = get_settings()
    if not s.enterprise_db_pool_min:
        return None
    from shared.db import resolve_dsn_ipv4

    ssl = _get_ssl_config()  # pylint: disable=assignment-from-none
    kwargs: dict[str, Any] = {
        "min_size": s.enterprise_db_pool_min,
        "max_size": s.enterprise_db_pool_max,
        "command_timeout": 120,
        "statement_cache_size": 0,  # Critical for PGBouncer/Render
    }
    if ssl:
        kwargs["ssl"] = ssl

    for attempt in range(1, 4):
        try:
            return await asyncpg.create_pool(resolve_dsn_ipv4(s.database_url), **kwargs)
        except asyncpg.PostgresError as exc:
            error_msg = str(exc)
            if (
                "Tenant or user not found" in error_msg
                or "password authentication failed" in error_msg
            ):
                logger.warning(
                    "Enterprise DB pool attempt %d/3 failed: %s. "
                    "This usually means DATABASE_URL credentials are incorrect. "
                    "Check that DB_USER, DB_PASSWORD, and DB_NAME match your Render PostgreSQL database.",
                    attempt,
                    exc,
                )
            elif (
                "connection refused" in error_msg.lower()
                or "could not connect" in error_msg.lower()
            ):
                logger.warning(
                    "Enterprise DB pool attempt %d/3 failed: %s. "
                    "Check that the database host is accessible and the port is correct.",
                    attempt,
                    exc,
                )
            else:
                logger.warning(
                    "Enterprise DB pool attempt %d/3 failed: %s", attempt, exc
                )
            if attempt < 3:
                await asyncio.sleep(3 * attempt)
        except Exception as exc:
            logger.error("Unexpected error creating enterprise DB pool: %s", exc)
            raise

    logger.warning(
        "Could not create enterprise DB pool after 3 attempts; using primary pool"
    )
    return None


# ---------------------------------------------------------------------------
# BrowserPoolManager — supports local Chromium and remote Browserless.io
# ---------------------------------------------------------------------------


class BrowserPoolManager:
    """Manages Playwright browser lifecycle with support for:
    - Local Chromium launch (default)
    - Remote Browserless.io via CDP (when browserless_url is configured)
    - Context recycling after N uses to prevent memory leaks
    - Active context count and usage metrics.
    """

    def __init__(self) -> None:
        self._playwright: Any = None
        self._browser: Any = None
        self._is_remote: bool = False
        self._context_use_counts: dict[int, int] = {}  # context id -> use count
        self._active_contexts: int = 0
        self._total_contexts_created: int = 0
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Initialize Playwright and connect/launch browser."""
        from playwright.async_api import async_playwright

        s = get_settings()

        self._playwright = await async_playwright().start()

        if s.browserless_url:
            # Remote browser via CDP (Browserless.io or compatible)
            url = s.browserless_url
            if s.browserless_token and "token=" not in url:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}token={s.browserless_token}"
            self._browser = await self._playwright.chromium.connect_over_cdp(url)
            self._is_remote = True
            logger.info(
                "Connected to remote browser via CDP: %s",
                s.browserless_url.split("?")[0],
            )
        else:
            # Local Chromium
            self._browser = await self._playwright.chromium.launch(
                headless=s.playwright_headless
            )
            self._is_remote = False
            logger.info("Launched local Chromium (headless=%s)", s.playwright_headless)

    # Realistic Chrome user-agent strings for rotation
    _USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    ]

    # Viewport sizes that look like real desktop monitors
    _VIEWPORTS = [
        {"width": 1280, "height": 800},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
        {"width": 1920, "height": 1080},
        {"width": 1280, "height": 720},
    ]

    async def create_context(self) -> Any:
        """Create a new browser context with randomized viewport and user-agent."""
        import random  # nosec B311 - random.choice used for browser fingerprinting, not security purposes

        if not self._browser:
            raise RuntimeError("BrowserPoolManager not started")

        viewport = random.choice(self._VIEWPORTS)  # nosec B311 - browser fingerprinting
        ua = random.choice(self._USER_AGENTS)  # nosec B311 - browser fingerprinting

        ctx = await self._browser.new_context(  # nosec B311
            viewport=viewport,
            user_agent=ua,
            # nosec B311 - browser fingerprinting
            locale=random.choice(["en-US", "en-GB", "en-CA"]),
            timezone_id=random.choice(  # nosec B311 - browser fingerprinting
                [
                    "America/New_York",
                    "America/Chicago",
                    "America/Los_Angeles",
                    "America/Denver",
                ]
            ),
        )
        async with self._lock:
            self._active_contexts += 1
            self._total_contexts_created += 1
            self._context_use_counts[id(ctx)] = 0
        incr("browser.context.created")
        observe("browser.active_contexts", float(self._active_contexts))
        return ctx

    async def record_context_use(self, ctx: Any) -> bool:
        """Record a use of the context. Returns True if context should be recycled
        (exceeded max_uses threshold).
        """
        s = get_settings()
        async with self._lock:
            ctx_id = id(ctx)
            self._context_use_counts[ctx_id] = (
                self._context_use_counts.get(ctx_id, 0) + 1
            )
            uses = self._context_use_counts[ctx_id]
        return uses >= s.browser_context_max_uses

    async def close_context(self, ctx: Any) -> None:
        """Close a browser context and update metrics."""
        try:
            await ctx.close()
        except Exception as exc:
            logger.warning("Error closing browser context: %s", exc)
        async with self._lock:
            self._active_contexts = max(0, self._active_contexts - 1)
            self._context_use_counts.pop(id(ctx), None)
        incr("browser.context.closed")
        observe("browser.active_contexts", float(self._active_contexts))

    async def shutdown(self) -> None:
        """Close the browser and Playwright."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception as exc:
                logger.warning("Error closing browser: %s", exc)
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as exc:
                logger.warning("Error stopping Playwright: %s", exc)
            self._playwright = None
        logger.info("BrowserPoolManager shut down")

    def get_stats(self) -> dict[str, Any]:
        """Return browser pool statistics for health checks."""
        return {
            "is_remote": self._is_remote,
            "active_contexts": self._active_contexts,
            "total_contexts_created": self._total_contexts_created,
            "context_use_counts": dict(self._context_use_counts),
        }


class WorkerScaler:
    """Manages N concurrent worker instances sharing a pool and browser."""

    def __init__(self, instance_count: int = 1):
        self.instance_count = instance_count
        self.primary_pool: asyncpg.Pool | None = None
        self.read_pool: asyncpg.Pool | None = None
        self.enterprise_pool: asyncpg.Pool | None = None
        self.browser_pool: BrowserPoolManager | None = None
        self._shutdown = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Initialize pools, browser, and launch worker instances."""
        logger.info("Starting %d worker instances...", self.instance_count)

        self.primary_pool = await get_db_pool()
        self.read_pool = await create_read_replica_pool()
        self.enterprise_pool = await create_enterprise_pool()

        # Initialize BrowserPoolManager (supports local and remote browsers)
        self.browser_pool = BrowserPoolManager()
        await self.browser_pool.start()

        async def context_factory():
            return await self.browser_pool.create_context()

        from worker.agent import FormAgent

        for i in range(self.instance_count):
            task = asyncio.create_task(
                self._worker_loop(i, FormAgent, context_factory),
                name=f"worker-{i}",
            )
            self._tasks.append(task)

        logger.info(
            "All %d workers started (primary_pool=%d/%d, read_replica=%s, enterprise_pool=%s, browser=%s)",
            self.instance_count,
            self.primary_pool.get_min_size(),
            self.primary_pool.get_max_size(),
            "yes" if self.read_pool else "no",
            "yes" if self.enterprise_pool else "no",
            "remote" if self.browser_pool._is_remote else "local",
        )

    async def _worker_loop(
        self, instance_id: int, agent_cls: Any, context_factory: Any
    ) -> None:
        """Single worker loop — claims and processes tasks."""
        s = get_settings()

        # Instantiate the agent for this worker
        # We share the primary pool.
        # Ideally, we might want dedicated pools per worker if we were strictly following the original design,
        # but sharing an asyncpg pool is thread/task-safe and efficient.
        agent = agent_cls(self.primary_pool, context_factory)

        while not self._shutdown.is_set():
            try:
                if self.primary_pool is None:
                    break

                processed = await agent.run_once()
                if not processed:
                    # No task available — back off
                    await asyncio.sleep(s.poll_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Worker-%d error: %s", instance_id, exc, exc_info=True)
                await asyncio.sleep(5)

    async def shutdown(self) -> None:
        """Gracefully shutdown all workers, browser, and pools."""
        if self._shutdown.is_set() and not self._tasks:
            # Already shut down
            return

        logger.info("Shutting down %d workers...", self.instance_count)
        self._shutdown.set()

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # Close browser pool
        if self.browser_pool:
            await self.browser_pool.shutdown()
            self.browser_pool = None

        if self.primary_pool:
            await self.primary_pool.close()
            self.primary_pool = None
        if self.read_pool:
            await self.read_pool.close()
            self.read_pool = None
        if self.enterprise_pool:
            await self.enterprise_pool.close()
            self.enterprise_pool = None

        logger.info("All workers shut down.")

    def get_pool_stats(self) -> dict[str, Any]:
        """Return connection pool and browser statistics."""
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
        if self.browser_pool:
            stats["browser"] = self.browser_pool.get_stats()
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
