"""LLM-Enhanced Career Path API endpoints.

Provides AI-powered career path analysis with endpoints for:
- Dynamic role generation using LLM
- Personalized career path analysis
- AI-powered skill gap identification
- Market-aware career recommendations
- Personalized learning path generation
- Industry trend integration

Key endpoints:
- POST /llm-career-path/generate-roles - Generate dynamic career roles
- POST /llm-career-path/analyze-path - Analyze personalized career path
- POST /llm-career-path/skill-gaps - Identify AI skill gaps
- POST /llm-career-path/recommendations - Get market-aware recommendations
- POST /llm-career-path/learning-path - Create personalized learning path
- GET /llm-career-path/market-trends - Get market trends
- GET /llm-career-path/emerging-skills - Get emerging skills
"""

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from packages.backend.domain.llm_career_path import get_llm_career_path_analyzer
from packages.backend.domain.tenant import TenantContext
from shared.ai_validation import sanitize_dict_for_ai, sanitize_for_ai
from shared.logging_config import get_logger

logger = get_logger("sorce.llm_career_path")

router = APIRouter(tags=["llm_career_path"])

_LLM_CAREER_PATH_RATE: Dict[str, List[float]] = defaultdict(list)
_LLM_CAREER_PATH_MAX_PER_HOUR = 15


def _check_llm_career_path_rate_limit(user_id: str) -> bool:
    now = time.time()
    key = f"llm_career_path:{user_id}"
    window = 3600
    _LLM_CAREER_PATH_RATE[key] = [t for t in _LLM_CAREER_PATH_RATE[key] if now - t < window]
    if len(_LLM_CAREER_PATH_RATE[key]) >= _LLM_CAREER_PATH_MAX_PER_HOUR:
        return False
    _LLM_CAREER_PATH_RATE[key].append(now)
    return True


def _sanitize_str(val: str, max_len: int = 200) -> str:
    r = sanitize_for_ai(str(val)[:max_len], max_length=max_len, min_length=None)
    return r.sanitized_input or str(val)[:max_len] if r.is_valid else str(val)[:max_len]


def _sanitize_str_list(vals: List[str], max_items: int = 20, max_item_len: int = 100) -> List[str]:
    out = []
    for v in (vals or [])[:max_items]:
        if isinstance(v, str) and v.strip():
            r = sanitize_for_ai(v[:max_item_len], max_length=max_item_len, min_length=None)
            if r.is_valid and r.sanitized_input:
                out.append(r.sanitized_input)
    return out


def _sanitize_dict(d: Optional[Dict[str, Any]], max_size: int = 5000) -> Optional[Dict[str, Any]]:
    if not d or not isinstance(d, dict):
        return d
    r = sanitize_dict_for_ai(d, max_size=max_size)
    return r.sanitized_input if r.is_valid else {}


class GenerateRolesRequest(BaseModel):
    """Request for dynamic role generation."""

    industry: str = Field(..., description="Industry focus")
    experience_level: str = Field(..., description="Experience level")
    skills: List[str] = Field(..., description="Current skills")
    preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="User preferences"
    )


class GenerateRolesResponse(BaseModel):
    """Response for dynamic role generation."""

    roles: List[Dict[str, Any]] = Field(..., description="Generated career roles")
    market_trends: List[Dict[str, Any]] = Field(
        ..., description="Relevant market trends"
    )
    generation_confidence: float = Field(..., description="Generation confidence score")
    total_roles: int = Field(..., description="Total roles generated")


class AnalyzePathRequest(BaseModel):
    """Request for personalized career path analysis."""

    user_profile: Dict[str, Any] = Field(..., description="User profile data")
    current_role: str = Field(..., description="Current role")
    target_role: str = Field(..., description="Target role")
    preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="User preferences"
    )


class AnalyzePathResponse(BaseModel):
    """Response for personalized career path analysis."""

    career_path: Dict[str, Any] = Field(..., description="Personalized career path")
    market_alignment: float = Field(..., description="Market alignment score")
    success_probability: float = Field(..., description="Success probability")
    key_insights: List[str] = Field(..., description="Key insights")
    next_steps: List[str] = Field(..., description="Recommended next steps")


class SkillGapsRequest(BaseModel):
    """Request for AI skill gap analysis."""

    current_role: str = Field(..., description="Current role")
    target_role: str = Field(..., description="Target role")
    current_skills: List[str] = Field(..., description="Current skills")
    industry: Optional[str] = Field(default=None, description="Industry context")


