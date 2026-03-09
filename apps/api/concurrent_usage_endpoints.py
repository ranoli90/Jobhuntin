"""
Concurrent Usage API Endpoints for Phase 12.1 Agent Improvements
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from packages.backend.domain.concurrent_tracker import (
    ConcurrentTracker,
    get_concurrent_tracker,
)
from packages.backend.domain.tenant import TenantContext

router = APIRouter(prefix="/concurrent-usage", tags=["concurrent-usage"])


async def get_tenant_context() -> TenantContext:
    """Tenant context dependency; override in main app."""
    raise NotImplementedError("Tenant context dependency not injected")


# Pydantic models
class ConcurrentSessionRequest(BaseModel):
    """Concurrent session creation request."""

    user_id: str = Field(..., description="User ID")
    application_id: Optional[str] = Field(None, description="Application ID")
    total_steps: int = Field(default=0, description="Total number of steps")


class ConcurrentSessionResponse(BaseModel):
    """Concurrent session response."""

    session_id: str
    user_id: str
    tenant_id: str
    application_id: Optional[str]
    status: str
    steps_completed: int
    total_steps: int
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[int]


class ConcurrentStatsResponse(BaseModel):
    """Concurrent usage statistics response."""

    total_active: int
    max_concurrent: int
    current_concurrent: int
    peak_concurrent: int
    active_sessions: List[str]
    tenant_stats: Dict[str, Dict[str, int]]


# Use imported get_concurrent_tracker for Depends()


@router.post("/track-session")
async def track_concurrent_session(
    request: ConcurrentSessionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> ConcurrentSessionResponse:
    """Track a concurrent usage session."""
    try:
        session_id = str(uuid.uuid4())

        session = await tracker.track_session(
            session_id=session_id,
            user_id=request.user_id,
            tenant_id=ctx.tenant_id,
            application_id=request.application_id,
            total_steps=request.total_steps,
        )

        return ConcurrentSessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            application_id=session.application_id,
            status=session.status,
            steps_completed=session.steps_completed,
            total_steps=session.total_steps,
            start_time=session.start_time.isoformat(),
            end_time=session.end_time.isoformat() if session.end_time else None,
            duration_seconds=session.duration_seconds,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track session: {str(e)}"
        )


@router.post("/complete-session")
async def complete_concurrent_session(
    session_id: str,
    status: str = "completed",
    error_count: int = 0,
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> Dict[str, str]:
    """Complete a concurrent usage session."""
    try:
        success = await tracker.complete_session(session_id, status, error_count)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "status": status,
            "message": "Session completed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to complete session: {str(e)}"
        )


@router.post("/fail-session")
async def fail_concurrent_session(
    session_id: str,
    error_count: int = 1,
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> Dict[str, str]:
    """Mark a concurrent usage session as failed."""
    try:
        success = await tracker.fail_session(session_id, error_count)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "status": "failed",
            "error_count": error_count,
            "message": "Session marked as failed",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fail session: {str(e)}")


@router.get("/sessions")
async def get_concurrent_sessions(
    session_id: Optional[str] = Query(None, description="Get specific session by ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> Dict[str, Any]:
    """Get concurrent usage sessions."""
    try:
        if session_id:
            # Get specific session
            session = tracker.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            return {
                "session": {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "tenant_id": session.tenant_id,
                    "application_id": session.application_id,
                    "status": session.status,
                    "steps_completed": session.steps_completed,
                    "total_steps": session.total_steps,
                    "error_count": session.error_count,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat()
                    if session.end_time
                    else None,
                    "duration_seconds": session.duration_seconds,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                }
            }
        else:
            # Get all active sessions
            active_sessions = tracker.get_active_sessions()

            # Filter sessions
            filtered_sessions = active_sessions
            if user_id:
                filtered_sessions = [
                    s for s in filtered_sessions if s.user_id == user_id
                ]
            if status:
                filtered_sessions = [s for s in filtered_sessions if s.status == status]

            # Apply pagination
            total = len(filtered_sessions)
            paginated_sessions = filtered_sessions[offset : offset + limit]

            return {
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "user_id": s.user_id,
                        "tenant_id": s.tenant_id,
                        "application_id": s.application_id,
                        "status": s.status,
                        "steps_completed": s.steps_completed,
                        "total_steps": s.total_steps,
                        "error_count": s.error_count,
                        "start_time": s.start_time.isoformat(),
                        "end_time": s.end_time.isoformat() if s.end_time else None,
                        "duration_seconds": s.duration_seconds,
                    }
                    for s in paginated_sessions
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.get("/active-tasks")
async def get_active_tasks(
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> Dict[str, List[str]]:
    """Get list of currently active task IDs."""
    try:
        active_tasks = tracker.get_active_tasks()

        return {
            "active_tasks": active_tasks,
            "total": len(active_tasks),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get active tasks: {str(e)}"
        )


@router.get("/stats")
async def get_concurrent_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> ConcurrentStatsResponse:
    """Get concurrent usage statistics."""
    try:
        stats = tracker.get_stats()

        return ConcurrentStatsResponse(
            total_active=stats.total_active,
            max_concurrent=stats.max_concurrent,
            current_concurrent=stats.current_concurrent,
            peak_concurrent=stats.peak_concurrent,
            active_sessions=stats.active_sessions,
            tenant_stats=stats.tenant_stats,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/tenant-stats")
async def get_tenant_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> Dict[str, Any]:
    """Get concurrent usage statistics for the current tenant."""
    try:
        tenant_stats = tracker.get_tenant_stats(ctx.tenant_id)

        return {
            "tenant_id": ctx.tenant_id,
            "stats": tenant_stats,
            "message": "Tenant statistics retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get tenant stats: {str(e)}"
        )


@router.post("/reset-stats")
async def reset_peak_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> Dict[str, str]:
    """Reset peak concurrent usage statistics."""
    try:
        await tracker.reset_stats()

        return {
            "message": "Peak statistics reset successfully",
            "tenant_id": ctx.tenant_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset stats: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_sessions(
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age in hours"),
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> Dict[str, Any]:
    """Clean up old session data."""
    try:
        cleaned_count = await tracker.cleanup_old_sessions(max_age_hours)

        return {
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours,
            "message": f"Cleaned up {cleaned_count} old sessions",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup sessions: {str(e)}"
        )


@router.get("/overview")
async def get_concurrent_overview(
    ctx: TenantContext = Depends(get_tenant_context),
    tracker: ConcurrentTracker = Depends(get_concurrent_tracker),
) -> Dict[str, Any]:
    """Get comprehensive concurrent usage overview."""
    try:
        stats = tracker.get_stats()
        active_sessions = tracker.get_active_tasks()
        tenant_stats = tracker.get_tenant_stats(ctx.tenant_id)

        return {
            "overview": {
                "total_active": stats.total_active,
                "current_concurrent": stats.current_concurrent,
                "max_concurrent": stats.max_concurrent,
                "peak_concurrent": stats.peak_concurrent,
                "active_tasks": active_sessions,
                "tenant_stats": tenant_stats,
            },
            "message": "Concurrent usage overview retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for concurrent usage system."""
    return {
        "status": "healthy",
        "service": "concurrent_tracker",
        "features": [
            "session_tracking",
            "concurrent_monitoring",
            "tenant_statistics",
            "cleanup_management",
        ],
    }
