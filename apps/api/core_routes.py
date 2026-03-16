"""Core API routes that were previously defined inline in main.py.

Extracted as part of PERF-001 to reduce main.py from ~2158 to ~1400 lines.
Contains:
  - /me/answer-memory   (smart pre-fill)
  - /me/skills          (rich skills management)
  - /me/work-style      (work style profile)
  - /me/dashboard       (user dashboard widget)
  - /me/team/members    (team member listing)
  - /webhook/resume_parse  (resume upload + parse)
  - /agent/resume_task     (answer hold questions)
  - /applications/{id}     (application detail)
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
from datetime import timedelta
from typing import Any
from urllib.parse import unquote

import asyncpg
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi import Path as FastAPIPath
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.deps import (
    get_current_user_id as _get_user_id,
    get_pool as _get_pool,
    get_tenant_context as _get_tenant_ctx,
)
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
    ProfileRepo,
    build_user_dashboard_cache_key,
    db_transaction,
)
from packages.backend.domain.resume import process_resume_upload
from packages.backend.domain.tenant import TenantContext
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr
from shared.query_cache import get_cached, set_cached
from shared.storage import get_storage_service
from shared.validators import validate_uuid

logger = get_logger("sorce.api.core_routes")

_DASHBOARD_CACHE_TTL = timedelta(seconds=30)


router = APIRouter(tags=["core"])

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
        """Sanitize HTML and prompt injection in user input."""
        from packages.backend.domain.sanitization import sanitize_text_input
        from shared.ai_validation import sanitize_for_ai

        v = sanitize_text_input(v, max_length=5000)
        r = sanitize_for_ai(v, max_length=5000, min_length=None)
        return r.sanitized_input or v[:5000] if r.is_valid else v[:5000]


class ResumeTaskRequest(BaseModel):
    application_id: str = Field(
        ..., min_length=36, max_length=36, description="Application identifier"
    )
    answers: list[AnswerItem] = Field(
        ...,
        max_length=100,
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
        """Sanitize free-text fields to prevent XSS."""
        if v is None:
            return None
        from packages.backend.domain.sanitization import sanitize_text_input

        return sanitize_text_input(v, max_length=500)

    @field_validator("related_to")
    @classmethod
    def sanitize_related_to(cls, v: list[str]) -> list[str]:
        """Sanitize related skill names."""
        from packages.backend.domain.sanitization import sanitize_text_input

        return [sanitize_text_input(x, max_length=100) for x in (v or [])[:20]]


class SaveSkillsRequest(BaseModel):
    skills: list[RichSkillRequest] = Field(
        ...,
        max_length=500,
        description="List of skills (max 500)",
    )


class WorkStyleRequest(BaseModel):
    autonomy_preference: str = Field(
        default="medium",
        pattern="^(low|medium|high)$",
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
        description="Career trajectory",
    )

    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------------------
# Answer Memory endpoints
# ---------------------------------------------------------------------------


@router.get("/me/answer-memory")
async def get_answer_memory(
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
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


@router.post("/me/answer-memory")
async def save_answer_memory(
    body: SaveAnswerRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
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


# ---------------------------------------------------------------------------
# Skills endpoints
# ---------------------------------------------------------------------------


@router.get("/me/skills")
async def get_user_skills(
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
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


@router.post("/me/skills")
async def save_user_skills(
    body: SaveSkillsRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Save user's rich skills (upsert)."""
    logger.info(
        "[SKILLS] Saving skills for user",
        extra={"user_id": user_id, "skill_count": len(body.skills)},
    )

    async with db.acquire() as conn:
        async with conn.transaction():
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

            if not user_id:
                logger.warning("Cannot update completeness: user_id is None")
                return {"status": "saved", "count": len(body.skills)}

            from packages.backend.domain.deep_profile import calculate_completeness
            from packages.backend.domain.profile_assembly import assemble_profile

            deep_profile = await assemble_profile(conn, user_id, use_cache=False)
            if deep_profile:
                completeness_score = calculate_completeness(deep_profile)
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


# ---------------------------------------------------------------------------
# Work Style endpoints
# ---------------------------------------------------------------------------


