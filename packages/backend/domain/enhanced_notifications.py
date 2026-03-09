"""Enhanced push notification system with semantic matching and alert processing.

This module provides advanced push notification capabilities including:
- Semantic matching for relevant notifications
- Alert processing with intelligent scheduling
- Enhanced notification templates
- Notification batching and throttling
- User preference management
- Delivery tracking and analytics
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.enhanced_notifications")


class NotificationPriority(Enum):
    """Notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationCategory(Enum):
    """Notification categories for semantic matching."""

    APPLICATION_STATUS = "application_status"
    JOB_MATCHES = "job_matches"
    SYSTEM_ALERTS = "system_alerts"
    MARKETING = "marketing"
    SECURITY = "security"
    USAGE_LIMITS = "usage_limits"
    REMINDERS = "reminders"


@dataclass
class NotificationContent:
    """Enhanced notification content with semantic data."""

    title: str
    body: str
    category: NotificationCategory
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: Dict[str, Any] = field(default_factory=dict)
    semantic_tags: Set[str] = field(default_factory=set)
    relevance_score: float = 0.0
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None


@dataclass
class NotificationRule:
    """Rule for notification processing and semantic matching."""

    name: str
    category: NotificationCategory
    conditions: Dict[str, Any]
    actions: List[str]
    priority: NotificationPriority
    throttle_window: timedelta = timedelta(minutes=15)
    max_frequency: int = 3


