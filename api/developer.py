"""
Developer Portal API — API key management, webhook config, usage dashboard.

Mounted at /developer prefix. Uses JWT auth (not API key auth).
"""

from __future__ import annotations

from typing import Any, Callable

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api_v2.auth import generate_api_key
from backend.domain.audit import record_audit_event
from backend.domain.tenant import TenantContext, TenantScopeError, require_role
from shared.logging_config import get_logger

logger = get_logger("sorce.api.developer")

router = APIRouter(prefix="/developer", tags=["developer"])

_get_pool: Callable[[], asyncpg.Pool] = lambda: (_ for _ in ()).throw(NotImplementedError)
_get_tenant_ctx: Callable[[], TenantContext] = lambda: (_ for _ in ()).throw(NotImplementedError)

TIER_LIMITS = {
    "free": {"rate_limit_rpm": 60, "monthly_quota": 100},
    "pro": {"rate_limit_rpm": 300, "monthly_quota": 10000},
    "enterprise": {"rate_limit_rpm": 1000, "monthly_quota": 0},
}


class CreateKeyRequest(BaseModel):
    name: str = "Default"
    tier: str = "free"


class CreateWebhookRequest(BaseModel):
    url: str
    events: list[str] = ["application.completed", "application.failed", "application.hold"]


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

@router.get("/api-keys")
async def list_api_keys(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, name, key_prefix, tier, rate_limit_rpm, monthly_quota,
                      calls_this_month, is_active, last_used_at, created_at
               FROM public.api_keys WHERE tenant_id = $1 ORDER BY created_at DESC""",
            ctx.tenant_id,
        )
    return [dict(r) for r in rows]


@router.post("/api-keys")
async def create_api_key(
    body: CreateKeyRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only admins can create API keys")

    tier = body.tier if body.tier in TIER_LIMITS else "free"
    limits = TIER_LIMITS[tier]
    raw_key, key_hash, key_prefix = generate_api_key()

    async with db.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*)::int FROM public.api_keys WHERE tenant_id = $1", ctx.tenant_id,
        )
        if count >= 20:
            raise HTTPException(status_code=400, detail="Maximum 20 API keys per tenant")

        row = await conn.fetchrow(
            """INSERT INTO public.api_keys
                   (tenant_id, name, key_hash, key_prefix, tier, rate_limit_rpm, monthly_quota)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               RETURNING id, name, key_prefix, tier, rate_limit_rpm, monthly_quota, created_at""",
            ctx.tenant_id, body.name, key_hash, key_prefix,
            tier, limits["rate_limit_rpm"], limits["monthly_quota"],
        )

        await record_audit_event(
            conn, ctx.tenant_id, ctx.user_id,
            action="developer.api_key_created",
            resource="api_key", resource_id=str(row["id"]),
            details={"name": body.name, "tier": tier},
        )

    return {**dict(row), "raw_key": raw_key}


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    try:
        require_role(ctx, "OWNER", "ADMIN")
    except TenantScopeError:
        raise HTTPException(status_code=403, detail="Only admins can revoke keys")

    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE public.api_keys SET is_active = false WHERE id = $1 AND tenant_id = $2",
            key_id, ctx.tenant_id,
        )
    return {"status": "revoked"}


# ---------------------------------------------------------------------------
# Webhooks (via JWT auth, not API key)
# ---------------------------------------------------------------------------

@router.get("/webhooks")
async def list_webhooks(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, url, events, is_active, failure_count, last_success_at, created_at
               FROM public.webhook_endpoints WHERE tenant_id = $1 ORDER BY created_at DESC""",
            ctx.tenant_id,
        )
    return [dict(r) for r in rows]


@router.post("/webhooks")
async def create_webhook(
    body: CreateWebhookRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    import secrets
    secret = "whsec_" + secrets.token_hex(24)

    async with db.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*)::int FROM public.webhook_endpoints WHERE tenant_id = $1", ctx.tenant_id,
        )
        if count >= 10:
            raise HTTPException(status_code=400, detail="Maximum 10 webhooks")

        row = await conn.fetchrow(
            """INSERT INTO public.webhook_endpoints (tenant_id, url, secret, events)
               VALUES ($1, $2, $3, $4) RETURNING id, url, events, is_active""",
            ctx.tenant_id, body.url, secret, body.events,
        )

    return {**dict(row), "secret": secret}


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    async with db.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.webhook_endpoints WHERE id = $1 AND tenant_id = $2",
            webhook_id, ctx.tenant_id,
        )
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Usage dashboard
# ---------------------------------------------------------------------------

@router.get("/usage")
async def get_usage_dashboard(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    async with db.acquire() as conn:
        keys = await conn.fetch(
            """SELECT ak.id, ak.name, ak.key_prefix, ak.tier, ak.calls_this_month,
                      ak.monthly_quota, ak.rate_limit_rpm
               FROM public.api_keys ak WHERE ak.tenant_id = $1 AND ak.is_active = true""",
            ctx.tenant_id,
        )
        daily = await conn.fetch(
            """SELECT DATE(created_at) AS day, COUNT(*)::int AS calls,
                      AVG(latency_ms)::int AS avg_latency
               FROM public.api_usage WHERE tenant_id = $1
                 AND created_at >= now() - interval '30 days'
               GROUP BY DATE(created_at) ORDER BY day""",
            ctx.tenant_id,
        )
        by_endpoint = await conn.fetch(
            """SELECT endpoint, method, COUNT(*)::int AS calls,
                      AVG(latency_ms)::int AS avg_latency
               FROM public.api_usage WHERE tenant_id = $1
                 AND created_at >= now() - interval '30 days'
               GROUP BY endpoint, method ORDER BY calls DESC LIMIT 20""",
            ctx.tenant_id,
        )

    return {
        "keys": [dict(k) for k in keys],
        "daily_usage": [dict(d) for d in daily],
        "by_endpoint": [dict(e) for e in by_endpoint],
    }
