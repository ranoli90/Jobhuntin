"""Resume PDF generation API endpoints.

Provides comprehensive PDF generation for tailored resumes with:
- Professional template generation
- ATS optimization integration
- Multiple template styles
- Compliance reporting
- Download functionality
- Preview generation

Key endpoints:
- POST /resume-pdf/generate - Generate tailored resume PDF
- GET /resume-pdf/templates - Get available templates
- POST /resume-pdf/ats-report - Generate ATS compliance report
- GET /resume-pdf/download/{resume_id} - Download generated PDF
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from packages.backend.domain.resume_pdf_generator import get_pdf_generator
from packages.backend.domain.resume_tailoring import get_tailoring_service
from packages.backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

from api.deps import get_tenant_context

logger = get_logger("sorce.resume_pdf")

router = APIRouter(tags=["resume_pdf"])


class GenerateResumePDFRequest(BaseModel):
    """Request for generating tailored resume PDF."""

    profile: Dict[str, Any] = Field(..., description="User profile data")
    job: Dict[str, Any] = Field(..., description="Job posting data")
    template_style: str = Field(default="professional", description="Template style")
    include_ats_keywords: bool = Field(
        default=True, description="Include ATS keywords section"
    )
    optimize_for_ats: bool = Field(default=True, description="Optimize for ATS systems")


class GenerateResumePDFResponse(BaseModel):
    """Response for resume PDF generation."""

    resume_id: str = Field(..., description="Generated resume ID")
    pdf_url: str = Field(..., description="URL to download PDF")
    ats_score: float = Field(..., description="ATS optimization score")
    file_size: int = Field(..., description="PDF file size in bytes")
    template_used: str = Field(..., description="Template style used")
    generation_time: float = Field(..., description="Generation time in seconds")


class ATSComplianceReport(BaseModel):
    """ATS compliance report for tailored resume."""

    ats_score: float = Field(..., description="Overall ATS score (0.0-1.0)")
    compliance_level: str = Field(..., description="Compliance level (High/Medium/Low)")
    keyword_match: int = Field(..., description="Number of matched keywords")
    skills_highlighted: int = Field(..., description="Number of highlighted skills")
    experiences_emphasized: int = Field(
        ..., description="Number of emphasized experiences"
    )
    recommendations: List[str] = Field(
        default=[], description="Improvement recommendations"
    )
    tailoring_confidence: str = Field(..., description="Tailoring confidence level")


class ResumeTemplate(BaseModel):
    """Resume template information."""

    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Template category")
    ats_optimized: bool = Field(default=True, description="ATS optimized")
    preview_url: Optional[str] = Field(default=None, description="Preview image URL")


@router.post("/generate", response_model=GenerateResumePDFResponse)
async def generate_tailored_resume_pdf(
    request: GenerateResumePDFRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> GenerateResumePDFResponse:
    """Generate a tailored resume PDF.

    This endpoint:
    1. Tailors the resume content for the specific job
    2. Generates ATS-optimized PDF
    3. Returns download information
    4. Stores the generated PDF for download

    Args:
        request: PDF generation request
        ctx: Tenant context for identification

    Returns:
        Generated resume PDF information
    """
    import time
    import uuid

    start_time = time.time()

    try:
        # Step 1: Tailor the resume content
        tailoring_service = get_tailoring_service()
        tailoring_result = await tailoring_service.tailor_resume(
            profile=request.profile,
            job=request.job,
        )

        # Step 2: Generate PDF
        pdf_generator = get_pdf_generator()
        pdf_bytes = pdf_generator.generate_tailored_resume_pdf(
            profile=request.profile,
            job=request.job,
            tailoring_result=tailoring_result,
            template_style=request.template_style,
        )

        # Step 3: Store PDF (in production, use cloud storage)
        resume_id = str(uuid.uuid4())

        # TODO: Store PDF in cloud storage or database
        # For now, we'll generate a temporary URL

        generation_time = time.time() - start_time

        logger.info(
            f"Generated tailored resume PDF for tenant {ctx.tenant_id}, "
            f"job {request.job.get('id', 'unknown')}, "
            f"ATS score: {tailoring_result.ats_optimization_score:.2f}"
        )

        return GenerateResumePDFResponse(
            resume_id=resume_id,
            pdf_url=f"/resume-pdf/download/{resume_id}",
            ats_score=tailoring_result.ats_optimization_score,
            file_size=len(pdf_bytes),
            template_used=request.template_style,
            generation_time=generation_time,
        )

    except Exception as e:
        logger.error(f"Resume PDF generation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate resume PDF. Please try again."
        )


@router.get("/download/{resume_id}")
async def download_resume_pdf(
    resume_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> StreamingResponse:
    """Download a generated resume PDF.

    Args:
        resume_id: Resume ID from generation
        ctx: Tenant context for authorization

    Returns:
        PDF file stream
    """
    try:
        # TODO: Retrieve stored PDF from storage
        # For now, we'll return a placeholder

        # In production, this would:
        # 1. Verify user owns this resume
        # 2. Retrieve PDF from storage
        # 3. Return as streaming response

        raise HTTPException(status_code=404, detail="Resume PDF not found or expired")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume PDF download failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to download resume PDF")


@router.get("/templates", response_model=List[ResumeTemplate])
async def get_resume_templates(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> List[ResumeTemplate]:
    """Get available resume templates.

    Returns:
        List of available resume templates
    """
    templates = [
        ResumeTemplate(
            id="professional",
            name="Professional",
            description="Clean, traditional format suitable for most industries",
            category="professional",
            ats_optimized=True,
        ),
        ResumeTemplate(
            id="modern",
            name="Modern",
            description="Contemporary design with subtle visual elements",
            category="modern",
            ats_optimized=True,
        ),
        ResumeTemplate(
            id="executive",
            name="Executive",
            description="Sophisticated format for senior-level positions",
            category="executive",
            ats_optimized=True,
        ),
        ResumeTemplate(
            id="technical",
            name="Technical",
            description="Format optimized for technical and engineering roles",
            category="technical",
            ats_optimized=True,
        ),
        ResumeTemplate(
            id="creative",
            name="Creative",
            description="Stylish format for creative and design roles",
            category="creative",
            ats_optimized=False,  # Creative templates may not be ATS-optimized
        ),
    ]

    return templates


@router.post("/ats-report", response_model=ATSComplianceReport)
async def generate_ats_compliance_report(
    profile: Dict[str, Any],
    job: Dict[str, Any],
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> ATSComplianceReport:
    """Generate ATS compliance report for resume.

    Args:
        profile: User profile data
        job: Job posting data
        ctx: Tenant context for identification

    Returns:
        ATS compliance report
    """
    try:
        # Tailor the resume
        tailoring_service = get_tailoring_service()
        tailoring_result = await tailoring_service.tailor_resume(
            profile=profile,
            job=job,
        )

        # Generate compliance report
        pdf_generator = get_pdf_generator()
        compliance_report = pdf_generator.generate_ats_compliance_report(
            profile=profile,
            job=job,
            tailoring_result=tailoring_result,
        )

        logger.info(
            f"Generated ATS compliance report for tenant {ctx.tenant_id}, "
            f"job {job.get('id', 'unknown')}, "
            f"score: {compliance_report['ats_score']:.2f}"
        )

        return ATSComplianceReport(**compliance_report)

    except Exception as e:
        logger.error(f"ATS compliance report generation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate ATS compliance report"
        )


@router.post("/preview")
async def preview_tailored_resume(
    profile: Dict[str, Any],
    job: Dict[str, Any],
    template_style: str = "professional",
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Generate a preview of the tailored resume (without full PDF generation).

    Args:
        profile: User profile data
        job: Job posting data
        template_style: Template style to use
        ctx: Tenant context for identification

    Returns:
        Resume preview data
    """
    try:
        # Tailor the resume content
        tailoring_service = get_tailoring_service()
        tailoring_result = await tailoring_service.tailor_resume(
            profile=profile,
            job=job,
        )

        # Generate preview data (not full PDF)
        preview_data = {
            "header": {
                "name": profile.get("name", "YOUR NAME"),
                "contact": {
                    "email": profile.get("email"),
                    "phone": profile.get("phone"),
                    "location": profile.get("location"),
                    "linkedin": profile.get("linkedin"),
                    "github": profile.get("github"),
                },
            },
            "summary": tailoring_result.tailored_summary,
            "skills": {
                "highlighted": tailoring_result.highlighted_skills,
                "technical": profile.get("skills", {}).get("technical", []),
                "soft": profile.get("skills", {}).get("soft", []),
            },
            "experience": tailoring_result.emphasized_experiences[:3],
            "education": profile.get("education", [])[:2],
            "certifications": profile.get("certifications", [])[:3],
            "keywords": tailoring_result.added_keywords,
            "ats_score": tailoring_result.ats_optimization_score,
            "template_style": template_style,
        }

        return preview_data

    except Exception as e:
        logger.error(f"Resume preview generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate resume preview")


@router.get("/stats")
async def get_resume_pdf_stats(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get resume PDF generation statistics.

    Args:
        ctx: Tenant context for identification

    Returns:
        Generation statistics
    """
    # TODO: Implement statistics tracking
    # For now, return placeholder data

    return {
        "total_generated": 0,
        "average_ats_score": 0.0,
        "popular_templates": {
            "professional": 0,
            "modern": 0,
            "executive": 0,
            "technical": 0,
            "creative": 0,
        },
        "generation_time_avg": 0.0,
        "success_rate": 1.0,
    }
