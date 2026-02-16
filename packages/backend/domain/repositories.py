"""
Typed repository layer for database access.

Provides thin, type-annotated wrappers around raw SQL.
Used by both API routes and the worker agent.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from backend.domain.models import (
    Application,
    ApplicationDetail,
    ApplicationEvent,
    ApplicationInput,
)

# ---------------------------------------------------------------------------
# Transaction helper
# ---------------------------------------------------------------------------

@asynccontextmanager
async def db_transaction(
    pool: asyncpg.Pool,
) -> AsyncGenerator[asyncpg.Connection, None]:
    """Short-lived transaction scope usable from routes or worker."""
    async with pool.acquire() as conn, conn.transaction():
        yield conn


# ---------------------------------------------------------------------------
# Event helper (shared by API and worker)
# ---------------------------------------------------------------------------

async def record_event(
    conn: asyncpg.Connection,
    application_id: str,
    event_type: str,
    payload: dict | None = None,
    *,
    tenant_id: str | None = None,
) -> None:
    """Insert an append-only event row into application_events."""
    await conn.execute(
        """
        INSERT INTO public.application_events (application_id, event_type, payload, tenant_id)
        VALUES ($1, $2::public.application_event_type, $3::jsonb, $4)
        """,
        application_id,
        event_type,
        json.dumps(payload or {}),
        tenant_id,
    )


# ---------------------------------------------------------------------------
# ApplicationRepo
# ---------------------------------------------------------------------------

CLAIM_QUEUED_SQL = """
WITH next_task AS (
    SELECT id
    FROM   public.applications
    WHERE  status = 'QUEUED'
      AND  attempt_count < $1
      AND  (available_at IS NULL OR available_at <= now())
    ORDER  BY created_at ASC
    LIMIT  1
    FOR UPDATE SKIP LOCKED
)
UPDATE public.applications a
SET    status           = 'PROCESSING',
       locked_at        = now(),
       attempt_count    = a.attempt_count + 1,
       last_processed_at = now(),
       updated_at       = now()
FROM   next_task
WHERE  a.id = next_task.id
RETURNING a.id, a.user_id, a.job_id, a.tenant_id, a.attempt_count, a.blueprint_key;
"""

CLAIM_RESUMABLE_SQL = """
WITH resumable AS (
    SELECT a.id
    FROM   public.applications a
    WHERE  a.status = 'REQUIRES_INPUT'
      AND  a.attempt_count < $1
      AND  NOT EXISTS (
               SELECT 1
               FROM   public.application_inputs ai
               WHERE  ai.application_id = a.id
                 AND  ai.answer IS NULL
           )
    ORDER  BY a.updated_at ASC
    LIMIT  1
    FOR UPDATE SKIP LOCKED
)
UPDATE public.applications a
SET    status            = 'PROCESSING',
       locked_at         = now(),
       attempt_count     = a.attempt_count + 1,
       last_processed_at = now(),
       updated_at        = now()
