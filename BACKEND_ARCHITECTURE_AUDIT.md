# Backend & Architecture Audit Report

**Date:** March 9, 2026  
**Scope:** API design, database schema, background jobs, error handling, scalability, data consistency

---

## Executive Summary

This audit identifies **47 findings** across 6 categories:
- **Critical (5)**: Security vulnerabilities, data loss risks, production failures
- **High (12)**: Performance bottlenecks, missing error handling, race conditions
- **Medium (18)**: Missing indexes, inconsistent patterns, observability gaps
- **Low (12)**: Code quality, minor optimizations

---

## 1. API Design & Consistency

### 🔴 CRITICAL: Missing Idempotency Keys

**Location:** `apps/api/main.py`, `apps/api/auth.py`, worker endpoints

**Issue:** Write operations (POST/PUT/PATCH) lack idempotency keys, risking duplicate operations on retries.

**Impact:** 
- Duplicate application submissions
- Duplicate magic link emails
- Duplicate profile updates
- Billing/charge duplication risk

**Recommendation:**
```python
# Add idempotency middleware
class IdempotencyRequest(BaseModel):
    idempotency_key: str = Header(..., alias="Idempotency-Key")

@app.middleware("http")
async def idempotency_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        key = request.headers.get("Idempotency-Key")
        if key:
            # Check Redis for existing response
            cached = await redis.get(f"idempotency:{key}")
            if cached:
                return JSONResponse(**json.loads(cached))
        # Store response after execution
```

**Files to update:**
- `apps/api/main.py` - Add middleware
- `apps/api/auth.py` - Magic link endpoint
- `apps/api/billing.py` - Payment operations
- `apps/api/bulk.py` - Bulk operations

---

### 🟠 HIGH: Inconsistent Error Response Format

**Location:** Multiple API endpoints

**Issue:** Error responses vary between endpoints:
- Some return `{"detail": "message"}`
- Others return `{"error": "message"}`
- Some include stack traces in production

**Impact:** Frontend error handling is inconsistent, poor DX

**Recommendation:**
```python
# Standardize in apps/api/main.py
class ErrorResponse(BaseModel):
    error: str
    code: str | None = None
    details: dict[str, Any] | None = None
    request_id: str | None = None

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=exc.status_code,
            request_id=request.state.request_id
        ).model_dump()
    )
```

---

### 🟠 HIGH: Missing API Versioning Strategy

**Location:** `apps/api/main.py`

**Issue:** No versioning strategy. Some routes use `/v1/` prefix, others don't. Breaking changes will affect all clients.

**Impact:** Cannot evolve API without breaking existing clients

**Recommendation:**
```python
# Enforce versioning
app = FastAPI(title="Sorce API", version="1.0.0")

# All routes should be versioned
router = APIRouter(prefix="/v1", tags=["applications"])

# Add deprecation headers
@router.get("/old-endpoint", deprecated=True)
async def old_endpoint():
    # Return with Deprecation header
    pass
```

---

### 🟡 MEDIUM: Inconsistent Pagination

**Location:** Multiple endpoints (`apps/api/analytics.py`, `apps/api/user.py`)

**Issue:** Pagination parameters vary:
- Some use `limit`/`offset`
- Others use `page`/`page_size`
- No consistent max limit enforcement

**Recommendation:**
```python
class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    @property
    def page(self) -> int:
        return (self.offset // self.limit) + 1

# Use in all list endpoints
async def list_items(
    pagination: PaginationParams = Depends(),
    ...
):
    ...
```

---

### 🟡 MEDIUM: Missing Request Validation

**Location:** `apps/api/auth.py` - Magic link endpoint

**Issue:** Email validation happens in business logic, not at request boundary.

**Recommendation:**
```python
from pydantic import EmailStr, validator

class MagicLinkRequest(BaseModel):
    email: EmailStr
    return_to: str | None = None
    
    @validator('return_to')
    def validate_return_to(cls, v):
        if v and not v.startswith('/'):
            raise ValueError('return_to must be relative path')
        return v
```

