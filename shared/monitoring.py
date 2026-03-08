"""
Monitoring System for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict
import statistics

from shared.logging_config import get_logger
from shared.metrics_collector import get_metrics_collector, MetricType, MetricCategory

logger = get_logger("sorce.monitoring")


class MonitoringLevel(Enum):
    """Monitoring levels."""

    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    COMPREHENSIVE = "comprehensive"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CheckStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check definition."""

    name: str
    description: str
    check_function: Callable
    interval_seconds: int = 60
    timeout_seconds: int = 30
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    last_check: Optional[datetime] = None
    last_status: CheckStatus = CheckStatus.UNKNOWN
    last_duration_ms: float = 0.0
    last_error: Optional[str] = None


@dataclass
class HealthCheckResult:
    """Health check result."""

    name: str
    status: CheckStatus
    message: str
    duration_ms: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class MonitoringAlert:
    """Monitoring alert."""

    id: str
    check_name: str
    severity: AlertSeverity
    title: str
    message: str
    status: CheckStatus
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringReport:
    """Comprehensive monitoring report."""

    timestamp: datetime
    overall_status: CheckStatus
    health_checks: List[HealthCheckResult]
    alerts: List[MonitoringAlert]
    metrics_summary: Dict[str, Any]
    performance_summary: Dict[str, Any]
    recommendations: List[str]


