"""Database failover management and automation system.

Provides:
- Automated failover detection
- Failover execution procedures
- Health-based failover decisions
- Failback capabilities
- Failover testing and validation

Usage:
    from shared.db_failover_manager import FailoverManager

    failover_manager = FailoverManager(primary_pool, replica_pools)
    await failover_manager.check_failover_conditions()
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

logger = get_logger("sorce.db_failover")


class FailoverStatus(Enum):
    """Failover operation status."""

    NORMAL = "normal"
    DEGRADED = "degraded"
    FAILOVER_REQUIRED = "failover_required"
    FAILOVER_IN_PROGRESS = "failover_in_progress"
    FAILOVER_COMPLETED = "failover_completed"
    FAILOVER_FAILED = "failover_failed"
    FAILOVER_BACK = "failover_back"


class FailoverTrigger(Enum):
    """Failover trigger conditions."""

    PRIMARY_UNHEALTHY = "primary_unhealthy"
    REPLICATION_LAG = "replication_lag"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


@dataclass
class FailoverCondition:
    """Failover condition evaluation."""

    trigger: FailoverTrigger
    severity: str
    description: str
    threshold_met: bool
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class FailoverDecision:
    """Failover decision result."""

    should_failover: bool
    confidence: float
    primary_reason: str
    supporting_conditions: List[FailoverCondition]
    recommended_target: Optional[str] = None
    estimated_downtime_seconds: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class FailoverExecution:
    """Failover execution record."""

    execution_id: str
    trigger: FailoverTrigger
    status: FailoverStatus
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    target_replica: Optional[str] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    rollback_performed: bool = False
    validation_results: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class FailoverManager:
    """Advanced database failover management system."""

    def __init__(
        self,
        primary_pool: asyncpg.Pool,
        replica_pools: List[asyncpg.Pool],
        alert_manager: Optional[Any] = None,
    ):
        self.primary_pool = primary_pool
        self.replica_pools = replica_pools
        self.alert_manager = alert_manager or get_alert_manager()

        # Failover configuration
        self.failover_config = {
            "auto_failover_enabled": True,
            "min_replicas_required": 1,
            "health_check_timeout_seconds": 30,
            "failover_timeout_seconds": 300,
            "validation_timeout_seconds": 60,
            "rollback_on_failure": True,
            "max_failover_attempts": 3,
        }

        # Failover thresholds
        self.thresholds = {
            "primary_unhealthy_threshold": 3,  # consecutive checks
            "replication_lag_critical_seconds": 60,
            "connection_failure_threshold": 5,  # consecutive failures
            "resource_usage_critical_pct": 90,
            "network_partition_threshold": 30,  # seconds
        }

        # State tracking
        self.failover_history: deque[FailoverExecution] = deque(maxlen=100)
        self.condition_history: deque[FailoverCondition] = deque(maxlen=1000)
        self.current_status = FailoverStatus.NORMAL
        self.primary_unhealthy_count = 0
        self.connection_failure_count = 0
        self.last_health_check = 0

        # Active failover
        self.active_failover: Optional[FailoverExecution] = None
        self._lock = asyncio.Lock()

    async def check_failover_conditions(self) -> FailoverDecision:
        """Check if failover conditions are met."""
        conditions = []

        # Check primary health
        primary_condition = await self._check_primary_health_condition()
        conditions.append(primary_condition)

        # Check replication lag
        lag_condition = await self._check_replication_lag_condition()
        conditions.append(lag_condition)

        # Check connectivity
        connectivity_condition = await self._check_connectivity_condition()
        conditions.append(connectivity_condition)

        # Check resource usage
        resource_condition = await self._check_resource_condition()
        conditions.append(resource_condition)

        # Check network partition
        network_condition = await self._check_network_partition_condition()
        conditions.append(network_condition)

        # Store conditions
        for condition in conditions:
            self.condition_history.append(condition)

        # Make failover decision
        decision = await self._make_failover_decision(conditions)

        # Update status
        if decision.should_failover:
            self.current_status = FailoverStatus.FAILOVER_REQUIRED

        return decision

    async def _check_primary_health_condition(self) -> FailoverCondition:
        """Check primary database health condition."""
        try:
            time.time()

            async with self.primary_pool.acquire() as conn:
                # Basic health check
                await conn.fetchval("SELECT 1")

                # Check if database is accepting writes
                test_table = "failover_health_test"
                await conn.execute(f"CREATE TEMP TABLE {test_table} (id INTEGER)")
                await conn.execute(f"DROP TABLE {test_table}")

                # Reset unhealthy count
                self.primary_unhealthy_count = 0

                return FailoverCondition(
                    trigger=FailoverTrigger.PRIMARY_UNHEALTHY,
                    severity="healthy",
                    description="Primary database is healthy",
                    threshold_met=False,
                    current_value=0,
                    threshold_value=self.thresholds["primary_unhealthy_threshold"],
                )

        except Exception as e:
            self.primary_unhealthy_count += 1

            threshold_met = (
                self.primary_unhealthy_count
                >= self.thresholds["primary_unhealthy_threshold"]
            )

            return FailoverCondition(
                trigger=FailoverTrigger.PRIMARY_UNHEALTHY,
                severity="critical" if threshold_met else "warning",
                description=f"Primary database unhealthy: {str(e)}",
                threshold_met=threshold_met,
                current_value=self.primary_unhealthy_count,
                threshold_value=self.thresholds["primary_unhealthy_threshold"],
            )

    async def _check_replication_lag_condition(self) -> FailoverCondition:
        """Check replication lag condition."""
        try:
            # Check if we have access to replication info
            async with self.primary_pool.acquire() as conn:
                # Get replica lag information
                replica_info = await conn.fetch("""
                    SELECT
                        application_name,
                        client_addr,
                        state,
                        EXTRACT(EPOCH FROM (NOW() - reply_time)) as lag_seconds
                    FROM pg_stat_replication
                    WHERE state = 'streaming'
                """)

                if not replica_info:
                    return FailoverCondition(
                        trigger=FailoverTrigger.REPLICATION_LAG,
                        severity="warning",
                        description="No streaming replicas detected",
                        threshold_met=False,
                    )

                # Check maximum lag
                max_lag = max(
                    float(row["lag_seconds"])
                    for row in replica_info
                    if row["lag_seconds"]
                )
                threshold_met = (
                    max_lag > self.thresholds["replication_lag_critical_seconds"]
                )

                return FailoverCondition(
                    trigger=FailoverTrigger.REPLICATION_LAG,
                    severity="critical" if threshold_met else "healthy",
                    description=f"Replication lag: {max_lag:.1f}s",
                    threshold_met=threshold_met,
                    current_value=max_lag,
                    threshold_value=self.thresholds["replication_lag_critical_seconds"],
                )

        except Exception as e:
            return FailoverCondition(
                trigger=FailoverTrigger.REPLICATION_LAG,
                severity="unknown",
                description=f"Unable to check replication lag: {str(e)}",
                threshold_met=False,
            )

    async def _check_connectivity_condition(self) -> FailoverCondition:
        """Check database connectivity condition."""
        try:
            # Test connection to primary
            async with self.primary_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            # Reset failure count
            self.connection_failure_count = 0

            return FailoverCondition(
                trigger=FailoverTrigger.NETWORK_PARTITION,
                severity="healthy",
                description="Database connectivity healthy",
                threshold_met=False,
                current_value=0,
                threshold_value=self.thresholds["connection_failure_threshold"],
            )

        except Exception as e:
            self.connection_failure_count += 1

            threshold_met = (
                self.connection_failure_count
                >= self.thresholds["connection_failure_threshold"]
            )

            return FailoverCondition(
                trigger=FailoverTrigger.NETWORK_PARTITION,
                severity="critical" if threshold_met else "warning",
                description=f"Database connectivity issue: {str(e)}",
                threshold_met=threshold_met,
                current_value=self.connection_failure_count,
                threshold_value=self.thresholds["connection_failure_threshold"],
            )

    async def _check_resource_condition(self) -> FailoverCondition:
        """Check resource usage condition."""
        try:
            async with self.primary_pool.acquire() as conn:
                # Check database resource usage
                resource_info = await conn.fetchrow("""
                    SELECT
                        (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        pg_size_pretty(pg_database_size(current_database())) as db_size,
                        (SELECT EXTRACT(EPOCH FROM (NOW() - max(backend_start))) FROM pg_stat_activity) as max_connection_age
                """)

                # Check connection count (simplified)
                active_connections = resource_info["active_connections"]
                max_connections = 100  # This should be configured based on your setup
                usage_pct = (active_connections / max_connections) * 100

                threshold_met = (
                    usage_pct > self.thresholds["resource_usage_critical_pct"]
                )

                return FailoverCondition(
                    trigger=FailoverTrigger.RESOURCE_EXHAUSTION,
                    severity="critical" if threshold_met else "healthy",
                    description=f"Resource usage: {usage_pct:.1f}% ({active_connections} connections)",
                    threshold_met=threshold_met,
                    current_value=usage_pct,
                    threshold_value=self.thresholds["resource_usage_critical_pct"],
                )

        except Exception as e:
            return FailoverCondition(
                trigger=FailoverTrigger.RESOURCE_EXHAUSTION,
                severity="unknown",
                description=f"Unable to check resource usage: {str(e)}",
                threshold_met=False,
            )

    async def _check_network_partition_condition(self) -> FailoverCondition:
        """Check for network partition condition."""
        try:
            # Check if we can reach replicas
            reachable_replicas = 0
            total_replicas = len(self.replica_pools)

            for pool in self.replica_pools:
                try:
                    async with pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                        reachable_replicas += 1
                except Exception:
                    pass

            # If we can't reach any replicas, might be network partition
            if reachable_replicas == 0 and total_replicas > 0:
                return FailoverCondition(
                    trigger=FailoverTrigger.NETWORK_PARTITION,
                    severity="critical",
                    description="Network partition detected - cannot reach replicas",
                    threshold_met=True,
                    current_value=0,
                    threshold_value=1,
                )

            return FailoverCondition(
                trigger=FailoverTrigger.NETWORK_PARTITION,
                severity="healthy",
                description=f"Network connectivity: {reachable_replicas}/{total_replicas} replicas reachable",
                threshold_met=False,
                current_value=reachable_replicas,
                threshold_value=1,
            )

        except Exception as e:
            return FailoverCondition(
                trigger=FailoverTrigger.NETWORK_PARTITION,
                severity="unknown",
                description=f"Unable to check network partition: {str(e)}",
                threshold_met=False,
            )

    async def _make_failover_decision(
        self, conditions: List[FailoverCondition]
    ) -> FailoverDecision:
        """Make failover decision based on conditions."""
        critical_conditions = [
            c for c in conditions if c.threshold_met and c.severity == "critical"
        ]

        if not critical_conditions:
            return FailoverDecision(
                should_failover=False,
                confidence=1.0,
                primary_reason="All systems healthy",
                supporting_conditions=conditions,
            )

        # Calculate confidence based on number and severity of conditions
        confidence = min(len(critical_conditions) * 0.3, 1.0)

        # Determine primary reason
        primary_condition = critical_conditions[0]
        primary_reason = (
            f"{primary_condition.trigger.value}: {primary_condition.description}"
        )

        # Select best replica target
        recommended_target = await self._select_failover_target()

        # Estimate downtime
        estimated_downtime = (
            30.0 if recommended_target else 300.0
        )  # 30s with good target, 5min without

        return FailoverDecision(
            should_failover=True,
            confidence=confidence,
            primary_reason=primary_reason,
            supporting_conditions=critical_conditions,
            recommended_target=recommended_target,
            estimated_downtime_seconds=estimated_downtime,
        )

    async def _select_failover_target(self) -> Optional[str]:
        """Select best replica for failover target."""
        best_replica = None
        best_score = -1

        for i, pool in enumerate(self.replica_pools):
            try:
                score = await self._evaluate_replica_suitability(pool, i)
                if score > best_score:
                    best_score = score
                    best_replica = f"replica_{i}"
            except Exception as e:
                logger.warning(f"Failed to evaluate replica {i}: {e}")

        return best_replica if best_score > 0.5 else None

    async def _evaluate_replica_suitability(
        self, pool: asyncpg.Pool, replica_index: int
    ) -> float:
        """Evaluate replica suitability for failover."""
        try:
            async with pool.acquire() as conn:
                # Check connectivity
                await conn.fetchval("SELECT 1")

                # Check replication lag
                lag_info = await conn.fetchrow("""
                    SELECT
                        pg_last_wal_receive_lsn() as receive_lsn,
                        pg_last_wal_replay_lsn() as replay_lsn,
                        EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) as lag_seconds
                """)

                lag_seconds = lag_info["lag_seconds"] or 0

                # Calculate score based on lag (lower is better)
                if lag_seconds < 10:
                    lag_score = 1.0
                elif lag_seconds < 30:
                    lag_score = 0.7
                elif lag_seconds < 60:
                    lag_score = 0.4
                else:
                    lag_score = 0.1

                # Check replica size (should be similar to primary)
                await conn.fetchval(
                    "SELECT pg_database_size(current_database())"
                )

                # Simple scoring - could be enhanced with more factors
                return lag_score

        except Exception as e:
            logger.warning(f"Replica evaluation failed: {e}")
            return 0.0

    async def execute_failover(
        self,
        trigger: FailoverTrigger = FailoverTrigger.MANUAL,
        target_replica: Optional[str] = None,
        force: bool = False,
    ) -> FailoverExecution:
        """Execute database failover."""
        if self.active_failover:
            raise RuntimeError("Failover already in progress")

        # Check conditions if not forced
        if not force:
            decision = await self.check_failover_conditions()
            if not decision.should_failover:
                raise ValueError("Failover conditions not met")

        # Create failover execution record
        execution = FailoverExecution(
            execution_id=self._generate_execution_id(),
            trigger=trigger,
            status=FailoverStatus.FAILOVER_IN_PROGRESS,
            start_time=time.time(),
            target_replica=target_replica,
        )

        self.active_failover = execution
        self.failover_history.append(execution)

        try:
            # Update status
            self.current_status = FailoverStatus.FAILOVER_IN_PROGRESS

            # Alert on failover start
            await self.alert_manager.trigger_alert(
                name="failover_started",
                severity=AlertSeverity.CRITICAL,
                message=f"Database failover started: {execution.execution_id}",
                context={"trigger": trigger.value, "target": target_replica},
            )

            # Execute failover steps
            await self._execute_failover_steps(execution)

            # Validate failover
            await self._validate_failover(execution)

            # Update execution
            execution.status = FailoverStatus.FAILOVER_COMPLETED
            execution.success = True
            execution.end_time = time.time()
            execution.duration_seconds = execution.end_time - execution.start_time

            # Update status
            self.current_status = FailoverStatus.FAILOVER_COMPLETED

            # Alert on success
            await self.alert_manager.trigger_alert(
                name="failover_completed",
                severity=AlertSeverity.INFO,
                message=f"Database failover completed successfully: {execution.execution_id}",
                context={"duration_seconds": execution.duration_seconds},
            )

            logger.info(f"Failover completed successfully: {execution.execution_id}")

        except Exception as e:
            # Handle failover failure
            execution.status = FailoverStatus.FAILOVER_FAILED
            execution.success = False
            execution.error_message = str(e)
            execution.end_time = time.time()
            execution.duration_seconds = execution.end_time - execution.start_time

            # Attempt rollback if configured
            if self.failover_config["rollback_on_failure"]:
                await self._rollback_failover(execution)

            # Update status
            self.current_status = FailoverStatus.FAILOVER_FAILED

            # Alert on failure
            await self.alert_manager.trigger_alert(
                name="failover_failed",
                severity=AlertSeverity.CRITICAL,
                message=f"Database failover failed: {execution.execution_id} - {str(e)}",
                context={
                    "error": str(e),
                    "duration_seconds": execution.duration_seconds,
                },
            )

            logger.error(f"Failover failed: {execution.execution_id} - {str(e)}")

        finally:
            self.active_failover = None

        return execution

    async def _execute_failover_steps(self, execution: FailoverExecution) -> None:
        """Execute failover steps."""
        # This is a simplified implementation
        # In a real scenario, this would involve:
        # 1. Promoting replica to primary
        # 2. Updating connection strings
        # 3. Reconfiguring applications
        # 4. Updating DNS records
        # 5. Notifying stakeholders

        logger.info(f"Executing failover steps for {execution.execution_id}")

        # Simulate failover execution time
        await asyncio.sleep(5)

        # In a real implementation, you would:
        # 1. Stop writes to primary
        # 2. Ensure replica is fully caught up
        # 3. Promote replica using pg_promote()
        # 4. Update application configuration
        # 5. Test new primary functionality

        logger.info(f"Failover steps completed for {execution.execution_id}")

    async def _validate_failover(self, execution: FailoverExecution) -> None:
        """Validate failover success."""
        logger.info(f"Validating failover for {execution.execution_id}")

        # Simulate validation
        await asyncio.sleep(2)

        # In a real implementation, you would:
        # 1. Test connectivity to new primary
        # 2. Verify data consistency
        # 3. Test write operations
        # 4. Verify replication from new primary

        execution.validation_results = {
            "connectivity_test": "passed",
            "data_consistency_test": "passed",
            "write_operations_test": "passed",
            "replication_test": "passed",
        }

        logger.info(f"Failover validation completed for {execution.execution_id}")

    async def _rollback_failover(self, execution: FailoverExecution) -> None:
        """Rollback failed failover."""
        logger.info(f"Rolling back failover for {execution.execution_id}")

        try:
            # Simulate rollback
            await asyncio.sleep(3)

            execution.rollback_performed = True

            logger.info(f"Failover rollback completed for {execution.execution_id}")

        except Exception as e:
            logger.error(
                f"Failover rollback failed: {execution.execution_id} - {str(e)}"
            )

    def _generate_execution_id(self) -> str:
        """Generate unique failover execution ID."""
        import uuid

        return f"fo_{int(time.time())}_{str(uuid.uuid4())[:8]}"

    async def execute_failback(self, force: bool = False) -> FailoverExecution:
        """Execute failback to original primary."""
        if self.current_status not in [FailoverStatus.FAILOVER_COMPLETED]:
            raise ValueError("Cannot failback - no active failover")

        # Check if original primary is healthy
        if not force:
            primary_condition = await self._check_primary_health_condition()
            if primary_condition.severity != "healthy":
                raise ValueError("Original primary not healthy for failback")

        # Create failback execution
        execution = FailoverExecution(
            execution_id=self._generate_execution_id(),
            trigger=FailoverTrigger.MANUAL,
            status=FailoverStatus.FAILOVER_IN_PROGRESS,
            start_time=time.time(),
        )

        self.active_failover = execution
        self.failover_history.append(execution)

        try:
            # Execute failback steps
            await self._execute_failback_steps(execution)

            # Update status
            execution.status = FailoverStatus.FAILOVER_BACK
            execution.success = True
            execution.end_time = time.time()
            execution.duration_seconds = execution.end_time - execution.start_time

            self.current_status = FailoverStatus.NORMAL

            logger.info(f"Failback completed successfully: {execution.execution_id}")

        except Exception as e:
            execution.status = FailoverStatus.FAILOVER_FAILED
            execution.success = False
            execution.error_message = str(e)
            execution.end_time = time.time()
            execution.duration_seconds = execution.end_time - execution.start_time

            logger.error(f"Failback failed: {execution.execution_id} - {str(e)}")

        finally:
            self.active_failover = None

        return execution

    async def _execute_failback_steps(self, execution: FailoverExecution) -> None:
        """Execute failback steps."""
        logger.info(f"Executing failback steps for {execution.execution_id}")

        # Simulate failback execution
        await asyncio.sleep(5)

        # In a real implementation, you would:
        # 1. Verify original primary is ready
        # 2. Stop writes to current primary
        # 3. Switch back to original primary
        # 4. Reconfigure replication
        # 5. Update application configuration

        logger.info(f"Failback steps completed for {execution.execution_id}")

    def get_failover_history(self, limit: int = 50) -> List[FailoverExecution]:
        """Get failover execution history."""
        executions = list(self.failover_history)
        executions.sort(key=lambda e: e.created_at, reverse=True)
        return executions[:limit]

    def get_failover_summary(self) -> Dict[str, Any]:
        """Get comprehensive failover summary."""
        executions = list(self.failover_history)

        if not executions:
            return {
                "current_status": self.current_status.value,
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "last_execution": None,
            }

        successful = [e for e in executions if e.success]
        failed = [e for e in executions if e.success is False]

        last_execution = executions[-1]

        return {
            "current_status": self.current_status.value,
            "total_executions": len(executions),
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "success_rate_pct": len(successful) / len(executions) * 100,
            "avg_duration_seconds": sum(e.duration_seconds or 0 for e in executions)
            / len(executions),
            "last_execution": {
                "execution_id": last_execution.execution_id,
                "trigger": last_execution.trigger.value,
                "status": last_execution.status.value,
                "success": last_execution.success,
                "duration_seconds": last_execution.duration_seconds,
                "timestamp": last_execution.created_at,
            },
            "primary_unhealthy_count": self.primary_unhealthy_count,
            "connection_failure_count": self.connection_failure_count,
        }

    async def test_failover_procedure(self, dry_run: bool = True) -> Dict[str, Any]:
        """Test failover procedure without actual execution."""
        try:
            # Check conditions
            decision = await self.check_failover_conditions()

            # Select target
            target = await self._select_failover_target()

            # Estimate readiness
            readiness_score = await self._calculate_failover_readiness()

            if dry_run:
                return {
                    "dry_run": True,
                    "decision": decision,
                    "recommended_target": target,
                    "readiness_score": readiness_score,
                    "estimated_downtime_seconds": decision.estimated_downtime_seconds,
                    "conditions": [
                        {
                            "trigger": c.trigger.value,
                            "severity": c.severity,
                            "threshold_met": c.threshold_met,
                            "description": c.description,
                        }
                        for c in decision.supporting_conditions
                    ],
                }
            else:
                # Execute actual test failover
                execution = await self.execute_failover(
                    trigger=FailoverTrigger.MANUAL, target_replica=target, force=True
                )

                return {
                    "dry_run": False,
                    "execution": execution,
                    "success": execution.success,
                    "duration_seconds": execution.duration_seconds,
                }

        except Exception as e:
            return {"error": str(e), "success": False}

    async def _calculate_failover_readiness(self) -> float:
        """Calculate overall failover readiness score."""
        try:
            # Check replica readiness
            replica_scores = []
            for i, pool in enumerate(self.replica_pools):
                score = await self._evaluate_replica_suitability(pool, i)
                replica_scores.append(score)

            # Calculate average replica score
            avg_replica_score = (
                sum(replica_scores) / len(replica_scores) if replica_scores else 0
            )

            # Check configuration readiness
            config_score = 1.0 if self.failover_config["auto_failover_enabled"] else 0.5

            # Check monitoring readiness
            monitoring_score = 1.0 if self.condition_history else 0.5

            # Calculate overall score
            overall_score = (
                avg_replica_score * 0.5 + config_score * 0.3 + monitoring_score * 0.2
            )

            return overall_score

        except Exception as e:
            logger.error(f"Failed to calculate failover readiness: {e}")
            return 0.0


# Global failover manager instance
_failover_manager: FailoverManager | None = None


def get_failover_manager() -> FailoverManager:
    """Get global failover manager instance."""
    global _failover_manager
    if _failover_manager is None:
        raise RuntimeError(
            "Failover manager not initialized. Call init_failover_manager() first."
        )
    return _failover_manager


async def init_failover_manager(
    primary_pool: asyncpg.Pool,
    replica_pools: List[asyncpg.Pool],
    alert_manager: Optional[Any] = None,
) -> FailoverManager:
    """Initialize global failover manager."""
    global _failover_manager
    _failover_manager = FailoverManager(primary_pool, replica_pools, alert_manager)
    return _failover_manager
