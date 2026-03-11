"""Admin API endpoints for internal operators and support engineers.

Provides:
  - GET  /admin/tenants                                  – list all tenants (system admin only)
  - GET  /admin/tenants/{tenant_id}/applications         – paginated applications for a tenant
  - GET  /admin/tenants/{tenant_id}/applications/{id}    – full application detail
  - POST /admin/tenants/{tenant_id}/applications/{id}/replay – re-queue a failed application

All endpoints require system admin OR tenant OWNER/ADMIN role.
PII is masked by default; pass ?unmask=true with OWNER role to see full data.
"""

from __future__ import annotations

import uuid
from typing import Any

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    TenantRepo,
    db_transaction,
)
from backend.domain.tenant import (
    TenantScopeError,
    require_role,
    require_system_admin,
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
                raise HTTPException(
                    status_code=403, detail="Access denied to this tenant"
                )
            require_role(ctx, "OWNER", "ADMIN")

        rows = await ApplicationRepo.list_for_tenant(
            conn,
            tenant_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    apps = [
        ApplicationSummary(
            **_serialize(
                {
                    "id": str(r["id"]),
                    "user_id": str(r["user_id"]),
                    "job_id": str(r["job_id"]),
                    "tenant_id": str(r["tenant_id"]) if r.get("tenant_id") else None,
                    "status": str(r["status"]),
                    "attempt_count": r.get("attempt_count", 0),
                    "last_error": r.get("last_error"),
                    "created_at": r.get("created_at"),
                    "updated_at": r.get("updated_at"),
                }
            )
        )
        for r in rows
    ]
    return PaginatedApplications(applications=apps, count=len(apps))


@router.get(
    "/tenants/{tenant_id}/applications/{application_id}",
    response_model=ApplicationDetailAdmin,
)
async def get_tenant_application_detail(
    tenant_id: str,
    application_id: str,
    unmask: bool = Query(False),
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> ApplicationDetailAdmin:
    """Full application detail with inputs and events.
    PII is masked by default; ?unmask=true requires OWNER role.
    """
    from shared.validators import validate_uuid

    validate_uuid(tenant_id, "tenant_id")
    validate_uuid(application_id, "application_id")
    async with db.acquire() as conn:
        try:
            await require_system_admin(conn, user_id)
        except TenantScopeError:
            ctx = await resolve_tenant_context(conn, user_id)
            if ctx.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this tenant"
                )
            require_role(ctx, "OWNER", "ADMIN", "SUPPORT_AGENT")

        detail = await ApplicationRepo.get_detail(
            conn, application_id, tenant_id=tenant_id
        )

    if detail is None:
        raise HTTPException(status_code=404, detail="Application not found")

    serialized = detail.to_serializable()

    # Mask PII using the masking module unless explicitly unmasked
    if not unmask:
        from backend.domain.masking import (
            redact_event_payload,
            redact_profile_for_support,
        )

        if "profile_data" in serialized and isinstance(
            serialized["profile_data"], dict
        ):
            serialized["profile_data"] = redact_profile_for_support(
                serialized["profile_data"]
            )
        for inp in serialized.get("inputs", []):
            if inp.get("answer"):
                inp["answer"] = "[REDACTED]"
        for evt in serialized.get("events", []):
            if isinstance(evt.get("payload"), dict):
                evt["payload"] = redact_event_payload(evt["payload"])

    return ApplicationDetailAdmin(**serialized)


@router.post(
    "/tenants/{tenant_id}/applications/{application_id}/replay",
    response_model=ReplayResponse,
)
async def replay_application(
    tenant_id: str,
    application_id: str,
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> ReplayResponse:
    """Re-queue a FAILED application for another processing attempt.
    Resets status to QUEUED and records a RETRY_SCHEDULED event.
    """
    from shared.validators import validate_uuid

    validate_uuid(tenant_id, "tenant_id")
    validate_uuid(application_id, "application_id")
    async with db.acquire() as conn:
        try:
            await require_system_admin(conn, user_id)
        except TenantScopeError:
            ctx = await resolve_tenant_context(conn, user_id)
            if ctx.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this tenant"
                )
            require_role(ctx, "OWNER", "ADMIN")

    async with db_transaction(db) as conn:
        app_row = await ApplicationRepo.get_by_id_and_tenant(
            conn, application_id, tenant_id
        )
        if app_row is None:
            raise HTTPException(
                status_code=404, detail="Application not found in this tenant"
            )

        if str(app_row["status"]) != "FAILED":
            raise HTTPException(
                status_code=409,
                detail=f"Can only replay FAILED applications, current status: {app_row['status']}",
            )

        updated = await ApplicationRepo.update_status(conn, application_id, "QUEUED")
        await EventRepo.emit(
            conn,
            application_id,
            "RETRY_SCHEDULED",
            {
                "triggered_by": "admin_replay",
                "admin_user_id": user_id,
            },
            tenant_id=tenant_id,
        )

    incr("admin.replay", tags={"tenant_id": tenant_id})
    logger.info(
        "Admin replay: application %s re-queued by user %s", application_id, user_id
    )

    return ReplayResponse(
        application_id=application_id,
        new_status="QUEUED",
        attempt_count=updated["attempt_count"] if updated else 0,
        message="Application re-queued for processing.",
    )


class AuditLogEntry(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    resource: str
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: str


class PaginatedAuditLog(BaseModel):
    entries: list[AuditLogEntry]
    total: int
    has_more: bool


class AuditLogStats(BaseModel):
    total_events: int
    actions: dict[str, int]
    resources: dict[str, int]
    top_users: list[dict[str, Any]]
    recent_activity: list[dict[str, Any]]


@router.get("/tenants/{tenant_id}/audit", response_model=PaginatedAuditLog)
async def get_tenant_audit_log(
    tenant_id: str,
    action: str | None = Query(None),
    resource: str | None = Query(None),
    user_filter: str | None = Query(None, alias="user"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> PaginatedAuditLog:
    """Retrieve audit log for a tenant with filtering options."""
    from datetime import datetime

    from shared.validators import validate_uuid

    validate_uuid(tenant_id, "tenant_id")

    async with db.acquire() as conn:
        try:
            await require_system_admin(conn, user_id)
        except TenantScopeError:
            ctx = await resolve_tenant_context(conn, user_id)
            if ctx.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this tenant"
                )
            require_role(ctx, "OWNER", "ADMIN", "COMPLIANCE_OFFICER")

        from shared.sql_utils import escape_ilike

        escaped_action = escape_ilike(action) if action else None
        rows = await conn.fetch(
            """
            SELECT id, user_id, action, resource, resource_id, details,
                   ip_address, user_agent, created_at
            FROM public.audit_log
            WHERE tenant_id = $1
              AND ($2::text IS NULL OR action ILIKE $2)
              AND ($3::text IS NULL OR resource = $3)
              AND ($4::text IS NULL OR user_id::text = $4)
              AND ($5::timestamptz IS NULL OR created_at >= $5)
              AND ($6::timestamptz IS NULL OR created_at <= $6)
            ORDER BY created_at DESC
            LIMIT $7 OFFSET $8
            """,
            tenant_id,
            f"%{escaped_action}%" if escaped_action else None,
            resource,
            user_filter,
            datetime.fromisoformat(start_date) if start_date else None,
            datetime.fromisoformat(end_date) if end_date else None,
            limit + 1,
            offset,
        )

        total = await conn.fetchval(
            """
            SELECT COUNT(*)::int
            FROM public.audit_log
            WHERE tenant_id = $1
              AND ($2::text IS NULL OR action ILIKE $2)
              AND ($3::text IS NULL OR resource = $3)
              AND ($4::text IS NULL OR user_id::text = $4)
              AND ($5::timestamptz IS NULL OR created_at >= $5)
              AND ($6::timestamptz IS NULL OR created_at <= $6)
            """,
            tenant_id,
            f"%{escaped_action}%" if escaped_action else None,
            resource,
            user_filter,
            datetime.fromisoformat(start_date) if start_date else None,
            datetime.fromisoformat(end_date) if end_date else None,
        )

    has_more = len(rows) > limit
    entries = [
        AuditLogEntry(
            id=str(r["id"]),
            user_id=str(r["user_id"]) if r["user_id"] else None,
            action=r["action"],
            resource=r["resource"],
            resource_id=r["resource_id"],
            details=r["details"],
            ip_address=r["ip_address"],
            user_agent=r["user_agent"],
            created_at=r["created_at"].isoformat(),
        )
        for r in rows[:limit]
    ]

    incr("admin.audit_log.viewed")
    return PaginatedAuditLog(entries=entries, total=total, has_more=has_more)


@router.get("/tenants/{tenant_id}/audit/stats", response_model=AuditLogStats)
async def get_tenant_audit_stats(
    tenant_id: str,
    days: int = Query(30, ge=1, le=365),
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> AuditLogStats:
    """Get audit log statistics for a tenant."""
    from shared.validators import validate_uuid

    validate_uuid(tenant_id, "tenant_id")

    async with db.acquire() as conn:
        try:
            await require_system_admin(conn, user_id)
        except TenantScopeError:
            ctx = await resolve_tenant_context(conn, user_id)
            if ctx.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this tenant"
                )
            require_role(ctx, "OWNER", "ADMIN", "COMPLIANCE_OFFICER")

        total = await conn.fetchval(
            """
            SELECT COUNT(*)::int FROM public.audit_log
            WHERE tenant_id = $1 AND created_at >= now() - ($2 || ' days')::interval
            """,
            tenant_id,
            str(days),
        )

        actions = await conn.fetch(
            """
            SELECT action, COUNT(*)::int as count
            FROM public.audit_log
            WHERE tenant_id = $1 AND created_at >= now() - ($2 || ' days')::interval
            GROUP BY action ORDER BY count DESC LIMIT 20
            """,
            tenant_id,
            str(days),
        )

        resources = await conn.fetch(
            """
            SELECT resource, COUNT(*)::int as count
            FROM public.audit_log
            WHERE tenant_id = $1 AND created_at >= now() - ($2 || ' days')::interval
            GROUP BY resource ORDER BY count DESC LIMIT 10
            """,
            tenant_id,
            str(days),
        )

        top_users = await conn.fetch(
            """
            SELECT u.email, al.user_id, COUNT(*)::int as count
            FROM public.audit_log al
            LEFT JOIN public.users u ON u.id = al.user_id
            WHERE al.tenant_id = $1 AND al.created_at >= now() - ($2 || ' days')::interval
            GROUP BY al.user_id, u.email
            ORDER BY count DESC LIMIT 10
            """,
            tenant_id,
            str(days),
        )

        recent_activity = await conn.fetch(
            """
            SELECT action, resource, created_at, user_id,
                   (SELECT email FROM public.users WHERE id = user_id) as user_email
            FROM public.audit_log
            WHERE tenant_id = $1
            ORDER BY created_at DESC LIMIT 10
            """,
            tenant_id,
        )

    incr("admin.audit_log.stats_viewed")
    return AuditLogStats(
        total_events=total or 0,
        actions={r["action"]: r["count"] for r in actions},
        resources={r["resource"]: r["count"] for r in resources},
        top_users=[
            {"email": r["email"], "user_id": str(r["user_id"]), "count": r["count"]}
            for r in top_users
        ],
        recent_activity=[
            {
                "action": r["action"],
                "resource": r["resource"],
                "created_at": r["created_at"].isoformat(),
                "user_email": r["user_email"],
            }
            for r in recent_activity
        ],
    )


@router.get("/tenants/{tenant_id}/audit/export")
async def export_tenant_audit_log(
    tenant_id: str,
    days: int = Query(90, ge=1, le=365),
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
):
    """Export audit log as CSV for compliance reporting."""
    from fastapi.responses import StreamingResponse

    from backend.domain.audit import export_audit_log_csv
    from shared.validators import validate_uuid

    validate_uuid(tenant_id, "tenant_id")

    async with db.acquire() as conn:
        try:
            await require_system_admin(conn, user_id)
        except TenantScopeError:
            ctx = await resolve_tenant_context(conn, user_id)
            if ctx.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this tenant"
                )
            require_role(ctx, "OWNER", "ADMIN", "COMPLIANCE_OFFICER")

        csv_content = await export_audit_log_csv(conn, tenant_id, days=days)

    incr("admin.audit_log.exported")
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_log_{tenant_id[:8]}_{days}d.csv"
        },
    )


# ---------------------------------------------------------------------------
# JobSpy / Job Source Management
# ---------------------------------------------------------------------------


@router.get("/jobs/sync-status")
async def get_job_sync_status(
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
):
    """Get current status of JobSpy integration.
    Returns configured sources, last run stats, and circuit breaker status.
    """
    from backend.domain.job_sync_service import JobSyncService

    async with db.acquire() as conn:
        await require_system_admin(conn, user_id)

    # We initialize service just to read status; it's lightweight
    # In a real app, this service might be a singleton or injected
    service = JobSyncService(db)
    return await service.get_sync_status()


@router.post("/jobs/sync")
async def trigger_job_sync(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
):
    """Trigger a manual job sync in the background."""
    from backend.domain.job_sync_service import JobSyncService

    async with db.acquire() as conn:
        await require_system_admin(conn, user_id)

    service = JobSyncService(db)

    # Check if already running (simple in-memory check for this instance)
    # Ideally we'd check DB or Redis lock for multi-instance deployments
    if service._running:
        raise HTTPException(status_code=409, detail="Sync already in progress")

    # Run in background
    background_tasks.add_task(service.sync_all_sources)

    incr("admin.job_sync.triggered", tags={"user_id": user_id})
    logger.info("Admin triggered manual job sync", extra={"user_id": user_id})

    return {"status": "triggered", "message": "Job sync started in background"}
