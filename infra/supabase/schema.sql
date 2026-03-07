-- Combined schema for local development (auto-generated for docker-compose)
-- Source: migrations/001_initial_schema.sql (Up section) + migrations/002_onboarding_tables.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255),
    domain VARCHAR(255) UNIQUE,
    plan VARCHAR(50) DEFAULT 'FREE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tenant members
CREATE TABLE IF NOT EXISTS tenant_members (
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    role VARCHAR(50) DEFAULT 'MEMBER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, user_id)
);

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    linkedin_url TEXT,
    resume_url TEXT,
    profile_completeness INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles (stores profile_data JSONB, resume URL, etc.)
CREATE TABLE IF NOT EXISTS public.profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    profile_data jsonb NOT NULL DEFAULT '{}'::jsonb,
    resume_url text,
    tenant_id text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles(user_id);

-- User preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    location TEXT,
    role_type TEXT,
    salary_min INTEGER,
    remote_only BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    url TEXT,
    posted_date DATE,
    remote_policy VARCHAR(50) DEFAULT 'onsite',
    experience_level VARCHAR(50) DEFAULT 'mid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job applications
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    status VARCHAR(50) DEFAULT 'SAVED',
    notes TEXT,
    applied_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application inputs (for dynamic forms)
CREATE TABLE IF NOT EXISTS application_inputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    selector VARCHAR(500),
    question TEXT NOT NULL,
    field_type VARCHAR(50) DEFAULT 'text',
    answer TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    meta JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events table for audit trail
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    data JSONB,
    tenant_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Answer memory for smart pre-fill
CREATE TABLE IF NOT EXISTS answer_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    field_label TEXT NOT NULL,
    field_type VARCHAR(50) DEFAULT 'text',
    answer_value TEXT NOT NULL,
    use_count INTEGER DEFAULT 1,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, field_label)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_application_inputs_application_id ON application_inputs(application_id);
CREATE INDEX IF NOT EXISTS idx_events_application_id ON events(application_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_answer_memory_user_id ON answer_memory(user_id);

-- Work style profiles (from migration 002)
CREATE TABLE IF NOT EXISTS public.work_style_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    autonomy_preference   TEXT NOT NULL DEFAULT 'medium',
    learning_style        TEXT NOT NULL DEFAULT 'building',
    company_stage_preference TEXT NOT NULL DEFAULT 'flexible',
    communication_style   TEXT NOT NULL DEFAULT 'mixed',
    pace_preference       TEXT NOT NULL DEFAULT 'steady',
    ownership_preference  TEXT NOT NULL DEFAULT 'team',
    career_trajectory     TEXT NOT NULL DEFAULT 'open',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_work_style_user UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_work_style_user ON public.work_style_profiles(user_id);

-- User skills (from migration 002)
CREATE TABLE IF NOT EXISTS public.user_skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    skill           TEXT NOT NULL,
    confidence      REAL NOT NULL DEFAULT 0.5,
    years_actual    REAL,
    context         TEXT DEFAULT '',
    last_used       TEXT,
    verified        BOOLEAN NOT NULL DEFAULT false,
    related_to      TEXT[] DEFAULT '{}',
    source          TEXT NOT NULL DEFAULT 'resume',
    project_count   INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_skill UNIQUE (user_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_user_skills_user ON public.user_skills(user_id);
