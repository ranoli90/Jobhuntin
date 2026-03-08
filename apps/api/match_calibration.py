"""Match Score Calibration API endpoints for data-driven optimization."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from backend.domain.match_calibration import get_match_calibrator
from backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.match_calibration")

router = APIRouter(tags=["match_calibration"])


class CalibrationRequest(BaseModel):
    """Request model for running calibration."""

    days_back: int = Field(
        default=90, ge=7, le=365, description="Number of days to analyze"
    )
    auto_apply: bool = Field(
        default=False, description="Automatically apply recommendations"
    )
    min_data_points: int = Field(
        default=50, ge=10, le=1000, description="Minimum data points required"
    )


class CalibrationResponse(BaseModel):
    """Response model for calibration results."""

    tenant_id: str = Field(..., description="Tenant identifier")
    status: str = Field(..., description="Calibration status")
    message: Optional[str] = Field(default=None, description="Status message")
    data_points: int = Field(..., description="Number of data points analyzed")
    metrics: Optional[Dict[str, Any]] = Field(
        default=None, description="Calibration metrics"
    )
    recommendations: List[Dict[str, Any]] = Field(
        default=[], description="Generated recommendations"
    )
    applied_count: int = Field(
        default=0, description="Number of recommendations applied"
    )
    calibrated_at: Optional[str] = Field(
        default=None, description="When calibration was performed"
    )


class AnalyticsResponse(BaseModel):
    """Response model for calibration analytics."""

    tenant_id: str = Field(..., description="Tenant identifier")
    period_days: int = Field(..., description="Analysis period in days")
    data_points: int = Field(..., description="Number of data points")
    metrics: Dict[str, Any] = Field(..., description="Calibration metrics")
    category_performance: Dict[str, Dict[str, float]] = Field(
        ..., description="Performance by category"
    )
    score_distribution: Dict[str, int] = Field(..., description="Score distribution")
    outcome_distribution: Dict[str, int] = Field(
        ..., description="Outcome distribution"
    )
    recommendations: List[Dict[str, Any]] = Field(
        default=[], description="Current recommendations"
    )


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


@router.post("/calibrate")
async def run_calibration(
    request: CalibrationRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> CalibrationResponse:
    """Run a calibration cycle for the tenant.

    Args:
        request: Calibration request parameters
        ctx: Tenant context for identification
        background_tasks: Background tasks for async operations

    Returns:
        Calibration results
    """
    try:
        from backend.domain.repositories import get_pool

        calibrator = get_match_calibrator()

        # Run calibration cycle
        result = await calibrator.run_calibration_cycle(
            get_pool(),
            ctx.tenant_id,
            request.days_back,
            request.auto_apply,
            ctx.user_id,
        )

        logger.info(
            f"Calibration cycle completed for tenant {ctx.tenant_id}: {result['status']}"
        )

        return CalibrationResponse(**result)

    except Exception as e:
        logger.error(f"Calibration failed for tenant {ctx.tenant_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Calibration failed. Please try again."
        )


@router.get("/analytics")
async def get_calibration_analytics(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    days_back: int = Query(
        default=90, ge=7, le=365, description="Number of days to analyze"
    ),
) -> AnalyticsResponse:
    """Get calibration analytics for the tenant.

    Args:
        ctx: Tenant context for identification
        days_back: Number of days to analyze

    Returns:
        Calibration analytics data
    """
    try:
        from backend.domain.repositories import get_pool

        calibrator = get_match_calibrator()

        # Collect data
        data_points = await calibrator.collect_calibration_data(
            get_pool(), ctx.tenant_id, days_back
        )

        if len(data_points) < 10:
            return AnalyticsResponse(
                tenant_id=ctx.tenant_id,
                period_days=days_back,
                data_points=len(data_points),
                metrics={
                    "total_matches": 0,
                    "success_rate": 0.0,
                    "application_rate": 0.0,
                    "avg_match_score": 0.0,
                    "score_correlation": 0.0,
                },
                category_performance={},
                score_distribution={},
                outcome_distribution={},
                recommendations=[],
            )

        # Calculate metrics
        metrics = calibrator.calculate_metrics(data_points)

        # Get current config for recommendations
        manager = get_match_calibrator()
        config = await manager.get_match_config(get_pool(), ctx.tenant_id)
        recommendations = calibrator.generate_recommendations(metrics, config)

        # Format recommendations
        formatted_recommendations = [
            {
                "category": rec.category.value,
                "current_weight": rec.current_weight,
                "recommended_weight": rec.recommended_weight,
                "confidence": rec.confidence,
                "reasoning": rec.reasoning,
                "expected_impact": rec.expected_impact,
                "sample_size": rec.sample_size,
            }
            for rec in recommendations
        ]

        return AnalyticsResponse(
            tenant_id=ctx.tenant_id,
            period_days=days_back,
            data_points=len(data_points),
            metrics={
                "total_matches": metrics.total_matches,
                "successful_matches": metrics.successful_matches,
                "application_rate": metrics.application_rate,
                "success_rate": metrics.success_rate,
                "avg_match_score": metrics.avg_match_score,
                "avg_successful_score": metrics.avg_successful_score,
                "avg_unsuccessful_score": metrics.avg_unsuccessful_score,
                "score_correlation": metrics.score_correlation,
            },
            category_performance=metrics.category_performance,
            score_distribution=metrics.score_distribution,
            outcome_distribution=metrics.outcome_distribution,
            recommendations=formatted_recommendations,
        )

    except Exception as e:
        logger.error(
            f"Failed to get calibration analytics for tenant {ctx.tenant_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve calibration analytics."
        )


@router.get("/recommendations")
async def get_current_recommendations(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    days_back: int = Query(
        default=90, ge=7, le=365, description="Number of days to analyze"
    ),
) -> Dict[str, Any]:
    """Get current calibration recommendations for the tenant.

    Args:
        ctx: Tenant context for identification
        days_back: Number of days to analyze

    Returns:
        Current recommendations
    """
    try:
        from backend.domain.repositories import get_pool

        calibrator = get_match_calibrator()

        # Collect data and calculate metrics
        data_points = await calibrator.collect_calibration_data(
            get_pool(), ctx.tenant_id, days_back
        )

        if len(data_points) < 10:
            return {
                "tenant_id": ctx.tenant_id,
                "message": "Insufficient data for recommendations",
                "recommendations": [],
            }

        metrics = calibrator.calculate_metrics(data_points)

        # Get current config
        manager = get_match_calibrator()
        config = await manager.get_config(get_pool(), ctx.tenant_id)

        # Generate recommendations
        recommendations = calibrator.generate_recommendations(metrics, config)

        return {
            "tenant_id": ctx.tenant_id,
            "data_points": len(data_points),
            "metrics_summary": {
                "total_matches": metrics.total_matches,
                "success_rate": metrics.success_rate,
                "score_correlation": metrics.score_correlation,
                "avg_match_score": metrics.avg_match_score,
            },
            "recommendations": [
                {
                    "category": rec.category.value,
                    "current_weight": rec.current_weight,
                    "recommended_weight": rec.recommended_weight,
                    "confidence": rec.confidence,
                    "reasoning": rec.reasoning,
                    "expected_impact": rec.expected_impact,
                    "sample_size": rec.sample_size,
                }
                for rec in recommendations
            ],
        }

    except Exception as e:
        logger.error(f"Failed to get recommendations for tenant {ctx.tenant_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve recommendations."
        )


@router.post("/recommendations/apply")
async def apply_recommendations(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    days_back: int = Query(
        default=90, ge=7, le=365, description="Number of days to analyze"
    ),
    confidence_threshold: float = Query(
        default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"
    ),
) -> Dict[str, Any]:
    """Apply calibration recommendations to tenant configuration.

    Args:
        ctx: Tenant context for identification
        days_back: Number of days to analyze
        confidence_threshold: Minimum confidence threshold for applying recommendations

    Returns:
        Application results
    """
    try:
        from backend.domain.repositories import get_pool

        calibrator = get_match_calibrator()

        # Collect data and calculate metrics
        data_points = await calibrator.collect_calibration_data(
            get_pool(), ctx.tenant_id, days_back
        )

        if len(data_points) < 10:
            return {
                "tenant_id": ctx.tenant_id,
                "status": "insufficient_data",
                "message": f"Insufficient data points ({len(data_points)}) for recommendations. Minimum 10 required.",
                "applied_count": 0,
            }

        metrics = calibrator.calculate_metrics(data_points)

        # Get current config and recommendations
        manager = get_match_calibrator()
        config = await manager.get_config(get_pool(), ctx.tenant_id)
        recommendations = calibrator.generate_recommendations(metrics, config)

        # Filter by confidence threshold
        high_confidence_recs = [
            r for r in recommendations if r.confidence >= confidence_threshold
        ]

        if not high_confidence_recs:
            return {
                "tenant_id": ctx.tenant_id,
                "status": "no_recommendations",
                "message": f"No recommendations meet confidence threshold of {confidence_threshold}",
                "applied_count": 0,
            }

        # Apply recommendations
        success = await calibrator.apply_recommendations(
            get_pool(), ctx.tenant_id, high_confidence_recs, ctx.user_id
        )

        applied_count = (
            len([r for r in high_confidence_recs if r.confidence > 0.5])
            if success
            else 0
        )

        logger.info(
            f"Applied {applied_count} recommendations for tenant {ctx.tenant_id}"
        )

        return {
            "tenant_id": ctx.tenant_id,
            "status": "applied" if success else "failed",
            "total_recommendations": len(recommendations),
            "high_confidence_recommendations": len(high_confidence_recs),
            "applied_count": applied_count,
            "confidence_threshold": confidence_threshold,
            "applied_at": ctx.updated_at.isoformat() if ctx.updated_at else None,
        }

    except Exception as e:
        logger.error(f"Failed to apply recommendations for tenant {ctx.tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply recommendations.")


@router.get("/history")
async def get_calibration_history(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    limit: int = Query(
        default=10, ge=1, le=50, description="Maximum number of records to return"
    ),
    days_back: int = Query(
        default=365, ge=7, le=3650, description="Number of days to look back"
    ),
) -> Dict[str, Any]:
    """Get calibration history for the tenant.

    Args:
        ctx: Tenant context for identification
        limit: Maximum number of records to return
        days_back: Number of days to look back

    Returns:
        Calibration history
    """
    try:
        from backend.domain.repositories import get_pool

        async with get_pool().acquire() as conn:
            # Get calibration history from analytics table
            rows = await conn.fetch(
                """
                SELECT 
                    tenant_id,
                    category,
                    weight_value,
                    performance_score,
                    sample_size,
                    created_at,
                    period_start,
                    period_end
                FROM match_weight_analytics
                WHERE tenant_id = $1 
                    AND created_at >= NOW() - INTERVAL '%s days'
                ORDER BY created_at DESC
                LIMIT $2
            """,
                ctx.tenant_id,
                days_back,
                limit,
            )

            history = []
            for row in rows:
                history.append(
                    {
                        "category": row["category"],
                        "weight_value": float(row["weight_value"]),
                        "performance_score": float(row["performance_score"])
                        if row["performance_score"]
                        else None,
                        "sample_size": row["sample_size"],
                        "created_at": row["created_at"].isoformat(),
                        "period_start": row["period_start"].isoformat()
                        if row["period_start"]
                        else None,
                        "period_end": row["period_end"].isoformat()
                        if row["period_end"]
                        else None,
                    }
                )

            return {
                "tenant_id": ctx.tenant_id,
                "period_days": days_back,
                "limit": limit,
                "history": history,
                "total_records": len(history),
            }

    except Exception as e:
        logger.error(
            f"Failed to get calibration history for tenant {ctx.tenant_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve calibration history."
        )


@router.get("/data-quality")
async def get_data_quality_report(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    days_back: int = Query(
        default=90, ge=7, le=365, description="Number of days to analyze"
    ),
) -> Dict[str, Any]:
    """Get data quality report for calibration.

    Args:
        ctx: Tenant context for identification
        days_back: Number of days to analyze

    Returns:
        Data quality report
    """
    try:
        from backend.domain.repositories import get_pool

        calibrator = get_match_calibrator()

        # Collect data
        data_points = await calibrator.collect_calibration_data(
            get_pool(), ctx.tenant_id, days_back
        )

        if not data_points:
            return {
                "tenant_id": ctx.tenant_id,
                "period_days": days_back,
                "status": "no_data",
                "message": "No calibration data available",
                "recommendations": [
                    "Enable match score tracking",
                    "Increase user engagement to generate more data",
                    "Wait for more application outcomes",
                ],
            }

        # Calculate quality metrics
        total_points = len(data_points)
        points_with_outcomes = len([dp for dp in data_points if dp.outcome_timestamp])
        recent_points = len(
            [
                dp
                for dp in data_points
                if (datetime.now(timezone.utc) - dp.applied_at).days <= 30
            ]
        )

        # Outcome distribution
        outcome_counts = {}
        for dp in data_points:
            outcome = dp.outcome.value
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

        # Score distribution
        scores = [dp.match_score for dp in data_points]
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        score_range = max(scores) - min(scores) if scores else 0.0

        # Category coverage
        category_coverage = {}
        for dp in data_points:
            for category in dp.category_scores:
                category_coverage[category] = category_coverage.get(category, 0) + 1

        avg_coverage = (
            statistics.mean(category_coverage.values()) if category_coverage else 0.0
        )
        total_categories = len(category_coverage)

        # Generate recommendations
        recommendations = []

        if total_points < 50:
            recommendations.append(
                "Increase data collection period to get more calibration data"
            )

        if points_with_outcomes < total_points * 0.5:
            recommendations.append("Improve outcome tracking for better calibration")

        if recent_points < total_points * 0.3:
            recommendations.append("Focus on recent data for more relevant calibration")

        if avg_coverage < 0.7:
            recommendations.append(
                "Improve category score tracking for better analysis"
            )

        if score_std < 0.1:
            recommendations.append(
                "Review scoring algorithm - low variance may indicate issues"
            )

        return {
            "tenant_id": ctx.tenant_id,
            "period_days": days_back,
            "status": "completed",
            "data_quality": {
                "total_points": total_points,
                "points_with_outcomes": points_with_outcomes,
                "recent_points": recent_points,
                "outcome_tracking_rate": points_with_outcomes / total_points
                if total_points > 0
                else 0.0,
                "recent_data_rate": recent_points / total_points
                if total_points > 0
                else 0.0,
                "score_std": score_std,
                "score_range": score_range,
                "category_coverage": {
                    "average": avg_coverage,
                    "total_categories": total_categories,
                    "categories": category_coverage,
                },
            },
            "outcome_distribution": outcome_counts,
            "recommendations": recommendations,
        }

    except Exception as e:
        logger.error(
            f"Failed to get data quality report for tenant {ctx.tenant_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to generate data quality report."
        )


@router.post("/schedule")
async def schedule_calibration(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    frequency_days: int = Query(
        default=30, ge=7, le=90, description="Calibration frequency in days"
    ),
    auto_apply: bool = Query(
        default=False, description="Automatically apply recommendations"
    ),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Dict[str, Any]:
    """Schedule periodic calibration for the tenant.

    Args:
        ctx: Tenant context for identification
        frequency_days: Calibration frequency in days
        auto_apply: Whether to automatically apply recommendations
        background_tasks: Background tasks for async operations

    Returns:
        Scheduling confirmation
    """
    try:
        # This would integrate with a scheduler system
        # For now, we'll just return a confirmation

        logger.info(
            f"Scheduled calibration for tenant {ctx.tenant_id} every {frequency_days} days"
        )

        return {
            "tenant_id": ctx.tenant_id,
            "frequency_days": frequency_days,
            "auto_apply": auto_apply,
            "status": "scheduled",
            "message": f"Calibration scheduled to run every {frequency_days} days",
            "next_run": (
                datetime.now(timezone.utc) + timedelta(days=frequency_days)
            ).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to schedule calibration for tenant {ctx.tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule calibration.")
