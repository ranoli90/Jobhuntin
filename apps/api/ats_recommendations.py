"""ATS Recommendations API endpoints.

Provides job-specific ATS optimization recommendations with endpoints for:
- Job analysis and ATS scoring
- Industry-specific recommendations
- Format compliance checking
- Content optimization suggestions
- Success probability prediction
- Implementation time estimation

Key endpoints:
- POST /ats-recommendations/analyze - Analyze job for ATS optimization
- GET /ats-recommendations/industry-rules/{industry} - Get industry-specific rules
- POST /ats-recommendations/keywords - Analyze keyword coverage
- GET /ats-recommendations/templates - Get ATS-optimized templates
- GET /ats-recommendations/stats - Get ATS recommendations statistics
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from packages.backend.domain.ats_recommendations import get_ats_recommendations_engine
from packages.backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.ats_recommendations")

router = APIRouter(tags=["ats_recommendations"])


class ATSAnalysisRequest(BaseModel):
    """Request for ATS analysis."""

    job: Dict[str, Any] = Field(..., description="Job posting data")
    profile: Dict[str, Any] = Field(..., description="User profile data")
    current_resume_text: Optional[str] = Field(
        default=None, description="Current resume text for analysis"
    )


class ATSAnalysisResponse(BaseModel):
    """Response for ATS analysis."""

    job_id: str = Field(..., description="Job identifier")
    job_title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry")
    ats_score_current: float = Field(..., description="Current ATS score (0.0-1.0)")
    ats_score_potential: float = Field(..., description="Potential ATS score (0.0-1.0)")
    improvement_potential: float = Field(
        ..., description="ATS score improvement potential"
    )
    recommendations: List[Dict[str, Any]] = Field(
        ..., description="ATS optimization recommendations"
    )
    keyword_analysis: Dict[str, Any] = Field(
        ..., description="Keyword analysis results"
    )
    format_compliance: Dict[str, Any] = Field(
        ..., description="Format compliance results"
    )
    content_optimization: Dict[str, Any] = Field(
        ..., description="Content optimization results"
    )
    success_probability: float = Field(..., description="Success probability (0.0-1.0)")
    estimated_processing_time: str = Field(..., description="Estimated processing time")
    industry_specific_rules: List[str] = Field(
        ..., description="Industry-specific ATS rules"
    )


class KeywordAnalysisRequest(BaseModel):
    """Request for keyword analysis."""

    job: Dict[str, Any] = Field(..., description="Job posting data")
    profile: Dict[str, Any] = Field(..., description="User profile data")


class KeywordAnalysisResponse(BaseModel):
    """Response for keyword analysis."""

    job_keywords: List[str] = Field(..., description="Keywords extracted from job")
    required_keywords: List[str] = Field(..., description="Required keywords from job")
    industry_keywords: List[str] = Field(..., description="Industry-specific keywords")
    profile_keywords: List[str] = Field(..., description="Keywords from profile")
    keyword_coverage: Dict[str, Any] = Field(
        ..., description="Keyword coverage analysis"
    )
    missing_keywords: List[str] = Field(..., description="Missing keywords")
    priority_keywords: List[str] = Field(..., description="Priority keywords")
    keyword_density: Dict[str, float] = Field(
        ..., description="Keyword density analysis"
    )


class FormatComplianceRequest(BaseModel):
    """Request for format compliance check."""

    resume_text: str = Field(..., description="Resume text to analyze")
    job: Optional[Dict[str, Any]] = Field(default=None, description="Job for context")


class FormatComplianceResponse(BaseModel):
    """Response for format compliance check."""

    compliant: bool = Field(..., description="Overall compliance status")
    score: float = Field(..., description="Compliance score (0.0-1.0)")
    issues: List[str] = Field(..., description="Compliance issues")
    checks: Dict[str, Any] = Field(..., description="Detailed compliance checks")


class IndustryRulesResponse(BaseModel):
    """Response for industry-specific rules."""

    industry: str = Field(..., description="Industry name")
    rules: List[Dict[str, Any]] = Field(..., description="Industry-specific ATS rules")
    common_keywords: List[str] = Field(..., description="Common industry keywords")
    formatting_guidelines: List[str] = Field(
        ..., description="Industry formatting guidelines"
    )
    success_factors: List[str] = Field(..., description="Industry success factors")


class ATSTemplatesResponse(BaseModel):
    """Response for ATS-optimized templates."""

    templates: List[Dict[str, Any]] = Field(..., description="ATS-optimized templates")
    template_categories: List[str] = Field(
        ..., description="Available template categories"
    )
    industry_templates: Dict[str, List[str]] = Field(
        ..., description="Industry-specific templates"
    )
    customization_tips: List[str] = Field(
        ..., description="Template customization tips"
    )


class ATSStatsResponse(BaseModel):
    """Response for ATS recommendations statistics."""

    total_analyses: int = Field(..., description="Total ATS analyses performed")
    average_ats_score: float = Field(..., description="Average ATS score")
    average_improvement: float = Field(..., description="Average improvement potential")
    industry_performance: Dict[str, float] = Field(
        ..., description="Performance by industry"
    )
    common_issues: List[Dict[str, Any]] = Field(..., description="Common ATS issues")
    success_rates: Dict[str, float] = Field(
        ..., description="Success rates by category"
    )


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


@router.post("/analyze", response_model=ATSAnalysisResponse)
async def analyze_job_for_ats(
    request: ATSAnalysisRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> ATSAnalysisResponse:
    """Analyze job and provide ATS-specific recommendations.

    This endpoint:
    1. Analyzes job requirements and keywords
    2. Checks ATS format compliance
    3. Evaluates content optimization
    4. Generates job-specific recommendations
    5. Calculates ATS scores and success probability
    6. Provides implementation time estimates

    Args:
        request: ATS analysis request
        ctx: Tenant context for identification

    Returns:
        Comprehensive ATS analysis and recommendations
    """
    try:
        ats_engine = get_ats_recommendations_engine()

        analysis_result = await ats_engine.analyze_job_for_ats(
            job=request.job,
            profile=request.profile,
            current_resume_text=request.current_resume_text,
        )

        return ATSAnalysisResponse(**analysis_result.to_dict())

    except Exception as e:
        logger.error(f"ATS analysis failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to analyze job for ATS optimization"
        )


@router.post("/keywords", response_model=KeywordAnalysisResponse)
async def analyze_keywords(
    request: KeywordAnalysisRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> KeywordAnalysisResponse:
    """Analyze keyword coverage between job and profile.

    Args:
        request: Keyword analysis request
        ctx: Tenant context for identification

    Returns:
        Keyword analysis results
    """
    try:
        ats_engine = get_ats_recommendations_engine()

        keyword_analysis = await ats_engine._analyze_keywords(
            job=request.job,
            profile=request.profile,
        )

        return KeywordAnalysisResponse(**keyword_analysis)

    except Exception as e:
        logger.error(f"Keyword analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze keywords")


@router.post("/format-compliance", response_model=FormatComplianceResponse)
async def check_format_compliance(
    request: FormatComplianceRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> FormatComplianceResponse:
    """Check ATS format compliance for resume.

    Args:
        request: Format compliance request
        ctx: Tenant context for identification

    Returns:
        Format compliance results
    """
    try:
        ats_engine = get_ats_recommendations_engine()

        format_compliance = await ats_engine._check_format_compliance(
            job=request.job or {},
            resume_text=request.resume_text,
        )

        return FormatComplianceResponse(**format_compliance)

    except Exception as e:
        logger.error(f"Format compliance check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check format compliance")


@router.get("/industry-rules/{industry}", response_model=IndustryRulesResponse)
async def get_industry_rules(
    industry: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> IndustryRulesResponse:
    """Get industry-specific ATS rules and guidelines.

    Args:
        industry: Industry name
        ctx: Tenant context for identification

    Returns:
        Industry-specific ATS rules
    """
    try:
        ats_engine = get_ats_recommendations_engine()

        industry_rules = ats_engine._get_industry_specific_rules(industry)
        industry_keywords = ats_engine._industry_keywords.get(industry.lower(), [])

        # Generate formatting guidelines
        formatting_guidelines = []
        for rule in industry_rules:
            formatting_guidelines.extend(rule.get("action_items", []))

        # Generate success factors
        success_factors = []
        for rule in industry_rules:
            success_factors.append(rule.get("description", ""))

        return IndustryRulesResponse(
            industry=industry,
            rules=industry_rules,
            common_keywords=industry_keywords,
            formatting_guidelines=formatting_guidelines,
            success_factors=success_factors,
        )

    except Exception as e:
        logger.error(f"Failed to get industry rules for {industry}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve industry-specific rules"
        )


@router.get("/templates", response_model=ATSTemplatesResponse)
async def get_ats_templates(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    industry: Optional[str] = None,
) -> ATSTemplatesResponse:
    """Get ATS-optimized resume templates.

    Args:
        ctx: Tenant context for identification
        industry: Optional industry filter

    Returns:
        ATS-optimized templates
    """
    try:
        # TODO: Implement actual template retrieval
        # For now, return placeholder data

        templates = [
            {
                "id": "professional_ats",
                "name": "Professional ATS Optimized",
                "description": "Clean, ATS-friendly professional template",
                "category": "professional",
                "ats_score": 0.95,
                "features": [
                    "Standard formatting",
                    "Keyword optimization",
                    "Clean layout",
                    "ATS-friendly fonts",
                ],
                "industries": ["technology", "finance", "healthcare", "education"],
            },
            {
                "id": "technical_ats",
                "name": "Technical ATS Optimized",
                "description": "ATS template optimized for technical roles",
                "category": "technical",
                "ats_score": 0.93,
                "features": [
                    "Skills section prominence",
                    "Technical keyword optimization",
                    "Project-based layout",
                    "Certification highlighting",
                ],
                "industries": ["technology", "engineering", "software"],
            },
            {
                "id": "executive_ats",
                "name": "Executive ATS Optimized",
                "description": "ATS template for executive positions",
                "category": "executive",
                "ats_score": 0.94,
                "features": [
                    "Leadership emphasis",
                    "Achievement focus",
                    "Strategic layout",
                    "Executive summary",
                ],
                "industries": ["finance", "healthcare", "technology", "government"],
            },
        ]

        template_categories = [
            "professional",
            "technical",
            "executive",
            "creative",
            "entry",
        ]

        industry_templates = {
            "technology": ["professional_ats", "technical_ats"],
            "healthcare": ["professional_ats", "executive_ats"],
            "finance": ["professional_ats", "executive_ats"],
            "education": ["professional_ats"],
            "government": ["executive_ats", "professional_ats"],
        }

        customization_tips = [
            "Use keywords from job description",
            "Quantify achievements with numbers",
            "Use action verbs to start bullet points",
            "Keep formatting simple and clean",
            "Avoid tables, images, and graphics",
            "Use standard fonts (Arial, Times New Roman)",
            "Set margins to 0.5-1 inch",
            "Keep resume length to 1-2 pages",
        ]

        return ATSTemplatesResponse(
            templates=templates,
            template_categories=template_categories,
            industry_templates=industry_templates,
            customization_tips=customization_tips,
        )

    except Exception as e:
        logger.error(f"Failed to get ATS templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ATS templates")


@router.get("/stats", response_model=ATSStatsResponse)
async def get_ats_recommendations_stats(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    industry: Optional[str] = None,
    date_range: Optional[str] = None,
) -> ATSStatsResponse:
    """Get ATS recommendations statistics and analytics.

    Args:
        ctx: Tenant context for identification
        industry: Optional industry filter
        date_range: Optional date range filter

    Returns:
        ATS recommendations statistics
    """
    try:
        # TODO: Implement actual statistics query
        # For now, return placeholder data

        return ATSStatsResponse(
            total_analyses=0,
            average_ats_score=0.0,
            average_improvement=0.0,
            industry_performance={
                "technology": 0.0,
                "healthcare": 0.0,
                "finance": 0.0,
                "education": 0.0,
                "government": 0.0,
            },
            common_issues=[
                {
                    "category": "keywords",
                    "issue": "Missing job keywords",
                    "frequency": 0,
                    "impact": "high",
                },
                {
                    "category": "formatting",
                    "issue": "Non-ATS friendly formatting",
                    "frequency": 0,
                    "impact": "medium",
                },
                {
                    "category": "content",
                    "issue": "Lack of quantifiable achievements",
                    "frequency": 0,
                    "impact": "medium",
                },
            ],
            success_rates={
                "keywords": 0.0,
                "formatting": 0.0,
                "content": 0.0,
                "industry": 0.0,
                "overall": 0.0,
            },
        )

    except Exception as e:
        logger.error(f"Failed to get ATS recommendations stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve ATS recommendations statistics"
        )


@router.post("/content-optimization")
async def analyze_content_optimization(
    resume_text: str,
    job: Dict[str, Any],
    profile: Dict[str, Any],
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Analyze content optimization for ATS.

    Args:
        resume_text: Resume text to analyze
        job: Job posting data
        profile: User profile data
        ctx: Tenant context for identification

    Returns:
        Content optimization analysis
    """
    try:
        ats_engine = get_ats_recommendations_engine()

        content_optimization = await ats_engine._analyze_content_optimization(
            job=job,
            profile=profile,
            resume_text=resume_text,
        )

        return content_optimization

    except Exception as e:
        logger.error(f"Content optimization analysis failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to analyze content optimization"
        )


