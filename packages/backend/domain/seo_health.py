"""SEO Health Check Module - Health monitoring for SEO engine.

Provides comprehensive health checks for the SEO engine including database
connectivity, table existence, quota status, and error monitoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.seo_health")

# Default daily quota limit (can be overridden per service)
DEFAULT_DAILY_QUOTA = 1000


@dataclass
class SEOHealthStatus:
    """Health status result for SEO engine."""

    healthy: bool
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    overall_status: str = "healthy"  # healthy, degraded, unhealthy
    recommendations: list[str] = field(default_factory=list)


class SEOHealthCheck:
    """Health check utility for SEO engine components."""

    # Table names to check
    PROGRESS_TABLE = "seo_engine_progress"
    CONTENT_TABLE = "seo_generated_content"
    METRICS_TABLE = "seo_metrics"
    LOGS_TABLE = "seo_logs"

    def __init__(self, conn: asyncpg.Connection) -> None:
        """Initialize health check with a database connection.

        Args:
            conn: AsyncPG database connection.
        """
        self._conn = conn
        self._default_quota = DEFAULT_DAILY_QUOTA

    async def check_database_connection(self) -> dict[str, Any]:
        """Verify database is accessible.

        Returns:
            Dictionary with check status, message, and timestamp.
        """
        try:
            # Simple query to test connection
            result = await self._conn.fetchval("SELECT 1")
            if result == 1:
                return {
                    "status": "healthy",
                    "message": "Database connection is active",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Database returned unexpected result",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except asyncpg.InvalidCatalogNameError as e:
            logger.error("Database catalog not found", extra={"error": str(e)})
            return {
                "status": "unhealthy",
                "message": f"Database not found: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except asyncpg.InvalidPasswordError as e:
            logger.error("Database authentication failed", extra={"error": str(e)})
            return {
                "status": "unhealthy",
                "message": "Database authentication failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except ConnectionError as e:
            logger.error("Database connection failed", extra={"error": str(e)})
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(
                "Database connection check failed",
                extra={"error": str(e)},
            )
            return {
                "status": "unhealthy",
                "message": f"Database connection error: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def check_progress_table(self) -> dict[str, Any]:
        """Verify seo_engine_progress table exists and is accessible.

        Returns:
            Dictionary with check status, message, and timestamp.
        """
        return await self._check_table_exists(
            self.PROGRESS_TABLE,
            "service_id, last_index, daily_quota_used, daily_quota_reset",
        )

    async def check_content_table(self) -> dict[str, Any]:
        """Verify seo_generated_content table exists and is accessible.

        Returns:
            Dictionary with check status, message, and timestamp.
        """
        return await self._check_table_exists(
            self.CONTENT_TABLE,
            "url, content_hash, topic, intent, created_at",
        )

    async def check_metrics_table(self) -> dict[str, Any]:
        """Verify seo_metrics table exists and is accessible.

        Returns:
            Dictionary with check status, message, and timestamp.
        """
        return await self._check_table_exists(
            self.METRICS_TABLE,
            "total_generated, total_submitted, success_rate",
        )

    async def _check_table_exists(
        self, table_name: str, columns_to_check: str
    ) -> dict[str, Any]:
        """Check if a table exists and has expected columns.

        Args:
            table_name: Name of the table to check.
            columns_to_check: Comma-separated list of columns to verify.

        Returns:
            Dictionary with check status, message, and timestamp.
        """
        try:
            # Check if table exists by querying it
            columns_list = [col.strip() for col in columns_to_check.split(",")]
            query_columns = ", ".join(columns_list[:2])  # Just check first 2 columns

            await self._conn.fetchval(
                f"SELECT {query_columns} FROM {table_name} LIMIT 1"
            )

            return {
                "status": "healthy",
                "message": f"Table '{table_name}' exists and is accessible",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except asyncpg.UndefinedTableError as e:
            logger.warning(
                "SEO table does not exist",
                extra={"table": table_name, "error": str(e)},
            )
            return {
                "status": "unhealthy",
                "message": f"Table '{table_name}' does not exist",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except asyncpg.UndefinedColumnError as e:
            logger.warning(
                "SEO table missing columns",
                extra={"table": table_name, "error": str(e)},
            )
            return {
                "status": "degraded",
                "message": f"Table '{table_name}' is missing expected columns: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to check SEO table",
                extra={"table": table_name, "error": str(e)},
            )
            return {
                "status": "unhealthy",
                "message": f"Error checking table '{table_name}': {e}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def check_quota_status(self, service_id: str) -> dict[str, Any]:
        """Check daily quota remaining for a service.

        Args:
            service_id: The service identifier to check quota for.

        Returns:
            Dictionary with check status, quota info, message, and timestamp.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT
                    service_id,
                    daily_quota_used,
                    daily_quota_reset,
                    updated_at
                FROM seo_engine_progress
                WHERE service_id = $1
                """,
                service_id,
            )

            if not row:
                return {
                    "status": "healthy",
                    "message": f"No progress record found for service '{service_id}' - no quota consumed",
                    "quota_used": 0,
                    "quota_remaining": self._default_quota,
                    "quota_limit": self._default_quota,
                    "quota_reset_at": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            quota_used = row["daily_quota_used"] or 0
            quota_limit = self._default_quota
            quota_remaining = max(0, quota_limit - quota_used)

            # Check if quota is running low (less than 10% remaining)
            if quota_remaining == 0:
                status = "unhealthy"
                message = f"Daily quota exhausted for service '{service_id}'"
            elif quota_remaining < quota_limit * 0.1:
                status = "degraded"
                message = (
                    f"Daily quota running low for service '{service_id}': "
                    f"{quota_remaining}/{quota_limit} remaining"
                )
            else:
                status = "healthy"
                message = (
                    f"Quota available for service '{service_id}': "
                    f"{quota_remaining}/{quota_limit} remaining"
                )

            reset_at = row["daily_quota_reset"]
            if reset_at:
                reset_at = reset_at.isoformat()

            return {
                "status": status,
                "message": message,
                "quota_used": quota_used,
                "quota_remaining": quota_remaining,
                "quota_limit": quota_limit,
                "quota_reset_at": reset_at,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to check quota status",
                extra={"service_id": service_id, "error": str(e)},
            )
            return {
                "status": "unhealthy",
                "message": f"Error checking quota: {e}",
                "quota_used": None,
                "quota_remaining": None,
                "quota_limit": self._default_quota,
                "quota_reset_at": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def check_recent_errors(self, hours: int = 24) -> dict[str, Any]:
        """Check for recent errors in SEO logs.

        Args:
            hours: Number of hours to look back for errors. Default is 24.

        Returns:
            Dictionary with check status, error count, messages, and timestamp.
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            rows = await self._conn.fetch(
                """
                SELECT id, level, message, meta, created_at
                FROM seo_logs
                WHERE level = 'error'
                  AND created_at >= $1
                ORDER BY created_at DESC
                LIMIT 100
                """,
                cutoff_time,
            )

            error_count = len(rows)
            error_messages = []

            if rows:
                for row in rows[:10]:  # Include up to 10 error messages
                    error_messages.append({
                        "id": str(row["id"]),
                        "message": row["message"],
                        "meta": dict(row["meta"]) if row["meta"] else None,
                        "created_at": row["created_at"].isoformat(),
                    })

            if error_count == 0:
                status = "healthy"
                message = f"No errors in the last {hours} hours"
            elif error_count <= 5:
                status = "healthy"
                message = f"Found {error_count} error(s) in the last {hours} hours"
            elif error_count <= 20:
                status = "degraded"
                message = f"Found {error_count} error(s) in the last {hours} hours - investigate"
            else:
                status = "unhealthy"
                message = f"Found {error_count} error(s) in the last {hours} hours - immediate attention required"

            # Check if there are recent errors (last hour)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
            recent_errors = await self._conn.fetch(
                """
                SELECT COUNT(*) as count
                FROM seo_logs
                WHERE level = 'error'
                  AND created_at >= $1
                """,
                recent_cutoff,
            )
            recent_error_count = recent_errors[0]["count"] if recent_errors else 0

            return {
                "status": status,
                "message": message,
                "error_count": error_count,
                "recent_error_count": recent_error_count,
                "errors": error_messages,
                "hours_checked": hours,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except asyncpg.UndefinedTableError:
            # Logs table doesn't exist - this is OK for health checks
            logger.warning("SEO logs table does not exist - skipping error check")
            return {
                "status": "healthy",
                "message": "SEO logs table does not exist - cannot check for errors",
                "error_count": 0,
                "recent_error_count": 0,
                "errors": [],
                "hours_checked": hours,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to check recent errors",
                extra={"hours": hours, "error": str(e)},
            )
            return {
                "status": "unhealthy",
                "message": f"Error checking logs: {e}",
                "error_count": None,
                "recent_error_count": None,
                "errors": [],
                "hours_checked": hours,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def run_all_checks(
        self, service_id: Optional[str] = None
    ) -> SEOHealthStatus:
        """Run all health checks and return summary.

        Args:
            service_id: Optional service ID for quota check. If not provided,
                       quota check will be skipped.

        Returns:
            SEOHealthStatus with overall health information.
        """
        checks: dict[str, dict[str, Any]] = {}
        recommendations: list[str] = []

        # Run database connection check
        checks["database_connection"] = await self.check_database_connection()

        # Only run table checks if database is accessible
        if checks["database_connection"]["status"] == "healthy":
            checks["progress_table"] = await self.check_progress_table()
            checks["content_table"] = await self.check_content_table()
            checks["metrics_table"] = await self.check_metrics_table()

            # Run quota check if service_id provided
            if service_id:
                checks["quota_status"] = await self.check_quota_status(service_id)
        else:
            # Database is down - mark all dependent checks as skipped
            checks["progress_table"] = {
                "status": "skipped",
                "message": "Skipped due to database connection failure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            checks["content_table"] = {
                "status": "skipped",
                "message": "Skipped due to database connection failure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            checks["metrics_table"] = {
                "status": "skipped",
                "message": "Skipped due to database connection failure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if service_id:
                checks["quota_status"] = {
                    "status": "skipped",
                    "message": "Skipped due to database connection failure",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        # Always check errors (gracefully handles missing logs table)
        checks["recent_errors"] = await self.check_recent_errors()

        # Determine overall status
        overall_status = "healthy"
        unhealthy_count = 0
        degraded_count = 0
        skipped_count = 0

        for check_name, result in checks.items():
            status = result.get("status", "unknown")
            if status == "unhealthy":
                unhealthy_count += 1
            elif status == "degraded":
                degraded_count += 1
            elif status == "skipped":
                skipped_count += 1

        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"

        # Generate recommendations
        if overall_status == "unhealthy":
            if checks.get("database_connection", {}).get("status") == "unhealthy":
                recommendations.append(
                    "Database connection is down - check database server and network connectivity"
                )
            if checks.get("progress_table", {}).get("status") == "unhealthy":
                recommendations.append(
                    "seo_engine_progress table is missing - run database migrations"
                )
            if checks.get("content_table", {}).get("status") == "unhealthy":
                recommendations.append(
                    "seo_generated_content table is missing - run database migrations"
                )
            if checks.get("metrics_table", {}).get("status") == "unhealthy":
                recommendations.append(
                    "seo_metrics table is missing - run database migrations"
                )
            if checks.get("quota_status", {}).get("status") == "unhealthy":
                quota_result = checks["quota_status"]
                recommendations.append(
                    f"Daily quota exhausted - "
                    f"reset at {quota_result.get('quota_reset_at', 'unknown')}"
                )
            if checks.get("recent_errors", {}).get("status") == "unhealthy":
                error_count = checks["recent_errors"].get("error_count", 0)
                recommendations.append(
                    f"High number of recent errors ({error_count}) - investigate immediately"
                )
        elif overall_status == "degraded":
            if checks.get("quota_status", {}).get("status") == "degraded":
                recommendations.append(
                    "Daily quota is running low - plan for quota reset or service expansion"
                )
            if checks.get("recent_errors", {}).get("status") == "degraded":
                error_count = checks["recent_errors"].get("error_count", 0)
                recommendations.append(
                    f"Moderate number of errors ({error_count}) - monitor and investigate"
                )
            if checks.get("progress_table", {}).get("status") == "degraded":
                recommendations.append(
                    "seo_engine_progress table has schema issues - review table columns"
                )
            if checks.get("content_table", {}).get("status") == "degraded":
                recommendations.append(
                    "seo_generated_content table has schema issues - review table columns"
                )
            if checks.get("metrics_table", {}).get("status") == "degraded":
                recommendations.append(
                    "seo_metrics table has schema issues - review table columns"
                )

        # Determine overall healthy status
        healthy = overall_status == "healthy"

        return SEOHealthStatus(
            healthy=healthy,
            checks=checks,
            overall_status=overall_status,
            recommendations=recommendations,
        )