FROM   resumable
WHERE  a.id = resumable.id
RETURNING a.id, a.user_id, a.job_id, a.tenant_id, a.attempt_count, a.blueprint_key;
"""


class ApplicationRepo:
    """CRUD and state-machine operations for applications."""

    @staticmethod
    async def claim_next(
        pool: asyncpg.Pool, max_attempts: int
    ) -> dict | None:
        """Atomically claim the next QUEUED or resumable task (any tenant)."""
        async with db_transaction(pool) as conn:
            row = await conn.fetchrow(CLAIM_QUEUED_SQL, max_attempts)
            if row is None:
                row = await conn.fetchrow(CLAIM_RESUMABLE_SQL, max_attempts)
            if row is None:
                return None
            task = dict(row)
            await record_event(
                conn, str(task["id"]), "CLAIMED",
                {"attempt_count": task["attempt_count"]},
                tenant_id=str(task["tenant_id"]) if task.get("tenant_id") else None,
            )
            return task



    @staticmethod
    async def update_status(
        conn: asyncpg.Connection,
        application_id: str,
        status: str,
        *,
        error_message: str | None = None,
    ) -> dict | None:
        """Update application status with appropriate side-effects."""
        if status == "APPLIED":
            row = await conn.fetchrow(
                """
                UPDATE public.applications
                SET    status        = $2::public.application_status,
                       submitted_at  = now(),
                       last_error    = NULL,
                       updated_at    = now()
                WHERE  id = $1
                RETURNING *
                """,
                application_id, status,
            )
        elif status == "FAILED":
            row = await conn.fetchrow(
                """
                UPDATE public.applications
                SET    status        = $2::public.application_status,
                       last_error    = $3,
                       updated_at    = now()
                WHERE  id = $1
                RETURNING *
                """,
                application_id, status, error_message,
            )
        else:
            row = await conn.fetchrow(
                """
                UPDATE public.applications
                SET    status     = $2::public.application_status,
                       last_error = CASE WHEN $2 = 'QUEUED' THEN NULL ELSE last_error END,
                       updated_at = now()
                WHERE  id = $1
                RETURNING *
                """,
                application_id, status,
            )
        return dict(row) if row else None

    @staticmethod
    async def get_by_id(
        conn: asyncpg.Connection, application_id: str
    ) -> dict | None:
        row = await conn.fetchrow(
            "SELECT * FROM public.applications WHERE id = $1",
            application_id,
        )
        return dict(row) if row else None

    @staticmethod
    async def get_by_id_and_tenant(
        conn: asyncpg.Connection, application_id: str, tenant_id: str
    ) -> dict | None:
        """Fetch application scoped to a tenant."""
        row = await conn.fetchrow(
            "SELECT * FROM public.applications WHERE id = $1 AND tenant_id = $2",
            application_id, tenant_id,
        )
        return dict(row) if row else None

    @staticmethod
    async def get_by_id_and_user(
        conn: asyncpg.Connection, application_id: str, user_id: str,
        tenant_id: str | None = None,
    ) -> dict | None:
        """Fetch application scoped to a user (and optionally tenant)."""
        if tenant_id:
            row = await conn.fetchrow(
                "SELECT * FROM public.applications WHERE id = $1 AND user_id = $2 AND tenant_id = $3",
                application_id, user_id, tenant_id,
            )
        else:
            row = await conn.fetchrow(
                "SELECT * FROM public.applications WHERE id = $1 AND user_id = $2",
                application_id, user_id,
            )
        return dict(row) if row else None

    @staticmethod
    async def list_for_tenant(
        conn: asyncpg.Connection,
        tenant_id: str,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Paginated list of applications for a tenant."""
        if status:
            rows = await conn.fetch(
                """
                SELECT * FROM public.applications
                WHERE  tenant_id = $1 AND status = $2::public.application_status
                ORDER  BY created_at DESC
                LIMIT  $3 OFFSET $4
                """,
                tenant_id, status, limit, offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT * FROM public.applications
                WHERE  tenant_id = $1
                ORDER  BY created_at DESC
                LIMIT  $2 OFFSET $3
                """,
                tenant_id, limit, offset,
            )
        return [dict(r) for r in rows]

    @staticmethod
    async def get_detail(
        conn: asyncpg.Connection, application_id: str,
        tenant_id: str | None = None,
    ) -> dict | None:
        """Fetch application + inputs + last 10 events."""
        if tenant_id:
            app_row = await conn.fetchrow(
                "SELECT * FROM public.applications WHERE id = $1 AND tenant_id = $2",
                application_id, tenant_id,
            )
        else:
            app_row = await conn.fetchrow(
                "SELECT * FROM public.applications WHERE id = $1",
                application_id,
            )
        if app_row is None:
            return None

        inputs_rows = await conn.fetch(
            """
            SELECT id, selector, question, field_type, answer, meta, resolved,
                   created_at, answered_at
            FROM   public.application_inputs
            WHERE  application_id = $1
            ORDER  BY created_at
            """,
            application_id,
        )

        events_rows = await conn.fetch(
            """
            SELECT id, event_type, payload, created_at
            FROM   public.application_events
            WHERE  application_id = $1
            ORDER  BY created_at DESC
            LIMIT  10
            """,
            application_id,
        )

        application = Application.model_validate(dict(app_row))
        inputs = [ApplicationInput.model_validate(dict(r)) for r in inputs_rows]
        events = [ApplicationEvent.model_validate(dict(r)) for r in events_rows]

        return ApplicationDetail(application=application, inputs=inputs, events=events)


# ---------------------------------------------------------------------------
# ProfileRepo
# ---------------------------------------------------------------------------

class ProfileRepo:
    """CRUD for user profiles."""

    @staticmethod
    async def get_profile_data(
        conn: asyncpg.Connection, user_id: str
    ) -> dict | None:
        """Return raw profile_data dict, or None."""
        row = await conn.fetchrow(
            "SELECT profile_data FROM public.profiles WHERE user_id = $1",
            user_id,
        )
        if row is None:
            return None
        data = row["profile_data"]
        return json.loads(data) if isinstance(data, str) else data

    @staticmethod
    async def upsert(
        conn: asyncpg.Connection,
        user_id: str,
        profile_data: dict,
        resume_url: str | None = None,
        tenant_id: str | None = None,
    ) -> dict:
        row = await conn.fetchrow(
            """
            INSERT INTO public.profiles (user_id, profile_data, resume_url, tenant_id)
            VALUES ($1, $2::jsonb, $3, $4)
            ON CONFLICT (user_id) DO UPDATE
                SET profile_data = EXCLUDED.profile_data,
                    resume_url   = COALESCE(EXCLUDED.resume_url, profiles.resume_url),
                    tenant_id    = COALESCE(EXCLUDED.tenant_id, profiles.tenant_id),
                    updated_at   = now()
            RETURNING id, user_id, profile_data, resume_url, tenant_id, created_at, updated_at
            """,
            user_id,
            json.dumps(profile_data),
            resume_url,
            tenant_id,
        )
        return dict(row)


# ---------------------------------------------------------------------------
# JobRepo
# ---------------------------------------------------------------------------

class JobRepo:
    """Read operations for jobs."""

    @staticmethod
    async def get_by_id(conn: asyncpg.Connection, job_id: str) -> dict | None:
        row = await conn.fetchrow(
            "SELECT * FROM public.jobs WHERE id = $1", job_id
        )
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# InputRepo
# ---------------------------------------------------------------------------

class InputRepo:
    """Operations on application_inputs."""

    @staticmethod
    async def get_answered(
        conn: asyncpg.Connection, application_id: str
    ) -> list[dict]:
        rows = await conn.fetch(
            """
            SELECT selector, question, answer
            FROM   public.application_inputs
            WHERE  application_id = $1
              AND  answer IS NOT NULL
            """,
            application_id,
        )
        return [dict(r) for r in rows]

    @staticmethod
    async def get_unresolved(
        conn: asyncpg.Connection, application_id: str
    ) -> list[dict]:
        rows = await conn.fetch(
            """
            SELECT id, selector, question, field_type, answer, meta,
                   resolved, created_at, answered_at
            FROM   public.application_inputs
            WHERE  application_id = $1
              AND  resolved = false
            ORDER  BY created_at
            """,
            application_id,
        )
        return [dict(r) for r in rows]

    @staticmethod
    async def insert_unresolved(
        conn: asyncpg.Connection,
        application_id: str,
        unresolved: list[dict],
        form_fields: list[dict],
        tenant_id: str | None = None,
    ) -> None:
        """Insert application_inputs rows with rich meta from form field descriptors."""
        field_lookup: dict[str, dict] = {f["selector"]: f for f in form_fields}
        rows = []
        for u in unresolved:
            sel = u["selector"]
            ff = field_lookup.get(sel)
            meta: dict[str, Any] = {}
            if ff:
                meta = {
                    "field_type": ff.get("type", "text"),
                    "label": ff.get("label", ""),
                    "options": ff.get("options"),
                    "step_index": ff.get("step_index", 0),
                }
            rows.append((
                application_id,
                sel,
                u["question"],
                ff.get("type", "text") if ff else "text",
                json.dumps(meta),
                tenant_id,
            ))

        await conn.executemany(
            """
            INSERT INTO public.application_inputs
                (application_id, selector, question, field_type, meta, tenant_id)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6)
            ON CONFLICT DO NOTHING
            """,
            rows,
        )

    @staticmethod
    async def update_answers(
        conn: asyncpg.Connection,
        answers: list[dict],
    ) -> None:
        """Set answer + resolved on each input row."""
        await conn.executemany(
            """
            UPDATE public.application_inputs
            SET    answer      = $2,
                   answered_at = now(),
                   resolved    = true
            WHERE  id = $1
            """,
            [(a["input_id"], a["answer"]) for a in answers],
        )


# ---------------------------------------------------------------------------
# EventRepo
# ---------------------------------------------------------------------------

class EventRepo:
    """Thin wrapper – delegates to record_event for consistency."""

    @staticmethod
    async def emit(
        conn: asyncpg.Connection,
        application_id: str,
        event_type: str,
        payload: dict | None = None,
        *,
        tenant_id: str | None = None,
    ) -> None:
        await record_event(conn, application_id, event_type, payload, tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# TenantRepo
# ---------------------------------------------------------------------------

class TenantRepo:
    """CRUD for tenants and tenant membership."""

    @staticmethod
    async def get_by_id(conn: asyncpg.Connection, tenant_id: str) -> dict | None:
        """Fetch tenant by ID."""
        row = await conn.fetchrow(
            "SELECT * FROM public.tenants WHERE id = $1", tenant_id
        )
        return dict(row) if row else None

    @staticmethod
    async def get_by_slug(conn: asyncpg.Connection, slug: str) -> dict | None:
        row = await conn.fetchrow(
            "SELECT * FROM public.tenants WHERE slug = $1", slug
        )
        return dict(row) if row else None

    @staticmethod
    async def update_plan(
        conn: asyncpg.Connection,
        tenant_id: str,
        plan: str,
        plan_metadata: dict | None = None,
    ) -> dict | None:
        row = await conn.fetchrow(
            """
            UPDATE public.tenants
            SET    plan          = $2::public.tenant_plan,
                   plan_metadata = COALESCE($3::jsonb, plan_metadata),
                   updated_at    = now()
            WHERE  id = $1
            RETURNING *
            """,
            tenant_id, plan,
            json.dumps(plan_metadata) if plan_metadata else None,
        )
        return dict(row) if row else None

    @staticmethod
    async def list_all(
        conn: asyncpg.Connection,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Paginated list of all tenants (admin only)."""
        rows = await conn.fetch(
            "SELECT * FROM public.tenants ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, offset,
        )
        return [dict(r) for r in rows]

    @staticmethod
    async def count_monthly_applications(
        conn: asyncpg.Connection, tenant_id: str
    ) -> int:
        """Count applications created by this tenant in the current calendar month."""
        row = await conn.fetchrow(
            """
            SELECT COUNT(*) AS cnt
            FROM   public.applications
            WHERE  tenant_id = $1
              AND  created_at >= date_trunc('month', now())
            """,
            tenant_id,
        )
        return int(row["cnt"]) if row else 0

    @staticmethod
    async def count_concurrent_processing(
        conn: asyncpg.Connection, tenant_id: str
    ) -> int:
        """Count applications currently PROCESSING for this tenant."""
        row = await conn.fetchrow(
            """
            SELECT COUNT(*) AS cnt
            FROM   public.applications
            WHERE  tenant_id = $1
              AND  status = 'PROCESSING'
            """,
            tenant_id,
        )
        return int(row["cnt"]) if row else 0


