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
from shared.config import Environment, get_settings
from shared.logging_config import LogContext, get_logger, setup_logging
from shared.metrics import incr, observe
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

from api.dependencies import (
    _pool_manager,
    get_current_user_id,
    get_pool,
    require_admin_user_id,
)


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

# CRITICAL: Add response compression middleware (early in stack to compress all responses)
from shared.api_compression import CompressionMiddleware, create_compression_config

compression_config = create_compression_config(
    min_size=512,  # Compress responses > 512 bytes
    enable_gzip=True,
    enable_brotli=True,
    enable_deflate=True,
)
app.add_middleware(CompressionMiddleware, config=compression_config)

# Add Request ID middleware for distributed tracing
setup_request_id_middleware(app)

# M3: API Versioning - Register versioned routers
# Note: api_v2 router is already registered below with prefix /api/v2
# For v1, we use the default routes (no prefix)


# M3: API Versioning Middleware - Add version headers and handle version negotiation
@app.middleware("http")
async def api_versioning_middleware(request: Request, call_next):
    """Add API version headers and handle version negotiation.

    Headers added:
    - X-API-Version: Actual API version used (v1 or v2)
    - X-Supported-Versions: Comma-separated list of supported versions
    - Deprecation, Sunset: For deprecated endpoints (per RFC 8594)
    - X-API-Deprecated, X-API-Sunset-Date: Custom deprecation headers (per API_VERSIONING.md)

    Version negotiation:
    - URL /api/v2/* implies v2; otherwise Accept-Version header or default v1
    - If Accept-Version not supported, returns 400 with supported versions
    """
    # Infer version from path: /api/v2/* always uses v2
    path = request.url.path
    if path.startswith("/api/v2/"):
        effective_version = "v2"
        request.state.api_version = "v2"
    else:
        requested_version = request.headers.get("Accept-Version")
        if requested_version:
            requested_version = requested_version.strip().lower()
            if requested_version not in SUPPORTED_VERSIONS:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "UNSUPPORTED_API_VERSION",
                            "message": f"API version '{requested_version}' is not supported",
                            "detail": f"Supported versions: {', '.join(SUPPORTED_VERSIONS)}",
                            "requested_version": requested_version,
                            "supported_versions": SUPPORTED_VERSIONS,
                        }
                    },
                    headers={
                        "X-API-Version": API_VERSION,
                        "X-Supported-Versions": ",".join(SUPPORTED_VERSIONS),
                    },
                )
            request.state.api_version = requested_version
            effective_version = requested_version
        else:
            request.state.api_version = API_VERSION
            effective_version = API_VERSION

    # Process request
    response = await call_next(request)

    # Add API version headers to response (reflect actual version used)
    response.headers["X-API-Version"] = effective_version
    response.headers["X-Supported-Versions"] = ",".join(SUPPORTED_VERSIONS)

    # Deprecation headers per API_VERSIONING.md and RFC 8594
    for prefix, sunset_date in DEPRECATED_PATHS:
        if path.startswith(prefix):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = sunset_date
            response.headers["X-API-Deprecated"] = "true"
            response.headers["X-API-Sunset-Date"] = sunset_date
            break

    return response


import time

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
    exempt_paths = {"/health", "/healthz", "/csrf/prepare"}
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


