"""Database health checking and monitoring system.

Provides:
- Connection health checks
- Query performance monitoring
- Database metrics collection
- Alert generation for issues
- Automated recovery procedures

Usage:
    from shared.db_health_checker import DatabaseHealthChecker

    checker = DatabaseHealthChecker(db_pool)
    health = await checker.check_health()
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

logger = get_logger("sorce.db_health")


class HealthStatus(Enum):
    """Database health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Individual health check result."""

    name: str
    status: HealthStatus
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class DatabaseHealth:
    """Comprehensive database health status."""

    overall_status: HealthStatus
    checks: List[HealthCheck]
    connection_pool_stats: Dict[str, Any]
    database_metrics: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    issues: List[str] = field(default_factory=list)


@dataclass
class QueryMetrics:
    """Query performance metrics."""

    query: str
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    total_executions: int
    error_rate: float
    timestamp: float = field(default_factory=time.time)


class DatabaseHealthChecker:
    """Advanced database health monitoring system."""

    def __init__(self, db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None):
        self.db_pool = db_pool
        self.alert_manager = alert_manager or get_alert_manager()
        self.metrics_history: deque[DatabaseHealth] = deque(maxlen=1000)
        self.query_metrics: Dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_checks: Dict[str, float] = {}
        self._lock = asyncio.Lock()

        # Health check thresholds
        self.thresholds = {
            "connection_time_ms": 100.0,
            "query_time_ms": 1000.0,
            "pool_usage_pct": 80.0,
            "error_rate_pct": 5.0,
            "replication_lag_s": 30.0,
            "disk_usage_pct": 85.0,
            "memory_usage_pct": 85.0,
            "cpu_usage_pct": 80.0,
        }

    async def check_health(self) -> DatabaseHealth:
        """Perform comprehensive database health check."""
        time.time()
        checks = []
        issues = []

        try:
            # Connection health
            connection_check = await self._check_connection_health()
            checks.append(connection_check)

            # Connection pool health
            pool_check = await self._check_pool_health()
            checks.append(pool_check)

            # Database accessibility
            accessibility_check = await self._check_database_accessibility()
            checks.append(accessibility_check)

            # Query performance
            query_check = await self._check_query_performance()
            checks.append(query_check)

            # Replication status (if applicable)
            replication_check = await self._check_replication_status()
            checks.append(replication_check)

            # Database size and storage
            storage_check = await self._check_storage_health()
            checks.append(storage_check)

            # Lock monitoring
            lock_check = await self._check_lock_health()
            checks.append(lock_check)

            # Transaction health
            transaction_check = await self._check_transaction_health()
            checks.append(transaction_check)

            # Determine overall status
            overall_status = self._determine_overall_status(checks)

            # Collect issues
            issues = [
                check.message
                for check in checks
                if check.status != HealthStatus.HEALTHY
            ]

            # Get connection pool stats
            pool_stats = await self._get_pool_stats()

            # Get database metrics
            db_metrics = await self._get_database_metrics()

            # Create health result
            health = DatabaseHealth(
                overall_status=overall_status,
                checks=checks,
                connection_pool_stats=pool_stats,
                database_metrics=db_metrics,
                issues=issues,
                timestamp=time.time(),
            )

            # Store in history
            async with self._lock:
                self.metrics_history.append(health)

            # Trigger alerts if needed
            await self._trigger_alerts(health)

            return health

        except Exception as e:
            logger.error(f"Health check failed: {e}")

            # Return critical status on error
            return DatabaseHealth(
                overall_status=HealthStatus.CRITICAL,
                checks=[
                    HealthCheck(
                        name="health_check_error",
                        status=HealthStatus.CRITICAL,
                        message=f"Health check failed: {str(e)}",
                    )
                ],
                connection_pool_stats={},
                database_metrics={},
                issues=[f"Health check failed: {str(e)}"],
                timestamp=time.time(),
            )

    async def _check_connection_health(self) -> HealthCheck:
        """Check database connection health."""
        start_time = time.time()

        try:
            async with self.db_pool.acquire() as conn:
                # Test basic connectivity
                await conn.fetchval("SELECT 1")

                # Test connection time
                conn_start = time.time()
                await conn.fetchval("SELECT version()")
                conn_time = (time.time() - conn_start) * 1000

                duration_ms = (time.time() - start_time) * 1000

                if conn_time > self.thresholds["connection_time_ms"]:
                    return HealthCheck(
                        name="connection_health",
                        status=HealthStatus.DEGRADED,
                        message=f"Connection time {conn_time:.1f}ms exceeds threshold {self.thresholds['connection_time_ms']}ms",
                        value=conn_time,
                        threshold=self.thresholds["connection_time_ms"],
                        duration_ms=duration_ms,
                    )

                return HealthCheck(
                    name="connection_health",
                    status=HealthStatus.HEALTHY,
                    message="Database connection healthy",
                    value=conn_time,
                    threshold=self.thresholds["connection_time_ms"],
                    duration_ms=duration_ms,
                )

        except Exception as e:
            return HealthCheck(
                name="connection_health",
                status=HealthStatus.CRITICAL,
                message=f"Connection failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _check_pool_health(self) -> HealthCheck:
        """Check connection pool health."""
        start_time = time.time()

        try:
            pool_size = self.db_pool.get_size()
            pool_free = self.db_pool.get_idle_size()
            pool_usage = (pool_size - pool_free) / pool_size * 100

            duration_ms = (time.time() - start_time) * 1000

            if pool_usage > self.thresholds["pool_usage_pct"]:
                return HealthCheck(
                    name="pool_health",
                    status=HealthStatus.DEGRADED,
                    message=f"Pool usage {pool_usage:.1f}% exceeds threshold {self.thresholds['pool_usage_pct']}%",
                    value=pool_usage,
                    threshold=self.thresholds["pool_usage_pct"],
                    duration_ms=duration_ms,
                )

            return HealthCheck(
                name="pool_health",
                status=HealthStatus.HEALTHY,
                message=f"Pool usage {pool_usage:.1f}%",
                value=pool_usage,
                threshold=self.thresholds["pool_usage_pct"],
                duration_ms=duration_ms,
            )

        except Exception as e:
            return HealthCheck(
                name="pool_health",
                status=HealthStatus.UNHEALTHY,
                message=f"Pool check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _check_database_accessibility(self) -> HealthCheck:
        """Check database accessibility and basic operations."""
        start_time = time.time()

        try:
            async with self.db_pool.acquire() as conn:
                # Test read operations
                await conn.fetchval("SELECT COUNT(*) FROM pg_stat_activity")

                # Test write operations (temporary table)
                await conn.execute("CREATE TEMP TABLE health_check_test (id INTEGER)")
                await conn.execute("DROP TABLE health_check_test")

                duration_ms = (time.time() - start_time) * 1000

                return HealthCheck(
                    name="database_accessibility",
                    status=HealthStatus.HEALTHY,
                    message="Database read/write operations healthy",
                    duration_ms=duration_ms,
                )

        except Exception as e:
            return HealthCheck(
                name="database_accessibility",
                status=HealthStatus.UNHEALTHY,
                message=f"Database accessibility check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _check_query_performance(self) -> HealthCheck:
        """Check query performance metrics."""
        start_time = time.time()

        try:
            async with self.db_pool.acquire() as conn:
                # Get slow queries
                slow_queries = await conn.fetch(
                    """
                    SELECT query, mean_exec_time, calls, total_exec_time
                    FROM pg_stat_statements
                    WHERE mean_exec_time > $1
                    ORDER BY mean_exec_time DESC
                    LIMIT 5
                """,
                    self.thresholds["query_time_ms"],
                )

                duration_ms = (time.time() - start_time) * 1000

                if slow_queries:
                    worst_query = slow_queries[0]
                    return HealthCheck(
                        name="query_performance",
                        status=HealthStatus.DEGRADED,
                        message=f"Found {len(slow_queries)} slow queries, worst: {worst_query['mean_exec_time']:.1f}ms",
                        value=worst_query["mean_exec_time"],
                        threshold=self.thresholds["query_time_ms"],
                        duration_ms=duration_ms,
                    )

                return HealthCheck(
                    name="query_performance",
                    status=HealthStatus.HEALTHY,
                    message="No slow queries detected",
                    duration_ms=duration_ms,
                )

        except Exception:
            # pg_stat_statements might not be available
            return HealthCheck(
                name="query_performance",
                status=HealthStatus.HEALTHY,
                message="Query performance monitoring not available",
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _check_replication_status(self) -> HealthCheck:
        """Check database replication status."""
        start_time = time.time()

        try:
            async with self.db_pool.acquire() as conn:
                # Check if replication is configured
                replication_info = await conn.fetchrow("""
                    SELECT
                        pg_is_in_recovery() as in_recovery,
                        pg_last_wal_receive_lsn() as last_receive_lsn,
                        pg_last_wal_replay_lsn() as last_replay_lsn,
                        pg_last_xact_replay_timestamp() as last_replay_timestamp
                """)

                duration_ms = (time.time() - start_time) * 1000

                if replication_info["in_recovery"]:
                    # This is a replica, check lag
                    if replication_info["last_replay_timestamp"]:
                        lag_time = (
                            time.time()
                            - replication_info["last_replay_timestamp"].timestamp()
                        )

                        if lag_time > self.thresholds["replication_lag_s"]:
                            return HealthCheck(
                                name="replication_status",
                                status=HealthStatus.DEGRADED,
                                message=f"Replication lag {lag_time:.1f}s exceeds threshold {self.thresholds['replication_lag_s']}s",
                                value=lag_time,
                                threshold=self.thresholds["replication_lag_s"],
                                duration_ms=duration_ms,
                            )

                    return HealthCheck(
                        name="replication_status",
                        status=HealthStatus.HEALTHY,
                        message="Replica server healthy",
                        value=lag_time if "lag_time" in locals() else 0,
                        threshold=self.thresholds["replication_lag_s"],
                        duration_ms=duration_ms,
                    )
                else:
                    # This is primary server
                    return HealthCheck(
                        name="replication_status",
                        status=HealthStatus.HEALTHY,
                        message="Primary server healthy",
                        duration_ms=duration_ms,
                    )

        except Exception:
            return HealthCheck(
                name="replication_status",
                status=HealthStatus.HEALTHY,
                message="Replication monitoring not available",
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _check_storage_health(self) -> HealthCheck:
        """Check database storage health."""
        start_time = time.time()

        try:
            async with self.db_pool.acquire() as conn:
                # Get database size
                db_size = await conn.fetchval("""
                    SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb
                """)

                # Get table sizes (top 10 largest)
                large_tables = await conn.fetch("""
                    SELECT
                        schemaname || '.' || tablename as table_name,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) / 1024 / 1024 as size_mb
                    FROM pg_tables
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """)

                duration_ms = (time.time() - start_time) * 1000

                return HealthCheck(
                    name="storage_health",
                    status=HealthStatus.HEALTHY,
                    message=f"Database size {db_size:.1f}MB, largest table: {large_tables[0]['table_name'] if large_tables else 'N/A'}",
                    value=db_size,
                    duration_ms=duration_ms,
                )

        except Exception as e:
            return HealthCheck(
                name="storage_health",
                status=HealthStatus.UNHEALTHY,
                message=f"Storage check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _check_lock_health(self) -> HealthCheck:
        """Check for problematic locks."""
        start_time = time.time()

        try:
            async with self.db_pool.acquire() as conn:
                # Check for long-running locks
                long_locks = await conn.fetch("""
                    SELECT
                        pid,
                        age(clock_timestamp(), xact_start) as age,
                        query,
                        mode
                    FROM pg_locks l
                    JOIN pg_stat_activity a ON l.pid = a.pid
                    WHERE NOT granted
                    AND age(clock_timestamp(), xact_start) > interval '5 minutes'
                    ORDER BY age DESC
                """)

                duration_ms = (time.time() - start_time) * 1000

                if long_locks:
                    return HealthCheck(
                        name="lock_health",
                        status=HealthStatus.DEGRADED,
                        message=f"Found {len(long_locks)} long-running locks",
                        duration_ms=duration_ms,
                    )

                return HealthCheck(
                    name="lock_health",
                    status=HealthStatus.HEALTHY,
                    message="No problematic locks detected",
                    duration_ms=duration_ms,
                )

        except Exception:
            return HealthCheck(
                name="lock_health",
                status=HealthStatus.HEALTHY,
                message="Lock monitoring not available",
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _check_transaction_health(self) -> HealthCheck:
        """Check transaction health."""
        start_time = time.time()

        try:
            async with self.db_pool.acquire() as conn:
                # Check for long-running transactions
                long_transactions = await conn.fetch("""
                    SELECT
                        pid,
                        age(clock_timestamp(), xact_start) as age,
                        query
                    FROM pg_stat_activity
                    WHERE xact_start IS NOT NULL
                    AND age(clock_timestamp(), xact_start) > interval '10 minutes'
                    AND state = 'active'
                    ORDER BY age DESC
                """)

                duration_ms = (time.time() - start_time) * 1000

                if long_transactions:
                    return HealthCheck(
                        name="transaction_health",
                        status=HealthStatus.DEGRADED,
                        message=f"Found {len(long_transactions)} long-running transactions",
                        duration_ms=duration_ms,
                    )

                return HealthCheck(
                    name="transaction_health",
                    status=HealthStatus.HEALTHY,
                    message="No long-running transactions detected",
                    duration_ms=duration_ms,
                )

        except Exception:
            return HealthCheck(
                name="transaction_health",
                status=HealthStatus.HEALTHY,
                message="Transaction monitoring not available",
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall health status from individual checks."""
        if any(check.status == HealthStatus.CRITICAL for check in checks):
            return HealthStatus.CRITICAL

        if any(check.status == HealthStatus.UNHEALTHY for check in checks):
            return HealthStatus.UNHEALTHY

        if any(check.status == HealthStatus.DEGRADED for check in checks):
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    async def _get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        try:
            return {
                "size": self.db_pool.get_size(),
                "idle_size": self.db_pool.get_idle_size(),
                "active_size": self.db_pool.get_size() - self.db_pool.get_idle_size(),
                "max_size": getattr(self.db_pool, "_maxsize", "unknown"),
                "min_size": getattr(self.db_pool, "_minsize", "unknown"),
            }
        except Exception as e:
            logger.error(f"Failed to get pool stats: {e}")
            return {"error": str(e)}

    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        try:
            async with self.db_pool.acquire() as conn:
                # Get basic database metrics
                metrics = await conn.fetchrow("""
                    SELECT
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)

                return {
                    "total_connections": metrics["total_connections"],
                    "active_connections": metrics["active_connections"],
                    "idle_connections": metrics["idle_connections"],
                }
        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {"error": str(e)}

    async def _trigger_alerts(self, health: DatabaseHealth) -> None:
        """Trigger alerts based on health check results."""
        for check in health.checks:
            if check.status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
                await self.alert_manager.trigger_alert(
                    name=f"db_health_{check.name}",
                    severity=AlertSeverity.CRITICAL
                    if check.status == HealthStatus.CRITICAL
                    else AlertSeverity.ERROR,
                    message=f"Database health issue: {check.message}",
                    metric_value=check.value,
                    threshold=check.threshold,
                )

    async def record_query_metrics(
        self, query: str, duration_ms: float, error: bool = False
    ) -> None:
        """Record query performance metrics."""
        query_hash = hash(query) % 10000  # Simple hash for grouping

        # Record duration
        self.query_metrics[query_hash].append(duration_ms)

        # Record error
        if error:
            self.error_counts[query_hash] += 1

    def get_query_metrics(self, query_hash: str) -> Optional[QueryMetrics]:
        """Get metrics for a specific query."""
        durations = list(self.query_metrics.get(query_hash, []))
        if not durations:
            return None

        durations.sort()
        total_executions = len(durations)
        error_count = self.error_counts.get(query_hash, 0)

        return QueryMetrics(
            query=f"query_{query_hash}",
            avg_duration_ms=sum(durations) / total_executions,
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            p95_duration_ms=durations[int(0.95 * total_executions)],
            p99_duration_ms=durations[int(0.99 * total_executions)],
            total_executions=total_executions,
            error_rate=error_count / total_executions * 100,
        )

    def get_health_trend(self, minutes: int = 60) -> List[DatabaseHealth]:
        """Get health trend over time."""
        cutoff_time = time.time() - (minutes * 60)

        return [
            health for health in self.metrics_history if health.timestamp >= cutoff_time
        ]

    async def start_monitoring(self, interval_seconds: int = 60) -> asyncio.Task:
        """Start continuous health monitoring."""

        async def monitor():
            while True:
                try:
                    await self.check_health()
                    await asyncio.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(interval_seconds)

        return asyncio.create_task(monitor())


# Global health checker instance
_health_checker: DatabaseHealthChecker | None = None


def get_db_health_checker() -> DatabaseHealthChecker:
    """Get global database health checker instance."""
    global _health_checker
    if _health_checker is None:
        raise RuntimeError(
            "Database health checker not initialized. Call init_db_health_checker() first."
        )
    return _health_checker


async def init_db_health_checker(
    db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None
) -> DatabaseHealthChecker:
    """Initialize global database health checker."""
    global _health_checker
    _health_checker = DatabaseHealthChecker(db_pool, alert_manager)
    return _health_checker
