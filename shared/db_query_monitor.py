"""Database query performance monitoring and optimization system.

Provides:
- Query performance tracking
- Slow query detection
- Query optimization recommendations
- Performance analytics
- Automated alerting

Usage:
    from shared.db_query_monitor import QueryMonitor

    monitor = QueryMonitor(db_pool)
    await monitor.track_query("SELECT * FROM users", 150.5)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import asyncpg

from shared.logging_config import get_logger
from shared.alerting import AlertSeverity, get_alert_manager

logger = get_logger("sorce.db_query_monitor")


class QueryStatus(Enum):
    """Query execution status."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class QueryExecution:
    """Individual query execution record."""

    query_hash: str
    query_template: str
    execution_time_ms: float
    status: QueryStatus
    timestamp: float
    rows_affected: Optional[int] = None
    error_message: Optional[str] = None
    connection_id: Optional[str] = None


@dataclass
class QueryStatistics:
    """Query performance statistics."""

    query_hash: str
    query_template: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    p95_execution_time_ms: float
    p99_execution_time_ms: float
    total_rows_affected: int
    error_rate_pct: float
    last_execution: float
    first_execution: float


@dataclass
class QueryOptimization:
    """Query optimization recommendation."""

    query_hash: str
    query_template: str
    issue_type: str
    description: str
    recommendation: str
    impact_estimate: str
    priority: str
    created_at: float = field(default_factory=time.time)


