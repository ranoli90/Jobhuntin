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
import uuid
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
from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.backend.domain.agent_improvements import create_agent_improvements_manager
from packages.backend.domain.analytics_events import (
    APPLICATION_STATUS_CHANGED,
    emit_analytics_event,
)
from packages.backend.domain.masking import mask_ip
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
from shared.api_response import (
    SuccessResponse,
    success_response,
)
from shared.config import Environment, get_settings
from shared.logging_config import LogContext, get_logger, setup_logging
from shared.metrics import incr, observe
from shared.middleware import setup_csrf_middleware, setup_request_id_middleware
from shared.redis_client import close_redis, get_redis
from shared.storage import get_storage_service
from shared.telemetry import setup_telemetry
from shared.validators import validate_uuid
from contextlib import asynccontextmanager
import time
from api.dependencies import (
    _pool_manager,
    get_current_user_id,
    get_pool,
    require_admin_user_id,
)
from shared.metrics import get_rate_limiter
from shared.middleware import get_client_ip, setup_security_headers

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

# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not _settings.jwt_secret:
        if _settings.env == Environment.PROD:
            logger.critical("JWT_SECRET missing in PROD. Aborting startup.")
            raise RuntimeError("JWT_SECRET must be set in production")
        logger.warning("JWT_SECRET not set. Authentication will fail.")

    await _pool_manager.initialize()

    # H2: IP Binding - Warn if disabled in production (security recommendation)
    if _settings.env == Environment.PROD and not _settings.magic_link_bind_to_ip:
        logger.warning(
            "MAGIC_LINK_BIND_TO_IP is disabled in production. "
            "This allows magic links to be used from any IP address, "
            "increasing the risk of token theft. "
            "Consider enabling IP binding by setting "
            "MAGIC_LINK_BIND_TO_IP=true for enhanced security."
        )

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


# M3: API Versioning - Current API version
API_VERSION = "v1"
SUPPORTED_VERSIONS = ["v1", "v2"]

# Deprecated path prefixes: (prefix, sunset_YYYY-MM-DD). Per API_VERSIONING.md: 6+ months notice.
DEPRECATED_PATHS: list[tuple[str, str]] = []

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


def _build_cors_origins() -> list[str]:
    """Build CORS allow list. Restrict localhost in prod; filter invalid entries."""
    base = {
        _settings.app_base_url.rstrip("/"),
        "https://sorce-web.onrender.com",
        "https://sorce-admin.onrender.com",
        "https://sorce-api.onrender.com",
        "https://jobhuntin.com",
        "https://app.jobhuntin.com",
    }
    if _settings.env == Environment.LOCAL:
        base.update(
            (
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            )
        )
    if _settings.cors_allowed_origins:
        for o in _settings.cors_allowed_origins.split(","):
            o = o.strip()
            if o:
                base.add(o)

    def _valid(o: str) -> bool:
        return bool(o) and "REDACTED" not in o and o.startswith(("http://", "https://"))

    return [o for o in base if _valid(o)]


CORS_ORIGINS = _build_cors_origins()

app.state.cors_origins = CORS_ORIGINS

# ---------------------------------------------------------------------------
# IMPORTANT: Middleware executes in REVERSE order of registration.
# CORS MUST be registered LAST so it executes FIRST (handles OPTIONS preflight).
# ---------------------------------------------------------------------------

# TEMPORARILY DISABLED: CompressionMiddleware returns None and breaks all endpoints.
# TODO: Fix CompressionMiddleware properly, then re-enable.
# from shared.api_compression import CompressionMiddleware, create_compression_config
#
# compression_config = create_compression_config(
#     min_size=512,  # Compress responses > 512 bytes
#     enable_gzip=True,
#     enable_brotli=True,
#     enable_deflate=True,
# )
# app.add_middleware(CompressionMiddleware, config=compression_config)

# Add Request ID middleware for distributed tracing
setup_request_id_middleware(app)

# M3: API Versioning - Register versioned routers
# Note: api_v2 router is already registered below with prefix /api/v2
# For v1, we use the default routes (no prefix)


# Proxy-friendly: Vite may forward /api/* without rewriting. Strip /api prefix for v1 routes.
@app.middleware("http")
async def api_prefix_rewrite_middleware(request: Request, call_next):
    """Rewrite /api/me/jobs -> /me/jobs so backend routes match. Skip /api/v2/."""
    path = request.scope.get("path", "")
    if path.startswith("/api/") and not path.startswith("/api/v2/"):
        request.scope["path"] = path[4:] or "/"  # /api/me/jobs -> /me/jobs
    return await call_next(request)


