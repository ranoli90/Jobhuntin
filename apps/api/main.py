"""Part 3: API and Worker Coordination (FastAPI).

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

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import json
import mimetypes
import os
import re
from typing import Any

import asyncpg
import jwt as pyjwt
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi import Path as FastAPIPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from packages.backend.domain.agent_improvements import create_agent_improvements_manager
from packages.backend.domain.analytics_events import (
    APPLICATION_STATUS_CHANGED,
    emit_analytics_event,
)
from packages.backend.domain.models import CanonicalProfile
from packages.backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    InputRepo,
    JobRepo,
    db_transaction,
)
from packages.backend.domain.resume import process_resume_upload
from packages.backend.domain.tenant import TenantContext, resolve_tenant_context
from shared.config import Environment, get_settings
from shared.logging_config import LogContext, get_logger, setup_logging
from shared.metrics import incr
from shared.middleware import setup_csrf_middleware, setup_request_id_middleware
from shared.redis_client import close_redis, get_redis
from shared.storage import get_storage_service
from shared.telemetry import setup_telemetry
from shared.validators import validate_uuid

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

if _settings.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=_settings.sentry_dsn,
            environment=_settings.sentry_environment or _settings.env.value,
            traces_sample_rate=_settings.sentry_traces_sample_rate,
            integrations=[FastApiIntegration()],
        )
        logger.info(f"Sentry initialized for {_settings.env.value}")
    except ImportError:
        logger.warning("sentry-sdk not installed - error tracking disabled")

from contextlib import asynccontextmanager

from api.dependencies import _pool_manager, get_current_user_id, get_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not _settings.jwt_secret:
        if _settings.env == Environment.PROD:
            logger.critical("JWT_SECRET missing in PROD. Aborting startup.")
            raise RuntimeError("JWT_SECRET must be set in production")
        logger.warning("JWT_SECRET not set. Authentication will fail.")

    await _pool_manager.initialize()
    # Initialize Redis (optional, but good to fail fast if config is bad)
    if _settings.redis_url:
        try:
            r = await get_redis()
            await r.ping()  # type: ignore[misc]
            is_internal = (
                "red-" in _settings.redis_url
                and ".render.com" not in _settings.redis_url
            )
            url_type = "internal" if is_internal else "external"
            logger.info(f"Redis connected ({url_type})")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    else:
        if _settings.env == Environment.PROD:
            logger.critical(
                "REDIS_URL not set in production. Magic-link token replay prevention "
                "uses in-memory store which is unsafe for multi-instance deployments. "
                "Set REDIS_URL for production."
            )
            raise RuntimeError(
                "REDIS_URL must be set in production for secure magic-link auth. "
                "In-memory token replay prevention is not safe across multiple workers."
            )
        logger.info("Redis disabled (REDIS_URL not set)")

    yield
    # Shutdown
    await close_redis()
    await _pool_manager.close()


app = FastAPI(
    title="Sorce API",
    version="0.4.0",
    lifespan=lifespan,
    description="""
AI-powered job application automation platform API.

## Authentication
All endpoints require Bearer token authentication via the Authorization header.

## Rate Limits
- FREE tier: 60 requests/minute
- PRO tier: 200 requests/minute
- TEAM tier: 500 requests/minute
- ENTERPRISE tier: Unlimited

