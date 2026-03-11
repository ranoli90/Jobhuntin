-- SEO Engine checkpoint table for durable progress tracking
CREATE TABLE IF NOT EXISTS seo_engine_progress (
  id SERIAL PRIMARY KEY,
  service_id TEXT UNIQUE NOT NULL,
  last_index INTEGER NOT NULL DEFAULT 0,
  last_submission_at TIMESTAMPTZ,
  daily_quota_used INTEGER NOT NULL DEFAULT 0,
  daily_quota_reset TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc' + interval '1 day'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_seo_engine_progress_service_id ON seo_engine_progress(service_id);

-- Optional: submission log for audit
CREATE TABLE IF NOT EXISTS seo_submission_log (
  id SERIAL PRIMARY KEY,
  service_id TEXT NOT NULL,
  batch_url_file TEXT,
  urls_submitted INTEGER NOT NULL,
  success BOOLEAN NOT NULL,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_seo_submission_log_service_id ON seo_submission_log(service_id);

-- Enable RLS for safety (optional, if you want to restrict access)
-- ALTER TABLE seo_engine_progress ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE seo_submission_log ENABLE ROW LEVEL SECURITY;

-- Job Dead Letter Queue (used by agent and DLQ manager)
CREATE TABLE IF NOT EXISTS public.job_dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
    tenant_id UUID,
    failure_reason TEXT NOT NULL,
    attempt_count INT NOT NULL DEFAULT 1,
    last_error TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_job_dead_letter_queue_application ON public.job_dead_letter_queue(application_id);
CREATE INDEX IF NOT EXISTS idx_job_dead_letter_queue_tenant ON public.job_dead_letter_queue(tenant_id);
CREATE INDEX IF NOT EXISTS idx_job_dead_letter_queue_created ON public.job_dead_letter_queue(created_at DESC);

-- 015: tenants.slug, jobs.external_id, jobs.application_url, applications.attempt_count (schema alignment for tests)
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS slug VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_slug ON public.tenants(slug) WHERE slug IS NOT NULL;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS application_url TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_external_id ON public.jobs(external_id) WHERE external_id IS NOT NULL;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0;

-- Stripe webhook idempotency: prevent duplicate processing on retries
CREATE TABLE IF NOT EXISTS public.processed_stripe_events (
    event_id TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
