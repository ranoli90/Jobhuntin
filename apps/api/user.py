"""User-facing web API — endpoints consumed by the web app (not admin).

- GET  /applications           — list applications for current user
- POST /applications           — create application from swipe (job_id, decision)
- POST /applications/{id}/answer — answer a hold question (single answer)
- GET  /jobs                   — list jobs with optional filters
- GET  /profile                — current user profile + onboarding state
- PATCH /profile              — update profile / preferences / onboarding
- POST /profile/resume        — upload resume (PDF) and parse
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import asyncpg
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi import Path as FastAPIPath
from pydantic import BaseModel, Field, field_validator, model_validator

from packages.backend.domain.document_processor import create_document_processor
from packages.backend.domain.masking import mask_email
from packages.backend.domain.quotas import (
    QuotaExceededError,
    check_can_create_application,
)
from packages.backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    InputRepo,
    JobRepo,
    ProfileRepo,
    db_transaction,
)
from packages.backend.domain.resume import process_resume_upload
from packages.backend.domain.tenant import TenantContext
from shared.config import get_settings
from shared.logging_config import get_logger, sanitize_for_log
from shared.metrics import RateLimiter
from shared.storage import get_storage_service

logger = get_logger("sorce.user")

# Initialize document processor for file type validation
processor = create_document_processor()

router = APIRouter(tags=["user"])

# Per-user rate limiters to prevent abuse on profile writes/uploads
_profile_limiters: dict[str, tuple[RateLimiter, float]] = {}
_upload_limiters: dict[str, tuple[RateLimiter, float]] = {}
_apply_limiters: dict[str, tuple[RateLimiter, float]] = {}
_job_refresh_limiters: dict[str, tuple[RateLimiter, float]] = {}
_LIMITER_TTL = 3600  # 1 hour
_APPLY_LIMIT_PER_MINUTE = 60  # P1: Rate limit applies (prevents spam)
_JOB_REFRESH_WINDOW = 10800  # 3 hours


def _get_job_refresh_limiter(user_id: str) -> RateLimiter:
    """Rate limiter for job refresh: 1 per 3 hours per user."""
    import time as _time

    now = _time.monotonic()
    entry = _job_refresh_limiters.get(user_id)
    if entry and now - entry[1] < _LIMITER_TTL:
        _job_refresh_limiters[user_id] = (entry[0], now)
        return entry[0]
    expired = [
        k for k, (_, ts) in _job_refresh_limiters.items() if now - ts > _LIMITER_TTL
    ]
    for k in expired:
        _job_refresh_limiters.pop(k, None)
    limiter = RateLimiter(
        max_calls=1,
        window_seconds=float(_JOB_REFRESH_WINDOW),
        name=f"job_refresh:{user_id}",
    )
    _job_refresh_limiters[user_id] = (limiter, now)
    return limiter


def _get_profile_limiter(user_id: str) -> RateLimiter:
    import time as _time

    now = _time.monotonic()
    entry = _profile_limiters.get(user_id)
    if entry and now - entry[1] < _LIMITER_TTL:
        _profile_limiters[user_id] = (entry[0], now)
        return entry[0]
    # Evict stale entries
    expired = [k for k, (_, ts) in _profile_limiters.items() if now - ts > _LIMITER_TTL]
    for k in expired:
        _profile_limiters.pop(k, None)
    limiter = RateLimiter(max_calls=30, window_seconds=300.0, name=f"profile:{user_id}")
    _profile_limiters[user_id] = (limiter, now)
    return limiter


def _get_apply_limiter(user_id: str) -> RateLimiter:
    import time as _time

    now = _time.monotonic()
    entry = _apply_limiters.get(user_id)
    if entry and now - entry[1] < _LIMITER_TTL:
        _apply_limiters[user_id] = (entry[0], now)
        return entry[0]
    expired = [k for k, (_, ts) in _apply_limiters.items() if now - ts > _LIMITER_TTL]
    for k in expired:
        _apply_limiters.pop(k, None)
    limiter = RateLimiter(
        max_calls=_APPLY_LIMIT_PER_MINUTE,
        window_seconds=60.0,
        name=f"apply:{user_id}",
    )
    _apply_limiters[user_id] = (limiter, now)
    return limiter


def _get_upload_limiter(user_id: str) -> RateLimiter:
    import time as _time

    now = _time.monotonic()
    entry = _upload_limiters.get(user_id)
    if entry and now - entry[1] < _LIMITER_TTL:
        _upload_limiters[user_id] = (entry[0], now)
        return entry[0]
    # Evict stale entries
    expired = [k for k, (_, ts) in _upload_limiters.items() if now - ts > _LIMITER_TTL]
    for k in expired:
        _upload_limiters.pop(k, None)
    limiter = RateLimiter(max_calls=10, window_seconds=600.0, name=f"upload:{user_id}")
    _upload_limiters[user_id] = (limiter, now)
    return limiter


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    raise NotImplementedError("Tenant context dependency not injected")


def _status_to_web(status: str) -> str:
    """Map backend application_status to web status."""
    if status in ("QUEUED", "PROCESSING"):
        return "APPLYING"
    if status == "REQUIRES_INPUT":
        return "HOLD"
    if status in ("APPLIED", "SUBMITTED", "COMPLETED", "REGISTERED"):
        return "APPLIED"
    return "FAILED"


def _format_application_response(app) -> dict:
    """Format an application for API response."""
    # Handle both dict and Pydantic model inputs
    if hasattr(app, "model_dump"):
        app_dict = app.model_dump()
    elif hasattr(app, "dict"):
        app_dict = app.dict()
    else:
        app_dict = app

    return {
        "id": app_dict.get("id"),
        "status": _status_to_web(app_dict.get("status", "")),
        "job_title": app_dict.get("job_title"),
        "company_name": app_dict.get("company_name"),
        "location": _format_location(app_dict.get("location")),
        "salary_min": app_dict.get("salary_min"),
        "salary_max": app_dict.get("salary_max"),
        "remote": app_dict.get("remote", False),
    }


def _format_salary_range(salary_min: int | None, salary_max: int | None) -> str:
    """Format a salary range for display."""
    if salary_min is None and salary_max is None:
        return "Salary not specified"
    if salary_min == salary_max:
        return f"${salary_min:,}"
    if salary_max is None:
        return f"${salary_min:,}+"
    if salary_min is None:
        return f"Up to ${salary_max:,}"
    return f"${salary_min:,} - ${salary_max:,}"


def _format_location(location: str | None) -> str:
    """Format a location for display."""
    if not location:
        return "Location not specified"
    return location


# ---------------------------------------------------------------------------
# GET /applications
# ---------------------------------------------------------------------------


@router.get("/me/applications")
async def list_applications(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """List applications for the current user with pagination; status mapped for web (HOLD, APPLYING, etc.)."""
    # Validate and limit pagination parameters
    limit = max(5, min(limit, 100))  # Between 5 and 100 items
    offset = max(0, offset)

    async with db.acquire() as conn:
        # Query with tenant filter (works when applications.tenant_id exists)
        count_sql = """
            SELECT COUNT(*)::bigint AS total
            FROM   public.applications a
            JOIN   public.jobs j ON j.id = a.job_id
            WHERE  a.user_id = $1 AND (a.tenant_id = $2 OR a.tenant_id IS NULL)
              AND a.status != 'REJECTED'
              AND (a.snoozed_until IS NULL OR a.snoozed_until < now())
            """
        rows_sql = """
            SELECT a.id, a.status::text, a.updated_at, a.snoozed_until,
                   j.title AS job_title, j.company,
                   (
                       SELECT question FROM public.application_inputs
                       WHERE application_id = a.id AND resolved = false
                       ORDER BY created_at LIMIT 1
                   ) AS hold_question
            FROM   public.applications a
            JOIN   public.jobs j ON j.id = a.job_id
            WHERE  a.user_id = $1 AND (a.tenant_id = $2 OR a.tenant_id IS NULL)
              AND a.status != 'REJECTED'
              AND (a.snoozed_until IS NULL OR a.snoozed_until < now())
            ORDER  BY a.updated_at DESC
            LIMIT $3 OFFSET $4
            """
        try:
            count_result = await conn.fetchrow(
                count_sql,
                ctx.user_id,
                ctx.tenant_id,
            )
            rows = await conn.fetch(
                rows_sql,
                ctx.user_id,
                ctx.tenant_id,
                limit,
                offset,
            )
        except asyncpg.UndefinedColumnError:
            # applications.tenant_id or snoozed_until may not exist in older schemas
            count_sql_fallback = """
                SELECT COUNT(*)::bigint AS total
                FROM   public.applications a
                JOIN   public.jobs j ON j.id = a.job_id
                WHERE  a.user_id = $1
                  AND a.status != 'REJECTED'
                """
            rows_sql_fallback = """
                SELECT a.id, a.status::text, a.updated_at, NULL::timestamptz AS snoozed_until,
                       j.title AS job_title, j.company,
                       (
                           SELECT question FROM public.application_inputs
                           WHERE application_id = a.id AND resolved = false
                           ORDER BY created_at LIMIT 1
                       ) AS hold_question
                FROM   public.applications a
                JOIN   public.jobs j ON j.id = a.job_id
                WHERE  a.user_id = $1
                  AND a.status != 'REJECTED'
                ORDER  BY a.updated_at DESC
                LIMIT $2 OFFSET $3
                """
            count_result = await conn.fetchrow(count_sql_fallback, ctx.user_id)
            rows = await conn.fetch(
                rows_sql_fallback,
                ctx.user_id,
                limit,
                offset,
            )

        total_count = int(count_result["total"]) if count_result else 0

    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": str(r["id"]),
                "job_title": r["job_title"],
                "company": r["company"],
                "status": _status_to_web(r["status"]),
                "last_activity": (
                    r["updated_at"].isoformat() if r["updated_at"] else None
                ),
                "hold_question": (
                    r["hold_question"] if r["status"] == "REQUIRES_INPUT" else None
                ),
            }
        )

    # Calculate pagination metadata
    has_more = offset + limit < total_count
    offset + limit if has_more else None
    max(0, offset - limit) if offset > 0 else None

    # MEDIUM: Use standardized pagination format
    from packages.backend.domain.pagination import (
        PaginatedResponse,
        create_pagination_meta,
    )

    pagination_meta = create_pagination_meta(total_count, limit, offset)

    return PaginatedResponse(
        items=out,
        pagination=pagination_meta,
    ).model_dump()


# ---------------------------------------------------------------------------
# GET /me/applications/queue-stats — queue position and ETA for APPLYING apps
# ---------------------------------------------------------------------------


@router.get("/me/applications/queue-stats")
async def get_queue_stats(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Return queue position and estimated wait for user's APPLYING applications.
    #36: Queue position/ETA for users.
    """
    safe_fallback = {"applications": [], "queue_ahead": 0, "eta_minutes": 0}

    async with db.acquire() as conn:
        try:
            # Minimal query - only user_id, status, created_at (no priority_score/tenant_id)
            user_applying = await conn.fetch(
                """
                SELECT id, created_at
                FROM public.applications
                WHERE user_id = $1::uuid AND status = 'QUEUED'
                ORDER BY created_at ASC
                """,
                str(ctx.user_id),
            )
            if not user_applying:
                return safe_fallback

            first = user_applying[0]
            ahead = await conn.fetchval(
                """
                SELECT COUNT(*) FROM public.applications
                WHERE status = 'QUEUED' AND created_at < $1
                """,
                first["created_at"],
            )
            applications_out = [
                {"id": str(r["id"]), "priority_score": 0} for r in user_applying
            ]
        except Exception as e:
            logger.warning("queue-stats error: %s", e, exc_info=True)
            return safe_fallback

        avg_min_per_app = 2
        eta_minutes = max(0, int(ahead or 0) * avg_min_per_app)

        return {
            "applications": applications_out,
            "queue_ahead": ahead or 0,
            "eta_minutes": eta_minutes,
        }


