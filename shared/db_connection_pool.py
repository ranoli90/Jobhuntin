"""Advanced database connection pooling and optimization system.

Provides:
- Intelligent connection pooling
- Pool size optimization
- Connection health monitoring
- Load balancing across pools
- Performance metrics and analytics

Usage:
    from shared.db_connection_pool import ConnectionPoolManager

    pool_manager = ConnectionPoolManager()
    await pool_manager.initialize_pools()
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import asyncpg

from shared.alerting import get_alert_manager
from shared.logging_config import get_logger

logger = get_logger("sorce.db_pool")


class PoolType(Enum):
    """Database pool types."""

    PRIMARY = "primary"
    REPLICA = "replica"
    ANALYTICS = "analytics"
    CACHE = "cache"


class PoolStatus(Enum):
    """Pool status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


@dataclass
class PoolConfiguration:
    """Connection pool configuration."""

    pool_type: PoolType
    min_size: int
    max_size: int
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0
    timeout: float = 30.0
    command_timeout: float = 10.0
    server_settings: Dict[str, str] = field(default_factory=dict)
    enable_health_checks: bool = True
    health_check_interval: float = 60.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class PoolMetrics:
    """Connection pool performance metrics."""

    pool_type: PoolType
    total_connections: int
    active_connections: int
    idle_connections: int
    waiting_requests: int
    avg_wait_time_ms: float
    max_wait_time_ms: float
    total_queries: int
    avg_query_time_ms: float
    failed_connections: int
    connection_errors: int
    health_check_failures: int
    last_health_check: float
    uptime_percentage: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConnectionStats:
    """Individual connection statistics."""

    connection_id: str
    created_at: float
    last_used: float
    queries_executed: int
    total_time_ms: float
    errors: int
    is_active: bool
    pool_type: PoolType


