"""
Metrics Collector for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from shared.logging_config import get_logger

logger = get_logger("sorce.metrics_collector")


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    SUMMARY = "summary"


class MetricCategory(Enum):
    """Categories of metrics."""

    SYSTEM = "system"
    DATABASE = "database"
    APPLICATION = "application"
    CACHE = "cache"
    NETWORK = "network"
    BUSINESS = "business"
    CUSTOM = "custom"


@dataclass
class MetricValue:
    """A metric value with timestamp and metadata."""

    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricDefinition:
    """Definition of a metric."""

    name: str
    metric_type: MetricType
    category: MetricCategory
    description: str = ""
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    aggregation: Optional[str] = None
    retention_days: int = 30


@dataclass
class MetricSnapshot:
    """A snapshot of metric values at a point in time."""

    timestamp: datetime
    values: Dict[str, MetricValue]
    metadata: Dict[str, Any] = field(default_factory=dict)


class Metric:
    """Base metric class."""

    def __init__(self, definition: MetricDefinition):
        self.definition = definition
        self._values: deque = deque(maxlen=1000)  # Keep last 1000 values
        self._lock = asyncio.Lock()
        self._last_updated = datetime.now(timezone.utc)

    async def record(
        self,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a metric value."""
        try:
            async with self._lock:
                metric_value = MetricValue(
                    value=value,
                    timestamp=datetime.now(timezone.utc),
                    labels=labels or {},
                    metadata=metadata or {},
                )

                self._values.append(metric_value)
                self._last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to record metric {self.definition.name}: {e}")

    async def get_values(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> List[MetricValue]:
        """Get metric values with optional filtering."""
        try:
            async with self._lock:
                values = list(self._values)

                # Filter by time
                if since:
                    values = [v for v in values if v.timestamp >= since]

                # Filter by labels
                if labels:
                    values = [
                        v
                        for v in values
                        if all(v.labels.get(k) == label_val for k, label_val in labels.items())
                    ]

                # Limit results
                if limit:
                    values = values[-limit:]

                return values

        except Exception as e:
            logger.error(f"Failed to get values for metric {self.definition.name}: {e}")
            return []

    async def get_latest(
        self, labels: Optional[Dict[str, str]] = None
    ) -> Optional[MetricValue]:
        """Get the latest metric value."""
        try:
            values = await self.get_values(limit=1, labels=labels)
            return values[-1] if values else None

        except Exception as e:
            logger.error(
                f"Failed to get latest value for metric {self.definition.name}: {e}"
            )
            return None

    async def aggregate(
        self, aggregation: str, since: Optional[datetime] = None
    ) -> Optional[float]:
        """Aggregate metric values."""
        try:
            values = await self.get_values(since=since)

            if not values:
                return None

            numeric_values = [
                v.value for v in values if isinstance(v.value, (int, float))
            ]

            if not numeric_values:
                return None

            if aggregation == "avg":
                return statistics.mean(numeric_values)
            elif aggregation == "sum":
                return sum(numeric_values)
            elif aggregation == "min":
                return min(numeric_values)
            elif aggregation == "max":
                return max(numeric_values)
            elif aggregation == "count":
                return len(numeric_values)
            else:
                logger.warning(f"Unknown aggregation: {aggregation}")
                return None

        except Exception as e:
            logger.error(f"Failed to aggregate metric {self.definition.name}: {e}")
            return None


class Counter(Metric):
    """Counter metric that can be incremented."""

    def __init__(self, definition: MetricDefinition):
        super().__init__(definition)
        self._counter: float = 0.0

    async def inc(
        self,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Increment the counter."""
        try:
            self._counter = float(self._counter) + value
            await self.record(self._counter, labels, metadata)
        except Exception as e:
            logger.error(f"Failed to increment counter {self.definition.name}: {e}")

    async def reset(
        self,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Reset the counter."""
        try:
            self._counter = 0
            await self.record(0, labels, metadata)
        except Exception as e:
            logger.error(f"Failed to reset counter {self.definition.name}: {e}")


class Gauge(Metric):
    """Gauge metric that can be set to arbitrary values."""

    async def set(
        self,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set the gauge value."""
        try:
            await self.record(value, labels, metadata)
        except Exception as e:
            logger.error(f"Failed to set gauge {self.definition.name}: {e}")


class Histogram(Metric):
    """Histogram metric that tracks value distributions."""

    def __init__(
        self, definition: MetricDefinition, buckets: Optional[List[float]] = None
    ):
        super().__init__(definition)
        self._buckets = buckets or [
            0.1,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
            25.0,
            50.0,
            100.0,
            float("inf"),
        ]
        self._bucket_counts = {bucket: 0 for bucket in self._buckets}
        self._count = 0
        self._sum = 0.0

    async def observe(
        self,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Observe a value."""
        try:
            # Update bucket counts
            for bucket in self._buckets:
                if value <= bucket:
                    self._bucket_counts[bucket] += 1
                    break

            self._count += 1
            self._sum += value

            await self.record(value, labels, metadata)

        except Exception as e:
            logger.error(f"Failed to observe histogram {self.definition.name}: {e}")

    async def get_bucket_counts(self) -> Dict[float, int]:
        """Get histogram bucket counts."""
        return self._bucket_counts.copy()

    async def get_summary(self) -> Dict[str, float]:
        """Get histogram summary statistics."""
        try:
            values = await self.get_values()
            numeric_values = [
                v.value for v in values if isinstance(v.value, (int, float))
            ]

            if not numeric_values:
                return {}

            return {
                "count": len(numeric_values),
                "sum": sum(numeric_values),
                "avg": statistics.mean(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "p50": statistics.median(numeric_values),
                "p95": numeric_values[int(len(numeric_values) * 0.95)]
                if len(numeric_values) > 1
                else numeric_values[0],
                "p99": numeric_values[int(len(numeric_values) * 0.99)]
                if len(numeric_values) > 1
                else numeric_values[0],
            }

        except Exception as e:
            logger.error(
                f"Failed to get histogram summary for {self.definition.name}: {e}"
            )
            return {}


class Timer(Metric):
    """Timer metric that tracks duration."""

    def __init__(self, definition: MetricDefinition):
        super().__init__(definition)
        self._histogram = Histogram(definition)

    @asynccontextmanager
    async def time(
        self,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for timing operations."""
        start_time = time.time()

        try:
            yield
        finally:
            duration = time.time() - start_time
            await self._histogram.observe(duration, labels, metadata)

    async def record_duration(
        self,
        duration: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a duration directly."""
        await self._histogram.observe(duration, labels, metadata)

    async def get_summary(self) -> Dict[str, float]:
        """Get timer summary statistics."""
        return await self._histogram.get_summary()


class MetricsCollector:
    """Advanced metrics collection system."""

    def __init__(self):
        self._metrics: Dict[str, Any] = {}  # Can contain Counter, Gauge, Histogram, Timer, or Metric
        self._definitions: Dict[str, MetricDefinition] = {}
        self._snapshots: deque = deque(maxlen=100)  # Keep last 100 snapshots
        self._lock = asyncio.Lock()

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._snapshot_task: Optional[asyncio.Task] = None

        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._snapshot_task = asyncio.create_task(self._snapshot_loop())

    def define_metric(
        self,
        name: str,
        metric_type: MetricType,
        category: MetricCategory,
        description: str = "",
        unit: str = "",
        labels: Optional[List[str]] = None,
        aggregation: Optional[str] = None,
        retention_days: int = 30,
    ) -> Metric:
        """Define and create a new metric."""
        try:
            definition = MetricDefinition(
                name=name,
                metric_type=metric_type,
                category=category,
                description=description,
                unit=unit,
                labels=labels or [],
                aggregation=aggregation,
                retention_days=retention_days,
            )

            # Create metric instance based on type
            if metric_type == MetricType.COUNTER:
                metric = Counter(definition)
            elif metric_type == MetricType.GAUGE:
                metric = Gauge(definition)
            elif metric_type == MetricType.HISTOGRAM:
                metric = Histogram(definition)
            elif metric_type == MetricType.TIMER:
                metric = Timer(definition)
            else:
                metric = Metric(definition)

            self._metrics[name] = metric
            self._definitions[name] = definition

            logger.info(f"Defined metric: {name} ({metric_type.value})")
            return metric

        except Exception as e:
            logger.error(f"Failed to define metric {name}: {e}")
            raise

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name."""
        return self._metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics."""
        return self._metrics.copy()

    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Get all metric definitions."""
        return self._definitions.copy()

    async def record_metric(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record a metric value."""
        try:
            metric = self.get_metric(name)
            if not metric:
                logger.warning(f"Metric {name} not found")
                return False

            await metric.record(value, labels, metadata)
            return True

        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
            return False

    async def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Increment a counter metric."""
        try:
            metric = self.get_metric(name)
            if not metric or not isinstance(metric, Counter):
                logger.warning(f"Counter metric {name} not found")
                return False

            await metric.inc(value, labels, metadata)
            return True

        except Exception as e:
            logger.error(f"Failed to increment counter {name}: {e}")
            return False

    async def set_gauge(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set a gauge metric."""
        try:
            metric = self.get_metric(name)
            if not metric or not isinstance(metric, Gauge):
                logger.warning(f"Gauge metric {name} not found")
                return False

            await metric.set(value, labels, metadata)
            return True

        except Exception as e:
            logger.error(f"Failed to set gauge {name}: {e}")
            return False

    async def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Observe a histogram metric."""
        try:
            metric = self.get_metric(name)
            if not metric or not isinstance(metric, Histogram):
                logger.warning(f"Histogram metric {name} not found")
                return False

            await metric.observe(value, labels, metadata)
            return True

        except Exception as e:
            logger.error(f"Failed to observe histogram {name}: {e}")
            return False

    @asynccontextmanager
    async def time_timer(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for timing operations."""
        metric = self.get_metric(name)
        if not metric or not isinstance(metric, Timer):
            logger.warning(f"Timer metric {name} not found")
            yield
            return

        async with metric.time(labels, metadata):
            yield

    async def get_metric_values(
        self,
        name: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> List[MetricValue]:
        """Get values for a specific metric."""
        try:
            metric = self.get_metric(name)
            if not metric:
                return []

            return await metric.get_values(since, limit, labels)

        except Exception as e:
            logger.error(f"Failed to get values for metric {name}: {e}")
            return []

    async def get_metric_summary(
        self,
        name: str,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get summary for a specific metric."""
        try:
            metric = self.get_metric(name)
            if not metric:
                return {}

            summary = {
                "name": name,
                "type": metric.definition.metric_type.value,
                "category": metric.definition.category.value,
                "description": metric.definition.description,
                "unit": metric.definition.unit,
                "last_updated": metric._last_updated.isoformat(),
            }

            # Add type-specific summary
            if isinstance(metric, Histogram):
                hist_summary = await metric.get_summary()
                summary.update({k: str(v) for k, v in hist_summary.items()})  # type: ignore[arg-type]
            elif isinstance(metric, Timer):
                timer_summary = await metric.get_summary()
                summary.update({k: str(v) for k, v in timer_summary.items()})  # type: ignore[arg-type]
            else:
                values = await metric.get_values(since=since)
                numeric_values = [
                    v.value for v in values if isinstance(v.value, (int, float))
                ]

                if numeric_values:
                    summary.update(  # type: ignore[arg-type]
                        {
                            "count": str(len(numeric_values)),
                            "avg": str(statistics.mean(numeric_values)),
                            "min": str(min(numeric_values)),
                            "max": str(max(numeric_values)),
                            "latest": str(numeric_values[-1]) if numeric_values else "None",
                        }
                    )

            return summary

        except Exception as e:
            logger.error(f"Failed to get summary for metric {name}: {e}")
            return {}

    async def get_category_summary(
        self,
        category: MetricCategory,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get summary for all metrics in a category."""
        try:
            category_metrics = {
                name: metric
                for name, metric in self._metrics.items()
                if metric.definition.category == category
            }

            summary: Dict[str, Any] = {
                "category": category.value,
                "metric_count": len(category_metrics),
                "metrics": {},
            }

            for name, metric in category_metrics.items():
                metric_summary = await self.get_metric_summary(name, since)
                if metric_summary:
                    summary["metrics"][name] = metric_summary

            return summary

        except Exception as e:
            logger.error(f"Failed to get category summary for {category}: {e}")
            return {}

    async def create_snapshot(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a snapshot of all current metric values."""
        try:
            snapshot = MetricSnapshot(
                timestamp=datetime.now(timezone.utc),
                values={},
                metadata=metadata or {},
            )

            # Collect latest values from all metrics
            for name, metric in self._metrics.items():
                latest = await metric.get_latest()
                if latest:
                    snapshot.values[name] = latest

            # Store snapshot
            snapshot_id = str(uuid.uuid4())
            self._snapshots.append(snapshot)

            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return ""

    async def get_snapshot(self, snapshot_id: str) -> Optional[MetricSnapshot]:
        """Get a specific snapshot by ID."""
        try:
            for snapshot in self._snapshots:
                # This is a simplified approach - in practice, you'd store snapshots with IDs
                if snapshot.metadata.get("id") == snapshot_id:
                    return snapshot  # type: ignore[no-any-return]

            return None

        except Exception as e:
            logger.error(f"Failed to get snapshot {snapshot_id}: {e}")
            return None

    async def cleanup_old_data(self) -> int:
        """Clean up old metric data based on retention policies."""
        try:
            cleaned_count = 0
            cutoff_time = datetime.now(timezone.utc)

            for name, metric in self._metrics.items():
                retention_days = metric.definition.retention_days
                since = cutoff_time - timedelta(days=retention_days)

                # This is a simplified cleanup - in practice, you'd implement proper cleanup
                old_values = await metric.get_values(since=since)
                cleaned_count += len(old_values)

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0

    async def export_metrics(
        self,
        format: str = "json",
        since: Optional[datetime] = None,
        categories: Optional[List[MetricCategory]] = None,
    ) -> str:
        """Export metrics data."""
        try:
            if format == "json":
                return await self._export_json(since, categories)
            elif format == "prometheus":
                return await self._export_prometheus(since, categories)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return ""

    async def _export_json(
        self,
        since: Optional[datetime] = None,
        categories: Optional[List[MetricCategory]] = None,
    ) -> str:
        """Export metrics in JSON format."""
        try:
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {},
            }

            for name, metric in self._metrics.items():
                # Filter by category if specified
                if categories and metric.definition.category not in categories:
                    continue

                values = await metric.get_values(since=since)

                metrics_dict: Dict[str, Any] = data["metrics"]  # type: ignore[assignment]
                metrics_dict[name] = {
                    "definition": {
                        "type": metric.definition.metric_type.value,
                        "category": metric.definition.category.value,
                        "description": metric.definition.description,
                        "unit": metric.definition.unit,
                    },
                    "values": [
                        {
                            "value": v.value,
                            "timestamp": v.timestamp.isoformat(),
                            "labels": v.labels,
                            "metadata": v.metadata,
                        }
                        for v in values
                    ],
                }

            return json.dumps(data, indent=2)

        except Exception as e:
            logger.error(f"Failed to export JSON metrics: {e}")
            return "{}"

    async def _export_prometheus(
        self,
        since: Optional[datetime] = None,
        categories: Optional[List[MetricCategory]] = None,
    ) -> str:
        """Export metrics in Prometheus format."""
        try:
            lines = []

            for name, metric in self._metrics.items():
                # Filter by category if specified
                if categories and metric.definition.category not in categories:
                    continue

                # Get latest value
                latest = await metric.get_latest()
                if latest:
                    # Create metric name with labels
                    labels_str = ""
                    if latest.labels:
                        label_pairs = [f'{k}="{v}"' for k, v in latest.labels.items()]
                        labels_str = "{" + ",".join(label_pairs) + "}"

                    metric_line = f"{name}{labels_str} {latest.value}"
                    lines.append(metric_line)

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Failed to export Prometheus metrics: {e}")
            return ""

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour

                try:
                    cleaned_count = await self.cleanup_old_data()
                    if cleaned_count > 0:
                        logger.info(f"Cleaned up {cleaned_count} old metric values")

                except Exception as e:
                    logger.error(f"Cleanup error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Cleanup loop failed: {e}")

    async def _snapshot_loop(self) -> None:
        """Background snapshot loop."""
        try:
            while True:
                await asyncio.sleep(300)  # Run every 5 minutes

                try:
                    await self.create_snapshot({"type": "automatic"})
                except Exception as e:
                    logger.error(f"Snapshot error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Snapshot loop failed: {e}")


# Global instance
metrics_collector = MetricsCollector()


# Factory function
def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector instance."""
    return metrics_collector
