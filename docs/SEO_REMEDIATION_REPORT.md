# SEO Engine Remediation Report

**Document Version:** 1.0  
**Date:** March 16, 2026  
**Status:** In Progress  
**Author:** Technical Architecture Team

---

## Executive Summary

This report documents the current state of the SEO Engine implementation and outlines a comprehensive remediation plan to achieve production-ready status. The SEO Engine is a sophisticated content generation and submission system designed to improve search visibility for the JobHuntin platform.

**Current Assessment:**
- ✅ Core infrastructure partially built (config, validation, state management)
- ✅ Multiple SEO engines implemented (smart, modern, aggressive variants)
- ✅ Content generation scripts operational
- ✅ Google submission scripts available
- ❌ No database backend for tracking
- ❌ No Python backend integration
- ❌ Limited metrics and logging
- ❌ Missing deduplication checks

**Key Recommendations:**
1. Implement database schema migrations for SEO tracking (Priority: Critical)
2. Create Python backend SEO modules (Priority: High)
3. Add comprehensive database logging (Priority: High)
4. Implement metrics collection (Priority: Medium)
5. Improve rate limiting and retry logic (Priority: Medium)
6. Add content deduplication checks (Priority: Medium)

---

## 1. Current Implementation Status

The following components have been built and are operational in the `apps/web/scripts/seo/` directory:

### 1.1 Configuration System ([`config.ts`](apps/web/scripts/seo/config.ts))

**Status:** ✅ Complete

The configuration system provides:
- Environment variable validation with strict type checking
- Google Service Account key validation (JSON or file path)
- Numeric configuration validation with min/max bounds
- Singleton pattern for configuration management
- Support for development and production environments

**Key Features:**
- Required env vars: `GOOGLE_SERVICE_ACCOUNT_KEY`, `DATABASE_URL`, `LLM_API_KEY`
- Optional env vars with defaults: `REDIS_URL`, `LLM_API_BASE`, `LLM_MODEL`
- Parallel workers: 1-10 (default: 2)
- Daily generation limit: 1-1000 (default: 50)
- Batch size: 1-50 (default: 5)
- Submission batch size: 1-100 (default: 10)
- Config validation at startup prevents runtime errors

### 1.2 Input Validation ([`validators.ts`](apps/web/scripts/seo/validators.ts))

**Status:** ✅ Complete

Comprehensive validation system with SQL injection prevention:
- Topic validation with character sanitization
- Intent type validation (informational, commercial, transactional, navigational)
- Competitor name validation
- URL validation (HTTPS only)
- Email validation
- Batch URL validation (up to 10,000 URLs)
- Service ID validation (alphanumeric, hyphens, underscores only)
- Batch size, retry count, and delay validation
- Logging sanitization to redact API keys and secrets

**Security Features:**
- SQL injection pattern detection (`OR`, `AND`, `DROP`, `INSERT`, `UPDATE`, `DELETE`)
- HTML/script tag removal
- Whitespace normalization
- Sensitive data redaction in logs

### 1.3 Atomic State Management ([`atomic-state.ts`](apps/web/scripts/seo/atomic-state.ts))

**Status:** ✅ Complete

Thread-safe state management with file locking:
- File-based locking mechanism to prevent race conditions
- Configurable lock timeout (default: 30 seconds)
- Atomic file writes using temp file + rename pattern
- State persistence across script executions
- Stale lock detection and recovery
- Default value handling for missing state files

**Use Cases:**
- Tracking generated content to prevent duplicates
- Managing daily quotas across multiple runs
- Maintaining submission progress

### 1.4 SEO Engines

**Status:** ⚠️ Partial (Core logic built, needs backend integration)

Three SEO engines are implemented:

#### 1.4.1 Smart SEO Engine ([`smart-seo-engine.ts`](apps/web/scripts/seo/smart-seo-engine.ts))
- High-impact content generation strategy
- Content type rotation for diversity (competitor comparisons, industry trends, how-to guides, location deep dives, role analysis, tool reviews)
- Daily generation limit: 100 items
- Batch size: 5 items
- 1-minute delay between batches
- Content rotation every 4 hours to prevent duplicates

#### 1.4.2 Modern SEO Engine ([`modern-seo-engine.ts`](apps/web/scripts/seo/modern-seo-engine.ts))
- Advanced content generation with modern SEO techniques
- Focus on featured snippets and rich results
- Entity-based content optimization

