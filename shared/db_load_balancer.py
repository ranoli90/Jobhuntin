"""Advanced database load balancing and traffic distribution system.

Provides:
- Multiple load balancing algorithms
- Health-aware routing
- Performance-based weighting
- Geographic load balancing
- Automatic failover

Usage:
    from shared.db_load_balancer import DatabaseLoadBalancer

    balancer = DatabaseLoadBalancer([pool1, pool2, pool3])
    await balancer.execute_query("SELECT * FROM users")
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import asyncpg

from shared.logging_config import get_logger
from shared.alerting import AlertSeverity, get_alert_manager

logger = get_logger("sorce.db_load_balancer")


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    HASH_BASED = "hash_based"
    GEOGRAPHIC = "geographic"
    ADAPTIVE = "adaptive"


class PoolHealth(Enum):
    """Pool health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


@dataclass
class PoolInfo:
    """Database pool information."""

    pool_id: str
    pool: asyncpg.Pool
    host: str
    port: int
    region: Optional[str] = None
    weight: float = 1.0
    priority: int = 1
    max_connections: int = 100
    health: PoolHealth = PoolHealth.HEALTHY
    last_health_check: float = field(default_factory=time.time)
    response_time_ms: float = 0.0
    connection_count: int = 0
    query_count: int = 0
    error_count: int = 0
    error_rate: float = 0.0
    last_error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class LoadBalancingMetrics:
    """Load balancing performance metrics."""

    total_queries: int = 0
    pool_distribution: Dict[str, int] = field(default_factory=dict)
    response_times: Dict[str, List[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    error_rates: Dict[str, float] = field(default_factory=dict)
    failover_count: int = 0
    rebalance_count: int = 0
    avg_response_time_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class BalancerConfig:
    """Load balancer configuration."""

    strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS
    health_check_interval_seconds: float = 30.0
    health_check_timeout_seconds: float = 5.0
    max_failures_before_removal: int = 3
    recovery_check_interval_seconds: float = 60.0
    enable_adaptive_weighting: bool = True
    enable_geographic_routing: bool = False
    enable_query_affinity: bool = False
    sticky_sessions: bool = False
    session_affinity_timeout: float = 300.0
    weight_adjustment_factor: float = 0.1
    min_weight: float = 0.1
    max_weight: float = 10.0


class DatabaseLoadBalancer:
    """Advanced database load balancing system."""

    def __init__(
        self,
        pools: List[asyncpg.Pool],
        pool_configs: Optional[List[Dict[str, Any]]] = None,
        config: Optional[BalancerConfig] = None,
        alert_manager: Optional[Any] = None,
    ):
        self.pools = pools
        self.config = config or BalancerConfig()
        self.alert_manager = alert_manager or get_alert_manager()

        # Pool management
        self.pool_info: Dict[str, PoolInfo] = {}
        self.healthy_pools: List[str] = []
        self.disabled_pools: List[str] = []

        # Load balancing state
        self.round_robin_index = 0
        self.query_affinity: Dict[str, str] = {}
        self.session_affinity: Dict[str, Tuple[str, float]] = {}

        # Metrics and monitoring
        self.metrics = LoadBalancingMetrics()
        self.response_time_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )

        # Background tasks
        self.health_check_task: Optional[asyncio.Task] = None
        self.adaptive_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        self._lock = asyncio.Lock()

        # Initialize pools
        self._initialize_pools(pool_configs or [])

    def _initialize_pools(self, pool_configs: List[Dict[str, Any]]) -> None:
        """Initialize pool information."""
        for i, pool in enumerate(self.pools):
            config = pool_configs[i] if i < len(pool_configs) else {}

            pool_info = PoolInfo(
                pool_id=config.get("id", f"pool_{i}"),
                pool=pool,
                host=config.get("host", "unknown"),
                port=config.get("port", 5432),
                region=config.get("region"),
                weight=config.get("weight", 1.0),
                priority=config.get("priority", 1),
                max_connections=config.get("max_connections", 100),
            )

            self.pool_info[pool_info.pool_id] = pool_info
            self.healthy_pools.append(pool_info.pool_id)

        logger.info(f"Initialized {len(self.pools)} database pools for load balancing")

    async def execute_query(
        self,
        query: str,
        *args,
        pool_id: Optional[str] = None,
        force_healthy: bool = True,
        timeout: Optional[float] = None,
    ) -> Any:
        """Execute query with load balancing."""
        start_time = time.time()
        selected_pool_id = pool_id
        selected_pool = None
        attempt_count = 0
        max_attempts = len(self.healthy_pools) if not force_healthy else len(self.pools)

        while attempt_count < max_attempts:
            try:
                # Select pool
                if not selected_pool_id:
                    selected_pool_id = await self._select_pool()

                if not selected_pool_id:
                    raise RuntimeError("No available database pools")

                selected_pool = self.pool_info[selected_pool_id].pool

                # Execute query
                if timeout:
                    result = await selected_pool.fetch(query, *args, timeout=timeout)
                else:
                    result = await selected_pool.fetch(query, *args)

                # Update metrics
                response_time_ms = (time.time() - start_time) * 1000
                await self._update_metrics(selected_pool_id, response_time_ms, None)

                return result

            except Exception as e:
                attempt_count += 1
                response_time_ms = (time.time() - start_time) * 1000

                # Update error metrics
                await self._update_metrics(selected_pool_id, response_time_ms, str(e))

                # Handle pool failure
                if selected_pool_id:
                    await self._handle_pool_failure(selected_pool_id, str(e))

                # Try next pool
                selected_pool_id = None

                logger.warning(
                    f"Query failed on pool {selected_pool_id}, trying next pool (attempt {attempt_count}/{max_attempts}): {e}"
                )

        # All pools failed
        error_msg = f"All {max_attempts} database pools failed"
        await self.alert_manager.trigger_alert(
            name="all_pools_failed",
            severity=AlertSeverity.CRITICAL,
            message=error_msg,
            context={
                "attempt_count": attempt_count,
                "pools_available": len(self.pools),
            },
        )

        raise RuntimeError(error_msg)

    async def _select_pool(self) -> Optional[str]:
        """Select optimal pool based on strategy."""
        available_pools = (
            self.healthy_pools if self.healthy_pools else list(self.pool_info.keys())
        )

        if not available_pools:
            return None

        if self.config.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_pools)
        elif self.config.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(available_pools)
        elif self.config.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_weighted_round_robin(available_pools)
        elif self.config.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._select_least_response_time(available_pools)
        elif self.config.strategy == LoadBalancingStrategy.RANDOM:
            return self._select_random(available_pools)
        elif self.config.strategy == LoadBalancingStrategy.HASH_BASED:
            return self._select_hash_based(available_pools)
        elif self.config.strategy == LoadBalancingStrategy.GEOGRAPHIC:
            return self._select_geographic(available_pools)
        elif self.config.strategy == LoadBalancingStrategy.ADAPTIVE:
            return self._select_adaptive(available_pools)
        else:
            return available_pools[0]

    def _select_round_robin(self, available_pools: List[str]) -> str:
        """Select pool using round-robin strategy."""
        pool_id = available_pools[self.round_robin_index % len(available_pools)]
        self.round_robin_index += 1
        return pool_id

    def _select_least_connections(self, available_pools: List[str]) -> str:
        """Select pool with least connections."""
        best_pool_id = None
        min_connections = float("inf")

        for pool_id in available_pools:
            pool_info = self.pool_info[pool_id]
            if pool_info.connection_count < min_connections:
                min_connections = pool_info.connection_count
                best_pool_id = pool_id

        return best_pool_id or available_pools[0]

    def _select_weighted_round_robin(self, available_pools: List[str]) -> str:
        """Select pool using weighted round-robin."""
        total_weight = sum(self.pool_info[pid].weight for pid in available_pools)

        if total_weight == 0:
            return available_pools[0]

        import random

        rand = random.random() * total_weight
        current_weight = 0

        for pool_id in available_pools:
            current_weight += self.pool_info[pool_id].weight
            if rand <= current_weight:
                return pool_id

        return available_pools[-1]

    def _select_least_response_time(self, available_pools: List[str]) -> str:
        """Select pool with least response time."""
        best_pool_id = None
        min_response_time = float("inf")

        for pool_id in available_pools:
            pool_info = self.pool_info[pool_id]

            # Get average response time
            response_times = self.response_time_history[pool_id]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
            else:
                avg_response_time = pool_info.response_time_ms

            if avg_response_time < min_response_time:
                min_response_time = avg_response_time
                best_pool_id = pool_id

        return best_pool_id or available_pools[0]

    def _select_random(self, available_pools: List[str]) -> str:
        """Select random pool."""
        import random

        return random.choice(available_pools)

    def _select_hash_based(self, available_pools: List[str]) -> str:
        """Select pool using hash-based routing."""
        # Simple hash-based selection (would use query/user ID in real implementation)
        import hashlib

        # Use current time as hash input for demo
        hash_input = str(time.time())
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        pool_index = hash_value % len(available_pools)
        return available_pools[pool_index]

    def _select_geographic(self, available_pools: List[str]) -> str:
        """Select pool based on geographic proximity."""
        # For demo, prefer pools in the same region
        # In real implementation, would use client location or request headers

        # Default to first available pool
        return available_pools[0]

    def _select_adaptive(self, available_pools: List[str]) -> str:
        """Select pool using adaptive algorithm."""
        # Combine multiple factors for selection
        scores = {}

        for pool_id in available_pools:
            pool_info = self.pool_info[pool_id]

            # Connection factor (lower is better)
            connection_factor = 1.0 / (pool_info.connection_count + 1)

            # Response time factor (lower is better)
            response_times = self.response_time_history[pool_id]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                response_factor = 1.0 / (avg_response_time + 1)
            else:
                response_factor = 1.0 / (pool_info.response_time_ms + 1)

            # Error rate factor (lower is better)
            error_factor = 1.0 - pool_info.error_rate

            # Weight factor
            weight_factor = pool_info.weight

            # Combined score
            scores[pool_id] = (
                connection_factor * 0.4
                + response_factor * 0.3
                + error_factor * 0.2
                + weight_factor * 0.1
            )

        # Select pool with highest score
        best_pool_id = max(scores.items(), key=lambda x: x[1])[0]
        return best_pool_id

    async def _update_metrics(
        self, pool_id: str, response_time_ms: float, error: Optional[str]
    ) -> None:
        """Update load balancing metrics."""
        pool_info = self.pool_info.get(pool_id)
        if not pool_info:
            return

        # Update pool info
        pool_info.response_time_ms = response_time_ms
        pool_info.query_count += 1

        if error:
            pool_info.error_count += 1
            pool_info.last_error = error

        # Update error rate
        if pool_info.query_count > 0:
            pool_info.error_rate = pool_info.error_count / pool_info.query_count

        # Update global metrics
        self.metrics.total_queries += 1
        self.metrics.pool_distribution[pool_id] = (
            self.metrics.pool_distribution.get(pool_id, 0) + 1
        )
        self.metrics.response_times[pool_id].append(response_time_ms)
        self.metrics.error_rates[pool_id] = pool_info.error_rate

        # Update average response time
        all_response_times = []
        for times in self.metrics.response_times.values():
            all_response_times.extend(times)

        if all_response_times:
            self.metrics.avg_response_time_ms = sum(all_response_times) / len(
                all_response_times
            )

        # Store in history
        self.response_time_history[pool_id].append(response_time_ms)

    async def _handle_pool_failure(self, pool_id: str, error: str) -> None:
        """Handle pool failure."""
        pool_info = self.pool_info.get(pool_id)
        if not pool_info:
            return

        pool_info.last_error = error
        pool_info.health = PoolHealth.UNHEALTHY

        # Remove from healthy pools
        if pool_id in self.healthy_pools:
            self.healthy_pools.remove(pool_id)
            self.disabled_pools.append(pool_id)

        # Increment failure count
        failure_count = self.metrics.pool_distribution.get(pool_id, 0)

        # Remove pool after too many failures
        if failure_count >= self.config.max_failures_before_removal:
            await self._remove_pool(pool_id)
            self.metrics.failover_count += 1

            await self.alert_manager.trigger_alert(
                name="pool_removed",
                severity=AlertSeverity.ERROR,
                message=f"Pool {pool_id} removed due to repeated failures",
                context={
                    "pool_id": pool_id,
                    "failure_count": failure_count,
                    "error": error,
                },
            )

    async def _remove_pool(self, pool_id: str) -> None:
        """Remove pool from load balancer."""
        self.healthy_pools = [pid for pid in self.healthy_pools if pid != pool_id]
        self.disabled_pools = [pid for pid in self.disabled_pools if pid != pool_id]

        logger.warning(f"Removed pool {pool_id} from load balancer")

    async def check_pool_health(self, pool_id: str) -> Dict[str, Any]:
        """Check health of specific pool."""
        pool_info = self.pool_info.get(pool_id)
        if not pool_info:
            return {"status": "not_found", "issues": ["Pool not configured"]}

        health_status = {"status": "healthy", "issues": [], "metrics": {}}

        try:
            start_time = time.time()

            # Test connectivity
            async with pool_info.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            response_time_ms = (time.time() - start_time) * 1000
            pool_info.response_time_ms = response_time_ms
            pool_info.last_health_check = time.time()

            health_status["metrics"]["response_time_ms"] = response_time_ms
            health_status["metrics"]["connection_count"] = pool_info.connection_count
            health_status["metrics"]["query_count"] = pool_info.query_count
            health_status["metrics"]["error_rate"] = pool_info.error_rate

            # Determine health status
            if response_time_ms > 5000:  # 5 seconds
                health_status["status"] = "degraded"
                health_status["issues"].append(
                    f"High response time: {response_time_ms:.1f}ms"
                )
                pool_info.health = PoolHealth.DEGRADED
            elif pool_info.error_rate > 0.1:  # 10% error rate
                health_status["status"] = "degraded"
                health_status["issues"].append(
                    f"High error rate: {pool_info.error_rate:.2%}"
                )
                pool_info.health = PoolHealth.DEGRADED
            else:
                pool_info.health = PoolHealth.HEALTHY

            # Update healthy pools list
            if (
                pool_info.health == PoolHealth.HEALTHY
                and pool_id not in self.healthy_pools
            ):
                if pool_id in self.disabled_pools:
                    self.disabled_pools.remove(pool_id)
                self.healthy_pools.append(pool_id)
                self.metrics.rebalance_count += 1
            elif (
                pool_info.health != PoolHealth.HEALTHY and pool_id in self.healthy_pools
            ):
                self.healthy_pools.remove(pool_id)
                if pool_id not in self.disabled_pools:
                    self.disabled_pools.append(pool_id)

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["issues"].append(f"Health check failed: {str(e)}")
            pool_info.health = PoolHealth.UNHEALTHY
            pool_info.last_error = str(e)

            # Remove from healthy pools
            if pool_id in self.healthy_pools:
                self.healthy_pools.remove(pool_id)
                if pool_id not in self.disabled_pools:
                    self.disabled_pools.append(pool_id)

        return health_status

    async def check_all_pools_health(self) -> Dict[str, Any]:
        """Check health of all pools."""
        health_results = {
            "overall_status": "healthy",
            "pool_status": {},
            "healthy_pools": len(self.healthy_pools),
            "unhealthy_pools": len(self.disabled_pools),
            "total_pools": len(self.pools),
        }

        healthy_count = 0

        for pool_id in self.pool_info:
            health = await self.check_pool_health(pool_id)
            health_results["pool_status"][pool_id] = health

            if health["status"] == "healthy":
                healthy_count += 1
            elif health["status"] == "unhealthy":
                health_results["overall_status"] = "degraded"
            elif (
                health["status"] == "degraded"
                and health_results["overall_status"] == "healthy"
            ):
                health_results["overall_status"] = "degraded"

        # Update counts
        health_results["healthy_pools"] = healthy_count
        health_results["unhealthy_pools"] = len(self.pools) - healthy_count

        return health_results

    async def update_weights(self, weight_adjustments: Dict[str, float]) -> int:
        """Update pool weights for adaptive load balancing."""
        updated_count = 0

        for pool_id, adjustment in weight_adjustments.items():
            if pool_id in self.pool_info:
                pool_info = self.pool_info[pool_id]
                old_weight = pool_info.weight

                # Apply adjustment with bounds
                new_weight = max(
                    self.config.min_weight,
                    min(self.config.max_weight, old_weight + adjustment),
                )

                pool_info.weight = new_weight
                updated_count += 1

                logger.info(
                    f"Updated weight for {pool_id}: {old_weight} -> {new_weight}"
                )

        return updated_count

    async def start_monitoring(self) -> None:
        """Start background monitoring tasks."""
        # Health check monitoring
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # Adaptive weight adjustment
        if self.config.enable_adaptive_weighting:
            self.adaptive_task = asyncio.create_task(self._adaptive_weight_loop())

        # Cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("Started load balancer monitoring")

    async def stop_monitoring(self) -> None:
        """Stop background monitoring tasks."""
        if self.health_check_task:
            self.health_check_task.cancel()
            self.health_check_task = None

        if self.adaptive_task:
            self.adaptive_task.cancel()
            self.adaptive_task = None

        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None

        logger.info("Stopped load balancer monitoring")

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await self.check_all_pools_health()
                await asyncio.sleep(self.config.health_check_interval_seconds)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.config.health_check_interval_seconds)

    async def _adaptive_weight_loop(self) -> None:
        """Background adaptive weight adjustment loop."""
        while True:
            try:
                await self._adjust_weights_adaptively()
                await asyncio.sleep(60)  # Adjust every minute
            except Exception as e:
                logger.error(f"Adaptive weight loop error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await self._cleanup_old_metrics()
                await self._cleanup_old_affinity()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)

    async def _adjust_weights_adaptively(self) -> None:
        """Adjust weights based on performance."""
        if not self.config.enable_adaptive_weighting:
            return

        weight_adjustments = {}

        for pool_id, pool_info in self.pool_info.items():
            # Calculate performance score
            response_times = self.response_time_history[pool_id]
            if not response_times:
                continue

            avg_response_time = sum(response_times) / len(response_times)
            error_rate = pool_info.error_rate

            # Lower response time and error rate = higher weight
            performance_score = (1.0 / (avg_response_time + 1)) * (1.0 - error_rate)

            # Calculate adjustment
            avg_score = sum(
                (
                    1.0
                    / (
                        sum(self.response_time_history[pid])
                        / len(self.response_time_history[pid])
                        + 1
                    )
                )
                * (1.0 - self.pool_info[pid].error_rate)
                for pid in self.pool_info.keys()
                if self.response_time_history[pid]
            )

            if avg_score > 0:
                adjustment = (
                    performance_score / avg_score - 1.0
                ) * self.config.weight_adjustment_factor
                weight_adjustments[pool_id] = adjustment

        if weight_adjustments:
            await self.update_weights(weight_adjustments)

    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics data."""
        cutoff_time = time.time() - 3600  # Keep 1 hour

        for pool_id in self.response_time_history:
            # Remove old response times
            while (
                self.response_time_history[pool_id]
                and self.response_time_history[pool_id][0] < cutoff_time
            ):
                self.response_time_history[pool_id].popleft()

    async def _cleanup_old_affinity(self) -> None:
        """Clean up old affinity data."""
        current_time = time.time()

        # Clean up session affinity
        expired_sessions = [
            session_id
            for session_id, (_, timestamp) in self.session_affinity.items()
            if current_time - timestamp > self.config.session_affinity_timeout
        ]

        for session_id in expired_sessions:
            del self.session_affinity[session_id]

    def get_load_balancing_stats(self) -> Dict[str, Any]:
        """Get comprehensive load balancing statistics."""
        stats = {
            "strategy": self.config.strategy.value,
            "total_queries": self.metrics.total_queries,
            "avg_response_time_ms": self.metrics.avg_response_time_ms,
            "failover_count": self.metrics.failover_count,
            "rebalance_count": self.metrics.rebalance_count,
            "healthy_pools": len(self.healthy_pools),
            "disabled_pools": len(self.disabled_pools),
            "total_pools": len(self.pools),
            "pool_distribution": dict(self.metrics.pool_distribution),
            "pool_details": {},
        }

        # Add pool details
        for pool_id, pool_info in self.pool_info.items():
            stats["pool_details"][pool_id] = {
                "host": pool_info.host,
                "port": pool_info.port,
                "region": pool_info.region,
                "weight": pool_info.weight,
                "priority": pool_info.priority,
                "health": pool_info.health.value,
                "response_time_ms": pool_info.response_time_ms,
                "connection_count": pool_info.connection_count,
                "query_count": pool_info.query_count,
                "error_count": pool_info.error_count,
                "error_rate": pool_info.error_rate,
                "last_health_check": pool_info.last_health_check,
                "last_error": pool_info.last_error,
            }

        return stats

    def update_strategy(self, new_strategy: LoadBalancingStrategy) -> None:
        """Update load balancing strategy."""
        old_strategy = self.config.strategy
        self.config.strategy = new_strategy

        # Reset round-robin index if switching away from round-robin
        if old_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            self.round_robin_index = 0

        logger.info(
            f"Load balancing strategy changed from {old_strategy.value} to {new_strategy.value}"
        )

    def set_pool_weight(self, pool_id: str, weight: float) -> bool:
        """Set weight for specific pool."""
        if pool_id not in self.pool_info:
            return False

        self.pool_info[pool_id].weight = max(
            self.config.min_weight, min(self.config.max_weight, weight)
        )
        logger.info(f"Set weight for {pool_id}: {weight}")
        return True

    def enable_pool(self, pool_id: str) -> bool:
        """Enable disabled pool."""
        if pool_id in self.disabled_pools and pool_id in self.pool_info:
            self.disabled_pools.remove(pool_id)

            # Check if pool is healthy
            if self.pool_info[pool_id].health == PoolHealth.HEALTHY:
                self.healthy_pools.append(pool_id)

            logger.info(f"Enabled pool: {pool_id}")
            return True

        return False

    def disable_pool(self, pool_id: str) -> bool:
        """Disable pool."""
        if pool_id in self.healthy_pools:
            self.healthy_pools.remove(pool_id)

        if pool_id not in self.disabled_pools and pool_id in self.pool_info:
            self.disabled_pools.append(pool_id)
            logger.info(f"Disabled pool: {pool_id}")
            return True

        return False


# Global load balancer instance
_load_balancer: DatabaseLoadBalancer | None = None


def get_load_balancer() -> DatabaseLoadBalancer:
    """Get global load balancer instance."""
    global _load_balancer
    if _load_balancer is None:
        raise RuntimeError(
            "Load balancer not initialized. Call init_load_balancer() first."
        )
    return _load_balancer


async def init_load_balancer(
    pools: List[asyncpg.Pool],
    pool_configs: Optional[List[Dict[str, Any]]] = None,
    config: Optional[BalancerConfig] = None,
    alert_manager: Optional[Any] = None,
) -> DatabaseLoadBalancer:
    """Initialize global load balancer."""
    global _load_balancer
    _load_balancer = DatabaseLoadBalancer(pools, pool_configs, config, alert_manager)
    await _load_balancer.start_monitoring()
    return _load_balancer
