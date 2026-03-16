"""
Phase 14.1 User Experience API endpoints.
Pipeline view, export applications, follow-up reminders, answer memory, multi-resume support, application notes.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from packages.backend.domain.answer_memory import (
    AnswerAttempt,
    AnswerMemory,
    AnswerMemoryManager,
    InterviewQuestion,
)
from packages.backend.domain.application_export import (
    ApplicationExportManager,
    ExportConfig,
)
from packages.backend.domain.application_notes import (
    ApplicationNote,
    ApplicationNotesManager,
    NoteTemplate,
)
from packages.backend.domain.application_pipeline import (
    ApplicationPipelineManager,
    PipelineView,
)
from packages.backend.domain.follow_up_reminders import (
    FollowUpManager,
    FollowUpReminder,
    ReminderSchedule,
)
from packages.backend.domain.multi_resume import (
    MultiResumeManager,
    ResumeAnalytics,
    ResumeComparison,
    ResumeVersion,
)
from packages.backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

from api.deps import (
    get_pool,
    get_pool as _get_pool,
    get_tenant_context,
    get_tenant_context as _get_tenant_ctx,
)

logger = get_logger("sorce.user_experience_api")

router = APIRouter(prefix="/ux", tags=["user_experience"])


# Placeholder dependencies - overridden by main.py with get_pool and get_tenant_context
# Manager factories - receive pool via Depends(_get_pool) so main.py override applies
def get_pipeline_manager(db=Depends(get_pool)):
    from packages.backend.domain.application_pipeline import create_pipeline_manager

    return create_pipeline_manager(db)


def get_export_manager(db=Depends(get_pool)):
    from packages.backend.domain.application_export import create_export_manager

    return create_export_manager(db)


def get_follow_up_manager(db=Depends(get_pool)):
    from packages.backend.domain.follow_up_reminders import create_follow_up_manager

    return create_follow_up_manager(db)


def get_answer_memory_manager(db=Depends(_get_pool)):
    from packages.backend.domain.answer_memory import create_answer_memory_manager

    return create_answer_memory_manager(db)


def get_multi_resume_manager(db=Depends(_get_pool)):
    from packages.backend.domain.multi_resume import create_multi_resume_manager

    return create_multi_resume_manager(db)


def get_application_notes_manager(db=Depends(_get_pool)):
    from packages.backend.domain.application_notes import (
        create_application_notes_manager,
    )

    return create_application_notes_manager(db)


# Pydantic models for API requests/responses


class PipelineViewRequest(BaseModel):
    filters: Optional[Dict[str, Any]] = {}
    sort_by: str = "last_activity"
    sort_order: str = "desc"

    @field_validator("filters", mode="before")
    @classmethod
    def parse_filters(cls, v: object) -> Dict[str, Any]:
        if isinstance(v, str):
            try:
                return json.loads(v) or {}
            except json.JSONDecodeError:
                return {}
        return v if isinstance(v, dict) else {}


class ExportRequest(BaseModel):
    format: str = "csv"
    fields: List[str] = [
        "company",
        "job_title",
        "status",
        "last_activity",
        "created_at",
    ]
    filters: Optional[Dict[str, Any]] = {}
    include_headers: bool = True
    date_format: str = "%Y-%m-%d %H:%M:%S"
    filename_prefix: str = "applications"
    compress: bool = False


class ReminderCreateRequest(BaseModel):
    application_id: str
    reminder_type: str
    scheduled_for: datetime
    message: str
    metadata: Optional[Dict[str, Any]] = {}


class ReminderScheduleRequest(BaseModel):
    reminder_type: str
    days_after_event: int
    is_active: bool = True
    conditions: Optional[Dict[str, Any]] = {}
    template_id: Optional[str] = None


class AnswerAttemptRequest(BaseModel):
    question_id: str
    answer: str
    confidence_score: float = 0.0

    @field_validator("answer")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        from packages.backend.domain.sanitization import sanitize_text_input
        return sanitize_text_input(v)


class AnswerMemoryRequest(BaseModel):
    question_id: str
    memorized_answer: str
    key_points: List[str] = []
    examples: List[str] = []

    @field_validator("memorized_answer")
    @classmethod
    def sanitize_memorized_answer(cls, v: str) -> str:
        from packages.backend.domain.sanitization import sanitize_text_input
        return sanitize_text_input(v)

    @field_validator("key_points", "examples", mode="before")
    @classmethod
    def sanitize_list_items(cls, v: List[str]) -> List[str]:
        from packages.backend.domain.sanitization import sanitize_text_input
        return [sanitize_text_input(str(x)) for x in (v or [])]


class ResumeVersionRequest(BaseModel):
    name: str
    resume_type: str
    file_path: str
    file_size: int
    file_format: str
    description: Optional[str] = None
    target_industries: List[str] = []
    target_roles: List[str] = []
    skills_emphasized: List[str] = []
    is_primary: bool = False


class NoteCreateRequest(BaseModel):
    application_id: str
    title: str
    content: str
    category: str = "general"
    tags: List[str] = []
    is_private: bool = True
    is_pinned: bool = False
    reminder_date: Optional[datetime] = None


class NoteUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_private: Optional[bool] = None
    is_pinned: Optional[bool] = None
    reminder_date: Optional[datetime] = None


# Pipeline view endpoints


@router.get("/pipeline")
async def get_pipeline_view(
    request: PipelineViewRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    pipeline_manager: ApplicationPipelineManager = Depends(get_pipeline_manager),
) -> PipelineView:
    """Get complete pipeline view for user applications."""
    return await pipeline_manager.get_pipeline_view(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        filters=request.filters,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
    )


@router.put("/pipeline/stage")
async def update_application_stage(
    application_id: str,
    new_stage: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    pipeline_manager: ApplicationPipelineManager = Depends(get_pipeline_manager),
) -> Dict[str, bool]:
    """Update application pipeline stage."""
    success = await pipeline_manager.update_application_stage(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        application_id=application_id,
        new_stage=new_stage,
    )
    return {"success": success}


@router.put("/pipeline/stage/bulk")
async def bulk_update_stages(
    application_ids: List[str],
    new_stage: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    pipeline_manager: ApplicationPipelineManager = Depends(get_pipeline_manager),
) -> Dict[str, bool]:
    """Bulk update application stages."""
    return await pipeline_manager.bulk_update_stages(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        application_ids=application_ids,
        new_stage=new_stage,
    )


# Export endpoints


@router.post("/export/applications")
async def export_applications(
    request: ExportRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    export_manager: ApplicationExportManager = Depends(get_export_manager),
):
    """Export applications in specified format."""
    config = ExportConfig(
        format=request.format,
        fields=request.fields,
        filters=request.filters,
        include_headers=request.include_headers,
        date_format=request.date_format,
        filename_prefix=request.filename_prefix,
        compress=request.compress,
    )

    return await export_manager.export_applications(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        config=config,
    )


@router.get("/export/templates")
async def get_export_templates(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    export_manager: ApplicationExportManager = Depends(get_export_manager),
) -> List[Dict[str, Any]]:
    """Get available export templates."""
    return await export_manager.get_export_templates(ctx.tenant_id)


# Follow-up reminders endpoints


@router.post("/reminders")
async def create_reminder(
    request: ReminderCreateRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    follow_up_manager: FollowUpManager = Depends(get_follow_up_manager),
) -> FollowUpReminder:
    """Create a new follow-up reminder."""
    return await follow_up_manager.create_reminder(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        application_id=request.application_id,
        reminder_type=request.reminder_type,
        scheduled_for=request.scheduled_for,
        message=request.message,
        metadata=request.metadata,
    )


@router.post("/reminders/schedule")
async def schedule_application_reminders(
    application_id: str,
    application_status: str,
    schedules: Optional[List[ReminderScheduleRequest]] = None,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    follow_up_manager: FollowUpManager = Depends(get_follow_up_manager),
) -> List[FollowUpReminder]:
    """Schedule reminders for a new application."""
    schedule_objects = []
    if schedules:
        for schedule in schedules:
            schedule_objects.append(
                ReminderSchedule(
                    reminder_type=schedule.reminder_type,
                    days_after_event=schedule.days_after_event,
                    is_active=schedule.is_active,
                    conditions=schedule.conditions,
                    template_id=schedule.template_id,
                )
            )

    return await follow_up_manager.schedule_application_reminders(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        application_id=application_id,
        application_status=application_status,
        schedules=schedule_objects,
    )


@router.get("/reminders")
async def get_user_reminders(
    status: Optional[str] = None,
    limit: int = 50,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    follow_up_manager: FollowUpManager = Depends(get_follow_up_manager),
) -> List[FollowUpReminder]:
    """Get user's reminders."""
    return await follow_up_manager.get_user_reminders(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        status=status,
        limit=limit,
    )