#### 1.4.3 Aggressive SEO Engine ([`aggressive-seo-engine.ts`](apps/web/scripts/seo/aggressive-seo-engine.ts))
- High-volume content generation
- Aggressive competitor analysis
- Maximum coverage strategy

### 1.5 Content Generation Scripts

**Status:** ✅ Complete (Frontend-side)

| Script | Purpose |
|--------|---------|
| [`generate-city-content.ts`](apps/web/scripts/seo/generate-city-content.ts) | City/region job market content |
| [`generate-competitor-content.ts`](apps/web/scripts/seo/generate-competitor-content.ts) | Competitor comparison content |
| [`generate-aggressive-competitor-content.ts`](apps/web/scripts/seo/generate-aggressive-competitor-content.ts) | High-volume competitor content |
| [`generate-intent-content.ts`](apps/web/scripts/seo/generate-intent-content.ts) | Search intent-based content |
| [`generate-trending-content.ts`](apps/web/scripts/seo/generate-trending-content.ts) | Trending topic content |
| [`generate-local-metadata.ts`](apps/web/scripts/seo/generate-local-metadata.ts) | Local SEO metadata |
| [`generate-competitor-gap.ts`](apps/web/scripts/seo/generate-competitor-gap.ts) | Competitor gap analysis |

### 1.6 Google Submission Scripts

**Status:** ✅ Complete (Frontend-side)

| Script | Purpose |
|--------|---------|
| [`submit-to-google.ts`](apps/web/scripts/seo/submit-to-google.ts) | Basic Google Indexing API submission |
| [`submit-to-google-enhanced.ts`](apps/web/scripts/seo/submit-to-google-enhanced.ts) | Enhanced submission with retry logic |
| [`submit-to-google-ultimate.ts`](apps/web/scripts/seo/submit-to-google-ultimate.ts) | Ultimate submission with full features |
| [`submit-all-urls.ts`](apps/web/scripts/seo/submit-all-urls.ts) | Batch URL submission |
| [`verify-google-indexing.ts`](apps/web/scripts/seo/verify-google-indexing.ts) | Verify indexing status |
| [`monitor-indexing.ts`](apps/web/scripts/seo/monitor-indexing.ts) | Ongoing indexing monitoring |

---

## 2. Gap Analysis

### 2.1 Database Schema (Critical Gap)

**Current State:** No database tables exist for SEO tracking

The current implementation uses file-based state management (`atomic-state.ts`), which has significant limitations:
- No multi-instance coordination
- No audit trail
- No querying capabilities
- Limited to single-machine deployments

**Required Tables:**
1. `seo_engine_progress` - Track generation progress per service
2. `seo_generated_content` - Store all generated content
3. `seo_submission_log` - Audit trail for Google submissions
4. `seo_metrics` - Performance tracking
5. `seo_logs` - Database logging
6. `seo_competitor_intelligence` - Competitor analysis data

### 2.2 Python Backend Modules (Critical Gap)

**Current State:** No backend SEO modules in `packages/backend/domain/`

The TypeScript scripts need Python backend support for:
- Database CRUD operations
- API endpoints for reporting
- Background job processing
- Integration with existing authentication

**Required Modules:**
1. `seo_engine_manager.py` - Main SEO engine orchestration
2. `seo_content_repository.py` - Content CRUD operations
3. `seo_submission_service.py` - Google submission handling
4. `seo_metrics_collector.py` - Metrics aggregation

### 2.3 Logging (High Priority Gap)

**Current State:** File-based logging only

Missing features:
- Database-level logging for audit compliance
- Structured logging format
- Log rotation and retention policies
- Log querying capabilities

### 2.4 Metrics Collection (Medium Priority Gap)

**Current State:** Basic tracking via atomic state files

Missing features:
- Content generation success rate
- Submission success rate
- Latency metrics
- Cost tracking (API usage)
- Trend analysis

### 2.5 Rate Limiting & Retry Logic (Medium Priority Gap)

**Current State:** Basic implementation in TypeScript scripts

Improvements needed:
- Per-service rate limiting in database
- Exponential backoff with jitter
- Circuit breaker pattern
- Rate limit violation alerts

### 2.6 Deduplication (Medium Priority Gap)

**Current State:** File-based state tracking only

Missing features:
- Content similarity detection
- Semantic duplicate checking
- Cross-service deduplication
- Historical content lookup

---

## 3. Prioritized Implementation Plan

### Phase 1: Database Foundation (Weeks 1-2)

**Objective:** Create the database schema foundation for SEO tracking

