"""
Alert Processor for Phase 13.1 Communication System
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.alert_processor")


class AlertType(Enum):
    """Alert types."""

    APPLICATION_SUCCESS = "application_success"
    APPLICATION_FAILED = "application_failed"
    RATE_LIMIT_WARNING = "rate_limit_warning"
    RATE_LIMIT_REACHED = "rate_limit_reached"
    SECURITY_ALERT = "security_alert"
    SYSTEM_ERROR = "system_error"
    MAINTENANCE = "maintenance"


class AlertPriority(Enum):
    """Alert priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """Alert processing rule."""

    id: str
    name: str
    alert_type: AlertType
    conditions: Dict[str, Any]
    actions: List[str]
    priority: AlertPriority
    enabled: bool = True
    throttle_minutes: int = 5
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class Alert:
    """Alert data structure."""

    id: str
    type: AlertType
    priority: AlertPriority
    user_id: str
    tenant_id: str
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, processed, failed, resolved
    processed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class AlertProcessingLog:
    """Alert processing log entry."""

    id: str
    alert_id: str
    rule_id: str
    action: str
    status: str
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    processing_time_ms: int = 0
    created_at: datetime = datetime.now(timezone.utc)


class AlertProcessor:
    """Intelligent alert processing system with rule-based routing."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._rules: Dict[str, AlertRule] = {}
        self._action_handlers: Dict[str, Callable] = {}
        self._throttling: Dict[str, datetime] = {}
        self._default_rules = self._initialize_default_rules()

    async def process_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Process an alert through rule-based system."""
        try:
            # Create alert object
            alert = Alert(
                id=str(uuid.uuid4()),
                type=AlertType(alert_data.get("type", "system_error")),
                priority=AlertPriority(alert_data.get("priority", "medium")),
                user_id=alert_data.get("user_id"),
                tenant_id=alert_data.get("tenant_id"),
                title=alert_data.get("title", "System Alert"),
                message=alert_data.get("message", "An alert has been triggered"),
                data=alert_data.get("data", {}),
                context=alert_data.get("context", {}),
            )

            # Save alert
            await self._save_alert(alert)

            # Find matching rules
            matching_rules = await self._find_matching_rules(alert)

            # Process through rules
            for rule in matching_rules:
                await self._process_alert_with_rule(alert, rule)

            # Update alert status
            alert.status = "processed"
            alert.processed_at = datetime.now(timezone.utc)
            await self._update_alert(alert)

            logger.info(f"Processed alert {alert.id} of type {alert.type.value}")
            return alert

        except Exception as e:
            logger.error(f"Failed to process alert: {e}")
            raise

    async def create_rule(
        self,
        name: str,
        alert_type: AlertType,
        conditions: Dict[str, Any],
        actions: List[str],
        priority: AlertPriority = AlertPriority.MEDIUM,
        throttle_minutes: int = 5,
    ) -> AlertRule:
        """Create a new alert processing rule."""
        try:
            rule = AlertRule(
                id=str(uuid.uuid4()),
                name=name,
                alert_type=alert_type,
                conditions=conditions,
                actions=actions,
                priority=priority,
                throttle_minutes=throttle_minutes,
            )

            # Save rule
            await self._save_rule(rule)

            # Load into memory
            self._rules[rule.id] = rule

            logger.info(f"Created alert rule: {name}")
            return rule

        except Exception as e:
            logger.error(f"Failed to create alert rule: {e}")
            raise

    async def get_rules(
        self, alert_type: Optional[AlertType] = None
    ) -> List[AlertRule]:
        """Get alert processing rules."""
        try:
            if alert_type:
                return [
                    rule
                    for rule in self._rules.values()
                    if rule.alert_type == alert_type
                ]
            return list(self._rules.values())
        except Exception as e:
            logger.error(f"Failed to get rules: {e}")
            return []

    async def update_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        actions: Optional[List[str]] = None,
        priority: Optional[AlertPriority] = None,
        enabled: Optional[bool] = None,
        throttle_minutes: Optional[int] = None,
    ) -> AlertRule:
        """Update an alert rule."""
        try:
            rule = self._rules.get(rule_id)
            if not rule:
                raise Exception(f"Rule {rule_id} not found")

            # Update fields
            if name is not None:
                rule.name = name
            if conditions is not None:
                rule.conditions = conditions
            if actions is not None:
                rule.actions = actions
            if priority is not None:
                rule.priority = priority
            if enabled is not None:
                rule.enabled = enabled
            if throttle_minutes is not None:
                rule.throttle_minutes = throttle_minutes

            rule.updated_at = datetime.now(timezone.utc)

            # Save to database
            await self._save_rule(rule)

            logger.info(f"Updated alert rule: {rule.name}")
            return rule

        except Exception as e:
            logger.error(f"Failed to update alert rule: {e}")
            raise

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        try:
            if rule_id not in self._rules:
                return False

            # Remove from memory
            del self._rules[rule_id]

            # Delete from database
            query = "DELETE FROM alert_rules WHERE id = $1"

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, rule_id)

            logger.info(f"Deleted alert rule: {rule_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete alert rule: {e}")
            return False

    async def get_alert_history(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        alert_type: Optional[AlertType] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Alert]:
        """Get alert history with filtering."""
        try:
            query = "SELECT * FROM alert_processing_log WHERE 1=1"
            params = []
            param_count = 0

            if user_id:
                param_count += 1
                query += f" AND user_id = ${param_count}"
                params.append(user_id)

            if tenant_id:
                param_count += 1
                query += f" AND tenant_id = ${param_count}"
                params.append(tenant_id)

            if alert_type:
                param_count += 1
                query += f" AND alert_type = ${param_count}"
                params.append(alert_type.value)

            if status:
                param_count += 1
                query += f" AND status = ${param_count}"
                params.append(status)

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

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                alerts = []
                for row in results:
                    alert = Alert(
                        id=row[0],
                        type=AlertType(row[1]),
                        priority=AlertPriority(row[2]),
                        user_id=row[3],
                        tenant_id=row[4],
                        title=row[5],
                        message=row[6],
                        data=row[7] or {},
                        context=row[8] or {},
                        status=row[9],
                        processed_at=row[10],
                        resolved_at=row[11],
                        created_at=row[12],
                        updated_at=row[13],
                    )
                    alerts.append(alert)

                return alerts

        except Exception as e:
            logger.error(f"Failed to get alert history: {e}")
            return []

    async def get_alert_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get alert processing statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_alerts,
                    COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as last_7d
                FROM alert_processing_log
            """
            params = []

            if tenant_id:
                query += " WHERE tenant_id = $1"
                params.append(tenant_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_alerts": result[0],
                        "processed": result[1],
                        "failed": result[2],
                        "resolved": result[3],
                        "last_24h": result[4],
                        "last_7d": result[5],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get alert stats: {e}")
            return {}

    async def register_action_handler(self, action: str, handler: Callable) -> None:
        """Register an action handler."""
        self._action_handlers[action] = handler
        logger.info(f"Registered action handler: {action}")

    async def _find_matching_rules(self, alert: Alert) -> List[AlertRule]:
        """Find rules that match the alert."""
        matching_rules = []

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            if rule.alert_type != alert.type:
                continue

            # Check conditions
            if await self._evaluate_conditions(rule.conditions, alert):
                # Check throttling
                if not self._is_throttled(rule, alert):
                    matching_rules.append(rule)

        # Sort by priority
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        matching_rules.sort(
            key=lambda r: priority_order.get(r.priority.value, 0), reverse=True
        )

        return matching_rules

    async def _evaluate_conditions(
        self, conditions: Dict[str, Any], alert: Alert
    ) -> bool:
        """Evaluate rule conditions against alert."""
        try:
            for field, condition in conditions.items():
                # Get alert field value
                alert_value = getattr(alert, field, None)
                if alert_value is None and field in alert.data:
                    alert_value = alert.data[field]

                # Evaluate condition
                if isinstance(condition, dict):
                    operator = condition.get("operator", "equals")
                    value = condition.get("value")

                    if operator == "equals":
                        if alert_value != value:
                            return False
                    elif operator == "contains":
                        if value not in str(alert_value):
                            return False
                    elif operator == "greater_than":
                        if (
                            not isinstance(alert_value, (int, float))
                            or alert_value <= value
                        ):
                            return False
                    elif operator == "less_than":
                        if (
                            not isinstance(alert_value, (int, float))
                            or alert_value >= value
                        ):
                            return False
                    elif operator == "in":
                        if alert_value not in value:
                            return False
                else:
                    # Simple equality check
                    if alert_value != condition:
                        return False

            return True

        except Exception as e:
            logger.error(f"Failed to evaluate conditions: {e}")
            return False

    def _is_throttled(self, rule: AlertRule, alert: Alert) -> bool:
        """Check if rule is throttled for this user/tenant."""
        try:
            throttle_key = f"{rule.id}:{alert.user_id}:{alert.tenant_id}"

            if throttle_key in self._throttling:
                last_execution = self._throttling[throttle_key]
                throttle_time = datetime.now(timezone.utc) - timedelta(
                    minutes=rule.throttle_minutes
                )

                if last_execution > throttle_time:
                    return True

            # Update throttle time
            self._throttling[throttle_key] = datetime.now(timezone.utc)
            return False

        except Exception:
            return False

    async def _process_alert_with_rule(self, alert: Alert, rule: AlertRule) -> None:
        """Process alert with a specific rule."""
        try:
            for action in rule.actions:
                start_time = datetime.now()

                try:
                    # Execute action
                    if action in self._action_handlers:
                        result = await self._action_handlers[action](alert, rule)
                    else:
                        result = await self._execute_default_action(action, alert, rule)

                    # Log successful action
                    processing_time = int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    )
                    await self._log_processing(
                        alert.id,
                        rule.id,
                        action,
                        "success",
                        result,
                        None,
                        processing_time,
                    )

                except Exception as e:
                    # Log failed action
                    processing_time = int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    )
                    await self._log_processing(
                        alert.id, rule.id, action, "failed", {}, str(e), processing_time
                    )

                    logger.error(
                        f"Failed to execute action {action} for alert {alert.id}: {e}"
                    )

        except Exception as e:
            logger.error(f"Failed to process alert with rule {rule.id}: {e}")

    async def _execute_default_action(
        self, action: str, alert: Alert, rule: AlertRule
    ) -> Dict[str, Any]:
        """Execute default action."""
        try:
            if action == "send_notification":
                # Send notification
                from packages.backend.domain.notification_manager import (
                    create_notification_manager,
                )

                notification_manager = create_notification_manager(self.db_pool)

                await notification_manager.send_notification(
                    user_id=alert.user_id,
                    tenant_id=alert.tenant_id,
                    title=alert.title,
                    message=alert.message,
                    category="alerts",
                    priority=alert.priority.value,
                    data=alert.data,
                )

                return {"status": "notification_sent"}

            elif action == "send_email":
                # Send email
                from packages.backend.domain.email_communication_manager import (
                    create_email_communication_manager,
                )

                email_manager = create_email_communication_manager(self.db_pool)

                await email_manager.send_email(
                    user_id=alert.user_id,
                    tenant_id=alert.tenant_id,
                    to_email="",  # Will be fetched from user data
                    subject=f"Alert: {alert.title}",
                    body=alert.message,
                    category="alerts",
                )

                return {"status": "email_sent"}

            elif action == "create_support_ticket":
                # Create support ticket
                ticket_data = {
                    "user_id": alert.user_id,
                    "tenant_id": alert.tenant_id,
                    "title": f"Alert: {alert.title}",
                    "description": alert.message,
                    "priority": alert.priority.value,
                    "alert_id": alert.id,
                    "alert_data": alert.data,
                }

                # This would integrate with a support ticket system
                logger.info(f"Support ticket created for alert {alert.id}")

                return {"status": "support_ticket_created", "ticket_data": ticket_data}

            elif action == "suspend_service":
                # Suspend user service
                suspension_data = {
                    "user_id": alert.user_id,
                    "tenant_id": alert.tenant_id,
                    "reason": alert.message,
                    "alert_id": alert.id,
                    "suspended_until": datetime.now(timezone.utc) + timedelta(hours=24),
                }

                # This would update user status in database
                logger.info(f"Service suspended for user {alert.user_id}")

                return {
                    "status": "service_suspended",
                    "suspension_data": suspension_data,
                }

            elif action == "log_security_event":
                # Log security event
                security_event = {
                    "user_id": alert.user_id,
                    "tenant_id": alert.tenant_id,
                    "event_type": alert.type.value,
                    "severity": alert.priority.value,
                    "description": alert.message,
                    "context": alert.context,
                    "alert_id": alert.id,
                }

                # This would log to security monitoring system
                logger.warning(f"Security event logged: {security_event}")

                return {"status": "security_event_logged", "event": security_event}

            else:
                logger.warning(f"Unknown action: {action}")
                return {"status": "unknown_action", "action": action}

        except Exception as e:
            logger.error(f"Failed to execute default action {action}: {e}")
            raise

    def _initialize_default_rules(self) -> List[AlertRule]:
        """Initialize default alert processing rules."""
        return [
            AlertRule(
                id=str(uuid.uuid4()),
                name="Application Success Notification",
                alert_type=AlertType.APPLICATION_SUCCESS,
                conditions={},
                actions=["send_notification"],
                priority=AlertPriority.MEDIUM,
                throttle_minutes=1,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="Application Failed Alert",
                alert_type=AlertType.APPLICATION_FAILED,
                conditions={},
                actions=["send_notification", "send_email"],
                priority=AlertPriority.HIGH,
                throttle_minutes=5,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="Rate Limit Warning",
                alert_type=AlertType.RATE_LIMIT_WARNING,
                conditions={},
                actions=["send_notification"],
                priority=AlertPriority.MEDIUM,
                throttle_minutes=30,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="Rate Limit Reached",
                alert_type=AlertType.RATE_LIMIT_REACHED,
                conditions={},
                actions=["send_notification", "send_email", "suspend_service"],
                priority=AlertPriority.HIGH,
                throttle_minutes=60,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="Security Alert",
                alert_type=AlertType.SECURITY_ALERT,
                conditions={},
                actions=["send_notification", "send_email", "log_security_event"],
                priority=AlertPriority.CRITICAL,
                throttle_minutes=1,
            ),
        ]

    async def _save_alert(self, alert: Alert) -> None:
        """Save alert to database."""
        try:
            query = """
                INSERT INTO alert_processing_log (
                    id, alert_type, priority, user_id, tenant_id, title,
                    message, data, context, status, processed_at, resolved_at,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    processed_at = EXCLUDED.processed_at,
                    resolved_at = EXCLUDED.resolved_at,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                alert.id,
                alert.type.value,
                alert.priority.value,
                alert.user_id,
                alert.tenant_id,
                alert.title,
                alert.message,
                alert.data,
                alert.context,
                alert.status,
                alert.processed_at,
                alert.resolved_at,
                alert.created_at,
                alert.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save alert: {e}")

    async def _update_alert(self, alert: Alert) -> None:
        """Update alert in database."""
        try:
            query = """
                UPDATE alert_processing_log
                SET status = $1, processed_at = $2, resolved_at = $3, updated_at = NOW()
                WHERE id = $4
            """

            params = [alert.status, alert.processed_at, alert.resolved_at, alert.id]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to update alert: {e}")

    async def _save_rule(self, rule: AlertRule) -> None:
        """Save rule to database."""
        try:
            query = """
                INSERT INTO alert_rules (
                    id, name, alert_type, conditions, actions, priority,
                    enabled, throttle_minutes, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    conditions = EXCLUDED.conditions,
                    actions = EXCLUDED.actions,
                    priority = EXCLUDED.priority,
                    enabled = EXCLUDED.enabled,
                    throttle_minutes = EXCLUDED.throttle_minutes,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                rule.id,
                rule.name,
                rule.alert_type.value,
                rule.conditions,
                rule.actions,
                rule.priority.value,
                rule.enabled,
                rule.throttle_minutes,
                rule.created_at,
                rule.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save rule: {e}")

    async def _log_processing(
        self,
        alert_id: str,
        rule_id: str,
        action: str,
        status: str,
        result: Dict[str, Any],
        error_message: Optional[str],
        processing_time_ms: int,
    ) -> None:
        """Log alert processing."""
        try:
            query = """
                INSERT INTO alert_processing_actions (
                    alert_id, rule_id, action, status, result, error_message,
                    processing_time_ms, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """

            params = [
                alert_id,
                rule_id,
                action,
                status,
                result,
                error_message,
                processing_time_ms,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to log processing: {e}")


# Factory function
def create_alert_processor(db_pool) -> AlertProcessor:
    """Create alert processor instance."""
    return AlertProcessor(db_pool)