@router.get("/reminders/pending")
async def get_pending_reminders(
    limit: int = 100,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    follow_up_manager: FollowUpManager = Depends(get_follow_up_manager),
) -> List[FollowUpReminder]:
    """Get pending reminders that are due."""
    return await follow_up_manager.get_pending_reminders(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        limit=limit,
    )


@router.put("/reminders/{reminder_id}/send")
async def send_reminder(
    reminder_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    follow_up_manager: FollowUpManager = Depends(get_follow_up_manager),
) -> Dict[str, bool]:
    """Send a reminder."""
    success = await follow_up_manager.send_reminder(reminder_id)
    return {"success": success}


@router.put("/reminders/{reminder_id}/complete")
async def complete_reminder(
    reminder_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    follow_up_manager: FollowUpManager = Depends(get_follow_up_manager),
) -> Dict[str, bool]:
    """Mark a reminder as completed."""
    success = await follow_up_manager.complete_reminder(reminder_id, ctx.user_id)
    return {"success": success}


@router.put("/reminders/{reminder_id}/snooze")
async def snooze_reminder(
    reminder_id: str,
    days: int = 1,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    follow_up_manager: FollowUpManager = Depends(get_follow_up_manager),
) -> Dict[str, bool]:
    """Snooze a reminder by specified days."""
    success = await follow_up_manager.snooze_reminder(reminder_id, ctx.user_id, days)
    return {"success": success}


