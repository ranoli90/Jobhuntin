"""Skill Gap Analysis API endpoints.

This module provides endpoints for analyzing skill gaps between user skills
and job requirements, with personalized recommendations and learning resources.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from packages.backend.domain.skill_gap_analyzer import (
    SkillGapAnalyzer,
    get_skill_gap_analyzer,
)
from packages.backend.domain.skills_taxonomy import get_skills_taxonomy
from packages.backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.api.skill_gap")

router = APIRouter(tags=["skill-gap"])


# ---------------------------------------------------------------------------
# Dependency stubs — injected by api/main.py at mount time
# ---------------------------------------------------------------------------


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class SkillGapRequest(BaseModel):
    """Request model for skill gap analysis."""

    current_skills: List[str] = Field(
        ..., description="List of user's current skills"
    )
    target_role: str = Field(..., description="Target job role or position")
    user_proficiency_levels: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional mapping of skills to proficiency levels (beginner, intermediate, advanced, expert)",
    )


class SkillGapResponse(BaseModel):
    """Response model for skill gap analysis."""

    target_role: str = Field(..., description="Target job role")
    current_skills: List[str] = Field(..., description="Validated current skills")
    required_skills: List[str] = Field(..., description="Required skills for target role")
    matched_skills: List[str] = Field(..., description="Skills user already has")
    missing_skills: List[str] = Field(..., description="Skills user needs to learn")
    gap_score: float = Field(..., description="Gap score from 0.0 to 1.0 (1.0 = no gaps)")
    skill_gaps: List[Dict[str, Any]] = Field(
        ..., description="Detailed skill gap information"
    )
    category_breakdown: Dict[str, Dict[str, Any]] = Field(
        ..., description="Breakdown by skill category"
    )
    recommendations: List[Dict[str, Any]] = Field(
        ..., description="Prioritized learning recommendations"
    )
    market_insights: Dict[str, Any] = Field(
        ..., description="Market insights for the target role"
    )


class SkillRecommendationRequest(BaseModel):
    """Request model for skill recommendations."""

    current_skills: List[str] = Field(
        ..., description="List of user's current skills"
    )
    target_role: str = Field(..., description="Target job role or position")
    limit: int = Field(
        default=10, ge=1, le=30, description="Maximum number of recommendations"
    )


class SkillRecommendationResponse(BaseModel):
    """Response model for skill recommendations."""

    target_role: str = Field(..., description="Target job role")
    recommendations: List[Dict[str, Any]] = Field(
        ..., description="Prioritized skill recommendations with resources"
    )
    total_missing: int = Field(..., description="Total number of missing skills")
    estimated_total_learning_weeks: float = Field(
        ..., description="Estimated total weeks to learn all recommended skills"
    )


class TargetRolesResponse(BaseModel):
    """Response model for available target roles."""

    roles: List[Dict[str, Any]] = Field(
        ..., description="List of available target roles with metadata"
    )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=SkillGapResponse)
async def analyze_skill_gap(
    request: SkillGapRequest,
    analyzer: SkillGapAnalyzer = Depends(get_skill_gap_analyzer),
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> SkillGapResponse:
    """Analyze skill gaps between user skills and target role requirements.

    This endpoint compares the user's current skills against the requirements
    for their target job role and provides a comprehensive gap analysis including:
    - Matched and missing skills
    - Gap score (0.0 to 1.0)
    - Detailed skill gap information with priorities
    - Category breakdown
    - Learning recommendations
    - Market insights

    Args:
        request: Skill gap analysis request with current skills and target role
        analyzer: Skill gap analyzer instance
        ctx: Tenant context for user identification

    Returns:
        Complete skill gap analysis with recommendations
    """
    try:
        logger.info(
            f"[SKILL_GAP] Analyzing skill gap for user {ctx.user_id}, "
            f"target role: '{request.target_role}', "
            f"current skills: {len(request.current_skills)}"
        )

        # Validate current skills against taxonomy
        taxonomy = get_skills_taxonomy()
        valid_skills, invalid_skills, _ = taxonomy.validate_user_skills(request.current_skills)

        if invalid_skills:
            logger.info(
                f"[SKILL_GAP] Invalid skills provided: {invalid_skills}"
            )

        # Run the analysis
        analysis = analyzer.analyze(
            current_skills=valid_skills,
            target_role=request.target_role,
            user_proficiency_levels=request.user_proficiency_levels,
        )

        # Convert skill gaps to dict format for JSON response
        skill_gaps_dict = []
        for gap in analysis.skill_gaps:
            skill_gaps_dict.append({
                "skill_name": gap.skill_name,
                "category": gap.category,
                "skill_type": gap.skill_type.value,
                "demand_score": gap.demand_score,
                "priority": gap.priority,
                "missing": gap.missing,
                "proficiency_gap": gap.proficiency_gap,
                "estimated_learning_weeks": gap.estimated_learning_weeks,
                "related_skills": gap.related_skills,
                "description": gap.description,
                "resources": gap.resources,
            })

        logger.info(
            f"[SKILL_GAP] Analysis complete for user {ctx.user_id}: "
            f"{len(analysis.matched_skills)}/{len(analysis.required_skills)} "
            f"skills matched, gap score: {analysis.gap_score:.2f}"
        )

        return SkillGapResponse(
            target_role=analysis.target_role,
            current_skills=analysis.current_skills,
            required_skills=analysis.required_skills,
            matched_skills=analysis.matched_skills,
            missing_skills=analysis.missing_skills,
            gap_score=analysis.gap_score,
            skill_gaps=skill_gaps_dict,
            category_breakdown=analysis.category_breakdown,
            recommendations=analysis.recommendations,
            market_insights=analysis.market_insights,
        )

    except Exception as e:
        logger.error(f"Skill gap analysis failed: {e}")
        raise HTTPException(
            status_code=500, detail="Skill gap analysis failed. Please try again."
        )


@router.post("/recommendations", response_model=SkillRecommendationResponse)
async def get_skill_recommendations(
    request: SkillRecommendationRequest,
    analyzer: SkillGapAnalyzer = Depends(get_skill_gap_analyzer),
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> SkillRecommendationResponse:
    """Get personalized skill recommendations for target role.

    This endpoint provides prioritized skill recommendations based on:
    - User's current skills
    - Target job role requirements
    - Market demand scores
    - Estimated learning times
    - Available learning resources

    Args:
        request: Skill recommendation request
        analyzer: Skill gap analyzer instance
        ctx: Tenant context for user identification

    Returns:
        Prioritized skill recommendations with learning resources
    """
    try:
        logger.info(
            f"[SKILL_GAP] Getting recommendations for user {ctx.user_id}, "
            f"target role: '{request.target_role}', limit: {request.limit}"
        )

        # Validate current skills
        taxonomy = get_skills_taxonomy()
        valid_skills, _, _ = taxonomy.validate_user_skills(request.current_skills)

        # Get recommendations
        recommendations = analyzer.get_recommendations(
            current_skills=valid_skills,
            target_role=request.target_role,
            limit=request.limit,
        )

        # Calculate total estimated learning time
        total_learning_weeks = sum(
            r.get("estimated_learning_weeks", 0) for r in recommendations
        )

        # Get total missing skills count
        analysis = analyzer.analyze(valid_skills, request.target_role)
        total_missing = len(analysis.missing_skills)

        logger.info(
            f"[SKILL_GAP] Generated {len(recommendations)} recommendations "
            f"for user {ctx.user_id}, total learning time: {total_learning_weeks:.1f} weeks"
        )

        return SkillRecommendationResponse(
            target_role=request.target_role,
            recommendations=recommendations,
            total_missing=total_missing,
            estimated_total_learning_weeks=total_learning_weeks,
        )

    except Exception as e:
        logger.error(f"Skill recommendations failed: {e}")
        raise HTTPException(
            status_code=500, detail="Skill recommendations failed. Please try again."
        )


@router.get("/roles", response_model=TargetRolesResponse)
async def get_target_roles(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> TargetRolesResponse:
    """Get available target roles for skill gap analysis.

    This endpoint returns a list of job roles that can be used as targets
    for skill gap analysis, along with metadata about each role.

    Args:
        ctx: Tenant context for user identification

    Returns:
        List of available target roles
    """
    try:
        from packages.backend.domain.skill_gap_analyzer import JobMarketData

        roles_data = JobMarketData.ROLE_REQUIREMENTS

        roles = []
        for role_name, role_info in roles_data.items():
            roles.append({
                "id": role_name,
                "name": role_name.replace("_", " ").title(),
                "required_skills_count": len(role_info.get("required_skills", [])),
                "preferred_skills_count": len(role_info.get("preferred_skills", [])),
                "experience_level": role_info.get("experience_level", "mid"),
                "demand_growth": role_info.get("demand_growth", 0),
            })

        # Sort by demand growth (highest first)
        roles.sort(key=lambda x: x.get("demand_growth", 0), reverse=True)

        logger.info(f"[SKILL_GAP] Served {len(roles)} target roles to user {ctx.user_id}")

        return TargetRolesResponse(roles=roles)

    except Exception as e:
        logger.error(f"Failed to get target roles: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve target roles."
        )


@router.get("/health")
async def skill_gap_health_check(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, str]:
    """Health check endpoint for skill gap analysis service.

    Args:
        ctx: Tenant context for user identification

    Returns:
        Health status
    """
    try:
        # Quick check that analyzer can be instantiated
        get_skill_gap_analyzer()
        taxonomy = get_skills_taxonomy()

        return {
            "status": "healthy",
            "taxonomy_skills": str(len(taxonomy._skills_db)),
            "service": "skill_gap_analysis",
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500, detail="Skill gap analysis service is unhealthy."
        )
