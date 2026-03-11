-- Job Dead Letter Queue — used by agent and DLQ manager
-- Matches schema expected by apps/worker/agent.py and apps/worker/dlq_manager.py

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
