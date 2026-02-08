#!/usr/bin/env python3
"""
Debug bundle CLI — fetch a comprehensive debug snapshot for a single application.

Usage:
    python scripts/debug_application.py <application_id>

Connects to the database configured in .env / environment variables and
prints a JSON debug bundle including:
  - Application row
  - Application events
  - Application inputs
  - Agent evaluations
  - Recent analytics events for the user
  - Experiment assignments for the tenant
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime
from typing import Any

import asyncpg

from backend.domain.masking import redact_event_payload
from shared.config import get_settings


def _json_serializer(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return str(obj)


async def fetch_debug_bundle(application_id: str) -> dict[str, Any]:
    s = get_settings()
    conn = await asyncpg.connect(s.database_url)

    try:
        # Application
        app_row = await conn.fetchrow(
            "SELECT * FROM public.applications WHERE id = $1",
            application_id,
        )
        if app_row is None:
            return {"error": f"Application {application_id} not found"}

        app_dict = dict(app_row)
        user_id = str(app_dict.get("user_id", ""))
        tenant_id = str(app_dict.get("tenant_id", "")) if app_dict.get("tenant_id") else None

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

        # Analytics events for this user (last 50)
        analytics = await conn.fetch(
            """
            SELECT * FROM public.analytics_events
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 50
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
                    payload = json.loads(payload)
                ed["payload"] = redact_event_payload(payload)
            redacted_events.append(ed)

        return {
            "application": app_dict,
            "events": redacted_events,
            "inputs": [dict(i) for i in inputs],
            "evaluations": [dict(ev) for ev in evaluations],
            "analytics_events": [dict(a) for a in analytics],
            "experiment_assignments": assignments,
        }
    finally:
        await conn.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_application.py <application_id>")
        sys.exit(1)

    application_id = sys.argv[1]
    bundle = asyncio.run(fetch_debug_bundle(application_id))
    print(json.dumps(bundle, indent=2, default=_json_serializer))


if __name__ == "__main__":
    main()
