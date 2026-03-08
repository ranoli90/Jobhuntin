"""
Notification Batch Processor for Phase 13.1 Communication System
"""

from __future__ import annotations

import uuid
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from shared.logging_config import get_logger

logger = get_logger("sorce.notification_batch_processor")


@dataclass
class NotificationBatch:
    """Notification batch configuration."""

    id: str
    name: str
    tenant_id: str
    user_ids: List[str]
    notification_template: Dict[str, Any]
    batch_size: int = 100
    priority: str = "medium"
    schedule_time: Optional[datetime] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class BatchProcessingResult:
    """Batch processing result."""

    batch_id: str
    total_users: int
    successful: int
    failed: int
    skipped: int
    processing_time_seconds: float
    error_details: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class UserNotificationBatch:
    """User notification batch entry."""

    id: str
    batch_id: str
    user_id: str
    tenant_id: str
    notification_data: Dict[str, Any]
    status: str = "pending"  # pending, processing, sent, failed, skipped
    error_message: Optional[str] = None
    processing_attempts: int = 0
    sent_at: Optional[datetime] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class NotificationBatchProcessor:
    """Advanced notification batch processing system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._processing_stats: Dict[str, Any] = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "average_processing_time": 0.0,
        }
        self._max_concurrent_batches = 5
        self._batch_timeout_seconds = 300  # 5 minutes
        self._retry_attempts = 3
        self._processing_lock = asyncio.Lock()

    async def create_batch(
        self,
        name: str,
        tenant_id: str,
        user_ids: List[str],
        notification_template: Dict[str, Any],
        batch_size: int = 100,
        priority: str = "medium",
        schedule_time: Optional[datetime] = None,
    ) -> NotificationBatch:
        """Create a new notification batch."""
        try:
            batch = NotificationBatch(
                id=str(uuid.uuid4()),
                name=name,
                tenant_id=tenant_id,
                user_ids=user_ids,
                notification_template=notification_template,
                batch_size=batch_size,
                priority=priority,
                schedule_time=schedule_time,
            )

            # Save batch
            await self._save_batch(batch)

            # Create user notification entries
            await self._create_user_notification_batches(batch)

            logger.info(
                f"Created notification batch {batch.id} for {len(user_ids)} users"
            )
            return batch

        except Exception as e:
            logger.error(f"Failed to create notification batch: {e}")
            raise

    async def process_batch(self, batch_id: str) -> BatchProcessingResult:
        """Process a notification batch."""
        try:
            start_time = datetime.now()

            # Get batch details
            batch = await self._get_batch(batch_id)
            if not batch:
                raise Exception(f"Batch {batch_id} not found")

            # Get user notification entries
            user_batches = await self._get_user_notification_batches(batch_id)

            # Process in chunks
            successful = 0
            failed = 0
            skipped = 0
            error_details = []

            # Split into chunks for processing
            chunks = self._split_into_chunks(user_batches, batch.batch_size)

            for chunk in chunks:
                chunk_results = await self._process_chunk(chunk, batch)
                successful += chunk_results["successful"]
                failed += chunk_results["failed"]
                skipped += chunk_results["skipped"]
                error_details.extend(chunk_results["error_details"])

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Create result
            result = BatchProcessingResult(
                batch_id=batch_id,
                total_users=len(user_batches),
                successful=successful,
                failed=failed,
                skipped=skipped,
                processing_time_seconds=processing_time,
                error_details=error_details,
            )

            # Save result
            await self._save_batch_result(result)

            # Update global stats
            await self._update_global_stats(result)

            logger.info(
                f"Processed batch {batch_id}: {successful} successful, {failed} failed, {skipped} skipped"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to process batch {batch_id}: {e}")
            raise

    async def schedule_batch_processing(self, batch_id: str) -> None:
        """Schedule batch for processing."""
        try:
            batch = await self._get_batch(batch_id)
            if not batch:
                raise Exception(f"Batch {batch_id} not found")

            # Add to processing queue
            await self._processing_queue.put(batch_id)

            logger.info(f"Scheduled batch {batch_id} for processing")

        except Exception as e:
            logger.error(f"Failed to schedule batch processing: {e}")

    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get batch processing status."""
        try:
            batch = await self._get_batch(batch_id)
            if not batch:
                return {"status": "not_found"}

            # Get user batch counts
            user_batches = await self._get_user_notification_batches(batch_id)

            status_counts = {}
            for user_batch in user_batches:
                status = user_batch.status
                status_counts[status] = status_counts.get(status, 0) + 1

            # Get latest result if available
            result = await self._get_latest_result(batch_id)

            return {
                "batch_id": batch_id,
                "name": batch.name,
                "status": "processing"
                if status_counts.get("pending", 0) > 0
                else "completed",
                "total_users": len(user_batches),
                "status_counts": status_counts,
                "created_at": batch.created_at.isoformat(),
                "updated_at": batch.updated_at.isoformat(),
                "latest_result": result.__dict__ if result else None,
            }

        except Exception as e:
            logger.error(f"Failed to get batch status: {e}")
            return {"status": "error", "error": str(e)}

    async def get_batch_history(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get batch processing history."""
        try:
            query = """
                SELECT * FROM notification_batches 
                WHERE tenant_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id, limit, offset)

                batches = []
                for row in results:
                    batch = {
                        "id": row[0],
                        "name": row[1],
                        "tenant_id": row[2],
                        "user_count": row[3],
                        "batch_size": row[4],
                        "priority": row[5],
                        "status": row[6],
                        "created_at": row[7].isoformat(),
                        "updated_at": row[8].isoformat(),
                    }
                    batches.append(batch)

                return batches

        except Exception as e:
            logger.error(f"Failed to get batch history: {e}")
            return []

    async def retry_failed_notifications(self, batch_id: str) -> Dict[str, Any]:
        """Retry failed notifications in a batch."""
        try:
            # Get failed user batches
            failed_batches = await self._get_failed_user_batches(batch_id)

            retry_results = []
            successful_retries = 0

            for user_batch in failed_batches:
                if user_batch.processing_attempts >= self._retry_attempts:
                    # Skip if max retries reached
                    user_batch.status = "skipped"
                    user_batch.error_message = "Max retry attempts reached"
                    await self._update_user_batch(user_batch)
                    continue

                # Reset for retry
                user_batch.status = "pending"
                user_batch.error_message = None
                user_batch.processing_attempts += 1
                await self._update_user_batch(user_batch)

                # Process retry
                try:
                    await self._process_user_notification(user_batch)
                    successful_retries += 1
                    retry_results.append(
                        {
                            "user_id": user_batch.user_id,
                            "status": "success",
                        }
                    )
                except Exception as e:
                    retry_results.append(
                        {
                            "user_id": user_batch.user_id,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

            logger.info(
                f"Retried {len(failed_batches)} failed notifications, {successful_retries} successful"
            )

            return {
                "total_retried": len(failed_batches),
                "successful": successful_retries,
                "failed": len(failed_batches) - successful_retries,
                "results": retry_results,
            }

        except Exception as e:
            logger.error(f"Failed to retry failed notifications: {e}")
            raise

    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch processing."""
        try:
            # Get batch
            batch = await self._get_batch(batch_id)
            if not batch:
                return False

            # Mark all pending user batches as skipped
            query = """
                UPDATE user_notification_batches 
                SET status = 'skipped', updated_at = NOW()
                WHERE batch_id = $1 AND status = 'pending'
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(query, batch_id)
                skipped_count = int(result.split()[-1]) if result else 0

            logger.info(
                f"Cancelled batch {batch_id}, skipped {skipped_count} notifications"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cancel batch: {e}")
            return False

    async def get_processing_stats(
        self, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get processing statistics."""
        try:
            stats = self._processing_stats.copy()

            if tenant_id:
                # Get tenant-specific stats
                query = """
                    SELECT 
                        COUNT(*) as total_batches,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                        SUM(user_count) as total_notifications,
                        AVG(processing_time_seconds) as avg_processing_time
                    FROM notification_batches 
                    WHERE tenant_id = $1
                """

                async with self.db_pool.acquire() as conn:
                    result = await conn.fetchrow(query, tenant_id)

                    if result:
                        stats.update(
                            {
                                "tenant_id": tenant_id,
                                "total_batches": result[0],
                                "completed_batches": result[1],
                                "total_notifications": result[2],
                                "average_processing_time": result[3] or 0.0,
                            }
                        )

            return stats

        except Exception as e:
            logger.error(f"Failed to get processing stats: {e}")
            return {}

    async def _process_chunk(
        self,
        chunk: List[UserNotificationBatch],
        batch: NotificationBatch,
    ) -> Dict[str, Any]:
        """Process a chunk of user notifications."""
        successful = 0
        failed = 0
        skipped = 0
        error_details = []

        # Process concurrently with limited concurrency
        semaphore = asyncio.Semaphore(10)  # Limit concurrent processing

        async def process_user_batch(user_batch: UserNotificationBatch):
            nonlocal successful, failed, skipped

            try:
                async with semaphore:
                    await self._process_user_notification(user_batch)
                    successful += 1
            except Exception as e:
                failed += 1
                error_details.append(
                    {
                        "user_id": user_batch.user_id,
                        "error": str(e),
                    }
                )

        # Process all user batches in the chunk
        tasks = [process_user_batch(user_batch) for user_batch in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "error_details": error_details,
        }

    async def _process_user_notification(
        self, user_batch: UserNotificationBatch
    ) -> None:
        """Process a single user notification."""
        try:
            # Update status to processing
            user_batch.status = "processing"
            await self._update_user_batch(user_batch)

            # Get notification manager
            from packages.backend.domain.notification_manager import (
                create_notification_manager,
            )

            notification_manager = create_notification_manager(self.db_pool)

            # Send notification
            await notification_manager.send_notification(
                user_id=user_batch.user_id,
                tenant_id=user_batch.tenant_id,
                **user_batch.notification_data,
            )

            # Update status to sent
            user_batch.status = "sent"
            user_batch.sent_at = datetime.now(timezone.utc)
            await self._update_user_batch(user_batch)

        except Exception as e:
            # Update status to failed
            user_batch.status = "failed"
            user_batch.error_message = str(e)
            user_batch.processing_attempts += 1
            await self._update_user_batch(user_batch)

            raise

    def _split_into_chunks(self, items: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split list into chunks."""
        chunks = []
        for i in range(0, len(items), chunk_size):
            chunks.append(items[i : i + chunk_size])
        return chunks

    async def _get_batch(self, batch_id: str) -> Optional[NotificationBatch]:
        """Get batch by ID."""
        try:
            query = """
                SELECT * FROM notification_batches 
                WHERE id = $1
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, batch_id)

                if result:
                    return NotificationBatch(
                        id=result[0],
                        name=result[1],
                        tenant_id=result[2],
                        user_ids=result[3] or [],
                        notification_template=result[4] or {},
                        batch_size=result[5] or 100,
                        priority=result[6] or "medium",
                        schedule_time=result[7],
                        created_at=result[8],
                        updated_at=result[9],
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to get batch: {e}")
            return None

    async def _get_user_notification_batches(
        self, batch_id: str
    ) -> List[UserNotificationBatch]:
        """Get user notification batches."""
        try:
            query = """
                SELECT * FROM user_notification_batches 
                WHERE batch_id = $1
                ORDER BY created_at
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, batch_id)

                user_batches = []
                for row in results:
                    user_batch = UserNotificationBatch(
                        id=row[0],
                        batch_id=row[1],
                        user_id=row[2],
                        tenant_id=row[3],
                        notification_data=row[4] or {},
                        status=row[5] or "pending",
                        error_message=row[6],
                        processing_attempts=row[7] or 0,
                        sent_at=row[8],
                        created_at=row[9],
                        updated_at=row[10],
                    )
                    user_batches.append(user_batch)

                return user_batches

        except Exception as e:
            logger.error(f"Failed to get user notification batches: {e}")
            return []

    async def _get_failed_user_batches(
        self, batch_id: str
    ) -> List[UserNotificationBatch]:
        """Get failed user notification batches."""
        try:
            query = """
                SELECT * FROM user_notification_batches 
                WHERE batch_id = $1 AND status = 'failed'
                ORDER BY created_at
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, batch_id)

                failed_batches = []
                for row in results:
                    user_batch = UserNotificationBatch(
                        id=row[0],
                        batch_id=row[1],
                        user_id=row[2],
                        tenant_id=row[3],
                        notification_data=row[4] or {},
                        status=row[5] or "pending",
                        error_message=row[6],
                        processing_attempts=row[7] or 0,
                        sent_at=row[8],
                        created_at=row[9],
                        updated_at=row[10],
                    )
                    failed_batches.append(user_batch)

                return failed_batches

        except Exception as e:
            logger.error(f"Failed to get failed user batches: {e}")
            return []

    async def _get_latest_result(
        self, batch_id: str
    ) -> Optional[BatchProcessingResult]:
        """Get latest processing result for batch."""
        try:
            query = """
                SELECT * FROM batch_processing_results 
                WHERE batch_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, batch_id)

                if result:
                    return BatchProcessingResult(
                        batch_id=result[0],
                        total_users=result[1],
                        successful=result[2],
                        failed=result[3],
                        skipped=result[4],
                        processing_time_seconds=result[5],
                        error_details=result[6] or [],
                        created_at=result[7],
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to get latest result: {e}")
            return None

    async def _save_batch(self, batch: NotificationBatch) -> None:
        """Save batch to database."""
        try:
            query = """
                INSERT INTO notification_batches (
                    id, name, tenant_id, user_ids, notification_template, 
                    batch_size, priority, schedule_time, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    notification_template = EXCLUDED.notification_template,
                    batch_size = EXCLUDED.batch_size,
                    priority = EXCLUDED.priority,
                    schedule_time = EXCLUDED.schedule_time,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                batch.id,
                batch.name,
                batch.tenant_id,
                batch.user_ids,
                batch.notification_template,
                batch.batch_size,
                batch.priority,
                batch.schedule_time,
                batch.created_at,
                batch.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save batch: {e}")

    async def _create_user_notification_batches(self, batch: NotificationBatch) -> None:
        """Create user notification batch entries."""
        try:
            for user_id in batch.user_ids:
                user_batch = UserNotificationBatch(
                    id=str(uuid.uuid4()),
                    batch_id=batch.id,
                    user_id=user_id,
                    tenant_id=batch.tenant_id,
                    notification_data=batch.notification_template,
                )

                await self._save_user_batch(user_batch)

        except Exception as e:
            logger.error(f"Failed to create user notification batches: {e}")

    async def _save_user_batch(self, user_batch: UserNotificationBatch) -> None:
        """Save user batch to database."""
        try:
            query = """
                INSERT INTO user_notification_batches (
                    id, batch_id, user_id, tenant_id, notification_data, 
                    status, error_message, processing_attempts, sent_at, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    error_message = EXCLUDED.error_message,
                    processing_attempts = EXCLUDED.processing_attempts,
                    sent_at = EXCLUDED.sent_at,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                user_batch.id,
                user_batch.batch_id,
                user_batch.user_id,
                user_batch.tenant_id,
                user_batch.notification_data,
                user_batch.status,
                user_batch.error_message,
                user_batch.processing_attempts,
                user_batch.sent_at,
                user_batch.created_at,
                user_batch.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save user batch: {e}")

    async def _update_user_batch(self, user_batch: UserNotificationBatch) -> None:
        """Update user batch in database."""
        try:
            query = """
                UPDATE user_notification_batches 
                SET status = $1, error_message = $2, processing_attempts = $3, 
                    sent_at = $4, updated_at = NOW()
                WHERE id = $5
            """

            params = [
                user_batch.status,
                user_batch.error_message,
                user_batch.processing_attempts,
                user_batch.sent_at,
                user_batch.id,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to update user batch: {e}")

    async def _save_batch_result(self, result: BatchProcessingResult) -> None:
        """Save batch processing result."""
        try:
            query = """
                INSERT INTO batch_processing_results (
                    batch_id, total_users, successful, failed, skipped, 
                    processing_time_seconds, error_details, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """

            params = [
                result.batch_id,
                result.total_users,
                result.successful,
                result.failed,
                result.skipped,
                result.processing_time_seconds,
                result.error_details,
                result.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save batch result: {e}")

    async def _update_global_stats(self, result: BatchProcessingResult) -> None:
        """Update global processing statistics."""
        try:
            self._processing_stats["total_processed"] += result.total_users
            self._processing_stats["successful"] += result.successful
            self._processing_stats["failed"] += result.failed
            self._processing_stats["skipped"] += result.skipped

            # Update average processing time
            total_time = self._processing_stats.get("total_processing_time", 0.0)
            total_batches = self._processing_stats.get("total_batches", 0)

            new_total_time = total_time + result.processing_time_seconds
            new_total_batches = total_batches + 1

            self._processing_stats["average_processing_time"] = (
                new_total_time / new_total_batches
            )
            self._processing_stats["total_processing_time"] = new_total_time
            self._processing_stats["total_batches"] = new_total_batches

        except Exception as e:
            logger.error(f"Failed to update global stats: {e}")


# Factory function
def create_notification_batch_processor(db_pool) -> NotificationBatchProcessor:
    """Create notification batch processor instance."""
    return NotificationBatchProcessor(db_pool)
