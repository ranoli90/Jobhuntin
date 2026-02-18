"""Run a full job sync to populate the database."""

import asyncio
import json
import os
import sys

# Must add paths BEFORE any imports
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "packages"))

import asyncpg
from jobspy import scrape_jobs

DATABASE_URL = "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/jobhuntin"


def normalize_job(row) -> dict:
    """Normalize a job row from JobSpy DataFrame."""
    import hashlib
    import math

    def clean_val(v):
        """Clean a value, handling NaN."""
        if v is None:
            return None
        if isinstance(v, float) and math.isnan(v):
            return None
        if str(v).lower() == "nan":
            return None
        return v

    source = str(clean_val(row.get("site")) or "unknown").lower()
    job_url = str(clean_val(row.get("job_url")) or "")

    if not job_url:
        return None

    # Generate external ID
    job_id = clean_val(row.get("id"))
    if job_id:
        external_id = f"{source}:{job_id}"
    else:
        url_hash = hashlib.sha256(job_url.encode()).hexdigest()[:16]
        external_id = f"{source}:{url_hash}"

    # Parse salary
    salary_min = clean_val(row.get("min_amount"))
    salary_max = clean_val(row.get("max_amount"))
    interval = clean_val(row.get("interval"))

    try:
        salary_min = int(float(salary_min)) if salary_min else None
    except Exception:
        salary_min = None
    try:
        salary_max = int(float(salary_max)) if salary_max else None
    except Exception:
        salary_max = None

    if interval == "hourly":
        salary_min = int(salary_min * 2080) if salary_min else None
        salary_max = int(salary_max * 2080) if salary_max else None

    # Build raw_data
    raw_data = {}
    for k, v in dict(row).items():
        try:
            cleaned = clean_val(v)
            if cleaned is not None:
                raw_data[k] = (
                    str(cleaned) if not isinstance(cleaned, (list, dict)) else cleaned
                )
        except Exception:
            pass

    return {
        "external_id": external_id,
        "title": str(clean_val(row.get("title")) or "Untitled")[:500],
        "company": str(clean_val(row.get("company")) or "Unknown")[:255],
        "description": str(clean_val(row.get("description")) or "")[:50000],
        "location": str(clean_val(row.get("location")) or "")[:500] or None,
        "is_remote": bool(clean_val(row.get("is_remote")) or False),
        "job_type": str(clean_val(row.get("job_type")) or "").lower()[:50] or None,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "application_url": job_url,
        "source": source,
        "date_posted": clean_val(row.get("date_posted")),
        "job_level": str(clean_val(row.get("job_level")) or "")[:50] or None,
        "company_industry": str(clean_val(row.get("company_industry")) or "")[:100]
        or None,
        "company_logo_url": clean_val(row.get("company_logo")),
        "raw_data": raw_data,
    }


async def sync_jobs():
    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)

    search_queries = [
        ("software engineer", "Remote"),
        ("software engineer", "San Francisco, CA"),
        ("product manager", "Remote"),
        ("data scientist", "Remote"),
    ]

    total_new = 0
    total_updated = 0
    total_skipped = 0

    for search_term, location in search_queries:
        print(f"\nFetching: '{search_term}' in '{location}'...")

        try:
            df = scrape_jobs(
                site_name=["indeed"],
                search_term=search_term,
                location=location,
                results_wanted=25,
                hours_old=168,
            )

            print(f"  Fetched {len(df)} jobs from Indeed")

            for _, row in df.iterrows():
                job = normalize_job(row)
                if not job:
                    total_skipped += 1
                    continue

                if len(job["description"]) < 50:
                    total_skipped += 1
                    continue

                # Check if exists
                existing = await conn.fetchrow(
                    "SELECT id FROM public.jobs WHERE external_id = $1",
                    job["external_id"],
                )

                if existing:
                    await conn.execute(
                        """
                        UPDATE public.jobs SET
                            title = $2, company = $3, description = $4,
                            location = $5, is_remote = $6, job_type = $7,
                            salary_min = $8, salary_max = $9,
                            application_url = $10, source = $11,
                            date_posted = $12, job_level = $13,
                            company_industry = $14, company_logo_url = $15,
                            raw_data = $16, last_synced_at = now()
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
                        job["source"],
                        job["date_posted"],
                        job["job_level"],
                        job["company_industry"],
                        job["company_logo_url"],
                        json.dumps(job["raw_data"]),
                    )
                    total_updated += 1
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
                    total_new += 1

            print(
                f"  Running totals: {total_new} new, {total_updated} updated, {total_skipped} skipped"
            )

        except Exception as e:
            print(f"  Error: {e}")

    # Check final count
    total_jobs = await conn.fetchval("SELECT COUNT(*) FROM public.jobs")
    print("\n=== Final Results ===")
    print(f"Total jobs in DB: {total_jobs}")
    print(f"New jobs added: {total_new}")
    print(f"Jobs updated: {total_updated}")
    print(f"Jobs skipped: {total_skipped}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(sync_jobs())
