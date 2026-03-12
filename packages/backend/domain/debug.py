"""Debug bundle generation logic."""

from __future__ import annotations

import contextlib
import json
from typing import Any, cast

import asyncpg

from packages.backend.domain.masking import redact_event_payload


async def build_debug_bundle(
    conn: asyncpg.Connection, application_id: str
) -> dict[str, Any] | None:
    """Build a comprehensive debug bundle for a single application.
    Returns None if application not found.
    """
    # Application
    app_row = await conn.fetchrow(
        "SELECT * FROM public.applications WHERE id = $1",
        application_id,
    )
    if app_row is None:
        return None

    app_dict = dict(app_row)
    user_id = str(app_dict.get("user_id", ""))
    tenant_id = (
        str(app_dict.get("tenant_id", "")) if app_dict.get("tenant_id") else None
    )

    # Events
    events = await conn.fetch(
        "SELECT * FROM public.application_events WHERE application_id = $1 ORDER BY created_at",
        application_id,
    )

    # Inputs
    inputs = await conn.fetch(
        "SELECT * FROM public.application_inputs WHERE application_id = $1 ORDER BY created_at",
        application_id,
    )

    # Evaluations
    evaluations = await conn.fetch(
        "SELECT * FROM public.agent_evaluations WHERE application_id = $1 ORDER BY created_at",
        application_id,
    )

    # Analytics events for this user (last 100)
    analytics = await conn.fetch(
        """
        SELECT * FROM public.analytics_events
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 100
        """,
        user_id,
    )

    # Experiment assignments for this tenant
    assignments: list[dict] = []
    if tenant_id:
        assignment_rows = await conn.fetch(
            """
            SELECT ea.*, e.key AS experiment_key
            FROM public.experiment_assignments ea
            JOIN public.experiments e ON e.id = ea.experiment_id
            WHERE ea.subject_id = $1
            """,
            tenant_id,
        )
        assignments = [dict(r) for r in assignment_rows]

    # Redact PII from event payloads
    redacted_events = []
    for e in events:
        ed = dict(e)
        if ed.get("payload"):
            payload = ed["payload"]
            if isinstance(payload, str):
                with contextlib.suppress(json.JSONDecodeError):
                    payload = json.loads(payload)
            ed["payload"] = redact_event_payload(payload)
        redacted_events.append(ed)

    return cast(
        dict[str, Any] | None,
        _serialize(
            {
                "application": app_dict,
                "events": redacted_events,
                "inputs": [dict(i) for i in inputs],
                "evaluations": [dict(ev) for ev in evaluations],
                "analytics_events": [dict(a) for a in analytics],
                "experiment_assignments": assignments,
            }
        ),
    )


def _serialize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    import uuid as _uuid

    if isinstance(obj, _uuid.UUID):
        return str(obj)
    return obj
