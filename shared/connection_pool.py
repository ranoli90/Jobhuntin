"""
Connection Pool for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.connection_pool")


class PoolStatus(Enum):
    """Connection pool status."""

    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"
    CLOSED = "closed"


class ConnectionType(Enum):
    """Types of database connections."""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    REPLICA = "replica"


@dataclass
class PoolConfiguration:
    """Connection pool configuration."""

    pool_name: str
    connection_type: ConnectionType
    host: str
    port: int
    database: str
    username: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    ssl_mode: str = "prefer"
    command_timeout: int = 30
    statement_timeout: int = 30000
    idle_timeout: int = 300
    max_lifetime: int = 3600
    max_queries_per_connection: int = 5000
    health_check_interval: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    connection_timeout: int = 10


@dataclass
class ConnectionMetrics:
    """Connection metrics."""

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
    bytes_sent: int = 0
    bytes_received: int = 0


@dataclass
class PoolMetrics:
    """Pool metrics."""

    pool_name: str
    status: PoolStatus
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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PooledConnection:
    """A wrapped database connection with metrics."""

    def __init__(self, connection: asyncpg.Connection, pool_name: str):
        self._connection = connection
        self._pool_name = pool_name
        self._connection_id = str(uuid.uuid4())
        self._created_at = datetime.now(timezone.utc)
        self._last_used = datetime.now(timezone.utc)
        self._query_count = 0
        self._error_count = 0
        self._total_query_time_ms = 0.0
        self._bytes_sent = 0
        self._bytes_received = 0
        self._is_active = True
        self._is_healthy = True

    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute a query with metrics tracking."""
        start_time = time.time()

        try:
            result = await self._connection.execute(query, *args, timeout=timeout)

            # Update metrics
            query_time_ms = (time.time() - start_time) * 1000
            self._update_query_metrics(query_time_ms, True)

            return str(result)  # type: ignore[arg-type]

        except Exception:
            self._update_query_metrics(0, False)
            self._error_count += 1
            raise

    async def fetch(
        self, query: str, *args, timeout: Optional[float] = None
    ) -> List[asyncpg.Record]:
        """Fetch query results with metrics tracking."""
        start_time = time.time()

        try:
            result = await self._connection.fetch(query, *args, timeout=timeout)

            # Update metrics
            query_time_ms = (time.time() - start_time) * 1000
            self._update_query_metrics(query_time_ms, True)

            return result  # type: ignore[no-any-return]

        except Exception:
            self._update_query_metrics(0, False)
            self._error_count += 1
            raise

    async def fetchrow(
        self, query: str, *args, timeout: Optional[float] = None
    ) -> asyncpg.Record:
        """Fetch single row with metrics tracking."""
        start_time = time.time()

        try:
            result = await self._connection.fetchrow(query, *args, timeout=timeout)

            # Update metrics
            query_time_ms = (time.time() - start_time) * 1000
            self._update_query_metrics(query_time_ms, True)

            return str(result)  # type: ignore[arg-type]

        except Exception:
            self._update_query_metrics(0, False)
            self._error_count += 1
            raise

    async def fetchval(self, query: str, *args, timeout: Optional[float] = None) -> Any:
        """Fetch single value with metrics tracking."""
        start_time = time.time()

        try:
            result = await self._connection.fetchval(query, *args, timeout=timeout)

            # Update metrics
            query_time_ms = (time.time() - start_time) * 1000
            self._update_query_metrics(query_time_ms, True)

            return str(result)  # type: ignore[arg-type]

        except Exception:
            self._update_query_metrics(0, False)
            self._error_count += 1
            raise

    def _update_query_metrics(self, query_time_ms: float, success: bool) -> None:
        """Update query metrics."""
        self._last_used = datetime.now(timezone.utc)
        self._query_count += 1

        if success:
            self._total_query_time_ms += query_time_ms

    @property
    def avg_query_time_ms(self) -> float:
        """Calculate average query time."""
        if self._query_count == 0:
            return 0.0
        return self._total_query_time_ms / self._query_count

    @property
    def metrics(self) -> ConnectionMetrics:
        """Get connection metrics."""
        return ConnectionMetrics(
            connection_id=self._connection_id,
            pool_name=self._pool_name,
            created_at=self._created_at,
            last_used=self._last_used,
            query_count=self._query_count,
            error_count=self._error_count,
            total_query_time_ms=self._total_query_time_ms,
            avg_query_time_ms=self.avg_query_time_ms,
            is_active=self._is_active,
            is_healthy=self._is_healthy,
            bytes_sent=self._bytes_sent,
            bytes_received=self._bytes_received,
        )


