"""
Part 3: API and Worker Coordination (FastAPI)

Hardened endpoints with:
  - Canonical profile normalization on resume parse
  - Event emission on every user-facing state change
  - resolved flag management on application_inputs
  - Debug endpoint for observability
  - Clean separation: routes → business logic → DB helpers

Worker coordination contract:
  - API NEVER calls the worker directly.
  - Worker discovers work exclusively via DB polling (status = QUEUED).
  - API sets status back to QUEUED after user answers; worker picks it up.
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Path,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.domain.analytics_events import (
    APPLICATION_STATUS_CHANGED,
    emit_analytics_event,
)
from backend.domain.debug_schema import debug_alter_stmts, debug_auth_shim, debug_critical_tables
from backend.domain.models import (
    CanonicalProfile,
    ErrorDetail,
    ErrorResponse,
)
from backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    InputRepo,
    db_transaction,
)
from backend.domain.resume import process_resume_upload
from backend.domain.tenant import (
    TenantContext,
    resolve_tenant_context,
)
from shared.config import Environment, get_settings
from shared.logging_config import LogContext, get_logger, setup_logging
from shared.metrics import dump as metrics_dump
from shared.metrics import incr
from shared.middleware import setup_csrf_middleware, setup_request_id_middleware
from shared.telemetry import setup_telemetry
from shared.redis_client import get_redis, close_redis

# ---------------------------------------------------------------------------
# Configuration (loaded from shared.config)
# ---------------------------------------------------------------------------
_settings = get_settings()

setup_logging(
    env=_settings.env.value,
    log_level=_settings.log_level,
    log_json=_settings.log_json,
)

logger = get_logger("sorce.api")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await _pool_manager.initialize()
    # Initialize Redis (optional, but good to fail fast if config is bad)
    if _settings.redis_url:
        try:
            r = await get_redis()
            await r.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    else:
        logger.info("Redis disabled (REDIS_URL not set)")

    yield
    # Shutdown
    await close_redis()
    await _pool_manager.close()

app = FastAPI(title="Sorce API", version="0.4.0", lifespan=lifespan)

# OpenTelemetry instrumentation
setup_telemetry("sorce-api", app)

app.add_middleware(
    CORSMiddleware,
    # Environment-aware origins - localhost only in development
    allow_origins=[o for o in {
        "https://sorce-web.onrender.com",
        "https://sorce-admin.onrender.com",
        _settings.app_base_url.rstrip("/"),
        "https://jobhuntin.com",
        "https://app.jobhuntin.com",
        # Include localhost ONLY in non-production environments
        *(["http://localhost:5173", "http://localhost:3000"] if _settings.env.value != "prod" else []),
    } if o],
    allow_credentials=True,
    # Explicit method list instead of wildcard
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    # Explicit header list instead of wildcard
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
    expose_headers=["X-Request-ID"],
    max_age=3600,  # Cache preflight for 1 hour to reduce OPTIONS requests
)

# Add Request ID middleware for distributed tracing
setup_request_id_middleware(app)

from shared.middleware import get_client_ip, setup_security_headers
from shared.metrics import get_rate_limiter

# ---------------------------------------------------------------------------  
# Security Headers Middleware
# ---------------------------------------------------------------------------
setup_security_headers(app)

# ---------------------------------------------------------------------------  
# Rate Limiting Middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware for API endpoints."""
    # Skip rate limiting for health checks and static files
    if request.url.path in ["/health", "/healthz"] or request.url.path.startswith("/static"):
        return await call_next(request)
    
    # Get client identifier (IP address)
    client_ip = get_client_ip(request)
    
    # Get rate limiter for this client
    limiter = get_rate_limiter(f"api:{client_ip}", max_calls=100, window_seconds=60)  # 100 requests per minute
    
    if not await limiter.acquire():
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded. Please try again later."
        )
    
    return await call_next(request)


# ---------------------------------------------------------------------------
# Mount sub-routers (billing, admin, export – added in Parts 2-4)
# ---------------------------------------------------------------------------

