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
                    logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
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
            
            observe(f"circuit_breaker.call.duration", elapsed, {"name": self.name, "success": "true"})
            incr("circuit_breaker.call.success", {"name": self.name})
            return result
            
        except self.expected_exception as e:
            # Failure
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.state == CircuitState.HALF_OPEN:
                    # Failed in half-open - open circuit again
                    self.state = CircuitState.OPEN
                    self.success_count = 0
                    logger.warning(f"Circuit breaker {self.name} OPEN (failed in half-open)")
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
            
            observe(f"circuit_breaker.call.duration", 0, {"name": self.name, "success": "false"})
            incr("circuit_breaker.call.failure", {"name": self.name})
            raise


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request is rejected."""
    pass


# Global circuit breakers for common services
_openrouter_breaker: CircuitBreaker | None = None
_email_breaker: CircuitBreaker | None = None
_storage_breaker: CircuitBreaker | None = None


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
