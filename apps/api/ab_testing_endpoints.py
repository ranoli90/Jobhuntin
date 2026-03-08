"""
A/B Testing Endpoints for Phase 14.1 User Experience
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel
import json

from apps.api.dependencies import get_db_pool, get_current_user, get_tenant_id
from packages.backend.domain.ab_testing_manager import (
    MetricType,
    create_ab_testing_manager,
)

router = APIRouter(prefix="/ab-testing", tags=["ab-testing"])


class ExperimentRequest(BaseModel):
    """Experiment request model."""

    name: str
    description: str
    variants_config: List[Dict[str, Any]]
    target_metrics: List[str]
    sample_size: int = 1000
    duration_days: int = 30
    target_audience: Optional[Dict[str, Any]] = None
    ai_model_config: Optional[Dict[str, Any]] = None
    traffic_allocation: float = 1.0


class VariantAssignmentRequest(BaseModel):
    """Variant assignment request model."""

    user_attributes: Optional[Dict[str, Any]] = None


@router.post("/experiments")
async def create_experiment(
    experiment: ExperimentRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Create a new A/B testing experiment."""
    try:
        # Validate metrics
        valid_metrics = [metric.value for metric in MetricType]
        for metric in experiment.target_metrics:
            if metric not in valid_metrics:
                raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")

        # Convert metrics to enum
        target_metrics = [MetricType(metric) for metric in experiment.target_metrics]

        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Create experiment
        created_experiment = await ab_manager.create_experiment(
            name=experiment.name,
            description=experiment.description,
            variants_config=experiment.variants_config,
            target_metrics=target_metrics,
            sample_size=experiment.sample_size,
            duration_days=experiment.duration_days,
            target_audience=experiment.target_audience,
            ai_model_config=experiment.ai_model_config,
            traffic_allocation=experiment.traffic_allocation,
        )

        return {
            "success": True,
            "experiment_id": created_experiment.id,
            "name": created_experiment.name,
            "status": created_experiment.status.value,
            "sample_size": created_experiment.sample_size,
            "duration_days": created_experiment.duration_days,
            "target_metrics": [
                metric.value for metric in created_experiment.target_metrics
            ],
            "variants": [
                {
                    "id": variant.id,
                    "name": variant.name,
                    "description": variant.description,
                    "variant_type": variant.variant_type,
                    "traffic_weight": variant.traffic_weight,
                    "is_control": variant.is_control,
                    "is_active": variant.is_active,
                }
                for variant in created_experiment.variants
            ],
            "created_at": created_experiment.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create experiment: {str(e)}"
        )


