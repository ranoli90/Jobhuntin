-- Migration 007: Blueprint support
--
-- Adds blueprint_key to tenants and applications so the worker can dispatch
-- to the correct AgentBlueprint implementation per task.
-- Creates SQL views with generic vocabulary (tasks, task_inputs, etc.).

-- ============================================================
-- Extend application_status enum for multi-blueprint support
-- ============================================================

-- Add SUBMITTED (used by grant, vendor-onboard, etc.)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'SUBMITTED'
          AND enumtypid = 'public.application_status'::regtype
    ) THEN
        ALTER TYPE public.application_status ADD VALUE 'SUBMITTED';
    END IF;
END$$;

-- Add COMPLETED (generic terminal status)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'COMPLETED'
          AND enumtypid = 'public.application_status'::regtype
    ) THEN
        ALTER TYPE public.application_status ADD VALUE 'COMPLETED';
    END IF;
END$$;

-- ============================================================
-- Add blueprint_key columns
-- ============================================================

ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS blueprint_key text NOT NULL DEFAULT 'job-app';

CREATE INDEX IF NOT EXISTS idx_tenants_blueprint_key ON public.tenants (blueprint_key);

ALTER TABLE public.applications
    ADD COLUMN IF NOT EXISTS blueprint_key text NOT NULL DEFAULT 'job-app';

CREATE INDEX IF NOT EXISTS idx_applications_blueprint_key ON public.applications (blueprint_key);

-- ============================================================
-- Generic vocabulary views
-- ============================================================

-- tasks: generic view over applications with status normalization
CREATE OR REPLACE VIEW public.tasks AS
SELECT
    id,
    user_id,
    job_id          AS target_form_id,
    tenant_id,
    blueprint_key,
    CASE
        WHEN status::text = 'APPLIED' THEN 'COMPLETED'
        ELSE status::text
    END             AS generic_status,
    status::text    AS raw_status,
    error_message,
    last_error,
    attempt_count,
    locked_at,
    submitted_at,
    last_processed_at,
    created_at,
    updated_at
FROM public.applications;

-- task_inputs: generic view over application_inputs
CREATE OR REPLACE VIEW public.task_inputs AS
SELECT
    id,
    application_id  AS task_id,
    tenant_id,
    selector,
    question,
    field_type,
    answer,
    resolved,
    meta,
    created_at,
    answered_at
FROM public.application_inputs;

-- task_events: generic view over application_events
CREATE OR REPLACE VIEW public.task_events AS
SELECT
    id,
    application_id  AS task_id,
    tenant_id,
    event_type,
    payload,
    created_at
FROM public.application_events;

-- target_forms: generic view over jobs
CREATE OR REPLACE VIEW public.target_forms AS
SELECT
    id,
    tenant_id,
    application_url AS form_url,
    COALESCE(tenant_id::text, 'global') AS scope,
    created_at
FROM public.jobs;
