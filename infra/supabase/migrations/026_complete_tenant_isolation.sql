-- Migration 026: Complete Multi-tenant Embedding Isolation with RLS Policies
--
-- Completes tenant isolation for embeddings:
-- 1. Auto-populates tenant_id on job_embeddings and profile_embeddings
-- 2. Provides functions for updating existing embeddings with correct tenant_id
-- 3. Adds tenant-aware functions for embedding operations
-- 4. Ensures all embedding queries are tenant-scoped

-- ============================================================
-- Function: Auto-populate tenant_id for job_embeddings
-- ============================================================
-- When a job_embedding is inserted, derive tenant_id from the job's owner
CREATE OR REPLACE FUNCTION public.set_job_embedding_tenant_id()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    job_tenant_id uuid;
BEGIN
    -- If tenant_id is already set, leave it alone
    IF NEW.tenant_id IS NOT NULL THEN
        RETURN NEW;
    END IF;
    
    -- Get tenant_id from the associated job -> user -> profile -> tenant
    SELECT p.tenant_id INTO job_tenant_id
    FROM public.jobs j
    JOIN public.profiles p ON p.user_id = j.user_id
    WHERE j.id = NEW.job_id
    LIMIT 1;
    
    IF job_tenant_id IS NOT NULL THEN
        NEW.tenant_id := job_tenant_id;
    END IF;
    
    RETURN NEW;
END;
$$;

-- Trigger for auto-populating tenant_id on job_embeddings insert
DROP TRIGGER IF EXISTS trg_job_embeddings_set_tenant_id ON public.job_embeddings;
CREATE TRIGGER trg_job_embeddings_set_tenant_id
    BEFORE INSERT ON public.job_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION public.set_job_embedding_tenant_id();

-- ============================================================
-- Function: Auto-populate tenant_id for profile_embeddings
-- ============================================================
-- When a profile_embedding is inserted, derive tenant_id from the profile
CREATE OR REPLACE FUNCTION public.set_profile_embedding_tenant_id()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    profile_tenant_id uuid;
BEGIN
    -- If tenant_id is already set, leave it alone
    IF NEW.tenant_id IS NOT NULL THEN
        RETURN NEW;
    END IF;
    
    -- Get tenant_id from the user's profile
    SELECT p.tenant_id INTO profile_tenant_id
    FROM public.profiles p
    WHERE p.user_id = NEW.user_id
    LIMIT 1;
    
    IF profile_tenant_id IS NOT NULL THEN
        NEW.tenant_id := profile_tenant_id;
    END IF;
    
    RETURN NEW;
END;
$$;

-- Trigger for auto-populating tenant_id on profile_embeddings insert
DROP TRIGGER IF EXISTS trg_profile_embeddings_set_tenant_id ON public.profile_embeddings;
CREATE TRIGGER trg_profile_embeddings_set_tenant_id
    BEFORE INSERT ON public.profile_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION public.set_profile_embedding_tenant_id();

-- ============================================================
-- Function: Update existing embeddings with correct tenant_id
-- ============================================================
CREATE OR REPLACE FUNCTION public.backfill_embedding_tenant_ids()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Update job_embeddings where tenant_id is NULL
    UPDATE public.job_embeddings je
    SET tenant_id = p.tenant_id
    FROM public.jobs j
    JOIN public.profiles p ON p.user_id = j.user_id
    WHERE je.job_id = j.id
      AND je.tenant_id IS NULL
      AND p.tenant_id IS NOT NULL;
    
    -- Update profile_embeddings where tenant_id is NULL
    UPDATE public.profile_embeddings pe
    SET tenant_id = p.tenant_id
    FROM public.profiles p
    WHERE pe.user_id = p.user_id
      AND pe.tenant_id IS NULL
      AND p.tenant_id IS NOT NULL;
    
    RAISE NOTICE 'Embedding tenant_id backfill completed';
END;
$$;

-- Execute the backfill
SELECT public.backfill_embedding_tenant_ids();

-- ============================================================
-- Tenant-aware functions for embedding operations
-- ============================================================

-- Function: Get job embeddings for a tenant
CREATE OR REPLACE FUNCTION public.get_job_embeddings_by_tenant(p_tenant_id uuid)
RETURNS TABLE (
    id uuid,
    job_id uuid,
    embedding jsonb,
    text_hash text,
    created_at timestamptz,
    updated_at timestamptz
)
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
    SELECT je.id, je.job_id, je.embedding, je.text_hash, je.created_at, je.updated_at
    FROM public.job_embeddings je
    WHERE je.tenant_id = p_tenant_id
       OR je.tenant_id IS NULL;  -- Include global embeddings
$$;

-- Function: Get profile embeddings for a user within tenant context
CREATE OR REPLACE FUNCTION public.get_profile_embedding_for_user(
    p_user_id uuid,
    p_tenant_id uuid
)
RETURNS TABLE (
    id uuid,
    user_id uuid,
    embedding jsonb,
    text_hash text,
    created_at timestamptz,
    updated_at timestamptz
)
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
    SELECT pe.id, pe.user_id, pe.embedding, pe.text_hash, pe.created_at, pe.updated_at
    FROM public.profile_embeddings pe
    WHERE pe.user_id = p_user_id
      AND (pe.tenant_id = p_tenant_id OR pe.tenant_id IS NULL);
$$;

