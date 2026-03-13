-- +migrate Up
-- Company Verification/Scoring System - Phase 1.5
-- Creates companies table for tracking verified entities,
-- caching verification results, and integrating with company_score field.

-- Companies table for verified company data
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(255),
    employee_count_range VARCHAR(50),
    linkedin_url VARCHAR(500),
    description TEXT,
    
    -- Verification status
    is_verified BOOLEAN DEFAULT FALSE,
    verification_level VARCHAR(50) DEFAULT 'none',
    verified_at TIMESTAMPTZ,
    verified_by UUID REFERENCES users(id),
    
    -- Reputation and scoring
    reputation_score FLOAT,
    company_score FLOAT,
    last_scored_at TIMESTAMPTZ,
    
    -- Domain information
    domain_registered BOOLEAN,
    domain_age_days INTEGER,
    domain_registrar VARCHAR(255),
    
    -- Company metadata
    founded_year INTEGER,
    company_type VARCHAR(100),
    company_size VARCHAR(50),
    headquarters VARCHAR(255),
    
    -- Known company status
    is_known_good BOOLEAN DEFAULT FALSE,
    is_suspicious BOOLEAN DEFAULT FALSE,
    known_scam BOOLEAN DEFAULT FALSE,
    
    -- Additional data as JSONB
    verification_data JSONB,
    raw_data JSONB,
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_company_domain UNIQUE (domain)
);

-- Index for domain lookups
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);

-- Index for company name search
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);

-- Index for reputation scoring
CREATE INDEX IF NOT EXISTS idx_companies_reputation_score ON companies(reputation_score) WHERE reputation_score IS NOT NULL;

-- Index for company_score filtering
CREATE INDEX IF NOT EXISTS idx_companies_company_score ON companies(company_score) WHERE company_score IS NOT NULL;

-- Index for verified companies
CREATE INDEX IF NOT EXISTS idx_companies_is_verified ON companies(is_verified) WHERE is_verified = TRUE;

-- Index for suspicious companies
CREATE INDEX IF NOT EXISTS idx_companies_suspicious ON companies(is_suspicious) WHERE is_suspicious = TRUE;

-- Index for known scams
CREATE INDEX IF NOT EXISTS idx_companies_known_scam ON companies(known_scam) WHERE known_scam = TRUE;

-- Add company_id foreign key to jobs table if not exists
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id);

-- Index for job-company relationship
CREATE INDEX IF NOT EXISTS idx_jobs_company_id ON jobs(company_id);

-- +migrate Down
-- Rollback company verification tables

DROP INDEX IF EXISTS idx_jobs_company_id;
ALTER TABLE jobs DROP COLUMN IF EXISTS company_id;

DROP INDEX IF EXISTS idx_companies_known_scam;
DROP INDEX IF EXISTS idx_companies_suspicious;
DROP INDEX IF EXISTS idx_companies_is_verified;
DROP INDEX IF EXISTS idx_companies_company_score;
DROP INDEX IF EXISTS idx_companies_reputation_score;
DROP INDEX IF EXISTS idx_companies_name;
DROP INDEX IF EXISTS idx_companies_domain;

DROP TABLE IF EXISTS companies;
