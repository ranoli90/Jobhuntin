"""
Agent evaluation logic — automatic (SYSTEM) labeling of task outcomes.

Called from the worker after task completion or failure to record a
structured evaluation row in `agent_evaluations`.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import asyncpg

logger = logging.getLogger("sorce.evaluations")


# ---------------------------------------------------------------------------
# System evaluation heuristics
# ---------------------------------------------------------------------------

_TERMINAL_SUCCESS_STATUSES = frozenset({"APPLIED", "SUBMITTED", "COMPLETED"})


async def record_system_evaluation(
    conn: asyncpg.Connection,
    application_id: str,
    status: str,
    attempt_count: int,
    error_message: str | None = None,
    tenant_id: str | None = None,
    user_id: str | None = None,
    *,
    had_hold: bool = False,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Insert a SYSTEM-generated evaluation row based on heuristics.

    Heuristics:
      - SUCCESS: terminal success status on first attempt, no hold.
      - PARTIAL: terminal success but attempt_count > 1 or had REQUIRES_INPUT.
      - FAILURE: status is FAILED.
    """
    label: str
    reason: str | None = None

    if status in _TERMINAL_SUCCESS_STATUSES:
        if attempt_count <= 1 and not had_hold:
            label = "SUCCESS"
            reason = f"Completed as {status} on first attempt"
        else:
            label = "PARTIAL"
            parts: list[str] = []
            if attempt_count > 1:
                parts.append(f"required {attempt_count} attempts")
            if had_hold:
                parts.append("required user input (HOLD)")
            reason = f"Completed as {status} but {', '.join(parts)}"
    elif status == "FAILED":
        label = "FAILURE"
        reason = error_message or f"Failed after {attempt_count} attempt(s)"
    else:
        # Non-terminal status — don't record an evaluation
        return

    await conn.execute(
        """
        INSERT INTO public.agent_evaluations
            (application_id, tenant_id, user_id, source, label, reason, metadata)
        VALUES ($1, $2, $3, 'SYSTEM', $4, $5, $6::jsonb)
        """,
        application_id,
        tenant_id,
        user_id,
        label,
        reason,
        json.dumps(metadata or {
            "status": status,
            "attempt_count": attempt_count,
            "had_hold": had_hold,
        }),
    )
    logger.info(
        "System evaluation for %s: label=%s reason=%s",
        application_id, label, reason,
    )


async def record_user_feedback(
    conn: asyncpg.Connection,
    application_id: str,
    user_id: str,
    label: str,
    comment: str | None = None,
    tenant_id: str | None = None,
) -> str:
    """
    Insert a USER-generated evaluation row from explicit feedback.

    Returns the evaluation id.
    """
    row = await conn.fetchrow(
        """
        INSERT INTO public.agent_evaluations
            (application_id, tenant_id, user_id, source, label, reason, metadata)
        VALUES ($1, $2, $3, 'USER', $4, $5, '{}'::jsonb)
        RETURNING id
        """,
        application_id,
        tenant_id,
        user_id,
        label,
        comment,
    )
    eval_id = str(row["id"])
    logger.info(
        "User feedback for %s: label=%s comment=%s",
        application_id, label, comment,
    )
    return eval_id
