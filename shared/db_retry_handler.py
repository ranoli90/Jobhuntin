"""Advanced database connection retry and resilience system.

Provides:
- Intelligent retry logic
- Circuit breaker pattern
- Exponential backoff
- Connection resilience
- Error classification

Usage:
    from shared.db_retry_handler import RetryHandler

    retry_handler = RetryHandler(db_pool)
    result = await retry_handler.execute_with_retry("SELECT * FROM users")
"""

from __future__ import annotations

import asyncio
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

import asyncpg

from shared.logging_config import get_logger
from shared.alerting import AlertSeverity, get_alert_manager

logger = get_logger("sorce.db_retry")


class ErrorType(Enum):
    """Database error types."""

    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    DEADLOCK_ERROR = "deadlock_error"
    CONSTRAINT_ERROR = "constraint_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


class RetryStrategy(Enum):
    """Retry strategies."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    IMMEDIATE = "immediate"
    NO_RETRY = "no_retry"


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    """Retry configuration."""

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True
    jitter_factor: float = 0.1
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_errors: List[ErrorType] = field(
        default_factory=lambda: [
            ErrorType.CONNECTION_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.DEADLOCK_ERROR,
            ErrorType.RESOURCE_ERROR,
        ]
    )
    non_retryable_errors: List[ErrorType] = field(
        default_factory=lambda: [ErrorType.CONSTRAINT_ERROR, ErrorType.PERMISSION_ERROR]
    )


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 60.0
    success_threshold: int = 3
    monitoring_window_seconds: float = 300.0


@dataclass
class RetryAttempt:
    """Retry attempt information."""

    attempt_number: int
    error_type: ErrorType
    error_message: str
    delay_seconds: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class RetryResult:
    """Retry execution result."""

    success: bool
    attempts: int
    total_time_seconds: float
    retry_attempts: List[RetryAttempt] = field(default_factory=list)
    final_error: Optional[str] = None
    circuit_breaker_triggered: bool = False


@dataclass
class CircuitBreakerState:
    """Circuit breaker state information."""

    state: CircuitState
    failure_count: int
    last_failure_time: float
    last_success_time: float
    next_attempt_time: float
    success_count: int = 0


class RetryHandler:
    """Advanced database retry and resilience handler."""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        alert_manager: Optional[Any] = None,
    ):
        self.db_pool = db_pool
        self.retry_config = retry_config or RetryConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()
        self.alert_manager = alert_manager or get_alert_manager()

        # Circuit breaker state
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}

        # Retry statistics
        self.retry_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "total_attempts": 0,
                "successful_attempts": 0,
                "failed_attempts": 0,
                "retry_count": 0,
                "circuit_breaker_trips": 0,
                "avg_retry_time": 0.0,
                "last_attempt": 0.0,
            }
        )

        # Error classification
        self.error_patterns = {
            ErrorType.CONNECTION_ERROR: [
                "connection",
                "connect",
                "network",
                "timeout",
                "unreachable",
                "refused",
                "reset",
                "broken",
                "closed",
            ],
            ErrorType.TIMEOUT_ERROR: ["timeout", "timed out", "time out"],
            ErrorType.DEADLOCK_ERROR: [
                "deadlock",
                "lock",
                "serialization",
                "serialization failure",
            ],
            ErrorType.CONSTRAINT_ERROR: [
                "constraint",
                "unique",
                "foreign key",
                "check constraint",
                "not null",
                "violation",
            ],
            ErrorType.PERMISSION_ERROR: [
                "permission",
                "access",
                "denied",
                "unauthorized",
                "privilege",
                "role",
                "rights",
            ],
            ErrorType.RESOURCE_ERROR: [
                "resource",
                "memory",
                "disk",
                "space",
                "limit",
                "exhausted",
                "too many connections",
                "out of memory",
            ],
        }

        self._lock = asyncio.Lock()

    async def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str = "database_operation",
        *args,
        **kwargs,
    ) -> Any:
        """Execute database operation with retry logic."""
        start_time = time.time()
        retry_attempts = []

        # Check circuit breaker
        if self.circuit_config.enabled and self._is_circuit_open(operation_name):
            return RetryResult(
                success=False,
                attempts=0,
                total_time_seconds=0,
                circuit_breaker_triggered=True,
                final_error=f"Circuit breaker open for {operation_name}",
            )

        # Initialize circuit breaker if needed
        if self.circuit_config.enabled and operation_name not in self.circuit_breakers:
            self.circuit_breakers[operation_name] = CircuitBreakerState(
                state=CircuitState.CLOSED,
                failure_count=0,
                last_failure_time=0,
                last_success_time=0,
                next_attempt_time=0,
            )

        # Update statistics
        self.retry_stats[operation_name]["total_attempts"] += 1
        self.retry_stats[operation_name]["last_attempt"] = time.time()

        for attempt in range(self.retry_config.max_attempts):
            try:
                # Execute operation
                if attempt == 0:
                    # First attempt - no delay
                    result = await operation(*args, **kwargs)
                else:
                    # Retry attempt
                    delay = self._calculate_retry_delay(attempt)
                    retry_attempts.append(
                        RetryAttempt(
                            attempt_number=attempt,
                            error_type=ErrorType.UNKNOWN_ERROR,
                            error_message="Previous attempt failed",
                            delay_seconds=delay,
                        )
                    )

                    await asyncio.sleep(delay)
                    result = await operation(*args, **kwargs)

                # Success - update circuit breaker and stats
                total_time = time.time() - start_time
                await self._handle_success(
                    operation_name, total_time, len(retry_attempts)
                )

                return RetryResult(
                    success=True,
                    attempts=attempt + 1,
                    total_time_seconds=total_time,
                    retry_attempts=retry_attempts,
                )

            except Exception as e:
                error_type = self._classify_error(str(e))
                error_message = str(e)

                # Check if error is retryable
                if not self._is_retryable_error(error_type):
                    # Non-retryable error - fail immediately
                    total_time = time.time() - start_time
                    await self._handle_failure(
                        operation_name, error_type, total_time, len(retry_attempts)
                    )

                    return RetryResult(
                        success=False,
                        attempts=attempt + 1,
                        total_time_seconds=total_time,
                        retry_attempts=retry_attempts,
                        final_error=error_message,
                    )

                # Log retry attempt
                if attempt < self.retry_config.max_attempts - 1:
                    logger.warning(
                        f"Operation {operation_name} failed (attempt {attempt + 1}/{self.retry_config.max_attempts}): "
                        f"{error_type.value} - {error_message}"
                    )

                    # Update retry attempt with actual error
                    if retry_attempts:
                        retry_attempts[-1].error_type = error_type
                        retry_attempts[-1].error_message = error_message

        # All attempts failed
        total_time = time.time() - start_time
        await self._handle_failure(
            operation_name, error_type, total_time, len(retry_attempts)
        )

        return RetryResult(
            success=False,
            attempts=self.retry_config.max_attempts,
            total_time_seconds=total_time,
            retry_attempts=retry_attempts,
            final_error=error_message,
        )

    def _classify_error(self, error_message: str) -> ErrorType:
        """Classify database error type."""
        error_lower = error_message.lower()

        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern in error_lower:
                    return error_type

        return ErrorType.UNKNOWN_ERROR

    def _is_retryable_error(self, error_type: ErrorType) -> bool:
        """Check if error type is retryable."""
        return error_type in self.retry_config.retryable_errors

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay based on strategy."""
        if self.retry_config.retry_strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        elif self.retry_config.retry_strategy == RetryStrategy.NO_RETRY:
            return float("inf")
        elif self.retry_config.retry_strategy == RetryStrategy.FIXED_INTERVAL:
            delay = self.retry_config.base_delay_seconds
        elif self.retry_config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.retry_config.base_delay_seconds * attempt
        else:  # EXPONENTIAL_BACKOFF
            delay = self.retry_config.base_delay_seconds * (
                self.retry_config.backoff_multiplier ** (attempt - 1)
            )

        # Apply maximum delay limit
        delay = min(delay, self.retry_config.max_delay_seconds)

        # Add jitter if enabled
        if self.retry_config.jitter_enabled:
            jitter = delay * self.retry_config.jitter_factor
            delay += random.uniform(-jitter, jitter)

        return max(0, delay)

    def _is_circuit_open(self, operation_name: str) -> bool:
        """Check if circuit breaker is open for operation."""
        if (
            not self.circuit_config.enabled
            or operation_name not in self.circuit_breakers
        ):
            return False

        circuit = self.circuit_breakers[operation_name]
        current_time = time.time()

        if circuit.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if current_time >= circuit.next_attempt_time:
                # Transition to half-open
                circuit.state = CircuitState.HALF_OPEN
                circuit.success_count = 0
                logger.info(
                    f"Circuit breaker for {operation_name} transitioning to half-open"
                )
                return False
            else:
                return True

        return False

    async def _handle_success(
        self, operation_name: str, total_time: float, retry_count: int
    ) -> None:
        """Handle successful operation."""
        async with self._lock:
            # Update statistics
            stats = self.retry_stats[operation_name]
            stats["successful_attempts"] += 1
            stats["retry_count"] += retry_count

            # Update average retry time
            if stats["avg_retry_time"] == 0:
                stats["avg_retry_time"] = total_time
            else:
                stats["avg_retry_time"] = (stats["avg_retry_time"] * 0.9) + (
                    total_time * 0.1
                )

            # Update circuit breaker
            if self.circuit_config.enabled and operation_name in self.circuit_breakers:
                circuit = self.circuit_breakers[operation_name]
                current_time = time.time()

                if circuit.state == CircuitState.HALF_OPEN:
                    circuit.success_count += 1

                    # Check if we should close the circuit
                    if circuit.success_count >= self.circuit_config.success_threshold:
                        circuit.state = CircuitState.CLOSED
                        circuit.failure_count = 0
                        logger.info(
                            f"Circuit breaker for {operation_name} closed after {circuit.success_count} successes"
                        )
                elif circuit.state == CircuitState.CLOSED:
                    # Reset failure count on success in closed state
                    circuit.failure_count = max(0, circuit.failure_count - 1)

                circuit.last_success_time = current_time

        logger.debug(
            f"Operation {operation_name} succeeded after {retry_count} retries"
        )

    async def _handle_failure(
        self,
        operation_name: str,
        error_type: ErrorType,
        total_time: float,
        retry_count: int,
    ) -> None:
        """Handle failed operation."""
        async with self._lock:
            # Update statistics
            stats = self.retry_stats[operation_name]
            stats["failed_attempts"] += 1
            stats["retry_count"] += retry_count

            # Update circuit breaker
            if self.circuit_config.enabled and operation_name in self.circuit_breakers:
                circuit = self.circuit_breakers[operation_name]
                current_time = time.time()

                circuit.failure_count += 1
                circuit.last_failure_time = current_time

                # Check if we should open the circuit
                if (
                    circuit.state == CircuitState.CLOSED
                    and circuit.failure_count >= self.circuit_config.failure_threshold
                ):
                    circuit.state = CircuitState.OPEN
                    circuit.next_attempt_time = (
                        current_time + self.circuit_config.recovery_timeout_seconds
                    )
                    stats["circuit_breaker_trips"] += 1

                    logger.warning(
                        f"Circuit breaker for {operation_name} opened after {circuit.failure_count} failures"
                    )

                    # Trigger alert
                    await self.alert_manager.trigger_alert(
                        name="circuit_breaker_opened",
                        severity=AlertSeverity.ERROR,
                        message=f"Circuit breaker opened for {operation_name}",
                        context={
                            "operation": operation_name,
                            "failure_count": circuit.failure_count,
                            "error_type": error_type.value,
                        },
                    )

                elif circuit.state == CircuitState.HALF_OPEN:
                    # Failure in half-open state - reopen circuit
                    circuit.state = CircuitState.OPEN
                    circuit.next_attempt_time = (
                        current_time + self.circuit_config.recovery_timeout_seconds
                    )
                    stats["circuit_breaker_trips"] += 1

                    logger.warning(
                        f"Circuit breaker for {operation_name} reopened from half-open state"
                    )

        logger.error(
            f"Operation {operation_name} failed after {retry_count} retries: {error_type.value}"
        )

    async def execute_query_with_retry(
        self,
        query: str,
        *args,
        operation_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Execute database query with retry logic."""
        if not operation_name:
            # Generate operation name from query
            operation_name = self._generate_operation_name(query)

        async def query_operation():
            async with self.db_pool.acquire() as conn:
                if timeout:
                    return await conn.fetch(query, *args, timeout=timeout)
                else:
                    return await conn.fetch(query, *args)

        return await self.execute_with_retry(query_operation, operation_name)

    def _generate_operation_name(self, query: str) -> str:
        """Generate operation name from query."""
        # Extract first word and table name
        query_upper = query.strip().upper()

        if query_upper.startswith("SELECT"):
            # For SELECT, extract table name after FROM
            if "FROM" in query_upper:
                from_part = query_upper.split("FROM")[1].split()[0]
                return f"select_{from_part.lower()}"
        elif query_upper.startswith("INSERT"):
            # For INSERT, extract table name
            if "INTO" in query_upper:
                into_part = query_upper.split("INTO")[1].split()[0]
                return f"insert_{into_part.lower()}"
        elif query_upper.startswith("UPDATE"):
            # For UPDATE, extract table name
            update_part = query_upper.split()[1]
            return f"update_{update_part.lower()}"
        elif query_upper.startswith("DELETE"):
            # For DELETE, extract table name
            if "FROM" in query_upper:
                from_part = query_upper.split("FROM")[1].split()[0]
                return f"delete_{from_part.lower()}"

        # Fallback to hash
        import hashlib

        return f"query_{hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()[:8]}"

    async def execute_transaction_with_retry(
        self,
        transaction_func: Callable,
        operation_name: str = "database_transaction",
        isolation_level: Optional[str] = None,
    ) -> Any:
        """Execute database transaction with retry logic."""

        async def transaction_operation():
            async with self.db_pool.acquire() as conn:
                async with conn.transaction(isolation=isolation_level):
                    return await transaction_func(conn)

        return await self.execute_with_retry(transaction_operation, operation_name)

    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get comprehensive retry statistics."""
        stats = {
            "total_operations": sum(
                s["total_attempts"] for s in self.retry_stats.values()
            ),
            "successful_operations": sum(
                s["successful_attempts"] for s in self.retry_stats.values()
            ),
            "failed_operations": sum(
                s["failed_attempts"] for s in self.retry_stats.values()
            ),
            "total_retries": sum(s["retry_count"] for s in self.retry_stats.values()),
            "circuit_breaker_trips": sum(
                s["circuit_breaker_trips"] for s in self.retry_stats.values()
            ),
            "success_rate": 0.0,
            "avg_retry_time": 0.0,
            "operations": {},
        }

        total_attempts = stats["total_operations"]
        if total_attempts > 0:
            stats["success_rate"] = (
                stats["successful_operations"] / total_attempts
            ) * 100

        total_retry_time = sum(
            s["avg_retry_time"] * s["total_attempts"] for s in self.retry_stats.values()
        )
        if total_attempts > 0:
            stats["avg_retry_time"] = total_retry_time / total_attempts

        # Per-operation statistics
        for operation_name, operation_stats in self.retry_stats.items():
            if operation_stats["total_attempts"] > 0:
                success_rate = (
                    operation_stats["successful_attempts"]
                    / operation_stats["total_attempts"]
                ) * 100
            else:
                success_rate = 0.0

            stats["operations"][operation_name] = {
                "total_attempts": operation_stats["total_attempts"],
                "successful_attempts": operation_stats["successful_attempts"],
                "failed_attempts": operation_stats["failed_attempts"],
                "retry_count": operation_stats["retry_count"],
                "success_rate": success_rate,
                "avg_retry_time": operation_stats["avg_retry_time"],
                "circuit_breaker_trips": operation_stats["circuit_breaker_trips"],
                "last_attempt": operation_stats["last_attempt"],
            }

        # Circuit breaker status
        stats["circuit_breakers"] = {}
        for operation_name, circuit in self.circuit_breakers.items():
            stats["circuit_breakers"][operation_name] = {
                "state": circuit.state.value,
                "failure_count": circuit.failure_count,
                "success_count": circuit.success_count,
                "last_failure_time": circuit.last_failure_time,
                "last_success_time": circuit.last_success_time,
                "next_attempt_time": circuit.next_attempt_time,
            }

        return stats

    async def reset_circuit_breaker(self, operation_name: str) -> bool:
        """Reset circuit breaker for specific operation."""
        if operation_name in self.circuit_breakers:
            self.circuit_breakers[operation_name] = CircuitBreakerState(
                state=CircuitState.CLOSED,
                failure_count=0,
                last_failure_time=0,
                last_success_time=0,
                next_attempt_time=0,
            )
            logger.info(f"Circuit breaker reset for {operation_name}")
            return True
        return False

    async def reset_all_circuit_breakers(self) -> int:
        """Reset all circuit breakers."""
        reset_count = 0
        for operation_name in list(self.circuit_breakers.keys()):
            if await self.reset_circuit_breaker(operation_name):
                reset_count += 1

        logger.info(f"Reset {reset_count} circuit breakers")
        return reset_count

    def update_retry_config(self, **kwargs) -> None:
        """Update retry configuration."""
        for key, value in kwargs.items():
            if hasattr(self.retry_config, key):
                setattr(self.retry_config, key, value)
                logger.info(f"Updated retry config {key} = {value}")

    def update_circuit_config(self, **kwargs) -> None:
        """Update circuit breaker configuration."""
        for key, value in kwargs.items():
            if hasattr(self.circuit_config, key):
                setattr(self.circuit_config, key, value)
                logger.info(f"Updated circuit config {key} = {value}")

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for all operations."""
        status = {
            "enabled": self.circuit_config.enabled,
            "total_circuits": len(self.circuit_breakers),
            "open_circuits": 0,
            "half_open_circuits": 0,
            "closed_circuits": 0,
            "circuits": {},
        }

        for operation_name, circuit in self.circuit_breakers.items():
            if circuit.state == CircuitState.OPEN:
                status["open_circuits"] += 1
            elif circuit.state == CircuitState.HALF_OPEN:
                status["half_open_circuits"] += 1
            else:
                status["closed_circuits"] += 1

            status["circuits"][operation_name] = {
                "state": circuit.state.value,
                "failure_count": circuit.failure_count,
                "success_count": circuit.success_count,
                "last_failure_time": circuit.last_failure_time,
                "next_attempt_time": circuit.next_attempt_time,
                "time_to_recovery": max(0, circuit.next_attempt_time - time.time()),
            }

        return status


# Global retry handler instance
_retry_handler: RetryHandler | None = None


def get_retry_handler() -> RetryHandler:
    """Get global retry handler instance."""
    global _retry_handler
    if _retry_handler is None:
        raise RuntimeError(
            "Retry handler not initialized. Call init_retry_handler() first."
        )
    return _retry_handler


async def init_retry_handler(
    db_pool: asyncpg.Pool,
    retry_config: Optional[RetryConfig] = None,
    circuit_config: Optional[CircuitBreakerConfig] = None,
    alert_manager: Optional[Any] = None,
) -> RetryHandler:
    """Initialize global retry handler."""
    global _retry_handler
    _retry_handler = RetryHandler(db_pool, retry_config, circuit_config, alert_manager)
    return _retry_handler