-- Function: Upsert job embedding with tenant scoping
CREATE OR REPLACE FUNCTION public.upsert_job_embedding(
    p_job_id uuid,
    p_embedding jsonb,
    p_text_hash text,
    p_tenant_id uuid DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_id uuid;
    v_tenant_id uuid;
BEGIN
    -- Auto-resolve tenant_id if not provided
    IF p_tenant_id IS NULL THEN
        SELECT p.tenant_id INTO v_tenant_id
        FROM public.jobs j
        JOIN public.profiles p ON p.user_id = j.user_id
        WHERE j.id = p_job_id
        LIMIT 1;
    ELSE
        v_tenant_id := p_tenant_id;
    END IF;
    
    INSERT INTO public.job_embeddings (job_id, embedding, text_hash, tenant_id)
    VALUES (p_job_id, p_embedding, p_text_hash, v_tenant_id)
    ON CONFLICT (job_id) 
    DO UPDATE SET 
        embedding = EXCLUDED.embedding,
        text_hash = EXCLUDED.text_hash,
        tenant_id = COALESCE(EXCLUDED.tenant_id, job_embeddings.tenant_id),
        updated_at = now()
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$;

-- Function: Upsert profile embedding with tenant scoping
CREATE OR REPLACE FUNCTION public.upsert_profile_embedding(
    p_user_id uuid,
    p_embedding jsonb,
    p_text_hash text,
    p_tenant_id uuid DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_id uuid;
    v_tenant_id uuid;
BEGIN
    -- Auto-resolve tenant_id if not provided
    IF p_tenant_id IS NULL THEN
        SELECT tenant_id INTO v_tenant_id
        FROM public.profiles
        WHERE user_id = p_user_id
        LIMIT 1;
    ELSE
        v_tenant_id := p_tenant_id;
    END IF;
    
    INSERT INTO public.profile_embeddings (user_id, embedding, text_hash, tenant_id)
    VALUES (p_user_id, p_embedding, p_text_hash, v_tenant_id)
    ON CONFLICT (user_id) 
    DO UPDATE SET 
        embedding = EXCLUDED.embedding,
        text_hash = EXCLUDED.text_hash,
        tenant_id = COALESCE(EXCLUDED.tenant_id, profile_embeddings.tenant_id),
        updated_at = now()
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$;

-- Function: Delete all embeddings for a tenant (for GDPR/tenant deletion)
CREATE OR REPLACE FUNCTION public.delete_tenant_embeddings(p_tenant_id uuid)
RETURNS int
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    deleted_count int;
BEGIN
    DELETE FROM public.job_embeddings WHERE tenant_id = p_tenant_id;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM public.profile_embeddings WHERE tenant_id = p_tenant_id;
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    RETURN deleted_count;
END;
$$;

-- ============================================================
-- Enhanced RLS Policies for Embeddings
-- ============================================================

-- Drop and recreate job embeddings policies with proper tenant scoping
DROP POLICY IF EXISTS "Users can read job embeddings in their tenant" ON public.job_embeddings;

CREATE POLICY "Users can read job embeddings in their tenant"
    ON public.job_embeddings FOR SELECT
    TO authenticated
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid()
        )
        OR tenant_id IS NULL  -- Global embeddings accessible to all
    );

-- Insert policy for job embeddings (tenant-scoped)
DROP POLICY IF EXISTS "Users can insert job embeddings in their tenant" ON public.job_embeddings;
CREATE POLICY "Users can insert job embeddings in their tenant"
    ON public.job_embeddings FOR INSERT
    TO authenticated
    WITH CHECK (
        tenant_id IN (
            SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid()
        )
        OR tenant_id IS NULL
    );

-- Update policy for job embeddings
DROP POLICY IF EXISTS "Users can update job embeddings in their tenant" ON public.job_embeddings;
CREATE POLICY "Users can update job embeddings in their tenant"
    ON public.job_embeddings FOR UPDATE
    TO authenticated
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid()
        )
    );

-- Enhanced profile embeddings policies
DROP POLICY IF EXISTS "Users can read own profile embeddings with tenant check" ON public.profile_embeddings;
CREATE POLICY "Users can read own profile embeddings with tenant check"
    ON public.profile_embeddings FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid()
        AND (
            tenant_id IN (
                SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid()
            )
            OR tenant_id IS NULL
        )
    );

DROP POLICY IF EXISTS "Users can insert own profile embeddings" ON public.profile_embeddings;
CREATE POLICY "Users can insert own profile embeddings"
    ON public.profile_embeddings FOR INSERT
    TO authenticated
    WITH CHECK (
        user_id = auth.uid()
        AND (
            tenant_id IN (
                SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid()
            )
            OR tenant_id IS NULL
        )
    );

DROP POLICY IF EXISTS "Users can update own profile embeddings" ON public.profile_embeddings;
CREATE POLICY "Users can update own profile embeddings"
    ON public.profile_embeddings FOR UPDATE
    TO authenticated
    USING (
        user_id = auth.uid()
        AND (
            tenant_id IN (
                SELECT tenant_id FROM public.profiles WHERE user_id = auth.uid()
            )
            OR tenant_id IS NULL
        )
    );

-- ============================================================
-- Composite indexes for tenant-scoped queries
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_job_embeddings_tenant_job ON public.job_embeddings (tenant_id, job_id);
CREATE INDEX IF NOT EXISTS idx_profile_embeddings_tenant_user ON public.profile_embeddings (tenant_id, user_id);

-- ============================================================
-- Grant execute permissions on functions
-- ============================================================
GRANT EXECUTE ON FUNCTION public.set_job_embedding_tenant_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.set_profile_embedding_tenant_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.backfill_embedding_tenant_ids() TO service_role;
GRANT EXECUTE ON FUNCTION public.get_job_embeddings_by_tenant(uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_profile_embedding_for_user(uuid, uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_job_embedding(uuid, jsonb, text, uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_profile_embedding(uuid, jsonb, text, uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.delete_tenant_embeddings(uuid) TO service_role;
