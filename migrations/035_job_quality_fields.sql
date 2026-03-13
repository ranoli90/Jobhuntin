-- +migrate Up
-- Job Quality Control System - Phase 1
-- Adds quality control fields to the jobs table for spam detection,
-- salary validation, duplicate detection, and company verification.

-- Spam detection fields
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_spam BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS spam_score FLOAT;

-- Salary validation fields
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_validated BOOLEAN;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_validation_notes TEXT;

-- Duplicate detection (self-reference to canonical job)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS canonical_job_id UUID REFERENCES jobs(id);

-- Company verification/reputation score
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_score FLOAT;

-- Additional quality indicators as JSONB
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS quality_flags JSONB;

-- Index for spam filtering (common query pattern)
CREATE INDEX IF NOT EXISTS idx_jobs_is_spam ON jobs(is_spam);

-- Index for canonical job lookups (duplicate detection)
CREATE INDEX IF NOT EXISTS idx_jobs_canonical_job_id ON jobs(canonical_job_id);

-- Index for company score filtering
CREATE INDEX IF NOT EXISTS idx_jobs_company_score ON jobs(company_score) WHERE company_score IS NOT NULL;

-- +migrate Down
-- Rollback job quality control fields

DROP INDEX IF EXISTS idx_jobs_company_score;
DROP INDEX IF EXISTS idx_jobs_canonical_job_id;
DROP INDEX IF EXISTS idx_jobs_is_spam;

ALTER TABLE jobs DROP COLUMN IF EXISTS quality_flags;
ALTER TABLE jobs DROP COLUMN IF EXISTS company_score;
ALTER TABLE jobs DROP COLUMN IF EXISTS canonical_job_id;
ALTER TABLE jobs DROP COLUMN IF EXISTS salary_validation_notes;
ALTER TABLE jobs DROP COLUMN IF EXISTS salary_validated;
ALTER TABLE jobs DROP COLUMN IF EXISTS spam_score;
ALTER TABLE jobs DROP COLUMN IF EXISTS is_spam;
