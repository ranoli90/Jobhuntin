"""
UX Metrics Collector Endpoints for Phase 14.1 User Experience
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.api.dependencies import get_current_user, get_db_pool, get_tenant_id
from packages.backend.domain.ux_metrics_collector import (
    MetricCategory,
    MetricType,
    create_ux_metrics_collector,
)

router = APIRouter(prefix="/ux-metrics", tags=["ux-metrics"])


class MetricRequest(BaseModel):
    """Metric collection request model."""

    metric_type: str
    metric_category: str
    metric_name: str
    value: float
    unit: str
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class MetricDefinitionRequest(BaseModel):
    """Metric definition request model."""

    name: str
    description: str
    metric_type: str
    metric_category: str
    unit: str
    calculation_method: str
    thresholds: Optional[Dict[str, float]] = None
    is_active: bool = True


@router.post("/collect")
async def collect_metric(
    metric: MetricRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Collect a UX metric."""
    try:
        # Validate metric type and category
        try:
            metric_type = MetricType(metric.metric_type)
            metric_category = MetricCategory(metric.metric_category)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid metric type or category: {str(e)}"
            )

        # Create metrics collector
        collector = create_ux_metrics_collector(db_pool)

        # Get session ID from user context
        session_id = current_user.get("session_id", str(current_user["id"]))

        # Collect metric
        ux_metric = await collector.collect_metric(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            session_id=session_id,
            metric_type=metric_type,
            metric_category=metric_category,
            metric_name=metric.metric_name,
            value=metric.value,
            unit=metric.unit,
            context=metric.context,
            metadata=metric.metadata,
        )

        if not ux_metric:
            raise HTTPException(status_code=400, detail="Metric not found or inactive")

        return {
            "success": True,
            "metric_id": ux_metric.id,
            "metric_name": ux_metric.metric_name,
            "value": ux_metric.value,
            "unit": ux_metric.unit,
            "collected_at": ux_metric.timestamp.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to collect UX metric: {str(e)}"
        )


@router.get("/summary")
async def get_metrics_summary(
    time_period_hours: int = Query(default=24, ge=1, le=720),
    metric_type: Optional[str] = None,
    metric_category: Optional[str] = None,
    user_id: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive UX metrics summary."""
    try:
        # Create metrics collector
        collector = create_ux_metrics_collector(db_pool)

        # Convert string to enum if provided
        metric_type_enum = None
        if metric_type:
            try:
                metric_type_enum = MetricType(metric_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid metric type: {metric_type}"
                )

        metric_category_enum = None
        if metric_category:
            try:
                metric_category_enum = MetricCategory(metric_category)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric category: {metric_category}",
                )

        # Get summary
        summary = await collector.get_metrics_summary(
            tenant_id=tenant_id,
            time_period_hours=time_period_hours,
            metric_type=metric_type_enum,
            metric_category=metric_category_enum,
            user_id=user_id,
        )

        return summary

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metrics summary: {str(e)}"
        )


@router.get("/metrics/{metric_name}")
async def get_metric_details(
    metric_name: str,
    time_period_hours: int = Query(default=24, ge=1, le=720),
    aggregation_type: str = Query(default="avg", regex="^(avg|min|max|sum|count)$"),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get detailed information for a specific metric."""
    try:
        # Create metrics collector
        collector = create_ux_metrics_collector(db_pool)

        # Get details
        details = await collector.get_metric_details(
            tenant_id=tenant_id,
            metric_name=metric_name,
            time_period_hours=time_period_hours,
            aggregation_type=aggregation_type,
        )

        if not details:
            raise HTTPException(status_code=404, detail="Metric not found")

        return details

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric details: {str(e)}"
        )


