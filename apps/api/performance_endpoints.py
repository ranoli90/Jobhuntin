"""
Performance Endpoints for Phase 15.1 Database & Performance
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from apps.api.dependencies import get_current_user, get_db_pool, get_tenant_id
from packages.backend.domain.cache_manager import create_cache_manager
from packages.backend.domain.connection_pool_manager import create_connection_pool_manager
from packages.backend.domain.database_performance_manager import create_database_performance_manager
from packages.backend.domain.index_analyzer import create_index_analyzer
from packages.backend.domain.performance_monitor import create_performance_monitor
from packages.backend.domain.query_optimizer import create_query_optimizer

router = APIRouter(prefix="/performance", tags=["performance"])


class MetricRequest(BaseModel):
    """Metric request model."""

    metric_type: str
    metric_category: str
    name: str
    value: float
    unit: str
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ThresholdRequest(BaseModel):
    """Threshold request model."""

    metric_name: str
    metric_type: str
    warning_threshold: float
    critical_threshold: float
    comparison_operator: str = "gt"
    enabled: bool = True


class QueryAnalysisRequest(BaseModel):
    """Query analysis request model."""

    query: str
    parameters: Optional[List[Any]] = None


class IndexAnalysisRequest(BaseModel):
    """Index analysis request model."""

    table_name: str
    include_usage_stats: bool = True


@router.post("/metrics/collect")
async def collect_metric(
    request: MetricRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Collect a performance metric."""
    try:
        # Create performance monitor
        monitor = create_performance_monitor(db_pool)

        # Convert string enums to actual enums
        from packages.backend.domain.performance_monitor import MetricCategory, MetricType

        metric_type = MetricType(request.metric_type)
        metric_category = MetricCategory(request.metric_category)

        # Collect metric
        metric = await monitor.collect_metric(
            tenant_id=tenant_id,
            metric_type=metric_type,
            metric_category=metric_category,
            name=request.name,
            value=request.value,
            unit=request.unit,
            metadata=request.metadata,
            tags=request.tags,
        )

        return {
            "success": True,
            "metric_id": metric.id,
            "timestamp": metric.timestamp.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to collect metric: {str(e)}"
        )


