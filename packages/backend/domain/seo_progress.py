"""SEO Engine Progress Repository - Tracks service progress and quotas.

Provides methods for managing SEO engine progress including quota tracking,
index management, and daily quota resets.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.seo_progress")


class SEOProgressRepository:
    """Repository for managing SEO engine progress and quotas."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        """Initialize the repository with a database connection.

        Args:
            conn: AsyncPG database connection.
        """
        self._conn = conn

    async def get_progress(self, service_id: str) -> Optional[dict[str, Any]]:
        """Get progress for a specific service.

        Args:
            service_id: The service identifier.

        Returns:
            Dictionary containing progress data or None if not found.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT
                    id,
                    service_id,
                    last_index,
                    last_submission_at,
                    daily_quota_used,
                    daily_quota_reset,
                    created_at,
                    updated_at
                FROM seo_engine_progress
                WHERE service_id = $1
                """,
                service_id,
            )

            if not row:
                return None

            return {
                "id": row["id"],
                "service_id": row["service_id"],
                "last_index": row["last_index"],
                "last_submission_at": (
                    row["last_submission_at"].isoformat()
                    if row["last_submission_at"]
                    else None
                ),
                "daily_quota_used": row["daily_quota_used"],
                "daily_quota_reset": (
                    row["daily_quota_reset"].isoformat()
                    if row["daily_quota_reset"]
                    else None
                ),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to get SEO progress",
                extra={"service_id": service_id, "error": str(e)},
            )
            raise

    async def update_progress(
        self,
        service_id: str,
        last_index: Optional[int] = None,
        daily_quota_used: Optional[int] = None,
    ) -> dict[str, Any]:
        """Update progress for a specific service.

        Args:
            service_id: The service identifier.
            last_index: New last index value.
            daily_quota_used: New daily quota used value.

        Returns:
            Updated progress data.
        """
        try:
            # Build dynamic update query
            updates = ["updated_at = NOW()"]
            params: list[Any] = [service_id]
            param_index = 2

            if last_index is not None:
                updates.append(f"last_index = ${param_index}")
                params.append(last_index)
                param_index += 1

            if daily_quota_used is not None:
                updates.append(f"daily_quota_used = ${param_index}")
                params.append(daily_quota_used)
                param_index += 1

            # Add last_submission_at update when last_index changes
            if last_index is not None:
                updates.append("last_submission_at = NOW()")

            query = f"""
                UPDATE seo_engine_progress
                SET {', '.join(updates)}
                WHERE service_id = $1
                RETURNING id, service_id, last_index, last_submission_at,
                          daily_quota_used, daily_quota_reset, created_at, updated_at
            """

            row = await self._conn.fetchrow(query, *params)

            if not row:
                # Create new record if it doesn't exist
                return await self._create_progress(service_id)

            return {
                "id": row["id"],
                "service_id": row["service_id"],
                "last_index": row["last_index"],
                "last_submission_at": (
                    row["last_submission_at"].isoformat()
                    if row["last_submission_at"]
                    else None
                ),
                "daily_quota_used": row["daily_quota_used"],
                "daily_quota_reset": (
                    row["daily_quota_reset"].isoformat()
                    if row["daily_quota_reset"]
                    else None
                ),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to update SEO progress",
                extra={
                    "service_id": service_id,
                    "last_index": last_index,
                    "daily_quota_used": daily_quota_used,
                    "error": str(e),
                },
            )
            raise

    async def reset_daily_quota(self, service_id: str) -> dict[str, Any]:
        """Reset daily quota for a specific service.

        This method resets the daily quota and sets the next reset time
        to midnight UTC.

        Args:
            service_id: The service identifier.

        Returns:
            Updated progress data with reset quota.
        """
        try:
            # Calculate next reset at midnight UTC
            now = datetime.now(timezone.utc)
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
            next_reset = tomorrow.replace(day=now.day + 1) if now.hour >= 0 else tomorrow

            row = await self._conn.fetchrow(
                """
                UPDATE seo_engine_progress
                SET daily_quota_used = 0,
                    daily_quota_reset = $2,
                    updated_at = NOW()
                WHERE service_id = $1
                RETURNING id, service_id, last_index, last_submission_at,
                          daily_quota_used, daily_quota_reset, created_at, updated_at
                """,
                service_id,
                next_reset,
            )

            if not row:
                # Create new record if it doesn't exist
                return await self._create_progress(service_id)

            logger.info(
                "Daily quota reset",
                extra={"service_id": service_id, "next_reset": next_reset.isoformat()},
            )

            return {
                "id": row["id"],
                "service_id": row["service_id"],
                "last_index": row["last_index"],
                "last_submission_at": (
                    row["last_submission_at"].isoformat()
                    if row["last_submission_at"]
                    else None
                ),
                "daily_quota_used": row["daily_quota_used"],
                "daily_quota_reset": (
                    row["daily_quota_reset"].isoformat()
                    if row["daily_quota_reset"]
                    else None
                ),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to reset daily quota",
                extra={"service_id": service_id, "error": str(e)},
            )
            raise

    async def increment_quota(self, service_id: str, amount: int = 1) -> dict[str, Any]:
        """Increment the daily quota used for a service.

        Also checks if quota needs to be reset based on the reset time.

        Args:
            service_id: The service identifier.
            amount: Amount to increment by (default 1).

        Returns:
            Updated progress data.
        """
        try:
            now = datetime.now(timezone.utc)

            # First get current state to check if reset is needed
            current = await self.get_progress(service_id)

            if current:
                # Check if we need to reset (past reset time)
                reset_time = current.get("daily_quota_reset")
                if reset_time:
                    reset_dt = datetime.fromisoformat(reset_time.replace("Z", "+00:00"))
                    if now >= reset_dt:
                        await self.reset_daily_quota(service_id)
                        current = await self.get_progress(service_id)

            # Increment quota
            row = await self._conn.fetchrow(
                """
                UPDATE seo_engine_progress
                SET daily_quota_used = daily_quota_used + $2,
                    updated_at = NOW()
                WHERE service_id = $1
                RETURNING id, service_id, last_index, last_submission_at,
                          daily_quota_used, daily_quota_reset, created_at, updated_at
                """,
                service_id,
                amount,
            )

            if not row:
                # Create new record if it doesn't exist
                return await self._create_progress(service_id)

            return {
                "id": row["id"],
                "service_id": row["service_id"],
                "last_index": row["last_index"],
                "last_submission_at": (
                    row["last_submission_at"].isoformat()
                    if row["last_submission_at"]
                    else None
                ),
                "daily_quota_used": row["daily_quota_used"],
                "daily_quota_reset": (
                    row["daily_quota_reset"].isoformat()
                    if row["daily_quota_reset"]
                    else None
                ),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to increment quota",
                extra={"service_id": service_id, "amount": amount, "error": str(e)},
            )
            raise

    async def _create_progress(self, service_id: str) -> dict[str, Any]:
        """Create a new progress record for a service.

        Args:
            service_id: The service identifier.

        Returns:
            Created progress data.
        """
        try:
            now = datetime.now(timezone.utc)
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
            next_reset = tomorrow.replace(day=now.day + 1)

            row = await self._conn.fetchrow(
                """
                INSERT INTO seo_engine_progress (service_id, last_index, daily_quota_used, daily_quota_reset)
                VALUES ($1, 0, 0, $2)
                RETURNING id, service_id, last_index, last_submission_at,
                          daily_quota_used, daily_quota_reset, created_at, updated_at
                """,
                service_id,
                next_reset,
            )

            logger.info(
                "Created SEO progress record",
                extra={"service_id": service_id},
            )

            return {
                "id": row["id"],
                "service_id": row["service_id"],
                "last_index": row["last_index"],
                "last_submission_at": (
                    row["last_submission_at"].isoformat()
                    if row["last_submission_at"]
                    else None
                ),
                "daily_quota_used": row["daily_quota_used"],
                "daily_quota_reset": (
                    row["daily_quota_reset"].isoformat()
                    if row["daily_quota_reset"]
                    else None
                ),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
        except Exception as e:
            logger.error(
                "Failed to create SEO progress",
                extra={"service_id": service_id, "error": str(e)},
            )
            raise
