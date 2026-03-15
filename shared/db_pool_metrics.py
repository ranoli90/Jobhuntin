"""Database connection pool metrics collection and analysis system.

Provides:
- Real-time pool metrics
- Performance analytics
- Historical data tracking
- Alert generation
- Trend analysis

Usage:
    from shared.db_pool_metrics import PoolMetricsCollector

    collector = PoolMetricsCollector(pool_manager)
    metrics = await collector.collect_metrics()
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import asyncpg

from shared.alerting import AlertSeverity, get_alert_manager
from shared.logging_config import get_logger

logger = get_logger("sorce.db_pool_metrics")


class MetricType(Enum):
    """Pool metric types."""

    CONNECTION_COUNT = "connection_count"
    ACTIVE_CONNECTIONS = "active_connections"
    IDLE_CONNECTIONS = "idle_connections"
    WAIT_TIME = "wait_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    UTILIZATION = "utilization"
    LIFETIME = "lifetime"


@dataclass
class PoolMetricSnapshot:
    """Pool metric snapshot at a point in time."""

    timestamp: float
    pool_id: str
    pool_size: int
    active_connections: int
    idle_connections: int
    waiting_requests: int
    total_acquires: int
    total_releases: int
    avg_wait_time_ms: float
    max_wait_time_ms: float
    min_wait_time_ms: float
    total_queries: int
    total_errors: int
    avg_query_time_ms: float
    max_query_time_ms: float
    min_query_time_ms: float
    bytes_sent: int
    bytes_received: int
    connection_errors: int
    timeouts: int
    utilization_pct: float


@dataclass
class PoolMetricsSummary:
    """Summary of pool metrics over a time period."""

    pool_id: str
    period_start: float
    period_end: float
    total_snapshots: int

    # Connection metrics
    avg_pool_size: float
    avg_active_connections: float
    avg_idle_connections: float
    max_active_connections: int
    max_idle_connections: int

    # Performance metrics
    avg_wait_time_ms: float
    max_wait_time_ms: float
    avg_query_time_ms: float
    max_query_time_ms: float
    avg_utilization_pct: float
    max_utilization_pct: float

    # Throughput metrics
    total_queries: int
    total_errors: int
    error_rate_pct: float
    queries_per_second: float
    throughput_mb_per_second: float

    # Error metrics
    connection_errors: int
    timeouts: int
    error_rate_trend: str  # "improving", "stable", "degrading"


@dataclass
class MetricsAlert:
    """Metrics alert."""

    alert_id: str
    alert_type: str
    severity: AlertSeverity
    pool_id: str
    message: str
    metric_value: float
    threshold_value: float
    created_at: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None


class PoolMetricsCollector:
    """Database connection pool metrics collection system."""

    def __init__(
        self,
        pool_manager,
        alert_manager: Optional[Any] = None,
        collection_interval_seconds: float = 30.0,
        history_retention_hours: float = 24.0,
    ):
        self.pool_manager = pool_manager
        self.alert_manager = alert_manager or get_alert_manager()
        self.collection_interval = collection_interval_seconds
        self.history_retention = history_retention_hours * 3600  # Convert to seconds

        # Metrics storage
        self.metrics_history: Dict[str, deque[PoolMetricSnapshot]] = defaultdict(
            lambda: deque(
                maxlen=int(self.history_retention / self.collection_interval_seconds)
            )
        )
        self.active_alerts: Dict[str, MetricsAlert] = {}

        # Alert thresholds
        self.thresholds = {
            "max_wait_time_ms": 1000.0,
            "avg_wait_time_ms": 100.0,
            "max_utilization_pct": 90.0,
            "avg_utilization_pct": 80.0,
            "error_rate_pct": 5.0,
            "connection_errors_per_minute": 10,
            "timeouts_per_hour": 5,
            "queries_per_second_low": 1.0,
            "queries_per_second_high": 1000.0,
        }

        # Collection state
        self._collection_task: Optional[asyncio.Task] = None
        self._analysis_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start_collection(self) -> None:
        """Start metrics collection."""
        if self._collection_task is None:
            self._collection_task = asyncio.create_task(self._collection_loop())

        if self._analysis_task is None:
            self._analysis_task = asyncio.create_task(self._analysis_loop())

        logger.info("Started pool metrics collection")

    async def stop_collection(self) -> None:
        """Stop metrics collection."""
        if self._collection_task:
            self._collection_task.cancel()
            self._collection_task = None

        if self._analysis_task:
            self._analysis_task.cancel()
            self._analysis_task = None

        logger.info("Stopped pool metrics collection")

    async def _collection_loop(self) -> None:
        """Main metrics collection loop."""
        while True:
            try:
                await self._collect_all_pool_metrics()
                await asyncio.sleep(self.collection_interval_seconds)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval_seconds)

    async def _analysis_loop(self) -> None:
        """Metrics analysis and alerting loop."""
        while True:
            try:
                await self._analyze_metrics_and_alerts()
                await asyncio.sleep(60)  # Analyze every minute
            except Exception as e:
                logger.error(f"Metrics analysis error: {e}")
                await asyncio.sleep(60)

    async def _collect_all_pool_metrics(self) -> None:
        """Collect metrics from all pools."""
        current_time = time.time()

        for pool_id, pool_info in self.pool_manager.pool_info.items():
            try:
                snapshot = await self._collect_pool_metrics(
                    pool_id, pool_info.pool, current_time, pool_info
                )

                async with self._lock:
                    self.metrics_history[pool_id].append(snapshot)

            except Exception as e:
                logger.error(f"Failed to collect metrics for pool {pool_id}: {e}")

    async def _collect_pool_metrics(
        self,
        pool_id: str,
        pool: asyncpg.Pool,
        timestamp: float,
        pool_info: Any = None,
    ) -> PoolMetricSnapshot:
        """Collect metrics from a specific pool."""
        # Get basic pool statistics
        pool_size = pool.get_size()
        idle_size = pool.get_idle_size()
        active_size = pool_size - idle_size

        # Use pool_info if available, else defaults
        resp_ms = getattr(pool_info, "response_time_ms", 0.0) if pool_info else 0.0
        q_count = getattr(pool_info, "query_count", 0) if pool_info else 0
        err_count = getattr(pool_info, "error_count", 0) if pool_info else 0
        conn_count = getattr(pool_info, "connection_count", 0) if pool_info else 0

        avg_wait_time = resp_ms
        max_wait_time = resp_ms
        min_wait_time = resp_ms
        total_queries = q_count
        total_errors = err_count
        avg_query_time = resp_ms
        max_query_time = resp_ms
        min_query_time = resp_ms

        # Calculate utilization
        utilization = (active_size / pool_size) * 100 if pool_size > 0 else 0

        # Calculate error rate
        (total_errors / max(total_queries, 1)) * 100

        # Create snapshot
        snapshot = PoolMetricSnapshot(
            timestamp=timestamp,
            pool_id=pool_id,
            pool_size=pool_size,
            active_connections=active_size,
            idle_connections=idle_size,
            waiting_requests=0,  # Would need to be tracked
            total_acquires=conn_count,
            total_releases=conn_count,
            avg_wait_time_ms=avg_wait_time,
            max_wait_time_ms=max_wait_time,
            min_wait_time_ms=min_wait_time,
            total_queries=total_queries,
            total_errors=total_errors,
            avg_query_time_ms=avg_query_time,
            max_query_time_ms=max_query_time,
            min_query_time_ms=min_query_time,
            bytes_sent=0,  # Would need to be tracked
            bytes_received=0,  # Would need to be tracked
            connection_errors=total_errors,
            timeouts=0,  # Would need to be tracked
            utilization_pct=utilization,
        )

        return snapshot

    async def _analyze_metrics_and_alerts(self) -> None:
        """Analyze metrics and generate alerts."""
        current_time = time.time()

        for pool_id, history in self.metrics_history.items():
            if not history:
                continue

            # Get recent snapshots (last 5 minutes)
            recent_snapshots = [
                snapshot
                for snapshot in history
                if current_time - snapshot.timestamp <= 300
            ]

            if len(recent_snapshots) < 2:
                continue

            # Calculate recent averages
            recent_avg = self._calculate_averages(recent_snapshots)

            # Check alert conditions
            await self._check_alert_conditions(
                pool_id, recent_avg, recent_snapshots[-1]
            )

            # Check trends
            if len(history) >= 10:
                await self._check_trends(pool_id, history)

    def _calculate_averages(
        self, snapshots: List[PoolMetricSnapshot]
    ) -> Dict[str, float]:
        """Calculate average values from snapshots."""
        if not snapshots:
            return {}

        averages = {
            "pool_size": sum(s.pool_size for s in snapshots) / len(snapshots),
            "active_connections": sum(s.active_connections for s in snapshots)
            / len(snapshots),
            "idle_connections": sum(s.idle_connections for s in snapshots)
            / len(snapshots),
            "avg_wait_time_ms": sum(s.avg_wait_time_ms for s in snapshots)
            / len(snapshots),
            "max_wait_time_ms": max(s.max_wait_time_ms for s in snapshots),
            "min_wait_time_ms": min(s.min_wait_time_ms for s in snapshots),
            "total_queries": sum(s.total_queries for s in snapshots),
            "total_errors": sum(s.total_errors for s in snapshots) / len(snapshots),
            "avg_query_time_ms": sum(s.avg_query_time_ms for s in snapshots)
            / len(snapshots),
            "max_query_time_ms": max(s.max_query_time_ms for s in snapshots),
            "min_query_time_ms": min(s.min_query_time_ms for s in snapshots),
            "utilization_pct": sum(s.utilization_pct for s in snapshots)
            / len(snapshots),
        }

        return averages

    async def _check_alert_conditions(
        self,
        pool_id: str,
        averages: Dict[str, float],
        latest_snapshot: PoolMetricSnapshot,
    ) -> None:
        """Check for alert conditions."""
        alerts_to_check = [
            ("max_wait_time_ms", AlertSeverity.ERROR),
            ("avg_wait_time_ms", AlertSeverity.WARNING),
            ("max_utilization_pct", AlertSeverity.WARNING),
            ("avg_utilization_pct", AlertSeverity.INFO),
            ("error_rate_pct", AlertSeverity.ERROR),
            ("queries_per_second", AlertSeverity.WARNING),
        ]

        for metric_name, severity in alerts_to_check:
            if metric_name in averages:
                value = averages[metric_name]
                threshold = self.thresholds.get(metric_name)

                if threshold and value > threshold:
                    await self._create_alert(
                        pool_id,
                        f"high_{metric_name}",
                        severity,
                        f"High {metric_name}: {value:.2f} (threshold: {threshold})",
                    )

    async def _check_trends(
        self, pool_id: str, history: deque[PoolMetricSnapshot]
    ) -> None:
        """Check for trends in metrics."""
        if len(history) < 10:
            return

        # Compare recent vs older periods
        recent_snapshots = list(history)[-5:]  # Last 5 snapshots
        older_snapshots = list(history)[:5]  # First 5 snapshots

        recent_avg = self._calculate_averages(recent_snapshots)
        older_avg = self._calculate_averages(older_snapshots)

        # Check for degrading trends
        for metric_name in ["avg_wait_time_ms", "error_rate_pct", "utilization_pct"]:
            if metric_name in recent_avg and metric_name in older_avg:
                recent_value = recent_avg[metric_name]
                older_value = older_avg[metric_name]

                # Check for significant degradation (>20% increase)
                if older_value > 0 and recent_value > older_value * 1.2:
                    await self._create_alert(
                        pool_id,
                        f"degrading_{metric_name}",
                        AlertSeverity.WARNING,
                        f"Degrading {metric_name}: {recent_value:.2f} vs {older_value:.2f} (
    {((recent_value / older_value - 1) * 100):.1f}% increase)",
                    )
                # Check for significant improvement (>20% decrease)
                elif older_value > 0 and recent_value < older_value * 0.8:
                    await self._create_alert(
                        pool_id,
                        f"improving_{metric_name}",
                        AlertSeverity.INFO,
                        f"Improving {metric_name}: {recent_value:.2f} vs {older_value:.2f} (
    {((older_value / recent_value - 1) * 100):.1f}% decrease)",
                    )

    async def _create_alert(
        self, pool_id: str, alert_type: str, severity: AlertSeverity, message: str
    ) -> None:
        """Create and handle metrics alert."""
        import uuid

        alert_id = f"metrics_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        alert = MetricsAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            pool_id=pool_id,
            message=message,
            created_at=time.time(),
        )

        # Check if similar alert already exists
        existing_alert = self._find_existing_alert(pool_id, alert_type)
        if existing_alert:
            # Update existing alert
            existing_alert.created_at = time.time()
        else:
            # Create new alert
            self.active_alerts[alert_id] = alert

            # Trigger external alert
            await self.alert_manager.trigger_alert(
                name=f"pool_metrics_{alert_type}",
                severity=severity,
                message=f"Pool {pool_id}: {message}",
                context={"pool_id": pool_id, "alert_type": alert_type},
            )

            logger.warning(f"Pool metrics alert created: {alert_type} - {message}")

    def _find_existing_alert(
        self, pool_id: str, alert_type: str
    ) -> Optional[MetricsAlert]:
        """Find existing alert of the same type."""
        for alert in self.active_alerts.values():
            if (
                alert.pool_id == pool_id
                and alert.alert_type == alert_type
                and not alert.resolved
            ):
                return alert
        return None

    async def collect_metrics(self, pool_id: str) -> Optional[PoolMetricSnapshot]:
        """Collect current metrics for a specific pool."""
        pool_info = self.pool_manager.pool_info.get(pool_id)
        if not pool_info:
            return None

        try:
            return await self._collect_pool_metrics(
                pool_id, pool_info.pool, time.time()
            )
        except Exception as e:
            logger.error(f"Failed to collect metrics for pool {pool_id}: {e}")
            return None

    def get_pool_metrics(
        self, pool_id: str, minutes: int = 60
    ) -> List[PoolMetricSnapshot]:
        """Get metrics history for a specific pool."""
        cutoff_time = time.time() - (minutes * 60)

        return [
            snapshot
            for snapshot in self.metrics_history.get(pool_id, [])
            if snapshot.timestamp >= cutoff_time
        ]

    def get_summary(
        self, pool_id: str, minutes: int = 60
    ) -> Optional[PoolMetricsSummary]:
        """Get summary statistics for a pool."""
        cutoff_time = time.time() - (minutes * 60)

        history = self.metrics_history.get(pool_id)
        if not history:
            return None

        # Filter snapshots within time range
        relevant_snapshots = [
            snapshot for snapshot in history if snapshot.timestamp >= cutoff_time
        ]

        if not relevant_snapshots:
            return None

        # Calculate summary
        period_start = relevant_snapshots[0].timestamp
        period_end = relevant_snapshots[-1].timestamp

        averages = self._calculate_averages(relevant_snapshots)

        # Calculate additional metrics
        total_queries = sum(s.total_queries for s in relevant_snapshots)
        total_errors = sum(s.total_errors for s in relevant_snapshots)
        period_duration = period_end - period_start

        queries_per_second = total_queries / max(period_duration, 1)

        # Estimate throughput (assuming 1KB per query)
        throughput_mb_per_second = (queries_per_second * 1024) / (
            1024 * 1024
        )  # Convert to MB

        # Determine trend
        error_rate_trend = "stable"
        if len(history) >= 20:
            recent_rate = self._calculate_averages(list(history)[-10:]).get(
                "error_rate_pct", 0
            )
            older_rate = self._calculate_averages(list(history)[:10]).get(
                "error_rate_pct", 0
            )

            if recent_rate > older_rate * 1.1:
                error_rate_trend = "degrading"
            elif recent_rate < older_rate * 0.9:
                error_rate_trend = "improving"

        return PoolMetricsSummary(
            pool_id=pool_id,
            period_start=period_start,
            period_end=period_end,
            total_snapshots=len(relevant_snapshots),
            avg_pool_size=averages["pool_size"],
            avg_active_connections=averages["active_connections"],
            avg_idle_connections=averages["idle_connections"],
            max_active_connections=max(
                s.active_connections for s in relevant_snapshots
            ),
            max_idle_connections=max(s.idle_connections for s in relevant_snapshots),
            avg_wait_time_ms=averages["avg_wait_time_ms"],
            max_wait_time_ms=averages["max_wait_time_ms"],
            avg_query_time_ms=averages["avg_query_time_ms"],
            max_query_time_ms=averages["max_query_time_ms"],
            avg_utilization_pct=averages["utilization_pct"],
            max_utilization_pct=averages["max_utilization_pct"],
            total_queries=total_queries,
            total_errors=total_errors,
            error_rate_pct=averages["error_rate_pct"],
            queries_per_second=queries_per_second,
            throughput_mb_per_second=throughput_mb_per_second,
            error_rate_trend=error_rate_trend,
        )

    def get_all_summaries(self, minutes: int = 60) -> Dict[str, PoolMetricsSummary]:
        """Get summaries for all pools."""
        summaries = {}

        for pool_id in self.metrics_history:
            summary = self.get_summary(pool_id, minutes)
            if summary:
                summaries[pool_id] = summary

        return summaries

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get active metrics alerts."""
        alerts = list(self.active_alerts.values())

        # Sort by creation time (newest first)
        alerts.sort(key=lambda a: a.created_at, reverse=True)

        # Convert to dict format
        alert_dicts = []
        for alert in alerts[:limit]:
            alert_dicts.append(
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity.value,
                    "pool_id": alert.pool_id,
                    "message": alert.message,
                    "metric_value": alert.metric_value,
                    "threshold_value": alert.threshold_value,
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

            logger.info(f"Resolved pool metrics alert: {alert_id}")
            return True

        return False

    def update_thresholds(self, **kwargs) -> None:
        """Update alert thresholds."""
        for key, value in kwargs.items():
            if key in self.thresholds:
                old_value = self.thresholds[key]
                self.thresholds[key] = value
                logger.info(f"Updated metrics threshold {key}: {old_value} -> {value}")

    def get_metrics_overview(self) -> Dict[str, Any]:
        """Get overview of all pool metrics."""
        overview = {
            "total_pools": len(self.pool_manager.pool_info),
            "healthy_pools": len(self.pool_manager.healthy_pools),
            "disabled_pools": len(self.pool_manager.disabled_pools),
            "active_alerts": len(self.active_alerts),
            "total_snapshots_collected": sum(
                len(history) for history in self.metrics_history.values()
            ),
            "collection_interval_seconds": self.collection_interval_seconds,
            "history_retention_hours": self.history_retention / 3600,
            "thresholds": self.thresholds,
        }

        # Add current averages across all pools
        if self.metrics_history:
            all_recent_snapshots = []
            for history in self.metrics_history.values():
                # Get last 5 snapshots from each pool
                recent = list(history)[-5:]
                all_recent_snapshots.extend(recent)

            if all_recent_snapshots:
                global_averages = self._calculate_averages(all_recent_snapshots)
                overview["global_averages"] = global_averages

        return overview


# Global metrics collector instance
_metrics_collector: PoolMetricsCollector | None = None


def get_metrics_collector() -> PoolMetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        raise RuntimeError(
            "Metrics collector not initialized. Call init_metrics_collector() first."
        )
    return _metrics_collector


async def init_metrics_collector(
    pool_manager,
    alert_manager: Optional[Any] = None,
    collection_interval_seconds: float = 30.0,
    history_retention_hours: float = 24.0,
) -> PoolMetricsCollector:
    """Initialize global metrics collector."""
    global _metrics_collector
    _metrics_collector = PoolMetricsCollector(
        pool_manager,
        alert_manager,
        collection_interval_seconds,
        history_retention_hours,
    )
    await _metrics_collector.start_collection()
    return _metrics_collector