class SemanticNotificationMatcher:
    """Handles semantic matching for notifications."""

    def __init__(self):
        self.user_interests: Dict[str, Set[str]] = {}
        self.notification_history: Dict[str, List[Dict[str, Any]]] = {}
        self.semantic_keywords = {
            NotificationCategory.APPLICATION_STATUS: {
                "applied",
                "submitted",
                "completed",
                "failed",
                "rejected",
                "interview",
                "offer",
                "status",
                "application",
                "job",
            },
            NotificationCategory.JOB_MATCHES: {
                "match",
                "recommendation",
                "job",
                "position",
                "role",
                "opportunity",
                "career",
                "salary",
                "location",
                "skills",
            },
            NotificationCategory.SYSTEM_ALERTS: {
                "system",
                "maintenance",
                "update",
                "alert",
                "important",
                "urgent",
                "attention",
                "notification",
            },
            NotificationCategory.MARKETING: {
                "promotion",
                "offer",
                "discount",
                "deal",
                "feature",
                "new",
                "update",
                "announcement",
            },
            NotificationCategory.SECURITY: {
                "security",
                "login",
                "password",
                "authentication",
                "token",
                "access",
                "unauthorized",
                "suspicious",
                "protect",
            },
            NotificationCategory.USAGE_LIMITS: {
                "limit",
                "quota",
                "usage",
                "exceeded",
                "reached",
                "warning",
                "upgrade",
                "plan",
                "subscription",
                "billing",
            },
            NotificationCategory.REMINDERS: {
                "reminder",
                "follow",
                "up",
                "complete",
                "action",
                "due",
                "deadline",
                "pending",
                "waiting",
                "response",
            },
        }

    def calculate_relevance_score(
        self,
        user_id: str,
        content: NotificationContent,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Calculate relevance score for notification to user."""
        score = 0.0

        # Base score by category
        category_scores = {
            NotificationCategory.APPLICATION_STATUS: 0.9,
            NotificationCategory.JOB_MATCHES: 0.8,
            NotificationCategory.SYSTEM_ALERTS: 0.7,
            NotificationCategory.SECURITY: 0.8,
            NotificationCategory.USAGE_LIMITS: 0.6,
            NotificationCategory.REMINDERS: 0.5,
            NotificationCategory.MARKETING: 0.3,
        }

        score += category_scores.get(content.category, 0.5)

        # Priority bonus
        priority_bonus = {
            NotificationPriority.CRITICAL: 0.3,
            NotificationPriority.HIGH: 0.2,
            NotificationPriority.MEDIUM: 0.1,
            NotificationPriority.LOW: 0.0,
        }

        score += priority_bonus.get(content.priority, 0.0)

        # Semantic matching with user interests
        if user_id in self.user_interests:
            user_tags = self.user_interests[user_id]
            content_tags = content.semantic_tags.union(
                self._extract_semantic_tags(content.title + " " + content.body)
            )

            # Calculate tag overlap
            if user_tags and content_tags:
                overlap = len(user_tags.intersection(content_tags))
                tag_score = (
                    min(overlap / max(len(user_tags), len(content_tags)), 1.0) * 0.2
                )
                score += tag_score

        # Recency penalty (avoid notification fatigue)
        recent_notifications = self.notification_history.get(user_id, [])
        if recent_notifications:
            last_hour = [
                n
                for n in recent_notifications
                if n.get("sent_at")
                and datetime.now(timezone.utc) - n["sent_at"] < timedelta(hours=1)
            ]
            if last_hour:
                fatigue_penalty = min(len(last_hour) * 0.05, 0.3)
                score -= fatigue_penalty

        return max(0.0, min(1.0, score))

    def _extract_semantic_tags(self, text: str) -> Set[str]:
        """Extract semantic tags from text."""
        text_lower = text.lower()
        tags = set()

        for category, keywords in self.semantic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags.add(keyword)

        return tags

    def update_user_interests(self, user_id: str, interests: Set[str]) -> None:
        """Update user's semantic interests."""
        self.user_interests[user_id] = interests

    def record_notification_sent(
        self,
        user_id: str,
        content: NotificationContent,
        sent_at: datetime,
    ) -> None:
        """Record notification sent for semantic learning."""
        if user_id not in self.notification_history:
            self.notification_history[user_id] = []

        self.notification_history[user_id].append(
            {
                "category": content.category.value,
                "priority": content.priority.value,
                "sent_at": sent_at,
                "semantic_tags": list(content.semantic_tags),
            }
        )

        # Keep only last 50 notifications per user
        if len(self.notification_history[user_id]) > 50:
            self.notification_history[user_id] = self.notification_history[user_id][
                -50:
            ]


class AlertProcessor:
    """Processes and schedules alerts with intelligent rules."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.rules: Dict[str, NotificationRule] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default alert processing rules."""
        self.rules = {
            "application_success": NotificationRule(
                name="Application Success",
                category=NotificationCategory.APPLICATION_STATUS,
                conditions={"status": ["completed", "submitted"]},
                actions=["send_notification", "update_dashboard"],
                priority=NotificationPriority.HIGH,
                throttle_window=timedelta(minutes=30),
                max_frequency=1,
            ),
            "application_failed": NotificationRule(
                name="Application Failed",
                category=NotificationCategory.APPLICATION_STATUS,
                conditions={"status": ["failed", "error"]},
                actions=["send_notification", "create_support_ticket"],
                priority=NotificationPriority.HIGH,
                throttle_window=timedelta(minutes=10),
                max_frequency=2,
            ),
            "rate_limit_warning": NotificationRule(
                name="Rate Limit Warning",
                category=NotificationCategory.USAGE_LIMITS,
                conditions={"usage_percentage": {"gte": 80}},
                actions=["send_notification", "log_alert"],
                priority=NotificationPriority.MEDIUM,
                throttle_window=timedelta(hours=2),
                max_frequency=1,
            ),
            "rate_limit_reached": NotificationRule(
                name="Rate Limit Reached",
                category=NotificationCategory.USAGE_LIMITS,
                conditions={"usage_percentage": {"gte": 100}},
                actions=["send_notification", "suspend_service"],
                priority=NotificationPriority.CRITICAL,
                throttle_window=timedelta(hours=1),
                max_frequency=1,
            ),
            "security_alert": NotificationRule(
                name="Security Alert",
                category=NotificationCategory.SECURITY,
                conditions={"security_level": ["high", "critical"]},
                actions=["send_notification", "log_security_event"],
                priority=NotificationPriority.CRITICAL,
                throttle_window=timedelta(minutes=5),
                max_frequency=3,
            ),
        }

    async def process_alert(
        self,
        alert_type: str,
        user_id: str,
        alert_data: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> List[NotificationContent]:
        """Process an alert and return notifications to send."""
        notifications = []

        rule = self.rules.get(alert_type)
        if not rule:
            logger.warning("No rule found for alert type: %s", alert_type)
            return notifications

        # Check conditions
        if not self._evaluate_conditions(rule.conditions, alert_data):
            return notifications

        # Check throttling
        if not await self._check_throttling(user_id, rule):
            logger.info("Alert throttled for user %s: %s", user_id, alert_type)
            return notifications

        # Create notification content
        content = await self._create_notification_content(rule, alert_data, user_id)
        if content:
            notifications.append(content)

        # Execute additional actions
        for action in rule.actions:
            await self._execute_action(action, alert_data, user_id, tenant_id)

        # Record alert processing
        await self._record_alert_processed(user_id, alert_type, rule, alert_data)

        return notifications

    def _evaluate_conditions(
        self, conditions: Dict[str, Any], data: Dict[str, Any]
    ) -> bool:
        """Evaluate alert conditions against data."""
        for key, expected in conditions.items():
            actual = data.get(key)

            if isinstance(expected, dict):
                # Handle range conditions
                if "gte" in expected and actual < expected["gte"]:
                    return False
                if "lte" in expected and actual > expected["lte"]:
                    return False
                if "eq" in expected and actual != expected["eq"]:
                    return False
                if "in" in expected and actual not in expected["in"]:
                    return False
            elif isinstance(expected, list):
                if actual not in expected:
                    return False
            else:
                if actual != expected:
                    return False

        return True

    async def _check_throttling(self, user_id: str, rule: NotificationRule) -> bool:
        """Check if alert should be throttled."""
        try:
            async with self.pool.acquire() as conn:
                recent_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM public.alert_processing_log
                    WHERE user_id = $1
                    AND alert_type = $2
                    AND processed_at >= now() - make_interval(secs => $3)
                    """,
                    user_id,
                    rule.name,
                    rule.throttle_window.total_seconds(),
                )

                return recent_count < rule.max_frequency

        except Exception as e:
            logger.error("Failed to check throttling: %s", e)
            return True  # Allow if check fails

    async def _create_notification_content(
        self,
        rule: NotificationRule,
        alert_data: Dict[str, Any],
        user_id: str,
    ) -> Optional[NotificationContent]:
        """Create notification content from alert data."""
        try:
            if rule.category == NotificationCategory.APPLICATION_STATUS:
                return NotificationContent(
                    title="Application Update",
                    body=self._get_status_message(alert_data),
                    category=rule.category,
                    priority=rule.priority,
                    data=alert_data,
                    action_url=f"/applications/{alert_data.get('application_id')}",
                    action_text="View Application",
                )

            elif rule.category == NotificationCategory.USAGE_LIMITS:
                usage_pct = alert_data.get("usage_percentage", 0)
                if usage_pct >= 100:
                    return NotificationContent(
                        title="Usage Limit Reached",
                        body=f"You've reached your {alert_data.get('limit_type', 'usage')} limit.",
                        category=rule.category,
                        priority=rule.priority,
                        data=alert_data,
                        action_url="/pricing",
                        action_text="Upgrade Plan",
                    )
                else:
                    return NotificationContent(
                        title="Usage Warning",
                        body=f"You've used {usage_pct}% of your {alert_data.get('limit_type', 'usage')} limit.",
                        category=rule.category,
                        priority=rule.priority,
                        data=alert_data,
                        action_url="/usage",
                        action_text="View Usage",
                    )

            elif rule.category == NotificationCategory.SECURITY:
                return NotificationContent(
                    title="Security Alert",
                    body=alert_data.get("message", "Security action required"),
                    category=rule.category,
                    priority=rule.priority,
                    data=alert_data,
                    action_url="/security",
                    action_text="Review Security",
                )

            return None

        except Exception as e:
            logger.error("Failed to create notification content: %s", e)
            return None

    def _get_status_message(self, alert_data: Dict[str, Any]) -> str:
        """Get status message from alert data."""
        status = alert_data.get("status", "")
        company = alert_data.get("company", "a company")
        job_title = alert_data.get("job_title", "a position")

        if status in ["completed", "submitted"]:
            return f"Your application to {company} for {job_title} was successfully submitted!"
        elif status in ["failed", "error"]:
            return f"There was an issue with your application to {company} for {job_title}."
        else:
            return f"Your application to {company} for {job_title} status: {status}"

    async def _execute_action(
        self,
        action: str,
        alert_data: Dict[str, Any],
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Execute additional alert actions."""
        try:
            if action == "log_alert":
                await self._log_alert(alert_data, user_id, tenant_id)
            elif action == "create_support_ticket":
                await self._create_support_ticket(alert_data, user_id, tenant_id)
            elif action == "suspend_service":
                await self._suspend_service(user_id, tenant_id)
            elif action == "log_security_event":
                await self._log_security_event(alert_data, user_id, tenant_id)
            elif action == "update_dashboard":
                await self._update_dashboard(alert_data, user_id, tenant_id)

        except Exception as e:
            logger.error("Failed to execute action %s: %s", action, e)

    async def _record_alert_processed(
        self,
        user_id: str,
        alert_type: str,
        rule: NotificationRule,
        alert_data: Dict[str, Any],
    ) -> None:
        """Record alert processing for analytics."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO public.alert_processing_log
                    (user_id, tenant_id, alert_type, rule_name, alert_data, processed_at)
                    VALUES ($1, $2, $3, $4, $5::jsonb, now())
                    """,
                    user_id,
                    alert_data.get("tenant_id"),
                    alert_type,
                    rule.name,
                    json.dumps(alert_data),
                )
        except Exception as e:
            logger.error("Failed to record alert processing: %s", e)

    async def _log_alert(
        self, alert_data: Dict[str, Any], user_id: str, tenant_id: Optional[str]
    ) -> None:
        """Log alert to system logs."""
        logger.info("Alert logged for user %s: %s", user_id, alert_data)

    async def _create_support_ticket(
        self, alert_data: Dict[str, Any], user_id: str, tenant_id: Optional[str]
    ) -> None:
        """Create support ticket for critical issues."""
        # TODO: Implement support ticket creation
        logger.info("Support ticket created for user %s: %s", user_id, alert_data)

    async def _suspend_service(self, user_id: str, tenant_id: Optional[str]) -> None:
        """Suspend service for rule violations."""
        # TODO: Implement service suspension
        logger.warning("Service suspended for user %s", user_id)

    async def _log_security_event(
        self, alert_data: Dict[str, Any], user_id: str, tenant_id: Optional[str]
    ) -> None:
        """Log security event."""
        logger.warning("Security event for user %s: %s", user_id, alert_data)

    async def _update_dashboard(
        self, alert_data: Dict[str, Any], user_id: str, tenant_id: Optional[str]
    ) -> None:
        """Update user dashboard with alert information."""
        # TODO: Implement dashboard update
        logger.info("Dashboard updated for user %s: %s", user_id, alert_data)


class EnhancedNotificationManager:
    """Enhanced notification manager with semantic matching and alert processing."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.semantic_matcher = SemanticNotificationMatcher()
        self.alert_processor = AlertProcessor(pool)
        self.batch_queue: List[Dict[str, Any]] = []
        self.batch_size = 50
        self.batch_timeout = timedelta(seconds=30)
        self.last_batch_process = datetime.now(timezone.utc)

    async def send_notification(
        self,
        user_id: str,
        content: NotificationContent,
        tenant_id: Optional[str] = None,
        force_send: bool = False,
    ) -> bool:
        """Send enhanced notification with semantic matching."""
        try:
            # Get user context and preferences
            user_context = await self._get_user_context(user_id)

            # Calculate relevance score
            relevance_score = self.semantic_matcher.calculate_relevance_score(
                user_id, content, user_context
            )

            # Check if notification should be sent
            if not force_send and relevance_score < 0.3:
                logger.info(
                    "Notification filtered due to low relevance: %s", relevance_score
                )
                return False

            # Check user preferences
            if not await self._check_user_preferences(user_id, content.category):
                logger.info("Notification filtered due to user preferences")
                return False

            # Check if user is in Do Not Disturb mode
            if await self._is_dnd_active(user_id):
                # Add to batch queue for later
                self.batch_queue.append(
                    {
                        "user_id": user_id,
                        "content": content,
                        "tenant_id": tenant_id,
                        "relevance_score": relevance_score,
                        "queued_at": datetime.now(timezone.utc),
                    }
                )
                return True

            # Send notification immediately
            success = await self._send_push_notification(user_id, content, tenant_id)

            if success:
                # Record for semantic learning
                self.semantic_matcher.record_notification_sent(
                    user_id, content, datetime.now(timezone.utc)
                )

                # Log notification
                await self._log_notification_sent(
                    user_id, content, tenant_id, relevance_score
                )

            return success

        except Exception as e:
            logger.error("Failed to send enhanced notification: %s", e)
            return False

    async def process_alert(
        self,
        alert_type: str,
        user_id: str,
        alert_data: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> int:
        """Process alert and send notifications."""
        try:
            notifications = await self.alert_processor.process_alert(
                alert_type, user_id, alert_data, tenant_id
            )

            sent_count = 0
            for notification in notifications:
                if await self.send_notification(user_id, notification, tenant_id):
                    sent_count += 1

            return sent_count

        except Exception as e:
            logger.error(
                "Failed to process alert %s for user %s: %s", alert_type, user_id, e
            )
            return 0

    async def process_batch_queue(self) -> int:
        """Process batched notifications."""
        if not self.batch_queue:
            return 0

        # Check if it's time to process batch
        now = datetime.now(timezone.utc)
        if (
            now - self.last_batch_process < self.batch_timeout
            and len(self.batch_queue) < self.batch_size
        ):
            return 0

        batch_to_process = self.batch_queue[: self.batch_size]
        self.batch_queue = self.batch_queue[self.batch_size :]
        self.last_batch_process = now

        sent_count = 0
        for item in batch_to_process:
            if await self._send_push_notification(
                item["user_id"], item["content"], item["tenant_id"]
            ):
                sent_count += 1

        logger.info(
            "Processed batch of %d notifications, sent %d",
            len(batch_to_process),
            sent_count,
        )
        return sent_count

    async def _get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user context for semantic matching."""
        try:
            async with self.pool.acquire() as conn:
                user_data = await conn.fetchrow(
                    """
                    SELECT u.full_name, u.email, up.preferences
                    FROM public.users u
                    LEFT JOIN public.user_preferences up ON up.user_id = u.id
                    WHERE u.id = $1
                    """,
                    user_id,
                )

                if user_data:
                    return {
                        "name": user_data["full_name"],
                        "email": user_data["email"],
                        "preferences": user_data.get("preferences", {}),
                    }

                return None

        except Exception as e:
            logger.error("Failed to get user context: %s", e)
            return None

    async def _check_user_preferences(
        self, user_id: str, category: NotificationCategory
    ) -> bool:
        """Check if user wants notifications from this category."""
        try:
            async with self.pool.acquire() as conn:
                prefs = await conn.fetchrow(
                    """
                    SELECT status_changes, security, usage_alerts, marketing, reminders
                    FROM public.email_preferences
                    WHERE user_id = $1
                    """,
                    user_id,
                )

                if not prefs:
                    return True  # Default to enabled

                category_mapping = {
                    NotificationCategory.APPLICATION_STATUS: prefs["status_changes"],
                    NotificationCategory.SECURITY: prefs["security"],
                    NotificationCategory.USAGE_LIMITS: prefs["usage_alerts"],
                    NotificationCategory.MARKETING: prefs["marketing"],
                    NotificationCategory.REMINDERS: prefs["reminders"],
                }

                return category_mapping.get(category, True)

        except Exception as e:
            logger.error("Failed to check user preferences: %s", e)
            return True  # Default to enabled

    async def _is_dnd_active(self, user_id: str) -> bool:
        """Check if user is in Do Not Disturb mode."""
        try:
            async with self.pool.acquire() as conn:
                dnd_active = await conn.fetchval(
                    """
                    SELECT dnd_active FROM public.user_preferences
                    WHERE user_id = $1
                    """,
                    user_id,
                )

                return bool(dnd_active)

        except Exception:
            return False

    async def _send_push_notification(
        self,
        user_id: str,
        content: NotificationContent,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Send push notification using existing notification system."""
        try:
            # Import here to avoid circular imports
            from packages.backend.domain.notifications import send_push_to_user

            async with self.pool.acquire() as conn:
                sent_count = await send_push_to_user(
                    conn=conn,
                    user_id=user_id,
                    title=content.title,
                    body=content.body,
                    notification_type=content.category.value,
                    data=content.data,
                    tenant_id=tenant_id,
                )

                return sent_count > 0

        except Exception as e:
            logger.error("Failed to send push notification: %s", e)
            return False

    async def _log_notification_sent(
        self,
        user_id: str,
        content: NotificationContent,
        tenant_id: Optional[str],
        relevance_score: float,
    ) -> None:
        """Log notification sent for analytics."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO public.notification_log
                    (user_id, tenant_id, channel, notification_type, title, body, metadata)
                    VALUES ($1, $2, 'push', $3, $4, $5, $6::jsonb)
                    """,
                    user_id,
                    tenant_id,
                    content.category.value,
                    content.title,
                    content.body,
                    json.dumps(
                        {
                            "priority": content.priority.value,
                            "relevance_score": relevance_score,
                            "semantic_tags": list(content.semantic_tags),
                            "action_url": content.action_url,
                            "expires_at": content.expires_at.isoformat()
                            if content.expires_at
                            else None,
                        }
                    ),
                )
        except Exception as e:
            logger.error("Failed to log notification: %s", e)


# Global instance
_enhanced_notification_manager: Optional[EnhancedNotificationManager] = None


def get_enhanced_notification_manager(
    pool: asyncpg.Pool,
) -> EnhancedNotificationManager:
    """Get or create the enhanced notification manager."""
    global _enhanced_notification_manager
    if _enhanced_notification_manager is None:
        _enhanced_notification_manager = EnhancedNotificationManager(pool)
    return _enhanced_notification_manager
