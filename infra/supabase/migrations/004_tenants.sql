-- Migration 004: Multi-tenancy — tenants, tenant_members, tenant_id on existing tables
--
-- Introduces logical tenant isolation on a shared Postgres instance.
-- Safe to re-run: uses IF NOT EXISTS / IF NOT EXISTS patterns.

-- ============================================================
-- Enum: tenant plan tiers
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tenant_plan') THEN
        CREATE TYPE public.tenant_plan AS ENUM ('FREE', 'PRO', 'ENTERPRISE');
    END IF;
END
$$;

-- ============================================================
-- Enum: tenant member roles
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tenant_member_role') THEN
        CREATE TYPE public.tenant_member_role AS ENUM ('OWNER', 'ADMIN', 'MEMBER', 'SUPPORT_AGENT');
    END IF;
END
$$;

-- ============================================================
-- Table: public.tenants
-- ============================================================
CREATE TABLE IF NOT EXISTS public.tenants (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text NOT NULL,
    slug            text NOT NULL UNIQUE,
    plan            public.tenant_plan NOT NULL DEFAULT 'FREE',
    plan_metadata   jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON public.tenants (slug);
CREATE INDEX IF NOT EXISTS idx_tenants_plan ON public.tenants (plan);

-- updated_at trigger
DROP TRIGGER IF EXISTS trg_tenants_updated_at ON public.tenants;
CREATE TRIGGER trg_tenants_updated_at
    BEFORE UPDATE ON public.tenants
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ============================================================
-- Table: public.tenant_members
-- ============================================================
CREATE TABLE IF NOT EXISTS public.tenant_members (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    user_id     uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
    role        public.tenant_member_role NOT NULL DEFAULT 'MEMBER',
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),

    UNIQUE (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_members_user_id   ON public.tenant_members (user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_members_tenant_id ON public.tenant_members (tenant_id);

DROP TRIGGER IF EXISTS trg_tenant_members_updated_at ON public.tenant_members;
CREATE TRIGGER trg_tenant_members_updated_at
    BEFORE UPDATE ON public.tenant_members
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ============================================================
-- Add tenant_id to existing tables
-- ============================================================

-- profiles: every profile belongs to a tenant
ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES public.tenants (id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_profiles_tenant_id ON public.profiles (tenant_id);

-- applications: every application belongs to a tenant
ALTER TABLE public.applications
    ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES public.tenants (id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_applications_tenant_id        ON public.applications (tenant_id);
CREATE INDEX IF NOT EXISTS idx_applications_tenant_status     ON public.applications (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_applications_tenant_created    ON public.applications (tenant_id, created_at);

-- application_inputs: inherit tenant from application (denormalized for query speed)
ALTER TABLE public.application_inputs
    ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES public.tenants (id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_app_inputs_tenant_id ON public.application_inputs (tenant_id);

-- application_events: inherit tenant from application (denormalized for query speed)
ALTER TABLE public.application_events
    ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES public.tenants (id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_app_events_tenant_id ON public.application_events (tenant_id);

-- jobs: nullable tenant_id (NULL = global/shared catalog from Adzuna)
ALTER TABLE public.jobs
    ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES public.tenants (id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_jobs_tenant_id ON public.jobs (tenant_id);

-- ============================================================
-- RLS for new tables
-- ============================================================
ALTER TABLE public.tenants        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_members ENABLE ROW LEVEL SECURITY;

-- Users can read tenants they belong to
DROP POLICY IF EXISTS "Users can read own tenants" ON public.tenants;
CREATE POLICY "Users can read own tenants"
    ON public.tenants FOR SELECT
    USING (
        id IN (SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid())
    );

-- Users can read their own memberships
DROP POLICY IF EXISTS "Users can read own memberships" ON public.tenant_members;
CREATE POLICY "Users can read own memberships"
    ON public.tenant_members FOR SELECT
    USING (user_id = auth.uid());

-- ============================================================
-- Update existing RLS policies to include tenant_id checks
-- ============================================================

-- profiles: user must own + be in tenant
DROP POLICY IF EXISTS "Users can read own profile" ON public.profiles;
CREATE POLICY "Users can read own profile"
    ON public.profiles FOR SELECT
    USING (
        auth.uid() = user_id
        AND tenant_id IN (SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid())
    );

-- applications: user must own + be in tenant
DROP POLICY IF EXISTS "Users can read own applications" ON public.applications;
CREATE POLICY "Users can read own applications"
    ON public.applications FOR SELECT
    USING (
        auth.uid() = user_id
        AND tenant_id IN (SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can insert own applications" ON public.applications;
CREATE POLICY "Users can insert own applications"
    ON public.applications FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND tenant_id IN (SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid())
    );

-- application_inputs: via tenant membership
DROP POLICY IF EXISTS "Users can read own application_inputs" ON public.application_inputs;
CREATE POLICY "Users can read own application_inputs"
    ON public.application_inputs FOR SELECT
    USING (
        tenant_id IN (SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid())
        AND application_id IN (SELECT id FROM public.applications WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can update own application_inputs answers" ON public.application_inputs;
CREATE POLICY "Users can update own application_inputs answers"
    ON public.application_inputs FOR UPDATE
    USING (
        tenant_id IN (SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid())
        AND application_id IN (SELECT id FROM public.applications WHERE user_id = auth.uid())
    )
    WITH CHECK (
        tenant_id IN (SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid())
        AND application_id IN (SELECT id FROM public.applications WHERE user_id = auth.uid())
    );

-- application_events: via tenant membership
DROP POLICY IF EXISTS "Users can read events for own applications" ON public.application_events;
CREATE POLICY "Users can read events for own applications"
    ON public.application_events FOR SELECT
    USING (
        tenant_id IN (SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid())
        AND application_id IN (SELECT id FROM public.applications WHERE user_id = auth.uid())
    );

-- Realtime for new tables
ALTER PUBLICATION supabase_realtime ADD TABLE public.tenants;
ALTER PUBLICATION supabase_realtime ADD TABLE public.tenant_members;
