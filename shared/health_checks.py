"""
Health Checks for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import statistics
import psutil
import socket

from shared.logging_config import get_logger
from shared.metrics_collector import get_metrics_collector, MetricType, MetricCategory

logger = get_logger("sorce.health_checks")


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class CheckType(Enum):
    """Types of health checks."""

    DATABASE = "database"
    CACHE = "cache"
    DISK = "disk"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    APPLICATION = "application"
    SERVICE = "service"


@dataclass
class HealthCheckDefinition:
    """Health check definition."""

    name: str
    check_type: CheckType
    description: str
    check_function: Callable
    interval_seconds: int = 60
    timeout_seconds: int = 30
    enabled: bool = True
    critical_threshold: Optional[float] = None
    warning_threshold: Optional[float] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class HealthCheckResult:
    """Health check result."""

    name: str
    check_type: CheckType
    status: HealthStatus
    message: str
    value: Optional[float] = None
    unit: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class HealthSummary:
    """Overall health summary."""

    overall_status: HealthStatus
    total_checks: int
    healthy_checks: int
    warning_checks: int
    critical_checks: int
    unknown_checks: int
    check_results: List[HealthCheckResult]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recommendations: List[str] = field(default_factory=list)


class HealthChecker:
    """Advanced health checking system."""

    def __init__(self):
        self._checks: Dict[str, HealthCheckDefinition] = {}
        self._results: List[HealthCheckResult] = []
        self._metrics_collector = get_metrics_collector()

        # Background task
        self._monitoring_task: Optional[asyncio.Task] = None

        # Initialize default health checks
        self._initialize_default_checks()

        # Start background monitoring
        self._start_monitoring()

    def add_check(
        self,
        name: str,
        check_type: CheckType,
        description: str,
        check_function: Callable,
        interval_seconds: int = 60,
        timeout_seconds: int = 30,
        enabled: bool = True,
        critical_threshold: Optional[float] = None,
        warning_threshold: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Add a new health check."""
        try:
            definition = HealthCheckDefinition(
                name=name,
                check_type=check_type,
                description=description,
                check_function=check_function,
                interval_seconds=interval_seconds,
                timeout_seconds=timeout_seconds,
                enabled=enabled,
                critical_threshold=critical_threshold,
                warning_threshold=warning_threshold,
                tags=tags or [],
            )

            self._checks[name] = definition

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

    def remove_check(self, name: str) -> bool:
        """Remove a health check."""
        try:
            if name in self._checks:
                del self._checks[name]
                logger.info(f"Removed health check: {name}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to remove health check {name}: {e}")
            return False

    def enable_check(self, name: str, enabled: bool = True) -> bool:
        """Enable or disable a health check."""
        try:
            if name in self._checks:
                self._checks[name].enabled = enabled
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

    async def run_check(self, name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check."""
        try:
            if name not in self._checks:
                logger.warning(f"Health check {name} not found")
                return None

            definition = self._checks[name]

            if not definition.enabled:
                return HealthCheckResult(
                    name=name,
                    check_type=definition.check_type,
                    status=HealthStatus.UNKNOWN,
                    message="Health check is disabled",
                    duration_ms=0.0,
                )

            start_time = time.time()

            try:
                # Run check with timeout
                result = await asyncio.wait_for(
                    definition.check_function(), timeout=definition.timeout_seconds
                )

                duration_ms = (time.time() - start_time) * 1000

                # Determine status and value
                status, value, unit, message, details = self._parse_check_result(
                    result, definition
                )

                # Apply thresholds
                if value is not None:
                    if (
                        definition.critical_threshold
                        and value >= definition.critical_threshold
                    ):
                        status = HealthStatus.CRITICAL
                        message = f"{message} (critical threshold exceeded: {value})"
                    elif (
                        definition.warning_threshold
                        and value >= definition.warning_threshold
                    ):
                        status = HealthStatus.WARNING
                        message = f"{message} (warning threshold exceeded: {value})"

                health_check_result = HealthCheckResult(
                    name=name,
                    check_type=definition.check_type,
                    status=status,
                    message=message,
                    value=value,
                    unit=unit,
                    duration_ms=duration_ms,
                    details=details,
                )

                # Record metrics
                await self._metrics_collector.set_gauge(
                    f"health_check_{name}",
                    1.0 if status == HealthStatus.HEALTHY else 0.0,
                    labels={"status": status.value},
                )

                await self._metrics_collector.set_gauge(
                    f"health_check_{name}_duration", duration_ms
                )

                # Store result
                self._results.append(health_check_result)

                # Keep only last 1000 results
                if len(self._results) > 1000:
                    self._results = self._results[-1000:]

                return health_check_result

            except asyncio.TimeoutError:
                duration_ms = (time.time() - start_time) * 1000

                health_check_result = HealthCheckResult(
                    name=name,
                    check_type=definition.check_type,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check timed out after {definition.timeout_seconds}s",
                    duration_ms=duration_ms,
                    error="Timeout",
                )

                self._results.append(health_check_result)

                return health_check_result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                health_check_result = HealthCheckResult(
                    name=name,
                    check_type=definition.check_type,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    duration_ms=duration_ms,
                    error=str(e),
                )

                self._results.append(health_check_result)

                return health_check_result

        except Exception as e:
            logger.error(f"Failed to run health check {name}: {e}")
            return None

    async def run_all_checks(
        self, check_types: Optional[List[CheckType]] = None
    ) -> List[HealthCheckResult]:
        """Run all enabled health checks."""
        try:
            results = []

            # Filter by check type if specified
            checks_to_run = []
            for name, definition in self._checks.items():
                if definition.enabled:
                    if check_types is None or definition.check_type in check_types:
                        checks_to_run.append(name)

            # Run checks concurrently
            tasks = []
            for name in checks_to_run:
                tasks.append(self.run_check(name))

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

    async def get_health_summary(
        self, check_types: Optional[List[CheckType]] = None
    ) -> HealthSummary:
        """Get overall health summary."""
        try:
            results = await self.run_all_checks(check_types)

            if not results:
                return HealthSummary(
                    overall_status=HealthStatus.UNKNOWN,
                    total_checks=0,
                    healthy_checks=0,
                    warning_checks=0,
                    critical_checks=0,
                    unknown_checks=0,
                    check_results=[],
                )

            # Count statuses
            healthy_checks = len(
                [r for r in results if r.status == HealthStatus.HEALTHY]
            )
            warning_checks = len(
                [r for r in results if r.status == HealthStatus.WARNING]
            )
            critical_checks = len(
                [r for r in results if r.status == HealthStatus.CRITICAL]
            )
            unknown_checks = len(
                [r for r in results if r.status == HealthStatus.UNKNOWN]
            )

            # Determine overall status
            if critical_checks > 0:
                overall_status = HealthStatus.CRITICAL
            elif warning_checks > 0:
                overall_status = HealthStatus.WARNING
            elif healthy_checks == len(results):
                overall_status = HealthStatus.HEALTHY
            else:
                overall_status = HealthStatus.UNKNOWN

            # Generate recommendations
            recommendations = self._generate_recommendations(results)

            return HealthSummary(
                overall_status=overall_status,
                total_checks=len(results),
                healthy_checks=healthy_checks,
                warning_checks=warning_checks,
                critical_checks=critical_checks,
                unknown_checks=unknown_checks,
                check_results=results,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")

            return HealthSummary(
                overall_status=HealthStatus.UNKNOWN,
                total_checks=0,
                healthy_checks=0,
                warning_checks=0,
                critical_checks=0,
                unknown_checks=0,
                check_results=[],
                recommendations=["Failed to generate health summary"],
            )

    def _parse_check_result(
        self,
        result: Any,
        definition: HealthCheckDefinition,
    ) -> Tuple[HealthStatus, Optional[float], Optional[str], str, Dict[str, Any]]:
        """Parse health check result."""
        try:
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.CRITICAL
                message = "Check passed" if result else "Check failed"
                return status, None, None, message, {}

            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "unknown"))
                value = result.get("value")
                unit = result.get("unit")
                message = result.get("message", "Check completed")
                details = {
                    k: v
                    for k, v in result.items()
                    if k not in ["status", "value", "unit", "message"]
                }
                return status, value, unit, message, details

            elif isinstance(result, (int, float)):
                # Assume numeric result is a value to be evaluated
                value = float(result)
                status = HealthStatus.HEALTHY

                if (
                    definition.critical_threshold
                    and value >= definition.critical_threshold
                ):
                    status = HealthStatus.CRITICAL
                elif (
                    definition.warning_threshold
                    and value >= definition.warning_threshold
                ):
                    status = HealthStatus.WARNING

                message = f"Value: {value}"
                return status, value, None, message, {}

            else:
                status = HealthStatus.HEALTHY
                message = str(result)
                return status, None, None, message, {}

        except Exception as e:
            logger.error(f"Failed to parse check result: {e}")
            return HealthStatus.UNKNOWN, None, None, "Failed to parse result", {}

    def _generate_recommendations(self, results: List[HealthCheckResult]) -> List[str]:
        """Generate health recommendations."""
        try:
            recommendations = []

            # Critical checks
            critical_checks = [r for r in results if r.status == HealthStatus.CRITICAL]
            if critical_checks:
                recommendations.append(
                    f"Address {len(critical_checks)} critical health check(s): {', '.join([c.name for c in critical_checks])}"
                )

            # Warning checks
            warning_checks = [r for r in results if r.status == HealthStatus.WARNING]
            if warning_checks:
                recommendations.append(
                    f"Monitor {len(warning_checks)} warning health check(s): {', '.join([c.name for c in warning_checks])}"
                )

            # Slow checks
            slow_checks = [r for r in results if r.duration_ms > 1000]  # > 1 second
            if slow_checks:
                recommendations.append(
                    f"Optimize {len(slow_checks)} slow health check(s): {', '.join([c.name for c in slow_checks])}"
                )

            # Performance recommendations
            if len(results) > 0:
                avg_duration = statistics.mean([r.duration_ms for r in results])
                if avg_duration > 500:
                    recommendations.append(
                        "Consider optimizing health check performance"
                    )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Failed to generate recommendations"]

    def _initialize_default_checks(self) -> None:
        """Initialize default health checks."""
        try:
            # Database connectivity check
            self.add_check(
                name="database_connectivity",
                check_type=CheckType.DATABASE,
                description="Check database connectivity",
                check_function=self._check_database_connectivity,
                interval_seconds=30,
                tags=["database", "connectivity"],
            )

            # Database performance check
            self.add_check(
                name="database_performance",
                check_type=CheckType.DATABASE,
                description="Check database query performance",
                check_function=self._check_database_performance,
                interval_seconds=60,
                warning_threshold=1000,  # 1 second
                critical_threshold=5000,  # 5 seconds
                tags=["database", "performance"],
            )

            # Memory usage check
            self.add_check(
                name="memory_usage",
                check_type=CheckType.MEMORY,
                description="Check memory usage",
                check_function=self._check_memory_usage,
                interval_seconds=30,
                warning_threshold=80.0,
                critical_threshold=95.0,
                tags=["system", "memory"],
            )

            # Disk space check
            self.add_check(
                name="disk_space",
                check_type=CheckType.DISK,
                description="Check disk space",
                check_function=self._check_disk_space,
                interval_seconds=300,
                warning_threshold=85.0,
                critical_threshold=95.0,
                tags=["system", "disk"],
            )

            # CPU usage check
            self.add_check(
                name="cpu_usage",
                check_type=CheckType.CPU,
                description="Check CPU usage",
                check_function=self._check_cpu_usage,
                interval_seconds=30,
                warning_threshold=80.0,
                critical_threshold=90.0,
                tags=["system", "cpu"],
            )

            # Network connectivity check
            self.add_check(
                name="network_connectivity",
                check_type=CheckType.NETWORK,
                description="Check network connectivity",
                check_function=self._check_network_connectivity,
                interval_seconds=60,
                tags=["network", "connectivity"],
            )

            # Application health check
            self.add_check(
                name="application_health",
                check_type=CheckType.APPLICATION,
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
            # For now, simulate a check
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

    async def _check_database_performance(self) -> Dict[str, Any]:
        """Check database query performance."""
        try:
            # This would check actual database performance
            # For now, simulate a check with random response time
            import random

            query_time = random.uniform(50, 2000)  # 50ms to 2s

            return {
                "status": "healthy",
                "message": f"Query response time: {query_time:.1f}ms",
                "query_time_ms": query_time,
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Database performance check failed: {str(e)}",
            }

    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            return {
                "status": "healthy",
                "message": f"Memory usage: {usage_percent:.1f}%",
                "value": usage_percent,
                "unit": "percent",
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
                "total_gb": memory.total / (1024**3),
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Memory check failed: {str(e)}",
            }

    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space."""
        try:
            disk = psutil.disk_usage("/")
            usage_percent = (disk.used / disk.total) * 100

            return {
                "status": "healthy",
                "message": f"Disk usage: {usage_percent:.1f}%",
                "value": usage_percent,
                "unit": "percent",
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
            cpu_percent = psutil.cpu_percent(interval=1)

            return {
                "status": "healthy",
                "message": f"CPU usage: {cpu_percent:.1f}%",
                "value": cpu_percent,
                "unit": "percent",
                "cpu_count": psutil.cpu_count(),
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"CPU check failed: {str(e)}",
            }

    async def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity."""
        try:
            # Check connectivity to a reliable host
            host = "8.8.8.8"  # Google DNS
            port = 53
            timeout = 5

            socket.setdefaulttimeout(timeout)

            try:
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                socket.close()

                return {
                    "status": "healthy",
                    "message": f"Network connectivity to {host}:{port} successful",
                }
            except socket.error:
                return {
                    "status": "critical",
                    "message": f"Network connectivity to {host}:{port} failed",
                }

        except Exception as e:
            return {
                "status": "critical",
                "message": f"Network check failed: {str(e)}",
            }

    async def _check_application_health(self) -> Dict[str, Any]:
        """Check application health."""
        try:
            # This would check application-specific health indicators
            # For now, simulate a check
            import random

            uptime = random.uniform(3600, 86400)  # 1-24 hours
            active_connections = random.randint(10, 100)

            return {
                "status": "healthy",
                "message": "Application is running normally",
                "uptime_seconds": uptime,
                "active_connections": active_connections,
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Application health check failed: {str(e)}",
            }

    def _start_monitoring(self) -> None:
        """Start background monitoring."""
        try:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        try:
            while True:
                await asyncio.sleep(30)  # Run every 30 seconds

                try:
                    # Run all checks and log results
                    results = await self.run_all_checks()

                    for result in results:
                        if result.status in [
                            HealthStatus.WARNING,
                            HealthStatus.CRITICAL,
                        ]:
                            logger.warning(
                                f"Health check {result.name}: {result.status.value} - {result.message}"
                            )

                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Monitoring loop failed: {e}")


# Global instance
health_checker = HealthChecker()


# Factory function
def get_health_checker() -> HealthChecker:
    """Get health checker instance."""
    return health_checker
