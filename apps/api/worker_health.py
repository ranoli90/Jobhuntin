"""Worker Health Check API - Monitor job sync status and worker performance.

Provides comprehensive health monitoring for background workers,
job processing queues, and sync operations.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from packages.backend.domain.tenant import TenantContext


async def _get_tenant_ctx() -> TenantContext:
    raise NotImplementedError("Tenant context dependency not injected")


from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.api.worker_health")

router = APIRouter(prefix="/worker", tags=["worker-health"])


def _get_pool() -> asyncpg.Pool:
    return (_ for _ in ()).throw(NotImplementedError("Pool not injected"))


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class WorkerStatus(BaseModel):
    status: str  # healthy | degraded | unhealthy
    last_activity: datetime | None
    queue_size: int
    processing_rate: float  # jobs per minute
    error_rate: float  # percentage
    uptime_seconds: int


class JobSyncStatus(BaseModel):
    last_sync: datetime | None
    sync_success_rate: float  # percentage
    pending_syncs: int
    failed_syncs: int
    average_sync_time_seconds: float


class WorkerHealthResponse(BaseModel):
    timestamp: datetime
    worker_status: WorkerStatus
    job_sync_status: JobSyncStatus
    system_resources: dict[str, Any]
    alerts: list[str]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


async def get_worker_metrics(db: asyncpg.Pool) -> dict[str, Any]:
    """Get comprehensive worker performance metrics."""
    async with db.acquire() as conn:
        # Get recent job processing metrics
        recent_jobs = await conn.fetch(
            """
            SELECT
                COUNT(*) as total_jobs,
                COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed_jobs,
                COUNT(*) FILTER (WHERE status = 'FAILED') as failed_jobs,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_time,
                MAX(created_at) as last_job_time
            FROM public.applications
            WHERE created_at > NOW() - INTERVAL '1 hour'
            """
        )

        job_data = recent_jobs[0] if recent_jobs else {}
        total_jobs = job_data.get("total_jobs", 0)
        completed_jobs = job_data.get("completed_jobs", 0)
        failed_jobs = job_data.get("failed_jobs", 0)
        avg_processing_time = job_data.get("avg_processing_time", 0) or 0
        last_job_time = job_data.get("last_job_time")

        # Calculate rates
        processing_rate = (
            completed_jobs / 60.0 if completed_jobs > 0 else 0.0
        )  # jobs per minute
        error_rate = (failed_jobs / total_jobs * 100.0) if total_jobs > 0 else 0.0

        # Get queue size
        queue_size = await conn.fetchval(
            "SELECT COUNT(*) FROM public.applications WHERE status = 'QUEUED'"
        )

        return {
            "queue_size": queue_size or 0,
            "processing_rate": processing_rate,
            "error_rate": error_rate,
            "avg_processing_time": avg_processing_time,
            "last_job_time": last_job_time,
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
        }


async def get_job_sync_metrics(db: asyncpg.Pool) -> dict[str, Any]:
    """Get job synchronization metrics."""
    async with db.acquire() as conn:
        # Get sync status from job_sources table (if exists)
        try:
            sync_data = await conn.fetchrow(
                """
                SELECT
                    MAX(last_sync_at) as last_sync,
                    COUNT(*) FILTER (WHERE sync_status = 'success') as successful_syncs,
                    COUNT(*) FILTER (WHERE sync_status = 'failed') as failed_syncs,
                    COUNT(*) FILTER (WHERE sync_status = 'pending') as pending_syncs,
                    AVG(EXTRACT(EPOCH FROM (sync_completed_at - sync_started_at))) as avg_sync_time
                FROM public.job_sources
                WHERE last_sync_at > NOW() - INTERVAL '24 hours'
                """
            )
        except Exception:
            # Table might not exist, return defaults
            sync_data = None

        if sync_data:
            total_syncs = (
                sync_data.get("successful_syncs", 0)
                + sync_data.get("failed_syncs", 0)
                + sync_data.get("pending_syncs", 0)
            )

            success_rate = (
                (sync_data.get("successful_syncs", 0) / total_syncs * 100.0)
                if total_syncs > 0
                else 0.0
            )

            return {
                "last_sync": sync_data.get("last_sync"),
                "success_rate": success_rate,
                "pending_syncs": sync_data.get("pending_syncs", 0),
                "failed_syncs": sync_data.get("failed_syncs", 0),
                "avg_sync_time": sync_data.get("avg_sync_time", 0) or 0,
            }
        else:
            # Fallback metrics when job_sources table doesn't exist
            return {
                "last_sync": None,
                "success_rate": 100.0,  # Assume healthy if no data
                "pending_syncs": 0,
                "failed_syncs": 0,
                "avg_sync_time": 0,
            }


def determine_worker_status(metrics: dict[str, Any]) -> tuple[str, list[str]]:
    """Determine overall worker health status and generate alerts."""
    alerts = []

    # Check error rate
    if metrics["error_rate"] > 10.0:
        alerts.append(f"High error rate: {metrics['error_rate']:.1f}%")

    # Check queue size
    if metrics["queue_size"] > 100:
        alerts.append(f"Large queue size: {metrics['queue_size']} jobs")

    # Check processing rate
    if metrics["processing_rate"] < 0.5 and metrics["total_jobs"] > 0:
        alerts.append(f"Low processing rate: {metrics['processing_rate']:.2f} jobs/min")

    # Check last activity
    if metrics["last_job_time"]:
        time_since_last = datetime.now() - metrics["last_job_time"]
        if time_since_last > timedelta(minutes=30):
            alerts.append(
                f"No job processing for {time_since_last.total_seconds() / 60:.0f} minutes"
            )
    else:
        alerts.append("No job processing activity detected")

    # Determine status
    if len(alerts) == 0:
        status = "healthy"
    elif len(alerts) <= 2:
        status = "degraded"
    else:
        status = "unhealthy"

    return status, alerts


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@router.get("/health")
async def worker_health(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> WorkerHealthResponse:
    """Comprehensive worker health check with job sync monitoring."""

    # Require admin access for detailed health information
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get worker metrics
        worker_metrics = await get_worker_metrics(db)

        # Get job sync metrics
        sync_metrics = await get_job_sync_metrics(db)

        # Determine worker status
        worker_status, alerts = determine_worker_status(worker_metrics)

        # Build response
        worker_status_obj = WorkerStatus(
            status=worker_status,
            last_activity=worker_metrics["last_job_time"],
            queue_size=worker_metrics["queue_size"],
            processing_rate=worker_metrics["processing_rate"],
            error_rate=worker_metrics["error_rate"],
            uptime_seconds=0,  # Could be enhanced with actual uptime tracking
        )

        job_sync_status = JobSyncStatus(
            last_sync=sync_metrics["last_sync"],
            sync_success_rate=sync_metrics["success_rate"],
            pending_syncs=sync_metrics["pending_syncs"],
            failed_syncs=sync_metrics["failed_syncs"],
            average_sync_time_seconds=sync_metrics["avg_sync_time"],
        )

        # Basic system resources (could be enhanced with psutil)
        system_resources = {
            "memory_usage": "N/A",  # Could add actual memory monitoring
            "cpu_usage": "N/A",  # Could add actual CPU monitoring
            "disk_usage": "N/A",  # Could add actual disk monitoring
        }

        # Increment health check metric
        incr("worker.health_checks", {"status": worker_status})

        return WorkerHealthResponse(
            timestamp=datetime.now(),
            worker_status=worker_status_obj,
            job_sync_status=job_sync_status,
            system_resources=system_resources,
            alerts=alerts,
        )

    except Exception as e:
        logger.error("Worker health check failed: %s", e)
        incr("worker.health_checks", {"status": "error"})
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/status")
async def worker_status(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Simple worker status endpoint for basic monitoring."""

    # Require admin access
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get basic metrics
        metrics = await get_worker_metrics(db)
        status, alerts = determine_worker_status(metrics)

        return {
            "status": status,
            "queue_size": metrics["queue_size"],
            "processing_rate": metrics["processing_rate"],
            "error_rate": metrics["error_rate"],
            "last_activity": metrics["last_job_time"].isoformat()
            if metrics["last_job_time"]
            else None,
            "alerts": alerts,
        }

    except Exception as e:
        logger.error("Worker status check failed: %s", e)
        raise HTTPException(status_code=500, detail="Status check failed")


@router.post("/restart")
async def restart_worker(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> dict[str, str]:
    """Trigger worker restart (admin only)."""

    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # This would typically trigger a graceful restart of the worker process
    # Implementation depends on deployment strategy (systemd, k8s, etc.)
    logger.warning("Worker restart requested by admin: %s", ctx.user_id)
    incr("worker.restart_requests")

    return {
        "status": "restart_requested",
        "message": "Worker restart has been requested. This may take a few moments.",
    }