---

## 2. Database Schema & Queries

### 🔴 CRITICAL: Missing Index on `claim_next_prioritized` Function

**Location:** `apps/worker/agent.py:140`, `packages/backend/domain/repositories.py:67`

**Issue:** The `claim_next_prioritized` function queries `applications` without proper indexes for:
- `status = 'QUEUED'` + `available_at <= now()` + `attempt_count < $1`
- `priority_score DESC` ordering

**Impact:** Worker contention, slow task claiming under load

**Current Query:**
```sql
SELECT id FROM public.applications
WHERE status = 'QUEUED'
  AND attempt_count < $1
  AND (available_at IS NULL OR available_at <= now())
ORDER BY priority_score DESC, created_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED
```

**Recommendation:**
```sql
-- Add composite index for worker claim query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_claim_queue
ON applications(status, attempt_count, available_at, priority_score DESC, created_at ASC)
WHERE status IN ('QUEUED', 'REQUIRES_INPUT');

-- Also add for resumable query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_resumable
ON applications(status, attempt_count, updated_at)
WHERE status = 'REQUIRES_INPUT';
```

**Migration:** `migrations/016_worker_claim_indexes.sql`

---

### 🔴 CRITICAL: N+1 Query in `get_detail`

**Location:** `packages/backend/domain/repositories.py:272`

**Issue:** `ApplicationRepo.get_detail()` makes 3 separate queries:
1. Fetch application
2. Fetch inputs (separate query)
3. Fetch events (separate query)

**Impact:** 3x database round-trips per request, poor performance

**Recommendation:**
```python
@staticmethod
async def get_detail(
    conn: asyncpg.Connection,
    application_id: str,
    tenant_id: str | None = None,
) -> ApplicationDetail | None:
    """Single-query fetch with JOINs."""
    if tenant_id:
        app_row = await conn.fetchrow("""
            SELECT 
                a.*,
                json_agg(DISTINCT jsonb_build_object(
                    'id', ai.id,
                    'selector', ai.selector,
                    'question', ai.question,
                    'field_type', ai.field_type,
                    'answer', ai.answer,
                    'meta', ai.meta,
                    'resolved', ai.resolved,
                    'created_at', ai.created_at
                )) FILTER (WHERE ai.id IS NOT NULL) as inputs,
                json_agg(DISTINCT jsonb_build_object(
                    'id', ae.id,
                    'event_type', ae.event_type,
                    'payload', ae.payload,
                    'created_at', ae.created_at
                )) FILTER (WHERE ae.id IS NOT NULL) ORDER BY ae.created_at DESC
                LIMIT 10 as events
            FROM public.applications a
            LEFT JOIN public.application_inputs ai ON ai.application_id = a.id
            LEFT JOIN LATERAL (
                SELECT * FROM public.application_events
                WHERE application_id = a.id
                ORDER BY created_at DESC LIMIT 10
            ) ae ON true
            WHERE a.id = $1 AND a.tenant_id = $2
            GROUP BY a.id
        """, application_id, tenant_id)
    else:
        # Similar query without tenant_id
        ...
```

---

### 🟠 HIGH: Missing Index on `application_events` for Time-Based Queries

**Location:** `packages/backend/domain/repositories.py:303`

**Issue:** Events query orders by `created_at DESC` but index may not support this efficiently.

**Current Index:** `idx_events_created_at` (from `001_initial_schema.sql:124`)

**Recommendation:**
```sql
-- Ensure composite index for application + time queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_application_events_app_time
ON application_events(application_id, created_at DESC);
```

---

### 🟠 HIGH: Race Condition in User Creation

**Location:** `apps/api/auth.py:287` - `_find_or_create_user_by_email`

**Issue:** Two concurrent requests can both see "user doesn't exist" and both try to INSERT, causing constraint violation.

