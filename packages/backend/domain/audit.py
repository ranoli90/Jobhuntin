"""
Audit log — SOC 2 compliance trail for enterprise tenants.

Records all significant actions: member changes, billing events,
SSO configuration, data exports, impersonation, etc.
"""

from __future__ import annotations

from typing import Any

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.audit")


async def record_audit_event(
    conn: asyncpg.Connection,
    tenant_id: str | None,
    user_id: str | None,
    action: str,
    resource: str,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Record an audit log entry."""
    import json
    await conn.execute(
        """
        INSERT INTO public.audit_log
            (tenant_id, user_id, action, resource, resource_id, details, ip_address, user_agent)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)
        """,
        tenant_id, user_id, action, resource, resource_id,
        json.dumps(details or {}), ip_address, user_agent,
    )


async def get_audit_log(
    conn: asyncpg.Connection,
    tenant_id: str,
    limit: int = 100,
    offset: int = 0,
    action_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve audit log entries for a tenant."""
    if action_filter:
        rows = await conn.fetch(
            """
            SELECT id, user_id, action, resource, resource_id, details,
                   ip_address, created_at
            FROM public.audit_log
            WHERE tenant_id = $1 AND action LIKE $4
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            tenant_id, limit, offset, f"%{action_filter}%",
        )
    else:
        rows = await conn.fetch(
            """
            SELECT id, user_id, action, resource, resource_id, details,
                   ip_address, created_at
            FROM public.audit_log
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            tenant_id, limit, offset,
        )
    return [dict(r) for r in rows]


async def get_audit_log_count(
    conn: asyncpg.Connection,
    tenant_id: str,
) -> int:
    """Count total audit log entries for a tenant."""
    return await conn.fetchval(
        "SELECT COUNT(*)::int FROM public.audit_log WHERE tenant_id = $1",
        tenant_id,
    ) or 0


async def export_audit_log_csv(
    conn: asyncpg.Connection,
    tenant_id: str,
    days: int = 90,
) -> str:
    """Export audit log as CSV string for compliance reports."""
    rows = await conn.fetch(
        """
        SELECT created_at, user_id, action, resource, resource_id, details, ip_address
        FROM public.audit_log
        WHERE tenant_id = $1 AND created_at >= now() - ($2 || ' days')::interval
        ORDER BY created_at DESC
        """,
        tenant_id, str(days),
    )
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "user_id", "action", "resource", "resource_id", "details", "ip_address"])
    for r in rows:
        writer.writerow([
            r["created_at"].isoformat(), str(r["user_id"] or ""),
            r["action"], r["resource"], r["resource_id"] or "",
            str(r["details"]), r["ip_address"] or "",
        ])
    return output.getvalue()
