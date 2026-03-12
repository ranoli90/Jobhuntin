"""Admin Dashboard API Endpoints.

Provides:
  - GET /admin/dashboard/overview - System health summary
  - GET /admin/dashboard/metrics - Detailed metrics for time range
  - GET /admin/dashboard/alerts - Active and recent alerts
  - POST /admin/dashboard/alerts/{id}/acknowledge - Acknowledge alert
  - GET /admin/dashboard/tenants - Tenant activity overview
  - GET /admin/dashboard/performance - Performance trends
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from shared.alerting import AlertSeverity, AlertStatus, get_alert_manager
from shared.circuit_breaker import get_all_circuit_breaker_statuses
from shared.logging_config import get_logger
from shared.monitoring_config import get_monitoring_config
from shared.structured_logging import get_structured_metrics

logger = get_logger("sorce.dashboard")

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


class HealthSummary(BaseModel):
    status: str
    uptime_seconds: float
    total_requests: int
    total_errors: int
    error_rate_pct: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    active_alerts: int
    circuit_breakers: dict[str, str]
    database_status: str
    redis_status: str


class MetricDataPoint(BaseModel):
    timestamp: str
    value: float


class MetricsResponse(BaseModel):
    metric_name: str
    unit: str
    data_points: list[MetricDataPoint]
    summary: dict[str, float]


class AlertResponse(BaseModel):
    id: str
    rule_name: str
    severity: str
    status: str
    message: str
    metric_value: float
    threshold: float
    triggered_at: str
    acknowledged_at: str | None = None
    acknowledged_by: str | None = None


class TenantActivity(BaseModel):
    tenant_id: str
    tenant_name: str
    plan: str
    active_users: int
    requests_last_hour: int
    requests_last_day: int
    error_count: int
    last_activity: str | None


class PerformanceTrend(BaseModel):
    timestamp: str
    requests_per_minute: float
    avg_latency_ms: float
    error_rate_pct: float
    active_connections: int


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    raise NotImplementedError("Tenant context dependency not injected")


async def _get_admin_user_id():
    raise NotImplementedError("Auth dependency not injected")


@router.get("/overview", response_model=HealthSummary)
async def get_overview(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> HealthSummary:
    """Get system health summary for dashboard."""
    structured_metrics = get_structured_metrics()
    all_metrics = structured_metrics.get_all_metrics()
    summary = all_metrics.get("summary", {})

    alert_manager = get_alert_manager()
    active_alerts = alert_manager.get_active_alerts()

    circuit_breakers = get_all_circuit_breaker_statuses()
    cb_status = {cb["name"]: cb["state"] for cb in circuit_breakers}
    any_open = any(cb["state"] == "open" for cb in circuit_breakers)

    db_ok = False
    try:
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception as e:
        logger.debug(f"Health check DB connection failed: {e}")

    redis_ok = False
    try:
        from shared.redis_client import get_redis

        redis = await get_redis()
        await redis.ping()
        redis_ok = True
    except Exception as e:
        logger.debug(f"Health check Redis connection failed: {e}")

    total_requests = summary.get("total_requests", 0)
    total_errors = summary.get("total_errors", 0)
    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0

    if not db_ok:
        status = "unhealthy"
    elif any_open:
        status = "degraded"
    elif len(active_alerts) > 0:
        status = "warning"
    else:
        status = "healthy"

    return HealthSummary(
        status=status,
        uptime_seconds=all_metrics.get("uptime_seconds", 0),
        total_requests=total_requests,
        total_errors=total_errors,
        error_rate_pct=round(error_rate, 2),
        latency_p50_ms=summary.get("overall_latency_p50_ms", 0),
        latency_p95_ms=summary.get("overall_latency_p95_ms", 0),
        latency_p99_ms=summary.get("overall_latency_p99_ms", 0),
        active_alerts=len(active_alerts),
        circuit_breakers=cb_status,
        database_status="ok" if db_ok else "unreachable",
        redis_status="ok" if redis_ok else "unavailable",
    )


@router.get("/metrics")
async def get_metrics(
    _admin: str = Depends(_get_admin_user_id),
    metric_type: str = Query("all", description="Type: all, endpoints, operations"),
    time_range: str = Query("1h", description="Time range: 1h, 6h, 24h, 7d"),
) -> dict[str, Any]:
    """Get detailed metrics for time range."""
    structured_metrics = get_structured_metrics()
    all_metrics = structured_metrics.get_all_metrics()

    monitoring_config = get_monitoring_config()

    response = {
        "collection_timestamp": all_metrics.get("collection_timestamp"),
        "uptime_seconds": all_metrics.get("uptime_seconds"),
        "config": {
            "environment": monitoring_config.environment,
            "thresholds": {
                "error_rate_pct": monitoring_config.thresholds.error_rate_pct,
                "latency_p99_ms": monitoring_config.thresholds.latency_p99_ms,
            },
        },
    }

    if metric_type in ("all", "endpoints"):
        response["endpoints"] = all_metrics.get("endpoints", {})

    if metric_type in ("all", "operations"):
        response["operations"] = all_metrics.get("operations", {})

    response["summary"] = all_metrics.get("summary", {})
    response["prometheus_export"] = structured_metrics.export_prometheus()

    return response


@router.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(
    _admin: str = Depends(_get_admin_user_id),
    status: str | None = Query(
        None, description="Filter by status: active, acknowledged, resolved"
    ),
    severity: str | None = Query(
        None, description="Filter by severity: info, warning, error, critical"
    ),
    limit: int = Query(50, ge=1, le=200),
) -> list[AlertResponse]:
    """Get active and recent alerts."""
    alert_manager = get_alert_manager()

    status_filter = None
    if status:
        try:
            status_filter = AlertStatus(status.lower())
        except ValueError:
            pass

    severity_filter = None
    if severity:
        try:
            severity_filter = AlertSeverity(severity.lower())
        except ValueError:
            pass

    # Get alerts based on status filter
    if status_filter == AlertStatus.FIRING:
        alerts = alert_manager.get_active_alerts()
    else:
        alerts = alert_manager.get_alert_history(limit=limit)

    # Apply severity filter if specified
    if severity_filter:
        alerts = [a for a in alerts if a.severity == severity_filter]

    # Apply limit
    alerts = alerts[:limit]

    return [
        AlertResponse(
            id=alert.id,
            rule_name=alert.rule_name,
            severity=alert.severity.value,
            status=alert.status.value,
            message=alert.message,
            metric_value=alert.metric_value,
            threshold=alert.threshold,
            triggered_at=alert.triggered_at.isoformat(),
            acknowledged_at=(
                alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
            ),
            acknowledged_by=alert.acknowledged_by,
        )
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user_id: str = Depends(_get_admin_user_id),
) -> dict[str, Any]:
    """Acknowledge an alert."""
    alert_manager = get_alert_manager()
    alert = alert_manager.acknowledge_alert(alert_id, user_id)

    if alert is None:
        raise HTTPException(
            status_code=404, detail="Alert not found or already acknowledged"
        )

    logger.info("Alert %s acknowledged by %s", alert_id, user_id)

    return {"status": "acknowledged", "alert": alert.to_dict()}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    user_id: str = Depends(_get_admin_user_id),
) -> dict[str, Any]:
    """Resolve an alert."""
    alert_manager = get_alert_manager()
    # Use acknowledge_alert as the resolve method
    alert = alert_manager.acknowledge_alert(alert_id, user_id)

    if alert is None:
        raise HTTPException(
            status_code=404, detail="Alert not found or already resolved"
        )

    logger.info("Alert %s resolved by %s", alert_id, user_id)

    return {"status": "resolved", "alert": alert.to_dict()}


@router.get("/tenants", response_model=list[TenantActivity])
async def get_tenant_activity(
    limit: int = Query(20, ge=1, le=100),
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_admin_user_id),
) -> list[TenantActivity]:
    """Get tenant activity overview."""
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                t.id as tenant_id,
                t.name as tenant_name,
                t.plan,
                COUNT(DISTINCT p.user_id) as active_users,
                COUNT(a.id) FILTER (
                    WHERE a.created_at > now() - interval '1 hour'
                ) as requests_last_hour,
                COUNT(a.id) FILTER (
                    WHERE a.created_at > now() - interval '24 hours'
                ) as requests_last_day,
                COUNT(a.id) FILTER (
                    WHERE a.status = 'FAILED'
                    AND a.updated_at > now() - interval '24 hours'
                ) as error_count,
                MAX(a.updated_at) as last_activity
            FROM public.tenants t
            LEFT JOIN public.profiles p ON p.tenant_id = t.id
            LEFT JOIN public.applications a ON a.user_id = p.user_id AND a.tenant_id = t.id
            GROUP BY t.id, t.name, t.plan
            ORDER BY requests_last_day DESC NULLS LAST
            LIMIT $1
        """,
            limit,
        )

    return [
        TenantActivity(
            tenant_id=str(r["tenant_id"]),
            tenant_name=r["tenant_name"] or "Unknown",
            plan=r["plan"] or "FREE",
            active_users=r["active_users"] or 0,
            requests_last_hour=r["requests_last_hour"] or 0,
            requests_last_day=r["requests_last_day"] or 0,
            error_count=r["error_count"] or 0,
            last_activity=(
                r["last_activity"].isoformat() if r["last_activity"] else None
            ),
        )
        for r in rows
    ]