# Answer memory endpoints


@router.get("/interview/questions/recommended")
async def get_recommended_questions(
    job_title: str,
    company_name: Optional[str] = None,
    limit: int = 10,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    answer_memory_manager: AnswerMemoryManager = Depends(get_answer_memory_manager),
) -> List[InterviewQuestion]:
    """Get recommended interview questions for a job."""
    return await answer_memory_manager.get_recommended_questions(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        job_title=job_title,
        company_name=company_name,
        limit=limit,
    )


@router.post("/interview/attempts")
async def save_answer_attempt(
    request: AnswerAttemptRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    answer_memory_manager: AnswerMemoryManager = Depends(get_answer_memory_manager),
) -> AnswerAttempt:
    """Save an answer attempt with AI scoring."""
    return await answer_memory_manager.save_answer_attempt(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        question_id=request.question_id,
        answer=request.answer,
        confidence_score=request.confidence_score,
    )


@router.post("/interview/memory")
async def create_answer_memory(
    request: AnswerMemoryRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    answer_memory_manager: AnswerMemoryManager = Depends(get_answer_memory_manager),
) -> AnswerMemory:
    """Create or update answer memory entry."""
    return await answer_memory_manager.create_answer_memory(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        question_id=request.question_id,
        memorized_answer=request.memorized_answer,
        key_points=request.key_points,
        examples=request.examples,
    )


