"""Match Weights Configuration API endpoints for per-tenant customization."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.domain.match_weights import (
    TenantMatchConfig,
    WeightCategory,
    get_match_weights_manager,
)
from backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.match_weights")

router = APIRouter(tags=["match_weights"])


class WeightConfigRequest(BaseModel):
    """Request model for updating a weight configuration."""

    category: str = Field(..., description="Weight category")
    weight: float = Field(
        ..., ge=0.0, le=2.0, description="Weight multiplier (0.0 to 2.0)"
    )
    enabled: bool = Field(default=True, description="Whether the weight is enabled")
    priority: int = Field(
        default=1, ge=1, le=10, description="Priority level (1=highest, 10=lowest)"
    )
    custom_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Custom scoring rules"
    )


class TenantConfigRequest(BaseModel):
    """Request model for updating tenant match configuration."""

    global_multiplier: float = Field(
        default=1.0, ge=0.1, le=3.0, description="Global score multiplier"
    )
    min_match_score: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Minimum match score threshold"
    )
    max_results: int = Field(
        default=100, ge=10, le=1000, description="Maximum results to return"
    )
    enable_ml_scoring: bool = Field(default=True, description="Enable ML-based scoring")
    custom_scoring_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Custom scoring rules"
    )


class MatchScoreRequest(BaseModel):
    """Request model for calculating match scores."""

    user_skills: List[str] = Field(default=[], description="User's skills")
    job_skills: List[str] = Field(default=[], description="Job's required skills")
    user_experience_years: float = Field(
        default=0.0, description="User's years of experience"
    )
    required_experience_years: float = Field(
        default=0.0, description="Required years of experience"
    )
    user_location: str = Field(default="", description="User's location")
    job_location: str = Field(default="", description="Job's location")
    is_remote: bool = Field(default=False, description="Whether the job is remote")
    user_prefers_remote: bool = Field(
        default=False, description="Whether user prefers remote work"
    )
    user_min_salary: float = Field(default=0.0, description="User's minimum salary")
    job_min_salary: float = Field(default=0.0, description="Job's minimum salary")
    job_max_salary: float = Field(default=0.0, description="Job's maximum salary")
    user_education_level: str = Field(default="", description="User's education level")
    required_education_level: str = Field(
        default="", description="Required education level"
    )
    user_remote_preference: str = Field(
        default="", description="User's remote preference"
    )
    job_remote_option: str = Field(default="", description="Job's remote option")
    user_seniority_level: str = Field(default="", description="User's seniority level")
    job_seniority_level: str = Field(default="", description="Job's seniority level")
    ml_score: Optional[float] = Field(default=None, description="ML-generated score")


class MatchScoreResponse(BaseModel):
    """Response model for match score calculation."""

    total_score: float = Field(..., description="Overall match score (0.0 to 1.0)")
    category_scores: Dict[str, float] = Field(
        ..., description="Individual category scores"
    )
    config_version: int = Field(..., description="Configuration version used")
    meets_threshold: bool = Field(
        ..., description="Whether score meets minimum threshold"
    )
    recommendations: List[str] = Field(
        default=[], description="Improvement recommendations"
    )


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


@router.get("/config")
async def get_tenant_config(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get the current match configuration for the tenant.

    Args:
        ctx: Tenant context for identification

    Returns:
        Current tenant match configuration
    """
    try:
        from backend.domain.repositories import get_pool

        manager = get_match_weights_manager()
        config = await manager.get_tenant_config(get_pool(), ctx.tenant_id)

        # Convert to serializable format
        weights_data = {}
        for category, weight_config in config.weights.items():
            weights_data[category.value] = {
                "weight": weight_config.weight,
                "enabled": weight_config.enabled,
                "priority": weight_config.priority,
                "custom_rules": weight_config.custom_rules,
                "description": weight_config.description,
                "last_updated": weight_config.last_updated.isoformat()
                if weight_config.last_updated
                else None,
                "updated_by": weight_config.updated_by,
            }

        return {
            "tenant_id": config.tenant_id,
            "weights": weights_data,
            "global_multiplier": config.global_multiplier,
            "min_match_score": config.min_match_score,
            "max_results": config.max_results,
            "enable_ml_scoring": config.enable_ml_scoring,
            "custom_scoring_rules": config.custom_scoring_rules,
            "version": config.version,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "created_by": config.created_by,
            "updated_by": config.updated_by,
        }

    except Exception as e:
        logger.error(f"Failed to get tenant config: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve match configuration."
        )