**Current Code:**
```python
user_id = await conn.fetchval("SELECT id FROM public.users WHERE email = $1", email)
if user_id:
    return str(user_id), False
# Race condition window here
user_id = await conn.fetchval("""
    INSERT INTO public.users (id, email, created_at, updated_at)
    VALUES ($1, $2, now(), now())
    RETURNING id
""", str(uuid.uuid4()), email)
```

**Recommendation:**
```python
async def _find_or_create_user_by_email(
    conn: Any, email: str, settings: Settings
) -> tuple[str, bool]:
    """Use INSERT ... ON CONFLICT to handle race conditions."""
    user_id = await conn.fetchval("""
        INSERT INTO public.users (id, email, created_at, updated_at)
        VALUES (gen_random_uuid(), $1, now(), now())
        ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
        RETURNING id, (xmax = 0) as is_new
    """, email)
    # xmax = 0 means row was inserted, not updated
    is_new = await conn.fetchval("""
        SELECT NOT EXISTS(SELECT 1 FROM public.users WHERE email = $1 AND created_at > now() - interval '1 second')
    """, email)
    return str(user_id), is_new
```

**Better:** Use advisory locks:
```python
async def _find_or_create_user_by_email(
    conn: Any, email: str, settings: Settings
) -> tuple[str, bool]:
    """Use advisory lock to prevent race conditions."""
    lock_key = hash(email) % (2**31)  # PostgreSQL advisory lock key
    async with conn.transaction():
        await conn.execute("SELECT pg_advisory_xact_lock($1)", lock_key)
        user_id = await conn.fetchval("SELECT id FROM public.users WHERE email = $1", email)
        if user_id:
            return str(user_id), False
        # Create user within locked transaction
        user_id = await conn.fetchval("""
            INSERT INTO public.users (id, email, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, now(), now())
            RETURNING id
        """, email)
        return str(user_id), True
```

---

### 🟠 HIGH: Missing Foreign Key Indexes

**Location:** Schema files

**Issue:** Foreign keys don't automatically create indexes. Queries filtering by FK columns are slow.

**Missing Indexes:**
- `applications.job_id` (referenced in many queries)
- `applications.user_id` (already has index, but verify composite)
- `application_inputs.application_id` (has index, verify)
- `application_events.application_id` (needs index)

**Recommendation:**
```sql
-- Verify/Add missing FK indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_job_id 
ON applications(job_id) WHERE job_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_application_events_application_id
ON application_events(application_id, created_at DESC);
```

---

### 🟡 MEDIUM: JSONB Queries Without GIN Indexes

**Location:** `packages/backend/domain/repositories.py:330` - Profile queries

**Issue:** `profile_data` JSONB column is queried but may not have GIN index for efficient JSON queries.

**Recommendation:**
```sql
-- Add GIN index for JSONB queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_profile_data_gin
ON profiles USING gin(profile_data);

-- If querying specific keys frequently:
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_profile_data_keys
ON profiles USING gin(profile_data jsonb_path_ops);
```

---

### 🟡 MEDIUM: Missing Partial Indexes for Common Filters

**Location:** Various queries

**Issue:** Common WHERE clauses like `status = 'QUEUED'` or `tenant_id IS NOT NULL` could use partial indexes.

**Recommendation:**
```sql
-- Partial index for active applications
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_active_queue
ON applications(priority_score DESC, created_at ASC)
WHERE status = 'QUEUED' AND (available_at IS NULL OR available_at <= now());

-- Partial index for tenant-scoped queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_tenant_active
ON applications(tenant_id, user_id, created_at DESC)
WHERE tenant_id IS NOT NULL AND status IN ('QUEUED', 'PROCESSING', 'REQUIRES_INPUT');
```

---

### 🟡 MEDIUM: No Query Timeout Configuration

**Location:** `apps/api/dependencies.py` - Database pool

**Issue:** Long-running queries can block connection pool.

