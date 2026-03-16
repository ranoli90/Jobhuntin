"""SEO Alerting Module - Alert management for SEO engine.

Provides comprehensive alerting capabilities for SEO operations including
quota tracking, health monitoring, error rate alerts, and performance alerts.
Integrates with the existing alerting system (alert_processor.py and alerting_v2.py).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

import asyncpg

from packages.backend.domain.alert_processor import AlertPriority, AlertProcessor
from packages.backend.domain.alerting_v2 import (
    send_opsgenie_alert,
    send_pagerduty_event,
    send_slack_message,
)
from packages.backend.domain.seo_health import SEOHealthCheck
from packages.backend.domain.seo_logging import SEOLogger
from packages.backend.domain.seo_metrics import SEOMetricsCollector
from packages.backend.domain.seo_progress import SEOProgressRepository
from shared.logging_config import get_logger

logger = get_logger("sorce.seo_alerting")


# Alert configuration defaults
ERROR_RATE_THRESHOLD = 0.1  # 10% error rate threshold
PERFORMANCE_THRESHOLD_MS = 5000  # 5 second threshold
HEALTH_CHECK_INTERVAL_MINUTES = 60


class SEOAlertType(Enum):
    """SEO-specific alert types."""

    QUOTA_EXCEEDED = "quota_exceeded"
    HEALTH_CHECK_FAILED = "health_check_failed"
    ERROR_RATE_HIGH = "error_rate_high"
    CONTENT_GENERATION_FAILED = "content_generation_failed"
    SUBMISSION_FAILED = "submission_failed"
    PERFORMANCE_DEGRADED = "performance_degraded"


class SEOAlertSeverity(Enum):
    """Alert severity levels for SEO alerts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SEOAlertRule:
    """Alert rule for SEO-specific conditions."""

    id: str
    alert_type: SEOAlertType
    name: str
    description: str
    severity: SEOAlertSeverity
    enabled: bool = True
    threshold: float = 0.0
    throttle_minutes: int = 15
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SEOAlert:
    """SEO alert data structure."""

    id: str
    alert_type: SEOAlertType
    severity: SEOAlertSeverity
    service_id: str
    title: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, sent, failed, resolved
    sent_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SEOAlertManager:
    """Manager for SEO-specific alerts.

    Provides methods to check various SEO conditions and send alerts
    when thresholds are exceeded or issues are detected.
    """

    # Map SEO alert types to generic alert types for integration
    ALERT_TYPE_MAPPING = {
        SEOAlertType.QUOTA_EXCEEDED: "system_error",
        SEOAlertType.HEALTH_CHECK_FAILED: "system_error",
        SEOAlertType.ERROR_RATE_HIGH: "system_error",
        SEOAlertType.CONTENT_GENERATION_FAILED: "application_failed",
        SEOAlertType.SUBMISSION_FAILED: "application_failed",
        SEOAlertType.PERFORMANCE_DEGRADED: "system_error",
    }

    # Map SEO severity to generic priority
    SEVERITY_TO_PRIORITY = {
        SEOAlertSeverity.INFO: AlertPriority.LOW,
        SEOAlertSeverity.WARNING: AlertPriority.MEDIUM,
        SEOAlertSeverity.ERROR: AlertPriority.HIGH,
        SEOAlertSeverity.CRITICAL: AlertPriority.CRITICAL,
    }

    def __init__(self, conn: asyncpg.Connection) -> None:
        """Initialize the SEO alert manager.

        Args:
            conn: AsyncPG database connection.
        """
        self._conn = conn
        self._progress_repo = SEOProgressRepository(conn)
        self._metrics_collector = SEOMetricsCollector(conn)
        self._health_check = SEOHealthCheck(conn)
        self._logger = SEOLogger(conn)
        self._alert_processor: Optional[AlertProcessor] = None
        self._throttling: dict[str, datetime] = {}

    def set_alert_processor(self, processor: AlertProcessor) -> None:
        """Set the alert processor for integration.

        Args:
            processor: The alert processor instance.
        """
        self._alert_processor = processor
        logger.info("Alert processor configured for SEO alerting")

    async def check_and_alert(self, service_id: str) -> list[SEOAlert]:
        """Run all alert checks for a service.

        Args:
            service_id: The service identifier to check.

        Returns:
            List of alerts that were triggered.
        """
        alerts = []

        # Check quota alert
        quota_alert = await self.check_quota_alert(service_id)
        if quota_alert:
            alerts.append(quota_alert)

        # Check error rate alert
        error_rate_alert = await self.check_error_rate_alert(service_id)
        if error_rate_alert:
            alerts.append(error_rate_alert)

        # Check performance alert
        performance_alert = await self.check_performance_alert(service_id)
        if performance_alert:
            alerts.append(performance_alert)

        # Check health alert
        health_alert = await self.check_health_alert()
        if health_alert:
            alerts.append(health_alert)

        logger.info(
            "Completed alert checks for service",
            extra={
                "service_id": service_id,
                "alerts_triggered": len(alerts),
            },
        )

        return alerts

    async def check_quota_alert(self, service_id: str) -> Optional[SEOAlert]:
        """Check if quota has been exceeded for a service.

        Args:
            service_id: The service identifier to check.

        Returns:
            SEOAlert if quota exceeded, None otherwise.
        """
        try:
            progress = await self._progress_repo.get_progress(service_id)
            if not progress:
                return None

            daily_quota_used = progress.get("daily_quota_used", 0)
            daily_quota_reset = progress.get("daily_quota_reset")

            if daily_quota_reset:
                reset_time = datetime.fromisoformat(daily_quota_reset)
                now = datetime.now(timezone.utc)

                # Check if quota is exhausted (using default 1000 as threshold)
                if daily_quota_used >= 1000:
                    # Check if we should throttle this alert
                    throttle_key = f"quota_{service_id}"
                    if self._is_throttled(throttle_key, 60):  # Throttle for 60 minutes
                        return None

                    alert = await self.send_alert(
                        alert_type=SEOAlertType.QUOTA_EXCEEDED,
                        message=f"Daily quota exhausted for service {service_id}. Used: {daily_quota_used}/1000",
                        severity=SEOAlertSeverity.WARNING,
                        metadata={
                            "service_id": service_id,
                            "quota_used": daily_quota_used,
                            "quota_limit": 1000,
                            "reset_time": daily_quota_reset,
                        },
                    )
                    return alert

            return None
        except Exception as e:
            logger.error(
                "Failed to check quota alert",
                extra={"service_id": service_id, "error": str(e)},
            )
            return None

    async def check_health_alert(self) -> Optional[SEOAlert]:
        """Check overall health status of the SEO engine.

        Returns:
            SEOAlert if health check failed, None otherwise.
        """
        try:
            # Check database connection
            db_health = await self._health_check.check_database_connection()
            if db_health.get("status") != "healthy":
                throttle_key = "health_database"
                if self._is_throttled(throttle_key, HEALTH_CHECK_INTERVAL_MINUTES):
                    return None

                alert = await self.send_alert(
                    alert_type=SEOAlertType.HEALTH_CHECK_FAILED,
                    message=f"SEO Health Check Failed: {db_health.get('message', 'Unknown error')}",
                    severity=SEOAlertSeverity.CRITICAL,
                    metadata={
                        "check_name": "database_connection",
                        "status": db_health.get("status"),
                        "message": db_health.get("message"),
                        "timestamp": db_health.get("timestamp"),
                    },
                )
                return alert

            # Check SEO tables exist
            tables_health = await self._health_check.check_tables_exist()
            if tables_health.get("status") != "healthy":
                throttle_key = "health_tables"
                if self._is_throttled(throttle_key, HEALTH_CHECK_INTERVAL_MINUTES):
                    return None

                alert = await self.send_alert(
                    alert_type=SEOAlertType.HEALTH_CHECK_FAILED,
                    message=f"SEO Tables Check Failed: {tables_health.get('message', 'Unknown error')}",
                    severity=SEOAlertSeverity.CRITICAL,
                    metadata={
                        "check_name": "tables_exist",
                        "status": tables_health.get("status"),
                        "message": tables_health.get("message"),
                    },
                )
                return alert

            return None
        except Exception as e:
            logger.error(
                "Failed to check health alert",
                extra={"error": str(e)},
            )
            return None

    async def check_error_rate_alert(
        self, service_id: str, hours: int = 24
    ) -> Optional[SEOAlert]:
        """Check error rate for a service in the specified time window.

        Args:
            service_id: The service identifier to check.
            hours: Time window in hours (default 24).

        Returns:
            SEOAlert if error rate exceeds threshold, None otherwise.
        """
        try:
            # Get error logs for the time period
            error_count = await self._get_error_count(service_id, hours)
            total_count = await self._get_log_count(service_id, hours)

            if total_count == 0:
                return None

            error_rate = error_count / total_count

            if error_rate >= ERROR_RATE_THRESHOLD:
                # Check throttling
                throttle_key = f"error_rate_{service_id}"
                if self._is_throttled(throttle_key, 60):
                    return None

                severity = (
                    SEOAlertSeverity.CRITICAL
                    if error_rate >= 0.25
                    else SEOAlertSeverity.ERROR
                )

                alert = await self.send_alert(
                    alert_type=SEOAlertType.ERROR_RATE_HIGH,
                    message=f"High error rate for service {service_id}: {error_rate:.1%} ({error_count}/{total_count} errors in {hours}h)",
                    severity=severity,
                    metadata={
                        "service_id": service_id,
                        "error_count": error_count,
                        "total_count": total_count,
                        "error_rate": error_rate,
                        "threshold": ERROR_RATE_THRESHOLD,
                        "time_window_hours": hours,
                    },
                )
                return alert

            return None
        except Exception as e:
            logger.error(
                "Failed to check error rate alert",
                extra={"service_id": service_id, "error": str(e)},
            )
            return None

    async def check_performance_alert(self, service_id: str) -> Optional[SEOAlert]:
        """Check performance metrics for a service.

        Args:
            service_id: The service identifier to check.

        Returns:
            SEOAlert if performance is degraded, None otherwise.
        """
        try:
            # Get recent performance data from database directly
            metrics_row = await self._conn.fetchrow(
                """
                SELECT average_generation_time_ms, average_submission_time_ms
                FROM seo_metrics
                ORDER BY created_at DESC
                LIMIT 1
                """
            )

            if not metrics_row:
                return None

            avg_generation_time = metrics_row.get("average_generation_time_ms", 0) or 0
            avg_submission_time = metrics_row.get("average_submission_time_ms", 0) or 0

            # Check generation time
            if avg_generation_time >= PERFORMANCE_THRESHOLD_MS:
                throttle_key = f"performance_gen_{service_id}"
                if self._is_throttled(throttle_key, 60):
                    return None

                severity = (
                    SEOAlertSeverity.CRITICAL
                    if avg_generation_time >= PERFORMANCE_THRESHOLD_MS * 2
                    else SEOAlertSeverity.WARNING
                )

                alert = await self.send_alert(
                    alert_type=SEOAlertType.PERFORMANCE_DEGRADED,
                    message=f"Content generation performance degraded for {service_id}: {avg_generation_time}ms",
                    severity=severity,
                    metadata={
                        "service_id": service_id,
                        "average_generation_time_ms": avg_generation_time,
                        "threshold_ms": PERFORMANCE_THRESHOLD_MS,
                        "metric_type": "generation_time",
                    },
                )
                return alert

            # Check submission time
            if avg_submission_time >= PERFORMANCE_THRESHOLD_MS:
                throttle_key = f"performance_sub_{service_id}"
                if self._is_throttled(throttle_key, 60):
                    return None

                severity = (
                    SEOAlertSeverity.CRITICAL
                    if avg_submission_time >= PERFORMANCE_THRESHOLD_MS * 2
                    else SEOAlertSeverity.WARNING
                )

                alert = await self.send_alert(
                    alert_type=SEOAlertType.PERFORMANCE_DEGRADED,
                    message=f"Submission performance degraded for {service_id}: {avg_submission_time}ms",
                    severity=severity,
                    metadata={
                        "service_id": service_id,
                        "average_submission_time_ms": avg_submission_time,
                        "threshold_ms": PERFORMANCE_THRESHOLD_MS,
                        "metric_type": "submission_time",
                    },
                )
                return alert

            return None
        except Exception as e:
            logger.error(
                "Failed to check performance alert",
                extra={"service_id": service_id, "error": str(e)},
            )
            return None

    async def send_alert(
        self,
        alert_type: SEOAlertType,
        message: str,
        severity: SEOAlertSeverity,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SEOAlert:
        """Send an SEO alert notification.

        Creates an alert and sends it through all configured channels
        (PagerDuty, Opsgenie, Slack) based on severity level.

        Args:
            alert_type: The type of SEO alert.
            message: The alert message.
            severity: The severity level of the alert.
            metadata: Additional metadata for the alert.

        Returns:
            The created SEOAlert.
        """
        alert = SEOAlert(
            id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            service_id=metadata.get("service_id", "unknown") if metadata else "unknown",
            title=f"SEO Alert: {alert_type.value.replace('_', ' ').title()}",
            message=message,
            metadata=metadata or {},
        )

        try:
            # Log the alert to SEO logs
            await self._logger.log(
                level="error" if severity in (SEOAlertSeverity.ERROR, SEOAlertSeverity.CRITICAL) else "warn",
                message=f"SEO Alert: {message}",
                meta=alert_type.value,
            )

            # Send to integrated alerting system if available
            if self._alert_processor:
                await self._send_to_alert_processor(alert)

            # Send to external services based on severity
            await self._send_to_external_services(alert)

            # Update alert status
            alert.status = "sent"
            alert.sent_at = datetime.now(timezone.utc)

            logger.info(
                "SEO alert sent",
                extra={
                    "alert_id": alert.id,
                    "alert_type": alert_type.value,
                    "severity": severity.value,
                    "service_id": alert.service_id,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to send SEO alert",
                extra={
                    "alert_id": alert.id,
                    "alert_type": alert_type.value,
                    "error": str(e),
                },
            )
            alert.status = "failed"

        return alert

    async def _send_to_alert_processor(self, alert: SEOAlert) -> None:
        """Send alert to the integrated alert processor.

        Args:
            alert: The SEOAlert to process.
        """
        try:
            generic_type = self.ALERT_TYPE_MAPPING.get(
                alert.alert_type, "system_error"
            )
            priority = self.SEVERITY_TO_PRIORITY.get(alert.severity, AlertPriority.MEDIUM)

            alert_data = {
                "type": generic_type,
                "priority": priority.value,
                "title": alert.title,
                "message": alert.message,
                "data": alert.metadata,
                "context": {
                    "alert_id": alert.id,
                    "seo_alert_type": alert.alert_type.value,
                    "seo_severity": alert.severity.value,
                },
            }

            await self._alert_processor.process_alert(alert_data)
        except Exception as e:
            logger.warning(
                "Failed to send alert to alert processor",
                extra={"alert_id": alert.id, "error": str(e)},
            )

    async def _send_to_external_services(self, alert: SEOAlert) -> None:
        """Send alert to external alerting services.

        Args:
            alert: The SEOAlert to send.
        """
        severity = alert.severity.value

        # Map SEO severity to PagerDuty severity
        pd_severity = "warning"
        if severity == "critical":
            pd_severity = "critical"
        elif severity == "error":
            pd_severity = "error"
        elif severity == "info":
            pd_severity = "info"

        # Send to PagerDuty for critical and error alerts
        if severity in ("critical", "error"):
            await send_pagerduty_event(
                summary=f"[SEO] {alert.title}: {alert.message}",
                severity=pd_severity,
                source="sorce-seo-engine",
                details={
                    "alert_id": alert.id,
                    "alert_type": alert.alert_type.value,
                    "service_id": alert.service_id,
                    **alert.metadata,
                },
            )

        # Send to Opsgenie based on severity
        opsgenie_priority = "P3"  # Default to moderate
        if severity == "critical":
            opsgenie_priority = "P1"
        elif severity == "error":
            opsgenie_priority = "P2"
        elif severity == "info":
            opsgenie_priority = "P4"

        if severity in ("critical", "error", "warning"):
            await send_opsgenie_alert(
                message=f"[SEO] {alert.title}",
                alias=f"seo-alert-{alert.id}",
                description=alert.message,
                priority=opsgenie_priority,
                tags=["seo", alert.alert_type.value],
                details={
                    "alert_id": alert.id,
                    "service_id": alert.service_id,
                    **alert.metadata,
                },
            )

        # Always send to Slack for all severity levels
        emoji = "ℹ️"
        if severity == "warning":
            emoji = "⚠️"
        elif severity == "error":
            emoji = "❌"
        elif severity == "critical":
            emoji = "🚨"

        slack_text = f"{emoji} *SEO {severity.upper()}*: {alert.title}\n{alert.message}"
        await send_slack_message(text=slack_text)

    async def _get_error_count(self, service_id: str, hours: int) -> int:
        """Get the count of error logs for a service.

        Args:
            service_id: The service identifier.
            hours: Time window in hours.

        Returns:
            Number of error logs.
        """
        try:
            result = await self._conn.fetchval(
                """
                SELECT COUNT(*)
                FROM seo_logs
                WHERE level = 'error'
                  AND created_at >= NOW() - INTERVAL '1 hour' * $1
                  AND ($2::text IS NULL OR meta->>'service_id' = $2)
                """,
                hours,
                service_id,
            )
            return result or 0
        except Exception as e:
            logger.error(
                "Failed to get error count",
                extra={"service_id": service_id, "error": str(e)},
            )
            return 0

    async def _get_log_count(self, service_id: str, hours: int) -> int:
        """Get the total count of logs for a service.

        Args:
            service_id: The service identifier.
            hours: Time window in hours.

        Returns:
            Total number of logs.
        """
        try:
            result = await self._conn.fetchval(
                """
                SELECT COUNT(*)
                FROM seo_logs
                WHERE created_at >= NOW() - INTERVAL '1 hour' * $1
                  AND ($2::text IS NULL OR meta->>'service_id' = $2)
                """,
                hours,
                service_id,
            )
            return result or 0
        except Exception as e:
            logger.error(
                "Failed to get log count",
                extra={"service_id": service_id, "error": str(e)},
            )
            return 0

    def _is_throttled(self, key: str, throttle_minutes: int) -> bool:
        """Check if an alert should be throttled.

        Args:
            key: The throttle key.
            throttle_minutes: Minutes to throttle.

        Returns:
            True if throttled, False otherwise.
        """
        if key in self._throttling:
            last_alert = self._throttling[key]
            throttle_time = datetime.now(timezone.utc) - timedelta(
                minutes=throttle_minutes
            )
            if last_alert > throttle_time:
                return True

        self._throttling[key] = datetime.now(timezone.utc)
        return False

    async def get_alert_history(
        self,
        service_id: Optional[str] = None,
        alert_type: Optional[SEOAlertType] = None,
        severity: Optional[SEOAlertSeverity] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get alert history with optional filtering.

        Args:
            service_id: Filter by service ID.
            alert_type: Filter by alert type.
            severity: Filter by severity.
            limit: Maximum number of results.

        Returns:
            List of alert history records.
        """
        try:
            query = """
                SELECT id, service_id, title, message, severity, alert_type,
                       metadata, status, created_at, sent_at, resolved_at
                FROM seo_alerts
                WHERE 1=1
            """
            params: list[Any] = []
            param_count = 0

            if service_id:
                param_count += 1
                query += f" AND service_id = ${param_count}"
                params.append(service_id)

            if alert_type:
                param_count += 1
                query += f" AND alert_type = ${param_count}"
                params.append(alert_type.value)

            if severity:
                param_count += 1
                query += f" AND severity = ${param_count}"
                params.append(severity.value)

            query += f" ORDER BY created_at DESC LIMIT {limit}"

            rows = await self._conn.fetch(query, *params)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(
                "Failed to get alert history",
                extra={"error": str(e)},
            )
            return []

    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved.

        Args:
            alert_id: The alert ID to resolve.

        Returns:
            True if resolved successfully, False otherwise.
        """
        try:
            await self._conn.execute(
                """
                UPDATE seo_alerts
                SET status = 'resolved',
                    resolved_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                """,
                alert_id,
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to resolve alert",
                extra={"alert_id": alert_id, "error": str(e)},
            )
            return False