@router.put("/config")
async def update_tenant_config(
    request: TenantConfigRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Update the tenant's match configuration.

    Args:
        request: Configuration update request
        ctx: Tenant context for identification

    Returns:
        Updated configuration
    """
    try:
        from backend.domain.repositories import get_pool

        manager = get_match_weights_manager()

        # Get current config
        config = await manager.get_tenant_config(get_pool(), ctx.tenant_id)

        # Update configuration
        config.global_multiplier = request.global_multiplier
        config.min_match_score = request.min_match_score
        config.max_results = request.max_results
        config.enable_ml_scoring = request.enable_ml_scoring
        config.custom_scoring_rules = request.custom_scoring_rules
        config.updated_by = ctx.user_id

        # Save updated configuration
        success = await manager.save_tenant_config(get_pool(), config, ctx.user_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save configuration.")

        logger.info(
            f"Updated match config v{config.version} for tenant {ctx.tenant_id}"
        )

        return {
            "tenant_id": config.tenant_id,
            "version": config.version,
            "updated_at": config.updated_at.isoformat(),
            "message": "Configuration updated successfully",
        }

    except Exception as e:
        logger.error(f"Failed to update tenant config: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update match configuration."
        )


@router.put("/weights/{category}")
async def update_weight(
    category: str,
    request: WeightConfigRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Update a specific weight configuration.

    Args:
        category: Weight category to update
        request: Weight configuration update
        ctx: Tenant context for identification

    Returns:
        Updated weight configuration
    """
    try:
        from backend.domain.repositories import get_pool

        # Validate category
        try:
            weight_category = WeightCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid weight category: {category}"
            )

        manager = get_match_weights_manager()

        # Update the weight
        success = await manager.update_weight(
            get_pool(),
            ctx.tenant_id,
            weight_category,
            request.weight,
            request.enabled,
            request.priority,
            request.custom_rules,
            ctx.user_id,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update weight.")

        logger.info(f"Updated weight {category} for tenant {ctx.tenant_id}")

        return {
            "category": category,
            "weight": request.weight,
            "enabled": request.enabled,
            "priority": request.priority,
            "updated_by": ctx.user_id,
            "message": "Weight updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update weight: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update weight configuration."
        )


@router.post("/calculate-score")
async def calculate_match_score(
    request: MatchScoreRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> MatchScoreResponse:
    """Calculate match score using tenant-specific configuration.

    Args:
        request: Match score calculation request
        ctx: Tenant context for identification

    Returns:
        Calculated match score with breakdown
    """
    try:
        from backend.domain.repositories import get_pool

        manager = get_match_weights_manager()
        config = await manager.get_tenant_config(get_pool(), ctx.tenant_id)

        # Prepare match data
        match_data = {
            "user_skills": request.user_skills,
            "job_skills": request.job_skills,
            "user_experience_years": request.user_experience_years,
            "required_experience_years": request.required_experience_years,
            "user_location": request.user_location,
            "job_location": request.job_location,
            "is_remote": request.is_remote,
            "user_prefers_remote": request.user_prefers_remote,
            "user_min_salary": request.user_min_salary,
            "job_min_salary": request.job_min_salary,
            "job_max_salary": request.job_max_salary,
            "user_education_level": request.user_education_level,
            "required_education_level": request.required_education_level,
            "user_remote_preference": request.user_remote_preference,
            "job_remote_option": request.job_remote_option,
            "user_seniority_level": request.user_seniority_level,
            "job_seniority_level": request.job_seniority_level,
        }

        if request.ml_score is not None:
            match_data["ml_score"] = request.ml_score

        # Calculate individual category scores
        category_scores = {}
        for category, weight_config in config.weights.items():
            if weight_config.enabled:
                category_score = manager._calculate_category_score(
                    category, match_data, weight_config
                )
                category_scores[category.value] = category_score

        # Calculate total score
        total_score = manager.calculate_match_score(config, match_data)

        # Generate recommendations
        recommendations = []
        if total_score < config.min_match_score:
            recommendations.append("Score below minimum threshold")

        if not request.user_skills and request.job_skills:
            recommendations.append("Add user skills to improve matching")

        if request.user_experience_years < request.required_experience_years * 0.5:
            recommendations.append("Consider roles with less experience requirements")

        if (
            request.user_min_salary > request.job_max_salary
            and request.job_max_salary > 0
        ):
            recommendations.append("Consider adjusting salary expectations")

        logger.info(
            f"Calculated match score {total_score:.3f} for tenant {ctx.tenant_id}"
        )

        return MatchScoreResponse(
            total_score=total_score,
            category_scores=category_scores,
            config_version=config.version,
            meets_threshold=total_score >= config.min_match_score,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Failed to calculate match score: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate match score.")


@router.get("/categories")
async def get_weight_categories(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> List[Dict[str, Any]]:
    """Get all available weight categories.

    Args:
        ctx: Tenant context for identification

    Returns:
        List of weight categories with descriptions
    """
    try:
        manager = get_match_weights_manager()

        categories = []
        for category in WeightCategory:
            default_config = manager._default_weights[category]
            categories.append(
                {
                    "category": category.value,
                    "description": default_config.description,
                    "default_weight": default_config.weight,
                    "default_priority": default_config.priority,
                    "custom_rules_example": default_config.custom_rules,
                }
            )

        # Sort by priority
        categories.sort(key=lambda x: x["default_priority"])

        return categories

    except Exception as e:
        logger.error(f"Failed to get weight categories: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve weight categories."
        )


@router.get("/analytics")
async def get_match_analytics(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to analyze"
    ),
) -> Dict[str, Any]:
    """Get match analytics for the tenant.

    Args:
        ctx: Tenant context for identification
        days: Number of days to analyze

    Returns:
        Match analytics data
    """
    try:
        from backend.domain.repositories import get_pool

        async with get_pool().acquire() as conn:
            # Get analytics from the view
            row = await conn.fetchrow(
                """
                SELECT * FROM tenant_match_analytics
                WHERE tenant_id = $1
                ORDER BY version DESC
                LIMIT 1
            """,
                ctx.tenant_id,
            )

            if not row:
                return {
                    "tenant_id": ctx.tenant_id,
                    "message": "No analytics data available",
                    "total_matches": 0,
                    "avg_match_score": 0.0,
                    "success_rate": 0.0,
                }

            # Get recent match history
            history_rows = await conn.fetch(
                """
                SELECT
                    match_score,
                    user_action,
                    outcome,
                    applied_at
                FROM match_score_history
                WHERE tenant_id = $1
                    AND applied_at >= NOW() - INTERVAL '%s days'
                ORDER BY applied_at DESC
            """,
                ctx.tenant_id,
                days,
            )

            # Process history data
            daily_scores = {}
            action_counts = {"viewed": 0, "applied": 0, "skipped": 0, "rejected": 0}
            outcome_counts = {"success": 0, "pending": 0, "failed": 0, "withdrawn": 0}

            for history_row in history_rows:
                date_key = history_row["applied_at"].strftime("%Y-%m-%d")
                if date_key not in daily_scores:
                    daily_scores[date_key] = []
                daily_scores[date_key].append(float(history_row["match_score"]))

                action = history_row["user_action"]
                if action in action_counts:
                    action_counts[action] += 1

                outcome = history_row["outcome"]
                if outcome in outcome_counts:
                    outcome_counts[outcome] += 1

            # Calculate daily averages
            daily_averages = {}
            for date, scores in daily_scores.items():
                daily_averages[date] = sum(scores) / len(scores)

            return {
                "tenant_id": ctx.tenant_id,
                "config_version": row["version"],
                "total_matches": row["total_matches"],
                "avg_match_score": float(row["avg_match_score"]),
                "successful_matches": row["successful_matches"],
                "total_applications": row["total_applications"],
                "success_rate": float(row["success_rate"] or 0.0),
                "period_days": days,
                "daily_scores": daily_averages,
                "action_counts": action_counts,
                "outcome_counts": outcome_counts,
                "global_multiplier": float(row["global_multiplier"]),
                "min_match_score": float(row["min_match_score"]),
                "enable_ml_scoring": row["enable_ml_scoring"],
            }

    except Exception as e:
        logger.error(f"Failed to get match analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve match analytics."
        )


@router.post("/reset")
async def reset_to_defaults(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Reset tenant configuration to defaults.

    Args:
        ctx: Tenant context for identification

    Returns:
        Reset confirmation
    """
    try:
        from backend.domain.repositories import get_pool

        manager = get_match_weights_manager()

        # Create new default configuration
        config = TenantMatchConfig(
            tenant_id=ctx.tenant_id,
            weights=manager._default_weights.copy(),
            global_multiplier=1.0,
            min_match_score=0.3,
            max_results=100,
            enable_ml_scoring=True,
            version=1,
            created_by=ctx.user_id,
            updated_by=ctx.user_id,
        )

        # Save the default configuration
        success = await manager.save_tenant_config(get_pool(), config, ctx.user_id)

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to reset configuration."
            )

        logger.info(f"Reset match config to defaults for tenant {ctx.tenant_id}")

        return {
            "tenant_id": ctx.tenant_id,
            "version": config.version,
            "message": "Configuration reset to defaults successfully",
            "reset_at": config.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to reset configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset configuration.")
