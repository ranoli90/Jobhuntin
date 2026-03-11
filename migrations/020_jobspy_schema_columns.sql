-- +migrate Up
-- Add JobSpy schema columns for backwards compatibility with 001/015 migrations.
-- infra/postgres/schema.sql uses these; job_sync_service and job_search expect them.

ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS application_url TEXT;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS is_remote BOOLEAN DEFAULT FALSE;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS date_posted TIMESTAMPTZ;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS job_level TEXT;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS company_industry TEXT;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS company_logo_url TEXT;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS raw_data JSONB DEFAULT '{}';
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS is_scam BOOLEAN DEFAULT FALSE;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS quality_score REAL;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ DEFAULT now();

-- Backfill is_remote from remote_policy where possible
UPDATE public.jobs SET is_remote = (remote_policy IN ('remote', 'hybrid'))
WHERE is_remote IS NULL AND remote_policy IS NOT NULL;

-- Backfill date_posted from posted_date
UPDATE public.jobs SET date_posted = posted_date::timestamptz
WHERE date_posted IS NULL AND posted_date IS NOT NULL;

-- Backfill job_level from experience_level
UPDATE public.jobs SET job_level = experience_level
WHERE job_level IS NULL AND experience_level IS NOT NULL;

-- Backfill application_url from url
UPDATE public.jobs SET application_url = url
WHERE application_url IS NULL AND url IS NOT NULL;

-- +migrate Down
-- (Columns are additive; no destructive down for compatibility)
