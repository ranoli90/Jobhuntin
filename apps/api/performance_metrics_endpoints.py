"""
Performance Metrics API Endpoints for Phase 12.1 Agent Improvements
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.dependencies import get_pool
from packages.backend.domain.agent_improvements import (
    AgentImprovementsManager,
    create_agent_improvements_manager,
)
from packages.backend.domain.tenant import TenantContext

router = APIRouter(prefix="/performance-metrics", tags=["performance-metrics"])


async def get_tenant_context() -> TenantContext:
    """Stub; inject tenant context via Depends in main app."""
    raise NotImplementedError("Tenant context dependency not injected")


# Pydantic models
class PerformanceMetricsRequest(BaseModel):
    """Performance metrics request."""

    application_id: str = Field(..., description="Application ID")
    metric_type: str = Field(..., description="Metric type")
    metric_value: float = Field(..., description="Metric value")
    metric_unit: Optional[str] = Field(None, description="Metric unit")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response."""

    metric_id: str
    application_id: str
    metric_type: str
    metric_value: float
    metric_unit: Optional[str]
    metadata: Dict[str, Any]
    created_at: str


class MetricsListResponse(BaseModel):
    """Metrics list response."""

    metrics: List[PerformanceMetricsResponse]
    total: int
    page: int
    per_page: int


# Dependency injection functions
def get_agent_improvements_manager():
    """Get agent improvements manager instance."""
    return create_agent_improvements_manager(get_pool())


