"""Job search domain logic.
Jobs are synced from JobSpy via background worker.
This module queries the local database with deduplication.
"""

import json
from typing import Any

import asyncpg

from backend.domain.job_dedup import deduplicate_jobs, normalize_job
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.job_search")


async def search_and_list_jobs(
    db_pool: asyncpg.Pool,
    location: str | None = None,
    min_salary: int | None = None,
    keywords: str | None = None,
    source: str | None = None,
    is_remote: bool | None = None,
    job_type: str | None = None,
    *,
    limit: int = 25,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Search jobs from local database (synced from JobSpy).

    No longer fetches from external APIs on-demand - uses background sync.
    """
    s = get_settings()

    async with db_pool.acquire() as conn:
        query, params = _build_job_search_query(
            s,
            location,
            min_salary,
            keywords,
            source,
            is_remote,
            job_type,
            limit,
            offset,
        )
        rows = await conn.fetch(query, *params)

    # Track popular searches for proactive syncing
    if keywords or location:
        await _track_search(db_pool, keywords, location)

    # Convert to dict format and normalize for deduplication
    raw_jobs = [_map_job_row(r) for r in rows]
    normalized_jobs = [normalize_job(job, "database") for job in raw_jobs]

    # Apply deduplication
    unique_jobs, duplicate_jobs = deduplicate_jobs(normalized_jobs, "database")

    # Log deduplication metrics
    if duplicate_jobs:
        logger.info(
            f"[DEDUP] Removed {len(duplicate_jobs)} duplicate jobs from search results",
            extra={
                "total_jobs": len(raw_jobs),
                "unique_jobs": len(unique_jobs),
                "duplicate_jobs": len(duplicate_jobs),
                "deduplication_rate": (
                    len(duplicate_jobs) / len(raw_jobs) if raw_jobs else 0
                ),
            },
        )

    return unique_jobs


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
) -> tuple[str, list[Any]]:
    query = """
        SELECT id, title, company, description, location,
               salary_min, salary_max, application_url, source,
               is_remote, job_type, date_posted, job_level,
               company_industry, company_logo_url, raw_data
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
        query += f" AND is_remote = ${n}"
        params.append(is_remote)

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

    query += (
        " ORDER BY date_posted DESC NULLS LAST, created_at DESC LIMIT $%d OFFSET $%d"
        % (n + 1, n + 2)
    )
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
        "is_remote": r.get("is_remote"),
        "job_type": r.get("job_type"),
        "date_posted": r["date_posted"].isoformat() if r.get("date_posted") else None,
        "job_level": r.get("job_level"),
        "company_industry": r.get("company_industry"),
        "logo_url": logo_url,
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
