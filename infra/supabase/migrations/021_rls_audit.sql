-- Migration 021: RLS Audit - Secure remaining tables
--
-- Enables RLS and adds policies for tables identified in audit.

-- ============================================================
-- 1. Marketplace Tables
-- ============================================================

ALTER TABLE public.author_payouts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Authors can read own payouts"
    ON public.author_payouts FOR SELECT
    USING (
        author_tenant_id IN (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
        )
    );

ALTER TABLE public.enterprise_onboarding ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenant admins manage onboarding"
    ON public.enterprise_onboarding FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
        )
    );

-- ============================================================
-- 2. Platform Tables
-- ============================================================

ALTER TABLE public.webhook_deliveries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenant admins read webhook logs"
    ON public.webhook_deliveries FOR SELECT
    USING (
        endpoint_id IN (
            SELECT id FROM public.webhook_endpoints
            WHERE tenant_id IN (
                SELECT tenant_id FROM public.tenant_members
                WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
            )
        )
    );

ALTER TABLE public.api_usage ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenant admins read api usage"
    ON public.api_usage FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
        )
    );

ALTER TABLE public.university_partners ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Partner admins manage own profile"
    ON public.university_partners FOR ALL
    USING (
        admin_tenant_id IN (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
        )
    );

ALTER TABLE public.university_student_imports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Partner admins manage imports"
    ON public.university_student_imports FOR ALL
    USING (
        partner_id IN (
            SELECT id FROM public.university_partners
            WHERE admin_tenant_id IN (
                SELECT tenant_id FROM public.tenant_members
                WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
            )
        )
    );

ALTER TABLE public.contract_renewals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenant admins read renewals"
    ON public.contract_renewals FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
        )
    );

ALTER TABLE public.platform_telemetry ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenant admins read own telemetry"
    ON public.platform_telemetry FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
        )
    );
