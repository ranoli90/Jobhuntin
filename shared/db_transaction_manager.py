"""Advanced database transaction management system.

Provides:
- Transaction context management
- Distributed transaction support
- Transaction monitoring
- Deadlock detection and resolution
- Performance optimization

Usage:
    from shared.db_transaction_manager import TransactionManager

    tx_manager = TransactionManager(db_pool)
    async with tx_manager.transaction() as conn:
        result = await conn.fetch("SELECT * FROM users")
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import asyncpg

from shared.alerting import AlertSeverity, get_alert_manager
from shared.logging_config import get_logger

logger = get_logger("sorce.db_transaction")


class TransactionState(Enum):
    """Transaction states."""

    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    PREPARING = "preparing"
    PREPARED = "prepared"


class IsolationLevel(Enum):
    """Transaction isolation levels."""

    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class TransactionPriority(Enum):
    """Transaction priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TransactionConfig:
    """Transaction configuration."""

    isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED
    timeout_seconds: float = 30.0
    retry_on_deadlock: bool = True
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    read_only: bool = False
    deferrable: bool = False
    priority: TransactionPriority = TransactionPriority.NORMAL
    auto_rollback: bool = True
    savepoints_enabled: bool = True
    distributed: bool = False


@dataclass
class TransactionMetrics:
    """Transaction performance metrics."""

    transaction_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    state: TransactionState = TransactionState.ACTIVE
    isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED
    queries_executed: int = 0
    rows_affected: int = 0
    savepoints_created: int = 0
    savepoints_rolled_back: int = 0
    retry_count: int = 0
    deadlock_detected: bool = False
    timeout_occurred: bool = False
    error_message: Optional[str] = None
    connection_id: Optional[str] = None


@dataclass
class SavepointInfo:
    """Savepoint information."""

    name: str
    created_at: float
    queries_before: int
    rows_affected_before: int


