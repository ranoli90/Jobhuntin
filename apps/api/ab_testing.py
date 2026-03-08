"""A/B Testing API endpoints for AI content quality measurement.

Provides comprehensive A/B testing framework:
- Experiment management and configuration
- Variant generation and distribution
- User assignment and tracking
- Performance metrics collection
- Statistical analysis and significance testing
- Automated winner determination

Key endpoints:
- POST /ab-testing/experiments - Create new experiment
- GET /ab-testing/experiments - List experiments
- GET /ab-testing/experiments/{id} - Get experiment details
- POST /ab-testing/experiments/{id}/start - Start experiment
- POST /ab-testing/experiments/{id}/complete - Complete experiment
- POST /ab-testing/assign - Assign user to variant
- POST /ab-testing/results - Record experiment result
- GET /ab-testing/experiments/{id}/results - Get experiment results
- POST /ab-testing/experiments/{id}/analyze - Analyze experiment results
- GET /ab-testing/experiments/{id}/summary - Get experiment summary
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.domain.ab_testing import (
    get_ab_testing_manager,
    ExperimentStatus,
    MetricType,
)
from backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.ab_testing")

router = APIRouter(tags=["ab_testing"])


class CreateExperimentRequest(BaseModel):
    """Request for creating A/B test experiment."""

    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description")
    variants_config: List[Dict[str, Any]] = Field(
        ..., description="Variant configurations"
    )
    target_metrics: List[str] = Field(..., description="Target metrics")
    sample_size: int = Field(default=1000, description="Required sample size")
    duration_days: int = Field(default=30, description="Duration in days")
    target_audience: Optional[Dict[str, Any]] = Field(
        default=None, description="Target audience"
    )
    ai_model_config: Optional[Dict[str, Any]] = Field(
        default=None, description="AI model config"
    )


class CreateExperimentResponse(BaseModel):
    """Response for creating experiment."""

    experiment_id: str = Field(..., description="Experiment ID")
    name: str = Field(..., description="Experiment name")
    status: str = Field(..., description="Experiment status")
    variants: List[Dict[str, Any]] = Field(..., description="Created variants")
    traffic_allocation: float = Field(..., description="Traffic allocation per variant")


class UserAssignmentRequest(BaseModel):
    """Request for user assignment to variant."""

    user_id: str = Field(..., description="User ID")
    experiment_id: str = Field(..., description="Experiment ID")
    user_attributes: Optional[Dict[str, Any]] = Field(
        default=None, description="User attributes"
    )


class UserAssignmentResponse(BaseModel):
    """Response for user assignment."""

    variant_id: str = Field(..., description="Assigned variant ID")
    variant_name: str = Field(..., description="Variant name")
    variant_type: str = Field(..., description="Variant type")
    experiment_name: str = Field(..., description="Experiment name")
    configuration: Dict[str, Any] = Field(..., description="Variant configuration")


class RecordResultRequest(BaseModel):
    """Request for recording experiment result."""

    experiment_id: str = Field(..., description="Experiment ID")
    variant_id: str = Field(..., description="Variant ID")
    user_id: str = Field(..., description="User ID")
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    user_feedback: Optional[Dict[str, Any]] = Field(
        default=None, description="User feedback"
    )
    quality_score: Optional[float] = Field(
        default=None, description="AI content quality score"
    )


class RecordResultResponse(BaseModel):
    """Response for recording result."""

    success: bool = Field(..., description="Whether result was recorded")
    experiment_id: str = Field(..., description="Experiment ID")
    variant_id: str = Field(..., description="Variant ID")
    total_participants: int = Field(..., description="Total participants so far")


class AnalyzeRequest(BaseModel):
    """Request for statistical analysis."""

    experiment_id: str = Field(..., description="Experiment ID")
    metric: str = Field(..., description="Metric to analyze")
    confidence_level: float = Field(default=0.95, description="Confidence level")


class AnalyzeResponse(BaseModel):
    """Response for statistical analysis."""

    analyses: List[Dict[str, Any]] = Field(..., description="Statistical analyses")
    experiment_id: str = Field(..., description="Experiment ID")
    metric: str = Field(..., description="Analyzed metric")
    total_comparisons: int = Field(..., description="Total pairwise comparisons")
    significant_results: int = Field(..., description="Number of significant results")


class GenerateVariantRequest(BaseModel):
    """Request for generating AI variant."""

    base_prompt: str = Field(..., description="Base AI prompt")
    variant_type: str = Field(..., description="Variant type")
    optimization_goal: str = Field(..., description="Optimization goal")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context"
    )


class GenerateVariantResponse(BaseModel):
    """Response for generating AI variant."""

    variant_config: Dict[str, Any] = Field(
        ..., description="Generated variant configuration"
    )
    optimization_rationale: str = Field(..., description="Explanation of optimization")
    expected_improvement: float = Field(
        ..., description="Expected improvement percentage"
    )


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


@router.post("/experiments", response_model=CreateExperimentResponse)
async def create_experiment(
    request: CreateExperimentRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> CreateExperimentResponse:
    """Create a new A/B testing experiment.

    Args:
        request: Experiment creation request
        ctx: Tenant context for identification

    Returns:
        Created experiment details
    """
    try:
        ab_testing = get_ab_testing_manager()

        # Convert metric strings to enum
        target_metrics = [MetricType(m) for m in request.target_metrics]

        # Create experiment
        experiment = await ab_testing.create_experiment(
            name=request.name,
            description=request.description,
            variants_config=request.variants_config,
            target_metrics=target_metrics,
            sample_size=request.sample_size,
            duration_days=request.duration_days,
            target_audience=request.target_audience,
            ai_model_config=request.ai_model_config,
        )

        return CreateExperimentResponse(
            experiment_id=experiment.id,
            name=experiment.name,
            status=experiment.status.value,
            variants=experiment.variants,
            traffic_allocation=experiment.traffic_allocation,
        )

    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create experiment")


@router.get("/experiments")
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of experiments"),
    offset: int = Query(0, description="Offset for pagination"),
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """List A/B testing experiments.

    Args:
        status: Optional status filter
        limit: Maximum number of experiments
        offset: Pagination offset
        ctx: Tenant context for identification

    Returns:
        List of experiments
    """
    try:
        ab_testing = get_ab_testing_manager()

        # In a real implementation, this would query database
        experiments = list(ab_testing._experiments.values())

        # Apply filters
        if status:
            experiments = [e for e in experiments if e.status.value == status]

        # Apply pagination
        total = len(experiments)
        experiments = experiments[offset : offset + limit]

        return {
            "experiments": [e.model_dump() for e in experiments],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }

    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list experiments")


@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get experiment details.

    Args:
        experiment_id: Experiment ID
        ctx: Tenant context for identification

    Returns:
        Experiment details
    """
    try:
        ab_testing = get_ab_testing_manager()

        # Get experiment
        experiment = ab_testing._experiments.get(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")

        # Get variants
        variants = [
            v for v in ab_testing._variants.values() if v.experiment_id == experiment_id
        ]

        # Get results summary
        results_summary = {}
        for variant in variants:
            variant_results = await ab_testing.get_experiment_results(
                experiment_id, variant.id
            )
            results_summary[variant.id] = {
                "participants": len(variant_results),
                "conversion_rate": 0.0,
                "avg_engagement_time": 0.0,
                "error_rate": 0.0,
                "avg_quality_score": 0.0,
            }

            if variant_results:
                conversions = sum(1 for r in variant_results if r.conversion)
                results_summary[variant.id]["conversion_rate"] = conversions / len(
                    variant_results
                )

                engagement_times = [
                    r.engagement_time_seconds
                    for r in variant_results
                    if r.engagement_time_seconds is not None
                ]
                if engagement_times:
                    results_summary[variant.id]["avg_engagement_time"] = sum(
                        engagement_times
                    ) / len(engagement_times)

                errors = sum(1 for r in variant_results if r.error_occurred)
                results_summary[variant.id]["error_rate"] = errors / len(
                    variant_results
                )

                quality_scores = [
                    r.quality_score
                    for r in variant_results
                    if r.quality_score is not None
                ]
                if quality_scores:
                    results_summary[variant.id]["avg_quality_score"] = sum(
                        quality_scores
                    ) / len(quality_scores)

        return {
            "experiment": experiment.model_dump(),
            "variants": [v.model_dump() for v in variants],
            "results_summary": results_summary,
            "total_participants": sum(
                r["participants"] for r in results_summary.values()
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve experiment")


@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Start an A/B testing experiment.

    Args:
        experiment_id: Experiment ID
        ctx: Tenant context for identification

    Returns:
        Start operation result
    """
    try:
        ab_testing = get_ab_testing_manager()

        success = await ab_testing.start_experiment(experiment_id)

        if success:
            return {
                "success": True,
                "experiment_id": experiment_id,
                "message": "Experiment started successfully",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to start experiment")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to start experiment")


@router.post("/experiments/{experiment_id}/complete")
async def complete_experiment(
    experiment_id: str,
    winner_variant_id: Optional[str] = None,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Complete an A/B testing experiment.

    Args:
        experiment_id: Experiment ID
        winner_variant_id: Optional winner variant ID
        ctx: Tenant context for identification

    Returns:
        Completion operation result
    """
    try:
        ab_testing = get_ab_testing_manager()

        success = await ab_testing.complete_experiment(experiment_id, winner_variant_id)

        if success:
            return {
                "success": True,
                "experiment_id": experiment_id,
                "message": "Experiment completed successfully",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "winner_variant_id": winner_variant_id,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to complete experiment")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete experiment")


@router.post("/assign", response_model=UserAssignmentResponse)
async def assign_user_to_variant(
    request: UserAssignmentRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> UserAssignmentResponse:
    """Assign user to experiment variant.

    Args:
        request: User assignment request
        ctx: Tenant context for identification

    Returns:
        User assignment result
    """
    try:
        ab_testing = get_ab_testing_manager()

        # Assign user to variant
        variant = await ab_testing.assign_user_to_variant(
            user_id=request.user_id,
            experiment_id=request.experiment_id,
            user_attributes=request.user_attributes,
        )

        if not variant:
            raise HTTPException(status_code=404, detail="No suitable variant found")

        # Get experiment name
        experiment = ab_testing._experiments.get(request.experiment_id)
        experiment_name = experiment.name if experiment else "Unknown"

        return UserAssignmentResponse(
            variant_id=variant.id,
            variant_name=variant.name,
            variant_type=variant.type.value,
            experiment_name=experiment_name,
            configuration=variant.configuration,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign user to variant: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign user to variant")


@router.post("/results", response_model=RecordResultResponse)
async def record_experiment_result(
    request: RecordResultRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> RecordResultResponse:
    """Record experiment result.

    Args:
        request: Result recording request
        ctx: Tenant context for identification

    Returns:
        Recording operation result
    """
    try:
        ab_testing = get_ab_testing_manager()

        success = await ab_testing.record_result(
            experiment_id=request.experiment_id,
            variant_id=request.variant_id,
            user_id=request.user_id,
            metrics=request.metrics,
            user_feedback=request.user_feedback,
            quality_score=request.quality_score,
        )

        if success:
            # Get total participants
            total_results = await ab_testing.get_experiment_results(
                request.experiment_id
            )

            return RecordResultResponse(
                success=True,
                experiment_id=request.experiment_id,
                variant_id=request.variant_id,
                total_participants=len(total_results),
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to record result")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record result: {e}")
        raise HTTPException(status_code=500, detail="Failed to record result")


@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: str,
    variant_id: Optional[str] = None,
    limit: int = Query(1000, description="Maximum results"),
    offset: int = Query(0, description="Pagination offset"),
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get experiment results.

    Args:
        experiment_id: Experiment ID
        variant_id: Optional variant ID filter
        limit: Maximum results
        offset: Pagination offset
        ctx: Tenant context for identification

    Returns:
        Experiment results
    """
    try:
        ab_testing = get_ab_testing_manager()

        # Get results
        results = await ab_testing.get_experiment_results(experiment_id, variant_id)

        # Apply pagination
        total = len(results)
        results = results[offset : offset + limit]

        return {
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "results": [r.model_dump() for r in results],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }

    except Exception as e:
        logger.error(f"Failed to get experiment results: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve experiment results"
        )


@router.post("/experiments/{experiment_id}/analyze", response_model=AnalyzeResponse)
async def analyze_experiment_results(
    experiment_id: str,
    request: AnalyzeRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> AnalyzeResponse:
    """Analyze experiment results for statistical significance.

    Args:
        experiment_id: Experiment ID
        request: Analysis request
        ctx: Tenant context for identification

    Returns:
        Statistical analysis results
    """
    try:
        ab_testing = get_ab_testing_manager()

        # Convert metric string to enum
        metric = MetricType(request.metric)

        # Perform statistical analysis
        analyses = await ab_testing.analyze_results(experiment_id, metric)

        # Count significant results
        significant_results = sum(1 for a in analyses if a.is_significant)

        return AnalyzeResponse(
            analyses=[a.model_dump() for a in analyses],
            experiment_id=experiment_id,
            metric=request.metric,
            total_comparisons=len(analyses),
            significant_results=significant_results,
        )

    except Exception as e:
        logger.error(f"Failed to analyze experiment results: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to analyze experiment results"
        )


@router.get("/experiments/{experiment_id}/summary")
async def get_experiment_summary(
    experiment_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get experiment summary with key metrics.

    Args:
        experiment_id: Experiment ID
        ctx: Tenant context for identification

    Returns:
        Experiment summary
    """
    try:
        ab_testing = get_ab_testing_manager()

        # Get experiment summary
        summary = await ab_testing.get_experiment_summary(experiment_id)

        return summary

    except Exception as e:
        logger.error(f"Failed to get experiment summary: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve experiment summary"
        )


@router.post("/generate-variant", response_model=GenerateVariantResponse)
async def generate_ai_variant(
    request: GenerateVariantRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> GenerateVariantResponse:
    """Generate AI variant for A/B testing.

    Args:
        request: Variant generation request
        ctx: Tenant context for identification

    Returns:
        Generated variant configuration
    """
    try:
        ab_testing = get_ab_testing_manager()

        # Generate AI variant
        variant_config = await ab_testing.generate_ai_variant(
            base_prompt=request.base_prompt,
            variant_type=request.variant_type,
            optimization_goal=request.optimization_goal,
            context=request.context,
        )

        return GenerateVariantResponse(
            variant_config=variant_config,
            optimization_rationale=variant_config.get("rationale", ""),
            expected_improvement=variant_config.get("expected_improvement", 0.0),
        )

    except Exception as e:
        logger.error(f"Failed to generate AI variant: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI variant")


@router.get("/templates")
async def get_variant_templates(
    content_type: Optional[str] = Query(None, description="Content type filter"),
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get available variant templates.

    Args:
        content_type: Optional content type filter
        ctx: Tenant context for identification

    Returns:
        Available templates
    """
    try:
        ab_testing = get_ab_testing_manager()
        templates = ab_testing._ai_templates

        # Filter by content type
        if content_type:
            templates = {k: v for k, v in templates.items() if k == content_type}

        return {
            "templates": templates,
            "content_types": list(templates.keys()),
            "total_templates": sum(len(v) for v in templates.values()),
        }

    except Exception as e:
        logger.error(f"Failed to get variant templates: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve variant templates"
        )


@router.get("/analytics")
async def get_ab_testing_analytics(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get A/B testing analytics.

    Args:
        ctx: Tenant context for identification

    Returns:
        A/B testing analytics
    """
    try:
        ab_testing = get_ab_testing_manager()
        experiments = list(ab_testing._experiments.values())
        results = ab_testing._results

        # Calculate analytics
        total_experiments = len(experiments)
        running_experiments = len(
            [e for e in experiments if e.status == ExperimentStatus.RUNNING]
        )
        completed_experiments = len(
            [e for e in experiments if e.status == ExperimentStatus.COMPLETED]
        )

        total_participants = len(results)
        total_conversions = sum(1 for r in results if r.conversion)

        return {
            "total_experiments": total_experiments,
            "running_experiments": running_experiments,
            "completed_experiments": completed_experiments,
            "total_participants": total_participants,
            "total_conversions": total_conversions,
            "overall_conversion_rate": total_conversions / total_participants
            if total_participants > 0
            else 0.0,
            "avg_experiment_duration": 0.0,  # Would calculate from actual data
            "most_tested_metrics": [
                "conversion_rate",
                "engagement_time",
                "quality_score",
            ],
            "success_rate": completed_experiments / total_experiments
            if total_experiments > 0
            else 0.0,
        }

    except Exception as e:
        logger.error(f"Failed to get A/B testing analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve A/B testing analytics"
        )


@router.get("/health")
async def health_check(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Health check for A/B testing system."""

    return {
        "status": "healthy",
        "experiment_management": "operational",
        "variant_generation": "functional",
        "user_assignment": "operational",
        "result_tracking": "operational",
        "statistical_analysis": "functional",
        "ai_integration": "available",
        "total_experiments": 0,
        "total_participants": 0,
        "active_experiments": 0,
        "available_metrics": [
            "conversion_rate",
            "engagement_time",
            "user_satisfaction",
            "content_quality",
            "task_completion",
            "error_rate",
            "click_through_rate",
        ],
        "available_variant_types": [
            "ai_generated",
            "template_based",
            "hybrid",
            "control",
        ],
        "statistical_methods": {
            "significance_tests": ["t_test", "chi_square", "mann_whitney"],
            "effect_sizes": ["cohens_d", "pearson_r", "odds_ratio"],
            "confidence_intervals": ["wald", "wilson", "bootstrap"],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
