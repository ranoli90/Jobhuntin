-- Migration 008: Product Analytics, Evaluations, and Experimentation
--
-- Adds:
--   1. analytics_events — client + server event tracking
--   2. user_properties — per-user metadata (device, cohort, etc.)
--   3. agent_evaluations — success/failure labels from SYSTEM and USER
--   4. experiments — A/B experiment definitions
--   5. experiment_assignments — sticky variant assignments per subject

-- ============================================================
-- 1. analytics_events
-- ============================================================

CREATE TABLE IF NOT EXISTS public.analytics_events (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid REFERENCES public.tenants(id) ON DELETE SET NULL,
    user_id         uuid REFERENCES public.users(id) ON DELETE SET NULL,
    session_id      uuid,
    event_type      text NOT NULL,
    properties      jsonb NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_tenant_created
    ON public.analytics_events (tenant_id, created_at);

CREATE INDEX IF NOT EXISTS idx_analytics_events_user_created
    ON public.analytics_events (user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_analytics_events_type_created
    ON public.analytics_events (event_type, created_at);

-- RLS: users can read their own events; service role can insert
ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY analytics_events_select_own ON public.analytics_events
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY analytics_events_insert_service ON public.analytics_events
    FOR INSERT WITH CHECK (true);

-- ============================================================
-- 2. user_properties (optional enrichment)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.user_properties (
    user_id     uuid PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    properties  jsonb NOT NULL DEFAULT '{}',
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- 3. agent_evaluations
-- ============================================================

CREATE TABLE IF NOT EXISTS public.agent_evaluations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  uuid NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
    tenant_id       uuid REFERENCES public.tenants(id) ON DELETE SET NULL,
    user_id         uuid REFERENCES public.users(id) ON DELETE SET NULL,
    source          text NOT NULL CHECK (source IN ('SYSTEM', 'USER')),
    label           text NOT NULL CHECK (label IN ('SUCCESS', 'PARTIAL', 'FAILURE')),
    reason          text,
    metadata        jsonb NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_evaluations_app_created
    ON public.agent_evaluations (application_id, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_evaluations_tenant_label_created
    ON public.agent_evaluations (tenant_id, label, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_evaluations_user_created
    ON public.agent_evaluations (user_id, created_at);

-- RLS: users can read evaluations for their own applications
ALTER TABLE public.agent_evaluations ENABLE ROW LEVEL SECURITY;

CREATE POLICY agent_evaluations_select_own ON public.agent_evaluations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY agent_evaluations_insert_service ON public.agent_evaluations
    FOR INSERT WITH CHECK (true);

-- ============================================================
-- 4. experiments
-- ============================================================

CREATE TABLE IF NOT EXISTS public.experiments (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    key                 text NOT NULL UNIQUE,
    variants            jsonb NOT NULL DEFAULT '[{"name":"A","traffic_pct":50},{"name":"B","traffic_pct":50}]',
    is_active           boolean NOT NULL DEFAULT true,
    metadata            jsonb NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- 5. experiment_assignments
-- ============================================================

CREATE TABLE IF NOT EXISTS public.experiment_assignments (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id   uuid NOT NULL REFERENCES public.experiments(id) ON DELETE CASCADE,
    subject_type    text NOT NULL CHECK (subject_type IN ('USER', 'TENANT')),
    subject_id      uuid NOT NULL,
    variant         text NOT NULL,
    assigned_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (experiment_id, subject_type, subject_id)
);

CREATE INDEX IF NOT EXISTS idx_experiment_assignments_experiment
    ON public.experiment_assignments (experiment_id);

CREATE INDEX IF NOT EXISTS idx_experiment_assignments_subject
    ON public.experiment_assignments (subject_type, subject_id);