**Tasks:**
- [ ] Create migration file `migrations/041_seo_engine_tables.sql`
- [ ] Implement all 6 SEO tables
- [ ] Add appropriate indexes for query performance
- [ ] Set up foreign key constraints
- [ ] Add initial seed data for configuration

**Effort:** 3-5 days

**Dependencies:** None

**Deliverables:**
- SQL migration file
- Database schema documentation

### Phase 2: Python Backend Modules (Weeks 3-5)

**Objective:** Create Python backend modules for SEO operations

**Tasks:**
- [ ] Create `packages/backend/domain/seo_engine_manager.py`
- [ ] Create `packages/backend/domain/seo_content_repository.py`
- [ ] Create `packages/backend/domain/seo_submission_service.py`
- [ ] Create `packages/backend/domain/seo_metrics_collector.py`
- [ ] Create API routes in `apps/api/seo.py`
- [ ] Add authentication/authorization

**Effort:** 10-15 days

**Dependencies:** Phase 1 complete

**Deliverables:**
- Python modules in `packages/backend/domain/`
- REST API endpoints
- Unit tests

### Phase 3: Logging & Monitoring (Weeks 6-7)

**Objective:** Add comprehensive logging and metrics

**Tasks:**
- [ ] Implement database logging for all SEO operations
- [ ] Add structured logging with correlation IDs
- [ ] Create metrics aggregation queries
- [ ] Build dashboard queries
- [ ] Set up log retention policies

**Effort:** 5-7 days

**Dependencies:** Phase 2 complete

**Deliverables:**
- Logging system
- Metrics queries
- Dashboard components

### Phase 4: Advanced Features (Weeks 8-10)

**Objective:** Implement advanced features for production readiness

**Tasks:**
- [ ] Add deduplication logic in content repository
- [ ] Implement circuit breaker for external APIs
- [ ] Add rate limiting in backend
- [ ] Create retry queue for failed submissions
- [ ] Add alerting for failures

**Effort:** 8-10 days

**Dependencies:** Phases 1-3 complete

**Deliverables:**
- Production-ready SEO system
- Monitoring and alerting
- Documentation

---

## 4. Database Schema SQL

### Migration: 041_seo_engine_tables.sql

