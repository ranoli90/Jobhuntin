-- Migration 025: Multi-tenant isolation for embeddings
--
-- Adds tenant_id to embeddings tables for proper isolation
-- and RLS policies for tenant data access

-- Add tenant_id to job_embeddings
ALTER TABLE public.job_embeddings 
ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES public.tenants (id) ON DELETE CASCADE;

-- Add tenant_id to profile_embeddings  
ALTER TABLE public.profile_embeddings
ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES public.tenants (id) ON DELETE CASCADE;

-- Create indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_job_embeddings_tenant_id ON public.job_embeddings (tenant_id);
CREATE INDEX IF NOT EXISTS idx_profile_embeddings_tenant_id ON public.profile_embeddings (tenant_id);

-- Update RLS policies for tenant isolation
DROP POLICY IF EXISTS "Authenticated users can read job embeddings" ON public.job_embeddings;

CREATE POLICY "Users can read job embeddings in their tenant"
    ON public.job_embeddings FOR SELECT
    TO authenticated
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid()
        )
        OR tenant_id IS NULL
    );

CREATE POLICY "Service role can manage all job embeddings"
    ON public.job_embeddings FOR ALL
    TO service_role
    USING (true);

DROP POLICY IF EXISTS "Users can read own profile embeddings" ON public.profile_embeddings;

CREATE POLICY "Users can read own profile embeddings with tenant check"
    ON public.profile_embeddings FOR SELECT
    USING (
        user_id = auth.uid()
        AND (
            tenant_id IN (
                SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid()
            )
            OR tenant_id IS NULL
        )
    );

CREATE POLICY "Users can insert own profile embeddings"
    ON public.profile_embeddings FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own profile embeddings"
    ON public.profile_embeddings FOR UPDATE
    USING (user_id = auth.uid());

-- Add tenant_id constraint to user_preferences (already has it from RLS, ensure indexed)
CREATE INDEX IF NOT EXISTS idx_user_preferences_tenant_id ON public.user_preferences (tenant_id);

-- Function to get tenant_id for a user (helper for RLS)
CREATE OR REPLACE FUNCTION public.get_user_tenant_id()
RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
    SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid() LIMIT 1;
$$;

-- Audit log table for GDPR operations
CREATE TABLE IF NOT EXISTS public.gdpr_audit_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
    tenant_id uuid REFERENCES public.tenants (id) ON DELETE SET NULL,
    operation text NOT NULL CHECK (operation IN ('export', 'delete', 'access_request')),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    request_id uuid NOT NULL DEFAULT gen_random_uuid(),
    ip_address text,
    user_agent text,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    metadata jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_gdpr_audit_user_id ON public.gdpr_audit_log (user_id);
CREATE INDEX IF NOT EXISTS idx_gdpr_audit_tenant_id ON public.gdpr_audit_log (tenant_id);
CREATE INDEX IF NOT EXISTS idx_gdpr_audit_created_at ON public.gdpr_audit_log (created_at);

-- RLS for GDPR audit log
ALTER TABLE public.gdpr_audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own GDPR audit entries"
    ON public.gdpr_audit_log FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Service role can manage all GDPR audit entries"
    ON public.gdpr_audit_log FOR ALL
    TO service_role
    USING (true);

-- Trigger for updated_at on GDPR audit log
DROP TRIGGER IF EXISTS trg_gdpr_audit_updated_at ON public.gdpr_audit_log;
CREATE TRIGGER trg_gdpr_audit_updated_at
    BEFORE UPDATE ON public.gdpr_audit_log
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