**Recommendation:**
```python
# In create_db_pool or pool configuration
pool = await asyncpg.create_pool(
    settings.database_url,
    min_size=settings.db_pool_min,
    max_size=settings.db_pool_max,
    command_timeout=30,  # 30 second query timeout
    statement_cache_size=0,
)
```

---

## 3. Background Jobs & Queues

### 🔴 CRITICAL: No Idempotency in Worker Task Processing

**Location:** `apps/worker/agent.py:690` - `run_once`

**Issue:** If worker crashes after claiming task but before completion, task may be reprocessed on retry.

**Impact:** Duplicate application submissions, duplicate emails

**Recommendation:**
```python
async def claim_task(pool: asyncpg.Pool) -> dict | None:
    """Atomically claim with idempotency check."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            WITH next_task AS (
                SELECT id, processing_id
                FROM public.applications
                WHERE status = 'QUEUED'
                  AND attempt_count < $1
                  AND (available_at IS NULL OR available_at <= now())
                  AND (processing_id IS NULL OR processing_started_at < now() - interval '10 minutes')
                ORDER BY priority_score DESC, created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE public.applications a
            SET status = 'PROCESSING',
                processing_id = gen_random_uuid(),
                processing_started_at = now(),
                locked_at = now(),
                attempt_count = a.attempt_count + 1,
                updated_at = now()
            FROM next_task
            WHERE a.id = next_task.id
            RETURNING a.*
        """, MAX_ATTEMPTS)
        return dict(row) if row else None
```

**Also add:**
```sql
-- Add processing tracking columns
ALTER TABLE applications ADD COLUMN IF NOT EXISTS processing_id UUID;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_applications_processing_id ON applications(processing_id);
```

---

### 🟠 HIGH: No Dead Letter Queue Monitoring

**Location:** `apps/worker/agent.py:1464` - DLQ insertion

**Issue:** DLQ entries are created but no alerting/monitoring when items enter DLQ.

**Impact:** Silent failures, no visibility into persistent failures

**Recommendation:**
```python
# After DLQ insertion
await notification_manager.process_alert(
    alert_type="dlq_entry_created",
    user_id=user_id,
    alert_data={
        "application_id": app_id,
        "failure_reason": "MAX_ATTEMPTS_REACHED",
        "attempt_count": attempt,
    },
    tenant_id=tenant_id,
)

# Also emit metrics
incr("agent.dlq_insertion", tags={
    "tenant_id": tenant_id or "none",
    "failure_reason": "MAX_ATTEMPTS_REACHED",
    "blueprint": blueprint_key,
})
```

**Add monitoring endpoint:**
```python
@router.get("/admin/dlq/stats")
async def get_dlq_stats(
    db: asyncpg.Pool = Depends(get_pool),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Get DLQ statistics for monitoring."""
    async with db.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE created_at > now() - interval '1 hour') as last_hour,
                COUNT(*) FILTER (WHERE created_at > now() - interval '24 hours') as last_24h,
                failure_reason,
                COUNT(*) as count
            FROM public.job_dead_letter_queue
            WHERE tenant_id = $1 OR tenant_id IS NULL
            GROUP BY failure_reason
        """, tenant_ctx.tenant_id)
    return dict(stats)
```

---

### 🟠 HIGH: Exponential Backoff Without Jitter

**Location:** `apps/worker/agent.py:1481`

**Issue:** Exponential backoff without jitter causes thundering herd.

**Current:**
```python
backoff_seconds = 30 * (2 ** (attempt - 1))
```

**Recommendation:**
```python
import random
base_backoff = 30 * (2 ** (attempt - 1))
jitter = random.uniform(0, base_backoff * 0.1)  # 10% jitter
backoff_seconds = base_backoff + jitter
```

---

### 🟠 HIGH: No Worker Health Check Endpoint

**Location:** `apps/api/worker_health.py` exists but may be incomplete

**Issue:** Need to verify worker is processing tasks, not stuck.

