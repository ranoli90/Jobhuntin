"""
User-facing web API — endpoints consumed by the web app (not admin).

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
from datetime import UTC
from pathlib import Path
from typing import Any

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, Path as FastAPIPath
from pydantic import BaseModel, field_validator

from backend.domain.quotas import QuotaExceededError, check_can_create_application
from backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    InputRepo,
    JobRepo,
    ProfileRepo,
    db_transaction,
)
from backend.domain.resume import process_resume_upload, upload_to_supabase_storage
from backend.domain.tenant import TenantContext
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import RateLimiter

logger = get_logger("sorce.user")

router = APIRouter(tags=["user"])

# Per-user rate limiters to prevent abuse on profile writes/uploads
_profile_limiters: dict[str, RateLimiter] = {}
_upload_limiters: dict[str, RateLimiter] = {}


def _get_profile_limiter(user_id: str) -> RateLimiter:
    limiter = _profile_limiters.get(user_id)
    if limiter is None:
        limiter = RateLimiter(max_calls=30, window_seconds=300.0, name=f"profile:{user_id}")
        _profile_limiters[user_id] = limiter
    return limiter


def _get_upload_limiter(user_id: str) -> RateLimiter:
    limiter = _upload_limiters.get(user_id)
    if limiter is None:
        limiter = RateLimiter(max_calls=10, window_seconds=600.0, name=f"upload:{user_id}")
        _upload_limiters[user_id] = limiter
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
              AND (a.snoozed_until IS NULL OR a.snoozed_until < now())
            ORDER  BY a.updated_at DESC
            """,
            ctx.user_id,
            ctx.tenant_id,
        )

    out: list[dict[str, Any]] = []
    for r in rows:
        out.append({
            "id": str(r["id"]),
            "job_title": r["job_title"],
            "company": r["company"],
            "status": _status_to_web(r["status"]),
            "last_activity": r["updated_at"].isoformat() if r["updated_at"] else None,
            "hold_question": r["hold_question"] if r["status"] == "REQUIRES_INPUT" else None,
        })
    return out


# ---------------------------------------------------------------------------
# POST /applications (swipe: create application)
# ---------------------------------------------------------------------------

class CreateApplicationBody(BaseModel):
    job_id: str
    decision: str  # ACCEPT | REJECT


