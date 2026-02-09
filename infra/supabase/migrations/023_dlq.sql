-- Migration 023: Dead Letter Queue (DLQ)
--
-- Stores jobs that have failed max_attempts times for manual review.

CREATE TABLE IF NOT EXISTS public.job_dead_letter_queue (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  uuid NOT NULL REFERENCES public.applications (id) ON DELETE CASCADE,
    tenant_id       uuid REFERENCES public.tenants (id) ON DELETE CASCADE,
    failure_reason  text NOT NULL,
    attempt_count   int NOT NULL,
    last_error      text,
    payload         jsonb,  -- snapshot of the job/task data at failure
    created_at      timestamptz NOT NULL DEFAULT now(),
    reviewed_at     timestamptz,
    reviewer_id     uuid REFERENCES auth.users (id) ON DELETE SET NULL,
    resolution      text    -- 'retry', 'ignore', 'refund', etc.
);

CREATE INDEX IF NOT EXISTS idx_dlq_created_at ON public.job_dead_letter_queue (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dlq_tenant_id ON public.job_dead_letter_queue (tenant_id);

-- RLS
ALTER TABLE public.job_dead_letter_queue ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Tenant admins view DLQ" ON public.job_dead_letter_queue;
CREATE POLICY "Tenant admins view DLQ"
    ON public.job_dead_letter_queue FOR SELECT
    USING (
        tenant_id IN (
            SELECT tm.tenant_id FROM public.tenant_members tm
            WHERE tm.user_id = auth.uid()
              AND tm.role IN ('OWNER', 'ADMIN')
        )
    );