class ConnectionPool:
    """Advanced database connection pool with metrics and health monitoring."""

    def __init__(self, config: PoolConfiguration):
        self.config = config
        self._pool: Optional[asyncpg.Pool] = None
        self._status = PoolStatus.INITIALIZING
        self._connections: Dict[str, PooledConnection] = {}
        self._queue: asyncio.Queue[Any] = asyncio.Queue()
        self._metrics = PoolMetrics(
            pool_name=config.pool_name,
            status=PoolStatus.INITIALIZING,
            total_connections=0,
            active_connections=0,
            idle_connections=0,
            queued_requests=0,
            avg_connection_time_ms=0.0,
            avg_query_time_ms=0.0,
            connection_errors=0,
            query_errors=0,
            health_check_failures=0,
            last_health_check=datetime.now(timezone.utc),
        )

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        # Initialize pool
        asyncio.create_task(self._initialize_pool())

    async def _initialize_pool(self) -> None:
        """Initialize the connection pool."""
        try:
            # Build connection string
            connection_string = (
                f"postgresql://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
                f"?sslmode={self.config.ssl_mode}"
            )

            # Create asyncpg pool
            self._pool = await asyncpg.create_pool(
                connection_string,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                server_settings={
                    "application_name": f"jobhuntin_pool_{self.config.pool_name}",
                    "jit": "off",
                },
            )

            self._status = PoolStatus.HEALTHY
            self._metrics.status = PoolStatus.HEALTHY
            self._metrics.total_connections = self.config.min_connections
            self._metrics.idle_connections = self.config.min_connections

            # Start background tasks
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            self._metrics_task = asyncio.create_task(self._metrics_loop())

            logger.info(
                f"Connection pool {self.config.pool_name} initialized successfully"
            )

        except Exception as e:
            self._status = PoolStatus.FAILED
            self._metrics.status = PoolStatus.FAILED
            logger.error(f"Failed to initialize pool {self.config.pool_name}: {e}")
            raise

    @asynccontextmanager
    async def acquire(
        self, timeout: Optional[float] = None
    ) -> AsyncIterator[PooledConnection]:
        """Acquire a connection from the pool."""
        if self._status == PoolStatus.FAILED:
            raise RuntimeError(f"Pool {self.config.pool_name} has failed")

        if self._pool is None:
            raise RuntimeError(f"Pool {self.config.pool_name} is not initialized")

        timeout = timeout or self.config.connection_timeout
        start_time = time.time()

        try:
            # Get connection from asyncpg pool
            raw_connection = await asyncio.wait_for(
                self._pool.acquire(), timeout=timeout
            )

            # Wrap with metrics
            connection = PooledConnection(raw_connection, self.config.pool_name)
            self._connections[connection._connection_id] = connection

            # Update metrics
            connection_time_ms = (time.time() - start_time) * 1000
            self._update_connection_metrics(connection_time_ms, True)

            try:
                yield connection
            finally:
                # Return connection to pool
                if self._pool:
                    await self._pool.release(raw_connection)

                # Remove from tracking
                if connection._connection_id in self._connections:
                    del self._connections[connection._connection_id]

                self._update_connection_metrics(0, False)

        except asyncio.TimeoutError:
            self._metrics.connection_errors += 1
            raise RuntimeError(f"Failed to acquire connection within {timeout}s")
        except Exception:
            self._metrics.connection_errors += 1
            raise

    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute a query using a connection from the pool."""
        async with self.acquire(timeout) as conn:
            result = await conn.execute(query, *args, timeout=timeout)
            return result  # type: ignore[no-any-return]

    async def fetch(
        self, query: str, *args, timeout: Optional[float] = None
    ) -> List[asyncpg.Record]:
        """Fetch query results using a connection from the pool."""
        async with self.acquire(timeout) as conn:
            result = await conn.fetch(query, *args, timeout=timeout)
            return result  # type: ignore[no-any-return]

    async def fetchrow(
        self, query: str, *args, timeout: Optional[float] = None
    ) -> asyncpg.Record:
        """Fetch single row using a connection from the pool."""
        async with self.acquire(timeout) as conn:
            result = await conn.fetchrow(query, *args, timeout=timeout)
            return result  # type: ignore[no-any-return]

    async def fetchval(self, query: str, *args, timeout: Optional[float] = None) -> Any:
        """Fetch single value using a connection from the pool."""
        async with self.acquire(timeout) as conn:
            return await conn.fetchval(query, *args, timeout=timeout)

    async def close(self) -> None:
        """Close the connection pool."""
        try:
            # Cancel background tasks
            if self._health_check_task:
                self._health_check_task.cancel()
            if self._metrics_task:
                self._metrics_task.cancel()

            # Close pool
            if self._pool:
                await self._pool.close()

            self._status = PoolStatus.CLOSED
            self._metrics.status = PoolStatus.CLOSED

            logger.info(f"Connection pool {self.config.pool_name} closed")

        except Exception as e:
            logger.error(f"Error closing pool {self.config.pool_name}: {e}")

    def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics."""
        return self._metrics

    def get_connection_metrics(self) -> List[ConnectionMetrics]:
        """Get metrics for all connections."""
        return [conn.metrics for conn in self._connections.values()]

    async def health_check(self) -> bool:
        """Perform health check on the pool."""
        try:
            if self._status == PoolStatus.FAILED:
                return False

            # Try to execute a simple query
            await self.execute("SELECT 1")

            self._metrics.last_health_check = datetime.now(timezone.utc)
            return True

        except Exception as e:
            self._metrics.health_check_failures += 1
            self._metrics.last_health_check = datetime.now(timezone.utc)

            # Update status based on failure count
            if self._metrics.health_check_failures > 3:
                self._status = PoolStatus.CRITICAL
                self._metrics.status = PoolStatus.CRITICAL
            elif self._metrics.health_check_failures > 1:
                self._status = PoolStatus.DEGRADED
                self._metrics.status = PoolStatus.DEGRADED

            logger.error(f"Health check failed for pool {self.config.pool_name}: {e}")
            return False

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        try:
            while True:
                await asyncio.sleep(self.config.health_check_interval)

                try:
                    await self.health_check()
                except Exception as e:
                    logger.error(f"Health check error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Health check loop failed: {e}")

    async def _metrics_loop(self) -> None:
        """Background metrics collection loop."""
        try:
            while True:
                await asyncio.sleep(60)  # Update metrics every minute

                try:
                    self._update_pool_metrics()
                except Exception as e:
                    logger.error(f"Metrics update error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Metrics loop failed: {e}")

    def _update_connection_metrics(
        self, connection_time_ms: float, is_acquire: bool
    ) -> None:
        """Update connection metrics."""
        try:
            if is_acquire:
                self._metrics.active_connections += 1
                self._metrics.idle_connections -= 1

                # Update average connection time
                if self._metrics.avg_connection_time_ms == 0:
                    self._metrics.avg_connection_time_ms = connection_time_ms
                else:
                    self._metrics.avg_connection_time_ms = (
                        self._metrics.avg_connection_time_ms * 0.9
                        + connection_time_ms * 0.1
                    )
            else:
                self._metrics.active_connections -= 1
                self._metrics.idle_connections += 1

        except Exception as e:
            logger.error(f"Failed to update connection metrics: {e}")

    def _update_pool_metrics(self) -> None:
        """Update pool metrics."""
        try:
            if self._pool:
                size = self._pool.get_size()
                self._metrics.total_connections = size

                # Calculate average query time from active connections
                if self._connections:
                    query_times = [
                        conn.avg_query_time_ms for conn in self._connections.values()
                    ]
                    if query_times:
                        self._metrics.avg_query_time_ms = sum(query_times) / len(
                            query_times
                        )

                # Update status
                if self._metrics.health_check_failures == 0:
                    self._status = PoolStatus.HEALTHY
                    self._metrics.status = PoolStatus.HEALTHY
                elif self._metrics.health_check_failures <= 1:
                    self._status = PoolStatus.DEGRADED
                    self._metrics.status = PoolStatus.DEGRADED
                else:
                    self._status = PoolStatus.CRITICAL
                    self._metrics.status = PoolStatus.CRITICAL

        except Exception as e:
            logger.error(f"Failed to update pool metrics: {e}")

    @property
    def status(self) -> PoolStatus:
        """Get pool status."""
        return self._status

    @property
    def is_healthy(self) -> bool:
        """Check if pool is healthy."""
        return self._status in [PoolStatus.HEALTHY, PoolStatus.DEGRADED]