def _mount_sub_routers() -> None:
    """Deferred import to avoid circular deps; called after deps are defined.

    Uses app.dependency_overrides so that Depends() references captured at
    route-definition time are correctly replaced at request time.
    """
    import api.billing as billing_mod
    app.dependency_overrides[billing_mod._get_pool] = get_pool
    app.dependency_overrides[billing_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(billing_mod.router)

    import api.admin as admin_mod
    app.dependency_overrides[admin_mod._get_pool] = get_pool
    app.dependency_overrides[admin_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[admin_mod._get_admin_user_id] = get_current_user_id
    app.include_router(admin_mod.router)

    import api.auth as auth_mod
    app.dependency_overrides[auth_mod._get_pool] = get_pool
    app.include_router(auth_mod.router)

    import api.export as export_mod
    app.dependency_overrides[export_mod._get_pool] = get_pool
    app.dependency_overrides[export_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(export_mod.router)

    import api.analytics as analytics_mod
    app.dependency_overrides[analytics_mod._get_pool] = get_pool
    app.dependency_overrides[analytics_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[analytics_mod._get_admin_user_id] = get_current_user_id
    app.include_router(analytics_mod.router)

    import api.growth as growth_mod
    app.dependency_overrides[growth_mod._get_pool] = get_pool
    app.dependency_overrides[growth_mod._get_user_id] = get_current_user_id
    app.dependency_overrides[growth_mod._get_admin_user_id] = get_current_user_id
    app.include_router(growth_mod.router)

    import api.sso as sso_mod
    app.dependency_overrides[sso_mod._get_pool] = get_pool
    app.dependency_overrides[sso_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(sso_mod.router)

    import api.bulk as bulk_mod
    app.dependency_overrides[bulk_mod._get_pool] = get_pool
    app.dependency_overrides[bulk_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(bulk_mod.router)

    import api.marketplace as marketplace_mod
    app.dependency_overrides[marketplace_mod._get_pool] = get_pool
    app.dependency_overrides[marketplace_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(marketplace_mod.router)

    import api_v2.router as api_v2_mod
    app.dependency_overrides[api_v2_mod._get_pool] = get_pool
    app.include_router(api_v2_mod.router)

    import partners.university.router as uni_mod
    from partners.university.router import router as uni_router
    app.dependency_overrides[uni_mod._get_pool] = get_pool
    app.dependency_overrides[uni_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(uni_router)

    import api.developer as dev_mod
    app.dependency_overrides[dev_mod._get_pool] = get_pool
    app.dependency_overrides[dev_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(dev_mod.router)

    import api.user as user_mod
    app.dependency_overrides[user_mod._get_pool] = get_pool
    app.dependency_overrides[user_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(user_mod.router)

    import api.og as og_mod
    app.include_router(og_mod.router)

    # AI Suggestions for smart onboarding
    import api.ai as ai_mod
    app.dependency_overrides[ai_mod._get_pool] = get_pool
    app.dependency_overrides[ai_mod._get_user_id] = get_current_user_id
    app.include_router(ai_mod.router)

# NOTE: _mount_sub_routers() is called at the bottom of this file,
# after get_pool and get_tenant_context are defined.

# ---------------------------------------------------------------------------
# Database pool lifecycle
# ---------------------------------------------------------------------------
class DatabasePoolManager:
    """Manages database pool lifecycle without global state."""

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None
        self._read_pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise HTTPException(status_code=503, detail="Database pool not available")
        return self._pool

    @property
    def read_pool(self) -> asyncpg.Pool:
        """Return the read replica pool if available, otherwise the primary pool."""
        if self._read_pool:
            return self._read_pool
        return self.pool

    async def initialize(self) -> None:
        """Initialize the database pool on startup."""
        s = get_settings()
        from backend.blueprints.registry import load_default_blueprints
        enabled = [slug.strip() for slug in s.enabled_blueprints.split(",") if slug.strip()]
        load_default_blueprints(enabled_slugs=enabled or None)

        ssl_arg = self._get_ssl_config(s)

        # Resolve the DB hostname to IPv4 to avoid [Errno 101] on Render (no IPv6).
        from shared.db import resolve_dsn_ipv4
        db_dsn = resolve_dsn_ipv4(s.database_url)

        for attempt in range(1, 4):
            try:
                self._pool = await asyncpg.create_pool(
                    db_dsn, min_size=s.db_pool_min, max_size=s.db_pool_max,
                    ssl=ssl_arg,
                    statement_cache_size=0,
                )
                logger.info("Database pool created (env=%s)", s.env.value)
                break
            except asyncpg.PostgresError as exc:
                # Provide more helpful error messages for common issues
                error_msg = str(exc)
                if "Tenant or user not found" in error_msg or "password authentication failed" in error_msg:
                    logger.warning(
                        "DB pool attempt %d/3 failed: %s. "
                        "This usually means DATABASE_URL credentials are incorrect. "
                        "Check that DB_USER, DB_PASSWORD, and DB_NAME match your Supabase project.",
                        attempt, exc
                    )
                elif "connection refused" in error_msg.lower() or "could not connect" in error_msg.lower():
                    logger.warning(
                        "DB pool attempt %d/3 failed: %s. "
                        "Check that the database host is accessible and the port is correct.",
                        attempt, exc
                    )
                else:
                    logger.warning("DB pool attempt %d/3 failed: %s", attempt, exc)
                if attempt < 3:
                    import asyncio
                    await asyncio.sleep(3 * attempt)
            except Exception as exc:
                logger.error("Unexpected error creating DB pool: %s", exc)
                raise
        else:
            logger.error(
                "Could not create DB pool after 3 attempts. "
                "The application will start in degraded mode without database connectivity. "
                "To fix this, verify your DATABASE_URL environment variable in Render dashboard."
            )
            # Do not raise RuntimeError, allow app to start in degraded mode
            # raise RuntimeError("Failed to initialize database pool")

        await self._run_migrations()

        # Initialize read replica if configured
        if s.read_replica_url and s.read_replica_url != s.database_url:
            read_dsn = resolve_dsn_ipv4(s.read_replica_url)
            
            try:
                self._read_pool = await asyncpg.create_pool(
                    read_dsn, min_size=s.db_pool_min, max_size=s.db_pool_max,
                    ssl=ssl_arg,
                    statement_cache_size=0,
                )
                logger.info("Read replica pool initialized")
            except Exception as exc:
                logger.warning("Failed to initialize read replica (falling back to primary): %s", exc)

    async def _run_migrations(self) -> None:
        """Run auto-migrations if needed."""
        if self._pool is None:
            return

        try:
            async with self._pool.acquire() as conn:
                has_tenants = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='tenants')"
                )
                if not has_tenants:
                    logger.info("Running auto-migration (tenants table missing)...")
                    import pathlib
                    base = pathlib.Path(__file__).resolve().parent.parent
                    from backend.domain.migrations import run_migrations
                    await run_migrations(conn, base)
        except asyncpg.PostgresError as exc:
            logger.warning("Auto-migration check failed (DB error): %s", exc)
        except Exception as exc:
            logger.warning("Auto-migration check failed: %s", exc)

    @staticmethod
    def _get_ssl_config(settings: Any) -> Any:
        """Get SSL config for database connection"""
        if not settings.database_url:
            return False
            
        # Render and many cloud databases require SSL/TLS connections
        import ssl
        return ssl.create_default_context()

    async def close(self) -> None:
        """Close the database pool on shutdown."""
        if self._pool:
            await self._pool.close()
            self._pool = None
        if self._read_pool:
            await self._read_pool.close()
            self._read_pool = None


# Global pool manager instance
_pool_manager = DatabasePoolManager()


# ---------------------------------------------------------------------------
# Standard error envelope handler
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return all HTTP errors in the standard ErrorResponse envelope."""
    body = ErrorResponse(
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        )
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


# Safety net for unhandled exceptions (500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions to prevent stack trace leaks in production."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # In local dev, we might want to see the error, but standard is to hide it.
    # FastAPI usually prints to console anyway.
    
    if _settings.env == Environment.LOCAL:
        msg = f"Internal Server Error: {str(exc)}"
    else:
        msg = "Internal Server Error"
        
    body = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message=msg,
        )
    )
    return JSONResponse(status_code=500, content=body.model_dump())




# ---------------------------------------------------------------------------
# Auth dependency – extract user_id from Supabase JWT
# ---------------------------------------------------------------------------

async def get_current_user_id(authorization: str = Header(...)) -> str:
    """
    Decode a JWT and return the `sub` claim as user_id.
    """
    import jwt as pyjwt

    s = get_settings()
    if not s.jwt_secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")

    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(
            token, s.jwt_secret, algorithms=["HS256"], audience="authenticated"
        )
        user_id: str = payload["sub"]
        return user_id
    except pyjwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Token error: {exc}")


async def get_pool() -> asyncpg.Pool:
    """Dependency for getting the primary database pool."""
    return _pool_manager.pool


async def get_read_pool() -> asyncpg.Pool:
    """Dependency for getting a read-replica pool if available."""
    return _pool_manager.read_pool


# ---------------------------------------------------------------------------
# Tenant context dependency
# ---------------------------------------------------------------------------

async def get_tenant_context(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> TenantContext:
    """Resolve TenantContext from JWT user_id. Auto-provisions FREE tenant if needed."""
    async with db.acquire() as conn:
        ctx = await resolve_tenant_context(conn, user_id)
    LogContext.set(tenant_id=ctx.tenant_id, user_id=ctx.user_id)
    return ctx


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ResumeParseResponse(BaseModel):
    user_id: str
    profile: CanonicalProfile
    resume_url: str | None = None


class AnswerItem(BaseModel):
    input_id: str
    answer: str


class ResumeTaskRequest(BaseModel):
    application_id: str
    answers: list[AnswerItem]


class ApplicationInputOut(BaseModel):
    id: str
    selector: str
    question: str
    field_type: str
    answer: str | None
    resolved: bool
    meta: dict[str, Any] | None = None


class ResumeTaskResponse(BaseModel):
    application_id: str
    status: str
    message: str
    unresolved_inputs: list[ApplicationInputOut]


class ApplicationDetailResponse(BaseModel):
    application: dict[str, Any]
    inputs: list[dict[str, Any]]
    events: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# M5: Answer Memory (Smart Pre-Fill) + User Dashboard
# ---------------------------------------------------------------------------

class SaveAnswerRequest(BaseModel):
    field_label: str
    field_type: str = "text"
    answer_value: str


@app.get("/me/answer-memory")
async def get_answer_memory(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Get memorized answers for smart pre-fill."""
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """SELECT field_label, field_type, answer_value, use_count, last_used_at
               FROM public.answer_memory WHERE user_id = $1
               ORDER BY use_count DESC, last_used_at DESC LIMIT 200""",
            user_id,
        )
    return [dict(r) for r in rows]


@app.post("/me/answer-memory")
async def save_answer_memory(
    body: SaveAnswerRequest,
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, str]:
    """Save an answer for future smart pre-fill."""
    async with db.acquire() as conn:
        await conn.execute(
            """INSERT INTO public.answer_memory (user_id, field_label, field_type, answer_value)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (user_id, field_label)
               DO UPDATE SET answer_value = $4, use_count = answer_memory.use_count + 1,
                             last_used_at = now()""",
            user_id, body.field_label, body.field_type, body.answer_value,
        )
    return {"status": "saved"}


@app.get("/me/dashboard")
async def user_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """User dashboard data for mobile v3 home screen + widget."""
    async with db.acquire() as conn:
        counts = await conn.fetchrow(
            """SELECT
                COUNT(*) FILTER (WHERE status IN ('QUEUED','PROCESSING'))::int AS active_count,
                COUNT(*) FILTER (WHERE status = 'REQUIRES_INPUT')::int AS hold_count,
                COUNT(*) FILTER (WHERE status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED')
                                 AND updated_at::date = CURRENT_DATE)::int AS completed_today,
                COUNT(*) FILTER (WHERE status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED')
                                 AND updated_at >= date_trunc('week', now()))::int AS completed_week,
                COUNT(*)::int AS total_all_time
               FROM public.applications WHERE user_id = $1""",
            user_id,
        )
        recent = await conn.fetch(
            """SELECT a.id, j.title AS job_title, a.status::text, a.updated_at
               FROM public.applications a
               LEFT JOIN public.jobs j ON j.id = a.job_id
               WHERE a.user_id = $1
               ORDER BY a.updated_at DESC LIMIT 10""",
            user_id,
        )

    return {
        **(dict(counts) if counts else {"active_count": 0, "hold_count": 0, "completed_today": 0, "completed_week": 0, "total_all_time": 0}),
        "recent": [dict(r) for r in recent],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

# -- 1. Resume Parse ---------------------------------------------------

@app.post("/webhook/resume_parse", response_model=ResumeParseResponse)
async def resume_parse(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> ResumeParseResponse:
    """Upload PDF → extract text → LLM parse → normalize → upsert profile."""
    user_id = ctx.user_id
    incr("api.resume_parse.requests", tags={"tenant_id": ctx.tenant_id})
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    from shared.config import get_settings as _get_settings
    _s = _get_settings()
    # Pre-check Content-Length header to reject before reading body into memory
    if file.size and file.size > _s.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_s.max_upload_size_bytes // 1_048_576} MB",
        )
    pdf_bytes = await file.read()
    if len(pdf_bytes) > _s.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_s.max_upload_size_bytes // 1_048_576} MB",
        )

    resume_url, canonical = await process_resume_upload(
        user_id=user_id,
        tenant_id=ctx.tenant_id,
        pdf_bytes=pdf_bytes,
        db_pool=db,
    )

    return ResumeParseResponse(
        user_id=user_id,
        profile=canonical,
        resume_url=resume_url,
    )


# -- 2. Resume Task (answer hold questions) ----------------------------

@app.post("/agent/resume_task", response_model=ResumeTaskResponse)
async def resume_task(
    body: ResumeTaskRequest,
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> ResumeTaskResponse:
    """
    User answers hold questions → update inputs → emit events → re-queue.
    """
    incr("api.resume_task.requests", tags={"tenant_id": ctx.tenant_id})
    # Verify ownership + tenant scope
    async with db.acquire() as conn:
        app_row = await ApplicationRepo.get_by_id_and_user(
            conn, body.application_id, ctx.user_id, tenant_id=ctx.tenant_id
        )
    if app_row is None:
        raise HTTPException(status_code=404, detail="Application not found or not owned by user")

    if app_row["status"] not in ("REQUIRES_INPUT",):
        raise HTTPException(
            status_code=409,
            detail=f"Application status is '{app_row['status']}', expected REQUIRES_INPUT",
        )

    async with db_transaction(db) as conn:
        # Update each answer and mark resolved
        await InputRepo.update_answers(
            conn,
            [{"input_id": a.input_id, "answer": a.answer} for a in body.answers],
        )

        # Emit USER_ANSWERED event per answer
        for a in body.answers:
            await EventRepo.emit(conn, body.application_id, "USER_ANSWERED", {
                "input_id": a.input_id,
                "answer": a.answer,
            }, tenant_id=ctx.tenant_id)

        # Re-queue so the worker picks it up
        updated = await ApplicationRepo.update_status(conn, body.application_id, "QUEUED")
        if updated is None:
            raise HTTPException(status_code=404, detail="Application not found")

        # Emit RETRY_SCHEDULED
        await EventRepo.emit(conn, body.application_id, "RETRY_SCHEDULED", {
            "answered_count": len(body.answers),
        }, tenant_id=ctx.tenant_id)

        # Fetch remaining unresolved inputs for the response
        remaining = await InputRepo.get_unresolved(conn, body.application_id)

    # Server-side analytics: status changed
    await emit_analytics_event(
        db, APPLICATION_STATUS_CHANGED,
        tenant_id=ctx.tenant_id, user_id=ctx.user_id,
        properties={
            "application_id": body.application_id,
            "from_status": "REQUIRES_INPUT",
            "to_status": "QUEUED",
        },
    )

    # Optional: nudge (no-op with polling; placeholder for pg_notify)
    background_tasks.add_task(_nudge_worker, body.application_id)

    return ResumeTaskResponse(
        application_id=body.application_id,
        status=str(updated["status"]),
        message="Answers saved; application re-queued for the agent.",
        unresolved_inputs=[
            ApplicationInputOut(
                id=str(r["id"]),
                selector=r["selector"],
                question=r["question"],
                field_type=r["field_type"],
                answer=r["answer"],
                resolved=r["resolved"],
                meta=json.loads(r["meta"]) if isinstance(r["meta"], str) else r.get("meta"),
            )
            for r in remaining
        ],
    )


async def _nudge_worker(application_id: str) -> None:
    """Placeholder for pg_notify or similar push. Worker polls regardless."""
    logger.info("Nudge: application %s re-queued", application_id)


# -- 3. Debug endpoint -------------------------------------------------

@app.get("/applications/{application_id}", response_model=ApplicationDetailResponse)
async def get_application_detail(
    application_id: str = Path(...),
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> ApplicationDetailResponse:
    """
    Application detail endpoint scoped to the requesting user's tenant.
    """
    from shared.validators import validate_uuid
    validate_uuid(application_id, "application_id")
    async with db.acquire() as conn:
        detail = await ApplicationRepo.get_detail(conn, application_id, tenant_id=ctx.tenant_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Application not found")

    serialized = detail.to_serializable()
    return ApplicationDetailResponse(**serialized)


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/healthz")
async def healthz(
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """Deep health check: pings DB and returns env + metrics summary."""
    from shared.circuit_breaker import get_all_circuit_breaker_statuses
    
    s = get_settings()
    db_ok = False
    try:
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception:
        pass

    # Get circuit breaker statuses
    circuit_breakers = get_all_circuit_breaker_statuses()
    cb_status = {cb["name"]: cb["state"] for cb in circuit_breakers}
    any_open = any(cb["state"] == "open" for cb in circuit_breakers)

    status = "ok" if db_ok and not any_open else "degraded"
    return {
        "status": status,
        "env": s.env.value,
        "db": "ok" if db_ok else "unreachable",
        "circuit_breakers": cb_status,
        "metrics": metrics_dump(),
    }


# ---------------------------------------------------------------------------
# Mount sub-routers (must be after all dependencies are defined)
# ---------------------------------------------------------------------------
_mount_sub_routers()
