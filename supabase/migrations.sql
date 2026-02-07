-- Part 1: Extended Database and Event Model
-- Migration to harden the existing schema with audit events, retry tracking,
-- and richer application_inputs metadata.

-- ============================================================
-- Enum: application event types
-- ============================================================
CREATE TYPE public.application_event_type AS ENUM (
    'CREATED',
    'CLAIMED',
    'STARTED_PROCESSING',
    'REQUIRES_INPUT_RAISED',
    'USER_ANSWERED',
    'RESUMED',
    'SUBMITTED',
    'FAILED',
    'RETRY_SCHEDULED'
);

-- ============================================================
-- Table: public.application_events
-- Append-only audit log for every agent and user-visible state
-- transition on an application.
-- ============================================================
CREATE TABLE public.application_events (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  uuid NOT NULL REFERENCES public.applications (id) ON DELETE CASCADE,
    event_type      public.application_event_type NOT NULL,
    payload         jsonb DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_app_events_app_created
    ON public.application_events (application_id, created_at);

CREATE INDEX idx_app_events_type_created
    ON public.application_events (event_type, created_at);

-- ============================================================
-- Extend: public.applications
-- Add retry tracking and last-error context columns.
-- ============================================================
ALTER TABLE public.applications
    ADD COLUMN IF NOT EXISTS attempt_count     integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error        text,
    ADD COLUMN IF NOT EXISTS last_processed_at timestamptz;

-- ============================================================
-- Extend: public.application_inputs
-- Add resolved flag and rich metadata for the field.
-- ============================================================
ALTER TABLE public.application_inputs
    ADD COLUMN IF NOT EXISTS resolved boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS meta     jsonb   DEFAULT '{}'::jsonb;

-- ============================================================
-- RLS for application_events (read-only for the owning user)
-- ============================================================
ALTER TABLE public.application_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read events for own applications"
    ON public.application_events FOR SELECT
    USING (
        application_id IN (
            SELECT id FROM public.applications WHERE user_id = auth.uid()
        )
    );

-- ============================================================
-- Realtime: publish application_events for observability
-- ============================================================
ALTER PUBLICATION supabase_realtime ADD TABLE public.application_events;

-- ============================================================
-- Event Emission Policy (reference documentation in SQL comments)
--
-- Every major state transition MUST produce exactly one event row:
--
--  Trigger                          | event_type              | payload example
-- ----------------------------------|-------------------------|---------------------------------------
--  User swipes right (app created)  | CREATED                 | {job_id, user_id}
--  Worker claims a QUEUED task      | CLAIMED                 | {attempt_count}
--  Worker begins DOM processing     | STARTED_PROCESSING      | {application_url}
--  Worker finds unresolved fields   | REQUIRES_INPUT_RAISED   | {unresolved_fields: [...]}
--  User answers hold questions      | USER_ANSWERED           | {input_id, question, answer}
--  Worker resumes after answers     | RESUMED                 | {attempt_count, answered_count}
--  Worker submits form successfully | SUBMITTED               | {submitted_at}
--  Worker encounters terminal error | FAILED                  | {error_message, attempt_count}
--  API re-queues after user answers | RETRY_SCHEDULED         | {application_id}
-- ============================================================