@router.post("/thresholds")
async def create_threshold(
    request: ThresholdRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Create a performance threshold."""
    try:
        # Create performance monitor
        monitor = create_performance_monitor(db_pool)

        # Convert string enum to actual enum
        from packages.backend.domain.performance_monitor import MetricType

        metric_type = MetricType(request.metric_type)

        # Create threshold
        threshold = await monitor.create_threshold(
            tenant_id=tenant_id,
            metric_name=request.metric_name,
            metric_type=metric_type,
            warning_threshold=request.warning_threshold,
            critical_threshold=request.critical_threshold,
            comparison_operator=request.comparison_operator,
            enabled=request.enabled,
        )

        return {
            "success": True,
            "threshold_id": threshold.id,
            "metric_name": request.metric_name,
            "warning_threshold": request.warning_threshold,
            "critical_threshold": request.critical_threshold,
            "comparison_operator": request.comparison_operator,
            "enabled": request.enabled,
            "created_at": threshold.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create threshold: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics(
    metric_type: Optional[str] = None,
    metric_category: Optional[str] = None,
    time_period_hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get performance metrics."""
    try:
        # Create performance monitor
        monitor = create_performance_monitor(db_pool)

        # Convert string enums to actual enums if provided
        metric_type_enum = None
        if metric_type:
            from packages.backend.domain.performance_monitor import MetricType

            try:
                metric_type_enum = MetricType(metric_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid metric type: {metric_type}"
                )

        metric_category_enum = None
        if metric_category:
            from packages.backend.domain.performance_monitor import MetricCategory

            try:
                metric_category_enum = MetricCategory(metric_category)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric category: {metric_category}",
                )

        # Get metrics
        metrics = await monitor.get_metrics(
            tenant_id=tenant_id,
            metric_type=metric_type_enum,
            metric_category=metric_category_enum,
            time_period_hours=time_period_hours,
            limit=limit,
        )

        return {
            "metrics": [
                {
                    "id": metric.id,
                    "tenant_id": metric.tenant_id,
                    "metric_type": metric.metric_type.value,
                    "metric_category": metric.metric_category.value,
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                    "metadata": metric.metadata,
                    "tags": metric.tags,
                }
                for metric in metrics
            ],
            "total_count": len(metrics),
            "filters": {
                "metric_type": metric_type,
                "metric_category": metric_category,
                "time_period_hours": time_period_hours,
                "limit": limit,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    time_period_hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get performance alerts."""
    try:
        # Create performance monitor
        monitor = create_performance_monitor(db_pool)

        # Convert string enum to actual enum if provided
        severity_enum = None
        if severity:
            from packages.backend.domain.performance_monitor import AlertSeverity

            try:
                severity_enum = AlertSeverity(severity)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid severity: {severity}"
                )

        # Get alerts
        alerts = await monitor.get_alerts(
            tenant_id=tenant_id,
            severity=severity_enum,
            resolved=resolved,
            time_period_hours=time_period_hours,
            limit=limit,
        )

        return {
            "alerts": [
                {
                    "id": alert.id,
                    "tenant_id": alert.tenant_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at.isoformat()
                    if alert.resolved_at
                    else None,
                    "metadata": alert.metadata,
                }
                for alert in alerts
            ],
            "total_count": len(alerts),
            "filters": {
                "severity": severity,
                "resolved": resolved,
                "time_period_hours": time_period_hours,
                "limit": limit,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/dashboard")
async def get_performance_dashboard(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive performance dashboard."""
    try:
        # Create performance monitor
        monitor = create_performance_monitor(db_pool)

        # Get dashboard
        dashboard = await monitor.get_dashboard(
            tenant_id=tenant_id,
            time_period_hours=time_period_hours,
        )

        return dashboard

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard: {str(e)}"
        )


@router.get("/system-metrics")
async def get_system_metrics(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get current system metrics."""
    try:
        # Create performance monitor
        monitor = create_performance_monitor(db_pool)

        # Get system metrics
        metrics = await monitor.get_system_metrics()

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get("/database-metrics")
async def get_database_metrics(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get database performance metrics."""
    try:
        # Create performance monitor
        monitor = create_performance_monitor(db_pool)

        # Get database metrics
        metrics = await monitor.get_database_metrics()

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get database metrics: {str(e)}"
        )


@router.post("/database/performance/analyze")
async def analyze_database_performance(
    tenant_id: str,
    time_period_hours: int = Query(default=24, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Analyze database performance."""
    try:
        # Create database performance manager
        db_manager = create_database_performance_manager(db_pool)

        # Analyze performance
        analysis = await db_manager.analyze_database_performance(
            tenant_id=tenant_id,
            time_period_hours=time_period_hours,
        )

        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze database performance: {str(e)}"
        )


@router.post("/database/optimize")
async def optimize_database(
    tenant_id: str,
    optimization_id: str,
    dry_run: bool = Query(default=True),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Execute database optimization."""
    try:
        # Create database performance manager
        db_manager = create_database_performance_manager(db_pool)

        # Execute optimization
        result = await db_manager.optimize_database(
            tenant_id=tenant_id,
            optimization_id=optimization_id,
            dry_run=dry_run,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize database: {str(e)}"
        )


@router.post("/queries/analyze")
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


@router.post("/queries/optimize")
async def optimize_query(
    request: QueryAnalysisRequest,
    optimization_types: Optional[List[str]] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Generate query optimizations."""
    try:
        # Create query optimizer
        optimizer = create_query_optimizer(db_pool)

        # Convert optimization types
        opt_types = None
        if optimization_types:
            from packages.backend.domain.query_optimizer import QueryOptimizationType

            opt_types = [QueryOptimizationType(opt) for opt in optimization_types]

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


@router.post("/indexes/analyze")
async def analyze_indexes(
    request: IndexAnalysisRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Analyze table indexes."""
    try:
        # Create index analyzer
        analyzer = create_index_analyzer(db_pool)

        # Analyze indexes
        analysis = await analyzer.analyze_table_indexes(
            tenant_id=tenant_id,
            table_name=request.table_name,
            include_usage_stats=request.include_usage_stats,
        )

        return {
            "analysis_id": analysis.id,
            "table_name": analysis.table_name,
            "total_indexes": analysis.total_indexes,
            "unused_indexes": [
                {
                    "index_name": index.index_name,
                    "index_type": index.index_type.value,
                    "column_names": index.column_names,
                    "size_bytes": index.size_bytes,
                    "scans": index.scans,
                    "status": index.status.value,
                }
                for index in analysis.unused_indexes
            ],
            "underutilized_indexes": [
                {
                    "index_name": index.index_name,
                    "index_type": index.index_type.value,
                    "column_names": index.column_names,
                    "size_bytes": index.size_bytes,
                    "scans": index.scans,
                    "status": index.status.value,
                }
                for index in analysis.underutilized_indexes
            ],
            "missing_indexes": [
                {
                    "id": rec.id,
                    "recommendation_type": rec.recommendation_type.value,
                    "table_name": rec.table_name,
                    "column_names": rec.column_names,
                    "index_type": rec.index_type.value,
                    "priority": rec.priority,
                    "impact_score": rec.impact_score,
                    "implementation_cost": rec.implementation_cost,
                    "reasoning": rec.reasoning,
                    "sql_statement": rec.sql_statement,
                }
                for rec in analysis.missing_indexes
            ],
            "fragmentation_score": analysis.fragmentation_score,
            "optimization_potential": analysis.optimization_potential,
            "created_at": analysis.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze indexes: {str(e)}"
        )


@router.post("/indexes/recommend")
async def get_index_recommendations(
    tenant_id: str,
    table_name: Optional[str] = None,
    recommendation_type: Optional[str] = None,
    priority: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Get index recommendations."""
    try:
        # Create index analyzer
        analyzer = create_index_analyzer(db_pool)

        # Convert recommendation type if provided
        rec_type = None
        if recommendation_type:
            from packages.backend.domain.index_analyzer import IndexRecommendationType

            try:
                rec_type = IndexRecommendationType(recommendation_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid recommendation type: {recommendation_type}",
                )

        # Get recommendations
        recommendations = await analyzer.get_index_recommendations(
            tenant_id=tenant_id,
            table_name=table_name,
            recommendation_type=rec_type,
            priority=priority,
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


@router.post("/indexes/implement")
async def implement_index_recommendation(
    tenant_id: str,
    recommendation_id: str,
    dry_run: bool = Query(default=True),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Implement an index recommendation."""
    try:
        # Create index analyzer
        analyzer = create_index_analyzer(db_pool)

        # Implement recommendation
        result = await analyzer.implement_recommendation(
            tenant_id=tenant_id,
            recommendation_id=recommendation_id,
            dry_run=dry_run,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to implement index recommendation: {str(e)}",
        )


@router.get("/cache/metrics")
async def get_cache_metrics(
    cache_type: Optional[str] = None,
    time_period_hours: int = Query(default=1, ge=1, le=24),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get cache performance metrics."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Get cache health
        health = await cache_manager.get_cache_health()

        # Get cache stats
        stats = await cache_manager.get_cache_stats(cache_type)

        return {
            "health": health,
            "stats": stats,
            "cache_type": cache_type,
            "period_hours": time_period_hours,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache metrics: {str(e)}"
        )


@router.post("/cache/warm")
async def warm_cache(
    data_loader: str,  # This would be a function name
    keys: List[str],
    ttl_seconds: Optional[int] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Warm cache with data."""
    try:
        # Create cache manager
        create_cache_manager()

        # This is a placeholder - in practice, data_loader would be a function
        # For now, return empty results
        return {
            "results": {},
            "message": "Cache warming not implemented yet",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(
    cache_level: Optional[str] = None,
    pattern: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Clear cache entries."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Clear cache
        success = await cache_manager.clear_cache(cache_level, pattern)

        return {
            "success": success,
            "cache_level": cache_level,
            "pattern": pattern,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/connection-pools/metrics")
async def get_connection_pool_metrics(
    pool_name: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get connection pool metrics."""
    try:
        # Create connection pool manager
        pool_manager = create_connection_pool_manager()

        # Get system metrics
        system_metrics = await pool_manager.get_system_metrics()

        # Get pool metrics
        pool_metrics = await pool_manager.get_pool_metrics(pool_name)

        return {
            "system_metrics": system_metrics,
            "pool_metrics": pool_metrics,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get connection pool metrics: {str(e)}"
        )


@router.post("/connection-pools/optimize")
async def optimize_connection_pool(
    pool_name: str,
    target_size: Optional[int] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Optimize connection pool size."""
    try:
        # Create connection pool manager
        pool_manager = create_connection_pool_manager()

        # Optimize pool
        success = await pool_manager.optimize_pool(pool_name, target_size)

        return {
            "success": success,
            "pool_name": pool_name,
            "target_size": target_size,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize connection pool: {str(e)}"
        )


@router.get("/health")
async def health_check(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Health check for performance monitoring system."""
    try:
        # Create performance monitor
        create_performance_monitor(db_pool)

        # Check database connection
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
                db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Check cache connection
        try:
            cache_manager = create_cache_manager()
            cache_health = await cache_manager.get_cache_health()
            cache_status = cache_health.get("overall", {}).get("status", "unknown")
        except Exception:
            cache_status = "unhealthy"

        # Overall status
        overall_status = "healthy"
        if db_status != "healthy" or cache_status != "healthy":
            overall_status = "degraded"

        return {
            "status": overall_status,
            "database": db_status,
            "cache": cache_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# All factory functions imported at top of file
