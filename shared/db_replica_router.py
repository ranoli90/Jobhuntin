"""Advanced database read replica routing and load balancing system.

Provides:
- Intelligent read replica routing
- Lag-aware routing decisions
- Health monitoring for replicas
- Automatic failover
- Performance optimization

Usage:
    from shared.db_replica_router import ReplicaRouter

    router = ReplicaRouter(primary_pool, replica_pools)
    await router.execute_read_query("SELECT * FROM users")
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import asyncpg

from shared.logging_config import get_logger
from shared.alerting import AlertSeverity, get_alert_manager

logger = get_logger("sorce.db_replica")


class ReplicaStatus(Enum):
    """Replica status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    LAGGING = "lagging"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


class RoutingStrategy(Enum):
    """Read replica routing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LAG_AWARE = "lag_aware"
    WEIGHTED = "weighted"
    GEOGRAPHIC = "geographic"
    RANDOM = "random"


@dataclass
class ReplicaInfo:
    """Replica information."""

    replica_id: str
    pool: asyncpg.Pool
    host: str
    port: int
    region: Optional[str] = None
    weight: float = 1.0
    max_lag_seconds: float = 30.0
    status: ReplicaStatus = ReplicaStatus.HEALTHY
    current_lag_seconds: float = 0.0
    connection_count: int = 0
    query_count: int = 0
    error_count: int = 0
    last_health_check: float = field(default_factory=time.time)
    response_time_ms: float = 0.0
    created_at: float = field(default_factory=time.time)


@dataclass
class RoutingMetrics:
    """Routing performance metrics."""

    total_queries: int = 0
    primary_queries: int = 0
    replica_queries: int = 0
    routing_errors: int = 0
    avg_response_time_ms: float = 0.0
    lag_aware_reroutes: int = 0
    failover_events: int = 0
    replica_utilization: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class RouterConfig:
    """Router configuration."""

    routing_strategy: RoutingStrategy = RoutingStrategy.LEAST_CONNECTIONS
    enable_lag_monitoring: bool = True
    max_acceptable_lag_seconds: float = 10.0
    health_check_interval_seconds: float = 30.0
    failover_enabled: bool = True
    primary_fallback_enabled: bool = True
    load_balance_writes: bool = False
    enable_query_hints: bool = True
    replica_timeout_seconds: float = 5.0
    primary_timeout_seconds: float = 10.0


class ReplicaRouter:
    """Advanced database read replica routing system."""

    def __init__(
        self,
        primary_pool: asyncpg.Pool,
        replica_pools: List[asyncpg.Pool],
        replica_configs: Optional[List[Dict[str, Any]]] = None,
        config: Optional[RouterConfig] = None,
        alert_manager: Optional[Any] = None,
    ):
        self.primary_pool = primary_pool
        self.replica_pools = replica_pools
        self.config = config or RouterConfig()
        self.alert_manager = alert_manager or get_alert_manager()

        # Replica management
        self.replicas: Dict[str, ReplicaInfo] = {}
        self.healthy_replicas: List[str] = []
        self.round_robin_index = 0

        # Routing metrics
        self.metrics = RoutingMetrics()
        self.query_history: deque[Dict[str, Any]] = deque(maxlen=1000)

        # Health monitoring
        self.health_check_task: Optional[asyncio.Task] = None
        self.lag_monitor_task: Optional[asyncio.Task] = None

        # Query analysis
        self.read_only_patterns = [
            "SELECT",
            "SHOW",
            "DESCRIBE",
            "EXPLAIN",
            "WITH",
            "VALUES",
        ]

        self._lock = asyncio.Lock()

        # Initialize replicas
        self._initialize_replicas(replica_configs or [])

    def _initialize_replicas(self, replica_configs: List[Dict[str, Any]]) -> None:
        """Initialize replica information."""
        for i, pool in enumerate(self.replica_pools):
            config = replica_configs[i] if i < len(replica_configs) else {}

            replica_info = ReplicaInfo(
                replica_id=config.get("id", f"replica_{i}"),
                pool=pool,
                host=config.get("host", "unknown"),
                port=config.get("port", 5432),
                region=config.get("region"),
                weight=config.get("weight", 1.0),
                max_lag_seconds=config.get("max_lag_seconds", 30.0),
            )

            self.replicas[replica_info.replica_id] = replica_info
            self.healthy_replicas.append(replica_info.replica_id)

        logger.info(f"Initialized {len(self.replicas)} read replicas")

    async def execute_query(
        self,
        query: str,
        *args,
        force_primary: bool = False,
        preferred_replica: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Execute query with intelligent routing."""
        start_time = time.time()
        target_pool = None
        query_type = "unknown"

        try:
            # Determine query type and target
            is_read_only = self._is_read_only_query(query)
            query_type = "read" if is_read_only else "write"

            if force_primary or not is_read_only:
                # Route to primary
                target_pool = self.primary_pool
                self.metrics.primary_queries += 1
                logger.debug("Routing query to primary (write or forced)")

            else:
                # Route to replica
                target_pool, replica_id = await self._select_replica(preferred_replica)
                if target_pool:
                    self.metrics.replica_queries += 1
                    logger.debug(f"Routing query to replica: {replica_id}")
                else:
                    # Fallback to primary
                    target_pool = self.primary_pool
                    self.metrics.primary_queries += 1
                    self.metrics.lag_aware_reroutes += 1
                    logger.debug("No healthy replicas available, routing to primary")

            # Execute query
            if timeout:
                result = await target_pool.fetch(query, *args, timeout=timeout)
            else:
                timeout_value = (
                    self.config.replica_timeout_seconds
                    if target_pool != self.primary_pool
                    else self.config.primary_timeout_seconds
                )
                result = await target_pool.fetch(query, *args, timeout=timeout_value)

            # Update metrics
            response_time_ms = (time.time() - start_time) * 1000
            self._update_routing_metrics(
                query_type, target_pool == self.primary_pool, response_time_ms, None
            )

            # Track query history
            self.query_history.append(
                {
                    "query": query[:100],  # Truncate for logging
                    "query_type": query_type,
                    "target": "primary"
                    if target_pool == self.primary_pool
                    else "replica",
                    "replica_id": None
                    if target_pool == self.primary_pool
                    else self._get_replica_id_by_pool(target_pool),
                    "response_time_ms": response_time_ms,
                    "timestamp": time.time(),
                }
            )

            return result

        except Exception as e:
            # Handle routing errors
            response_time_ms = (time.time() - start_time) * 1000
            self._update_routing_metrics(
                query_type, target_pool == self.primary_pool, response_time_ms, str(e)
            )

            # If replica failed, try primary fallback
            if (
                target_pool != self.primary_pool
                and self.config.primary_fallback_enabled
            ):
                logger.warning(f"Replica query failed, retrying on primary: {e}")
                try:
                    result = await self.primary_pool.fetch(
                        query, *args, timeout=self.config.primary_timeout_seconds
                    )
                    self.metrics.failover_events += 1
                    return result
                except Exception as primary_error:
                    logger.error(f"Primary fallback also failed: {primary_error}")

            logger.error(f"Query execution failed: {e}")
            raise

    def _is_read_only_query(self, query: str) -> bool:
        """Determine if query is read-only."""
        query_upper = query.strip().upper()

        # Check for read-only patterns
        for pattern in self.read_only_patterns:
            if query_upper.startswith(pattern):
                return True

        # Check for write operations
        write_patterns = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "DROP",
            "ALTER",
            "TRUNCATE",
        ]
        for pattern in write_patterns:
            if query_upper.startswith(pattern):
                return False

        # Default to read-only for safety
        return True

    async def _select_replica(
        self, preferred_replica: Optional[str] = None
    ) -> Tuple[asyncpg.Pool, str]:
        """Select optimal replica based on routing strategy."""
        async with self._lock:
            # Filter healthy replicas
            available_replicas = [
                replica_id
                for replica_id in self.healthy_replicas
                if self.replicas[replica_id].status == ReplicaStatus.HEALTHY
            ]

            if not available_replicas:
                return None, None

            # Use preferred replica if specified and available
            if preferred_replica and preferred_replica in available_replicas:
                return self.replicas[preferred_replica].pool, preferred_replica

            # Apply routing strategy
            if self.config.routing_strategy == RoutingStrategy.ROUND_ROBIN:
                return self._select_round_robin(available_replicas)
            elif self.config.routing_strategy == RoutingStrategy.LEAST_CONNECTIONS:
                return self._select_least_connections(available_replicas)
            elif self.config.routing_strategy == RoutingStrategy.LAG_AWARE:
                return self._select_lag_aware(available_replicas)
            elif self.config.routing_strategy == RoutingStrategy.WEIGHTED:
                return self._select_weighted(available_replicas)
            elif self.config.routing_strategy == RoutingStrategy.GEOGRAPHIC:
                return self._select_geographic(available_replicas)
            else:  # RANDOM
                return self._select_random(available_replicas)

    def _select_round_robin(
        self, available_replicas: List[str]
    ) -> Tuple[asyncpg.Pool, str]:
        """Select replica using round-robin strategy."""
        replica_id = available_replicas[
            self.round_robin_index % len(available_replicas)
        ]
        self.round_robin_index += 1
        return self.replicas[replica_id].pool, replica_id

    def _select_least_connections(
        self, available_replicas: List[str]
    ) -> Tuple[asyncpg.Pool, str]:
        """Select replica with least connections."""
        best_replica = min(
            available_replicas, key=lambda rid: self.replicas[rid].connection_count
        )
        return self.replicas[best_replica].pool, best_replica

    def _select_lag_aware(
        self, available_replicas: List[str]
    ) -> Tuple[asyncpg.Pool, str]:
        """Select replica based on replication lag."""
        # Filter replicas with acceptable lag
        acceptable_replicas = [
            rid
            for rid in available_replicas
            if self.replicas[rid].current_lag_seconds
            <= self.config.max_acceptable_lag_seconds
        ]

        if not acceptable_replicas:
            # No replicas with acceptable lag, use least lagging
            best_replica = min(
                available_replicas,
                key=lambda rid: self.replicas[rid].current_lag_seconds,
            )
        else:
            # Use replica with lowest lag among acceptable ones
            best_replica = min(
                acceptable_replicas,
                key=lambda rid: self.replicas[rid].current_lag_seconds,
            )

        return self.replicas[best_replica].pool, best_replica

    def _select_weighted(
        self, available_replicas: List[str]
    ) -> Tuple[asyncpg.Pool, str]:
        """Select replica using weighted routing."""
        import random

        # Calculate weights
        total_weight = sum(self.replicas[rid].weight for rid in available_replicas)

        if total_weight == 0:
            return self._select_random(available_replicas)

        # Weighted random selection
        rand = random.random() * total_weight
        current_weight = 0

        for replica_id in available_replicas:
            current_weight += self.replicas[replica_id].weight
            if rand <= current_weight:
                return self.replicas[replica_id].pool, replica_id

        # Fallback to last replica
        last_replica = available_replicas[-1]
        return self.replicas[last_replica].pool, last_replica

    def _select_geographic(
        self, available_replicas: List[str]
    ) -> Tuple[asyncpg.Pool, str]:
        """Select replica based on geographic proximity."""
        # For now, prefer replicas in the same region (simplified)
        # In a real implementation, you'd use client location or IP geolocation

        # Default to first available replica
        first_replica = available_replicas[0]
        return self.replicas[first_replica].pool, first_replica

    def _select_random(self, available_replicas: List[str]) -> Tuple[asyncpg.Pool, str]:
        """Select random replica."""
        import random

        replica_id = random.choice(available_replicas)
        return self.replicas[replica_id].pool, replica_id

    def _get_replica_id_by_pool(self, pool: asyncpg.Pool) -> Optional[str]:
        """Get replica ID by pool reference."""
        for replica_id, replica_info in self.replicas.items():
            if replica_info.pool == pool:
                return replica_id
        return None

    async def check_replica_health(self, replica_id: str) -> Dict[str, Any]:
        """Check health of specific replica."""
        if replica_id not in self.replicas:
            return {"status": "not_found", "issues": ["Replica not configured"]}

        replica_info = self.replicas[replica_id]
        health_status = {"status": "healthy", "issues": [], "metrics": {}}

        try:
            # Test connectivity
            start_time = time.time()
            async with replica_info.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            replica_info.response_time_ms = (time.time() - start_time) * 1000
            health_status["metrics"]["response_time_ms"] = replica_info.response_time_ms

            # Check replication lag
            if self.config.enable_lag_monitoring:
                lag_info = await self._get_replication_lag(conn)
                replica_info.current_lag_seconds = lag_info["lag_seconds"]
                health_status["metrics"]["lag_seconds"] = lag_info["lag_seconds"]

                if lag_info["lag_seconds"] > replica_info.max_lag_seconds:
                    health_status["status"] = "lagging"
                    health_status["issues"].append(
                        f"High replication lag: {lag_info['lag_seconds']:.1f}s"
                    )

            # Check connection count
            replica_info.connection_count = (
                replica_info.pool.get_size() - replica_info.pool.get_idle_size()
            )
            health_status["metrics"]["connection_count"] = replica_info.connection_count

            # Update replica status
            replica_info.status = ReplicaStatus(health_status["status"])
            replica_info.last_health_check = time.time()

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["issues"].append(f"Health check failed: {str(e)}")
            replica_info.status = ReplicaStatus.UNHEALTHY
            replica_info.error_count += 1

        return health_status

    async def _get_replication_lag(self, conn: asyncpg.Connection) -> Dict[str, Any]:
        """Get replication lag information."""
        try:
            lag_info = await conn.fetchrow("""
                SELECT 
                    pg_last_wal_receive_lsn() as receive_lsn,
                    pg_last_wal_replay_lsn() as replay_lsn,
                    pg_last_xact_replay_timestamp() as replay_timestamp,
                    EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) as lag_seconds,
                    pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()) as lag_bytes
            """)

            return {
                "receive_lsn": str(lag_info["receive_lsn"]),
                "replay_lsn": str(lag_info["replay_lsn"]),
                "replay_timestamp": lag_info["replay_timestamp"],
                "lag_seconds": lag_info["lag_seconds"] or 0,
                "lag_bytes": lag_info["lag_bytes"] or 0,
            }

        except Exception as e:
            logger.error(f"Failed to get replication lag: {e}")
            return {"lag_seconds": 0, "lag_bytes": 0, "error": str(e)}

    async def monitor_all_replicas(self) -> Dict[str, Any]:
        """Monitor health of all replicas."""
        monitoring_results = {
            "overall_status": "healthy",
            "replica_status": {},
            "unhealthy_replicas": [],
            "lagging_replicas": [],
            "summary": {},
        }

        healthy_count = 0

        for replica_id in self.replicas:
            health = await self.check_replica_health(replica_id)
            monitoring_results["replica_status"][replica_id] = health

            if health["status"] == "healthy":
                healthy_count += 1
            elif health["status"] == "unhealthy":
                monitoring_results["unhealthy_replicas"].append(replica_id)
                monitoring_results["overall_status"] = "degraded"
            elif health["status"] == "lagging":
                monitoring_results["lagging_replicas"].append(replica_id)
                if monitoring_results["overall_status"] == "healthy":
                    monitoring_results["overall_status"] = "degraded"

        # Update healthy replicas list
        async with self._lock:
            self.healthy_replicas = [
                rid
                for rid, health in monitoring_results["replica_status"].items()
                if health["status"] == "healthy"
            ]

        # Summary statistics
        monitoring_results["summary"] = {
            "total_replicas": len(self.replicas),
            "healthy_replicas": healthy_count,
            "unhealthy_replicas": len(monitoring_results["unhealthy_replicas"]),
            "lagging_replicas": len(monitoring_results["lagging_replicas"]),
            "available_for_routing": len(self.healthy_replicas),
        }

        # Trigger alerts if needed
        await self._check_replica_alerts(monitoring_results)

        return monitoring_results

    async def _check_replica_alerts(self, monitoring_results: Dict[str, Any]) -> None:
        """Check for replica-related alerts."""
        # All replicas unhealthy
        if len(monitoring_results["unhealthy_replicas"]) == len(self.replicas):
            await self.alert_manager.trigger_alert(
                name="all_replicas_unhealthy",
                severity=AlertSeverity.CRITICAL,
                message="All read replicas are unhealthy",
                context={
                    "unhealthy_replicas": monitoring_results["unhealthy_replicas"]
                },
            )

        # Multiple replicas unhealthy
        elif len(monitoring_results["unhealthy_replicas"]) > len(self.replicas) // 2:
            await self.alert_manager.trigger_alert(
                name="multiple_replicas_unhealthy",
                severity=AlertSeverity.ERROR,
                message=f"Multiple replicas unhealthy: {len(monitoring_results['unhealthy_replicas'])}/{len(self.replicas)}",
                context={
                    "unhealthy_replicas": monitoring_results["unhealthy_replicas"]
                },
            )

        # High replication lag
        if len(monitoring_results["lagging_replicas"]) > 0:
            await self.alert_manager.trigger_alert(
                name="replica_lag",
                severity=AlertSeverity.WARNING,
                message=f"Replicas with high lag: {len(monitoring_results['lagging_replicas'])}",
                context={"lagging_replicas": monitoring_results["lagging_replicas"]},
            )

    def _update_routing_metrics(
        self,
        query_type: str,
        used_primary: bool,
        response_time_ms: float,
        error: Optional[str],
    ) -> None:
        """Update routing performance metrics."""
        self.metrics.total_queries += 1

        if error:
            self.metrics.routing_errors += 1

        # Update average response time
        if self.metrics.avg_response_time_ms == 0:
            self.metrics.avg_response_time_ms = response_time_ms
        else:
            self.metrics.avg_response_time_ms = (
                self.metrics.avg_response_time_ms * 0.9
            ) + (response_time_ms * 0.1)

        # Update replica utilization
        if not used_primary:
            for replica_id, replica_info in self.replicas.items():
                if replica_info.status == ReplicaStatus.HEALTHY:
                    utilization = (
                        (replica_info.connection_count / replica_info.pool.get_size())
                        if replica_info.pool.get_size() > 0
                        else 0
                    )
                    self.metrics.replica_utilization[replica_id] = utilization

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get comprehensive routing statistics."""
        stats = {
            "routing_strategy": self.config.routing_strategy.value,
            "total_queries": self.metrics.total_queries,
            "primary_queries": self.metrics.primary_queries,
            "replica_queries": self.metrics.replica_queries,
            "routing_errors": self.metrics.routing_errors,
            "avg_response_time_ms": self.metrics.avg_response_time_ms,
            "lag_aware_reroutes": self.metrics.lag_aware_reroutes,
            "failover_events": self.metrics.failover_events,
            "replica_utilization": self.metrics.replica_utilization,
            "query_distribution": {
                "primary_pct": (
                    self.metrics.primary_queries / max(self.metrics.total_queries, 1)
                )
                * 100,
                "replica_pct": (
                    self.metrics.replica_queries / max(self.metrics.total_queries, 1)
                )
                * 100,
            },
            "replica_details": {},
        }

        # Add replica details
        for replica_id, replica_info in self.replicas.items():
            stats["replica_details"][replica_id] = {
                "status": replica_info.status.value,
                "current_lag_seconds": replica_info.current_lag_seconds,
                "connection_count": replica_info.connection_count,
                "query_count": replica_info.query_count,
                "error_count": replica_info.error_count,
                "response_time_ms": replica_info.response_time_ms,
                "weight": replica_info.weight,
                "region": replica_info.region,
            }

        return stats

    async def update_routing_strategy(self, new_strategy: RoutingStrategy) -> None:
        """Update routing strategy."""
        old_strategy = self.config.routing_strategy
        self.config.routing_strategy = new_strategy

        logger.info(
            f"Routing strategy changed from {old_strategy.value} to {new_strategy.value}"
        )

        # Reset round-robin index if switching away from round-robin
        if old_strategy == RoutingStrategy.ROUND_ROBIN:
            self.round_robin_index = 0

    async def set_replica_weight(self, replica_id: str, weight: float) -> bool:
        """Set weight for specific replica."""
        if replica_id not in self.replicas:
            return False

        self.replicas[replica_id].weight = max(0.0, weight)
        logger.info(f"Updated weight for {replica_id}: {weight}")
        return True

    async def set_replica_maintenance_mode(
        self, replica_id: str, enabled: bool
    ) -> bool:
        """Enable or disable maintenance mode for replica."""
        if replica_id not in self.replicas:
            return False

        replica_info = self.replicas[replica_id]

        if enabled:
            replica_info.status = ReplicaStatus.MAINTENANCE
            # Remove from healthy replicas
            async with self._lock:
                if replica_id in self.healthy_replicas:
                    self.healthy_replicas.remove(replica_id)
        else:
            # Reset to healthy and re-check
            replica_info.status = ReplicaStatus.HEALTHY
            health = await self.check_replica_health(replica_id)
            if health["status"] == "healthy":
                async with self._lock:
                    if replica_id not in self.healthy_replicas:
                        self.healthy_replicas.append(replica_id)

        logger.info(f"Set maintenance mode for {replica_id}: {enabled}")
        return True

    async def start_monitoring(self) -> None:
        """Start background monitoring tasks."""
        # Health check monitoring
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # Lag monitoring (if enabled)
        if self.config.enable_lag_monitoring:
            self.lag_monitor_task = asyncio.create_task(self._lag_monitor_loop())

        logger.info("Started replica router monitoring")

    async def stop_monitoring(self) -> None:
        """Stop background monitoring tasks."""
        if self.health_check_task:
            self.health_check_task.cancel()
            self.health_check_task = None

        if self.lag_monitor_task:
            self.lag_monitor_task.cancel()
            self.lag_monitor_task = None

        logger.info("Stopped replica router monitoring")

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await self.monitor_all_replicas()
                await asyncio.sleep(self.config.health_check_interval_seconds)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.config.health_check_interval_seconds)

    async def _lag_monitor_loop(self) -> None:
        """Background lag monitoring loop."""
        while True:
            try:
                # Update lag for all healthy replicas
                for replica_id in self.healthy_replicas:
                    await self.check_replica_health(replica_id)

                await asyncio.sleep(10)  # Check lag every 10 seconds
            except Exception as e:
                logger.error(f"Lag monitor loop error: {e}")
                await asyncio.sleep(10)


# Global replica router instance
_replica_router: ReplicaRouter | None = None


def get_replica_router() -> ReplicaRouter:
    """Get global replica router instance."""
    global _replica_router
    if _replica_router is None:
        raise RuntimeError(
            "Replica router not initialized. Call init_replica_router() first."
        )
    return _replica_router


async def init_replica_router(
    primary_pool: asyncpg.Pool,
    replica_pools: List[asyncpg.Pool],
    replica_configs: Optional[List[Dict[str, Any]]] = None,
    config: Optional[RouterConfig] = None,
    alert_manager: Optional[Any] = None,
) -> ReplicaRouter:
    """Initialize global replica router."""
    global _replica_router
    _replica_router = ReplicaRouter(
        primary_pool, replica_pools, replica_configs, config, alert_manager
    )
    await _replica_router.start_monitoring()
    return _replica_router
