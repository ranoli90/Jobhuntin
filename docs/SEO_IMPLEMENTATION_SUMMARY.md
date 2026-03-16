# SEO Implementation Summary Report

**Document Version:** 1.0  
**Date:** March 16, 2026  
**Status:** Complete  
**Author:** Technical Architecture Team

---

## 1. Executive Summary

This report documents the completed implementation of the SEO Engine remediation work. The SEO Engine is a sophisticated content generation and submission system designed to improve search visibility for the JobHuntin platform.

### What Was Accomplished

The remediation addressed critical gaps identified in the original SEO audit by implementing:

1. **Database Foundation** - Created 6 new database tables with proper indexes for SEO tracking
2. **Python Backend Integration** - Built 6 Python modules for database operations and business logic
3. **TypeScript Utilities** - Implemented 3 core utility modules for client-side operations
4. **Error Handling** - Created comprehensive error classes with retry logic and rate limiting
5. **Health Monitoring** - Implemented health check capabilities for system monitoring

### Key Metrics

| Metric | Before | After |
|--------|--------|-------|
| Database Tables for SEO | 0 | 6 |
| Python Backend Modules | 0 | 6 |
| TypeScript Utilities | 0 | 3 |
| Error Types | 0 | 6+ |
| Health Checks | 0 | 6+ |

---

## 2. Completed Work

### 2.1 Database Migration

**File:** [`migrations/041_seo_engine_tables.sql`](migrations/041_seo_engine_tables.sql)

Created 6 database tables with comprehensive indexes:

1. **[`seo_engine_progress`](migrations/041_seo_engine_tables.sql:5)** - Tracks service progress and quotas
   - Fields: service_id, last_index, daily_quota_used, daily_quota_reset
   - Indexes: service_id, daily_quota_reset

2. **[`seo_generated_content`](migrations/041_seo_engine_tables.sql:17)** - Stores generated SEO content
   - Fields: url, title, topic, intent, competitor, content_hash, quality_score, google_indexed, clicks, impressions, ctr, position
   - Indexes: topic, intent, competitor, google_indexed, created_at, deleted_at
   - Unique constraint on url

3. **[`seo_submission_log`](migrations/041_seo_engine_tables.sql:39)** - Audit trail for Google submissions
   - Fields: service_id, batch_url_file, urls_submitted, urls_successful, success, error_message, error_code, retry_count
   - Indexes: service_id, created_at, success

4. **[`seo_metrics`](migrations/041_seo_engine_tables.sql:53)** - Performance metrics tracking
   - Fields: total_generated, total_submitted, success_rate, average_generation_time_ms, average_submission_time_ms, api_calls_today, quota_used_today, metrics (JSONB)
   - Indexes: created_at

5. **[`seo_logs`](migrations/041_seo_engine_tables.sql:67)** - Database logging
   - Fields: level, message, meta (JSONB)
   - Indexes: level, created_at

6. **[`seo_competitor_intelligence`](migrations/041_seo_engine_tables.sql:76)** - Competitor analysis data
   - Fields: competitor_name, search_volume, difficulty_score, intent, keywords, content_gaps, weaknesses
   - Indexes: competitor_name, last_updated

### 2.2 Python Backend Modules

All modules are located in [`packages/backend/domain/`](packages/backend/domain/)

#### 2.2.1 SEOProgressRepository

**File:** [`packages/backend/domain/seo_progress.py`](packages/backend/domain/seo_progress.py)

Manages SEO engine progress and quotas:

| Method | Purpose |
|--------|---------|
| [`get_progress()`](packages/backend/domain/seo_progress.py:30) | Retrieve progress for a specific service |
| [`update_progress()`](packages/backend/domain/seo_progress.py:85) | Update progress with last_index and daily_quota_used |
| [`reset_daily_quota()`](packages/backend/domain/seo_progress.py:165) | Reset daily quota at midnight UTC |
| [`increment_quota()`](packages/backend/domain/seo_progress.py:231) | Increment quota usage with auto-reset |

#### 2.2.2 SEOContentRepository

**File:** [`packages/backend/domain/seo_content.py`](packages/backend/domain/seo_content.py)

Manages generated SEO content with deduplication:

