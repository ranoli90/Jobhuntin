-- Migration 015: M4 Enterprise Features
--
-- SSO configuration, priority queue scoring, enterprise settings,
-- audit logs, bulk campaigns.

-- ============================================================
-- 1. SSO configuration per tenant
-- ============================================================

CREATE TABLE IF NOT EXISTS public.sso_configs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL UNIQUE REFERENCES public.tenants (id) ON DELETE CASCADE,
    provider        text NOT NULL DEFAULT 'saml',  -- saml, oidc
    entity_id       text NOT NULL DEFAULT '',
    sso_url         text NOT NULL DEFAULT '',       -- IdP SSO endpoint
    certificate     text NOT NULL DEFAULT '',       -- IdP X.509 cert (PEM)
    oidc_client_id  text NOT NULL DEFAULT '',
    oidc_client_secret text NOT NULL DEFAULT '',
    oidc_issuer     text NOT NULL DEFAULT '',
    metadata_xml    text,
    is_active       boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.sso_configs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Tenant admins manage SSO" ON public.sso_configs;
CREATE POLICY "Tenant admins manage SSO"
    ON public.sso_configs FOR ALL
    USING (
        tenant_id IN (
            SELECT tm.tenant_id FROM public.tenant_members tm
            WHERE tm.user_id = auth.uid()
              AND tm.role IN ('OWNER', 'ADMIN')
        )
    );

-- ============================================================
-- 2. Priority score on applications (for priority queue)
-- ============================================================

ALTER TABLE public.applications
    ADD COLUMN IF NOT EXISTS priority_score int NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_applications_priority_queue
    ON public.applications (priority_score DESC, created_at ASC)
    WHERE status IN ('QUEUED', 'PROCESSING');

-- ============================================================
-- 3. Enterprise settings per tenant
-- ============================================================

CREATE TABLE IF NOT EXISTS public.enterprise_settings (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL UNIQUE REFERENCES public.tenants (id) ON DELETE CASCADE,
    custom_domain   text,
    white_label     jsonb NOT NULL DEFAULT '{}'::jsonb,  -- logo_url, brand_color, app_name
    sla_tier        text NOT NULL DEFAULT 'standard',     -- standard, premium, dedicated
    dedicated_pool  boolean NOT NULL DEFAULT false,
    support_email   text,
    support_slack   text,
    contract_start  timestamptz,
    contract_end    timestamptz,
    monthly_price   int,  -- custom pricing in cents
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.enterprise_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Tenant admins manage enterprise settings" ON public.enterprise_settings;
CREATE POLICY "Tenant admins manage enterprise settings"
    ON public.enterprise_settings FOR ALL
    USING (
        tenant_id IN (
            SELECT tm.tenant_id FROM public.tenant_members tm
            WHERE tm.user_id = auth.uid()
              AND tm.role IN ('OWNER', 'ADMIN')
        )
    );

-- ============================================================
-- 4. Audit log (SOC 2 compliance)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.audit_log (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid REFERENCES public.tenants (id) ON DELETE SET NULL,
    user_id     uuid REFERENCES auth.users (id) ON DELETE SET NULL,
    action      text NOT NULL,     -- member.invited, member.removed, sso.configured, billing.changed, etc.
    resource    text NOT NULL,     -- tenant, member, application, sso, billing
    resource_id text,
    details     jsonb NOT NULL DEFAULT '{}'::jsonb,
    ip_address  text,
    user_agent  text,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_tenant
    ON public.audit_log (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action
    ON public.audit_log (action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user
    ON public.audit_log (user_id, created_at DESC);

ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Tenant admins read audit logs" ON public.audit_log;
CREATE POLICY "Tenant admins read audit logs"
    ON public.audit_log FOR SELECT
    USING (
        tenant_id IN (
            SELECT tm.tenant_id FROM public.tenant_members tm
            WHERE tm.user_id = auth.uid()
              AND tm.role IN ('OWNER', 'ADMIN')
        )
    );

-- ============================================================
-- 5. Bulk campaigns
-- ============================================================

CREATE TABLE IF NOT EXISTS public.bulk_campaigns (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    created_by  uuid NOT NULL REFERENCES auth.users (id),
    name        text NOT NULL,
    filters     jsonb NOT NULL DEFAULT '{}'::jsonb,  -- {title, location, company, blueprint_key}
    status      text NOT NULL DEFAULT 'draft',        -- draft, running, paused, completed
    total_jobs  int NOT NULL DEFAULT 0,
    applied     int NOT NULL DEFAULT 0,
    failed      int NOT NULL DEFAULT 0,
    created_at  timestamptz NOT NULL DEFAULT now(),
    started_at  timestamptz,
    completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_bulk_campaigns_tenant
    ON public.bulk_campaigns (tenant_id, status);

ALTER TABLE public.bulk_campaigns ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Tenant members manage campaigns" ON public.bulk_campaigns;
CREATE POLICY "Tenant members manage campaigns"
    ON public.bulk_campaigns FOR ALL
    USING (
        tenant_id IN (
            SELECT tm.tenant_id FROM public.tenant_members tm
            WHERE tm.user_id = auth.uid()
        )
    );

-- ============================================================
-- 6. Update claim_next to use priority_score
-- ============================================================

CREATE OR REPLACE FUNCTION public.claim_next_prioritized(
    p_max_attempts int DEFAULT 3
)
RETURNS SETOF public.applications AS $$
BEGIN
    RETURN QUERY
    UPDATE public.applications
    SET status = 'PROCESSING',
        locked_at = now(),
        updated_at = now()
    WHERE id = (
        SELECT id FROM public.applications
        WHERE (status = 'QUEUED' OR (status = 'PROCESSING' AND locked_at < now() - interval '10 minutes'))
          AND attempt_count < p_max_attempts
        ORDER BY priority_score DESC, created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    RETURNING *;
END;
$$ LANGUAGE plpgsql;
