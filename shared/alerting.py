"""Alerting System for Production Monitoring.

Provides:
  - AlertRule dataclass for defining alert conditions
  - AlertManager for managing alerts with threshold-based evaluation
  - Sliding window evaluation for rate-based alerts
  - Alert deduplication and cooldown periods
  - Multi-channel notification support (email, Slack webhook)
  - Built-in alert rules for common conditions
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from shared.logging_config import get_logger

logger = get_logger("sorce.alerting")

# Define UTC constant for Python < 3.12 compatibility
UTC = timezone.utc


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class AlertRule:
    """Defines an alert condition with evaluation logic."""

    name: str
    description: str
    severity: AlertSeverity
    window_seconds: int = 300
    threshold: float = 0.0
    comparison: str = "gt"
    cooldown_seconds: int = 300
    enabled: bool = True
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    def evaluate(self, value: float) -> bool:
        """Check if the value triggers this alert."""
        if not self.enabled:
            return False
        if self.comparison == "gt":
            return value > self.threshold
        elif self.comparison == "gte":
            return value >= self.threshold
        elif self.comparison == "lt":
            return value < self.threshold
        elif self.comparison == "lte":
            return value <= self.threshold
        elif self.comparison == "eq":
            return value == self.threshold
        elif self.comparison == "neq":
            return value != self.threshold
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "window_seconds": self.window_seconds,
            "threshold": self.threshold,
            "comparison": self.comparison,
            "cooldown_seconds": self.cooldown_seconds,
            "enabled": self.enabled,
            "labels": self.labels,
            "annotations": self.annotations,
        }


@dataclass
class Alert:
    """Represents an active or historical alert."""

    id: str
    rule_name: str
    status: AlertStatus
    severity: AlertSeverity
    value: float
    threshold: float
    message: str
    labels: dict[str, str]
    fired_at: float
    resolved_at: float | None = None
    acknowledged_at: float | None = None
    acknowledged_by: str | None = None
    notification_sent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "status": self.status.value,
            "severity": self.severity.value,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "labels": self.labels,
            "fired_at": (
                datetime.fromtimestamp(self.fired_at, timezone.utc).isoformat()
                if self.fired_at
                else None
            ),
            "resolved_at": (
                datetime.fromtimestamp(self.resolved_at, timezone.utc).isoformat()
                if self.resolved_at
                else None
            ),
            "acknowledged_at": (
                datetime.fromtimestamp(self.acknowledged_at, timezone.utc).isoformat()
                if self.acknowledged_at
                else None
            ),
            "acknowledged_by": self.acknowledged_by,
            "notification_sent": self.notification_sent,
        }


@dataclass
class MetricSample:
    """A single metric sample for sliding window calculation."""

    value: float
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)


class NotificationChannel:
    """Base class for notification channels."""

    async def send(self, alert: Alert, rule: AlertRule) -> bool:
        raise NotImplementedError


class SlackWebhookChannel(NotificationChannel):
    """Sends alerts to Slack via webhook."""

    def __init__(self, webhook_url: str, channel: str | None = None):
        self.webhook_url = webhook_url
        self.channel = channel

    async def send(self, alert: Alert, rule: AlertRule) -> bool:
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        severity_colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.ERROR: "#ff6600",
            AlertSeverity.CRITICAL: "#ff0000",
        }

        payload = {
            "attachments": [
                {
                    "color": severity_colors.get(alert.severity, "#808080"),
                    "title": f"[{alert.severity.value.upper()}] {rule.name}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Value",
                            "value": f"{alert.value:.2f}",
                            "short": True,
                        },
                        {
                            "title": "Threshold",
                            "value": f"{alert.threshold:.2f}",
                            "short": True,
                        },
                        {"title": "Status", "value": alert.status.value, "short": True},
                        {
                            "title": "Time",
                            "value": datetime.fromtimestamp(
                                alert.fired_at, timezone.utc
                            ).isoformat(),
                            "short": False,
                        },
                    ],
                    "footer": "Sorce Alerting",
                    "footer_icon": "https://sorce.app/favicon.ico",
                }
            ]
        }

        if self.channel:
            payload["channel"] = self.channel

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info("Alert %s sent to Slack", alert.id)
                        return True
                    else:
                        logger.error(
                            "Failed to send alert to Slack: %s", await resp.text()
                        )
                        return False
        except Exception as e:
            logger.error("Error sending alert to Slack: %s", e)
            return False


class EmailChannel(NotificationChannel):
    """Sends alerts via email (uses Resend API)."""

    def __init__(self, recipients: list[str], from_address: str = "alerts@sorce.app"):
        self.recipients = recipients
        self.from_address = from_address

    async def send(self, alert: Alert, rule: AlertRule) -> bool:
        if not self.recipients:
            logger.warning("No email recipients configured")
            return False

        subject = f"[{alert.severity.value.upper()}] {rule.name}"
        body = f"""
Alert: {rule.name}
Severity: {alert.severity.value}
Status: {alert.status.value}

{alert.message}