class ConnectionPoolManager:
    """Advanced database connection pool management system."""

    def __init__(self, alert_manager: Optional[Any] = None):
        self.alert_manager = alert_manager or get_alert_manager()

        # Pool storage
        self.pools: Dict[PoolType, asyncpg.Pool] = {}
        self.pool_configs: Dict[PoolType, PoolConfiguration] = {}
        self.pool_metrics: Dict[PoolType, PoolMetrics] = {}
        self.connection_stats: Dict[str, ConnectionStats] = {}

        # Pool optimization
        self.optimization_enabled = True
        self.auto_scaling_enabled = True
        self.load_balancing_enabled = True

        # Monitoring
        self.metrics_history: Dict[PoolType, deque[PoolMetrics]] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.health_check_task: Optional[asyncio.Task] = None
        self.optimization_task: Optional[asyncio.Task] = None

        # Load balancing
        self.round_robin_counter: Dict[PoolType, int] = defaultdict(int)
        self.pool_weights: Dict[PoolType, float] = {}

        # Performance thresholds
        self.thresholds = {
            "max_wait_time_ms": 1000.0,
            "avg_wait_time_ms": 100.0,
            "connection_error_rate": 0.05,
            "health_check_failure_rate": 0.1,
            "pool_utilization_pct": 80.0,
            "query_time_ms": 500.0,
        }

        self._lock = asyncio.Lock()

    async def initialize_pools(
        self, database_configs: Dict[PoolType, Dict[str, Any]]
    ) -> None:
        """Initialize database connection pools."""
        for pool_type, config in database_configs.items():
            # Create pool configuration
            pool_config = PoolConfiguration(
                pool_type=pool_type,
                min_size=config.get("min_size", 5),
                max_size=config.get("max_size", 20),
                max_queries=config.get("max_queries", 50000),
                max_inactive_connection_lifetime=config.get(
                    "max_inactive_connection_lifetime", 300.0
                ),
                timeout=config.get("timeout", 30.0),
                command_timeout=config.get("command_timeout", 10.0),
                server_settings=config.get("server_settings", {}),
                enable_health_checks=config.get("enable_health_checks", True),
                health_check_interval=config.get("health_check_interval", 60.0),
                retry_attempts=config.get("retry_attempts", 3),
                retry_delay=config.get("retry_delay", 1.0),
            )

            self.pool_configs[pool_type] = pool_config

            # Initialize pool
            await self._create_pool(pool_type, config)

            # Initialize metrics
            self.pool_metrics[pool_type] = PoolMetrics(
                pool_type=pool_type,
                total_connections=0,
                active_connections=0,
                idle_connections=0,
                waiting_requests=0,
                avg_wait_time_ms=0.0,
                max_wait_time_ms=0.0,
                total_queries=0,
                avg_query_time_ms=0.0,
                failed_connections=0,
                connection_errors=0,
                health_check_failures=0,
                last_health_check=time.time(),
                uptime_percentage=100.0,
            )

            # Set default pool weight
            self.pool_weights[pool_type] = 1.0

        # Start monitoring tasks
        await self._start_monitoring()

        logger.info(f"Initialized {len(self.pools)} database connection pools")

    async def _create_pool(self, pool_type: PoolType, config: Dict[str, Any]) -> None:
        """Create a single connection pool."""
        try:
            pool = await asyncpg.create_pool(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                database=config["database"],
                min_size=self.pool_configs[pool_type].min_size,
                max_size=self.pool_configs[pool_type].max_size,
                max_queries=self.pool_configs[pool_type].max_queries,
                max_inactive_connection_lifetime=self.pool_configs[
                    pool_type
                ].max_inactive_connection_lifetime,
                timeout=self.pool_configs[pool_type].timeout,
                command_timeout=self.pool_configs[pool_type].command_timeout,
                server_settings=self.pool_configs[pool_type].server_settings,
                setup=self._setup_connection,
                init=self._init_connection,
            )

            self.pools[pool_type] = pool
            logger.info(f"Created {pool_type.value} connection pool")

        except Exception as e:
            logger.error(f"Failed to create {pool_type.value} pool: {e}")
            raise

    async def _setup_connection(self, conn: asyncpg.Connection) -> None:
        """Setup connection with custom configuration."""
        # Set connection parameters
        await conn.set_builtin_type_codec(
            "json", codec_name="jsonb", schema="pg_catalog"
        )

        # Set application name
        await conn.execute("SET application_name = 'jobhuntin_pool'")

        # Set timezone
        await conn.execute("SET timezone = 'UTC'")

    async def _init_connection(self, conn: asyncpg.Connection) -> None:
        """Initialize connection with health check."""
        try:
            # Basic health check
            await conn.fetchval("SELECT 1")

            # Record connection stats
            connection_id = f"{id(conn)}_{int(time.time())}"
            self.connection_stats[connection_id] = ConnectionStats(
                connection_id=connection_id,
                created_at=time.time(),
                last_used=time.time(),
                queries_executed=0,
                total_time_ms=0.0,
                errors=0,
                is_active=True,
                pool_type=self._get_connection_pool_type(conn),
            )

        except Exception as e:
            logger.error(f"Connection initialization failed: {e}")
            raise

    def _get_connection_pool_type(self, conn: asyncpg.Connection) -> PoolType:
        """Determine pool type from connection."""
        # This would need to be implemented based on connection attributes
        # For now, return primary as default
        return PoolType.PRIMARY

    async def get_connection(
        self,
        pool_type: Optional[PoolType] = None,
        read_only: bool = False,
        preferred_pools: Optional[List[PoolType]] = None,
    ) -> asyncpg.Connection:
        """Get database connection with intelligent routing."""
        start_time = time.time()

        try:
            # Determine target pool
            target_pool = await self._select_target_pool(
                pool_type, read_only, preferred_pools
            )

            if target_pool is None or target_pool not in self.pools:
                raise RuntimeError(
                    f"No available pool for request: pool_type={pool_type}, read_only={read_only}"
                )

            # Get connection from pool
            conn = await self.pools[target_pool].acquire()

            # Update metrics
            wait_time_ms = (time.time() - start_time) * 1000
            await self._update_pool_metrics(target_pool, wait_time_ms, "acquire")

            # Track connection usage
            await self._track_connection_usage(conn, target_pool)

            return conn

        except Exception as e:
            # Record failed acquisition
            wait_time_ms = (time.time() - start_time) * 1000
            if pool_type:
                await self._update_pool_metrics(
                    pool_type, wait_time_ms, "acquire_error"
                )

            logger.error(f"Failed to acquire connection: {e}")
            raise

    async def _select_target_pool(
        self,
        pool_type: Optional[PoolType],
        read_only: bool,
        preferred_pools: Optional[List[PoolType]],
    ) -> Optional[PoolType]:
        """Select optimal target pool based on request characteristics."""
        available_pools = list(self.pools.keys())

        # Filter by preferred pools if specified
        if preferred_pools:
            available_pools = [p for p in available_pools if p in preferred_pools]

        # Filter by read-only requirements
        if read_only:
            read_only_pools = [PoolType.REPLICA, PoolType.ANALYTICS]
            available_pools = [p for p in available_pools if p in read_only_pools]

        # Use specific pool type if requested
        if pool_type and pool_type in available_pools:
            return pool_type

        # Load balancing if enabled
        if self.load_balancing_enabled and len(available_pools) > 1:
            return await self._select_pool_by_load_balancing(available_pools)

        # Return first available pool
        return available_pools[0] if available_pools else None

    async def _select_pool_by_load_balancing(
        self, available_pools: List[PoolType]
    ) -> PoolType:
        """Select pool using load balancing algorithm."""
        # Get current pool metrics
        pool_scores = {}

        for pool_type in available_pools:
            metrics = self.pool_metrics.get(pool_type)
            if not metrics:
                continue

            # Calculate load score (lower is better)
            utilization = (
                (metrics.active_connections / metrics.total_connections)
                if metrics.total_connections > 0
                else 0
            )
            wait_time_factor = metrics.avg_wait_time_ms / 1000  # Convert to seconds

            # Weighted score
            score = (utilization * 0.6) + (wait_time_factor * 0.4)
            pool_scores[pool_type] = score

        if not pool_scores:
            return available_pools[0]

        # Select pool with lowest score
        selected_pool = min(pool_scores.items(), key=lambda x: x[1])[0]

        # Update round-robin counter
        self.round_robin_counter[selected_pool] += 1

        return selected_pool

    async def release_connection(self, conn: asyncpg.Connection) -> None:
        """Release connection back to pool."""
        try:
            # Get connection pool type
            pool_type = self._get_connection_pool_type(conn)

            if pool_type in self.pools:
                await self.pools[pool_type].release(conn)
                await self._update_pool_metrics(pool_type, 0, "release")
            else:
                # Close unknown connection
                await conn.close()

        except Exception as e:
            logger.error(f"Failed to release connection: {e}")
            raise

    async def execute_query(
        self,
        query: str,
        *args,
        pool_type: Optional[PoolType] = None,
        read_only: bool = False,
        timeout: Optional[float] = None,
    ) -> Any:
        """Execute query with automatic connection management."""
        start_time = time.time()

        async with await self.get_connection(pool_type, read_only) as conn:
            try:
                # Execute query
                if timeout:
                    result = await conn.fetch(query, *args, timeout=timeout)
                else:
                    result = await conn.fetch(query, *args)

                # Update metrics
                query_time_ms = (time.time() - start_time) * 1000
                await self._update_pool_metrics(
                    pool_type or PoolType.PRIMARY, query_time_ms, "query"
                )

                return result

            except Exception as e:
                # Record query error
                query_time_ms = (time.time() - start_time) * 1000
                await self._update_pool_metrics(
                    pool_type or PoolType.PRIMARY, query_time_ms, "query_error"
                )

                logger.error(f"Query execution failed: {e}")
                raise

    async def _update_pool_metrics(
        self, pool_type: PoolType, duration_ms: float, operation: str
    ) -> None:
        """Update pool performance metrics."""
        if pool_type not in self.pool_metrics:
            return

        metrics = self.pool_metrics[pool_type]

        # Update basic metrics
        if pool_type in self.pools:
            pool = self.pools[pool_type]
            metrics.total_connections = pool.get_size()
            metrics.active_connections = pool.get_size() - pool.get_idle_size()
            metrics.idle_connections = pool.get_idle_size()

        # Update operation-specific metrics
        if operation == "acquire":
            # Update wait time metrics
            if metrics.avg_wait_time_ms == 0:
                metrics.avg_wait_time_ms = duration_ms
            else:
                metrics.avg_wait_time_ms = (metrics.avg_wait_time_ms * 0.9) + (
                    duration_ms * 0.1
                )

            metrics.max_wait_time_ms = max(metrics.max_wait_time_ms, duration_ms)

        elif operation == "query":
            # Update query metrics
            metrics.total_queries += 1

            if metrics.avg_query_time_ms == 0:
                metrics.avg_query_time_ms = duration_ms
            else:
                metrics.avg_query_time_ms = (metrics.avg_query_time_ms * 0.99) + (
                    duration_ms * 0.01
                )

        elif operation == "acquire_error":
            metrics.failed_connections += 1

        elif operation == "query_error":
            metrics.connection_errors += 1

        # Update timestamp
        metrics.timestamp = time.time()

        # Store in history
        self.metrics_history[pool_type].append(metrics)

    async def _track_connection_usage(
        self, conn: asyncpg.Connection, pool_type: PoolType
    ) -> None:
        """Track individual connection usage."""
        connection_id = str(id(conn))

        if connection_id in self.connection_stats:
            stats = self.connection_stats[connection_id]
            stats.last_used = time.time()
            stats.queries_executed += 1
            stats.is_active = True

    async def optimize_pool_sizes(self) -> Dict[str, Any]:
        """Optimize pool sizes based on current usage patterns."""
        optimization_results = {
            "optimized_pools": [],
            "recommendations": [],
            "estimated_improvements": {},
        }

        if not self.optimization_enabled:
            return optimization_results

        for pool_type, pool in self.pools.items():
            metrics = self.pool_metrics.get(pool_type)
            config = self.pool_configs[pool_type]

            if not metrics:
                continue

            # Calculate optimal pool size
            current_size = pool.get_size()
            optimal_size = await self._calculate_optimal_pool_size(
                pool_type, metrics, config
            )

            if optimal_size != current_size:
                # Recommend pool size change
                recommendation = {
                    "pool_type": pool_type.value,
                    "current_size": current_size,
                    "recommended_size": optimal_size,
                    "reason": self._get_pool_size_recommendation_reason(
                        metrics, current_size, optimal_size
                    ),
                }

                optimization_results["recommendations"].append(recommendation)

                # Apply optimization if auto-scaling enabled
                if self.auto_scaling_enabled:
                    await self._resize_pool(pool_type, optimal_size)
                    optimization_results["optimized_pools"].append(pool_type.value)

                    # Estimate improvement
                    improvement = await self._estimate_pool_improvement(
                        pool_type, current_size, optimal_size
                    )
                    optimization_results["estimated_improvements"][pool_type.value] = (
                        improvement
                    )

        return optimization_results

    async def _calculate_optimal_pool_size(
        self, pool_type: PoolType, metrics: PoolMetrics, config: PoolConfiguration
    ) -> int:
        """Calculate optimal pool size based on metrics."""
        current_size = metrics.total_connections
        utilization = (
            (metrics.active_connections / current_size) if current_size > 0 else 0
        )
        avg_wait = metrics.avg_wait_time_ms

        # Base calculation on utilization
        if utilization > 0.9:  # High utilization
            recommended_size = int(current_size * 1.5)
        elif utilization > 0.8:  # Moderate utilization
            recommended_size = int(current_size * 1.2)
        elif utilization < 0.3 and current_size > config.min_size:  # Low utilization
            recommended_size = max(int(current_size * 0.8), config.min_size)
        else:
            recommended_size = current_size

        # Factor in wait times
        if avg_wait > self.thresholds["avg_wait_time_ms"]:
            recommended_size = max(recommended_size, int(current_size * 1.3))

        # Apply constraints
        recommended_size = max(recommended_size, config.min_size)
        recommended_size = min(recommended_size, config.max_size)

        return recommended_size

    def _get_pool_size_recommendation_reason(
        self, metrics: PoolMetrics, current: int, recommended: int
    ) -> str:
        """Get reason for pool size recommendation."""
        utilization = (metrics.active_connections / current) if current > 0 else 0

        if recommended > current:
            if utilization > 0.9:
                return f"High utilization ({utilization:.1%}) - increase capacity"
            elif metrics.avg_wait_time_ms > self.thresholds["avg_wait_time_ms"]:
                return f"High wait times ({metrics.avg_wait_time_ms:.1f}ms) - increase capacity"
            else:
                return "Moderate utilization - proactive scaling"
        else:
            if utilization < 0.3:
                return f"Low utilization ({utilization:.1%}) - reduce capacity"
            else:
                return "Optimization - balance performance and resources"

    async def _resize_pool(self, pool_type: PoolType, new_size: int) -> None:
        """Resize connection pool."""
        try:
            old_pool = self.pools[pool_type]
            config = self.pool_configs[pool_type]

            # Create new pool with updated size
            new_config = {
                "host": old_pool._host,
                "port": old_pool._port,
                "user": old_pool._user,
                "password": old_pool._password,
                "database": old_pool._database,
                "min_size": new_size,
                "max_size": new_size,
                "max_queries": config.max_queries,
                "max_inactive_connection_lifetime": config.max_inactive_connection_lifetime,
                "timeout": config.timeout,
                "command_timeout": config.command_timeout,
                "server_settings": config.server_settings,
            }

            await self._create_pool(pool_type, new_config)

            # Close old pool gracefully
            await old_pool.close()

            logger.info(f"Resized {pool_type.value} pool to {new_size} connections")

        except Exception as e:
            logger.error(f"Failed to resize {pool_type.value} pool: {e}")
            raise

    async def _estimate_pool_improvement(
        self, pool_type: PoolType, old_size: int, new_size: int
    ) -> Dict[str, float]:
        """Estimate performance improvement from pool resize."""
        metrics = self.pool_metrics.get(pool_type)
        if not metrics:
            return {"wait_time_improvement_pct": 0.0, "throughput_improvement_pct": 0.0}

        # Simple estimation based on size change
        size_ratio = new_size / old_size

        # Wait time improvement (inverse relationship)
        wait_improvement = max(0, (size_ratio - 1) * 100)

        # Throughput improvement (direct relationship)
        throughput_improvement = min((size_ratio - 1) * 100, 50)  # Cap at 50%

        return {
            "wait_time_improvement_pct": wait_improvement,
            "throughput_improvement_pct": throughput_improvement,
        }

    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on all pools."""
        health_results = {
            "overall_status": "healthy",
            "pool_status": {},
            "failed_checks": [],
            "recommendations": [],
        }

        for pool_type, pool in self.pools.items():
            try:
                # Perform health check
                health_status = await self._check_pool_health(pool_type)
                health_results["pool_status"][pool_type.value] = health_status

                # Update overall status
                if health_status["status"] == "unhealthy":
                    health_results["overall_status"] = "unhealthy"
                elif (
                    health_status["status"] == "degraded"
                    and health_results["overall_status"] == "healthy"
                ):
                    health_results["overall_status"] = "degraded"

                # Record health check failures
                if health_status["status"] != "healthy":
                    health_results["failed_checks"].append(
                        {
                            "pool": pool_type.value,
                            "status": health_status["status"],
                            "issues": health_status["issues"],
                        }
                    )

            except Exception as e:
                health_results["pool_status"][pool_type.value] = {
                    "status": "error",
                    "issues": [f"Health check failed: {str(e)}"],
                }
                health_results["failed_checks"].append(
                    {"pool": pool_type.value, "status": "error", "issues": [str(e)]}
                )

        return health_results

    async def _check_pool_health(self, pool_type: PoolType) -> Dict[str, Any]:
        """Check health of specific pool."""
        health_status = {"status": "healthy", "issues": [], "metrics": {}}

        try:
            pool = self.pools[pool_type]
            metrics = self.pool_metrics.get(pool_type)
            config = self.pool_configs[pool_type]

            if not metrics:
                health_status["status"] = "degraded"
                health_status["issues"].append("No metrics available")
                return health_status

            # Check connection availability
            if pool.get_size() == 0:
                health_status["status"] = "unhealthy"
                health_status["issues"].append("No connections available")

            # Check wait times
            if metrics.avg_wait_time_ms > self.thresholds["max_wait_time_ms"]:
                health_status["status"] = "degraded"
                health_status["issues"].append(
                    f"High wait times: {metrics.avg_wait_time_ms:.1f}ms"
                )

            # Check error rates
            total_operations = metrics.total_queries + metrics.failed_connections
            if total_operations > 0:
                error_rate = (
                    metrics.connection_errors + metrics.failed_connections
                ) / total_operations
                if error_rate > self.thresholds["connection_error_rate"]:
                    health_status["status"] = "degraded"
                    health_status["issues"].append(f"High error rate: {error_rate:.2%}")

            # Check pool utilization
            if metrics.total_connections > 0:
                utilization = (
                    metrics.active_connections / metrics.total_connections
                ) * 100
                if utilization > self.thresholds["pool_utilization_pct"]:
                    health_status["status"] = "degraded"
                    health_status["issues"].append(
                        f"High utilization: {utilization:.1f}%"
                    )

            # Include metrics in response
            health_status["metrics"] = {
                "total_connections": metrics.total_connections,
                "active_connections": metrics.active_connections,
                "avg_wait_time_ms": metrics.avg_wait_time_ms,
                "total_queries": metrics.total_queries,
                "failed_connections": metrics.failed_connections,
            }

        except Exception as e:
            health_status["status"] = "error"
            health_status["issues"].append(f"Health check error: {str(e)}")

        return health_status

    async def _start_monitoring(self) -> None:
        """Start background monitoring tasks."""
        # Health check monitoring
        if self.pool_configs and any(
            config.enable_health_checks for config in self.pool_configs.values()
        ):
            self.health_check_task = asyncio.create_task(self._health_check_loop())

        # Pool optimization monitoring
        if self.auto_scaling_enabled:
            self.optimization_task = asyncio.create_task(self._optimization_loop())

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await self.perform_health_checks()

                # Sleep based on minimum health check interval
                min_interval = min(
                    config.health_check_interval
                    for config in self.pool_configs.values()
                    if config.enable_health_checks
                )
                await asyncio.sleep(min_interval)

            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)

    async def _optimization_loop(self) -> None:
        """Background pool optimization loop."""
        while True:
            try:
                await self.optimize_pool_sizes()
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(300)

    def get_pool_summary(self) -> Dict[str, Any]:
        """Get comprehensive pool summary."""
        summary = {
            "total_pools": len(self.pools),
            "pool_types": [pool_type.value for pool_type in self.pools.keys()],
            "total_connections": sum(pool.get_size() for pool in self.pools.values()),
            "active_connections": sum(
                pool.get_size() - pool.get_idle_size() for pool in self.pools.values()
            ),
            "pool_details": {},
        }

        # Add detailed pool information
        for pool_type, pool in self.pools.items():
            metrics = self.pool_metrics.get(pool_type)
            config = self.pool_configs[pool_type]

            summary["pool_details"][pool_type.value] = {
                "size": pool.get_size(),
                "idle": pool.get_idle_size(),
                "active": pool.get_size() - pool.get_idle_size(),
                "min_size": config.min_size,
                "max_size": config.max_size,
                "metrics": {
                    "total_queries": metrics.total_queries if metrics else 0,
                    "avg_wait_time_ms": metrics.avg_wait_time_ms if metrics else 0,
                    "avg_query_time_ms": metrics.avg_query_time_ms if metrics else 0,
                    "failed_connections": metrics.failed_connections if metrics else 0,
                }
                if metrics
                else {},
            }

        return summary

    async def close_all_pools(self) -> None:
        """Close all connection pools."""
        # Stop monitoring tasks
        if self.health_check_task:
            self.health_check_task.cancel()
            self.health_check_task = None

        if self.optimization_task:
            self.optimization_task.cancel()
            self.optimization_task = None

        # Close all pools
        for pool_type, pool in self.pools.items():
            try:
                await pool.close()
                logger.info(f"Closed {pool_type.value} connection pool")
            except Exception as e:
                logger.error(f"Failed to close {pool_type.value} pool: {e}")

        self.pools.clear()
        self.pool_metrics.clear()
        self.connection_stats.clear()


# Global pool manager instance
_pool_manager: ConnectionPoolManager | None = None


def get_pool_manager() -> ConnectionPoolManager:
    """Get global pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        raise RuntimeError(
            "Pool manager not initialized. Call init_pool_manager() first."
        )
    return _pool_manager


async def init_pool_manager(
    database_configs: Dict[PoolType, Dict[str, Any]],
    alert_manager: Optional[Any] = None,
) -> ConnectionPoolManager:
    """Initialize global pool manager."""
    global _pool_manager
    _pool_manager = ConnectionPoolManager(alert_manager)
    await _pool_manager.initialize_pools(database_configs)
    return _pool_manager
