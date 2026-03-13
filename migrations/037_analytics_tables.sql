-- +migrate Up
-- Phase 5: Analytics Tables for Database Schema Enhancements
-- Creates tables for tracking user behavior and application outcomes

-- =============================================================================
-- USER EVENTS TABLE
-- Track user events for analytics and behavior monitoring
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for user events by user (common query pattern)
CREATE INDEX IF NOT EXISTS idx_user_events_user_id ON user_events(user_id);

-- Index for user events by type (filtering by event type)
CREATE INDEX IF NOT EXISTS idx_user_events_event_type ON user_events(event_type);

-- Index for user events by created_at (time-based queries)
CREATE INDEX IF NOT EXISTS idx_user_events_created_at ON user_events(created_at);

-- Composite index for user + event type queries
CREATE INDEX IF NOT EXISTS idx_user_events_user_type ON user_events(user_id, event_type);

-- Composite index for user + created_at (user activity timeline)
CREATE INDEX IF NOT EXISTS idx_user_events_user_created ON user_events(user_id, created_at DESC);

-- =============================================================================
-- JOB VIEWS TABLE
-- Track job view duration for engagement analytics
-- =============================================================================
CREATE TABLE IF NOT EXISTS job_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for job views by user
CREATE INDEX IF NOT EXISTS idx_job_views_user_id ON job_views(user_id);

-- Index for job views by job
CREATE INDEX IF NOT EXISTS idx_job_views_job_id ON job_views(job_id);

-- Index for job views by created_at (time-based queries)
CREATE INDEX IF NOT EXISTS idx_job_views_created_at ON job_views(created_at);

-- Composite index for user + job (unique view tracking)
CREATE INDEX IF NOT EXISTS idx_user_job_views ON job_views(user_id, job_id);

-- Composite index for job engagement analysis
CREATE INDEX IF NOT EXISTS idx_job_views_engagement ON job_views(job_id, created_at DESC);

-- =============================================================================
-- APPLICATION OUTCOMES TABLE
-- Track application results and response times
-- =============================================================================
CREATE TABLE IF NOT EXISTS application_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    response_time_days INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for application outcomes by application
CREATE INDEX IF NOT EXISTS idx_application_outcomes_application_id ON application_outcomes(application_id);

-- Index for application outcomes by status
CREATE INDEX IF NOT EXISTS idx_application_outcomes_status ON application_outcomes(status);

-- Index for application outcomes by created_at
CREATE INDEX IF NOT EXISTS idx_application_outcomes_created_at ON application_outcomes(created_at);

-- Composite index for status + created_at (outcome trends)
CREATE INDEX IF NOT EXISTS idx_application_outcomes_status_date ON application_outcomes(status, created_at DESC);

-- Index for response time analysis
CREATE INDEX IF NOT EXISTS idx_application_outcomes_response_time ON application_outcomes(response_time_days) WHERE response_time_days IS NOT NULL;

-- =============================================================================
-- SWIPE EVENTS TABLE
-- Track user swipe patterns for matching analytics
-- =============================================================================
CREATE TABLE IF NOT EXISTS swipe_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL CHECK (action IN ('save', 'skip', 'apply')),
    match_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for swipe events by user
CREATE INDEX IF NOT EXISTS idx_swipe_events_user_id ON swipe_events(user_id);

-- Index for swipe events by job
CREATE INDEX IF NOT EXISTS idx_swipe_events_job_id ON swipe_events(job_id);

-- Index for swipe events by action
CREATE INDEX IF NOT EXISTS idx_swipe_events_action ON swipe_events(action);

-- Index for swipe events by created_at
CREATE INDEX IF NOT EXISTS idx_swipe_events_created_at ON swipe_events(created_at);

-- Composite index for user + action (action distribution per user)
CREATE INDEX IF NOT EXISTS idx_swipe_events_user_action ON swipe_events(user_id, action);

-- Composite index for job + action (job attractiveness)
CREATE INDEX IF NOT EXISTS idx_swipe_events_job_action ON swipe_events(job_id, action);

-- Composite index for user + created_at (user activity timeline)
CREATE INDEX IF NOT EXISTS idx_swipe_events_user_created ON swipe_events(user_id, created_at DESC);

-- Index for match score analysis
CREATE INDEX IF NOT EXISTS idx_swipe_events_match_score ON swipe_events(match_score) WHERE match_score IS NOT NULL;

-- +migrate Down
-- Rollback analytics tables

-- Drop swipe_events indexes
DROP INDEX IF EXISTS idx_swipe_events_match_score;
DROP INDEX IF EXISTS idx_swipe_events_user_created;
DROP INDEX IF EXISTS idx_swipe_events_job_action;
DROP INDEX IF EXISTS idx_swipe_events_user_action;
DROP INDEX IF EXISTS idx_swipe_events_created_at;
DROP INDEX IF EXISTS idx_swipe_events_action;
DROP INDEX IF EXISTS idx_swipe_events_job_id;
DROP INDEX IF EXISTS idx_swipe_events_user_id;
DROP TABLE IF EXISTS swipe_events;

-- Drop application_outcomes indexes
DROP INDEX IF EXISTS idx_application_outcomes_response_time;
DROP INDEX IF EXISTS idx_application_outcomes_status_date;
DROP INDEX IF EXISTS idx_application_outcomes_created_at;
DROP INDEX IF EXISTS idx_application_outcomes_status;
DROP INDEX IF EXISTS idx_application_outcomes_application_id;
DROP TABLE IF EXISTS application_outcomes;

-- Drop job_views indexes
DROP INDEX IF EXISTS idx_job_views_engagement;
DROP INDEX IF EXISTS idx_user_job_views;
DROP INDEX IF EXISTS idx_job_views_created_at;
DROP INDEX IF EXISTS idx_job_views_job_id;
DROP INDEX IF EXISTS idx_job_views_user_id;
DROP TABLE IF EXISTS job_views;

-- Drop user_events indexes
DROP INDEX IF EXISTS idx_user_events_user_created;
DROP INDEX IF EXISTS idx_user_events_user_type;
DROP INDEX IF EXISTS idx_user_events_created_at;
DROP INDEX IF EXISTS idx_user_events_event_type;
DROP INDEX IF EXISTS idx_user_events_user_id;
DROP TABLE IF EXISTS user_events;
