"""
Circuit Breaker implementation for external service calls.

Provides automatic failure detection and recovery with configurable thresholds.
Uses the Circuit Breaker pattern to prevent cascading failures.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from shared.logging_config import get_logger

logger = get_logger("sorce.circuit_breaker")

T = TypeVar('T')


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation, requests flow through
    OPEN = "open"          # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""
    name: str
    failure_threshold: int = 5       # Number of failures before opening
    success_threshold: int = 2       # Successes needed to close in half-open
    timeout_seconds: float = 30.0    # How long to wait before trying again
    half_open_max_calls: int = 3     # Max concurrent calls in half-open state


@dataclass
class CircuitStats:
    """Runtime statistics for a circuit breaker."""
    failures: int = 0
    successes: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    half_open_calls: int = 0


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is open and rejects a request."""
    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker '{name}' is open. Retry after {retry_after:.1f}s")


@dataclass
class CircuitBreaker:
    """
    Circuit Breaker for protecting external service calls.
    
    Usage:
        cb = CircuitBreaker(CircuitBreakerConfig(name="llm"))
        
        async def call_llm():
            async with cb:
                return await make_llm_request()
    
    Or as a decorator:
        @cb.protect
        async def call_llm():
            return await make_llm_request()
    """
    config: CircuitBreakerConfig
    state: CircuitState = field(default=CircuitState.CLOSED)
    stats: CircuitStats = field(default_factory=CircuitStats)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _opened_at: float = 0.0

    async def __aenter__(self) -> "CircuitBreaker":
        await self._before_call()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_type is None:
            await self._on_success()
        else:
            await self._on_failure(exc_val)
        return False  # Don't suppress exceptions

    async def _before_call(self) -> None:
        """Check state before allowing a call through."""
        async with self._lock:
            now = time.monotonic()
            self.stats.total_calls += 1

            if self.state == CircuitState.OPEN:
                # Check if timeout has passed
                if now - self._opened_at >= self.config.timeout_seconds:
                    logger.info(
                        "Circuit %s transitioning to half-open after timeout",
                        self.config.name
                    )
                    self.state = CircuitState.HALF_OPEN
                    self.stats.half_open_calls = 0
                else:
                    retry_after = self.config.timeout_seconds - (now - self._opened_at)
                    raise CircuitBreakerOpen(self.config.name, retry_after)

            if self.state == CircuitState.HALF_OPEN:
                if self.stats.half_open_calls >= self.config.half_open_max_calls:
                    retry_after = 1.0  # Short wait before next attempt
                    raise CircuitBreakerOpen(self.config.name, retry_after)
                self.stats.half_open_calls += 1

    async def _on_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self.stats.successes += 1
            self.stats.total_successes += 1
            self.stats.last_success_time = time.monotonic()

            if self.state == CircuitState.HALF_OPEN:
                if self.stats.successes >= self.config.success_threshold:
                    logger.info(
                        "Circuit %s closing after %d successes",
                        self.config.name,
                        self.stats.successes
                    )
                    self.state = CircuitState.CLOSED
                    self.stats.failures = 0
                    self.stats.successes = 0

            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.stats.failures = 0

    async def _on_failure(self, error: Exception) -> None:
        """Record a failed call."""
        async with self._lock:
            self.stats.failures += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = time.monotonic()

            logger.warning(
                "Circuit %s recorded failure #%d: %s",
                self.config.name,
                self.stats.failures,
                str(error)[:100]
            )

            if self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                logger.warning(
                    "Circuit %s reopening after failure in half-open state",
                    self.config.name
                )
                self.state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                self.stats.successes = 0

            elif self.state == CircuitState.CLOSED:
                if self.stats.failures >= self.config.failure_threshold:
                    logger.error(
                        "Circuit %s opening after %d failures",
                        self.config.name,
                        self.stats.failures
                    )
                    self.state = CircuitState.OPEN
                    self._opened_at = time.monotonic()

    def protect(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """Decorator to protect an async function with this circuit breaker."""
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async with self:
                return await func(*args, **kwargs)
        return wrapper

    def get_status(self) -> dict:
        """Get current circuit breaker status for monitoring."""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "failures": self.stats.failures,
            "successes": self.stats.successes,
            "total_calls": self.stats.total_calls,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
        }


# Global circuit breakers for common services
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, **config_overrides: Any) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        # Default configs for known services
        defaults = {
            "llm": {"failure_threshold": 3, "timeout_seconds": 60.0},
            "stripe": {"failure_threshold": 5, "timeout_seconds": 30.0},
            "supabase": {"failure_threshold": 5, "timeout_seconds": 15.0},
            "adzuna": {"failure_threshold": 10, "timeout_seconds": 120.0},
            "resend": {"failure_threshold": 5, "timeout_seconds": 30.0},
        }
        config_kwargs = {"name": name, **defaults.get(name, {}), **config_overrides}
        config = CircuitBreakerConfig(**config_kwargs)
        _circuit_breakers[name] = CircuitBreaker(config)
    return _circuit_breakers[name]


def get_all_circuit_breaker_statuses() -> list[dict]:
    """Get status of all circuit breakers for health checks."""
    return [cb.get_status() for cb in _circuit_breakers.values()]