class SkillGapsResponse(BaseModel):
    """Response for AI skill gap analysis."""

    skill_gaps: List[Dict[str, Any]] = Field(..., description="Identified skill gaps")
    priority_gaps: List[Dict[str, Any]] = Field(..., description="Priority skill gaps")
    total_gaps: int = Field(..., description="Total skill gaps")
    estimated_timeline_weeks: int = Field(..., description="Estimated timeline")
    learning_recommendations: List[str] = Field(
        ..., description="Learning recommendations"
    )


class RecommendationsRequest(BaseModel):
    """Request for market-aware recommendations."""

    user_profile: Dict[str, Any] = Field(..., description="User profile data")
    career_goals: List[str] = Field(..., description="Career goals")
    constraints: Optional[Dict[str, Any]] = Field(
        default=None, description="Constraints"
    )


class RecommendationsResponse(BaseModel):
    """Response for market-aware recommendations."""

    recommendations: List[Dict[str, Any]] = Field(
        ..., description="Career recommendations"
    )
    market_insights: List[str] = Field(..., description="Market insights")
    opportunity_score: float = Field(..., description="Overall opportunity score")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment")


class LearningPathRequest(BaseModel):
    """Request for personalized learning path."""

    skill_gaps: List[Dict[str, Any]] = Field(..., description="Skill gaps to address")
    learning_style: Optional[str] = Field(default=None, description="Learning style")
    time_commitment: Optional[str] = Field(default=None, description="Time commitment")
    budget: Optional[int] = Field(default=None, description="Learning budget")


class LearningPathResponse(BaseModel):
    """Response for personalized learning path."""

    learning_path: Dict[str, Any] = Field(..., description="Personalized learning path")
    total_timeline_weeks: int = Field(..., description="Total timeline")
    estimated_cost: int = Field(..., description="Estimated cost")
    success_metrics: List[str] = Field(..., description="Success metrics")
    milestones: List[Dict[str, Any]] = Field(..., description="Learning milestones")


class MarketTrendsResponse(BaseModel):
    """Response for market trends."""

    trends: List[Dict[str, Any]] = Field(..., description="Market trends")
    industry_focus: List[str] = Field(..., description="Industry focus areas")
    growth_areas: List[str] = Field(..., description="High-growth areas")
    declining_areas: List[str] = Field(..., description="Declining areas")


class EmergingSkillsResponse(BaseModel):
    """Response for emerging skills."""

    skills: List[Dict[str, Any]] = Field(..., description="Emerging skills")
    skill_categories: Dict[str, List[str]] = Field(..., description="Skill categories")
    demand_scores: Dict[str, float] = Field(..., description="Demand scores")
    learning_timelines: Dict[str, int] = Field(..., description="Learning timelines")


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