@router.get("/interview/memory")
async def get_user_memories(
    category: Optional[str] = None,
    mastery_threshold: float = 0.0,
    limit: int = 50,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    answer_memory_manager: AnswerMemoryManager = Depends(get_answer_memory_manager),
) -> List[AnswerMemory]:
    """Get user's answer memories."""
    return await answer_memory_manager.get_user_memories(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        category=category,
        mastery_threshold=mastery_threshold,
        limit=limit,
    )


@router.get("/interview/analytics/{question_id}")
async def get_question_analytics(
    question_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    answer_memory_manager: AnswerMemoryManager = Depends(get_answer_memory_manager),
) -> Optional[Dict[str, Any]]:
    """Get analytics for a specific question."""
    analytics = await answer_memory_manager.get_question_analytics(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        question_id=question_id,
    )
    return analytics.model_dump() if analytics else None


@router.put("/interview/mastery/{question_id}")
async def update_mastery_level(
    question_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    answer_memory_manager: AnswerMemoryManager = Depends(get_answer_memory_manager),
) -> Dict[str, float]:
    """Update and return mastery level for a question."""
    mastery = await answer_memory_manager.update_mastery_level(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        question_id=question_id,
    )
    return {"mastery_level": mastery}


# Multi-resume endpoints


@router.post("/resumes")
async def create_resume_version(
    request: ResumeVersionRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    multi_resume_manager: MultiResumeManager = Depends(get_multi_resume_manager),
) -> ResumeVersion:
    """Create a new resume version."""
    return await multi_resume_manager.create_resume_version(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        name=request.name,
        resume_type=request.resume_type,
        file_path=request.file_path,
        file_size=request.file_size,
        file_format=request.file_format,
        description=request.description,
        target_industries=request.target_industries,
        target_roles=request.target_roles,
        skills_emphasized=request.skills_emphasized,
        is_primary=request.is_primary,
    )


@router.get("/resumes")
async def get_user_resumes(
    resume_type: Optional[str] = None,
    is_active: bool = True,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    multi_resume_manager: MultiResumeManager = Depends(get_multi_resume_manager),
) -> List[ResumeVersion]:
    """Get user's resume versions."""
    return await multi_resume_manager.get_user_resumes(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        resume_type=resume_type,
        is_active=is_active,
    )


@router.get("/resumes/recommend")
async def recommend_resume_for_job(
    job_title: str,
    company_industry: str,
    job_description: str = "",
    required_skills: List[str] = [],
    ctx: TenantContext = Depends(_get_tenant_ctx),
    multi_resume_manager: MultiResumeManager = Depends(get_multi_resume_manager),
) -> Optional[ResumeVersion]:
    """Recommend the best resume for a specific job."""
    return await multi_resume_manager.recommend_resume_for_job(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        job_title=job_title,
        company_industry=company_industry,
        job_description=job_description,
        required_skills=required_skills,
    )


@router.post("/resumes/compare")
async def compare_resumes(
    resume1_id: str,
    resume2_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    multi_resume_manager: MultiResumeManager = Depends(get_multi_resume_manager),
) -> ResumeComparison:
    """Compare two resume versions."""
    comparison = await multi_resume_manager.compare_resumes(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        resume1_id=resume1_id,
        resume2_id=resume2_id,
    )
    if not comparison:
        raise HTTPException(status_code=404, detail="One or both resumes not found")
    return comparison


@router.get("/resumes/{resume_id}/analytics")
async def get_resume_analytics(
    resume_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    multi_resume_manager: MultiResumeManager = Depends(get_multi_resume_manager),
) -> ResumeAnalytics:
    """Get analytics for a specific resume."""
    return await multi_resume_manager.update_resume_analytics(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        resume_id=resume_id,
    )