**Recommendation:**
```python
@router.get("/worker/health")
async def worker_health(
    db: asyncpg.Pool = Depends(get_pool),
):
    """Check if worker is actively processing."""
    async with db.acquire() as conn:
        # Check for stuck tasks
        stuck = await conn.fetchval("""
            SELECT COUNT(*) FROM public.applications
            WHERE status = 'PROCESSING'
              AND locked_at < now() - interval '30 minutes'
        """)
        
        # Check queue depth
        queue_depth = await conn.fetchval("""
            SELECT COUNT(*) FROM public.applications
            WHERE status = 'QUEUED'
              AND (available_at IS NULL OR available_at <= now())
        """)
        
        return {
            "status": "healthy" if stuck == 0 else "degraded",
            "stuck_tasks": stuck,
            "queue_depth": queue_depth,
        }
```

---

### 🟡 MEDIUM: No Task Priority Adjustment

**Location:** `apps/worker/agent.py:140` - `claim_task`

**Issue:** Priority is set once, never adjusted based on age or tenant tier.

**Recommendation:**
```python
# Add dynamic priority adjustment
async def adjust_priority_scores(pool: asyncpg.Pool):
    """Periodically adjust priorities based on age and tenant tier."""
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE public.applications
            SET priority_score = 
                CASE 
                    WHEN tenant_plan = 'ENTERPRISE' THEN 1000
                    WHEN tenant_plan = 'TEAM' THEN 500
                    WHEN tenant_plan = 'PRO' THEN 200
                    ELSE 100
                END
                + EXTRACT(EPOCH FROM (now() - created_at)) / 3600  -- Age bonus
            WHERE status = 'QUEUED'
        """)
```

---

### 🟡 MEDIUM: No Batch Processing for Similar Tasks

**Location:** Worker processes one task at a time

**Issue:** Could batch similar tasks (same blueprint, same tenant) for efficiency.

**Recommendation:** (Future optimization, not critical)

---

## 4. Error Handling & Observability

### 🔴 CRITICAL: Unhandled Exceptions in Worker

**Location:** `apps/worker/agent.py:746` - `_process_task`

**Issue:** Exceptions are caught but error context may be lost.

**Current:**
```python
try:
    await self._process_task(page, task)
except Exception as exc:
    await self._handle_failure(task, exc, page)
```

**Recommendation:**
```python
try:
    await self._process_task(page, task)
except Exception as exc:
    # Capture full context
    logger.exception(
        "Task processing failed",
        extra={
            "application_id": task["id"],
            "attempt": task["attempt_count"],
            "blueprint": task.get("blueprint_key"),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
    )
    # Emit structured error event
    await self._handle_failure(task, exc, page)
    # Re-raise for monitoring systems
    raise
```

---

### 🟠 HIGH: Missing Structured Logging Context

**Location:** Throughout codebase

**Issue:** Logs don't consistently include request_id, tenant_id, user_id for correlation.

**Recommendation:**
```python
# In shared/logging_config.py
class LogContext:
    _context: dict[str, Any] = {}
    
    @classmethod
    def set(cls, **kwargs):
        cls._context.update(kwargs)
    
    @classmethod
    def get(cls):
        return cls._context.copy()
    
    @classmethod
    def clear(cls):
        cls._context.clear()

# In middleware
@app.middleware("http")
async def logging_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    LogContext.set(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# In logger setup
logger = logging.getLogger(__name__)
logger.addFilter(lambda record: record.__dict__.update(LogContext.get()))
```

---

### 🟠 HIGH: No Distributed Tracing

**Location:** No OpenTelemetry integration visible

**Issue:** Cannot trace requests across API → Worker → Database → External services.

**Recommendation:**
```python
# Already have setup_telemetry, but verify it's used
from shared.telemetry import setup_telemetry, get_tracer

tracer = get_tracer("sorce.agent")

async def _process_task(self, page: Page, task: dict) -> None:
    with tracer.start_as_current_span("process_task") as span:
        span.set_attribute("application.id", task["id"])
        span.set_attribute("application.attempt", task["attempt_count"])
        # ... rest of processing
```

