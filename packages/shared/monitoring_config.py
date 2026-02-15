"""
Monitoring Configuration for Production

Provides:
  - Alert threshold configuration
  - Notification channel configuration
  - Health check configuration
  - Integration points for external monitoring (PagerDuty, Datadog)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from shared.config import get_settings


class MonitoringProvider(Enum):
    INTERNAL = "internal"
    DATADOG = "datadog"
    PAGERDUTY = "pagerduty"
    GRAFANA = "grafana"
    NEW_RELIC = "new_relic"


@dataclass
class ThresholdConfig:
    """Configuration for alert thresholds."""

    error_rate_pct: float = 5.0
    error_rate_5xx_pct: float = 2.0
    latency_p99_ms: float = 1000.0
    latency_p95_ms: float = 500.0
    latency_p50_ms: float = 200.0
    db_connection_errors: int = 3
    circuit_breaker_open: int = 1
    rate_limit_usage_pct: float = 80.0
    queue_backlog: int = 100
    llm_timeout_rate_pct: float = 10.0
    memory_usage_pct: float = 85.0
    cpu_usage_pct: float = 80.0
    disk_usage_pct: float = 85.0


@dataclass
class WindowConfig:
    """Configuration for evaluation windows."""

    short_window_seconds: int = 60
    medium_window_seconds: int = 300
    long_window_seconds: int = 900
    extended_window_seconds: int = 3600


@dataclass
class CooldownConfig:
    """Configuration for alert cooldowns."""

    info_cooldown_seconds: int = 1800
    warning_cooldown_seconds: int = 900
    error_cooldown_seconds: int = 600
    critical_cooldown_seconds: int = 300


@dataclass
class NotificationConfig:
    """Configuration for notification channels."""

    enabled: bool = True
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    slack_username: str = "Sorce Alerts"

    email_enabled: bool = False
    email_recipients: list[str] = field(default_factory=list)
    email_from: str = "alerts@sorce.io"

    pagerduty_enabled: bool = False
    pagerduty_api_key: str = ""
    pagerduty_service_id: str = ""

    datadog_enabled: bool = False
    datadog_api_key: str = ""
    datadog_app_key: str = ""
    datadog_host: str = "api.datadoghq.com"


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""

    enabled: bool = True
    endpoint: str = "/healthz"
    interval_seconds: int = 30
    timeout_seconds: int = 10
    unhealthy_threshold: int = 3
    healthy_threshold: int = 2

    checks: dict[str, bool] = field(
        default_factory=lambda: {
            "database": True,
            "redis": True,
            "circuit_breakers": True,
            "memory": False,
            "disk": False,
        }
    )


@dataclass
class MetricsExportConfig:
    """Configuration for metrics export."""

    prometheus_enabled: bool = True
    prometheus_endpoint: str = "/metrics"
    prometheus_port: int = 9090

    otlp_enabled: bool = False
    otlp_endpoint: str = ""
    otlp_insecure: bool = True

    datadog_enabled: bool = False
    datadog_namespace: str = "sorce"

    custom_tags: dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Complete monitoring configuration."""

    provider: MonitoringProvider = MonitoringProvider.INTERNAL
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    windows: WindowConfig = field(default_factory=WindowConfig)
    cooldowns: CooldownConfig = field(default_factory=CooldownConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    metrics_export: MetricsExportConfig = field(default_factory=MetricsExportConfig)

    environment: str = "local"
    service_name: str = "sorce-api"
    service_version: str = "0.4.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider.value,
            "environment": self.environment,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "thresholds": {
                "error_rate_pct": self.thresholds.error_rate_pct,
                "error_rate_5xx_pct": self.thresholds.error_rate_5xx_pct,
                "latency_p99_ms": self.thresholds.latency_p99_ms,
                "latency_p95_ms": self.thresholds.latency_p95_ms,
                "latency_p50_ms": self.thresholds.latency_p50_ms,
                "db_connection_errors": self.thresholds.db_connection_errors,
                "circuit_breaker_open": self.thresholds.circuit_breaker_open,
                "rate_limit_usage_pct": self.thresholds.rate_limit_usage_pct,
                "queue_backlog": self.thresholds.queue_backlog,
                "llm_timeout_rate_pct": self.thresholds.llm_timeout_rate_pct,
            },
            "windows": {
                "short_seconds": self.windows.short_window_seconds,
                "medium_seconds": self.windows.medium_window_seconds,
                "long_seconds": self.windows.long_window_seconds,
            },
            "notifications": {
                "enabled": self.notifications.enabled,
                "slack_enabled": self.notifications.slack_enabled,
                "email_enabled": self.notifications.email_enabled,
                "pagerduty_enabled": self.notifications.pagerduty_enabled,
                "datadog_enabled": self.notifications.datadog_enabled,
            },
            "health_check": {
                "enabled": self.health_check.enabled,
                "endpoint": self.health_check.endpoint,
                "interval_seconds": self.health_check.interval_seconds,
            },
        }


