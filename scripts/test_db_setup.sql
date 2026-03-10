-- Test DB schema setup: run before pytest when using Docker Postgres
-- Ensures all tables/columns required by tests exist

-- Tenants
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS slug VARCHAR(255);

-- Jobs
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS application_url TEXT;

-- Applications
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS blueprint_key VARCHAR(50) DEFAULT 'job-app';
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS priority_score INTEGER DEFAULT 0;
CREATE UNIQUE INDEX IF NOT EXISTS idx_applications_user_job ON public.applications(user_id, job_id);

-- Profiles (if missing)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    resume_url TEXT,
    tenant_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS profiles_user_id_key ON profiles(user_id);

-- Application events (for failure_drills, record_event)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'application_event_type') THEN
    CREATE TYPE public.application_event_type AS ENUM (
      'CREATED', 'CLAIMED', 'STARTED_PROCESSING', 'REQUIRES_INPUT', 'APPLIED', 'SUBMITTED',
      'COMPLETED', 'REGISTERED', 'FAILED', 'REVOKED'
    );
  END IF;
END $$;
-- Ensure CREATED exists (for tests that use it)
ALTER TYPE public.application_event_type ADD VALUE IF NOT EXISTS 'CREATED';
CREATE TABLE IF NOT EXISTS application_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    event_type public.application_event_type NOT NULL,
    payload JSONB DEFAULT '{}',
    tenant_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);
