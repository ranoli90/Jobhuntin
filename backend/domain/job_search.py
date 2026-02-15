"""
Job search domain logic.
Jobs are synced from JobSpy via background worker.
This module queries the local database.
"""
import json
from typing import Any

import asyncpg
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
    """
    Search jobs from local database (synced from JobSpy).
    
    No longer fetches from external APIs on-demand - uses background sync.
    """
    s = get_settings()
    
    async with db_pool.acquire() as conn:
        query, params = _build_job_search_query(
            s, location, min_salary, keywords, source, is_remote, job_type, limit, offset
        )
        rows = await conn.fetch(query, *params)
    
    # Track popular searches for proactive syncing
    if keywords or location:
        await _track_search(db_pool, keywords, location)
    
    return [_map_job_row(r) for r in rows]


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
        query += f" AND (title ILIKE ${n} OR company ILIKE ${n} OR description ILIKE ${n})"
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
    ttl_days = getattr(settings, 'jobspy_job_ttl_days', 7)
    if ttl_days > 0:
        query += f" AND (last_synced_at IS NULL OR last_synced_at >= now() - interval '{ttl_days} days')"
    
    query += " ORDER BY date_posted DESC NULLS LAST, created_at DESC LIMIT $%d OFFSET $%d" % (n + 1, n + 2)
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
    
    return {
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


async def _track_search(db_pool: asyncpg.Pool, keywords: str | None, location: str | None):
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
    async with db_pool.acquire() as conn:
        config = await conn.fetch("SELECT * FROM public.job_sync_config ORDER BY source")
        recent = await conn.fetch(
            """
            SELECT source, status, jobs_new, jobs_updated, duration_ms, started_at, completed_at
            FROM public.job_sync_runs
            WHERE started_at > now() - interval '24 hours'
            ORDER BY started_at DESC
            LIMIT 20
            """
        )
        total_jobs = await conn.fetchval("SELECT COUNT(*) FROM public.jobs WHERE last_synced_at > now() - interval '7 days'")
    
    return {
        "sources": [dict(c) for c in config],
        "recent_runs": [dict(r) for r in recent],
        "total_active_jobs": total_jobs,
    }
