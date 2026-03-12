"""Data retention and cleanup routines.

Provides scheduled-task-compatible functions for:
  - Deleting stale resume PDFs from Supabase Storage
  - Anonymizing old application_events payloads
  - Finding records eligible for cleanup

Retention defaults:
  - Raw resume PDFs: 90 days
  - Event payload PII: anonymized after 180 days
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg

from packages.backend.domain.masking import redact_event_payload
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.retention")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RESUME_RETENTION_DAYS = 90
EVENT_PII_RETENTION_DAYS = 180


# ---------------------------------------------------------------------------
# Resume cleanup
# ---------------------------------------------------------------------------


async def find_stale_resumes(
    conn: asyncpg.Connection,
    retention_days: int = RESUME_RETENTION_DAYS,
) -> list[dict[str, Any]]:
    """Find profiles with resume_url that are older than the retention period.
    Returns list of dicts with id, user_id, tenant_id, resume_url, updated_at.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    rows = await conn.fetch(
        """
        SELECT id, user_id, tenant_id, resume_url, updated_at
        FROM   public.profiles
        WHERE  resume_url IS NOT NULL
          AND  updated_at < $1
        ORDER  BY updated_at ASC
        LIMIT  500
        """,
        cutoff,
    )
    return [dict(r) for r in rows]


async def cleanup_old_resumes(
    pool: asyncpg.Pool,
    delete_from_storage_fn: Any = None,
    retention_days: int = RESUME_RETENTION_DAYS,
) -> int:
    """Delete stale resume PDFs from storage and clear resume_url on profiles.

    Args:
        pool: Database connection pool.
        delete_from_storage_fn: Async callable(bucket, path) that deletes from
            Supabase Storage. Pass None for dry-run (logs only).
        retention_days: Number of days to retain resumes.

    Returns:
        Number of resumes cleaned up.

    """
    count = 0
    async with pool.acquire() as conn:
        stale = await find_stale_resumes(conn, retention_days)

    for record in stale:
        resume_url = record["resume_url"]
        profile_id = str(record["id"])

        if delete_from_storage_fn:
            try:
                # Extract path from URL: .../storage/v1/object/public/{bucket}/{path}
                parts = resume_url.split("/storage/v1/object/public/")
                if len(parts) == 2:
                    bucket_and_path = parts[1]
                    slash_idx = bucket_and_path.index("/")
                    bucket = bucket_and_path[:slash_idx]
                    path = bucket_and_path[slash_idx + 1 :]
                    await delete_from_storage_fn(bucket, path)
            except Exception as exc:
                logger.warning(
                    "Failed to delete resume from storage for profile %s: %s",
                    profile_id,
                    exc,
                )
                continue

        # Clear resume_url on the profile row
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.profiles
                SET    resume_url = NULL, updated_at = now()
                WHERE  id = $1
                """,
                profile_id,
            )
        count += 1

    if count > 0:
        logger.info(
            "Cleaned up %d stale resumes (retention=%d days)", count, retention_days
        )
        incr("retention.resumes_cleaned", value=count)

    return count


# ---------------------------------------------------------------------------
# Event payload anonymization
# ---------------------------------------------------------------------------


async def find_old_events(
    conn: asyncpg.Connection,
    retention_days: int = EVENT_PII_RETENTION_DAYS,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Find application_events with payloads older than the retention period."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    rows = await conn.fetch(
        """
        SELECT id, payload
        FROM   public.application_events
        WHERE  created_at < $1
          AND  payload != '{}'::jsonb
          AND  payload != '{"_anonymized": true}'::jsonb
        ORDER  BY created_at ASC
        LIMIT  $2
        """,
        cutoff,
        limit,
    )
    return [dict(r) for r in rows]


async def anonymize_old_events(
    pool: asyncpg.Pool,
    retention_days: int = EVENT_PII_RETENTION_DAYS,
    batch_size: int = 500,
) -> int:
    """Anonymize PII in old event payloads by redacting sensitive fields.

    Returns number of events anonymized.
    """
    import json

    count = 0
    async with pool.acquire() as conn:
        events = await find_old_events(conn, retention_days, limit=batch_size)

    for event in events:
        event_id = str(event["id"])
        payload = event["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)

        redacted = redact_event_payload(payload)
        redacted["_anonymized"] = True

        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.application_events
                SET    payload = $2::jsonb
                WHERE  id = $1
                """,
                event_id,
                json.dumps(redacted),
            )
        count += 1

    if count > 0:
        logger.info(
            "Anonymized %d old event payloads (retention=%d days)",
            count,
            retention_days,
        )
        incr("retention.events_anonymized", value=count)

    return count
