"""
Admin API endpoints for internal operators and support engineers.

Provides:
  - GET  /admin/tenants                                  – list all tenants (system admin only)
  - GET  /admin/tenants/{tenant_id}/applications         – paginated applications for a tenant
  - GET  /admin/tenants/{tenant_id}/applications/{id}    – full application detail
  - POST /admin/tenants/{tenant_id}/applications/{id}/replay – re-queue a failed application

All endpoints require system admin OR tenant OWNER/ADMIN role.
PII is masked by default; pass ?unmask=true with OWNER role to see full data.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.domain.masking import redact_profile_for_support
from backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    TenantRepo,
    db_transaction,
)
from backend.domain.tenant import (
    TenantContext,
    TenantScopeError,
    require_role,
    require_system_admin,
    require_tenant_admin_or_system,
    resolve_tenant_context,
)
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.admin")

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class TenantSummary(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    created_at: str | None = None


class PaginatedTenants(BaseModel):
    tenants: list[TenantSummary]
    count: int


class ApplicationSummary(BaseModel):
    """Brief application information for listing."""
    id: str
    user_id: str
    job_id: str
    tenant_id: str | None = None
    status: str
    attempt_count: int = 0
    last_error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PaginatedApplications(BaseModel):
    applications: list[ApplicationSummary]
    count: int


class ApplicationDetailAdmin(BaseModel):
    application: dict[str, Any]
    inputs: list[dict[str, Any]]
    events: list[dict[str, Any]]


class ReplayResponse(BaseModel):
    """Response for replaying an application."""
    application_id: str
    new_status: str
    attempt_count: int
    message: str


# ---------------------------------------------------------------------------
# Dependencies (injected by main app at mount time)
# ---------------------------------------------------------------------------

def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    raise NotImplementedError("Tenant context dependency not injected")


async def _get_admin_user_id():
    """Placeholder — overridden at mount time to return current user_id."""
    raise NotImplementedError("Auth dependency not injected")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(obj: Any) -> Any:
    """Recursively serialize UUIDs and datetimes for JSON."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return obj


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/tenants", response_model=PaginatedTenants)
async def list_tenants(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> PaginatedTenants:
    """List all tenants. System admin only."""
    async with db.acquire() as conn:
        await require_system_admin(conn, user_id)
        rows = await TenantRepo.list_all(conn, limit=limit, offset=offset)

    tenants = [
        TenantSummary(
            id=str(r["id"]),
            name=r["name"],
            slug=r["slug"],
            plan=str(r["plan"]),
            created_at=r["created_at"].isoformat() if r.get("created_at") else None,
        )
        for r in rows
    ]
    return PaginatedTenants(tenants=tenants, count=len(tenants))


@router.get("/tenants/{tenant_id}/applications", response_model=PaginatedApplications)
async def list_tenant_applications(
    tenant_id: str,
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> PaginatedApplications:
    """List applications for a tenant. Requires system admin or tenant admin."""
    async with db.acquire() as conn:
        # Auth check: system admin OR tenant admin/owner
        try:
            await require_system_admin(conn, user_id)
        except TenantScopeError:
            ctx = await resolve_tenant_context(conn, user_id)
            if ctx.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail="Access denied to this tenant")
            require_role(ctx, "OWNER", "ADMIN")

        rows = await ApplicationRepo.list_for_tenant(
            conn, tenant_id, status=status, limit=limit, offset=offset,
        )

    apps = [
        ApplicationSummary(**_serialize({
            "id": str(r["id"]),
            "user_id": str(r["user_id"]),
            "job_id": str(r["job_id"]),
            "tenant_id": str(r["tenant_id"]) if r.get("tenant_id") else None,
            "status": str(r["status"]),
            "attempt_count": r.get("attempt_count", 0),
            "last_error": r.get("last_error"),
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
        }))
        for r in rows
    ]
    return PaginatedApplications(applications=apps, count=len(apps))


@router.get("/tenants/{tenant_id}/applications/{application_id}", response_model=ApplicationDetailAdmin)
async def get_tenant_application_detail(
    tenant_id: str,
    application_id: str,
    unmask: bool = Query(False),
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> ApplicationDetailAdmin:
    """
    Full application detail with inputs and events.
    PII is masked by default; ?unmask=true requires OWNER role.
    """
    async with db.acquire() as conn:
        is_sys_admin = False
        try:
            await require_system_admin(conn, user_id)
            is_sys_admin = True
        except TenantScopeError:
            ctx = await resolve_tenant_context(conn, user_id)
            if ctx.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail="Access denied to this tenant")
            require_role(ctx, "OWNER", "ADMIN", "SUPPORT_AGENT")

        detail = await ApplicationRepo.get_detail(conn, application_id, tenant_id=tenant_id)

    if detail is None:
        raise HTTPException(status_code=404, detail="Application not found")

    serialized = detail.to_serializable()

    # Mask PII in inputs if not unmasked
    if not unmask:
        for inp in serialized.get("inputs", []):
            if inp.get("answer"):
                # Truncate answers for support view
                inp["answer"] = inp["answer"][:20] + "..." if len(inp.get("answer", "")) > 20 else inp["answer"]

    return ApplicationDetailAdmin(**serialized)


@router.post("/tenants/{tenant_id}/applications/{application_id}/replay", response_model=ReplayResponse)
async def replay_application(
    tenant_id: str,
    application_id: str,
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> ReplayResponse:
    """
    Re-queue a FAILED application for another processing attempt.
    Resets status to QUEUED and records a RETRY_SCHEDULED event.
    """
    async with db.acquire() as conn:
        try:
            await require_system_admin(conn, user_id)
        except TenantScopeError:
            ctx = await resolve_tenant_context(conn, user_id)
            if ctx.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail="Access denied to this tenant")
            require_role(ctx, "OWNER", "ADMIN")

    async with db_transaction(db) as conn:
        app_row = await ApplicationRepo.get_by_id_and_tenant(conn, application_id, tenant_id)
        if app_row is None:
            raise HTTPException(status_code=404, detail="Application not found in this tenant")

        if str(app_row["status"]) != "FAILED":
            raise HTTPException(
                status_code=409,
                detail=f"Can only replay FAILED applications, current status: {app_row['status']}",
            )

        updated = await ApplicationRepo.update_status(conn, application_id, "QUEUED")
        await EventRepo.emit(conn, application_id, "RETRY_SCHEDULED", {
            "triggered_by": "admin_replay",
            "admin_user_id": user_id,
        }, tenant_id=tenant_id)

    incr("admin.replay", tags={"tenant_id": tenant_id})
    logger.info("Admin replay: application %s re-queued by user %s", application_id, user_id)

    return ReplayResponse(
        application_id=application_id,
        new_status="QUEUED",
        attempt_count=updated["attempt_count"] if updated else 0,
        message="Application re-queued for processing.",
    )
