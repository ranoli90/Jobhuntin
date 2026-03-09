# Backend Architecture Audit - Executive Summary

## Critical Findings (5)

1. **Missing Idempotency Keys** - Write operations risk duplicates
2. **Missing Index on Worker Claim Query** - Performance bottleneck
3. **N+1 Query in get_detail** - 3x database round-trips
4. **Race Condition in User Creation** - Constraint violations
5. **Connection Pool Exhaustion Risk** - No monitoring/circuit breaker

## High Priority Findings (12)

1. Inconsistent error response format
2. Missing API versioning strategy
3. Missing index on application_events
4. Missing foreign key indexes
5. No idempotency in worker task processing
6. No dead letter queue monitoring
7. Exponential backoff without jitter
8. No worker health check endpoint
9. Unhandled exceptions in worker
10. Missing structured logging context
11. No distributed tracing
12. Missing error metrics

## Quick Wins (Can Fix Today)

1. Add jitter to exponential backoff (5 min)
2. Add worker health check endpoint (15 min)
3. Standardize error response format (30 min)
4. Add missing FK indexes (10 min)
5. Add connection pool stats endpoint (20 min)

## Database Indexes to Add

```sql
-- Worker claim query (CRITICAL)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_claim_queue
ON applications(status, attempt_count, available_at, priority_score DESC, created_at ASC)
WHERE status IN ('QUEUED', 'REQUIRES_INPUT');

-- Application events (HIGH)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_application_events_app_time
ON application_events(application_id, created_at DESC);

-- Foreign keys (HIGH)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_job_id 
ON applications(job_id) WHERE job_id IS NOT NULL;
```

## Code Changes Required

### 1. Idempotency Middleware (apps/api/main.py)
- Add middleware to check Redis for duplicate requests
- Store responses for idempotent operations

### 2. Fix N+1 Query (packages/backend/domain/repositories.py:272)
- Replace 3 separate queries with single JOIN query
- Use json_agg for inputs and events

### 3. Fix Race Condition (apps/api/auth.py:287)
- Use INSERT ... ON CONFLICT
- Or use advisory locks for user creation

### 4. Add Pool Monitoring (apps/api/dependencies.py)
- Expose pool stats endpoint
- Add metrics for pool usage
- Add circuit breaker for exhaustion

## Metrics to Add

- `api.request.duration` (histogram)
- `api.error.count` (counter)
- `db.pool.size` (gauge)
- `db.pool.wait_time` (histogram)
- `agent.task.duration` (histogram)
- `agent.queue.depth` (gauge)

## Alerts to Configure

1. Error rate > 5% for 5 minutes
2. Database pool exhaustion
3. Worker queue depth > 1000
4. DLQ entries created
5. API p95 latency > 1s

---

**Full Report:** See `BACKEND_ARCHITECTURE_AUDIT.md`
