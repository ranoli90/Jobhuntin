"""
Performance Metrics for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
import statistics
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger
from shared.metrics_collector import MetricCategory, MetricType, get_metrics_collector

logger = get_logger("sorce.performance_metrics")


class MetricAggregation(Enum):
    """Types of metric aggregations."""

    AVERAGE = "average"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"
    RATE = "rate"


class MetricWindow(Enum):
    """Time windows for metrics."""

    LAST_MINUTE = "last_minute"
    LAST_5_MINUTES = "last_5_minutes"
    LAST_15_MINUTES = "last_15_minutes"
    LAST_HOUR = "last_hour"
    LAST_6_HOURS = "last_6_hours"
    LAST_24_HOURS = "last_24_hours"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"


@dataclass
class PerformanceMetric:
    """A performance metric with enhanced tracking."""

    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    unit: Optional[str] = None
    aggregation: Optional[MetricAggregation] = None


@dataclass
class MetricStatistics:
    """Statistical information about metrics."""

    metric_name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    std_deviation: float
    percentile_50: float
    percentile_95: float
    percentile_99: float
    sum_value: float
    rate_per_second: Optional[float] = None
    trend: Optional[str] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MetricAlert:
    """Performance metric alert."""

    id: str
    metric_name: str
    alert_type: str
    severity: str
    threshold: float
    current_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMetrics:
    """Advanced performance metrics collection and analysis system."""

    def __init__(self):
        self._metrics_collector = get_metrics_collector()
        self._metric_stats: Dict[str, MetricStatistics] = {}
        self._alerts: List[MetricAlert] = []
        self._metric_windows = self._initialize_windows()
        self._lock = threading.Lock()

        # Background tasks
        self._analysis_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None

        # Start background analysis
        self._start_background_tasks()

    def define_performance_metric(
        self,
        name: str,
        category: MetricCategory,
        description: str = "",
        unit: str = "",
        aggregation: Optional[MetricAggregation] = None,
        labels: Optional[List[str]] = None,
        alert_thresholds: Optional[Dict[str, float]] = None,
    ) -> bool:
        """Define a performance metric with enhanced features."""
        try:
            # Define base metric
            self._metrics_collector.define_metric(
                name=name,
                metric_type=MetricType.GAUGE,
                category=category,
                description=description,
                unit=unit,
                labels=labels or [],
                aggregation=aggregation.value if aggregation else None,
            )

            # Define additional metrics for analysis
            self._metrics_collector.define_metric(
                name=f"{name}_rate",
                metric_type=MetricType.GAUGE,
                category=category,
                description=f"Rate metric for {name}",
                unit="per_second",
            )

            self._metrics_collector.define_metric(
                name=f"{name}_histogram",
                metric_type=MetricType.HISTOGRAM,
                category=category,
                description=f"Histogram for {name}",
                unit=unit,
            )

            # Initialize statistics
            self._metric_stats[name] = MetricStatistics(
                metric_name=name,
                count=0,
                min_value=0.0,
                max_value=0.0,
                avg_value=0.0,
                median_value=0.0,
                std_deviation=0.0,
                percentile_50=0.0,
                percentile_95=0.0,
                percentile_99=0.0,
                sum_value=0.0,
            )

            logger.info(f"Defined performance metric: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to define performance metric {name}: {e}")
            return False

    async def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Record a performance metric."""
        try:
            # Record base metric
            success = await self._metrics_collector.record_metric(
                name=name,
                value=value,
                labels=labels,
                metadata=metadata,
            )

            if success:
                # Update statistics
                self._update_statistics(name)

                # Check for alerts
                await self._check_alerts(name, value, labels, metadata)

            return success

        except Exception as e:
            logger.error(f"Failed to record performance metric {name}: {e}")
            return False

    async def record_timing(
        self,
        name: str,
        duration_ms: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record a timing metric."""
        try:
            # Record as gauge
            success = await self.record_metric(
                name=name,
                value=duration_ms,
                labels=labels,
                metadata={**(metadata or {}), "metric_type": "timing"},
            )

            # Also record in histogram
            await self._metrics_collector.observe_histogram(
                name=f"{name}_histogram",
                value=duration_ms,
                labels=labels,
                metadata=metadata,
            )

            return success

        except Exception as e:
            logger.error(f"Failed to record timing metric {name}: {e}")
            return False

    @asynccontextmanager
    async def time_operation(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for timing operations."""
        start_time = time.time()

        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            await self.record_timing(name, duration_ms, labels, metadata)

    async def get_metric_statistics(
        self,
        name: str,
        window: Optional[MetricWindow] = None,
        since: Optional[datetime] = None,
    ) -> Optional[MetricStatistics]:
        """Get statistics for a metric."""
        try:
            with self._lock:
                if name not in self._metric_stats:
                    return None

                base_stats = self._metric_stats[name]

                # Get recent values for analysis
                cutoff_time = self._get_cutoff_time(window, since)
                values = await self._get_recent_values(name, cutoff_time)

                if not values:
                    return base_stats

                # Calculate statistics
                numeric_values = [
                    v.value for v in values if isinstance(v.value, (int, float))
                ]

                if not numeric_values:
                    return base_stats

                stats = MetricStatistics(
                    metric_name=name,
                    count=len(numeric_values),
                    min_value=min(numeric_values),
                    max_value=max(numeric_values),
                    avg_value=statistics.mean(numeric_values),
                    median_value=statistics.median(numeric_values),
                    std_deviation=statistics.stdev(numeric_values)
                    if len(numeric_values) > 1
                    else 0.0,
                    percentile_50=statistics.median(numeric_values),
                    percentile_95=numeric_values[int(len(numeric_values) * 0.95)]
                    if len(numeric_values) > 1
                    else numeric_values[0],
                    percentile_99=numeric_values[int(len(numeric_values) * 0.99)]
                    if len(numeric_values) > 1
                    else numeric_values[0],
                    sum_value=sum(numeric_values),
                )

                # Calculate rate if enough data
                if len(values) >= 2:
                    time_span = (
                        values[-1].timestamp - values[0].timestamp
                    ).total_seconds()
                    if time_span > 0:
                        stats.rate_per_second = len(values) / time_span

                # Calculate trend
                stats.trend = self._calculate_trend(numeric_values)

                # Update cached statistics
                self._metric_stats[name] = stats

                return stats

        except Exception as e:
            logger.error(f"Failed to get statistics for metric {name}: {e}")
            return None

    async def get_metric_summary(
        self,
        category: Optional[MetricCategory] = None,
        window: Optional[MetricWindow] = None,
    ) -> Dict[str, Any]:
        """Get summary of metrics."""
        try:
            summary = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {},
                "category": category.value if category else "all",
                "window": window.value if window else "all",
            }

            # Get all metrics or filter by category
            all_metrics = self._metrics_collector.get_all_metrics()

            filtered_metrics = {}
            for name, metric in all_metrics.items():
                if category is None or metric.definition.category == category:
                    filtered_metrics[name] = metric

            # Get statistics for each metric
            for name, metric in filtered_metrics.items():
                stats = await self.get_metric_statistics(name, window)
                if stats:
                    summary["metrics"][name] = {
                        "definition": {
                            "category": metric.definition.category.value,
                            "description": metric.definition.description,
                            "unit": metric.definition.unit,
                            "aggregation": metric.definition.aggregation,
                        },
                        "statistics": {
                            "count": stats.count,
                            "avg": stats.avg_value,
                            "min": stats.min_value,
                            "max": stats.max_value,
                            "median": stats.median_value,
                            "std_dev": stats.std_deviation,
                            "percentile_50": stats.percentile_50,
                            "percentile_95": stats.percentile_95,
                            "percentile_99": stats.percentile_99,
                            "rate_per_second": stats.rate_per_second,
                            "trend": stats.trend,
                            "last_updated": stats.last_updated.isoformat(),
                        },
                    }

            return summary

        except Exception as e:
            logger.error(f"Failed to get metric summary: {e}")
            return {}

    async def create_alert(
        self,
        metric_name: str,
        alert_type: str,
        severity: str,
        threshold: float,
        current_value: float,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a performance metric alert."""
        try:
            alert = MetricAlert(
                id=str(uuid.uuid4()),
                metric_name=metric_name,
                alert_type=alert_type,
                severity=severity,
                threshold=threshold,
                current_value=current_value,
                message=message,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
            )

            self._alerts.append(alert)

            # Keep only last 1000 alerts
            if len(self._alerts) > 1000:
                self._alerts = self._alerts[-1000:]

            logger.warning(f"Created performance alert: {metric_name} - {message}")
            return alert.id

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return ""

    async def resolve_alert(
        self, alert_id: str, resolution_note: Optional[str] = None
    ) -> bool:
        """Resolve a performance alert."""
        try:
            for alert in self._alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now(timezone.utc)

                    if resolution_note:
                        alert.metadata["resolution_note"] = resolution_note

                    logger.info(f"Resolved performance alert: {alert_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False

    async def get_alerts(
        self,
        metric_name: Optional[str] = None,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        since: Optional[datetime] = None,
    ) -> List[MetricAlert]:
        """Get performance alerts with filtering."""
        try:
            alerts = self._alerts.copy()

            # Filter by metric name
            if metric_name:
                alerts = [a for a in alerts if a.metric_name == metric_name]

            # Filter by severity
            if severity:
                alerts = [a for a in alerts if a.severity == severity]

            # Filter by resolution status
            if resolved is not None:
                alerts = [a for a in alerts if a.resolved == resolved]

            # Filter by time
            if since:
                alerts = [a for a in alerts if a.timestamp >= since]

            return alerts

        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    async def get_performance_report(
        self,
        time_period_hours: int = 24,
        categories: Optional[List[MetricCategory]] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Get metrics summary
            metrics_summary = {}
            if categories:
                for category in categories:
                    summary = await self.get_metric_summary(category)
                    if summary["metrics"]:
                        metrics_summary[category.value] = summary
            else:
                summary = await self.get_metric_summary()
                if summary["metrics"]:
                    metrics_summary["all"] = summary

            # Get alerts summary
            alerts = await self.get_alerts(since=cutoff_time)
            alerts_summary = {
                "total": len(alerts),
                "active": len([a for a in alerts if not a.resolved]),
                "resolved": len([a for a in alerts if a.resolved]),
                "by_severity": {
                    severity: len([a for a in alerts if a.severity == severity])
                    for severity in set(a.severity for a in alerts)
                },
                "by_metric": {
                    metric: len([a for a in alerts if a.metric_name == metric])
                    for metric in set(a.metric_name for a in alerts)
                },
            }

            # Get top performers and issues
            top_metrics = await self._get_top_performers(cutoff_time)
            issue_metrics = await self._get_issue_metrics(cutoff_time)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                metrics_summary, alerts
            )

            report = {
                "period_hours": time_period_hours,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "metrics_summary": metrics_summary,
                "alerts_summary": alerts_summary,
                "top_performers": top_metrics,
                "issue_metrics": issue_metrics,
                "recommendations": recommendations,
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {}

    def _update_statistics(self, name: str) -> None:
        """Update cached statistics for a metric."""
        try:
            # This is a simplified update - in practice, you'd implement proper incremental updates
            pass

        except Exception as e:
            logger.error(f"Failed to update statistics for {name}: {e}")

    def _initialize_windows(self) -> Dict[MetricWindow, timedelta]:
        """Initialize time windows."""
        return {
            MetricWindow.LAST_MINUTE: timedelta(minutes=1),
            MetricWindow.LAST_5_MINUTES: timedelta(minutes=5),
            MetricWindow.LAST_15_MINUTES: timedelta(minutes=15),
            MetricWindow.LAST_HOUR: timedelta(hours=1),
            MetricWindow.LAST_6_HOURS: timedelta(hours=6),
            MetricWindow.LAST_24_HOURS: timedelta(hours=24),
            MetricWindow.LAST_7_DAYS: timedelta(days=7),
            MetricWindow.LAST_30_DAYS: timedelta(days=30),
        }

    def _get_cutoff_time(
        self, window: Optional[MetricWindow], since: Optional[datetime]
    ) -> datetime:
        """Get cutoff time for filtering."""
        if since:
            return since
        elif window and window in self._metric_windows:
            return datetime.now(timezone.utc) - self._metric_windows[window]
        else:
            return datetime.now(timezone.utc) - timedelta(hours=1)

    async def _get_recent_values(
        self, name: str, cutoff_time: datetime
    ) -> List[PerformanceMetric]:
        """Get recent values for a metric."""
        try:
            # Get values from metrics collector
            metric_values = await self._metrics_collector.get_metric_values(
                name, since=cutoff_time
            )

            # Convert to PerformanceMetric objects
            performance_metrics = []
            for value in metric_values:
                perf_metric = PerformanceMetric(
                    name=name,
                    value=value.value,
                    timestamp=value.timestamp,
                    labels=value.labels,
                    metadata=value.metadata,
                )
                performance_metrics.append(perf_metric)

            return performance_metrics

        except Exception as e:
            logger.error(f"Failed to get recent values for {name}: {e}")
            return []

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction."""
        try:
            if len(values) < 2:
                return "stable"

            # Simple trend calculation
            first_half = values[: len(values) // 2]
            second_half = values[len(values) // 2 :]

            if not first_half or not second_half:
                return "stable"

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            if second_avg > first_avg * 1.1:
                return "increasing"
            elif second_avg < first_half * 0.9:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"Failed to calculate trend: {e}")
            return "unknown"

    async def _check_alerts(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Check if metric should trigger alerts."""
        try:
            # This would check against configured alert thresholds
            # For now, implement basic alerting for high values

            # Example: Alert on high response times
            if "response_time" in name.lower() and value > 5000:
                await self.create_alert(
                    metric_name=name,
                    alert_type="high_response_time",
                    severity="warning",
                    threshold=5000.0,
                    current_value=value,
                    message=f"High response time detected: {value:.1f}ms",
                    metadata=metadata,
                )

            # Example: Alert on high error rates
            if "error_rate" in name.lower() and value > 0.1:
                await self.create_alert(
                    metric_name=name,
                    alert_type="high_error_rate",
                    severity="critical",
                    threshold=0.1,
                    current_value=value,
                    message=f"High error rate detected: {value:.2%}",
                    metadata=metadata,
                )

        except Exception as e:
            logger.error(f"Failed to check alerts for {name}: {e}")

    async def _get_top_performers(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get top performing metrics."""
        try:
            top_performers = []

            # Get all metrics with their statistics
            for name in self._metric_stats.keys():
                stats = await self.get_metric_statistics(name, since=cutoff_time)
                if stats and stats.count > 0:
                    # Consider metrics with good performance
                    if (
                        (stats.avg_value < 1000 and "response_time" in name.lower())
                        or (stats.avg_value < 0.9 and "error_rate" in name.lower())
                        or (stats.avg_value > 0.95 and "success_rate" in name.lower())
                    ):
                        top_performers.append(
                            {
                                "metric_name": name,
                                "avg_value": stats.avg_value,
                                "count": stats.count,
                                "trend": stats.trend,
                            }
                        )

            # Sort by performance (lower is better for response time, higher is better for success rate)
            top_performers.sort(
                key=lambda x: (
                    -x["avg_value"]
                    if "response_time" in x["metric_name"]
                    else x["avg_value"]
                )
            )

            return top_performers[:10]  # Top 10

        except Exception as e:
            logger.error(f"Failed to get top performers: {e}")
            return []

    async def _get_issue_metrics(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get metrics with performance issues."""
        try:
            issue_metrics = []

            # Get all metrics with their statistics
            for name in self._metric_stats.keys():
                stats = await self.get_metric_statistics(name, since=cutoff_time)
                if stats and stats.count > 0:
                    # Consider metrics with poor performance
                    if (
                        (stats.avg_value > 2000 and "response_time" in name.lower())
                        or (stats.avg_value > 0.05 and "error_rate" in name.lower())
                        or (stats.avg_value < 0.9 and "success_rate" in name.lower())
                    ):
                        issue_metrics.append(
                            {
                                "metric_name": name,
                                "avg_value": stats.avg_value,
                                "count": stats.count,
                                "trend": stats.trend,
                            }
                        )

            # Sort by performance severity
            issue_metrics.sort(
                key=lambda x: (
                    x["avg_value"]
                    if "response_time" in x["metric_name"]
                    else -x["avg_value"]
                ),
                reverse=True,
            )

            return issue_metrics[:10]  # Top 10 issues

        except Exception as e:
            logger.error(f"Failed to get issue metrics: {e}")
            return []

    async def _generate_recommendations(
        self,
        metrics_summary: Dict[str, Any],
        alerts: List[MetricAlert],
    ) -> List[str]:
        """Generate performance recommendations."""
        try:
            recommendations = []

            # Generate alert recommendations
            recommendations.extend(self._generate_alert_recommendations(alerts))

            # Generate metrics recommendations
            recommendations.extend(self._generate_metrics_recommendations(metrics_summary))

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Failed to generate recommendations"]

    def _generate_alert_recommendations(self, alerts: List[MetricAlert]) -> List[str]:
        """Generate recommendations based on performance alerts."""
        recommendations = []

        critical_alerts = [a for a in alerts if a.severity == "critical"]
        if critical_alerts:
            recommendations.append(
                f"Address {len(critical_alerts)} critical performance alerts"
            )

        warning_alerts = [a for a in alerts if a.severity == "warning"]
        if warning_alerts:
            recommendations.append(
                f"Monitor {len(warning_alerts)} performance warnings"
            )

        return recommendations

    def _generate_metrics_recommendations(self, metrics_summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on metrics analysis."""
        recommendations = []

        for category_name, category_data in metrics_summary.items():
            if isinstance(category_data, dict) and "metrics" in category_data:
                recommendations.extend(
                    self._analyze_category_metrics(category_name, category_data["metrics"])
                )

        return recommendations

    def _analyze_category_metrics(self, category_name: str, metrics: Dict[str, Any]) -> List[str]:
        """Analyze metrics within a category and generate recommendations."""
        recommendations = []

        for metric_name, metric_data in metrics.items():
            if (
                isinstance(metric_data, dict)
                and "statistics" in metric_data
            ):
                stats = metric_data["statistics"]
                recommendations.extend(
                    self._analyze_metric_performance(metric_name, stats)
                )

        return recommendations

    def _analyze_metric_performance(self, metric_name: str, stats: Dict[str, Any]) -> List[str]:
        """Analyze individual metric performance and generate recommendations."""
        recommendations = []

        # Check for slow response times
        if (
            "response_time" in metric_name.lower()
            and stats.get("avg_value", 0) > 1000
        ):
            recommendations.append(
                f"Optimize {metric_name}: average {stats['avg_value']:.1f}ms"
            )

        # Check for high error rates
        if (
            "error_rate" in metric_name.lower()
            and stats.get("avg_value", 0) > 0.05
        ):
            recommendations.append(
                f"Reduce {metric_name}: average {stats['avg_value']:.2%}"
            )

        # Check for low success rates
        if (
            "success_rate" in metric_name.lower()
            and stats.get("avg_value", 0) < 0.95
        ):
            recommendations.append(
                f"Improve {metric_name}: average {stats['avg_value']:.2%}"
            )

        return recommendations

    def _start_background_tasks(self) -> None:
        """Start background analysis tasks."""
        try:
            self._analysis_task = asyncio.create_task(self._analysis_loop())
            self._alert_task = asyncio.create_task(self._alert_loop())

        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")

    async def _analysis_loop(self) -> None:
        """Background analysis loop."""
        try:
            while True:
                await asyncio.sleep(300)  # Run every 5 minutes

                try:
                    # Update statistics for all metrics
                    for name in self._metric_stats.keys():
                        await self._update_statistics(name)

                except Exception as e:
                    logger.error(f"Analysis loop error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Analysis loop failed: {e}")

    async def _alert_loop(self) -> None:
        """Background alert processing loop."""
        try:
            while True:
                await asyncio.sleep(600)  # Run every 10 minutes

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
performance_metrics = PerformanceMetrics()


# Factory function
def get_performance_metrics() -> PerformanceMetrics:
    """Get performance metrics instance."""
    return performance_metrics
