"""Job search domain logic.
Jobs are synced from JobSpy via background worker.
This module queries the local database with deduplication.
When user_id is provided, loads profile and scores jobs by match.
"""

import json
import time
from typing import Any

import asyncpg

from backend.domain.job_dedup import deduplicate_jobs, normalize_job
from backend.domain.job_scoring import apply_dealbreaker_filters, score_job_match
from backend.domain.profile_assembly import assemble_profile
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.job_search")

# Sort options: match_score requires profile; others use SQL
SORT_OPTIONS = ("match_score", "recently_matched", "salary", "date_posted")


async def search_and_list_jobs(
    db_pool: asyncpg.Pool,
    location: str | None = None,
    min_salary: int | None = None,
    keywords: str | None = None,
    source: str | None = None,
    is_remote: bool | None = None,
    job_type: str | None = None,
    *,
    user_id: str | None = None,
    sort_by: str = "date_posted",
    min_match_score: int | None = None,
    limit: int = 25,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Search jobs from local database, with Adzuna live fallback when DB is empty.

    When user_id is provided and profile exists, jobs are scored by match and
    optionally sorted by match_score. Dealbreakers are applied.
    """
    s = get_settings()
    if sort_by not in SORT_OPTIONS:
        sort_by = "date_posted"

    # When scoring, fetch more to account for dealbreaker filtering and pagination
    if user_id:
        fetch_limit = min(offset + limit * 3, 200)
        fetch_offset = 0
    else:
        fetch_limit = limit
        fetch_offset = offset

    async with db_pool.acquire() as conn:
        query, params = _build_job_search_query(
            s,
            location,
            min_salary,
            keywords,
            source,
            is_remote,
            job_type,
            fetch_limit,
            fetch_offset,
            sort_by=sort_by if not user_id else "date_posted",
        )
        rows = await conn.fetch(query, *params)

    # Track popular searches for proactive syncing
    if keywords or location:
        await _track_search(db_pool, keywords, location)

    # If DB is empty (first page), try live Adzuna fetch and persist results
    if not rows and offset == 0 and s.adzuna_app_id and s.adzuna_api_key:
        logger.info("[JOB_SEARCH] DB empty, fetching from Adzuna live")
        try:
            from backend.domain.job_sync_service import JobSyncService

            sync = JobSyncService(db_pool, s)
            search_kw = keywords or "software engineer"
            await sync.sync_adzuna(keywords=search_kw, location=location)

            async with db_pool.acquire() as conn:
                query2, params2 = _build_job_search_query(
                    s,
                    location,
                    min_salary,
                    keywords,
                    source,
                    is_remote,
                    job_type,
                    fetch_limit,
                    fetch_offset,
                    sort_by=sort_by if not user_id else "date_posted",
                )
                rows = await conn.fetch(query2, *params2)
        except Exception as e:
            logger.warning("[JOB_SEARCH] Adzuna live fallback failed: %s", e)

    raw_jobs = [_map_job_row(r) for r in rows]
    normalized_jobs = [normalize_job(job, "database") for job in raw_jobs]
    unique_norm, duplicate_jobs = deduplicate_jobs(normalized_jobs, "database")

    # Map back to full dicts (preserve salary_min, salary_max, logo_url, etc.)
    raw_by_id = {j["id"]: j for j in raw_jobs}
    result = [raw_by_id[j.id] for j in unique_norm if j.id in raw_by_id]

    if duplicate_jobs:
        logger.info(
            f"[DEDUP] Removed {len(duplicate_jobs)} duplicate jobs from search results",
            extra={
                "total_jobs": len(raw_jobs),
                "unique_jobs": len(result),
                "duplicate_jobs": len(duplicate_jobs),
                "deduplication_rate": (
                    len(duplicate_jobs) / len(raw_jobs) if raw_jobs else 0
                ),
            },
        )

    # Profile-based scoring when user_id provided
    if user_id and result:
        t0 = time.monotonic()
        async with db_pool.acquire() as conn:
            profile = await assemble_profile(conn, user_id)
        if profile:
            result = apply_dealbreaker_filters(result, profile.dealbreakers)
            for job in result:
                # Ensure job has keys expected by score_job_match
                job.setdefault("requirements", job.get("skills") or [])
                score_job_match(job, profile)
            duration = time.monotonic() - t0
            observe("job_search.match_scoring_latency_seconds", duration)
            incr("job_search.jobs_scored", {"user_id": user_id}, value=len(result))
            # Filter by min_match_score if requested
            if min_match_score is not None:
                result = [j for j in result if (j.get("match_score") or 0) >= min_match_score]
            # MEDIUM: Optimize match score sorting for large datasets
            # Note: For very large result sets, consider pre-computing and storing match scores
            # in the database and using SQL ORDER BY instead of in-memory sorting
            if sort_by in ("match_score", "recently_matched"):
                # Use stable sort with proper type handling
                result.sort(
                    key=lambda j: (
                        float(j.get("match_score") or 0),  # Ensure numeric comparison
                        j.get("date_posted") or "",  # String comparison for dates
                    ),
                    reverse=True,
                )
            elif sort_by == "salary":
                result.sort(
                    key=lambda j: (
                        j.get("salary_max") or 0,
                        j.get("salary_min") or 0,
                    ),
                    reverse=True,
                )
        # When user_id provided we fetched extra; always slice to requested page
        result = result[offset : offset + limit]

    return result


def _build_job_search_query(
    settings: Any,
    location: str | None,
    min_salary: int | None,
    keywords: str | None,
    source: str | None,
    is_remote: bool | None,
    job_type: str | None,
    limit: int,
    offset: int,
    *,
    sort_by: str = "date_posted",
) -> tuple[str, list[Any]]:
    query = """
        SELECT id, title, company, description, location,
               salary_min, salary_max, url as application_url, '' as source,
               remote_policy, '' as job_type, posted_date as date_posted, experience_level as job_level,
               '' as company_industry, '' as company_logo_url, '{}'::jsonb as raw_data, ARRAY[]::text[] as skills
        FROM   public.jobs
        WHERE  1=1
    """
    params: list[Any] = []
    n = 0

    if location:
        n += 1
        query += f" AND location ILIKE ${n}"
        params.append(f"%{location}%")

    if min_salary is not None:
        n += 1
        query += f" AND (salary_max IS NULL OR salary_max >= ${n})"
        params.append(min_salary)

    if keywords:
        n += 1
        query += (
            f" AND (title ILIKE ${n} OR company ILIKE ${n} OR description ILIKE ${n})"
        )
        params.append(f"%{keywords}%")

    if source:
        n += 1
        query += f" AND source = ${n}"
        params.append(source.lower())

    if is_remote is not None:
        n += 1
        # Map is_remote boolean to remote_policy values
        if is_remote:
            query += f" AND (remote_policy = 'remote' OR remote_policy = 'hybrid')"
        else:
            query += f" AND remote_policy = 'onsite'"

    if job_type:
        n += 1
        query += f" AND job_type = ${n}"
        params.append(job_type.lower())

    # Filter out expired jobs using last_synced_at
    from datetime import timedelta

    ttl_days = getattr(settings, "jobspy_job_ttl_days", 7)
    if ttl_days > 0:
        n += 1
        query += (
            f" AND (last_synced_at IS NULL OR last_synced_at >= now() - ${n}::interval)"
        )
        params.append(timedelta(days=ttl_days))

    # ORDER BY
    if sort_by == "salary":
        order_clause = "salary_max DESC NULLS LAST, salary_min DESC NULLS LAST, created_at DESC"
    else:
        order_clause = "date_posted DESC NULLS LAST, created_at DESC"

    query += f" ORDER BY {order_clause} LIMIT ${n + 1} OFFSET ${n + 2}"
    params.extend([limit, offset])

    return query, params


def _map_job_row(r: Any) -> dict[str, Any]:
    raw = r.get("raw_data") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}

    logo_url = r.get("company_logo_url")
    if not logo_url and isinstance(raw, dict):
        logo_url = raw.get("logo_url") or raw.get("logo")

    skills = r.get("skills")
    if skills is None:
        skills = []
    elif isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    requirements = list(skills) if isinstance(skills, (list, tuple)) else []

    job_data = {
        "id": str(r["id"]),
        "title": r["title"],
        "company": r["company"],
        "description": r["description"],
        "location": r["location"],
        "salary_min": float(r["salary_min"]) if r["salary_min"] is not None else None,
        "salary_max": float(r["salary_max"]) if r["salary_max"] is not None else None,
        "url": r["application_url"],
        "source": r.get("source"),
        "is_remote": r.get("remote_policy") in ("remote", "hybrid") if r.get("remote_policy") else None,
        "job_type": r.get("job_type"),
        "date_posted": r.get("posted_date").isoformat() if r.get("posted_date") else (r.get("date_posted").isoformat() if r.get("date_posted") else None),
        "job_level": r.get("job_level"),
        "company_industry": r.get("company_industry"),
        "logo_url": logo_url,
        "skills": requirements,
        "requirements": requirements,
    }

    # Apply source verification and scam detection
    job_data.update(_verify_job_legitimacy(job_data))

    return job_data


def _verify_job_legitimacy(job: dict[str, Any]) -> dict[str, Any]:
    """Verify job legitimacy and detect potential scams."""
    verification_score = 100
    verification_flags = []

    title = job.get("title", "").lower()
    company = job.get("company", "").lower()
    description = job.get("description", "").lower()
    source = job.get("source", "").lower()
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")

    # Scam detection patterns
    scam_indicators = [
        "wire transfer",
        "western union",
        "money order",
        "bitcoin",
        "cryptocurrency",
        "investment",
        "training fee",
        "equipment purchase",
        "background check fee",
        "work from home",
        "no experience needed",
        "immediate start",
        "unlimited earning",
        "easy money",
        "quick cash",
        "get rich quick",
    ]

    # Check for scam indicators in title/description
    for indicator in scam_indicators:
        if indicator in title or indicator in description:
            verification_score -= 15
            verification_flags.append(f"scam_indicator_{indicator.replace(' ', '_')}")

    # Check for unrealistic salary ranges
    if salary_min and salary_max:
        if salary_max > salary_min * 10:  # More than 10x range
            verification_score -= 10
            verification_flags.append("unrealistic_salary_range")

    # Check for missing key information
    if not company or len(company) < 2:
        verification_score -= 20
        verification_flags.append("missing_company")

    if not description or len(description) < 50:
        verification_score -= 15
        verification_flags.append("vague_description")

    # Check for suspicious company names
    suspicious_companies = [
        "hiring team",
        "recruitment agency",
        "hr department",
        "talent acquisition",
        "confidential company",
        "anonymous employer",
        "private client",
    ]

    for suspicious in suspicious_companies:
        if suspicious in company:
            verification_score -= 10
            verification_flags.append("suspicious_company_name")

    # Check for legitimate sources
    trusted_sources = ["linkedin", "indeed", "glassdoor", "monster", "careerbuilder"]
    source_trust = 0
    for trusted in trusted_sources:
        if trusted in source:
            source_trust += 25
            break

    verification_score += source_trust

    # Determine legitimacy level
    if verification_score >= 80:
        legitimacy_level = "high"
    elif verification_score >= 60:
        legitimacy_level = "medium"
    elif verification_score >= 40:
        legitimacy_level = "low"
    else:
        legitimacy_level = "suspicious"

    return {
        "verification_score": max(0, verification_score),
        "legitimacy_level": legitimacy_level,
        "verification_flags": verification_flags,
        "is_trusted_source": source_trust > 0,
    }


async def _track_search(
    db_pool: asyncpg.Pool, keywords: str | None, location: str | None
):
    """Track search for proactive syncing."""
    if not keywords:
        return

    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.popular_searches (search_term, location, search_count, last_searched_at)
                VALUES ($1, $2, 1, now())
                ON CONFLICT (search_term, location) DO UPDATE SET
                    search_count = popular_searches.search_count + 1,
                    last_searched_at = now()
                """,
                keywords,
                location,
            )
    except Exception as e:
        logger.warning(f"Failed to track search: {e}")