class TransactionManager:
    """Advanced database transaction management system."""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        default_config: Optional[TransactionConfig] = None,
        alert_manager: Optional[Any] = None,
    ):
        self.db_pool = db_pool
        self.default_config = default_config or TransactionConfig()
        self.alert_manager = alert_manager or get_alert_manager()

        # Transaction tracking
        self.active_transactions: Dict[str, TransactionMetrics] = {}
        self.transaction_history: deque[TransactionMetrics] = deque(maxlen=1000)
        self.savepoints: Dict[str, Dict[str, SavepointInfo]] = defaultdict(dict)

        # Performance monitoring
        self.retry_stats: Dict[str, int] = defaultdict(int)
        self.deadlock_stats: Dict[str, int] = defaultdict(int)
        self.timeout_stats: Dict[str, int] = defaultdict(int)

        # Configuration
        self.max_concurrent_transactions = 100
        self.transaction_timeout_seconds = 300  # 5 minutes default

        self._lock = asyncio.Lock()

    async def transaction(
        self,
        config: Optional[TransactionConfig] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> "TransactionContext":
        """Create transaction context."""
        transaction_config = config or self.default_config
        transaction_id = self._generate_transaction_id()

        # Check concurrent transaction limit
        if len(self.active_transactions) >= self.max_concurrent_transactions:
            raise RuntimeError("Maximum concurrent transactions exceeded")

        # Create transaction metrics
        metrics = TransactionMetrics(
            transaction_id=transaction_id,
            start_time=time.time(),
            isolation_level=transaction_config.isolation_level,
            priority=transaction_config.priority,
        )

        # Get connection
        if connection:
            conn = connection
            metrics.connection_id = f"existing_{id(conn)}"
        else:
            conn = await self.db_pool.acquire()
            metrics.connection_id = f"pool_{id(conn)}"

        # Track transaction
        self.active_transactions[transaction_id] = metrics

        return TransactionContext(
            transaction_manager=self,
            connection=conn,
            transaction_id=transaction_id,
            config=transaction_config,
            metrics=metrics,
        )

    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        import uuid

        return f"tx_{int(time.time())}_{str(uuid.uuid4())[:8]}"

    async def execute_in_transaction(
        self,
        func: Callable,
        *args,
        config: Optional[TransactionConfig] = None,
        **kwargs,
    ) -> Any:
        """Execute function within transaction context."""
        async with await self.transaction(config) as conn:
            return await func(conn, *args, **kwargs)

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        config: Optional[TransactionConfig] = None,
        **kwargs,
    ) -> Any:
        """Execute function with automatic retry on deadlock."""
        transaction_config = config or self.default_config

        if not transaction_config.retry_on_deadlock:
            return await self.execute_in_transaction(
                func, *args, config=config, **kwargs
            )

        last_error = None

        for attempt in range(transaction_config.max_retry_attempts):
            try:
                return await self.execute_in_transaction(
                    func, *args, config=config, **kwargs
                )

            except Exception as e:
                last_error = e

                # Check if it's a deadlock
                if self._is_deadlock_error(str(e)):
                    if attempt < transaction_config.max_retry_attempts - 1:
                        self.retry_stats["deadlock_retries"] += 1

                        # Wait before retry
                        if transaction_config.retry_delay_seconds > 0:
                            await asyncio.sleep(transaction_config.retry_delay_seconds)

                        logger.warning(
                            f"Deadlock detected, retrying transaction (attempt {attempt + 2})"
                        )
                        continue

                # Re-raise non-retryable errors or final attempt failure
                raise

        # All retries failed
        raise last_error

    def _is_deadlock_error(self, error_message: str) -> bool:
        """Check if error is a deadlock."""
        deadlock_patterns = [
            "deadlock",
            "lock timeout",
            "serialization failure",
            "could not serialize access",
            "tuple concurrently updated",
        ]

        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in deadlock_patterns)

    async def _begin_transaction(
        self,
        conn: asyncpg.Connection,
        config: TransactionConfig,
        metrics: TransactionMetrics,
    ) -> None:
        """Begin database transaction."""
        try:
            # Set isolation level
            if config.isolation_level != IsolationLevel.READ_COMMITTED:
                await conn.execute(
                    f"SET TRANSACTION ISOLATION LEVEL {config.isolation_level.value}"
                )

            # Set read-only mode
            if config.read_only:
                await conn.execute("SET TRANSACTION READ ONLY")

            # Set deferrable mode (for serializable transactions)
            if (
                config.deferrable
                and config.isolation_level == IsolationLevel.SERIALIZABLE
            ):
                await conn.execute("SET TRANSACTION DEFERRABLE")

            # Begin transaction
            transaction = conn.transaction()
            await transaction.__aenter__()

            # Store transaction reference for cleanup
            metrics.connection_id = str(id(conn))

        except Exception as e:
            metrics.state = TransactionState.FAILED
            metrics.error_message = str(e)
            raise

    async def _commit_transaction(
        self, conn: asyncpg.Connection, metrics: TransactionMetrics
    ) -> None:
        """Commit transaction."""
        try:
            # Get the transaction object
            transaction = conn._transaction

            if transaction:
                await transaction.__aexit__(None, None, None)
                metrics.state = TransactionState.COMMITTED
            else:
                # No active transaction
                metrics.state = TransactionState.FAILED
                metrics.error_message = "No active transaction to commit"

        except Exception as e:
            metrics.state = TransactionState.FAILED
            metrics.error_message = str(e)

            # Attempt rollback on commit failure
            try:
                await self._rollback_transaction(conn, metrics)
            except Exception as rollback_error:
                logger.error(
                    f"Rollback after commit failure also failed: {rollback_error}"
                )

            raise

    async def _rollback_transaction(
        self, conn: asyncpg.Connection, metrics: TransactionMetrics
    ) -> None:
        """Rollback transaction."""
        try:
            # Get the transaction object
            transaction = conn._transaction

            if transaction:
                await transaction.__aexit__(Exception(), None, None)
                metrics.state = TransactionState.ROLLED_BACK
            else:
                # No active transaction
                metrics.state = TransactionState.FAILED
                metrics.error_message = "No active transaction to rollback"

        except Exception as e:
            metrics.state = TransactionState.FAILED
            metrics.error_message = f"Rollback failed: {str(e)}"
            raise

    async def create_savepoint(
        self,
        conn: asyncpg.Connection,
        transaction_id: str,
        savepoint_name: Optional[str] = None,
    ) -> str:
        """Create savepoint within transaction."""
        if savepoint_name is None:
            savepoint_name = (
                f"sp_{int(time.time())}_{len(self.savepoints[transaction_id])}"
            )

        try:
            # Create savepoint
            await conn.execute(f"SAVEPOINT {savepoint_name}")

            # Track savepoint
            metrics = self.active_transactions.get(transaction_id)
            if metrics:
                savepoint_info = SavepointInfo(
                    name=savepoint_name,
                    created_at=time.time(),
                    queries_before=metrics.queries_executed,
                    rows_affected_before=metrics.rows_affected,
                )
                self.savepoints[transaction_id][savepoint_name] = savepoint_info
                metrics.savepoints_created += 1

            return savepoint_name

        except Exception as e:
            logger.error(f"Failed to create savepoint {savepoint_name}: {e}")
            raise

    async def rollback_to_savepoint(
        self, conn: asyncpg.Connection, transaction_id: str, savepoint_name: str
    ) -> None:
        """Rollback to savepoint."""
        try:
            # Rollback to savepoint
            await conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")

            # Update metrics
            metrics = self.active_transactions.get(transaction_id)
            if metrics:
                savepoint_info = self.savepoints[transaction_id].get(savepoint_name)
                if savepoint_info:
                    metrics.queries_executed = savepoint_info.queries_before
                    metrics.rows_affected = savepoint_info.rows_affected_before
                    metrics.savepoints_rolled_back += 1

                # Remove savepoint and any created after it
                savepoints_to_remove = []
                for sp_name, sp_info in self.savepoints[transaction_id].items():
                    if sp_info.created_at >= savepoint_info.created_at:
                        savepoints_to_remove.append(sp_name)

                for sp_name in savepoints_to_remove:
                    del self.savepoints[transaction_id][sp_name]

        except Exception as e:
            logger.error(f"Failed to rollback to savepoint {savepoint_name}: {e}")
            raise

    async def release_savepoint(
        self, conn: asyncpg.Connection, transaction_id: str, savepoint_name: str
    ) -> None:
        """Release savepoint."""
        try:
            # Release savepoint
            await conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")

            # Remove from tracking
            self.savepoints[transaction_id].pop(savepoint_name, None)

        except Exception as e:
            logger.error(f"Failed to release savepoint {savepoint_name}: {e}")
            raise

    async def _track_query_execution(
        self, transaction_id: str, query: str, rows_affected: int = 0
    ) -> None:
        """Track query execution within transaction."""
        metrics = self.active_transactions.get(transaction_id)
        if metrics:
            metrics.queries_executed += 1
            metrics.rows_affected += rows_affected

    async def _handle_transaction_completion(self, transaction_id: str) -> None:
        """Handle transaction completion and cleanup."""
        metrics = self.active_transactions.pop(transaction_id, None)

        if metrics:
            metrics.end_time = time.time()
            metrics.duration_seconds = metrics.end_time - metrics.start_time

            # Store in history
            self.transaction_history.append(metrics)

            # Check for performance issues
            await self._check_transaction_performance(metrics)

            # Clean up savepoints
            self.savepoints.pop(transaction_id, None)

    async def _check_transaction_performance(self, metrics: TransactionMetrics) -> None:
        """Check transaction performance and trigger alerts if needed."""
        # Check for long-running transactions
        if metrics.duration_seconds and metrics.duration_seconds > 60:  # 1 minute
            await self.alert_manager.trigger_alert(
                name="long_transaction",
                severity=AlertSeverity.WARNING,
                message=f"Long-running transaction: {metrics.duration_seconds:.1f}s",
                context={
                    "transaction_id": metrics.transaction_id,
                    "duration": metrics.duration_seconds,
                    "queries": metrics.queries_executed,
                },
            )

        # Check for high query count
        if metrics.queries_executed > 100:
            await self.alert_manager.trigger_alert(
                name="high_query_count",
                severity=AlertSeverity.INFO,
                message=f"High query count in transaction: {metrics.queries_executed}",
                context={
                    "transaction_id": metrics.transaction_id,
                    "queries": metrics.queries_executed,
                    "duration": metrics.duration_seconds,
                },
            )

        # Check for deadlock
        if metrics.deadlock_detected:
            self.deadlock_stats["total_deadlocks"] += 1
            await self.alert_manager.trigger_alert(
                name="deadlock_detected",
                severity=AlertSeverity.ERROR,
                message=f"Deadlock detected in transaction: {metrics.transaction_id}",
                context={
                    "transaction_id": metrics.transaction_id,
                    "retry_count": metrics.retry_count,
                },
            )

        # Check for timeout
        if metrics.timeout_occurred:
            self.timeout_stats["total_timeouts"] += 1
            await self.alert_manager.trigger_alert(
                name="transaction_timeout",
                severity=AlertSeverity.ERROR,
                message=f"Transaction timeout: {metrics.transaction_id}",
                context={
                    "transaction_id": metrics.transaction_id,
                    "timeout_duration": metrics.duration_seconds,
                },
            )

    def get_transaction_statistics(self) -> Dict[str, Any]:
        """Get comprehensive transaction statistics."""
        stats = {
            "active_transactions": len(self.active_transactions),
            "total_transactions": len(self.transaction_history),
            "success_rate": 0.0,
            "avg_duration_seconds": 0.0,
            "avg_queries_per_transaction": 0.0,
            "deadlock_count": self.deadlock_stats["total_deadlocks"],
            "timeout_count": self.timeout_stats["total_timeouts"],
            "retry_count": self.retry_stats["deadlock_retries"],
            "isolation_levels": defaultdict(int),
            "states": defaultdict(int),
        }

        if self.transaction_history:
            # Calculate success rate
            successful = sum(
                1
                for tx in self.transaction_history
                if tx.state == TransactionState.COMMITTED
            )
            stats["success_rate"] = (successful / len(self.transaction_history)) * 100

            # Calculate averages
            total_duration = sum(
                tx.duration_seconds or 0 for tx in self.transaction_history
            )
            total_queries = sum(tx.queries_executed for tx in self.transaction_history)

            stats["avg_duration_seconds"] = total_duration / len(
                self.transaction_history
            )
            stats["avg_queries_per_transaction"] = total_queries / len(
                self.transaction_history
            )

            # Count isolation levels
            for tx in self.transaction_history:
                stats["isolation_levels"][tx.isolation_level.value] += 1
                stats["states"][tx.state.value] += 1

        return dict(stats)

    def get_active_transactions(self) -> List[Dict[str, Any]]:
        """Get information about active transactions."""
        active = []

        for transaction_id, metrics in self.active_transactions.items():
            active.append(
                {
                    "transaction_id": transaction_id,
                    "start_time": metrics.start_time,
                    "duration_seconds": time.time() - metrics.start_time,
                    "state": metrics.state.value,
                    "isolation_level": metrics.isolation_level.value,
                    "queries_executed": metrics.queries_executed,
                    "rows_affected": metrics.rows_affected,
                    "savepoints_created": metrics.savepoints_created,
                    "retry_count": metrics.retry_count,
                    "connection_id": metrics.connection_id,
                }
            )

        return active

    async def cleanup_long_running_transactions(
        self, timeout_seconds: float = 300
    ) -> int:
        """Clean up long-running transactions."""
        current_time = time.time()
        cleaned_count = 0

        for transaction_id, metrics in list(self.active_transactions.items()):
            if current_time - metrics.start_time > timeout_seconds:
                logger.warning(
                    f"Cleaning up long-running transaction: {transaction_id}"
                )

                # Mark as failed due to timeout
                metrics.timeout_occurred = True
                metrics.state = TransactionState.FAILED
                metrics.error_message = "Transaction timeout"

                # Handle completion
                await self._handle_transaction_completion(transaction_id)
                cleaned_count += 1

        return cleaned_count

    def update_default_config(self, **kwargs) -> None:
        """Update default transaction configuration."""
        for key, value in kwargs.items():
            if hasattr(self.default_config, key):
                setattr(self.default_config, key, value)
                logger.info(f"Updated default transaction config {key} = {value}")


