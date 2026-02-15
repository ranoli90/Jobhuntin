-- ============================================
-- JobSpy Integration Migration
-- Adds columns for multi-source job data
-- ============================================

-- Add new columns to jobs table
ALTER TABLE public.jobs 
  ADD COLUMN IF NOT EXISTS is_remote BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS job_type VARCHAR(50),
  ADD COLUMN IF NOT EXISTS date_posted DATE,
  ADD COLUMN IF NOT EXISTS job_level VARCHAR(50),
  ADD COLUMN IF NOT EXISTS company_industry VARCHAR(100),
  ADD COLUMN IF NOT EXISTS company_logo_url TEXT,
  ADD COLUMN IF NOT EXISTS emails TEXT[],
  ADD COLUMN IF NOT EXISTS raw_data JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_jobs_is_remote ON public.jobs(is_remote);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON public.jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_date_posted ON public.jobs(date_posted DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON public.jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_last_synced ON public.jobs(last_synced_at);

-- Add source check constraint
ALTER TABLE public.jobs 
  DROP CONSTRAINT IF EXISTS check_job_source;

ALTER TABLE public.jobs 
  ADD CONSTRAINT check_job_source 
  CHECK (source IN ('adzuna', 'indeed', 'linkedin', 'zip_recruiter', 'glassdoor', 'google', 'bayt', 'manual', 'api'));

-- ============================================
-- Job Sync Tracking Tables
-- ============================================

-- Track sync runs
CREATE TABLE IF NOT EXISTS public.job_sync_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source VARCHAR(50) NOT NULL,
  search_term VARCHAR(255) NOT NULL,
  location VARCHAR(255),
  status VARCHAR(50) NOT NULL DEFAULT 'running',
  jobs_fetched INTEGER DEFAULT 0,
  jobs_new INTEGER DEFAULT 0,
  jobs_updated INTEGER DEFAULT 0,
  jobs_skipped INTEGER DEFAULT 0,
  jobs_deduplicated INTEGER DEFAULT 0,
  error_message TEXT,
  error_stack TEXT,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  duration_ms INTEGER,
  proxy_used VARCHAR(255),
  rate_limited BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_job_sync_runs_source ON public.job_sync_runs(source);
CREATE INDEX IF NOT EXISTS idx_job_sync_runs_status ON public.job_sync_runs(status);
CREATE INDEX IF NOT EXISTS idx_job_sync_runs_started ON public.job_sync_runs(started_at DESC);

-- Track popular search terms for proactive syncing
CREATE TABLE IF NOT EXISTS public.popular_searches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  search_term VARCHAR(255) NOT NULL,
  location VARCHAR(255),
  search_count INTEGER DEFAULT 1,
  last_searched_at TIMESTAMPTZ DEFAULT now(),
  last_synced_at TIMESTAMPTZ,
  priority INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  UNIQUE(search_term, location)
);

CREATE INDEX IF NOT EXISTS idx_popular_searches_count ON public.popular_searches(search_count DESC);
CREATE INDEX IF NOT EXISTS idx_popular_searches_priority ON public.popular_searches(priority DESC);
CREATE INDEX IF NOT EXISTS idx_popular_searches_sync ON public.popular_searches(last_synced_at) WHERE is_active = TRUE;

-- ============================================
-- Job Sync Configuration
-- ============================================

CREATE TABLE IF NOT EXISTS public.job_sync_config (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source VARCHAR(50) NOT NULL UNIQUE,
  enabled BOOLEAN DEFAULT TRUE,
  results_per_search INTEGER DEFAULT 50,
  min_hours_between_syncs INTEGER DEFAULT 4,
  last_sync_at TIMESTAMPTZ,
  last_error_at TIMESTAMPTZ,
  last_error_message TEXT,
  consecutive_failures INTEGER DEFAULT 0,
  total_jobs_fetched INTEGER DEFAULT 0,
  total_syncs INTEGER DEFAULT 0
);

-- Insert default config for each source
INSERT INTO public.job_sync_config (source, enabled, results_per_search) VALUES
  ('indeed', TRUE, 50),
  ('linkedin', TRUE, 50),
  ('zip_recruiter', TRUE, 50),
  ('glassdoor', TRUE, 50)
ON CONFLICT (source) DO NOTHING;

-- ============================================
-- Row Level Security
-- ============================================

ALTER TABLE public.job_sync_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.popular_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_sync_config ENABLE ROW LEVEL SECURITY;

-- Only service role can access sync tables
CREATE POLICY "Service role full access on job_sync_runs" ON public.job_sync_runs
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "Service role full access on popular_searches" ON public.popular_searches
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "Service role full access on job_sync_config" ON public.job_sync_config
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

-- ============================================
-- Views for Monitoring
-- ============================================

CREATE OR REPLACE VIEW public.job_sync_summary AS
SELECT 
  source,
  COUNT(*) FILTER (WHERE status = 'completed') AS successful_syncs,
  COUNT(*) FILTER (WHERE status = 'failed') AS failed_syncs,
  COUNT(*) FILTER (WHERE status = 'partial') AS partial_syncs,
  SUM(jobs_new) AS total_new_jobs,
  SUM(jobs_updated) AS total_updated_jobs,
  AVG(duration_ms) FILTER (WHERE status = 'completed') AS avg_duration_ms,
  MAX(started_at) AS last_sync_at
FROM public.job_sync_runs
WHERE started_at > now() - interval '7 days'
GROUP BY source;

CREATE OR REPLACE VIEW public.job_source_stats AS
SELECT 
  source,
  COUNT(*) AS total_jobs,
  COUNT(*) FILTER (WHERE is_remote = TRUE) AS remote_jobs,
  COUNT(*) FILTER (WHERE salary_min IS NOT NULL OR salary_max IS NOT NULL) AS jobs_with_salary,
  COUNT(*) FILTER (WHERE last_synced_at > now() - interval '7 days') AS recently_synced,
  MAX(last_synced_at) AS last_synced_at
FROM public.jobs
GROUP BY source;

-- ============================================
-- Cleanup Function (called by worker)
-- ============================================

CREATE OR REPLACE FUNCTION public.cleanup_expired_jobs(ttl_days INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM public.jobs 
  WHERE source IN ('indeed', 'linkedin', 'zip_recruiter', 'glassdoor', 'adzuna')
    AND last_synced_at IS NOT NULL
    AND last_synced_at < now() - (ttl_days || ' days')::interval;
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