@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Start an A/B testing experiment."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Start experiment
        success = await ab_manager.start_experiment(experiment_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to start experiment")

        return {
            "success": True,
            "experiment_id": experiment_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start experiment: {str(e)}"
        )


@router.post("/experiments/{experiment_id}/complete")
async def complete_experiment(
    experiment_id: str,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Complete an experiment and determine winner."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Complete experiment
        analysis = await ab_manager.complete_experiment(experiment_id)

        return {
            "success": True,
            "experiment_id": experiment_id,
            "analysis_id": analysis.id,
            "winner": analysis.winner,
            "recommended_action": analysis.recommended_action,
            "is_significant": analysis.is_significant,
            "p_value": analysis.p_value,
            "effect_size": analysis.effect_size,
            "confidence_level": analysis.confidence_level,
            "confidence_interval": analysis.confidence_interval,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to complete experiment: {str(e)}"
        )


@router.post("/assign-variant")
async def assign_user_to_variant(
    experiment_id: str,
    request: VariantAssignmentRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Assign user to experiment variant."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Assign user to variant
        variant = await ab_manager.assign_user_to_variant(
            user_id=current_user["id"],
            experiment_id=experiment_id,
            user_attributes=request.user_attributes,
        )

        if not variant:
            return {
                "success": False,
                "message": "User not eligible for experiment or experiment not running",
                "variant": None,
            }

        return {
            "success": True,
            "experiment_id": experiment_id,
            "variant": {
                "id": variant.id,
                "name": variant.name,
                "description": variant.description,
                "variant_type": variant.variant_type,
                "configuration": variant.configuration,
                "is_control": variant.is_control,
                "traffic_weight": variant.traffic_weight,
            },
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to assign user to variant: {str(e)}"
        )


@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    user_id: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get experiment results."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Get results
        results = await ab_manager.get_experiment_results(
            experiment_id=experiment_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        return {
            "experiment_id": experiment_id,
            "results": [
                {
                    "id": result.id,
                    "variant_id": result.variant_id,
                    "user_id": result.user_id,
                    "metrics": result.metrics,
                    "created_at": result.created_at.isoformat(),
                }
                for result in results
            ],
            "total_count": len(results),
            "limit": limit,
            "offset": offset,
            "filters": {
                "user_id": user_id,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get experiment results: {str(e)}"
        )


@router.get("/analytics")
async def get_experiment_analytics(
    time_period_days: int = Query(default=30, ge=1, le=365),
    experiment_id: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive experiment analytics."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Get analytics
        analytics = await ab_manager.get_experiment_analytics(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            experiment_id=experiment_id,
        )

        return analytics

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get experiment analytics: {str(e)}"
        )


@router.get("/user-experiments")
async def get_user_experiments(
    limit: int = Query(default=10, ge=1, le=100),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get experiments for a user."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Get user experiments
        experiments = await ab_manager.get_user_experiments(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            limit=limit,
        )

        return {
            "user_id": current_user["id"],
            "experiments": experiments,
            "total_count": len(experiments),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user experiments: {str(e)}"
        )


@router.get("/experiments")
async def get_experiments(
    status: Optional[str] = Query(
        None, regex="^(draft|running|paused|completed|cancelled)$"
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get experiments with filtering."""
    try:
        # Build query
        query = """
            SELECT * FROM experiments 
            WHERE tenant_id = $1
        """
        params = [tenant_id]

        if status:
            query += " AND status = $2"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT $3 OFFSET $4"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            experiments = []
            for row in results:
                experiment = {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "status": row[3],
                    "traffic_allocation": row[4],
                    "sample_size": row[5],
                    "duration_days": row[6],
                    "target_metrics": json.loads(row[7]) if row[7] else [],
                    "target_audience": json.loads(row[8]) if row[8] else {},
                    "ai_model_config": json.loads(row[9]) if row[9] else {},
                    "created_at": row[10].isoformat(),
                    "updated_at": row[11].isoformat(),
                }
                experiments.append(experiment)

        # Get variants for each experiment
        for experiment in experiments:
            variants_query = """
                SELECT * FROM experiment_variants 
                WHERE experiment_id = $1 AND is_active = true
                ORDER BY created_at ASC
            """

            async with db_pool.acquire() as conn:
                variant_results = await conn.fetch(variants_query, experiment["id"])

                variants = []
                for variant_row in variant_results:
                    variant = {
                        "id": variant_row[0],
                        "experiment_id": variant_row[1],
                        "name": variant_row[2],
                        "description": variant_row[3],
                        "variant_type": variant_row[4],
                        "configuration": json.loads(variant_row[5])
                        if variant_row[5]
                        else {},
                        "traffic_weight": variant_row[6],
                        "is_control": variant_row[7],
                        "is_active": variant_row[8],
                        "created_at": variant_row[9].isoformat(),
                    }
                    variants.append(variant)

                experiment["variants"] = variants

        return {
            "experiments": experiments,
            "total_count": len(experiments),
            "limit": limit,
            "offset": offset,
            "filters": {
                "status": status,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get experiments: {str(e)}"
        )


@router.get("/experiments/{experiment_id}")
async def get_experiment_by_id(
    experiment_id: str,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get experiment by ID."""
    try:
        # Get experiment
        query = """
            SELECT * FROM experiments 
            WHERE id = $1 AND tenant_id = $2
        """

        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, experiment_id, tenant_id)

            if not result:
                raise HTTPException(status_code=404, detail="Experiment not found")

            experiment = {
                "id": result[0],
                "name": result[1],
                "description": result[2],
                "status": result[3],
                "traffic_allocation": result[4],
                "sample_size": result[5],
                "duration_days": result[6],
                "target_metrics": json.loads(result[7]) if result[7] else [],
                "target_audience": json.loads(result[8]) if result[8] else {},
                "ai_model_config": json.loads(result[9]) if result[9] else {},
                "created_at": result[10].isoformat(),
                "updated_at": result[11].isoformat(),
            }

        # Get variants
        variants_query = """
            SELECT * FROM experiment_variants 
            WHERE experiment_id = $1
            ORDER BY created_at ASC
        """

        async with db_pool.acquire() as conn:
            variant_results = await conn.fetch(variants_query, experiment_id)

            variants = []
            for variant_row in variant_results:
                variant = {
                    "id": variant_row[0],
                    "experiment_id": variant_row[1],
                    "name": variant_row[2],
                    "description": variant_row[3],
                    "variant_type": variant_row[4],
                    "configuration": json.loads(variant_row[5])
                    if variant_row[5]
                    else {},
                    "traffic_weight": variant_row[6],
                    "is_control": variant_row[7],
                    "is_active": variant_row[8],
                    "created_at": variant_row[9].isoformat(),
                }
                variants.append(variant)

            experiment["variants"] = variants

        # Get statistical analyses
        analyses_query = """
            SELECT * FROM statistical_analyses 
            WHERE experiment_id = $1
            ORDER BY created_at DESC
        """

        async with db_pool.acquire() as conn:
            analysis_results = await conn.fetch(analyses_query, experiment_id)

            analyses = []
            for analysis_row in analysis_results:
                analysis = {
                    "id": analysis_row[0],
                    "experiment_id": analysis_row[1],
                    "variant_a_id": analysis_row[2],
                    "variant_b_id": analysis_row[3],
                    "metric": analysis_row[4],
                    "variant_a_mean": analysis_row[5],
                    "variant_b_mean": analysis_row[6],
                    "variant_a_std": analysis_row[7],
                    "variant_b_std": analysis_row[8],
                    "variant_a_count": analysis_row[9],
                    "variant_b_count": analysis_row[10],
                    "p_value": analysis_row[11],
                    "confidence_level": analysis_row[12],
                    "confidence_interval": json.loads(analysis_row[13])
                    if analysis_row[13]
                    else [],
                    "is_significant": analysis_row[14],
                    "effect_size": analysis_row[15],
                    "winner": analysis_row[16],
                    "recommended_action": analysis_row[17],
                    "created_at": analysis_row[18].isoformat(),
                }
                analyses.append(analysis)

            experiment["statistical_analyses"] = analyses

        return experiment

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get experiment: {str(e)}"
        )


@router.get("/metrics/types")
async def get_metric_types(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get available metric types."""
    try:
        return {
            "metric_types": [
                {
                    "value": metric.value,
                    "name": metric.value.replace("_", " ").title(),
                }
                for metric in MetricType
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric types: {str(e)}"
        )


@router.get("/dashboard")
async def get_ab_testing_dashboard(
    time_period_days: int = Query(default=30, ge=1, le=365),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive A/B testing dashboard."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Get analytics
        analytics = await ab_manager.get_experiment_analytics(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        # Get recent experiments
        recent_experiments_query = """
            SELECT id, name, status, created_at, updated_at
            FROM experiments 
            WHERE tenant_id = $1
            ORDER BY updated_at DESC
            LIMIT 10
        """

        async with db_pool.acquire() as conn:
            recent_results = await conn.fetch(recent_experiments_query, tenant_id)

            recent_experiments = []
            for row in recent_results:
                experiment = {
                    "id": row[0],
                    "name": row[1],
                    "status": row[2],
                    "created_at": row[3].isoformat(),
                    "updated_at": row[4].isoformat(),
                }
                recent_experiments.append(experiment)

        # Get user's current experiments
        user_experiments = await ab_manager.get_user_experiments(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            limit=5,
        )

        return {
            "period_days": time_period_days,
            "analytics": analytics,
            "recent_experiments": recent_experiments,
            "user_experiments": user_experiments["experiments"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get A/B testing dashboard: {str(e)}"
        )


@router.get("/export/experiments")
async def export_experiments(
    format: str = Query(default="json", regex="^(json|csv)$"),
    time_period_days: int = Query(default=30, ge=1, le=365),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Any:
    """Export experiment data."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Get analytics
        analytics = await ab_manager.get_experiment_analytics(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        if format == "json":
            return JSONResponse(
                content=analytics,
                headers={
                    "Content-Disposition": f"attachment; filename=experiments_{time_period_days}days.json"
                },
            )
        elif format == "csv":
            # Convert to CSV format
            csv_data = _convert_experiments_to_csv(analytics)

            from fastapi.responses import Response

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=experiments_{time_period_days}days.csv"
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export experiments: {str(e)}"
        )


def _convert_experiments_to_csv(data: Dict[str, Any]) -> str:
    """Convert experiment data to CSV format."""
    try:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Metric", "Value", "Category"])

        # Write experiment statistics
        if "experiment_statistics" in data:
            exp_stats = data["experiment_statistics"]
            writer.writerow(
                [
                    "Total Experiments",
                    exp_stats.get("total_experiments", 0),
                    "Experiments",
                ]
            )
            writer.writerow(
                [
                    "Completed Experiments",
                    exp_stats.get("completed_experiments", 0),
                    "Experiments",
                ]
            )
            writer.writerow(
                [
                    "Running Experiments",
                    exp_stats.get("running_experiments", 0),
                    "Experiments",
                ]
            )
            writer.writerow(
                [
                    "Average Sample Size",
                    exp_stats.get("avg_sample_size", 0),
                    "Experiments",
                ]
            )
            writer.writerow(
                ["Average Duration", exp_stats.get("avg_duration", 0), "Experiments"]
            )

        # Write variant statistics
        if "variant_statistics" in data:
            variant_stats = data["variant_statistics"]
            writer.writerow(
                ["Total Variants", variant_stats.get("total_variants", 0), "Variants"]
            )
            writer.writerow(
                ["Active Variants", variant_stats.get("active_variants", 0), "Variants"]
            )
            writer.writerow(
                [
                    "Average Traffic Weight",
                    variant_stats.get("avg_traffic_weight", 0),
                    "Variants",
                ]
            )

        # Write assignment statistics
        if "assignment_statistics" in data:
            assignment_stats = data["assignment_statistics"]
            writer.writerow(
                [
                    "Total Assignments",
                    assignment_stats.get("total_assignments", 0),
                    "Assignments",
                ]
            )
            writer.writerow(
                ["Unique Users", assignment_stats.get("unique_users", 0), "Assignments"]
            )
            writer.writerow(
                [
                    "Experiments Participated",
                    assignment_stats.get("experiments_participated", 0),
                    "Assignments",
                ]
            )

        # Write performance metrics
        if "performance_metrics" in data:
            perf_metrics = data["performance_metrics"]
            writer.writerow(
                [
                    "Average Processing Time",
                    perf_metrics.get("avg_processing_time", 0),
                    "Performance",
                ]
            )
            writer.writerow(
                [
                    "Average Success Rate",
                    perf_metrics.get("avg_success_rate", 0),
                    "Performance",
                ]
            )
            writer.writerow(
                ["Total Errors", perf_metrics.get("total_errors", 0), "Performance"]
            )

        return output.getvalue()

    except Exception as e:
        return f"Error converting to CSV: {str(e)}"


@router.get("/health")
async def health_check(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Health check for A/B testing system."""
    try:
        # Create A/B testing manager
        ab_manager = create_ab_testing_manager(db_pool)

        # Test database connection
        try:
            async with db_pool.acquire() as conn:
                await conn.fetch("SELECT 1")
                db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Test experiments
        try:
            query = "SELECT COUNT(*) FROM experiments WHERE tenant_id = $1"
            async with db_pool.acquire() as conn:
                await conn.fetchval(query, tenant_id)
                experiments_status = "healthy"
        except Exception:
            experiments_status = "unhealthy"

        return {
            "status": "healthy"
            if db_status == "healthy" and experiments_status == "healthy"
            else "unhealthy",
            "database": db_status,
            "experiments": experiments_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
