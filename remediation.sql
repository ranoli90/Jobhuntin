-- JobHuntin Remediation Migrations
-- Run this against your Supabase database

-- TASK 1: Worker Retry Logic
-- Add column to schedule retries in the future
ALTER TABLE public.applications
ADD COLUMN IF NOT EXISTS available_at timestamptz DEFAULT NULL;

-- TASK 2: AI Result Caching
-- Cache table to avoid expensive LLM re-computation
CREATE TABLE IF NOT EXISTS public.job_match_cache (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id        text NOT NULL,
    profile_hash  text NOT NULL,
    score_data    jsonb NOT NULL,
    created_at    timestamptz DEFAULT now(),
    UNIQUE(job_id, profile_hash)
);

CREATE INDEX IF NOT EXISTS idx_job_match_cache_lookup ON public.job_match_cache(job_id, profile_hash);

-- TASK 3: Database Bottlenecks
-- Index for worker polling hot path (status='QUEUED')
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_status_attempt
ON public.applications(status, attempt_count);

-- Index for tenant member lookup (2 calls per API request)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenant_members_user_id
ON public.tenant_members(user_id);

-- Index for checking held input status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_application_inputs_status 
ON public.application_inputs(application_id);