@router.post("/definitions")
async def create_metric_definition(
    definition: MetricDefinitionRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Create a new UX metric definition."""
    try:
        # Validate metric type and category
        try:
            metric_type = MetricType(definition.metric_type)
            metric_category = MetricCategory(definition.metric_category)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid metric type or category: {str(e)}"
            )

        # Create metrics collector
        collector = create_ux_metrics_collector(db_pool)

        # Create definition
        metric_definition = await collector.create_metric_definition(
            name=definition.name,
            description=definition.description,
            metric_type=metric_type,
            metric_category=metric_category,
            unit=definition.unit,
            calculation_method=definition.calculation_method,
            thresholds=definition.thresholds,
            is_active=definition.is_active,
        )

        return {
            "success": True,
            "definition": {
                "id": metric_definition.id,
                "name": metric_definition.name,
                "description": metric_definition.description,
                "metric_type": metric_definition.metric_type.value,
                "metric_category": metric_definition.metric_category.value,
                "unit": metric_definition.unit,
                "calculation_method": metric_definition.calculation_method,
                "thresholds": metric_definition.thresholds,
                "is_active": metric_definition.is_active,
                "created_at": metric_definition.created_at.isoformat(),
                "updated_at": metric_definition.updated_at.isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create metric definition: {str(e)}"
        )


@router.put("/definitions/{metric_name}/thresholds")
async def update_metric_thresholds(
    metric_name: str,
    thresholds: Dict[str, float],
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Update metric thresholds."""
    try:
        # Create metrics collector
        collector = create_ux_metrics_collector(db_pool)

        # Update thresholds
        success = await collector.update_metric_thresholds(
            metric_name=metric_name,
            thresholds=thresholds,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Metric definition not found")

        return {
            "success": True,
            "metric_name": metric_name,
            "thresholds": thresholds,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update metric thresholds: {str(e)}"
        )


@router.get("/definitions")
async def get_metric_definitions(
    metric_type: Optional[str] = None,
    metric_category: Optional[str] = None,
    active_only: bool = Query(default=True),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get metric definitions."""
    try:
        # Build query
        query = """
            SELECT * FROM ux_metric_definitions
            WHERE tenant_id = $1
        """
        params = [tenant_id]

        if active_only:
            query += " AND is_active = true"

        if metric_type:
            query += " AND metric_type = $2"
            params.append(metric_type)

        if metric_category:
            query += " AND metric_category = $3"
            params.append(metric_category)

        query += " ORDER BY name"

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            definitions = []
            for row in results:
                definition = {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "metric_type": row[3],
                    "metric_category": row[4],
                    "unit": row[5],
                    "calculation_method": row[6],
                    "thresholds": json.loads(row[7]) if row[7] else {},
                    "is_active": row[8],
                    "created_at": row[9].isoformat(),
                    "updated_at": row[10].isoformat(),
                }
                definitions.append(definition)

        return {
            "definitions": definitions,
            "total_count": len(definitions),
            "filters": {
                "metric_type": metric_type,
                "metric_category": metric_category,
                "active_only": active_only,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric definitions: {str(e)}"
        )


@router.get("/benchmarks")
async def get_performance_benchmarks(
    metric_type: Optional[str] = None,
    metric_category: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get performance benchmarks."""
    try:
        # Convert string to enum if provided
        metric_type_enum = None
        if metric_type:
            try:
                metric_type_enum = MetricType(metric_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid metric type: {metric_type}"
                )

        metric_category_enum = None
        if metric_category:
            try:
                metric_category_enum = MetricCategory(metric_category)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric category: {metric_category}",
                )

        # Create metrics collector
        collector = create_ux_metrics_collector(db_pool)

        # Get benchmarks
        benchmarks = await collector.get_performance_benchmarks(
            tenant_id=tenant_id,
            metric_type=metric_type_enum,
            metric_category=metric_category_enum,
        )

        return benchmarks

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance benchmarks: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    metric_name: Optional[str] = None,
    metric_type: Optional[str] = None,
    metric_category: Optional[str] = None,
    user_id: Optional[str] = None,
    time_period_hours: int = Query(default=24, ge=1, le=720),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get metrics with filtering."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_period_hours)

        # Build query
        query = """
            SELECT * FROM ux_metrics
            WHERE tenant_id = $1 AND timestamp > $2
        """
        params = [tenant_id, cutoff_time]

        if metric_name:
            query += " AND metric_name = $3"
            params.append(metric_name)

        if metric_type:
            query += " AND metric_type = $4"
            params.append(metric_type)

        if metric_category:
            query += " AND metric_category = $5"
            params.append(metric_category)

        if user_id:
            query += " AND user_id = $6"
            params.append(user_id)

        query += " ORDER BY timestamp DESC LIMIT $7 OFFSET $8"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            metrics = []
            for row in results:
                metric = {
                    "id": row[0],
                    "user_id": row[1],
                    "tenant_id": row[2],
                    "session_id": row[3],
                    "metric_type": row[4],
                    "metric_category": row[5],
                    "metric_name": row[6],
                    "value": row[7],
                    "unit": row[8],
                    "context": json.loads(row[9]) if row[9] else {},
                    "metadata": json.loads(row[10]) if row[10] else {},
                    "timestamp": row[11].isoformat(),
                    "created_at": row[12].isoformat(),
                }
                metrics.append(metric)

        return {
            "metrics": metrics,
            "total_count": len(metrics),
            "limit": limit,
            "offset": offset,
            "filters": {
                "metric_name": metric_name,
                "metric_type": metric_type,
                "metric_category": metric_category,
                "user_id": user_id,
                "time_period_hours": time_period_hours,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/aggregations")
async def get_metric_aggregations(
    time_period_hours: int = Query(default=24, ge=1, le=720),
    metric_type: Optional[str] = None,
    metric_category: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get metric aggregations."""
    try:
        # Build query
        query = """
            SELECT * FROM ux_metric_aggregations
            WHERE tenant_id = $1 AND period_hours = $2
        """
        params = [tenant_id, time_period_hours]

        if metric_type:
            query += " AND metric_type = $3"
            params.append(metric_type)

        if metric_category:
            query += " AND metric_category = $4"
            params.append(metric_category)

        query += " ORDER BY created_at DESC"

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            aggregations = []
            for row in results:
                aggregation = {
                    "id": row[0],
                    "tenant_id": row[1],
                    "metric_type": row[2],
                    "metric_category": row[3],
                    "metric_name": row[4],
                    "aggregation_type": row[5],
                    "period_hours": row[6],
                    "value": row[7],
                    "sample_size": row[8],
                    "threshold_compliance": json.loads(row[9]) if row[9] else {},
                    "created_at": row[10].isoformat(),
                }
                aggregations.append(aggregation)

        return {
            "aggregations": aggregations,
            "total_count": len(aggregations),
            "period_hours": time_period_hours,
            "filters": {
                "metric_type": metric_type,
                "metric_category": metric_category,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric aggregations: {str(e)}"
        )


@router.get("/alerts")
async def get_metric_alerts(
    metric_type: Optional[str] = None,
    metric_category: Optional[str] = None,
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    resolved_only: bool = Query(default=False),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get metric alerts."""
    try:
        # Build query
        query = """
            SELECT * FROM ux_metric_alerts
            WHERE tenant_id = $1
        """
        params = [tenant_id]

        if metric_type:
            query += " AND metric_name IN (SELECT name FROM ux_metric_definitions WHERE metric_type = $2)"
            params.append(metric_type)

        if metric_category:
            query += " AND metric_name IN (SELECT name FROM ux_metric_definitions WHERE metric_category = $3)"
            params.append(metric_category)

        if severity:
            query += " AND severity = $4"
            params.append(severity)

        if resolved_only:
            query += " AND is_resolved = true"
        else:
            query += " AND is_resolved = false"

        query += " ORDER BY created_at DESC"

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            alerts = []
            for row in results:
                alert = {
                    "id": row[0],
                    "tenant_id": row[1],
                    "metric_name": row[2],
                    "alert_type": row[3],
                    "severity": row[4],
                    "message": row[5],
                    "current_value": row[6],
                    "threshold_value": row[7],
                    "trend_data": json.loads(row[8]) if row[8] else None,
                    "is_resolved": row[9],
                    "created_at": row[10].isoformat(),
                    "resolved_at": row[11].isoformat() if row[11] else None,
                }
                alerts.append(alert)

        return {
            "alerts": alerts,
            "total_count": len(alerts),
            "filters": {
                "metric_type": metric_type,
                "metric_category": metric_category,
                "severity": severity,
                "resolved_only": resolved_only,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric alerts: {str(e)}"
        )


@router.get("/types")
async def get_metric_types(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get available metric types and categories."""
    try:
        return {
            "metric_types": [
                {
                    "value": mt.value,
                    "name": mt.value.replace("_", " ").title(),
                }
                for mt in MetricType
            ],
            "metric_categories": [
                {
                    "value": mc.value,
                    "name": mc.value.replace("_", " ").title(),
                }
                for mc in MetricCategory
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric types: {str(e)}"
        )


@router.get("/dashboard")
async def get_ux_metrics_dashboard(
    time_period_hours: int = Query(default=24, ge=1, le=720),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive UX metrics dashboard."""
    try:
        # Create metrics collector
        collector = create_ux_metrics_collector(db_pool)

        # Get summary
        summary = await collector.get_metrics_summary(
            tenant_id=tenant_id,
            time_period_hours=time_period_hours,
        )

        # Get aggregations
        aggregations = await collector.get_metric_aggregations(
            tenant_id=tenant_id,
            time_period_hours=time_period_hours,
        )

        # Get active alerts
        alerts_query = """
            SELECT * FROM ux_metric_alerts
            WHERE tenant_id = $1 AND is_resolved = false
            ORDER BY created_at DESC
            LIMIT 10
        """

        async with db_pool.acquire() as conn:
            alert_results = await conn.fetch(alerts_query, tenant_id)

            active_alerts = []
            for row in alert_results:
                alert = {
                    "id": row[0],
                    "metric_name": row[2],
                    "alert_type": row[3],
                    "severity": row[4],
                    "message": row[5],
                    "current_value": row[6],
                    "threshold_value": row[7],
                    "created_at": row[10].isoformat(),
                }
                active_alerts.append(alert)

        # Get benchmarks
        benchmarks = await collector.get_performance_benchmarks(
            tenant_id=tenant_id,
        )

        return {
            "period_hours": time_period_hours,
            "summary": summary,
            "aggregations": aggregations["aggregations"],
            "active_alerts": active_alerts,
            "benchmarks": benchmarks,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get UX metrics dashboard: {str(e)}"
        )


@router.get("/export/metrics")
async def export_metrics(
    format: str = Query(default="json", regex="^(json|csv)$"),
    time_period_hours: int = Query(default=24, ge=1, le=720),
    metric_type: Optional[str] = None,
    metric_category: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Any:
    """Export UX metrics data."""
    try:
        # Create metrics collector
        collector = create_ux_metrics_collector(db_pool)

        # Convert string to enum if provided
        metric_type_enum = None
        if metric_type:
            try:
                metric_type_enum = MetricType(metric_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid metric type: {metric_type}"
                )

        metric_category_enum = None
        if metric_category:
            try:
                metric_category_enum = MetricCategory(metric_category)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric category: {metric_category}",
                )

        # Get summary
        summary = await collector.get_metrics_summary(
            tenant_id=tenant_id,
            time_period_hours=time_period_hours,
            metric_type=metric_type_enum,
            metric_category=metric_category_enum,
        )

        if format == "json":
            return JSONResponse(
                content=summary,
                headers={
                    "Content-Disposition": f"attachment; filename=ux_metrics_{time_period_hours}hrs.json"
                },
            )
        elif format == "csv":
            # Convert to CSV format
            csv_data = _convert_metrics_to_csv(summary)

            from fastapi.responses import Response

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=ux_metrics_{time_period_hours}hrs.csv"
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export UX metrics: {str(e)}"
        )


def _convert_metrics_to_csv(data: Dict[str, Any]) -> str:
    """Convert UX metrics data to CSV format."""
    try:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Metric", "Value", "Category"])

        # Write metric statistics
        if "metric_statistics" in data:
            stats = data["metric_statistics"]
            writer.writerow(
                ["Total Metrics", stats.get("total_metrics", 0), "Statistics"]
            )
            writer.writerow(
                ["Unique Metrics", stats.get("unique_metrics", 0), "Statistics"]
            )
            writer.writerow(
                ["Unique Users", stats.get("unique_users", 0), "Statistics"]
            )
            writer.writerow(["Average Value", stats.get("avg_value", 0), "Statistics"])
            writer.writerow(["Minimum Value", stats.get("min_value", 0), "Statistics"])
            writer.writerow(["Maximum Value", stats.get("max_value", 0), "Statistics"])

        # Write aggregations
        if "aggregations" in data:
            aggregations = data["aggregations"]
            for aggregation in aggregations:
                writer.writerow(
                    [
                        f"Aggregation: {aggregation['metric_name']}",
                        aggregation.get("value", 0),
                        "Aggregations",
                    ]
                )

        # Write active alerts
        if "active_alerts" in data:
            alerts = data["active_alerts"]
            writer.writerow(["Active Alerts", len(alerts), "Alerts"])
            for alert in alerts:
                writer.writerow(
                    [
                        f"Alert: {alert['metric_name']}",
                        alert.get("current_value", 0),
                        "Alerts",
                    ]
                )

        # Write benchmarks
        if "benchmarks" in data:
            benchmarks = data["benchmarks"]
            if "current_performance" in benchmarks:
                current_perf = benchmarks["current_performance"]
                for metric, value in current_perf.items():
                    writer.writerow([f"Current: {metric}", value, "Benchmarks"])

        return output.getvalue()

    except Exception as e:
        return f"Error converting to CSV: {str(e)}"


@router.get("/health")
async def health_check(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Health check for UX metrics collector."""
    try:
        # Create metrics collector
        create_ux_metrics_collector(db_pool)

        # Test database connection
        try:
            async with db_pool.acquire() as conn:
                await conn.fetch("SELECT 1")
                db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Test metric definitions
        try:
            query = "SELECT COUNT(*) FROM ux_metric_definitions WHERE tenant_id = $1"
            async with db_pool.acquire() as conn:
                await conn.fetchval(query, tenant_id)
                definitions_status = "healthy"
        except Exception:
            definitions_status = "unhealthy"

        # Test metrics collection
        try:
            query = "SELECT COUNT(*) FROM ux_metrics WHERE tenant_id = $1"
            async with db_pool.acquire() as conn:
                await conn.fetchval(query, tenant_id)
                metrics_status = "healthy"
        except Exception:
            metrics_status = "unhealthy"

        return {
            "status": "healthy"
            if all(
                s == "healthy" for s in [db_status, definitions_status, metrics_status]
            )
            else "unhealthy",
            "database": db_status,
            "definitions": definitions_status,
            "metrics": metrics_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
