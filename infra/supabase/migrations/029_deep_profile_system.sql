-- Deep Profile System Migration
-- Creates tables for rich skills, work style profiles, job signals, and deep profiles

-- ============================================================
-- Table: user_skills
-- Rich skills with confidence, context, and verification status
-- ============================================================
CREATE TABLE IF NOT EXISTS user_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill VARCHAR(100) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    years_actual DECIMAL(4,1),
    context TEXT,
    last_used DATE,
    verified BOOLEAN DEFAULT FALSE,
    related_to TEXT[],
    source VARCHAR(50) DEFAULT 'resume' CHECK (source IN ('resume', 'github', 'linkedin', 'manual')),
    project_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_user_skills_confidence ON user_skills(user_id, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_user_skills_skill ON user_skills(skill);

-- ============================================================
-- Table: work_style_profiles
-- Behavioral profile data from calibration questions
-- ============================================================
CREATE TABLE IF NOT EXISTS work_style_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    autonomy_preference VARCHAR(20) DEFAULT 'medium' CHECK (autonomy_preference IN ('high', 'medium', 'low')),
    learning_style VARCHAR(20) DEFAULT 'building' CHECK (learning_style IN ('docs', 'building', 'pairing', 'courses')),
    company_stage_preference VARCHAR(20) DEFAULT 'flexible' CHECK (company_stage_preference IN ('early_startup', 'growth', 'enterprise', 'flexible')),
    communication_style VARCHAR(20) DEFAULT 'mixed' CHECK (communication_style IN ('async', 'sync', 'mixed', 'flexible')),
    pace_preference VARCHAR(20) DEFAULT 'steady' CHECK (pace_preference IN ('fast', 'steady', 'methodical', 'flexible')),
    ownership_preference VARCHAR(20) DEFAULT 'team' CHECK (ownership_preference IN ('solo', 'team', 'lead', 'flexible')),
    career_trajectory VARCHAR(20) DEFAULT 'open' CHECK (career_trajectory IN ('ic', 'tech_lead', 'manager', 'founder', 'open')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Table: job_signals
-- Extracted work style and growth signals from job postings
-- ============================================================
CREATE TABLE IF NOT EXISTS job_signals (
    job_id UUID PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
    company_stage VARCHAR(20) CHECK (company_stage IN ('early_startup', 'growth', 'enterprise')),
    pace VARCHAR(20) CHECK (pace IN ('fast', 'steady', 'methodical')),
    autonomy_level VARCHAR(20) CHECK (autonomy_level IN ('high', 'medium', 'low')),
    growth_potential VARCHAR(20) CHECK (growth_potential IN ('ic_path', 'lead_path', 'manager_path', 'limited')),
    team_size VARCHAR(20) CHECK (team_size IN ('small', 'medium', 'large')),
    remote_culture VARCHAR(20) CHECK (remote_culture IN ('async_first', 'hybrid', 'onsite_culture')),
    signals_detected JSONB,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_signals_company_stage ON job_signals(company_stage);
CREATE INDEX IF NOT EXISTS idx_job_signals_growth ON job_signals(growth_potential);
CREATE INDEX IF NOT EXISTS idx_job_signals_pace ON job_signals(pace);

-- ============================================================
-- Table: deep_profiles
-- Cached aggregated profile for fast matching
-- ============================================================
CREATE TABLE IF NOT EXISTS deep_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    profile_json JSONB NOT NULL,
    completeness_score DECIMAL(5,2) CHECK (completeness_score >= 0 AND completeness_score <= 100),
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_deep_profiles_completeness ON deep_profiles(completeness_score DESC);

-- ============================================================
-- Table: job_embeddings (for semantic matching)
-- ============================================================
CREATE TABLE IF NOT EXISTS job_embeddings (
    job_id UUID PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
    embedding JSONB,
    text_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Table: profile_embeddings (for semantic matching)
-- ============================================================
CREATE TABLE IF NOT EXISTS profile_embeddings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    embedding JSONB,
    text_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Add columns to users table
-- ============================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completeness DECIMAL(5,2) DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS has_completed_onboarding BOOLEAN DEFAULT FALSE;

-- ============================================================
-- Triggers for updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_skills_updated_at ON user_skills;
CREATE TRIGGER trg_user_skills_updated_at
    BEFORE UPDATE ON user_skills
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_work_style_profiles_updated_at ON work_style_profiles;
CREATE TRIGGER trg_work_style_profiles_updated_at
    BEFORE UPDATE ON work_style_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