| Method | Purpose |
|--------|---------|
| [`check_content_exists()`](packages/backend/domain/seo_content.py:36) | Check if URL exists |
| [`check_content_hash_exists()`](packages/backend/domain/seo_content.py:62) | Check for duplicate content hash |
| [`record_generated_content()`](packages/backend/domain/seo_content.py:88) | Record new content with validation |
| [`get_content_by_topic_intent()`](packages/backend/domain/seo_content.py:171) | Find content by topic/intent |
| [`get_content_by_url()`](packages/backend/domain/seo_content.py:230) | Retrieve content by URL |
| [`update_google_indexing()`](packages/backend/domain/seo_content.py:263) | Update indexing status |
| [`update_performance_metrics()`](packages/backend/domain/seo_content.py:308) | Update clicks, impressions, CTR, position |
| [`soft_delete_content()`](packages/backend/domain/seo_content.py:376) | Soft delete content |
| [`get_content_count()`](packages/backend/domain/seo_content.py:471) | Get content count with filters |

#### 2.2.3 SEOMetricsCollector

**File:** [`packages/backend/domain/seo_metrics.py`](packages/backend/domain/seo_metrics.py)

Collects and aggregates SEO performance metrics:

| Method | Purpose |
|--------|---------|
| [`record_generation()`](packages/backend/domain/seo_metrics.py:30) | Record content generation event |
| [`record_submission()`](packages/backend/domain/seo_metrics.py:91) | Record Google submission |
| [`save_metrics()`](packages/backend/domain/seo_metrics.py:202) | Save custom metrics |
| [`get_metrics()`](packages/backend/domain/seo_metrics.py:233) | Get metrics for last N days |
| [`get_latest_metrics()`](packages/backend/domain/seo_metrics.py:265) | Get most recent metrics |
| [`get_submission_logs()`](packages/backend/domain/seo_metrics.py:294) | Get submission logs with filters |
| [`get_success_rate()`](packages/backend/domain/seo_metrics.py:362) | Calculate submission success rate |
| [`get_average_generation_time()`](packages/backend/domain/seo_metrics.py:394) | Calculate average generation time |

#### 2.2.4 SEOLogger

**File:** [`packages/backend/domain/seo_logging.py`](packages/backend/domain/seo_logging.py)

Winston-style database logging for SEO operations:

| Method | Purpose |
|--------|---------|
| [`log()`](packages/backend/domain/seo_logging.py:43) | Log at specified level |
| [`debug()`](packages/backend/domain/seo_logging.py:110) | Log debug message |
| [`info()`](packages/backend/domain/seo_logging.py:122) | Log info message |
| [`warn()`](packages/backend/domain/seo_logging.py:134) | Log warning message |
| [`error()`](packages/backend/domain/seo_logging.py:146) | Log error message |
| [`get_recent_logs()`](packages/backend/domain/seo_logging.py:158) | Get recent log entries |
| [`get_logs_by_level()`](packages/backend/domain/seo_logging.py:212) | Filter logs by level |
| [`get_error_logs()`](packages/backend/domain/seo_logging.py:233) | Get all error logs |
| [`search_logs()`](packages/backend/domain/seo_logging.py:247) | Search logs by message |
| [`get_logs_by_timerange()`](packages/backend/domain/seo_logging.py:303) | Get logs within time range |
| [`clear_old_logs()`](packages/backend/domain/seo_logging.py:394) | Delete logs older than N days |

#### 2.2.5 SEOCompetitorRepository

**File:** [`packages/backend/domain/seo_competitor.py`](packages/backend/domain/seo_competitor.py)

Manages competitor intelligence data:

| Method | Purpose |
|--------|---------|
| [`get_competitor()`](packages/backend/domain/seo_competitor.py:30) | Get competitor by name |
| [`update_competitor()`](packages/backend/domain/seo_competitor.py:72) | Update competitor data |
| [`create_competitor()`](packages/backend/domain/seo_competitor.py:168) | Create new competitor |
| [`get_all_competitors()`](packages/backend/domain/seo_competitor.py:226) | List all competitors |
| [`delete_competitor()`](packages/backend/domain/seo_competitor.py:258) | Delete competitor |
| [`get_competitors_by_difficulty()`](packages/backend/domain/seo_competitor.py:292) | Filter by difficulty score |
| [`get_competitors_by_intent()`](packages/backend/domain/seo_competitor.py:329) | Filter by search intent |
| [`get_content_gaps()`](packages/backend/domain/seo_competitor.py:364) | Get content gaps |
| [`add_content_gap()`](packages/backend/domain/seo_competitor.py:428) | Add content gap |

