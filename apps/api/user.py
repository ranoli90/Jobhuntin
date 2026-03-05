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
from datetime import timezone
from pathlib import Path
from typing import Any, Literal

import asyncpg
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi import (
    Path as FastAPIPath,
)
from pydantic import BaseModel, Field, field_validator
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.storage import get_storage_service

from backend.domain.quotas import QuotaExceededError, check_can_create_application
from backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    InputRepo,
    JobRepo,
    ProfileRepo,
    db_transaction,
)
from backend.domain.resume import process_resume_upload
from backend.domain.tenant import TenantContext
from shared.metrics import RateLimiter

logger = get_logger("sorce.user")

router = APIRouter(tags=["user"])

# Per-user rate limiters to prevent abuse on profile writes/uploads
_profile_limiters: dict[str, tuple[RateLimiter, float]] = {}
_upload_limiters: dict[str, tuple[RateLimiter, float]] = {}
_LIMITER_TTL = 3600  # 1 hour


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
    limiter = RateLimiter(
        max_calls=30, window_seconds=300.0, name=f"profile:{user_id}"
    )
    _profile_limiters[user_id] = (limiter, now)
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
    limiter = RateLimiter(
        max_calls=10, window_seconds=600.0, name=f"upload:{user_id}"
    )
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


# ---------------------------------------------------------------------------
# GET /applications
# ---------------------------------------------------------------------------


