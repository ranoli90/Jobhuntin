"""
Performance Monitor for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

import psutil

from shared.logging_config import get_logger

logger = get_logger("sorce.performance_monitor")


class MetricType(Enum):
    """Types of performance metrics."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    APPLICATION = "application"
    CACHE = "cache"
    QUEUE = "queue"


class MetricCategory(Enum):
    """Categories of performance metrics."""

    SYSTEM = "system"
    DATABASE = "database"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    USER_EXPERIENCE = "user_experience"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Performance metric data point."""

    id: str
    tenant_id: str
    metric_type: MetricType
    metric_category: MetricCategory
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class PerformanceAlert:
    """Performance alert."""

    id: str
    tenant_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""

    id: str
    tenant_id: str
    metric_name: str
    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    comparison_operator: str  # gt, lt, eq, ne
    enabled: bool = True
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class PerformanceDashboard:
    """Performance dashboard data."""

    tenant_id: str
    period_hours: int
    system_metrics: Dict[str, Any]
    database_metrics: Dict[str, Any]
    application_metrics: Dict[str, Any]
    alerts: List[PerformanceAlert]
    trends: Dict[str, Any]
    health_score: float
    generated_at: datetime = datetime.now(timezone.utc)


class PerformanceMonitor:
    """Advanced performance monitoring and alerting system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._metrics_buffer: List[PerformanceMetric] = []
        self._alerts_buffer: List[PerformanceAlert] = []
        self._thresholds: Dict[str, PerformanceThreshold] = {}
        self._alert_handlers: Dict[str, callable] = []

        # Initialize default thresholds
        self._initialize_default_thresholds()

        # Start background monitoring
        asyncio.create_task(self._start_monitoring())
        asyncio.create_task(self._start_alert_processing())

    async def collect_metric(
        self,
        tenant_id: str,
        metric_type: MetricType,
        metric_category: MetricCategory,
        name: str,
        value: float,
        unit: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> PerformanceMetric:
        """Collect a performance metric."""
        try:
            # Create metric
            metric = PerformanceMetric(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                metric_type=metric_type,
                metric_category=metric_category,
                name=name,
                value=value,
                unit=unit,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
                tags=tags or [],
            )

            # Add to buffer
            self._metrics_buffer.append(metric)

            # Check thresholds
            await self._check_thresholds(metric)

            # Process buffer if it gets too large
            if len(self._metrics_buffer) > 1000:
                await self._process_metrics_buffer()

            return metric

        except Exception as e:
            logger.error(f"Failed to collect metric: {e}")
            raise

    async def create_threshold(
        self,
        tenant_id: str,
        metric_name: str,
        metric_type: MetricType,
        warning_threshold: float,
        critical_threshold: float,
        comparison_operator: str = "gt",
        enabled: bool = True,
    ) -> PerformanceThreshold:
        """Create a performance threshold."""
        try:
            threshold = PerformanceThreshold(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                metric_name=metric_name,
                metric_type=metric_type,
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
                comparison_operator=comparison_operator,
                enabled=enabled,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # Save threshold
            await self._save_threshold(threshold)

            # Update local cache
            threshold_key = f"{tenant_id}:{metric_name}"
            self._thresholds[threshold_key] = threshold

            logger.info(
                f"Created threshold: {metric_name} (warning: {warning_threshold}, critical: {critical_threshold})"
            )
            return threshold

        except Exception as e:
            logger.error(f"Failed to create threshold: {e}")
            raise

    async def get_metrics(
        self,
        tenant_id: str,
        metric_type: Optional[MetricType] = None,
        metric_category: Optional[MetricCategory] = None,
        time_period_hours: int = 1,
        limit: int = 100,
    ) -> List[PerformanceMetric]:
        """Get performance metrics."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Build query
            query = """
                SELECT * FROM performance_metrics
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if metric_type:
                query += " AND metric_type = $3"
                params.append(metric_type.value)

            if metric_category:
                query += " AND metric_category = $4"
                params.append(metric_category.value)

            query += " ORDER BY timestamp DESC LIMIT $5"
            params.append(limit)

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                metrics = []
                for row in results:
                    metric = PerformanceMetric(
                        id=row[0],
                        tenant_id=row[1],
                        metric_type=MetricType(row[2]),
                        metric_category=MetricCategory(row[3]),
                        name=row[4],
                        value=row[5],
                        unit=row[6],
                        timestamp=row[7],
                        metadata=json.loads(row[8]) if row[8] else {},
                        tags=json.loads(row[9]) if row[9] else [],
                    )
                    metrics.append(metric)

                return metrics

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []

    async def get_alerts(
        self,
        tenant_id: str,
        severity: Optional[AlertSeverity] = None,
        resolved: Optional[bool] = None,
        time_period_hours: int = 24,
        limit: int = 100,
    ) -> List[PerformanceAlert]:
        """Get performance alerts."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Build query
            query = """
                SELECT * FROM performance_alerts
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if severity:
                query += " AND severity = $3"
                params.append(severity.value)

            if resolved is not None:
                query += " AND resolved = $3"
                params.append(resolved)

            query += " ORDER BY timestamp DESC LIMIT $4"
            params.append(limit)

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                alerts = []
                for row in results:
                    alert = PerformanceAlert(
                        id=row[0],
                        tenant_id=row[1],
                        alert_type=row[2],
                        severity=AlertSeverity(row[3]),
                        title=row[4],
                        message=row[5],
                        metric_name=row[6],
                        current_value=row[7],
                        threshold_value=row[8],
                        timestamp=row[9],
                        resolved=row[10],
                        resolved_at=row[11],
                        metadata=json.loads(row[12]) if row[12] else {},
                    )
                    alerts.append(alert)

                return alerts

        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    async def get_dashboard(
        self,
        tenant_id: str,
        time_period_hours: int = 24,
    ) -> PerformanceDashboard:
        """Get comprehensive performance dashboard."""
        try:
            datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Get metrics for different categories
            system_metrics = await self._get_category_metrics(
                tenant_id, MetricCategory.SYSTEM, time_period_hours
            )
            database_metrics = await self._get_category_metrics(
                tenant_id, MetricCategory.DATABASE, time_period_hours
            )
            application_metrics = await self._get_category_metrics(
                tenant_id, MetricCategory.APPLICATION, time_period_hours
            )

            # Get alerts
            alerts = await self.get_alerts(
                tenant_id, time_period_hours=time_period_hours
            )

            # Get trends
            trends = await self._calculate_trends(tenant_id, time_period_hours)

            # Calculate health score
            health_score = await self._calculate_health_score(tenant_id)

            dashboard = PerformanceDashboard(
                tenant_id=tenant_id,
                period_hours=time_period_hours,
                system_metrics=system_metrics,
                database_metrics=database_metrics,
                application_metrics=application_metrics,
                alerts=alerts,
                trends=trends,
                health_score=health_score,
                generated_at=datetime.now(timezone.utc),
            )

            return dashboard

        except Exception as e:
            logger.error(f"Failed to get dashboard: {e}")
            raise

    async def register_alert_handler(
        self,
        alert_type: str,
        handler: callable,
    ) -> None:
        """Register an alert handler."""
        try:
            self._alert_handlers[alert_type] = handler
            logger.info(f"Registered alert handler for: {alert_type}")

        except Exception as e:
            logger.error(f"Failed to register alert handler: {e}")

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk metrics
            disk_usage = psutil.disk_usage("/")
            disk_partitions = psutil.disk_partitions()

            # Network metrics
            network_io = psutil.net_io_counters()

            # Process metrics
            process_count = len(psutil.pids())

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": cpu_freq.current if cpu_freq else 0,
                    "per_cpu": psutil.cpu_percent(percpu=True),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent,
                    "swap": {
                        "total": swap.total,
                        "used": swap.used,
                        "free": swap.free,
                        "percent": swap.percent,
                    },
                },
                "disk": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent,
                    "partitions": [
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": partition.total,
                            "used": partition.used,
                            "free": partition.free,
                            "percent": partition.percent,
                        }
                        for partition in disk_partitions
                    ],
                },
                "network": {
                    "bytes_sent": network_io.bytes_sent,
                    "bytes_recv": network_io.bytes_recv,
                    "packets_sent": network_io.packets_sent,
                    "packets_recv": network_io.packets_recv,
                    "errin": network_io.errin,
                    "errout": network_io.errout,
                    "dropin": network_io.dropin,
                    "dropout": network_io.dropout,
                },
                "process": {
                    "count": process_count,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}

    async def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        try:
            # Get connection pool metrics
            pool_metrics = await self._get_connection_pool_metrics()

            # Get database size
            db_size = await self._get_database_size()

            # Get query statistics
            query_stats = await self._get_query_statistics()

            # Get index statistics
            index_stats = await self._get_index_statistics()

            # Get cache statistics
            cache_stats = await self._get_cache_statistics()

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "connection_pool": pool_metrics,
                "database_size": db_size,
                "queries": query_stats,
                "indexes": index_stats,
                "cache": cache_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {}

    def _initialize_default_thresholds(self) -> None:
        """Initialize default performance thresholds."""
        try:
            # System thresholds
            default_thresholds = [
                PerformanceThreshold(
                    id=str(uuid.uuid4()),
                    tenant_id="default",
                    metric_name="cpu_percent",
                    metric_type=MetricType.CPU,
                    warning_threshold=70.0,
                    critical_threshold=90.0,
                    comparison_operator="gt",
                    enabled=True,
                ),
                PerformanceThreshold(
                    id=str(uuid4()),
                    tenant_id="default",
                    metric_name="memory_percent",
                    metric_type=MetricType.MEMORY,
                    warning_threshold=80.0,
                    critical_threshold=95.0,
                    comparison_operator="gt",
                    enabled=True,
                ),
                PerformanceThreshold(
                    id=str(uuid4()),
                    tenant_id="default",
                    metric_name="disk_percent",
                    metric_type=MetricType.DISK,
                    warning_threshold=80.0,
                    critical_threshold=95.0,
                    comparison_operator="gt",
                    enabled=True,
                ),
                PerformanceThreshold(
                    id=str(uuid4()),
                    tenant_id="default",
                    metric_name="connection_pool_utilization",
                    metric_type=MetricType.DATABASE,
                    warning_threshold=80.0,
                    critical_threshold=95.0,
                    comparison_operator="gt",
                    enabled=True,
                ),
                PerformanceThreshold(
                    id=str(uuid4()),
                    tenant_id="default",
                    metric_name="query_response_time",
                    metric_type=MetricType.DATABASE,
                    warning_threshold=1000.0,  # 1 second
                    critical_threshold=5000.0,  # 5 seconds
                    comparison_operator="gt",
                    enabled=True,
                ),
            ]

            # Store thresholds
            for threshold in default_thresholds:
                threshold_key = f"{threshold.tenant_id}:{threshold.metric_name}"
                self._thresholds[threshold_key] = threshold

        except Exception as e:
            logger.error(f"Failed to initialize default thresholds: {e}")

    async def _start_monitoring(self) -> None:
        """Start background performance monitoring."""
        try:
            while True:
                await asyncio.sleep(30)  # Run every 30 seconds

                # Collect system metrics
                await self._collect_system_metrics()

                # Collect database metrics
                await self._collect_database_metrics()

                # Process metrics buffer
                await self._process_metrics_buffer()

                # Process alerts buffer
                await self._process_alerts_buffer()

        except Exception as e:
            logger.error(f"Background monitoring failed: {e}")

    async def _start_alert_processing(self) -> None:
        """Start background alert processing."""
        try:
            while True:
                await asyncio.sleep(60)  # Run every minute

                # Process alerts
                await self._process_alerts_buffer()

                # Check for resolved alerts
                await self._check_resolved_alerts()

        except Exception as e:
            logger.error(f"Background alert processing failed: {e}")

    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            system_metrics = await self.get_system_metrics()

            # CPU metrics
            await self.collect_metric(
                tenant_id="system",
                metric_type=MetricType.CPU,
                metric_category=MetricCategory.SYSTEM,
                name="cpu_percent",
                value=system_metrics["cpu"]["percent"],
                unit="percent",
                metadata={"cpu_count": system_metrics["cpu"]["count"]},
                tags=["system", "cpu"],
            )

            # Memory metrics
            await self.collect_metric(
                tenant_id="system",
                metric_type=MetricType.MEMORY,
                metric_category=MetricCategory.SYSTEM,
                name="memory_percent",
                value=system_metrics["memory"]["percent"],
                unit="percent",
                metadata={
                    "total": system_metrics["memory"]["total"],
                    "available": system_metrics["memory"]["available"],
                    "used": system_metrics["memory"]["used"],
                },
                tags=["system", "memory"],
            )

            # Disk metrics
            await self.collect_metric(
                tenant_id="system",
                metric_type=MetricType.DISK,
                metric_category=MetricCategory.SYSTEM,
                name="disk_percent",
                value=system_metrics["disk"]["percent"],
                unit="percent",
                metadata={
                    "total": system_metrics["disk"]["total"],
                    "used": system_metrics["disk"]["used"],
                    "free": system_metrics["disk"]["free"],
                },
                tags=["system", "disk"],
            )

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    async def _collect_database_metrics(self) -> None:
        """Collect database performance metrics."""
        try:
            db_metrics = await self.get_database_metrics()

            # Connection pool metrics
            if "connection_pool" in db_metrics:
                pool = db_metrics["connection_pool"]
                await self.collect_metric(
                    tenant_id="database",
                    metric_type=MetricType.DATABASE,
                    metric_category=MetricCategory.DATABASE,
                    name="connection_pool_utilization",
                    value=pool.get("utilization", 0),
                    unit="percent",
                    metadata=pool,
                    tags=["database", "connection_pool"],
                )

            # Query metrics
            if "queries" in db_metrics:
                queries = db_metrics["queries"]
                await self.collect_metric(
                    tenant_id="database",
                    metric_type=MetricType.DATABASE,
                    metric_category=MetricCategory.DATABASE,
                    name="avg_query_time",
                    value=queries.get("avg_time_ms", 0),
                    unit="milliseconds",
                    metadata=queries,
                    tags=["database", "queries"],
                )

            # Index metrics
            if "indexes" in db_metrics:
                indexes = db_metrics["indexes"]
                await self.collect_metric(
                    tenant_id="database",
                    metric_type=MetricType.DATABASE,
                    metric_category=MetricCategory.DATABASE,
                    name="index_hit_rate",
                    value=indexes.get("hit_rate", 0),
                    unit="percent",
                    metadata=indexes,
                    tags=["database", "indexes"],
                )

        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")

    async def _process_metrics_buffer(self) -> None:
        """Process metrics buffer and save to database."""
        try:
            if not self._metrics_buffer:
                return

            # Batch insert metrics
            await self._save_metrics_batch(self._metrics_buffer)

            # Clear buffer
            self._metrics_buffer.clear()

        except Exception as e:
            logger.error(f"Failed to process metrics buffer: {e}")

    async def _process_alerts_buffer(self) -> None:
        """Process alerts buffer and save to database."""
        try:
            if not self._alerts_buffer:
                return

            # Batch insert alerts
            await self._save_alerts_batch(self._alerts_buffer)

            # Clear buffer
            self._alerts_buffer.clear()

        except Exception as e:
            logger.error(f"Failed to process alerts buffer: {e}")

    async def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check metric against thresholds and create alerts."""
        try:
            threshold_key = f"{metric.tenant_id}:{metric.name}"

            # Check tenant-specific threshold first
            threshold = self._thresholds.get(threshold_key)
            if not threshold:
                # Check default threshold
                default_threshold_key = f"default:{metric.name}"
                threshold = self._thresholds.get(default_threshold_key)

            if not threshold or not threshold.enabled:
                return

            # Check thresholds
            alert = None

            if self._compare_values(
                metric.value, threshold.warning_threshold, threshold.comparison_operator
            ):
                alert = PerformanceAlert(
                    id=str(uuid4()),
                    tenant_id=metric.tenant_id,
                    alert_type="threshold_warning",
                    severity=AlertSeverity.WARNING,
                    title=f"Performance Warning: {metric.name}",
                    message=f"{metric.name} exceeded warning threshold: {metric.value} {metric.unit} > {threshold.warning_threshold} {metric.unit}",
                    metric_name=metric.name,
                    current_value=metric.value,
                    threshold_value=threshold.warning_threshold,
                    timestamp=metric.timestamp,
                    metadata=metric.metadata,
                )

            elif self._compare_values(
                metric.value,
                threshold.critical_threshold,
                threshold.comparison_operator,
            ):
                alert = PerformanceAlert(
                    id=str(uuid4()),
                    tenant_id=metric.tenant_id,
                    alert_type="threshold_critical",
                    severity=AlertSeverity.CRITICAL,
                    title=f"Performance Critical: {metric.name}",
                    message=f"{metric.name} exceeded critical threshold: {metric.value} {metric.unit} > {threshold.critical_threshold} {metric.unit}",
                    metric_name=metric.name,
                    current_value=metric.value,
                    threshold_value=threshold.critical_threshold,
                    timestamp=metric.timestamp,
                    metadata=metric.metadata,
                )

            if alert:
                self._alerts_buffer.append(alert)

                # Call alert handlers
                await self._call_alert_handlers(alert)

        except Exception as e:
            logger.error(f"Failed to check thresholds: {e}")

    def _compare_values(self, value: float, threshold: float, operator: str) -> bool:
        """Compare values based on operator."""
        try:
            if operator == "gt":
                return value > threshold
            elif operator == "lt":
                return value < threshold
            elif operator == "eq":
                return value == threshold
            elif operator == "ne":
                return value != threshold
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to compare values: {e}")
            return False

    async def _call_alert_handlers(self, alert: PerformanceAlert) -> None:
        """Call registered alert handlers."""
        try:
            for alert_type, handler in self._alert_handlers.items():
                if alert_type in alert.alert_type or alert_type == "all":
                    try:
                        await handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler failed for {alert_type}: {e}")

        except Exception as e:
            logger.error(f"Failed to call alert handlers: {e}")

    async def _save_metric(self, metric: PerformanceMetric) -> None:
        """Save single metric to database."""
        try:
            query = """
                INSERT INTO performance_metrics (
                    id, tenant_id, metric_type, metric_category, name, value, unit,
                    timestamp, metadata, tags, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """

            params = [
                metric.id,
                metric.tenant_id,
                metric.metric_type.value,
                metric.metric_category.value,
                metric.name,
                metric.value,
                metric.unit,
                metric.timestamp,
                json.dumps(metric.metadata),
                json.dumps(metric.tags),
                metric.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save metric: {e}")

    async def _save_metrics_batch(self, metrics: List[PerformanceMetric]) -> None:
        """Save metrics in batch."""
        try:
            if not metrics:
                return

            query = """
                INSERT INTO performance_metrics (
                    id, tenant_id, metric_type, metric_category, name, value, unit,
                    timestamp, metadata, tags, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """

            params_list = []
            for metric in metrics:
                params_list.append(
                    (
                        metric.id,
                        metric.tenant_id,
                        metric.metric_type.value,
                        metric.metric_category.value,
                        metric.name,
                        metric.value,
                        metric.unit,
                        metric.timestamp,
                        json.dumps(metric.metadata),
                        json.dumps(metric.tags),
                        metric.created_at,
                    )
                )

            async with self.db_pool.acquire() as conn:
                await conn.executemany(query, params_list)

        except Exception as e:
            logger.error(f"Failed to save metrics batch: {e}")

    async def _save_alert(self, alert: PerformanceAlert) -> None:
        """Save single alert to database."""
        try:
            query = """
                INSERT INTO performance_alerts (
                    id, tenant_id, alert_type, severity, title, message,
                    metric_name, current_value, threshold_value, timestamp,
                    resolved, resolved_at, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """

            params = [
                alert.id,
                alert.tenant_id,
                alert.alert_type,
                alert.severity.value,
                alert.title,
                alert.message,
                alert.metric_name,
                alert.current_value,
                alert.threshold_value,
                alert.timestamp,
                alert.resolved,
                alert.resolved_at,
                json.dumps(alert.metadata),
                alert.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save alert: {e}")

    async def _save_alerts_batch(self, alerts: List[PerformanceAlert]) -> None:
        """Save alerts in batch."""
        try:
            if not alerts:
                return

            query = """
                INSERT INTO performance_alerts (
                    id, tenant_id, alert_type, severity, title, message,
                    metric_name, current_value, threshold_value, timestamp,
                    resolved, resolved_at, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """

            params_list = []
            for alert in alerts:
                params_list.append(
                    (
                        alert.id,
                        alert.tenant_id,
                        alert.alert_type,
                        alert.severity.value,
                        alert.title,
                        alert.message,
                        alert.metric_name,
                        alert.current_value,
                        alert.threshold_value,
                        alert.timestamp,
                        alert.resolved,
                        alert.resolved_at,
                        json.dumps(alert.metadata),
                        alert.created_at,
                    )
                )

            async with self.db_pool.acquire() as conn:
                await conn.executemany(query, params_list)

        except Exception as e:
            logger.error(f"Failed to save alerts batch: {e}")

    async def _save_threshold(self, threshold: PerformanceThreshold) -> None:
        """Save threshold to database."""
        try:
            query = """
                INSERT INTO performance_thresholds (
                    id, tenant_id, metric_name, metric_type, warning_threshold,
                    critical_threshold, comparison_operator, enabled,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (tenant_id, metric_name) DO UPDATE SET
                    warning_threshold = EXCLUDED.warning_threshold,
                    critical_threshold = EXCLUDED.critical_threshold,
                    comparison_operator = EXCLUDED.comparison_operator,
                    enabled = EXCLUDED.enabled,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                threshold.id,
                threshold.tenant_id,
                threshold.metric_name,
                threshold.metric_type.value,
                threshold.warning_threshold,
                threshold.critical_threshold,
                threshold.comparison_operator,
                threshold.enabled,
                threshold.created_at,
                threshold.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save threshold: {e}")

    async def _get_category_metrics(
        self,
        tenant_id: str,
        category: MetricCategory,
        time_period_hours: int,
    ) -> Dict[str, Any]:
        """Get metrics for a specific category."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Get metrics for category
            query = """
                SELECT
                    name, AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    COUNT(*) as count,
                    unit
                FROM performance_metrics
                WHERE tenant_id = $1 AND metric_category = $2 AND timestamp > $3
                GROUP BY name, unit
                ORDER BY avg_value DESC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(
                    query, tenant_id, category.value, cutoff_time
                )

                metrics = {}
                for row in results:
                    metrics[row[0]] = {
                        "avg_value": float(row[1]),
                        "min_value": float(row[2]),
                        "max_value": float(row[3]),
                        "count": row[4],
                        "unit": row[5],
                    }

                return metrics

        except Exception as e:
            logger.error(f"Failed to get category metrics: {e}")
            return {}

    async def _calculate_trends(
        self,
        tenant_id: str,
        time_period_hours: int,
    ) -> Dict[str, Any]:
        """Calculate performance trends."""
        try:
            trends = {}

            # Get metrics for the period
            metrics = await self.get_metrics(
                tenant_id, time_period_hours=time_period_hours
            )

            # Group metrics by name
            metrics_by_name = defaultdict(list)
            for metric in metrics:
                metrics_by_name[metric.name].append(metric)

            # Calculate trends for each metric
            for name, metric_list in metrics_by_name.items():
                if len(metric_list) >= 2:
                    values = [m.value for m in metric_list]
                    [m.timestamp for m in metric_list]

                    # Calculate trend direction
                    first_half = values[: len(values) // 2]
                    second_half = values[len(values) // 2 :]

                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)

                    if second_avg > first_avg * 1.1:
                        trend_direction = "increasing"
                    elif second_avg < first_half * 0.9:
                        trend_direction = "decreasing"
                    else:
                        trend_direction = "stable"

                    trends[name] = {
                        "direction": trend_direction,
                        "current_value": values[-1],
                        "average_value": sum(values) / len(values),
                        "trend_percentage": ((second_avg - first_avg) / first_avg * 100)
                        if first_avg > 0
                        else 0,
                        "data_points": len(values),
                        "period_hours": time_period_hours,
                    }

            return trends

        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            return {}

    async def _calculate_health_score(self, tenant_id: str) -> float:
        """Calculate overall health score."""
        try:
            # Get recent alerts
            recent_alerts = await self.get_alerts(tenant_id, time_period_hours=1)

            # Get recent metrics
            recent_metrics = await self.get_metrics(tenant_id, time_period_hours=1)

            # Calculate health factors
            factors = {}

            # Alert factor (negative impact)
            critical_alerts = [
                a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL
            ]
            warning_alerts = [
                a for a in recent_alerts if a.severity == AlertSeverity.WARNING
            ]

            factors["alerts"] = max(
                0, 1.0 - (len(critical_alerts) * 0.4 + len(warning_alerts) * 0.2)
            )

            # CPU factor
            cpu_metrics = [m for m in recent_metrics if m.metric_type == MetricType.CPU]
            if cpu_metrics:
                avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics)
                factors["cpu"] = max(0, 1.0 - (avg_cpu / 100))

            # Memory factor
            memory_metrics = [
                m for m in recent_metrics if m.metric_type == MetricType.MEMORY
            ]
            if memory_metrics:
                avg_memory = sum(m.value for m in memory_metrics) / len(memory_metrics)
                factors["memory"] = max(0, 1.0 - (avg_memory / 100))

            # Database factor
            db_metrics = [
                m for m in recent_metrics if m.metric_type == MetricType.DATABASE
            ]
            if db_metrics:
                # For database metrics, lower is better for response time
                avg_db_time = sum(m.value for m in db_metrics) / len(db_metrics)
                factors["database"] = max(0, 1.0 - (avg_db_time / 10000))  # 10s is bad

            # Calculate overall score
            if factors:
                overall_score = sum(factors.values()) / len(factors)
            else:
                overall_score = 0.5  # Default to middle

            return overall_score

        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return 0.0

    async def _get_connection_pool_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics."""
        try:
            # This would get actual connection pool metrics
            # For now, return placeholder data
            return {
                "total_connections": 10,
                "active_connections": 3,
                "idle_connections": 7,
                "utilization": 30.0,
                "queue_size": 0,
            }

        except Exception as e:
            logger.error(f"Failed to get connection pool metrics: {e}")
            return {}

    async def _get_database_size(self) -> Dict[str, Any]:
        """Get database size information."""
        try:
            # This would get actual database size
            return {
                "total_size_mb": 1024,
                "table_size_mb": 800,
                "index_size_mb": 224,
            }

        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return {}

    async def _get_query_statistics(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        try:
            # This would get actual query statistics from pg_stat_statements
            return {
                "total_queries": 1000,
                "avg_time_ms": 50.0,
                "slow_queries": 5,
                "error_rate": 0.01,
            }

        except Exception as e:
            logger.error(f"Failed to get query statistics: {e}")
            return {}

    async def _get_index_statistics(self) -> Dict[str, Any]:
        """Get index performance statistics."""
        try:
            # This would get actual index statistics from pg_stat_user_indexes
            return {
                "total_indexes": 25,
                "unused_indexes": 3,
                "avg_hit_rate": 0.85,
                "total_size_mb": 224,
            }

        except Exception as e:
            logger.error(f"Failed to get index statistics: {e}")
            return {}

    async def _get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        try:
            # This would get actual cache statistics
            return {
                "hit_rate": 0.85,
                "miss_rate": 0.15,
                "memory_usage_mb": 256,
                "entries": 1000,
            }

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {}

    async def _check_resolved_alerts(self) -> None:
        """Check for resolved alerts and update them."""
        try:
            # Get unresolved alerts
            unresolved_alerts = [
                alert for alert in self._alerts_buffer if not alert.resolved
            ]

            # Check if alerts should be resolved
            for alert in unresolved_alerts:
                if self._should_resolve_alert(alert):
                    alert.resolved = True
                    alert.resolved_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to check resolved alerts: {e}")

    def _should_resolve_alert(self, alert: PerformanceAlert) -> bool:
        """Check if alert should be resolved."""
        try:
            # Auto-resolve info and warning alerts after 1 hour
            if alert.severity in [AlertSeverity.INFO, AlertSeverity.WARNING]:
                return (
                    datetime.now(timezone.utc) - alert.timestamp
                ).total_seconds() > 3600

            # Auto-resolve critical alerts if metric has been good for 30 minutes
            if alert.severity == AlertSeverity.CRITICAL:
                # This would require checking current metric value
                return False  # Don't auto-resolve critical alerts

            return False

        except Exception as e:
            logger.error(f"Failed to check if alert should be resolved: {e}")
            return False


# Factory function
def create_performance_monitor(db_pool) -> PerformanceMonitor:
    """Create performance monitor instance."""
    return PerformanceMonitor(db_pool)
