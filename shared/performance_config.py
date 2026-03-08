"""
Performance Configuration for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from shared.logging_config import get_logger

logger = get_logger("sorce.performance_config")


class PerformanceLevel(Enum):
    """Performance levels for configuration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class MetricType(Enum):
    """Types of performance metrics."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    APPLICATION = "application"
    CACHE = "cache"


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""

    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    comparison_operator: str = "gt"
    enabled: bool = True
    cooldown_period_minutes: int = 5


@dataclass
class PerformanceSettings:
    """Performance settings configuration."""

    level: PerformanceLevel
    monitoring_interval_seconds: int
    alerting_enabled: bool
    auto_optimization_enabled: bool
    retention_days: int
    thresholds: Dict[str, PerformanceThreshold] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class PerformanceConfig:
    """Advanced performance configuration manager."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "performance_config.json"
        self._settings: Dict[str, PerformanceSettings] = {}
        self._default_thresholds = self._initialize_default_thresholds()
        self._performance_levels = self._initialize_performance_levels()

        # Load configuration
        self._load_configuration()

    def get_settings(self, tenant_id: str) -> PerformanceSettings:
        """Get performance settings for a tenant."""
        try:
            if tenant_id not in self._settings:
                return self._get_default_settings()

            return self._settings[tenant_id]

        except Exception as e:
            logger.error(f"Failed to get settings for tenant {tenant_id}: {e}")
            return self._get_default_settings()

    def update_settings(self, tenant_id: str, settings: PerformanceSettings) -> bool:
        """Update performance settings for a tenant."""
        try:
            self._settings[tenant_id] = settings
            self._save_configuration()

            logger.info(f"Updated performance settings for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update settings for tenant {tenant_id}: {e}")
            return False

    def get_threshold(
        self, tenant_id: str, metric_name: str
    ) -> Optional[PerformanceThreshold]:
        """Get threshold for a specific metric."""
        try:
            settings = self.get_settings(tenant_id)
            return settings.thresholds.get(metric_name)

        except Exception as e:
            logger.error(f"Failed to get threshold for {metric_name}: {e}")
            return None

    def set_threshold(
        self,
        tenant_id: str,
        metric_name: str,
        threshold: PerformanceThreshold,
    ) -> bool:
        """Set threshold for a specific metric."""
        try:
            settings = self.get_settings(tenant_id)
            settings.thresholds[metric_name] = threshold

            return self.update_settings(tenant_id, settings)

        except Exception as e:
            logger.error(f"Failed to set threshold for {metric_name}: {e}")
            return False

    def get_performance_level_config(self, level: PerformanceLevel) -> Dict[str, Any]:
        """Get configuration for a performance level."""
        try:
            return self._performance_levels.get(level.value, {})

        except Exception as e:
            logger.error(f"Failed to get performance level config for {level}: {e}")
            return {}

    def calculate_optimal_settings(
        self,
        tenant_id: str,
        system_resources: Dict[str, Any],
        workload_characteristics: Dict[str, Any],
    ) -> PerformanceSettings:
        """Calculate optimal performance settings based on system and workload."""
        try:
            # Determine performance level based on resources and workload
            level = self._determine_performance_level(
                system_resources, workload_characteristics
            )

            # Get base settings for the level
            level_config = self.get_performance_level_config(level)

            # Customize settings based on workload
            customized_settings = self._customize_settings(
                level_config, system_resources, workload_characteristics
            )

            # Create performance settings
            settings = PerformanceSettings(
                level=level,
                monitoring_interval_seconds=customized_settings.get(
                    "monitoring_interval", 60
                ),
                alerting_enabled=customized_settings.get("alerting_enabled", True),
                auto_optimization_enabled=customized_settings.get(
                    "auto_optimization", False
                ),
                retention_days=customized_settings.get("retention_days", 30),
                thresholds=self._calculate_optimal_thresholds(
                    system_resources, workload_characteristics
                ),
                custom_settings=customized_settings,
            )

            return settings

        except Exception as e:
            logger.error(f"Failed to calculate optimal settings: {e}")
            return self._get_default_settings()

    def validate_settings(self, settings: PerformanceSettings) -> List[str]:
        """Validate performance settings."""
        try:
            errors = []

            # Validate monitoring interval
            if settings.monitoring_interval_seconds < 10:
                errors.append("Monitoring interval must be at least 10 seconds")
            elif settings.monitoring_interval_seconds > 3600:
                errors.append("Monitoring interval cannot exceed 1 hour")

            # Validate retention period
            if settings.retention_days < 1:
                errors.append("Retention period must be at least 1 day")
            elif settings.retention_days > 365:
                errors.append("Retention period cannot exceed 365 days")

            # Validate thresholds
            for metric_name, threshold in settings.thresholds.items():
                if threshold.warning_threshold >= threshold.critical_threshold:
                    errors.append(
                        f"Warning threshold must be less than critical threshold for {metric_name}"
                    )

                if threshold.warning_threshold < 0 or threshold.critical_threshold < 0:
                    errors.append(f"Thresholds must be positive for {metric_name}")

            return errors

        except Exception as e:
            logger.error(f"Failed to validate settings: {e}")
            return ["Validation failed due to system error"]

    def export_settings(self, tenant_id: str) -> Dict[str, Any]:
        """Export settings for a tenant."""
        try:
            settings = self.get_settings(tenant_id)

            return {
                "tenant_id": tenant_id,
                "level": settings.level.value,
                "monitoring_interval_seconds": settings.monitoring_interval_seconds,
                "alerting_enabled": settings.alerting_enabled,
                "auto_optimization_enabled": settings.auto_optimization_enabled,
                "retention_days": settings.retention_days,
                "thresholds": {
                    name: {
                        "metric_type": threshold.metric_type.value,
                        "warning_threshold": threshold.warning_threshold,
                        "critical_threshold": threshold.critical_threshold,
                        "comparison_operator": threshold.comparison_operator,
                        "enabled": threshold.enabled,
                        "cooldown_period_minutes": threshold.cooldown_period_minutes,
                    }
                    for name, threshold in settings.thresholds.items()
                },
                "custom_settings": settings.custom_settings,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to export settings for tenant {tenant_id}: {e}")
            return {}

    def import_settings(self, tenant_id: str, settings_data: Dict[str, Any]) -> bool:
        """Import settings for a tenant."""
        try:
            # Convert thresholds
            thresholds = {}
            for name, threshold_data in settings_data.get("thresholds", {}).items():
                threshold = PerformanceThreshold(
                    metric_type=MetricType(threshold_data["metric_type"]),
                    warning_threshold=threshold_data["warning_threshold"],
                    critical_threshold=threshold_data["critical_threshold"],
                    comparison_operator=threshold_data.get("comparison_operator", "gt"),
                    enabled=threshold_data.get("enabled", True),
                    cooldown_period_minutes=threshold_data.get(
                        "cooldown_period_minutes", 5
                    ),
                )
                thresholds[name] = threshold

            # Create settings
            settings = PerformanceSettings(
                level=PerformanceLevel(settings_data.get("level", "medium")),
                monitoring_interval_seconds=settings_data.get(
                    "monitoring_interval_seconds", 60
                ),
                alerting_enabled=settings_data.get("alerting_enabled", True),
                auto_optimization_enabled=settings_data.get(
                    "auto_optimization_enabled", False
                ),
                retention_days=settings_data.get("retention_days", 30),
                thresholds=thresholds,
                custom_settings=settings_data.get("custom_settings", {}),
            )

            # Validate settings
            errors = self.validate_settings(settings)
            if errors:
                logger.error(f"Invalid settings for import: {errors}")
                return False

            # Save settings
            return self.update_settings(tenant_id, settings)

        except Exception as e:
            logger.error(f"Failed to import settings for tenant {tenant_id}: {e}")
            return False

    def _initialize_default_thresholds(self) -> Dict[str, PerformanceThreshold]:
        """Initialize default performance thresholds."""
        return {
            "cpu_percent": PerformanceThreshold(
                metric_type=MetricType.CPU,
                warning_threshold=70.0,
                critical_threshold=90.0,
            ),
            "memory_percent": PerformanceThreshold(
                metric_type=MetricType.MEMORY,
                warning_threshold=80.0,
                critical_threshold=95.0,
            ),
            "disk_percent": PerformanceThreshold(
                metric_type=MetricType.DISK,
                warning_threshold=80.0,
                critical_threshold=95.0,
            ),
            "connection_pool_utilization": PerformanceThreshold(
                metric_type=MetricType.DATABASE,
                warning_threshold=80.0,
                critical_threshold=95.0,
            ),
            "query_response_time": PerformanceThreshold(
                metric_type=MetricType.DATABASE,
                warning_threshold=1000.0,
                critical_threshold=5000.0,
            ),
            "cache_hit_rate": PerformanceThreshold(
                metric_type=MetricType.CACHE,
                warning_threshold=0.7,
                critical_threshold=0.5,
                comparison_operator="lt",
            ),
            "application_response_time": PerformanceThreshold(
                metric_type=MetricType.APPLICATION,
                warning_threshold=500.0,
                critical_threshold=2000.0,
            ),
        }

    def _initialize_performance_levels(self) -> Dict[str, Dict[str, Any]]:
        """Initialize performance level configurations."""
        return {
            "low": {
                "monitoring_interval": 300,  # 5 minutes
                "alerting_enabled": True,
                "auto_optimization": False,
                "retention_days": 7,
                "description": "Basic monitoring with minimal overhead",
            },
            "medium": {
                "monitoring_interval": 60,  # 1 minute
                "alerting_enabled": True,
                "auto_optimization": False,
                "retention_days": 30,
                "description": "Standard monitoring for production workloads",
            },
            "high": {
                "monitoring_interval": 30,  # 30 seconds
                "alerting_enabled": True,
                "auto_optimization": True,
                "retention_days": 90,
                "description": "Advanced monitoring with auto-optimization",
            },
            "ultra": {
                "monitoring_interval": 10,  # 10 seconds
                "alerting_enabled": True,
                "auto_optimization": True,
                "retention_days": 365,
                "description": "Maximum monitoring for critical systems",
            },
        }

    def _get_default_settings(self) -> PerformanceSettings:
        """Get default performance settings."""
        return PerformanceSettings(
            level=PerformanceLevel.MEDIUM,
            monitoring_interval_seconds=60,
            alerting_enabled=True,
            auto_optimization_enabled=False,
            retention_days=30,
            thresholds=self._default_thresholds,
        )

    def _determine_performance_level(
        self,
        system_resources: Dict[str, Any],
        workload_characteristics: Dict[str, Any],
    ) -> PerformanceLevel:
        """Determine appropriate performance level."""
        try:
            # Check system resources
            cpu_cores = system_resources.get("cpu_cores", 4)
            memory_gb = system_resources.get("memory_gb", 8)
            disk_gb = system_resources.get("disk_gb", 100)

            # Check workload characteristics
            request_rate = workload_characteristics.get("request_rate", 100)
            criticality = workload_characteristics.get("criticality", "medium")
            user_count = workload_characteristics.get("user_count", 100)

            # Determine level based on resources and workload
            if (
                cpu_cores >= 16
                and memory_gb >= 64
                and request_rate > 1000
                and criticality == "high"
            ):
                return PerformanceLevel.ULTRA
            elif (
                cpu_cores >= 8
                and memory_gb >= 32
                and request_rate > 500
                and criticality in ["medium", "high"]
            ):
                return PerformanceLevel.HIGH
            elif cpu_cores >= 4 and memory_gb >= 16 and request_rate > 100:
                return PerformanceLevel.MEDIUM
            else:
                return PerformanceLevel.LOW

        except Exception as e:
            logger.error(f"Failed to determine performance level: {e}")
            return PerformanceLevel.MEDIUM

    def _customize_settings(
        self,
        level_config: Dict[str, Any],
        system_resources: Dict[str, Any],
        workload_characteristics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Customize settings based on system and workload."""
        try:
            customized = level_config.copy()

            # Adjust monitoring interval based on request rate
            request_rate = workload_characteristics.get("request_rate", 100)
            if request_rate > 1000:
                customized["monitoring_interval"] = min(
                    customized["monitoring_interval"], 30
                )
            elif request_rate < 50:
                customized["monitoring_interval"] = max(
                    customized["monitoring_interval"], 300
                )

            # Adjust retention based on storage availability
            disk_gb = system_resources.get("disk_gb", 100)
            if disk_gb > 1000:
                customized["retention_days"] = min(customized["retention_days"], 365)
            elif disk_gb < 100:
                customized["retention_days"] = max(customized["retention_days"], 7)

            # Enable auto-optimization for high-performance systems
            if (
                system_resources.get("cpu_cores", 4) >= 8
                and workload_characteristics.get("criticality") == "high"
            ):
                customized["auto_optimization"] = True

            return customized

        except Exception as e:
            logger.error(f"Failed to customize settings: {e}")
            return level_config

    def _calculate_optimal_thresholds(
        self,
        system_resources: Dict[str, Any],
        workload_characteristics: Dict[str, Any],
    ) -> Dict[str, PerformanceThreshold]:
        """Calculate optimal thresholds based on system and workload."""
        try:
            thresholds = {}

            # CPU thresholds based on core count
            cpu_cores = system_resources.get("cpu_cores", 4)
            if cpu_cores >= 16:
                thresholds["cpu_percent"] = PerformanceThreshold(
                    metric_type=MetricType.CPU,
                    warning_threshold=80.0,
                    critical_threshold=95.0,
                )
            elif cpu_cores >= 8:
                thresholds["cpu_percent"] = PerformanceThreshold(
                    metric_type=MetricType.CPU,
                    warning_threshold=70.0,
                    critical_threshold=90.0,
                )
            else:
                thresholds["cpu_percent"] = PerformanceThreshold(
                    metric_type=MetricType.CPU,
                    warning_threshold=60.0,
                    critical_threshold=85.0,
                )

            # Memory thresholds based on available memory
            memory_gb = system_resources.get("memory_gb", 8)
            if memory_gb >= 64:
                thresholds["memory_percent"] = PerformanceThreshold(
                    metric_type=MetricType.MEMORY,
                    warning_threshold=85.0,
                    critical_threshold=95.0,
                )
            elif memory_gb >= 32:
                thresholds["memory_percent"] = PerformanceThreshold(
                    metric_type=MetricType.MEMORY,
                    warning_threshold=80.0,
                    critical_threshold=95.0,
                )
            else:
                thresholds["memory_percent"] = PerformanceThreshold(
                    metric_type=MetricType.MEMORY,
                    warning_threshold=75.0,
                    critical_threshold=90.0,
                )

            # Database thresholds based on request rate
            request_rate = workload_characteristics.get("request_rate", 100)
            if request_rate > 1000:
                thresholds["query_response_time"] = PerformanceThreshold(
                    metric_type=MetricType.DATABASE,
                    warning_threshold=500.0,
                    critical_threshold=2000.0,
                )
            elif request_rate > 100:
                thresholds["query_response_time"] = PerformanceThreshold(
                    metric_type=MetricType.DATABASE,
                    warning_threshold=1000.0,
                    critical_threshold=5000.0,
                )
            else:
                thresholds["query_response_time"] = PerformanceThreshold(
                    metric_type=MetricType.DATABASE,
                    warning_threshold=2000.0,
                    critical_threshold=10000.0,
                )

            # Add default thresholds for other metrics
            for name, default_threshold in self._default_thresholds.items():
                if name not in thresholds:
                    thresholds[name] = default_threshold

            return thresholds

        except Exception as e:
            logger.error(f"Failed to calculate optimal thresholds: {e}")
            return self._default_thresholds

    def _load_configuration(self) -> None:
        """Load configuration from file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.info(
                    f"Configuration file {self.config_path} not found, using defaults"
                )
                return

            with open(config_file, "r") as f:
                data = json.load(f)

            # Load settings for each tenant
            for tenant_id, settings_data in data.get("tenants", {}).items():
                thresholds = {}
                for name, threshold_data in settings_data.get("thresholds", {}).items():
                    threshold = PerformanceThreshold(
                        metric_type=MetricType(threshold_data["metric_type"]),
                        warning_threshold=threshold_data["warning_threshold"],
                        critical_threshold=threshold_data["critical_threshold"],
                        comparison_operator=threshold_data.get(
                            "comparison_operator", "gt"
                        ),
                        enabled=threshold_data.get("enabled", True),
                        cooldown_period_minutes=threshold_data.get(
                            "cooldown_period_minutes", 5
                        ),
                    )
                    thresholds[name] = threshold

                settings = PerformanceSettings(
                    level=PerformanceLevel(settings_data.get("level", "medium")),
                    monitoring_interval_seconds=settings_data.get(
                        "monitoring_interval_seconds", 60
                    ),
                    alerting_enabled=settings_data.get("alerting_enabled", True),
                    auto_optimization_enabled=settings_data.get(
                        "auto_optimization_enabled", False
                    ),
                    retention_days=settings_data.get("retention_days", 30),
                    thresholds=thresholds,
                    custom_settings=settings_data.get("custom_settings", {}),
                )

                self._settings[tenant_id] = settings

            logger.info(f"Loaded configuration for {len(self._settings)} tenants")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def _save_configuration(self) -> None:
        """Save configuration to file."""
        try:
            config_data = {
                "tenants": {
                    tenant_id: {
                        "level": settings.level.value,
                        "monitoring_interval_seconds": settings.monitoring_interval_seconds,
                        "alerting_enabled": settings.alerting_enabled,
                        "auto_optimization_enabled": settings.auto_optimization_enabled,
                        "retention_days": settings.retention_days,
                        "thresholds": {
                            name: {
                                "metric_type": threshold.metric_type.value,
                                "warning_threshold": threshold.warning_threshold,
                                "critical_threshold": threshold.critical_threshold,
                                "comparison_operator": threshold.comparison_operator,
                                "enabled": threshold.enabled,
                                "cooldown_period_minutes": threshold.cooldown_period_minutes,
                            }
                            for name, threshold in settings.thresholds.items()
                        },
                        "custom_settings": settings.custom_settings,
                    }
                    for tenant_id, settings in self._settings.items()
                },
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Saved configuration to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")


# Global instance
performance_config = PerformanceConfig()


# Factory function
def get_performance_config() -> PerformanceConfig:
    """Get performance configuration instance."""
    return performance_config