## Response Codes
- 200: Success
- 400: Bad Request (validation error)
- 401: Unauthorized
- 403: Forbidden (tenant limit exceeded)
- 404: Not Found
- 429: Too Many Requests (rate limited)
- 500: Internal Server Error
""",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# OpenTelemetry instrumentation
setup_telemetry("sorce-api", app)

CORS_ORIGINS = [
    o
    for o in {
        "https://sorce-web.onrender.com",
        "https://sorce-admin.onrender.com",
        "https://sorce-api.onrender.com",
        _settings.app_base_url.rstrip("/"),
        "https://jobhuntin.com",
        "https://app.jobhuntin.com",
        *(
            ["http://localhost:5173", "http://localhost:3000"]
            if _settings.env.value != "prod"
            else []
        ),
    }
    if o
]

app.state.cors_origins = CORS_ORIGINS

# ---------------------------------------------------------------------------
# IMPORTANT: Middleware executes in REVERSE order of registration.
# CORS MUST be registered LAST so it executes FIRST (handles OPTIONS preflight).
# ---------------------------------------------------------------------------

# Add Request ID middleware for distributed tracing
setup_request_id_middleware(app)

from shared.metrics import get_rate_limiter
from shared.middleware import get_client_ip, setup_security_headers

# ---------------------------------------------------------------------------
# CSRF Protection Middleware
# ---------------------------------------------------------------------------
# SECURITY: Enable CSRF protection for all non-exempt endpoints
setup_csrf_middleware(app, _settings.csrf_secret)

# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
setup_security_headers(app)

# ---------------------------------------------------------------------------
# Rate Limiting Middleware (Tenant-aware)
# ---------------------------------------------------------------------------

from shared.tenant_rate_limit import TenantTier, get_tenant_rate_limiter


def _is_exempt_path(path: str) -> bool:
    """Check if the request path is exempt from rate limiting."""
    exempt_paths = ["/health", "/healthz"]
    return path in exempt_paths or path.startswith("/static")


async def _get_tenant_info(auth_header: str) -> tuple[str | None, TenantTier]:
    """Extract tenant_id and tier from JWT token."""
    if not auth_header.startswith("Bearer "):
        return None, TenantTier.FREE

    try:
        token = auth_header.replace("Bearer ", "")

        if not _settings.jwt_secret:
            return None, TenantTier.FREE

        payload = pyjwt.decode(
            token,
            _settings.jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        if not user_id:
            return None, TenantTier.FREE

        try:
            async with _pool_manager.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT p.tenant_id, t.plan
                       FROM public.profiles p
                       LEFT JOIN public.tenants t ON t.id = p.tenant_id
                       WHERE p.user_id = $1""",
                    user_id,
                )
                if row:
                    tenant_id = row["tenant_id"]
                    tier = (
                        TenantTier(row["plan"].upper())
                        if row["plan"]
                        else TenantTier.FREE
                    )
                    return tenant_id, tier
        except Exception as e:
            logger.debug(f"Failed to fetch tenant info from DB: {e}")
    except Exception as e:
        logger.debug(f"Failed to decode JWT for tenant info: {e}")

    return None, TenantTier.FREE


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Tenant-aware rate limiting middleware for API endpoints."""
    if _is_exempt_path(request.url.path):
        return await call_next(request)

    client_ip = get_client_ip(request)
    auth_header = request.headers.get("Authorization", "")
    tenant_id, tenant_tier = await _get_tenant_info(auth_header)

    if tenant_id:
        tenant_limiter = get_tenant_rate_limiter()
        allowed, metadata = await tenant_limiter.acquire(
            tenant_id=tenant_id,
            tier=tenant_tier,
            endpoint=request.url.path,
        )
        if not allowed:
            incr(
                "api.rate_limit_exceeded",
                tags={"tenant_id": str(tenant_id), "endpoint": request.url.path},
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Limit: {metadata.get('limit', 'unknown')} requests/minute. Try again in {metadata.get('reset_in', 60)} seconds.",
            )
    else:
        ip_limiter = get_rate_limiter(f"api:{client_ip}", max_calls=100, window_seconds=60)
        if not await ip_limiter.acquire():
            incr("api.rate_limit_exceeded", tags={"client_ip": client_ip})
            raise HTTPException(
                status_code=429, detail="Rate limit exceeded. Please try again later."
            )

    return await call_next(request)


# ---------------------------------------------------------------------------
# CORS Middleware - MUST be registered LAST so it executes FIRST
# (FastAPI middleware executes in reverse order of registration)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-CSRF-Token",
        "x-csrftoken",
    ],
    expose_headers=["X-Request-ID"],
    max_age=3600,
)


# ---------------------------------------------------------------------------
# Mount sub-routers (billing, admin, export – added in Parts 2-4)
# ---------------------------------------------------------------------------


def _mount_sub_routers() -> None:
    """Deferred import to avoid circular deps; called after deps are defined.

    Uses app.dependency_overrides so that Depends() references captured at
    route-definition time are correctly replaced at request time.
    """
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

    try:
        import api.sso as sso_mod

        app.dependency_overrides[sso_mod._get_pool] = get_pool
        app.dependency_overrides[sso_mod._get_tenant_ctx] = get_tenant_context
        app.include_router(sso_mod.router)
    except ImportError as exc:
        logger.warning(
            "SSO module unavailable (signxml/pyOpenSSL issue): %s — SSO endpoints disabled",
            exc,
        )

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

    # Skills taxonomy and validation
    import api.skills as skills_mod

    app.dependency_overrides[skills_mod._get_pool] = get_pool
    app.dependency_overrides[skills_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(skills_mod.router)

    # Match weights configuration
    import api.match_weights as match_weights_mod

    app.dependency_overrides[match_weights_mod._get_pool] = get_pool
    app.dependency_overrides[match_weights_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(match_weights_mod.router)

    # Match score calibration
    import api.match_calibration as match_calibration_mod

    app.dependency_overrides[match_calibration_mod._get_pool] = get_pool
    app.dependency_overrides[match_calibration_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(match_calibration_mod.router)

    # Job details and listings
    import api.job_details as job_details_mod

    app.dependency_overrides[job_details_mod._get_pool] = get_pool
    app.dependency_overrides[job_details_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(job_details_mod.router)

    # Resume PDF generation
    import api.resume_pdf as resume_pdf_mod

    app.dependency_overrides[resume_pdf_mod._get_pool] = get_pool
    app.dependency_overrides[resume_pdf_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(resume_pdf_mod.router)

    # Resume agent integration
    import api.resume_integration as resume_integration_mod

    app.dependency_overrides[resume_integration_mod._get_pool] = get_pool
    app.dependency_overrides[resume_integration_mod._get_tenant_ctx] = (
        get_tenant_context
    )
    app.include_router(resume_integration_mod.router)

    # ATS recommendations
    import api.ats_recommendations as ats_recommendations_mod

    app.dependency_overrides[ats_recommendations_mod._get_pool] = get_pool
    app.dependency_overrides[ats_recommendations_mod._get_tenant_ctx] = (
        get_tenant_context
    )
    app.include_router(ats_recommendations_mod.router)

    # Voice interview simulator
    import api.voice_interviews as voice_interviews_mod

    app.dependency_overrides[voice_interviews_mod._get_pool] = get_pool
    app.dependency_overrides[voice_interviews_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(voice_interviews_mod.router)

    # LLM career path analyzer
    import api.llm_career_path as llm_career_path_mod

    app.dependency_overrides[llm_career_path_mod._get_pool] = get_pool
    app.dependency_overrides[llm_career_path_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(llm_career_path_mod.router)

    # AI onboarding system
    import api.ai_onboarding as ai_onboarding_mod

    app.dependency_overrides[ai_onboarding_mod._get_pool] = get_pool
    app.dependency_overrides[ai_onboarding_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(ai_onboarding_mod.router)

    # A/B testing system
    import api.ab_testing as ab_testing_mod

    app.dependency_overrides[ab_testing_mod._get_pool] = get_pool
    app.dependency_overrides[ab_testing_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(ab_testing_mod.router)

    # Billing routes
    import api.billing as billing_mod

    app.dependency_overrides[billing_mod._get_pool] = get_pool
    app.dependency_overrides[billing_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(billing_mod.router)

    import api.og as og_mod

    app.include_router(og_mod.router)

    # AI Suggestions for smart onboarding
    import api.ai as ai_mod

    app.dependency_overrides[ai_mod._get_pool] = get_pool
    app.dependency_overrides[ai_mod._get_user_id] = get_current_user_id
    app.include_router(ai_mod.router)

    import api.dashboard as dashboard_mod

    app.dependency_overrides[dashboard_mod._get_pool] = get_pool
    app.dependency_overrides[dashboard_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[dashboard_mod._get_admin_user_id] = get_current_user_id
    app.include_router(dashboard_mod.router)

    import api.sessions as sessions_mod

    app.dependency_overrides[sessions_mod._get_pool] = get_pool
    app.dependency_overrides[sessions_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[sessions_mod._get_user_id] = get_current_user_id
    app.include_router(sessions_mod.router)

    import api.job_alerts as job_alerts_mod

    app.dependency_overrides[job_alerts_mod._get_pool] = get_pool
    app.dependency_overrides[job_alerts_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(job_alerts_mod.router)

    import api.mfa as mfa_mod

    app.dependency_overrides[mfa_mod._get_pool] = get_pool
    app.dependency_overrides[mfa_mod._get_user_id] = get_current_user_id
    app.include_router(mfa_mod.router)

    import api.ccpa as ccpa_mod

    app.include_router(ccpa_mod.router)

    import api.gdpr as gdpr_mod

    app.dependency_overrides[gdpr_mod._get_pool] = get_pool
    app.dependency_overrides[gdpr_mod._get_user_id] = get_current_user_id
    app.include_router(gdpr_mod.router)

    import api.interviews as interviews_mod

    app.dependency_overrides[interviews_mod._get_pool] = get_pool
    app.dependency_overrides[interviews_mod._get_user_id] = get_current_user_id
    app.include_router(interviews_mod.router)

    import api.career as career_mod

    app.dependency_overrides[career_mod._get_pool] = get_pool
    app.dependency_overrides[career_mod._get_user_id] = get_current_user_id
    app.include_router(career_mod.router)

    import api.saved_jobs as saved_jobs_mod

    app.dependency_overrides[saved_jobs_mod._get_pool] = get_pool
    app.dependency_overrides[saved_jobs_mod._get_user_id] = get_current_user_id
    app.dependency_overrides[saved_jobs_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(saved_jobs_mod.router)

    import api.calendar_api as calendar_mod

    async def _get_tenant_id_from_context(ctx=Depends(get_tenant_context)) -> str:
        return str(ctx.tenant_id)

    app.dependency_overrides[calendar_mod._get_pool] = get_pool
    app.dependency_overrides[calendar_mod._get_user_id] = get_current_user_id
    app.dependency_overrides[calendar_mod._get_tenant_id] = _get_tenant_id_from_context
    app.include_router(calendar_mod.router)

    import api.worker_health as worker_health_mod

    app.dependency_overrides[worker_health_mod._get_pool] = get_pool
    app.dependency_overrides[worker_health_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(worker_health_mod.router)

    # Import routers

    import api.integrations as integrations_mod

    app.dependency_overrides[integrations_mod._get_pool] = get_pool
    app.dependency_overrides[integrations_mod._get_user_id] = get_current_user_id
    app.dependency_overrides[integrations_mod._get_tenant_id] = (
        _get_tenant_id_from_context
    )
    app.include_router(integrations_mod.router)

    import api.admin_security as admin_sec_mod

    app.dependency_overrides[admin_sec_mod._get_pool] = get_pool
    app.dependency_overrides[admin_sec_mod._get_user_id] = get_current_user_id
    app.dependency_overrides[admin_sec_mod._get_tenant_id] = _get_tenant_id_from_context
    app.include_router(admin_sec_mod.router)

    # Phase 12.1 Agent Improvements
    import api.agent_improvements_endpoints as agent_improvements_mod

    app.dependency_overrides[agent_improvements_mod.get_tenant_context] = (
        get_tenant_context
    )
    app.dependency_overrides[agent_improvements_mod.get_agent_improvements_manager] = (
        lambda: create_agent_improvements_manager(get_pool())
    )
    app.include_router(agent_improvements_mod.router)

    # Phase 13.1 Communication System
    import api.communication_endpoints as communication_mod

    app.dependency_overrides[communication_mod._get_pool] = get_pool
    app.dependency_overrides[communication_mod.get_tenant_context] = get_tenant_context
    app.include_router(communication_mod.router)

    # Phase 14.1 User Experience System
    import api.user_experience_endpoints as ux_mod

    app.dependency_overrides[ux_mod._get_pool] = get_pool
    app.dependency_overrides[ux_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(ux_mod.router)

    # DLQ Management and Concurrent Usage
    import api.dlq_endpoints as dlq_mod

    app.dependency_overrides[dlq_mod._get_pool] = get_pool
    app.dependency_overrides[dlq_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[dlq_mod._get_admin_user_id] = get_current_user_id
    app.include_router(dlq_mod.router)

    # Concurrent Usage (Phase 12.1)
    import api.concurrent_usage_endpoints as concurrent_usage_mod

    app.dependency_overrides[concurrent_usage_mod.get_tenant_context] = (
        get_tenant_context
    )
    app.include_router(concurrent_usage_mod.router)


# NOTE: _mount_sub_routers() is called at the bottom of this file,
# after get_pool and get_tenant_context are defined.


# ---------------------------------------------------------------------------
# Database pool lifecycle
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Standard error envelope handler
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return all HTTP errors in FastAPI standard format."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions to prevent stack trace leaks in production."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    if _settings.env == Environment.LOCAL:
        msg = f"Internal Server Error: {str(exc)}"
    else:
        msg = "Internal Server Error"

    return JSONResponse(status_code=500, content={"detail": msg})


# ---------------------------------------------------------------------------
# Auth dependency – extract user_id from Supabase JWT
# ---------------------------------------------------------------------------


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
            user_id,
            body.field_label,
            body.field_type,
            body.answer_value,
        )
    return {"status": "saved"}


class RichSkillRequest(BaseModel):
    skill: str
    confidence: float = 0.5
    years_actual: float | None = None
    context: str = ""
    last_used: str | None = None
    verified: bool = False
    related_to: list[str] = []
    source: str = "manual"
    project_count: int = 0


class SaveSkillsRequest(BaseModel):
    skills: list[RichSkillRequest]


@app.get("/me/skills")
async def get_user_skills(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Get user's rich skills with confidence and metadata."""
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """SELECT skill, confidence, years_actual, context, last_used, verified,
                      related_to, source, project_count, created_at, updated_at
               FROM public.user_skills WHERE user_id = $1
               ORDER BY confidence DESC, skill""",
            user_id,
        )
    return [dict(r) for r in rows]