@router.post("/success-prediction")
async def predict_success_probability(
    current_ats_score: float,
    potential_ats_score: float,
    industry: str,
    job_title: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Predict success probability based on ATS scores and job factors.

    Args:
        current_ats_score: Current ATS score
        potential_ats_score: Potential ATS score
        industry: Industry name
        job_title: Job title
        ctx: Tenant context for identification

    Returns:
        Success probability prediction
    """
    try:
        ats_engine = get_ats_recommendations_engine()

        success_probability = ats_engine._predict_success_probability(
            current_score=current_ats_score,
            potential_score=potential_ats_score,
            industry=industry,
            job_title=job_title,
        )

        # Additional analysis
        improvement_factor = (potential_ats_score - current_ats_score) * 100

        return {
            "success_probability": success_probability,
            "current_ats_score": current_ats_score,
            "potential_ats_score": potential_ats_score,
            "improvement_factor": improvement_factor,
            "recommendation": "Implement ATS optimization recommendations"
            if improvement_factor > 10
            else "Current ATS score is good",
            "confidence_level": "high"
            if success_probability > 0.6
            else "medium"
            if success_probability > 0.4
            else "low",
        }

    except Exception as e:
        logger.error(f"Success prediction failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to predict success probability"
        )


@router.get("/industries")
async def get_supported_industries(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get list of supported industries for ATS recommendations.

    Args:
        ctx: Tenant context for identification

    Returns:
        Supported industries and their characteristics
    """
    try:
        ats_engine = get_ats_recommendations_engine()

        industries = list(ats_engine._industry_rules.keys())
        industry_keywords = ats_engine._industry_keywords

        industry_info = {}
        for industry in industries:
            industry_info[industry] = {
                "keywords_count": len(industry_keywords.get(industry, [])),
                "rules_count": len(ats_engine._industry_rules.get(industry, [])),
                "common_keywords": industry_keywords.get(industry, [])[
                    :5
                ],  # First 5 keywords
                "has_specific_rules": len(ats_engine._industry_rules.get(industry, []))
                > 0,
            }

        return {
            "supported_industries": industries,
            "industry_info": industry_info,
            "total_industries": len(industries),
            "most_common_keywords": {
                industry: keywords[:3]
                for industry, keywords in industry_keywords.items()
                if keywords
            },
        }

    except Exception as e:
        logger.error(f"Failed to get supported industries: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve supported industries"
        )


@router.post("/batch-analysis")
async def batch_analyze_jobs(
    jobs: List[Dict[str, Any]],
    profile: Dict[str, Any],
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> List[Dict[str, Any]]:
    """Analyze multiple jobs for ATS optimization in batch.

    Args:
        jobs: List of job postings to analyze
        profile: User profile data
        ctx: Tenant context for identification

    Returns:
        Batch ATS analysis results
    """
    try:
        ats_engine = get_ats_recommendations_engine()

        results = []
        for job in jobs:
            try:
                analysis_result = await ats_engine.analyze_job_for_ats(
                    job=job,
                    profile=profile,
                    current_resume_text=None,
                )
                results.append(analysis_result.to_dict())
            except Exception as e:
                logger.error(f"Failed to analyze job {job.get('id', 'unknown')}: {e}")
                results.append(
                    {
                        "job_id": job.get("id", ""),
                        "error": str(e),
                        "success": False,
                    }
                )

        return results

    except Exception as e:
        logger.error(f"Batch ATS analysis failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to perform batch ATS analysis"
        )
