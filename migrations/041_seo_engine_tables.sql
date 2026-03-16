-- +migrate Up
-- SEO Engine Tables - Migration 041

-- 1. seo_engine_progress - Tracks service progress and quotas
CREATE TABLE IF NOT EXISTS seo_engine_progress (
    id SERIAL PRIMARY KEY,
    service_id TEXT UNIQUE NOT NULL,
    last_index INTEGER DEFAULT 0,
    last_submission_at TIMESTAMPTZ,
    daily_quota_used INTEGER DEFAULT 0,
    daily_quota_reset TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. seo_generated_content - Stores generated SEO content
CREATE TABLE IF NOT EXISTS seo_generated_content (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    intent TEXT CHECK (intent IN ('informational', 'commercial', 'transactional', 'navigational')),
    competitor TEXT,
    content_hash TEXT UNIQUE,
    quality_score NUMERIC(3,2),
    google_indexed BOOLEAN DEFAULT FALSE,
    indexed_at TIMESTAMPTZ,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr NUMERIC(5,4),
    position NUMERIC(5,2),
    last_updated TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. seo_submission_log - Audit trail for Google submissions
CREATE TABLE IF NOT EXISTS seo_submission_log (
    id SERIAL PRIMARY KEY,
    service_id TEXT NOT NULL,
    batch_url_file TEXT,
    urls_submitted INTEGER NOT NULL,
    urls_successful INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    error_code TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. seo_metrics - Performance metrics tracking
CREATE TABLE IF NOT EXISTS seo_metrics (
    id SERIAL PRIMARY KEY,
    total_generated INTEGER,
    total_submitted INTEGER,
    success_rate NUMERIC(5,4),
    average_generation_time_ms INTEGER,
    average_submission_time_ms INTEGER,
    api_calls_today INTEGER,
    quota_used_today INTEGER,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. seo_logs - Database logging
CREATE TABLE IF NOT EXISTS seo_logs (
    id SERIAL PRIMARY KEY,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. seo_competitor_intelligence - Competitor analysis data
CREATE TABLE IF NOT EXISTS seo_competitor_intelligence (
    id SERIAL PRIMARY KEY,
    competitor_name TEXT UNIQUE NOT NULL,
    search_volume INTEGER,
    difficulty_score INTEGER,
    intent TEXT,
    keywords JSONB,
    content_gaps JSONB,
    weaknesses JSONB,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for seo_engine_progress
CREATE INDEX IF NOT EXISTS idx_seo_engine_progress_service_id ON seo_engine_progress(service_id);
CREATE INDEX IF NOT EXISTS idx_seo_engine_progress_daily_quota_reset ON seo_engine_progress(daily_quota_reset);

-- Indexes for seo_generated_content
CREATE INDEX IF NOT EXISTS idx_seo_generated_content_topic ON seo_generated_content(topic);
CREATE INDEX IF NOT EXISTS idx_seo_generated_content_intent ON seo_generated_content(intent);
CREATE INDEX IF NOT EXISTS idx_seo_generated_content_competitor ON seo_generated_content(competitor);
CREATE INDEX IF NOT EXISTS idx_seo_generated_content_google_indexed ON seo_generated_content(google_indexed);
CREATE INDEX IF NOT EXISTS idx_seo_generated_content_created_at ON seo_generated_content(created_at);
CREATE INDEX IF NOT EXISTS idx_seo_generated_content_deleted_at ON seo_generated_content(deleted_at) WHERE deleted_at IS NULL;

-- Indexes for seo_submission_log
CREATE INDEX IF NOT EXISTS idx_seo_submission_log_service_id ON seo_submission_log(service_id);
CREATE INDEX IF NOT EXISTS idx_seo_submission_log_created_at ON seo_submission_log(created_at);
CREATE INDEX IF NOT EXISTS idx_seo_submission_log_success ON seo_submission_log(success);

-- Indexes for seo_metrics
CREATE INDEX IF NOT EXISTS idx_seo_metrics_created_at ON seo_metrics(created_at);

-- Indexes for seo_logs
CREATE INDEX IF NOT EXISTS idx_seo_logs_level ON seo_logs(level);
CREATE INDEX IF NOT EXISTS idx_seo_logs_created_at ON seo_logs(created_at);

-- Indexes for seo_competitor_intelligence
CREATE INDEX IF NOT EXISTS idx_seo_competitor_intelligence_competitor_name ON seo_competitor_intelligence(competitor_name);
CREATE INDEX IF NOT EXISTS idx_seo_competitor_intelligence_last_updated ON seo_competitor_intelligence(last_updated);

-- +migrate Down
-- Drop indexes
DROP INDEX IF EXISTS idx_seo_engine_progress_service_id;
DROP INDEX IF EXISTS idx_seo_engine_progress_daily_quota_reset;
DROP INDEX IF EXISTS idx_seo_generated_content_topic;
DROP INDEX IF EXISTS idx_seo_generated_content_intent;
DROP INDEX IF EXISTS idx_seo_generated_content_competitor;
DROP INDEX IF EXISTS idx_seo_generated_content_google_indexed;
DROP INDEX IF EXISTS idx_seo_generated_content_created_at;
DROP INDEX IF EXISTS idx_seo_generated_content_deleted_at;
DROP INDEX IF EXISTS idx_seo_submission_log_service_id;
DROP INDEX IF EXISTS idx_seo_submission_log_created_at;
DROP INDEX IF EXISTS idx_seo_submission_log_success;
DROP INDEX IF EXISTS idx_seo_metrics_created_at;
DROP INDEX IF EXISTS idx_seo_logs_level;
DROP INDEX IF EXISTS idx_seo_logs_created_at;
DROP INDEX IF EXISTS idx_seo_competitor_intelligence_competitor_name;
DROP INDEX IF EXISTS idx_seo_competitor_intelligence_last_updated;

-- Drop tables
DROP TABLE IF EXISTS seo_competitor_intelligence;
DROP TABLE IF EXISTS seo_logs;
DROP TABLE IF EXISTS seo_metrics;
DROP TABLE IF EXISTS seo_submission_log;
DROP TABLE IF EXISTS seo_generated_content;
DROP TABLE IF EXISTS seo_engine_progress;