```sql
-- =====================================================
-- SEO Engine Database Schema
-- Migration: 041_seo_engine_tables.sql
-- Created: March 16, 2026
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Table: seo_engine_progress
-- Purpose: Track generation progress per service
-- =====================================================
CREATE TABLE seo_engine_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id VARCHAR(100) NOT NULL UNIQUE,
    engine_type VARCHAR(50) NOT NULL DEFAULT 'smart',
    last_index INTEGER NOT NULL DEFAULT 0,
    daily_quota INTEGER NOT NULL DEFAULT 100,
    daily_used INTEGER NOT NULL DEFAULT 0,
    quota_reset_at TIMESTAMPTZ NOT NULL,
    total_generated INTEGER NOT NULL DEFAULT 0,
    total_submitted INTEGER NOT NULL DEFAULT 0,
    total_indexed INTEGER NOT NULL DEFAULT 0,
    last_run_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_error TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seo_engine_progress_service_id ON seo_engine_progress(service_id);
CREATE INDEX idx_seo_engine_progress_is_active ON seo_engine_progress(is_active);
CREATE INDEX idx_seo_engine_progress_quota_reset_at ON seo_engine_progress(quota_reset_at);

-- =====================================================
-- Table: seo_generated_content
-- Purpose: Store all generated SEO content
-- =====================================================
CREATE TABLE seo_generated_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    topic VARCHAR(200) NOT NULL,
    intent VARCHAR(50) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    competitor VARCHAR(100),
    location VARCHAR(100),
    role VARCHAR(100),
    content JSONB NOT NULL,
    meta_description TEXT,
    meta_keywords TEXT[],
    h1_tag TEXT,
    quality_score DECIMAL(3,2),
    originality_score DECIMAL(3,2),
    keyword_density DECIMAL(5,4),
    word_count INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    generated_by VARCHAR(50) NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    indexed_at TIMESTAMPTZ,
    google_index_url VARCHAR(500),
    google_index_status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seo_generated_content_url ON seo_generated_content(url);
CREATE INDEX idx_seo_generated_content_topic ON seo_generated_content(topic);
CREATE INDEX idx_seo_generated_content_intent ON seo_generated_content(intent);
CREATE INDEX idx_seo_generated_content_content_type ON seo_generated_content(content_type);
CREATE INDEX idx_seo_generated_content_competitor ON seo_generated_content(competitor);
CREATE INDEX idx_seo_generated_content_status ON seo_generated_content(status);
CREATE INDEX idx_seo_generated_content_generated_at ON seo_generated_content(generated_at);
CREATE INDEX idx_seo_generated_content_google_index_status ON seo_generated_content(google_index_status);
CREATE INDEX idx_seo_generated_content_topic_intent ON seo_generated_content(topic, intent);
CREATE UNIQUE INDEX idx_seo_generated_content_url_unique ON seo_generated_content(url) WHERE status != 'failed';

-- Full-text search index for content
CREATE INDEX idx_seo_generated_content_fts ON seo_generated_content USING GIN(to_tsvector('english', title || ' ' || COALESCE(meta_description, '')));

-- =====================================================
-- Table: seo_submission_log
-- Purpose: Audit trail for Google submissions
-- =====================================================
CREATE TABLE seo_submission_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES seo_generated_content(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    action VARCHAR(20) NOT NULL,
    method VARCHAR(20) NOT NULL DEFAULT 'URL_UPDATED',
    status_code INTEGER,
    response_body JSONB,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    submitted_by VARCHAR(100) NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seo_submission_log_content_id ON seo_submission_log(content_id);
CREATE INDEX idx_seo_submission_log_url ON seo_submission_log(url);
CREATE INDEX idx_seo_submission_log_submitted_at ON seo_submission_log(submitted_at);
CREATE INDEX idx_seo_submission_log_status_code ON seo_submission_log(status_code);
CREATE INDEX idx_seo_submission_log_action ON seo_submission_log(action);

-- =====================================================
-- Table: seo_metrics
-- Purpose: Performance tracking and analytics
-- =====================================================
CREATE TABLE seo_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_date DATE NOT NULL,
    metric_hour INTEGER NOT NULL CHECK (metric_hour >= 0 AND metric_hour <= 23),
    service_id VARCHAR(100) NOT NULL,
    engine_type VARCHAR(50) NOT NULL,
    
    -- Generation metrics
    content_generated_total INTEGER NOT NULL DEFAULT 0,
    content_generated_success INTEGER NOT NULL DEFAULT 0,
    content_generated_failed INTEGER NOT NULL DEFAULT 0,
    generation_latency_avg_ms DECIMAL(10,2),
    generation_latency_p95_ms DECIMAL(10,2),
    generation_latency_p99_ms DECIMAL(10,2),
    
    -- Submission metrics
    submission_attempts INTEGER NOT NULL DEFAULT 0,
    submission_success INTEGER NOT NULL DEFAULT 0,
    submission_failed INTEGER NOT NULL DEFAULT 0,
    submission_latency_avg_ms DECIMAL(10,2),
    
    -- Indexing metrics
    indexed_total INTEGER NOT NULL DEFAULT 0,
    indexing_rate DECIMAL(5,4),
    
    -- Quality metrics
    avg_quality_score DECIMAL(3,2),
    avg_originality_score DECIMAL(3,2),
    
    -- Cost metrics
    api_calls INTEGER NOT NULL DEFAULT 0,
    api_cost_usd DECIMAL(10,4) NOT NULL DEFAULT 0,
    
    -- Rate limiting
    rate_limit_hits INTEGER NOT NULL DEFAULT 0,
    rate_limit_quota_used INTEGER NOT NULL DEFAULT 0,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(metric_date, metric_hour, service_id)
);

CREATE INDEX idx_seo_metrics_date ON seo_metrics(metric_date);
CREATE INDEX idx_seo_metrics_service_id ON seo_metrics(service_id);
CREATE INDEX idx_seo_metrics_engine_type ON seo_metrics(engine_type);
CREATE INDEX idx_seo_metrics_composite_date_service ON seo_metrics(metric_date, service_id);

-- =====================================================
-- Table: seo_logs
-- Purpose: Database logging for audit compliance
-- =====================================================
CREATE TABLE seo_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL')),
    logger VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    service_id VARCHAR(100),
    content_id UUID,
    url TEXT,
    metadata JSONB,
    trace_id UUID,
    span_id UUID,
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seo_logs_level ON seo_logs(level);
CREATE INDEX idx_seo_logs_created_at ON seo_logs(created_at);
CREATE INDEX idx_seo_logs_service_id ON seo_logs(service_id);
CREATE INDEX idx_seo_logs_content_id ON seo_logs(content_id);
CREATE INDEX idx_seo_logs_trace_id ON seo_logs(trace_id);
CREATE INDEX idx_seo_logs_level_created ON seo_logs(level, created_at);

-- Partition by date for better performance (lasts 90 days)
CREATE INDEX idx_seo_logs_created_at_partition ON seo_logs(created_at) 
    WITH (fillfactor = 80);

-- =====================================================
-- Table: seo_competitor_intelligence
-- Purpose: Competitor analysis and tracking
-- =====================================================
CREATE TABLE seo_competitor_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    competitor_name VARCHAR(100) NOT NULL,
    competitor_domain VARCHAR(255) NOT NULL,
    
    -- Rankings
    target_keyword VARCHAR(200),
    current_rank INTEGER,
    previous_rank INTEGER,
    rank_change INTEGER GENERATED ALWAYS AS (current_rank - previous_rank) STORED,
    
    -- Traffic estimates
    estimated_monthly_visits INTEGER,
    estimated_monthly_traffic_value DECIMAL(10,2),
    
    -- Content analysis
    content_count INTEGER NOT NULL DEFAULT 0,
    avg_content_length INTEGER,
    avg_quality_score DECIMAL(3,2),
    
    -- Backlinks
    total_backlinks INTEGER,
    domain_authority INTEGER,
    
    -- Analysis metadata
    analysis_type VARCHAR(50) NOT NULL,
    analysis_data JSONB,
    insights JSONB,
    
    -- Timestamps
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    next_analysis_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seo_competitor_intelligence_competitor_name ON seo_competitor_intelligence(competitor_name);
CREATE INDEX idx_seo_competitor_intelligence_competitor_domain ON seo_competitor_intelligence(competitor_domain);
CREATE INDEX idx_seo_competitor_intelligence_target_keyword ON seo_competitor_intelligence(target_keyword);
CREATE INDEX idx_seo_competitor_intelligence_analyzed_at ON seo_competitor_intelligence(analyzed_at);
CREATE UNIQUE INDEX idx_seo_competitor_intelligence_unique 
    ON seo_competitor_intelligence(competitor_name, target_keyword, analysis_type);

-- =====================================================
-- Table: seo_quota_tracking
-- Purpose: Track API quotas and usage
-- =====================================================
CREATE TABLE seo_quota_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id VARCHAR(100) NOT NULL,
    quota_type VARCHAR(50) NOT NULL,
    quota_limit INTEGER NOT NULL,
    quota_used INTEGER NOT NULL DEFAULT 0,
    quota_remaining INTEGER GENERATED ALWAYS AS (quota_limit - quota_used) STORED,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    is_hard_limit BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(service_id, quota_type, window_start)
);

CREATE INDEX idx_seo_quota_tracking_service_id ON seo_quota_tracking(service_id);
CREATE INDEX idx_seo_quota_tracking_window ON seo_quota_tracking(window_start, window_end);

-- =====================================================
-- Function: Update updated_at timestamp
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================
-- Triggers: Update timestamps
-- =====================================================
CREATE TRIGGER update_seo_engine_progress_updated_at 
    BEFORE UPDATE ON seo_engine_progress 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seo_generated_content_updated_at 
    BEFORE UPDATE ON seo_generated_content 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seo_competitor_intelligence_updated_at 
    BEFORE UPDATE ON seo_competitor_intelligence 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seo_metrics_updated_at 
    BEFORE UPDATE ON seo_metrics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seo_quota_tracking_updated_at 
    BEFORE UPDATE ON seo_quota_tracking 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- View: seo_content_summary
-- Purpose: Quick overview of content status
-- =====================================================
CREATE OR REPLACE VIEW seo_content_summary AS
SELECT 
    status,
    content_type,
    intent,
    COUNT(*) as count,
    AVG(quality_score) as avg_quality,
    AVG(originality_score) as avg_originality
FROM seo_generated_content
GROUP BY status, content_type, intent;

-- =====================================================
-- View: seo_daily_performance
-- Purpose: Daily performance metrics
-- =====================================================
CREATE OR REPLACE VIEW seo_daily_performance AS
SELECT 
    metric_date,
    service_id,
    engine_type,
    content_generated_total,
    content_generated_success,
    submission_success,
    indexed_total,
    api_cost_usd,
    rate_limit_hits
FROM seo_metrics
ORDER BY metric_date DESC;

-- =====================================================
-- View: seo_submission_success_rate
-- Purpose: Track submission success rates
-- =====================================================
CREATE OR REPLACE VIEW seo_submission_success_rate AS
SELECT 
    DATE(submitted_at) as submission_date,
    COUNT(*) as total_submissions,
    SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status_code != 200 THEN 1 ELSE 0 END) as failed,
    ROUND(
        SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END)::numeric / 
        COUNT(*)::numeric * 100, 2
    ) as success_rate_percent
FROM seo_submission_log
WHERE submitted_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(submitted_at)
ORDER BY submission_date DESC;
```

