"""Retry Utilities - Exponential backoff and resilient operations.

Provides configurable retry mechanisms with exponential backoff,
jitter, and circuit breaker patterns for reliable operations.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, TypeVar

from shared.logging_config import get_logger

logger = get_logger("sorce.retry")

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Multiplier for exponential backoff
    jitter: bool = True  # Add random jitter to prevent thundering herd
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number with exponential backoff."""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add ±25% random jitter
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, attempts: int, last_exception: Exception):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


async def retry_async(
    config: RetryConfig, operation_name: str = "operation"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for async functions with retry logic."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)

                    if attempt > 1:
                        logger.info(
                            f"[RETRY] {operation_name} succeeded on attempt {attempt}",
                            extra={"operation": operation_name, "attempt": attempt},
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if exception is retryable
                    if not isinstance(e, config.retryable_exceptions):
                        logger.error(
                            f"[RETRY] {operation_name} failed with non-retryable error: {e}",
                            extra={"operation": operation_name, "attempt": attempt},
                        )
                        raise

                    # Check if this was the last attempt
                    if attempt == config.max_attempts:
                        logger.error(
                            f"[RETRY] {operation_name} failed after {attempt} attempts",
                            extra={
                                "operation": operation_name,
                                "attempts": attempt,
                                "final_error": str(e),
                            },
                        )
                        raise RetryError(
                            f"Operation '{operation_name}' failed after {attempt} attempts",
                            attempts=attempt,
                            last_exception=e,
                        ) from e

                    # Calculate delay for next attempt
                    delay = config.get_delay(attempt)

                    logger.warning(
                        f"[RETRY] {operation_name} failed on attempt {attempt}, retrying in {delay:.2f}s: {e}",
                        extra={
                            "operation": operation_name,
                            "attempt": attempt,
                            "delay": delay,
                            "error": str(e),
                        },
                    )

                    await asyncio.sleep(delay)

            # This should never be reached
            raise RetryError(
                f"Unexpected error in retry logic for {operation_name}",
                attempts=config.max_attempts,
                last_exception=last_exception or Exception("Unknown error"),
            )

        return wrapper

    return decorator


def retry_sync(
    config: RetryConfig, operation_name: str = "operation"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for sync functions with retry logic."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = func(*args, **kwargs)

                    if attempt > 1:
                        logger.info(
                            f"[RETRY] {operation_name} succeeded on attempt {attempt}",
                            extra={"operation": operation_name, "attempt": attempt},
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if exception is retryable
                    if not isinstance(e, config.retryable_exceptions):
                        logger.error(
                            f"[RETRY] {operation_name} failed with non-retryable error: {e}",
                            extra={"operation": operation_name, "attempt": attempt},
                        )
                        raise

                    # Check if this was the last attempt
                    if attempt == config.max_attempts:
                        logger.error(
                            f"[RETRY] {operation_name} failed after {attempt} attempts",
                            extra={
                                "operation": operation_name,
                                "attempts": attempt,
                                "final_error": str(e),
                            },
                        )
                        raise RetryError(
                            f"Operation '{operation_name}' failed after {attempt} attempts",
                            attempts=attempt,
                            last_exception=e,
                        ) from e

                    # Calculate delay for next attempt
                    delay = config.get_delay(attempt)

                    logger.warning(
                        f"[RETRY] {operation_name} failed on attempt {attempt}, retrying in {delay:.2f}s: {e}",
                        extra={
                            "operation": operation_name,
                            "attempt": attempt,
                            "delay": delay,
                            "error": str(e),
                        },
                    )

                    time.sleep(delay)

            # This should never be reached
            raise RetryError(
                f"Unexpected error in retry logic for {operation_name}",
                attempts=config.max_attempts,
                last_exception=last_exception or Exception("Unknown error"),
            )

        return wrapper

    return decorator


# Predefined retry configurations
class RetryConfigs:
    """Common retry configurations for different scenarios."""

    # For database operations - quick retries for transient issues
    DATABASE = RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=True,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            # Add specific database exceptions as needed
        ),
    )

    # For external API calls - longer delays, more attempts
    EXTERNAL_API = RetryConfig(
        max_attempts=5,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            # Add HTTP-specific exceptions as needed
        ),
    )

    # For file operations - quick retries
    FILE_OPERATIONS = RetryConfig(
        max_attempts=3,
        base_delay=0.2,
        max_delay=2.0,
        exponential_base=2.0,
        jitter=True,
        retryable_exceptions=(
            OSError,
            IOError,
            PermissionError,
        ),
    )

    # For critical operations - aggressive retry
    CRITICAL = RetryConfig(
        max_attempts=7,
        base_delay=0.1,
        max_delay=10.0,
        exponential_base=1.5,
        jitter=True,
        retryable_exceptions=(Exception,),
    )


# Convenience decorators
@retry_async(RetryConfigs.DATABASE, "database operation")
async def retry_database_async(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for database operations with retry logic."""
    return func


@retry_async(RetryConfigs.EXTERNAL_API, "external API call")
async def retry_api_async(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for external API calls with retry logic."""
    return func


@retry_sync(RetryConfigs.FILE_OPERATIONS, "file operation")
def retry_file_sync(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for file operations with retry logic."""
    return func


# Circuit breaker pattern
class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self._call_async(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return self._call_sync(func, *args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    async def _call_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("[CIRCUIT_BREAKER] Attempting to reset circuit")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _call_sync(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("[CIRCUIT_BREAKER] Attempting to reset circuit")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self) -> None:
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("[CIRCUIT_BREAKER] Circuit reset to CLOSED")

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"[CIRCUIT_BREAKER] Circuit opened after {self.failure_count} failures"
            )
