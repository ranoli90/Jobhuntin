"""API Error Handler - Consistent error handling for API endpoints.

This module provides utilities to reduce code duplication in API error handling.
Instead of repeating:
    except Exception as e:
        logger.error(f"Failed to <action>: {e}")
        raise HTTPException(status_code=500, detail="Failed to <action>")

You can use:
    @handle_api_error("create_user")
    async def create_user(...):
        ...

Or use the handle_error helper:
    try:
        await do_something()
    except Exception as e:
        handle_error(e, "do_something")

Usage:
    from shared.api_error_handler import handle_api_error, handle_error, api_error_context
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from fastapi import HTTPException

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.api_errors")

F = TypeVar("F", bound=Callable[..., Any])


def handle_error(
    exc: Exception,
    operation: str,
    message: str | None = None,
    status_code: int = 500,
    reraise: bool = True,
) -> None:
    """Handle an error with consistent logging and HTTPException raising.

    This is a utility function that handles the common pattern of logging an error
    and raising an HTTPException with a standardized message.

    Args:
        exc: The exception that was caught
        operation: The name of the operation (e.g., "create_user", "fetch_job")
        message: Optional custom error message. If not provided, a default will be generated.
        status_code: HTTP status code to return (default 500)
        reraise: Whether to re-raise as HTTPException (default True)

    Example:
        try:
            await db.create_user(...)
        except Exception as e:
            handle_error(e, "create_user")
    """
    error_msg = str(exc)
    operation_human = operation.replace("_", " ")
    
    if message is None:
        display_message = f"Failed to {operation_human}"
    else:
        display_message = message

    # Log the error with structured data
    logger.error(
        f"Failed to {operation}: {error_msg}",
        extra={
            "operation": operation,
            "error": error_msg,
            "error_type": type(exc).__name__,
        },
        exc_info=True,
    )

    # Increment error metric
    incr("error", {"operation": operation, "type": type(exc).__name__})

    if reraise:
        raise HTTPException(
            status_code=status_code,
            detail=display_message,
        )


def handle_database_error(
    exc: Exception,
    operation: str,
    reraise: bool = True,
) -> None:
    """Handle database errors with consistent logging.

    Args:
        exc: The database exception that was caught
        operation: The name of the database operation
        reraise: Whether to re-raise as HTTPException (default True)

    Example:
        try:
            await db.query(...)
        except Exception as e:
            handle_database_error(e, "fetch_user_profiles")
    """
    error_msg = str(exc)
    operation_human = operation.replace("_", " ")

    logger.error(
        f"Database error during {operation}: {error_msg}",
        extra={
            "operation": operation,
            "error": error_msg,
            "error_type": type(exc).__name__,
            "category": "database",
        },
        exc_info=True,
    )

    incr("error", {"operation": operation, "type": type(exc).__name__, "category": "database"})

    if reraise:
        raise HTTPException(
            status_code=500,
            detail=f"Database error during {operation_human}",
        )


def handle_validation_error(
    field: str,
    message: str | None = None,
    status_code: int = 422,
) -> None:
    """Raise a validation error HTTPException.

    Args:
        field: The field that failed validation
        message: Optional custom error message
        status_code: HTTP status code (default 422 for validation errors)

    Example:
        if not email:
            handle_validation_error("email", "Email is required")
    """
    if message is None:
        message = f"Invalid value for field: {field}"

    logger.warning(
        f"Validation error: {message}",
        extra={"field": field, "error": message},
    )

    raise HTTPException(
        status_code=status_code,
        detail={"field": field, "message": message},
    )


def handle_not_found(
    resource: str,
    identifier: str | None = None,
) -> None:
    """Raise a not found HTTPException.

    Args:
        resource: The type of resource (e.g., "User", "Job")
        identifier: Optional identifier that wasn't found

    Example:
        user = await get_user(user_id)
        if not user:
            handle_not_found("User", user_id)
    """
    if identifier:
        message = f"{resource} not found: {identifier}"
    else:
        message = f"{resource} not found"

    logger.warning(
        message,
        extra={"resource": resource, "identifier": identifier},
    )

    raise HTTPException(
        status_code=404,
        detail=message,
    )


def handle_forbidden(
    message: str = "Access denied",
) -> None:
    """Raise a forbidden HTTPException.

    Args:
        message: Custom error message

    Example:
        if not user.has_permission("edit_jobs"):
            handle_forbidden("You don't have permission to edit jobs")
    """
    logger.warning(
        message,
        extra={"error_type": "forbidden"},
    )

    raise HTTPException(
        status_code=403,
        detail=message,
    )


def handle_unauthorized(
    message: str = "Authentication required",
) -> None:
    """Raise an unauthorized HTTPException.

    Args:
        message: Custom error message

    Example:
        if not token:
            handle_unauthorized()
    """
    logger.warning(
        message,
        extra={"error_type": "unauthorized"},
    )

    raise HTTPException(
        status_code=401,
        detail=message,
    )


def handle_rate_limit(
    message: str = "Rate limit exceeded. Please try again later.",
    retry_after: int | None = None,
) -> None:
    """Raise a rate limit HTTPException.

    Args:
        message: Custom error message
        retry_after: Optional seconds until retry is allowed

    Example:
        if is_rate_limited():
            handle_rate_limit(retry_after=60)
    """
    logger.warning(
        message,
        extra={"error_type": "rate_limit", "retry_after": retry_after},
    )

    raise HTTPException(
        status_code=429,
        detail=message,
        headers={"Retry-After": str(retry_after)} if retry_after else None,
    )


class api_error_context:
    """Context manager for handling errors within a specific operation.

    Usage:
        with api_error_context("process_payment", user_id=user_id):
            payment = await process(amount)

    This will automatically:
    - Log any errors that occur
    - Increment error metrics
    - Raise HTTPException with appropriate message
    """

    def __init__(self, operation: str, **context: Any):
        """Initialize the error context.

        Args:
            operation: Name of the operation being performed
            **context: Additional context to include in logs
        """
        self.operation = operation
        self.context = context
        self._operation_human = operation.replace("_", " ")

    def __enter__(self) -> None:
        """Enter the context."""
        return None

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Exit the context and handle any exceptions."""
        if exc_type is None:
            # No exception, success
            return False

        # We have an exception - handle it
        error_msg = str(exc_val) if exc_val else "Unknown error"

        logger.error(
            f"Failed to {self._operation_human}: {error_msg}",
            extra={
                "operation": self.operation,
                "error": error_msg,
                "error_type": exc_type.__name__ if exc_type else "Unknown",
                **self.context,
            },
            exc_info=True,
        )

        incr(
            "error",
            {"operation": self.operation, "type": exc_type.__name__ if exc_type else "Unknown"},
        )

        # Re-raise as HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Failed to {self._operation_human}",
        )