---

## 5. Estimated Effort Summary

| Phase | Task | Effort (Days) | Priority |
|-------|------|---------------|----------|
| 1 | Database Schema | 3-5 | Critical |
| 2 | Python Backend Modules | 10-15 | High |
| 3 | Logging & Monitoring | 5-7 | High |
| 4 | Advanced Features | 8-10 | Medium |
| **Total** | | **26-37** | |

### Phase 1 Detailed Breakdown

| Task | Effort |
|------|--------|
| Create migration file | 0.5 days |
| Implement seo_engine_progress table | 0.5 days |
| Implement seo_generated_content table | 0.5 days |
| Implement seo_submission_log table | 0.5 days |
| Implement seo_metrics table | 0.5 days |
| Implement seo_logs table | 0.5 days |
| Implement seo_competitor_intelligence table | 0.5 days |
| Add indexes and constraints | 0.5 days |
| Create views | 0.5 days |
| Add triggers | 0.5 days |
| Testing | 1 day |

### Phase 2 Detailed Breakdown

| Task | Effort |
|------|--------|
| SEO engine manager module | 3 days |
| Content repository module | 3 days |
| Submission service module | 2 days |
| Metrics collector module | 2 days |
| API routes | 3 days |
| Authentication | 1 day |
| Unit tests | 2 days |

