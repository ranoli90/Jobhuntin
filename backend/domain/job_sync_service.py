"""Background job synchronization service.
Fetches jobs from JobSpy on schedule and syncs to database.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any

import asyncpg

from backend.domain.jobspy_client import JobSpyClient, JobSpyError
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.job_sync")


# Default search queries for proactive syncing
DEFAULT_SEARCH_QUERIES = [
    ("software engineer", "San Francisco, CA"),
    ("software engineer", "New York, NY"),
    ("software engineer", "Remote"),
    ("software engineer", "Austin, TX"),
    ("software engineer", "Seattle, WA"),
    ("product manager", "San Francisco, CA"),
    ("product manager", "Remote"),
    ("data scientist", "New York, NY"),
    ("data scientist", "Remote"),
    ("frontend developer", "Remote"),
    ("backend developer", "Remote"),
    ("full stack developer", "Remote"),
    ("devops engineer", "Seattle, WA"),
    ("machine learning engineer", "Remote"),
    ("engineering manager", "San Francisco, CA"),
]


@dataclass
class SyncResult:
    """Result of a sync operation."""

    source: str
    search_term: str
    location: str | None
    status: str
    jobs_fetched: int
    jobs_new: int
    jobs_updated: int
    jobs_skipped: int
    error: str | None = None
    duration_ms: int = 0
    sync_run_id: str | None = None


class JobSyncService:
    """Service for syncing jobs from multiple sources (Adzuna + JobSpy)."""

    def __init__(self, db_pool: asyncpg.Pool, settings=None):
        self.db_pool = db_pool
        self.settings = settings or get_settings()
        self.jobspy = JobSpyClient(self.settings)
        self._running = False

    async def sync_adzuna(
        self,
        keywords: str | None = None,
        location: str | None = None,
    ) -> SyncResult:
        """Sync jobs from Adzuna API into the database."""
        from backend.domain.job_boards import AdzunaClient

        start_time = time.time()
        client = AdzunaClient(self.settings)

        try:
            raw_jobs = await client.fetch_jobs(keywords=keywords, location=location)
            if not raw_jobs:
                return SyncResult(
                    source="adzuna", search_term=keywords or "",
                    location=location, status="completed",
                    jobs_fetched=0, jobs_new=0, jobs_updated=0, jobs_skipped=0,
                )

            mapped = []
            for rj in raw_jobs:
                db_job = client.map_to_db(rj)
                db_job.setdefault("is_remote", False)
                db_job.setdefault("job_type", None)
                db_job.setdefault("date_posted", None)
                db_job.setdefault("job_level", None)
                db_job.setdefault("company_industry",
                                  (rj.get("category") or {}).get("label"))
                db_job.setdefault("company_logo_url", None)
                mapped.append(db_job)

            new_count, updated_count, skipped_count = await self._sync_jobs_to_db(mapped)
            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Adzuna sync: %d fetched, %d new, %d updated, %d skipped in %dms",
                len(raw_jobs), new_count, updated_count, skipped_count, duration_ms,
            )
            return SyncResult(
                source="adzuna", search_term=keywords or "",
                location=location, status="completed",
                jobs_fetched=len(raw_jobs), jobs_new=new_count,
                jobs_updated=updated_count, jobs_skipped=skipped_count,
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error("Adzuna sync failed: %s", e)
            return SyncResult(
                source="adzuna", search_term=keywords or "",
                location=location, status="failed",
                jobs_fetched=0, jobs_new=0, jobs_updated=0, jobs_skipped=0,
                error=str(e), duration_ms=int((time.time() - start_time) * 1000),
            )

    async def sync_all_sources(
        self,
        search_queries: list[tuple[str, str]] | None = None,
        max_concurrent: int = 2,
    ) -> list[SyncResult]:
        """Sync jobs from all configured sources.

        Args:
            search_queries: List of (search_term, location) tuples.
            max_concurrent: Max number of concurrent source scrapes.

        """
        if self._running:
            logger.warning("Sync already in progress, skipping")
            return []

        self._running = True
        queries = search_queries or await self._get_search_queries()
        results: list[SyncResult] = []

        try:
            logger.info(
                f"Starting sync for {len(queries)} queries across {len(self.jobspy.sources)} sources"
            )

            # Process queries with limited concurrency
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_query(search_term: str, location: str | None):
                async with semaphore:
                    return await self._sync_query(search_term, location)

            tasks = [process_query(term, loc) for term, loc in queries]
            query_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(query_results):
                if isinstance(result, Exception):
                    logger.error(f"Query {i} failed: {result}")
                elif isinstance(result, list):
                    results.extend(result)

            # Cleanup expired jobs
            expired = await self.cleanup_expired_jobs()
            logger.info(f"Cleaned up {expired} expired jobs")

            # Log summary
            total_new = sum(r.jobs_new for r in results)
            total_updated = sum(r.jobs_updated for r in results)
            total_failed = sum(1 for r in results if r.status == "failed")

            logger.info(
                f"Sync complete: {total_new} new, {total_updated} updated, {total_failed} failed"
            )
            incr("jobspy.sync_complete", 1)

        finally:
            self._running = False

        return results

    async def _sync_query(
        self,
        search_term: str,
        location: str | None,
    ) -> list[SyncResult]:
        """Sync jobs for a single search query across all sources."""
        results = []

        for source in self.jobspy.sources:
            try:
                result = await self._sync_single_source(
                    source=source,
                    search_term=search_term,
                    location=location,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Sync failed for {source}/{search_term}: {e}")
                results.append(
                    SyncResult(
                        source=source,
                        search_term=search_term,
                        location=location,
                        status="failed",
                        jobs_fetched=0,
                        jobs_new=0,
                        jobs_updated=0,
                        jobs_skipped=0,
                        error=str(e),
                    )
                )

        return results

    async def _sync_single_source(
        self,
        source: str,
        search_term: str,
        location: str | None,
    ) -> SyncResult:
        """Sync jobs from a single source."""
        start_time = time.time()
        sync_run_id = None

        # Record sync start
        sync_run_id = await self._record_sync_start(source, search_term, location)

        try:
            # Fetch jobs from JobSpy
            jobs = await self.jobspy.fetch_jobs(
                search_term=search_term,
                location=location,
                sources=[source],
            )

            # Sync to database
            new_count, updated_count, skipped_count = await self._sync_jobs_to_db(jobs)

            duration_ms = int((time.time() - start_time) * 1000)

            # Update sync run
            await self._record_sync_complete(
                sync_run_id=sync_run_id,
                status="completed",
                jobs_fetched=len(jobs),
                jobs_new=new_count,
                jobs_updated=updated_count,
                jobs_skipped=skipped_count,
                duration_ms=duration_ms,
            )

            # Update source config
            await self._update_source_config(source, success=True, jobs_count=len(jobs))

            incr("jobspy.sync_success", 1, {"source": source})

            return SyncResult(
                source=source,
                search_term=search_term,
                location=location,
                status="completed",
                jobs_fetched=len(jobs),
                jobs_new=new_count,
                jobs_updated=updated_count,
                jobs_skipped=skipped_count,
                duration_ms=duration_ms,
                sync_run_id=sync_run_id,
            )

        except JobSpyError as e:
            duration_ms = int((time.time() - start_time) * 1000)

            await self._record_sync_complete(
                sync_run_id=sync_run_id,
                status="failed",
                error_message=str(e),
                duration_ms=duration_ms,
            )

            await self._update_source_config(source, success=False, error=str(e))

            return SyncResult(
                source=source,
                search_term=search_term,
                location=location,
                status="failed",
                jobs_fetched=0,
                jobs_new=0,
                jobs_updated=0,
                jobs_skipped=0,
                error=str(e),
                duration_ms=duration_ms,
                sync_run_id=sync_run_id,
            )

    async def _sync_jobs_to_db(
        self,
        jobs: list[dict[str, Any]],
    ) -> tuple[int, int, int]:
        """Sync jobs to database with deduplication."""
        new_count = 0
        updated_count = 0
        skipped_count = 0

        async with self.db_pool.acquire() as conn:
            for job in jobs:
                if not self._is_quality_job(job):
                    skipped_count += 1
                    continue

                existing = await conn.fetchrow(
                    "SELECT id FROM public.jobs WHERE external_id = $1",
                    job["external_id"],
                )

                try:
                    if existing:
                        await conn.execute(
                            """
                            UPDATE public.jobs SET
                                title = $2,
                                company = $3,
                                description = $4,
                                location = $5,
                                is_remote = $6,
                                job_type = $7,
                                salary_min = $8,
                                salary_max = $9,
                                application_url = $10,
                                date_posted = $11,
                                job_level = $12,
                                company_industry = $13,
                                company_logo_url = $14,
                                raw_data = $15,
                                last_synced_at = now()
                            WHERE id = $1
                            """,
                            existing["id"],
                            job["title"],
                            job["company"],
                            job["description"],
                            job["location"],
                            job["is_remote"],
                            job["job_type"],
                            job["salary_min"],
                            job["salary_max"],
                            job["application_url"],
                            job["date_posted"],
                            job["job_level"],
                            job["company_industry"],
                            job["company_logo_url"],
                            json.dumps(job["raw_data"]),
                        )
                        updated_count += 1
                    else:
                        await conn.execute(
                            """
                            INSERT INTO public.jobs (
                                external_id, title, company, description, location,
                                is_remote, job_type, salary_min, salary_max,
                                application_url, source, date_posted, job_level,
                                company_industry, company_logo_url, raw_data, last_synced_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, now())
                            """,
                            job["external_id"],
                            job["title"],
                            job["company"],
                            job["description"],
                            job["location"],
                            job["is_remote"],
                            job["job_type"],
                            job["salary_min"],
                            job["salary_max"],
                            job["application_url"],
                            job["source"],
                            job["date_posted"],
                            job["job_level"],
                            job["company_industry"],
                            job["company_logo_url"],
                            json.dumps(job["raw_data"]),
                        )
                        new_count += 1
                except Exception as e:
                    logger.warning(f"Failed to upsert job {job['external_id']}: {e}")
                    skipped_count += 1

        return new_count, updated_count, skipped_count

    def _is_quality_job(self, job: dict[str, Any]) -> bool:
        """Check if job meets quality threshold."""
        if not job.get("title") or not job.get("company"):
            return False
        if not job.get("application_url"):
            return False
        desc = job.get("description", "")
        min_len = getattr(self.settings, "jobspy_quality_min_desc_length", 50)
        if len(desc) < min_len:
            return False
        return True

    async def _get_search_queries(self) -> list[tuple[str, str]]:
        """Get search queries from popular searches or defaults."""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT search_term, location FROM public.popular_searches
                    ORDER BY search_count DESC, last_searched_at DESC
                    LIMIT 15
                    """
                )

            if rows:
                return [(r["search_term"], r["location"]) for r in rows]
        except Exception as e:
            logger.warning(f"Failed to get popular searches: {e}")

        return DEFAULT_SEARCH_QUERIES

    async def _record_sync_start(
        self,
        source: str,
        search_term: str,
        location: str | None,
    ) -> str:
        """Record sync start in database."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO public.job_sync_runs
                    (source, search_term, location, status, started_at)
                VALUES ($1, $2, $3, 'running', now())
                RETURNING id
                """,
                source,
                search_term,
                location,
            )
            return str(row["id"])

    async def _record_sync_complete(
        self,
        sync_run_id: str,
        status: str,
        jobs_fetched: int = 0,
        jobs_new: int = 0,
        jobs_updated: int = 0,
        jobs_skipped: int = 0,
        error_message: str | None = None,
        duration_ms: int = 0,
    ) -> None:
        """Record sync completion in database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.job_sync_runs SET
                    status = $2,
                    jobs_fetched = $3,
                    jobs_new = $4,
                    jobs_updated = $5,
                    jobs_skipped = $6,
                    error_message = $7,
                    duration_ms = $8,
                    completed_at = now()
                WHERE id = $1
                """,
                sync_run_id,
                status,
                jobs_fetched,
                jobs_new,
                jobs_updated,
                jobs_skipped,
                error_message,
                duration_ms,
            )

    async def _update_source_config(
        self,
        source: str,
        success: bool,
        jobs_count: int = 0,
        error: str | None = None,
    ) -> None:
        """Update source config after sync."""
        async with self.db_pool.acquire() as conn:
            if success:
                await conn.execute(
                    """
                    UPDATE public.job_sync_config SET
                        last_sync_at = now(),
                        consecutive_failures = 0,
                        total_jobs_fetched = total_jobs_fetched + $2,
                        total_syncs = total_syncs + 1
                    WHERE source = $1
                    """,
                    source,
                    jobs_count,
                )
            else:
                await conn.execute(
                    """
                    UPDATE public.job_sync_config SET
                        last_error_at = now(),
                        last_error_message = $2,
                        consecutive_failures = consecutive_failures + 1
                    WHERE source = $1
                    """,
                    source,
                    error,
                )

    async def cleanup_expired_jobs(self) -> int:
        """Remove jobs older than TTL."""
        ttl_days = getattr(self.settings, "jobspy_job_ttl_days", 7)
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "SELECT public.cleanup_expired_jobs($1)",
                ttl_days,
            )
            # Parse result
            if result:
                try:
                    deleted = int(result.split()[-1])
                    incr("jobspy.jobs_expired", deleted)
                    return deleted
                except Exception:
                    return 0
        return 0

    async def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status for all sources."""
        async with self.db_pool.acquire() as conn:
            configs = await conn.fetch(
                "SELECT * FROM public.job_sync_config ORDER BY source"
            )
            recent_runs = await conn.fetch(
                """
                SELECT source, status, jobs_new, jobs_updated, duration_ms, started_at
                FROM public.job_sync_runs
                WHERE started_at > now() - interval '24 hours'
                ORDER BY started_at DESC
                """
            )
            job_stats = await conn.fetch("SELECT * FROM public.job_source_stats")

        return {
            "sources": [dict(c) for c in configs],
            "recent_runs": [dict(r) for r in recent_runs],
            "job_stats": [dict(s) for s in job_stats],
            "circuit_breakers": {
                source: state.get("status", "closed")
                for source, state in self.jobspy._circuit_breaker_state.items()
            },
        }