def handle_api_error(
    operation: str,
    status_code: int = 500,
) -> Callable[[F], F]:
    """Decorator for consistent API error handling.

    This decorator wraps an async or sync function to handle exceptions
    consistently with logging and proper HTTPException raising.

    Args:
        operation: Name of the operation (used in logs and error messages)
        status_code: HTTP status code to return on error (default 500)

    Returns:
        A decorator function that wraps the target function

    Example:
        @handle_api_error("create_job")
        async def create_job(request: CreateJobRequest):
            # Your logic here
            pass

        # Or with custom status code:
        @handle_api_error("update_profile", status_code=400)
        async def update_profile(user_id: str, data: ProfileData):
            pass
    """
    operation_human = operation.replace("_", " ")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPExceptions as-is (they're already handled)
                raise
            except Exception as exc:
                logger.error(
                    f"Failed to {operation_human}: {exc}",
                    extra={
                        "operation": operation,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    exc_info=True,
                )
                incr("error", {"operation": operation, "type": type(exc).__name__})
                raise HTTPException(
                    status_code=status_code,
                    detail=f"Failed to {operation_human}",
                )

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(
                    f"Failed to {operation_human}: {exc}",
                    extra={
                        "operation": operation,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    exc_info=True,
                )
                incr("error", {"operation": operation, "type": type(exc).__name__})
                raise HTTPException(
                    status_code=status_code,
                    detail=f"Failed to {operation_human}",
                )

        # Return appropriate wrapper based on whether func is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator
