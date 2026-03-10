"""Skills Analysis API endpoints for skill validation and job matching."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.domain.skills_taxonomy import get_skills_taxonomy, validate_user_skills
from backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.skills")

router = APIRouter(tags=["skills"])


class SkillsValidationRequest(BaseModel):
    """Request model for skills validation."""

    skills: List[str] = Field(..., description="List of raw skill strings to validate")


class SkillsValidationResponse(BaseModel):
    """Response model for skills validation."""

    valid_skills: List[str] = Field(
        ..., description="Validated and normalized skill names"
    )
    invalid_skills: List[str] = Field(
        ..., description="Skills that could not be validated"
    )
    analysis: Dict[str, Any] = Field(..., description="Detailed analysis of skills")
    suggestions: List[str] = Field(
        default=[], description="Skill suggestions for improvement"
    )


class SkillSuggestionRequest(BaseModel):
    """Request model for skill suggestions."""

    current_skills: List[str] = Field(..., description="User's current skills")
    target_role: str = Field(..., description="Target job role or position")


class SkillSuggestionResponse(BaseModel):
    """Response model for skill suggestions."""

    missing_skills: List[str] = Field(..., description="Recommended skills to learn")
    skill_gap_score: float = Field(..., description="Skill gap score (0.0 to 1.0)")
    target_role_skills: List[str] = Field(
        ..., description="Expected skills for target role"
    )
    learning_priority: List[Dict[str, Any]] = Field(
        ..., description="Prioritized learning recommendations"
    )


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


@router.post("/validate")
async def validate_skills(
    request: SkillsValidationRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> SkillsValidationResponse:
    """Validate and normalize a list of skills.

    This endpoint validates raw skill inputs against the standardized skills taxonomy,
    normalizes them to canonical names, and provides detailed analysis.

    Args:
        request: Skills validation request with raw skill strings
        ctx: Tenant context for user identification

    Returns:
        Skills validation response with valid/invalid skills and analysis
    """
    try:
        taxonomy = get_skills_taxonomy()
        valid_skills, invalid_skills, analysis = validate_user_skills(request.skills)

        # Generate suggestions for invalid skills
        suggestions = []
        for invalid_skill in invalid_skills:
            # Try to find close matches
            normalized = taxonomy.normalize_skill(invalid_skill)
            if normalized:
                suggestions.append(f"'{invalid_skill}' → '{normalized}'")
            else:
                # Suggest similar skills
                for skill_name, skill_info in taxonomy._skills_db.items():
                    if (
                        invalid_skill.lower() in skill_name.lower()
                        or skill_name.lower() in invalid_skill.lower()
                    ):
                        suggestions.append(f"'{invalid_skill}' → '{skill_name}'")
                        break

        logger.info(
            f"[SKILLS] Validated {len(valid_skills)}/{len(request.skills)} skills for user {ctx.user_id}"
        )

        return SkillsValidationResponse(
            valid_skills=valid_skills,
            invalid_skills=invalid_skills,
            analysis=analysis,
            suggestions=suggestions[:10],  # Limit suggestions
        )

    except Exception as e:
        logger.error(f"Skills validation failed: {e}")
        raise HTTPException(
            status_code=500, detail="Skills validation failed. Please try again."
        )


@router.post("/suggestions")
async def get_skill_suggestions(
    request: SkillSuggestionRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> SkillSuggestionResponse:
    """Get skill suggestions based on current skills and target role.

    This endpoint analyzes the user's current skills against the requirements
    for a target role and provides personalized learning recommendations.

    Args:
        request: Skill suggestion request with current skills and target role
        ctx: Tenant context for user identification

    Returns:
        Skill suggestion response with missing skills and learning priorities
    """
    try:
        taxonomy = get_skills_taxonomy()

        # Validate current skills
        valid_skills, _, _ = validate_user_skills(request.current_skills)

        # Get target role skills
        target_role_skills = taxonomy._get_target_role_skills(request.target_role)

        # Find missing skills
        user_skill_set = set(valid_skills)
        missing_skills = []

        for target_skill in target_role_skills:
            if target_skill not in user_skill_set:
                missing_skills.append(target_skill)

        # Calculate skill gap score
        skill_gap_score = (
            len(missing_skills) / len(target_role_skills) if target_role_skills else 0.0
        )

        # Create learning priority recommendations
        learning_priority = []
        for skill in missing_skills:
            skill_info = taxonomy.get_skill_info(skill)
            if skill_info:
                learning_priority.append(
                    {
                        "skill": skill,
                        "category": skill_info.category.value,
                        "demand_score": skill_info.demand_score,
                        "description": skill_info.description,
                        "priority": "high"
                        if skill_info.demand_score > 0.8
                        else "medium"
                        if skill_info.demand_score > 0.6
                        else "low",
                    }
                )

        # Sort by demand score (highest priority first)
        learning_priority.sort(key=lambda x: x["demand_score"], reverse=True)

        logger.info(
            f"[SKILLS] Generated {len(missing_skills)} skill suggestions for role '{request.target_role}' for user {ctx.user_id}"
        )

        return SkillSuggestionResponse(
            missing_skills=missing_skills,
            skill_gap_score=skill_gap_score,
            target_role_skills=target_role_skills,
            learning_priority=learning_priority,
        )

    except Exception as e:
        logger.error(f"Skill suggestions failed: {e}")
        raise HTTPException(
            status_code=500, detail="Skill suggestions failed. Please try again."
        )


@router.get("/taxonomy")
async def get_skills_taxonomy_info(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get the complete skills taxonomy information.

    This endpoint returns the full skills taxonomy including all categories,
    skills, and their metadata for frontend applications.

    Args:
        ctx: Tenant context for user identification

    Returns:
        Complete skills taxonomy information
    """
    try:
        taxonomy = get_skills_taxonomy()

        # Build taxonomy response
        categories = {}
        for category in taxonomy.get_skill_categories():
            skills = taxonomy.get_skills_by_category(category)
            items = []
            for skill_name in skills:
                info = taxonomy.get_skill_info(skill_name)
                if info is None:
                    continue
                items.append(
                    {
                        "name": skill_name,
                        "aliases": list(info.aliases),
                        "demand_score": info.demand_score,
                        "description": info.description,
                        "proficiency_levels": info.proficiency_levels,
                        "technical_level": info.technical_level,
                    }
                )
            categories[category.value] = items

        logger.info(f"[SKILLS] Served taxonomy info to user {ctx.user_id}")

        return {
            "categories": categories,
            "total_skills": len(taxonomy._skills_db),
            "taxonomy_version": "1.0",
            "last_updated": "2024-03-08",
        }

    except Exception as e:
        logger.error(f"Taxonomy retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve skills taxonomy."
        )


