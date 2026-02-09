-- Migration 012: M3 Team Features
--
-- Extends tenants for TEAM plan, adds team_invites table, seat tracking.

-- ============================================================
-- 1. Add TEAM to tenant_plan enum
-- ============================================================

ALTER TYPE public.tenant_plan ADD VALUE IF NOT EXISTS 'TEAM';

-- ============================================================
-- 2. Seat tracking columns on tenants
-- ============================================================

ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS seat_count int NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS max_seats int NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS team_name text;

-- ============================================================
-- 3. Team invites
-- ============================================================

CREATE TABLE IF NOT EXISTS public.team_invites (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    invited_by      uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    email           text NOT NULL,
    role            text NOT NULL DEFAULT 'MEMBER',  -- MEMBER, ADMIN
    status          text NOT NULL DEFAULT 'pending',  -- pending, accepted, expired, revoked
    token           text NOT NULL UNIQUE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    expires_at      timestamptz NOT NULL DEFAULT (now() + interval '7 days'),
    accepted_at     timestamptz
);

CREATE INDEX IF NOT EXISTS idx_team_invites_tenant
    ON public.team_invites (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_team_invites_email
    ON public.team_invites (email, status);
CREATE INDEX IF NOT EXISTS idx_team_invites_token
    ON public.team_invites (token) WHERE status = 'pending';

ALTER TABLE public.team_invites ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Tenant admins manage invites" ON public.team_invites;
CREATE POLICY "Tenant admins manage invites"
    ON public.team_invites FOR ALL
    USING (
        tenant_id IN (
            SELECT tm.tenant_id FROM public.tenant_members tm
            WHERE tm.user_id = auth.uid()
              AND tm.role IN ('OWNER', 'ADMIN')
        )
    );

-- ============================================================
-- 4. Add stripe_subscription_item_id to billing_customers
--    (needed for per-seat quantity updates)
-- ============================================================

ALTER TABLE public.billing_customers
    ADD COLUMN IF NOT EXISTS stripe_subscription_item_id text;

-- ============================================================
-- 5. Shared job lists for teams
-- ============================================================

CREATE TABLE IF NOT EXISTS public.team_job_lists (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    name        text NOT NULL DEFAULT 'Shared List',
    created_by  uuid NOT NULL REFERENCES auth.users (id),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.team_job_list_items (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id     uuid NOT NULL REFERENCES public.team_job_lists (id) ON DELETE CASCADE,
    job_id      uuid NOT NULL REFERENCES public.jobs (id) ON DELETE CASCADE,
    added_by    uuid NOT NULL REFERENCES auth.users (id),
    notes       text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (list_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_team_job_lists_tenant
    ON public.team_job_lists (tenant_id);
CREATE INDEX IF NOT EXISTS idx_team_job_list_items_list
    ON public.team_job_list_items (list_id);

ALTER TABLE public.team_job_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_job_list_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Team members access lists" ON public.team_job_lists;
CREATE POLICY "Team members access lists"
    ON public.team_job_lists FOR ALL
    USING (
        tenant_id IN (
            SELECT tm.tenant_id FROM public.tenant_members tm
            WHERE tm.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Team members access list items" ON public.team_job_list_items;
CREATE POLICY "Team members access list items"
    ON public.team_job_list_items FOR ALL
    USING (
        list_id IN (
            SELECT tjl.id FROM public.team_job_lists tjl
            JOIN public.tenant_members tm ON tm.tenant_id = tjl.tenant_id
            WHERE tm.user_id = auth.uid()
        )
    );
