"""
API Monitoring and Analytics Endpoints

Provides endpoints for accessing API metrics, logs, and monitoring data.
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from shared.api_auth_middleware import get_current_user, require_permissions
from shared.api_logger import api_logger
from shared.logging_config import get_logger

logger = get_logger("sorce.api_monitoring")

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    try:
        # Check if monitoring system is active
        active_requests = api_logger.metrics_collector.get_active_requests_count()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "active_requests": active_requests,
            "monitoring_active": True,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable",
        )


@router.get("/metrics")
async def get_metrics(
    hours: int = Query(default=1, ge=1, le=168),  # Max 7 days
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:read"])),
):
    """Get comprehensive API metrics."""
    try:
        # Get performance summary
        performance = api_logger.metrics_collector.get_performance_summary(hours)

        # Get endpoint statistics
        endpoint_stats = api_logger.metrics_collector.get_endpoint_stats()

        # Get error summary
        error_summary = api_logger.metrics_collector.get_error_summary()

        # Get security events
        security_events = api_logger.metrics_collector.get_security_events(hours)

        # Get active requests count
        active_requests = api_logger.metrics_collector.get_active_requests_count()

        return {
            "performance": performance,
            "endpoints": endpoint_stats,
            "errors": error_summary,
            "security_events": security_events,
            "active_requests": active_requests,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics",
        )


@router.get("/performance")
async def get_performance_metrics(
    hours: int = Query(default=1, ge=1, le=24),
    endpoint: Optional[str] = Query(default=None),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:read"])),
):
    """Get detailed performance metrics."""
    try:
        performance = api_logger.metrics_collector.get_performance_summary(hours)

        # Filter by endpoint if specified
        if endpoint:
            endpoint_stats = api_logger.metrics_collector.get_endpoint_stats(endpoint)
            performance["endpoint"] = endpoint_stats

        return {
            "performance": performance,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics",
        )


@router.get("/endpoints")
async def get_endpoint_stats(
    endpoint: Optional[str] = Query(default=None),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:read"])),
):
    """Get endpoint-specific statistics."""
    try:
        endpoint_stats = api_logger.metrics_collector.get_endpoint_stats(endpoint)

        return {"endpoints": endpoint_stats, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error(f"Failed to get endpoint stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve endpoint statistics",
        )


@router.get("/errors")
async def get_error_summary(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:read"])),
):
    """Get error summary and trends."""
    try:
        error_summary = api_logger.metrics_collector.get_error_summary()

        # Calculate error rate
        performance = api_logger.metrics_collector.get_performance_summary(hours)
        total_requests = performance.get("total_requests", 0)
        total_errors = sum(error_summary.values())
        error_rate = total_errors / total_requests if total_requests > 0 else 0

        return {
            "error_counts": error_summary,
            "total_errors": total_errors,
            "total_requests": total_requests,
            "error_rate": error_rate,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get error summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve error summary",
        )


@router.get("/security")
async def get_security_events(
    hours: int = Query(default=24, ge=1, le=168),
    severity: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:read", "security:read"])),
):
    """Get security events and alerts."""
    try:
        security_events = api_logger.metrics_collector.get_security_events(hours)

        # Filter by severity if specified
        if severity:
            security_events = [
                event for event in security_events if event.get("severity") == severity
            ]

        # Filter by event type if specified
        if event_type:
            security_events = [
                event
                for event in security_events
                if event.get("event_type") == event_type
            ]

        # Count events by type and severity
        event_counts = {}
        severity_counts = {}

        for event in security_events:
            event_type = event.get("event_type", "unknown")
            event_severity = event.get("severity", "unknown")

            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            severity_counts[event_severity] = severity_counts.get(event_severity, 0) + 1

        return {
            "events": security_events,
            "event_counts": event_counts,
            "severity_counts": severity_counts,
            "total_events": len(security_events),
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events",
        )


@router.get("/active-requests")
async def get_active_requests(
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:read"])),
):
    """Get information about currently active requests."""
    try:
        active_count = api_logger.metrics_collector.get_active_requests_count()

        return {
            "active_requests_count": active_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get active requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active requests",
        )


@router.get("/dashboard")
async def get_dashboard_data(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:read"])),
):
    """Get consolidated dashboard data."""
    try:
        # Get all metrics
        metrics = api_logger.get_metrics()

        # Calculate additional dashboard metrics
        performance = metrics["performance"]
        errors = metrics["errors"]
        security = metrics["security"]

        # Calculate health score (0-100)
        health_score = 100

        # Deduct for high error rate
        error_rate = performance.get("error_rate", 0)
        if error_rate > 0.1:  # > 10%
            health_score -= 30
        elif error_rate > 0.05:  # > 5%
            health_score -= 15

        # Deduct for slow response times
        avg_response_time = performance.get("avg_response_time", 0)
        if avg_response_time > 2000:  # > 2 seconds
            health_score -= 20
        elif avg_response_time > 1000:  # > 1 second
            health_score -= 10

        # Deduct for security events
        security_events_count = len(security)
        if security_events_count > 50:
            health_score -= 25
        elif security_events_count > 20:
            health_score -= 10

        health_score = max(0, health_score)

        # Get top endpoints by request count
        top_endpoints = sorted(
            metrics["endpoints"].items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True,
        )[:10]

        # Get recent error trends
        recent_errors = dict(list(errors.items())[:5])

        return {
            "health_score": health_score,
            "summary": {
                "total_requests": performance.get("total_requests", 0),
                "avg_response_time": avg_response_time,
                "error_rate": error_rate,
                "active_requests": metrics["active_requests"],
                "security_events": security_events_count,
            },
            "top_endpoints": top_endpoints,
            "recent_errors": recent_errors,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data",
        )


@router.post("/test-logging")
async def test_logging(
    event_type: str = Query(default="info"),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:write"])),
):
    """Test endpoint for logging functionality."""
    try:
        import uuid

        from shared.api_logger import (
            APIRequest,
            APIResponse,
            PerformanceMetrics,
            SecurityEvent,
        )

        request_id = str(uuid.uuid4())

        if event_type == "request":
            # Test request logging
            test_request = APIRequest(
                request_id=request_id,
                method="GET",
                url="/test",
                path="/test",
                query_params={"test": "true"},
                headers={"user-agent": "test-agent"},
                user_agent="test-agent",
                ip_address="127.0.0.1",
                user_id=current_user.get("user_id"),
            )

            api_logger.log_request_start(test_request)

            test_response = APIResponse(
                request_id=request_id, status_code=200, response_time_ms=150.0
            )

            api_logger.log_request_end(test_response)

        elif event_type == "security":
            # Test security event logging
            test_event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                request_id=request_id,
                event_type="test_event",
                severity="low",
                description="Test security event",
                ip_address="127.0.0.1",
                user_agent="test-agent",
                user_id=current_user.get("user_id"),
                details={"test": True},
            )

            api_logger.log_security_event(test_event)

        elif event_type == "performance":
            # Test performance metrics
            test_metrics = PerformanceMetrics(
                request_id=request_id,
                endpoint="/test",
                method="GET",
                response_time_ms=150.0,
                db_query_time_ms=25.0,
                cache_lookup_time_ms=5.0,
            )

            api_logger.log_performance_metrics(test_metrics)

        return {
            "message": f"Test {event_type} logging completed",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Test logging failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test logging failed",
        )


@router.get("/export")
async def export_metrics(
    hours: int = Query(default=24, ge=1, le=168),
    format: str = Query(default="json", regex="^(json|csv)$"),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_permissions(["monitoring:export"])),
):
    """Export metrics data in specified format."""
    try:
        metrics = api_logger.get_metrics()

        if format == "csv":
            # Convert to CSV format (simplified for key metrics)
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(["metric", "value", "timestamp"])

            # Write performance metrics
            perf = metrics["performance"]
            for key, value in perf.items():
                writer.writerow(
                    [f"performance.{key}", value, datetime.utcnow().isoformat()]
                )

            # Write error counts
            for status_code, count in metrics["errors"].items():
                writer.writerow(
                    [f"errors.{status_code}", count, datetime.utcnow().isoformat()]
                )

            csv_data = output.getvalue()
            output.close()

            return JSONResponse(
                content=csv_data,
                headers={
                    "Content-Disposition": f"attachment; filename=metrics_{hours}h.csv"
                },
                media_type="text/csv",
            )

        else:
            # Return JSON format
            return metrics

    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export metrics",
        )