Details:
- Current Value: {alert.value:.2f}
- Threshold: {alert.threshold:.2f}
- Time: {datetime.fromtimestamp(alert.fired_at, timezone.utc).isoformat()}

Labels: {json.dumps(alert.labels, indent=2)}
"""
        try:
            from shared.config import get_settings

            settings = get_settings()
            if not settings.resend_api_key:
                logger.warning("Resend API key not configured for email alerts")
                return False

            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                    json={
                        "from": self.from_address,
                        "to": self.recipients,
                        "subject": subject,
                        "text": body,
                    },
                ) as resp:
                    if resp.status == 200:
                        logger.info("Alert %s sent via email", alert.id)
                        return True
                    else:
                        logger.error(
                            "Failed to send alert email: %s", await resp.text()
                        )
                        return False
        except Exception as e:
            logger.error("Error sending alert email: %s", e)
            return False


class AlertManager:
    """Manages alert rules, evaluation, and notifications.

    Features:
    - Threshold-based alert evaluation
    - Sliding window metrics for rate calculations
    - Alert deduplication via fingerprinting
    - Cooldown periods to prevent alert storms
    - Multi-channel notifications
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rules: dict[str, AlertRule] = {}
        self._active_alerts: dict[str, Alert] = {}
        self._alert_history: list[Alert] = []
        self._cooldowns: dict[str, float] = {}
        self._notification_channels: list[NotificationChannel] = []
        self._metric_samples: dict[str, list[MetricSample]] = defaultdict(list)
        self._max_history: int = 1000
        self._max_samples: int = 10000

    def add_rule(self, rule: AlertRule) -> None:
        """Register an alert rule."""
        with self._lock:
            self._rules[rule.name] = rule
        logger.info("Added alert rule: %s", rule.name)

    def remove_rule(self, rule_name: str) -> None:
        """Remove an alert rule."""
        with self._lock:
            self._rules.pop(rule_name, None)

    def add_notification_channel(self, channel: NotificationChannel) -> None:
        """Add a notification channel."""
        self._notification_channels.append(channel)

    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record a metric sample for sliding window evaluation."""
        sample = MetricSample(
            value=value,
            timestamp=time.time(),
            tags=tags or {},
        )
        with self._lock:
            samples = self._metric_samples[metric_name]
            samples.append(sample)
            if len(samples) > self._max_samples:
                self._metric_samples[metric_name] = samples[-self._max_samples // 2 :]

    def get_window_stats(
        self,
        metric_name: str,
        window_seconds: int,
    ) -> dict[str, float]:
        """Get statistics for a metric over a sliding window."""
        cutoff = time.time() - window_seconds
        with self._lock:
            samples = self._metric_samples.get(metric_name, [])
            recent = [s for s in samples if s.timestamp >= cutoff]

        if not recent:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0, "rate": 0}

        values = [s.value for s in recent]
        total = sum(values)
        count = len(values)
        return {
            "count": count,
            "sum": total,
            "avg": total / count,
            "min": min(values),
            "max": max(values),
            "rate": count / window_seconds if window_seconds > 0 else 0,
        }

    def _generate_alert_id(self, rule: AlertRule, labels: dict[str, str]) -> str:
        """Generate a unique ID for deduplication."""
        key = f"{rule.name}:{json.dumps(sorted(labels.items()), sort_keys=True)}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _is_in_cooldown(self, rule: AlertRule, alert_id: str) -> bool:
        """Check if an alert is in cooldown period."""
        last_fired = self._cooldowns.get(alert_id, 0)
        return time.time() - last_fired < rule.cooldown_seconds

    def evaluate_rules(self) -> list[Alert]:
        """Evaluate all rules and return new/updated alerts."""
        new_alerts: list[Alert] = []

        with self._lock:
            rules_copy = dict(self._rules)

        for rule_name, rule in rules_copy.items():
            if not rule.enabled:
                continue

            metric_name = rule.labels.get("metric", rule_name)
            stats = self.get_window_stats(metric_name, rule.window_seconds)

            value = stats.get(rule.labels.get("stat", "avg"), 0)
            labels = {**rule.labels, "metric": metric_name}
            alert_id = self._generate_alert_id(rule, labels)

            should_fire = rule.evaluate(value)

            with self._lock:
                existing_alert = self._active_alerts.get(alert_id)

                if should_fire:
                    if existing_alert and existing_alert.status == AlertStatus.FIRING:
                        continue

                    if self._is_in_cooldown(rule, alert_id):
                        continue

                    alert = Alert(
                        id=alert_id,
                        rule_name=rule.name,
                        status=AlertStatus.FIRING,
                        severity=rule.severity,
                        value=value,
                        threshold=rule.threshold,
                        message=f"{rule.description} (current: {value:.2f}, threshold: {rule.threshold:.2f})",
                        labels=labels,
                        fired_at=time.time(),
                    )

                    self._active_alerts[alert_id] = alert
                    self._cooldowns[alert_id] = time.time()
                    self._add_to_history(alert)
                    new_alerts.append(alert)

                elif existing_alert and existing_alert.status == AlertStatus.FIRING:
                    existing_alert.status = AlertStatus.RESOLVED
                    existing_alert.resolved_at = time.time()
                    self._add_to_history(existing_alert)
                    del self._active_alerts[alert_id]

        return new_alerts

    def _add_to_history(self, alert: Alert) -> None:
        """Add alert to history with size limit."""
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history // 2 :]

    async def send_notifications(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert to all notification channels."""
        for channel in self._notification_channels:
            try:
                await channel.send(alert, rule)
            except Exception as e:
                logger.error(
                    "Failed to send notification via %s: %s", type(channel).__name__, e
                )

        with self._lock:
            if alert.id in self._active_alerts:
                self._active_alerts[alert.id].notification_sent = True

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Alert | None:
        """Acknowledge an active alert."""
        with self._lock:
            alert = self._active_alerts.get(alert_id)
            if alert:
                alert.acknowledged_at = time.time()
                alert.acknowledged_by = acknowledged_by
                return alert
        return None

    def get_active_alerts(self) -> list[Alert]:
        """Get all currently active alerts."""
        with self._lock:
            return list(self._active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> list[Alert]:
        """Get recent alert history."""
        with self._lock:
            return list(self._alert_history[-limit:])

    def get_rules(self) -> list[AlertRule]:
        """Get all registered rules."""
        with self._lock:
            return list(self._rules.values())

    def run_evaluation_loop(self, interval_seconds: int = 30) -> None:
        """Run periodic evaluation loop (call from background task)."""

        async def _loop():
            while True:
                try:
                    new_alerts = self.evaluate_rules()
                    for alert in new_alerts:
                        rule = self._rules.get(alert.rule_name)
                        if rule:
                            await self.send_notifications(alert, rule)
                except Exception as e:
                    logger.error("Error in alert evaluation loop: %s", e)
                await asyncio.sleep(interval_seconds)

        return _loop


_alert_manager: AlertManager | None = None
_alert_manager_lock = threading.Lock()


def get_alert_manager() -> AlertManager:
    """Get or create the singleton AlertManager instance."""
    global _alert_manager
    with _alert_manager_lock:
        if _alert_manager is None:
            _alert_manager = AlertManager()
            _register_builtin_rules(_alert_manager)
        return _alert_manager


def _register_builtin_rules(manager: AlertManager) -> None:
    """Register built-in alert rules."""
    manager.add_rule(
        AlertRule(
            name="high_error_rate",
            description="Error rate exceeds 5% in the last 5 minutes",
            severity=AlertSeverity.ERROR,
            window_seconds=300,
            threshold=5.0,
            comparison="gt",
            cooldown_seconds=300,
            labels={"metric": "error_rate", "stat": "avg"},
            annotations={"runbook": "https://docs.sorce.app/runbooks/high-error-rate"},
        )
    )

    manager.add_rule(
        AlertRule(
            name="high_latency_p99",
            description="P99 latency exceeds 1 second",
            severity=AlertSeverity.WARNING,
            window_seconds=300,
            threshold=1000.0,
            comparison="gt",
            cooldown_seconds=300,
            labels={"metric": "latency_p99", "stat": "max"},
            annotations={"runbook": "https://docs.sorce.app/runbooks/high-latency"},
        )
    )

    manager.add_rule(
        AlertRule(
            name="database_connection_failure",
            description="Database connection failures detected",
            severity=AlertSeverity.CRITICAL,
            window_seconds=60,
            threshold=0,
            comparison="gt",
            cooldown_seconds=180,
            labels={"metric": "db_connection_errors", "stat": "count"},
            annotations={"runbook": "https://docs.sorce.app/runbooks/db-connection"},
        )
    )

    manager.add_rule(
        AlertRule(
            name="circuit_breaker_trip",
            description="Circuit breaker has opened",
            severity=AlertSeverity.ERROR,
            window_seconds=60,
            threshold=0,
            comparison="gt",
            cooldown_seconds=300,
            labels={"metric": "circuit_breaker_open", "stat": "count"},
            annotations={"runbook": "https://docs.sorce.app/runbooks/circuit-breaker"},
        )
    )

    manager.add_rule(
        AlertRule(
            name="rate_limit_threshold",
            description="Rate limit usage exceeds 80% of limit",
            severity=AlertSeverity.WARNING,
            window_seconds=60,
            threshold=80.0,
            comparison="gt",
            cooldown_seconds=600,
            labels={"metric": "rate_limit_usage_pct", "stat": "avg"},
            annotations={"runbook": "https://docs.sorce.app/runbooks/rate-limit"},
        )
    )


def setup_alerting_notifications(
    slack_webhook_url: str | None = None,
    slack_channel: str | None = None,
    email_recipients: list[str] | None = None,
) -> None:
    """Configure notification channels for the alert manager."""
    manager = get_alert_manager()

    if slack_webhook_url:
        manager.add_notification_channel(
            SlackWebhookChannel(slack_webhook_url, slack_channel)
        )
        logger.info("Slack notification channel configured")

    if email_recipients:
        manager.add_notification_channel(EmailChannel(email_recipients))
        logger.info(
            "Email notification channel configured with %d recipients",
            len(email_recipients),
        )