@router.post("/generate-roles", response_model=GenerateRolesResponse)
async def generate_dynamic_roles(
    request: GenerateRolesRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> GenerateRolesResponse:
    """Generate dynamic career roles using LLM and market data.

    Args:
        request: Dynamic role generation request
        ctx: Tenant context for identification

    Returns:
        Generated career roles with market insights
    """
    if not _check_llm_career_path_rate_limit(ctx.user_id):
        raise HTTPException(429, "Rate limit exceeded. Try again later.")
    industry = _sanitize_str(request.industry)
    experience_level = _sanitize_str(request.experience_level)
    skills = _sanitize_str_list(request.skills)
    preferences = _sanitize_dict(request.preferences)
    try:
        llm_analyzer = get_llm_career_path_analyzer()

        # Generate dynamic roles
        roles = await llm_analyzer.generate_dynamic_career_roles(
            industry=industry,
            experience_level=experience_level,
            skills=skills,
            preferences=preferences,
        )

        # Get relevant market trends
        market_trends = llm_analyzer._get_relevant_trends(industry)

        # Calculate generation confidence
        confidence = 0.8 if len(roles) >= 3 else 0.6 if len(roles) >= 1 else 0.3

        return GenerateRolesResponse(
            roles=[role.model_dump() for role in roles],
            market_trends=[trend.model_dump() for trend in market_trends],
            generation_confidence=confidence,
            total_roles=len(roles),
        )

    except Exception as e:
        logger.error(f"Failed to generate dynamic roles: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate dynamic career roles"
        )


@router.post("/analyze-path", response_model=AnalyzePathResponse)
async def analyze_personalized_career_path(
    request: AnalyzePathRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> AnalyzePathResponse:
    """Analyze personalized career path using AI.

    Args:
        request: Personalized career path analysis request
        ctx: Tenant context for identification

    Returns:
        Personalized career path with AI insights
    """
    if not _check_llm_career_path_rate_limit(ctx.user_id):
        raise HTTPException(429, "Rate limit exceeded. Try again later.")
    user_profile = _sanitize_dict(request.user_profile, max_size=10000)
    current_role = _sanitize_str(request.current_role)
    target_role = _sanitize_str(request.target_role)
    preferences = _sanitize_dict(request.preferences)
    try:
        llm_analyzer = get_llm_career_path_analyzer()

        # Analyze personalized career path
        career_path = await llm_analyzer.analyze_personalized_career_path(
            user_profile=user_profile or {},
            current_role=current_role,
            target_role=target_role,
            preferences=preferences,
        )

        # Generate key insights
        key_insights = [
            f"Market alignment score: {career_path.market_alignment_score:.2f}",
            f"Estimated timeline: {career_path.estimated_timeline_months} months",
            f"Salary increase potential: {career_path.potential_salary_increase_pct:.1%}",
            f"AI confidence: {career_path.ai_confidence:.2f}",
        ]

        # Generate next steps
        next_steps = []
        for step in career_path.steps[:3]:
            if isinstance(step, dict) and "description" in step:
                next_steps.append(step["description"])

        # Calculate success probability
        success_probability = (
            career_path.market_alignment_score * 0.6 + career_path.ai_confidence * 0.4
        )

        return AnalyzePathResponse(
            career_path=career_path.model_dump(),
            market_alignment=career_path.market_alignment_score,
            success_probability=success_probability,
            key_insights=key_insights,
            next_steps=next_steps,
        )

    except Exception as e:
        logger.error(f"Failed to analyze personalized career path: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to analyze personalized career path"
        )


@router.post("/skill-gaps", response_model=SkillGapsResponse)
async def identify_ai_skill_gaps(
    request: SkillGapsRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> SkillGapsResponse:
    """Identify skill gaps using AI analysis.

    Args:
        request: Skill gap analysis request
        ctx: Tenant context for identification

    Returns:
        AI-identified skill gaps with recommendations
    """
    if not _check_llm_career_path_rate_limit(ctx.user_id):
        raise HTTPException(429, "Rate limit exceeded. Try again later.")
    current_role = _sanitize_str(request.current_role)
    target_role = _sanitize_str(request.target_role)
    current_skills = _sanitize_str_list(request.current_skills)
    industry = _sanitize_str(request.industry) if request.industry else None
    try:
        llm_analyzer = get_llm_career_path_analyzer()

        # Identify AI skill gaps
        skill_gaps = await llm_analyzer.identify_ai_skill_gaps(
            current_role=current_role,
            target_role=target_role,
            current_skills=current_skills,
            industry=industry,
        )

        # Sort by importance
        priority_gaps = sorted(
            skill_gaps,
            key=lambda gap: (
                1.0
                if gap.importance == "critical"
                else 0.6
                if gap.importance == "important"
                else 0.3
            ),
            reverse=True,
        )

        # Calculate total timeline
        total_timeline = sum(gap.estimated_time_weeks for gap in skill_gaps)

        # Generate learning recommendations
        learning_recommendations = [
            f"Focus on {gap.skill} - estimated {gap.estimated_time_weeks} weeks"
            for gap in priority_gaps[:3]
        ]

        return SkillGapsResponse(
            skill_gaps=[gap.model_dump() for gap in skill_gaps],
            priority_gaps=[gap.model_dump() for gap in priority_gaps],
            total_gaps=len(skill_gaps),
            estimated_timeline_weeks=total_timeline,
            learning_recommendations=learning_recommendations,
        )

    except Exception as e:
        logger.error(f"Failed to identify AI skill gaps: {e}")
        raise HTTPException(status_code=500, detail="Failed to identify AI skill gaps")


@router.post("/recommendations", response_model=RecommendationsResponse)
async def generate_market_aware_recommendations(
    request: RecommendationsRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> RecommendationsResponse:
    """Generate market-aware career recommendations.

    Args:
        request: Market-aware recommendations request
        ctx: Tenant context for identification

    Returns:
        Market-aware career recommendations
    """
    if not _check_llm_career_path_rate_limit(ctx.user_id):
        raise HTTPException(429, "Rate limit exceeded. Try again later.")
    user_profile = _sanitize_dict(request.user_profile, max_size=10000)
    career_goals = _sanitize_str_list(request.career_goals, max_items=10)
    constraints = _sanitize_dict(request.constraints)
    try:
        llm_analyzer = get_llm_career_path_analyzer()

        # Generate market-aware recommendations
        recommendations = await llm_analyzer.generate_market_aware_recommendations(
            user_profile=user_profile or {},
            career_goals=career_goals,
            constraints=constraints,
        )

        # Calculate opportunity score
        opportunity_score = 0.0
        if recommendations:
            opportunity_score = sum(
                rec.get("alignment_with_goals", 0.5) * rec.get("market_demand", 0.5)
                for rec in recommendations
            ) / len(recommendations)

        # Generate market insights
        market_insights = [
            f"Generated {len(recommendations)} personalized recommendations",
            f"Average market demand: {opportunity_score:.2f}",
            f"Based on {len(career_goals)} career goals",
        ]

        # Risk assessment
        risk_assessment = {
            "overall_risk": "medium",
            "market_volatility": "low",
            "skill_obsolescence": "medium",
            "competition_level": "high",
        }

        return RecommendationsResponse(
            recommendations=recommendations,
            market_insights=market_insights,
            opportunity_score=opportunity_score,
            risk_assessment=risk_assessment,
        )

    except Exception as e:
        logger.error(f"Failed to generate market-aware recommendations: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate market-aware recommendations"
        )


@router.post("/learning-path", response_model=LearningPathResponse)
async def create_personalized_learning_path(
    request: LearningPathRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> LearningPathResponse:
    """Create personalized learning path using AI.

    Args:
        request: Learning path generation request
        ctx: Tenant context for identification

    Returns:
        Personalized learning path
    """
    if not _check_llm_career_path_rate_limit(ctx.user_id):
        raise HTTPException(429, "Rate limit exceeded. Try again later.")
    # Sanitize skill_gaps list - each gap is a dict with skill, etc.
    sanitized_gaps = []
    for g in (request.skill_gaps or [])[:15]:
        if isinstance(g, dict):
            skill = _sanitize_str(g.get("skill", ""), max_len=100)
            sanitized_gaps.append(
                {
                    **g,
                    "skill": skill,
                    "importance": _sanitize_str(str(g.get("importance", "medium"))[:50]),
                    "acquisition_method": _sanitize_str(str(g.get("acquisition_method", "self_study"))[:50]),
                    "estimated_time_weeks": min(max(int(g.get("estimated_time_weeks", 4)), 1), 104),
                    "resources": _sanitize_str_list(g.get("resources", []), max_items=5),
                }
            )
    learning_style = _sanitize_str(request.learning_style or "") if request.learning_style else None
    time_commitment = _sanitize_str(request.time_commitment or "") if request.time_commitment else None
    budget = request.budget
    if budget is not None and (not isinstance(budget, int) or budget < 0 or budget > 100000):
        budget = None
    try:
        llm_analyzer = get_llm_career_path_analyzer()

        # Convert skill gaps to proper format
        from packages.backend.domain.career_path import SkillGap

        skill_gaps = [
            SkillGap(
                skill=gap.get("skill", ""),
                importance=gap.get("importance", "medium"),
                acquisition_method=gap.get("acquisition_method", "self_study"),
                estimated_time_weeks=gap.get("estimated_time_weeks", 4),
                resources=gap.get("resources", []),
            )
            for gap in sanitized_gaps
        ]

        # Create personalized learning path
        learning_path = await llm_analyzer.create_personalized_learning_path(
            skill_gaps=skill_gaps,
            learning_style=learning_style,
            time_commitment=time_commitment,
            budget=budget,
        )

        # Extract key information
        total_timeline = learning_path.get("total_timeline_weeks", 0)
        estimated_cost = budget or 0

        # Generate success metrics
        success_metrics = [
            "Complete all skill gap requirements",
            "Achieve target role qualifications",
            "Demonstrate practical application",
            "Maintain learning consistency",
        ]

        # Generate milestones
        milestones = learning_path.get("phases", [])

        return LearningPathResponse(
            learning_path=learning_path,
            total_timeline_weeks=total_timeline,
            estimated_cost=estimated_cost,
            success_metrics=success_metrics,
            milestones=milestones,
        )

    except Exception as e:
        logger.error(f"Failed to create personalized learning path: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create personalized learning path"
        )


@router.get("/market-trends", response_model=MarketTrendsResponse)
async def get_market_trends(
    industry: Optional[str] = None,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> MarketTrendsResponse:
    """Get market trends for career planning.

    Args:
        industry: Optional industry filter
        ctx: Tenant context for identification

    Returns:
        Market trends data
    """
    try:
        llm_analyzer = get_llm_career_path_analyzer()

        # Get market trends
        trends = llm_analyzer._market_trends

        # Filter by industry if specified (sanitize to prevent injection)
        if industry:
            sanitized_industry = _sanitize_str(industry)
            relevant_trends = llm_analyzer._get_relevant_trends(sanitized_industry)
        else:
            relevant_trends = trends

        # Extract industry focus areas
        industry_focus = list(
            set([focus for trend in relevant_trends for focus in trend.affected_roles])
        )[:10]

        # Identify growth and declining areas
        growth_areas = [
            trend.trend_name
            for trend in relevant_trends
            if trend.trend_type == "growth"
        ]

        declining_areas = [
            trend.trend_name
            for trend in relevant_trends
            if trend.trend_type == "decline"
        ]

        return MarketTrendsResponse(
            trends=[trend.model_dump() for trend in relevant_trends],
            industry_focus=industry_focus,
            growth_areas=growth_areas,
            declining_areas=declining_areas,
        )

    except Exception as e:
        logger.error(f"Failed to get market trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve market trends")


@router.get("/emerging-skills", response_model=EmergingSkillsResponse)
async def get_emerging_skills(
    industry: Optional[str] = None,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> EmergingSkillsResponse:
    """Get emerging skills for career planning.

    Args:
        industry: Optional industry filter
        ctx: Tenant context for identification

    Returns:
        Emerging skills data
    """
    try:
        llm_analyzer = get_llm_career_path_analyzer()

        # Get emerging skills
        emerging_skills_data = llm_analyzer._emerging_skills

        # Filter by industry if specified (sanitize to prevent injection)
        if industry:
            sanitized_industry = _sanitize_str(industry)
            relevant_skills = llm_analyzer._get_relevant_emerging_skills(sanitized_industry)
        else:
            relevant_skills = []
            for skill_data in emerging_skills_data:
                relevant_skills.extend(skill_data.get("skills", []))

        # Remove duplicates and limit
        unique_skills = list(set(relevant_skills))[:20]

        # Create skill categories
        skill_categories = {
            "technical": [],
            "business": [],
            "soft_skills": [],
            "emerging_tech": [],
        }

        # Categorize skills (simplified categorization)
        for skill in unique_skills:
            if any(
                tech in skill.lower()
                for tech in ["programming", "coding", "development", "engineering"]
            ):
                skill_categories["technical"].append(skill)
            elif any(
                biz in skill.lower()
                for biz in ["management", "strategy", "business", "marketing"]
            ):
                skill_categories["business"].append(skill)
            elif any(
                soft in skill.lower()
                for soft in ["communication", "leadership", "collaboration", "teamwork"]
            ):
                skill_categories["soft_skills"].append(skill)
            else:
                skill_categories["emerging_tech"].append(skill)

        # Calculate demand scores
        demand_scores = {}
        for skill_data in emerging_skills_data:
            for skill in skill_data.get("skills", []):
                if skill in unique_skills:
                    demand_scores[skill] = skill_data.get("growth_rate", 0.1)

        # Calculate learning timelines
        learning_timelines = {}
        for skill_data in emerging_skills_data:
            for skill in skill_data.get("skills", []):
                if skill in unique_skills:
                    learning_timelines[skill] = skill_data.get("timeline_months", 6)

        return EmergingSkillsResponse(
            skills=[
                {
                    "skill": skill,
                    "demand_score": demand_scores.get(skill, 0.1),
                    "timeline_months": learning_timelines.get(skill, 6),
                }
                for skill in unique_skills
            ],
            skill_categories=skill_categories,
            demand_scores=demand_scores,
            learning_timelines=learning_timelines,
        )

    except Exception as e:
        logger.error(f"Failed to get emerging skills: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve emerging skills"
        )


@router.get("/industry-patterns")
async def get_industry_patterns(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get industry-specific patterns for career planning.

    Args:
        ctx: Tenant context for identification

    Returns:
        Industry-specific patterns
    """
    try:
        llm_analyzer = get_llm_career_path_analyzer()

        return {
            "industries": list(llm_analyzer._industry_patterns.keys()),
            "patterns": llm_analyzer._industry_patterns,
            "available_analyses": [
                "growth_rate",
                "emerging_areas",
                "declining_areas",
                "key_skills",
            ],
        }

    except Exception as e:
        logger.error(f"Failed to get industry patterns: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve industry patterns"
        )


@router.get("/health")
async def health_check(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Health check for LLM career path analyzer."""

    return {
        "status": "healthy",
        "llm_integration": "operational",
        "market_data": "available",
        "ai_capabilities": {
            "role_generation": True,
            "path_analysis": True,
            "skill_gap_analysis": True,
            "recommendations": True,
            "learning_paths": True,
        },
        "data_sources": {
            "market_trends": "available",
            "emerging_skills": "available",
            "industry_patterns": "available",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
