-- Combined schema for local development (auto-generated for docker-compose)
-- All tables required by the backend API, worker, and job sync pipeline

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- Core: Tenants & Users
-- ============================================================

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255),
    domain VARCHAR(255) UNIQUE,
    plan VARCHAR(50) DEFAULT 'FREE',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_members (
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    role VARCHAR(50) DEFAULT 'MEMBER',
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, user_id)
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    linkedin_url TEXT,
    resume_url TEXT,
    profile_completeness INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    profile_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    resume_url TEXT,
    tenant_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    location TEXT,
    role_type TEXT,
    salary_min INTEGER,
    remote_only BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- Jobs: Listings synced from external sources (JobSpy)
-- ============================================================

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id TEXT UNIQUE,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    application_url TEXT,
    source TEXT,
    is_remote BOOLEAN DEFAULT FALSE,
    job_type TEXT,
    date_posted TIMESTAMPTZ,
    job_level TEXT,
    company_industry TEXT,
    company_logo_url TEXT,
    raw_data JSONB DEFAULT '{}',
    is_scam BOOLEAN DEFAULT FALSE,
    quality_score REAL,
    dedup_key TEXT,
    skills TEXT[],
    benefits TEXT,
    last_synced_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- Job Sync: Configuration and run tracking for JobSpy pipeline
-- ============================================================

CREATE TABLE IF NOT EXISTS job_sync_config (
    source TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ,
    sync_interval_hours INTEGER DEFAULT 4,
    max_results INTEGER DEFAULT 50,
    search_queries JSONB DEFAULT '[]',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_sync_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    jobs_fetched INTEGER DEFAULT 0,
    jobs_new INTEGER DEFAULT 0,
    jobs_updated INTEGER DEFAULT 0,
    jobs_skipped INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    duration_ms INTEGER,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS popular_searches (
    search_term TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    search_count INTEGER DEFAULT 1,
    last_searched_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (search_term, location)
);

-- ============================================================
-- Applications: User job applications tracked by the agent
-- ============================================================

CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    tenant_id UUID REFERENCES tenants(id),
    blueprint_key VARCHAR(50) DEFAULT 'job-app',
    status VARCHAR(50) DEFAULT 'QUEUED',
    priority_score INTEGER DEFAULT 0,
    stage VARCHAR(50) DEFAULT 'new',
    priority INTEGER DEFAULT 0,
    notes_count INTEGER DEFAULT 0,
    reminders_count INTEGER DEFAULT 0,
    notes TEXT,
    applied_date DATE,
    snoozed_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, job_id)
);

-- Agent event log (record_event, repositories)
DO $$ BEGIN
    CREATE TYPE application_event_type AS ENUM (
        'CREATED', 'CLAIMED', 'STARTED_PROCESSING',
        'FIELDS_EXTRACTED', 'FORM_FILLED', 'SUBMITTED',
        'APPLIED', 'FAILED', 'HOLD', 'RESUMED', 'RETRY_SCHEDULED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS application_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    event_type application_event_type NOT NULL,
    payload JSONB,
    tenant_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS application_inputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    selector VARCHAR(500),
    question TEXT NOT NULL,
    field_type VARCHAR(50) DEFAULT 'text',
    answer TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    data JSONB,
    tenant_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS application_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    tenant_id UUID,
    content TEXT NOT NULL,
    note_type VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS follow_up_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    tenant_id UUID,
    remind_at TIMESTAMPTZ NOT NULL,
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- ============================================================
-- User Data: Skills, Work Style, Answer Memory
-- ============================================================

CREATE TABLE IF NOT EXISTS answer_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    field_label TEXT NOT NULL,
    field_type VARCHAR(50) DEFAULT 'text',
    answer_value TEXT NOT NULL,
    use_count INTEGER DEFAULT 1,
    last_used_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, field_label)
);