#### 2.2.6 SEOHealthCheck

**File:** [`packages/backend/domain/seo_health.py`](packages/backend/domain/seo_health.py)

Comprehensive health monitoring:

| Method | Purpose |
|--------|---------|
| [`check_database_connection()`](packages/backend/domain/seo_health.py:51) | Verify database connectivity |
| [`check_progress_table()`](packages/backend/domain/seo_health.py:104) | Verify progress table exists |
| [`check_content_table()`](packages/backend/domain/seo_health.py:115) | Verify content table exists |
| [`check_metrics_table()`](packages/backend/domain/seo_health.py:126) | Verify metrics table exists |
| [`check_quota_status()`](packages/backend/domain/seo_health.py:194) | Check daily quota remaining |
| [`check_recent_errors()`](packages/backend/domain/seo_health.py:277) | Check for recent errors |
| [`run_all_checks()`](packages/backend/domain/seo_health.py:375) | Run all health checks |

### 2.3 TypeScript Utility Modules

All modules are located in [`apps/web/scripts/seo/`](apps/web/scripts/seo/)

#### 2.3.1 RateLimiter

**File:** [`apps/web/scripts/seo/rate-limiter.ts`](apps/web/scripts/seo/rate-limiter.ts)

Token bucket rate limiting implementation:

- **[`RateLimiter`](apps/web/scripts/seo/rate-limiter.ts:31)** class - Token bucket algorithm
  - [`acquire()`](apps/web/scripts/seo/rate-limiter.ts:68) - Acquire token (wait if needed)
  - [`tryAcquire()`](apps/web/scripts/seo/rate-limiter.ts:93) - Try to acquire without waiting
  - [`getAvailableTokens()`](apps/web/scripts/seo/rate-limiter.ts:109) - Get current tokens
  - [`reset()`](apps/web/scripts/seo/rate-limiter.ts:120) - Reset to full capacity

- **[`MultiRateLimiter`](apps/web/scripts/seo/rate-limiter.ts:180)** - Manage multiple rate limiters

- **Presets:**
  - `googleIndexing` - 100 requests/100 seconds
  - `searchConsole` - 60 requests/minute
  - `general` - 60 requests/minute
  - `aggressive` - 120 requests/minute
  - `conservative` - 30 requests/minute

#### 2.3.2 Retry Module

**File:** [`apps/web/scripts/seo/retry.ts`](apps/web/scripts/seo/retry.ts)

Exponential backoff with jitter:

- **[`retryWithBackoff<T>()`](apps/web/scripts/seo/retry.ts:98)** - Retry with exponential backoff
- **[`retryWithRateLimitHandling<T>()`](apps/web/scripts/seo/retry.ts:163)** - Retry with rate limit awareness
- **[`retryWithResult<T>()`](apps/web/scripts/seo/retry.ts:236)** - Retry returning result metadata
- **[`retryBatch<T, R>()`](apps/web/scripts/seo/retry.ts:367)** - Batch retry with results
- **[`withRetry<T>()`](apps/web/scripts/seo/retry.ts:349)** - Decorator for retry logic

- **Presets:**
  - `fast` - 3 attempts, 500ms initial, 5s max
  - `standard` - 5 attempts, 1s initial, 30s max
  - `conservative` - 3 attempts, 2s initial, 60s max
  - `googleApi` - 5 attempts, 1s initial, 60s max (Google-specific)
  - `none` - No retries

#### 2.3.3 Error Module

**File:** [`apps/web/scripts/seo/errors.ts`](apps/web/scripts/seo/errors.ts)

Comprehensive error handling:

- **Error Codes:**
  - `GENERATION_FAILED` - Content generation failed
  - `SUBMISSION_FAILED` - URL submission failed
  - `RATE_LIMITED` - Rate limit exceeded
  - `QUOTA_EXCEEDED` - API quota exceeded
  - `VALIDATION_FAILED` - Input validation failed
  - `NETWORK_ERROR` - Network error
  - `AUTH_ERROR` - Authentication error
  - `TIMEOUT` - Timeout error
  - `DATABASE_ERROR` - Database error
  - `CONFIG_ERROR` - Configuration error
  - `INTERNAL_ERROR` - Internal error

