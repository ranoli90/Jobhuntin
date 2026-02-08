"""
Bulk Operations API — campaign management for enterprise/team tenants.

Mounted at /bulk prefix by api/main.py.
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.domain.audit import record_audit_event
from backend.domain.tenant import TenantContext, TenantScopeError, require_role
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.api.bulk")

router = APIRouter(prefix="/bulk", tags=["bulk"])

# ---------------------------------------------------------------------------
# Dependency stubs (injected by api/main.py)
# ---------------------------------------------------------------------------

def _get_pool() -> asyncpg.Pool:
    return (_ for _ in ()).throw(
    NotImplementedError("Pool not injected")
)
def _get_tenant_ctx() -> TenantContext:
    return (_ for _ in ()).throw(
    NotImplementedError("Tenant ctx not injected")
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class CreateCampaignRequest(BaseModel):
    name: str
    filters: dict[str, str] = {}  # title, location, company, blueprint_key


class StartCampaignRequest(BaseModel):
    pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/campaigns")
async def list_campaigns(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """List bulk campaigns for the current tenant."""
    if ctx.plan not in ("TEAM", "ENTERPRISE"):
        raise HTTPException(status_code=403, detail="Bulk operations require TEAM or ENTERPRISE plan")

    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, status, filters, total_jobs, applied, failed,
                   created_at, started_at, completed_at
            FROM public.bulk_campaigns
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT 50
            """,
            ctx.tenant_id,
        )
    return [dict(r) for r in rows]


@router.post("/campaigns")
async def create_campaign(
    body: CreateCampaignRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Create a new bulk campaign (draft)."""
    if ctx.plan not in ("TEAM", "ENTERPRISE"):
        raise HTTPException(status_code=403, detail="Bulk operations require TEAM or ENTERPRISE plan")
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only admins can create campaigns")

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO public.bulk_campaigns (tenant_id, created_by, name, filters)
            VALUES ($1, $2, $3, $4::jsonb)
            RETURNING id, name, status, filters, total_jobs, applied, failed, created_at
            """,
            ctx.tenant_id, ctx.user_id, body.name, json.dumps(body.filters),
        )

        await record_audit_event(
            conn, ctx.tenant_id, ctx.user_id,
            action="bulk.campaign_created",
            resource="bulk_campaign",
            resource_id=str(row["id"]),
            details={"name": body.name, "filters": body.filters},
        )

    incr("bulk.campaign.created", tags={"tenant_id": ctx.tenant_id})
    return dict(row)


@router.post("/campaigns/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Start a draft bulk campaign — queues applications for matching jobs."""
    if ctx.plan not in ("TEAM", "ENTERPRISE"):
        raise HTTPException(status_code=403, detail="Bulk operations require TEAM or ENTERPRISE plan")
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only admins can start campaigns")

    async with db.acquire() as conn:
        # Verify campaign ownership and status
        campaign = await conn.fetchrow(
            "SELECT * FROM public.bulk_campaigns WHERE id = $1 AND tenant_id = $2",
            campaign_id, ctx.tenant_id,
        )
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        if campaign["status"] != "draft":
            raise HTTPException(status_code=409, detail=f"Campaign is already {campaign['status']}")

        filters = campaign["filters"] or {}
        title_filter = filters.get("title", "")
        location_filter = filters.get("location", "")

        # Find matching jobs
        query = """
            SELECT id FROM public.jobs
            WHERE (tenant_id = $1 OR tenant_id IS NULL)
        """
        params: list[Any] = [ctx.tenant_id]
        if title_filter:
            params.append(f"%{title_filter}%")
            query += f" AND title ILIKE ${len(params)}"
        if location_filter:
            params.append(f"%{location_filter}%")
            query += f" AND location ILIKE ${len(params)}"
        query += " LIMIT 500"

        job_rows = await conn.fetch(query, *params)
        total = len(job_rows)

        if total == 0:
            raise HTTPException(status_code=404, detail="No matching jobs found")

        # Compute priority score for bulk
        from backend.domain.priority import compute_priority_score
        priority = compute_priority_score(ctx.plan, is_bulk=True)

        # Create applications for each job
        blueprint_key = filters.get("blueprint_key", "job-app")
        for job in job_rows:
            await conn.execute(
                """
                INSERT INTO public.applications
                    (user_id, job_id, tenant_id, blueprint_key, status, priority_score)
                VALUES ($1, $2, $3, $4, 'QUEUED', $5)
                ON CONFLICT DO NOTHING
                """,
                ctx.user_id, job["id"], ctx.tenant_id, blueprint_key, priority,
            )

        # Update campaign
        await conn.execute(
            """
            UPDATE public.bulk_campaigns
            SET status = 'running', total_jobs = $2, started_at = now()
            WHERE id = $1
            """,
            campaign_id, total,
        )

        await record_audit_event(
            conn, ctx.tenant_id, ctx.user_id,
            action="bulk.campaign_started",
            resource="bulk_campaign",
            resource_id=campaign_id,
            details={"total_jobs": total, "filters": filters},
        )

    incr("bulk.campaign.started", tags={"tenant_id": ctx.tenant_id, "jobs": str(total)})
    return {"status": "running", "campaign_id": campaign_id, "total_jobs": total}


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get details of a specific bulk campaign."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name, status, filters, total_jobs, applied, failed,
                   created_at, started_at, completed_at
            FROM public.bulk_campaigns
            WHERE id = $1 AND tenant_id = $2
            """,
            campaign_id, ctx.tenant_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return dict(row)