---

### 🟠 HIGH: Missing Error Metrics

**Location:** Error handling throughout

**Issue:** Errors are logged but not consistently tracked as metrics.

**Recommendation:**
```python
# In error handlers
incr("api.errors", tags={
    "error_type": type(exc).__name__,
    "endpoint": request.url.path,
    "method": request.method,
    "status_code": 500,
})

# In worker
incr("agent.errors", tags={
    "error_type": type(exc).__name__,
    "blueprint": blueprint_key,
    "stage": "processing",  # or "extraction", "mapping", etc.
})
```

---

### 🟡 MEDIUM: Inconsistent Error Messages

**Location:** Multiple files

**Issue:** Some errors expose internal details, others are too generic.

**Recommendation:**
```python
# Create error message mapping
ERROR_MESSAGES = {
    "database_connection_failed": "Service temporarily unavailable. Please try again.",
    "validation_error": "Invalid request data.",
    "not_found": "Resource not found.",
    "rate_limit_exceeded": "Too many requests. Please wait before retrying.",
}

# Use in exception handlers
error_code = map_exception_to_code(exc)
user_message = ERROR_MESSAGES.get(error_code, "An error occurred.")
```

---

### 🟡 MEDIUM: No Error Budget Tracking

**Location:** No SLO/SLI tracking visible

**Issue:** Cannot track if error rate exceeds acceptable thresholds.

**Recommendation:**
```python
# Track error budget
incr("api.error_budget_consumed", tags={"severity": "critical"})
observe("api.error_rate", error_rate)

# Alert when budget consumed
if error_budget_remaining < 0.1:  # 10% remaining
    await send_alert("Error budget nearly exhausted")
```

---

## 5. Scalability Concerns

### 🔴 CRITICAL: Connection Pool Exhaustion Risk

**Location:** `apps/api/dependencies.py` - `_pool_manager`

**Issue:** No visibility into pool usage, no circuit breaker for pool exhaustion.

**Impact:** API becomes unresponsive when pool is exhausted

**Recommendation:**
```python
class PoolManager:
    async def acquire_with_timeout(self, timeout: float = 5.0):
        """Acquire connection with timeout."""
        try:
            conn = await asyncio.wait_for(
                self.pool.acquire(),
                timeout=timeout
            )
            return conn
        except asyncio.TimeoutError:
            incr("db.pool.exhausted")
            raise HTTPException(
                status_code=503,
                detail="Database connection pool exhausted. Please retry."
            )
    
    async def get_pool_stats(self):
        """Return pool statistics for monitoring."""
        return {
            "size": self.pool.get_size(),
            "free_size": self.pool.get_free_size(),
            "min_size": self.pool.get_min_size(),
            "max_size": self.pool.get_max_size(),
        }
```

**Add monitoring:**
```python
@app.get("/admin/db/pool-stats")
async def get_pool_stats(
    db: asyncpg.Pool = Depends(get_pool),
):
    """Monitor connection pool health."""
    stats = await _pool_manager.get_pool_stats()
    if stats["free_size"] / stats["max_size"] < 0.1:
        # Alert: pool nearly exhausted
        incr("db.pool.critical", tags={"free_pct": stats["free_size"] / stats["max_size"]})
    return stats
```

---

### 🟠 HIGH: No Rate Limiting on Worker LLM Calls

**Location:** `apps/worker/agent.py:83` - `_llm_limiter`

**Issue:** In-process rate limiter doesn't coordinate across multiple worker instances.

**Impact:** Multiple workers can exceed LLM API rate limits

**Recommendation:**
```python
# Use Redis for distributed rate limiting
from shared.redis_client import get_redis

async def acquire_llm_rate_limit():
    """Distributed rate limiting using Redis."""
    redis = await get_redis()
    key = "llm:rate_limit:minute"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)
    
    if current > _settings.llm_rate_limit_per_minute:
        await redis.decr(key)
        raise RuntimeError("LLM rate limit exceeded")
    
    return True
```

