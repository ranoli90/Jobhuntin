"""
API v2 Platform Router — public API for integrators.

Endpoints:
  - POST /api/v2/applications       — submit a single application
  - POST /api/v2/applications/batch  — submit multiple applications
  - GET  /api/v2/applications/{id}   — get application status
  - POST /api/v2/staffing/bulk-submit — staffing agency bulk candidate submission
  - GET  /api/v2/staffing/status/{batch_id} — staffing batch status
  - POST /api/v2/webhooks            — register webhook endpoint
  - GET  /api/v2/webhooks            — list webhook endpoints
  - DELETE /api/v2/webhooks/{id}     — delete webhook
  - GET  /api/v2/usage               — API usage stats
"""

from __future__ import annotations

import json
import time
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.api_v2")

router = APIRouter(prefix="/api/v2", tags=["api-v2"])

def _get_pool() -> asyncpg.Pool:
    raise NotImplementedError("Pool dependency not injected")


# ---------------------------------------------------------------------------
# Dependency: API key auth
# ---------------------------------------------------------------------------

async def _get_api_key(request: Request) -> dict[str, Any]:
    from api_v2.auth import resolve_api_key
    pool = _get_pool()
    return await resolve_api_key(request, pool)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SubmitApplicationRequest(BaseModel):
    job_url: str
    blueprint_key: str = "job-app"
    resume_text: str = ""
    resume_url: str = ""
    metadata: dict[str, Any] = {}


class BatchSubmitRequest(BaseModel):
    applications: list[SubmitApplicationRequest]


class StaffingBulkRequest(BaseModel):
    client_name: str
    client_portal: str
    role_title: str
    role_description: str = ""
    candidates: list[dict[str, Any]]
    priority: str = "normal"


class WebhookCreateRequest(BaseModel):
    url: str
    events: list[str] = ["application.completed", "application.failed", "application.hold"]


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

@router.post("/applications")
async def submit_application(
    body: SubmitApplicationRequest,
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Submit a single application via API."""
    start = time.time()
    tenant_id = api_key["tenant_id"]

    from backend.domain.priority import compute_priority_score
    priority = compute_priority_score(api_key.get("tenant_plan", "PRO"))

    async with db.acquire() as conn:
        # Find or create job
        job = await conn.fetchrow(
            "SELECT id FROM public.jobs WHERE url = $1 LIMIT 1", body.job_url,
        )
        job_id = job["id"] if job else None
        if not job_id:
            job_id = await conn.fetchval(
                """INSERT INTO public.jobs (url, title, tenant_id)
                   VALUES ($1, $2, $3) RETURNING id""",
                body.job_url, body.metadata.get("title", "API Submission"), tenant_id,
            )

        # Create application
        app_id = await conn.fetchval(
            """INSERT INTO public.applications
                   (user_id, job_id, tenant_id, blueprint_key, status, priority_score)
               VALUES (
                   (SELECT user_id FROM public.tenant_members WHERE tenant_id = $1 AND role = 'OWNER' LIMIT 1),
                   $2, $1, $3, 'QUEUED', $4
               ) RETURNING id""",
            tenant_id, job_id, body.blueprint_key, priority,
        )

    from api_v2.auth import record_api_usage
    latency = int((time.time() - start) * 1000)
    await record_api_usage(db, str(api_key["id"]), tenant_id, "/applications", "POST", 201, latency)
    incr("api_v2.application.submitted")

    return {"id": str(app_id), "status": "QUEUED", "job_url": body.job_url}


@router.post("/applications/batch")
async def batch_submit(
    body: BatchSubmitRequest,
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Submit multiple applications in one call."""
    if len(body.applications) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 applications per batch")

    results = []
    for app_req in body.applications:
        try:
            r = await submit_application(app_req, api_key, db)
            results.append({**r, "success": True})
        except Exception as exc:
            results.append({"job_url": app_req.job_url, "success": False, "error": str(exc)})

    return {
        "total": len(results),
        "succeeded": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "results": results,
    }


@router.get("/applications/{application_id}")
async def get_application_status(
    application_id: str,
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get real-time status of an application."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT a.id, a.status::text, a.blueprint_key, a.created_at, a.updated_at,
                      j.title AS job_title, j.url AS job_url, j.company AS job_company
               FROM public.applications a
               LEFT JOIN public.jobs j ON j.id = a.job_id
               WHERE a.id = $1 AND a.tenant_id = $2""",
            application_id, api_key["tenant_id"],
        )
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    return dict(row)


# ---------------------------------------------------------------------------
# Staffing Agency
# ---------------------------------------------------------------------------

@router.post("/staffing/bulk-submit")
async def staffing_bulk_submit(
    body: StaffingBulkRequest,
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """
    Submit a batch of candidates to a client ATS portal.
    Creates a staffing_batch record, then queues individual applications.
    """
    start = time.time()
    tenant_id = api_key["tenant_id"]
    if api_key.get("tenant_plan") not in ("TEAM", "ENTERPRISE"):
        raise HTTPException(status_code=403, detail="Staffing API requires TEAM or ENTERPRISE plan")

    if len(body.candidates) > 25:
        raise HTTPException(status_code=400, detail="Maximum 25 candidates per batch")

    s = get_settings()
    from backend.domain.priority import compute_priority_score
    priority = compute_priority_score(api_key.get("tenant_plan", "ENTERPRISE"), is_bulk=True)

    async with db.acquire() as conn:
        batch = await conn.fetchrow(
            """INSERT INTO public.staffing_batches
                   (tenant_id, client_name, client_portal, role_title, role_description,
                    candidates, candidate_count, status,
                    price_per_submission_cents, base_monthly_cents)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, 'submitting', $8, $9)
               RETURNING id, status""",
            tenant_id, body.client_name, body.client_portal,
            body.role_title, body.role_description,
            json.dumps(body.candidates), len(body.candidates),
            s.staffing_price_per_submit_cents, s.staffing_base_monthly_cents,
        )
        batch_id = str(batch["id"])

        # Queue individual applications per candidate
        for candidate in body.candidates:
            candidate_name = candidate.get("full_name", candidate.get("name", "Candidate"))
            await conn.execute(
                """INSERT INTO public.applications
                       (user_id, tenant_id, blueprint_key, status, priority_score)
                   VALUES (
                       (SELECT user_id FROM public.tenant_members WHERE tenant_id = $1 AND role = 'OWNER' LIMIT 1),
                       $1, 'staffing-agency', 'QUEUED', $2
                   )""",
                tenant_id, priority,
            )

    from api_v2.auth import record_api_usage
    latency = int((time.time() - start) * 1000)
    await record_api_usage(db, str(api_key["id"]), tenant_id, "/staffing/bulk-submit", "POST", 201, latency)
    incr("api_v2.staffing.batch_created", tags={"candidates": str(len(body.candidates))})

    return {
        "batch_id": batch_id,
        "status": "submitting",
        "candidate_count": len(body.candidates),
        "client_name": body.client_name,
        "role_title": body.role_title,
        "estimated_cost_cents": len(body.candidates) * s.staffing_price_per_submit_cents,
    }


@router.get("/staffing/status/{batch_id}")
async def staffing_batch_status(
    batch_id: str,
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get status of a staffing batch submission."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT * FROM public.staffing_batches
               WHERE id = $1 AND tenant_id = $2""",
            batch_id, api_key["tenant_id"],
        )
    if not row:
        raise HTTPException(status_code=404, detail="Batch not found")
    return dict(row)


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

