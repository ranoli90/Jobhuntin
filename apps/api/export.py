"""Data export endpoint for user self-service data access.

Provides:
  - GET /me/export – streaming JSON export of profile + applications + events

Rate limited to 1 request per minute per user to prevent abuse.
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from packages.backend.domain.repositories import ApplicationRepo, ProfileRepo
from packages.backend.domain.tenant import TenantContext
from shared.logging_config import get_logger
from shared.metrics import RateLimiter, incr

logger = get_logger("sorce.export")

router = APIRouter(tags=["export"])

# Per-user rate limiters: 1 export per minute
_export_limiters: dict[str, RateLimiter] = defaultdict(
    lambda: RateLimiter(max_calls=1, window_seconds=60.0)
)


# ---------------------------------------------------------------------------
# Dependencies (injected at mount time)
# ---------------------------------------------------------------------------


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    raise NotImplementedError("Tenant context dependency not injected")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize(obj: Any) -> Any:
    """Recursively serialize UUIDs and datetimes."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return obj


async def _stream_export(
    db: asyncpg.Pool,
    ctx: TenantContext,
):
    """Generator that yields newline-delimited JSON objects:
    {"type": "profile", "data": {...}}
    {"type": "application", "data": {...}}
    {"type": "event", "data": {...}}.
    """
    async with db.acquire() as conn:
        # 1. Profile
        profile_data = await ProfileRepo.get_profile_data(conn, ctx.user_id)
        if profile_data:
            yield (
                json.dumps({"type": "profile", "data": _serialize(profile_data)}) + "\n"
            )

        # 2. Applications (paginated)
        offset = 0
        batch_size = 100
        while True:
            rows = await ApplicationRepo.list_for_tenant(
                conn,
                ctx.tenant_id,
                limit=batch_size,
                offset=offset,
            )
            if not rows:
                break
            for row in rows:
                # Only export user's own applications
                if str(row.get("user_id")) != ctx.user_id:
                    continue
                app_data = _serialize(row)
                yield json.dumps({"type": "application", "data": app_data}) + "\n"

                # 3. Events for this application
                events = await conn.fetch(
                    """
                    SELECT id, event_type, payload, created_at
                    FROM   public.application_events
                    WHERE  application_id = $1
                    ORDER  BY created_at ASC
                    """,
                    str(row["id"]),
                )
                for ev in events:
                    ev_data = _serialize(dict(ev))
                    yield json.dumps({"type": "event", "data": ev_data}) + "\n"

            offset += batch_size
            if len(rows) < batch_size:
                break


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get("/me/export")
async def export_my_data(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
):
    """Export all user data as newline-delimited JSON.

    Includes: profile, applications, events.
    Rate limited: 1 request per minute per user.
    """
    # Rate limit check
    limiter = _export_limiters[ctx.user_id]
    if not limiter.allow():
        raise HTTPException(
            status_code=429,
            detail="Export rate limit exceeded. Please wait 1 minute between exports.",
        )

    incr("export.requests", tags={"tenant_id": ctx.tenant_id})
    logger.info(
        "Data export requested by user %s (tenant %s)", ctx.user_id, ctx.tenant_id
    )

    return StreamingResponse(
        _stream_export(db, ctx),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f"attachment; filename=sorce-export-{ctx.user_id[:8]}.ndjson",
        },
    )