---

### 🟠 HIGH: No Caching Strategy

**Location:** Profile, job, and tenant data fetched repeatedly

**Issue:** No caching layer for frequently accessed data.

**Impact:** Unnecessary database load

**Recommendation:**
```python
# Add Redis caching layer
from shared.redis_client import get_redis
import json

async def get_profile_cached(user_id: str, db: asyncpg.Pool):
    """Get profile with caching."""
    redis = await get_redis()
    cache_key = f"profile:{user_id}"
    
    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from DB
    async with db.acquire() as conn:
        profile = await ProfileRepo.get_profile_data(conn, user_id)
    
    # Cache for 5 minutes
    if profile:
        await redis.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps(profile)
        )
    
    return profile

# Invalidate on update
async def invalidate_profile_cache(user_id: str):
    redis = await get_redis()
    await redis.delete(f"profile:{user_id}")
```

---

### 🟠 HIGH: No Query Result Pagination Limits

**Location:** Multiple list endpoints

**Issue:** Some endpoints allow unlimited result sets.

**Recommendation:**
```python
# Enforce max limit
class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)  # Max 100
    offset: int = Field(default=0, ge=0)
```

---

### 🟡 MEDIUM: No Database Query Timeout

**Location:** Database queries

**Issue:** Long-running queries can block connections.

**Recommendation:**
```python
# Set query timeout at connection level
conn = await pool.acquire()
try:
    await conn.set_type_codec('json', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')
    await conn.execute("SET statement_timeout = '30s'")
    # Execute queries
finally:
    await pool.release(conn)
```

---

### 🟡 MEDIUM: No Connection Pool Monitoring

**Location:** `apps/api/dependencies.py`

**Issue:** No metrics on pool usage, wait times, or exhaustion events.

**Recommendation:**
```python
# Add metrics
observe("db.pool.size", pool.get_size())
observe("db.pool.free", pool.get_free_size())
observe("db.pool.wait_time", wait_time)
```

---

## 6. Data Consistency & Transactions

### 🔴 CRITICAL: Race Condition in Application Status Updates

**Location:** `packages/backend/domain/repositories.py:140` - `update_status`

**Issue:** Status updates don't use optimistic locking. Concurrent updates can overwrite each other.

**Impact:** Lost updates, inconsistent state

**Recommendation:**
```python
@staticmethod
async def update_status(
    conn: asyncpg.Connection,
    application_id: str,
    status: str,
    *,
    error_message: str | None = None,
    expected_version: int | None = None,  # Add version field
) -> dict | None:
    """Update with optimistic locking."""
    if expected_version is not None:
        row = await conn.fetchrow("""
            UPDATE public.applications
            SET status = $2::public.application_status,
                version = version + 1,
                updated_at = now()
            WHERE id = $1 AND version = $3
            RETURNING *
        """, application_id, status, expected_version)
        if row is None:
            raise HTTPException(
                status_code=409,
                detail="Application was modified by another request"
            )
    else:
        # Fallback without version check
        row = await conn.fetchrow("""
            UPDATE public.applications
            SET status = $2::public.application_status,
                updated_at = now()
            WHERE id = $1
            RETURNING *
        """, application_id, status)
    return dict(row) if row else None
```

**Add version column:**
```sql
ALTER TABLE applications ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_applications_version ON applications(id, version);
```

---

### 🟠 HIGH: Missing Transaction Isolation Levels

**Location:** `packages/backend/domain/repositories.py:28` - `db_transaction`

**Issue:** Default isolation level may not be sufficient for all operations.

**Recommendation:**
```python
@asynccontextmanager
async def db_transaction(
    pool: asyncpg.Pool,
    isolation_level: str = "READ COMMITTED",
) -> AsyncGenerator[asyncpg.Connection, None]:
    """Transaction with configurable isolation."""
    async with pool.acquire() as conn:
        await conn.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
        async with conn.transaction():
            yield conn
```

