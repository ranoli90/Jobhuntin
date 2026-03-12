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

from packages.backend.domain.job_search import _verify_job_legitimacy
from packages.backend.domain.jobspy_client import JobSpyClient, JobSpyError
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
        self._running_lock = asyncio.Lock()

    async def sync_adzuna(
        self,
        keywords: str | None = None,
        location: str | None = None,
    ) -> SyncResult:
        """Sync jobs from Adzuna API into the database."""
        from packages.backend.domain.job_boards import AdzunaClient

        start_time = time.time()
        client = AdzunaClient(self.settings)

        try:
            raw_jobs = await client.fetch_jobs(keywords=keywords, location=location)
            if not raw_jobs:
                return SyncResult(
                    source="adzuna",
                    search_term=keywords or "",
                    location=location,
                    status="completed",
                    jobs_fetched=0,
                    jobs_new=0,
                    jobs_updated=0,
                    jobs_skipped=0,
                )

            mapped = []
            for rj in raw_jobs:
                db_job = client.map_to_db(rj)
                db_job.setdefault("is_remote", False)
                db_job.setdefault("job_type", None)
                db_job.setdefault("date_posted", None)
                db_job.setdefault("job_level", None)
                db_job.setdefault(
                    "company_industry", (rj.get("category") or {}).get("label")
                )
                db_job.setdefault("company_logo_url", None)
                if isinstance(db_job.get("raw_data"), dict):
                    pass
                mapped.append(db_job)

            new_count, updated_count, skipped_count = await self._sync_jobs_to_db(
                mapped
            )
            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Adzuna sync: %d fetched, %d new, %d updated, %d skipped in %dms",
                len(raw_jobs),
                new_count,
                updated_count,
                skipped_count,
                duration_ms,
            )
            return SyncResult(
                source="adzuna",
                search_term=keywords or "",
                location=location,
                status="completed",
                jobs_fetched=len(raw_jobs),
                jobs_new=new_count,
                jobs_updated=updated_count,
                jobs_skipped=skipped_count,
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error("Adzuna sync failed: %s", e)
            return SyncResult(
                source="adzuna",
                search_term=keywords or "",
                location=location,
                status="failed",
                jobs_fetched=0,
                jobs_new=0,
                jobs_updated=0,
                jobs_skipped=0,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
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
        async with self._running_lock:
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

            # Cleanup expired jobs (don't let cleanup failure abort sync)
            try:
                expired = await self.cleanup_expired_jobs()
                logger.info(f"Cleaned up {expired} expired jobs")
            except Exception as e:
                logger.error("Cleanup expired jobs failed: %s", e, exc_info=True)

            # Log summary
            total_new = sum(r.jobs_new for r in results)
            total_updated = sum(r.jobs_updated for r in results)
            total_failed = sum(1 for r in results if r.status == "failed")

            logger.info(
                f"Sync complete: {total_new} new, {total_updated} updated, {total_failed} failed"
            )
            incr("jobspy.sync_complete", 1)

        finally:
            async with self._running_lock:
                self._running = False

        return results

    async def sync_for_user(
        self,
        user_id: str,
        max_concurrent: int = 2,
    ) -> list[SyncResult]:
        """Sync jobs for a specific user's preferences, profile, and job_alerts.
        Uses user-specific queries; jobs still go to shared public.jobs table.
        """
        queries = await self._get_search_queries_for_user(user_id)
        if not queries:
            logger.info("No search queries for user %s, using defaults", user_id)
            queries = DEFAULT_SEARCH_QUERIES[:5]  # Limit for per-user
        logger.info("Per-user sync for %s: %d queries", user_id, len(queries))
        return await self.sync_all_sources(search_queries=queries, max_concurrent=max_concurrent)

    async def _get_search_queries_for_user(
        self,
        user_id: str,
    ) -> list[tuple[str, str]]:
        """Get search queries for a specific user from preferences, profile, job_alerts."""
        seen: set[tuple[str, str]] = set()
        queries: list[tuple[str, str]] = []

        try:
            async with self.db_pool.acquire() as conn:
                # 1. user_preferences (role_type, location)
                row = await conn.fetchrow(
                    """
                    SELECT role_type, location FROM public.user_preferences
                    WHERE user_id = $1
                    """,
                    user_id,
                )
                if row and (row.get("role_type") or row.get("location")):
                    term = (row["role_type"] or "software engineer").strip()
                    loc = (row["location"] or "Remote").strip() or "Remote"
                    if (term, loc) not in seen:
                        seen.add((term, loc))
                        queries.append((term, loc))

                # 2. profiles.profile_data
                prof = await conn.fetchrow(
                    """
                    SELECT profile_data FROM public.profiles WHERE user_id = $1
                    """,
                    user_id,
                )
                if prof and prof.get("profile_data"):
                    pd = prof["profile_data"] or {}
                    prefs = pd.get("preferences") or {}
                    goals = pd.get("career_goals") or {}
                    term = (prefs.get("role_type") or (goals.get("target_roles") or [None])[0] or "").strip()
                    loc = (prefs.get("location") or "Remote").strip() or "Remote"
                    if term and (term, loc) not in seen:
                        seen.add((term, loc))
                        queries.append((term, loc))

                # 3. job_alerts (user's alerts)
                alert_rows = await conn.fetch(
                    """
                    SELECT keywords, locations FROM public.job_alerts
                    WHERE user_id = $1 AND is_active = true
                    """,
                    user_id,
                )
                for r in alert_rows:
                    kw_list = r["keywords"] if isinstance(r["keywords"], list) else []
                    loc_list = r["locations"] if isinstance(r["locations"], list) else []
                    if not kw_list:
                        kw_list = ["software engineer"]
                    if not loc_list:
                        loc_list = ["Remote"]
                    for kw in kw_list[:3]:
                        term = (kw if isinstance(kw, str) else str(kw)).strip()
                        for loc in loc_list[:3]:
                            loc_str = (loc if isinstance(loc, str) else str(loc)).strip() or "Remote"
                            if term and (term, loc_str) not in seen:
                                seen.add((term, loc_str))
                                queries.append((term, loc_str))

        except Exception as e:
            logger.warning("Failed to get search queries for user %s: %s", user_id, e)

        return queries

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

            # Apply scam/quality scoring before sync
            jobs = self._apply_legitimacy_scores(jobs)

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

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error("Sync failed for %s: %s", source, e, exc_info=True)
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
        """Sync jobs to database with batch upsert and deduplication."""
        quality_jobs = [j for j in jobs if self._is_quality_job(j)]
        skipped_count = len(jobs) - len(quality_jobs)
        if not quality_jobs:
            return 0, 0, skipped_count

        new_count = 0
        updated_count = 0
        batch_size = 50

        async with self.db_pool.acquire() as conn:
            for i in range(0, len(quality_jobs), batch_size):
                batch = quality_jobs[i : i + batch_size]
                ext_ids = [j["external_id"] for j in batch]

                # Count existing for this batch
                existing_count = await conn.fetchval(
                    "SELECT count(*)::int FROM public.jobs WHERE external_id = ANY($1)",
                    ext_ids,
                )

                n, u = await self._batch_upsert_jobs(conn, batch)
                updated_count += min(existing_count, n + u)
                new_count += max(0, n + u - existing_count)

        return new_count, updated_count, skipped_count

    async def _batch_upsert_jobs(
        self, conn: asyncpg.Connection, jobs: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """Batch upsert jobs using INSERT ... ON CONFLICT. Returns (new, updated) approx."""
        if not jobs:
            return 0, 0

        # Build multi-row INSERT with ON CONFLICT
        # Use unnest for arrays to avoid huge param lists
        ext_ids = [j["external_id"] for j in jobs]
        titles = [j["title"] for j in jobs]
        companies = [j["company"] for j in jobs]
        descriptions = [j["description"] or "" for j in jobs]
        locations = [j.get("location") or "" for j in jobs]
        is_remotes = [j.get("is_remote") or False for j in jobs]
        job_types = [j.get("job_type") for j in jobs]
        salary_mins = [j.get("salary_min") for j in jobs]
        salary_maxs = [j.get("salary_max") for j in jobs]
        app_urls = [j.get("application_url") or "" for j in jobs]
        sources = [j.get("source") or "" for j in jobs]
        date_posted = [j.get("date_posted") for j in jobs]
        job_levels = [j.get("job_level") for j in jobs]
        company_industries = [j.get("company_industry") for j in jobs]
        company_logos = [j.get("company_logo_url") for j in jobs]
        raw_datas = [json.dumps(j.get("raw_data") or {}) for j in jobs]
        is_scams = [j.get("is_scam", False) for j in jobs]
        quality_scores = [j.get("quality_score") for j in jobs]

        # Normalize date_posted for PostgreSQL
        date_posted_vals = []
        for d in date_posted:
            if d is None:
                date_posted_vals.append(None)
            elif hasattr(d, "isoformat"):
                date_posted_vals.append(d.isoformat())
            else:
                date_posted_vals.append(str(d) if d else None)

        await conn.execute(
            """
            INSERT INTO public.jobs (
                external_id, title, company, description, location,
                is_remote, job_type, salary_min, salary_max,
                application_url, source, date_posted, job_level,
                company_industry, company_logo_url, raw_data,
                is_scam, quality_score, last_synced_at
            )
            SELECT ext_id, ttl, comp, descr, loc, rem, jt, smin, smax, url, src,
                   dp::timestamptz, jl, ci, cl, rd::jsonb, scam, qs, now()
            FROM unnest(
                $1::text[], $2::text[], $3::text[], $4::text[], $5::text[],
                $6::bool[], $7::text[], $8::int[], $9::int[],
                $10::text[], $11::text[], $12::text[], $13::text[], $14::text[], $15::text[],
                $16::text[], $17::bool[], $18::real[]
            ) AS t(ext_id, ttl, comp, descr, loc, rem, jt, smin, smax, url, src, dp, jl, ci, cl, rd, scam, qs)
            ON CONFLICT (external_id) DO UPDATE SET
                title = EXCLUDED.title,
                company = EXCLUDED.company,
                description = EXCLUDED.description,
                location = EXCLUDED.location,
                is_remote = EXCLUDED.is_remote,
                job_type = EXCLUDED.job_type,
                salary_min = EXCLUDED.salary_min,
                salary_max = EXCLUDED.salary_max,
                application_url = EXCLUDED.application_url,
                date_posted = EXCLUDED.date_posted,
                job_level = EXCLUDED.job_level,
                company_industry = EXCLUDED.company_industry,
                company_logo_url = EXCLUDED.company_logo_url,
                raw_data = EXCLUDED.raw_data,
                is_scam = EXCLUDED.is_scam,
                quality_score = EXCLUDED.quality_score,
                last_synced_at = now()
            """,
            ext_ids,
            titles,
            companies,
            descriptions,
            locations,
            is_remotes,
            job_types,
            salary_mins,
            salary_maxs,
            app_urls,
            sources,
            date_posted_vals,
            job_levels,
            company_industries,
            company_logos,
            raw_datas,
            is_scams,
            quality_scores,
        )

        return len(jobs), 0

    def _apply_legitimacy_scores(self, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply is_scam and quality_score from _verify_job_legitimacy to each job."""
        for job in jobs:
            legitimacy = _verify_job_legitimacy({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "description": job.get("description", ""),
                "source": job.get("source", ""),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
            })
            score = legitimacy.get("verification_score") or 0
            job["is_scam"] = score < 40
            job["quality_score"] = float(score) if score is not None else None
        return jobs

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
        """Get search queries from popular searches, tenant preferences, or defaults."""
        seen: set[tuple[str, str]] = set()
        queries: list[tuple[str, str]] = []

        try:
            async with self.db_pool.acquire() as conn:
                # 1. Popular searches (platform-wide)
                try:
                    rows = await conn.fetch(
                        """
                        SELECT search_term, location FROM public.popular_searches
                        ORDER BY search_count DESC, last_searched_at DESC
                        LIMIT 10
                        """
                    )
                    for r in rows:
                        term = (r["search_term"] or "").strip()
                        loc = (r["location"] or "Remote").strip() or "Remote"
                        if term and (term, loc) not in seen:
                            seen.add((term, loc))
                            queries.append((term, loc))
                except Exception as e:
                    logger.warning("Failed to get popular searches: %s", e)

                # 2. Tenant-specific: user_preferences (role_type, location from onboarding)
                try:
                    pref_rows = await conn.fetch(
                        """
                        SELECT DISTINCT role_type, location
                        FROM public.user_preferences
                        WHERE role_type IS NOT NULL AND role_type != ''
                        LIMIT 15
                        """
                    )
                    for r in pref_rows:
                        term = (r["role_type"] or "").strip()
                        loc = (r["location"] or "Remote").strip() or "Remote"
                        if term and (term, loc) not in seen:
                            seen.add((term, loc))
                            queries.append((term, loc))
                except Exception as e:
                    logger.warning("Failed to get user_preferences queries: %s", e)

                # 3. Tenant-specific: profile_data preferences (from onboarding)
                try:
                    profile_rows = await conn.fetch(
                        """
                        SELECT DISTINCT
                            COALESCE(
                                profile_data->'preferences'->>'role_type',
                                profile_data->'career_goals'->'target_roles'->>0
                            ) AS role_type,
                            COALESCE(profile_data->'preferences'->>'location', 'Remote') AS location
                        FROM public.profiles
                        WHERE profile_data IS NOT NULL
                          AND (
                            profile_data->'preferences'->>'role_type' IS NOT NULL
                            OR profile_data->'career_goals'->'target_roles'->>0 IS NOT NULL
                          )
                        LIMIT 15
                        """
                    )
                    for r in profile_rows:
                        term = (r["role_type"] or "").strip()
                        loc = (r["location"] or "Remote").strip() or "Remote"
                        if term and (term, loc) not in seen:
                            seen.add((term, loc))
                            queries.append((term, loc))
                except Exception as e:
                    logger.warning("Failed to get profile_data queries: %s", e)

                # 4. Job alerts: keywords × locations from active alerts
                try:
                    alert_rows = await conn.fetch(
                        """
                        SELECT keywords, locations FROM public.job_alerts
                        WHERE is_active = true
                          AND (keywords != '[]'::jsonb OR locations != '[]'::jsonb)
                        LIMIT 20
                        """
                    )
                    for r in alert_rows:
                        kw_list = r["keywords"] if isinstance(r["keywords"], list) else []
                        loc_list = r["locations"] if isinstance(r["locations"], list) else []
                        if not kw_list:
                            kw_list = ["software engineer"]
                        if not loc_list:
                            loc_list = ["Remote"]
                        for kw in kw_list[:3]:
                            term = (kw if isinstance(kw, str) else str(kw)).strip()
                            for loc in loc_list[:3]:
                                loc_str = (loc if isinstance(loc, str) else str(loc)).strip() or "Remote"
                                if term and (term, loc_str) not in seen:
                                    seen.add((term, loc_str))
                                    queries.append((term, loc_str))
                except Exception as e:
                    logger.warning("Failed to get job_alerts queries: %s", e)

        except Exception as e:
            logger.warning("Failed to get search queries: %s", e)

        if queries:
            logger.info("Using %d tenant-aware search queries", len(queries))
            return queries

        return DEFAULT_SEARCH_QUERIES

    async def _record_sync_start(
        self,
        source: str,
        search_term: str,
        location: str | None,
    ) -> str:
        """Record sync start in database. Schema: source, status, started_at only."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO public.job_sync_runs (source, status, started_at)
                VALUES ($1, 'running', now())
                RETURNING id
                """,
                source,
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
        """Record sync completion. Schema uses errors JSONB, not error_message."""
        errors_json = json.dumps([{"message": error_message}]) if error_message else "[]"
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.job_sync_runs SET
                    status = $2,
                    jobs_fetched = $3,
                    jobs_new = $4,
                    jobs_updated = $5,
                    jobs_skipped = $6,
                    errors = $7::jsonb,
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
                errors_json,
                duration_ms,
            )

    async def _update_source_config(
        self,
        source: str,
        success: bool,
        jobs_count: int = 0,
        error: str | None = None,
    ) -> None:
        """Update source config. Schema has last_synced_at; store extras in config JSONB."""
        async with self.db_pool.acquire() as conn:
            if success:
                await conn.execute(
                    """
                    UPDATE public.job_sync_config SET
                        last_synced_at = now(),
                        config = config || jsonb_build_object(
                            'consecutive_failures', 0,
                            'total_jobs_fetched', COALESCE((config->>'total_jobs_fetched')::int, 0) + $2,
                            'total_syncs', COALESCE((config->>'total_syncs')::int, 0) + 1
                        ),
                        updated_at = now()
                    WHERE source = $1
                    """,
                    source,
                    jobs_count,
                )
            else:
                await conn.execute(
                    """
                    UPDATE public.job_sync_config SET
                        config = config || jsonb_build_object(
                            'last_error_at', now(),
                            'last_error_message', $2,
                            'consecutive_failures', COALESCE((config->>'consecutive_failures')::int, 0) + 1
                        ),
                        updated_at = now()
                    WHERE source = $1
                    """,
                    source,
                    error,
                )

    async def cleanup_expired_jobs(self) -> int:
        """Remove jobs older than TTL. Uses direct DELETE (no DB function)."""
        ttl_days = getattr(self.settings, "jobspy_job_ttl_days", 7)
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM public.jobs
                WHERE last_synced_at < now() - ($1::int || ' days')::interval
                   OR (last_synced_at IS NULL AND created_at < now() - ($1::int || ' days')::interval)
                """,
                ttl_days,
            )
            try:
                deleted = int(result.split()[-1]) if result else 0
            except Exception as e:
                logger.warning("Failed to parse cleanup result %r: %s", result, e)
                deleted = 0
            incr("jobspy.jobs_expired", deleted)
            return deleted

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
            job_stats: list[dict[str, Any]] = []
            try:
                job_stats = [dict(s) for s in await conn.fetch("SELECT * FROM public.job_source_stats")]
            except Exception:
                # job_source_stats table may not exist; derive from job_sync_runs
                agg = await conn.fetch(
                    """
                    SELECT source, sum(jobs_new) as jobs_new, sum(jobs_updated) as jobs_updated
                    FROM public.job_sync_runs
                    WHERE started_at > now() - interval '24 hours'
                    GROUP BY source
                    """
                )
                job_stats = [dict(r) for r in agg]

        return {
            "sources": [dict(c) for c in configs],
            "recent_runs": [dict(r) for r in recent_runs],
            "job_stats": job_stats,
            "circuit_breakers": {
                source: state.get("status", "closed")
                for source, state in self.jobspy._circuit_breaker_state.items()
            },
        }
