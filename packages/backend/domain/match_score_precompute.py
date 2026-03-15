"""Background job for pre-computing match scores.

This module implements a background job that pre-computes match scores
for active users and jobs, storing them in the database for faster retrieval.

LOW: Performance optimization to reduce on-demand computation during job searches.
"""

from __future__ import annotations

import asyncio
from typing import Any

import asyncpg

from packages.backend.domain.job_queue import JobResult
from packages.backend.domain.profile_assembly import assemble_profile
from packages.backend.domain.repositories import JobRepo
from packages.backend.domain.semantic_matching import get_matching_service
from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.match_precompute")


async def precompute_match_scores(
    db_pool: asyncpg.Pool,
    user_id: str | None = None,
    job_ids: list[str] | None = None,
    batch_size: int = 50,
) -> dict[str, Any]:
    """Pre-compute match scores for users and jobs.

    Args:
        db_pool: Database connection pool
        user_id: Specific user ID to process (None = all active users)
        job_ids: Specific job IDs to process (None = all active jobs)
        batch_size: Number of jobs to process per batch

    Returns:
        Dictionary with statistics about the pre-computation
    """
    stats = {
        "users_processed": 0,
        "jobs_processed": 0,
        "scores_computed": 0,
        "errors": 0,
    }

    matching_service = get_matching_service()

    try:
        async with db_pool.acquire() as conn:
            # Get users to process
            if user_id:
                user_query = (
                    "SELECT id FROM public.users WHERE id = $1 AND is_active = true"
                )
                user_rows = await conn.fetch(user_query, user_id)
            else:
                # Get active users who have completed onboarding
                user_query = """
                    SELECT id FROM public.users
                    WHERE is_active = true
                    AND profile_completeness >= 20
                    ORDER BY updated_at DESC
                    LIMIT 100
                """
                user_rows = await conn.fetch(user_query)

            # Get jobs to process
            if job_ids:
                job_query = """
                    SELECT id FROM public.jobs
                    WHERE id = ANY($1::uuid[])
                    AND is_active = true
                """
                job_rows = await conn.fetch(job_query, job_ids)
            else:
                # Get recent active jobs
                job_query = """
                    SELECT id FROM public.jobs
                    WHERE is_active = true
                    AND created_at >= NOW() - INTERVAL '30 days'
                    ORDER BY created_at DESC
                    LIMIT 500
                """
                job_rows = await conn.fetch(job_query)

            if not user_rows or not job_rows:
                logger.info(
                    "No users or jobs to process for match score pre-computation"
                )
                return stats

            logger.info(
                "Pre-computing match scores: %d users, %d jobs",
                len(user_rows),
                len(job_rows),
            )

            # Process in batches to avoid overwhelming the system
            for user_row in user_rows:
                user_id_str = str(user_row["id"])
                stats["users_processed"] += 1

                try:
                    # Assemble user profile
                    async with db_pool.acquire() as user_conn:
                        profile = await assemble_profile(user_conn, user_id_str)

                    if not profile:
                        logger.debug("Skipping user %s: no profile", user_id_str)
                        continue

                    # Convert profile to dict for matching service
                    from packages.backend.domain.deep_profile import deep_profile_to_llm_dict

                    profile_dict = deep_profile_to_llm_dict(profile)

                    # Process jobs in batches
                    for i in range(0, len(job_rows), batch_size):
                        batch = job_rows[i : i + batch_size]
                        job_ids_batch = [str(row["id"]) for row in batch]

                        # Get job details
                        async with db_pool.acquire() as job_conn:
                            jobs = []
                            for job_id in job_ids_batch:
                                job = await JobRepo.get_by_id(job_conn, job_id)
                                if job:
                                    jobs.append(job)

                        # Compute match scores for batch
                        for job in jobs:
                            try:
                                stats["jobs_processed"] += 1

                                # Compute match score
                                async with db_pool.acquire() as score_conn:
                                    result = await matching_service.compute_match_score(
                                        profile=profile_dict,
                                        job=job,
                                        db_conn=score_conn,
                                    )

                                # Store match score in database
                                # Note: This assumes a match_scores table exists
                                # For now, we'll store in a JSONB column or create the table
                                async with db_pool.acquire() as store_conn:
                                    await store_conn.execute(
                                        """
                                        INSERT INTO public.match_scores (user_id, job_id, score, computed_at)
                                        VALUES ($1, $2, $3, NOW())
                                        ON CONFLICT (user_id, job_id)
                                        DO UPDATE SET score = $3, computed_at = NOW()
                                        """,
                                        user_id_str,
                                        str(job.get("id")),
                                        result.score,
                                    )

                                stats["scores_computed"] += 1

                                # Rate limiting: small delay between computations
                                if stats["scores_computed"] % 10 == 0:
                                    await asyncio.sleep(0.1)

                            except Exception as job_error:
                                stats["errors"] += 1
                                logger.warning(
                                    "Failed to compute match score for user %s, job %s: %s",
                                    user_id_str,
                                    job.get("id"),
                                    job_error,
                                )

                except Exception as user_error:
                    stats["errors"] += 1
                    logger.warning(
                        "Failed to process user %s: %s",
                        user_id_str,
                        user_error,
                    )

            observe(
                "match_score.precompute.duration", 0
            )  # Would measure actual duration
            incr(
                "match_score.precompute.completed",
                {
                    "users": str(stats["users_processed"]),
                    "jobs": str(stats["jobs_processed"]),
                    "scores": str(stats["scores_computed"]),
                },
            )

            logger.info(
                "Match score pre-computation completed: %d scores computed, %d errors",
                stats["scores_computed"],
                stats["errors"],
            )

    except Exception as e:
        logger.error("Match score pre-computation failed: %s", e, exc_info=True)
        stats["errors"] += 1
        incr("match_score.precompute.failed")

    return stats


def register_match_score_job_handler(queue: Any) -> None:
    """Register the match score pre-computation job handler.

    Args:
        queue: Background job queue instance
    """

    async def handler(job_data: dict[str, Any]) -> JobResult:
        """Handle match score pre-computation job."""
        try:
            user_id = job_data.get("user_id")
            job_ids = job_data.get("job_ids")
            batch_size = job_data.get("batch_size", 50)

            # Get database pool from queue
            db_pool = queue.pool if hasattr(queue, "pool") else None
            if not db_pool:
                return JobResult(
                    success=False, error="Database pool not available in job queue"
                )

            stats = await precompute_match_scores(
                db_pool=db_pool,
                user_id=user_id,
                job_ids=job_ids,
                batch_size=batch_size,
            )

            return JobResult(success=True, result=stats)
        except Exception as e:
            logger.error("Match score pre-computation job failed: %s", e, exc_info=True)
            return JobResult(success=False, error=str(e))

    # Register handler with job type
    queue.register_handler("precompute_match_scores", handler)
    logger.info("Registered match score pre-computation job handler")