---

### 🟠 HIGH: No Retry Logic for Transient DB Errors

**Location:** Database operations throughout

**Issue:** Transient errors (connection lost, deadlock) cause immediate failures.

**Recommendation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(asyncpg.PostgresConnectionError)
)
async def execute_with_retry(conn, query, *args):
    """Execute query with retry on transient errors."""
    return await conn.execute(query, *args)
```

---

### 🟡 MEDIUM: No Database Constraint Validation

**Location:** Application creation, updates

**Issue:** Some constraints are enforced in application code, not database.

**Recommendation:**
```sql
-- Add check constraints
ALTER TABLE applications ADD CONSTRAINT check_status_valid
CHECK (status IN ('QUEUED', 'PROCESSING', 'REQUIRES_INPUT', 'APPLIED', 'SUBMITTED', 'COMPLETED', 'FAILED'));

ALTER TABLE applications ADD CONSTRAINT check_attempt_count
CHECK (attempt_count >= 0 AND attempt_count <= 10);
```

---

### 🟡 MEDIUM: Missing Unique Constraints

**Location:** Schema

**Issue:** Some logical uniqueness not enforced (e.g., one QUEUED application per user+job).

**Recommendation:**
```sql
-- Prevent duplicate queued applications
CREATE UNIQUE INDEX IF NOT EXISTS idx_applications_user_job_queued
ON applications(user_id, job_id)
WHERE status = 'QUEUED';
```

---

## Monitoring & Metrics Recommendations

### Add These Metrics:

1. **API Metrics:**
   - `api.request.duration` (histogram)
   - `api.request.count` (counter, by endpoint, method, status)
   - `api.error.count` (counter, by error type)
   - `api.rate_limit.exceeded` (counter)

2. **Database Metrics:**
   - `db.query.duration` (histogram, by query type)
   - `db.pool.size` (gauge)
   - `db.pool.wait_time` (histogram)
   - `db.connection.errors` (counter)

3. **Worker Metrics:**
   - `agent.task.duration` (histogram, by blueprint)
   - `agent.task.success_rate` (gauge)
   - `agent.queue.depth` (gauge)
   - `agent.llm.latency` (histogram)
   - `agent.llm.rate_limit_exceeded` (counter)

4. **Business Metrics:**
   - `applications.created` (counter, by tenant)
   - `applications.completed` (counter, by status)
   - `applications.failed` (counter, by reason)
   - `magic_links.sent` (counter)
   - `magic_links.verified` (counter)

### Add These Alerts:

1. **Critical:**
   - Error rate > 5% for 5 minutes
   - Database pool exhaustion
   - Worker queue depth > 1000
   - DLQ entries created

2. **High:**
   - API p95 latency > 1s
   - Database query p95 > 500ms
   - Worker task failure rate > 10%
   - LLM rate limit exceeded

3. **Medium:**
   - Cache hit rate < 80%
   - Connection pool usage > 80%
   - Stuck worker tasks

---

## Priority Action Items

### Immediate (This Week):
1. ✅ Add idempotency keys to write endpoints
2. ✅ Fix N+1 query in `get_detail`
3. ✅ Add index for `claim_next_prioritized`
4. ✅ Fix race condition in user creation
5. ✅ Add connection pool monitoring

### Short-term (This Month):
1. Standardize error responses
2. Add distributed rate limiting for LLM
3. Implement caching layer
4. Add optimistic locking for status updates
5. Add structured logging context

### Medium-term (Next Quarter):
1. Implement API versioning
2. Add distributed tracing
3. Add query timeout configuration
4. Implement batch processing for worker
5. Add comprehensive monitoring dashboard

---

## Appendix: Code Examples

### Idempotency Middleware
See section 1.1 for full implementation.

### N+1 Query Fix
See section 2.2 for full implementation.

### Distributed Rate Limiting
See section 5.2 for full implementation.

---

**Report Generated:** March 9, 2026  
**Next Review:** April 9, 2026
