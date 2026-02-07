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
import logging
import os
import time
import uuid
from typing import Any

import asyncpg
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Header,
    Path,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from shared.config import Settings, get_settings, settings_dependency
from shared.logging_config import LogContext, setup_logging, get_logger
from shared.metrics import incr, observe, dump as metrics_dump
from backend.domain.models import (
    CanonicalContact,
    CanonicalEducation,
    CanonicalExperience,
    CanonicalProfile,
    CanonicalSkills,
    ErrorDetail,
    ErrorResponse,
    normalize_profile,
)
from backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    InputRepo,
    JobRepo,
    ProfileRepo,
    TenantRepo,
    db_transaction,
    record_event,
)
from backend.domain.tenant import (
    TenantContext,
    TenantScopeError,
    resolve_tenant_context,
    assert_tenant_owns,
)
from backend.domain.quotas import QuotaExceededError, check_can_create_application
from backend.llm.client import LLMClient, LLMError
from backend.llm.contracts import (
    ResumeParseResponse_V1,
    build_resume_parse_prompt,
)
from backend.domain.analytics_events import (
    RESUME_PARSED_SUCCESS,
    RESUME_PARSED_FAILED,
    APPLICATION_STATUS_CHANGED,
)

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

app = FastAPI(title="Sorce API", version="0.4.0")

# ---------------------------------------------------------------------------
# LLM client singleton
# ---------------------------------------------------------------------------
_llm_client = LLMClient(_settings)

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

    from partners.university.router import router as uni_router
    import partners.university.router as uni_mod
    app.dependency_overrides[uni_mod._get_pool] = get_pool
    app.dependency_overrides[uni_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(uni_router)

    import api.developer as dev_mod
    app.dependency_overrides[dev_mod._get_pool] = get_pool
    app.dependency_overrides[dev_mod._get_tenant_ctx] = get_tenant_context
    app.include_router(dev_mod.router)

# NOTE: _mount_sub_routers() is called at the bottom of this file,
# after get_pool and get_tenant_context are defined.

# ---------------------------------------------------------------------------
# Database pool lifecycle
# ---------------------------------------------------------------------------
pool: asyncpg.Pool | None = None


@app.on_event("startup")
async def startup() -> None:
    global pool
    s = get_settings()
    from backend.blueprints.registry import load_default_blueprints
    load_default_blueprints()
    # Determine SSL: skip for Render internal connections, use for external
    ssl_arg: Any = False
    if "pooler.supabase.com" in s.database_url or "supabase.co" in s.database_url:
        import ssl as _ssl
        ssl_ctx = _ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = _ssl.CERT_NONE
        ssl_arg = ssl_ctx
    for attempt in range(1, 4):
        try:
            pool = await asyncpg.create_pool(
                s.database_url, min_size=s.db_pool_min, max_size=s.db_pool_max,
                ssl=ssl_arg,
                statement_cache_size=0,
            )
            logger.info("Database pool created (env=%s)", s.env.value)
            break
        except Exception as exc:
            logger.warning("DB pool attempt %d/3 failed: %s", attempt, exc)
            if attempt < 3:
                import asyncio
                await asyncio.sleep(3 * attempt)
    else:
        logger.error("Could not create DB pool after 3 attempts")
        return
    # Auto-migrate: if auth schema missing, run all SQL files
    try:
        async with pool.acquire() as conn:
            has_auth = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name='auth')"
            )
            if not has_auth:
                logger.info("Running auto-migration (first boot)...")
                await _run_migrations(conn)
    except Exception as exc:
        logger.warning("Auto-migration check failed: %s", exc)


async def _run_migrations(conn: asyncpg.Connection) -> None:
    """Run auth shim + schema.sql + all numbered migrations."""
    import pathlib
    base = pathlib.Path(__file__).resolve().parent.parent
    # Auth compatibility shim
    auth_shim = """
    CREATE SCHEMA IF NOT EXISTS auth;
    CREATE TABLE IF NOT EXISTS auth.users (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        email text,
        encrypted_password text,
        email_confirmed_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        raw_user_meta_data jsonb DEFAULT '{}'::jsonb
    );
    """
    await conn.execute(auth_shim)
    logger.info("  auth shim created")
    # Base schema
    schema_file = base / "supabase" / "schema.sql"
    if schema_file.exists():
        await conn.execute(schema_file.read_text(encoding="utf-8"))
        logger.info("  schema.sql applied")
    # Numbered migrations
    mig_dir = base / "supabase" / "migrations"
    if mig_dir.exists():
        for mf in sorted(mig_dir.glob("[0-9]*.sql")):
            sql = mf.read_text(encoding="utf-8").strip()
            if not sql:
                continue
            try:
                await conn.execute(sql)
                logger.info("  %s applied", mf.name)
            except Exception as e:
                msg = str(e)
                if "already exists" in msg or "duplicate" in msg.lower():
                    logger.info("  %s skipped (already exists)", mf.name)
                else:
                    logger.warning("  %s FAILED: %s", mf.name, msg[:200])