- **Error Classes:**
  - **[`SEOEngineError`](apps/web/scripts/seo/errors.ts:80)** - Base error class
  - **[`SEOValidationError`](apps/web/scripts/seo/errors.ts:165)** - Validation errors
  - **[`RateLimitError`](apps/web/scripts/seo/errors.ts:188)** - Rate limit errors
  - **[`QuotaExceededError`](apps/web/scripts/seo/errors.ts:212)** - Quota exceeded
  - **[`SubmissionError`](apps/web/scripts/seo/errors.ts:236)** - URL submission errors
  - **[`GenerationError`](apps/web/scripts/seo/errors.ts:260)** - Content generation errors
  - **[`AggregateSEOError`](apps/web/scripts/seo/errors.ts:430)** - Multiple errors

- **Utility Functions:**
  - [`isRetryable()`](apps/web/scripts/seo/errors.ts:295) - Check if error is retryable
  - [`isRateLimitError()`](apps/web/scripts/seo/errors.ts:319) - Check for rate limit
  - [`isQuotaError()`](apps/web/scripts/seo/errors.ts:339) - Check for quota error
  - [`getRetryDelay()`](apps/web/scripts/seo/errors.ts:360) - Extract retry delay
  - [`formatError()`](apps/web/scripts/seo/errors.ts:379) - Format error for logging
  - [`withErrorHandling()`](apps/web/scripts/seo/errors.ts:394) - Wrap function with error handling

---

## 3. Files Created/Modified

### Database Migration

| File | Lines | Purpose |
|------|-------|---------|
| [`migrations/041_seo_engine_tables.sql`](migrations/041_seo_engine_tables.sql) | 142 | 6 SEO tables with indexes |

### Python Backend

| File | Lines | Classes/Functions |
|------|-------|-------------------|
| [`packages/backend/domain/seo_progress.py`](packages/backend/domain/seo_progress.py) | 354 | `SEOProgressRepository` |
| [`packages/backend/domain/seo_content.py`](packages/backend/domain/seo_content.py) | 544 | `SEOContentRepository`, `VALID_INTENTS` |
| [`packages/backend/domain/seo_metrics.py`](packages/backend/domain/seo_metrics.py) | 445 | `SEOMetricsCollector` |
| [`packages/backend/domain/seo_logging.py`](packages/backend/domain/seo_logging.py) | 426 | `SEOLogger`, `SEOLogLevel` |
| [`packages/backend/domain/seo_competitor.py`](packages/backend/domain/seo_competitor.py) | 551 | `SEOCompetitorRepository` |
| [`packages/backend/domain/seo_health.py`](packages/backend/domain/seo_health.py) | 509 | `SEOHealthCheck`, `SEOHealthStatus` |

### TypeScript Utilities

| File | Lines | Classes/Functions |
|------|-------|-------------------|
| [`apps/web/scripts/seo/rate-limiter.ts`](apps/web/scripts/seo/rate-limiter.ts) | 232 | `RateLimiter`, `MultiRateLimiter`, `RateLimiterPresets` |
| [`apps/web/scripts/seo/retry.ts`](apps/web/scripts/seo/retry.ts) | 387 | `retryWithBackoff`, `retryWithRateLimitHandling`, `RetryPresets` |
| [`apps/web/scripts/seo/errors.ts`](apps/web/scripts/seo/errors.ts) | 461 | `SEOEngineError`, `ErrorCode`, utility functions |

### Documentation

| File | Purpose |
|------|---------|
| [`docs/SEO_REMEDIATION_REPORT.md`](docs/SEO_REMEDIATION_REPORT.md) | Comprehensive remediation plan (source document) |
| [`docs/SEO_IMPLEMENTATION_SUMMARY.md`](docs/SEO_IMPLEMENTATION_SUMMARY.md) | This implementation summary |

---