@app.post("/me/skills")
async def save_user_skills(
    body: SaveSkillsRequest,
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """Save user's rich skills (upsert)."""
    logger.info(
        "[SKILLS] Saving skills for user",
        extra={"user_id": user_id, "skill_count": len(body.skills)},
    )

    if not body.skills:
        logger.warning(
            "[SKILLS] Empty skills list received", extra={"user_id": user_id}
        )
        return {"status": "saved", "count": 0}

    async with db.acquire() as conn:
        async with conn.transaction():
            # Clear existing skills and insert new ones (atomic)
            await conn.execute(
                "DELETE FROM public.user_skills WHERE user_id = $1", user_id
            )

            for skill in body.skills:
                try:
                    await conn.execute(
                        """INSERT INTO public.user_skills
                           (user_id, skill, confidence, years_actual, context, last_used,
                            verified, related_to, source, project_count)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                        user_id,
                        skill.skill,
                        skill.confidence,
                        skill.years_actual,
                        skill.context,
                        skill.last_used,
                        skill.verified,
                        skill.related_to,
                        skill.source,
                        skill.project_count,
                    )
                except Exception as e:
                    logger.error(
                        "[SKILLS] Failed to insert skill",
                        extra={
                            "user_id": user_id,
                            "skill": skill.skill,
                            "error": str(e),
                        },
                    )
                    raise

            # Update profile completeness with proper capping at 100%
            await conn.execute(
                """UPDATE public.users SET profile_completeness =
                   LEAST(100, COALESCE(profile_completeness, 0) +
                   CASE WHEN (SELECT COUNT(*) FROM public.user_skills WHERE user_id = $1) >= 3
                        THEN 20 ELSE 10 END)
                   WHERE id = $1""",
                user_id,
            )

    logger.info(
        "[SKILLS] Skills saved successfully",
        extra={"user_id": user_id, "count": len(body.skills)},
    )
    return {"status": "saved", "count": len(body.skills)}


class WorkStyleRequest(BaseModel):
    autonomy_preference: str = "medium"
    learning_style: str = "building"
    company_stage_preference: str = "flexible"
    communication_style: str = "mixed"
    pace_preference: str = "steady"
    ownership_preference: str = "team"
    career_trajectory: str = "open"

    class Config:
        extra = "ignore"  # Ignore extra fields


@app.get("/me/work-style")
async def get_work_style(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any] | None:
    """Get user's work style profile."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT autonomy_preference, learning_style, company_stage_preference,
                      communication_style, pace_preference, ownership_preference,
                      career_trajectory, created_at, updated_at
               FROM public.work_style_profiles WHERE user_id = $1""",
            user_id,
        )
    return dict(row) if row else None


@app.post("/me/work-style")
async def save_work_style(
    body: WorkStyleRequest,
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """Save user's work style profile."""
    logger.info(
        "[WORK_STYLE] Saving work style for user",
        extra={"user_id": user_id, "data": body.model_dump()},
    )

    async with db.acquire() as conn:
        # Check if user has already saved work style (only add completeness on first save)
        had_work_style = await conn.fetchval(
            "SELECT 1 FROM public.work_style_profiles WHERE user_id = $1 LIMIT 1",
            user_id,
        )

        await conn.execute(
            """INSERT INTO public.work_style_profiles
               (user_id, autonomy_preference, learning_style, company_stage_preference,
                communication_style, pace_preference, ownership_preference, career_trajectory)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
               ON CONFLICT (user_id) DO UPDATE SET
                autonomy_preference = $2,
                learning_style = $3,
                company_stage_preference = $4,
                communication_style = $5,
                pace_preference = $6,
                ownership_preference = $7,
                career_trajectory = $8,
                updated_at = now()""",
            user_id,
            body.autonomy_preference,
            body.learning_style,
            body.company_stage_preference,
            body.communication_style,
            body.pace_preference,
            body.ownership_preference,
            body.career_trajectory,
        )

        # Update profile completeness only on first work style save
        if not had_work_style:
            await conn.execute(
                """UPDATE public.users SET profile_completeness =
                   LEAST(100, COALESCE(profile_completeness, 0) + 20)
                   WHERE id = $1""",
                user_id,
            )

        # Sync work_style to profile_data JSONB so the scoring engine can read it
        existing = await conn.fetchrow(
            "SELECT profile_data FROM public.profiles WHERE user_id = $1",
            user_id,
        )
        if existing:
            pd = existing["profile_data"]
            profile_data = json.loads(pd) if isinstance(pd, str) else (pd or {})
            profile_data["work_style"] = body.model_dump()
            await conn.execute(
                "UPDATE public.profiles SET profile_data = $1 WHERE user_id = $2",
                json.dumps(profile_data),
                user_id,
            )

    logger.info("[WORK_STYLE] Saved successfully", extra={"user_id": user_id})
    return {"status": "saved"}


@app.get("/me/dashboard")
async def user_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """User dashboard data for mobile v3 home screen + widget."""
    # TODO: applications table lacks tenant_id column per audit; add tenant_id filter when
    # column is added for multi-tenant isolation
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
        **(
            dict(counts)
            if counts
            else {
                "active_count": 0,
                "hold_count": 0,
                "completed_today": 0,
                "completed_week": 0,
                "total_all_time": 0,
            }
        ),
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

    # Pre-check Content-Length header to reject before reading body into memory
    if file.size and file.size > _settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_settings.max_upload_size_bytes // 1_048_576} MB",
        )
    pdf_bytes = await file.read()
    if len(pdf_bytes) > _settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_settings.max_upload_size_bytes // 1_048_576} MB",
        )

    resume_url, canonical_dict = await process_resume_upload(
        user_id=user_id,
        tenant_id=ctx.tenant_id,
        file_bytes=pdf_bytes,
        filename=file.filename or "resume.pdf",
        content_type=file.content_type or "application/pdf",
        db_pool=db,
        storage=get_storage_service(),
    )

    return ResumeParseResponse(
        user_id=user_id,
        profile=CanonicalProfile.model_validate(canonical_dict),
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
    """User answers hold questions → update inputs → emit events → re-queue."""
    incr("api.resume_task.requests", tags={"tenant_id": ctx.tenant_id})
    # Verify ownership + tenant scope
    async with db.acquire() as conn:
        app_row = await ApplicationRepo.get_by_id_and_user(
            conn, body.application_id, ctx.user_id, tenant_id=ctx.tenant_id
        )
    if app_row is None:
        raise HTTPException(
            status_code=404, detail="Application not found or not owned by user"
        )

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
            await EventRepo.emit(
                conn,
                body.application_id,
                "USER_ANSWERED",
                {
                    "input_id": a.input_id,
                    "answer": a.answer,
                },
                tenant_id=ctx.tenant_id,
            )

        # Re-queue so the worker picks it up
        updated = await ApplicationRepo.update_status(
            conn, body.application_id, "QUEUED"
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Application not found")

        # Emit RETRY_SCHEDULED
        await EventRepo.emit(
            conn,
            body.application_id,
            "RETRY_SCHEDULED",
            {
                "answered_count": len(body.answers),
            },
            tenant_id=ctx.tenant_id,
        )

        # Fetch remaining unresolved inputs for the response
        remaining = await InputRepo.get_unresolved(conn, body.application_id)

    # Server-side analytics: status changed
    await emit_analytics_event(
        db,
        APPLICATION_STATUS_CHANGED,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
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
                meta=(
                    json.loads(r["meta"])
                    if isinstance(r["meta"], str)
                    else r.get("meta")
                ),
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
    application_id: str = FastAPIPath(...),
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> ApplicationDetailResponse:
    """Application detail endpoint scoped to the requesting user's tenant."""
    validate_uuid(application_id, "application_id")
    async with db.acquire() as conn:
        detail = await ApplicationRepo.get_detail(
            conn, application_id, tenant_id=ctx.tenant_id
        )
        if detail is None:
            raise HTTPException(status_code=404, detail="Application not found")

        serialized = detail.to_serializable()
        app_dict = serialized["application"]

        job = (
            await JobRepo.get_by_id(conn, app_dict["job_id"])
            if app_dict.get("job_id")
            else None
        )
        if job:
            app_dict["company"] = job.get("company") or ""
            app_dict["job_title"] = job.get("title") or ""

        unresolved = next((inp for inp in detail.inputs if not inp.resolved), None)
        if unresolved:
            app_dict["hold_question"] = unresolved.question

        if app_dict.get("updated_at"):
            app_dict["last_activity"] = app_dict["updated_at"]

    return ApplicationDetailResponse(**serialized)


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/csrf/prepare")
async def csrf_prepare() -> dict[str, str]:
    """No-op endpoint to ensure CSRF cookie is issued to the client."""
    return {"status": "ok"}


@app.get("/healthz")
async def healthz(
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """Deep health check: pings DB and returns env + basic status.

    NOTE: circuit_breakers and metrics removed to avoid exposing internal
    operational data to unauthenticated callers (S-40).
    """
    s = get_settings()
    db_ok = False
    try:
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception as e:
        logger.debug(f"Health check DB connection failed: {e}")

    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "env": s.env.value,
        "db": "ok" if db_ok else "unreachable",
    }


# ---------------------------------------------------------------------------
# Storage endpoint - serve files from Render Disk or local storage
# ---------------------------------------------------------------------------
@app.get("/api/storage/{bucket}/{path:path}")
async def serve_storage_file(
    bucket: str,
    path: str,
    user_id: str = Depends(get_current_user_id),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Serve files from storage (e.g., resumes, avatars)."""
    # SECURITY: Prevent path traversal with canonicalization

    # Validate bucket name (alphanumeric, hyphens, underscores only)
    if not re.match(r"^[a-zA-Z0-9_-]+$", bucket):
        raise HTTPException(status_code=400, detail="Invalid bucket name")

    # SECURITY: Ensure user can only access their own tenant's files
    # Add tenant_id prefix to prevent cross-tenant access
    tenant_id = tenant_ctx.tenant_id or ""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Validate path components
    # Normalize path and check for traversal attempts
    normalized_path = os.path.normpath(path)
    if (
        ".." in normalized_path
        or normalized_path.startswith("/")
        or normalized_path.startswith("\\")
    ):
        raise HTTPException(status_code=400, detail="Invalid path")

    # Additional checks for encoded traversal attempts
    decoded_path = path.replace("%2e%2e", "..").replace("%2E%2E", "..")
    if ".." in decoded_path:
        raise HTTPException(status_code=400, detail="Invalid path")

    # SECURITY: Add tenant isolation to storage path
    # Only allow access to files within user's tenant directory
    storage_path = f"{tenant_id}/{bucket}/{normalized_path}"

    storage = get_storage_service()

    try:
        data = await storage.download_file(storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

    # Determine content type based on file extension
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"

    return Response(content=data, media_type=content_type)


# ---------------------------------------------------------------------------
# Mount sub-routers (must be after all dependencies are defined)
# ---------------------------------------------------------------------------
_mount_sub_routers()
