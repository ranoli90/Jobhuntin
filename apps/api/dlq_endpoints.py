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
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.deps import (
    get_pool as _get_pool,
    get_tenant_context,
    get_tenant_context as _get_tenant_ctx,
    require_admin_user_id as _get_admin_user_id,
)
from packages.backend.domain.tenant import TenantContext
from shared.config import get_settings
from shared.logging_config import get_logger

try:
    from apps.worker.dlq_manager import DLQItem, RetryResult, get_dlq_manager
except ImportError:
    get_dlq_manager = None
    DLQItem = None
    RetryResult = None

try:
    from apps.worker.concurrent_tracker import get_concurrent_tracker
except ImportError:
    get_concurrent_tracker = None


# Stub DLQ manager returned when real implementation is not available.
# Methods raise NotImplementedError so endpoints can catch and return 501.
class _StubDLQManager:
    def __getattr__(self, name: str):
        async def _raise(*args: Any, **kwargs: Any) -> None:
            raise NotImplementedError("DLQ management not implemented")

        return _raise

logger = get_logger("sorce.dlq_api")

router = APIRouter(prefix="/admin/dlq", tags=["dlq"])


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
    item_ids: List[str] = Field(
        ..., max_length=100, description="List of DLQ item IDs to retry"
    )
    force: bool = Field(
        False, description="Force retry even if application not in FAILED status"
    )


class RetryResponse(BaseModel):
    results: List[RetryResult]
    success_count: int
    failure_count: int


class BulkDeleteRequest(BaseModel):
    tenant_id: Optional[str] = Field(None, max_length=36)
    failure_reason: Optional[str] = Field(None, max_length=500)
    older_than_days: Optional[int] = Field(
        None, ge=1, le=365, description="Delete items older than N days"
    )


class ConcurrentUsageResponse(BaseModel):
    total_active: int
    active_by_tenant: Dict[str, int]
    peak_usage: int
    peak_timestamp: datetime
    max_concurrent: int
    max_per_tenant: int


async def _require_tenant_scope_or_system_admin(
    pool, user_id: str, ctx: TenantContext, requested_tenant_id: str
) -> None:
    """Tenant admin can only access own tenant; system admin can access any."""
    from packages.backend.domain.tenant import TenantScopeError, require_system_admin

    async with pool.acquire() as conn:
        try:
            await require_system_admin(conn, user_id)
            return
        except TenantScopeError:
            pass
    if ctx.tenant_id != requested_tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")