CREATE TABLE IF NOT EXISTS work_style_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    autonomy_preference TEXT NOT NULL DEFAULT 'medium',
    learning_style TEXT NOT NULL DEFAULT 'building',
    company_stage_preference TEXT NOT NULL DEFAULT 'flexible',
    communication_style TEXT NOT NULL DEFAULT 'mixed',
    pace_preference TEXT NOT NULL DEFAULT 'steady',
    ownership_preference TEXT NOT NULL DEFAULT 'team',
    career_trajectory TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5,
    years_actual REAL,
    context TEXT DEFAULT '',
    last_used TEXT,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    related_to TEXT[] DEFAULT '{}',
    source TEXT NOT NULL DEFAULT 'resume',
    project_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, skill)
);

-- ============================================================
-- Billing
-- ============================================================

CREATE TABLE IF NOT EXISTS billing_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    provider TEXT DEFAULT 'stripe',
    provider_customer_id TEXT,
    status TEXT DEFAULT 'active',
    plan TEXT DEFAULT 'FREE',
    current_subscription_id TEXT,
    current_subscription_status TEXT DEFAULT 'none',
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- Saved Jobs & Cover Letters
-- ============================================================

CREATE TABLE IF NOT EXISTS saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, job_id)
);

CREATE TABLE IF NOT EXISTS cover_letters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id),
    content TEXT NOT NULL,
    tone TEXT DEFAULT 'professional',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_external_id ON jobs(external_id);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_last_synced ON jobs(last_synced_at);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_tenant ON applications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_applications_tenant_id ON applications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id_status ON applications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_applications_tenant_user ON applications(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_application_notes_app_id ON application_notes(application_id);
CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_user ON follow_up_reminders(user_id, status);
CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_remind_at ON follow_up_reminders(remind_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_application_inputs_app ON application_inputs(application_id);
CREATE INDEX IF NOT EXISTS idx_events_application ON events(application_id);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_answer_memory_user ON answer_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_work_style_user ON work_style_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_skills_user ON user_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_runs_source ON job_sync_runs(source);
CREATE INDEX IF NOT EXISTS idx_sync_runs_started ON job_sync_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_billing_customers_tenant ON billing_customers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_billing_customers_user ON billing_customers(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user ON saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_cover_letters_user ON cover_letters(user_id);

-- ============================================================
-- Performance Indexes (C6: Database Indexes - Audit Fix)
-- ============================================================

-- Critical: Composite index for worker claim query (claim_next_prioritized function)
-- This index optimizes the query: WHERE status = 'QUEUED' ORDER BY priority_score DESC, created_at ASC
CREATE INDEX IF NOT EXISTS idx_applications_claim 
    ON applications(status, priority_score DESC, created_at ASC) 
    WHERE status = 'QUEUED';

-- Index for resumable applications (REQUIRES_INPUT status)
CREATE INDEX IF NOT EXISTS idx_applications_resumable 
    ON applications(status, updated_at ASC) 
    WHERE status = 'REQUIRES_INPUT';

-- Foreign key indexes for commonly queried relationships
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id) WHERE job_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_application_events_application_id ON application_events(application_id);
CREATE INDEX IF NOT EXISTS idx_application_events_tenant_id ON application_events(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_application_events_created_at ON application_events(created_at);

-- Index for processing stale locked applications
CREATE INDEX IF NOT EXISTS idx_applications_locked_at 
    ON applications(status, locked_at) 
    WHERE status = 'PROCESSING' AND locked_at IS NOT NULL;

-- ============================================================
-- Seed: Default job sync sources
-- ============================================================

INSERT INTO job_sync_config (source, enabled, sync_interval_hours, max_results)
VALUES
    ('adzuna', TRUE, 4, 50),
    ('indeed', TRUE, 4, 50),
    ('linkedin', TRUE, 4, 50),
    ('glassdoor', TRUE, 6, 30),
    ('zip_recruiter', TRUE, 6, 30)
ON CONFLICT (source) DO NOTHING;
