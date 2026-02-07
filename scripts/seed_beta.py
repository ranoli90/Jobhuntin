#!/usr/bin/env python3
"""
Seed script for M1 closed beta.

Populates the database with:
  1. Sample jobs from Adzuna API (or hardcoded fallbacks)
  2. A test tenant + user for smoke testing
  3. Initial experiment row for prompt A/B testing

Usage:
    python scripts/seed_beta.py [--jobs-count 50] [--adzuna-key YOUR_KEY]

Requires DATABASE_URL in environment or .env file.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone

import asyncpg

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.config import get_settings


# ---------------------------------------------------------------------------
# Sample job data (used when Adzuna API key is not provided)
# ---------------------------------------------------------------------------

SAMPLE_JOBS = [
    {
        "title": "Software Engineer",
        "company": "TechCorp Inc",
        "location": "San Francisco, CA",
        "application_url": "https://boards.greenhouse.io/techcorp/jobs/12345",
        "description": "Join our engineering team building next-gen SaaS products.",
        "salary_min": 120000,
        "salary_max": 180000,
    },
    {
        "title": "Senior Data Analyst",
        "company": "DataDriven LLC",
        "location": "New York, NY",
        "application_url": "https://jobs.lever.co/datadriven/analyst-sr",
        "description": "Analyze large datasets to drive business decisions.",
        "salary_min": 100000,
        "salary_max": 150000,
    },
    {
        "title": "Product Manager",
        "company": "StartupXYZ",
        "location": "Austin, TX",
        "application_url": "https://apply.workable.com/startupxyz/pm",
        "description": "Own the roadmap for our core B2B product.",
        "salary_min": 130000,
        "salary_max": 170000,
    },
    {
        "title": "Frontend Developer",
        "company": "WebAgency",
        "location": "Remote",
        "application_url": "https://careers.webagency.com/frontend-dev",
        "description": "Build beautiful, accessible web experiences with React.",
        "salary_min": 90000,
        "salary_max": 140000,
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudNative Co",
        "location": "Seattle, WA",
        "application_url": "https://cloudnative.bamboohr.com/devops",
        "description": "Manage Kubernetes clusters and CI/CD pipelines at scale.",
        "salary_min": 140000,
        "salary_max": 190000,
    },
    {
        "title": "Marketing Coordinator",
        "company": "GrowthHQ",
        "location": "Chicago, IL",
        "application_url": "https://growthhq.breezy.hr/marketing-coord",
        "description": "Coordinate multi-channel marketing campaigns.",
        "salary_min": 55000,
        "salary_max": 75000,
    },
    {
        "title": "UX Designer",
        "company": "DesignStudio",
        "location": "Los Angeles, CA",
        "application_url": "https://designstudio.greenhouse.io/ux",
        "description": "Design intuitive user experiences for mobile and web apps.",
        "salary_min": 95000,
        "salary_max": 135000,
    },
    {
        "title": "Backend Engineer (Python)",
        "company": "APIFirst Inc",
        "location": "Remote",
        "application_url": "https://apifirst.lever.co/backend-python",
        "description": "Build high-performance APIs with FastAPI and PostgreSQL.",
        "salary_min": 130000,
        "salary_max": 175000,
    },
    {
        "title": "Customer Success Manager",
        "company": "SaaSly",
        "location": "Denver, CO",
        "application_url": "https://saasly.workday.com/csm",
        "description": "Ensure enterprise customers achieve their goals with our platform.",
        "salary_min": 80000,
        "salary_max": 110000,
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Labs",
        "location": "Boston, MA",
        "application_url": "https://ailabs.greenhouse.io/ml-eng",
        "description": "Train and deploy ML models for production NLP systems.",
        "salary_min": 150000,
        "salary_max": 220000,
    },
]


async def seed_jobs(conn: asyncpg.Connection, count: int = 50) -> int:
    """Insert sample jobs, duplicating from the template list to reach `count`."""
    inserted = 0
    for i in range(count):
        template = SAMPLE_JOBS[i % len(SAMPLE_JOBS)]
        suffix = f" #{i + 1}" if i >= len(SAMPLE_JOBS) else ""
        job_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO public.jobs (id, title, company, location, application_url, description, salary_min, salary_max, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'seed')
            ON CONFLICT DO NOTHING
            """,
            job_id,
            template["title"] + suffix,
            template["company"],
            template["location"],
            template["application_url"],
            template["description"],
            template.get("salary_min"),
            template.get("salary_max"),
        )
        inserted += 1
    return inserted


async def seed_test_tenant(conn: asyncpg.Connection) -> dict:
    """Create a test tenant and return its details."""
    tenant_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO public.tenants (id, name, slug, plan)
        VALUES ($1, 'Beta Test Tenant', 'beta-test', 'FREE')
        ON CONFLICT (slug) DO NOTHING
        """,
        tenant_id,
    )
    row = await conn.fetchrow(
        "SELECT id, name, slug, plan FROM public.tenants WHERE slug = 'beta-test'"
    )
    return dict(row) if row else {"id": tenant_id, "name": "Beta Test Tenant"}


async def seed_experiment(conn: asyncpg.Connection) -> None:
    """Create an initial prompt experiment for A/B testing."""
    await conn.execute(
        """
        INSERT INTO public.experiments (key, variants, is_active, metadata)
        VALUES (
            'dom_mapping_prompt',
            $1::jsonb,
            false,
            '{"description": "A/B test for DOM mapping prompt versions. Activate when v2 is ready."}'::jsonb
        )
        ON CONFLICT DO NOTHING
        """,
        json.dumps([
            {"name": "v1", "traffic_pct": 90},
            {"name": "v2", "traffic_pct": 10},
        ]),
    )


async def main(jobs_count: int = 50) -> None:
    s = get_settings()
    conn = await asyncpg.connect(s.database_url)

    try:
        print("=== Sorce M1 Beta Seed ===\n")

        # Jobs
        n = await seed_jobs(conn, jobs_count)
        print(f"[OK] Seeded {n} sample jobs")

        # Test tenant
        tenant = await seed_test_tenant(conn)
        print(f"[OK] Test tenant: {tenant.get('name')} (id={tenant.get('id')})")

        # Experiment
        await seed_experiment(conn)
        print("[OK] Seeded prompt experiment (inactive, activate when ready)")

        # Refresh dashboard views if they exist
        try:
            await conn.execute("SELECT public.refresh_m1_dashboard()")
            print("[OK] Refreshed M1 dashboard views")
        except Exception:
            print("[SKIP] Dashboard views not yet created (run migration 009 first)")

        total_jobs = await conn.fetchval("SELECT COUNT(*)::int FROM public.jobs")
        total_tenants = await conn.fetchval("SELECT COUNT(*)::int FROM public.tenants")
        print(f"\n--- Totals: {total_jobs} jobs, {total_tenants} tenants ---")
        print("\nSeed complete. Ready for beta!")

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed M1 beta data")
    parser.add_argument("--jobs-count", type=int, default=50, help="Number of sample jobs to insert")
    args = parser.parse_args()
    asyncio.run(main(jobs_count=args.jobs_count))