@router.get("/applications")
async def list_applications(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """List applications for the current user; status mapped for web (HOLD, APPLYING, etc.)."""
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
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
            """,
            ctx.user_id,
            ctx.tenant_id,
        )

    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": str(r["id"]),
                "job_title": r["job_title"],
                "company": r["company"],
                "status": _status_to_web(r["status"]),
                "last_activity": r["updated_at"].isoformat()
                if r["updated_at"]
                else None,
                "hold_question": r["hold_question"]
                if r["status"] == "REQUIRES_INPUT"
                else None,
            }
        )
    return out


# ---------------------------------------------------------------------------
# POST /applications (swipe: create application)
# ---------------------------------------------------------------------------


class CreateApplicationBody(BaseModel):
    job_id: str
    decision: Literal["ACCEPT", "REJECT"]


@router.post("/applications")
async def create_application(
    body: CreateApplicationBody,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Create an application when user swipes ACCEPT; record REJECTED for REJECT."""
    from shared.validators import validate_uuid

    validate_uuid(body.job_id, "job_id")

    # N-7: Import at function scope to keep it visible
    from backend.domain.priority import compute_priority_score

    if body.decision != "ACCEPT":
        # H-3: Persist rejection with REJECTED status (not FAILED) to avoid
        # inflating failure metrics while still preventing job resurfacing.
        async with db.acquire() as conn:
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

        return {"status": "recorded", "decision": body.decision}

    async with db.acquire() as conn:
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

    return {
        "id": str(app_id),
        "job_id": body.job_id,
        "status": "QUEUED",
        "decision": "ACCEPT",
    }


# ---------------------------------------------------------------------------
# POST /applications/{job_id}/undo
# NOTE (M-7): The path parameter is `job_id` (not application_id).
# The endpoint looks up the application by (user_id, job_id) pair.
# ---------------------------------------------------------------------------


@router.post("/applications/{job_id}/undo")
async def undo_application(
    job_id: str = FastAPIPath(..., description="The job ID (not application ID) whose swipe to undo"),
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
        if created_at and datetime.now(timezone.utc) - created_at > timedelta(seconds=10):
            raise HTTPException(status_code=400, detail="Undo window has expired")

        # Delete the application record
        # nosemgrep: python.lang.security.audit.sqli.asyncpg-sqli.asyncpg-sqli - parameterized $1,$2
        await conn.execute(
            """
            DELETE FROM public.applications
            WHERE user_id = $1 AND job_id = $2
            """,
            ctx.user_id,
            job_id,
        )

        return {"status": "undone", "job_id": job_id}


# ---------------------------------------------------------------------------
# POST /applications/{application_id}/answer
# ---------------------------------------------------------------------------


class AnswerHoldBody(BaseModel):
    answer: str


@router.post("/applications/{application_id}/answer")
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
    first_id = str(unresolved[0]["id"])
    answers = [{"input_id": first_id, "answer": body.answer}]

    async with db_transaction(db) as conn:
        await InputRepo.update_answers(conn, answers)
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


@router.post("/applications/{application_id}/snooze")
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
# GET /jobs
# ---------------------------------------------------------------------------


@router.get("/jobs")
async def list_jobs(
    location: str | None = None,
    min_salary: int | None = None,
    keywords: str | None = None,
    source: str | None = None,
    is_remote: bool | None = None,
    job_type: str | None = None,
    limit: int = 25,
    offset: int = 0,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """List jobs from DB with optional filters. Returns { jobs: [...], next_offset } for web."""
    from backend.domain.job_search import search_and_list_jobs

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
        limit=limit,
        offset=offset,
    )

    next_offset = offset + len(jobs) if len(jobs) == limit else None
    return {"jobs": jobs, "next_offset": next_offset}


@router.get("/jobs/sources")
async def get_job_sources(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """Get list of available job sources with stats."""
    from backend.domain.job_search import get_job_sources
    return await get_job_sources(db)


# ---------------------------------------------------------------------------
# GET /applications/export
# ---------------------------------------------------------------------------


@router.get("/applications/export")
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


@router.get("/profile")
async def get_profile(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Current user profile for web: id, email, has_completed_onboarding, resume_url, preferences."""
    logger.info("[PROFILE] Fetching profile", extra={"user_id": str(ctx.user_id)})

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
            "email": user_row["email"],
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
    }


# ---------------------------------------------------------------------------
# PATCH /profile
# ---------------------------------------------------------------------------


class Preferences(BaseModel):
    location: str | None = None
    role_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    remote_only: bool | None = None
    onsite_only: bool | None = None
    work_authorized: bool | None = None
    visa_sponsorship: bool | None = None
    excluded_companies: list[str] | None = None
    excluded_keywords: list[str] | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    headline: str | None = None
    bio: str | None = None
    has_completed_onboarding: bool | None = None
    preferences: Preferences | None = None
    avatar_url: str | None = None
    resume_url: str | None = None
    contact: dict | None = None
    career_goals: dict | None = None
    work_style: dict | None = None

    @field_validator("avatar_url")
    @classmethod
    def _validate_avatar(cls, value: str | None) -> str | None:
        if value and not value.startswith("http"):
            raise ValueError("avatar_url must be a full URL")
        return value


@router.patch("/profile")
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
            "updates": body.model_dump(exclude_none=True),
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
            resume_url=body.resume_url
            if body.resume_url is not None
            else current_resume,
            tenant_id=ctx.tenant_id,
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
    """Merge nested contact fields from update body into contact dict."""
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
            contact[field] = body_contact[field]
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
    """Background task to pre-fetch and cache job matches after onboarding.

    Attempts profile-aware scoring first; falls back to basic search.
    """
    try:
        logger.info("Hydrating job matches for user %s", user_id)

        # Try profile-aware scoring first
        try:
            from backend.domain.deep_profile import dict_to_profile
            from backend.domain.job_search import search_jobs_for_profile

            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT profile_data FROM public.profiles WHERE user_id = $1",
                    user_id,
                )
            if row and row["profile_data"]:
                import json as _json
                pd = row["profile_data"]
                data = _json.loads(pd) if isinstance(pd, str) else pd
                data["user_id"] = user_id
                profile = dict_to_profile(data)
                await search_jobs_for_profile(db_pool, profile, limit=25)
                logger.info("Hydrated scored matches for user %s", user_id)
                return
        except Exception as inner:
            logger.warning("Profile-aware hydration failed, falling back: %s", inner)

        # Fallback: basic search
        from backend.domain.job_search import search_and_list_jobs

        location = preferences.get("location")
        role = preferences.get("role_type")
        salary_str = preferences.get("salary_min")
        salary = int(salary_str) if salary_str and str(salary_str).isdigit() else None

        await search_and_list_jobs(
            db_pool=db_pool,
            location=location,
            keywords=role,
            min_salary=salary,
            limit=20,
            offset=0,
        )
    except Exception as e:
        logger.error("Failed to hydrate job matches: %s", e)


# ---------------------------------------------------------------------------
# POST /profile/resume
# ---------------------------------------------------------------------------


@router.post("/profile/resume")
async def upload_resume(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Upload PDF resume: extract text, parse via LLM, upsert profile, store file. Returns parsed data."""
    limiter = _get_upload_limiter(ctx.user_id)
    if not await limiter.acquire():
        raise HTTPException(
            status_code=429, detail="Too many uploads. Please retry later."
        )
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if file.size == 0:
        raise HTTPException(status_code=400, detail="File is empty or corrupted")

    settings = get_settings()
    if file.size and file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // 1_048_576} MB",
        )
    pdf_bytes = await file.read()
    if len(pdf_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // 1_048_576} MB",
        )

    try:
        resume_url, canonical = await process_resume_upload(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            pdf_bytes=pdf_bytes,
            db_pool=db,
            storage=get_storage_service(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Resume upload failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Resume processing failed. Please try again."
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


@router.post("/profile/avatar")
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
    ext = Path(file.filename or "").suffix.lower()
    fallback_ext = allowed_types[file.content_type.lower()]  # type: ignore[operator]
    suffix = ext if ext in allowed_types.values() else fallback_ext
    storage_path = f"avatars/{ctx.user_id}/{uuid.uuid4()}{suffix}"

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
# Admin Job Sync Endpoints
# ---------------------------------------------------------------------------


@router.get("/admin/jobs/sync/status")
async def get_job_sync_status(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get current job sync status (admin only)."""
    if not ctx.is_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")

    from backend.domain.job_search import get_sync_status
    return await get_sync_status(db)


@router.post("/admin/jobs/sync/trigger")
async def trigger_job_sync(
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Manually trigger a job sync (admin only)."""
    if not ctx.is_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")

    from backend.domain.job_sync_service import JobSyncService

    sync_service = JobSyncService(db)
    background_tasks.add_task(sync_service.sync_all_sources, None, 2)

    return {"status": "sync_started", "message": "Job sync triggered in background"}