@app.on_event("shutdown")
async def shutdown() -> None:
    global pool
    if pool:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise HTTPException(status_code=503, detail="Database pool not available")
    return pool


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


# ---------------------------------------------------------------------------
# Auth dependency – extract user_id from Supabase JWT
# ---------------------------------------------------------------------------

async def get_current_user_id(authorization: str = Header(...)) -> str:
    """
    Decode a Supabase JWT (HS256) and return the `sub` claim as user_id.
    """
    import jwt as pyjwt

    s = get_settings()
    if not s.supabase_jwt_secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")

    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(
            token, s.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated"
        )
        user_id: str = payload["sub"]
        return user_id
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")


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
# Supabase Storage helper
# ---------------------------------------------------------------------------

async def upload_to_supabase_storage(
    bucket: str,
    path: str,
    data: bytes,
    content_type: str = "application/pdf",
) -> str:
    import httpx

    s = get_settings()
    url = f"{s.supabase_url}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {s.supabase_service_key}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=data, headers=headers)
        resp.raise_for_status()

    return f"{s.supabase_url}/storage/v1/object/public/{bucket}/{path}"


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    import fitz  # PyMuPDF

    text_parts: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


# ---------------------------------------------------------------------------
# Resume parsing via LLM client
# ---------------------------------------------------------------------------

async def parse_resume_to_profile(resume_text: str) -> dict:
    """Use the LLM client with the versioned resume parse contract."""
    prompt = build_resume_parse_prompt(resume_text)
    result = await _llm_client.call(
        prompt=prompt,
        response_format=ResumeParseResponse_V1,
    )
    return result.model_dump()


# ---------------------------------------------------------------------------
# Server-side analytics helper
# ---------------------------------------------------------------------------

async def _emit_analytics_event(
    pool: asyncpg.Pool,
    event_type: str,
    *,
    tenant_id: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    properties: dict | None = None,
) -> None:
    """Insert a server-generated analytics event (fire-and-forget)."""
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.analytics_events
                    (tenant_id, user_id, session_id, event_type, properties)
                VALUES ($1, $2, $3, $4, $5::jsonb)
                """,
                tenant_id,
                user_id,
                session_id,
                event_type,
                json.dumps(properties or {}),
            )
    except Exception as exc:
        logger.warning("Failed to emit analytics event %s: %s", event_type, exc)


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

    pdf_bytes = await file.read()

    # 1. Upload raw PDF to Supabase Storage
    s = get_settings()
    storage_path = f"{user_id}/{uuid.uuid4()}.pdf"
    resume_url = await upload_to_supabase_storage(
        s.supabase_storage_bucket, storage_path, pdf_bytes
    )

    # 2. Extract text
    resume_text = extract_text_from_pdf(pdf_bytes)
    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")

    # 3. LLM parse
    t0 = time.monotonic()
    try:
        raw_profile = await parse_resume_to_profile(resume_text)
    except LLMError as exc:
        observe("api.llm_latency_seconds", time.monotonic() - t0, {"endpoint": "resume_parse"})
        incr("api.resume_parse.llm_error")
        # Server-side analytics: resume parse failed
        await _emit_analytics_event(
            db, RESUME_PARSED_FAILED,
            tenant_id=ctx.tenant_id, user_id=user_id,
            properties={"error": str(exc)[:200]},
        )
        raise HTTPException(
            status_code=502,
            detail=f"Resume parsing failed: {exc}",
        )
    observe("api.llm_latency_seconds", time.monotonic() - t0, {"endpoint": "resume_parse"})

    # 4. Normalize into canonical schema
    canonical = normalize_profile(raw_profile)

    # 5. Upsert into profiles (store the canonical dict)
    async with db.acquire() as conn:
        await ProfileRepo.upsert(conn, user_id, canonical.model_dump(), resume_url, tenant_id=ctx.tenant_id)

    # Server-side analytics: resume parse succeeded
    await _emit_analytics_event(
        db, RESUME_PARSED_SUCCESS,
        tenant_id=ctx.tenant_id, user_id=user_id,
        properties={"resume_url": resume_url},
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
    await _emit_analytics_event(
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
    async with db.acquire() as conn:
        detail = await ApplicationRepo.get_detail(conn, application_id, tenant_id=ctx.tenant_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Application not found")

    # Serialize UUIDs and datetimes for JSON
    def _serialize(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_serialize(v) for v in obj]
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return obj

    return ApplicationDetailResponse(**_serialize(detail))


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
    s = get_settings()
    db_ok = False
    try:
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception:
        pass

    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "env": s.env.value,
        "db": "ok" if db_ok else "unreachable",
        "metrics": metrics_dump(),
    }


# ---------------------------------------------------------------------------
# Mount sub-routers (must be after all dependencies are defined)
# ---------------------------------------------------------------------------
_mount_sub_routers()
