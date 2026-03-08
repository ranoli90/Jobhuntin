"""API endpoints for DLQ management and concurrent usage tracking.

This module provides FastAPI endpoints for:
- DLQ inspection and management
- Concurrent usage monitoring
- Retry operations for failed applications
- Admin dashboard functionality
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.domain.tenant import TenantContext


async def get_tenant_context() -> TenantContext:
    raise NotImplementedError("Tenant context dependency not injected")


try:
    from apps.worker.dlq_manager import get_dlq_manager, DLQItem, RetryResult
except ImportError:
    get_dlq_manager = None
    DLQItem = None
    RetryResult = None

try:
    from apps.worker.concurrent_tracker import get_concurrent_tracker
except ImportError:
    get_concurrent_tracker = None
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.dlq_api")

router = APIRouter(prefix="/admin/dlq", tags=["dlq"])


async def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_tenant_ctx():
    raise NotImplementedError("Tenant context dependency not injected")


async def _get_admin_user_id():
    raise NotImplementedError("Admin user ID dependency not injected")


# Pydantic models
class DLQItemResponse(BaseModel):
    id: str
    application_id: str
    tenant_id: Optional[str]
    failure_reason: str
    attempt_count: int
    last_error: str
    payload: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dlq_item(cls, item: DLQItem) -> "DLQItemResponse":
        return cls(
            id=item.id,
            application_id=item.application_id,
            tenant_id=item.tenant_id,
            failure_reason=item.failure_reason,
            attempt_count=item.attempt_count,
            last_error=item.last_error,
            payload=item.payload,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class RetryRequest(BaseModel):
    item_ids: List[str] = Field(..., description="List of DLQ item IDs to retry")
    force: bool = Field(
        False, description="Force retry even if application not in FAILED status"
    )


class RetryResponse(BaseModel):
    results: List[RetryResult]
    success_count: int
    failure_count: int


class BulkDeleteRequest(BaseModel):
    tenant_id: Optional[str] = None
    failure_reason: Optional[str] = None
    older_than_days: Optional[int] = Field(
        None, ge=1, description="Delete items older than N days"
    )


class ConcurrentUsageResponse(BaseModel):
    total_active: int
    active_by_tenant: Dict[str, int]
    peak_usage: int
    peak_timestamp: datetime
    max_concurrent: int
    max_per_tenant: int


# Dependency to get DLQ manager
async def get_dlq_manager_dep() -> get_dlq_manager:
    """Get DLQ manager instance."""
    settings = get_settings()
    # TODO: Get database pool from settings
    # For now, return a placeholder
    raise NotImplementedError("Database pool dependency needed")


@router.get("/items", response_model=List[DLQItemResponse])
async def get_dlq_items(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    limit: int = Query(50, ge=1, le=1000, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    failure_reason: Optional[str] = Query(None, description="Filter by failure reason"),
    date_from: Optional[datetime] = Query(
        None, description="Filter items from this date"
    ),
    date_to: Optional[datetime] = Query(None, description="Filter items to this date"),
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Get items from the dead letter queue."""
    # Require admin access
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        items = await dlq_manager.get_dlq_items(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            failure_reason=failure_reason,
            date_from=date_from,
            date_to=date_to,
        )
        return [DLQItemResponse.from_dlq_item(item) for item in items]
    except Exception as e:
        logger.error("Failed to get DLQ items: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve DLQ items")


@router.get("/items/{item_id}", response_model=DLQItemResponse)
async def get_dlq_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Get a specific DLQ item by ID."""
    try:
        item = await dlq_manager.get_dlq_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="DLQ item not found")
        return DLQItemResponse.from_dlq_item(item)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get DLQ item %s: %s", item_id, e)
        raise HTTPException(status_code=500, detail="Failed to retrieve DLQ item")


@router.get("/stats")
async def get_dlq_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Get statistics about the dead letter queue."""
    # Require admin access
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        stats = await dlq_manager.get_dlq_stats(tenant_id)
        return stats
    except Exception as e:
        logger.error("Failed to get DLQ stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve DLQ statistics")


