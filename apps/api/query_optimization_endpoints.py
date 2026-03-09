"""
Query Optimization Endpoints for Phase 15.1 Database & Performance
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.api.dependencies import get_current_user, get_db_pool, get_tenant_id
from packages.backend.domain.query_optimizer import (
    create_query_optimizer,
)

router = APIRouter(prefix="/query-optimization", tags=["query-optimization"])


class QueryAnalysisRequest(BaseModel):
    """Query analysis request model."""

    query: str
    parameters: Optional[List[Any]] = None
    optimization_types: Optional[List[str]] = None


class QueryOptimizationRequest(BaseModel):
    """Query optimization request model."""

    query: str
    parameters: Optional[List[Any]] = None
    optimization_types: Optional[List[str]] = None


class IndexRecommendationRequest(BaseModel):
    """Index recommendation request model."""

    table_name: Optional[str] = None
    query_patterns: Optional[List[str]] = None
    recommendation_type: Optional[str] = None
    priority: Optional[str] = None


@router.post("/analyze")
async def analyze_query(
    request: QueryAnalysisRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Analyze a SQL query for optimization opportunities."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Convert optimization types if provided
        if request.optimization_types:
            from packages.backend.domain.query_optimizer import QueryOptimizationType

            try:
                [
                    QueryOptimizationType(opt) for opt in request.optimization_types
                ]
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid optimization type: {str(e)}"
                )

        # Analyze query
        analysis = await optimizer.analyze_query(
            tenant_id=tenant_id,
            query=request.query,
            parameters=request.parameters,
        )

        return {
            "analysis_id": analysis.id,
            "query": request.query,
            "normalized_query": analysis.normalized_query,
            "execution_plan": analysis.execution_plan,
            "performance_metrics": analysis.performance_metrics,
            "identified_issues": analysis.identified_issues,
            "optimization_opportunities": analysis.optimization_opportunities,
            "complexity_score": analysis.complexity_score,
            "estimated_cost": analysis.estimated_cost,
            "created_at": analysis.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze query: {str(e)}"
        )


@router.post("/optimize")
async def optimize_query(
    request: QueryOptimizationRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Generate query optimizations."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Convert optimization types if provided
        opt_types = None
        if request.optimization_types:
            from packages.backend.domain.query_optimizer import QueryOptimizationType

            try:
                opt_types = [
                    QueryOptimizationType(opt) for opt in request.optimization_types
                ]
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid optimization type: {str(e)}"
                )

        # Generate optimizations
        optimizations = await optimizer.optimize_query(
            tenant_id=tenant_id,
            query=request.query,
            optimization_types=opt_types,
        )

        return {
            "query": request.query,
            "optimizations": [
                {
                    "id": opt.id,
                    "optimization_type": opt.optimization_type.value,
                    "original_query": opt.original_query,
                    "optimized_query": opt.optimized_query,
                    "description": opt.description,
                    "performance_improvement": opt.performance_improvement,
                    "implementation_complexity": opt.implementation_complexity,
                    "priority": opt.priority.value,
                    "reasoning": opt.reasoning,
                }
                for opt in optimizations
            ],
            "total_optimizations": len(optimizations),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize query: {str(e)}"
        )


@router.post("/recommendations/indexes")
async def get_index_recommendations(
    request: IndexRecommendationRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get index recommendations."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Convert recommendation type if provided
        if request.recommendation_type:
            from packages.backend.domain.index_analyzer import IndexRecommendationType

            try:
                IndexRecommendationType(request.recommendation_type)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid recommendation type: {str(e)}"
                )

        # Get index recommendations
        recommendations = await optimizer.recommend_indexes(
            tenant_id=tenant_id,
            table_name=request.table_name,
            query_patterns=request.query_patterns,
        )

        return {
            "recommendations": [
                {
                    "id": rec.id,
                    "recommendation_type": rec.recommendation_type.value,
                    "index_name": rec.index_name,
                    "table_name": rec.table_name,
                    "column_names": rec.column_names,
                    "index_type": rec.index_type.value,
                    "priority": rec.priority,
                    "impact_score": rec.impact_score,
                    "implementation_cost": rec.implementation_cost,
                    "reasoning": rec.reasoning,
                    "sql_statement": rec.sql_statement,
                    "estimated_benefit": rec.estimated_benefit,
                    "risks": rec.risks,
                    "created_at": rec.created_at.isoformat(),
                }
                for rec in recommendations
            ],
            "total_recommendations": len(recommendations),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get index recommendations: {str(e)}"
        )


@router.post("/recommendations/queries")
async def get_query_recommendations(
    query: str,
    optimization_types: Optional[List[str]] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get query recommendations for a specific query."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Convert optimization types if provided
        opt_types = None
        if optimization_types:
            from packages.backend.domain.query_optimizer import QueryOptimizationType

            try:
                opt_types = [QueryOptimizationType(opt) for opt in optimization_types]
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid optimization type: {str(e)}"
                )

        # Generate optimizations for the query
        optimizations = await optimizer.optimize_query(
            tenant_id=tenant_id,
            query=query,
            optimization_types=opt_types,
        )

        return {
            "query": query,
            "optimizations": [
                {
                    "id": opt.id,
                    "optimization_type": opt.optimization_type.value,
                    "original_query": opt.original_query,
                    "optimized_query": opt.optimized_query,
                    "description": opt.description,
                    "performance_improvement": opt.performance_improvement,
                    "implementation_complexity": opt.implementation_complexity,
                    "priority": opt.priority.value,
                    "reasoning": opt.reasoning,
                }
                for opt in optimizations
            ],
            "total_optimizations": len(optimizations),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get query recommendations: {str(e)}"
        )


@router.get("/analysis/history")
async def get_query_analysis_history(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get query analysis history."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Get analysis history
        history = await optimizer.get_query_analyses(tenant_id, time_period_hours)

        return {
            "analyses": [
                {
                    "id": analysis.id,
                    "query": analysis.original_query,
                    "normalized_query": analysis.normalized_query,
                    "complexity_score": analysis.complexity_score,
                    "estimated_cost": analysis.estimated_cost,
                    "identified_issues": analysis.identified_issues,
                    "optimization_opportunities": analysis.optimization_opportunities,
                    "created_at": analysis.created_at.isoformat(),
                }
                for analysis in history
            ],
            "total_analyses": len(history),
            "period_hours": time_period_hours,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get query analysis history: {str(e)}"
        )


@router.get("/recommendations/history")
async def get_optimization_recommendations(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get optimization recommendations history."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Get optimization history
        history = await optimizer.get_query_optimizations(tenant_id, time_period_hours)

        return {
            "optimizations": [
                {
                    "id": opt.id,
                    "query_id": opt.query_id,
                    "optimization_type": opt.optimization_type.value,
                    "original_query": opt.original_query,
                    "optimized_query": opt.optimized_query,
                    "description": opt.description,
                    "performance_improvement": opt.performance_improvement,
                    "implementation_complexity": opt.implementation_complexity,
                    "priority": opt.priority.value,
                    "reasoning": opt.reasoning,
                    "created_at": opt.created_at.isoformat(),
                }
                for opt in history
            ],
            "total_optimizations": len(history),
            "period_hours": time_period_hours,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get optimization recommendations: {str(e)}",
        )


@router.get("/statistics")
async def get_optimization_statistics(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get optimization statistics."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Get optimization report
        report = await optimizer.get_optimization_report(tenant_id, time_period_hours)

        return report

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get optimization statistics: {str(e)}"
        )


@router.post("/slow-queries")
async def get_slow_queries(
    limit: int = Query(default=10, ge=1, le=100),
    min_execution_time: float = Query(default=1000.0),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get slow queries from pg_stat_statements."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Get slow queries
        slow_queries = await optimizer.get_slow_queries(limit, min_execution_time)

        return {
            "slow_queries": slow_queries,
            "total_slow_queries": len(slow_queries),
            "min_execution_time_ms": min_execution_time,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get slow queries: {str(e)}"
        )


@router.get("/query-patterns")
async def get_query_patterns(
    table_name: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get common query patterns."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Get query patterns
        patterns = await optimizer.get_query_patterns(table_name, limit)

        return {
            "patterns": patterns,
            "table_name": table_name,
            "total_patterns": len(patterns),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get query patterns: {str(e)}"
        )


@router.post("/explain")
async def explain_query(
    query: str,
    parameters: Optional[List[Any]] = None,
    analyze: bool = True,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get query execution plan."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Get execution plan
        plan = await optimizer.get_execution_plan(query, parameters)

        # Analyze the plan if requested
        analysis = None
        if analyze:
            analysis = await optimizer.analyze_execution_plan(plan)

        return {
            "query": query,
            "execution_plan": plan,
            "analysis": analysis,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get query execution plan: {str(e)}"
        )


@router.get("/performance/trends")
async def get_performance_trends(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get query performance trends."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Get performance trends
        trends = await optimizer.get_performance_trends(tenant_id, time_period_hours)

        return trends

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance trends: {str(e)}"
        )


@router.post("/health")
async def health_check(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Health check for query optimization system."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Check database connection
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
                db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Check optimizer health
        try:
            # Test basic functionality
            test_query = "SELECT 1"
            await optimizer.get_execution_plan(test_query, [])
            optimizer_status = "healthy"
        except Exception:
            optimizer_status = "unhealthy"

        # Overall status
        overall_status = "healthy"
        if db_status != "healthy" or optimizer_status != "healthy":
            overall_status = "degraded"

        return {
            "status": overall_status,
            "database": db_status,
            "optimizer": optimizer_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/export")
async def export_optimization_data(
    format: str = Query(default="json", regex="^(json|csv)$"),
    time_period_hours: int = Query(default=24, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Any:
    """Export optimization data."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Get optimization report
        report = await optimizer.get_optimization_report(tenant_id, time_period_hours)

        if format == "json":
            return JSONResponse(
                content=report,
                headers={
                    "Content-Disposition": f"attachment; filename=query_optimization_{time_period_hours}hrs.json"
                },
            )
        elif format == "csv":
            # Convert to CSV format
            csv_data = _convert_optimization_to_csv(report)

            from fastapi.responses import Response

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=query_optimization_{time_period_hours}hrs.csv"
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export optimization data: {str(e)}"
        )


def _convert_optimization_to_csv(data: Dict[str, Any]) -> str:
    """Convert optimization data to CSV format."""
    try:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Query",
                "Optimization Type",
                "Original Query",
                "Optimized Query",
                "Performance Improvement",
                "Implementation Complexity",
                "Priority",
                "Reasoning",
                "Created At",
            ]
        )

        # Write optimization data
        if "optimizations" in data:
            for opt in data["optimizations"]:
                writer.writerow(
                    [
                        opt.get("query", ""),
                        opt.get("optimization_type", ""),
                        opt.get("original_query", ""),
                        opt.get("optimized_query", ""),
                        opt.get("performance_improvement", 0.0),
                        opt.get("implementation_complexity", ""),
                        opt.get("priority", ""),
                        opt.get("reasoning", ""),
                        opt.get("created_at", ""),
                    ]
                )

        return output.getvalue()

    except Exception as e:
        return f"Error converting to CSV: {str(e)}"


# create_query_optimizer imported from packages.backend.domain.query_optimizer
