-- Migration 024: Vector Embeddings for Semantic Job Matching
--
-- Implements the "Precision Matcher" archetype from competitive analysis.
-- Stores embeddings for jobs and profiles to enable semantic similarity search.
-- Uses JSON storage for embeddings (Render Postgres doesn't have pgvector).

-- Job embeddings cache
CREATE TABLE IF NOT EXISTS public.job_embeddings (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id      uuid NOT NULL REFERENCES public.jobs (id) ON DELETE CASCADE,
    embedding   jsonb NOT NULL,
    text_hash   text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    
    UNIQUE (job_id)
);

CREATE INDEX IF NOT EXISTS idx_job_embeddings_job_id ON public.job_embeddings (job_id);
CREATE INDEX IF NOT EXISTS idx_job_embeddings_hash ON public.job_embeddings (text_hash);

-- Profile embeddings cache
CREATE TABLE IF NOT EXISTS public.profile_embeddings (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
    embedding   jsonb NOT NULL,
    text_hash   text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    
    UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_profile_embeddings_user_id ON public.profile_embeddings (user_id);
CREATE INDEX IF NOT EXISTS idx_profile_embeddings_hash ON public.profile_embeddings (text_hash);

-- User dealbreaker preferences
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
    min_salary            numeric(12, 2),
    max_salary            numeric(12, 2),
    preferred_locations   jsonb DEFAULT '[]'::jsonb,
    remote_only           boolean DEFAULT false,
    onsite_only           boolean DEFAULT false,
    visa_sponsorship      boolean DEFAULT false,
    excluded_companies    jsonb DEFAULT '[]'::jsonb,
    excluded_keywords     jsonb DEFAULT '[]'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    
    UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON public.user_preferences (user_id);

-- RLS policies
ALTER TABLE public.job_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

-- Job embeddings are readable by all authenticated users (for matching)
CREATE POLICY "Authenticated users can read job embeddings"
    ON public.job_embeddings FOR SELECT
    TO authenticated
    USING (true);

-- Profile embeddings are only readable by the owner
DROP POLICY IF EXISTS "Users can read own profile embeddings" ON public.profile_embeddings;
CREATE POLICY "Users can read own profile embeddings"
    ON public.profile_embeddings FOR SELECT
    USING (user_id = auth.uid());

-- User preferences are only readable/writable by the owner
DROP POLICY IF EXISTS "Users can manage own preferences" ON public.user_preferences;
CREATE POLICY "Users can manage own preferences"
    ON public.user_preferences FOR ALL
    USING (user_id = auth.uid());

-- Trigger for updated_at
DROP TRIGGER IF EXISTS trg_job_embeddings_updated_at ON public.job_embeddings;
CREATE TRIGGER trg_job_embeddings_updated_at
    BEFORE UPDATE ON public.job_embeddings
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_profile_embeddings_updated_at ON public.profile_embeddings;
CREATE TRIGGER trg_profile_embeddings_updated_at
    BEFORE UPDATE ON public.profile_embeddings
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_user_preferences_updated_at ON public.user_preferences;
CREATE TRIGGER trg_user_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Realtime publication
ALTER PUBLICATION supabase_realtime ADD TABLE public.user_preferences;
