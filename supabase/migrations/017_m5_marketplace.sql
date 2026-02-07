-- Migration 017: M5 — Blueprint Marketplace + Self-Serve Enterprise + Revenue Intelligence
--
-- Marketplace tables, annual billing, contract management, revenue share.

-- ============================================================
-- 1. Blueprint marketplace
-- ============================================================

CREATE TABLE IF NOT EXISTS public.marketplace_blueprints (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug                text NOT NULL UNIQUE,
    name                text NOT NULL,
    description         text NOT NULL DEFAULT '',
    long_description    text NOT NULL DEFAULT '',
    category            text NOT NULL DEFAULT 'general',
    icon_url            text,
    author_tenant_id    uuid REFERENCES public.tenants (id) ON DELETE SET NULL,
    author_name         text NOT NULL DEFAULT '',
    version             text NOT NULL DEFAULT '1.0.0',
    source_code         jsonb NOT NULL DEFAULT '{}'::jsonb,
    config_schema       jsonb NOT NULL DEFAULT '{}'::jsonb,
    approval_status     text NOT NULL DEFAULT 'pending',  -- pending, approved, rejected, deprecated
    install_count       int NOT NULL DEFAULT 0,
    rating_avg          numeric(3,2) NOT NULL DEFAULT 0,
    rating_count        int NOT NULL DEFAULT 0,
    price_cents         int NOT NULL DEFAULT 0,           -- 0 = free
    revenue_share_pct   int NOT NULL DEFAULT 70,          -- author gets 70%
    stripe_product_id   text,
    stripe_price_id     text,
    is_featured         boolean NOT NULL DEFAULT false,
    is_active           boolean NOT NULL DEFAULT true,
    published_at        timestamptz,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mp_blueprints_status ON public.marketplace_blueprints (approval_status, is_active);
CREATE INDEX IF NOT EXISTS idx_mp_blueprints_category ON public.marketplace_blueprints (category);
CREATE INDEX IF NOT EXISTS idx_mp_blueprints_author ON public.marketplace_blueprints (author_tenant_id);

-- ============================================================
-- 2. Blueprint installations
-- ============================================================

CREATE TABLE IF NOT EXISTS public.blueprint_installations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    blueprint_id    uuid NOT NULL REFERENCES public.marketplace_blueprints (id) ON DELETE CASCADE,
    tenant_id       uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    installed_by    uuid REFERENCES auth.users (id),
    version         text NOT NULL,
    config          jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_active       boolean NOT NULL DEFAULT true,
    installed_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (blueprint_id, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_bp_installs_tenant ON public.blueprint_installations (tenant_id);

-- ============================================================
-- 3. Blueprint reviews
-- ============================================================

CREATE TABLE IF NOT EXISTS public.blueprint_reviews (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    blueprint_id    uuid NOT NULL REFERENCES public.marketplace_blueprints (id) ON DELETE CASCADE,
    tenant_id       uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES auth.users (id),
    rating          int NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text     text NOT NULL DEFAULT '',
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (blueprint_id, user_id)
);

-- ============================================================
-- 4. Blueprint author payouts (Stripe Connect)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.author_payouts (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    author_tenant_id    uuid NOT NULL REFERENCES public.tenants (id),
    blueprint_id        uuid NOT NULL REFERENCES public.marketplace_blueprints (id),
    amount_cents        int NOT NULL,
    platform_fee_cents  int NOT NULL,
    stripe_transfer_id  text,
    status              text NOT NULL DEFAULT 'pending',  -- pending, paid, failed
    period_start        timestamptz NOT NULL,
    period_end          timestamptz NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- 5. Stripe Connect accounts for blueprint authors
-- ============================================================

ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS stripe_connect_id text,
    ADD COLUMN IF NOT EXISTS contract_value_cents int,
    ADD COLUMN IF NOT EXISTS contract_start timestamptz,
    ADD COLUMN IF NOT EXISTS contract_end timestamptz,
    ADD COLUMN IF NOT EXISTS billing_interval text NOT NULL DEFAULT 'monthly',  -- monthly, annual
    ADD COLUMN IF NOT EXISTS churn_risk_score numeric(5,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS annual_discount_pct int NOT NULL DEFAULT 0;

-- ============================================================
-- 6. Enterprise self-serve onboarding steps
-- ============================================================

CREATE TABLE IF NOT EXISTS public.enterprise_onboarding (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL UNIQUE REFERENCES public.tenants (id) ON DELETE CASCADE,
    step            text NOT NULL DEFAULT 'domain',  -- domain, sso, contract, billing, complete
    custom_domain   text,
    contract_signed boolean NOT NULL DEFAULT false,
    contract_pdf    text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- 7. Smart pre-fill learning (per-user answer memory)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.answer_memory (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    field_label     text NOT NULL,
    field_type      text NOT NULL DEFAULT 'text',
    answer_value    text NOT NULL,
    use_count       int NOT NULL DEFAULT 1,
    last_used_at    timestamptz NOT NULL DEFAULT now(),
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, field_label)
);

CREATE INDEX IF NOT EXISTS idx_answer_memory_user ON public.answer_memory (user_id);

-- ============================================================
-- 8. RLS
-- ============================================================

ALTER TABLE public.marketplace_blueprints ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone reads approved blueprints" ON public.marketplace_blueprints;
CREATE POLICY "Anyone reads approved blueprints"
    ON public.marketplace_blueprints FOR SELECT
    USING (approval_status = 'approved' AND is_active = true);

ALTER TABLE public.blueprint_installations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Tenant members manage installations" ON public.blueprint_installations;
CREATE POLICY "Tenant members manage installations"
    ON public.blueprint_installations FOR ALL
    USING (tenant_id IN (SELECT tm.tenant_id FROM public.tenant_members tm WHERE tm.user_id = auth.uid()));

ALTER TABLE public.blueprint_reviews ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users manage own reviews" ON public.blueprint_reviews;
CREATE POLICY "Users manage own reviews"
    ON public.blueprint_reviews FOR ALL
    USING (user_id = auth.uid());

ALTER TABLE public.answer_memory ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users manage own answers" ON public.answer_memory;
CREATE POLICY "Users manage own answers"
    ON public.answer_memory FOR ALL
    USING (user_id = auth.uid());