## 4. Architecture Overview

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SEO Engine Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   Web Frontend  │    │   Admin Panel   │    │  Worker Jobs    │        │
│  │  (TypeScript)   │    │   (TypeScript)  │    │   (Python)      │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                       │                       │                  │
│           │   ┌─────────────────────────────────────────────────────────┐  │
│           └──►│            FastAPI Backend (Port 8000)                │  │
│               │  ┌─────────────────────────────────────────────────────┐│  │
│               │  │              packages/backend/domain/             ││  │
│               │  │  ┌──────────────┐  ┌──────────────┐              ││  │
│               │  │  │seo_progress  │  │seo_content   │              ││  │
│               │  │  │.py           │  │.py           │              ││  │
│               │  │  └──────────────┘  └──────────────┘              ││  │
│               │  │  ┌──────────────┐  ┌──────────────┐              ││  │
│               │  │  │seo_metrics   │  │seo_logging  │              ││  │
│               │  │  │.py           │  │.py           │              ││  │
│               │  │  └──────────────┘  └──────────────┘              ││  │
│               │  │  ┌──────────────┐  ┌──────────────┐              ││  │
│               │  │  │seo_competitor│  │seo_health    │              ││  │
│               │  │  │.py           │  │.py           │              ││  │
│               │  │  └──────────────┘  └──────────────┘              ││  │
│               │  └─────────────────────────────────────────────────────┘│  │
│               └───────────────────────────────────────────────────────────┘  │
│                                       │                                       │
│                                       ▼                                       │
│               ┌───────────────────────────────────────────────────────────┐   │
│               │         PostgreSQL Database (Port 5432)                 │   │
│               │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│               │  │seo_engine    │  │seo_generated │  │seo_submission│  │   │
│               │  │_progress     │  │_content      │  │_log          │  │   │
│               │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│               │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│               │  │seo_metrics   │  │seo_logs      │  │seo_competitor│  │   │
│               │  │              │  │              │  │_intelligence │  │   │
│               │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│               └───────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow

#### Content Generation Flow

```
1. Client Request
       │
       ▼
2. Validate Input (validators.ts)
       │
       ▼
3. Check Quota (SEOProgressRepository)
       │
       ▼
4. Generate Content (LLM)
       │
       ▼
5. Check Deduplication (SEOContentRepository)
       │
       ├── Duplicate Found ──► Skip & Log
       │
       └── Unique ──► Record Content
                           │
                           ▼
                    Update Metrics (SEOMetricsCollector)
                           │
                           ▼
                    Log Operation (SEOLogger)
```

#### Submission Flow

```
1. Submit URL to Google
       │
       ▼
2. Rate Limiter (rate-limiter.ts)
       │ (Wait if needed)
       ▼
3. Retry with Backoff (retry.ts)
       │ (On failure)
       ▼
4. Log Submission (SEOMetricsCollector)
       │
       ▼
5. Update Indexing Status (SEOContentRepository)
       │
       ▼
6. Health Check (SEOHealthCheck)
```

### 4.3 Component Interactions

| Component | Depends On | Provides To |
|-----------|-----------|-------------|
| SEOProgressRepository | Database | Quota tracking |
| SEOContentRepository | Database, SEOProgressRepository | Content management |
| SEOMetricsCollector | Database | Performance data |
| SEOLogger | Database | Audit trail |
| SEOCompetitorRepository | Database | Competitor analysis |
| SEOHealthCheck | All repositories | System health |
| RateLimiter | Error module | Request throttling |
| Retry Module | Error module | Resilience |
| Error Module | None | Error handling |

---

## 5. Remaining Work

Based on the original audit, the following items were identified but remain incomplete:

### 5.1 High Priority

| Item | Description | Status |
|------|-------------|--------|
| API Routes | REST endpoints for SEO operations in `apps/api/seo.py` | Not started |
| Authentication | Integration with existing auth system | Not started |
| Background Jobs | Worker jobs for automated generation/submission | Not started |

### 5.2 Medium Priority

| Item | Description | Status |
|------|-------------|--------|
| Circuit Breaker | Pattern for external API resilience | Not implemented |
| Alerting | Alerts for failures and quota exhaustion | Not implemented |
| Dashboard UI | Admin dashboard components for SEO management | Not started |

### 5.3 Lower Priority

| Item | Description | Status |
|------|-------------|--------|
| Full-text Search | Advanced content search capabilities | Not implemented |
| ML-based Deduplication | Semantic duplicate detection | Not implemented |
| Automated Reporting | Scheduled report generation | Not started |

---

