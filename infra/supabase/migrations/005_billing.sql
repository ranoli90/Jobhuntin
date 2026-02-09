-- Migration 005: Billing customers table
--
-- Stores the mapping between tenants and external billing providers (e.g., Stripe).
-- Actual payment logic lives in application code; this table tracks state.

CREATE TABLE IF NOT EXISTS public.billing_customers (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   uuid NOT NULL UNIQUE REFERENCES public.tenants (id) ON DELETE CASCADE,
    provider                    text NOT NULL DEFAULT 'STRIPE',
    provider_customer_id        text,
    current_subscription_id     text,
    current_subscription_status text NOT NULL DEFAULT 'none',  -- none, active, past_due, canceled, trialing
    current_period_end          timestamptz,
    metadata                    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    updated_at                  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_billing_customers_tenant_id ON public.billing_customers (tenant_id);
CREATE INDEX IF NOT EXISTS idx_billing_customers_provider   ON public.billing_customers (provider, provider_customer_id);

DROP TRIGGER IF EXISTS trg_billing_customers_updated_at ON public.billing_customers;
CREATE TRIGGER trg_billing_customers_updated_at
    BEFORE UPDATE ON public.billing_customers
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.billing_customers ENABLE ROW LEVEL SECURITY;

-- Only tenant owners/admins can see billing info (via application code; RLS blocks direct access)
DROP POLICY IF EXISTS "Tenant owners can read billing" ON public.billing_customers;
CREATE POLICY "Tenant owners can read billing"
    ON public.billing_customers FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members
            WHERE user_id = auth.uid() AND role IN ('OWNER', 'ADMIN')
        )
    );
