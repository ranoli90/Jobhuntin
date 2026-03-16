"""SEO Metrics Collector - Performance tracking for SEO operations.

Provides methods for recording and retrieving SEO metrics including
generation times, submission success rates, and API usage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.seo_metrics")


class SEOMetricsCollector:
    """Collector for SEO performance metrics."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        """Initialize the collector with a database connection.

        Args:
            conn: AsyncPG database connection.
        """
        self._conn = conn

    async def record_generation(
        self,
        generation_time_ms: int,
        success: bool = True,
        topic: Optional[str] = None,
    ) -> dict[str, Any]:
        """Record a content generation event.

        Args:
            generation_time_ms: Time taken to generate content in milliseconds.
            success: Whether the generation was successful.
            topic: Optional topic that was generated.

        Returns:
            Recorded metrics data.
        """
        try:
            # Get today's metrics or create new entry
            today = datetime.now(timezone.utc).date()

            row = await self._conn.fetchrow(
                """
                INSERT INTO seo_metrics (total_generated, metrics)
                VALUES (1, $1)
                ON CONFLICT (id) DO UPDATE
                SET total_generated = seo_metrics.total_generated + 1,
                    metrics = COALESCE(seo_metrics.metrics, '{}'::jsonb) || $1,
                    created_at = CASE
                        WHEN DATE(seo_metrics.created_at) = $2
                        THEN seo_metrics.created_at
                        ELSE NOW()
                    END
                RETURNING id, total_generated, total_submitted, success_rate,
                          average_generation_time_ms, average_submission_time_ms,
                          api_calls_today, quota_used_today, metrics, created_at
                """,
                {
                    "last_generation_time_ms": generation_time_ms,
                    "last_generation_success": success,
                    "last_generation_topic": topic,
                    "last_generation_at": datetime.now(timezone.utc).isoformat(),
                },
                today,
            )

            logger.info(
                "Recorded SEO generation metrics",
                extra={
                    "generation_time_ms": generation_time_ms,
                    "success": success,
                },
            )

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to record generation metrics",
                extra={"generation_time_ms": generation_time_ms, "error": str(e)},
            )
            raise

    async def record_submission(
        self,
        service_id: str,
        urls_submitted: int,
        urls_successful: int,
        success: bool,
        batch_url_file: Optional[str] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        submission_time_ms: Optional[int] = None,
    ) -> dict[str, Any]:
        """Record a Google URL submission event.

        Args:
            service_id: The service identifier.
            urls_submitted: Number of URLs submitted.
            urls_successful: Number of successfully submitted URLs.
            success: Whether the submission was successful.
            batch_url_file: Optional batch file used.
            error_message: Optional error message if failed.
            error_code: Optional error code.
            submission_time_ms: Optional time taken for submission.

        Returns:
            Recorded submission log data.
        """
        try:
            # Record submission log
            log_row = await self._conn.fetchrow(
                """
                INSERT INTO seo_submission_log (
                    service_id, batch_url_file, urls_submitted,
                    urls_successful, success, error_message, error_code
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, service_id, batch_url_file, urls_submitted,
                          urls_successful, success, error_message,
                          error_code, retry_count, created_at
                """,
                service_id,
                batch_url_file,
                urls_submitted,
                urls_successful,
                success,
                error_message,
                error_code,
            )

            # Update aggregate metrics
            today = datetime.now(timezone.utc).date()
            success_rate = (
                (urls_successful / urls_submitted * 100) if urls_submitted > 0 else 0
            )

            await self._conn.execute(
                """
                INSERT INTO seo_metrics (total_submitted, success_rate, metrics)
                VALUES ($1, $2, $3)
                ON CONFLICT (id) DO UPDATE
                SET total_submitted = seo_metrics.total_submitted + $1,
                    success_rate = (
                        (seo_metrics.total_submitted * COALESCE(seo_metrics.success_rate, 0) + $2 * $1)
                        / (seo_metrics.total_submitted + $1)
                    ),
                    metrics = COALESCE(seo_metrics.metrics, '{}'::jsonb) || $3,
                    created_at = CASE
                        WHEN DATE(seo_metrics.created_at) = $4
                        THEN seo_metrics.created_at
                        ELSE NOW()
                    END
                """,
                urls_submitted,
                success_rate,
                {
                    "last_submission_at": datetime.now(timezone.utc).isoformat(),
                    "last_submission_success": success,
                    "last_submission_service_id": service_id,
                    "last_submission_time_ms": submission_time_ms,
                },
                today,
            )

            logger.info(
                "Recorded SEO submission",
                extra={
                    "service_id": service_id,
                    "urls_submitted": urls_submitted,
                    "urls_successful": urls_successful,
                    "success": success,
                },
            )

            return {
                "id": log_row["id"],
                "service_id": log_row["service_id"],
                "batch_url_file": log_row["batch_url_file"],
                "urls_submitted": log_row["urls_submitted"],
                "urls_successful": log_row["urls_successful"],
                "success": log_row["success"],
                "error_message": log_row["error_message"],
                "error_code": log_row["error_code"],
                "retry_count": log_row["retry_count"],
                "created_at": log_row["created_at"].isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to record submission metrics",
                extra={"service_id": service_id, "error": str(e)},
            )
            raise

    async def save_metrics(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Save custom metrics data.

        Args:
            metrics: Dictionary of metrics to save.

        Returns:
            Saved metrics data.
        """
        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO seo_metrics (metrics)
                VALUES ($1)
                RETURNING id, total_generated, total_submitted, success_rate,
                          average_generation_time_ms, average_submission_time_ms,
                          api_calls_today, quota_used_today, metrics, created_at
                """,
                metrics,
            )

            logger.info("Saved SEO metrics", extra={"metrics": metrics})

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to save metrics",
                extra={"error": str(e)},
            )
            raise

    async def get_metrics(
        self, days: int = 30
    ) -> list[dict[str, Any]]:
        """Get metrics for the last N days.

        Args:
            days: Number of days to retrieve.

        Returns:
            List of metrics by day.
        """
        try:
            rows = await self._conn.fetch(
                """
                SELECT id, total_generated, total_submitted, success_rate,
                       average_generation_time_ms, average_submission_time_ms,
                       api_calls_today, quota_used_today, metrics, created_at
                FROM seo_metrics
                WHERE created_at >= NOW() - INTERVAL '1 day' * $1
                ORDER BY created_at DESC
                """,
                days,
            )

            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(
                "Failed to get metrics",
                extra={"days": days, "error": str(e)},
            )
            raise

    async def get_latest_metrics() -> Optional[dict[str, Any]]:
        """Get the most recent metrics entry.

        Returns:
            Latest metrics data or None if not found.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT id, total_generated, total_submitted, success_rate,
                       average_generation_time_ms, average_submission_time_ms,
                       api_calls_today, quota_used_today, metrics, created_at
                FROM seo_metrics
                ORDER BY created_at DESC
                LIMIT 1
                """
            )

            if not row:
                return None

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to get latest metrics",
                extra={"error": str(e)},
            )
            raise

    async def get_submission_logs(
        self,
        service_id: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get submission logs with optional filters.

        Args:
            service_id: Optional service ID filter.
            success: Optional success filter.
            limit: Maximum number of results.

        Returns:
            List of submission logs.
        """
        try:
            query = """
                SELECT id, service_id, batch_url_file, urls_submitted,
                       urls_successful, success, error_message, error_code,
                       retry_count, created_at
                FROM seo_submission_log
                WHERE 1=1
            """
            params: list[Any] = []
            param_index = 1

            if service_id:
                query += f" AND service_id = ${param_index}"
                params.append(service_id)
                param_index += 1

            if success is not None:
                query += f" AND success = ${param_index}"
                params.append(success)
                param_index += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_index}"
            params.append(limit)

            rows = await self._conn.fetch(query, *params)

            return [
                {
                    "id": row["id"],
                    "service_id": row["service_id"],
                    "batch_url_file": row["batch_url_file"],
                    "urls_submitted": row["urls_submitted"],
                    "urls_successful": row["urls_successful"],
                    "success": row["success"],
                    "error_message": row["error_message"],
                    "error_code": row["error_code"],
                    "retry_count": row["retry_count"],
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(
                "Failed to get submission logs",
                extra={
                    "service_id": service_id,
                    "success": success,
                    "error": str(e),
                },
            )
            raise

    async def get_success_rate(self, days: int = 30) -> float:
        """Get overall submission success rate for the last N days.

        Args:
            days: Number of days to calculate from.

        Returns:
            Success rate as a percentage (0-100).
        """
        try:
            # This uses a subquery to calculate weighted average
            row = await self._conn.fetchrow(
                """
                SELECT
                    COALESCE(
                        SUM(urls_successful)::float / NULLIF(SUM(urls_submitted), 0) * 100,
                        0
                    ) AS success_rate
                FROM seo_submission_log
                WHERE created_at >= NOW() - INTERVAL '1 day' * $1
                """,
                days,
            )

            return float(row["success_rate"]) if row["success_rate"] else 0.0
        except Exception as e:
            logger.error(
                "Failed to get success rate",
                extra={"days": days, "error": str(e)},
            )
            raise

    async def get_average_generation_time(self, days: int = 30) -> Optional[float]:
        """Get average generation time for the last N days.

        Args:
            days: Number of days to calculate from.

        Returns:
            Average generation time in milliseconds, or None if no data.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT AVG(
                    (metrics->>'last_generation_time_ms')::integer
                )::float AS avg_time
                FROM seo_metrics
                WHERE created_at >= NOW() - INTERVAL '1 day' * $1
                  AND metrics ? 'last_generation_time_ms'
                """,
                days,
            )

            return float(row["avg_time"]) if row["avg_time"] else None
        except Exception as e:
            logger.error(
                "Failed to get average generation time",
                extra={"days": days, "error": str(e)},
            )
            raise

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> dict[str, Any]:
        """Convert a database row to a dictionary.

        Args:
            row: The database record.

        Returns:
            Dictionary representation of the row.
        """
        return {
            "id": row["id"],
            "total_generated": row["total_generated"],
            "total_submitted": row["total_submitted"],
            "success_rate": float(row["success_rate"]) if row["success_rate"] else None,
            "average_generation_time_ms": row["average_generation_time_ms"],
            "average_submission_time_ms": row["average_submission_time_ms"],
            "api_calls_today": row["api_calls_today"],
            "quota_used_today": row["quota_used_today"],
            "metrics": dict(row["metrics"]) if row["metrics"] else {},
            "created_at": row["created_at"].isoformat(),
        }
