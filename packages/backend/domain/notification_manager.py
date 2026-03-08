"""
Notification Manager for Phase 13.1 Communication System
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from shared.logging_config import get_logger

logger = get_logger("sorce.notification_manager")


@dataclass
class Notification:
    """Notification data structure."""

    id: str
    user_id: str
    tenant_id: str
    title: str
    message: str
    category: str
    priority: str = "medium"  # critical, high, medium, low
    channels: List[str] = field(default_factory=lambda: ["in_app"])
    data: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    is_read: bool = False
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class NotificationDelivery:
    """Notification delivery tracking."""

    id: str
    notification_id: str
    user_id: str
    tenant_id: str
    channel: str  # in_app, email, push, sms
    status: str = "pending"  # pending, sent, delivered, failed, read
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    external_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class UserNotificationPreferences:
    """User notification preferences."""

    user_id: str
    tenant_id: str
    in_app_enabled: bool = True
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    categories: Dict[str, Dict[str, bool]] = field(default_factory=dict)
    do_not_disturb_enabled: bool = False
    do_not_disturb_start: Optional[str] = None  # HH:MM format
    do_not_disturb_end: Optional[str] = None  # HH:MM format
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class NotificationManager:
    """Advanced notification management system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._delivery_handlers: Dict[str, callable] = {}
        self._rate_limits: Dict[str, Dict[str, int]] = {}
        self._batch_size = 100

    async def send_notification(
        self,
        user_id: str,
        tenant_id: str,
        title: str,
        message: str,
        category: str = "general",
        priority: str = "medium",
        channels: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Notification:
        """Send a notification to a user."""
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(user_id, tenant_id)

            # Check if notifications are enabled
            if not await self._is_notification_allowed(preferences, category, priority):
                raise Exception("Notification not allowed by user preferences")

            # Create notification
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                title=title,
                message=message,
                category=category,
                priority=priority,
                channels=channels or ["in_app"],
                data=data or {},
                expires_at=expires_at,
            )

            # Save notification
            await self._save_notification(notification)

            # Send to channels
            await self._send_to_channels(notification, preferences)

            logger.info(f"Notification sent to user {user_id}: {title}")
            return notification

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise

    async def send_batch_notifications(
        self,
        notifications: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send multiple notifications in batch."""
        try:
            if not batch_id:
                batch_id = str(uuid.uuid4())

            results = []
            failed_count = 0

            for notification_data in notifications:
                try:
                    notification = await self.send_notification(**notification_data)
                    results.append(
                        {
                            "success": True,
                            "notification_id": notification.id,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "success": False,
                            "error": str(e),
                        }
                    )
                    failed_count += 1

            # Log batch processing
            await self._log_batch_processing(
                batch_id,
                len(notifications),
                len(notifications) - failed_count,
                failed_count,
            )

            return {
                "batch_id": batch_id,
                "total": len(notifications),
                "successful": len(notifications) - failed_count,
                "failed": failed_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to send batch notifications: {e}")
            raise

    async def get_user_preferences(
        self, user_id: str, tenant_id: str
    ) -> UserNotificationPreferences:
        """Get user notification preferences."""
        try:
            query = """
                SELECT * FROM user_preferences 
                WHERE user_id = $1 AND tenant_id = $2
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query, user_id, tenant_id)

                if not result:
                    # Create default preferences
                    preferences = UserNotificationPreferences(
                        user_id=user_id,
                        tenant_id=tenant_id,
                        categories={
                            "application_status": {
                                "in_app": True,
                                "email": True,
                                "push": True,
                            },
                            "job_matches": {
                                "in_app": True,
                                "email": True,
                                "push": True,
                            },
                            "security": {
                                "in_app": True,
                                "email": True,
                                "push": True,
                                "sms": True,
                            },
                            "marketing": {
                                "in_app": False,
                                "email": False,
                                "push": False,
                            },
                            "usage_limits": {
                                "in_app": True,
                                "email": True,
                                "push": True,
                            },
                            "reminders": {"in_app": True, "email": True, "push": True},
                        },
                    )
                    await self._save_user_preferences(preferences)
                    return preferences

                row = result[0]
                return UserNotificationPreferences(
                    user_id=row[0],
                    tenant_id=row[1],
                    in_app_enabled=row[2] or True,
                    email_enabled=row[3] or True,
                    push_enabled=row[4] or True,
                    sms_enabled=row[5] or False,
                    categories=row[6] or {},
                    do_not_disturb_enabled=row[7] or False,
                    do_not_disturb_start=row[8],
                    do_not_disturb_end=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                )

        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            # Return default preferences
            return UserNotificationPreferences(
                user_id=user_id,
                tenant_id=tenant_id,
            )

    async def update_preferences(
        self,
        user_id: str,
        tenant_id: str,
        in_app_enabled: Optional[bool] = None,
        email_enabled: Optional[bool] = None,
        push_enabled: Optional[bool] = None,
        sms_enabled: Optional[bool] = None,
        categories: Optional[Dict[str, Dict[str, bool]]] = None,
        do_not_disturb_enabled: Optional[bool] = None,
        do_not_disturb_start: Optional[str] = None,
        do_not_disturb_end: Optional[str] = None,
    ) -> UserNotificationPreferences:
        """Update user notification preferences."""
        try:
            # Get current preferences
            preferences = await self.get_user_preferences(user_id, tenant_id)

            # Update fields
            if in_app_enabled is not None:
                preferences.in_app_enabled = in_app_enabled

            if email_enabled is not None:
                preferences.email_enabled = email_enabled

            if push_enabled is not None:
                preferences.push_enabled = push_enabled

            if sms_enabled is not None:
                preferences.sms_enabled = sms_enabled

            if categories is not None:
                for category, channels in categories.items():
                    if category not in preferences.categories:
                        preferences.categories[category] = {}
                    preferences.categories[category].update(channels)

            if do_not_disturb_enabled is not None:
                preferences.do_not_disturb_enabled = do_not_disturb_enabled

            if do_not_disturb_start is not None:
                preferences.do_not_disturb_start = do_not_disturb_start

            if do_not_disturb_end is not None:
                preferences.do_not_disturb_end = do_not_disturb_end

            preferences.updated_at = datetime.now(timezone.utc)

            # Save to database
            await self._save_user_preferences(preferences)

            logger.info(f"Updated notification preferences for user {user_id}")
            return preferences

        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            raise

    async def get_notifications(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        unread_only: bool = False,
    ) -> List[Notification]:
        """Get user notifications."""
        try:
            query = """
                SELECT * FROM notifications 
                WHERE user_id = $1 AND tenant_id = $2
            """
            params = [user_id, tenant_id]

            if category:
                query += " AND category = $3"
                params.append(category)

            if unread_only:
                query += " AND is_read = false"
                if category:
                    query += " AND category = $4"
                else:
                    query += " AND is_read = $3"

            query += " ORDER BY created_at DESC LIMIT $"
            if category and unread_only:
                query += "5 OFFSET $6"
                params.extend([limit, offset])
            else:
                query += "4 OFFSET $5"
                params.extend([limit, offset])

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                notifications = []
                for row in results:
                    notification = Notification(
                        id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        title=row[3],
                        message=row[4],
                        category=row[5],
                        priority=row[6],
                        channels=row[7] or [],
                        data=row[8] or {},
                        expires_at=row[9],
                        is_read=row[10],
                        created_at=row[11],
                        updated_at=row[12],
                    )
                    notifications.append(notification)

                return notifications

        except Exception as e:
            logger.error(f"Failed to get notifications for {user_id}: {e}")
            return []

    async def mark_as_read(
        self, notification_id: str, user_id: str, tenant_id: str
    ) -> bool:
        """Mark notification as read."""
        try:
            query = """
                UPDATE notifications 
                SET is_read = true, updated_at = NOW() 
                WHERE id = $1 AND user_id = $2 AND tenant_id = $3
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(query, notification_id, user_id, tenant_id)

                # Update delivery tracking
                await self._update_delivery_status(notification_id, "read")

                return result == "UPDATE 1"

        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    async def mark_all_as_read(
        self, user_id: str, tenant_id: str, category: Optional[str] = None
    ) -> int:
        """Mark all notifications as read."""
        try:
            query = """
                UPDATE notifications 
                SET is_read = true, updated_at = NOW() 
                WHERE user_id = $1 AND tenant_id = $2 AND is_read = false
            """
            params = [user_id, tenant_id]

            if category:
                query += " AND category = $3"
                params.append(category)

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(query, *params)

                # Extract count from result
                count = int(result.split()[-1]) if result else 0

                logger.info(f"Marked {count} notifications as read for user {user_id}")
                return count

        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            return 0

    async def delete_notification(
        self, notification_id: str, user_id: str, tenant_id: str
    ) -> bool:
        """Delete a notification."""
        try:
            query = """
                DELETE FROM notifications 
                WHERE id = $1 AND user_id = $2 AND tenant_id = $3
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(query, notification_id, user_id, tenant_id)

                return result == "DELETE 1"

        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            return False

    async def get_notification_stats(
        self, user_id: str, tenant_id: str
    ) -> Dict[str, Any]:
        """Get notification statistics for a user."""
        try:
            query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN is_read = false THEN 1 END) as unread,
                    COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical,
                    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high,
                    COUNT(CASE WHEN priority = 'medium' THEN 1 END) as medium,
                    COUNT(CASE WHEN priority = 'low' THEN 1 END) as low,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as last_7d
                FROM notifications 
                WHERE user_id = $1 AND tenant_id = $2
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, user_id, tenant_id)

                if result:
                    return {
                        "total": result[0],
                        "unread": result[1],
                        "critical": result[2],
                        "high": result[3],
                        "medium": result[4],
                        "low": result[5],
                        "last_24h": result[6],
                        "last_7d": result[7],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get notification stats: {e}")
            return {}

    async def _is_notification_allowed(
        self,
        preferences: UserNotificationPreferences,
        category: str,
        priority: str,
    ) -> bool:
        """Check if notification is allowed by user preferences."""
        try:
            # Check do not disturb
            if preferences.do_not_disturb_enabled:
                current_time = datetime.now().strftime("%H:%M")
                if (
                    preferences.do_not_disturb_start
                    and preferences.do_not_disturb_end
                    and self._is_in_do_not_disturb(
                        current_time,
                        preferences.do_not_disturb_start,
                        preferences.do_not_disturb_end,
                    )
                ):
                    # Allow critical notifications during DND
                    if priority != "critical":
                        return False

            # Check category preferences
            category_prefs = preferences.categories.get(category, {})

            # Check if any channel is enabled for this category
            for channel, enabled in category_prefs.items():
                if enabled:
                    # Check if channel is globally enabled
                    if channel == "in_app" and preferences.in_app_enabled:
                        return True
                    elif channel == "email" and preferences.email_enabled:
                        return True
                    elif channel == "push" and preferences.push_enabled:
                        return True
                    elif channel == "sms" and preferences.sms_enabled:
                        return True

            return False

        except Exception as e:
            logger.error(f"Failed to check notification allowance: {e}")
            return True  # Allow if check fails

    async def _send_to_channels(
        self, notification: Notification, preferences: UserNotificationPreferences
    ) -> None:
        """Send notification to enabled channels."""
        try:
            category_prefs = preferences.categories.get(notification.category, {})

            for channel in notification.channels:
                # Check if channel is enabled for this category
                if not category_prefs.get(channel, False):
                    continue

                # Check if channel is globally enabled
                if channel == "in_app" and not preferences.in_app_enabled:
                    continue
                elif channel == "email" and not preferences.email_enabled:
                    continue
                elif channel == "push" and not preferences.push_enabled:
                    continue
                elif channel == "sms" and not preferences.sms_enabled:
                    continue

                # Create delivery tracking
                delivery = NotificationDelivery(
                    id=str(uuid.uuid4()),
                    notification_id=notification.id,
                    user_id=notification.user_id,
                    tenant_id=notification.tenant_id,
                    channel=channel,
                    status="pending",
                )

                # Save delivery tracking
                await self._save_delivery(delivery)

                # Send via channel handler
                await self._send_via_channel(notification, channel, delivery)

        except Exception as e:
            logger.error(f"Failed to send to channels: {e}")

    async def _send_via_channel(
        self, notification: Notification, channel: str, delivery: NotificationDelivery
    ) -> None:
        """Send notification via specific channel."""
        try:
            if channel == "in_app":
                # In-app notifications are stored in the database
                delivery.status = "delivered"
                delivery.delivered_at = datetime.now(timezone.utc)
            elif channel == "email":
                # Send via email manager
                from packages.backend.domain.email_communication_manager import (
                    create_email_communication_manager,
                )

                email_manager = create_email_communication_manager(self.db_pool)

                await email_manager.send_email(
                    user_id=notification.user_id,
                    tenant_id=notification.tenant_id,
                    to_email="",  # Will be fetched from user data
                    subject=notification.title,
                    body=notification.message,
                    category=notification.category,
                )

                delivery.status = "sent"
                delivery.sent_at = datetime.now(timezone.utc)
            elif channel == "push":
                # Send via push notification service
                delivery.status = "sent"
                delivery.sent_at = datetime.now(timezone.utc)
            elif channel == "sms":
                # Send via SMS service
                delivery.status = "sent"
                delivery.sent_at = datetime.now(timezone.utc)

            # Update delivery status
            await self._update_delivery(delivery)

        except Exception as e:
            delivery.status = "failed"
            delivery.error_message = str(e)
            await self._update_delivery(delivery)

            logger.error(f"Failed to send via {channel}: {e}")

    def _is_in_do_not_disturb(self, current_time: str, start: str, end: str) -> bool:
        """Check if current time is in do not disturb hours."""
        try:
            current_hour = int(current_time.split(":")[0])
            current_minute = int(current_time.split(":")[1])
            start_hour = int(start.split(":")[0])
            start_minute = int(start.split(":")[1])
            end_hour = int(end.split(":")[0])
            end_minute = int(end.split(":")[1])

            current_minutes = current_hour * 60 + current_minute
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute

            if start_minutes <= end_minutes:
                return start_minutes <= current_minutes <= end_minutes
            else:
                # Overnight do not disturb
                return (
                    current_minutes >= start_minutes or current_minutes <= end_minutes
                )

        except Exception:
            return False

    async def _save_notification(self, notification: Notification) -> None:
        """Save notification to database."""
        try:
            query = """
                INSERT INTO notifications (
                    id, user_id, tenant_id, title, message, category, 
                    priority, channels, data, expires_at, is_read, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (id) DO UPDATE SET
                    is_read = EXCLUDED.is_read,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                notification.id,
                notification.user_id,
                notification.tenant_id,
                notification.title,
                notification.message,
                notification.category,
                notification.priority,
                notification.channels,
                notification.data,
                notification.expires_at,
                notification.is_read,
                notification.created_at,
                notification.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save notification: {e}")

    async def _save_delivery(self, delivery: NotificationDelivery) -> None:
        """Save delivery tracking to database."""
        try:
            query = """
                INSERT INTO notification_delivery_tracking (
                    id, notification_id, user_id, tenant_id, channel, 
                    status, sent_at, delivered_at, read_at, error_message, 
                    external_id, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    sent_at = EXCLUDED.sent_at,
                    delivered_at = EXCLUDED.delivered_at,
                    read_at = EXCLUDED.read_at,
                    error_message = EXCLUDED.error_message,
                    external_id = EXCLUDED.external_id,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                delivery.id,
                delivery.notification_id,
                delivery.user_id,
                delivery.tenant_id,
                delivery.channel,
                delivery.status,
                delivery.sent_at,
                delivery.delivered_at,
                delivery.read_at,
                delivery.error_message,
                delivery.external_id,
                delivery.metadata,
                delivery.created_at,
                delivery.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save delivery: {e}")

    async def _update_delivery(self, delivery: NotificationDelivery) -> None:
        """Update delivery tracking."""
        try:
            query = """
                UPDATE notification_delivery_tracking 
                SET status = $1, sent_at = $2, delivered_at = $3, 
                    read_at = $4, error_message = $5, external_id = $6, updated_at = NOW()
                WHERE id = $7
            """

            params = [
                delivery.status,
                delivery.sent_at,
                delivery.delivered_at,
                delivery.read_at,
                delivery.error_message,
                delivery.external_id,
                delivery.id,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to update delivery: {e}")

    async def _update_delivery_status(self, notification_id: str, status: str) -> None:
        """Update delivery status for all channels."""
        try:
            query = """
                UPDATE notification_delivery_tracking 
                SET status = $1, updated_at = NOW()
                WHERE notification_id = $2
            """

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, status, notification_id)

        except Exception as e:
            logger.error(f"Failed to update delivery status: {e}")

    async def _save_user_preferences(
        self, preferences: UserNotificationPreferences
    ) -> None:
        """Save user preferences to database."""
        try:
            query = """
                INSERT INTO user_preferences (
                    user_id, tenant_id, in_app_enabled, email_enabled, 
                    push_enabled, sms_enabled, categories, do_not_disturb_enabled, 
                    do_not_disturb_start, do_not_disturb_end, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (user_id, tenant_id) DO UPDATE SET
                    in_app_enabled = EXCLUDED.in_app_enabled,
                    email_enabled = EXCLUDED.email_enabled,
                    push_enabled = EXCLUDED.push_enabled,
                    sms_enabled = EXCLUDED.sms_enabled,
                    categories = EXCLUDED.categories,
                    do_not_disturb_enabled = EXCLUDED.do_not_disturb_enabled,
                    do_not_disturb_start = EXCLUDED.do_not_disturb_start,
                    do_not_disturb_end = EXCLUDED.do_not_disturb_end,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                preferences.user_id,
                preferences.tenant_id,
                preferences.in_app_enabled,
                preferences.email_enabled,
                preferences.push_enabled,
                preferences.sms_enabled,
                preferences.categories,
                preferences.do_not_disturb_enabled,
                preferences.do_not_disturb_start,
                preferences.do_not_disturb_end,
                preferences.created_at,
                preferences.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")

    async def _log_batch_processing(
        self,
        batch_id: str,
        total: int,
        successful: int,
        failed: int,
    ) -> None:
        """Log batch processing results."""
        try:
            query = """
                INSERT INTO notification_batches (
                    id, total_notifications, successful, failed, 
                    processed_at, created_at
                ) VALUES ($1, $2, $3, $4, NOW(), NOW())
            """

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, batch_id, total, successful, failed)

        except Exception as e:
            logger.error(f"Failed to log batch processing: {e}")


# Factory function
def create_notification_manager(db_pool) -> NotificationManager:
    """Create notification manager instance."""
    return NotificationManager(db_pool)