## 6. Next Steps

### 6.1 Immediate Actions

1. **Run Database Migration**
   ```bash
   alembic upgrade head
   ```
   This will create all 6 SEO tables.

2. **Verify Installation**
   ```bash
   # Run health checks
   PYTHONPATH=apps:packages:. python -c "
   import asyncio
   from packages.backend.domain.seo_health import SEOHealthCheck
   # Test health checks
   "
   ```

3. **Integration Testing**
   - Test all Python modules with database
   - Test TypeScript utilities in web application

### 6.2 Recommended Implementation Order

1. **Week 1-2**: Deploy migration and verify database
2. **Week 3-4**: Create API routes in `apps/api/`
3. **Week 5-6**: Add authentication and authorization
4. **Week 7-8**: Implement background worker jobs
5. **Week 9-10**: Build admin dashboard components

### 6.3 Best Practices

- Always use parameterized queries (already implemented)
- Implement proper logging at each layer
- Monitor rate limits and quotas
- Set up alerting for errors and failures
- Regular health check monitoring

---

## 7. Integration Guide

### 7.1 Python Backend Integration

#### Initialize Database Connection

```python
import asyncpg
from packages.backend.domain.seo_progress import SEOProgressRepository
from packages.backend.domain.seo_content import SEOContentRepository
from packages.backend.domain.seo_metrics import SEOMetricsCollector
from packages.backend.domain.seo_logging import SEOLogger
from packages.backend.domain.seo_competitor import SEOCompetitorRepository
from packages.backend.domain.seo_health import SEOHealthCheck

async def get_seo_repositories(conn: asyncpg.Connection):
    """Get all SEO repositories with a shared connection."""
    return {
        "progress": SEOProgressRepository(conn),
        "content": SEOContentRepository(conn),
        "metrics": SEOMetricsCollector(conn),
        "logger": SEOLogger(conn),
        "competitor": SEOCompetitorRepository(conn),
        "health": SEOHealthCheck(conn),
    }
```

#### Record Generated Content

```python
from packages.backend.domain.seo_content import SEOContentRepository

async def record_new_content(conn, url, title, topic, intent, content_hash):
    repo = SEOContentRepository(conn)
    
    try:
        content = await repo.record_generated_content(
            url=url,
            title=title,
            topic=topic,
            intent=intent,
            content_hash=content_hash,
            competitor=None,
            quality_score=0.85,
        )
        return content
    except ValueError as e:
        # Handle duplicate content
        print(f"Duplicate content: {e}")
        return None
```

#### Track Metrics

```python
from packages.backend.domain.seo_metrics import SEOMetricsCollector
import time

async def track_generation(conn, topic):
    collector = SEOMetricsCollector(conn)
    
    start = time.time()
    # ... generate content ...
    duration_ms = int((time.time() - start) * 1000)
    
    await collector.record_generation(
        generation_time_ms=duration_ms,
        success=True,
        topic=topic,
    )
```

#### Health Monitoring

```python
from packages.backend.domain.seo_health import SEOHealthCheck

async def check_system_health(conn):
    health = SEOHealthCheck(conn)
    status = await health.run_all_checks(service_id="default")
    
    print(f"Overall status: {status.overall_status}")
    print(f"Healthy: {status.healthy}")
    
    for check_name, result in status.checks.items():
        print(f"  {check_name}: {result['status']}")
```

### 7.2 TypeScript Frontend Integration

#### Rate Limiting

```typescript
import { RateLimiter, RateLimiterPresets } from './scripts/seo/rate-limiter';

// Use preset for Google Indexing API
const limiter = RateLimiterPresets.googleIndexing();

async function makeApiCall() {
    await limiter.acquire(); // Wait if needed
    // ... make API call ...
}
```

#### Retry Logic

```typescript
import { retryWithBackoff, RetryPresets } from './scripts/seo/retry';

async function fetchWithRetry() {
    return retryWithBackoff(
        () => fetch('/api/seo/content'),
        RetryPresets.googleApi()
    );
}
```

#### Error Handling

```typescript
import { SEOEngineError, ErrorCode, isRetryable } from './scripts/seo/errors';

try {
    await generateContent();
} catch (error) {
    if (error instanceof SEOEngineError) {
        console.log(`Error code: ${error.code}`);
        console.log(`Retryable: ${error.retryable}`);
        
        if (error.isRateLimited()) {
            // Handle rate limit specifically
        }
    }
}
```

