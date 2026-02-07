-- Migration 013: Grant Blueprint Schema Extensions
--
-- Adds grant-specific profile storage and grant application metadata.

-- ============================================================
-- 1. Grant applicant profiles
-- ============================================================

CREATE TABLE IF NOT EXISTS public.grant_profiles (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    tenant_id           uuid REFERENCES public.tenants (id) ON DELETE SET NULL,
    organization_name   text NOT NULL DEFAULT '',
    organization_ein    text NOT NULL DEFAULT '',
    organization_type   text NOT NULL DEFAULT '',
    project_title       text NOT NULL DEFAULT '',
    project_description text NOT NULL DEFAULT '',
    requested_amount    numeric,
    budget_narrative    text NOT NULL DEFAULT '',
    grant_category      text NOT NULL DEFAULT '',
    contact_name        text NOT NULL DEFAULT '',
    contact_email       text NOT NULL DEFAULT '',
    contact_phone       text NOT NULL DEFAULT '',
    contact_location    text NOT NULL DEFAULT '',
    qualifications      jsonb NOT NULL DEFAULT '[]'::jsonb,
    raw_document_text   text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_grant_profiles_user
    ON public.grant_profiles (user_id);
CREATE INDEX IF NOT EXISTS idx_grant_profiles_tenant
    ON public.grant_profiles (tenant_id) WHERE tenant_id IS NOT NULL;

ALTER TABLE public.grant_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own grant profiles" ON public.grant_profiles;
CREATE POLICY "Users manage own grant profiles"
    ON public.grant_profiles FOR ALL
    USING (user_id = auth.uid());

-- ============================================================
-- 2. Grant-specific application metadata
-- ============================================================

ALTER TABLE public.applications
    ADD COLUMN IF NOT EXISTS grant_profile_id uuid REFERENCES public.grant_profiles (id);

-- ============================================================
-- 3. Grant portal registry (known grant sites)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.grant_portals (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text NOT NULL,
    domain          text NOT NULL UNIQUE,
    portal_type     text NOT NULL DEFAULT 'generic',  -- generic, grants_gov, foundation, university
    submit_selectors jsonb NOT NULL DEFAULT '[]'::jsonb,
    field_hints     jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now()
);

INSERT INTO public.grant_portals (name, domain, portal_type, submit_selectors) VALUES
    ('Grants.gov', 'grants.gov', 'grants_gov', '["button:has-text(\"Submit\")","button:has-text(\"Submit Application\")"]'),
    ('Foundation Directory Online', 'fdo.foundationcenter.org', 'foundation', '["button[type=\"submit\"]"]'),
    ('Generic Grant Portal', '*', 'generic', '["button[type=\"submit\"]","button:has-text(\"Submit\")"]')
ON CONFLICT (domain) DO NOTHING;