### Phase 3 Detailed Breakdown

| Task | Effort |
|------|--------|
| Database logging implementation | 2 days |
| Structured logging format | 1 day |
| Metrics aggregation queries | 1 day |
| Dashboard queries | 1 day |
| Log retention policies | 1 day |
| Testing | 1 day |

### Phase 4 Detailed Breakdown

| Task | Effort |
|------|--------|
| Deduplication logic | 3 days |
| Circuit breaker pattern | 2 days |
| Backend rate limiting | 2 days |
| Retry queue | 2 days |
| Alerting | 1 day |
| Testing | 2 days |

---

## 6. Appendix: Environment Variables

### Required Environment Variables

```bash
# Google API
GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
GOOGLE_SEARCH_CONSOLE_SITE='https://jobhuntin.com'

# Database
DATABASE_URL='postgresql://user:pass@host:5432/db'

# Redis (optional)
REDIS_URL='redis://localhost:6379/0'

# LLM
LLM_API_KEY='sk-...'
LLM_API_BASE='https://openrouter.ai/api/v1'
LLM_MODEL='openai/gpt-4o-mini'

# SEO Configuration
SEO_PARALLEL_WORKERS=2
SEO_DAILY_LIMIT=50
SEO_BATCH_SIZE=5
SEO_BATCH_DELAY_MS=30000
SEO_CONTENT_FRESHNESS_HOURS=2
SEO_SUBMISSION_BATCH_SIZE=10
SEO_SUBMISSION_DELAY_MS=2000
SEO_SUBMISSION_MAX_RETRIES=5

# Environment
NODE_ENV='production'
LOG_LEVEL='info'
BASE_URL='https://jobhuntin.com'
```

---

## 7. Appendix: API Endpoints

### Proposed SEO API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/seo/content | List generated content |
| POST | /api/v1/seo/content | Create new content |
| GET | /api/v1/seo/content/{id} | Get content by ID |
| PUT | /api/v1/seo/content/{id} | Update content |
| DELETE | /api/v1/seo/content/{id} | Delete content |
| POST | /api/v1/seo/submit | Submit URL to Google |
| GET | /api/v1/seo/submissions | List submission logs |
| GET | /api/v1/seo/metrics | Get metrics |
| GET | /api/v1/seo/progress | Get engine progress |
| POST | /api/v1/seo/reset | Reset daily quota |

---

## 8. Appendix: References

- [Google Indexing API Documentation](https://developers.google.com/search/apis/indexing-api/v3/quickstart)
- [PostgreSQL UUID Extension](https://www.postgresql.org/docs/current/uuid-ossp.html)
- [GIN Indexes](https://www.postgresql.org/docs/current/gin.html)
