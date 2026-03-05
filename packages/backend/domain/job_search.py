"""Job search domain logic: Adzuna integration and job listing/filtering."""
import json
from typing import Any

import asyncpg
from shared.config import get_settings
from shared.logging_config import get_logger

from backend.domain.job_boards import AdzunaClient

logger = get_logger("sorce.job_search")


async def search_jobs_for_profile(
    db_pool: asyncpg.Pool,
    profile: "DeepProfile",
    *,
    limit: int = 25,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Profile-aware job search: fetch, filter by dealbreakers, score, and rank.

    1. Fetches candidate jobs using the standard SQL query with profile preferences.
    2. Applies hard dealbreaker filters (excluded companies, keywords, salary floor).
    3. Scores every remaining job against the user's deep profile.
    4. Returns top results sorted by match score descending.
    """
    from backend.domain.deep_profile import DeepProfile  # noqa: F811
    from backend.domain.job_scoring import apply_dealbreaker_filters, score_job_match

    raw_jobs = await search_and_list_jobs(
        db_pool,
        location=profile.preferences.get("location"),
        min_salary=profile.dealbreakers.min_salary,
        keywords=profile.preferences.get("role_type"),
        is_remote=profile.dealbreakers.remote_only or None,
        user_id=profile.user_id,
        limit=limit * 3,  # over-fetch to allow for filtering
    )

    filtered = apply_dealbreaker_filters(raw_jobs, profile.dealbreakers)
    scored = [score_job_match(job, profile) for job in filtered]
    scored.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return scored[offset : offset + limit]

async def search_and_list_jobs(
    db_pool: asyncpg.Pool,
    location: str | None = None,
    min_salary: int | None = None,
    keywords: str | None = None,
    source: str | None = None,
    is_remote: bool | None = None,
    job_type: str | None = None,
    user_id: str | None = None,
    *,
    limit: int = 25,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Search jobs:
    1. Fetch from Adzuna (if keywords/location provided) and sync to DB.
    2. Query DB with filters.
    3. Exclude jobs user already swiped on.
    """
    s = get_settings()

    # Proactively fetch from Adzuna if we have keywords/location
    if keywords or location:
        await _fetch_and_sync_adzuna(db_pool, s, location, keywords)

    async with db_pool.acquire() as conn:
        query, params = _build_job_search_query(
            s, location, min_salary, keywords, source, is_remote, job_type, limit, offset,
            user_id=user_id,
        )
        rows = await conn.fetch(query, *params)

    return [_map_job_row(r) for r in rows]


async def _fetch_and_sync_adzuna(
    db_pool: asyncpg.Pool,
    settings: Any,
    location: str | None,
    keywords: str | None,
) -> None:
    adzuna = AdzunaClient(settings)
    adz_results = await adzuna.fetch_jobs(keywords=keywords, location=location)
    if adz_results:
        await _sync_adzuna_jobs(
            db_pool, adzuna, adzuna_results=adz_results, ttl_days=settings.adzuna_job_ttl_days
        )


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
    user_id: str | None = None,
) -> tuple[str, list[Any]]:
    query = """
        SELECT id, title, company, description, location,
               salary_min, salary_max, application_url, raw_data, source,
               created_at
        FROM   public.jobs
        WHERE  1=1
    """
    params: list[Any] = []
    n = 0
    # Exclude jobs the user already swiped on
    if user_id:
        n += 1
        query += f" AND id NOT IN (SELECT job_id FROM public.applications WHERE user_id = ${n})"
        params.append(user_id)
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
        params.append(source)
    if is_remote is True:
        query += " AND (location ILIKE '%remote%' OR location ILIKE '%anywhere%')"
    if job_type:
        n += 1
        query += f" AND (raw_data->>'job_type' ILIKE ${n} OR raw_data->>'employment_type' ILIKE ${n})"
        params.append(f"%{job_type}%")
    if settings.adzuna_job_ttl_days > 0:
        query += f" AND (source != 'adzuna' OR created_at >= now() - interval '{settings.adzuna_job_ttl_days} days')"
    query += " ORDER BY created_at DESC LIMIT $%d OFFSET $%d" % (n + 1, n + 2)
    params.extend([limit, offset])
    return query, params


