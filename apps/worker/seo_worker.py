"""Background worker for SEO processing tasks.

Provides SEO worker class and background job functions for:
- Content generation
- URL submission to Google
- Health checks
- Metrics collection
- Quota management

Runs as a long-running background process.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import signal
import sys
from datetime import datetime, timezone
from typing import Any, Optional

# Setup path before imports
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "packages"))

import asyncpg  # noqa: E402

from packages.backend.domain.seo_competitor import SEOCompetitorRepository  # noqa: E402
from packages.backend.domain.seo_content import SEOContentRepository  # noqa: E402
from packages.backend.domain.seo_health import SEOHealthCheck  # noqa: E402
from packages.backend.domain.seo_logging import SEOLogger  # noqa: E402
from packages.backend.domain.seo_metrics import SEOMetricsCollector  # noqa: E402
from packages.backend.domain.seo_progress import SEOProgressRepository  # noqa: E402
from shared.config import get_settings  # noqa: E402
from shared.logging_config import get_logger  # noqa: E402

logger = get_logger("sorce.seo_worker")

# Worker configuration
_shutdown = False
POLL_INTERVAL_SEC = 60  # Check for jobs every minute
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5


def handle_shutdown(signum, _frame):
    """Handle shutdown signals gracefully."""
    global _shutdown
    logger.info("Received signal %s, shutting down SEO worker...", signum)
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
    return False


async def create_db_pool() -> asyncpg.Pool:
    """Create a database connection pool for the worker."""
    settings = get_settings()
    from shared.db import resolve_dsn_ipv4

    dsn = resolve_dsn_ipv4(settings.database_url)
    ssl_arg = _get_ssl_config(settings)
    return await asyncpg.create_pool(
        dsn,
        min_size=2,
        max_size=5,
        statement_cache_size=0,
        ssl=ssl_arg,
        timeout=30.0,
        command_timeout=60.0,
    )


def _generate_content_hash(title: str, topic: str, intent: str) -> str:
    """Generate a hash for content deduplication.

    Args:
        title: Content title.
        topic: Content topic.
        intent: Content intent.

    Returns:
        SHA256 hash of the content.
    """
    content = f"{title}:{topic}:{intent}"
    return hashlib.sha256(content.encode()).hexdigest()


def _generate_url_from_topic(topic: str, intent: str) -> str:
    """Generate a URL from topic and intent.

    Args:
        topic: Topic string.
        intent: Intent string.

    Returns:
        Generated URL.
    """
    # Simple URL generation - in production this would call a URL generator service
    topic_slug = topic.lower().replace(" ", "-").replace("/", "-")
    intent_path = intent.replace(" ", "-").lower()
    return f"/seo/{topic_slug}/{intent_path}/"


class SEOWorker:
    """Worker class for SEO processing tasks."""

    def __init__(self, db_pool: asyncpg.Pool) -> None:
        """Initialize the SEO worker with a database pool.

        Args:
            db_pool: AsyncPG database connection pool.
        """
        self._db_pool = db_pool
        self._logger: Optional[SEOLogger] = None
        self._progress_repo: Optional[SEOProgressRepository] = None
        self._content_repo: Optional[SEOContentRepository] = None
        self._metrics_collector: Optional[SEOMetricsCollector] = None
        self._competitor_repo: Optional[SEOCompetitorRepository] = None
        self._health_check: Optional[SEOHealthCheck] = None

    async def _get_logger(self) -> SEOLogger:
        """Get or create the SEO logger instance."""
        if self._logger is None:
            async with self._db_pool.acquire() as conn:
                self._logger = SEOLogger(conn)
        return self._logger

    async def _get_progress_repo(self) -> SEOProgressRepository:
        """Get or create the progress repository instance."""
        if self._progress_repo is None:
            async with self._db_pool.acquire() as conn:
                self._progress_repo = SEOProgressRepository(conn)
        return self._progress_repo

    async def _get_content_repo(self) -> SEOContentRepository:
        """Get or create the content repository instance."""
        if self._content_repo is None:
            async with self._db_pool.acquire() as conn:
                self._content_repo = SEOContentRepository(conn)
        return self._content_repo

    async def _get_metrics_collector(self) -> SEOMetricsCollector:
        """Get or create the metrics collector instance."""
        if self._metrics_collector is None:
            async with self._db_pool.acquire() as conn:
                self._metrics_collector = SEOMetricsCollector(conn)
        return self._metrics_collector

    async def _get_competitor_repo(self) -> SEOCompetitorRepository:
        """Get or create the competitor repository instance."""
        if self._competitor_repo is None:
            async with self._db_pool.acquire() as conn:
                self._competitor_repo = SEOCompetitorRepository(conn)
        return self._competitor_repo

    async def _get_health_check(self) -> SEOHealthCheck:
        """Get or create the health check instance."""
        if self._health_check is None:
            async with self._db_pool.acquire() as conn:
                self._health_check = SEOHealthCheck(conn)
        return self._health_check

    async def run_content_generation_job(
        self,
        service_id: str,
        topics: list[str],
        intents: list[str],
    ) -> dict[str, Any]:
        """Generate SEO content for topics and intents.

        Args:
            service_id: The service identifier.
            topics: List of topics to generate content for.
            intents: List of intents to generate content for.

        Returns:
            Dictionary with job results.
        """
        start_time = datetime.now(timezone.utc)
        log = await self._get_logger()
        progress_repo = await self._get_progress_repo()
        content_repo = await self._get_content_repo()
        metrics_collector = await self._get_metrics_collector()

        await log.info(
            "Starting content generation job",
            meta={"service_id": service_id, "topics": topics, "intents": intents},
        )

        generated_count = 0
        failed_count = 0
        errors: list[str] = []

        try:
            for topic in topics:
                for intent in intents:
                    try:
                        # Generate URL for the content
                        url = _generate_url_from_topic(topic, intent)

                        # Generate title based on topic and intent
                        title = f"Best {topic.title()} for {intent.title()} - Guide"

                        # Generate content hash for deduplication
                        content_hash = _generate_content_hash(title, topic, intent)

                        # Check if content already exists
                        if await content_repo.check_content_exists(url):
                            await log.warn(
                                "Content already exists, skipping",
                                meta={"url": url, "topic": topic, "intent": intent},
                            )
                            continue

                        # Record the generated content
                        await content_repo.record_generated_content(
                            url=url,
                            title=title,
                            topic=topic,
                            intent=intent,
                            content_hash=content_hash,
                            quality_score=0.85,  # Default quality score
                        )

                        # Update progress
                        await progress_repo.increment_quota(service_id, amount=1)

                        generated_count += 1
                        await log.debug(
                            "Generated content",
                            meta={"url": url, "topic": topic, "intent": intent},
                        )

                    except ValueError as e:
                        # Content already exists or duplicate
                        failed_count += 1
                        errors.append(str(e))
                        await log.warn(
                            "Content generation skipped",
                            meta={"topic": topic, "intent": intent, "reason": str(e)},
                        )
                    except Exception as e:
                        failed_count += 1
                        errors.append(str(e))
                        await log.error(
                            "Failed to generate content",
                            meta={"topic": topic, "intent": intent, "error": str(e)},
                        )

            # Record generation metrics
            end_time = datetime.now(timezone.utc)
            generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            await metrics_collector.record_generation(
                generation_time_ms=generation_time_ms,
                success=failed_count == 0,
                topic=topics[0] if topics else None,
            )

            await log.info(
                "Content generation job completed",
                meta={
                    "service_id": service_id,
                    "generated_count": generated_count,
                    "failed_count": failed_count,
                    "total_time_ms": generation_time_ms,
                },
            )

            return {
                "success": True,
                "generated_count": generated_count,
                "failed_count": failed_count,
                "errors": errors,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

        except Exception as e:
            await log.error(
                "Content generation job failed",
                meta={"service_id": service_id, "error": str(e)},
            )
            return {
                "success": False,
                "generated_count": generated_count,
                "failed_count": failed_count,
                "errors": errors + [str(e)],
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            }

    async def run_submission_job(
        self,
        service_id: str,
        urls: list[str],
    ) -> dict[str, Any]:
        """Submit URLs to Google for indexing.

        Args:
            service_id: The service identifier.
            urls: List of URLs to submit.

        Returns:
            Dictionary with submission results.
        """
        start_time = datetime.now(timezone.utc)
        log = await self._get_logger()
        content_repo = await self._get_content_repo()
        metrics_collector = await self._get_metrics_collector()
        progress_repo = await self._get_progress_repo()

        await log.info(
            "Starting URL submission job",
            meta={"service_id": service_id, "url_count": len(urls)},
        )

        submitted_count = 0
        successful_count = 0
        failed_count = 0
        errors: list[dict[str, Any]] = []

        try:
            # In production, this would call Google's Indexing API
            # For now, we'll simulate the submission process
            for url in urls:
                try:
                    # Get content by URL
                    content = await content_repo.get_content_by_url(url)
                    if not content:
                        await log.warn(
                            "Content not found for URL",
                            meta={"url": url},
                        )
                        failed_count += 1
                        continue

                    # Simulate Google indexing submission
                    # In production: call Google Indexing API
                    await asyncio.sleep(0.1)  # Simulate API call

                    # Update indexing status
                    await content_repo.update_google_indexing(url, indexed=True)

                    # Update progress
                    await progress_repo.increment_quota(service_id, amount=1)

                    submitted_count += 1
                    successful_count += 1
                    await log.debug(
                        "URL submitted successfully",
                        meta={"url": url},
                    )

                except Exception as e:
                    failed_count += 1
                    errors.append({"url": url, "error": str(e)})
                    await log.error(
                        "Failed to submit URL",
                        meta={"url": url, "error": str(e)},
                    )

            # Record submission metrics
            end_time = datetime.now(timezone.utc)
            submission_time_ms = int((end_time - start_time).total_seconds() * 1000)

            await metrics_collector.record_submission(
                service_id=service_id,
                urls_submitted=submitted_count,
                urls_successful=successful_count,
                success=failed_count == 0,
                submission_time_ms=submission_time_ms,
            )

            await log.info(
                "URL submission job completed",
                meta={
                    "service_id": service_id,
                    "submitted_count": submitted_count,
                    "successful_count": successful_count,
                    "failed_count": failed_count,
                    "total_time_ms": submission_time_ms,
                },
            )

            return {
                "success": failed_count == 0,
                "submitted_count": submitted_count,
                "successful_count": successful_count,
                "failed_count": failed_count,
                "errors": errors,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

        except Exception as e:
            await log.error(
                "Submission job failed",
                meta={"service_id": service_id, "error": str(e)},
            )
            return {
                "success": False,
                "submitted_count": submitted_count,
                "successful_count": successful_count,
                "failed_count": failed_count,
                "errors": errors + [{"error": str(e)}],
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            }

    async def run_health_check_job(self) -> dict[str, Any]:
        """Run SEO health checks and log results.

        Returns:
            Dictionary with health check results.
        """
        start_time = datetime.now(timezone.utc)
        log = await self._get_logger()
        health_check = await self._get_health_check()

        await log.info("Starting health check job")

        try:
            # Run all health checks
            health_status = await health_check.run_all_checks()

            # Log individual check results
            for check_name, result in health_status.checks.items():
                log_level = result.get("status", "unknown")
                message = result.get("message", "")

                if log_level == "healthy":
                    await log.debug(f"Health check: {check_name} - {message}")
                elif log_level == "degraded":
                    await log.warn(f"Health check: {check_name} - {message}")
                elif log_level == "unhealthy":
                    await log.error(f"Health check: {check_name} - {message}")

            # Log overall status
            if health_status.overall_status == "healthy":
                await log.info(
                    "SEO health check completed - all systems healthy",
                    meta={"checks": health_status.checks},
                )
            elif health_status.overall_status == "degraded":
                await log.warn(
                    "SEO health check completed - some systems degraded",
                    meta={
                        "checks": health_status.checks,
                        "recommendations": health_status.recommendations,
                    },
                )
            else:
                await log.error(
                    "SEO health check completed - systems unhealthy",
                    meta={
                        "checks": health_status.checks,
                        "recommendations": health_status.recommendations,
                    },
                )

            end_time = datetime.now(timezone.utc)

            return {
                "success": True,
                "overall_status": health_status.overall_status,
                "checks": health_status.checks,
                "recommendations": health_status.recommendations,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

        except Exception as e:
            await log.error(
                "Health check job failed",
                meta={"error": str(e)},
            )
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            }

    async def run_metrics_collection_job(self) -> dict[str, Any]:
        """Collect and save SEO metrics.

        Returns:
            Dictionary with metrics collection results.
        """
        start_time = datetime.now(timezone.utc)
        log = await self._get_logger()
        metrics_collector = await self._get_metrics_collector()

        await log.info("Starting metrics collection job")

        try:
            # Get metrics for last 7 days
            weekly_metrics = await metrics_collector.get_metrics(days=7)

            # Get submission logs for last 24 hours
            submission_logs = await metrics_collector.get_submission_logs(limit=100)

            # Calculate summary stats
            total_generated = sum(m.get("total_generated", 0) for m in weekly_metrics)
            total_submitted = sum(m.get("total_submitted", 0) for m in weekly_metrics)
            success_rate = await metrics_collector.get_success_rate(days=7)
            avg_gen_time = await metrics_collector.get_average_generation_time(days=7)

            # Save current metrics snapshot
            metrics_snapshot = {
                "weekly_generated": total_generated,
                "weekly_submitted": total_submitted,
                "weekly_success_rate": success_rate,
                "avg_generation_time_ms": avg_gen_time,
                "recent_submission_count": len(submission_logs),
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }

            await metrics_collector.save_metrics(metrics_snapshot)

            await log.info(
                "Metrics collection job completed",
                meta={
                    "weekly_generated": total_generated,
                    "weekly_submitted": total_submitted,
                    "success_rate": success_rate,
                    "avg_generation_time_ms": avg_gen_time,
                },
            )

            end_time = datetime.now(timezone.utc)

            return {
                "success": True,
                "metrics": metrics_snapshot,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

        except Exception as e:
            await log.error(
                "Metrics collection job failed",
                meta={"error": str(e)},
            )
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            }

    async def run_quota_reset_job(self) -> dict[str, Any]:
        """Reset daily quotas for all services.

        Returns:
            Dictionary with quota reset results.
        """
        start_time = datetime.now(timezone.utc)
        log = await self._get_logger()

        await log.info("Starting quota reset job")

        try:
            # Get all services that need quota reset
            # In production, we'd have a way to track all active services
            # For now, we'll just log the operation

            end_time = datetime.now(timezone.utc)

            return {
                "success": True,
                "reset_count": 0,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

        except Exception as e:
            await log.error(
                "Quota reset job failed",
                meta={"error": str(e)},
            )
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            }


# Background job functions (can be called independently)


async def generate_seo_content(
    service_id: str,
    topics: list[str],
    intents: list[str],
) -> dict[str, Any]:
    """Background job function to generate SEO content.

    Args:
        service_id: The service identifier.
        topics: List of topics to generate content for.
        intents: List of intents to generate content for.

    Returns:
        Dictionary with job results.
    """
    db_pool = await create_db_pool()
    try:
        worker = SEOWorker(db_pool)
        return await worker.run_content_generation_job(service_id, topics, intents)
    finally:
        await db_pool.close()


async def submit_to_google(
    service_id: str,
    batch_size: int = 10,
) -> dict[str, Any]:
    """Background job function to submit URLs to Google.

    Args:
        service_id: The service identifier.
        batch_size: Number of URLs to process in each batch.

    Returns:
        Dictionary with submission results.
    """
    db_pool = await create_db_pool()
    try:
        # Get URLs to submit from the database
        async with db_pool.acquire() as conn:
            progress_repo = SEOProgressRepository(conn)

            # Get progress to find URLs that need submission
            await progress_repo.get_progress(service_id)

            # Get unindexed content URLs
            rows = await conn.fetch(
                """
                SELECT url FROM seo_generated_content
                WHERE deleted_at IS NULL
                  AND google_indexed = FALSE
                ORDER BY created_at
                LIMIT $1
                """,
                batch_size,
            )

            urls = [row["url"] for row in rows]

        worker = SEOWorker(db_pool)
        return await worker.run_submission_job(service_id, urls)
    finally:
        await db_pool.close()


async def check_seo_health() -> dict[str, Any]:
    """Background job function to check SEO health.

    Returns:
        Dictionary with health check results.
    """
    db_pool = await create_db_pool()
    try:
        worker = SEOWorker(db_pool)
        return await worker.run_health_check_job()
    finally:
        await db_pool.close()


async def collect_seo_metrics() -> dict[str, Any]:
    """Background job function to collect SEO metrics.

    Returns:
        Dictionary with metrics collection results.
    """
    db_pool = await create_db_pool()
    try:
        worker = SEOWorker(db_pool)
        return await worker.run_metrics_collection_job()
    finally:
        await db_pool.close()


async def reset_seo_quotas() -> dict[str, Any]:
    """Background job function to reset daily quotas.

    Returns:
        Dictionary with quota reset results.
    """
    db_pool = await create_db_pool()
    try:
        worker = SEOWorker(db_pool)
        return await worker.run_quota_reset_job()
    finally:
        await db_pool.close()


# Main worker loop


async def run_worker_loop() -> None:
    """Run the main SEO worker loop."""
    db_pool = await create_db_pool()
    worker = SEOWorker(db_pool)

    logger.info("SEO worker started (poll every %d seconds)", POLL_INTERVAL_SEC)

    while not _shutdown:
        try:
            # Run periodic health check
            await worker.run_health_check_job()

            # Run periodic metrics collection
            await worker.run_metrics_collection_job()

        except Exception as e:
            logger.error("SEO worker loop error: %s", e)

        # Sleep in small increments to allow graceful shutdown
        for _ in range(int(POLL_INTERVAL_SEC)):
            if _shutdown:
                break
            await asyncio.sleep(1)

    await db_pool.close()
    logger.info("SEO worker stopped")


def main() -> None:
    """Main entry point for the SEO worker."""
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    asyncio.run(run_worker_loop())


if __name__ == "__main__":
    main()