### 7.3 Complete Workflow Example

```python
import asyncio
import asyncpg
from packages.backend.domain import (
    SEOProgressRepository,
    SEOContentRepository,
    SEOMetricsCollector,
    SEOLogger,
    SEOHealthCheck,
)

async def seo_workflow(conn: asyncpg.Connection):
    """Complete SEO content generation workflow."""
    
    # Initialize repositories
    progress_repo = SEOProgressRepository(conn)
    content_repo = SEOContentRepository(conn)
    metrics_collector = SEOMetricsCollector(conn)
    logger = SEOLogger(conn)
    health_check = SEOHealthCheck(conn)
    
    service_id = "content-generator"
    
    # 1. Check health
    health = await health_check.run_all_checks(service_id)
    if not health.healthy:
        print(f"System not healthy: {health.recommendations}")
        return
    
    # 2. Check quota
    quota = await health_check.check_quota_status(service_id)
    if quota["quota_remaining"] <= 0:
        print("Daily quota exhausted")
        return
    
    # 3. Log start
    await logger.info("Starting content generation", {"service_id": service_id})
    
    # 4. Generate content (pseudocode)
    url = "https://example.com/jobs/software-engineer-seattle"
    title = "Best Software Engineer Jobs in Seattle 2026"
    topic = "software engineer jobs"
    intent = "informational"
    content_hash = "abc123"  # Generated from content
    
    # 5. Check for duplicates
    if await content_repo.check_content_hash_exists(content_hash):
        await logger.warn("Duplicate content detected", {"hash": content_hash})
        return
    
    # 6. Record content
    try:
        content = await content_repo.record_generated_content(
            url=url,
            title=title,
            topic=topic,
            intent=intent,
            content_hash=content_hash,
            quality_score=0.85,
        )
        await logger.info("Content recorded", {"url": url})
    except ValueError as e:
        await logger.error(f"Failed to record content: {e}")
        return
    
    # 7. Increment quota
    await progress_repo.increment_quota(service_id)
    
    # 8. Record metrics
    await metrics_collector.record_generation(
        generation_time_ms=1500,
        success=True,
        topic=topic,
    )
    
    await logger.info("Content generation complete", {"url": url})

# Run workflow
async def main():
    conn = await asyncpg.connect("postgresql://...")
    try:
        await seo_workflow(conn)
    finally:
        await conn.close()

asyncio.run(main())
```

---

## Appendix A: Database Schema Quick Reference

### Table: seo_engine_progress

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| service_id | TEXT | Unique service identifier |
| last_index | INTEGER | Last processed index |
| last_submission_at | TIMESTAMPTZ | Last submission timestamp |
| daily_quota_used | INTEGER | Quota consumed today |
| daily_quota_reset | TIMESTAMPTZ | Next quota reset |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

### Table: seo_generated_content

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| url | TEXT | Unique content URL |
| title | TEXT | Content title |
| topic | TEXT | Content topic |
| intent | TEXT | Search intent |
| competitor | TEXT | Related competitor |
| content_hash | TEXT | Content hash for deduplication |
| quality_score | NUMERIC | Quality score 0-1 |
| google_indexed | BOOLEAN | Google indexing status |
| clicks | INTEGER | Search clicks |
| impressions | INTEGER | Search impressions |
| ctr | NUMERIC | Click-through rate |
| position | NUMERIC | Average search position |

---

## Appendix B: Error Code Reference

| Code | HTTP Status | Retryable | Description |
|------|-------------|-----------|-------------|
| GENERATION_FAILED | 500 | No | Content generation failed |
| SUBMISSION_FAILED | 500 | Yes | URL submission failed |
| RATE_LIMITED | 429 | Yes | Rate limit exceeded |
| QUOTA_EXCEEDED | 429 | Yes | API quota exceeded |
| VALIDATION_FAILED | 400 | No | Input validation failed |
| NETWORK_ERROR | 503 | Yes | Network error |
| AUTH_ERROR | 401 | No | Authentication error |
| TIMEOUT | 504 | Yes | Timeout error |
| DATABASE_ERROR | 500 | Yes | Database error |
| CONFIG_ERROR | 500 | No | Configuration error |
| INTERNAL_ERROR | 500 | No | Unknown error |