@app.middleware("http")
async def idempotency_middleware(request: Request, call_next):
    """C2: Idempotency Keys - Prevent duplicate writes on retries.

    Checks for Idempotency-Key header on POST/PUT/PATCH requests.
    If present, caches the response in Redis and returns cached response
    for duplicate requests within the TTL window.
    """
    import json

    # Only apply to write operations
    if request.method not in ["POST", "PUT", "PATCH"]:
        return await call_next(request)

    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        # No idempotency key provided - proceed normally
        # (Optional: could require it for certain endpoints)
        return await call_next(request)

    # Validate key format (UUID or alphanumeric, max 128 chars)
    if (
        not idempotency_key
        or len(idempotency_key) > 128
        or not idempotency_key.replace("-", "").replace("_", "").isalnum()
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Idempotency-Key format. Must be alphanumeric, max 128 characters.",
        )

    # Check Redis for cached response
    if _settings.redis_url:
        try:
            from shared.redis_client import get_redis

            r = await get_redis()
            # Scope by method+path+user to prevent cross-user/cross-endpoint collisions
            user_scope = "anon"
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer ") and _settings.jwt_secret:
                try:
                    token = auth_header.replace("Bearer ", "").strip()
                    payload = pyjwt.decode(
                        token, _settings.jwt_secret, algorithms=["HS256"], audience="authenticated"
                    )
                    user_scope = payload.get("sub") or "anon"
                except Exception:
                    pass
            scope = f"{request.method}:{request.url.path}:{user_scope}"
            cache_key = f"idempotency:{scope}:{idempotency_key}"

            # CRITICAL: Use atomic SET NX to prevent race condition
            # Two requests with same key will both check, but only one can set the lock
            lock_key = f"{cache_key}:lock"
            lock_acquired = await r.set(lock_key, "1", nx=True, ex=30)  # 30 second lock

            if not lock_acquired:
                # Another request is processing with this key, wait and check cache
                import asyncio

                await asyncio.sleep(0.1)  # Brief wait
                cached = await r.get(cache_key)
                if cached:
                    logger.info(
                        "Idempotent request detected (race condition avoided) - returning cached response",
                        extra={
                            "idempotency_key": idempotency_key[:16] + "...",
                            "path": request.url.path,
                        },
                    )
                    try:
                        cached_data = json.loads(cached)
                        return JSONResponse(
                            content=cached_data.get("body", {}),
                            status_code=cached_data.get("status_code", 200),
                            headers=cached_data.get("headers", {}),
                        )
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse cached idempotency response")
                        # Release lock and fall through
                        await r.delete(lock_key)
                        return await call_next(request)
                # No cache yet, release lock and proceed (shouldn't happen but handle gracefully)
                await r.delete(lock_key)
                # Continue to process request normally - fall through to line 425

            # Check for existing cached response (double-check after acquiring lock)
            cached = await r.get(cache_key)
            if cached:
                # Release lock since we found cached response
                await r.delete(lock_key)
                logger.info(
                    "Idempotent request detected - returning cached response",
                    extra={
                        "idempotency_key": idempotency_key[:16] + "...",
                        "path": request.url.path,
                    },
                )
                try:
                    cached_data = json.loads(cached)
                    return JSONResponse(
                        content=cached_data.get("body", {}),
                        status_code=cached_data.get("status_code", 200),
                        headers=cached_data.get("headers", {}),
                    )
                except json.JSONDecodeError:
                    logger.warning("Failed to parse cached idempotency response")
                    # Do not reprocess - idempotency would be violated (duplicate mutations)
                    return JSONResponse(
                        content={"error": "Cached response corrupted"},
                        status_code=503,
                    )

            # Process request (we hold the lock)
            try:
                response = await call_next(request)
            finally:
                # Always release lock
                await r.delete(lock_key)

            # Cache successful responses (2xx status codes)
            if 200 <= response.status_code < 300:
                try:
                    # Read response body
                    response_body = b""
                    async for chunk in response.body_iterator:
                        response_body += chunk

                    # Parse JSON if possible
                    try:
                        body_json = json.loads(response_body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        body_json = {"raw": response_body.decode(errors="ignore")[:100]}

                    # Cache response for 1 hour
                    cache_data = {
                        "body": body_json,
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    }
                    await r.setex(cache_key, 3600, json.dumps(cache_data))

                    # Return new response with body
                    return JSONResponse(
                        content=body_json,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                    )
                except Exception as e:
                    logger.warning("Failed to cache idempotency response: %s", e)
                    # Return original response if caching fails
                    return response
            else:
                # Don't cache error responses
                return response

        except Exception as e:
            logger.warning("Idempotency check failed (Redis unavailable): %s", e)
            # Fail open - process request normally if Redis is down
            return await call_next(request)
    else:
        # No Redis - can't provide idempotency (log warning in production)
        if _settings.env.value == "prod":
            logger.warning(
                "Idempotency-Key provided but Redis not available - idempotency disabled"
            )
        return await call_next(request)


@app.middleware("http")
async def latency_middleware(request: Request, call_next):
    """Track API latency and performance metrics (H3: API Performance Monitoring).

    M4: Enhanced with OpenTelemetry span attributes for distributed tracing.
    """
    # M4: Get current span (created by FastAPI instrumentation) and add attributes
    from opentelemetry import trace

    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        # Add request attributes to existing span
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.route", request.url.path)

    start_time = time.time()
    path = request.url.path
    method = request.method

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # M4: Add response attributes to span
        if span and span.get_span_context().is_valid:
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute(
                "http.response_size", response.headers.get("content-length", "0")
            )

        # Record latency metric
        observe(
            "api.latency",
            duration,
            tags={
                "path": path,
                "method": method,
                "status_code": str(response.status_code),
            },
        )

        # Track slow requests (>1 second)
        if duration > 1.0:
            logger.warning(
                "Slow API request detected",
                extra={
                    "path": path,
                    "method": method,
                    "duration": duration,
                    "status_code": response.status_code,
                },
            )
            incr(
                "api.slow_requests",
                tags={
                    "path": path,
                    "method": method,
                    "status_code": str(response.status_code),
                },
            )

        # Track request count
        incr(
            "api.requests",
            tags={
                "path": path,
                "method": method,
                "status_code": str(response.status_code),
            },
        )

        return response
    except Exception as exc:
        duration = time.time() - start_time

        # M4: Record exception in span
        if span and span.get_span_context().is_valid:
            span.record_exception(exc)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
            span.set_attribute("http.status_code", 500)

            # Record error latency
            observe(
                "api.latency",
                duration,
                tags={
                    "path": path,
                    "method": method,
                    "status_code": "500",
                    "error": "true",
                },
            )
            incr(
                "api.errors",
                tags={
                    "path": path,
                    "method": method,
                    "error_type": type(exc).__name__,
                },
            )
            raise


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
        ip_limiter = get_rate_limiter(
            f"api:{client_ip}", max_calls=100, window_seconds=60
        )
        if not await ip_limiter.acquire():
            incr("api.rate_limit_exceeded", tags={"ip_hash": mask_ip(client_ip)})
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
    import api.admin as admin_mod

    app.dependency_overrides[admin_mod._get_pool] = get_pool
    app.dependency_overrides[admin_mod._get_tenant_ctx] = get_tenant_context
    app.dependency_overrides[admin_mod._get_admin_user_id] = require_admin_user_id
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
    if "TooManyConnections" in exc_name or "PoolTimeout" in exc_name or (
        isinstance(exc, (TimeoutError, ConnectionError)) and "pool" in str(exc).lower()
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
    except Exception as exc:
        logger.error("[TENANT] Error resolving tenant context: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resolve tenant context")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ResumeParseResponse(BaseModel):
    user_id: str
    profile: CanonicalProfile
    resume_url: str | None = None


class AnswerItem(BaseModel):
    input_id: str = Field(
        ..., min_length=1, max_length=100, description="Input identifier"
    )
    answer: str = Field(
        ..., max_length=5000, description="Answer text (max 5000 characters)"
    )

    @field_validator("answer")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        """MEDIUM: Sanitize HTML and prompt injection in user input."""
        from packages.backend.domain.sanitization import sanitize_text_input
        from shared.ai_validation import sanitize_for_ai

        v = sanitize_text_input(v, max_length=5000)
        # Prompt injection protection before answers reach agent LLM
        r = sanitize_for_ai(v, max_length=5000, min_length=None)
        return r.sanitized_input or v[:5000] if r.is_valid else v[:5000]


class ResumeTaskRequest(BaseModel):
    application_id: str = Field(..., min_length=36, max_length=36, description="Application identifier")
    answers: list[AnswerItem] = Field(
        ...,
        max_length=100,  # HIGH: Limit to prevent DoS
        description="List of answers (max 100)",
    )


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
    field_label: str = Field(
        ..., min_length=1, max_length=200, description="Field label"
    )
    field_type: str = Field(default="text", max_length=50, description="Field type")
    answer_value: str = Field(
        ..., max_length=5000, description="Answer value (max 5000 characters)"
    )

    @field_validator("field_label")
    @classmethod
    def sanitize_field_label(cls, v: str) -> str:
        from packages.backend.domain.sanitization import sanitize_text_input
        return sanitize_text_input(v, max_length=200)

    @field_validator("field_type")
    @classmethod
    def sanitize_field_type(cls, v: str) -> str:
        from packages.backend.domain.sanitization import sanitize_text_input
        return sanitize_text_input(v, max_length=50)

    @field_validator("answer_value")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        from packages.backend.domain.sanitization import sanitize_text_input
        return sanitize_text_input(v, max_length=5000)


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
    skill: str = Field(..., min_length=1, max_length=100, description="Skill name")
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence level (0.0-1.0)"
    )
    years_actual: float | None = Field(
        default=None, ge=0.0, le=50.0, description="Years of experience"
    )
    context: str = Field(default="", max_length=500, description="Context description")
    last_used: str | None = Field(
        default=None, max_length=50, description="Last used date"
    )
    verified: bool = Field(default=False, description="Whether skill is verified")
    related_to: list[str] = Field(
        default_factory=list, max_length=20, description="Related skills (max 20)"
    )
    source: str = Field(default="manual", max_length=50, description="Skill source")
    project_count: int = Field(
        default=0, ge=0, le=1000, description="Number of projects using this skill"
    )

    @field_validator("skill", "context", "last_used", "source")
    @classmethod
    def sanitize_text(cls, v: str | None) -> str | None:
        """BC4: Sanitize free-text fields to prevent XSS."""
        if v is None:
            return None
        from packages.backend.domain.sanitization import sanitize_text_input
        return sanitize_text_input(v, max_length=500)

    @field_validator("related_to")
    @classmethod
    def sanitize_related_to(cls, v: list[str]) -> list[str]:
        """BC4: Sanitize related skill names."""
        from packages.backend.domain.sanitization import sanitize_text_input
        return [sanitize_text_input(x, max_length=100) for x in (v or [])[:20]]


class SaveSkillsRequest(BaseModel):
    skills: list[RichSkillRequest] = Field(
        ...,
        max_length=500,  # HIGH: Limit to prevent DoS with large skill lists
        description="List of skills (max 500)",
    )


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

    async with db.acquire() as conn:
        async with conn.transaction():
            # Clear existing skills (empty list = clear all)
            await conn.execute(
                "DELETE FROM public.user_skills WHERE user_id = $1", user_id
            )

            if not body.skills:
                logger.info(
                    "[SKILLS] Cleared all skills for user",
                    extra={"user_id": user_id},
                )
                return {"status": "saved", "count": 0}

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

            # MEDIUM: Use centralized calculate_completeness() instead of SQL increments
            # MEDIUM: Add null check for user_id (OB-008: return proper body even in edge case)
            if not user_id:
                logger.warning("Cannot update completeness: user_id is None")
                return {"status": "saved", "count": len(body.skills)}

            from packages.backend.domain.deep_profile import calculate_completeness
            from packages.backend.domain.profile_assembly import assemble_profile

            deep_profile = await assemble_profile(conn, user_id)
            if deep_profile:
                completeness_score = calculate_completeness(deep_profile)
                # Verify user exists before updating
                user_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM public.users WHERE id = $1)",
                    user_id,
                )
                if user_exists:
                    await conn.execute(
                        "UPDATE public.users SET profile_completeness = $1 WHERE id = $2",
                        completeness_score,
                        user_id,
                    )

    logger.info(
        "[SKILLS] Skills saved successfully",
        extra={"user_id": user_id, "count": len(body.skills)},
    )
    return {"status": "saved", "count": len(body.skills)}