def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring configuration from settings."""
    settings = get_settings()

    config = MonitoringConfig(
        environment=settings.env.value,
        service_name="sorce-api",
        service_version="0.4.0",
    )

    if settings.slack_webhook_url:
        config.notifications.slack_enabled = True
        config.notifications.slack_webhook_url = settings.slack_webhook_url
        config.notifications.slack_channel = settings.slack_ops_channel

    if settings.pagerduty_api_key and settings.pagerduty_service_id:
        config.notifications.pagerduty_enabled = True
        config.notifications.pagerduty_api_key = settings.pagerduty_api_key
        config.notifications.pagerduty_service_id = settings.pagerduty_service_id

    if settings.sentry_dsn:
        config.notifications.datadog_enabled = False

    if settings.env.value == "prod":
        config.notifications.enabled = True
        config.thresholds.error_rate_pct = 3.0
        config.thresholds.latency_p99_ms = 800.0
        config.cooldowns.critical_cooldown_seconds = 180

    return config


def setup_datadog_integration(config: MonitoringConfig) -> bool:
    """Setup Datadog integration if configured."""
    if not config.metrics_export.datadog_enabled:
        return False

    try:
        from datadog import initialize

        initialize(
            api_key=config.notifications.datadog_api_key,
            app_key=config.notifications.datadog_app_key,
            host=config.notifications.datadog_host,
        )

        return True
    except ImportError:
        return False
    except Exception:
        return False


def setup_pagerduty_integration(config: MonitoringConfig) -> bool:
    """Setup PagerDuty integration if configured."""
    if not config.notifications.pagerduty_enabled:
        return False

    if not config.notifications.pagerduty_api_key:
        return False

    return True


def get_alert_thresholds_for_datadog() -> dict[str, dict[str, Any]]:
    """Return alert thresholds formatted for Datadog monitors."""
    config = get_monitoring_config()

    return {
        "high_error_rate": {
            "query": "avg(last_5m):sum:sorce.requests.error{*} / sum:sorce.requests.total{*} * 100",
            "threshold": config.thresholds.error_rate_pct,
            "notify_no_data": True,
            "message": "Error rate has exceeded {{threshold}}% over the last 5 minutes.",
        },
        "high_latency_p99": {
            "query": "avg(last_5m):percentile:sorce.latency{*} by {endpoint}",
            "threshold": config.thresholds.latency_p99_ms,
            "notify_no_data": False,
            "message": "P99 latency has exceeded {{threshold}}ms.",
        },
        "database_errors": {
            "query": "sum:last_5m):sum:sorce.db.errors{*}.as_count()",
            "threshold": config.thresholds.db_connection_errors,
            "notify_no_data": False,
            "message": "Database connection errors detected.",
        },
        "circuit_breaker_open": {
            "query": "max:last_5m):sum:sorce.circuit_breaker.open{*}",
            "threshold": config.thresholds.circuit_breaker_open,
            "notify_no_data": False,
            "message": "Circuit breaker has tripped.",
        },
    }


def get_alert_thresholds_for_pagerduty() -> dict[str, dict[str, Any]]:
    """Return alert thresholds formatted for PagerDuty services."""
    config = get_monitoring_config()

    return {
        "high_error_rate": {
            "severity": "critical",
            "threshold": config.thresholds.error_rate_pct,
            "window_minutes": 5,
        },
        "high_latency_p99": {
            "severity": "warning",
            "threshold": config.thresholds.latency_p99_ms,
            "window_minutes": 5,
        },
        "database_errors": {
            "severity": "critical",
            "threshold": config.thresholds.db_connection_errors,
            "window_minutes": 5,
        },
        "circuit_breaker_open": {
            "severity": "error",
            "threshold": config.thresholds.circuit_breaker_open,
            "window_minutes": 1,
        },
    }