class ConnectionPoolManager:
    """Manages multiple connection pools."""

    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}
        self._configurations: Dict[str, PoolConfiguration] = {}

    async def create_pool(self, config: PoolConfiguration) -> ConnectionPool:
        """Create a new connection pool."""
        try:
            if config.pool_name in self._pools:
                raise ValueError(f"Pool {config.pool_name} already exists")

            pool = ConnectionPool(config)
            self._pools[config.pool_name] = pool
            self._configurations[config.pool_name] = config

            # Wait for initialization
            await asyncio.sleep(0.1)

            if pool.status == PoolStatus.FAILED:
                raise RuntimeError(f"Pool {config.pool_name} failed to initialize")

            logger.info(f"Created connection pool: {config.pool_name}")
            return pool

        except Exception as e:
            logger.error(f"Failed to create pool {config.pool_name}: {e}")
            raise

    def get_pool(self, pool_name: str) -> Optional[ConnectionPool]:
        """Get a connection pool by name."""
        return self._pools.get(pool_name)

    async def close_pool(self, pool_name: str) -> bool:
        """Close a connection pool."""
        try:
            if pool_name not in self._pools:
                logger.warning(f"Pool {pool_name} not found")
                return False

            pool = self._pools[pool_name]
            await pool.close()

            del self._pools[pool_name]
            del self._configurations[pool_name]

            logger.info(f"Closed connection pool: {pool_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to close pool {pool_name}: {e}")
            return False

    async def close_all(self) -> None:
        """Close all connection pools."""
        for pool_name in list(self._pools.keys()):
            await self.close_pool(pool_name)

    def get_all_metrics(self) -> Dict[str, PoolMetrics]:
        """Get metrics for all pools."""
        return {name: pool.get_metrics() for name, pool in self._pools.items()}

    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all pools."""
        results = {}

        for name, pool in self._pools.items():
            try:
                results[name] = await pool.health_check()
            except Exception as e:
                logger.error(f"Health check failed for pool {name}: {e}")
                results[name] = False

        return results


# Global instance
connection_pool_manager = ConnectionPoolManager()


# Factory function
def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get connection pool manager instance."""
    return connection_pool_manager
