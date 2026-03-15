"""Saved Jobs API - Job Bookmarking Functionality.

Allows users to save/bookmark jobs without applying, providing a way to
track interesting opportunities for later review.
"""

from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from packages.backend.domain.tenant import TenantContext
from shared.logging_config import get_logger
from shared.validators import validate_uuid


async def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_user_id() -> str:
    raise NotImplementedError("User ID dependency not injected")


async def _get_tenant_ctx() -> TenantContext:
    raise NotImplementedError("Tenant context dependency not injected")


logger = get_logger("sorce.saved_jobs")

router = APIRouter(prefix="/saved-jobs", tags=["saved-jobs"])


class SavedJobResponse(BaseModel):
    """Response model for saved job."""

    id: str
    job_id: str
    user_id: str
    tenant_id: str
    created_at: str
    updated_at: str
    # Include job details for frontend convenience
    job_data: dict | None = None


class SaveJobRequest(BaseModel):
    """Request model for saving a job."""

    job_id: str


@router.post("", response_model=SavedJobResponse, status_code=status.HTTP_201_CREATED)
async def save_job(
    request: SaveJobRequest,
    user_id: str = Depends(_get_user_id),
    ctx: dict = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> SavedJobResponse:
    """Save/bookmark a job for later review."""

    # Validate job_id format
    try:
        validate_uuid(request.job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    async with db.acquire() as conn:
        # Check if job exists (jobs may not have tenant_id)
        job = await conn.fetchrow(
            "SELECT id, title, company, location, salary_min, salary_max FROM public.jobs WHERE id = $1::uuid",
            request.job_id,
        )

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if already saved
        existing = await conn.fetchrow(
            "SELECT id FROM public.saved_jobs WHERE user_id = $1::uuid AND job_id = $2::uuid",
            user_id,
            request.job_id,
        )

        if existing:
            raise HTTPException(status_code=409, detail="Job already saved")

        # Save the job (tenant_id may not exist in schema)
        try:
            saved = await conn.fetchrow(
                """
                INSERT INTO public.saved_jobs (user_id, job_id, tenant_id)
                VALUES ($1::uuid, $2::uuid, $3::uuid)
                RETURNING id, user_id, job_id, tenant_id, created_at, updated_at
                """,
                user_id,
                request.job_id,
                ctx.tenant_id,
            )
        except (asyncpg.UndefinedColumnError, asyncpg.ProgrammingError):
            saved = await conn.fetchrow(
                """
                INSERT INTO public.saved_jobs (user_id, job_id)
                VALUES ($1::uuid, $2::uuid)
                RETURNING id, user_id, job_id, created_at
                """,
                user_id,
                request.job_id,
            )

        logger.info(f"User {user_id} saved job {request.job_id}")

        created = saved["created_at"]
        updated = saved.get("updated_at", created)
        return SavedJobResponse(
            id=str(saved["id"]),
            job_id=str(saved["job_id"]),
            user_id=str(saved["user_id"]),
            tenant_id=str(saved.get("tenant_id", "")),
            created_at=created.isoformat(),
            updated_at=updated.isoformat(),
            job_data={
                "id": str(job["id"]),
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "salary_min": job["salary_min"],
                "salary_max": job["salary_max"],
            },
        )


@router.get("", response_model=list[SavedJobResponse])
async def list_saved_jobs(
    user_id: str = Depends(_get_user_id),
    ctx: dict = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
    limit: int = 50,
    offset: int = 0,
) -> list[SavedJobResponse]:
    """Get user's saved/bookmarked jobs."""

    async with db.acquire() as conn:
        try:
            rows = await conn.fetch(
                """
                SELECT
                    sj.id, sj.user_id, sj.job_id, sj.tenant_id, sj.created_at, sj.updated_at,
                    j.title, j.company, j.location, j.salary_min, j.salary_max, j.description
                FROM public.saved_jobs sj
                INNER JOIN public.jobs j ON sj.job_id = j.id
                WHERE sj.user_id = $1::uuid AND sj.tenant_id = $2::uuid
                ORDER BY sj.created_at DESC
                LIMIT $3 OFFSET $4
                """,
                user_id,
                ctx.tenant_id,
                limit,
                offset,
            )
        except (asyncpg.UndefinedColumnError, asyncpg.ProgrammingError):
            rows = await conn.fetch(
                """
                SELECT
                    sj.id, sj.user_id, sj.job_id, sj.created_at,
                    j.title, j.company, j.location, j.salary_min, j.salary_max, j.description
                FROM public.saved_jobs sj
                INNER JOIN public.jobs j ON sj.job_id = j.id
                WHERE sj.user_id = $1::uuid
                ORDER BY sj.created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset,
            )

        def row_updated_at(r):
            u = r.get("updated_at")
            return u.isoformat() if u else r["created_at"].isoformat()

        return [
            SavedJobResponse(
                id=str(row["id"]),
                job_id=str(row["job_id"]),
                user_id=str(row["user_id"]),
                tenant_id=str(row.get("tenant_id", "")),
                created_at=row["created_at"].isoformat(),
                updated_at=row_updated_at(row),
                job_data={
                    "id": str(row["job_id"]),
                    "title": row["title"],
                    "company": row["company"],
                    "location": row["location"],
                    "salary_min": row["salary_min"],
                    "salary_max": row["salary_max"],
                    "description": row.get("description", ""),
                },
            )
            for row in rows
        ]


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    job_id: str,
    user_id: str = Depends(_get_user_id),
    ctx: dict = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> None:
    """Remove a job from saved/bookmarked jobs."""

    # Validate job_id format
    try:
        validate_uuid(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    async with db.acquire() as conn:
        try:
            result = await conn.execute(
                "DELETE FROM public.saved_jobs WHERE user_id = $1::uuid AND job_id = $2::uuid AND tenant_id = $3::uuid",
                user_id,
                job_id,
                ctx.tenant_id,
            )
        except (asyncpg.UndefinedColumnError, asyncpg.ProgrammingError):
            result = await conn.execute(
                "DELETE FROM public.saved_jobs WHERE user_id = $1::uuid AND job_id = $2::uuid",
                user_id,
                job_id,
            )

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Saved job not found")

        logger.info(f"User {user_id} unsaved job {job_id}")


@router.get("/{job_id}", response_model=SavedJobResponse)
async def get_saved_job(
    job_id: str,
    user_id: str = Depends(_get_user_id),
    ctx: dict = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> SavedJobResponse:
    """Get a specific saved job."""

    # Validate job_id format
    try:
        validate_uuid(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    async with db.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                SELECT
                    sj.id, sj.user_id, sj.job_id, sj.tenant_id, sj.created_at, sj.updated_at,
                    j.title, j.company, j.location, j.salary_min, j.salary_max, j.description
                FROM public.saved_jobs sj
                INNER JOIN public.jobs j ON sj.job_id = j.id
                WHERE sj.user_id = $1::uuid AND sj.job_id = $2::uuid AND sj.tenant_id = $3::uuid
                """,
                user_id,
                job_id,
                ctx.tenant_id,
            )
        except (asyncpg.UndefinedColumnError, asyncpg.ProgrammingError):
            row = await conn.fetchrow(
                """
                SELECT
                    sj.id, sj.user_id, sj.job_id, sj.created_at,
                    j.title, j.company, j.location, j.salary_min, j.salary_max, j.description
                FROM public.saved_jobs sj
                INNER JOIN public.jobs j ON sj.job_id = j.id
                WHERE sj.user_id = $1::uuid AND sj.job_id = $2::uuid
                """,
                user_id,
                job_id,
            )

        if not row:
            raise HTTPException(status_code=404, detail="Saved job not found")

        updated = row.get("updated_at") or row["created_at"]
        return SavedJobResponse(
            id=str(row["id"]),
            job_id=str(row["job_id"]),
            user_id=str(row["user_id"]),
            tenant_id=str(row.get("tenant_id", "")),
            created_at=row["created_at"].isoformat(),
            updated_at=updated.isoformat(),
            job_data={
                "id": str(row["job_id"]),
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "salary_min": row["salary_min"],
                "salary_max": row["salary_max"],
                "description": row.get("description", ""),
            },
        )


@router.get("/count")
async def get_saved_jobs_count(
    user_id: str = Depends(_get_user_id),
    ctx: dict = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, int]:
    """Get total count of user's saved jobs."""

    async with db.acquire() as conn:
        try:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM public.saved_jobs WHERE user_id = $1::uuid AND tenant_id = $2::uuid",
                user_id,
                ctx.tenant_id,
            )
        except (asyncpg.UndefinedColumnError, asyncpg.ProgrammingError):
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM public.saved_jobs WHERE user_id = $1::uuid",
                user_id,
            )

        return {"count": count}