class QueryMonitor:
    """Advanced database query monitoring system."""

    def __init__(self, db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None):
        self.db_pool = db_pool
        self.alert_manager = alert_manager or get_alert_manager()

        # Query tracking
        self.query_executions: Dict[str, deque[QueryExecution]] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.query_templates: Dict[str, str] = {}
        self.active_queries: Dict[str, QueryExecution] = {}

        # Performance thresholds
        self.thresholds = {
            "slow_query_ms": 1000.0,
            "very_slow_query_ms": 5000.0,
            "error_rate_pct": 5.0,
            "frequent_query_count": 100,
            "high_impact_query_ms": 10000.0,
        }

        # Optimization tracking
        self.optimizations: Dict[str, List[QueryOptimization]] = defaultdict(list)
        self.index_suggestions: Dict[str, List[str]] = defaultdict(list)

        # Monitoring state
        self._lock = asyncio.Lock()
        self._monitoring_task: Optional[asyncio.Task] = None

        # Query normalization cache
        self._normalization_cache: Dict[str, str] = {}

    async def track_query(
        self,
        query: str,
        execution_time_ms: float,
        status: QueryStatus = QueryStatus.SUCCESS,
        rows_affected: Optional[int] = None,
        error_message: Optional[str] = None,
        connection_id: Optional[str] = None,
    ) -> None:
        """Track a query execution."""
        # Normalize query for grouping
        query_template = await self._normalize_query(query)
        query_hash = self._hash_query(query_template)

        # Store template
        self.query_templates[query_hash] = query_template

        # Create execution record
        execution = QueryExecution(
            query_hash=query_hash,
            query_template=query_template,
            execution_time_ms=execution_time_ms,
            status=status,
            timestamp=time.time(),
            rows_affected=rows_affected,
            error_message=error_message,
            connection_id=connection_id,
        )

        # Store execution
        async with self._lock:
            self.query_executions[query_hash].append(execution)

        # Check for alerts
        await self._check_query_alerts(execution)

        # Check for optimization opportunities
        await self._analyze_for_optimization(execution)

    async def _normalize_query(self, query: str) -> str:
        """Normalize query by removing parameters and formatting."""
        # Check cache first
        if query in self._normalization_cache:
            return self._normalization_cache[query]

        # Basic normalization
        normalized = query.strip()

        # Remove common parameter patterns
        import re

        # Remove numeric literals
        normalized = re.sub(r"\b\d+\b", "?", normalized)

        # Remove string literals
        normalized = re.sub(r"'[^']*'", "?", normalized)
        normalized = re.sub(r'"[^"]*"', "?", normalized)

        # Remove UUID patterns
        normalized = re.sub(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            "?",
            normalized,
            flags=re.IGNORECASE,
        )

        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = re.sub(r"\s*,\s*", ", ", normalized)
        normalized = re.sub(r"\s*\(\s*", "(", normalized)
        normalized = re.sub(r"\s*\)\s*", ")", normalized)

        # Cache result
        self._normalization_cache[query] = normalized

        return normalized

    def _hash_query(self, query_template: str) -> str:
        """Create hash for query template."""
        return hashlib.md5(query_template.encode(), usedforsecurity=False).hexdigest()[
            :16
        ]

    async def _check_query_alerts(self, execution: QueryExecution) -> None:
        """Check if query execution should trigger alerts."""
        # Slow query alert
        if execution.execution_time_ms > self.thresholds["very_slow_query_ms"]:
            await self.alert_manager.trigger_alert(
                name="very_slow_query",
                severity=AlertSeverity.ERROR,
                message=f"Very slow query detected: {execution.query_template[:100]}...",
                metric_value=execution.execution_time_ms,
                threshold=self.thresholds["very_slow_query_ms"],
            )
        elif execution.execution_time_ms > self.thresholds["slow_query_ms"]:
            await self.alert_manager.trigger_alert(
                name="slow_query",
                severity=AlertSeverity.WARNING,
                message=f"Slow query detected: {execution.query_template[:100]}...",
                metric_value=execution.execution_time_ms,
                threshold=self.thresholds["slow_query_ms"],
            )

        # Query error alert
        if execution.status == QueryStatus.ERROR:
            await self.alert_manager.trigger_alert(
                name="query_error",
                severity=AlertSeverity.ERROR,
                message=f"Query error: {execution.error_message}",
                context={"query_template": execution.query_template},
            )

        # High impact query alert
        if execution.execution_time_ms > self.thresholds["high_impact_query_ms"]:
            await self.alert_manager.trigger_alert(
                name="high_impact_query",
                severity=AlertSeverity.CRITICAL,
                message=f"High impact query detected: {execution.query_template[:100]}...",
                metric_value=execution.execution_time_ms,
                threshold=self.thresholds["high_impact_query_ms"],
            )

    async def _analyze_for_optimization(self, execution: QueryExecution) -> None:
        """Analyze query for optimization opportunities."""
        if execution.status != QueryStatus.SUCCESS:
            return

        # Check for missing indexes
        await self._check_missing_indexes(execution)

        # Check for inefficient patterns
        await self._check_inefficient_patterns(execution)

        # Check for table scan opportunities
        await self._check_table_scans(execution)

    async def _check_missing_indexes(self, execution: QueryExecution) -> None:
        """Check if query could benefit from missing indexes."""
        try:
            async with self.db_pool.acquire() as conn:
                # Get query plan
                plan = await conn.fetchval(
                    f"EXPLAIN (FORMAT JSON) {execution.query_template}"
                )

                if isinstance(plan, str):
                    plan = json.loads(plan)  # Parse JSON string

                # Analyze plan for missing indexes
                if isinstance(plan, list) and plan:
                    plan_node = plan[0].get("Plan", {})
                    await self._analyze_plan_for_indexes(
                        execution.query_hash, plan_node
                    )

        except Exception as e:
            logger.debug(f"Failed to analyze query plan: {e}")

    async def _analyze_plan_for_indexes(
        self, query_hash: str, plan_node: Dict[str, Any]
    ) -> None:
        """Analyze query plan node for index opportunities."""
        # Check for sequential scans
        if plan_node.get("Node Type") == "Seq Scan":
            table_name = plan_node.get("Relation Name")
            if table_name:
                suggestion = f"Consider adding index on table {table_name} for frequently filtered columns"
                if suggestion not in self.index_suggestions[query_hash]:
                    self.index_suggestions[query_hash].append(suggestion)

        # Check for hash joins without indexes
        if plan_node.get("Node Type") == "Hash Join":
            # This could potentially benefit from better indexes
            pass

        # Recursively analyze child nodes
        for child in plan_node.get("Plans", []):
            await self._analyze_plan_for_indexes(query_hash, child)

    async def _check_inefficient_patterns(self, execution: QueryExecution) -> None:
        """Check for inefficient query patterns."""
        query = execution.query_template.lower()

        # Check for SELECT *
        if "select *" in query:
            await self._add_optimization(
                execution.query_hash,
                execution.query_template,
                "select_star",
                "Using SELECT * can be inefficient",
                "Specify only the columns you need instead of SELECT *",
                "Medium",
            )

        # Check for missing WHERE clauses on large tables
        if (
            "select" in query
            and "where" not in query
            and execution.rows_affected
            and execution.rows_affected > 1000
        ):
            await self._add_optimization(
                execution.query_hash,
                execution.query_template,
                "missing_where",
                "Query without WHERE clause returning many rows",
                "Add WHERE clause to filter results or use LIMIT",
                "High",
            )

        # Check for ORDER BY without LIMIT
        if "order by" in query and "limit" not in query:
            await self._add_optimization(
                execution.query_hash,
                execution.query_template,
                "order_without_limit",
                "ORDER BY without LIMIT can be expensive",
                "Add LIMIT clause or ensure proper indexing on ORDER BY columns",
                "Medium",
            )

    async def _check_table_scans(self, execution: QueryExecution) -> None:
        """Check for expensive table scans."""
        if execution.execution_time_ms > self.thresholds["slow_query_ms"]:
            await self._add_optimization(
                execution.query_hash,
                execution.query_template,
                "expensive_scan",
                "Slow query may indicate expensive table scan",
                "Review query execution plan and consider adding indexes",
                "High",
            )

    async def _add_optimization(
        self,
        query_hash: str,
        query_template: str,
        issue_type: str,
        description: str,
        recommendation: str,
        priority: str,
    ) -> None:
        """Add optimization recommendation."""
        optimization = QueryOptimization(
            query_hash=query_hash,
            query_template=query_template,
            issue_type=issue_type,
            description=description,
            recommendation=recommendation,
            impact_estimate="Performance improvement varies",
            priority=priority,
        )

        # Avoid duplicates
        existing = self.optimizations[query_hash]
        for existing_opt in existing:
            if (
                existing_opt.issue_type == issue_type
                and existing_opt.description == description
            ):
                return

        self.optimizations[query_hash].append(optimization)

    def get_query_statistics(self, query_hash: str) -> Optional[QueryStatistics]:
        """Get statistics for a specific query."""
        executions = list(self.query_executions.get(query_hash, []))
        if not executions:
            return None

        # Calculate statistics
        execution_times = [
            e.execution_time_ms for e in executions if e.status == QueryStatus.SUCCESS
        ]
        successful = [e for e in executions if e.status == QueryStatus.SUCCESS]
        failed = [e for e in executions if e.status == QueryStatus.ERROR]

        if not execution_times:
            return None

        execution_times.sort()
        total_executions = len(executions)

        return QueryStatistics(
            query_hash=query_hash,
            query_template=self.query_templates.get(query_hash, ""),
            total_executions=total_executions,
            successful_executions=len(successful),
            failed_executions=len(failed),
            avg_execution_time_ms=sum(execution_times) / len(execution_times),
            min_execution_time_ms=min(execution_times),
            max_execution_time_ms=max(execution_times),
            p95_execution_time_ms=execution_times[int(0.95 * len(execution_times))],
            p99_execution_time_ms=execution_times[int(0.99 * len(execution_times))],
            total_rows_affected=sum(e.rows_affected or 0 for e in successful),
            error_rate_pct=len(failed) / total_executions * 100,
            last_execution=max(e.timestamp for e in executions),
            first_execution=min(e.timestamp for e in executions),
        )

    def get_slow_queries(self, limit: int = 50) -> List[Tuple[str, QueryStatistics]]:
        """Get slowest queries by average execution time."""
        stats = []

        for query_hash in self.query_executions:
            stat = self.get_query_statistics(query_hash)
            if stat and stat.avg_execution_time_ms > self.thresholds["slow_query_ms"]:
                stats.append((query_hash, stat))

        # Sort by average execution time
        stats.sort(key=lambda x: x[1].avg_execution_time_ms, reverse=True)
        return stats[:limit]

    def get_frequent_queries(
        self, limit: int = 50
    ) -> List[Tuple[str, QueryStatistics]]:
        """Get most frequently executed queries."""
        stats = []

        for query_hash in self.query_executions:
            stat = self.get_query_statistics(query_hash)
            if (
                stat
                and stat.total_executions >= self.thresholds["frequent_query_count"]
            ):
                stats.append((query_hash, stat))

        # Sort by execution count
        stats.sort(key=lambda x: x[1].total_executions, reverse=True)
        return stats[:limit]

    def get_error_prone_queries(
        self, limit: int = 50
    ) -> List[Tuple[str, QueryStatistics]]:
        """Get queries with highest error rates."""
        stats = []

        for query_hash in self.query_executions:
            stat = self.get_query_statistics(query_hash)
            if stat and stat.error_rate_pct > self.thresholds["error_rate_pct"]:
                stats.append((query_hash, stat))

        # Sort by error rate
        stats.sort(key=lambda x: x[1].error_rate_pct, reverse=True)
        return stats[:limit]

    def get_query_optimizations(self, query_hash: str) -> List[QueryOptimization]:
        """Get optimization recommendations for a query."""
        return self.optimizations.get(query_hash, [])

    def get_all_optimizations(
        self, priority: Optional[str] = None
    ) -> List[QueryOptimization]:
        """Get all optimization recommendations."""
        all_opts = []

        for opts in self.optimizations.values():
            all_opts.extend(opts)

        if priority:
            all_opts = [opt for opt in all_opts if opt.priority == priority]

        # Sort by priority and creation time
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        all_opts.sort(key=lambda x: (priority_order.get(x.priority, 3), -x.created_at))

        return all_opts

    def get_index_suggestions(self, query_hash: str) -> List[str]:
        """Get index suggestions for a query."""
        return self.index_suggestions.get(query_hash, [])

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        total_executions = sum(
            len(executions) for executions in self.query_executions.values()
        )
        total_errors = sum(
            sum(1 for e in executions if e.status == QueryStatus.ERROR)
            for executions in self.query_executions.values()
        )

        # Calculate average execution time
        all_times = []
        for executions in self.query_executions.values():
            all_times.extend(
                e.execution_time_ms
                for e in executions
                if e.status == QueryStatus.SUCCESS
            )

        avg_time = sum(all_times) / len(all_times) if all_times else 0

        return {
            "total_queries_tracked": len(self.query_executions),
            "total_executions": total_executions,
            "total_errors": total_errors,
            "error_rate_pct": (total_errors / total_executions * 100)
            if total_executions > 0
            else 0,
            "avg_execution_time_ms": avg_time,
            "optimization_suggestions": len(self.get_all_optimizations()),
            "index_suggestions": sum(
                len(suggestions) for suggestions in self.index_suggestions.values()
            ),
        }

    async def start_monitoring(self, interval_seconds: int = 300) -> asyncio.Task:
        """Start continuous query monitoring."""

        async def monitor():
            while True:
                try:
                    # Clean up old data
                    await self._cleanup_old_data()

                    # Generate periodic reports
                    await self._generate_performance_report()

                    await asyncio.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Query monitoring error: {e}")
                    await asyncio.sleep(interval_seconds)

        self._monitoring_task = asyncio.create_task(monitor)
        return self._monitoring_task

    async def _cleanup_old_data(self) -> None:
        """Clean up old query execution data."""
        cutoff_time = time.time() - (24 * 60 * 60)  # Keep last 24 hours

        async with self._lock:
            for query_hash, executions in list(self.query_executions.items()):
                # Filter old executions
                filtered = deque(
                    (e for e in executions if e.timestamp >= cutoff_time), maxlen=1000
                )

                if filtered:
                    self.query_executions[query_hash] = filtered
                else:
                    # Remove empty query tracking
                    del self.query_executions[query_hash]
                    self.query_templates.pop(query_hash, None)
                    self.optimizations.pop(query_hash, None)
                    self.index_suggestions.pop(query_hash, None)

    async def _generate_performance_report(self) -> None:
        """Generate periodic performance report."""
        summary = self.get_performance_summary()
        logger.info(f"Query performance summary: {summary}")

        # Alert on high error rates
        if summary["error_rate_pct"] > 10:
            await self.alert_manager.trigger_alert(
                name="high_error_rate",
                severity=AlertSeverity.ERROR,
                message=f"High query error rate: {summary['error_rate_pct']:.1f}%",
                metric_value=summary["error_rate_pct"],
                threshold=10.0,
            )

    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None


# Global query monitor instance
_query_monitor: QueryMonitor | None = None


def get_query_monitor() -> QueryMonitor:
    """Get global query monitor instance."""
    global _query_monitor
    if _query_monitor is None:
        raise RuntimeError(
            "Query monitor not initialized. Call init_query_monitor() first."
        )
    return _query_monitor


async def init_query_monitor(
    db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None
) -> QueryMonitor:
    """Initialize global query monitor."""
    global _query_monitor
    _query_monitor = QueryMonitor(db_pool, alert_manager)
    return _query_monitor