@router.post("/retry", response_model=RetryResponse)
async def retry_applications(
    request: RetryRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Retry failed applications from the DLQ."""
    # Require admin access
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        results = await dlq_manager.batch_retry_applications(
            item_ids=request.item_ids, force=request.force
        )

        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        return RetryResponse(
            results=results, success_count=success_count, failure_count=failure_count
        )
    except Exception as e:
        logger.error("Failed to retry applications: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retry applications")


@router.post("/retry/{item_id}", response_model=RetryResult)
async def retry_single_application(
    item_id: str,
    force: bool = Query(
        False, description="Force retry even if application not in FAILED status"
    ),
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Retry a single failed application from the DLQ."""
    try:
        result = await dlq_manager.retry_application(item_id, force=force)
        return result
    except Exception as e:
        logger.error("Failed to retry application %s: %s", item_id, e)
        raise HTTPException(status_code=500, detail="Failed to retry application")


@router.delete("/items/{item_id}")
async def delete_dlq_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Delete an item from the DLQ without retrying."""
    try:
        success = await dlq_manager.delete_dlq_item(item_id)
        if not success:
            raise HTTPException(status_code=404, detail="DLQ item not found")
        return {"message": "DLQ item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete DLQ item %s: %s", item_id, e)
        raise HTTPException(status_code=500, detail="Failed to delete DLQ item")


@router.post("/bulk-delete")
async def bulk_delete_dlq_items(
    request: BulkDeleteRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Bulk delete DLQ items based on criteria."""
    try:
        deleted_count = await dlq_manager.bulk_delete_dlq_items(
            tenant_id=request.tenant_id,
            failure_reason=request.failure_reason,
            older_than_days=request.older_than_days,
        )
        return {"deleted_count": deleted_count}
    except Exception as e:
        logger.error("Failed to bulk delete DLQ items: %s", e)
        raise HTTPException(status_code=500, detail="Failed to bulk delete DLQ items")


@router.get("/failure-reasons")
async def get_failure_reasons(
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Get list of unique failure reasons."""
    try:
        reasons = await dlq_manager.get_failure_reasons()
        return {"failure_reasons": reasons}
    except Exception as e:
        logger.error("Failed to get failure reasons: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve failure reasons"
        )


@router.get("/tenant/{tenant_id}/summary")
async def get_tenant_dlq_summary(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Get DLQ summary for a specific tenant."""
    try:
        summary = await dlq_manager.get_tenant_dlq_summary(tenant_id)
        return summary
    except Exception as e:
        logger.error("Failed to get tenant DLQ summary for %s: %s", tenant_id, e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve tenant DLQ summary"
        )


# Concurrent usage endpoints
@router.get("/concurrent-usage", response_model=ConcurrentUsageResponse)
async def get_concurrent_usage(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Get current concurrent usage statistics."""
    try:
        tracker = get_concurrent_tracker()
        stats = await tracker.get_stats()

        settings = get_settings()

        return ConcurrentUsageResponse(
            total_active=stats.total_active,
            active_by_tenant=stats.active_by_tenant,
            peak_usage=stats.peak_usage,
            peak_timestamp=datetime.fromtimestamp(
                stats.peak_timestamp, tz=timezone.utc
            ),
            max_concurrent=getattr(settings, "max_concurrent_applications", 10),
            max_per_tenant=getattr(settings, "max_concurrent_per_tenant", 3),
        )
    except Exception as e:
        logger.error("Failed to get concurrent usage stats: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve concurrent usage statistics"
        )


@router.get("/concurrent-usage/reset")
async def reset_concurrent_usage_stats(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Reset peak concurrent usage statistics."""
    try:
        tracker = get_concurrent_tracker()
        await tracker.reset_stats()
        return {"message": "Concurrent usage statistics reset successfully"}
    except Exception as e:
        logger.error("Failed to reset concurrent usage stats: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to reset concurrent usage statistics"
        )


@router.get("/active-tasks")
async def get_active_tasks(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Get list of currently active task IDs."""
    try:
        tracker = get_concurrent_tracker()
        active_tasks = await tracker.get_active_tasks()
        return {"active_tasks": list(active_tasks)}
    except Exception as e:
        logger.error("Failed to get active tasks: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve active tasks")


@router.get("/health")
async def dlq_health_check(
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Health check for DLQ system."""
    try:
        # Get basic stats
        stats = await dlq_manager.get_dlq_stats()

        # Check concurrent usage
        tracker = get_concurrent_tracker()
        concurrent_stats = await tracker.get_stats()

        return {
            "status": "healthy",
            "dlq_stats": {
                "total_items": stats.get("total_items", 0),
                "unique_tenants": stats.get("unique_tenants", 0),
                "oldest_item_age_hours": None,  # TODO: Calculate from oldest_item
            },
            "concurrent_usage": {
                "total_active": concurrent_stats.total_active,
                "peak_usage": concurrent_stats.peak_usage,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error("DLQ health check failed: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
