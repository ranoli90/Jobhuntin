"""Background Job Queue — async task processing with retries and scheduling.

Uses PostgreSQL as a reliable queue backend (no external dependencies like Redis/Celery).
Supports:
- Delayed job execution
- Automatic retries with exponential backoff
- Priority queues
- Dead letter queue for failed jobs
- Job deduplication
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Coroutine
from datetime import timezone, UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import asyncpg
from pydantic import BaseModel, Field
from shared.logging_config import get_logger

from shared.metrics import incr, observe

logger = get_logger("sorce.job_queue")


class JobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    queue: str = "default"
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    attempts: int = 0
    max_attempts: int = 3
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None
    dedup_key: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str | None = None


class JobResult(BaseModel):
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    retry_after: float | None = None


JobHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, JobResult]]


class JobQueueConfig:
    DEFAULT_RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min
    MAX_RETRY_ATTEMPTS = 3
    CLAIM_TIMEOUT_SECONDS = 300
    BATCH_SIZE = 10
    POLL_INTERVAL_SECONDS = 5


class JobQueueRepo:
    @staticmethod
    async def enqueue(
        conn: asyncpg.Connection,
        job: Job,
    ) -> str:
        row = await conn.fetchrow(
            """
            INSERT INTO public.background_jobs
                (id, queue, job_type, payload, status, priority, max_attempts,
                 scheduled_at, dedup_key, tenant_id)
            VALUES ($1, $2, $3, $4::jsonb, $5::public.job_status, $6::public.job_priority, $7, $8, $9, $10)
            ON CONFLICT (dedup_key) WHERE dedup_key IS NOT NULL DO NOTHING
            RETURNING id
            """,
            job.id,
            job.queue,
            job.job_type,
            json.dumps(job.payload),
            JobStatus.QUEUED.value if not job.scheduled_at else JobStatus.PENDING.value,
            job.priority.value,
            job.max_attempts,
            job.scheduled_at,
            job.dedup_key,
            job.tenant_id,
        )
        if row:
            incr("job_queue.enqueued", {"queue": job.queue, "job_type": job.job_type})
            return str(row["id"])
        return ""

    @staticmethod
    async def claim(
        conn: asyncpg.Connection,
        queues: list[str] | None = None,
        batch_size: int = JobQueueConfig.BATCH_SIZE,
    ) -> list[Job]:
        queue_filter = ""
        params: list[Any] = [batch_size, JobQueueConfig.CLAIM_TIMEOUT_SECONDS]
        if queues:
            queue_filter = "AND queue = ANY($3)"
            params.append(queues)

        rows = await conn.fetch(
            f"""  # nosec
            WITH claimable AS (
                SELECT id
                FROM public.background_jobs
                WHERE status IN ('queued', 'pending')
                  AND (scheduled_at IS NULL OR scheduled_at <= now())
                  AND attempts < max_attempts
                  {queue_filter}
                ORDER BY
                    CASE priority
                        WHEN 'critical' THEN 0
                        WHEN 'high' THEN 1
                        WHEN 'normal' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    created_at ASC
                LIMIT $1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE public.background_jobs j
            SET status = 'running',
                started_at = now(),
                attempts = j.attempts + 1,
                locked_at = now(),
                lock_expires_at = now() + interval '1 second' * $2
            FROM claimable c
            WHERE j.id = c.id
            RETURNING j.*
            """,
            *params,
        )
        return [JobQueueRepo._row_to_model(r) for r in rows]

    @staticmethod
    async def complete(
        conn: asyncpg.Connection,
        job_id: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        await conn.execute(
            """
            UPDATE public.background_jobs
            SET status = 'completed',
                completed_at = now(),
                result = $2::jsonb,
                locked_at = NULL,
                lock_expires_at = NULL
            WHERE id = $1
            """,
            job_id,
            json.dumps(result) if result else None,
        )
        incr("job_queue.completed")

    @staticmethod
    async def fail(
        conn: asyncpg.Connection,
        job_id: str,
        error_message: str,
        retry_after_seconds: int | None = None,
    ) -> None:
        if retry_after_seconds:
            scheduled_at = f"now() + interval '{retry_after_seconds} seconds'"
            await conn.execute(
                f"""  # nosec
                UPDATE public.background_jobs
                SET status = 'queued',
                    error_message = $2,
                    scheduled_at = {scheduled_at},
                    locked_at = NULL,
                    lock_expires_at = NULL
                WHERE id = $1
                """,
                job_id,
                error_message[:500],
            )
            incr("job_queue.retry_scheduled")
        else:
            await conn.execute(
                """
                UPDATE public.background_jobs
                SET status = 'failed',
                    error_message = $2,
                    completed_at = now(),
                    locked_at = NULL,
                    lock_expires_at = NULL
                WHERE id = $1
                """,
                job_id,
                error_message[:500],
            )
            incr("job_queue.failed")

    @staticmethod
    async def get_stats(
        conn: asyncpg.Connection, queue: str | None = None
    ) -> dict[str, int]:
        queue_filter = "WHERE queue = $1" if queue else ""
        params = [queue] if queue else []

        row = await conn.fetchrow(
            f"""  # nosec
            SELECT
                COUNT(*) FILTER (WHERE status = 'pending')::int AS pending,
                COUNT(*) FILTER (WHERE status = 'queued')::int AS queued,
                COUNT(*) FILTER (WHERE status = 'running')::int AS running,
                COUNT(*) FILTER (WHERE status = 'completed')::int AS completed,
                COUNT(*) FILTER (WHERE status = 'failed')::int AS failed
            FROM public.background_jobs
            {queue_filter}
            """,
            *params,
        )
        return dict(row) if row else {}

    @staticmethod
    async def cleanup_old_jobs(
        conn: asyncpg.Connection,
        days_old: int = 30,
    ) -> int:
        result = await conn.execute(
            """
            DELETE FROM public.background_jobs
            WHERE status IN ('completed', 'failed', 'cancelled')
              AND completed_at < now() - interval '1 day' * $1
            """,
            days_old,
        )
        deleted = int(result.split()[-1]) if "DELETE" in result else 0
        if deleted > 0:
            logger.info("Cleaned up %d old jobs", deleted)
        return deleted

    @staticmethod
    def _row_to_model(row: asyncpg.Record) -> Job:
        return Job(
            id=str(row["id"]),
            queue=row["queue"],
            job_type=row["job_type"],
            payload=json.loads(row["payload"]) if row["payload"] else {},
            status=JobStatus(row["status"]),
            priority=JobPriority(row["priority"]),
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            scheduled_at=row["scheduled_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error_message=row["error_message"],
            result=json.loads(row["result"]) if row["result"] else None,
            dedup_key=row["dedup_key"],
            tenant_id=str(row["tenant_id"]) if row["tenant_id"] else None,
            created_at=row["created_at"],
        )


class BackgroundJobQueue:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.handlers: dict[str, JobHandler] = {}
        self._running = False

    def register_handler(self, job_type: str, handler: JobHandler) -> None:
        self.handlers[job_type] = handler
        logger.info("Registered handler for job type: %s", job_type)

    async def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any],
        *,
        queue: str = "default",
        priority: JobPriority = JobPriority.NORMAL,
        scheduled_at: datetime | None = None,
        dedup_key: str | None = None,
        max_attempts: int = 3,
        tenant_id: str | None = None,
    ) -> str:
        job = Job(
            job_type=job_type,
            payload=payload,
            queue=queue,
            priority=priority,
            scheduled_at=scheduled_at,
            dedup_key=dedup_key,
            max_attempts=max_attempts,
            tenant_id=tenant_id,
        )
        async with self.pool.acquire() as conn:
            return await JobQueueRepo.enqueue(conn, job)

    async def enqueue_delayed(
        self,
        job_type: str,
        payload: dict[str, Any],
        delay_seconds: int,
        **kwargs,
    ) -> str:
        scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        return await self.enqueue(
            job_type, payload, scheduled_at=scheduled_at, **kwargs
        )

    async def process_jobs(
        self,
        queues: list[str] | None = None,
        batch_size: int = JobQueueConfig.BATCH_SIZE,
    ) -> int:
        processed = 0
        async with self.pool.acquire() as conn:
            jobs = await JobQueueRepo.claim(conn, queues=queues, batch_size=batch_size)

            for job in jobs:
                if job.job_type not in self.handlers:
                    logger.error("No handler for job type: %s", job.job_type)
                    await JobQueueRepo.fail(
                        conn, job.id, f"No handler for job type: {job.job_type}"
                    )
                    continue

                handler = self.handlers[job.job_type]
                start_time = datetime.now(timezone.utc)

                try:
                    result = await handler(job.payload)
                    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                    observe(
                        "job_queue.job_duration_seconds",
                        duration,
                        {"job_type": job.job_type},
                    )

                    if result.success:
                        await JobQueueRepo.complete(conn, job.id, result.result)
                        processed += 1
                    else:
                        retry_after = None
                        if job.attempts < job.max_attempts:
                            retry_idx = min(
                                job.attempts - 1,
                                len(JobQueueConfig.DEFAULT_RETRY_DELAYS) - 1,
                            )
                            retry_after = (
                                result.retry_after
                                or JobQueueConfig.DEFAULT_RETRY_DELAYS[retry_idx]
                            )

                        await JobQueueRepo.fail(
                            conn, job.id, result.error or "Job failed", retry_after
                        )

                except Exception as e:
                    logger.exception("Job %s failed with exception", job.id)
                    retry_after = None
                    if job.attempts < job.max_attempts:
                        retry_idx = min(
                            job.attempts - 1,
                            len(JobQueueConfig.DEFAULT_RETRY_DELAYS) - 1,
                        )
                        retry_after = JobQueueConfig.DEFAULT_RETRY_DELAYS[retry_idx]
                    await JobQueueRepo.fail(conn, job.id, str(e)[:500], retry_after)

        return processed

    async def get_stats(self, queue: str | None = None) -> dict[str, int]:
        async with self.pool.acquire() as conn:
            return await JobQueueRepo.get_stats(conn, queue)

    async def cleanup(self, days_old: int = 30) -> int:
        async with self.pool.acquire() as conn:
            return await JobQueueRepo.cleanup_old_jobs(conn, days_old)


async def create_job_queue_tables(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS public.background_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            queue TEXT NOT NULL DEFAULT 'default',
            job_type TEXT NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            status public.job_status NOT NULL DEFAULT 'pending',
            priority public.job_priority NOT NULL DEFAULT 'normal',
            attempts INT NOT NULL DEFAULT 0,
            max_attempts INT NOT NULL DEFAULT 3,
            scheduled_at TIMESTAMPTZ,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            locked_at TIMESTAMPTZ,
            lock_expires_at TIMESTAMPTZ,
            error_message TEXT,
            result JSONB,
            dedup_key TEXT UNIQUE,
            tenant_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            CONSTRAINT valid_status CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled'))
        );

        CREATE INDEX IF NOT EXISTS idx_background_jobs_status_scheduled ON public.background_jobs (status, scheduled_at)
            WHERE status IN ('pending', 'queued');
        CREATE INDEX IF NOT EXISTS idx_background_jobs_queue_priority ON public.background_jobs (queue, priority, created_at);
        CREATE INDEX IF NOT EXISTS idx_background_jobs_dedup ON public.background_jobs (dedup_key)
            WHERE dedup_key IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_background_jobs_locked ON public.background_jobs (locked_at, lock_expires_at);

        CREATE TABLE IF NOT EXISTS public.job_alert_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            alert_id UUID NOT NULL REFERENCES public.job_alerts(id) ON DELETE CASCADE,
            jobs_count INT NOT NULL DEFAULT 0,
            job_ids JSONB NOT NULL DEFAULT '[]',
            sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS public.job_alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            tenant_id UUID,
            name TEXT NOT NULL DEFAULT 'Job Alert',
            keywords JSONB NOT NULL DEFAULT '[]',
            locations JSONB NOT NULL DEFAULT '[]',
            salary_min INT,
            salary_max INT,
            companies_include JSONB NOT NULL DEFAULT '[]',
            companies_exclude JSONB NOT NULL DEFAULT '[]',
            job_types JSONB NOT NULL DEFAULT '[]',
            remote_only BOOLEAN NOT NULL DEFAULT false,
            frequency public.alert_frequency NOT NULL DEFAULT 'daily',
            is_active BOOLEAN NOT NULL DEFAULT true,
            last_sent_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_job_alerts_user ON public.job_alerts (user_id);
        CREATE INDEX IF NOT EXISTS idx_job_alerts_due ON public.job_alerts (frequency, last_sent_at)
            WHERE is_active = true;

        DROP TYPE IF EXISTS public.job_status CASCADE;
        CREATE TYPE public.job_status AS ENUM ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled');

        DROP TYPE IF EXISTS public.job_priority CASCADE;
        CREATE TYPE public.job_priority AS ENUM ('low', 'normal', 'high', 'critical');

        DROP TYPE IF EXISTS public.alert_frequency CASCADE;
        CREATE TYPE public.alert_frequency AS ENUM ('daily', 'weekly', 'immediate');
    """)
    logger.info("Job queue tables created/verified")