# M3: API Versioning Middleware - Add version headers and handle version negotiation
# @app.middleware("http")
# async def api_versioning_middleware(request: Request, call_next):
#     """Add API version headers and handle version negotiation.
#
#     Headers added:
#     - X-API-Version: Actual API version used (v1 or v2)
#     - X-Supported-Versions: Comma-separated list of supported versions
#     - Deprecation, Sunset: For deprecated endpoints (per RFC 8594)
#     - X-API-Deprecated, X-API-Sunset-Date: Custom deprecation headers (per API_VERSIONING.md)
#
#     Version negotiation:
#     - URL /api/v2/* implies v2; otherwise Accept-Version header or default v1
#     - If Accept-Version not supported, returns 400 with supported versions
#     """
#     # Infer version from path: /api/v2/* always uses v2
#     path = request.url.path
#     if path.startswith("/api/v2/"):
#         effective_version = "v2"
#         request.state.api_version = "v2"
#     else:
#         requested_version = request.headers.get("Accept-Version")
#         if requested_version:
#             requested_version = requested_version.strip().lower()
#             if requested_version not in SUPPORTED_VERSIONS:
#                 return JSONResponse(
#                     status_code=400,
#                     content={
#                         "error": {
#                             "code": "UNSUPPORTED_API_VERSION",
#                             "message": f"API version '{requested_version}' is not supported",
#                             "detail": f"Supported versions: {', '.join(SUPPORTED_VERSIONS)}",
#                             "requested_version": requested_version,
#                             "supported_versions": SUPPORTED_VERSIONS,
#                         }
#                     },
#                     headers={
#                         "X-API-Version": API_VERSION,
#                         "X-Supported-Versions": ",".join(SUPPORTED_VERSIONS),
#                     },
#                 )
#             request.state.api_version = requested_version
#             effective_version = requested_version
#         else:
#             request.state.api_version = API_VERSION
#             effective_version = API_VERSION
#
#     # Process request
#     response = await call_next(request)
#
#     # Add API version headers to response (reflect actual version used)
#     response.headers["X-API-Version"] = effective_version
#     response.headers["X-Supported-Versions"] = ",".join(SUPPORTED_VERSIONS)
#
#     # Deprecation headers per API_VERSIONING.md and RFC 8594
#     for prefix, sunset_date in DEPRECATED_PATHS:
#         if path.startswith(prefix):
#             response.headers["Deprecation"] = "true"
#             response.headers["Sunset"] = sunset_date
#             response.headers["X-API-Deprecated"] = "true"
#             response.headers["X-API-Sunset-Date"] = sunset_date
#             break
#
#     return response


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
    exempt_paths = {
        "/health",
        "/healthz",
        "/csrf/prepare",
        "/billing/tiers",
        "/agent-improvements/health",
        "/ai/llm/health",
        "/auth/logout",  # Critical auth flow - must not be rate limited
        "/openapi.json",  # Used by API discovery/tooling
        "/docs",
        "/redoc",
    }
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
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            return None, TenantTier.FREE

        # JWT sub is string; cast to UUID for profiles.user_id (uuid column)
        try:
            uuid.UUID(str(user_id_raw))
        except (ValueError, TypeError):
            return None, TenantTier.FREE

        try:
            async with _pool_manager.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT p.tenant_id, t.plan
                       FROM public.profiles p
                       LEFT JOIN public.tenants t ON t.id::text = p.tenant_id
                       WHERE p.user_id = $1::uuid""",
                    str(user_id_raw),
                )
                if row and row["tenant_id"]:
                    tenant_id = str(row["tenant_id"])
                    try:
                        tier = (
                            TenantTier(row["plan"].upper())
                            if row.get("plan")
                            else TenantTier.FREE
                        )
                    except ValueError:
                        tier = TenantTier.FREE
                    return tenant_id, tier
        except Exception as e:
            logger.debug(f"Failed to fetch tenant info from DB: {e}")
    except Exception as e:
        logger.debug(f"Failed to decode JWT for tenant info: {e}")

    return None, TenantTier.FREE


# ---------------------------------------------------------------------------
# Latency / Observability Middleware
# ---------------------------------------------------------------------------
# NOTE: Middleware executes in REVERSE order of registration.
# Registration order below: latency → rate-limit → CORS (last = first to run).


@app.middleware("http")
async def latency_middleware(request: Request, call_next):
    """Track API latency, request count, and OpenTelemetry span attributes."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.route", request.url.path)
    except Exception:
        span = None

    start_time = time.time()
    path = request.url.path
    method = request.method

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        if span and span.get_span_context().is_valid:
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute(
                "http.response_size", response.headers.get("content-length", "0")
            )

        observe(
            "api.latency",
            duration,
            tags={"path": path, "method": method, "status_code": str(response.status_code)},
        )

        if duration > 1.0:
            logger.warning(
                "Slow API request detected",
                extra={"path": path, "method": method, "duration": duration, "status_code": response.status_code},
            )
            incr("api.slow_requests", tags={"path": path, "method": method, "status_code": str(response.status_code)})

        incr("api.requests", tags={"path": path, "method": method, "status_code": str(response.status_code)})
        return response
    except Exception as exc:
        duration = time.time() - start_time
        if span and span.get_span_context().is_valid:
            span.record_exception(exc)
            from opentelemetry import trace as _trace

            span.set_status(_trace.Status(_trace.StatusCode.ERROR, str(exc)))
            span.set_attribute("http.status_code", 500)

        observe("api.latency", duration, tags={"path": path, "method": method, "status_code": "500", "error": "true"})
        incr("api.errors", tags={"path": path, "method": method, "error_type": type(exc).__name__})
        raise