class WorkStyleRequest(BaseModel):
    autonomy_preference: str = Field(
        default="medium",
        pattern="^(low|medium|high)$",  # HIGH: Validate enum values
        description="Autonomy preference",
    )
    learning_style: str = Field(
        default="building",
        pattern="^(building|studying|mixed|docs|hands_on)$",
        description="Learning style",
    )
    company_stage_preference: str = Field(
        default="flexible",
        pattern="^(startup|early_startup|growth|enterprise|flexible)$",
        description="Company stage preference",
    )
    communication_style: str = Field(
        default="mixed",
        pattern="^(async|sync|mixed|flexible)$",
        description="Communication style",
    )
    pace_preference: str = Field(
        default="steady",
        pattern="^(fast|steady|relaxed|methodical|flexible)$",
        description="Pace preference",
    )
    ownership_preference: str = Field(
        default="team",
        pattern="^(individual|team|mixed|solo|lead|flexible)$",
        description="Ownership preference",
    )
    career_trajectory: str = Field(
        default="open",
        pattern="^(open|focused|exploring|ic|tech_lead|manager|founder)$",
        description="Career trajectory (ic, tech_lead, manager, founder, open, focused, exploring)",
    )

    model_config = ConfigDict(extra="ignore")


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
        extra={"user_id": user_id},
    )

    # HIGH: Wrap multi-table updates in transaction to ensure atomicity
    from packages.backend.domain.repositories import db_transaction

    async with db_transaction(db) as conn:
        # Check if user has already saved work style (only add completeness on first save)
        await conn.fetchval(
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

        # MEDIUM: Use centralized calculate_completeness() instead of SQL increments
        # Recalculate completeness after work style is saved
        # MEDIUM: Add null check for user_id
        if not user_id:
            logger.warning("Cannot update completeness: user_id is None")
            return

        from packages.backend.domain.deep_profile import calculate_completeness
        from packages.backend.domain.profile_assembly import assemble_profile

        deep_profile = await assemble_profile(conn, user_id)
        if deep_profile:
            completeness_score = calculate_completeness(deep_profile)
            # Verify user exists before updating
            user_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM public.users WHERE id = $1)",
                user_id,
            )
            if user_exists:
                await conn.execute(
                    "UPDATE public.users SET profile_completeness = $1 WHERE id = $2",
                    completeness_score,
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
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """User dashboard data for mobile v3 home screen + widget."""
    user_id = ctx.user_id
    tenant_id = ctx.tenant_id
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
               FROM public.applications
               WHERE user_id = $1 AND (tenant_id = $2 OR tenant_id IS NULL)""",
            user_id,
            tenant_id,
        )
        recent = await conn.fetch(
            """SELECT a.id, j.title AS job_title, a.status::text, a.updated_at
               FROM public.applications a
               LEFT JOIN public.jobs j ON j.id = a.job_id
               WHERE a.user_id = $1 AND (a.tenant_id = $2 OR a.tenant_id IS NULL)
               ORDER BY a.updated_at DESC LIMIT 10""",
            user_id,
            tenant_id,
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
    if file.content_type not in ("application/pdf",):
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

    # MIME validation: verify PDF magic bytes (prevent content-type spoofing)
    if len(pdf_bytes) < 8 or not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF format - file content does not match declared type",
        )

    # Virus scan before processing
    from shared.virus_scanner import is_file_type_allowed, scan_uploaded_file

    filename = file.filename or "resume.pdf"
    if not is_file_type_allowed(filename, file.content_type or "application/pdf"):
        raise HTTPException(status_code=400, detail="File type not allowed")
    scan_result = await scan_uploaded_file(pdf_bytes, filename)
    if not scan_result.clean:
        logger.warning(
            "[RESUME] Virus scan failed",
            extra={"tenant_id": ctx.tenant_id, "filename": filename[:50]},
        )
        incr("api.resume_parse.virus_scan_failed", tags={"tenant_id": ctx.tenant_id})
        raise HTTPException(
            status_code=400,
            detail="File security scan failed. Please upload a different file.",
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

    incr("api.resume_parse.success", tags={"tenant_id": ctx.tenant_id})
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
        logger.info(
            "[RESUME_TASK] Application not found",
            extra={"application_id": body.application_id, "tenant_id": ctx.tenant_id},
        )
        incr("api.resume_task.not_found", tags={"tenant_id": ctx.tenant_id})
        raise HTTPException(
            status_code=404, detail="Application not found or not owned by user"
        )

    if app_row["status"] not in ("REQUIRES_INPUT",):
        logger.info(
            "[RESUME_TASK] Status conflict",
            extra={
                "application_id": body.application_id,
                "status": app_row["status"],
                "tenant_id": ctx.tenant_id,
            },
        )
        incr(
            "api.resume_task.status_conflict",
            tags={"status": app_row["status"], "tenant_id": ctx.tenant_id},
        )
        raise HTTPException(
            status_code=409,
            detail=f"Application status is '{app_row['status']}', expected REQUIRES_INPUT",
        )

    async with db_transaction(db) as conn:
        # Update each answer and mark resolved (scope by application_id to prevent IDOR)
        await InputRepo.update_answers(
            conn,
            [{"input_id": a.input_id, "answer": a.answer} for a in body.answers],
            application_id=body.application_id,
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

    incr("api.resume_task.success", tags={"tenant_id": ctx.tenant_id})
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
            conn, application_id, tenant_id=ctx.tenant_id, user_id=ctx.user_id
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

    # Validate path components - prevent path traversal (incl. encoded variants)
    from urllib.parse import unquote

    decoded_path = unquote(path)
    if ".." in decoded_path or ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    if "%2e" in path.lower() or "%252e" in path.lower():
        raise HTTPException(status_code=400, detail="Invalid path")
    normalized_path = os.path.normpath(decoded_path)
    if normalized_path.startswith("/") or normalized_path.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid path")

    # SECURITY: Add tenant isolation to storage path
    # Only allow access to files within user's tenant directory
    storage_path = f"{tenant_id}/{bucket}/{normalized_path}"

    storage = get_storage_service()

    try:
        data = await storage.download_file(storage_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception:
        logger.exception("Storage download failed for %s", storage_path)
        raise HTTPException(status_code=500, detail="Failed to retrieve file")

    # Determine content type based on file extension
    content_type = mimetypes.guess_type(normalized_path)[0] or "application/octet-stream"

    return Response(content=data, media_type=content_type)


# ---------------------------------------------------------------------------
# Mount sub-routers (must be after all dependencies are defined)
# ---------------------------------------------------------------------------
_mount_sub_routers()
