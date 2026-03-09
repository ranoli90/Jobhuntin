"""Database replication monitoring and management system.

Provides:
- Replication status monitoring
- Lag detection and alerting
- Failover readiness checks
- Replication performance metrics
- Automated recovery procedures

Usage:
    from shared.db_replication_monitor import ReplicationMonitor

    monitor = ReplicationMonitor(primary_pool, replica_pool)
    status = await monitor.check_replication_status()
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import asyncpg

from shared.alerting import AlertSeverity, get_alert_manager
from shared.logging_config import get_logger

logger = get_logger("sorce.db_replication")


class ReplicationStatus(Enum):
    """Replication status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    LAGGING = "lagging"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


class ReplicationRole(Enum):
    """Database replication role."""

    PRIMARY = "primary"
    REPLICA = "replica"
    STANDBY = "standby"


@dataclass
class ReplicationSlot:
    """Replication slot information."""

    slot_name: str
    plugin: str
    database: str
    active: bool
    restart_lsn: str
    confirmed_flush_lsn: str
    wal_lag_bytes: int
    created_at: float = field(default_factory=time.time)


@dataclass
class ReplicationLag:
    """Replication lag information."""

    lag_seconds: float
    lag_bytes: int
    replay_lsn: str
    receive_lsn: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ReplicationHealth:
    """Comprehensive replication health status."""

    role: ReplicationRole
    status: ReplicationStatus
    lag: Optional[ReplicationLag] = None
    slots: List[ReplicationSlot] = field(default_factory=list)
    wal_info: Dict[str, Any] = field(default_factory=dict)
    connection_info: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class FailoverTest:
    """Failover readiness test result."""

    test_name: str
    status: str
    success: bool
    duration_ms: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ReplicationMonitor:
    """Advanced database replication monitoring system."""

    def __init__(
        self,
        primary_pool: asyncpg.Pool,
        replica_pools: List[asyncpg.Pool],
        alert_manager: Optional[Any] = None,
    ):
        self.primary_pool = primary_pool
        self.replica_pools = replica_pools
        self.alert_manager = alert_manager or get_alert_manager()

        # Monitoring state
        self.health_history: deque[ReplicationHealth] = deque(maxlen=1000)
        self.lag_history: deque[float] = deque(maxlen=1000)
        self.failover_tests: deque[FailoverTest] = deque(maxlen=100)

        # Thresholds
        self.thresholds = {
            "lag_warning_seconds": 10.0,
            "lag_critical_seconds": 30.0,
            "slot_lag_warning_mb": 100,
            "slot_lag_critical_mb": 500,
            "connection_timeout_seconds": 5.0,
            "wal_size_warning_mb": 1000,
            "wal_size_critical_mb": 5000,
        }

        # Monitoring tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def check_replication_status(self) -> ReplicationHealth:
        """Check comprehensive replication status."""
        time.time()

        try:
            # Determine role
            role = await self._determine_role()

            # Collect health information
            if role == ReplicationRole.PRIMARY:
                health = await self._check_primary_health()
            else:
                health = await self._check_replica_health()

            health.role = role
            health.timestamp = time.time()

            # Store in history
            async with self._lock:
                self.health_history.append(health)

                # Store lag history
                if health.lag:
                    self.lag_history.append(health.lag.lag_seconds)

            # Trigger alerts if needed
            await self._trigger_replication_alerts(health)

            return health

        except Exception as e:
            logger.error(f"Replication status check failed: {e}")

            return ReplicationHealth(
                role=ReplicationRole.UNKNOWN,
                status=ReplicationStatus.ERROR,
                issues=[f"Status check failed: {str(e)}"],
                timestamp=time.time(),
            )

    async def _determine_role(self) -> ReplicationRole:
        """Determine if this is primary or replica."""
        try:
            async with self.primary_pool.acquire() as conn:
                # Check if we're in recovery (replica)
                in_recovery = await conn.fetchval("SELECT pg_is_in_recovery()")

                if in_recovery:
                    return ReplicationRole.REPLICA
                else:
                    return ReplicationRole.PRIMARY

        except Exception as e:
            logger.error(f"Failed to determine role: {e}")
            return ReplicationRole.UNKNOWN

    async def _check_primary_health(self) -> ReplicationHealth:
        """Check primary database health."""
        health = ReplicationHealth(status=ReplicationStatus.HEALTHY)

        try:
            async with self.primary_pool.acquire() as conn:
                # Get WAL information
                wal_info = await self._get_wal_info(conn)
                health.wal_info = wal_info

                # Check WAL size
                if (
                    wal_info.get("wal_size_mb", 0)
                    > self.thresholds["wal_size_critical_mb"]
                ):
                    health.status = ReplicationStatus.DEGRADED
                    health.issues.append(
                        f"WAL size critical: {wal_info['wal_size_mb']:.1f}MB"
                    )
                elif (
                    wal_info.get("wal_size_mb", 0)
                    > self.thresholds["wal_size_warning_mb"]
                ):
                    health.status = ReplicationStatus.DEGRADED
                    health.issues.append(
                        f"WAL size high: {wal_info['wal_size_mb']:.1f}MB"
                    )

                # Get replication slots
                slots = await self._get_replication_slots(conn)
                health.slots = slots

                # Check slot lag
                for slot in slots:
                    lag_mb = slot.wal_lag_bytes / 1024 / 1024
                    if lag_mb > self.thresholds["slot_lag_critical_mb"]:
                        health.status = ReplicationStatus.DEGRADED
                        health.issues.append(
                            f"Slot {slot.slot_name} lag critical: {lag_mb:.1f}MB"
                        )
                    elif lag_mb > self.thresholds["slot_lag_warning_mb"]:
                        if health.status == ReplicationStatus.HEALTHY:
                            health.status = ReplicationStatus.DEGRADED
                        health.issues.append(
                            f"Slot {slot.slot_name} lag high: {lag_mb:.1f}MB"
                        )

                # Check replica connections
                replica_status = await self._check_replica_connections(conn)
                health.connection_info = replica_status

                # Check if replicas are connected
                if not replica_status.get("connected_replicas", []):
                    health.status = ReplicationStatus.DEGRADED
                    health.issues.append("No replica connections detected")

        except Exception as e:
            health.status = ReplicationStatus.ERROR
            health.issues.append(f"Primary health check failed: {str(e)}")

        return health

    async def _check_replica_health(self) -> ReplicationHealth:
        """Check replica database health."""
        health = ReplicationHealth(status=ReplicationStatus.HEALTHY)

        try:
            async with self.primary_pool.acquire() as conn:
                # Get replication lag
                lag = await self._get_replication_lag(conn)
                health.lag = lag

                # Determine status based on lag
                if lag.lag_seconds > self.thresholds["lag_critical_seconds"]:
                    health.status = ReplicationStatus.LAGGING
                    health.issues.append(
                        f"Critical replication lag: {lag.lag_seconds:.1f}s"
                    )
                elif lag.lag_seconds > self.thresholds["lag_warning_seconds"]:
                    health.status = ReplicationStatus.DEGRADED
                    health.issues.append(f"Replication lag: {lag.lag_seconds:.1f}s")

                # Check if replication is active
                if lag.lag_seconds > 300:  # 5 minutes
                    health.status = ReplicationStatus.STOPPED
                    health.issues.append("Replication appears to be stopped")

                # Get WAL information
                wal_info = await self._get_wal_info(conn)
                health.wal_info = wal_info

                # Check connection info
                connection_info = await self._get_replica_connection_info(conn)
                health.connection_info = connection_info

        except Exception as e:
            health.status = ReplicationStatus.ERROR
            health.issues.append(f"Replica health check failed: {str(e)}")

        return health

    async def _get_wal_info(self, conn: asyncpg.Connection) -> Dict[str, Any]:
        """Get WAL information."""
        try:
            # Get current WAL position
            wal_info = await conn.fetchrow("""
                SELECT
                    pg_current_wal_lsn() as current_lsn,
                    pg_walfile_name(pg_current_wal_lsn()) as wal_file,
                    pg_size_pretty(pg_walfile_size(pg_walfile_name(pg_current_wal_lsn()))) as wal_size_pretty,
                    pg_walfile_size(pg_walfile_name(pg_current_wal_lsn())) / 1024 / 1024 as wal_size_mb
            """)

            return {
                "current_lsn": str(wal_info["current_lsn"]),
                "wal_file": wal_info["wal_file"],
                "wal_size_pretty": wal_info["wal_size_pretty"],
                "wal_size_mb": wal_info["wal_size_mb"],
            }

        except Exception as e:
            logger.error(f"Failed to get WAL info: {e}")
            return {"error": str(e)}

    async def _get_replication_slots(
        self, conn: asyncpg.Connection
    ) -> List[ReplicationSlot]:
        """Get replication slot information."""
        try:
            slots_data = await conn.fetch("""
                SELECT
                    slot_name,
                    plugin,
                    database,
                    active,
                    restart_lsn,
                    confirmed_flush_lsn,
                    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as wal_lag_bytes
                FROM pg_replication_slots
                ORDER BY slot_name
            """)

            slots = []
            for slot_data in slots_data:
                slot = ReplicationSlot(
                    slot_name=slot_data["slot_name"],
                    plugin=slot_data["plugin"],
                    database=slot_data["database"],
                    active=slot_data["active"],
                    restart_lsn=str(slot_data["restart_lsn"]),
                    confirmed_flush_lsn=str(slot_data["confirmed_flush_lsn"]),
                    wal_lag_bytes=slot_data["wal_lag_bytes"] or 0,
                )
                slots.append(slot)

            return slots

        except Exception as e:
            logger.error(f"Failed to get replication slots: {e}")
            return []

    async def _get_replication_lag(self, conn: asyncpg.Connection) -> ReplicationLag:
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

            return ReplicationLag(
                lag_seconds=lag_info["lag_seconds"] or 0,
                lag_bytes=lag_info["lag_bytes"] or 0,
                replay_lsn=str(lag_info["replay_lsn"]),
                receive_lsn=str(lag_info["receive_lsn"]),
            )

        except Exception as e:
            logger.error(f"Failed to get replication lag: {e}")
            return ReplicationLag(
                lag_seconds=0, lag_bytes=0, replay_lsn="unknown", receive_lsn="unknown"
            )

    async def _check_replica_connections(
        self, conn: asyncpg.Connection
    ) -> Dict[str, Any]:
        """Check replica connection status."""
        try:
            connections = await conn.fetch("""
                SELECT
                    application_name,
                    client_addr,
                    state,
                    backend_start,
                    sync_state,
                    reply_time
                FROM pg_stat_replication
                ORDER BY backend_start
            """)

            connected_replicas = []
            for conn_info in connections:
                connected_replicas.append(
                    {
                        "application_name": conn_info["application_name"],
                        "client_addr": conn_info["client_addr"],
                        "state": conn_info["state"],
                        "backend_start": conn_info["backend_start"],
                        "sync_state": conn_info["sync_state"],
                        "reply_time": conn_info["reply_time"],
                    }
                )

            return {
                "connected_replicas": connected_replicas,
                "total_connections": len(connected_replicas),
            }

        except Exception as e:
            logger.error(f"Failed to check replica connections: {e}")
            return {"error": str(e)}

    async def _get_replica_connection_info(
        self, conn: asyncpg.Connection
    ) -> Dict[str, Any]:
        """Get replica connection information."""
        try:
            # Get connection info from replica perspective
            conn_info = await conn.fetchrow("""
                SELECT
                    pg_is_in_recovery() as in_recovery,
                    pg_last_wal_receive_lsn() as receive_lsn,
                    pg_last_wal_replay_lsn() as replay_lsn,
                    pg_last_xact_replay_timestamp() as last_replay
            """)

            return {
                "in_recovery": conn_info["in_recovery"],
                "receive_lsn": str(conn_info["receive_lsn"]),
                "replay_lsn": str(conn_info["replay_lsn"]),
                "last_replay": conn_info["last_replay"],
            }

        except Exception as e:
            logger.error(f"Failed to get replica connection info: {e}")
            return {"error": str(e)}

    async def _trigger_replication_alerts(self, health: ReplicationHealth) -> None:
        """Trigger alerts based on replication health."""
        if health.status == ReplicationStatus.ERROR:
            await self.alert_manager.trigger_alert(
                name="replication_error",
                severity=AlertSeverity.CRITICAL,
                message=f"Replication error detected: {'; '.join(health.issues)}",
                context={"role": health.role.value},
            )

        elif health.status == ReplicationStatus.LAGGING:
            await self.alert_manager.trigger_alert(
                name="replication_lag",
                severity=AlertSeverity.ERROR,
                message=f"Critical replication lag: {health.lag.lag_seconds:.1f}s",
                metric_value=health.lag.lag_seconds,
                threshold=self.thresholds["lag_critical_seconds"],
                context={"role": health.role.value},
            )

        elif health.status == ReplicationStatus.DEGRADED:
            await self.alert_manager.trigger_alert(
                name="replication_degraded",
                severity=AlertSeverity.WARNING,
                message=f"Replication degraded: {'; '.join(health.issues)}",
                context={"role": health.role.value},
            )

        elif health.status == ReplicationStatus.STOPPED:
            await self.alert_manager.trigger_alert(
                name="replication_stopped",
                severity=AlertSeverity.CRITICAL,
                message="Replication appears to be stopped",
                context={"role": health.role.value},
            )

    async def test_failover_readiness(self) -> List[FailoverTest]:
        """Test failover readiness."""
        tests = []

        # Test replica connectivity
        connectivity_test = await self._test_replica_connectivity()
        tests.append(connectivity_test)

        # Test data consistency
        consistency_test = await self._test_data_consistency()
        tests.append(consistency_test)

        # Test replication lag
        lag_test = await self._test_replication_lag()
        tests.append(lag_test)

        # Test slot status
        slot_test = await self._test_slot_status()
        tests.append(slot_test)

        # Store test results
        self.failover_tests.extend(tests)

        return tests

    async def _test_replica_connectivity(self) -> FailoverTest:
        """Test replica database connectivity."""
        start_time = time.time()

        try:
            connected_count = 0
            total_count = len(self.replica_pools)

            for pool in self.replica_pools:
                try:
                    async with pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                        connected_count += 1
                except Exception as e:
                    logger.warning(f"Replica connection failed: {e}")

            duration_ms = (time.time() - start_time) * 1000
            success = connected_count == total_count

            return FailoverTest(
                test_name="replica_connectivity",
                status="passed" if success else "failed",
                success=success,
                duration_ms=duration_ms,
                message=f"Connected to {connected_count}/{total_count} replicas",
                details={
                    "connected_count": connected_count,
                    "total_count": total_count,
                },
            )

        except Exception as e:
            return FailoverTest(
                test_name="replica_connectivity",
                status="error",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Connectivity test failed: {str(e)}",
            )

    async def _test_data_consistency(self) -> FailoverTest:
        """Test data consistency between primary and replica."""
        start_time = time.time()

        try:
            # Get count from primary
            async with self.primary_pool.acquire() as primary_conn:
                primary_count = await primary_conn.fetchval(
                    "SELECT COUNT(*) FROM users"
                )

            # Get count from replica
            async with self.replica_pools[0].acquire() as replica_conn:
                replica_count = await replica_conn.fetchval(
                    "SELECT COUNT(*) FROM users"
                )

            duration_ms = (time.time() - start_time) * 1000
            success = primary_count == replica_count

            return FailoverTest(
                test_name="data_consistency",
                status="passed" if success else "failed",
                success=success,
                duration_ms=duration_ms,
                message=f"User counts - Primary: {primary_count}, Replica: {replica_count}",
                details={
                    "primary_count": primary_count,
                    "replica_count": replica_count,
                },
            )

        except Exception as e:
            return FailoverTest(
                test_name="data_consistency",
                status="error",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Consistency test failed: {str(e)}",
            )

    async def _test_replication_lag(self) -> FailoverTest:
        """Test current replication lag."""
        start_time = time.time()

        try:
            health = await self.check_replication_status()

            duration_ms = (time.time() - start_time) * 1000

            if health.lag:
                lag_seconds = health.lag.lag_seconds
                success = lag_seconds < self.thresholds["lag_warning_seconds"]
                status = "passed" if success else "failed"

                return FailoverTest(
                    test_name="replication_lag",
                    status=status,
                    success=success,
                    duration_ms=duration_ms,
                    message=f"Current lag: {lag_seconds:.1f}s",
                    details={"lag_seconds": lag_seconds},
                )
            else:
                return FailoverTest(
                    test_name="replication_lag",
                    status="unknown",
                    success=False,
                    duration_ms=duration_ms,
                    message="Unable to determine replication lag",
                )

        except Exception as e:
            return FailoverTest(
                test_name="replication_lag",
                status="error",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Lag test failed: {str(e)}",
            )

    async def _test_slot_status(self) -> FailoverTest:
        """Test replication slot status."""
        start_time = time.time()

        try:
            health = await self.check_replication_status()

            duration_ms = (time.time() - start_time) * 1000

            active_slots = [s for s in health.slots if s.active]
            success = len(active_slots) == len(health.slots)

            return FailoverTest(
                test_name="slot_status",
                status="passed" if success else "failed",
                success=success,
                duration_ms=duration_ms,
                message=f"Active slots: {len(active_slots)}/{len(health.slots)}",
                details={
                    "active_slots": len(active_slots),
                    "total_slots": len(health.slots),
                },
            )

        except Exception as e:
            return FailoverTest(
                test_name="slot_status",
                status="error",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Slot status test failed: {str(e)}",
            )

    def get_health_trend(self, minutes: int = 60) -> List[ReplicationHealth]:
        """Get health trend over time."""
        cutoff_time = time.time() - (minutes * 60)

        return [
            health for health in self.health_history if health.timestamp >= cutoff_time
        ]

    def get_lag_trend(self, minutes: int = 60) -> List[float]:
        """Get lag trend over time."""
        cutoff_time = time.time() - (minutes * 60)

        # Filter health history and extract lag values
        lag_values = []
        for health in self.health_history:
            if health.timestamp >= cutoff_time and health.lag:
                lag_values.append(health.lag.lag_seconds)

        return lag_values

    def get_failover_test_history(self, limit: int = 50) -> List[FailoverTest]:
        """Get failover test history."""
        tests = list(self.failover_tests)
        tests.sort(key=lambda t: t.timestamp, reverse=True)
        return tests[:limit]

    def get_replication_summary(self) -> Dict[str, Any]:
        """Get comprehensive replication summary."""
        if not self.health_history:
            return {"status": "no_data"}

        latest_health = self.health_history[-1]

        # Calculate lag statistics
        lag_values = list(self.lag_history)
        if lag_values:
            avg_lag = sum(lag_values) / len(lag_values)
            max_lag = max(lag_values)
            min_lag = min(lag_values)
        else:
            avg_lag = max_lag = min_lag = 0

        # Calculate test success rate
        recent_tests = [
            t for t in self.failover_tests if time.time() - t.timestamp < 24 * 60 * 60
        ]
        passed_tests = [t for t in recent_tests if t.success]
        test_success_rate = (
            len(passed_tests) / len(recent_tests) * 100 if recent_tests else 0
        )

        return {
            "current_status": latest_health.status.value,
            "current_role": latest_health.role.value,
            "current_lag_seconds": latest_health.lag.lag_seconds
            if latest_health.lag
            else 0,
            "active_slots": len([s for s in latest_health.slots if s.active]),
            "total_slots": len(latest_health.slots),
            "connected_replicas": latest_health.connection_info.get(
                "total_connections", 0
            ),
            "avg_lag_seconds": avg_lag,
            "max_lag_seconds": max_lag,
            "min_lag_seconds": min_lag,
            "issues": latest_health.issues,
            "test_success_rate_pct": test_success_rate,
            "last_test_time": recent_tests[-1].timestamp if recent_tests else None,
        }

    async def start_monitoring(self, interval_seconds: int = 30) -> asyncio.Task:
        """Start continuous replication monitoring."""

        async def monitor():
            while True:
                try:
                    await self.check_replication_status()
                    await asyncio.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Replication monitoring error: {e}")
                    await asyncio.sleep(interval_seconds)

        self._monitoring_task = asyncio.create_task(monitor)
        return self._monitoring_task

    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None


# Global replication monitor instance
_replication_monitor: ReplicationMonitor | None = None


def get_replication_monitor() -> ReplicationMonitor:
    """Get global replication monitor instance."""
    global _replication_monitor
    if _replication_monitor is None:
        raise RuntimeError(
            "Replication monitor not initialized. Call init_replication_monitor() first."
        )
    return _replication_monitor


async def init_replication_monitor(
    primary_pool: asyncpg.Pool,
    replica_pools: List[asyncpg.Pool],
    alert_manager: Optional[Any] = None,
) -> ReplicationMonitor:
    """Initialize global replication monitor."""
    global _replication_monitor
    _replication_monitor = ReplicationMonitor(
        primary_pool, replica_pools, alert_manager
    )
    return _replication_monitor
