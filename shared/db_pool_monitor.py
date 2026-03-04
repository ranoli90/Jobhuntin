"""Database connection pool monitoring and tuning utilities.

This addresses recommendation #18: Tune db_pool_min/max based on load testing.

Provides:
- Pool statistics collection
- Automatic pool sizing recommendations
- Connection health monitoring
- Metrics for observability
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shared.logging_config import get_logger
from shared.metrics import gauge, incr

if TYPE_CHECKING:
    import asyncpg

logger = get_logger("sorce.db.pool")


@dataclass
class PoolStats:
    """Statistics about a database connection pool."""

    min_size: int = 0
    max_size: int = 0
    current_size: int = 0
    idle_connections: int = 0
    active_connections: int = 0
    waiting_queries: int = 0
    total_queries: int = 0
    failed_queries: int = 0
    avg_query_time_ms: float = 0.0
    peak_connections: int = 0
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/metrics."""
        return {
            "min_size": self.min_size,
            "max_size": self.max_size,
            "current_size": self.current_size,
            "idle_connections": self.idle_connections,
            "active_connections": self.active_connections,
            "waiting_queries": self.waiting_queries,
            "utilization_pct": (
                (self.active_connections / self.max_size * 100)
                if self.max_size > 0
                else 0
            ),
            "peak_connections": self.peak_connections,
            "total_queries": self.total_queries,
            "failed_queries": self.failed_queries,
            "avg_query_time_ms": self.avg_query_time_ms,
        }


@dataclass
class PoolRecommendation:
    """Recommendations for pool sizing."""

    current_min: int
    current_max: int
    recommended_min: int
    recommended_max: int
    reason: str
    confidence: str  # "low", "medium", "high"

    def __str__(self) -> str:
        """Human-readable recommendation."""
        if (
            self.recommended_min == self.current_min
            and self.recommended_max == self.current_max
        ):
            return f"Pool sizing is optimal (min={self.current_min}, max={self.current_max})"
        return (
            f"Recommend changing pool size from ({self.current_min}, {self.current_max}) "
            f"to ({self.recommended_min}, {self.recommended_max}): {self.reason}"
        )


