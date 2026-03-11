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

-- 015: tenants.slug, jobs.external_id, jobs.application_url, applications columns (schema alignment)
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS slug VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_slug ON public.tenants(slug) WHERE slug IS NOT NULL;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS application_url TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_external_id ON public.jobs(external_id) WHERE external_id IS NOT NULL;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ;
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS available_at TIMESTAMPTZ;

-- Worker claim function (claim_next_prioritized)
CREATE OR REPLACE FUNCTION public.claim_next_prioritized(p_max_attempts int DEFAULT 3)
RETURNS SETOF public.applications AS $$
BEGIN
  RETURN QUERY
  UPDATE public.applications
  SET status = 'PROCESSING', locked_at = now(), updated_at = now()
  WHERE id = (
    SELECT id FROM public.applications
    WHERE (status = 'QUEUED' OR (status = 'PROCESSING' AND locked_at < now() - interval '10 minutes'))
      AND (snoozed_until IS NULL OR snoozed_until < now())
      AND (available_at IS NULL OR available_at <= now())
      AND attempt_count < p_max_attempts
    ORDER BY priority_score DESC, created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
  )
  RETURNING *;
END;
$$ LANGUAGE plpgsql;

-- Stripe webhook idempotency: prevent duplicate processing on retries
CREATE TABLE IF NOT EXISTS public.processed_stripe_events (
    event_id TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Contact form submissions from public marketing site (jobhuntin.com/contact)
CREATE TABLE IF NOT EXISTS public.contact_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    company VARCHAR(200),
    inquiry_type VARCHAR(50) NOT NULL DEFAULT 'general' CHECK (inquiry_type IN ('general', 'support', 'sales', 'partnership')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_contact_messages_created_at ON public.contact_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contact_messages_inquiry_type ON public.contact_messages(inquiry_type);
