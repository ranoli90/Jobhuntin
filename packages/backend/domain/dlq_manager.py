"""
DLQ Manager for Phase 12.1 Agent Improvements
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from pydantic import BaseModel
from shared.logging_config import get_logger

logger = get_logger("sorce.dlq_manager")


@dataclass
class DLQItem:
    """Dead Letter Queue item."""

    id: str
    application_id: str
    tenant_id: str
    failure_reason: str
    error_details: Dict[str, Any] = {}
    attempt_count: int = 1
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    payload: Dict[str, Any] = {}
    status: str = "pending"  # pending, retrying, completed, failed, cancelled
    priority: int = 0  # Higher priority = retry sooner
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class RetryResult:
    """Result of retrying a DLQ item."""

    success: bool
    message: str
    new_attempt_count: int
    next_retry_at: Optional[datetime] = None
    error_details: Optional[Dict[str, Any]] = None


@dataclass
class BulkRetryRequest(BaseModel):
    """Request for bulk retry operations."""

    item_ids: List[str]
    force: bool = False


@dataclass
class BulkDeleteRequest(BaseModel):
    """Request for bulk delete operations."""

    tenant_id: Optional[str] = None
    failure_reason: Optional[str] = None
    older_than_days: int = 7


class DLQManager:
    """Dead Letter Queue management system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._max_retries = 3
        self._base_retry_delay = 60  # 1 minute
        self._max_retry_delay = 3600  # 1 hour

    async def add_to_dlq(
        self,
        application_id: str,
        tenant_id: str,
        failure_reason: str,
        error_details: Dict[str, Any],
        payload: Dict[str, Any],
        max_retries: int = 3,
        priority: int = 0,
    ) -> DLQItem:
        """Add failed application to Dead Letter Queue."""
        dlq_item = DLQItem(
            id=str(uuid.uuid4()),
            application_id=application_id,
            tenant_id=tenant_id,
            failure_reason=failure_reason,
            error_details=error_details,
            attempt_count=1,
            max_retries=max_retries,
            payload=payload,
            status="pending",
            priority=priority,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Store DLQ item in database
        await self._store_dlq_item(dlq_item)

        logger.info(f"Added to DLQ: {dlq_item.id} for application {application_id}")
        return dlq_item

    async def get_dlq_items(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        failure_reason: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[DLQItem]:
        """Get DLQ items with filtering."""
        try:
            query = """
                SELECT * FROM dead_letter_queue
                WHERE 1=1
            """
            params = []

            if tenant_id:
                query += " AND tenant_id = $1"
                params.append(tenant_id)

            if status:
                query += " AND status = $1"
                params.append(status)

            if failure_reason:
                query += " AND failure_reason = $1"
                params.append(failure_reason)

            if date_from:
                query += " AND created_at >= $1"
                params.append(date_from)

            if date_to:
                query += " AND created_at <= $1"
                params.append(date_to)

            query += " ORDER BY created_at DESC"
            query += " LIMIT $1 OFFSET $2"
            params.extend([limit, offset])

            # Execute query
            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)
                items = []

                for row in results:
                    dlq_item = DLQItem(
                        id=row[0],
                        application_id=row[1],
                        tenant_id=row[2],
                        failure_reason=row[3],
                        error_details=row[4],
                        attempt_count=row[5],
                        max_retries=row[6],
                        next_retry_at=row[7],
                        payload=row[8],
                        status=row[9],
                        priority=row[10],
                        created_at=row[11],
                        updated_at=row[12],
                    )
                    items.append(dlq_item)

                return items

        except Exception as e:
            logger.error(f"Failed to get DLQ items: {e}")
            return []

    async def get_dlq_item(self, dlq_item_id: str) -> Optional[DLQItem]:
        """Get a specific DLQ item by ID."""
        try:
            query = "SELECT * FROM dead_letter_queue WHERE id = $1"

            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query, [dlq_item_id])

                if not result:
                    return None

                row = result[0]
                dlq_item = DLQItem(
                    id=row[0],
                    application_id=row[1],
                    tenant_id=row[2],
                    failure_reason=row[3],
                    error_details=row[4],
                    attempt_count=row[5],
                    max_retries=row[6],
                    next_retry_at=row[7],
                    payload=row[8],
                    status=row[9],
                    priority=row[10],
                    created_at=row[11],
                    updated_at=row[12],
                )

                return dlq_item

        except Exception as e:
            logger.error(f"Failed to get DLQ item {dlq_item_id}: {e}")
            return None

    async def delete_dlq_item(self, dlq_item_id: str) -> bool:
        """Delete a DLQ item."""
        try:
            query = "DELETE FROM dead_letter_queue WHERE id = $1"

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(query, [dlq_item_id])

                return result == "DELETE 1"

        except Exception as e:
            logger.error(f"Failed to delete DLQ item {dlq_item_id}: {e}")
            return False

    async def batch_retry_applications(
        self,
        item_ids: List[str],
        force: bool = False,
    ) -> List[RetryResult]:
        """Retry multiple DLQ items."""
        results = []

        for item_id in item_ids:
            success = await self.retry_dlq_item(item_id, force=force)
            results.append(success)

        return results

    async def retry_dlq_item(
        self,
        dlq_item_id: str,
        force: bool = False,
    ) -> RetryResult:
        """Retry a DLQ item."""
        try:
            dlq_item = await self.get_dlq_item(dlq_item_id)
            if not dlq_item:
                return RetryResult(
                    success=False,
                    message="DLQ item not found",
                    new_attempt_count=0,
                )

            # Check if retry is allowed
            if not force and dlq_item.attempt_count >= dlq_item.max_retries:
                return RetryResult(
                    success=False,
                    message="Max retries exceeded",
                    new_attempt_count=dlq_item.attempt_count,
                )

            # Check if retry time has arrived
            if dlq_item.next_retry_at and dlq_item.next_retry_at > datetime.now(
                timezone.utc
            ):
                return RetryResult(
                    success=False,
                    message="Retry time not reached",
                    new_attempt_count=dlq_item.attempt_count,
                    next_retry_at=dlq_item.next_retry_at,
                )

            try:
                # Attempt retry logic here
                success = await self._execute_retry(dlq_item)

                if success:
                    # Remove from DLQ on success
                    await self._remove_dlq_item(dlq_item_id)
                    return RetryResult(
                        success=True,
                        message="Retry successful",
                        new_attempt_count=dlq_item.attempt_count + 1,
                    )
                else:
                    # Update DLQ item for next retry
                    next_retry_at = self._calculate_next_retry_time(
                        dlq_item.attempt_count
                    )
                    await self._update_dlq_item_retry(
                        dlq_item_id,
                        dlq_item.attempt_count + 1,
                        next_retry_at,
                    )

                    return RetryResult(
                        success=False,
                        message="Retry failed, scheduled for next attempt",
                        new_attempt_count=dlq_item.attempt_count + 1,
                        next_retry_at=next_retry_at,
                        error_details={"error": "Retry failed"},
                    )

            except Exception as e:
                logger.error(f"Failed to retry DLQ item {dlq_item_id}: {e}")
                return RetryResult(
                    success=False,
                    message=f"Retry execution failed: {str(e)}",
                    new_attempt_count=dlq_item.attempt_count + 1,
                    error_details={"error": str(e)},
                )

        except Exception as e:
            logger.error(f"Failed to retry DLQ item {dlq_item_id}: {e}")
            return RetryResult(
                success=False,
                message=f"Retry execution failed: {str(e)}",
                new_attempt_count=0,
                error_details={"error": str(e)},
            )

    async def get_dlq_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get DLQ statistics."""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN status = 'pending') as pending_count,
                    COUNT(CASE WHEN status = 'retrying' as retrying_count,
                    COUNT(CASE WHEN status = 'completed') as completed_count,
                    COUNT(CASE WHEN status = 'failed' as failed_count
                FROM dead_letter_queue
            """

            if tenant_id:
                query += " WHERE tenant_id = $1"
                params = [tenant_id]

            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query, params)
                row = result[0] if result else {}

                stats = {
                    "total_items": row[0],
                    "pending_count": row[1],
                    "retrying_count": row[2],
                    "completed_count": row[3],
                    "failed_count": row[4],
                }

                return stats

        except Exception as e:
            logger.error(f"Failed to get DLQ stats: {e}")
            return {}

    async def get_failure_reasons(self) -> List[str]:
        """Get list of unique failure reasons."""
        try:
            query = "SELECT DISTINCT failure_reason FROM dead_letter_queue ORDER BY failure_reason"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query)
                return [row[0] for row in results]

        except Exception as e:
            logger.error(f"Failed to get failure reasons: {e}")
            return []

    async def get_tenant_dlq_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get DLQ summary for a specific tenant."""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN status = 'pending') as pending_count,
                    COUNT(CASE WHEN status = 'retrying' as retrying_count,
                    COUNT(CASE WHEN status = 'completed' as completed_count,
                    COUNT(CASE WHEN status = 'failed' as failed_count
                FROM dead_letter_queue
                WHERE tenant_id = $1
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query, [tenant_id])
                row = result[0] if result else {}

                summary = {
                    "total_items": row[0],
                    "pending_count": row[1],
                    "retrying_count": row[2],
                    "completed_count": row[3],
                    "failed_count": row[4],
                }

                return summary

        except Exception as e:
            logger.error(f"Failed to get tenant DLQ summary for {tenant_id}: {e}")
            return {}

    def _store_dlq_item(self, dlq_item: DLQItem) -> None:
        """Store DLQ item in database."""
        try:
            query = """
                INSERT INTO dead_letter_queue (
                    id, application_id, tenant_id, failure_reason, error_details, 
                    attempt_count, max_retries, next_retry_at, payload, status, priority, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """

            params = [
                dlq_item.id,
                dlq_item.application_id,
                dlq_item.tenant_id,
                dlq_item.failure_reason,
                str(dlq_item.error_details),
                dlq_item.attempt_count,
                dlq_item.max_retries,
                dlq_item.next_retry_at,
                str(dlq_item.payload),
                dlq_item.status,
                dlq_item.priority,
                dlq_item.created_at,
                dlq_item.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, params)

        except Exception as e:
            logger.error(f"Failed to store DLQ item: {e}")

    def _remove_dlq_item(self, dlq_item_id: str) -> None:
        """Remove DLQ item from database."""
        try:
            query = "DELETE FROM dead_letter_queue WHERE id = $1"

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, [dlq_item_id])

        except Exception as e:
            logger.error(f"Failed to remove DLQ item: {e}")

    def _update_dlq_item_retry(
        self,
        dlq_item_id: str,
        attempt_count: int,
        next_retry_at: datetime,
    ) -> None:
        """Update DLQ item retry information."""
        try:
            query = """
                UPDATE dead_letter_queue 
                SET attempt_count = $1, next_retry_at = $2
                WHERE id = $3
            """

            params = [attempt_count + 1, next_retry_at.isoformat(), dlq_item_id]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, params)

        except Exception as e:
            logger.error(f"Failed to update DLQ item retry: {e}")

    def _execute_retry(self, dlq_item: DLQItem) -> bool:
        """Execute retry logic for DLQ item."""
        try:
            # This would contain the actual retry logic
            # For now, return False to simulate failure
            logger.warning(
                f"Retry execution not implemented for DLQ item {dlq_item.id}"
            )
            return False
        except Exception as e:
            logger.error(f"Retry execution failed for DLQ item {dlq_item.id}: {e}")
            return False

    def _calculate_next_retry_time(self, attempt_count: int) -> datetime:
        """Calculate next retry time using exponential backoff."""
        delay_minutes = min(5 ** (attempt_count - 1), 600)  # Max 10 hours
        return datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)


# Factory function
def get_dlq_manager() -> DLQManager:
    """Create DLQ manager instance."""
    from apps.worker.dlq_manager import DLQManager

    return DLQManager()