# Dependency to get DLQ manager
async def get_dlq_manager_dep(pool=Depends(_get_pool)):
    """Get DLQ manager instance. Uses real implementation when available."""
    try:
        from apps.worker.dlq_manager import DLQManager

        return DLQManager(pool)
    except ImportError:
        return _StubDLQManager()


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
    pool=Depends(_get_pool),
):
    """Get items from the dead letter queue."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    effective_tenant_id = tenant_id
    if tenant_id is not None:
        await _require_tenant_scope_or_system_admin(
            pool, ctx.user_id, ctx, tenant_id
        )
    else:
        from packages.backend.domain.tenant import (
            TenantScopeError,
            require_system_admin,
        )

        async with pool.acquire() as conn:
            try:
                await require_system_admin(conn, ctx.user_id)
            except TenantScopeError:
                effective_tenant_id = ctx.tenant_id
    try:
        items = await dlq_manager.get_dlq_items(
            tenant_id=effective_tenant_id,
            limit=limit,
            offset=offset,
            failure_reason=failure_reason,
            date_from=date_from,
            date_to=date_to,
        )
        return [DLQItemResponse.from_dlq_item(item) for item in items]
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
    except Exception as e:
        logger.error("Failed to get DLQ items: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve DLQ items")


@router.get("/items/{item_id}", response_model=DLQItemResponse)
async def get_dlq_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
    pool=Depends(_get_pool),
):
    """Get a specific DLQ item by ID."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        item = await dlq_manager.get_dlq_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="DLQ item not found")
        if item.tenant_id:
            await _require_tenant_scope_or_system_admin(
                pool, ctx.user_id, ctx, item.tenant_id
            )
        return DLQItemResponse.from_dlq_item(item)
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
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
    pool=Depends(_get_pool),
):
    """Get statistics about the dead letter queue."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    effective_tenant_id = tenant_id
    if tenant_id is not None:
        await _require_tenant_scope_or_system_admin(
            pool, ctx.user_id, ctx, tenant_id
        )
    else:
        from packages.backend.domain.tenant import (
            TenantScopeError,
            require_system_admin,
        )

        async with pool.acquire() as conn:
            try:
                await require_system_admin(conn, ctx.user_id)
            except TenantScopeError:
                effective_tenant_id = ctx.tenant_id
    try:
        stats = await dlq_manager.get_dlq_stats(effective_tenant_id)
        return stats
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
    except Exception as e:
        logger.error("Failed to get DLQ stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve DLQ statistics")


@router.post("/retry", response_model=RetryResponse)
async def retry_applications(
    request: RetryRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
    pool=Depends(_get_pool),
):
    """Retry failed applications from the DLQ."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    from packages.backend.domain.tenant import TenantScopeError, require_system_admin

    async with pool.acquire() as conn:
        try:
            await require_system_admin(conn, ctx.user_id)
        except TenantScopeError:
            for item_id in request.item_ids:
                item = await dlq_manager.get_dlq_item(item_id)
                if item and item.tenant_id and item.tenant_id != ctx.tenant_id:
                    raise HTTPException(
                        status_code=403, detail="Access denied to this tenant"
                    )
    try:
        results = await dlq_manager.batch_retry_applications(
            item_ids=request.item_ids, force=request.force
        )

        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        return RetryResponse(
            results=results, success_count=success_count, failure_count=failure_count
        )
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
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
    pool=Depends(_get_pool),
):
    """Retry a single failed application from the DLQ."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    item = await dlq_manager.get_dlq_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    if item.tenant_id:
        await _require_tenant_scope_or_system_admin(
            pool, ctx.user_id, ctx, item.tenant_id
        )
    try:
        result = await dlq_manager.retry_application(item_id, force=force)
        return result
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
    except Exception as e:
        logger.error("Failed to retry application %s: %s", item_id, e)
        raise HTTPException(status_code=500, detail="Failed to retry application")


@router.delete("/items/{item_id}")
async def delete_dlq_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
    pool=Depends(_get_pool),
):
    """Delete an item from the DLQ without retrying."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    item = await dlq_manager.get_dlq_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    if item.tenant_id:
        await _require_tenant_scope_or_system_admin(
            pool, ctx.user_id, ctx, item.tenant_id
        )
    try:
        success = await dlq_manager.delete_dlq_item(item_id)
        if not success:
            raise HTTPException(status_code=404, detail="DLQ item not found")
        return {"message": "DLQ item deleted successfully"}
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
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
    pool=Depends(_get_pool),
):
    """Bulk delete DLQ items based on criteria."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    effective_tenant_id = request.tenant_id
    if request.tenant_id is not None:
        await _require_tenant_scope_or_system_admin(
            pool, ctx.user_id, ctx, request.tenant_id
        )
    else:
        from packages.backend.domain.tenant import (
            TenantScopeError,
            require_system_admin,
        )

        async with pool.acquire() as conn:
            try:
                await require_system_admin(conn, ctx.user_id)
            except TenantScopeError:
                effective_tenant_id = ctx.tenant_id
    try:
        deleted_count = await dlq_manager.bulk_delete_dlq_items(
            tenant_id=effective_tenant_id,
            failure_reason=request.failure_reason,
            older_than_days=request.older_than_days,
        )
        return {"deleted_count": deleted_count}
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
    except Exception as e:
        logger.error("Failed to bulk delete DLQ items: %s", e)
        raise HTTPException(status_code=500, detail="Failed to bulk delete DLQ items")


@router.get("/failure-reasons")
async def get_failure_reasons(
    ctx: TenantContext = Depends(get_tenant_context),
    dlq_manager: get_dlq_manager = Depends(get_dlq_manager_dep),
):
    """Get list of unique failure reasons."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        reasons = await dlq_manager.get_failure_reasons()
        return {"failure_reasons": reasons}
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
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
    pool=Depends(_get_pool),
):
    """Get DLQ summary for a specific tenant."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    await _require_tenant_scope_or_system_admin(pool, ctx.user_id, ctx, tenant_id)
    try:
        summary = await dlq_manager.get_tenant_dlq_summary(tenant_id)
        return summary
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
    except Exception as e:
        logger.error("Failed to get tenant DLQ summary for %s: %s", tenant_id, e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve tenant DLQ summary"
        )


# Concurrent usage endpoints
@router.get("/concurrent-usage", response_model=ConcurrentUsageResponse)
async def get_concurrent_usage(
    ctx: TenantContext = Depends(get_tenant_context),
    pool=Depends(_get_pool),
):
    """Get current concurrent usage statistics."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        tracker = get_concurrent_tracker()
        if tracker is None:
            return JSONResponse(
                status_code=501,
                content={"detail": "Concurrent usage tracking not implemented"},
            )
        stats = await tracker.get_stats()

        from packages.backend.domain.tenant import (
            TenantScopeError,
            require_system_admin,
        )

        active_by_tenant = stats.active_by_tenant
        async with pool.acquire() as conn:
            try:
                await require_system_admin(conn, ctx.user_id)
            except TenantScopeError:
                active_by_tenant = {
                    k: v
                    for k, v in stats.active_by_tenant.items()
                    if k == ctx.tenant_id
                }

        settings = get_settings()

        return ConcurrentUsageResponse(
            total_active=stats.total_active,
            active_by_tenant=active_by_tenant,
            peak_usage=stats.peak_usage,
            peak_timestamp=datetime.fromtimestamp(
                stats.peak_timestamp, tz=timezone.utc
            ),
            max_concurrent=getattr(settings, "max_concurrent_applications", 10),
            max_per_tenant=getattr(settings, "max_concurrent_per_tenant", 3),
        )
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "Concurrent usage tracking not implemented"},
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
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        tracker = get_concurrent_tracker()
        if tracker is None:
            return JSONResponse(
                status_code=501,
                content={"detail": "Concurrent usage tracking not implemented"},
            )
        await tracker.reset_stats()
        return {"message": "Concurrent usage statistics reset successfully"}
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "Concurrent usage tracking not implemented"},
        )
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
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        tracker = get_concurrent_tracker()
        if tracker is None:
            return JSONResponse(
                status_code=501,
                content={"detail": "Concurrent usage tracking not implemented"},
            )
        active_tasks = await tracker.get_active_tasks()
        return {"active_tasks": list(active_tasks)}
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "Concurrent usage tracking not implemented"},
        )
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
        if tracker is None:
            return JSONResponse(
                status_code=501,
                content={"detail": "DLQ and concurrent usage tracking not implemented"},
            )
        concurrent_stats = await tracker.get_stats()

        oldest_item = stats.get("oldest_item")
        oldest_item_age_hours: Optional[float] = None
        if oldest_item:
            ts = (
                oldest_item
                if oldest_item.tzinfo
                else oldest_item.replace(tzinfo=timezone.utc)
            )
            delta = datetime.now(timezone.utc) - ts
            oldest_item_age_hours = round(delta.total_seconds() / 3600, 1)

        return {
            "status": "healthy",
            "dlq_stats": {
                "total_items": stats.get("total_items", 0),
                "unique_tenants": stats.get("unique_tenants", 0),
                "oldest_item_age_hours": oldest_item_age_hours,
            },
            "concurrent_usage": {
                "total_active": concurrent_stats.total_active,
                "peak_usage": concurrent_stats.peak_usage,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except NotImplementedError:
        return JSONResponse(
            status_code=501,
            content={"detail": "DLQ management not implemented"},
        )
    except Exception as e:
        logger.error("DLQ health check failed: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
