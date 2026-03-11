"""Resume Agent Integration API endpoints.

Provides integration between the resume tailoring system and the
Playwright-based application agent with endpoints for:

- Automatic resume preparation for applications
- Template recommendation and selection
- ATS optimization integration
- Application agent resume updates
- Integration analytics and monitoring
- Batch processing capabilities

Key endpoints:
- POST /resume-integration/prepare - Prepare resume for application
- GET /resume-integration/status/{application_id} - Get integration status
- POST /resume-integration/batch - Batch prepare multiple resumes
- GET /resume-integration/analytics - Get integration analytics
- POST /resume-integration/recommend-template - Get template recommendation
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import asyncpg
from backend.domain.resume_agent_integration import get_resume_agent_integration
from backend.domain.tenant import TenantContext
from shared.logging_config import get_logger
from shared.validators import validate_uuid

logger = get_logger("sorce.resume_integration")

router = APIRouter(tags=["resume_integration"])


class PrepareResumeRequest(BaseModel):
    """Request for preparing resume for application."""

    application_id: str = Field(..., description="Application identifier")
    profile: Dict[str, Any] = Field(..., description="User profile data")
    job: Dict[str, Any] = Field(..., description="Job posting data")
    template_style: Optional[str] = Field(
        default=None, description="Template style override"
    )
    force_tailoring: bool = Field(default=False, description="Force retailoring")


class PrepareResumeResponse(BaseModel):
    """Response for resume preparation."""

    success: bool = Field(..., description="Preparation success status")
    application_id: str = Field(..., description="Application identifier")
    template_style: Optional[str] = Field(
        default=None, description="Template style used"
    )
    ats_score: Optional[float] = Field(
        default=None, description="ATS optimization score"
    )
    tailoring_confidence: Optional[str] = Field(
        default=None, description="Tailoring confidence level"
    )
    pdf_id: Optional[str] = Field(default=None, description="Generated PDF ID")
    file_size: Optional[int] = Field(default=None, description="PDF file size in bytes")
    highlighted_skills: List[str] = Field(default=[], description="Highlighted skills")
    emphasized_experiences: List[Dict[str, Any]] = Field(
        default=[], description="Emphasized experiences"
    )
    added_keywords: List[str] = Field(default=[], description="Added keywords")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BatchPrepareRequest(BaseModel):
    """Request for batch resume preparation."""

    applications: List[Dict[str, Any]] = Field(..., description="List of applications")
    profiles: Dict[str, Dict[str, Any]] = Field(
        ..., description="User profiles mapping"
    )
    jobs: Dict[str, Dict[str, Any]] = Field(..., description="Job data mapping")
    template_style: Optional[str] = Field(
        default=None, description="Default template style"
    )
    force_tailoring: bool = Field(default=False, description="Force retailoring")


class BatchPrepareResponse(BaseModel):
    """Response for batch resume preparation."""

    results: List[PrepareResumeResponse] = Field(..., description="Preparation results")
    total_processed: int = Field(..., description="Total applications processed")
    successful: int = Field(..., description="Successful preparations")
    failed: int = Field(..., description="Failed preparations")
    success_rate: float = Field(..., description="Success rate percentage")


class IntegrationStatusResponse(BaseModel):
    """Response for integration status."""

    application_id: str = Field(..., description="Application identifier")
    resume_prepared: bool = Field(..., description="Whether resume was prepared")
    template_used: Optional[str] = Field(
        default=None, description="Template style used"
    )
    ats_score: Optional[float] = Field(
        default=None, description="ATS optimization score"
    )
    pdf_generated: bool = Field(..., description="Whether PDF was generated")
    integration_status: str = Field(..., description="Integration status")
    error_message: Optional[str] = Field(
        default=None, description="Error message if any"
    )


class TemplateRecommendationRequest(BaseModel):
    """Request for template recommendation."""

    job: Dict[str, Any] = Field(..., description="Job posting data")
    profile: Dict[str, Any] = Field(..., description="User profile data")


class TemplateRecommendationResponse(BaseModel):
    """Response for template recommendation."""

    recommended_template: str = Field(..., description="Recommended template style")
    reasoning: str = Field(..., description="Recommendation reasoning")
    confidence: float = Field(..., description="Recommendation confidence (0.0-1.0)")
    alternatives: List[str] = Field(default=[], description="Alternative templates")


class IntegrationAnalyticsResponse(BaseModel):
    """Response for integration analytics."""

    total_integrations: int = Field(..., description="Total integrations")
    success_rate: float = Field(..., description="Success rate percentage")
    average_ats_score: float = Field(..., description="Average ATS optimization score")
    template_usage: Dict[str, int] = Field(..., description="Template usage counts")
    performance_metrics: Dict[str, float] = Field(
        ..., description="Performance metrics"
    )


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


@router.post("/prepare", response_model=PrepareResumeResponse)
async def prepare_resume_for_application(
    request: PrepareResumeRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> PrepareResumeResponse:
    """Prepare a tailored resume for job application.

    This endpoint:
    1. Analyzes job requirements and user profile
    2. Determines optimal template style
    3. Generates ATS-optimized tailored resume
    4. Stores PDF for application agent
    5. Updates application with resume info

    Args:
        request: Resume preparation request
        ctx: Tenant context for identification

    Returns:
        Preparation result with metadata
    """
    try:
        validate_uuid(request.application_id, "application_id")
        async with db.acquire() as conn:
            app = await conn.fetchrow(
                """SELECT id FROM public.applications
                   WHERE id = $1 AND user_id = $2 AND (tenant_id = $3 OR tenant_id IS NULL)""",
                request.application_id,
                ctx.user_id,
                ctx.tenant_id,
            )
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")

        integration_service = get_resume_agent_integration()

        job = request.job or {}
        result = await integration_service.prepare_resume_for_application(
            user_id=ctx.user_id,
            job_id=job.get("id", ""),
            application_id=request.application_id,
            profile=request.profile,
            job=job,
            template_style=request.template_style,
            force_tailoring=request.force_tailoring,
        )

        return PrepareResumeResponse(**result)

    except Exception as e:
        logger.error(
            f"Resume preparation failed for application {request.application_id}: {e}"
        )
        return PrepareResumeResponse(
            success=False,
            application_id=request.application_id,
            error=str(e),
        )


@router.get("/status/{application_id}", response_model=IntegrationStatusResponse)
async def get_integration_status(
    application_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> IntegrationStatusResponse:
    """Get the status of resume integration for an application.

    Args:
        application_id: Application identifier
        ctx: Tenant context for authorization

    Returns:
        Integration status information
    """
    try:
        validate_uuid(application_id, "application_id")
        async with db.acquire() as conn:
            app = await conn.fetchrow(
                """SELECT id FROM public.applications
                   WHERE id = $1 AND user_id = $2 AND (tenant_id = $3 OR tenant_id IS NULL)""",
                application_id,
                ctx.user_id,
                ctx.tenant_id,
            )
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")

        integration_service = get_resume_agent_integration()

        status = await integration_service.get_resume_integration_status(
            application_id=application_id
        )

        return IntegrationStatusResponse(**status)

    except Exception as e:
        logger.error(f"Failed to get integration status for {application_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve integration status"
        )


@router.post("/batch", response_model=BatchPrepareResponse)
async def batch_prepare_resumes(
    request: BatchPrepareRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> BatchPrepareResponse:
    """Prepare resumes for multiple applications in batch.

    Args:
        request: Batch preparation request
        ctx: Tenant context for identification

    Returns:
        Batch preparation results
    """
    try:
        # API-4: Reject applications not belonging to current user
        for app in request.applications:
            uid = app.get("user_id") if isinstance(app, dict) else getattr(app, "user_id", None)
            if uid is not None and str(uid) != str(ctx.user_id):
                raise HTTPException(
                    status_code=403,
                    detail="Cannot prepare resumes for other users' applications",
                )

        integration_service = get_resume_agent_integration()

        results = await integration_service.batch_prepare_resumes(
            applications=request.applications,
            profiles=request.profiles,
            jobs=request.jobs,
        )

        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        success_rate = (successful / len(results)) * 100 if results else 0

        return BatchPrepareResponse(
            results=[PrepareResumeResponse(**result) for result in results],
            total_processed=len(results),
            successful=successful,
            failed=failed,
            success_rate=success_rate,
        )

    except Exception as e:
        logger.error(f"Batch resume preparation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process batch resume preparation"
        )


@router.post("/recommend-template", response_model=TemplateRecommendationResponse)
async def recommend_template(
    request: TemplateRecommendationRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> TemplateRecommendationResponse:
    """Get template recommendation for job application.

    Args:
        request: Template recommendation request
        ctx: Tenant context for identification

    Returns:
        Template recommendation with reasoning
    """
    try:
        integration_service = get_resume_agent_integration()

        recommended_template = await integration_service._recommend_template(
            job=request.job,
            profile=request.profile,
        )

        # Generate reasoning based on job and profile analysis
        request.job.get("title", "").lower()
        request.job.get("description", "").lower()

        reasoning = ""
        confidence = 0.8
        alternatives = ["professional", "modern", "executive", "technical", "creative"]
        alternatives.remove(recommended_template)

        if recommended_template == "executive":
            reasoning = "Executive-level position detected. Senior format with achievement focus recommended."
            confidence = 0.9
        elif recommended_template == "technical":
            reasoning = "Technical/engineering role detected. Skills-focused format with technical emphasis recommended."
            confidence = 0.85
        elif recommended_template == "creative":
            reasoning = "Creative/design role detected. Stylish format with visual elements recommended."
            confidence = 0.8
        elif recommended_template == "professional":
            reasoning = "Professional role detected. Clean, traditional format suitable for most industries recommended."
            confidence = 0.75
        else:
            reasoning = (
                "Default professional template recommended for broad compatibility."
            )
            confidence = 0.7

        return TemplateRecommendationResponse(
            recommended_template=recommended_template,
            reasoning=reasoning,
            confidence=confidence,
            alternatives=alternatives[:3],
        )

    except Exception as e:
        logger.error(f"Template recommendation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate template recommendation"
        )


@router.get("/analytics", response_model=IntegrationAnalyticsResponse)
async def get_integration_analytics(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    user_id: Optional[str] = None,
    job_id: Optional[str] = None,
    template_style: Optional[str] = None,
    date_range: Optional[str] = None,
) -> IntegrationAnalyticsResponse:
    """Get analytics for resume integration.

    Args:
        ctx: Tenant context for identification
        user_id: Optional user filter
        job_id: Optional job filter
        template_style: Optional template filter
        date_range: Optional date range filter

    Returns:
        Integration analytics data
    """
    try:
        integration_service = get_resume_agent_integration()

        analytics = await integration_service.get_integration_analytics(
            user_id=user_id,
            job_id=job_id,
            template_style=template_style,
            date_range=date_range,
        )

        return IntegrationAnalyticsResponse(**analytics)

    except Exception as e:
        logger.error(f"Failed to get integration analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve integration analytics"
        )


@router.post("/update-agent-resume")
async def update_application_agent_resume(
    application_id: str,
    pdf_path: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> Dict[str, Any]:
    """Update the application agent with a new resume file.

    Args:
        application_id: Application identifier
        pdf_path: Path to the tailored PDF
        ctx: Tenant context for authorization

    Returns:
        Update result
    """
    try:
        validate_uuid(application_id, "application_id")
        async with db.acquire() as conn:
            app = await conn.fetchrow(
                """SELECT id FROM public.applications
                   WHERE id = $1 AND user_id = $2 AND (tenant_id = $3 OR tenant_id IS NULL)""",
                application_id,
                ctx.user_id,
                ctx.tenant_id,
            )
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")

        integration_service = get_resume_agent_integration()

        success = await integration_service.update_application_agent_resume(
            application_id=application_id,
            pdf_path=pdf_path,
        )

        if success:
            return {
                "success": True,
                "application_id": application_id,
                "message": "Application agent resume updated successfully",
            }
        else:
            return {
                "success": False,
                "application_id": application_id,
                "message": "Failed to update application agent resume",
            }

    except Exception as e:
        logger.error(
            f"Failed to update application agent resume for {application_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to update application agent resume"
        )


@router.get("/template-usage")
async def get_template_usage_stats(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get template usage statistics.

    Args:
        ctx: Tenant context for identification

    Returns:
        Template usage statistics
    """
    try:
        # TODO: Implement actual template usage query
        # This would aggregate template usage from the database

        return {
            "total_usage": 0,
            "template_breakdown": {
                "professional": 0,
                "modern": 0,
                "executive": 0,
                "technical": 0,
                "creative": 0,
            },
            "recent_trends": {
                "last_7_days": {
                    "professional": 0,
                    "modern": 0,
                    "executive": 0,
                    "technical": 0,
                    "creative": 0,
                },
                "last_30_days": {
                    "professional": 0,
                    "modern": 0,
                    "executive": 0,
                    "technical": 0,
                    "creative": 0,
                },
            },
            "performance_by_template": {
                "professional": {
                    "usage_count": 0,
                    "average_ats_score": 0.0,
                    "success_rate": 0.0,
                },
                "modern": {
                    "usage_count": 0,
                    "average_ats_score": 0.0,
                    "success_rate": 0.0,
                },
                "executive": {
                    "usage_count": 0,
                    "average_ats_score": 0.0,
                    "success_rate": 0.0,
                },
                "technical": {
                    "usage_count": 0,
                    "average_ats_score": 0.0,
                    "success_rate": 0.0,
                },
                "creative": {
                    "usage_count": 0,
                    "average_ats_score": 0.0,
                    "success_rate": 0.0,
                },
            },
        }

    except Exception as e:
        logger.error(f"Failed to get template usage stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve template usage statistics"
        )
