-- Migration 001: Application Events table and enum
--
-- Adds append-only audit log for agent and user state transitions.
-- Safe to re-run: uses IF NOT EXISTS / OR REPLACE where possible.

-- Enum for event types
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'application_event_type') THEN
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
    END IF;
END
$$;

-- Events table
CREATE TABLE IF NOT EXISTS public.application_events (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  uuid NOT NULL REFERENCES public.applications (id) ON DELETE CASCADE,
    event_type      public.application_event_type NOT NULL,
    payload         jsonb DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_app_events_app_created
    ON public.application_events (application_id, created_at);

CREATE INDEX IF NOT EXISTS idx_app_events_type_created
    ON public.application_events (event_type, created_at);

-- RLS
ALTER TABLE public.application_events ENABLE ROW LEVEL SECURITY;

-- Policy (idempotent via DROP IF EXISTS + CREATE)
DROP POLICY IF EXISTS "Users can read events for own applications" ON public.application_events;
CREATE POLICY "Users can read events for own applications"
    ON public.application_events FOR SELECT
    USING (
        application_id IN (
            SELECT id FROM public.applications WHERE user_id = auth.uid()
        )
    );

-- Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.application_events;

-- Adding new event types to the enum (forward-compatible pattern):
-- When new event types are needed, add them like this:
--   ALTER TYPE public.application_event_type ADD VALUE IF NOT EXISTS 'NEW_EVENT';
-- This is backwards-compatible: old code that doesn't know the new value
-- simply won't emit it. Reads using .get() with defaults are safe.