# ---------------------------------------------------------------------------
# CoverLetterRepo
# ---------------------------------------------------------------------------

class CoverLetterRepo:
    """CRUD for cover letters."""

    @staticmethod
    async def create(
        conn: asyncpg.Connection,
        user_id: str,
        job_id: str,
        content: str,
        template_id: str | None = None,
        tone: str | None = None,
        quality_score: float | None = None,
        suggestions: list[str] | None = None,
    ) -> dict:
        row = await conn.fetchrow(
            """
            INSERT INTO public.cover_letters (
                user_id, job_id, content, template_id, tone,
                quality_score, suggestions
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            RETURNING *
            """,
            user_id, job_id, content, template_id, tone,
            quality_score, json.dumps(suggestions) if suggestions else None,
        )
        return dict(row)

    @staticmethod
    async def list_by_user(
        conn: asyncpg.Connection,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        rows = await conn.fetch(
            """
            SELECT * FROM public.cover_letters
            WHERE  user_id = $1
            ORDER  BY created_at DESC
            LIMIT  $2 OFFSET $3
            """,
            user_id, limit, offset,
        )
        return [dict(r) for r in rows]

    @staticmethod
    async def get_by_id(
        conn: asyncpg.Connection,
        letter_id: str,
    ) -> dict | None:
        row = await conn.fetchrow(
            "SELECT * FROM public.cover_letters WHERE id = $1",
            letter_id,
        )
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# JobMatchCacheRepo
# ---------------------------------------------------------------------------

class JobMatchCacheRepo:
    """Read/Write access to the AI job match cache."""

    @staticmethod
    async def get(
        conn: asyncpg.Connection,
        job_id: str,
        profile_hash: str,
    ) -> dict | None:
        """Retrieve cached score if it exists."""
        row = await conn.fetchrow(
            """
            SELECT score_data
            FROM   public.job_match_cache
            WHERE  job_id = $1 AND profile_hash = $2
            """,
            job_id,
            profile_hash,
        )
        return json.loads(row["score_data"]) if row else None

    @staticmethod
    async def put(
        conn: asyncpg.Connection,
        job_id: str,
        profile_hash: str,
        score_data: dict,
    ) -> None:
        """Cache a score result (upsert)."""
        await conn.execute(
            """
            INSERT INTO public.job_match_cache (job_id, profile_hash, score_data)
            VALUES ($1, $2, $3::jsonb)
            ON CONFLICT (job_id, profile_hash)
            DO UPDATE SET
                score_data = EXCLUDED.score_data,
                created_at = now()
            """,
            job_id,
            profile_hash,
            json.dumps(score_data),
        )