---

## 8. Configuration

### 8.1 Environment Variables

All SEO scripts use centralized configuration via [`apps/web/scripts/seo/config.ts`](apps/web/scripts/seo/config.ts). The following environment variables are supported:

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Path to Google service account JSON key file or raw JSON content | `/path/to/key.json` |
| `DATABASE_URL` | PostgreSQL database connection string | `postgresql://user:pass@host:5432/db` |
| `LLM_API_KEY` | OpenRouter API key for LLM content generation | `sk-...` |

#### Optional Variables - URLs

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `https://jobhuntin.com` | Primary site URL |
| `OPENROUTER_API_URL` | `https://openrouter.ai/api/v1` | OpenRouter API endpoint |
| `GOOGLE_SEARCH_CONSOLE_SITE` | (none) | Google Search Console verified site URL |

#### Optional Variables - Generation Settings

| Variable | Default | Range | Description |
|----------|---------|-------|-------------|
| `SEO_PARALLEL_WORKERS` | `2` | 1-10 | Max parallel content generation workers |
| `SEO_DAILY_LIMIT` | `50` | 1-1000 | Daily content generation limit |
| `SEO_BATCH_SIZE` | `5` | 1-50 | Content batch size |
| `SEO_BATCH_DELAY_MS` | `30000` | 1000-300000 | Delay between batches (ms) |
| `SEO_CONTENT_FRESHNESS_HOURS` | `2` | 1-168 | Content freshness check interval (hours) |

#### Optional Variables - Submission Settings

| Variable | Default | Range | Description |
|----------|---------|-------|-------------|
| `SEO_SUBMISSION_BATCH_SIZE` | `10` | 1-100 | URLs per submission batch |
| `SEO_SUBMISSION_DELAY_MS` | `2000` | 100-60000 | Delay between submissions (ms) |
| `SEO_SUBMISSION_MAX_RETRIES` | `5` | 1-20 | Max retry attempts |

#### Optional Variables - Other

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `LLM_API_BASE` | (from config) | LLM API base URL |
| `LLM_MODEL` | `openai/gpt-4o-mini` | Default LLM model |
| `NODE_ENV` | `development` | Environment (development/production) |
| `LOG_LEVEL` | `info` | Log level (debug/info/warn/error) |
| `INDEXNOW_API_KEY` | (none) | IndexNow API key for Bing/Yandex submission |
| `SEO_COMPETITOR_DATA_FILE` | `../../src/data/competitors.json` | Path to competitor data JSON |

### 8.2 URL Endpoints Configuration

The SEO engine uses centralized URL endpoints defined in [`config.ts`](apps/web/scripts/seo/config.ts):

```typescript
interface SEOUrlEndpoints {
  baseUrl: string;                    // Site base URL
  openRouterApiUrl: string;           // LLM API endpoint
  googleIndexingApiUrl: string;       // Google Indexing API
  googleSitemapPingUrl: string;       // Google sitemap ping
  bingSitemapPingUrl: string;         // Bing sitemap ping
  indexNowEndpoints: string[];        // IndexNow API endpoints
}
```

Default endpoints:
- Google Indexing API: `https://indexing.googleapis.com/v3/urlNotifications:publish`
- Google Sitemap Ping: `https://www.google.com/ping`
- Bing Sitemap Ping: `https://www.bing.com/ping`
- IndexNow: `https://api.indexnow.org/indexnow`, `https://www.bing.com/indexnow`, `https://yandex.com/indexnow`

### 8.3 Competitor Data Configuration

Competitor data is loaded from JSON files:

- **Primary source**: `apps/web/src/data/competitors.json`
- **Configurable via**: `SEO_COMPETITOR_DATA_FILE` environment variable

The modern-seo-engine.ts script dynamically loads competitor data from JSON and generates intelligence (volume, difficulty, keywords) from the data. Fallback to default intelligence data occurs if the JSON file is unavailable.

### 8.4 Testing Configuration

Run tests with proper environment:
```bash
cd apps/web
npx jest scripts/seo/__tests__/ --testPathIgnorePatterns=integration
npx ts-node scripts/seo/__tests__/seo-integration.test.ts
```

---

**End of Document**
