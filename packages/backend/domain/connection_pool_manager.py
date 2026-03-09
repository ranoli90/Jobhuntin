"""
Connection Pool Manager for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import asyncpg
import psutil

from shared.logging_config import get_logger

logger = get_logger("sorce.connection_pool_manager")


class PoolStatus(Enum):
    """Connection pool status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"


class ConnectionType(Enum):
    """Types of database connections."""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    REPLICA = "replica"


@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration."""

    pool_name: str
    min_connections: int
    max_connections: int
    connection_type: ConnectionType
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    command_timeout: int = 30
    statement_timeout: int = 30000
    idle_timeout: int = 300
    max_lifetime: int = 3600
    max_queries_per_connection: int = 5000
    health_check_interval: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class PoolMetrics:
    """Connection pool metrics."""

    pool_name: str
    total_connections: int
    active_connections: int
    idle_connections: int
    queued_requests: int
    avg_connection_time_ms: float
    avg_query_time_ms: float
    connection_errors: int
    query_errors: int
    health_check_failures: int
    last_health_check: datetime
    status: PoolStatus
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class ConnectionStats:
    """Individual connection statistics."""

    connection_id: str
    pool_name: str
    created_at: datetime
    last_used: datetime
    query_count: int
    error_count: int
    total_query_time_ms: float
    avg_query_time_ms: float
    is_active: bool
    is_healthy: bool


class ConnectionPoolManager:
    """Advanced database connection pool management system."""

    def __init__(self):
        self._pools: Dict[str, asyncpg.Pool] = {}
        self._pool_configs: Dict[str, ConnectionPoolConfig] = {}
        self._pool_metrics: Dict[str, PoolMetrics] = {}
        self._connection_stats: Dict[str, ConnectionStats] = {}
        self._pool_health: Dict[str, PoolStatus] = {}

        # Initialize default pool configurations
        self._initialize_default_configs()

        # Start background monitoring
        asyncio.create_task(self._start_pool_monitoring())

    async def create_pool(self, config: ConnectionPoolConfig) -> bool:
        """Create a new connection pool."""
        try:
            # Build connection string
            connection_string = self._build_connection_string(config)

            # Create pool
            pool = await asyncpg.create_pool(
                connection_string,
                min_size=config.min_connections,
                max_size=config.max_connections,
                command_timeout=config.command_timeout,
                server_settings={
                    "application_name": f"jobhuntin_pool_{config.pool_name}",
                    "jit": "off",  # Disable JIT for connection pooling
                },
            )

            # Store pool and config
            self._pools[config.pool_name] = pool
            self._pool_configs[config.pool_name] = config
            self._pool_health[config.pool_name] = PoolStatus.HEALTHY

            # Initialize metrics
            self._pool_metrics[config.pool_name] = PoolMetrics(
                pool_name=config.pool_name,
                total_connections=config.min_connections,
                active_connections=0,
                idle_connections=config.min_connections,
                queued_requests=0,
                avg_connection_time_ms=0.0,
                avg_query_time_ms=0.0,
                connection_errors=0,
                query_errors=0,
                health_check_failures=0,
                last_health_check=datetime.now(timezone.utc),
                status=PoolStatus.HEALTHY,
            )

            logger.info(
                f"Created connection pool: {config.pool_name} "
                f"(min={config.min_connections}, max={config.max_connections})"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to create pool {config.pool_name}: {e}")
            return False

    async def get_connection(
        self,
        pool_name: str,
        timeout: Optional[float] = None,
    ) -> asyncpg.Connection:
        """Get connection from pool."""
        try:
            if pool_name not in self._pools:
                raise ValueError(f"Pool {pool_name} not found")

            pool = self._pools[pool_name]
            config = self._pool_configs[pool_name]

            # Use configured timeout if not provided
            if timeout is None:
                timeout = config.command_timeout

            # Get connection with retry logic
            for attempt in range(config.retry_attempts):
                try:
                    start_time = datetime.now(timezone.utc)
                    connection = await pool.acquire(timeout=timeout)

                    # Record connection time
                    connection_time = (
                        datetime.now(timezone.utc) - start_time
                    ).total_seconds() * 1000
                    await self._update_connection_time_metrics(
                        pool_name, connection_time
                    )

                    # Track connection usage
                    connection_id = str(id(connection))
                    if connection_id not in self._connection_stats:
                        self._connection_stats[connection_id] = ConnectionStats(
                            connection_id=connection_id,
                            pool_name=pool_name,
                            created_at=datetime.now(timezone.utc),
                            last_used=datetime.now(timezone.utc),
                            query_count=0,
                            error_count=0,
                            total_query_time_ms=0.0,
                            avg_query_time_ms=0.0,
                            is_active=True,
                            is_healthy=True,
                        )

                    return connection

                except Exception as e:
                    logger.warning(
                        f"Connection attempt {attempt + 1} failed for pool {pool_name}: {e}"
                    )
                    if attempt < config.retry_attempts - 1:
                        await asyncio.sleep(
                            config.retry_delay * (2**attempt)
                        )  # Exponential backoff
                    else:
                        await self._record_connection_error(pool_name)
                        raise

        except Exception as e:
            logger.error(f"Failed to get connection from pool {pool_name}: {e}")
            raise

    async def release_connection(
        self,
        connection: asyncpg.Connection,
        pool_name: str,
    ) -> None:
        """Release connection back to pool."""
        try:
            if pool_name not in self._pools:
                logger.warning(f"Pool {pool_name} not found, cannot release connection")
                return

            pool = self._pools[pool_name]
            connection_id = str(id(connection))

            # Update connection stats
            if connection_id in self._connection_stats:
                stats = self._connection_stats[connection_id]
                stats.is_active = False
                stats.last_used = datetime.now(timezone.utc)

            # Release connection
            await pool.release(connection)

        except Exception as e:
            logger.error(f"Failed to release connection to pool {pool_name}: {e}")

    async def execute_query(
        self,
        pool_name: str,
        query: str,
        *args,
        timeout: Optional[float] = None,
        fetch: Optional[str] = None,
    ) -> Any:
        """Execute query using connection from pool."""
        try:
            connection = await self.get_connection(pool_name, timeout)

            try:
                start_time = datetime.now(timezone.utc)

                if fetch == "one":
                    result = await connection.fetchrow(query, *args)
                elif fetch == "all":
                    result = await connection.fetch(query, *args)
                elif fetch == "val":
                    result = await connection.fetchval(query, *args)
                else:
                    result = await connection.execute(query, *args)

                # Record query metrics
                query_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                await self._update_query_metrics(
                    pool_name, str(id(connection)), query_time, False
                )

                return result

            finally:
                await self.release_connection(connection, pool_name)

        except Exception as e:
            await self._record_query_error(pool_name, str(id(connection)))
            logger.error(f"Failed to execute query on pool {pool_name}: {e}")
            raise

    async def close_pool(self, pool_name: str) -> bool:
        """Close a connection pool."""
        try:
            if pool_name not in self._pools:
                logger.warning(f"Pool {pool_name} not found")
                return False

            pool = self._pools[pool_name]
            await pool.close()

            # Remove from tracking
            del self._pools[pool_name]
            del self._pool_configs[pool_name]
            del self._pool_metrics[pool_name]
            del self._pool_health[pool_name]

            logger.info(f"Closed connection pool: {pool_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to close pool {pool_name}: {e}")
            return False

    async def get_pool_metrics(
        self, pool_name: Optional[str] = None
    ) -> Dict[str, PoolMetrics]:
        """Get pool metrics."""
        try:
            if pool_name:
                if pool_name in self._pool_metrics:
                    await self._update_pool_metrics(pool_name)
                    return {pool_name: self._pool_metrics[pool_name]}
                else:
                    return {}
            else:
                # Update all pool metrics
                for name in self._pools.keys():
                    await self._update_pool_metrics(name)

                return self._pool_metrics.copy()

        except Exception as e:
            logger.error(f"Failed to get pool metrics: {e}")
            return {}

    async def get_pool_health(
        self, pool_name: Optional[str] = None
    ) -> Dict[str, PoolStatus]:
        """Get pool health status."""
        try:
            if pool_name:
                if pool_name in self._pool_health:
                    await self._check_pool_health(pool_name)
                    return {pool_name: self._pool_health[pool_name]}
                else:
                    return {}
            else:
                # Check all pool health
                for name in self._pools.keys():
                    await self._check_pool_health(name)

                return self._pool_health.copy()

        except Exception as e:
            logger.error(f"Failed to get pool health: {e}")
            return {}

    async def optimize_pool(
        self, pool_name: str, target_size: Optional[int] = None
    ) -> bool:
        """Optimize pool size based on current usage."""
        try:
            if pool_name not in self._pools:
                logger.error(f"Pool {pool_name} not found")
                return False

            config = self._pool_configs[pool_name]
            metrics = self._pool_metrics[pool_name]

            if target_size is None:
                # Calculate optimal size based on usage
                avg_active = metrics.active_connections
                avg_idle = metrics.idle_connections
                avg_queued = metrics.queued_requests

                # Simple optimization logic
                if avg_queued > 0:
                    # Increase pool size if there are queued requests
                    target_size = min(
                        config.max_connections, config.min_connections + avg_queued
                    )
                elif avg_active < config.min_connections // 2:
                    # Decrease pool size if underutilized
                    target_size = max(
                        config.min_connections, avg_active + avg_idle // 2
                    )
                else:
                    # Keep current size
                    return True

            # Apply new size
            if target_size != config.min_connections:
                logger.info(
                    f"Optimizing pool {pool_name} from {config.min_connections} to {target_size}"
                )

                # Create new pool with optimized size
                old_config = config
                new_config = ConnectionPoolConfig(
                    pool_name=config.pool_name,
                    min_connections=target_size,
                    max_connections=config.max_connections,
                    connection_type=config.connection_type,
                    host=config.host,
                    port=config.port,
                    database=config.database,
                    username=config.username,
                    password=config.password,
                    ssl_mode=config.ssl_mode,
                    command_timeout=config.command_timeout,
                    statement_timeout=config.statement_timeout,
                    idle_timeout=config.idle_timeout,
                    max_lifetime=config.max_lifetime,
                    max_queries_per_connection=config.max_queries_per_connection,
                    health_check_interval=config.health_check_interval,
                    retry_attempts=config.retry_attempts,
                    retry_delay=config.retry_delay,
                )

                # Close old pool and create new one
                await self.close_pool(pool_name)
                success = await self.create_pool(new_config)

                if success:
                    logger.info(
                        f"Successfully optimized pool {pool_name} to {target_size} connections"
                    )
                else:
                    logger.error(f"Failed to optimize pool {pool_name}")
                    # Try to restore original configuration
                    await self.create_pool(old_config)

                return success

            return True

        except Exception as e:
            logger.error(f"Failed to optimize pool {pool_name}: {e}")
            return False

    def _initialize_default_configs(self) -> None:
        """Initialize default pool configurations."""
        # Note: These would be loaded from environment variables or config files
        # For now, we'll create placeholder configs
        pass

    def _build_connection_string(self, config: ConnectionPoolConfig) -> str:
        """Build PostgreSQL connection string."""
        try:
            return (
                f"postgresql://{config.username}:{config.password}"
                f"@{config.host}:{config.port}/{config.database}"
                f"?sslmode={config.ssl_mode}"
            )
        except Exception as e:
            logger.error(f"Failed to build connection string: {e}")
            return ""

    async def _start_pool_monitoring(self) -> None:
        """Start background pool monitoring."""
        try:
            while True:
                await asyncio.sleep(60)  # Run every minute

                # Update pool metrics
                for pool_name in self._pools.keys():
                    try:
                        await self._update_pool_metrics(pool_name)
                        await self._check_pool_health(pool_name)
                    except Exception as e:
                        logger.error(f"Failed to monitor pool {pool_name}: {e}")

                # Optimize pools if needed
                await self._optimize_pools_if_needed()

        except Exception as e:
            logger.error(f"Background pool monitoring failed: {e}")

    async def _update_pool_metrics(self, pool_name: str) -> None:
        """Update pool metrics."""
        try:
            if pool_name not in self._pools:
                return

            pool = self._pools[pool_name]
            metrics = self._pool_metrics[pool_name]

            # Get pool size
            metrics.total_connections = pool.get_size()

            # Count active and idle connections
            active_count = 0
            idle_count = 0

            for connection_id, stats in self._connection_stats.items():
                if stats.pool_name == pool_name:
                    if stats.is_active:
                        active_count += 1
                    else:
                        idle_count += 1

            metrics.active_connections = active_count
            metrics.idle_connections = idle_count

            # Update timestamp
            metrics.last_health_check = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to update pool metrics for {pool_name}: {e}")

    async def _check_pool_health(self, pool_name: str) -> None:
        """Check pool health status."""
        try:
            if pool_name not in self._pools:
                self._pool_health[pool_name] = PoolStatus.FAILED
                return

            pool = self._pools[pool_name]
            config = self._pool_configs[pool_name]
            metrics = self._pool_metrics[pool_name]

            # Perform health check
            try:
                # Try to get a connection
                connection = await pool.acquire(timeout=5)
                await connection.execute("SELECT 1")
                await pool.release(connection)

                # Check metrics
                error_rate = 0
                total_requests = metrics.connection_errors + metrics.query_errors

                if total_requests > 0:
                    error_rate = total_requests / total_requests

                # Determine health status
                if error_rate > 0.1:  # 10% error rate
                    status = PoolStatus.CRITICAL
                elif error_rate > 0.05:  # 5% error rate
                    status = PoolStatus.DEGRADED
                elif metrics.queued_requests > 10:
                    status = PoolStatus.DEGRADED
                else:
                    status = PoolStatus.HEALTHY

                self._pool_health[pool_name] = status

            except Exception as e:
                logger.error(f"Health check failed for pool {pool_name}: {e}")
                metrics.health_check_failures += 1
                self._pool_health[pool_name] = PoolStatus.CRITICAL

        except Exception as e:
            logger.error(f"Failed to check pool health for {pool_name}: {e}")

    async def _update_connection_time_metrics(
        self, pool_name: str, connection_time: float
    ) -> None:
        """Update connection time metrics."""
        try:
            metrics = self._pool_metrics[pool_name]

            # Update average connection time
            if metrics.avg_connection_time_ms == 0:
                metrics.avg_connection_time_ms = connection_time
            else:
                metrics.avg_connection_time_ms = (
                    metrics.avg_connection_time_ms * 0.9 + connection_time * 0.1
                )

        except Exception as e:
            logger.error(f"Failed to update connection time metrics: {e}")

    async def _update_query_metrics(
        self,
        pool_name: str,
        connection_id: str,
        query_time: float,
        is_error: bool,
    ) -> None:
        """Update query metrics."""
        try:
            # Update pool metrics
            metrics = self._pool_metrics[pool_name]

            if is_error:
                metrics.query_errors += 1
            else:
                # Update average query time
                if metrics.avg_query_time_ms == 0:
                    metrics.avg_query_time_ms = query_time
                else:
                    metrics.avg_query_time_ms = (
                        metrics.avg_query_time_ms * 0.9 + query_time * 0.1
                    )

            # Update connection stats
            if connection_id in self._connection_stats:
                stats = self._connection_stats[connection_id]
                stats.query_count += 1

                if is_error:
                    stats.error_count += 1
                else:
                    stats.total_query_time_ms += query_time
                    stats.avg_query_time_ms = (
                        stats.total_query_time_ms / stats.query_count
                    )

                stats.last_used = datetime.now(timezone.utc)

                # Check connection health
                if stats.error_count > 10:  # Too many errors
                    stats.is_healthy = False
                elif stats.avg_query_time_ms > 5000:  # Too slow
                    stats.is_healthy = False

        except Exception as e:
            logger.error(f"Failed to update query metrics: {e}")

    async def _record_connection_error(self, pool_name: str) -> None:
        """Record connection error."""
        try:
            metrics = self._pool_metrics[pool_name]
            metrics.connection_errors += 1
        except Exception as e:
            logger.error(f"Failed to record connection error: {e}")

    async def _record_query_error(self, pool_name: str, connection_id: str) -> None:
        """Record query error."""
        try:
            await self._update_query_metrics(pool_name, connection_id, 0, True)
        except Exception as e:
            logger.error(f"Failed to record query error: {e}")

    async def _optimize_pools_if_needed(self) -> None:
        """Optimize pools if needed based on metrics."""
        try:
            for pool_name in self._pools.keys():
                try:
                    metrics = self._pool_metrics[pool_name]
                    config = self._pool_configs[pool_name]

                    # Check if optimization is needed
                    if metrics.queued_requests > 5:
                        # Too many queued requests, increase pool size
                        new_size = min(
                            config.max_connections, config.min_connections + 2
                        )
                        await self.optimize_pool(pool_name, new_size)
                    elif metrics.active_connections < config.min_connections // 3:
                        # Pool underutilized, decrease size
                        new_size = max(
                            config.min_connections // 2, config.min_connections
                        )
                        await self.optimize_pool(pool_name, new_size)

                except Exception as e:
                    logger.error(f"Failed to optimize pool {pool_name}: {e}")

        except Exception as e:
            logger.error(f"Failed to optimize pools: {e}")

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics for all pools."""
        try:
            total_connections = 0
            total_active = 0
            total_idle = 0
            total_queued = 0
            total_errors = 0

            pool_details = {}

            for pool_name, metrics in self._pool_metrics.items():
                total_connections += metrics.total_connections
                total_active += metrics.active_connections
                total_idle += metrics.idle_connections
                total_queued += metrics.queued_requests
                total_errors += metrics.connection_errors + metrics.query_errors

                pool_details[pool_name] = {
                    "connections": metrics.total_connections,
                    "active": metrics.active_connections,
                    "idle": metrics.idle_connections,
                    "queued": metrics.queued_requests,
                    "errors": metrics.connection_errors + metrics.query_errors,
                    "avg_connection_time": metrics.avg_connection_time_ms,
                    "avg_query_time": metrics.avg_query_time_ms,
                    "status": metrics.status.value,
                }

            # Get system resource usage
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pools": pool_details,
                "totals": {
                    "connections": total_connections,
                    "active": total_active,
                    "idle": total_idle,
                    "queued": total_queued,
                    "errors": total_errors,
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "memory_used_gb": memory.used / (1024**3),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}

    async def get_connection_stats(
        self, pool_name: Optional[str] = None
    ) -> Dict[str, List[ConnectionStats]]:
        """Get detailed connection statistics."""
        try:
            if pool_name:
                return {
                    pool_name: [
                        stats
                        for stats in self._connection_stats.values()
                        if stats.pool_name == pool_name
                    ]
                }
            else:
                # Group by pool
                stats_by_pool = defaultdict(list)
                for stats in self._connection_stats.values():
                    stats_by_pool[stats.pool_name].append(stats)

                return dict(stats_by_pool)

        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {}

    async def cleanup_stale_connections(self) -> int:
        """Clean up stale connection statistics."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            cleaned_count = 0

            stale_connections = [
                conn_id
                for conn_id, stats in self._connection_stats.items()
                if stats.last_used < cutoff_time and not stats.is_active
            ]

            for conn_id in stale_connections:
                del self._connection_stats[conn_id]
                cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} stale connection statistics")

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup stale connections: {e}")
            return 0


# Factory function
def create_connection_pool_manager() -> ConnectionPoolManager:
    """Create connection pool manager instance."""
    return ConnectionPoolManager()