# ---------------------------------------------------------------------------
# Tenant-Aware Rate Limiting Middleware
# ---------------------------------------------------------------------------


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
            incr("api.rate_limit_exceeded", tags={"tenant_id": str(tenant_id), "endpoint": request.url.path})
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Limit: {metadata.get('limit', 'unknown')} requests/minute. "
                        f"Try again in {metadata.get('reset_in', 60)} seconds.",
                    }
                },
            )
    else:
        ip_limiter = get_rate_limiter(f"api:{client_ip}", max_calls=100, window_seconds=60)
        if not await ip_limiter.acquire():
            incr("api.rate_limit_exceeded", tags={"ip_hash": mask_ip(client_ip)})
            return JSONResponse(
                status_code=429,
                content =
    {"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded. Please try again later."}},
            )

    response = await call_next(request)
    if response is None:
        return JSONResponse(
    status_code=500, content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "No response"}})
    return response


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
        "Idempotency-Key",
        "Accept-Version",
    ],
    expose_headers=[
        "X-Request-ID",
        "X-API-Version",
        "X-Supported-Versions",
        "Deprecation",
        "Sunset",
        "X-API-Deprecated",
        "X-API-Sunset-Date",
    ],
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

    async def _get_tenant_id_from_context(ctx=Depends(get_tenant_context)) -> str:
        return str(ctx.tenant_id)

    # Core routes extracted from main.py (PERF-001)
    import api.core_routes as core_routes_mod

    app.dependency_overrides[core_routes_mod._get_pool] = get_pool
    app.dependency_overrides[core_routes_mod._get_user_id] = get_current_user_id
    app.dependency_overrides[core_routes_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(core_routes_mod.router)

    import api.admin as admin_mod

    app.dependency_overrides[admin_mod._get_pool] = get_pool
    app.dependency_overrides[admin_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[admin_mod._get_admin_user_id] = require_admin_user_id
    app.include_router(admin_mod.router)

    import api.auth as auth_mod

    # auth uses get_pool directly from api.dependencies
    app.include_router(auth_mod.router)

    import api.export as export_mod

    app.dependency_overrides[export_mod._get_pool] = get_pool
    app.dependency_overrides[export_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(export_mod.router)

    import api.analytics as analytics_mod

    app.dependency_overrides[analytics_mod._get_pool] = get_pool
    app.dependency_overrides[analytics_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[analytics_mod._get_admin_user_id] = require_admin_user_id
    app.include_router(analytics_mod.router)

    import api.growth as growth_mod

    app.dependency_overrides[growth_mod._get_pool] = get_pool
    app.dependency_overrides[growth_mod._get_user_id] = get_current_user_id
    app.dependency_overrides[growth_mod._get_admin_user_id] = require_admin_user_id
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

    # Skill gap analysis
    import api.skill_gap_analysis as skill_gap_mod

    app.dependency_overrides[skill_gap_mod._get_pool] = get_pool
    app.dependency_overrides[skill_gap_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(skill_gap_mod.router, prefix="/skill-gap")

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
    app.include_router(job_details_mod.router, prefix="/jobs")

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

    # Billing routes (uses get_pool, get_tenant_context directly from api.dependencies/main)
    import api.billing as billing_mod

    app.include_router(billing_mod.router)

    import api.og as og_mod

    app.include_router(og_mod.router)

    # AI Suggestions for smart onboarding
    import api.ai as ai_mod

    app.dependency_overrides[ai_mod._get_pool] = get_pool
    app.dependency_overrides[ai_mod._get_user_id] = get_current_user_id
    app.dependency_overrides[ai_mod._get_tenant_id] = _get_tenant_id_from_context
    app.include_router(ai_mod.router)

    import api.dashboard as dashboard_mod

    app.dependency_overrides[dashboard_mod._get_pool] = get_pool
    app.dependency_overrides[dashboard_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[dashboard_mod._get_admin_user_id] = require_admin_user_id
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

    import api.contact as contact_mod

    app.include_router(contact_mod.router)

    import api.gdpr as gdpr_mod

    app.dependency_overrides[gdpr_mod._get_pool] = get_pool
    app.dependency_overrides[gdpr_mod._get_user_id] = get_current_user_id
    app.include_router(gdpr_mod.router)

    # Phase 9.3 Consent Management
    import api.consent as consent_mod

    app.dependency_overrides[consent_mod.get_pool] = get_pool
    app.include_router(consent_mod.router)

    # Phase 9.4 Compliance Reporting
    import api.compliance_reports as compliance_mod

    app.dependency_overrides[compliance_mod._get_admin_user_id] = require_admin_user_id
    app.dependency_overrides[compliance_mod._get_pool] = get_pool
    app.include_router(compliance_mod.router)

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
    app.dependency_overrides[agent_improvements_mod._get_pool] = get_pool
    app.dependency_overrides[agent_improvements_mod.get_agent_improvements_manager] = (
        lambda: create_agent_improvements_manager(get_pool())
    )
    app.include_router(agent_improvements_mod.router)

    # Phase 13.1 Communication System
    import api.communication_endpoints as communication_mod

    app.dependency_overrides[communication_mod._get_pool] = get_pool
    app.dependency_overrides[communication_mod.get_tenant_context] = get_tenant_context
    app.include_router(communication_mod.router)

    # Phase 13.1 Communications (email history, preferences) — /email/history, /email/preferences
    import api.communications_endpoints as communications_mod

    app.dependency_overrides[communications_mod.get_tenant_context] = get_tenant_context
    app.include_router(communications_mod.router)

    # Phase 14.1 User Experience System
    import api.user_experience_endpoints as ux_mod

    app.dependency_overrides[ux_mod._get_pool] = get_pool
    app.dependency_overrides[ux_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(ux_mod.router)

    # DLQ Management and Concurrent Usage
    import api.dlq_endpoints as dlq_mod

    app.dependency_overrides[dlq_mod._get_pool] = get_pool
    app.dependency_overrides[dlq_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[dlq_mod.get_tenant_context] = get_tenant_context
    app.dependency_overrides[dlq_mod._get_admin_user_id] = require_admin_user_id
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
    """C7: Error Handling - Standardize error responses.

    Returns consistent error format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "detail": "Additional context",
            "request_id": "X-Request-ID"
        }
    }
    """
    request_id = request.headers.get("X-Request-ID", "unknown")

    # MEDIUM: Extract error code from status code or detail message
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        402: "PAYMENT_REQUIRED",
        413: "PAYLOAD_TOO_LARGE",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    # Try to extract specific error code from detail message
    error_code = error_codes.get(exc.status_code, "HTTP_ERROR")
    detail_lower = (exc.detail or "").lower()

    # Map common error messages to specific error codes
    if "invalid job id" in detail_lower:
        error_code = "INVALID_JOB_ID_FORMAT"
    elif "invalid application id" in detail_lower:
        error_code = "INVALID_APPLICATION_ID_FORMAT"
    elif "undo window" in detail_lower or "expired" in detail_lower:
        error_code = "UNDO_WINDOW_EXPIRED"
    elif "invalid captcha" in detail_lower:
        error_code = "INVALID_CAPTCHA"
    elif "file is empty" in detail_lower or "corrupted" in detail_lower:
        error_code = "FILE_CORRUPTED"
    elif "invalid file type" in detail_lower or "not allowed" in detail_lower:
        error_code = "INVALID_FILE_TYPE"
    elif "missing signature" in detail_lower:
        error_code = "MISSING_SIGNATURE"
    elif "invalid signature" in detail_lower:
        error_code = "INVALID_SIGNATURE"
    elif "missing authentication" in detail_lower:
        error_code = "MISSING_AUTHENTICATION"
    elif "invalid.*token" in detail_lower or "expired.*token" in detail_lower:
        error_code = "INVALID_TOKEN"
    elif "admin access required" in detail_lower or "admin.*required" in detail_lower:
        error_code = "ADMIN_ACCESS_REQUIRED"
    elif "plan.*upgrade" in detail_lower or "enterprise plan" in detail_lower:
        error_code = "PLAN_UPGRADE_REQUIRED"
    elif "access denied" in detail_lower:
        error_code = "ACCESS_DENIED"
    elif "not found" in detail_lower:
        if "job" in detail_lower:
            error_code = "JOB_NOT_FOUND"
        elif "application" in detail_lower:
            error_code = "APPLICATION_NOT_FOUND"
        elif "user" in detail_lower:
            error_code = "USER_NOT_FOUND"
        elif "session" in detail_lower:
            error_code = "SESSION_NOT_FOUND"
    elif "already exists" in detail_lower or "duplicate" in detail_lower:
        error_code = "RESOURCE_ALREADY_EXISTS"
    elif "status conflict" in detail_lower or "status.*conflict" in detail_lower:
        error_code = "APPLICATION_STATUS_CONFLICT"
    elif "no pending questions" in detail_lower:
        error_code = "NO_PENDING_QUESTIONS"
    elif "email service" in detail_lower:
        if "timeout" in detail_lower:
            error_code = "EMAIL_SERVICE_TIMEOUT"
        else:
            error_code = "EMAIL_SERVICE_ERROR"
    elif (
        "database.*unavailable" in detail_lower or "pool.*not available" in detail_lower
    ):
        error_code = "DATABASE_UNAVAILABLE"
    elif "rating" in detail_lower and ("1" in detail_lower or "5" in detail_lower):
        error_code = "INVALID_RATING"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": exc.detail or "Something went wrong. Please try again.",
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """C7: Error Handling - Catch-all for unhandled exceptions.

    Prevents stack trace leaks in production while providing useful
    error information in development. B1: Return 503 for pool exhaustion.
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    # B1: DB pool exhausted - return 503
    exc_name = type(exc).__name__
    if (
        "TooManyConnections" in exc_name
        or "PoolTimeout" in exc_name
        or (
            isinstance(exc, (TimeoutError, ConnectionError))
            and "pool" in str(exc).lower()
        )
    ):
        logger.warning("Database pool exhausted or timeout: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Service temporarily unavailable. Please try again.",
                    "request_id": request_id,
                }
            },
        )
    logger.error(
        "Unhandled exception",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_id": request_id,
            "path": request.url.path,
        },
        exc_info=True,
    )

    if _settings.env == Environment.LOCAL:
        msg = f"Internal Server Error: {str(exc)}"
        detail = f"{type(exc).__name__}: {str(exc)}"
    else:
        msg = "Internal Server Error"
        detail = "An unexpected error occurred. Our team has been notified."

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": msg,
                "detail": detail,
                "request_id": request_id,
            }
        },
    )


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
    from packages.backend.domain.tenant import TenantScopeError

    try:
        async with db.acquire() as conn:
            ctx = await resolve_tenant_context(conn, user_id)
        if ctx is None:
            logger.error(
                "[TENANT] resolve_tenant_context returned None for user_id: %s", user_id
            )
            raise HTTPException(
                status_code=500, detail="Failed to resolve tenant context"
            )
        LogContext.set(tenant_id=ctx.tenant_id, user_id=ctx.user_id)
        return ctx
    except HTTPException:
        raise
    except TenantScopeError as exc:
        if "not found" in str(exc).lower() or "sign in again" in str(exc).lower():
            raise HTTPException(
                status_code=401,
                detail="User not found. Please sign in again.",
            )
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:
        logger.error("[TENANT] Error resolving tenant context: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resolve tenant context")


# ---------------------------------------------------------------------------
# Pydantic models and inline endpoints have been extracted to core_routes.py
# (PERF-001). They are mounted in _mount_sub_routers() below.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


@app.get("/health")
@app.get("/api/health")  # Proxy-friendly: Vite may forward /api/health without rewrite
async def health(
    request: Request,
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """Basic health check with dependency validation.

    M8: Include database and Redis health checks to ensure all critical
    dependencies are available before reporting healthy status.
    """
    s = get_settings()
    checks = {
        "database": "unknown",
        "redis": "unknown",
    }

    # Check database connection
    try:
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)[:50]}"

    # Check Redis if configured
    if s.redis_url:
        try:
            from shared.redis_client import get_redis

            r = await get_redis()
            await r.ping()
            checks["redis"] = "healthy"
        except Exception as e:
            checks["redis"] = f"unhealthy: {str(e)[:50]}"
    else:
        checks["redis"] = "not_configured"

    # Determine overall status
    db_healthy = checks["database"] == "healthy"
    redis_healthy = checks["redis"] in ("healthy", "not_configured")

    if db_healthy and redis_healthy:
        return {"status": "ok", "checks": checks}
    else:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "SERVICE_UNAVAILABLE", "message": "One or more dependencies are unhealthy"}},
        )


@app.get("/agent-improvements/health")
async def agent_improvements_health(request: Request) -> SuccessResponse[dict[str, Any]]:
    """Health check for agent improvements system. Defined in main to avoid middleware edge cases.
    
    Returns standardized response format.
    """
    return success_response({
        "status": "healthy",
        "service": "agent_improvements",
        "features": [
            "button_detection",
            "form_field_detection",
            "oauth_handling",
            "screenshot_capture",
            "concurrent_usage_tracking",
            "dlq_management",
            "document_type_tracking",
            "performance_metrics",
        ],
    }, request=request)


@app.get("/csrf/prepare")
async def csrf_prepare(request: Request) -> SuccessResponse[dict[str, str]]:
    """No-op endpoint to ensure CSRF cookie is issued to the client.
    
    Returns standardized response format.
    """
    return success_response({"status": "ok"}, request=request)


@app.get("/healthz")
async def healthz(
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """Deep health check: pings DB and returns env + basic status.

    H6: Connection Pool Monitoring - Includes pool statistics for monitoring.
    NOTE: circuit_breakers and metrics removed to avoid exposing internal
    operational data to unauthenticated callers (S-40).
    """
    from api.dependencies import _pool_manager

    s = get_settings()
    db_ok = False
    pool_stats = {}

    try:
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception as e:
        logger.debug(f"Health check DB connection failed: {e}")

    # H6: Collect connection pool statistics
    try:
        pool = _pool_manager.pool
        pool_size = pool.get_size()
        idle_size = pool.get_idle_size()
        min_size = pool.get_min_size()
        max_size = pool.get_max_size()
        active_size = pool_size - idle_size
        utilization_pct = (active_size / max_size * 100) if max_size > 0 else 0

        pool_stats = {
            "size": pool_size,
            "idle": idle_size,
            "active": active_size,
            "min": min_size,
            "max": max_size,
            "utilization_pct": round(utilization_pct, 2),
        }

        # Track pool metrics for alerting
        observe("db.pool.size", pool_size, tags={"type": "total"})
        observe("db.pool.active", active_size, tags={"type": "active"})
        observe("db.pool.idle", idle_size, tags={"type": "idle"})
        observe("db.pool.utilization", utilization_pct, tags={"type": "percentage"})

        # Alert if pool is near capacity (H6: Connection Pool Monitoring)
        if utilization_pct > 80:
            logger.warning(
                "Database pool utilization high: %.1f%% (%d/%d active connections)",
                utilization_pct,
                active_size,
                max_size,
            )
            incr("db.pool.high_utilization", tags={"threshold": "80"})
        elif utilization_pct > 90:
            logger.error(
                "Database pool critically high utilization: %.1f%% (%d/%d active connections)",
                utilization_pct,
                active_size,
                max_size,
            )
            incr("db.pool.critical_utilization", tags={"threshold": "90"})

    except Exception as e:
        logger.debug(f"Failed to collect pool stats: {e}")
        pool_stats = {"error": "unavailable"}

    status = "ok" if db_ok else "degraded"
    response = {
        "status": status,
        "env": s.env.value,
        "db": "ok" if db_ok else "unreachable",
    }

    # H6: Include pool stats in health check response
    if pool_stats:
        response["pool"] = pool_stats

    return response


# ---------------------------------------------------------------------------
# Mount sub-routers (must be after all dependencies are defined)
# ---------------------------------------------------------------------------
_mount_sub_routers()