@router.get("/me/work-style")
async def get_work_style(
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
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


@router.post("/me/work-style")
async def save_work_style(
    body: WorkStyleRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Save user's work style profile."""
    logger.info(
        "[WORK_STYLE] Saving work style for user",
        extra={"user_id": user_id},
    )

    async with db_transaction(db) as conn:
        existing_snapshot = await ProfileRepo.get_profile_snapshot(
            conn,
            user_id,
            use_cache=False,
        )
        profile_data = dict(existing_snapshot["profile_data"] or {})

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

        if not user_id:
            logger.warning("Cannot update completeness: user_id is None")
            return {"status": "saved"}

        from packages.backend.domain.deep_profile import calculate_completeness
        from packages.backend.domain.profile_assembly import assemble_profile

        deep_profile = await assemble_profile(conn, user_id, use_cache=False)
        if deep_profile:
            completeness_score = calculate_completeness(deep_profile)
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

        if existing_snapshot["exists"]:
            profile_data["work_style"] = body.model_dump()
            await ProfileRepo.upsert(
                conn,
                user_id,
                profile_data,
                resume_url=existing_snapshot["resume_url"],
            )

    logger.info("[WORK_STYLE] Saved successfully", extra={"user_id": user_id})
    return {"status": "saved"}


# ---------------------------------------------------------------------------
# Dashboard & Team endpoints
# ---------------------------------------------------------------------------


@router.get("/me/dashboard")
async def user_dashboard(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """User dashboard data for mobile v3 home screen + widget."""
    user_id = ctx.user_id
    tenant_id = ctx.tenant_id
    cache_key = build_user_dashboard_cache_key(user_id, tenant_id)

    cached_dashboard = await get_cached(cache_key)
    if cached_dashboard is not None:
        return cached_dashboard

    async with db.acquire() as conn:
        dashboard_row = await conn.fetchrow(
            """
            WITH filtered_applications AS (
                SELECT id, job_id, status, updated_at
                FROM public.applications
                WHERE user_id = $1 AND (tenant_id = $2 OR tenant_id IS NULL)
            ),
            counts AS (
                SELECT
                    COUNT(*) FILTER (WHERE status IN ('QUEUED','PROCESSING'))::int AS active_count,
                    COUNT(*) FILTER (WHERE status = 'REQUIRES_INPUT')::int AS hold_count,
                    COUNT(*) FILTER (
                        WHERE status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED')
                          AND updated_at::date = CURRENT_DATE
                    )::int AS completed_today,
                    COUNT(*) FILTER (
                        WHERE status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED')
                          AND updated_at >= date_trunc('week', now())
                    )::int AS completed_week,
                    COUNT(*)::int AS total_all_time
                FROM filtered_applications
            ),
            recent AS (
                SELECT COALESCE(
                    json_agg(
                        json_build_object(
                            'id', recent_app.id,
                            'job_title', recent_app.job_title,
                            'status', recent_app.status,
                            'updated_at', recent_app.updated_at
                        )
                        ORDER BY recent_app.updated_at DESC
                    ),
                    '[]'::json
                ) AS items
                FROM (
                    SELECT
                        a.id,
                        j.title AS job_title,
                        a.status::text AS status,
                        a.updated_at
                    FROM filtered_applications a
                    LEFT JOIN public.jobs j ON j.id = a.job_id
                    ORDER BY a.updated_at DESC
                    LIMIT 10
                ) recent_app
            )
            SELECT
                counts.active_count,
                counts.hold_count,
                counts.completed_today,
                counts.completed_week,
                counts.total_all_time,
                recent.items AS recent
            FROM counts
            CROSS JOIN recent
            """,
            user_id,
            tenant_id,
        )

    recent_items = dashboard_row["recent"] if dashboard_row else []
    if isinstance(recent_items, str):
        recent_items = json.loads(recent_items)

    result = {
        **(
            {
                "active_count": dashboard_row["active_count"] or 0,
                "hold_count": dashboard_row["hold_count"] or 0,
                "completed_today": dashboard_row["completed_today"] or 0,
                "completed_week": dashboard_row["completed_week"] or 0,
                "total_all_time": dashboard_row["total_all_time"] or 0,
            }
            if dashboard_row
            else {
                "active_count": 0,
                "hold_count": 0,
                "completed_today": 0,
                "completed_week": 0,
                "total_all_time": 0,
            }
        ),
        "recent": recent_items,
    }

    await set_cached(cache_key, result, _DASHBOARD_CACHE_TTL)
    return result


@router.get("/me/team/members")
async def get_team_members(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """Get tenant members for the current user's workspace (team page)."""
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT tm.user_id, tm.role, tm.created_at,
                   u.email, u.full_name, u.avatar_url
            FROM public.tenant_members tm
            LEFT JOIN public.users u ON u.id = tm.user_id
            WHERE tm.tenant_id = $1
            ORDER BY
                CASE tm.role WHEN 'OWNER' THEN 0 WHEN 'ADMIN' THEN 1 ELSE 2 END,
                tm.created_at ASC
            """,
            ctx.tenant_id,
        )
    return [
        {
            "user_id": str(r["user_id"]),
            "email": r["email"],
            "full_name": r["full_name"],
            "avatar_url": r["avatar_url"],
            "role": r["role"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Resume Parse endpoint
# ---------------------------------------------------------------------------


@router.post("/webhook/resume_parse", response_model=ResumeParseResponse)
async def resume_parse(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> ResumeParseResponse:
    """Upload PDF -> extract text -> LLM parse -> normalize -> upsert profile."""
    _settings = get_settings()
    user_id = ctx.user_id
    incr("api.resume_parse.requests", tags={"tenant_id": ctx.tenant_id})
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

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

    if len(pdf_bytes) < 8 or not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF format - file content does not match declared type",
        )

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


# ---------------------------------------------------------------------------
# Resume Task (answer hold questions)
# ---------------------------------------------------------------------------


@router.post("/agent/resume_task", response_model=ResumeTaskResponse)
async def resume_task(
    body: ResumeTaskRequest,
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> ResumeTaskResponse:
    """User answers hold questions -> update inputs -> emit events -> re-queue."""
    incr("api.resume_task.requests", tags={"tenant_id": ctx.tenant_id})
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
        await InputRepo.update_answers(
            conn,
            [{"input_id": a.input_id, "answer": a.answer} for a in body.answers],
            application_id=body.application_id,
        )

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

        updated = await ApplicationRepo.update_status(
            conn, body.application_id, "QUEUED"
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Application not found")

        await EventRepo.emit(
            conn,
            body.application_id,
            "RETRY_SCHEDULED",
            {
                "answered_count": len(body.answers),
            },
            tenant_id=ctx.tenant_id,
        )

        remaining = await InputRepo.get_unresolved(conn, body.application_id)

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


# ---------------------------------------------------------------------------
# Application Detail endpoint
# ---------------------------------------------------------------------------


@router.get("/applications/{application_id}", response_model=ApplicationDetailResponse)
async def get_application_detail(
    application_id: str = FastAPIPath(...),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
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
# Storage endpoint — serve files from Render Disk or local storage
# ---------------------------------------------------------------------------


@router.get("/api/storage/{bucket}/{path:path}")
async def serve_storage_file(
    bucket: str,
    path: str,
    user_id: str = Depends(_get_user_id),
    tenant_ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Response:
    """Serve files from storage (e.g., resumes, avatars)."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", bucket):
        raise HTTPException(status_code=400, detail="Invalid bucket name")

    tenant_id = tenant_ctx.tenant_id or ""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    decoded_path = unquote(path)
    if ".." in decoded_path or ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    if "%2e" in path.lower() or "%252e" in path.lower():
        raise HTTPException(status_code=400, detail="Invalid path")
    normalized_path = os.path.normpath(decoded_path)
    if normalized_path.startswith("/") or normalized_path.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid path")

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

    content_type = (
        mimetypes.guess_type(normalized_path)[0] or "application/octet-stream"
    )

    return Response(content=data, media_type=content_type)