@router.get("/webhooks")
async def list_webhooks(
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """List registered webhook endpoints."""
    async with db.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, url, events, is_active, failure_count, last_success_at, created_at FROM public.webhook_endpoints WHERE tenant_id = $1",
            api_key["tenant_id"],
        )
    return [dict(r) for r in rows]


@router.post("/webhooks")
async def create_webhook(
    body: WebhookCreateRequest,
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Register a new webhook endpoint."""
    import secrets
    secret = "whsec_" + secrets.token_hex(24)

    async with db.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*)::int FROM public.webhook_endpoints WHERE tenant_id = $1",
            api_key["tenant_id"],
        )
        if count >= 10:
            raise HTTPException(status_code=400, detail="Maximum 10 webhook endpoints")

        row = await conn.fetchrow(
            """INSERT INTO public.webhook_endpoints (tenant_id, url, secret, events)
               VALUES ($1, $2, $3, $4) RETURNING id, url, events, is_active""",
            api_key["tenant_id"], body.url, secret, body.events,
        )

    return {**dict(row), "secret": secret}


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Delete a webhook endpoint."""
    async with db.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.webhook_endpoints WHERE id = $1 AND tenant_id = $2",
            webhook_id, api_key["tenant_id"],
        )
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

@router.get("/usage")
async def get_usage(
    api_key: dict = Depends(_get_api_key),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get API usage statistics for the current key."""
    async with db.acquire() as conn:
        today = await conn.fetchrow(
            """SELECT COUNT(*)::int AS calls,
                      AVG(latency_ms)::int AS avg_latency_ms
               FROM public.api_usage
               WHERE api_key_id = $1 AND created_at >= CURRENT_DATE""",
            api_key["id"],
        )
        month = await conn.fetchrow(
            """SELECT COUNT(*)::int AS calls,
                      COUNT(DISTINCT DATE(created_at))::int AS active_days
               FROM public.api_usage
               WHERE api_key_id = $1 AND created_at >= date_trunc('month', now())""",
            api_key["id"],
        )
    return {
        "key_prefix": api_key["key_prefix"],
        "tier": api_key["tier"],
        "rate_limit_rpm": api_key["rate_limit_rpm"],
        "monthly_quota": api_key["monthly_quota"],
        "calls_this_month": api_key["calls_this_month"],
        "today": dict(today) if today else {},
        "this_month": dict(month) if month else {},
    }
