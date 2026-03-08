"""Advanced database connection monitoring and analytics system.

Provides:
- Real-time connection monitoring
- Performance analytics
- Health checking
- Alert generation
- Historical data tracking

Usage:
    from shared.db_connection_monitor import ConnectionMonitor

    monitor = ConnectionMonitor(db_pool)
    await monitor.start_monitoring()
    stats = monitor.get_connection_stats()
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

import asyncpg

from shared.logging_config import get_logger
from shared.alerting import AlertSeverity, get_alert_manager

logger = get_logger("sorce.db_connection_monitor")


class ConnectionStatus(Enum):
    """Connection status levels."""

    IDLE = "idle"
    ACTIVE = "active"
    IN_TRANSACTION = "in_transaction"
    ERROR = "error"
    CLOSED = "closed"


class AlertType(Enum):
    """Alert types for connection monitoring."""

    HIGH_CONNECTION_COUNT = "high_connection_count"
    LONG_LIVED_CONNECTION = "long_lived_connection"
    HIGH_ERROR_RATE = "high_error_rate"
    POOL_EXHAUSTION = "pool_exhaustion"
    SLOW_QUERY = "slow_query"
    CONNECTION_TIMEOUT = "connection_timeout"


@dataclass
class ConnectionMetrics:
    """Individual connection metrics."""

    connection_id: str
    created_at: float
    last_activity: float
    status: ConnectionStatus
    queries_executed: int
    total_time_ms: float
    avg_query_time_ms: float
    error_count: int
    transaction_count: int
    bytes_sent: int
    bytes_received: int
    backend_pid: Optional[int] = None
    application_name: str = ""
    client_addr: Optional[str] = None


@dataclass
class PoolMetrics:
    """Connection pool metrics."""

    pool_size: int
    active_connections: int
    idle_connections: int
    waiting_requests: int
    total_acquires: int
    total_releases: int
    avg_wait_time_ms: float
    max_wait_time_ms: float
    connection_errors: int
    timeouts: int
    utilization_pct: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConnectionAlert:
    """Connection monitoring alert."""

    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    connection_id: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None


class ConnectionMonitor:
    """Advanced database connection monitoring system."""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        alert_manager: Optional[Any] = None,
        monitoring_interval_seconds: float = 30.0,
    ):
        self.db_pool = db_pool
        self.alert_manager = alert_manager or get_alert_manager()
        self.monitoring_interval = monitoring_interval_seconds

        # Connection tracking
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.pool_metrics_history: deque[PoolMetrics] = deque(maxlen=1000)
        self.active_alerts: Dict[str, ConnectionAlert] = {}

        # Monitoring configuration
        self.config = {
            "max_connection_age_seconds": 3600,  # 1 hour
            "max_idle_time_seconds": 300,  # 5 minutes
            "slow_query_threshold_ms": 1000,
            "high_connection_count_threshold": 0.8,  # 80% of pool size
            "error_rate_threshold": 0.05,  # 5%
            "enable_connection_tracking": True,
            "enable_query_tracking": True,
            "enable_performance_alerts": True,
        }

        # Monitoring state
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # Statistics
        self.total_connections_created = 0
        self.total_connections_closed = 0
        self.total_queries_executed = 0
        self.total_errors = 0

    async def start_monitoring(self) -> None:
        """Start connection monitoring."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("Started connection monitoring")

    async def stop_monitoring(self) -> None:
        """Stop connection monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None

        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

        logger.info("Stopped connection monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                await self._collect_pool_metrics()
                await self._check_connection_health()
                await self._analyze_connection_patterns()
                await self._check_alert_conditions()

                await asyncio.sleep(self.monitoring_interval_seconds)

            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval_seconds)

    async def _cleanup_loop(self) -> None:
        """Cleanup loop for old connections."""
        while True:
            try:
                await self._cleanup_old_connections()
                await self._cleanup_old_alerts()

                # Run cleanup every 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"Connection cleanup error: {e}")
                await asyncio.sleep(300)

    async def _collect_pool_metrics(self) -> None:
        """Collect connection pool metrics."""
        try:
            pool_size = self.db_pool.get_size()
            idle_size = self.db_pool.get_idle_size()
            active_size = pool_size - idle_size

            # Calculate utilization
            utilization = (active_size / pool_size) * 100 if pool_size > 0 else 0

            metrics = PoolMetrics(
                pool_size=pool_size,
                active_connections=active_size,
                idle_connections=idle_size,
                waiting_requests=0,  # Would need to be tracked separately
                total_acquires=self.total_connections_created,
                total_releases=self.total_connections_closed,
                avg_wait_time_ms=0.0,  # Would need to be tracked
                max_wait_time_ms=0.0,  # Would need to be tracked
                connection_errors=self.total_errors,
                timeouts=0,  # Would need to be tracked
                utilization_pct=utilization,
            )

            self.pool_metrics_history.append(metrics)

        except Exception as e:
            logger.error(f"Failed to collect pool metrics: {e}")

    async def _check_connection_health(self) -> None:
        """Check health of individual connections."""
        if not self.config["enable_connection_tracking"]:
            return

        current_time = time.time()

        async with self._lock:
            for connection_id, metrics in list(self.connection_metrics.items()):
                # Check for long-lived connections
                connection_age = current_time - metrics.created_at
                if connection_age > self.config["max_connection_age_seconds"]:
                    await self._create_alert(
                        AlertType.LONG_LIVED_CONNECTION,
                        AlertSeverity.WARNING,
                        f"Long-lived connection detected: {connection_age:.1f}s old",
                        connection_id=connection_id,
                        properties={"age_seconds": connection_age},
                    )

                # Check for idle connections
                idle_time = current_time - metrics.last_activity
                if idle_time > self.config["max_idle_time_seconds"]:
                    await self._create_alert(
                        AlertType.LONG_LIVED_CONNECTION,
                        AlertSeverity.INFO,
                        f"Idle connection detected: {idle_time:.1f}s idle",
                        connection_id=connection_id,
                        properties={"idle_time_seconds": idle_time},
                    )

                # Check for high error rate
                if metrics.queries_executed > 0:
                    error_rate = metrics.error_count / metrics.queries_executed
                    if error_rate > self.config["error_rate_threshold"]:
                        await self._create_alert(
                            AlertType.HIGH_ERROR_RATE,
                            AlertSeverity.ERROR,
                            f"High error rate: {error_rate:.2%}",
                            connection_id=connection_id,
                            properties={
                                "error_rate": error_rate,
                                "errors": metrics.error_count,
                            },
                        )

    async def _analyze_connection_patterns(self) -> None:
        """Analyze connection usage patterns."""
        current_time = time.time()

        async with self._lock:
            # Update connection statuses based on activity
            for connection_id, metrics in self.connection_metrics.items():
                time_since_activity = current_time - metrics.last_activity

                if time_since_activity < 1.0:  # Active in last second
                    metrics.status = ConnectionStatus.ACTIVE
                elif metrics.transaction_count > 0:
                    metrics.status = ConnectionStatus.IN_TRANSACTION
                else:
                    metrics.status = ConnectionStatus.IDLE

    async def _check_alert_conditions(self) -> None:
        """Check for alert conditions."""
        current_metrics = (
            self.pool_metrics_history[-1] if self.pool_metrics_history else None
        )

        if not current_metrics:
            return

        # Check for high connection count
        if (
            current_metrics.utilization_pct
            > self.config["high_connection_count_threshold"] * 100
        ):
            await self._create_alert(
                AlertType.HIGH_CONNECTION_COUNT,
                AlertSeverity.WARNING,
                f"High connection utilization: {current_metrics.utilization_pct:.1f}%",
                metrics={
                    "utilization_pct": current_metrics.utilization_pct,
                    "active_connections": current_metrics.active_connections,
                    "pool_size": current_metrics.pool_size,
                },
            )

        # Check for pool exhaustion
        if current_metrics.active_connections >= current_metrics.pool_size * 0.95:
            await self._create_alert(
                AlertType.POOL_EXHAUSTION,
                AlertSeverity.CRITICAL,
                f"Connection pool nearly exhausted: {current_metrics.active_connections}/{current_metrics.pool_size}",
                metrics={
                    "active_connections": current_metrics.active_connections,
                    "pool_size": current_metrics.pool_size,
                    "utilization_pct": current_metrics.utilization_pct,
                },
            )

    async def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        connection_id: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create and handle connection alert."""
        import uuid

        alert_id = f"conn_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        alert = ConnectionAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            connection_id=connection_id,
            metrics=metrics or {},
        )

        # Check if similar alert already exists
        existing_alert = self._find_existing_alert(alert_type, connection_id)
        if existing_alert:
            # Update existing alert
            existing_alert.metrics.update(alert.metrics)
            existing_alert.created_at = time.time()
        else:
            # Create new alert
            self.active_alerts[alert_id] = alert

            # Trigger external alert
            await self.alert_manager.trigger_alert(
                name=f"connection_{alert_type.value}",
                severity=severity,
                message=message,
                context=alert.metrics,
            )

            logger.warning(f"Connection alert created: {alert_type.value} - {message}")

    def _find_existing_alert(
        self, alert_type: AlertType, connection_id: Optional[str]
    ) -> Optional[ConnectionAlert]:
        """Find existing alert of the same type."""
        for alert in self.active_alerts.values():
            if (
                alert.alert_type == alert_type
                and alert.connection_id == connection_id
                and not alert.resolved
            ):
                return alert
        return None

    async def _cleanup_old_connections(self) -> int:
        """Clean up old connection metrics."""
        current_time = time.time()
        cleaned_count = 0

        async with self._lock:
            connections_to_remove = []

            for connection_id, metrics in self.connection_metrics.items():
                # Remove connections closed for more than 1 hour
                if (
                    metrics.status == ConnectionStatus.CLOSED
                    and current_time - metrics.last_activity > 3600
                ):
                    connections_to_remove.append(connection_id)

            for connection_id in connections_to_remove:
                del self.connection_metrics[connection_id]
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old connection metrics")

        return cleaned_count

    async def _cleanup_old_alerts(self) -> int:
        """Clean up old resolved alerts."""
        current_time = time.time()
        cleaned_count = 0

        alerts_to_remove = []

        for alert_id, alert in self.active_alerts.items():
            # Remove alerts resolved more than 1 hour ago
            if (
                alert.resolved
                and alert.resolved_at
                and current_time - alert.resolved_at > 3600
            ):
                alerts_to_remove.append(alert_id)

        for alert_id in alerts_to_remove:
            del self.active_alerts[alert_id]
            cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old alerts")

        return cleaned_count

    async def track_connection_created(self, connection_id: str) -> None:
        """Track new connection creation."""
        if not self.config["enable_connection_tracking"]:
            return

        async with self._lock:
            self.connection_metrics[connection_id] = ConnectionMetrics(
                connection_id=connection_id,
                created_at=time.time(),
                last_activity=time.time(),
                status=ConnectionStatus.IDLE,
                queries_executed=0,
                total_time_ms=0.0,
                avg_query_time_ms=0.0,
                error_count=0,
                transaction_count=0,
                bytes_sent=0,
                bytes_received=0,
            )

        self.total_connections_created += 1

    async def track_connection_closed(self, connection_id: str) -> None:
        """Track connection closure."""
        async with self._lock:
            if connection_id in self.connection_metrics:
                self.connection_metrics[connection_id].status = ConnectionStatus.CLOSED
                self.connection_metrics[connection_id].last_activity = time.time()

        self.total_connections_closed += 1

    async def track_query_executed(
        self, connection_id: str, query_time_ms: float, error: bool = False
    ) -> None:
        """Track query execution."""
        if not self.config["enable_query_tracking"]:
            return

        async with self._lock:
            if connection_id in self.connection_metrics:
                metrics = self.connection_metrics[connection_id]

                # Update query metrics
                metrics.queries_executed += 1
                metrics.total_time_ms += query_time_ms
                metrics.last_activity = time.time()

                # Update average query time
                if metrics.queries_executed == 1:
                    metrics.avg_query_time_ms = query_time_ms
                else:
                    metrics.avg_query_time_ms = (
                        metrics.avg_query_time_ms * (metrics.queries_executed - 1)
                        + query_time_ms
                    ) / metrics.queries_executed

                # Update status
                metrics.status = ConnectionStatus.ACTIVE

                # Track errors
                if error:
                    metrics.error_count += 1
                    self.total_errors += 1

                    # Check for slow query alert
                    if query_time_ms > self.config["slow_query_threshold_ms"]:
                        await self._create_alert(
                            AlertType.SLOW_QUERY,
                            AlertSeverity.WARNING,
                            f"Slow query detected: {query_time_ms:.1f}ms",
                            connection_id=connection_id,
                            properties={"query_time_ms": query_time_ms},
                        )

                self.total_queries_executed += 1

    async def track_transaction_started(self, connection_id: str) -> None:
        """Track transaction start."""
        async with self._lock:
            if connection_id in self.connection_metrics:
                self.connection_metrics[connection_id].transaction_count += 1
                self.connection_metrics[
                    connection_id
                ].status = ConnectionStatus.IN_TRANSACTION

    async def track_transaction_ended(self, connection_id: str) -> None:
        """Track transaction end."""
        async with self._lock:
            if connection_id in self.connection_metrics:
                metrics = self.connection_metrics[connection_id]
                metrics.transaction_count = max(0, metrics.transaction_count - 1)

                if metrics.transaction_count == 0:
                    metrics.status = ConnectionStatus.ACTIVE

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics."""
        stats = {
            "total_connections_created": self.total_connections_created,
            "total_connections_closed": self.total_connections_closed,
            "total_queries_executed": self.total_queries_executed,
            "total_errors": self.total_errors,
            "active_connections": len(self.connection_metrics),
            "active_alerts": len(self.active_alerts),
            "error_rate": 0.0,
            "avg_queries_per_connection": 0.0,
            "connection_status_distribution": defaultdict(int),
            "pool_metrics": {},
        }

        # Calculate error rate
        if self.total_queries_executed > 0:
            stats["error_rate"] = (
                self.total_errors / self.total_queries_executed
            ) * 100

        # Calculate average queries per connection
        if self.connection_metrics:
            total_queries = sum(
                m.queries_executed for m in self.connection_metrics.values()
            )
            stats["avg_queries_per_connection"] = total_queries / len(
                self.connection_metrics
            )

            # Status distribution
            for metrics in self.connection_metrics.values():
                stats["connection_status_distribution"][metrics.status.value] += 1

        # Latest pool metrics
        if self.pool_metrics_history:
            latest_metrics = self.pool_metrics_history[-1]
            stats["pool_metrics"] = {
                "pool_size": latest_metrics.pool_size,
                "active_connections": latest_metrics.active_connections,
                "idle_connections": latest_metrics.idle_connections,
                "utilization_pct": latest_metrics.utilization_pct,
                "total_acquires": latest_metrics.total_acquires,
                "total_releases": latest_metrics.total_releases,
                "connection_errors": latest_metrics.connection_errors,
            }

        # Alert summary
        stats["alerts"] = {
            "total_active": len(self.active_alerts),
            "by_type": defaultdict(int),
            "by_severity": defaultdict(int),
        }

        for alert in self.active_alerts.values():
            stats["alerts"]["by_type"][alert.alert_type.value] += 1
            stats["alerts"]["by_severity"][alert.severity.value] += 1

        return dict(stats)

    def get_connection_details(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific connection."""
        async with self._lock:
            metrics = self.connection_metrics.get(connection_id)
            if not metrics:
                return None

            return {
                "connection_id": metrics.connection_id,
                "created_at": metrics.created_at,
                "last_activity": metrics.last_activity,
                "status": metrics.status.value,
                "age_seconds": time.time() - metrics.created_at,
                "idle_time_seconds": time.time() - metrics.last_activity,
                "queries_executed": metrics.queries_executed,
                "total_time_ms": metrics.total_time_ms,
                "avg_query_time_ms": metrics.avg_query_time_ms,
                "error_count": metrics.error_count,
                "transaction_count": metrics.transaction_count,
                "error_rate": (metrics.error_count / max(metrics.queries_executed, 1))
                * 100,
                "backend_pid": metrics.backend_pid,
                "application_name": metrics.application_name,
                "client_addr": metrics.client_addr,
            }

    def get_active_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get active connection alerts."""
        alerts = list(self.active_alerts.values())

        # Sort by creation time (newest first)
        alerts.sort(key=lambda a: a.created_at, reverse=True)

        # Convert to dict format
        alert_dicts = []
        for alert in alerts[:limit]:
            alert_dicts.append(
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "connection_id": alert.connection_id,
                    "metrics": alert.metrics,
                    "created_at": alert.created_at,
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at,
                }
            )

        return alert_dicts

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.active_alerts[alert_id].resolved_at = time.time()

            logger.info(f"Resolved connection alert: {alert_id}")
            return True

        return False

    def update_config(self, **kwargs) -> None:
        """Update monitoring configuration."""
        for key, value in kwargs.items():
            if key in self.config:
                old_value = self.config[key]
                self.config[key] = value
                logger.info(f"Updated monitoring config {key}: {old_value} -> {value}")

    def get_pool_metrics_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get pool metrics history."""
        cutoff_time = time.time() - (minutes * 60)

        history = []
        for metrics in self.pool_metrics_history:
            if metrics.timestamp >= cutoff_time:
                history.append(
                    {
                        "timestamp": metrics.timestamp,
                        "pool_size": metrics.pool_size,
                        "active_connections": metrics.active_connections,
                        "idle_connections": metrics.idle_connections,
                        "utilization_pct": metrics.utilization_pct,
                        "total_acquires": metrics.total_acquires,
                        "total_releases": metrics.total_releases,
                        "avg_wait_time_ms": metrics.avg_wait_time_ms,
                        "max_wait_time_ms": metrics.max_wait_time_ms,
                        "connection_errors": metrics.connection_errors,
                    }
                )

        return history


# Global connection monitor instance
_connection_monitor: ConnectionMonitor | None = None


def get_connection_monitor() -> ConnectionMonitor:
    """Get global connection monitor instance."""
    global _connection_monitor
    if _connection_monitor is None:
        raise RuntimeError(
            "Connection monitor not initialized. Call init_connection_monitor() first."
        )
    return _connection_monitor


async def init_connection_monitor(
    db_pool: asyncpg.Pool,
    alert_manager: Optional[Any] = None,
    monitoring_interval_seconds: float = 30.0,
) -> ConnectionMonitor:
    """Initialize global connection monitor."""
    global _connection_monitor
    _connection_monitor = ConnectionMonitor(
        db_pool, alert_manager, monitoring_interval_seconds
    )
    await _connection_monitor.start_monitoring()
    return _connection_monitor
