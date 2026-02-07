"""
Priority scoring for task queue — ENTERPRISE > TEAM > PRO > FREE.

Assigns priority_score to applications at creation time based on
the tenant's plan. Enterprise tasks are processed first.
"""

from __future__ import annotations

from typing import Any

import asyncpg

from backend.domain.plans import PLAN_CONFIGS
from shared.logging_config import get_logger

logger = get_logger("sorce.priority")

# Plan → base priority score
PLAN_PRIORITY: dict[str, int] = {
    "FREE": 0,
    "PRO": 10,
    "TEAM": 20,
    "ENTERPRISE": 100,
}


def compute_priority_score(plan: str, is_bulk: bool = False) -> int:
    """
    Compute priority score for a new application.

    Enterprise tasks get highest priority. Bulk campaigns get a slight
    penalty to avoid starving individual requests.
    """
    base = PLAN_PRIORITY.get(plan, 0)
    if is_bulk:
        base = max(0, base - 5)  # slight penalty for bulk
    return base


async def set_application_priority(
    conn: asyncpg.Connection,
    application_id: str,
    plan: str,
    is_bulk: bool = False,
) -> int:
    """Set priority_score on an application. Returns the score."""
    score = compute_priority_score(plan, is_bulk)
    await conn.execute(
        "UPDATE public.applications SET priority_score = $2 WHERE id = $1",
        application_id, score,
    )
    return score


async def bulk_set_priority(
    conn: asyncpg.Connection,
    tenant_id: str,
    plan: str,
) -> int:
    """Set priority_score for all QUEUED applications of a tenant."""
    score = compute_priority_score(plan)
    result = await conn.execute(
        """
        UPDATE public.applications SET priority_score = $2
        WHERE tenant_id = $1 AND status = 'QUEUED'
        """,
        tenant_id, score,
    )
    count = int(result.split()[-1]) if result else 0
    logger.info("Set priority %d for %d queued apps (tenant=%s)", score, count, tenant_id)
    return count
