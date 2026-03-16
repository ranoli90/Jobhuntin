-- Migration: Add job sync tables for jobspy integration
-- Created: 2026-03-16
-- Purpose: Create tables required by job_sync_service.py worker

-- +migrate Up

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

-- Add comment for documentation
COMMENT ON TABLE public.popular_searches IS 'Tracks popular job search terms for sync prioritization';
COMMENT ON TABLE public.job_sync_runs IS 'History of job synchronization runs';
COMMENT ON TABLE public.job_sync_config IS 'Configuration for job sync sources';
COMMENT ON TABLE public.job_source_stats IS 'Aggregated statistics per job source';

-- +migrate Down

DROP TABLE IF EXISTS public.job_source_stats;
DROP TABLE IF EXISTS public.job_sync_config;
DROP TABLE IF EXISTS public.job_sync_runs;
DROP TABLE IF EXISTS public.popular_searches;