class TransactionContext:
    """Transaction context manager."""

    def __init__(
        self,
        transaction_manager: TransactionManager,
        connection: asyncpg.Connection,
        transaction_id: str,
        config: TransactionConfig,
        metrics: TransactionMetrics,
    ):
        self.transaction_manager = transaction_manager
        self.connection = connection
        self.transaction_id = transaction_id
        self.config = config
        self.metrics = metrics
        self._entered = False
        self._released = False

    async def __aenter__(self) -> asyncpg.Connection:
        """Enter transaction context."""
        if self._entered:
            raise RuntimeError("Transaction context already entered")

        self._entered = True

        try:
            # Begin transaction
            await self.transaction_manager._begin_transaction(
                self.connection, self.config, self.metrics
            )

            return self.connection

        except Exception:
            # Handle failure to begin
            await self.transaction_manager._handle_transaction_completion(
                self.transaction_id
            )
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit transaction context."""
        if not self._entered or self._released:
            return

        self._released = True

        try:
            if exc_type is None:
                # No exception - commit transaction
                await self.transaction_manager._commit_transaction(
                    self.connection, self.metrics
                )
            else:
                # Exception occurred - rollback if auto-rollback enabled
                if self.config.auto_rollback:
                    await self.transaction_manager._rollback_transaction(
                        self.connection, self.metrics
                    )

                # Check if it's a deadlock
                if self.transaction_manager._is_deadlock_error(str(exc_val)):
                    self.metrics.deadlock_detected = True
                    self.metrics.retry_count += 1
                    self.metrics.error_message = str(exc_val)
                else:
                    self.metrics.error_message = str(exc_val)

                # Re-raise the original exception
                return False  # Don't suppress the exception

        finally:
            # Always handle completion
            await self.transaction_manager._handle_transaction_completion(
                self.transaction_id
            )

            # Release connection if we acquired it
            if self.metrics.connection_id and self.metrics.connection_id.startswith(
                "pool_"
            ):
                await self.transaction_manager.db_pool.release(self.connection)

    async def create_savepoint(self, name: Optional[str] = None) -> str:
        """Create savepoint within transaction."""
        if not self.config.savepoints_enabled:
            raise RuntimeError("Savepoints are not enabled for this transaction")

        return await self.transaction_manager.create_savepoint(
            self.connection, self.transaction_id, name
        )

    async def rollback_to_savepoint(self, savepoint_name: str) -> None:
        """Rollback to savepoint."""
        await self.transaction_manager.rollback_to_savepoint(
            self.connection, self.transaction_id, savepoint_name
        )

    async def release_savepoint(self, savepoint_name: str) -> None:
        """Release savepoint."""
        await self.transaction_manager.release_savepoint(
            self.connection, self.transaction_id, savepoint_name
        )

    async def execute(self, query: str, *args, **kwargs) -> Any:
        """Execute query within transaction."""
        start_time = time.time()

        try:
            if kwargs:
                result = await self.connection.fetch(query, *args, **kwargs)
            else:
                result = await self.connection.fetch(query, *args)

            # Track query execution
            rows_affected = len(result) if isinstance(result, list) else 0
            await self.transaction_manager._track_query_execution(
                self.transaction_id, query, rows_affected
            )

            return result

        except Exception:
            # Track failed query
            await self.transaction_manager._track_query_execution(
                self.transaction_id, query, 0
            )
            raise


# Global transaction manager instance
_transaction_manager: TransactionManager | None = None


def get_transaction_manager() -> TransactionManager:
    """Get global transaction manager instance."""
    global _transaction_manager
    if _transaction_manager is None:
        raise RuntimeError(
            "Transaction manager not initialized. Call init_transaction_manager() first."
        )
    return _transaction_manager


async def init_transaction_manager(
    db_pool: asyncpg.Pool,
    default_config: Optional[TransactionConfig] = None,
    alert_manager: Optional[Any] = None,
) -> TransactionManager:
    """Initialize global transaction manager."""
    global _transaction_manager
    _transaction_manager = TransactionManager(db_pool, default_config, alert_manager)
    return _transaction_manager