@router.post("/record")
async def record_performance_metric(
    request: PerformanceMetricsRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> PerformanceMetricsResponse:
    """Record a performance metric."""
    try:
        metric = await manager.record_performance_metric(
            application_id=request.application_id,
            metric_type=request.metric_type,
            metric_value=request.metric_value,
            metric_unit=request.metric_unit,
            metadata=request.metadata or {},
        )

        return PerformanceMetricsResponse(
            metric_id=metric.metric_id,
            application_id=metric.application_id,
            metric_type=metric.metric_type,
            metric_value=metric.metric_value,
            metric_unit=metric.metric_unit,
            metadata=metric.metadata,
            created_at=metric.created_at.isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to record metric: {str(e)}"
        )


@router.get("/list")
async def list_performance_metrics(
    application_id: Optional[str] = Query(None, description="Application ID"),
    metric_type: Optional[str] = Query(None, description="Metric type"),
    date_from: Optional[str] = Query(None, description="Date from"),
    date_to: Optional[str] = Query(None, description="Date to"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> MetricsListResponse:
    """List performance metrics."""
    try:
        metrics = await manager.get_performance_metrics(
            application_id=application_id,
            metric_type=metric_type,
            date_from=date_from,
            date_to=date_to,
            limit=per_page,
            offset=(page - 1) * per_page,
        )

        return MetricsListResponse(
            metrics=[
                PerformanceMetricsResponse(
                    metric_id=m.metric_id,
                    application_id=m.application_id,
                    metric_type=m.metric_type,
                    metric_value=m.metric_value,
                    metric_unit=m.metric_unit,
                    metadata=m.metadata,
                    created_at=m.created_at.isoformat(),
                )
                for m in metrics
            ],
            total=len(metrics),
            page=page,
            per_page=per_page,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list metrics: {str(e)}")


@router.get("/{metric_id}")
async def get_performance_metric(
    metric_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> PerformanceMetricsResponse:
    """Get a specific performance metric."""
    try:
        metric = await manager.get_performance_metric(metric_id)

        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")

        return PerformanceMetricsResponse(
            metric_id=metric.metric_id,
            application_id=metric.application_id,
            metric_type=metric.metric_type,
            metric_value=metric.metric_value,
            metric_unit=metric.metric_unit,
            metadata=metric.metadata,
            created_at=metric.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metric: {str(e)}")


@router.get("/types")
async def get_supported_metric_types() -> Dict[str, Any]:
    """Get supported metric types."""
    try:
        metric_types = [
            {
                "type": "button_detection_accuracy",
                "name": "Button Detection Accuracy",
                "description": "Accuracy of button detection",
                "unit": "percentage",
                "category": "detection",
            },
            {
                "type": "form_field_detection_accuracy",
                "name": "Form Field Detection Accuracy",
                "description": "Accuracy of form field detection",
                "unit": "percentage",
                "category": "detection",
            },
            {
                "type": "screenshot_capture_time",
                "name": "Screenshot Capture Time",
                "description": "Time taken to capture screenshot",
                "unit": "milliseconds",
                "category": "performance",
            },
            {
                "type": "processing_time",
                "name": "Processing Time",
                "description": "Total processing time",
                "unit": "seconds",
                "category": "performance",
            },
            {
                "type": "success_rate",
                "name": "Success Rate",
                "description": "Overall success rate",
                "unit": "percentage",
                "category": "success",
            },
            {
                "type": "error_rate",
                "name": "Error Rate",
                "description": "Overall error rate",
                "unit": "percentage",
                "category": "errors",
            },
            {
                "type": "concurrent_sessions",
                "name": "Concurrent Sessions",
                "description": "Number of concurrent sessions",
                "unit": "count",
                "category": "concurrency",
            },
            {
                "type": "memory_usage",
                "name": "Memory Usage",
                "description": "Memory usage",
                "unit": "megabytes",
                "category": "resources",
            },
            {
                "type": "cpu_usage",
                "name": "CPU Usage",
                "description": "CPU usage",
                "unit": "percentage",
                "category": "resources",
            },
        ]

        return {
            "metric_types": metric_types,
            "total": len(metric_types),
            "message": "Supported metric types retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metric types: {str(e)}"
        )


@router.get("/stats")
async def get_performance_stats(
    application_id: Optional[str] = Query(None, description="Application ID"),
    metric_type: Optional[str] = Query(None, description="Metric type"),
    date_from: Optional[str] = Query(None, description="Date from"),
    date_to: Optional[str] = Query(None, description="Date to"),
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, Any]:
    """Get performance statistics."""
    try:
        stats = await manager.get_performance_stats(
            application_id=application_id,
            metric_type=metric_type,
            date_from=date_from,
            date_to=date_to,
        )

        return {
            "stats": stats,
            "message": "Performance statistics retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/dashboard")
async def get_performance_dashboard(
    date_from: Optional[str] = Query(None, description="Date from"),
    date_to: Optional[str] = Query(None, description="Date to"),
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, Any]:
    """Get performance dashboard data."""
    try:
        dashboard = await manager.get_performance_dashboard(
            date_from=date_from,
            date_to=date_to,
        )

        return {
            "dashboard": dashboard,
            "message": "Performance dashboard retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard: {str(e)}"
        )


@router.post("/batch-record")
async def batch_record_metrics(
    metrics: List[PerformanceMetricsRequest],
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, Any]:
    """Batch record multiple metrics."""
    try:
        results = []

        for metric in metrics:
            try:
                recorded_metric = await manager.record_performance_metric(
                    application_id=metric.application_id,
                    metric_type=metric.metric_type,
                    metric_value=metric.metric_value,
                    metric_unit=metric.metric_unit,
                    metadata=metric.metadata or {},
                )
                results.append(
                    {
                        "success": True,
                        "metric_id": recorded_metric.metric_id,
                        "metric_type": recorded_metric.metric_type,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "success": False,
                        "error": str(e),
                        "application_id": metric.application_id,
                    }
                )

        successful = sum(1 for r in results if r["success"])

        return {
            "results": results,
            "total": len(metrics),
            "successful": successful,
            "failed": len(metrics) - successful,
            "message": f"Batch recording completed: {successful}/{len(metrics)} successful",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to batch record metrics: {str(e)}"
        )


@router.delete("/{metric_id}")
async def delete_performance_metric(
    metric_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, str]:
    """Delete a performance metric."""
    try:
        success = await manager.delete_performance_metric(metric_id)

        if not success:
            raise HTTPException(status_code=404, detail="Metric not found")

        return {
            "metric_id": metric_id,
            "message": "Metric deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete metric: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for performance metrics system."""
    return {
        "status": "healthy",
        "service": "performance_metrics",
        "features": [
            "metric_recording",
            "metric_analytics",
            "performance_dashboard",
            "batch_operations",
        ],
    }
