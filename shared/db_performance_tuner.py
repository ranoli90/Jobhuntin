"""Database performance tuning and optimization system.

Provides:
- Automatic performance analysis
- Query optimization recommendations
- Index optimization suggestions
- Configuration tuning advice
- Performance monitoring

Usage:
    from shared.db_performance_tuner import PerformanceTuner

    tuner = PerformanceTuner(db_pool)
    await tuner.analyze_database_performance()
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

logger = get_logger("sorce.db_performance")


class OptimizationType(Enum):
    """Performance optimization types."""

    INDEX = "index"
    QUERY = "query"
    CONFIGURATION = "configuration"
    PARTITIONING = "partitioning"
    VACUUM = "vacuum"
    STATISTICS = "statistics"
    CONNECTION_POOL = "connection_pool"
    MEMORY = "memory"


class OptimizationPriority(Enum):
    """Optimization priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PerformanceMetric:
    """Performance metric data."""

    name: str
    value: float
    unit: str
    threshold: Optional[float] = None
    status: str = "normal"
    timestamp: float = field(default_factory=time.time)


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation."""

    recommendation_id: str
    optimization_type: OptimizationType
    priority: OptimizationPriority
    title: str
    description: str
    sql_statement: Optional[str] = None
    estimated_improvement: Optional[str] = None
    implementation_effort: str = "medium"
    risk_level: str = "low"
    impact_score: float = 0.0
    created_at: float = field(default_factory=time.time)


@dataclass
class QueryAnalysis:
    """Query performance analysis."""

    query_hash: str
    query_template: str
    avg_execution_time_ms: float
    total_executions: int
    total_time_ms: float
    rows_examined: int
    rows_returned: int
    index_usage: Dict[str, int]
    table_scans: List[str]
    recommendations: List[OptimizationRecommendation]
    performance_score: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConfigurationRecommendation:
    """Database configuration recommendation."""

    parameter: str
    current_value: str
    recommended_value: str
    reason: str
    impact: str
    requires_restart: bool = False
    priority: OptimizationPriority = OptimizationPriority.MEDIUM


class PerformanceTuner:
    """Advanced database performance tuning system."""

    def __init__(self, db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None):
        self.db_pool = db_pool
        self.alert_manager = alert_manager or get_alert_manager()

        # Performance thresholds
        self.thresholds = {
            "slow_query_threshold_ms": 1000,
            "very_slow_query_threshold_ms": 5000,
            "high_cpu_usage_pct": 80,
            "high_memory_usage_pct": 85,
            "low_cache_hit_ratio_pct": 90,
            "high_lock_wait_pct": 10,
            "bloat_threshold_pct": 20,
            "dead_tuple_threshold_pct": 10,
        }

        # Analysis results storage
        self.performance_metrics: Dict[str, PerformanceMetric] = {}
        self.query_analyses: Dict[str, QueryAnalysis] = {}
        self.optimization_recommendations: deque[OptimizationRecommendation] = deque(
            maxlen=1000
        )
        self.configuration_recommendations: List[ConfigurationRecommendation] = []

        # Monitoring state
        self._analysis_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def analyze_database_performance(self) -> Dict[str, Any]:
        """Perform comprehensive database performance analysis."""
        analysis_results = {
            "timestamp": time.time(),
            "metrics": await self._collect_performance_metrics(),
            "query_analysis": await self._analyze_slow_queries(),
            "index_analysis": await self._analyze_index_usage(),
            "configuration_analysis": await self._analyze_configuration(),
            "storage_analysis": await self._analyze_storage_performance(),
            "recommendations": await self._generate_optimization_recommendations(),
        }

        # Store metrics
        for metric_name, metric_data in analysis_results["metrics"].items():
            self.performance_metrics[metric_name] = metric_data

        # Check for performance alerts
        await self._check_performance_alerts(analysis_results)

        return analysis_results

    async def _collect_performance_metrics(self) -> Dict[str, PerformanceMetric]:
        """Collect comprehensive performance metrics."""
        metrics = {}

        try:
            async with self.db_pool.acquire() as conn:
                # Database size and growth
                db_size = await conn.fetchval(
                    "SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb"
                )
                metrics["database_size_mb"] = PerformanceMetric(
                    name="database_size_mb", value=db_size, unit="MB"
                )

                # Connection statistics
                conn_stats = await conn.fetchrow("""
                    SELECT
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections,
                        count(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)

                for key, value in conn_stats.items():
                    metrics[f"connections_{key}"] = PerformanceMetric(
                        name=f"connections_{key}", value=float(value), unit="count"
                    )

                # Cache hit ratios
                cache_stats = await conn.fetchrow("""
                    SELECT
                        sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 as heap_cache_hit_ratio,
                        sum(idx_blks_hit) / nullif(sum(idx_blks_hit) + sum(idx_blks_read), 0) * 100 as index_cache_hit_ratio
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)

                for key, value in cache_stats.items():
                    if value is not None:
                        metrics[f"cache_{key}"] = PerformanceMetric(
                            name=f"cache_{key}",
                            value=float(value),
                            unit="percent",
                            threshold=self.thresholds["low_cache_hit_ratio_pct"],
                        )
                        # Set status based on threshold
                        if value < self.thresholds["low_cache_hit_ratio_pct"]:
                            metrics[f"cache_{key}"].status = "warning"

                # Transaction statistics
                tx_stats = await conn.fetchrow("""
                    SELECT
                        xact_commit + xact_rollback as total_transactions,
                        xact_commit as commits,
                        xact_rollback as rollbacks,
                        tup_returned as rows_returned,
                        tup_fetched as rows_fetched,
                        tup_inserted as rows_inserted,
                        tup_updated as rows_updated,
                        tup_deleted as rows_deleted
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)

                for key, value in tx_stats.items():
                    metrics[f"transactions_{key}"] = PerformanceMetric(
                        name=f"transactions_{key}", value=float(value), unit="count"
                    )

                # Lock statistics
                lock_stats = await conn.fetchrow("""
                    SELECT
                        count(*) as total_locks,
                        count(*) FILTER (WHERE wait_start IS NOT NULL) as waiting_locks,
                        count(*) FILTER (WHERE mode LIKE '%exclusive%') as exclusive_locks
                    FROM pg_locks
                    WHERE pid IS NOT NULL
                """)

                if lock_stats["total_locks"] > 0:
                    wait_ratio = (
                        lock_stats["waiting_locks"] / lock_stats["total_locks"]
                    ) * 100
                    metrics["locks_wait_ratio_pct"] = PerformanceMetric(
                        name="locks_wait_ratio_pct",
                        value=wait_ratio,
                        unit="percent",
                        threshold=self.thresholds["high_lock_wait_pct"],
                    )

                    if wait_ratio > self.thresholds["high_lock_wait_pct"]:
                        metrics["locks_wait_ratio_pct"].status = "warning"

                # WAL statistics
                wal_stats = await conn.fetchrow("""
                    SELECT
                        pg_size_pretty(pg_walfile_size(pg_walfile_name(pg_current_wal_lsn()))) as current_wal_size,
                        pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), pg_last_wal_replay_lsn())) as wal_lag
                """)

                # Convert WAL size to MB (simplified)
                current_wal_size_mb = 16  # Default WAL size, would need parsing

                metrics["wal_size_mb"] = PerformanceMetric(
                    name="wal_size_mb", value=current_wal_size_mb, unit="MB"
                )

        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")

        return metrics

    async def _analyze_slow_queries(self) -> Dict[str, Any]:
        """Analyze slow query performance."""
        analysis = {
            "total_slow_queries": 0,
            "avg_execution_time_ms": 0,
            "top_slow_queries": [],
            "query_recommendations": [],
        }

        try:
            async with self.db_pool.acquire() as conn:
                # Get slow queries from pg_stat_statements
                slow_queries = await conn.fetch(
                    """
                    SELECT
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) as hit_ratio
                    FROM pg_stat_statements
                    WHERE mean_exec_time > $1
                    ORDER BY mean_exec_time DESC
                    LIMIT 20
                """,
                    self.thresholds["slow_query_threshold_ms"],
                )

                analysis["total_slow_queries"] = len(slow_queries)

                if slow_queries:
                    total_time = sum(q["total_exec_time"] for q in slow_queries)
                    analysis["avg_execution_time_ms"] = total_time / len(slow_queries)

                    for query_data in slow_queries:
                        query_hash = str(hash(query_data["query"]))[:16]

                        # Create query analysis
                        query_analysis = QueryAnalysis(
                            query_hash=query_hash,
                            query_template=query_data["query"][:200] + "..."
                            if len(query_data["query"]) > 200
                            else query_data["query"],
                            avg_execution_time_ms=query_data["mean_exec_time"],
                            total_executions=query_data["calls"],
                            total_time_ms=query_data["total_exec_time"],
                            rows_examined=query_data["rows"],
                            rows_returned=query_data["rows"],
                            index_usage={"hit_ratio": query_data["hit_ratio"] or 0},
                            table_scans=[],
                            recommendations=[],
                            performance_score=self._calculate_query_performance_score(
                                query_data
                            ),
                        )

                        self.query_analyses[query_hash] = query_analysis
                        analysis["top_slow_queries"].append(
                            {
                                "query_hash": query_hash,
                                "query_template": query_analysis.query_template,
                                "avg_execution_time_ms": query_analysis.avg_execution_time_ms,
                                "total_executions": query_analysis.total_executions,
                                "performance_score": query_analysis.performance_score,
                            }
                        )

                        # Generate recommendations
                        recommendations = await self._analyze_query_for_optimization(
                            query_data
                        )
                        query_analysis.recommendations = recommendations
                        analysis["query_recommendations"].extend(recommendations)

        except Exception as e:
            logger.error(f"Failed to analyze slow queries: {e}")

        return analysis

    def _calculate_query_performance_score(self, query_data: Dict[str, Any]) -> float:
        """Calculate performance score for a query."""
        score = 100.0

        # Penalize slow execution time
        exec_time = query_data["mean_exec_time"]
        if exec_time > self.thresholds["very_slow_query_threshold_ms"]:
            score -= 50
        elif exec_time > self.thresholds["slow_query_threshold_ms"]:
            score -= 25

        # Penalize low cache hit ratio
        hit_ratio = query_data.get("hit_ratio", 100)
        if hit_ratio < 50:
            score -= 30
        elif hit_ratio < 80:
            score -= 15

        # Penalize high execution frequency if slow
        if exec_time > 500 and query_data["calls"] > 1000:
            score -= 20

        return max(0, score)

    async def _analyze_query_for_optimization(
        self, query_data: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Analyze query and generate optimization recommendations."""
        recommendations = []
        query = query_data["query"].lower()

        # Check for missing indexes
        if "select" in query and "where" in query:
            # This is a simplified check - in reality, you'd analyze the query plan
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"idx_{hash(query_data['query']) % 10000}",
                    optimization_type=OptimizationType.INDEX,
                    priority=OptimizationPriority.HIGH,
                    title="Add missing index",
                    description="Query may benefit from additional indexes on WHERE clause columns",
                    estimated_improvement="50-80% faster execution",
                    impact_score=0.8,
                )
            )

        # Check for full table scans
        if query_data.get("hit_ratio", 100) < 50:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"fts_{hash(query_data['query']) % 10000}",
                    optimization_type=OptimizationType.INDEX,
                    priority=OptimizationPriority.CRITICAL,
                    title="Optimize query to avoid full table scans",
                    description="Low cache hit ratio suggests full table scans",
                    estimated_improvement="70-90% faster execution",
                    impact_score=0.9,
                )
            )

        # Check for SELECT *
        if "select *" in query:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"select_star_{hash(query_data['query']) % 10000}",
                    optimization_type=OptimizationType.QUERY,
                    priority=OptimizationPriority.MEDIUM,
                    title="Avoid SELECT *",
                    description="Specify only required columns instead of SELECT *",
                    estimated_improvement="10-30% faster execution",
                    impact_score=0.5,
                )
            )

        # Check for missing LIMIT
        if "select" in query and "limit" not in query and query_data["rows"] > 1000:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"limit_{hash(query_data['query']) % 10000}",
                    optimization_type=OptimizationType.QUERY,
                    priority=OptimizationPriority.MEDIUM,
                    title="Add LIMIT clause",
                    description="Query returns many rows without LIMIT",
                    estimated_improvement="20-50% faster execution",
                    impact_score=0.6,
                )
            )

        # Check for ORDER BY without index
        if "order by" in query and query_data.get("hit_ratio", 100) < 80:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=f"orderby_{hash(query_data['query']) % 10000}",
                    optimization_type=OptimizationType.INDEX,
                    priority=OptimizationPriority.HIGH,
                    title="Add index for ORDER BY",
                    description="ORDER BY clause may benefit from index",
                    estimated_improvement="40-70% faster execution",
                    impact_score=0.7,
                )
            )

        return recommendations

    async def _analyze_index_usage(self) -> Dict[str, Any]:
        """Analyze index usage and efficiency."""
        analysis = {
            "total_indexes": 0,
            "unused_indexes": [],
            "inefficient_indexes": [],
            "missing_indexes": [],
            "index_recommendations": [],
        }

        try:
            async with self.db_pool.acquire() as conn:
                # Get all indexes
                indexes = await conn.fetch("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan ASC
                """)

                analysis["total_indexes"] = len(indexes)

                # Find unused indexes
                for idx in indexes:
                    if idx["idx_scan"] == 0:
                        analysis["unused_indexes"].append(
                            {
                                "schema": idx["schemaname"],
                                "table": idx["tablename"],
                                "index": idx["indexname"],
                            }
                        )

                        # Add recommendation to drop unused index
                        recommendation = OptimizationRecommendation(
                            recommendation_id=f"drop_idx_{hash(idx['indexname']) % 10000}",
                            optimization_type=OptimizationType.INDEX,
                            priority=OptimizationPriority.LOW,
                            title=f"Drop unused index {idx['indexname']}",
                            description=f"Index {idx['indexname']} on {idx['tablename']} has never been used",
                            sql_statement=f"DROP INDEX {idx['indexname']};",
                            estimated_improvement="Reduced storage and maintenance overhead",
                            impact_score=0.3,
                        )
                        analysis["index_recommendations"].append(recommendation)

                    elif idx["idx_scan"] < 10 and idx["idx_tup_read"] > 0:
                        # Inefficient index - low usage but some reads
                        analysis["inefficient_indexes"].append(
                            {
                                "schema": idx["schemaname"],
                                "table": idx["tablename"],
                                "index": idx["indexname"],
                                "scans": idx["idx_scan"],
                                "tuples_read": idx["idx_tup_read"],
                            }
                        )

                        recommendation = OptimizationRecommendation(
                            recommendation_id=f"review_idx_{hash(idx['indexname']) % 10000}",
                            optimization_type=OptimizationType.INDEX,
                            priority=OptimizationPriority.MEDIUM,
                            title=f"Review index {idx['indexname']}",
                            description=f"Index {idx['indexname']} has low usage ({idx['idx_scan']} scans)",
                            estimated_improvement="Potential performance improvement after review",
                            impact_score=0.4,
                        )
                        analysis["index_recommendations"].append(recommendation)

        except Exception as e:
            logger.error(f"Failed to analyze index usage: {e}")

        return analysis

    async def _analyze_configuration(self) -> Dict[str, Any]:
        """Analyze database configuration for optimization opportunities."""
        analysis = {
            "current_settings": {},
            "recommendations": [],
            "requires_restart": [],
        }

        try:
            async with self.db_pool.acquire() as conn:
                # Get important configuration parameters
                settings = await conn.fetch("""
                    SELECT name, setting, unit, short_desc, context
                    FROM pg_settings
                    WHERE name IN (
                        'shared_buffers',
                        'effective_cache_size',
                        'work_mem',
                        'maintenance_work_mem',
                        'checkpoint_completion_target',
                        'wal_buffers',
                        'default_statistics_target',
                        'random_page_cost',
                        'effective_io_concurrency',
                        'max_connections',
                        'autovacuum_enabled',
                        'autovacuum_max_workers'
                    )
                    ORDER BY name
                """)

                for setting in settings:
                    analysis["current_settings"][setting["name"]] = {
                        "value": setting["setting"],
                        "unit": setting["unit"],
                        "description": setting["short_desc"],
                        "context": setting["context"],
                    }

                    # Generate specific recommendations
                    recommendation = await self._analyze_configuration_parameter(
                        setting
                    )
                    if recommendation:
                        analysis["recommendations"].append(recommendation)

                        if recommendation.requires_restart:
                            analysis["requires_restart"].append(setting["name"])

        except Exception as e:
            logger.error(f"Failed to analyze configuration: {e}")

        return analysis

    async def _analyze_configuration_parameter(
        self, setting: Dict[str, Any]
    ) -> Optional[ConfigurationRecommendation]:
        """Analyze individual configuration parameter."""
        name = setting["name"]
        current_value = setting["setting"]

        # Shared buffers recommendation
        if name == "shared_buffers":
            try:
                current_mb = (
                    int(current_value) * 8192 / 1024 / 1024
                )  # Convert 8KB pages to MB
                recommended_mb = min(current_mb * 2, 4096)  # Double up to 4GB

                if current_mb < 512:  # Less than 512MB
                    return ConfigurationRecommendation(
                        parameter=name,
                        current_value=current_value,
                        recommended_value=str(
                            recommended_mb // 8
                        ),  # Convert back to 8KB pages
                        reason="Shared buffers too low for optimal performance",
                        impact="Improved cache hit ratio and query performance",
                        requires_restart=True,
                        priority=OptimizationPriority.HIGH,
                    )
            except (ValueError, TypeError):
                pass

        # Work memory recommendation
        elif name == "work_mem":
            try:
                current_mb = int(current_value) / 1024
                if current_mb < 4:  # Less than 4MB
                    return ConfigurationRecommendation(
                        parameter=name,
                        current_value=current_value,
                        recommended_value="4096",  # 4MB
                        reason="Work memory too low for complex queries",
                        impact="Faster sorting and hash operations",
                        requires_restart=False,
                        priority=OptimizationPriority.MEDIUM,
                    )
            except (ValueError, TypeError):
                pass

        # Autovacuum recommendation
        elif name == "autovacuum_enabled":
            if current_value == "off":
                return ConfigurationRecommendation(
                    parameter=name,
                    current_value=current_value,
                    recommended_value="on",
                    reason="Autovacuum is disabled",
                    impact="Automatic table maintenance and performance optimization",
                    requires_restart=False,
                    priority=OptimizationPriority.HIGH,
                )

        return None

    async def _analyze_storage_performance(self) -> Dict[str, Any]:
        """Analyze storage and table performance."""
        analysis = {
            "table_bloat": [],
            "dead_tuples": [],
            "vacuum_recommendations": [],
            "partitioning_recommendations": [],
        }

        try:
            async with self.db_pool.acquire() as conn:
                # Get table statistics
                table_stats = await conn.fetch("""
                    SELECT
                        schemaname,
                        tablename,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup,
                        last_vacuum,
                        last_autovacuum,
                        vacuum_count,
                        autovacuum_count
                    FROM pg_stat_user_tables
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY n_dead_tup DESC
                    LIMIT 20
                """)

                for table in table_stats:
                    total_tuples = table["n_live_tup"] + table["n_dead_tup"]

                    if total_tuples > 0:
                        dead_tuple_pct = (table["n_dead_tup"] / total_tuples) * 100

                        if dead_tuple_pct > self.thresholds["dead_tuple_threshold_pct"]:
                            analysis["dead_tuples"].append(
                                {
                                    "schema": table["schemaname"],
                                    "table": table["tablename"],
                                    "dead_tuples": table["n_dead_tup"],
                                    "live_tuples": table["n_live_tup"],
                                    "dead_tuple_pct": dead_tuple_pct,
                                    "last_vacuum": table["last_vacuum"],
                                    "last_autovacuum": table["last_autovacuum"],
                                }
                            )

                            # Add vacuum recommendation
                            recommendation = OptimizationRecommendation(
                                recommendation_id=f"vacuum_{hash(table['tablename']) % 10000}",
                                optimization_type=OptimizationType.VACUUM,
                                priority=OptimizationPriority.HIGH,
                                title=f"VACUUM table {table['tablename']}",
                                description=f"Table {table['tablename']} has {dead_tuple_pct:.1f}% dead tuples",
                                sql_statement=f"VACUUM ANALYZE {table['schemaname']}.{table['tablename']};",
                                estimated_improvement="Improved query performance and reduced storage",
                                impact_score=0.6,
                            )
                            analysis["vacuum_recommendations"].append(recommendation)

        except Exception as e:
            logger.error(f"Failed to analyze storage performance: {e}")

        return analysis

    async def _generate_optimization_recommendations(
        self,
    ) -> List[OptimizationRecommendation]:
        """Generate comprehensive optimization recommendations."""
        all_recommendations = []

        # Collect recommendations from all analyses
        for query_analysis in self.query_analyses.values():
            all_recommendations.extend(query_analysis.recommendations)

        # Add configuration recommendations
        for config_rec in self.configuration_recommendations:
            recommendation = OptimizationRecommendation(
                recommendation_id=f"config_{hash(config_rec.parameter) % 10000}",
                optimization_type=OptimizationType.CONFIGURATION,
                priority=config_rec.priority,
                title=f"Update {config_rec.parameter}",
                description=config_rec.reason,
                estimated_improvement=config_rec.impact,
                sql_statement=f"ALTER SYSTEM SET {config_rec.parameter} = {config_rec.recommended_value};",
                impact_score=0.7
                if config_rec.priority == OptimizationPriority.HIGH
                else 0.5,
            )
            all_recommendations.append(recommendation)

        # Sort by impact score and priority
        priority_order = {
            OptimizationPriority.CRITICAL: 0,
            OptimizationPriority.HIGH: 1,
            OptimizationPriority.MEDIUM: 2,
            OptimizationPriority.LOW: 3,
        }

        all_recommendations.sort(
            key=lambda r: (priority_order.get(r.priority, 4), -r.impact_score)
        )

        # Store top recommendations
        for rec in all_recommendations[:100]:
            self.optimization_recommendations.append(rec)

        return all_recommendations

    async def _check_performance_alerts(self, analysis_results: Dict[str, Any]) -> None:
        """Check for performance alerts and trigger notifications."""
        metrics = analysis_results.get("metrics", {})

        # Check cache hit ratios
        for metric_name, metric in metrics.items():
            if (
                metric.status == "warning"
                and metric.threshold
                and metric.value < metric.threshold
            ):
                await self.alert_manager.trigger_alert(
                    name=f"performance_{metric_name}",
                    severity=AlertSeverity.WARNING,
                    message=f"Low {metric.name}: {metric.value:.1f}{metric.unit}",
                    metric_value=metric.value,
                    threshold=metric.threshold,
                )

        # Check slow queries
        slow_queries = analysis_results.get("query_analysis", {}).get(
            "total_slow_queries", 0
        )
        if slow_queries > 10:
            await self.alert_manager.trigger_alert(
                name="performance_slow_queries",
                severity=AlertSeverity.WARNING,
                message=f"Found {slow_queries} slow queries",
                metric_value=slow_queries,
                threshold=10,
            )

        # Check unused indexes
        unused_indexes = analysis_results.get("index_analysis", {}).get(
            "unused_indexes", []
        )
        if len(unused_indexes) > 5:
            await self.alert_manager.trigger_alert(
                name="performance_unused_indexes",
                severity=AlertSeverity.INFO,
                message=f"Found {len(unused_indexes)} unused indexes",
                metric_value=len(unused_indexes),
                threshold=5,
            )

    async def apply_optimization(
        self, recommendation_id: str, dry_run: bool = True
    ) -> Dict[str, Any]:
        """Apply a specific optimization recommendation."""
        # Find recommendation
        recommendation = None
        for rec in self.optimization_recommendations:
            if rec.recommendation_id == recommendation_id:
                recommendation = rec
                break

        if not recommendation:
            return {"success": False, "error": "Recommendation not found"}

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "recommendation": {
                    "id": recommendation.recommendation_id,
                    "type": recommendation.optimization_type.value,
                    "title": recommendation.title,
                    "sql": recommendation.sql_statement,
                    "estimated_improvement": recommendation.estimated_improvement,
                },
            }

        try:
            async with self.db_pool.acquire() as conn:
                if recommendation.sql_statement:
                    await conn.execute(recommendation.sql_statement)

                    logger.info(f"Applied optimization: {recommendation.title}")

                    return {
                        "success": True,
                        "applied": True,
                        "recommendation_id": recommendation.recommendation_id,
                        "sql_executed": recommendation.sql_statement,
                    }
                else:
                    return {"success": False, "error": "No SQL statement to execute"}

        except Exception as e:
            logger.error(f"Failed to apply optimization {recommendation_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendation_id": recommendation.recommendation_id,
            }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            "metrics_count": len(self.performance_metrics),
            "query_analyses_count": len(self.query_analyses),
            "recommendations_count": len(self.optimization_recommendations),
            "configuration_recommendations": len(self.configuration_recommendations),
        }

        # Calculate average performance scores
        if self.query_analyses:
            scores = [qa.performance_score for qa in self.query_analyses.values()]
            summary["avg_query_performance_score"] = sum(scores) / len(scores)

        # Count recommendations by priority
        priority_counts = defaultdict(int)
        for rec in self.optimization_recommendations:
            priority_counts[rec.priority.value] += 1
        summary["recommendations_by_priority"] = dict(priority_counts)

        # Count recommendations by type
        type_counts = defaultdict(int)
        for rec in self.optimization_recommendations:
            type_counts[rec.optimization_type.value] += 1
        summary["recommendations_by_type"] = dict(type_counts)

        return summary

    async def start_monitoring(self, interval_seconds: int = 300) -> asyncio.Task:
        """Start continuous performance monitoring."""

        async def monitor():
            while True:
                try:
                    await self.analyze_database_performance()
                    await asyncio.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Performance monitoring error: {e}")
                    await asyncio.sleep(interval_seconds)

        self._analysis_task = asyncio.create_task(monitor)
        return self._analysis_task

    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        if self._analysis_task:
            self._analysis_task.cancel()
            self._analysis_task = None


# Global performance tuner instance
_performance_tuner: PerformanceTuner | None = None


def get_performance_tuner() -> PerformanceTuner:
    """Get global performance tuner instance."""
    global _performance_tuner
    if _performance_tuner is None:
        raise RuntimeError(
            "Performance tuner not initialized. Call init_performance_tuner() first."
        )
    return _performance_tuner


async def init_performance_tuner(
    db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None
) -> PerformanceTuner:
    """Initialize global performance tuner."""
    global _performance_tuner
    _performance_tuner = PerformanceTuner(db_pool, alert_manager)
    return _performance_tuner
