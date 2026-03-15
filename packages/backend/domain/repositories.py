"""Typed repository layer for database access.

Provides thin, type-annotated wrappers around raw SQL.
Used by both API routes and the worker agent.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, List

import asyncpg

from packages.backend.domain.models import (
    Application,
    ApplicationDetail,
    ApplicationEvent,
    ApplicationInput,
)
from shared.sql_utils import escape_ilike

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
    async def claim_next(pool: asyncpg.Pool, max_attempts: int) -> dict | None:
        """Atomically claim the next QUEUED or resumable task (any tenant)."""
        async with db_transaction(pool) as conn:
            row = await conn.fetchrow(CLAIM_QUEUED_SQL, max_attempts)
            if row is None:
                row = await conn.fetchrow(CLAIM_RESUMABLE_SQL, max_attempts)
            if row is None:
                return None
            task = dict(row)
            await record_event(
                conn,
                str(task["id"]),
                "CLAIMED",
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
                application_id,
                status,
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
                application_id,
                status,
                error_message,
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
                application_id,
                status,
            )
        return dict(row) if row else None

    @staticmethod
    async def get_by_id(conn: asyncpg.Connection, application_id: str) -> dict | None:
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
            application_id,
            tenant_id,
        )
        return dict(row) if row else None

    @staticmethod
    async def get_by_id_and_user(
        conn: asyncpg.Connection,
        application_id: str,
        user_id: str,
        tenant_id: str | None = None,
    ) -> dict | None:
        """Fetch application scoped to a user (and optionally tenant)."""
        if tenant_id:
            row = await conn.fetchrow(
                "SELECT * FROM public.applications WHERE id = $1 AND user_id = $2 AND tenant_id = $3",
                application_id,
                user_id,
                tenant_id,
            )
        else:
            row = await conn.fetchrow(
                "SELECT * FROM public.applications WHERE id = $1 AND user_id = $2",
                application_id,
                user_id,
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
                tenant_id,
                status,
                limit,
                offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT * FROM public.applications
                WHERE  tenant_id = $1
                ORDER  BY created_at DESC
                LIMIT  $2 OFFSET $3
                """,
                tenant_id,
                limit,
                offset,
            )
        return [dict(r) for r in rows]

    @staticmethod
    async def get_detail(
        conn: asyncpg.Connection,
        application_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> ApplicationDetail | None:
        """Fetch application + inputs + last 10 events.

        H5: N+1 Query Fix - Uses single query with JOINs instead of 3 separate queries.
        This reduces database round-trips from 3 to 1, improving performance.
        """
        import json

        # Single query with LEFT JOINs and array aggregation
        if tenant_id:
            row = await conn.fetchrow(
                """
                SELECT
                    a.*,
                    COALESCE(
                        json_agg(
                            DISTINCT jsonb_build_object(
                                'id', ai.id,
                                'selector', ai.selector,
                                'question', ai.question,
                                'field_type', ai.field_type,
                                'answer', ai.answer,
                                'meta', ai.meta,
                                'resolved', ai.resolved,
                                'created_at', ai.created_at,
                                'answered_at', ai.answered_at
                            )
                            ORDER BY ai.created_at
                        ) FILTER (WHERE ai.id IS NOT NULL),
                        '[]'::json
                    ) AS inputs_array,
                    COALESCE(
                        json_agg(
                            DISTINCT jsonb_build_object(
                                'id', ae.id,
                                'event_type', ae.event_type,
                                'payload', ae.payload,
                                'created_at', ae.created_at
                            )
                            ORDER BY ae.created_at DESC
                        ) FILTER (WHERE ae.id IS NOT NULL),
                        '[]'::json
                    ) AS events_array
                FROM public.applications a
                LEFT JOIN public.application_inputs ai ON ai.application_id = a.id
                LEFT JOIN (
                    SELECT id, event_type, payload, created_at, application_id
                    FROM public.application_events
                    WHERE application_id = $1
                    ORDER BY created_at DESC
                    LIMIT 10
                ) ae ON ae.application_id = a.id
                WHERE a.id = $1 AND (a.tenant_id = $2 OR $2 IS NULL)
                  AND (a.user_id = $3 OR $3 IS NULL)
                GROUP BY a.id
                """,
                application_id,
                tenant_id,
                user_id,
            )
        else:
            row = await conn.fetchrow(
                """
                SELECT
                    a.*,
                    COALESCE(
                        json_agg(
                            DISTINCT jsonb_build_object(
                                'id', ai.id,
                                'selector', ai.selector,
                                'question', ai.question,
                                'field_type', ai.field_type,
                                'answer', ai.answer,
                                'meta', ai.meta,
                                'resolved', ai.resolved,
                                'created_at', ai.created_at,
                                'answered_at', ai.answered_at
                            )
                            ORDER BY ai.created_at
                        ) FILTER (WHERE ai.id IS NOT NULL),
                        '[]'::json
                    ) AS inputs_array,
                    COALESCE(
                        json_agg(
                            DISTINCT jsonb_build_object(
                                'id', ae.id,
                                'event_type', ae.event_type,
                                'payload', ae.payload,
                                'created_at', ae.created_at
                            )
                            ORDER BY ae.created_at DESC
                        ) FILTER (WHERE ae.id IS NOT NULL),
                        '[]'::json
                    ) AS events_array
                FROM public.applications a
                LEFT JOIN public.application_inputs ai ON ai.application_id = a.id
                LEFT JOIN (
                    SELECT id, event_type, payload, created_at, application_id
                    FROM public.application_events
                    WHERE application_id = $1
                    ORDER BY created_at DESC
                    LIMIT 10
                ) ae ON ae.application_id = a.id
                WHERE a.id = $1
                GROUP BY a.id
                """,
                application_id,
            )

        if row is None:
            return None

        # Extract application data (all columns except the aggregated arrays)
        app_dict = {
            k: v
            for k, v in dict(row).items()
            if k not in ("inputs_array", "events_array")
        }
        application = Application.model_validate(app_dict)

        # Parse aggregated JSON arrays
        inputs_data = row.get("inputs_array") or []
        if isinstance(inputs_data, str):
            inputs_data = json.loads(inputs_data)
        inputs = [ApplicationInput.model_validate(dict(inp)) for inp in inputs_data]

        events_data = row.get("events_array") or []
        if isinstance(events_data, str):
            events_data = json.loads(events_data)
        events = [ApplicationEvent.model_validate(dict(evt)) for evt in events_data]

        return ApplicationDetail(application=application, inputs=inputs, events=events)


# ---------------------------------------------------------------------------
# ProfileRepo
# ---------------------------------------------------------------------------


class ProfileRepo:
    """CRUD for user profiles."""

    @staticmethod
    async def get_profile_data(conn: asyncpg.Connection, user_id: str) -> dict | None:
        """Return raw profile_data dict, or None."""
        row = await conn.fetchrow(
            "SELECT profile_data FROM public.profiles WHERE user_id = $1",
            user_id,
        )
        if row is None:
            return None
        data = row["profile_data"]
        result = json.loads(data) if isinstance(data, str) else data
        return result  # type: ignore[no-any-return]

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
                    resume_url   = CASE WHEN EXCLUDED.resume_url = '' THEN NULL ELSE COALESCE(
    NULLIF(EXCLUDED.resume_url, ''), profiles.resume_url) END,
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
    """Read operations for jobs with comprehensive job details."""

    @staticmethod
    async def get_by_id(conn: asyncpg.Connection, job_id: str) -> dict | None:
        """Get job details by ID. Works with JobSpy schema (no companies join)."""
        row = await conn.fetchrow(
            "SELECT * FROM public.jobs WHERE id = $1",
            job_id,
        )
        if not row:
            return None

        def _iso(d):
            return d.isoformat() if d and hasattr(d, "isoformat") else d

        skills = row.get("skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]

        app_url = row.get("application_url") or row.get("url")
        is_remote = row.get("is_remote")
        if is_remote is None and row.get("remote_policy"):
            is_remote = row["remote_policy"] in ("remote", "hybrid")

        return {
            "id": str(row["id"]),
            "title": row["title"],
            "company": row["company"],
            "location": row.get("location"),
            "remote": is_remote,
            "salary_min": row.get("salary_min"),
            "salary_max": row.get("salary_max"),
            "job_type": row.get("job_type"),
            "description": row.get("description"),
            "requirements": skills,
            "responsibilities": [],
            "qualifications": [],
            "benefits": [],
            "work_environment": [],
            "company_name": row.get("company"),
            "company_description": None,
            "company_logo_url": row.get("company_logo_url"),
            "company_size": None,
            "company_industry": row.get("company_industry"),
            "company_culture": None,
            "company_values": [],
            "company_technologies": [],
            "company_benefits": [],
            "company_work_style": None,
            "company_growth_stage": None,
            "company_funding_stage": None,
            "company_headquarters_location": None,
            "employee_count": None,
            "founded_year": None,
            "company_website": None,
            "company_linkedin_url": None,
            "created_at": _iso(row.get("created_at")),
            "updated_at": _iso(row.get("updated_at")),
            "is_active": True,
            "source": row.get("source"),
            "job_level": row.get("job_level") or row.get("experience_level") or "",
            "experience_years_min": None,
            "experience_years_max": None,
            "education_required": None,
            "skills_required": skills,
            "industry_focus": None,
            "remote_option": is_remote,
            "visa_sponsorship": None,
            "deadline": None,
            "application_url": app_url,
        }

    @staticmethod
    async def list_jobs(
        conn: asyncpg.Connection,
        limit: int = 100,
        offset: int = 0,
        filters: dict | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> List[dict]:
        """List jobs with comprehensive details.

        SECURITY: Uses parameterized queries to prevent SQL injection.
        All filters and pagination parameters are properly bound.
        """
        query = """
            SELECT
                j.*,
                c.name as company_name,
                c.description as company_description,
                c.logo_url as company_logo_url,
                c.size as company_size,
                c.industry as company_industry,
                c.culture as company_culture,
                c.values as company_values,
                c.technologies as company_technologies,
                c.benefits as company_benefits,
                c.work_style as company_work_style,
                c.growth_stage as company_growth_stage,
                c.funding_stage as company_funding_stage,
                c.headquarters_location as company_headquarters_location,
                c.employee_count as employee_count,
                c.founded_year as founded_year,
                c.website as company_website,
                c.linkedin_url as company_linkedin_url
            FROM public.jobs j
            LEFT JOIN public.companies c ON j.company_id = c.id
            WHERE j.is_active = true
        """

        # Build parameter array and conditions (CRITICAL: asyncpg uses $1, $2, etc. as literal strings)
        params: list[Any] = []
        conditions: list[str] = []

        # Apply filters if provided (build conditions with proper $N placeholders)
        if filters:
            if "location" in filters:
                location_value = filters["location"]
                if location_value:
                    params.append(f"%{escape_ilike(location_value)}%")
                    conditions.append("j.location ILIKE ${" + str(len(params)) + "}")

            if "keywords" in filters:
                keywords_value = filters["keywords"]
                if keywords_value:
                    params.append(f"%{escape_ilike(keywords_value)}%")
                    n = len(params)
                    conditions.append(
                        "("
                        f"j.title ILIKE ${n} OR j.description ILIKE ${n} OR j.company ILIKE ${n})"
                        ")"
                    )

            if "company_name" in filters:
                company_value = filters["company_name"]
                if company_value:
                    params.append(f"%{escape_ilike(company_value)}%")
                    conditions.append("j.company ILIKE ${" + str(len(params)) + "}")

            if "remote" in filters:
                remote_value = filters["remote"]
                if remote_value is not None:
                    params.append(remote_value)
                    conditions.append("j.remote = ${" + str(len(params)) + "}")

            if "job_type" in filters:
                job_type_value = filters["job_type"]
                if job_type_value:
                    params.append(job_type_value)
                    conditions.append("j.job_type = ${" + str(len(params)) + "}")

            if "company_size" in filters:
                company_size_value = filters["company_size"]
                if company_size_value:
                    params.append(company_size_value)
                    conditions.append("c.size = ${" + str(len(params)) + "}")

            if "industry" in filters:
                industry_value = filters["industry"]
                if industry_value:
                    params.append(industry_value)
                    conditions.append("c.industry = ${" + str(len(params)) + "}")

            if "salary_min" in filters:
                salary_min_value = filters["salary_min"]
                if salary_min_value is not None:
                    params.append(salary_min_value)
                    conditions.append("j.salary_min >= ${" + str(len(params)) + "}")

            if "salary_max" in filters:
                salary_max_value = filters["salary_max"]
                if salary_max_value is not None:
                    params.append(salary_max_value)
                    conditions.append("j.salary_max <= ${" + str(len(params)) + "}")

        # Add WHERE conditions if any
        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY j.created_at DESC"

        # Add pagination with proper parameter binding
        if offset > 0:
            params.append(offset)
            query += " OFFSET ${" + str(len(params)) + "}"

        if limit > 0:
            params.append(limit)
            query += " LIMIT ${" + str(len(params)) + "}"

        # CRITICAL: Replace ${N} patterns with actual $N for asyncpg
        # asyncpg requires literal $1, $2, etc. in the query string
        # Use regex to replace ${N} with $N
        import re

        final_query = re.sub(r"\$\{(\d+)\}", lambda m: "$" + m.group(1), query)

        # Execute query with parameters
        rows = await conn.fetch(final_query, *params)

        # Format with comprehensive job details
        jobs = []
        for row in rows:
            job_details = {
                "id": row["id"],
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "remote": row["remote"],
                "salary_min": row["salary_min"],
                "salary_max": row["salary_max"],
                "job_type": row["job_type"],
                "description": row["description"],
                "requirements": row["requirements"] or [],
                "responsibilities": row["responsibilities"] or [],
                "qualifications": row["qualifications"] or [],
                "benefits": row["benefits"] or [],
                "work_environment": row["work_environment"] or [],
                "company_name": row["company_name"],
                "company_description": row["company_description"],
                "company_logo_url": row["company_logo_url"],
                "company_size": row["company_size"],
                "company_industry": row["company_industry"],
                "company_culture": row["company_culture"],
                "company_values": row["company_values"] or [],
                "company_technologies": row["company_technologies"] or [],
                "company_benefits": row["company_benefits"] or [],
                "company_work_style": row["company_work_style"] or [],
                "company_growth_stage": row["company_growth_stage"] or "",
                "company_funding_stage": row["company_funding_stage"] or "",
                "company_headquarters_location": row["company_headquarters_location"]
                or "",
                "employee_count": row["employee_count"],
                "founded_year": row["founded_year"],
                "company_website": row["company_website"],
                "company_linkedin_url": row["company_linkedin_url"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
                "is_active": row["is_active"],
                "source": row["source"],
                "job_level": row.get("job_level", ""),
                "experience_years_min": row.get("experience_years_min"),
                "experience_years_max": row.get("experience_years_max"),
                "education_required": row.get("education_required"),
                "skills_required": row.get("skills_required") or [],
                "industry_focus": row.get("industry_focus"),
                "remote_option": row.get("remote_option"),
                "visa_sponsorship": row.get("visa_sponsorship"),
                "deadline": row.get("deadline"),
                "application_url": row.get("application_url"),
            }
            jobs.append(job_details)

        return jobs


# ---------------------------------------------------------------------------
# InputRepo
# ---------------------------------------------------------------------------


class InputRepo:
    """Operations on application_inputs."""

    @staticmethod
    async def get_answered(conn: asyncpg.Connection, application_id: str) -> list[dict]:
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
            rows.append(
                (
                    application_id,
                    sel,
                    u["question"],
                    ff.get("type", "text") if ff else "text",
                    json.dumps(meta),
                    tenant_id,
                )
            )

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
        application_id: str | None = None,
    ) -> None:
        """Set answer + resolved on each input row. Scoped by application_id to prevent IDOR."""
        if not application_id:
            raise ValueError("application_id is required to prevent IDOR")
        for a in answers:
            await conn.execute(
                """
                UPDATE public.application_inputs
                SET    answer      = $2,
                       answered_at = now(),
                       resolved    = true
                WHERE  id = $1 AND application_id = $3
                """,
                a["input_id"],
                a["answer"],
                application_id,
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
        await record_event(
            conn, application_id, event_type, payload, tenant_id=tenant_id
        )


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
        row = await conn.fetchrow("SELECT * FROM public.tenants WHERE slug = $1", slug)
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
            tenant_id,
            plan,
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
            limit,
            offset,
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
            user_id,
            job_id,
            content,
            template_id,
            tone,
            quality_score,
            json.dumps(suggestions) if suggestions else None,
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
            user_id,
            limit,
            offset,
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

    @staticmethod
    async def get_by_job_user(
        conn: asyncpg.Connection,
        user_id: str,
        job_id: str,
    ) -> dict | None:
        """Get most recent cover letter for user+job."""
        row = await conn.fetchrow(
            """
            SELECT * FROM public.cover_letters
            WHERE user_id = $1 AND job_id = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
            job_id,
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


# ---------------------------------------------------------------------------
# SubscriptionRepo (stub for billing tests; full impl when billing schema exists)
# ---------------------------------------------------------------------------


class SubscriptionRepo:
    """Stub for subscription queries. Extend when billing tables exist."""

    @staticmethod
    async def get_by_user_id(conn: asyncpg.Connection, user_id: str) -> dict | None:
        row = await conn.fetchrow(
            "SELECT id, user_id, stripe_subscription_id, tier, status "
            "FROM public.billing_subscriptions WHERE user_id = $1 LIMIT 1",
            user_id,
        )
        return dict(row) if row else None

    @staticmethod
    async def update_tier(
        conn: asyncpg.Connection, user_id: str, tier: str
    ) -> None:
        await conn.execute(
            "UPDATE public.billing_subscriptions SET tier = $1 WHERE user_id = $2",
            tier,
            user_id,
        )


# ---------------------------------------------------------------------------
# UsageRepo (stub for billing tests; full impl when usage tables exist)
# ---------------------------------------------------------------------------


class UsageRepo:
    """Stub for usage tracking. Extend when usage tables exist."""

    @staticmethod
    async def track_usage(
        conn: asyncpg.Connection,
        *,
        tenant_id: str,
        endpoint: str,
        tokens_used: int,
    ) -> None:
        await conn.execute(
            """
            INSERT INTO public.billing_usage (tenant_id, endpoint, tokens_used)
            VALUES ($1, $2, $3)
            """,
            tenant_id,
            endpoint,
            tokens_used,
        )

    @staticmethod
    async def get_monthly_usage(
        conn: asyncpg.Connection, tenant_id: str
    ) -> dict[str, Any]:
        row = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(tokens_used), 0) AS total_tokens,
                   COUNT(*) AS api_calls,
                   0 AS jobs_matched
            FROM public.billing_usage
            WHERE tenant_id = $1 AND created_at >= date_trunc('month', now())
            """,
            tenant_id,
        )
        return dict(row) if row else {"total_tokens": 0, "api_calls": 0, "jobs_matched": 0}