class PoolMonitor:
    """Monitors database connection pool health and provides tuning recommendations.

    Usage:
        monitor = PoolMonitor(pool)
        stats = await monitor.collect_stats()
        recommendation = monitor.get_recommendation(stats)
    """

    def __init__(
        self,
        pool: asyncpg.Pool,
        name: str = "primary",
        sample_interval_seconds: float = 60.0,
    ) -> None:
        self._pool = pool
        self._name = name
        self._sample_interval = sample_interval_seconds
        self._stats_history: list[PoolStats] = []
        self._max_history = 1440  # 24 hours at 1-minute intervals
        self._query_times: list[float] = []
        self._total_queries = 0
        self._failed_queries = 0
        self._peak_connections = 0

    async def collect_stats(self) -> PoolStats:
        """Collect current pool statistics."""
        try:
            # Get pool internals
            min_size = self._pool._minsize
            max_size = self._pool._maxsize
            current_size = len(self._pool._holders)
            idle = sum(1 for h in self._pool._holders if not h._in_use)
            active = current_size - idle
            waiting = len(self._pool._waiting)

            # Update peak
            if active > self._peak_connections:
                self._peak_connections = active

            # Calculate average query time
            avg_query_time = (
                sum(self._query_times[-100:]) / len(self._query_times[-100:])
                if self._query_times
                else 0.0
            )

            stats = PoolStats(
                min_size=min_size,
                max_size=max_size,
                current_size=current_size,
                idle_connections=idle,
                active_connections=active,
                waiting_queries=waiting,
                total_queries=self._total_queries,
                failed_queries=self._failed_queries,
                avg_query_time_ms=avg_query_time * 1000,
                peak_connections=self._peak_connections,
            )

            # Store in history
            self._stats_history.append(stats)
            if len(self._stats_history) > self._max_history:
                self._stats_history = self._stats_history[-self._max_history :]

            # Emit metrics
            self._emit_metrics(stats)

            return stats

        except Exception as exc:
            logger.error("Failed to collect pool stats: %s", exc)
            return PoolStats()

    def record_query(self, duration_seconds: float, success: bool = True) -> None:
        """Record a query execution for statistics."""
        self._query_times.append(duration_seconds)
        if len(self._query_times) > 1000:
            self._query_times = self._query_times[-1000:]
        self._total_queries += 1
        if not success:
            self._failed_queries += 1

    def _emit_metrics(self, stats: PoolStats) -> None:
        """Emit metrics to the metrics system."""
        gauge(f"db.pool.{self._name}.size", stats.current_size)
        gauge(f"db.pool.{self._name}.idle", stats.idle_connections)
        gauge(f"db.pool.{self._name}.active", stats.active_connections)
        gauge(f"db.pool.{self._name}.waiting", stats.waiting_queries)
        gauge(f"db.pool.{self._name}.utilization_pct", stats.utilization_pct)
        gauge(f"db.pool.{self._name}.peak", stats.peak_connections)

        if stats.waiting_queries > 0:
            incr(f"db.pool.{self._name}.waiting_events")

    def get_recommendation(self, stats: PoolStats | None = None) -> PoolRecommendation:
        """Generate pool sizing recommendation based on collected statistics.

        Uses the following heuristics:
        - If peak utilization > 80%, increase max pool size
        - If average utilization < 20%, decrease pool size
        - If queries are waiting, increase pool size
        - If avg query time is high, pool may be too small or too large
        """
        stats = stats or (self._stats_history[-1] if self._stats_history else PoolStats())

        current_min = stats.min_size
        current_max = stats.max_size

        # Default: no change
        rec_min = current_min
        rec_max = current_max
        reason = "Pool sizing is within acceptable parameters"
        confidence = "medium"

        # Calculate average utilization over recent history
        if len(self._stats_history) >= 10:
            recent = self._stats_history[-10:]
            avg_utilization = sum(
                s.active_connections / s.max_size * 100 if s.max_size > 0 else 0
                for s in recent
            ) / len(recent)
            peak_utilization = max(
                s.active_connections / s.max_size * 100 if s.max_size > 0 else 0
                for s in recent
            )
            avg_waiting = sum(s.waiting_queries for s in recent) / len(recent)
        else:
            avg_utilization = 0
            peak_utilization = 0
            avg_waiting = 0

        # High utilization - need more connections
        if peak_utilization > 80 or avg_waiting > 0:
            rec_max = min(current_max * 2, 50)  # Cap at 50
            rec_min = max(rec_min, current_min + 1)
            reason = f"High utilization (peak={peak_utilization:.0f}%, avg_waiting={avg_waiting:.1f})"
            confidence = "high"

        # Low utilization - can reduce pool
        elif avg_utilization < 20 and peak_utilization < 50:
            rec_max = max(current_max - 2, 5)  # Floor at 5
            rec_min = max(2, rec_max // 3)
            reason = f"Low utilization (avg={avg_utilization:.0f}%, peak={peak_utilization:.0f}%)"
            confidence = "medium"

        # High query time might indicate pool contention
        if stats.avg_query_time_ms > 500:
            if avg_utilization > 50:
                rec_max = min(current_max + 5, 50)
                reason = f"High query time ({stats.avg_query_time_ms:.0f}ms) with high utilization"
                confidence = "medium"

        return PoolRecommendation(
            current_min=current_min,
            current_max=current_max,
            recommended_min=rec_min,
            recommended_max=rec_max,
            reason=reason,
            confidence=confidence,
        )

    async def start_monitoring(self) -> None:
        """Start background monitoring task."""
        while True:
            try:
                stats = await self.collect_stats()
                rec = self.get_recommendation(stats)

                # Log warnings for suboptimal configurations
                if rec.confidence == "high" and (
                    rec.recommended_max != rec.current_max
                    or rec.recommended_min != rec.current_min
                ):
                    logger.warning(
                        "Pool %s sizing recommendation: %s",
                        self._name,
                        rec,
                    )

                # Log periodic stats
                logger.debug(
                    "Pool %s stats: size=%d, idle=%d, active=%d, waiting=%d, peak=%d",
                    self._name,
                    stats.current_size,
                    stats.idle_connections,
                    stats.active_connections,
                    stats.waiting_queries,
                    stats.peak_connections,
                )

            except Exception as exc:
                logger.error("Pool monitoring error: %s", exc)

            await asyncio.sleep(self._sample_interval)

    def get_summary(self) -> dict:
        """Get a summary of pool health over time."""
        if not self._stats_history:
            return {"status": "no_data"}

        recent = self._stats_history[-60:]  # Last hour at 1-min intervals

        avg_active = sum(s.active_connections for s in recent) / len(recent)
        peak_active = max(s.active_connections for s in recent)
        avg_waiting = sum(s.waiting_queries for s in recent) / len(recent)
        max_waiting = max(s.waiting_queries for s in recent)

        # Health score (0-100)
        health_score = 100
        if avg_waiting > 0:
            health_score -= min(50, avg_waiting * 10)
        if peak_active >= recent[0].max_size:
            health_score -= 20
        if self._failed_queries > self._total_queries * 0.01:  # >1% failure rate
            health_score -= 30

        return {
            "status": "healthy" if health_score >= 70 else "degraded",
            "health_score": max(0, health_score),
            "avg_active_connections": round(avg_active, 1),
            "peak_active_connections": peak_active,
            "avg_waiting_queries": round(avg_waiting, 2),
            "max_waiting_queries": max_waiting,
            "total_queries": self._total_queries,
            "failed_queries": self._failed_queries,
            "failure_rate_pct": (
                round(self._failed_queries / self._total_queries * 100, 2)
                if self._total_queries > 0
                else 0
            ),
            "recommendation": str(self.get_recommendation()),
        }


def calculate_optimal_pool_size(
    cpu_cores: int,
    expected_concurrent_users: int,
    avg_query_time_ms: float,
    target_response_time_ms: float = 200,
) -> tuple[int, int]:
    """Calculate optimal pool size based on system parameters.

    Uses the formula from the Universal Scalability Law and PostgreSQL best practices:
    - min_size = max(2, cpu_cores)
    - max_size = connections needed to handle expected load

    Args:
        cpu_cores: Number of CPU cores available
        expected_concurrent_users: Expected number of concurrent users
        avg_query_time_ms: Average query execution time in milliseconds
        target_response_time_ms: Target response time in milliseconds

    Returns:
        Tuple of (min_size, max_size)

    """
    # Minimum pool size should be at least equal to CPU cores
    min_size = max(2, cpu_cores)

    # Calculate how many concurrent queries we can handle
    # Little's Law: L = λW
    # L = average number of items in system
    # λ = arrival rate
    # W = average wait time

    # If we expect N concurrent users with avg query time T,
    # we need approximately N * T / target_time connections
    if target_response_time_ms > 0 and avg_query_time_ms > 0:
        connections_per_user = avg_query_time_ms / target_response_time_ms
        max_size = int(expected_concurrent_users * connections_per_user * 1.5)
    else:
        # Fallback: 10 connections per expected concurrent user
        max_size = expected_concurrent_users * 10

    # Apply bounds
    max_size = max(min_size * 2, min(max_size, 100))

    return min_size, max_size


# Pool monitor instances
_monitors: dict[str, PoolMonitor] = {}


def get_pool_monitor(pool: asyncpg.Pool, name: str = "primary") -> PoolMonitor:
    """Get or create a pool monitor instance."""
    if name not in _monitors:
        _monitors[name] = PoolMonitor(pool, name)
    return _monitors[name]


async def monitor_all_pools() -> None:
    """Start monitoring all registered pools."""
    tasks = [monitor.start_monitoring() for monitor in _monitors.values()]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