@router.put("/resumes/{resume_id}/primary")
async def set_primary_resume(
    resume_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    multi_resume_manager: MultiResumeManager = Depends(get_multi_resume_manager),
) -> Dict[str, bool]:
    """Set a resume as the primary resume."""
    success = await multi_resume_manager.set_primary_resume(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        resume_id=resume_id,
    )
    return {"success": success}


@router.delete("/resumes/{resume_id}")
async def delete_resume_version(
    resume_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    multi_resume_manager: MultiResumeManager = Depends(get_multi_resume_manager),
) -> Dict[str, bool]:
    """Delete a resume version."""
    success = await multi_resume_manager.delete_resume_version(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        resume_id=resume_id,
    )
    return {"success": success}


# Application notes endpoints


@router.post("/notes")
async def create_note(
    request: NoteCreateRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> ApplicationNote:
    """Create a new application note."""
    return await notes_manager.create_note(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        application_id=request.application_id,
        title=request.title,
        content=request.content,
        category=request.category,
        tags=request.tags,
        is_private=request.is_private,
        is_pinned=request.is_pinned,
        reminder_date=request.reminder_date,
    )


@router.get("/notes/search")
async def search_notes(
    query: str = "",
    application_id: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> List[Dict[str, Any]]:
    """Search notes with relevance scoring. Empty query returns recent notes."""
    if not query.strip():
        notes = await notes_manager.get_recent_notes(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            limit=limit,
        )
        return [
            {"note": n.model_dump(), "relevance_score": 0.0, "matched_terms": []}
            for n in notes
        ]
    results = await notes_manager.search_notes(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        search_query=query,
        application_id=application_id,
        category=category,
        tags=tags,
        limit=limit,
    )
    return [result.model_dump() for result in results]


@router.get("/notes/reminders")
async def get_notes_with_reminders(
    days_ahead: int = 7,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> List[ApplicationNote]:
    """Get notes with upcoming reminders."""
    return await notes_manager.get_notes_with_reminders(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        days_ahead=days_ahead,
    )


@router.get("/notes/templates")
async def get_note_templates(
    category: Optional[str] = None,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> List[NoteTemplate]:
    """Get available note templates."""
    return await notes_manager.get_note_templates(category=category)


@router.post("/notes/from-template")
async def create_note_from_template(
    application_id: str,
    template_id: str,
    variables: Dict[str, str],
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> ApplicationNote:
    """Create a note from a template."""
    return await notes_manager.create_note_from_template(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        application_id=application_id,
        template_id=template_id,
        variables=variables,
    )


@router.get("/notes/statistics")
async def get_note_statistics(
    days_back: int = 30,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> Dict[str, Any]:
    """Get statistics about user's notes."""
    return await notes_manager.get_note_statistics(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        days_back=days_back,
    )


@router.get("/notes/{application_id}")
async def get_application_notes(
    application_id: str,
    category: Optional[str] = None,
    include_private: bool = True,
    limit: int = 50,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> List[ApplicationNote]:
    """Get notes for a specific application."""
    return await notes_manager.get_application_notes(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        application_id=application_id,
        category=category,
        include_private=include_private,
        limit=limit,
    )


@router.put("/notes/{note_id}")
async def update_note(
    note_id: str,
    request: NoteUpdateRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> Dict[str, bool]:
    """Update an existing note."""
    success = await notes_manager.update_note(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        note_id=note_id,
        title=request.title,
        content=request.content,
        category=request.category,
        tags=request.tags,
        is_private=request.is_private,
        is_pinned=request.is_pinned,
        reminder_date=request.reminder_date,
    )
    return {"success": success}


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    notes_manager: ApplicationNotesManager = Depends(get_application_notes_manager),
) -> Dict[str, bool]:
    """Delete a note."""
    success = await notes_manager.delete_note(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        note_id=note_id,
    )
    return {"success": success}


# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for user experience features."""
    return {"status": "healthy", "service": "user_experience"}
