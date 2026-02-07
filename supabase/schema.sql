-- Part 1: Database Schema (Supabase/Postgres)

-- ============================================================
-- Enum: application status state machine
-- ============================================================
CREATE TYPE public.application_status AS ENUM (
    'QUEUED',
    'PROCESSING',
    'REQUIRES_INPUT',
    'APPLIED',
    'FAILED'
);

-- ============================================================
-- Table: public.users
-- 1-to-1 mirror of auth.users; all app-level data hangs here.
-- ============================================================
CREATE TABLE public.users (
    id          uuid PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    full_name   text,
    email       text,
    avatar_url  text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_email ON public.users (email);

-- ============================================================
-- Table: public.profiles
-- The "Digital Twin": structured JSON extracted from the resume.
-- ============================================================
CREATE TABLE public.profiles (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       uuid NOT NULL UNIQUE REFERENCES public.users (id) ON DELETE CASCADE,
    profile_data  jsonb NOT NULL DEFAULT '{}'::jsonb,
    resume_url    text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_user_id ON public.profiles (user_id);

-- ============================================================
-- Table: public.jobs
-- Cached job listings from the Adzuna feed (or mock).
-- ============================================================
CREATE TABLE public.jobs (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id      text NOT NULL UNIQUE,
    title            text NOT NULL,
    company          text NOT NULL,
    description      text,
    location         text,
    salary_min       numeric(12, 2),
    salary_max       numeric(12, 2),
    category         text,
    application_url  text NOT NULL,
    source           text NOT NULL DEFAULT 'adzuna',
    raw_data         jsonb,
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_jobs_external_id ON public.jobs (external_id);
CREATE INDEX idx_jobs_category    ON public.jobs (category);

-- ============================================================
-- Table: public.applications
-- The task queue linking a user to a job application attempt.
-- ============================================================
CREATE TABLE public.applications (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES public.users (id) ON DELETE CASCADE,
    job_id          uuid NOT NULL REFERENCES public.jobs (id) ON DELETE CASCADE,
    status          public.application_status NOT NULL DEFAULT 'QUEUED',
    error_message   text,
    locked_at       timestamptz,
    submitted_at    timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),

    UNIQUE (user_id, job_id)
);

CREATE INDEX idx_applications_status   ON public.applications (status);
CREATE INDEX idx_applications_user_id  ON public.applications (user_id);
CREATE INDEX idx_applications_job_id   ON public.applications (job_id);

-- ============================================================
-- Table: public.application_inputs
-- Each row is a question the agent could not answer ("Hold").
-- ============================================================
CREATE TABLE public.application_inputs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  uuid NOT NULL REFERENCES public.applications (id) ON DELETE CASCADE,
    selector        text NOT NULL,
    question        text NOT NULL,
    field_type      text NOT NULL DEFAULT 'text',
    answer          text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    answered_at     timestamptz
);

CREATE INDEX idx_app_inputs_application_id ON public.application_inputs (application_id);
CREATE INDEX idx_app_inputs_unanswered     ON public.application_inputs (application_id)
    WHERE answer IS NULL;

-- ============================================================
-- Helper: auto-update updated_at on row modification
-- ============================================================
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_applications_updated_at
    BEFORE UPDATE ON public.applications
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ============================================================
-- Supabase Realtime: enable publication for live subscriptions
-- ============================================================
ALTER PUBLICATION supabase_realtime ADD TABLE public.applications;
ALTER PUBLICATION supabase_realtime ADD TABLE public.application_inputs;

-- ============================================================
-- Row-Level Security (RLS) stubs
-- ============================================================
ALTER TABLE public.users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.applications       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.application_inputs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own row"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can read own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can read own applications"
    ON public.applications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own applications"
    ON public.applications FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can read own application_inputs"
    ON public.application_inputs FOR SELECT
    USING (
        application_id IN (
            SELECT id FROM public.applications WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own application_inputs answers"
    ON public.application_inputs FOR UPDATE
    USING (
        application_id IN (
            SELECT id FROM public.applications WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        application_id IN (
            SELECT id FROM public.applications WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Jobs are readable by all authenticated users"
    ON public.jobs FOR SELECT
    USING (true);

ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