@router.get("/categories")
async def get_skill_categories(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> List[str]:
    """Get all available skill categories.

    Args:
        ctx: Tenant context for user identification

    Returns:
        List of skill category names
    """
    try:
        taxonomy = get_skills_taxonomy()
        categories = [category.value for category in taxonomy.get_skill_categories()]

        logger.info(
            f"[SKILLS] Served {len(categories)} categories to user {ctx.user_id}"
        )

        return categories

    except Exception as e:
        logger.error(f"Categories retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve skill categories."
        )


@router.get("/search")
async def search_skills(
    query: str = Query(..., description="Search query for skills"),
    category: str = Query(None, description="Filter by skill category"),
    limit: int = Query(
        default=10, ge=1, le=50, description="Maximum number of results"
    ),
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> List[Dict[str, Any]]:
    """Search for skills by name or keyword.

    Args:
        query: Search query string
        category: Optional category filter
        limit: Maximum number of results to return
        ctx: Tenant context for user identification

    Returns:
        List of matching skills with metadata
    """
    try:
        taxonomy = get_skills_taxonomy()

        # Normalize query
        normalized_query = query.lower().strip()

        matching_skills = []

        for skill_name, skill_info in taxonomy._skills_db.items():
            # Check if query matches skill name or aliases
            name_match = normalized_query in skill_name.lower()
            alias_match = any(
                normalized_query in alias.lower() for alias in skill_info.aliases
            )
            desc_match = normalized_query in skill_info.description.lower()

            if name_match or alias_match or desc_match:
                # Apply category filter if specified
                if category and skill_info.category.value != category:
                    continue

                matching_skills.append(
                    {
                        "name": skill_name,
                        "category": skill_info.category.value,
                        "aliases": list(skill_info.aliases),
                        "demand_score": skill_info.demand_score,
                        "description": skill_info.description,
                        "proficiency_levels": skill_info.proficiency_levels,
                        "technical_level": skill_info.technical_level,
                    }
                )

        # Sort by relevance (exact name match first, then demand score)
        def sort_key(x: Dict[str, Any]) -> tuple[int, float]:
            name_match = (
                0
                if isinstance(x.get("name"), str)
                and str(x["name"]).lower() == normalized_query
                else 1
            )
            score = x.get("demand_score", 0)
            score_val = float(score) if isinstance(score, (int, float)) else 0.0
            return (name_match, -score_val)

        matching_skills.sort(key=sort_key)

        # Limit results
        results = matching_skills[:limit]

        logger.info(
            f"[SKILLS] Search for '{query}' returned {len(results)} results for user {ctx.user_id}"
        )

        return results

    except Exception as e:
        logger.error(f"Skill search failed: {e}")
        raise HTTPException(
            status_code=500, detail="Skill search failed. Please try again."
        )