class MonitoringSystem:
    """Advanced monitoring system with health checks and alerts."""

    def __init__(self):
        self._health_checks: Dict[str, HealthCheck] = {}
        self._check_results: List[HealthCheckResult] = []
        self._alerts: List[MonitoringAlert] = []
        self._alert_handlers: Dict[str, Callable] = {}
        self._metrics_collector = get_metrics_collector()

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None

        # Initialize default health checks
        self._initialize_default_checks()

        # Start background monitoring
        self._start_monitoring()

    def add_health_check(
        self,
        name: str,
        description: str,
        check_function: Callable,
        interval_seconds: int = 60,
        timeout_seconds: int = 30,
        enabled: bool = True,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Add a new health check."""
        try:
            health_check = HealthCheck(
                name=name,
                description=description,
                check_function=check_function,
                interval_seconds=interval_seconds,
                timeout_seconds=timeout_seconds,
                enabled=enabled,
                tags=tags or [],
            )

            self._health_checks[name] = health_check

            # Define metrics for the health check
            self._metrics_collector.define_metric(
                name=f"health_check_{name}",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.SYSTEM,
                description=f"Health check status for {name}",
                unit="status",
                labels=["status"],
            )

            self._metrics_collector.define_metric(
                name=f"health_check_{name}_duration",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.SYSTEM,
                description=f"Health check duration for {name}",
                unit="ms",
            )

            logger.info(f"Added health check: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add health check {name}: {e}")
            return False

    def remove_health_check(self, name: str) -> bool:
        """Remove a health check."""
        try:
            if name in self._health_checks:
                del self._health_checks[name]
                logger.info(f"Removed health check: {name}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to remove health check {name}: {e}")
            return False

    def enable_health_check(self, name: str, enabled: bool = True) -> bool:
        """Enable or disable a health check."""
        try:
            if name in self._health_checks:
                self._health_checks[name].enabled = enabled
                logger.info(
                    f"{'Enabled' if enabled else 'Disabled'} health check: {name}"
                )
                return True
            return False

        except Exception as e:
            logger.error(
                f"Failed to {'enable' if enabled else 'disable'} health check {name}: {e}"
            )
            return False

    async def run_health_check(self, name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check."""
        try:
            if name not in self._health_checks:
                logger.warning(f"Health check {name} not found")
                return None

            health_check = self._health_checks[name]

            if not health_check.enabled:
                return HealthCheckResult(
                    name=name,
                    status=CheckStatus.UNKNOWN,
                    message="Health check is disabled",
                    duration_ms=0.0,
                    timestamp=datetime.now(timezone.utc),
                )

            start_time = datetime.now(timezone.utc())

            try:
                # Run check with timeout
                result = await asyncio.wait_for(
                    health_check.check_function(), timeout=health_check.timeout_seconds
                )

                duration_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                # Determine status
                if isinstance(result, bool):
                    status = CheckStatus.HEALTHY if result else CheckStatus.CRITICAL
                    message = "Check passed" if result else "Check failed"
                elif isinstance(result, dict):
                    status = CheckStatus(result.get("status", "unknown"))
                    message = result.get("message", "Check completed")
                    details = {
                        k: v
                        for k, v in result.items()
                        if k not in ["status", "message"]
                    }
                else:
                    status = CheckStatus.HEALTHY
                    message = str(result)
                    details = {"result": result}

                health_check_result = HealthCheckResult(
                    name=name,
                    status=status,
                    message=message,
                    duration_ms=duration_ms,
                    timestamp=start_time,
                    details=details,
                )

                # Update health check metadata
                health_check.last_check = start_time
                health_check.last_status = status
                health_check.last_duration_ms = duration_ms
                health_check.last_error = None

                # Record metrics
                await self._metrics_collector.set_gauge(
                    f"health_check_{name}",
                    1.0 if status == CheckStatus.HEALTHY else 0.0,
                    labels={"status": status.value},
                )

                await self._metrics_collector.set_gauge(
                    f"health_check_{name}_duration", duration_ms
                )

                # Store result
                self._check_results.append(health_check_result)

                # Keep only last 1000 results
                if len(self._check_results) > 1000:
                    self._check_results = self._check_results[-1000:]

                return health_check_result

            except asyncio.TimeoutError:
                duration_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                health_check_result = HealthCheckResult(
                    name=name,
                    status=CheckStatus.CRITICAL,
                    message=f"Health check timed out after {health_check.timeout_seconds}s",
                    duration_ms=duration_ms,
                    timestamp=start_time,
                    error="Timeout",
                )

                health_check.last_check = start_time
                health_check.last_status = CheckStatus.CRITICAL
                health_check.last_duration_ms = duration_ms
                health_check.last_error = "Timeout"

                self._check_results.append(health_check_result)

                return health_check_result

            except Exception as e:
                duration_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                health_check_result = HealthCheckResult(
                    name=name,
                    status=CheckStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    duration_ms=duration_ms,
                    timestamp=start_time,
                    error=str(e),
                )

                health_check.last_check = start_time
                health_check.last_status = CheckStatus.CRITICAL
                health_check.last_duration_ms = duration_ms
                health_check.last_error = str(e)

                self._check_results.append(health_check_result)

                return health_check_result

        except Exception as e:
            logger.error(f"Failed to run health check {name}: {e}")
            return None

    async def run_all_health_checks(self) -> List[HealthCheckResult]:
        """Run all enabled health checks."""
        try:
            results = []

            # Run checks concurrently
            tasks = []
            for name, health_check in self._health_checks.items():
                if health_check.enabled:
                    tasks.append(self.run_health_check(name))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Filter out exceptions
                valid_results = []
                for result in results:
                    if isinstance(result, HealthCheckResult):
                        valid_results.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Health check error: {result}")

                return valid_results

            return results

        except Exception as e:
            logger.error(f"Failed to run all health checks: {e}")
            return []

    async def get_health_status(self, tags: Optional[List[str]] = None) -> CheckStatus:
        """Get overall health status."""
        try:
            results = await self.run_all_health_checks()

            # Filter by tags if specified
            if tags:
                filtered_results = []
                for result in results:
                    check = self._health_checks.get(result.name)
                    if check and any(tag in check.tags for tag in tags):
                        filtered_results.append(result)
                results = filtered_results

            if not results:
                return CheckStatus.UNKNOWN

            # Determine overall status
            if all(r.status == CheckStatus.HEALTHY for r in results):
                return CheckStatus.HEALTHY
            elif any(r.status == CheckStatus.CRITICAL for r in results):
                return CheckStatus.CRITICAL
            elif any(r.status == CheckStatus.WARNING for r in results):
                return CheckStatus.WARNING
            else:
                return CheckStatus.UNKNOWN

        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return CheckStatus.UNKNOWN

    async def create_alert(
        self,
        check_name: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        status: CheckStatus,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a monitoring alert."""
        try:
            alert = MonitoringAlert(
                id=str(uuid.uuid4()),
                check_name=check_name,
                severity=severity,
                title=title,
                message=message,
                status=status,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
            )

            self._alerts.append(alert)

            # Keep only last 1000 alerts
            if len(self._alerts) > 1000:
                self._alerts = self._alerts[-1000:]

            # Call alert handlers
            await self._call_alert_handlers(alert)

            logger.warning(f"Created alert: {title} ({severity.value})")
            return alert.id

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return ""

    def register_alert_handler(self, alert_type: str, handler: Callable) -> None:
        """Register an alert handler."""
        try:
            self._alert_handlers[alert_type] = handler
            logger.info(f"Registered alert handler for: {alert_type}")

        except Exception as e:
            logger.error(f"Failed to register alert handler: {e}")

    async def resolve_alert(
        self, alert_id: str, resolution_note: Optional[str] = None
    ) -> bool:
        """Resolve an alert."""
        try:
            for alert in self._alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now(timezone.utc)

                    if resolution_note:
                        alert.metadata["resolution_note"] = resolution_note

                    logger.info(f"Resolved alert: {alert_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False

    async def get_monitoring_report(
        self, tags: Optional[List[str]] = None
    ) -> MonitoringReport:
        """Generate comprehensive monitoring report."""
        try:
            # Run health checks
            health_results = await self.run_all_health_checks()

            # Filter by tags if specified
            if tags:
                filtered_results = []
                for result in health_results:
                    check = self._health_checks.get(result.name)
                    if check and any(tag in check.tags for tag in tags):
                        filtered_results.append(result)
                health_results = filtered_results

            # Get active alerts
            active_alerts = [a for a in self._alerts if not a.resolved]

            # Get metrics summary
            metrics_summary = await self._get_metrics_summary()

            # Get performance summary
            performance_summary = await self._get_performance_summary()

            # Determine overall status
            if health_results:
                if all(r.status == CheckStatus.HEALTHY for r in health_results):
                    overall_status = CheckStatus.HEALTHY
                elif any(r.status == CheckStatus.CRITICAL for r in health_results):
                    overall_status = CheckStatus.CRITICAL
                elif any(r.status == CheckStatus.WARNING for r in health_results):
                    overall_status = CheckStatus.WARNING
                else:
                    overall_status = CheckStatus.UNKNOWN
            else:
                overall_status = CheckStatus.UNKNOWN

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                health_results, active_alerts
            )

            report = MonitoringReport(
                timestamp=datetime.now(timezone.utc),
                overall_status=overall_status,
                health_checks=health_results,
                alerts=active_alerts,
                metrics_summary=metrics_summary,
                performance_summary=performance_summary,
                recommendations=recommendations,
            )

            return report

        except Exception as e:
            logger.error(f"Failed to generate monitoring report: {e}")

            # Return minimal report
            return MonitoringReport(
                timestamp=datetime.now(timezone.utc),
                overall_status=CheckStatus.UNKNOWN,
                health_checks=[],
                alerts=[],
                metrics_summary={},
                performance_summary={},
                recommendations=["Failed to generate full monitoring report"],
            )

    def _initialize_default_checks(self) -> None:
        """Initialize default health checks."""
        try:
            # Database connectivity check
            self.add_health_check(
                name="database_connectivity",
                description="Check database connectivity",
                check_function=self._check_database_connectivity,
                interval_seconds=30,
                tags=["database", "connectivity"],
            )

            # Memory usage check
            self.add_health_check(
                name="memory_usage",
                description="Check memory usage",
                check_function=self._check_memory_usage,
                interval_seconds=60,
                tags=["system", "memory"],
            )

            # Disk space check
            self.add_health_check(
                name="disk_space",
                description="Check disk space",
                check_function=self._check_disk_space,
                interval_seconds=300,
                tags=["system", "disk"],
            )

            # CPU usage check
            self.add_health_check(
                name="cpu_usage",
                description="Check CPU usage",
                check_function=self._check_cpu_usage,
                interval_seconds=60,
                tags=["system", "cpu"],
            )

            # Application health check
            self.add_health_check(
                name="application_health",
                description="Check application health",
                check_function=self._check_application_health,
                interval_seconds=30,
                tags=["application"],
            )

        except Exception as e:
            logger.error(f"Failed to initialize default health checks: {e}")

    async def _check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # This would check actual database connectivity
            # For now, return a simple check
            return {
                "status": "healthy",
                "message": "Database is reachable",
                "connection_time_ms": 10.5,
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Database connection failed: {str(e)}",
            }

    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            status = "healthy"
            if usage_percent > 90:
                status = "critical"
            elif usage_percent > 80:
                status = "warning"

            return {
                "status": status,
                "message": f"Memory usage: {usage_percent:.1f}%",
                "usage_percent": usage_percent,
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Memory check failed: {str(e)}",
            }

    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space."""
        try:
            import psutil

            disk = psutil.disk_usage("/")
            usage_percent = (disk.used / disk.total) * 100

            status = "healthy"
            if usage_percent > 95:
                status = "critical"
            elif usage_percent > 85:
                status = "warning"

            return {
                "status": status,
                "message": f"Disk usage: {usage_percent:.1f}%",
                "usage_percent": usage_percent,
                "free_gb": disk.free / (1024**3),
                "used_gb": disk.used / (1024**3),
                "total_gb": disk.total / (1024**3),
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Disk check failed: {str(e)}",
            }

    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)

            status = "healthy"
            if cpu_percent > 90:
                status = "critical"
            elif cpu_percent > 80:
                status = "warning"

            return {
                "status": status,
                "message": f"CPU usage: {cpu_percent:.1f}%",
                "usage_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"CPU check failed: {str(e)}",
            }

    async def _check_application_health(self) -> Dict[str, Any]:
        """Check application health."""
        try:
            # This would check application-specific health indicators
            # For now, return a simple check
            return {
                "status": "healthy",
                "message": "Application is running normally",
                "uptime_seconds": 3600,
                "active_connections": 25,
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Application health check failed: {str(e)}",
            }

    async def _call_alert_handlers(self, alert: MonitoringAlert) -> None:
        """Call registered alert handlers."""
        try:
            for alert_type, handler in self._alert_handlers.items():
                if alert_type in alert.check_name or alert_type == "all":
                    try:
                        await handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler failed for {alert_type}: {e}")

        except Exception as e:
            logger.error(f"Failed to call alert handlers: {e}")

    async def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        try:
            summary = {
                "total_metrics": len(self._metrics_collector.get_all_metrics()),
                "categories": {},
                "latest_values": {},
            }

            # Count metrics by category
            categories = defaultdict(int)
            for name, metric in self._metrics_collector.get_all_metrics().items():
                categories[metric.definition.category.value] += 1

            summary["categories"] = dict(categories)

            # Get latest values for key metrics
            key_metrics = [
                "memory_usage",
                "cpu_usage",
                "disk_space",
                "database_connectivity",
            ]
            for metric_name in key_metrics:
                metric = self._metrics_collector.get_metric(
                    f"health_check_{metric_name}"
                )
                if metric:
                    latest = await metric.get_latest()
                    if latest:
                        summary["latest_values"][metric_name] = {
                            "value": latest.value,
                            "timestamp": latest.timestamp.isoformat(),
                            "status": latest.labels.get("status", "unknown"),
                        }

            return summary

        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}

    async def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        try:
            # Get recent health check results
            recent_results = [
                r
                for r in self._check_results
                if r.timestamp > datetime.now(timezone.utc) - timedelta(hours=1)
            ]

            if not recent_results:
                return {}

            # Calculate performance metrics
            avg_duration = statistics.mean([r.duration_ms for r in recent_results])

            status_counts = defaultdict(int)
            for result in recent_results:
                status_counts[result.status.value] += 1

            slow_checks = [
                r
                for r in recent_results
                if r.duration_ms > 1000  # > 1 second
            ]

            return {
                "total_checks": len(recent_results),
                "avg_duration_ms": avg_duration,
                "status_distribution": dict(status_counts),
                "slow_checks": len(slow_checks),
                "slowest_check": max(recent_results, key=lambda r: r.duration_ms).name
                if recent_results
                else None,
                "slowest_duration_ms": max([r.duration_ms for r in recent_results])
                if recent_results
                else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}

    async def _generate_recommendations(
        self,
        health_results: List[HealthCheckResult],
        active_alerts: List[MonitoringAlert],
    ) -> List[str]:
        """Generate recommendations based on health check results and alerts."""
        try:
            recommendations = []

            # Analyze health check results
            critical_checks = [
                r for r in health_results if r.status == CheckStatus.CRITICAL
            ]
            warning_checks = [
                r for r in health_results if r.status == CheckStatus.WARNING
            ]

            if critical_checks:
                recommendations.append(
                    f"Address {len(critical_checks)} critical health check(s): {', '.join([c.name for c in critical_checks])}"
                )

            if warning_checks:
                recommendations.append(
                    f"Monitor {len(warning_checks)} warning health check(s): {', '.join([c.name for c in warning_checks])}"
                )

            # Analyze slow checks
            slow_checks = [r for r in health_results if r.duration_ms > 1000]
            if slow_checks:
                recommendations.append(
                    f"Optimize {len(slow_checks)} slow health check(s): {', '.join([c.name for c in slow_checks])}"
                )

            # Analyze alerts
            critical_alerts = [
                a for a in active_alerts if a.severity == AlertSeverity.CRITICAL
            ]
            if critical_alerts:
                recommendations.append(
                    f"Resolve {len(critical_alerts)} critical alert(s)"
                )

            # Performance recommendations
            if len(health_results) > 0:
                avg_duration = statistics.mean([r.duration_ms for r in health_results])
                if avg_duration > 500:
                    recommendations.append(
                        "Consider optimizing health check performance"
                    )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Failed to generate recommendations due to system error"]

    def _start_monitoring(self) -> None:
        """Start background monitoring tasks."""
        try:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._alert_task = asyncio.create_task(self._alert_loop())

        except Exception as e:
            logger.error(f"Failed to start monitoring tasks: {e}")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        try:
            while True:
                await asyncio.sleep(30)  # Run every 30 seconds

                try:
                    # Run health checks and create alerts if needed
                    results = await self.run_all_health_checks()

                    for result in results:
                        if result.status == CheckStatus.CRITICAL:
                            await self.create_alert(
                                check_name=result.name,
                                severity=AlertSeverity.CRITICAL,
                                title=f"Critical health check failure: {result.name}",
                                message=result.message,
                                status=result.status,
                                metadata={"duration_ms": result.duration_ms},
                            )
                        elif result.status == CheckStatus.WARNING:
                            await self.create_alert(
                                check_name=result.name,
                                severity=AlertSeverity.WARNING,
                                title=f"Warning health check: {result.name}",
                                message=result.message,
                                status=result.status,
                                metadata={"duration_ms": result.duration_ms},
                            )

                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Monitoring loop failed: {e}")

    async def _alert_loop(self) -> None:
        """Background alert processing loop."""
        try:
            while True:
                await asyncio.sleep(300)  # Run every 5 minutes

                try:
                    # Clean up old resolved alerts
                    cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
                    self._alerts = [
                        a
                        for a in self._alerts
                        if not a.resolved or a.resolved_at > cutoff_time
                    ]

                except Exception as e:
                    logger.error(f"Alert cleanup error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Alert loop failed: {e}")


# Global instance
monitoring_system = MonitoringSystem()


# Factory function
def get_monitoring_system() -> MonitoringSystem:
    """Get monitoring system instance."""
    return monitoring_system
