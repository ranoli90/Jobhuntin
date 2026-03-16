#!/usr/bin/env python3
"""Apply migration 042 to Render PostgreSQL database."""

import asyncio
import asyncpg
import os
import sys

# Database connection string from Render (use environment variable)
DATABASE_URL = os.environ.get("RENDER_DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: RENDER_DATABASE_URL environment variable not set")
    sys.exit(1)

MIGRATION_SQL = """
-- Table for tracking popular job search terms
CREATE TABLE IF NOT EXISTS public.popular_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_term TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT 'Remote',
    search_count INTEGER NOT NULL DEFAULT 1,
    last_searched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(search_term, location)
);

CREATE INDEX IF NOT EXISTS idx_popular_searches_count ON public.popular_searches (search_count DESC, last_searched_at DESC);

-- Table for tracking job sync run history
CREATE TABLE IF NOT EXISTS public.job_sync_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    jobs_fetched INTEGER NOT NULL DEFAULT 0,
    jobs_new INTEGER NOT NULL DEFAULT 0,
    jobs_updated INTEGER NOT NULL DEFAULT 0,
    jobs_skipped INTEGER NOT NULL DEFAULT 0,
    errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    duration_ms INTEGER,
    search_term TEXT,
    location TEXT
);

CREATE INDEX IF NOT EXISTS idx_job_sync_runs_source ON public.job_sync_runs (source);
CREATE INDEX IF NOT EXISTS idx_job_sync_runs_started_at ON public.job_sync_runs (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_sync_runs_status ON public.job_sync_runs (status);

-- Table for job sync source configuration
CREATE TABLE IF NOT EXISTS public.job_sync_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL UNIQUE,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_sync_config_source ON public.job_sync_config (source);

-- Insert default sync sources
INSERT INTO public.job_sync_config (source, is_enabled, config)
VALUES 
    ('indeed', true, '{"rate_limit": 100, "priority": 1}'::jsonb),
    ('linkedin', true, '{"rate_limit": 50, "priority": 2}'::jsonb),
    ('zip_recruiter', true, '{"rate_limit": 100, "priority": 3}'::jsonb),
    ('glassdoor', true, '{"rate_limit": 50, "priority": 4}'::jsonb)
ON CONFLICT (source) DO NOTHING;

-- Table for job source statistics (optional, referenced in code)
CREATE TABLE IF NOT EXISTS public.job_source_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL UNIQUE,
    total_jobs INTEGER NOT NULL DEFAULT 0,
    new_jobs_24h INTEGER NOT NULL DEFAULT 0,
    updated_jobs_24h INTEGER NOT NULL DEFAULT 0,
    avg_quality_score REAL,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

async def apply_migration():
    print("Connecting to Render PostgreSQL...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Applying migration 042_job_sync_tables.sql...")
        
        # Execute each statement separately
        statements = [s.strip() for s in MIGRATION_SQL.split(';') if s.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                print(f"  Executing statement {i+1}/{len(statements)}...")
                try:
                    await conn.execute(statement)
                except Exception as e:
                    print(f"    Warning: {e}")
        
        print("\n✅ Migration applied successfully!")
        
        # Verify tables exist
        print("\nVerifying tables...")
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('popular_searches', 'job_sync_runs', 'job_sync_config', 'job_source_stats')
            ORDER BY table_name
        """)
        
        print("Tables created:")
        for t in tables:
            print(f"  - {t['table_name']}")
        
        # Check config data
        config_count = await conn.fetchval("SELECT COUNT(*) FROM public.job_sync_config")
        print(f"\nJob sync config entries: {config_count}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_migration())