@router.post("/applications")
async def create_application(
    body: CreateApplicationBody,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Create an application when user swipes ACCEPT; REJECT is a no-op."""
    if body.decision != "ACCEPT":
        # Persist rejection to avoid resurfacing the same job in feeds
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
                VALUES ($1, $2, $3, $4, 'FAILED', 0)
                ON CONFLICT (user_id, job_id) DO UPDATE SET
                    status = 'FAILED',
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

        from backend.domain.priority import compute_priority_score
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
        raise HTTPException(status_code=409, detail="No pending questions for this application")

    # Use first unresolved input; single answer applies to it
    first_id = str(unresolved[0]["id"])
    answers = [{"input_id": first_id, "answer": body.answer}]

    async with db_transaction(db) as conn:
        await InputRepo.update_answers(conn, answers)
        await EventRepo.emit(conn, application_id, "USER_ANSWERED", {"input_id": first_id, "answer": body.answer}, tenant_id=ctx.tenant_id)
        await ApplicationRepo.update_status(conn, application_id, "QUEUED")
        await EventRepo.emit(conn, application_id, "RETRY_SCHEDULED", {"answered_count": 1}, tenant_id=ctx.tenant_id)

    return {"status": "saved", "application_id": application_id, "message": "Answer saved; application re-queued."}


# ---------------------------------------------------------------------------
# POST /applications/{id}/snooze
# ---------------------------------------------------------------------------

class SnoozeBody(BaseModel):
    hours: int = 24


@router.post("/applications/{application_id}/snooze")
async def snooze_application(
    application_id: str = FastAPIPath(...),
    body: SnoozeBody = SnoozeBody(),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Snooze an application for N hours."""
    from shared.validators import validate_uuid
    validate_uuid(application_id, "application_id")
    from datetime import datetime, timedelta

    until = datetime.now(UTC) + timedelta(hours=body.hours)

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
    limit: int = 25,
    offset: int = 0,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """List jobs from DB with optional filters. Returns { jobs: [...], next_offset } for web."""
    from backend.domain.job_search import search_and_list_jobs

    # Clamp limit to prevent runaway payloads
    limit = max(5, min(limit, 100))
    offset = max(0, offset)

    jobs = await search_and_list_jobs(
        db_pool=db,
        location=location,
        min_salary=min_salary,
        keywords=keywords,
        limit=limit,
        offset=offset,
    )

    next_offset = offset + len(jobs) if len(jobs) == limit else None
    return {"jobs": jobs, "next_offset": next_offset}


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
    writer.writerow(["ID", "Job Title", "Company", "Location", "Status", "Last Activity"])
    for r in rows:
        writer.writerow([
            str(r["id"]),
            r["job_title"],
            r["company"],
            r["location"],
            _status_to_web(r["status"]),
            r["updated_at"].isoformat() if r["updated_at"] else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"}
    )

@router.get("/profile")
async def get_profile(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Current user profile for web: id, email, has_completed_onboarding, resume_url, preferences."""
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
    return {
        "id": str(user_row["id"]),
        "email": user_row["email"] or "",
        "has_completed_onboarding": profile_data.get("has_completed_onboarding", False),
        "resume_url": resume_url,
        "preferences": prefs,
        "contact": contact,
        "headline": profile_data.get("headline", ""),
        "bio": profile_data.get("summary", ""),
    }


# ---------------------------------------------------------------------------
# PATCH /profile
# ---------------------------------------------------------------------------

class Preferences(BaseModel):
    location: str | None = None
    role_type: str | None = None
    salary_min: int | None = None
    remote_only: bool | None = None
    work_authorized: bool | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    headline: str | None = None
    bio: str | None = None
    has_completed_onboarding: bool | None = None
    preferences: Preferences | None = None
    avatar_url: str | None = None
    resume_url: str | None = None
    contact: dict | None = None

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
    limiter = _get_profile_limiter(ctx.user_id)
    if not await limiter.acquire():
        from shared.metrics import incr
        incr("profile.update.rate_limited", {"user_id": ctx.user_id})
        raise HTTPException(status_code=429, detail="Too many profile updates. Please retry later.")
    async with db.acquire() as conn:
        existing = await ProfileRepo.get_profile_data(conn, ctx.user_id)
        profile_data = dict(existing or {})
        
        # Check if we are completing onboarding
        was_onboarding = profile_data.get("has_completed_onboarding", False)
        
        _merge_profile_update(profile_data, body)
        
        now_onboarding = profile_data.get("has_completed_onboarding", False)
        
        if not was_onboarding and now_onboarding:
            background_tasks.add_task(
                _hydrate_job_matches,
                db_pool=db,
                user_id=ctx.user_id,
                tenant_id=ctx.tenant_id,
                preferences=profile_data.get("preferences", {})
            )

        existing_row = await conn.fetchrow(
            "SELECT resume_url FROM public.profiles WHERE user_id = $1",
            ctx.user_id,
        )
        current_resume = existing_row["resume_url"] if existing_row else None

        await ProfileRepo.upsert(
            conn, ctx.user_id, profile_data,
            resume_url=body.resume_url if body.resume_url is not None else current_resume,
            tenant_id=ctx.tenant_id,
        )
        row = await conn.fetchrow(
            "SELECT resume_url FROM public.profiles WHERE user_id = $1",
            ctx.user_id,
        )
        final_resume = row["resume_url"] if row else None

    return {
        "id": ctx.user_id,
        "email": user_row["email"] if (user_row := await conn.fetchrow("SELECT email FROM public.users WHERE id = $1", ctx.user_id)) else "",
        "has_completed_onboarding": profile_data.get("has_completed_onboarding", False),
        "resume_url": final_resume,
        "preferences": profile_data.get("preferences") or {},
        "contact": profile_data.get("contact") or {},
    }


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

    avatar_url = body.avatar_url if body.avatar_url is not None else contact.get("avatar_url")
    if avatar_url:
        contact["avatar_url"] = avatar_url

    # Merge nested contact fields sent from Onboarding / Settings
    if body.contact is not None:
        _CONTACT_FIELDS = (
            "first_name", "last_name", "full_name", "email", "phone",
            "linkedin_url", "portfolio_url", "location",
        )
        for field in _CONTACT_FIELDS:
            if field in body.contact and body.contact[field] is not None:
                contact[field] = body.contact[field]
        # Preserve avatar_url from the existing contact if not in body.contact
        if "avatar_url" in body.contact and body.contact["avatar_url"]:
            contact["avatar_url"] = body.contact["avatar_url"]

    profile_data["contact"] = contact


async def _hydrate_job_matches(
    db_pool: asyncpg.Pool,
    user_id: str,
    tenant_id: str,
    preferences: dict
) -> None:
    """Background task to pre-fetch and cache job matches after onboarding."""
    try:
        from backend.domain.job_search import search_and_list_jobs
        
        # Extract basic filters from preferences
        location = preferences.get("location")
        role = preferences.get("role_type")
        salary_str = preferences.get("salary_min")
        salary = int(salary_str) if salary_str and str(salary_str).isdigit() else None
        
        logger.info(u"Hydrating job matches for user %s", user_id)
        
        # Fetch top 20 jobs to populate specific caches
        await search_and_list_jobs(
            db_pool=db_pool,
            location=location,
            keywords=role,
            min_salary=salary,
            limit=20,
            offset=0
        )
    except Exception as e:
        logger.error(u"Failed to hydrate job matches: %s", e)


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
        raise HTTPException(status_code=429, detail="Too many uploads. Please retry later.")
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Simple corruption guard: reject empty files
    if file.size == 0:
        raise HTTPException(status_code=400, detail="File is empty or corrupted")

    settings = get_settings()
    # Pre-check Content-Length header to reject before reading body into memory
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

    resume_url, canonical = await process_resume_upload(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        pdf_bytes=pdf_bytes,
        db_pool=db,
    )

    # Telemetry: successful upload
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
        raise HTTPException(status_code=429, detail="Too many uploads. Please retry later.")
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

    avatar_url = await upload_to_supabase_storage(
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
