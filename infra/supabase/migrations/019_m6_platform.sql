-- Migration 019: M6 — Platform API, Staffing Agency, University Partners, Telemetry
--
-- API keys, webhooks, metered billing, staffing batches, university partners,
-- contract renewals, platform telemetry.

-- ============================================================
-- 1. API Keys for developer platform
-- ============================================================

CREATE TABLE IF NOT EXISTS public.api_keys (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    name            text NOT NULL DEFAULT 'Default',
    key_hash        text NOT NULL UNIQUE,
    key_prefix      text NOT NULL,              -- first 8 chars for display (sk_live_xxxx...)
    tier            text NOT NULL DEFAULT 'free', -- free, pro, enterprise
    scopes          text[] NOT NULL DEFAULT '{read,write}',
    rate_limit_rpm  int NOT NULL DEFAULT 60,     -- requests per minute
    monthly_quota   int NOT NULL DEFAULT 100,    -- 0 = unlimited
    calls_this_month int NOT NULL DEFAULT 0,
    is_active       boolean NOT NULL DEFAULT true,
    last_used_at    timestamptz,
    expires_at      timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON public.api_keys (tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON public.api_keys (key_prefix);

-- ============================================================
-- 2. Webhook endpoints
-- ============================================================

CREATE TABLE IF NOT EXISTS public.webhook_endpoints (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    url             text NOT NULL,
    secret          text NOT NULL,
    events          text[] NOT NULL DEFAULT '{application.completed,application.failed,application.hold}',
    is_active       boolean NOT NULL DEFAULT true,
    failure_count   int NOT NULL DEFAULT 0,
    last_success_at timestamptz,
    last_failure_at timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_webhooks_tenant ON public.webhook_endpoints (tenant_id);

-- ============================================================
-- 3. Webhook delivery log
-- ============================================================

CREATE TABLE IF NOT EXISTS public.webhook_deliveries (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_id     uuid NOT NULL REFERENCES public.webhook_endpoints (id) ON DELETE CASCADE,
    event_type      text NOT NULL,
    payload         jsonb NOT NULL DEFAULT '{}'::jsonb,
    response_status int,
    response_body   text,
    attempt         int NOT NULL DEFAULT 1,
    delivered_at    timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- 4. API usage metering (Stripe metered billing)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.api_usage (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id      uuid NOT NULL REFERENCES public.api_keys (id) ON DELETE CASCADE,
    tenant_id       uuid NOT NULL REFERENCES public.tenants (id),
    endpoint        text NOT NULL,
    method          text NOT NULL DEFAULT 'GET',
    status_code     int NOT NULL DEFAULT 200,
    latency_ms      int,
    metered         boolean NOT NULL DEFAULT false,
    stripe_usage_id text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_usage_key ON public.api_usage (api_key_id, created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_tenant ON public.api_usage (tenant_id, created_at);

-- ============================================================
-- 5. Staffing agency batches
-- ============================================================

CREATE TABLE IF NOT EXISTS public.staffing_batches (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    client_name     text NOT NULL,
    client_portal   text NOT NULL DEFAULT '',
    role_title      text NOT NULL,
    role_description text NOT NULL DEFAULT '',
    candidates      jsonb NOT NULL DEFAULT '[]'::jsonb,
    candidate_count int NOT NULL DEFAULT 0,
    submitted       int NOT NULL DEFAULT 0,
    succeeded       int NOT NULL DEFAULT 0,
    failed          int NOT NULL DEFAULT 0,
    status          text NOT NULL DEFAULT 'draft',  -- draft, submitting, completed, partial
    price_per_submission_cents int NOT NULL DEFAULT 200,
    base_monthly_cents int NOT NULL DEFAULT 200000,
    created_at      timestamptz NOT NULL DEFAULT now(),
    completed_at    timestamptz
);

CREATE INDEX IF NOT EXISTS idx_staffing_tenant ON public.staffing_batches (tenant_id, status);

-- ============================================================
-- 6. University partner accounts
-- ============================================================

CREATE TABLE IF NOT EXISTS public.university_partners (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                text NOT NULL,
    domain              text NOT NULL UNIQUE,
    logo_url            text,
    admin_tenant_id     uuid REFERENCES public.tenants (id),
    bundle_id           text,                       -- custom app bundle (white-label)
    branding            jsonb NOT NULL DEFAULT '{}'::jsonb,
    revenue_share_pct   int NOT NULL DEFAULT 50,    -- 50% of student PRO upgrades
    total_students      int NOT NULL DEFAULT 0,
    active_students     int NOT NULL DEFAULT 0,
    total_applications  int NOT NULL DEFAULT 0,
    is_active           boolean NOT NULL DEFAULT true,
    contract_start      timestamptz,
    contract_end        timestamptz,
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- 7. University student imports
-- ============================================================

CREATE TABLE IF NOT EXISTS public.university_student_imports (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id      uuid NOT NULL REFERENCES public.university_partners (id),
    imported_by     uuid REFERENCES auth.users (id),
    filename        text NOT NULL DEFAULT '',
    total_rows      int NOT NULL DEFAULT 0,
    created_count   int NOT NULL DEFAULT 0,
    skipped_count   int NOT NULL DEFAULT 0,
    error_count     int NOT NULL DEFAULT 0,
    status          text NOT NULL DEFAULT 'processing',  -- processing, completed, failed
    errors          jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- 8. Contract renewal tracking
-- ============================================================

CREATE TABLE IF NOT EXISTS public.contract_renewals (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    renewal_date    timestamptz NOT NULL,
    contract_value  int NOT NULL DEFAULT 0,
    status          text NOT NULL DEFAULT 'upcoming', -- upcoming, notified_90, notified_60, notified_30, renewed, churned
    notification_log jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_renewals_date ON public.contract_renewals (renewal_date, status);

-- ============================================================
-- 9. Platform telemetry events
-- ============================================================

CREATE TABLE IF NOT EXISTS public.platform_telemetry (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      text NOT NULL,
    tenant_id       uuid REFERENCES public.tenants (id),
    blueprint_key   text,
    vertical        text,
    metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_type ON public.platform_telemetry (event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_telemetry_vertical ON public.platform_telemetry (vertical, created_at);

-- ============================================================
-- 10. RLS
-- ============================================================

ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Tenant manages own keys" ON public.api_keys;
CREATE POLICY "Tenant manages own keys" ON public.api_keys FOR ALL
    USING (tenant_id IN (SELECT tm.tenant_id FROM public.tenant_members tm WHERE tm.user_id = auth.uid()));

ALTER TABLE public.webhook_endpoints ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Tenant manages own webhooks" ON public.webhook_endpoints;
CREATE POLICY "Tenant manages own webhooks" ON public.webhook_endpoints FOR ALL
    USING (tenant_id IN (SELECT tm.tenant_id FROM public.tenant_members tm WHERE tm.user_id = auth.uid()));

ALTER TABLE public.staffing_batches ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Tenant manages own batches" ON public.staffing_batches;
CREATE POLICY "Tenant manages own batches" ON public.staffing_batches FOR ALL
    USING (tenant_id IN (SELECT tm.tenant_id FROM public.tenant_members tm WHERE tm.user_id = auth.uid()));
