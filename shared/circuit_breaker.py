"""Circuit breaker pattern for external API calls.

Prevents cascading failures by stopping requests to failing services.
"""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any, Callable

from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for external service calls.

    Prevents cascading failures by:
    - Opening circuit after failure threshold
    - Rejecting requests when open
    - Testing recovery in half-open state
    - Closing circuit when service recovers
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
        expected_exception: type[Exception] | tuple[type[Exception], ...] = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            name: Circuit breaker name (for logging/metrics)
            failure_threshold: Number of failures before opening
            success_threshold: Number of successes in half-open to close
            timeout_seconds: Time before attempting recovery (half-open)
            expected_exception: Exception types that count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self._lock = asyncio.Lock()

    async def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If function call fails
        """
        async with self._lock:
            # Check circuit state
            if self.state == CircuitState.OPEN:
                # Check if timeout has passed
                if (
                    self.last_failure_time
                    and time.time() - self.last_failure_time > self.timeout_seconds
                ):
                    # Transition to half-open
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(
                        f"Circuit breaker {self.name} transitioning to HALF_OPEN"
                    )
                else:
                    # Still open, reject request
                    incr("circuit_breaker.rejected", {"name": self.name})
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Service unavailable. Retry after timeout."
                    )

        # Attempt call
        try:
            start_time = time.time()
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time

            # Success
            async with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= self.success_threshold:
                        # Recovered - close circuit
                        self.state = CircuitState.CLOSED
                        self.failure_count = 0
                        logger.info(f"Circuit breaker {self.name} CLOSED (recovered)")
                        incr("circuit_breaker.closed", {"name": self.name})
                elif self.state == CircuitState.CLOSED:
                    # Reset failure count on success
                    self.failure_count = 0

            observe(
                "circuit_breaker.call.duration",
                elapsed,
                {"name": self.name, "success": "true"},
            )
            incr("circuit_breaker.call.success", {"name": self.name})
            return result

        except self.expected_exception:
            # Failure
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.state == CircuitState.HALF_OPEN:
                    # Failed in half-open - open circuit again
                    self.state = CircuitState.OPEN
                    self.success_count = 0
                    logger.warning(
                        f"Circuit breaker {self.name} OPEN (failed in half-open)"
                    )
                elif (
                    self.state == CircuitState.CLOSED
                    and self.failure_count >= self.failure_threshold
                ):
                    # Too many failures - open circuit
                    self.state = CircuitState.OPEN
                    logger.error(
                        f"Circuit breaker {self.name} OPEN "
                        f"(failure_count={self.failure_count})"
                    )
                    incr("circuit_breaker.opened", {"name": self.name})

            observe(
                "circuit_breaker.call.duration",
                0,
                {"name": self.name, "success": "false"},
            )
            incr("circuit_breaker.call.failure", {"name": self.name})
            raise


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request is rejected."""

    pass


# Global circuit breakers for common services
_openrouter_breaker: CircuitBreaker | None = None
_email_breaker: CircuitBreaker | None = None
_storage_breaker: CircuitBreaker | None = None
_breakers: dict[str, CircuitBreaker] = {}


def get_openrouter_breaker() -> CircuitBreaker:
    """Get circuit breaker for OpenRouter API."""
    global _openrouter_breaker
    if _openrouter_breaker is None:
        _openrouter_breaker = CircuitBreaker(
            name="openrouter",
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60.0,
            expected_exception=(Exception,),
        )
    return _openrouter_breaker


def get_email_breaker() -> CircuitBreaker:
    """Get circuit breaker for email service."""
    global _email_breaker
    if _email_breaker is None:
        _email_breaker = CircuitBreaker(
            name="email_service",
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60.0,
            expected_exception=(Exception,),
        )
    return _email_breaker


def get_storage_breaker() -> CircuitBreaker:
    """Get circuit breaker for storage service."""
    global _storage_breaker
    if _storage_breaker is None:
        _storage_breaker = CircuitBreaker(
            name="storage_service",
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60.0,
            expected_exception=(Exception,),
        )
    return _storage_breaker


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name.

    Args:
        name: Circuit breaker name (e.g., "resend", "stripe", "embeddings")

    Returns:
        CircuitBreaker instance for the given name
    """
    global _breakers
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60.0,
            expected_exception=(Exception,),
        )
    return _breakers[name]


def get_all_circuit_breaker_statuses() -> dict[str, dict[str, Any]]:
    """Get status of all circuit breakers.

    Returns:
        Dictionary mapping circuit breaker names to their status
    """
    statuses: dict[str, dict[str, Any]] = {}

    # Add named breakers
    for name, breaker in _breakers.items():
        statuses[name] = {
            "state": breaker.state.value,
            "failure_count": breaker.failure_count,
            "success_count": breaker.success_count,
            "last_failure_time": breaker.last_failure_time,
        }

    # Add specific breakers if they exist
    if _openrouter_breaker:
        statuses["openrouter"] = {
            "state": _openrouter_breaker.state.value,
            "failure_count": _openrouter_breaker.failure_count,
            "success_count": _openrouter_breaker.success_count,
            "last_failure_time": _openrouter_breaker.last_failure_time,
        }

    if _email_breaker:
        statuses["email_service"] = {
            "state": _email_breaker.state.value,
            "failure_count": _email_breaker.failure_count,
            "success_count": _email_breaker.success_count,
            "last_failure_time": _email_breaker.last_failure_time,
        }

    if _storage_breaker:
        statuses["storage_service"] = {
            "state": _storage_breaker.state.value,
            "failure_count": _storage_breaker.failure_count,
            "success_count": _storage_breaker.success_count,
            "last_failure_time": _storage_breaker.last_failure_time,
        }

    return statuses
