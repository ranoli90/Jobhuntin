"""
Job search domain logic: Adzuna integration and job listing/filtering.
"""
import json
from typing import Any

import asyncpg

from shared.config import get_settings
from backend.domain.job_boards import AdzunaClient

async def search_and_list_jobs(
    db_pool: asyncpg.Pool,
    location: str | None = None,
    min_salary: int | None = None,
    keywords: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search jobs:
    1. Fetch from Adzuna (if keywords/location provided) and sync to DB.
    2. Query DB with filters.
    """
    s = get_settings()
    adzuna = AdzunaClient(s)
    
    # Proactively fetch from Adzuna if we have keywords/location
    if keywords or location:
        adz_results = await adzuna.fetch_jobs(keywords=keywords, location=location)
        if adz_results:
            async with db_pool.acquire() as conn:
                for raw_job in adz_results:
                    job_data = adzuna.map_to_db(raw_job)
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
                            raw_data = EXCLUDED.raw_data
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

    async with db_pool.acquire() as conn:
        query = """
            SELECT id, title, company, description, location,
                   salary_min, salary_max, application_url, raw_data
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
        query += " ORDER BY created_at DESC LIMIT 100"
        rows = await conn.fetch(query, *params)

    jobs = []
    for r in rows:
        raw = r.get("raw_data") or {}
        # Handle case where raw_data might be a string (if not automatically decoded by asyncpg codec)
        # But asyncpg usually decodes jsonb to dict if configured. 
        # The original code did `raw.get("logo_url")` assuming it's a dict.
        # But wait, `raw_data` in DB is jsonb. asyncpg returns it as string unless type codec is set.
        # However, the original code had `raw = r.get("raw_data") or {}` and then checked `hasattr(raw, "get")`.
        # If it's a string, it doesn't have `get`.
        # Let's keep the safety check.
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except:
                raw = {}
        
        logo_url = None
        if isinstance(raw, dict):
            logo_url = raw.get("logo_url") or raw.get("logo")
            
        jobs.append({
            "id": str(r["id"]),
            "title": r["title"],
            "company": r["company"],
            "description": r["description"],
            "location": r["location"],
            "salary_min": float(r["salary_min"]) if r["salary_min"] is not None else None,
            "salary_max": float(r["salary_max"]) if r["salary_max"] is not None else None,
            "url": r["application_url"],
            "logo_url": logo_url,
        })
    return jobs
