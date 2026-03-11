-- +migrate Up
-- Add tenants.slug, jobs.external_id, applications.attempt_count for tests and production schema alignment.
-- Required by: TenantRepo.get_by_slug, job_sync_service, agent claim logic, test_agent_integration, test_failure_drills.

-- Tenants: slug for tenant lookup (e.g. beta-test, test-xxx)
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS slug VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_slug ON public.tenants(slug) WHERE slug IS NOT NULL;

-- Jobs: external_id for deduplication (JobSpy, Adzuna); application_url for agent (001 has url)
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS application_url TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_external_id ON public.jobs(external_id) WHERE external_id IS NOT NULL;

-- Applications: attempt_count for agent retry logic
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0;

-- +migrate Down
ALTER TABLE public.applications DROP COLUMN IF EXISTS attempt_count;
DROP INDEX IF EXISTS public.idx_jobs_external_id;
ALTER TABLE public.jobs DROP COLUMN IF EXISTS external_id;
ALTER TABLE public.jobs DROP COLUMN IF EXISTS application_url;
DROP INDEX IF EXISTS public.idx_tenants_slug;
ALTER TABLE public.tenants DROP COLUMN IF EXISTS slug;
