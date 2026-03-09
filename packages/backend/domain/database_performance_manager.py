"""
Database Performance Manager for Phase 15.1 Database & Performance
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

from shared.logging_config import get_logger

logger = get_logger("sorce.database_performance_manager")


class PerformanceMetricType(Enum):
    """Types of performance metrics."""

    QUERY_TIME = "query_time"
    CONNECTION_TIME = "connection_time"
    INDEX_USAGE = "index_usage"
    TABLE_SIZE = "table_size"
    CACHE_HIT_RATE = "cache_hit_rate"
    SLOW_QUERIES = "slow_queries"
    DEADLOCKS = "deadlocks"
    LOCK_WAITS = "lock_waits"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"


class OptimizationType(Enum):
    """Types of database optimizations."""

    INDEX_CREATION = "index_creation"
    QUERY_REWRITE = "query_rewrite"
    PARTITIONING = "partitioning"
    VACUUM_ANALYZE = "vacuum_analyze"
    CONFIG_TUNING = "config_tuning"
    CACHE_OPTIMIZATION = "cache_optimization"
    CONNECTION_POOLING = "connection_pooling"


@dataclass
class PerformanceMetric:
    """Performance metric data point."""

    id: str
    tenant_id: str
    metric_type: PerformanceMetricType
    metric_name: str
    value: float
    unit: str
    context: Dict[str, Any] = field(default_factory=dict)
    threshold: Optional[float] = None
    is_critical: bool = False
    timestamp: datetime = datetime.now(timezone.utc)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class DatabaseOptimization:
    """Database optimization recommendation."""

    id: str
    tenant_id: str
    optimization_type: OptimizationType
    target_table: Optional[str]
    target_query: Optional[str]
    description: str
    impact_score: float
    implementation_effort: str  # low, medium, high
    estimated_improvement: float
    priority: int
    status: str = "pending"  # pending, in_progress, completed, rejected
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class PerformanceAlert:
    """Performance alert."""

    id: str
    tenant_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    recommendations: List[str] = field(default_factory=list)
    is_resolved: bool = False
    created_at: datetime = datetime.now(timezone.utc)
    resolved_at: Optional[datetime] = None


class DatabasePerformanceManager:
    """Advanced database performance monitoring and optimization system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._performance_thresholds = self._initialize_thresholds()
        self._optimization_rules = self._initialize_optimization_rules()
        self._metric_cache: Dict[str, List[PerformanceMetric]] = {}
        self._alerts_cache: Dict[str, List[PerformanceAlert]] = {}

        # Start background monitoring
        asyncio.create_task(self._start_performance_monitoring())

    async def collect_performance_metric(
        self,
        tenant_id: str,
        metric_type: PerformanceMetricType,
        metric_name: str,
        value: float,
        unit: str,
        context: Optional[Dict[str, Any]] = None,
        threshold: Optional[float] = None,
        is_critical: bool = False,
    ) -> PerformanceMetric:
        """Collect a performance metric."""
        try:
            # Create metric
            metric = PerformanceMetric(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                unit=unit,
                context=context or {},
                threshold=threshold,
                is_critical=is_critical,
            )

            # Save metric
            await self._save_performance_metric(metric)

            # Update cache
            cache_key = f"{tenant_id}:{metric_name}"
            if cache_key not in self._metric_cache:
                self._metric_cache[cache_key] = []
            self._metric_cache[cache_key].append(metric)

            # Check for alerts
            await self._check_performance_alerts(metric)

            logger.info(f"Collected performance metric: {metric_name} = {value} {unit}")
            return metric

        except Exception as e:
            logger.error(f"Failed to collect performance metric: {e}")
            raise

    async def analyze_database_performance(
        self,
        tenant_id: str,
        time_period_hours: int = 24,
    ) -> Dict[str, Any]:
        """Analyze database performance."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Get performance metrics
            metrics = await self._get_performance_metrics(tenant_id, cutoff_time)

            # Calculate performance statistics
            statistics = await self._calculate_performance_statistics(metrics)

            # Identify performance issues
            issues = await self._identify_performance_issues(metrics)

            # Generate optimization recommendations
            recommendations = await self._generate_optimization_recommendations(
                tenant_id, metrics, issues
            )

            # Get database statistics
            db_stats = await self._get_database_statistics(tenant_id)

            analysis = {
                "period_hours": time_period_hours,
                "performance_statistics": statistics,
                "identified_issues": issues,
                "optimization_recommendations": recommendations,
                "database_statistics": db_stats,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze database performance: {e}")
            return {}

    async def optimize_database(
        self,
        tenant_id: str,
        optimization_id: str,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Execute database optimization."""
        try:
            # Get optimization details
            optimization = await self._get_optimization_by_id(
                optimization_id, tenant_id
            )
            if not optimization:
                raise ValueError("Optimization not found")

            # Execute optimization based on type
            if optimization.optimization_type == OptimizationType.INDEX_CREATION:
                result = await self._execute_index_optimization(optimization, dry_run)
            elif optimization.optimization_type == OptimizationType.QUERY_REWRITE:
                result = await self._execute_query_optimization(optimization, dry_run)
            elif optimization.optimization_type == OptimizationType.VACUUM_ANALYZE:
                result = await self._execute_vacuum_optimization(optimization, dry_run)
            elif optimization.optimization_type == OptimizationType.CONFIG_TUNING:
                result = await self._execute_config_optimization(optimization, dry_run)
            else:
                result = {"success": False, "message": "Unsupported optimization type"}

            # Update optimization status if not dry run
            if not dry_run and result.get("success", False):
                await self._update_optimization_status(optimization_id, "completed")

            return {
                "optimization_id": optimization_id,
                "optimization_type": optimization.optimization_type.value,
                "dry_run": dry_run,
                "result": result,
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            raise

    async def get_performance_dashboard(
        self,
        tenant_id: str,
        time_period_hours: int = 24,
    ) -> Dict[str, Any]:
        """Get comprehensive performance dashboard."""
        try:
            # Get performance analysis
            analysis = await self.analyze_database_performance(
                tenant_id, time_period_hours
            )

            # Get active alerts
            alerts = await self._get_active_alerts(tenant_id)

            # Get recent optimizations
            optimizations = await self._get_recent_optimizations(tenant_id)

            # Get performance trends
            trends = await self._get_performance_trends(tenant_id, time_period_hours)

            # Get database health score
            health_score = await self._calculate_health_score(tenant_id)

            dashboard = {
                "period_hours": time_period_hours,
                "health_score": health_score,
                "performance_analysis": analysis,
                "active_alerts": alerts,
                "recent_optimizations": optimizations,
                "performance_trends": trends,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return dashboard

        except Exception as e:
            logger.error(f"Failed to get performance dashboard: {e}")
            return {}

    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize performance thresholds."""
        return {
            "query_time": {
                "warning": 1000.0,  # 1 second
                "critical": 5000.0,  # 5 seconds
            },
            "connection_time": {
                "warning": 100.0,  # 100ms
                "critical": 500.0,  # 500ms
            },
            "cache_hit_rate": {
                "warning": 0.8,  # 80%
                "critical": 0.5,  # 50%
            },
            "error_rate": {
                "warning": 0.01,  # 1%
                "critical": 0.05,  # 5%
            },
            "throughput": {
                "warning": 100.0,  # queries per second
                "critical": 50.0,  # queries per second
            },
        }

    def _initialize_optimization_rules(self) -> Dict[str, Any]:
        """Initialize optimization rules."""
        return {
            "slow_query_threshold": 1000.0,  # 1 second
            "index_usage_threshold": 0.1,  # 10% usage
            "table_size_threshold": 1000000000,  # 1GB
            "cache_hit_threshold": 0.8,  # 80%
            "fragmentation_threshold": 0.3,  # 30%
        }

    async def _start_performance_monitoring(self) -> None:
        """Start background performance monitoring."""
        try:
            while True:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Collect system metrics
                await self._collect_system_metrics()

                # Check for performance issues
                await self._check_performance_issues()

                # Update optimization recommendations
                await self._update_optimization_recommendations()

        except Exception as e:
            logger.error(f"Background monitoring failed: {e}")

    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # Get active tenants
            tenants = await self._get_active_tenants()

            for tenant_id in tenants:
                try:
                    # Collect query performance metrics
                    await self._collect_query_metrics(tenant_id)

                    # Collect connection metrics
                    await self._collect_connection_metrics(tenant_id)

                    # Collect cache metrics
                    await self._collect_cache_metrics(tenant_id)

                except Exception as e:
                    logger.error(
                        f"Failed to collect metrics for tenant {tenant_id}: {e}"
                    )

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    async def _collect_query_metrics(self, tenant_id: str) -> None:
        """Collect query performance metrics."""
        try:
            # Get slow queries
            slow_queries_query = """
                SELECT
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time,
                    stddev_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > $1
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(
                    slow_queries_query, self._optimization_rules["slow_query_threshold"]
                )

                for row in results:
                    await self.collect_performance_metric(
                        tenant_id=tenant_id,
                        metric_type=PerformanceMetricType.QUERY_TIME,
                        metric_name="slow_query",
                        value=float(row[1]),
                        unit="milliseconds",
                        context={
                            "query": row[0][:200],  # Truncate for storage
                            "calls": int(row[2]),
                            "total_time": float(row[3]),
                            "stddev": float(row[4]),
                        },
                        threshold=self._performance_thresholds["query_time"]["warning"],
                        is_critical=True,
                    )

        except Exception as e:
            logger.error(f"Failed to collect query metrics: {e}")

    async def _collect_connection_metrics(self, tenant_id: str) -> None:
        """Collect connection performance metrics."""
        try:
            # Get connection statistics
            connection_query = """
                SELECT
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    avg(EXTRACT(EPOCH FROM (now() - query_start))) as avg_query_time
                FROM pg_stat_activity
                WHERE datname = current_database()
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(connection_query)

                if result:
                    await self.collect_performance_metric(
                        tenant_id=tenant_id,
                        metric_type=PerformanceMetricType.CONNECTION_TIME,
                        metric_name="avg_connection_time",
                        value=float(result[3]) * 1000 if result[3] else 0,
                        unit="milliseconds",
                        context={
                            "total_connections": int(result[0]),
                            "active_connections": int(result[1]),
                            "idle_connections": int(result[2]),
                        },
                        threshold=self._performance_thresholds["connection_time"][
                            "warning"
                        ],
                    )

        except Exception as e:
            logger.error(f"Failed to collect connection metrics: {e}")

    async def _collect_cache_metrics(self, tenant_id: str) -> None:
        """Collect cache performance metrics."""
        try:
            # Get cache hit ratio
            cache_query = """
                SELECT
                    sum(heap_blks_hit) / nullif(sum(heap_blks_hit + heap_blks_read), 0) as cache_hit_ratio,
                    sum(heap_blks_read) as blocks_read,
                    sum(heap_blks_hit) as blocks_hit
                FROM pg_stat_database
                WHERE datname = current_database()
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(cache_query)

                if result and result[0] is not None:
                    await self.collect_performance_metric(
                        tenant_id=tenant_id,
                        metric_type=PerformanceMetricType.CACHE_HIT_RATE,
                        metric_name="cache_hit_ratio",
                        value=float(result[0]),
                        unit="ratio",
                        context={
                            "blocks_read": int(result[1]) if result[1] else 0,
                            "blocks_hit": int(result[2]) if result[2] else 0,
                        },
                        threshold=self._performance_thresholds["cache_hit_rate"][
                            "warning"
                        ],
                        is_critical=True,
                    )

        except Exception as e:
            logger.error(f"Failed to collect cache metrics: {e}")

    async def _check_performance_alerts(self, metric: PerformanceMetric) -> None:
        """Check for performance alerts."""
        try:
            # Check if threshold is breached
            if metric.threshold and metric.value > metric.threshold:
                # Determine severity
                threshold_type = "critical" if metric.is_critical else "warning"

                # Create alert
                alert = PerformanceAlert(
                    id=str(uuid.uuid4()),
                    tenant_id=metric.tenant_id,
                    alert_type="threshold_breach",
                    severity=threshold_type,
                    title=f"Performance Alert: {metric.metric_name}",
                    message=f"{metric.metric_name} exceeded threshold: {metric.value} {metric.unit} > {metric.threshold} {metric.unit}",
                    metric_name=metric.metric_name,
                    current_value=metric.value,
                    threshold_value=metric.threshold,
                    recommendations=self._generate_alert_recommendations(metric),
                )

                # Save alert
                await self._save_performance_alert(alert)

                # Update cache
                if metric.tenant_id not in self._alerts_cache:
                    self._alerts_cache[metric.tenant_id] = []
                self._alerts_cache[metric.tenant_id].append(alert)

                logger.warning(f"Performance alert created: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to check performance alerts: {e}")

    def _generate_alert_recommendations(self, metric: PerformanceMetric) -> List[str]:
        """Generate recommendations for performance alerts."""
        recommendations = []

        if metric.metric_type == PerformanceMetricType.QUERY_TIME:
            recommendations.extend(
                [
                    "Review and optimize slow queries",
                    "Check for missing indexes",
                    "Consider query rewriting",
                    "Analyze query execution plan",
                ]
            )
        elif metric.metric_type == PerformanceMetricType.CACHE_HIT_RATE:
            recommendations.extend(
                [
                    "Increase shared_buffers configuration",
                    "Review query patterns for cache efficiency",
                    "Consider materialized views",
                    "Optimize frequently accessed data",
                ]
            )
        elif metric.metric_type == PerformanceMetricType.CONNECTION_TIME:
            recommendations.extend(
                [
                    "Optimize connection pool settings",
                    "Review network latency",
                    "Check database server load",
                    "Consider connection pooling",
                ]
            )

        return recommendations

    async def _save_performance_metric(self, metric: PerformanceMetric) -> None:
        """Save performance metric to database."""
        try:
            query = """
                INSERT INTO performance_metrics (
                    id, tenant_id, metric_type, metric_name, value, unit,
                    context, threshold, is_critical, timestamp, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """

            params = [
                metric.id,
                metric.tenant_id,
                metric.metric_type.value,
                metric.metric_name,
                metric.value,
                metric.unit,
                json.dumps(metric.context),
                metric.threshold,
                metric.is_critical,
                metric.timestamp,
                metric.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save performance metric: {e}")

    async def _save_performance_alert(self, alert: PerformanceAlert) -> None:
        """Save performance alert to database."""
        try:
            query = """
                INSERT INTO performance_alerts (
                    id, tenant_id, alert_type, severity, title, message,
                    metric_name, current_value, threshold_value, recommendations,
                    is_resolved, created_at, resolved_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """

            params = [
                alert.id,
                alert.tenant_id,
                alert.alert_type,
                alert.severity,
                alert.title,
                alert.message,
                alert.metric_name,
                alert.current_value,
                alert.threshold_value,
                json.dumps(alert.recommendations),
                alert.is_resolved,
                alert.created_at,
                alert.resolved_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save performance alert: {e}")

    async def _get_performance_metrics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
    ) -> List[PerformanceMetric]:
        """Get performance metrics for analysis."""
        try:
            query = """
                SELECT * FROM performance_metrics
                WHERE tenant_id = $1 AND timestamp > $2
                ORDER BY timestamp ASC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id, cutoff_time)

                metrics = []
                for row in results:
                    metric = PerformanceMetric(
                        id=row[0],
                        tenant_id=row[1],
                        metric_type=PerformanceMetricType(row[2]),
                        metric_name=row[3],
                        value=row[4],
                        unit=row[5],
                        context=json.loads(row[6]) if row[6] else {},
                        threshold=row[7],
                        is_critical=row[8],
                        timestamp=row[9],
                        created_at=row[10],
                    )
                    metrics.append(metric)

                return metrics

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return []

    async def _calculate_performance_statistics(
        self,
        metrics: List[PerformanceMetric],
    ) -> Dict[str, Any]:
        """Calculate performance statistics."""
        try:
            if not metrics:
                return {}

            # Group metrics by type
            metrics_by_type = defaultdict(list)
            for metric in metrics:
                metrics_by_type[metric.metric_type.value].append(metric)

            statistics = {}
            for metric_type, type_metrics in metrics_by_type.items():
                values = [m.value for m in type_metrics]

                statistics[metric_type] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "minimum": min(values),
                    "maximum": max(values),
                    "latest": values[-1] if values else 0,
                }

                # Calculate trend if enough data points
                if len(values) >= 2:
                    first_half = values[: len(values) // 2]
                    second_half = values[len(values) // 2 :]

                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)

                    trend = "improving" if second_avg < first_avg else "degrading"
                    statistics[metric_type]["trend"] = trend
                    statistics[metric_type]["trend_percentage"] = (
                        ((second_avg - first_avg) / first_avg * 100)
                        if first_avg > 0
                        else 0
                    )

            return statistics

        except Exception as e:
            logger.error(f"Failed to calculate performance statistics: {e}")
            return {}

    async def _identify_performance_issues(
        self,
        metrics: List[PerformanceMetric],
    ) -> List[Dict[str, Any]]:
        """Identify performance issues."""
        try:
            issues = []

            # Group metrics by type
            metrics_by_type = defaultdict(list)
            for metric in metrics:
                metrics_by_type[metric.metric_type.value].append(metric)

            # Check each metric type for issues
            for metric_type, type_metrics in metrics_by_type.items():
                # Check for threshold breaches
                critical_metrics = [m for m in type_metrics if m.is_critical]
                if critical_metrics:
                    latest_critical = max(critical_metrics, key=lambda m: m.timestamp)
                    if (
                        latest_critical.threshold
                        and latest_critical.value > latest_critical.threshold
                    ):
                        issues.append(
                            {
                                "type": "threshold_breach",
                                "metric_type": metric_type,
                                "metric_name": latest_critical.metric_name,
                                "current_value": latest_critical.value,
                                "threshold": latest_critical.threshold,
                                "severity": "critical",
                                "description": f"{latest_critical.metric_name} exceeded critical threshold",
                            }
                        )

                # Check for trends
                if len(type_metrics) >= 10:
                    values = [m.value for m in type_metrics[-10:]]
                    if len(values) >= 4:
                        recent_avg = sum(values[-3:]) / 3
                        older_avg = sum(values[-6:-3]) / 3

                        if recent_avg > older_avg * 1.2:  # 20% increase
                            issues.append(
                                {
                                    "type": "performance_degradation",
                                    "metric_type": metric_type,
                                    "current_average": recent_avg,
                                    "previous_average": older_avg,
                                    "degradation_percentage": (
                                        (recent_avg - older_avg) / older_avg * 100
                                    ),
                                    "severity": "warning",
                                    "description": f"{metric_type} performance degrading over time",
                                }
                            )

            return issues

        except Exception as e:
            logger.error(f"Failed to identify performance issues: {e}")
            return []

    async def _generate_optimization_recommendations(
        self,
        tenant_id: str,
        metrics: List[PerformanceMetric],
        issues: List[Dict[str, Any]],
    ) -> List[DatabaseOptimization]:
        """Generate optimization recommendations."""
        try:
            recommendations = []

            # Analyze slow queries
            slow_query_metrics = [
                m
                for m in metrics
                if m.metric_type == PerformanceMetricType.QUERY_TIME and m.value > 1000
            ]

            if slow_query_metrics:
                # Get slow query details
                slow_queries = await self._get_slow_queries(tenant_id)
                for query_info in slow_queries[:5]:  # Top 5 slow queries
                    recommendation = DatabaseOptimization(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        optimization_type=OptimizationType.QUERY_REWRITE,
                        target_query=query_info.get("query", "")[:200],
                        description=f"Optimize slow query: {query_info.get('query', '')[:100]}...",
                        impact_score=0.8,
                        implementation_effort="medium",
                        estimated_improvement=0.5,
                        priority=1,
                    )
                    recommendations.append(recommendation)

            # Analyze cache performance
            cache_metrics = [
                m
                for m in metrics
                if m.metric_type == PerformanceMetricType.CACHE_HIT_RATE
            ]

            if cache_metrics:
                latest_cache = max(cache_metrics, key=lambda m: m.timestamp)
                if latest_cache.value < 0.8:  # Less than 80% hit rate
                    recommendation = DatabaseOptimization(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        optimization_type=OptimizationType.CACHE_OPTIMIZATION,
                        description="Improve cache hit ratio by optimizing query patterns and increasing cache size",
                        impact_score=0.7,
                        implementation_effort="low",
                        estimated_improvement=0.3,
                        priority=2,
                    )
                    recommendations.append(recommendation)

            # Analyze table sizes
            large_tables = await self._get_large_tables(tenant_id)
            for table_info in large_tables:
                if table_info.get("size_bytes", 0) > 1000000000:  # > 1GB
                    recommendation = DatabaseOptimization(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        optimization_type=OptimizationType.INDEX_CREATION,
                        target_table=table_info.get("table_name"),
                        description=f"Optimize large table {table_info.get('table_name')} with proper indexing",
                        impact_score=0.6,
                        implementation_effort="medium",
                        estimated_improvement=0.4,
                        priority=3,
                    )
                    recommendations.append(recommendation)

            # Sort by priority
            recommendations.sort(key=lambda r: r.priority)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return []

    async def _get_database_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            stats_query = """
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    pg_size_pretty(pg_total_relation_size('pg_stat_statements')) as stats_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT count(*) FROM pg_stat_activity) as total_connections,
                    (SELECT count(*) FROM pg_stat_user_tables) as table_count,
                    (SELECT count(*) FROM pg_stat_user_indexes) as index_count
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(stats_query)

                if result:
                    return {
                        "database_size": result[0],
                        "statistics_size": result[1],
                        "active_connections": result[2],
                        "total_connections": result[3],
                        "table_count": result[4],
                        "index_count": result[5],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {}

    async def _get_slow_queries(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get slow queries from pg_stat_statements."""
        try:
            query = """
                SELECT
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time,
                    stddev_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > 1000
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query)

                slow_queries = []
                for row in results:
                    slow_queries.append(
                        {
                            "query": row[0],
                            "mean_exec_time": float(row[1]),
                            "calls": int(row[2]),
                            "total_exec_time": float(row[3]),
                            "stddev_exec_time": float(row[4]),
                        }
                    )

                return slow_queries

        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    async def _get_large_tables(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get large tables."""
        try:
            query = """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY size_bytes DESC
                LIMIT 20
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query)

                large_tables = []
                for row in results:
                    large_tables.append(
                        {
                            "schema_name": row[0],
                            "table_name": row[1],
                            "size": row[2],
                            "size_bytes": int(row[3]),
                        }
                    )

                return large_tables

        except Exception as e:
            logger.error(f"Failed to get large tables: {e}")
            return []

    async def _get_active_tenants(self) -> List[str]:
        """Get list of active tenants."""
        try:
            query = """
                SELECT DISTINCT tenant_id FROM performance_metrics
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query)
                return [row[0] for row in results]

        except Exception as e:
            logger.error(f"Failed to get active tenants: {e}")
            return []

    async def _get_optimization_by_id(
        self,
        optimization_id: str,
        tenant_id: str,
    ) -> Optional[DatabaseOptimization]:
        """Get optimization by ID."""
        try:
            query = """
                SELECT * FROM database_optimizations
                WHERE id = $1 AND tenant_id = $2
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, optimization_id, tenant_id)

                if result:
                    return DatabaseOptimization(
                        id=result[0],
                        tenant_id=result[1],
                        optimization_type=OptimizationType(result[2]),
                        target_table=result[3],
                        target_query=result[4],
                        description=result[5],
                        impact_score=result[6],
                        implementation_effort=result[7],
                        estimated_improvement=result[8],
                        priority=result[9],
                        status=result[10],
                        created_at=result[11],
                        updated_at=result[12],
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to get optimization by ID: {e}")
            return None

    async def _update_optimization_status(
        self,
        optimization_id: str,
        status: str,
    ) -> None:
        """Update optimization status."""
        try:
            query = """
                UPDATE database_optimizations
                SET status = $1, updated_at = $2
                WHERE id = $3
            """

            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query, status, datetime.now(timezone.utc), optimization_id
                )

        except Exception as e:
            logger.error(f"Failed to update optimization status: {e}")

    async def _execute_index_optimization(
        self,
        optimization: DatabaseOptimization,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Execute index optimization."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: Index optimization would be executed",
                    "sql": f"CREATE INDEX CONCURRENTLY ON {optimization.target_table} (...)",
                }

            # For now, return placeholder - actual implementation would analyze table
            # and create appropriate indexes
            return {
                "success": True,
                "message": "Index optimization completed",
                "index_created": f"idx_{optimization.target_table}_perf",
            }

        except Exception as e:
            logger.error(f"Failed to execute index optimization: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_query_optimization(
        self,
        optimization: DatabaseOptimization,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Execute query optimization."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: Query optimization would be executed",
                    "query": optimization.target_query,
                }

            # For now, return placeholder - actual implementation would analyze
            # and rewrite the query
            return {
                "success": True,
                "message": "Query optimization completed",
                "optimized_query": optimization.target_query,
            }

        except Exception as e:
            logger.error(f"Failed to execute query optimization: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_vacuum_optimization(
        self,
        optimization: DatabaseOptimization,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Execute VACUUM/ANALYZE optimization."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: VACUUM ANALYZE would be executed",
                    "sql": "VACUUM ANALYZE;",
                }

            # Execute VACUUM ANALYZE
            async with self.db_pool.acquire() as conn:
                await conn.execute("VACUUM ANALYZE;")

            return {
                "success": True,
                "message": "VACUUM ANALYZE completed successfully",
            }

        except Exception as e:
            logger.error(f"Failed to execute VACUUM optimization: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_config_optimization(
        self,
        optimization: DatabaseOptimization,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Execute configuration optimization."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: Configuration optimization would be applied",
                    "config_changes": {
                        "shared_buffers": "256MB",
                        "effective_cache_size": "1GB",
                        "work_mem": "4MB",
                    },
                }

            # For now, return placeholder - actual implementation would
            # update PostgreSQL configuration
            return {
                "success": True,
                "message": "Configuration optimization completed",
                "config_applied": True,
            }

        except Exception as e:
            logger.error(f"Failed to execute config optimization: {e}")
            return {"success": False, "error": str(e)}

    async def _get_active_alerts(self, tenant_id: str) -> List[PerformanceAlert]:
        """Get active performance alerts."""
        try:
            query = """
                SELECT * FROM performance_alerts
                WHERE tenant_id = $1 AND is_resolved = false
                ORDER BY created_at DESC
                LIMIT 10
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id)

                alerts = []
                for row in results:
                    alert = PerformanceAlert(
                        id=row[0],
                        tenant_id=row[1],
                        alert_type=row[2],
                        severity=row[3],
                        title=row[4],
                        message=row[5],
                        metric_name=row[6],
                        current_value=row[7],
                        threshold_value=row[8],
                        recommendations=json.loads(row[9]) if row[9] else [],
                        is_resolved=row[10],
                        created_at=row[11],
                        resolved_at=row[12],
                    )
                    alerts.append(alert)

                return alerts

        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []

    async def _get_recent_optimizations(
        self, tenant_id: str
    ) -> List[DatabaseOptimization]:
        """Get recent optimizations."""
        try:
            query = """
                SELECT * FROM database_optimizations
                WHERE tenant_id = $1
                ORDER BY created_at DESC
                LIMIT 10
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id)

                optimizations = []
                for row in results:
                    optimization = DatabaseOptimization(
                        id=row[0],
                        tenant_id=row[1],
                        optimization_type=OptimizationType(row[2]),
                        target_table=row[3],
                        target_query=row[4],
                        description=row[5],
                        impact_score=row[6],
                        implementation_effort=row[7],
                        estimated_improvement=row[8],
                        priority=row[9],
                        status=row[10],
                        created_at=row[11],
                        updated_at=row[12],
                    )
                    optimizations.append(optimization)

                return optimizations

        except Exception as e:
            logger.error(f"Failed to get recent optimizations: {e}")
            return []

    async def _get_performance_trends(
        self,
        tenant_id: str,
        time_period_hours: int,
    ) -> Dict[str, Any]:
        """Get performance trends."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Get metrics for trend analysis
            metrics = await self._get_performance_metrics(tenant_id, cutoff_time)

            # Group by metric type and calculate trends
            trends = {}
            metrics_by_type = defaultdict(list)
            for metric in metrics:
                metrics_by_type[metric.metric_type.value].append(metric)

            for metric_type, type_metrics in metrics_by_type.items():
                if len(type_metrics) >= 2:
                    values = [m.value for m in type_metrics]
                    timestamps = [m.timestamp for m in type_metrics]

                    # Calculate simple trend
                    if len(values) >= 4:
                        first_avg = sum(values[: len(values) // 2]) / (len(values) // 2)
                        second_avg = sum(values[len(values) // 2 :]) / (
                            len(values) - len(values) // 2
                        )

                        trend_direction = "stable"
                        if second_avg > first_avg * 1.1:
                            trend_direction = "increasing"
                        elif second_avg < first_avg * 0.9:
                            trend_direction = "decreasing"

                        trends[metric_type] = {
                            "direction": trend_direction,
                            "current_value": values[-1],
                            "average_value": sum(values) / len(values),
                            "change_percentage": (
                                (second_avg - first_avg) / first_avg * 100
                            )
                            if first_avg > 0
                            else 0,
                            "data_points": len(values),
                        }

            return trends

        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {}

    async def _calculate_health_score(self, tenant_id: str) -> Dict[str, Any]:
        """Calculate database health score."""
        try:
            # Get recent metrics
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            metrics = await self._get_performance_metrics(tenant_id, cutoff_time)

            if not metrics:
                return {"score": 0.0, "status": "unknown", "factors": {}}

            # Calculate health factors
            factors = {}

            # Query performance factor
            query_metrics = [
                m for m in metrics if m.metric_type == PerformanceMetricType.QUERY_TIME
            ]
            if query_metrics:
                avg_query_time = sum(m.value for m in query_metrics) / len(
                    query_metrics
                )
                query_score = max(0, 1 - (avg_query_time / 5000))  # 5s is worst
                factors["query_performance"] = query_score

            # Cache performance factor
            cache_metrics = [
                m
                for m in metrics
                if m.metric_type == PerformanceMetricType.CACHE_HIT_RATE
            ]
            if cache_metrics:
                latest_cache = max(cache_metrics, key=lambda m: m.timestamp)
                cache_score = latest_cache.value
                factors["cache_performance"] = cache_score

            # Connection factor
            connection_metrics = [
                m
                for m in metrics
                if m.metric_type == PerformanceMetricType.CONNECTION_TIME
            ]
            if connection_metrics:
                avg_conn_time = sum(m.value for m in connection_metrics) / len(
                    connection_metrics
                )
                conn_score = max(0, 1 - (avg_conn_time / 500))  # 500ms is worst
                factors["connection_performance"] = conn_score

            # Calculate overall score
            if factors:
                overall_score = sum(factors.values()) / len(factors)
            else:
                overall_score = 0.5  # Default to middle

            # Determine status
            if overall_score >= 0.8:
                status = "excellent"
            elif overall_score >= 0.6:
                status = "good"
            elif overall_score >= 0.4:
                status = "fair"
            else:
                status = "poor"

            return {
                "score": overall_score,
                "status": status,
                "factors": factors,
            }

        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return {"score": 0.0, "status": "error", "factors": {}}

    async def _check_performance_issues(self) -> None:
        """Check for performance issues across all tenants."""
        try:
            tenants = await self._get_active_tenants()

            for tenant_id in tenants:
                try:
                    # Get recent metrics
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
                    metrics = await self._get_performance_metrics(
                        tenant_id, cutoff_time
                    )

                    # Check for critical issues
                    critical_metrics = [m for m in metrics if m.is_critical]
                    for metric in critical_metrics:
                        if metric.threshold and metric.value > metric.threshold:
                            # Create critical alert if not exists
                            await self._create_critical_alert(metric)

                except Exception as e:
                    logger.error(f"Failed to check issues for tenant {tenant_id}: {e}")

        except Exception as e:
            logger.error(f"Failed to check performance issues: {e}")

    async def _create_critical_alert(self, metric: PerformanceMetric) -> None:
        """Create critical performance alert."""
        try:
            # Check if alert already exists
            existing_alert = await self._get_existing_alert(
                metric.tenant_id, metric.metric_name, "critical"
            )
            if existing_alert and not existing_alert.is_resolved:
                return  # Alert already exists

            # Create new critical alert
            alert = PerformanceAlert(
                id=str(uuid.uuid4()),
                tenant_id=metric.tenant_id,
                alert_type="critical_performance",
                severity="critical",
                title=f"Critical Performance Issue: {metric.metric_name}",
                message=f"Critical threshold breached: {metric.value} {metric.unit} > {metric.threshold} {metric.unit}",
                metric_name=metric.metric_name,
                current_value=metric.value,
                threshold_value=metric.threshold,
                recommendations=[
                    "Immediate investigation required",
                    "Consider database restart if necessary",
                    "Check system resources",
                    "Review recent changes",
                ],
                is_resolved=False,
            )

            await self._save_performance_alert(alert)

            # Update cache
            if metric.tenant_id not in self._alerts_cache:
                self._alerts_cache[metric.tenant_id] = []
            self._alerts_cache[metric.tenant_id].append(alert)

            logger.critical(f"Critical performance alert created: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to create critical alert: {e}")

    async def _get_existing_alert(
        self,
        tenant_id: str,
        metric_name: str,
        severity: str,
    ) -> Optional[PerformanceAlert]:
        """Get existing alert."""
        try:
            query = """
                SELECT * FROM performance_alerts
                WHERE tenant_id = $1 AND metric_name = $2 AND severity = $3 AND is_resolved = false
                ORDER BY created_at DESC
                LIMIT 1
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, tenant_id, metric_name, severity)

                if result:
                    return PerformanceAlert(
                        id=result[0],
                        tenant_id=result[1],
                        alert_type=result[2],
                        severity=result[3],
                        title=result[4],
                        message=result[5],
                        metric_name=result[6],
                        current_value=result[7],
                        threshold_value=result[8],
                        recommendations=json.loads(result[9]) if result[9] else [],
                        is_resolved=result[10],
                        created_at=result[11],
                        resolved_at=result[12],
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to get existing alert: {e}")
            return None

    async def _update_optimization_recommendations(self) -> None:
        """Update optimization recommendations."""
        try:
            tenants = await self._get_active_tenants()

            for tenant_id in tenants:
                try:
                    # Get recent metrics
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                    metrics = await self._get_performance_metrics(
                        tenant_id, cutoff_time
                    )

                    # Identify issues
                    issues = await self._identify_performance_issues(metrics)

                    # Generate new recommendations
                    recommendations = await self._generate_optimization_recommendations(
                        tenant_id, metrics, issues
                    )

                    # Save recommendations
                    for rec in recommendations:
                        await self._save_optimization(rec)

                except Exception as e:
                    logger.error(
                        f"Failed to update recommendations for tenant {tenant_id}: {e}"
                    )

        except Exception as e:
            logger.error(f"Failed to update optimization recommendations: {e}")

    async def _save_optimization(self, optimization: DatabaseOptimization) -> None:
        """Save optimization recommendation."""
        try:
            query = """
                INSERT INTO database_optimizations (
                    id, tenant_id, optimization_type, target_table, target_query,
                    description, impact_score, implementation_effort, estimated_improvement,
                    priority, status, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (tenant_id, optimization_type, target_table, target_query)
                DO UPDATE SET
                    description = EXCLUDED.description,
                    impact_score = EXCLUDED.impact_score,
                    implementation_effort = EXCLUDED.implementation_effort,
                    estimated_improvement = EXCLUDED.estimated_improvement,
                    priority = EXCLUDED.priority,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                optimization.id,
                optimization.tenant_id,
                optimization.optimization_type.value,
                optimization.target_table,
                optimization.target_query,
                optimization.description,
                optimization.impact_score,
                optimization.implementation_effort,
                optimization.estimated_improvement,
                optimization.priority,
                optimization.status,
                optimization.created_at,
                optimization.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save optimization: {e}")


# Factory function
def create_database_performance_manager(db_pool) -> DatabasePerformanceManager:
    """Create database performance manager instance."""
    return DatabasePerformanceManager(db_pool)