@router.get("/performance", response_model=list[PerformanceTrend])
async def get_performance_trends(
    time_range: str = Query("1h", description="Time range: 1h, 6h, 24h"),
    interval: str = Query("5m", description="Interval: 1m, 5m, 15m, 1h"),
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_admin_user_id),
) -> list[PerformanceTrend]:
    """Get performance trends over time."""
    time_range_map = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
    }
    duration = time_range_map.get(time_range, timedelta(hours=1))

    interval_hours = duration.total_seconds() / 3600
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                date_trunc('minute', created_at) -
                (EXTRACT(minute FROM created_at)::int % 5) * interval '1 minute' as bucket,
                COUNT(*) as requests,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) * 1000)
                    as avg_latency_ms,
                COUNT(*) FILTER (WHERE status = 'FAILED')::float
                    / NULLIF(COUNT(*), 0) * 100 as error_rate_pct
            FROM public.applications
            WHERE created_at > now() - interval '1 hour' * $1
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT 60
            """,
            interval_hours,
        )

    return [
        PerformanceTrend(
            timestamp=(
                r["bucket"].isoformat()
                if r["bucket"]
                else datetime.now(timezone.utc).isoformat()
            ),
            requests_per_minute=r["requests"] / 5.0 if r["requests"] else 0,
            avg_latency_ms=round(r["avg_latency_ms"] or 0, 2),
            error_rate_pct=round(r["error_rate_pct"] or 0, 2),
            active_connections=0,
        )
        for r in rows
    ]


@router.get("/config")
async def get_dashboard_config(
    _admin: str = Depends(_get_admin_user_id),
) -> dict[str, Any]:
    """Get monitoring configuration for dashboard."""
    config = get_monitoring_config()
    return config.to_dict()


@router.post("/alerts/evaluate")
async def evaluate_alerts(
    user_id: str = Depends(_get_admin_user_id),
) -> dict[str, Any]:
    """Manually trigger alert evaluation."""
    alert_manager = get_alert_manager()

    from shared.structured_logging import get_structured_metrics

    metrics = get_structured_metrics()
    all_metrics = metrics.get_all_metrics()
    summary = all_metrics.get("summary", {})

    total_requests = summary.get("total_requests", 0)
    total_errors = summary.get("total_errors", 0)
    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0

    alert_manager.record_metric("error_rate", error_rate)
    alert_manager.record_metric(
        "latency_p99_ms", summary.get("overall_latency_p99_ms", 0)
    )
    alert_manager.record_metric(
        "latency_p95_ms", summary.get("overall_latency_p95_ms", 0)
    )
    alert_manager.record_metric(
        "latency_p50_ms", summary.get("overall_latency_p50_ms", 0)
    )

    circuit_breakers = get_all_circuit_breaker_statuses()
    open_count = sum(1 for cb in circuit_breakers if cb["state"] == "open")
    alert_manager.record_metric("circuit_breaker_open", float(open_count))

    new_alerts = alert_manager.evaluate_rules()

    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "new_alerts_count": len(new_alerts),
        "new_alerts": [a.to_dict() for a in new_alerts],
    }