async def get_job_sources(db_pool: asyncpg.Pool) -> list[dict[str, Any]]:
    """Get list of available job sources with stats."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                source,
                COUNT(*) AS total_jobs,
                COUNT(*) FILTER (WHERE is_remote = TRUE) AS remote_jobs,
                COUNT(*) FILTER (WHERE salary_min IS NOT NULL) AS jobs_with_salary,
                MAX(last_synced_at) AS last_synced_at
            FROM public.jobs
            WHERE last_synced_at > now() - interval '7 days'
            GROUP BY source
            ORDER BY total_jobs DESC
            """
        )
    return [dict(r) for r in rows]


async def get_sync_status(db_pool: asyncpg.Pool) -> dict[str, Any]:
    """Get current sync status for monitoring."""
    # nosemgrep: python.lang.security.audit.sqli.asyncpg-sqli.asyncpg-sqli - static queries only
    async with db_pool.acquire() as conn:
        config = await conn.fetch(
            "SELECT * FROM public.job_sync_config ORDER BY source"
        )
        recent = await conn.fetch(
            """
            SELECT source, status, jobs_new, jobs_updated, duration_ms, started_at, completed_at
            FROM public.job_sync_runs
            WHERE started_at > now() - interval '24 hours'
            ORDER BY started_at DESC
            LIMIT 20
            """
        )
        total_jobs = await conn.fetchval(
            "SELECT COUNT(*) FROM public.jobs WHERE last_synced_at > now() - interval '7 days'"
        )

    return {
        "sources": [dict(c) for c in config],
        "recent_runs": [dict(r) for r in recent],
        "total_active_jobs": total_jobs,
    }