def _map_job_row(r: Any) -> dict[str, Any]:
    raw = r.get("raw_data") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}

    logo_url = None
    is_remote = False
    job_type = None
    requirements = []
    date_posted = None
    if isinstance(raw, dict):
        logo_url = raw.get("logo_url") or raw.get("logo")
        job_type = raw.get("job_type") or raw.get("employment_type")
        requirements = raw.get("requirements") or []
        date_posted = raw.get("date_posted")

    location = r["location"] or ""
    if "remote" in location.lower() or "anywhere" in location.lower():
        is_remote = True

    return {
        "id": str(r["id"]),
        "title": r["title"],
        "company": r["company"],
        "description": r["description"],
        "location": location,
        "salary_min": float(r["salary_min"]) if r["salary_min"] is not None else None,
        "salary_max": float(r["salary_max"]) if r["salary_max"] is not None else None,
        "url": r["application_url"],
        "logo_url": logo_url,
        "source": r.get("source"),
        "is_remote": is_remote,
        "job_type": job_type,
        "requirements": requirements,
        "date_posted": date_posted or (r["created_at"].isoformat() if r.get("created_at") else None),
    }


async def _sync_adzuna_jobs(
    db_pool: asyncpg.Pool,
    adzuna: AdzunaClient,
    adzuna_results: list[dict[str, Any]],
    ttl_days: int,
) -> None:
    seen_external_ids: set[str] = set()
    seen_fingerprints: set[str] = set()
    cleaned_jobs: list[dict[str, Any]] = []

    for raw in adzuna_results:
        job_data = adzuna.map_to_db(raw)
        external_id = job_data["external_id"]
        fingerprint = f"{job_data['title']}::{job_data['company']}::{job_data['location']}".lower()

        if external_id in seen_external_ids or fingerprint in seen_fingerprints:
            continue
        if not _is_quality_listing(job_data):
            continue

        seen_external_ids.add(external_id)
        seen_fingerprints.add(fingerprint)
        cleaned_jobs.append(job_data)

    if not cleaned_jobs:
        return

    async with db_pool.acquire() as conn:
        await _cleanup_expired_adzuna_jobs(conn, ttl_days)
        for job_data in cleaned_jobs:
            await conn.execute(
                """
                INSERT INTO public.jobs
                    (external_id, title, company, description, location,
                     salary_min, salary_max, category, application_url, source, raw_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (external_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    description = EXCLUDED.description,
                    location = EXCLUDED.location,
                    salary_min = EXCLUDED.salary_min,
                    salary_max = EXCLUDED.salary_max,
                    application_url = EXCLUDED.application_url,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = now()
                """,
                job_data["external_id"],
                job_data["title"],
                job_data["company"],
                job_data["description"],
                job_data["location"],
                job_data["salary_min"],
                job_data["salary_max"],
                job_data["category"],
                job_data["application_url"],
                job_data["source"],
                json.dumps(job_data["raw_data"]),
            )


def _is_quality_listing(job_data: dict[str, Any]) -> bool:
    if not job_data.get("application_url"):
        return False
    description = job_data.get("description") or ""
    if len(description) < 80:
        return False
    salary_min = job_data.get("salary_min")
    salary_max = job_data.get("salary_max")
    return not (salary_min is None and salary_max is None)


async def _cleanup_expired_adzuna_jobs(conn: asyncpg.Connection, ttl_days: int) -> None:
    if ttl_days <= 0:
        return
    await conn.execute(
        "DELETE FROM public.jobs WHERE source = 'adzuna' AND created_at < now() - $1::interval",
        f"{ttl_days} days",
    )
