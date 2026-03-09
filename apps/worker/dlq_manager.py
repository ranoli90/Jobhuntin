"""DLQ (Dead Letter Queue) inspection and management for admin dashboard.

This module provides functionality for inspecting, managing, and retrying
failed applications from the dead letter queue.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.dlq_manager")


@dataclass
class DLQItem:
    """Represents an item in the dead letter queue."""

    id: str
    application_id: str
    tenant_id: Optional[str]
    failure_reason: str
    attempt_count: int
    last_error: str
    payload: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "DLQItem":
        """Create DLQItem from database row."""
        return cls(
            id=str(row["id"]),
            application_id=str(row["application_id"]),
            tenant_id=str(row["tenant_id"]) if row["tenant_id"] else None,
            failure_reason=row["failure_reason"],
            attempt_count=row["attempt_count"],
            last_error=row["last_error"],
            payload=json.loads(row["payload"])
            if isinstance(row["payload"], str)
            else row["payload"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class RetryResult:
    """Result of a retry operation."""

    success: bool
    message: str
    application_id: str
    new_status: Optional[str] = None
    error: Optional[str] = None


class DLQManager:
    """Manages the dead letter queue for failed applications."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_dlq_items(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        failure_reason: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[DLQItem]:
        """Get items from the dead letter queue with filtering."""
        try:
            query = """
                SELECT * FROM public.job_dead_letter_queue
                WHERE 1=1
            """
            params = []
            param_count = 0

            if tenant_id:
                param_count += 1
                query += f" AND tenant_id = ${param_count}"
                params.append(tenant_id)

            if failure_reason:
                param_count += 1
                query += f" AND failure_reason = ${param_count}"
                params.append(failure_reason)

            if date_from:
                param_count += 1
                query += f" AND created_at >= ${param_count}"
                params.append(date_from)

            if date_to:
                param_count += 1
                query += f" AND created_at <= ${param_count}"
                params.append(date_to)

            query += " ORDER BY created_at DESC"

            if limit:
                param_count += 1
                query += f" LIMIT ${param_count}"
                params.append(limit)

            if offset:
                param_count += 1
                query += f" OFFSET ${param_count}"
                params.append(offset)

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [DLQItem.from_row(dict(row)) for row in rows]

        except Exception as e:
            logger.error("Failed to get DLQ items: %s", e)
            return []

    async def get_dlq_item(self, item_id: str) -> Optional[DLQItem]:
        """Get a specific DLQ item by ID."""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM public.job_dead_letter_queue WHERE id = $1", item_id
                )
                if row:
                    return DLQItem.from_row(dict(row))
                return None
        except Exception as e:
            logger.error("Failed to get DLQ item %s: %s", item_id, e)
            return None

    async def get_dlq_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about the dead letter queue."""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(DISTINCT tenant_id) as unique_tenants,
                    COUNT(DISTINCT failure_reason) as unique_failure_reasons,
                    MAX(attempt_count) as max_attempts,
                    AVG(attempt_count) as avg_attempts,
                    MIN(created_at) as oldest_item,
                    MAX(created_at) as newest_item
                FROM public.job_dead_letter_queue
                WHERE 1=1
            """
            params = []
            param_count = 0

            if tenant_id:
                param_count += 1
                query += f" AND tenant_id = ${param_count}"
                params.append(tenant_id)

            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                stats = dict(row) if row else {}

                # Get failure reason breakdown
                breakdown_query = """
                    SELECT failure_reason, COUNT(*) as count
                    FROM public.job_dead_letter_queue
                    WHERE 1=1
                """
                if tenant_id:
                    breakdown_query += " AND tenant_id = $1"
                    breakdown_rows = await conn.fetch(breakdown_query, tenant_id)
                else:
                    breakdown_rows = await conn.fetch(breakdown_query)

                stats["failure_breakdown"] = [
                    {"reason": row["failure_reason"], "count": row["count"]}
                    for row in breakdown_rows
                ]

                return stats

        except Exception as e:
            logger.error("Failed to get DLQ stats: %s", e)
            return {}

    async def retry_application(self, item_id: str, force: bool = False) -> RetryResult:
        """Retry a failed application from the DLQ."""
        try:
            async with self.pool.acquire() as conn:
                # Start transaction
                async with conn.transaction():
                    # Get DLQ item
                    dlq_row = await conn.fetchrow(
                        "SELECT * FROM public.job_dead_letter_queue WHERE id = $1",
                        item_id,
                    )

                    if not dlq_row:
                        return RetryResult(
                            success=False,
                            message="DLQ item not found",
                            application_id=item_id,
                        )

                    dlq_item = DLQItem.from_row(dict(dlq_row))

                    # Check if application still exists and is in FAILED status
                    app_row = await conn.fetchrow(
                        "SELECT status FROM public.applications WHERE id = $1",
                        dlq_item.application_id,
                    )

                    if not app_row:
                        return RetryResult(
                            success=False,
                            message="Application not found",
                            application_id=dlq_item.application_id,
                        )

                    if app_row["status"] != "FAILED" and not force:
                        return RetryResult(
                            success=False,
                            message=f"Application status is {app_row['status']}, not FAILED. Use force to override.",
                            application_id=dlq_item.application_id,
                            new_status=app_row["status"],
                        )

                    # Reset application to QUEUED status
                    await conn.execute(
                        """
                        UPDATE public.applications
                        SET 
                            status = 'QUEUED',
                            last_error = NULL,
                            available_at = now(),
                            updated_at = now(),
                            attempt_count = 0
                        WHERE id = $1
                        """,
                        dlq_item.application_id,
                    )

                    # Remove from DLQ
                    await conn.execute(
                        "DELETE FROM public.job_dead_letter_queue WHERE id = $1",
                        item_id,
                    )

                    # Log retry event
                    await conn.execute(
                        """
                        INSERT INTO public.application_events
                        (application_id, event_type, event_data, created_at, tenant_id)
                        VALUES ($1, 'DLQ_RETRY', $2, now(), $3)
                        """,
                        dlq_item.application_id,
                        json.dumps(
                            {
                                "dlq_item_id": item_id,
                                "original_failure": dlq_item.failure_reason,
                                "original_attempts": dlq_item.attempt_count,
                                "retry_timestamp": datetime.now(
                                    timezone.utc
                                ).isoformat(),
                            }
                        ),
                        dlq_item.tenant_id,
                    )

                    logger.info(
                        "Retried application %s from DLQ (item %s)",
                        dlq_item.application_id,
                        item_id,
                    )

                    return RetryResult(
                        success=True,
                        message="Application successfully queued for retry",
                        application_id=dlq_item.application_id,
                        new_status="QUEUED",
                    )

        except Exception as e:
            logger.error("Failed to retry application from DLQ item %s: %s", item_id, e)
            return RetryResult(
                success=False,
                message=f"Retry failed: {str(e)}",
                application_id=item_id,
                error=str(e),
            )

    async def batch_retry_applications(
        self, item_ids: List[str], force: bool = False
    ) -> List[RetryResult]:
        """Retry multiple applications from the DLQ."""
        results = []

        for item_id in item_ids:
            result = await self.retry_application(item_id, force)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        logger.info(
            "Batch retry completed: %d/%d successful", success_count, len(item_ids)
        )

        return results

    async def delete_dlq_item(self, item_id: str) -> bool:
        """Delete an item from the DLQ without retrying."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM public.job_dead_letter_queue WHERE id = $1", item_id
                )

                deleted = result.split()[-1] == "1"
                if deleted:
                    logger.info("Deleted DLQ item %s", item_id)
                else:
                    logger.warning("DLQ item %s not found for deletion", item_id)

                return deleted

        except Exception as e:
            logger.error("Failed to delete DLQ item %s: %s", item_id, e)
            return False

    async def bulk_delete_dlq_items(
        self,
        tenant_id: Optional[str] = None,
        failure_reason: Optional[str] = None,
        older_than_days: Optional[int] = None,
    ) -> int:
        """Bulk delete DLQ items based on criteria."""
        try:
            query = "DELETE FROM public.job_dead_letter_queue WHERE 1=1"
            params = []
            param_count = 0

            if tenant_id:
                param_count += 1
                query += f" AND tenant_id = ${param_count}"
                params.append(tenant_id)

            if failure_reason:
                param_count += 1
                query += f" AND failure_reason = ${param_count}"
                params.append(failure_reason)

            if older_than_days:
                param_count += 1
                query += f" AND created_at < now() - interval '{older_than_days} days'"

            async with self.pool.acquire() as conn:
                result = await conn.execute(query, *params)
                deleted_count = int(result.split()[-1])

                logger.info(
                    "Bulk deleted %d DLQ items (tenant=%s, reason=%s, older_than=%d days)",
                    deleted_count,
                    tenant_id,
                    failure_reason,
                    older_than_days,
                )

                return deleted_count

        except Exception as e:
            logger.error("Failed to bulk delete DLQ items: %s", e)
            return 0

    async def get_failure_reasons(self) -> List[str]:
        """Get list of unique failure reasons."""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT DISTINCT failure_reason FROM public.job_dead_letter_queue ORDER BY failure_reason"
                )
                return [row["failure_reason"] for row in rows]
        except Exception as e:
            logger.error("Failed to get failure reasons: %s", e)
            return []

    async def get_tenant_dlq_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get DLQ summary for a specific tenant."""
        try:
            stats = await self.get_dlq_stats(tenant_id)
            items = await self.get_dlq_items(tenant_id, limit=10)

            return {
                "stats": stats,
                "recent_items": [
                    {
                        "id": item.id,
                        "application_id": item.application_id,
                        "failure_reason": item.failure_reason,
                        "attempt_count": item.attempt_count,
                        "created_at": item.created_at.isoformat(),
                        "last_error": item.last_error[:200] + "..."
                        if len(item.last_error) > 200
                        else item.last_error,
                    }
                    for item in items
                ],
            }
        except Exception as e:
            logger.error("Failed to get tenant DLQ summary for %s: %s", tenant_id, e)
            return {"stats": {}, "recent_items": []}


# Singleton instance
_dlq_manager: Optional[DLQManager] = None


def get_dlq_manager(pool: asyncpg.Pool) -> DLQManager:
    """Get or create the DLQ manager instance."""
    global _dlq_manager
    if _dlq_manager is None:
        _dlq_manager = DLQManager(pool)
    return _dlq_manager
