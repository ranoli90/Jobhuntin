"""Structured error handling utilities.

Provides decorators and context managers for consistent error handling
with proper logging and metrics.
"""

from __future__ import annotations

import functools
from contextlib import contextmanager
from typing import Any, Callable, TypeVar

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.errors")

F = TypeVar("F", bound=Callable[..., Any])


class AppError(Exception):
    """Base application error with structured context."""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(AppError):
    """Input validation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class RateLimitError(AppError):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: int | None = None):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after},
        )


def handle_errors(
    operation: str,
    reraise: bool = True,
    default_return: Any = None,
    log_level: str = "error",
) -> Callable[[F], F]:
    """Decorator for consistent error handling.

    Args:
        operation: Name of the operation for logging
        reraise: Whether to re-raise the exception
        default_return: Value to return if not reraising
        log_level: Log level for errors
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except AppError:
                raise
            except Exception as exc:
                incr("error", {"operation": operation, "type": type(exc).__name__})
                log_func = getattr(logger, log_level)
                log_func(
                    f"Error in {operation}: {exc}",
                    extra={"operation": operation, "error": str(exc)},
                    exc_info=True,
                )
                if reraise:
                    raise AppError(
                        message=f"Failed to {operation}",
                        code="INTERNAL_ERROR",
                        details={"original_error": str(exc)},
                    ) from exc
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except AppError:
                raise
            except Exception as exc:
                incr("error", {"operation": operation, "type": type(exc).__name__})
                log_func = getattr(logger, log_level)
                log_func(
                    f"Error in {operation}: {exc}",
                    extra={"operation": operation, "error": str(exc)},
                    exc_info=True,
                )
                if reraise:
                    raise AppError(
                        message=f"Failed to {operation}",
                        code="INTERNAL_ERROR",
                        details={"original_error": str(exc)},
                    ) from exc
                return default_return

        # Return appropriate wrapper based on whether func is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


@contextmanager
def error_context(operation: str, **context: Any):
    """Context manager for error handling with context.

    Usage:
        with error_context("process_payment", user_id=user_id):
            process_payment(amount)
    """
    try:
        yield
    except Exception as exc:
        incr("error", {"operation": operation, "type": type(exc).__name__})
        logger.error(
            f"Error in {operation}: {exc}",
            extra={"operation": operation, "context": context, "error": str(exc)},
            exc_info=True,
        )
        raise