# ---------------------------------------------------------------------------
# POST /applications (swipe: create application)
# ---------------------------------------------------------------------------


class CreateApplicationBody(BaseModel):
    job_id: str = Field(..., min_length=32, max_length=36, description="Job UUID")
    decision: Literal["ACCEPT", "REJECT"]


@router.post("/me/applications")
async def create_application(
    request: Request,
    body: CreateApplicationBody,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Create an application when user swipes ACCEPT; record REJECTED for REJECT.

    P0: Idempotency - Optional Idempotency-Key header. When provided with Redis,
    returns cached response for duplicate requests within 24h. ON CONFLICT handles
    DB-level dedup when Redis unavailable.
    """
    idempotency_key = request.headers.get("Idempotency-Key")
    _idem_cache_key = (
        f"idem:apply:{ctx.user_id}:{idempotency_key}"
        if idempotency_key and len(idempotency_key) <= 128
        else None
    )

    if _idem_cache_key and get_settings().redis_url:
        try:
            from shared.redis_client import get_redis

            r = await get_redis()
            cached = await r.get(_idem_cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug("Idempotency cache read failed: %s", e)

    async def _idem_set(result: dict[str, Any]) -> None:
        if not _idem_cache_key or not get_settings().redis_url:
            return
        try:
            from shared.redis_client import get_redis

            r = await get_redis()
            await r.setex(_idem_cache_key, 86400, json.dumps(result))  # 24h TTL
        except Exception as e:
            logger.debug("Idempotency cache write failed: %s", e)

    from shared.validators import validate_uuid

    # P1: Rate limit applies per user (60/min)
    apply_limiter = _get_apply_limiter(str(ctx.user_id))
    if not await apply_limiter.acquire():
        raise HTTPException(
            status_code=429,
            detail="Too many applications. Please wait a moment before applying to more jobs.",
        )

    validate_uuid(body.job_id, "job_id")

    # N-7: Import at function scope to keep it visible
    from packages.backend.domain.priority import compute_priority_score

    if body.decision != "ACCEPT":
        # H-3: Persist rejection with REJECTED status (not FAILED) to avoid
        # inflating failure metrics while still preventing job resurfacing.
        # CRITICAL: Use transaction to prevent race conditions in concurrent swipes
        async with db_transaction(db) as conn:
            # CRITICAL: Use SELECT FOR UPDATE to lock the row and prevent race conditions
            # This ensures only one request can check and insert for the same user_id + job_id
            existing_app = await conn.fetchrow(
                """
                SELECT id, status, created_at, updated_at
                FROM public.applications
                WHERE user_id = $1 AND job_id = $2 AND tenant_id = $3
                FOR UPDATE
                """,
                ctx.user_id,
                body.job_id,
                ctx.tenant_id,
            )

            if existing_app:
                # Return appropriate response for duplicate application
                logger.info(
                    f"[APPLICATION] Duplicate application prevented: user={ctx.user_id}, job={body.job_id}, existing_status={existing_app['status']}"
                )
                result = {
                    "status": "duplicate",
                    "message": "You have already applied to this job",
                    "existing_application": {
                        "id": str(existing_app["id"]),
                        "status": existing_app["status"],
                        "created_at": existing_app["created_at"].isoformat()
                        if existing_app["created_at"]
                        else None,
                        "updated_at": existing_app["updated_at"].isoformat()
                        if existing_app["updated_at"]
                        else None,
                    },
                }
                await _idem_set(result)
                return result

            job = await JobRepo.get_by_id(conn, body.job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            s = get_settings()
            blueprint_key = s.default_blueprint_key or "job-app"

            await conn.execute(
                """
                INSERT INTO public.applications
                    (user_id, job_id, tenant_id, blueprint_key, status, priority_score)
                VALUES ($1, $2, $3, $4, 'REJECTED', 0)
                ON CONFLICT (user_id, job_id) DO UPDATE SET
                    status = 'REJECTED',
                    updated_at = now()
                """,
                ctx.user_id,
                body.job_id,
                ctx.tenant_id,
                blueprint_key,
            )

        result = {"status": "recorded", "decision": body.decision}
        await _idem_set(result)
        return result

    # CRITICAL: Use transaction to prevent race conditions in concurrent swipes
    async with db_transaction(db) as conn:
        # CRITICAL: Use SELECT FOR UPDATE to lock the row and prevent race conditions
        # This ensures only one request can check and insert for the same user_id + job_id
        existing_app = await conn.fetchrow(
            """
            SELECT id, status, created_at, updated_at
            FROM public.applications
            WHERE user_id = $1 AND job_id = $2 AND tenant_id = $3
            FOR UPDATE
            """,
            ctx.user_id,
            body.job_id,
            ctx.tenant_id,
        )

        if existing_app:
            # Return appropriate response for duplicate application
            logger.info(
                f"[APPLICATION] Duplicate application prevented: user={ctx.user_id}, job={body.job_id}, existing_status={existing_app['status']}"
            )
            result = {
                "status": "duplicate",
                "message": "You have already applied to this job",
                "existing_application": {
                    "id": str(existing_app["id"]),
                    "status": existing_app["status"],
                    "created_at": existing_app["created_at"].isoformat()
                    if existing_app["created_at"]
                    else None,
                    "updated_at": existing_app["updated_at"].isoformat()
                    if existing_app["updated_at"]
                    else None,
                },
            }
            await _idem_set(result)
            return result

        # MEDIUM: Add null check for user-provided job_id
        if not body.job_id:
            raise HTTPException(status_code=400, detail="Job ID is required")

        job = await JobRepo.get_by_id(conn, body.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        try:
            await check_can_create_application(conn, ctx.tenant_id, ctx.plan)
        except QuotaExceededError as e:
            raise HTTPException(status_code=402, detail=e.message)

        s = get_settings()
        blueprint_key = s.default_blueprint_key or "job-app"

        priority = compute_priority_score(ctx.plan)

        app_id = await conn.fetchval(
            """
            INSERT INTO public.applications
                (user_id, job_id, tenant_id, blueprint_key, status, priority_score)
            VALUES ($1, $2, $3, $4, 'QUEUED', $5)
            ON CONFLICT (user_id, job_id) DO UPDATE SET
                status = 'QUEUED',
                updated_at = now()
            RETURNING id
            """,
            ctx.user_id,
            body.job_id,
            ctx.tenant_id,
            blueprint_key,
            priority,
        )

        # Wake auto-apply agent immediately (it listens for job_queue)
        await conn.execute("NOTIFY job_queue")

    result = {
        "id": str(app_id),
        "job_id": body.job_id,
        "status": "QUEUED",
        "decision": "ACCEPT",
        "tenant_id": ctx.tenant_id,
        "priority_score": priority,
    }
    await _idem_set(result)
    return result


# ---------------------------------------------------------------------------
# POST /applications/{job_id}/undo
# NOTE (M-7): The path parameter is `job_id` (not application_id).
# The endpoint looks up the application by (user_id, job_id) pair.
# ---------------------------------------------------------------------------


@router.post("/me/applications/{job_id}/undo")
async def undo_application(
    job_id: str = FastAPIPath(
        ..., description="The job ID (not application ID) whose swipe to undo"
    ),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Undo the last swipe decision for a job (identified by job_id) within 10 second window."""
    from shared.validators import validate_uuid

    # Validate job_id format
    try:
        validate_uuid(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    async with db.acquire() as conn:
        # Find the application for this user/job
        app = await conn.fetchrow(
            """
            SELECT id, status, created_at
            FROM public.applications
            WHERE user_id = $1 AND job_id = $2
            """,
            ctx.user_id,
            job_id,
        )

        if not app:
            raise HTTPException(
                status_code=404, detail="No application found for this job"
            )

        # Check if within 10 second undo window
        from datetime import datetime, timedelta

        created_at = app["created_at"]
        if created_at and datetime.now(timezone.utc) - created_at > timedelta(
            seconds=10
        ):
            raise HTTPException(status_code=400, detail="Undo window has expired")

        # Delete the application record (tenant_id for defense in depth)
        # nosemgrep: python.lang.security.audit.sqli.asyncpg-sqli.asyncpg-sqli - parameterized
        await conn.execute(
            """
            DELETE FROM public.applications
            WHERE user_id = $1 AND job_id = $2 AND (tenant_id = $3 OR $3 IS NULL)
            """,
            ctx.user_id,
            job_id,
            ctx.tenant_id,
        )

        return {"status": "undone", "job_id": job_id}


# ---------------------------------------------------------------------------
# POST /applications/{application_id}/answer
# ---------------------------------------------------------------------------


class AnswerHoldBody(BaseModel):
    answer: str = Field(..., min_length=1, max_length=5000)

    @field_validator("answer")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        from packages.backend.domain.sanitization import sanitize_text_input

        return sanitize_text_input(v, max_length=5000)


@router.post("/me/applications/{application_id}/answer")
async def answer_hold(
    application_id: str = FastAPIPath(...),
    body: AnswerHoldBody = ...,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Submit a single answer for a hold; applies to first unresolved input and re-queues."""
    from shared.validators import validate_uuid

    validate_uuid(application_id, "application_id")
    async with db.acquire() as conn:
        app_row = await ApplicationRepo.get_by_id_and_user(
            conn, application_id, ctx.user_id, tenant_id=ctx.tenant_id
        )
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")
    if app_row["status"] != "REQUIRES_INPUT":
        raise HTTPException(
            status_code=409,
            detail=f"Application status is {app_row['status']}, expected REQUIRES_INPUT",
        )

    async with db.acquire() as conn:
        unresolved = await InputRepo.get_unresolved(conn, application_id)
    if not unresolved:
        raise HTTPException(
            status_code=409, detail="No pending questions for this application"
        )

    # Use first unresolved input; single answer applies to it
    first_row = unresolved[0]
    first_id = str(first_row.get("id", ""))
    if not first_id:
        raise HTTPException(status_code=500, detail="Invalid input data")
    answers = [{"input_id": first_id, "answer": body.answer}]

    async with db_transaction(db) as conn:
        await InputRepo.update_answers(conn, answers, application_id=application_id)
        await EventRepo.emit(
            conn,
            application_id,
            "USER_ANSWERED",
            {"input_id": first_id, "answer": body.answer},
            tenant_id=ctx.tenant_id,
        )
        await ApplicationRepo.update_status(conn, application_id, "QUEUED")
        await EventRepo.emit(
            conn,
            application_id,
            "RETRY_SCHEDULED",
            {"answered_count": 1},
            tenant_id=ctx.tenant_id,
        )

    return {
        "status": "saved",
        "application_id": application_id,
        "message": "Answer saved; application re-queued.",
    }


# ---------------------------------------------------------------------------
# POST /applications/{id}/snooze
# ---------------------------------------------------------------------------


class SnoozeBody(BaseModel):
    hours: int = Field(default=24, ge=1, le=720)


@router.post("/me/applications/{application_id}/snooze")
async def snooze_application(
    application_id: str = FastAPIPath(...),
    body: SnoozeBody | None = None,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Snooze an application for N hours."""
    if body is None:
        body = SnoozeBody()
    from shared.validators import validate_uuid

    validate_uuid(application_id, "application_id")
    from datetime import datetime, timedelta

    until = datetime.now(timezone.utc) + timedelta(hours=body.hours)

    async with db.acquire() as conn:
        res = await conn.execute(
            """
            UPDATE public.applications
            SET    snoozed_until = $1,
                   updated_at = now()
            WHERE  id = $2 AND user_id = $3 AND (tenant_id = $4 OR tenant_id IS NULL)
            """,
            until,
            application_id,
            ctx.user_id,
            ctx.tenant_id,
        )
        if res == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Application not found")

    return {
        "status": "snoozed",
        "application_id": application_id,
        "snoozed_until": until.isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /me/applications/{application_id}/review
# ---------------------------------------------------------------------------


@router.post("/me/applications/{application_id}/review")
async def mark_application_reviewed(
    application_id: str = FastAPIPath(...),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Mark an application as reviewed (acknowledge its current status)."""
    from shared.validators import validate_uuid

    validate_uuid(application_id, "application_id")
    async with db.acquire() as conn:
        res = await conn.execute(
            """
            UPDATE public.applications
            SET    updated_at = now()
            WHERE  id = $1 AND user_id = $2 AND (tenant_id = $3 OR tenant_id IS NULL)
            """,
            application_id,
            ctx.user_id,
            ctx.tenant_id,
        )
        if res == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Application not found")

    return {"status": "reviewed", "application_id": application_id}


# ---------------------------------------------------------------------------
# POST /me/applications/{application_id}/withdraw
# ---------------------------------------------------------------------------


@router.post("/me/applications/{application_id}/withdraw")
async def withdraw_application(
    application_id: str = FastAPIPath(...),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Withdraw/cancel an application."""
    from shared.validators import validate_uuid

    validate_uuid(application_id, "application_id")
    async with db.acquire() as conn:
        app_row = await conn.fetchrow(
            """
            SELECT status FROM public.applications
            WHERE id = $1 AND user_id = $2 AND (tenant_id = $3 OR tenant_id IS NULL)
            """,
            application_id,
            ctx.user_id,
            ctx.tenant_id,
        )
        if not app_row:
            raise HTTPException(status_code=404, detail="Application not found")

        if app_row["status"] in ("APPLIED", "SUBMITTED", "COMPLETED"):
            raise HTTPException(
                status_code=409,
                detail="Cannot withdraw an already submitted application",
            )

        await conn.execute(
            """
            UPDATE public.applications
            SET    status = 'REJECTED', updated_at = now()
            WHERE  id = $1 AND user_id = $2 AND (tenant_id = $3 OR tenant_id IS NULL)
            """,
            application_id,
            ctx.user_id,
            ctx.tenant_id,
        )

    return {"status": "withdrawn", "application_id": application_id}


# ---------------------------------------------------------------------------
# PATCH /me/applications/{application_id}/status
# ---------------------------------------------------------------------------


class UpdateApplicationStatusBody(BaseModel):
    """Request body for updating application status."""

    status: str = Field(
        ...,
        max_length=50,
        description="New status: 'INTERVIEW_SCHEDULED', 'OFFER_RECEIVED', 'ACCEPTED', 'REJECTED'",
    )
    notes: str | None = Field(
        None, max_length=5000, description="Optional notes about the status update"
    )

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: str | None) -> str | None:
        if v is None:
            return None
        from packages.backend.domain.sanitization import sanitize_text_input

        return sanitize_text_input(v, max_length=5000)


@router.patch("/me/applications/{application_id}/status")
async def update_application_status(
    application_id: str = FastAPIPath(..., description="Application ID to update"),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
    body: UpdateApplicationStatusBody = Body(...),
) -> dict[str, Any]:
    """Update application status manually."""
    from shared.validators import validate_uuid

    # Validate application_id format
    try:
        validate_uuid(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID format")

    # Validate status
    valid_statuses = [
        "INTERVIEW_SCHEDULED",
        "OFFER_RECEIVED",
        "ACCEPTED",
        "REJECTED",
        "WITHDRAWN",
    ]
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    async with db.acquire() as conn:
        # Check if application exists and belongs to user (tenant scoping for consistency)
        app = await conn.fetchrow(
            """SELECT id, user_id, status FROM public.applications
               WHERE id = $1 AND user_id = $2 AND (tenant_id = $3 OR tenant_id IS NULL)""",
            application_id,
            ctx.user_id,
            ctx.tenant_id,
        )

        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # Update status and notes ($1=application_id, $2=user_id, $3=tenant_id, $4=status, $5=notes optional)
        params: list[Any] = [application_id, ctx.user_id, ctx.tenant_id, body.status]
        update_fields = ["status = $4", "updated_at = CURRENT_TIMESTAMP"]
        if body.notes:
            update_fields.append("notes = $5")
            params.append(body.notes)

        # nosemgrep: python.lang.security.audit.sqli.asyncpg-sqli.asyncpg-sqli - parameterized query
        await conn.execute(
            f"""
            UPDATE public.applications
            SET {", ".join(update_fields)}
            WHERE id = $1 AND user_id = $2 AND (tenant_id = $3 OR tenant_id IS NULL)
            """,
            *params,
        )

        logger.info(
            f"Application {application_id} status updated to {body.status} by user {ctx.user_id}"
        )

        return {
            "status": "updated",
            "application_id": application_id,
            "new_status": body.status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# GET /jobs
# ---------------------------------------------------------------------------


@router.get("/me/jobs")
async def list_jobs(
    location: str | None = None,
    min_salary: int | None = None,
    keywords: str | None = None,
    source: str | None = None,
    is_remote: bool | None = None,
    job_type: str | None = None,
    sort_by: str = "date_posted",
    min_match_score: int | None = None,
    limit: int = 25,
    offset: int = 0,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """List jobs from DB with optional filters. Returns { jobs: [...], next_offset } for web.

    sort_by: match_score | recently_matched | salary | date_posted
    min_match_score: When scoring, filter jobs below this score (0-100).
    When authenticated, match_score/recently_matched use profile-based scoring.
    """
    from packages.backend.domain.job_search import search_and_list_jobs

    limit = max(5, min(limit, 100))
    offset = max(0, offset)

    jobs = await search_and_list_jobs(
        db_pool=db,
        location=location,
        min_salary=min_salary,
        keywords=keywords,
        source=source,
        is_remote=is_remote,
        job_type=job_type,
        user_id=str(ctx.user_id),
        sort_by=sort_by,
        min_match_score=min_match_score,
        limit=limit,
        offset=offset,
    )

    next_offset = offset + len(jobs) if len(jobs) == limit else None
    return {"jobs": jobs, "next_offset": next_offset}


@router.get("/me/jobs/sources")
async def get_job_sources(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """Get list of available job sources with stats."""
    from packages.backend.domain.job_search import get_job_sources

    return await get_job_sources(db)


# ---------------------------------------------------------------------------
# GET /applications/export
# ---------------------------------------------------------------------------


@router.get("/me/applications/export")
async def export_applications(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
):
    """Export applications as CSV."""
    import csv
    import io

    from fastapi.responses import StreamingResponse

    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT a.id, a.status::text, a.updated_at,
                   j.title AS job_title, j.company, j.location
            FROM   public.applications a
            JOIN   public.jobs j ON j.id = a.job_id
            WHERE  a.user_id = $1 AND (a.tenant_id = $2 OR a.tenant_id IS NULL)
            ORDER  BY a.updated_at DESC
            """,
            ctx.user_id,
            ctx.tenant_id,
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["ID", "Job Title", "Company", "Location", "Status", "Last Activity"]
    )
    for r in rows:
        writer.writerow(
            [
                str(r["id"]),
                r["job_title"],
                r["company"],
                r["location"],
                _status_to_web(r["status"]),
                r["updated_at"].isoformat() if r["updated_at"] else "",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"},
    )


@router.get("/me/profile")
async def get_profile(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Current user profile for web: id, email, has_completed_onboarding, resume_url, preferences."""
    logger.info("[PROFILE] Fetching profile", extra={"user_id": str(ctx.user_id)})

    try:
        async with db.acquire() as conn:
            # Fetch user profile from public.users
            user_row = await conn.fetchrow(
                "SELECT id, email, full_name FROM public.users WHERE id = $1",
                ctx.user_id,
            )
            profile_row = await conn.fetchrow(
                "SELECT profile_data, resume_url FROM public.profiles WHERE user_id = $1",
                ctx.user_id,
            )
            # Item 23: Include role for AdminGuard (admin/superadmin = OWNER/ADMIN or is_system_admin)
            role: str = "user"
            if ctx.is_admin:
                role = "admin"
            try:
                is_system_admin = await conn.fetchval(
                    "SELECT COALESCE(is_system_admin, false) FROM public.users WHERE id = $1",
                    ctx.user_id,
                )
                if is_system_admin:
                    role = "superadmin"
            except Exception as e:
                logger.debug(
                    "is_system_admin check failed (column may not exist): %s", e
                )
    except Exception as exc:
        logger.error(
            "[PROFILE] Database error fetching profile: %s", exc, exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

    if not user_row:
        logger.warning("[PROFILE] User not found", extra={"user_id": str(ctx.user_id)})
        raise HTTPException(status_code=404, detail="User not found")

    profile_data: dict = {}
    resume_url: str | None = None
    if profile_row:
        pd = profile_row["profile_data"]
        profile_data = json.loads(pd) if isinstance(pd, str) else (pd or {})
        resume_url = profile_row["resume_url"]

    # Web expects has_completed_onboarding and preferences from profile_data
    prefs = profile_data.get("preferences") or {}
    if isinstance(prefs, str):
        prefs = {}
    contact = profile_data.get("contact") or {}

    has_completed_onboarding = profile_data.get("has_completed_onboarding", False)

    logger.info(
        "[PROFILE] Profile fetched successfully",
        extra={
            "user_id": str(ctx.user_id),
            "email": mask_email(user_row["email"] or ""),
            "has_completed_onboarding": has_completed_onboarding,
            "has_resume": bool(resume_url),
            "has_preferences": bool(prefs),
        },
    )

    return {
        "id": str(user_row["id"]),
        "email": user_row["email"] or "",
        "has_completed_onboarding": has_completed_onboarding,
        "resume_url": resume_url,
        "preferences": prefs,
        "contact": contact,
        "headline": profile_data.get("headline", ""),
        "bio": profile_data.get("summary", ""),
        "career_goals": profile_data.get("career_goals", {}),
        "work_style": profile_data.get("work_style", {}),
        "onboarding_step": profile_data.get("onboarding_step"),
        "onboarding_completed_steps": profile_data.get("onboarding_completed_steps")
        or [],
        "role": role,
    }


# ---------------------------------------------------------------------------
# PATCH /profile
# ---------------------------------------------------------------------------


class Preferences(BaseModel):
    location: str | None = Field(None, max_length=200)
    role_type: str | None = Field(None, max_length=100)
    salary_min: int | None = None
    salary_max: int | None = None
    remote_only: bool | None = None
    onsite_only: bool | None = None
    work_authorized: bool | None = None
    visa_sponsorship: bool | None = None
    excluded_companies: list[str] | None = Field(None, max_length=100)
    excluded_keywords: list[str] | None = Field(None, max_length=50)

    @field_validator("excluded_companies")
    @classmethod
    def _validate_companies(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return [str(x).strip()[:100] for x in v[:100] if x]

    @field_validator("excluded_keywords")
    @classmethod
    def _validate_keywords(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return [str(x).strip()[:100] for x in v[:50] if x]

    @model_validator(mode="after")
    def _validate_salary_range(self) -> "Preferences":
        mn, mx = self.salary_min, self.salary_max
        if mn is not None and (mn < 0 or mn > 10_000_000):
            raise ValueError("salary_min must be between 0 and 10,000,000")
        if mx is not None and (mx < 0 or mx > 10_000_000):
            raise ValueError("salary_max must be between 0 and 10,000,000")
        if mn is not None and mx is not None and mn > mx:
            raise ValueError("salary_min must be less than or equal to salary_max")
        return self


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=200)
    headline: str | None = None
    bio: str | None = None
    has_completed_onboarding: bool | None = None
    preferences: Preferences | None = None
    avatar_url: str | None = None
    resume_url: str | None = None
    contact: dict | None = None
    career_goals: dict | None = None
    work_style: dict | None = None
    # P1: Server-side onboarding progress for cross-device resume
    onboarding_step: int | None = None
    onboarding_completed_steps: list[str] | None = None

    @field_validator("career_goals")
    @classmethod
    def _validate_career_goals(cls, value: dict | None) -> dict | None:
        """Validate career_goals experience_level and urgency when provided."""
        if value is None:
            return None
        allowed_exp = {"entry", "mid", "senior", "staff", "principal", "executive"}
        allowed_urgency = {"passive", "casual", "active", "urgent"}
        exp = value.get("experience_level")
        if exp is not None and str(exp).lower() not in allowed_exp:
            raise ValueError(f"experience_level must be one of {sorted(allowed_exp)}")
        urgency = value.get("urgency")
        if urgency is not None and str(urgency).lower() not in allowed_urgency:
            raise ValueError(f"urgency must be one of {sorted(allowed_urgency)}")
        return value

    @field_validator("contact")
    @classmethod
    def _validate_contact(cls, value: dict | None) -> dict | None:
        """D3: Align with frontend - validate email and phone format when provided."""
        if value is None:
            return None
        import re

        email = value.get("email")
        if email is not None and str(email).strip():
            if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", str(email).strip()):
                raise ValueError("Invalid email format")
        phone = value.get("phone")
        if phone is not None and str(phone).strip():
            digits = re.sub(r"[^\d+]", "", str(phone))
            if digits.startswith("+"):
                digits = digits[1:]
            if len(digits) < 10 or len(digits) > 15:
                raise ValueError("Invalid phone number")
        return value

    @field_validator("headline")
    @classmethod
    def sanitize_headline(cls, v: str | None) -> str | None:
        """Item 44: Sanitize headline to prevent XSS."""
        if v is None:
            return None
        from packages.backend.domain.sanitization import sanitize_text_input

        return sanitize_text_input(v, max_length=200)

    @field_validator("bio")
    @classmethod
    def sanitize_bio(cls, v: str | None) -> str | None:
        """Item 44: Sanitize bio to prevent XSS."""
        if v is None:
            return None
        from packages.backend.domain.sanitization import sanitize_text_input

        return sanitize_text_input(v, max_length=5000)

    @field_validator("avatar_url", "resume_url")
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        if not value:
            return None
        if not value.startswith("http"):
            raise ValueError("URL must be a full http(s) URL")
        if len(value) > 2048:
            raise ValueError("URL must be at most 2048 characters")
        return value

    @field_validator("work_style")
    @classmethod
    def _validate_work_style(cls, value: dict | None) -> dict | None:
        """Validate work_style field and handle unknown fields properly."""
        if value is None:
            return None

        # Define allowed work style fields
        allowed_fields = {
            "preferred_work_environment",
            "work_hours",
            "team_size_preference",
            "management_style",
            "communication_style",
            "work_life_balance_priority",
            "learning_preference",
            "company_culture_fit",
        }

        # Filter out unknown fields but preserve known ones
        validated_style = {}
        for key, val in value.items():
            if key in allowed_fields:
                validated_style[key] = val
            else:
                logger.warning(f"Unknown work_style field ignored: {key}")

        return validated_style if validated_style else None


@router.patch("/me/profile")
async def update_profile(
    body: ProfileUpdate,
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Update profile: onboarding flag and preferences stored in profile_data."""
    logger.info(
        "[PROFILE] Update requested",
        extra={
            "user_id": str(ctx.user_id),
            "updates": sanitize_for_log(body.model_dump(exclude_none=True)),
        },
    )

    limiter = _get_profile_limiter(ctx.user_id)
    if not await limiter.acquire():
        from shared.metrics import incr

        incr("profile.update.rate_limited", {"user_id": ctx.user_id})
        logger.warning("[PROFILE] Rate limited", extra={"user_id": str(ctx.user_id)})
        raise HTTPException(
            status_code=429, detail="Too many profile updates. Please retry later."
        )
    async with db.acquire() as conn:
        async with conn.transaction():
            existing = await ProfileRepo.get_profile_data(conn, ctx.user_id)
            profile_data = dict(existing or {})

            # Check if we are completing onboarding
            was_onboarding = profile_data.get("has_completed_onboarding", False)

            _merge_profile_update(profile_data, body)

            now_onboarding = profile_data.get("has_completed_onboarding", False)

            if not was_onboarding and now_onboarding:
                logger.info(
                    "[PROFILE] Onboarding completion detected",
                    extra={"user_id": str(ctx.user_id)},
                )
                background_tasks.add_task(
                    _hydrate_job_matches,
                    db_pool=db,
                    user_id=ctx.user_id,
                    tenant_id=ctx.tenant_id,
                    preferences=profile_data.get("preferences", {}),
                )

            existing_row = await conn.fetchrow(
                "SELECT resume_url FROM public.profiles WHERE user_id = $1",
                ctx.user_id,
            )
            current_resume = existing_row["resume_url"] if existing_row else None

            await ProfileRepo.upsert(
                conn,
                ctx.user_id,
                profile_data,
                resume_url=(
                    body.resume_url if body.resume_url is not None else current_resume
                ),
                tenant_id=ctx.tenant_id,
            )

            # Sync full_name to users table for display consistency
            contact = profile_data.get("contact") or {}
            full_name = contact.get("full_name") or ""
            if not full_name:
                first = contact.get("first_name", "")
                last = contact.get("last_name", "")
                full_name = f"{first} {last}".strip()
            if full_name:
                await conn.execute(
                    "UPDATE public.users SET full_name = $1, updated_at = now() WHERE id = $2",
                    full_name,
                    ctx.user_id,
                )

        logger.info(
            "[PROFILE] Profile updated successfully",
            extra={
                "user_id": str(ctx.user_id),
                "has_completed_onboarding": now_onboarding,
            },
        )
        row = await conn.fetchrow(
            "SELECT resume_url FROM public.profiles WHERE user_id = $1",
            ctx.user_id,
        )
        final_resume = row["resume_url"] if row else None

        user_row = await conn.fetchrow(
            "SELECT email FROM public.users WHERE id = $1", ctx.user_id
        )
        user_email = user_row["email"] if user_row else ""

    return {
        "id": ctx.user_id,
        "email": user_email,
        "has_completed_onboarding": profile_data.get("has_completed_onboarding", False),
        "resume_url": final_resume,
        "preferences": profile_data.get("preferences") or {},
        "contact": profile_data.get("contact") or {},
    }


def _merge_contact_fields(contact: dict, body_contact: dict) -> None:
    """Merge nested contact fields from update body into contact dict. OB-015: Only copy allowed keys."""
    contact_fields = (
        "first_name",
        "last_name",
        "full_name",
        "email",
        "phone",
        "linkedin_url",
        "portfolio_url",
        "location",
    )
    for field in contact_fields:
        if field in body_contact and body_contact[field] is not None:
            val = body_contact[field]
            if isinstance(val, str):
                from packages.backend.domain.sanitization import sanitize_text_input

                val = sanitize_text_input(val, max_length=500)
            contact[field] = val
    if "avatar_url" in body_contact and body_contact["avatar_url"]:
        contact["avatar_url"] = body_contact["avatar_url"]


def _merge_profile_update(profile_data: dict, body: ProfileUpdate) -> None:
    """Merge update body into profile_data dict in-place."""
    contact = dict(profile_data.get("contact") or {})

    if body.full_name is not None:
        contact["full_name"] = body.full_name
    if body.headline is not None:
        profile_data["headline"] = body.headline
    if body.bio is not None:
        profile_data["summary"] = body.bio

    if body.has_completed_onboarding is not None:
        profile_data["has_completed_onboarding"] = body.has_completed_onboarding
    if body.preferences is not None:
        profile_data["preferences"] = body.preferences.model_dump(exclude_unset=True)

    if body.career_goals is not None:
        profile_data["career_goals"] = body.career_goals
    if body.work_style is not None:
        profile_data["work_style"] = body.work_style
    # C1/C3: Merge onboarding progress; never go backwards; union completed steps (two tabs)
    # R1: Reject out-of-order step jumps (step 3 before step 2)
    if body.onboarding_step is not None:
        current_step = profile_data.get("onboarding_step", 0)
        requested = body.onboarding_step
        if requested > current_step + 1:
            requested = current_step + 1  # Clamp to prevent skip-ahead
        profile_data["onboarding_step"] = max(current_step, requested)
    if body.onboarding_completed_steps is not None:
        existing = set(profile_data.get("onboarding_completed_steps") or [])
        profile_data["onboarding_completed_steps"] = list(
            existing | set(body.onboarding_completed_steps)
        )

    avatar_url = (
        body.avatar_url if body.avatar_url is not None else contact.get("avatar_url")
    )
    if avatar_url:
        contact["avatar_url"] = avatar_url

    if body.contact is not None:
        _merge_contact_fields(contact, body.contact)

    profile_data["contact"] = contact


async def _hydrate_job_matches(
    db_pool: asyncpg.Pool, user_id: str, tenant_id: str, preferences: dict
) -> None:
    """Background task to pre-fetch and cache job matches after onboarding."""
    try:
        logger.info("Hydrating job matches for user %s", user_id)

        from packages.backend.domain.job_search import search_and_list_jobs

        location = preferences.get("location")
        role = preferences.get("role_type")
        salary_val = preferences.get("salary_min")
        salary = (
            int(salary_val)
            if salary_val and str(salary_val).isdigit() and int(str(salary_val)) > 0
            else None
        )

        await search_and_list_jobs(
            db_pool=db_pool,
            location=location,
            keywords=role,
            min_salary=salary,
            limit=25,
            offset=0,
            user_id=user_id,
            sort_by="match_score",
        )
        logger.info("Hydrated job matches for user %s", user_id)
    except Exception as e:
        logger.error("Failed to hydrate job matches: %s", e)
        from shared.metrics import incr

        incr("growth.hydrate_job_matches.failed", {"user_id": user_id})


# ---------------------------------------------------------------------------
# POST /profile/resume
# ---------------------------------------------------------------------------


@router.post("/me/profile/resume")
async def upload_resume(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Upload resume: extract text, parse via LLM, upsert profile, store file. Returns parsed data."""
    limiter = _get_upload_limiter(ctx.user_id)
    if not await limiter.acquire():
        raise HTTPException(
            status_code=429, detail="Too many uploads. Please retry later."
        )

    # Enhanced file type validation for multiple formats
    supported_types = (
        processor.SUPPORTED_PDF_TYPES
        | processor.SUPPORTED_DOCX_TYPES
        | processor.SUPPORTED_IMAGE_TYPES
    )
    if file.content_type not in supported_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Supported formats: PDF, DOCX, and images.",
        )

    if file.size == 0:
        raise HTTPException(status_code=400, detail="File is empty or corrupted")

    settings = get_settings()
    if file.size and file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // 1_048_576} MB",
        )

    # Enhanced file validation with virus scanning
    filename = (file.filename or "upload.pdf").lower()

    # Check for suspicious file extensions disguised as PDF
    suspicious_extensions = [
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".scr",
        ".pif",
        ".vbs",
        ".js",
        ".jar",
        ".app",
        ".deb",
        ".rpm",
        ".dmg",
        ".pkg",
        ".msi",
        ".torrent",
    ]

    for ext in suspicious_extensions:
        if filename.endswith(ext):
            logger.warning(f"[UPLOAD] Suspicious file extension detected: {ext}")
            raise HTTPException(status_code=400, detail="Invalid file type")

    # Validate file type is allowed for scanning
    from shared.virus_scanner import is_file_type_allowed

    if not is_file_type_allowed(filename, file.content_type):
        raise HTTPException(status_code=400, detail="File type not allowed")

    # Read file content for validation and scanning
    file_bytes = await file.read()
    await file.seek(0)  # Reset file pointer for later use

    # Perform virus scan before processing
    from shared.virus_scanner import generate_file_hash, scan_uploaded_file

    scan_result = await scan_uploaded_file(file_bytes, filename)

    if not scan_result.clean:
        logger.error(f"[UPLOAD] Virus scan failed: {scan_result.threats}")
        raise HTTPException(
            status_code=400,
            detail="File security scan failed. Please upload a different file.",
        )

    # Log file hash for audit trail
    file_hash = generate_file_hash(file_bytes)
    logger.info(f"[UPLOAD] File hash: {file_hash}, scan engine: {scan_result.engine}")

    # Enhanced validation for different file types
    if file.content_type in processor.SUPPORTED_PDF_TYPES:
        # PDF-specific validation
        if len(file_bytes) < 8:
            raise HTTPException(
                status_code=400, detail="File too small to be a valid PDF"
            )

        # PDF files start with %PDF-
        if not file_bytes.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF format - does not contain PDF header",
            )

        # Check for PDF version (should be 1.x)
        try:
            version_part = file_bytes[5:8].decode("ascii")
            major_version = int(version_part[0])
            minor_version = int(version_part[2]) if len(version_part) > 2 else 0
            if major_version < 1 or major_version > 2:
                logger.warning(
                    f"[UPLOAD] Unusual PDF version: {major_version}.{minor_version}"
                )
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Invalid PDF version format")

        # Check for embedded malicious content patterns
        pdf_content = file_bytes.decode("latin-1", errors="ignore").lower()
        malicious_patterns = [
            "javascript:",
            "vbscript:",
            "data:text/html",
            "<script",
            "eval(",
            "document.write",
        ]

        for pattern in malicious_patterns:
            if pattern in pdf_content:
                logger.warning(
                    f"[UPLOAD] Malicious content pattern detected: {pattern}"
                )
                raise HTTPException(
                    status_code=400, detail="PDF contains potentially malicious content"
                )

    elif file.content_type in processor.SUPPORTED_DOCX_TYPES:
        # DOCX-specific validation
        if len(file_bytes) < 1000:  # DOCX files have minimum size due to ZIP structure
            raise HTTPException(
                status_code=400, detail="File too small to be a valid DOCX"
            )

        # Check for DOCX magic number (PK header for ZIP files)
        if not file_bytes.startswith(b"PK"):
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX format - does not contain ZIP header",
            )

    elif file.content_type in processor.SUPPORTED_IMAGE_TYPES:
        # Image-specific validation
        if len(file_bytes) < 100:
            raise HTTPException(
                status_code=400, detail="File too small to be a valid image"
            )

        # Basic image validation - check for common image headers
        image_headers = {
            b"\xff\xd8\xff": "JPEG",
            b"\x89PNG\r\n\x1a\n": "PNG",
            b"II*\x00": "TIFF",
            b"MM\x00*": "TIFF",
            b"BM": "BMP",
        }

        valid_image = any(
            file_bytes.startswith(header) for header in image_headers.keys()
        )
        if not valid_image:
            raise HTTPException(
                status_code=400, detail="Invalid image format - unsupported image type"
            )

    settings = get_settings()

    # Check file size again after reading
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // 1_048_576} MB",
        )

    try:
        resume_url, canonical = await process_resume_upload(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            file_bytes=file_bytes,
            filename=file.filename or "upload",
            content_type=file.content_type,
            db_pool=db,
            storage=get_storage_service(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Resume upload failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Resume processing failed. Please try again."
        )

    from shared.metrics import incr

    incr("profile.resume.uploaded", {"user_id": ctx.user_id})

    parsed = canonical.model_dump()
    contact = parsed.get("contact") or {}
    prefs = parsed.get("preferences") or {}
    return {
        "resume_url": resume_url,
        "parsed_profile": parsed,
        "contact": contact,
        "preferences": prefs if isinstance(prefs, dict) else {},
    }


@router.post("/me/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Upload an avatar image to storage and persist URL to profile."""
    limiter = _get_upload_limiter(ctx.user_id)
    if not await limiter.acquire():
        raise HTTPException(
            status_code=429, detail="Too many uploads. Please retry later."
        )
    allowed_types = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
    }
    if (file.content_type or "").lower() not in allowed_types:
        raise HTTPException(status_code=400, detail="Avatar must be PNG, JPG, or WEBP")

    settings = get_settings()
    # Pre-check Content-Length header to reject before reading body into memory
    if file.size and file.size > settings.max_avatar_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Avatar too large. Maximum size is {settings.max_avatar_size_bytes // 1_048_576} MB",
        )
    data = await file.read()
    if len(data) > settings.max_avatar_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Avatar too large. Maximum size is {settings.max_avatar_size_bytes // 1_048_576} MB",
        )
    # Validate magic bytes to prevent content-type spoofing (e.g. HTML as image)
    avatar_magic = {
        b"\xff\xd8\xff": "JPEG",
        b"\x89PNG\r\n\x1a\n": "PNG",
        b"RIFF": "WEBP",  # WEBP: RIFF....WEBP at offset 8
    }
    valid = any(data.startswith(m) for m in avatar_magic if m != b"RIFF") or (
        len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    )
    if not valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format - file content does not match declared type",
        )
    ext = Path(file.filename or "").suffix.lower()
    fallback_ext = allowed_types[(file.content_type or "image/png").lower()]
    suffix = ext if ext in allowed_types.values() else fallback_ext
    storage_path = f"{ctx.user_id}/{uuid.uuid4()}{suffix}"

    storage = get_storage_service()
    avatar_url = await storage.upload_file(
        "avatars", storage_path, data, content_type=file.content_type or "image/png"
    )

    async with db.acquire() as conn:
        existing = await ProfileRepo.get_profile_data(conn, ctx.user_id)
        profile_data = dict(existing or {})
        contact = dict(profile_data.get("contact") or {})
        contact["avatar_url"] = avatar_url
        profile_data["contact"] = contact

        existing_row = await conn.fetchrow(
            "SELECT resume_url FROM public.profiles WHERE user_id = $1",
            ctx.user_id,
        )
        current_resume = existing_row["resume_url"] if existing_row else None

        await ProfileRepo.upsert(
            conn,
            ctx.user_id,
            profile_data,
            resume_url=current_resume,
            tenant_id=ctx.tenant_id,
        )

    return {"avatar_url": avatar_url}


# ---------------------------------------------------------------------------
# User Job Refresh (per-user sync)
# ---------------------------------------------------------------------------


@router.post("/me/jobs/refresh")
async def refresh_my_jobs(
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Trigger per-user job sync for current user's preferences and job alerts.
    Rate-limited to once per 3 hours per user.
    """
    from packages.backend.domain.job_sync_service import JobSyncService

    # Rate limit: 1 refresh per 3 hours per user
    limiter = _get_job_refresh_limiter(ctx.user_id)
    if not await limiter.acquire():
        raise HTTPException(
            status_code=429,
            detail="Job refresh is limited to once every 3 hours. Please try again later.",
        )

    sync_service = JobSyncService(db)
    background_tasks.add_task(sync_service.sync_for_user, ctx.user_id, 2)

    return {
        "status": "refresh_started",
        "message": "Job sync triggered for your preferences. New jobs will appear shortly.",
    }


# ---------------------------------------------------------------------------
# Admin Job Sync Endpoints
# ---------------------------------------------------------------------------


@router.get("/me/admin/jobs/sync/status")
async def get_job_sync_status(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get current job sync status (admin only)."""
    if not ctx.is_admin:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Admin access required")

    from packages.backend.domain.job_search import get_sync_status

    return await get_sync_status(db)


@router.post("/me/admin/jobs/sync/trigger")
async def trigger_job_sync(
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Manually trigger a job sync (admin only)."""
    if not ctx.is_admin:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Admin access required")

    from packages.backend.domain.job_sync_service import JobSyncService

    sync_service = JobSyncService(db)
    background_tasks.add_task(sync_service.sync_all_sources, None, 2)

    return {"status": "sync_started", "message": "Job sync triggered in background"}


# ---------------------------------------------------------------------------
# DELETE /user/delete-account — GDPR/CCPA account erasure
# ---------------------------------------------------------------------------


@router.delete("/user/delete-account")
async def delete_account(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Permanently delete the current user's account and all associated data.

    GDPR Article 17 / CCPA right to erasure. Settings UI requires typing "DELETE"
    before calling this endpoint.
    """
    from packages.backend.domain.ccpa import CCPAComplianceManager

    result = await CCPAComplianceManager.handle_data_deletion_request(ctx.user_id, db)
    return {
        "status": result.get("status", "completed"),
        "message": "Account deletion completed. You will receive a confirmation email shortly.",
    }
