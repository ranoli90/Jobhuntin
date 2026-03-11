"""GDPR Compliance — data export and deletion for user privacy rights.

Implements:
- Right to Access (Article 15): Export all user data
- Right to Erasure (Article 17): Delete user data
- Data Portability (Article 20): Machine-readable export format
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.gdpr")


async def export_user_data(
    conn: asyncpg.Connection,
    user_id: str,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "sections": {},
    }

    user = await conn.fetchrow(
        """
        SELECT id, email, raw_user_meta_data, created_at, last_sign_in_at
        FROM auth.users
        WHERE id = $1
        """,
        user_id,
    )
    if user:
        data["sections"]["user"] = dict(user)

    profile = await conn.fetchrow(
        """
        SELECT resume_url, canonical_profile, created_at, updated_at
        FROM public.profiles
        WHERE user_id = $1
        """,
        user_id,
    )
    if profile:
        data["sections"]["profile"] = dict(profile)

    applications = await conn.fetch(
        """
        SELECT id, job_id, status, error_message, attempt_count,
               created_at, updated_at, submitted_at
        FROM public.applications
        WHERE user_id = $1
        ORDER BY created_at DESC
        """,
        user_id,
    )
    data["sections"]["applications"] = [dict(a) for a in applications]

    if applications:
        app_ids = [str(a["id"]) for a in applications]
        events = await conn.fetch(
            """
            SELECT application_id, event_type, payload, created_at
            FROM public.application_events
            WHERE application_id = ANY($1::uuid[])
            ORDER BY created_at DESC
            """,
            app_ids,
        )
        data["sections"]["application_events"] = [dict(e) for e in events]

        inputs = await conn.fetch(
            """
            SELECT application_id, selector, question, answer, resolved, created_at
            FROM public.application_inputs
            WHERE application_id = ANY($1::uuid[])
            ORDER BY created_at DESC
            """,
            app_ids,
        )
        data["sections"]["application_inputs"] = [dict(i) for i in inputs]

    analytics = await conn.fetch(
        """
        SELECT event_type, properties, created_at
        FROM public.analytics_events
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 1000
        """,
        user_id,
    )
    data["sections"]["analytics_events"] = [dict(a) for a in analytics]

    alerts = await conn.fetch(
        """
        SELECT name, keywords, locations, frequency, is_active, created_at
        FROM public.job_alerts
        WHERE user_id = $1
        """,
        user_id,
    )
    data["sections"]["job_alerts"] = [dict(a) for a in alerts]

    # PRIV-005: answer_memory (smart pre-fill) keyed by user_id
    answer_memory = await conn.fetch(
        """
        SELECT field_label, field_type, answer_value, use_count, last_used_at, created_at
        FROM public.answer_memory
        WHERE user_id = $1
        ORDER BY last_used_at DESC
        """,
        user_id,
    )
    data["sections"]["answer_memory"] = [dict(r) for r in answer_memory]

    incr("gdpr.export_completed")
    logger.info("GDPR export completed for user %s", user_id)

    return data


def export_to_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, default=str, ensure_ascii=False)


async def delete_user_data(
    conn: asyncpg.Connection,
    user_id: str,
    *,
    soft_delete: bool = True,
    retain_analytics: bool = False,
) -> dict[str, int]:
    deleted: dict[str, int] = {}

    if not soft_delete:
        deleted["job_alerts"] = await conn.execute(
            "DELETE FROM public.job_alerts WHERE user_id = $1",
            user_id,
        )
        deleted["job_alerts"] = _count_from_result(deleted["job_alerts"])

        deleted["analytics_events"] = await conn.execute(
            (
                "DELETE FROM public.analytics_events WHERE user_id = $1"
                if not retain_analytics
                else "UPDATE public.analytics_events SET user_id = NULL, properties = properties - 'email' WHERE user_id = $1"
            ),
            user_id,
        )
        deleted["analytics_events"] = _count_from_result(deleted["analytics_events"])

        deleted["application_inputs"] = await conn.execute(
            """
            DELETE FROM public.application_inputs
            WHERE application_id IN (SELECT id FROM public.applications WHERE user_id = $1)
            """,
            user_id,
        )
        deleted["application_inputs"] = _count_from_result(
            deleted["application_inputs"]
        )

        # PRIV-005: answer_memory keyed by user_id
        deleted["answer_memory"] = await conn.execute(
            "DELETE FROM public.answer_memory WHERE user_id = $1",
            user_id,
        )
        deleted["answer_memory"] = _count_from_result(deleted["answer_memory"])

        deleted["application_events"] = await conn.execute(
            """
            DELETE FROM public.application_events
            WHERE application_id IN (SELECT id FROM public.applications WHERE user_id = $1)
            """,
            user_id,
        )
        deleted["application_events"] = _count_from_result(
            deleted["application_events"]
        )

        deleted["applications"] = await conn.execute(
            "DELETE FROM public.applications WHERE user_id = $1",
            user_id,
        )
        deleted["applications"] = _count_from_result(deleted["applications"])

        deleted["profiles"] = await conn.execute(
            "DELETE FROM public.profiles WHERE user_id = $1",
            user_id,
        )
        deleted["profiles"] = _count_from_result(deleted["profiles"])

        deleted["team_members"] = await conn.execute(
            "DELETE FROM public.team_members WHERE user_id = $1",
            user_id,
        )
        deleted["team_members"] = _count_from_result(deleted["team_members"])

        await conn.execute(
            """
            UPDATE auth.users
            SET email = 'deleted_' || id || '@deleted.invalid',
                raw_user_meta_data = '{}',
                deleted_at = NOW()
            WHERE id = $1
            """,
            user_id,
        )
    else:
        await conn.execute(
            """
            UPDATE auth.users
            SET raw_user_meta_data = jsonb_set(
                COALESCE(raw_user_meta_data, '{}'),
                '{deletion_requested}',
                to_jsonb(NOW())
            )
            WHERE id = $1
            """,
            user_id,
        )

        deleted["soft_delete_scheduled"] = 1

    total = sum(deleted.values())
    incr("gdpr.deletion_completed", value=total)
    logger.info("GDPR deletion completed for user %s: %s", user_id, deleted)

    return deleted


def _count_from_result(result: str) -> int:
    if "DELETE" in result:
        parts = result.split()
        return int(parts[-1]) if len(parts) > 1 else 0
    return 0


async def get_gdpr_status(
    conn: asyncpg.Connection,
    user_id: str,
) -> dict[str, Any]:
    user = await conn.fetchrow(
        """
        SELECT
            raw_user_meta_data->>'deletion_requested' AS deletion_requested,
            raw_user_meta_data->>'export_requested' AS export_requested
        FROM auth.users
        WHERE id = $1
        """,
        user_id,
    )

    applications_count = await conn.fetchval(
        "SELECT COUNT(*) FROM public.applications WHERE user_id = $1",
        user_id,
    )

    return {
        "user_id": user_id,
        "deletion_requested": user["deletion_requested"] if user else None,
        "export_requested": user["export_requested"] if user else None,
        "applications_count": applications_count or 0,
        "has_data": applications_count > 0,
    }
