"""Standardized error response format for API endpoints.

This module provides:
- Standard error codes for consistent error handling
- Custom exception classes for different error types
- FastAPI exception handlers for automatic error formatting
- Helper functions for creating standardized error responses

Usage:
    from shared.error_responses import (
        ErrorCodes,
        APIError,
        ValidationError,
        AuthenticationError,
        NotFoundError,
        RateLimitError,
        register_exception_handlers,
    )

    # In main.py:
    register_exception_handlers(app)

    # In endpoints:
    raise AuthenticationError("Invalid token")
    raise NotFoundError("User", "123")
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from shared.middleware import get_request_id


# ---------------------------------------------------------------------------
# Error Codes
# ---------------------------------------------------------------------------


class ErrorCodes:
    """Standard error codes for API responses.

    These codes provide programmatic error handling for clients.
    """

    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Authentication errors (401)
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    MISSING_CREDENTIALS = "MISSING_CREDENTIALS"

    # Authorization errors (403)
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    ACCESS_DENIED = "ACCESS_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    TENANT_ACCESS_DENIED = "TENANT_ACCESS_DENIED"

    # Not found errors (404)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    APPLICATION_NOT_FOUND = "APPLICATION_NOT_FOUND"

    # Conflict errors (409)
    CONFLICT = "CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    INVALID_STATE = "INVALID_STATE"

    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Server errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

    # Service unavailable (503)
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Detailed error information for a specific field or aspect."""

    field: str | None = Field(default=None, description="Field that caused the error")
    message: str = Field(description="Error message for this detail")
    code: str | None = Field(default=None, description="Specific error code for this detail")


class ErrorInfo(BaseModel):
    """Error information structure for API responses."""

    code: str = Field(description="Standard error code")
    message: str = Field(description="Human-readable error message")
    details: list[ErrorDetail] = Field(
        default_factory=list, description="Detailed error list"
    )


class ErrorResponse(BaseModel):
    """Standard error response format.

    Format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": [...]
        },
        "request_id": "abc-123",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """

    error: ErrorInfo = Field(description="Error information")
    request_id: str | None = Field(default=None, description="Request tracking ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO8601 timestamp",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": [{"field": "email", "message": "Invalid email format"}],
                },
                "request_id": "abc-123",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


# ---------------------------------------------------------------------------
# Custom Exception Classes
# ---------------------------------------------------------------------------


class APIError(HTTPException):
    """Base exception for API errors with standardized response format.

    All custom API exceptions should inherit from this class.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: list[ErrorDetail] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            code: Standard error code from ErrorCodes
            message: Human-readable error message
            status_code: HTTP status code
            details: Optional list of detailed errors
            headers: Optional HTTP headers to include in response
        """
        self.code = code
        self.message = message
        self.details = details or []
        super().__init__(status_code=status_code, detail=message, headers=headers)

    def to_response(self, request_id: str | None = None) -> dict[str, Any]:
        """Convert error to response dictionary.

        Args:
            request_id: Optional request tracking ID

        Returns:
            Dictionary matching ErrorResponse format
        """
        return ErrorResponse(
            error=ErrorInfo(
                code=self.code,
                message=self.message,
                details=self.details,
            ),
            request_id=request_id,
        ).model_dump()


class ValidationError(APIError):
    """Exception for validation errors (400 Bad Request)."""

    def __init__(
        self,
        message: str = "Validation error",
        details: list[ErrorDetail] | None = None,
        field_errors: dict[str, str] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error message
            details: Optional list of detailed errors
            field_errors: Optional dict of field names to error messages
        """
        if field_errors and not details:
            details = [
                ErrorDetail(field=field, message=msg)
                for field, msg in field_errors.items()
            ]
        super().__init__(
            code=ErrorCodes.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class AuthenticationError(APIError):
    """Exception for authentication errors (401 Unauthorized)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = ErrorCodes.AUTHENTICATION_FAILED,
    ) -> None:
        """Initialize authentication error.

        Args:
            message: Human-readable error message
            code: Specific error code (default: AUTHENTICATION_FAILED)
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(APIError):
    """Exception for authorization errors (403 Forbidden)."""

    def __init__(
        self,
        message: str = "Access denied",
        code: str = ErrorCodes.AUTHORIZATION_FAILED,
    ) -> None:
        """Initialize authorization error.

        Args:
            message: Human-readable error message
            code: Specific error code (default: AUTHORIZATION_FAILED)
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundError(APIError):
    """Exception for resource not found errors (404 Not Found)."""

    def __init__(
        self,
        resource: str = "Resource",
        identifier: str | None = None,
        code: str = ErrorCodes.RESOURCE_NOT_FOUND,
    ) -> None:
        """Initialize not found error.

        Args:
            resource: Type of resource (e.g., "User", "Job")
            identifier: Optional resource identifier
            code: Specific error code (default: RESOURCE_NOT_FOUND)
        """
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} not found: {identifier}"
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(APIError):
    """Exception for conflict errors (409 Conflict)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = ErrorCodes.CONFLICT,
    ) -> None:
        """Initialize conflict error.

        Args:
            message: Human-readable error message
            code: Specific error code (default: CONFLICT)
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class RateLimitError(APIError):
    """Exception for rate limit errors (429 Too Many Requests)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after: int | None = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Human-readable error message
            retry_after: Optional seconds until retry is allowed
        """
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)

        details = []
        if retry_after is not None:
            details.append(
                ErrorDetail(
                    field="retry_after",
                    message=f"Try again in {retry_after} seconds",
                )
            )

        super().__init__(
            code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            headers=headers if headers else None,
        )


class InternalError(APIError):
    """Exception for internal server errors (500 Internal Server Error)."""

    def __init__(
        self,
        message: str = "An internal error occurred",
        code: str = ErrorCodes.INTERNAL_ERROR,
    ) -> None:
        """Initialize internal error.

        Args:
            message: Human-readable error message
            code: Specific error code (default: INTERNAL_ERROR)
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ConfigurationError(APIError):
    """Exception for server configuration errors (500 Internal Server Error)."""

    def __init__(
        self,
        message: str = "Server configuration error",
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Human-readable error message
        """
        super().__init__(
            code=ErrorCodes.CONFIGURATION_ERROR,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ServiceUnavailableError(APIError):
    """Exception for service unavailable errors (503 Service Unavailable)."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int | None = None,
    ) -> None:
        """Initialize service unavailable error.

        Args:
            message: Human-readable error message
            retry_after: Optional seconds until retry is allowed
        """
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)

        super().__init__(
            code=ErrorCodes.SERVICE_UNAVAILABLE,
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers=headers if headers else None,
        )


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------


def _get_request_id_safe(request: Request) -> str | None:
    """Safely get request ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Request ID string or None
    """
    try:
        return get_request_id(request)
    except Exception:
        return getattr(request.state, "request_id", None)


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions with standardized response format.

    Args:
        request: FastAPI request object
        exc: APIError exception

    Returns:
        JSONResponse with standardized error format
    """
    request_id = _get_request_id_safe(request)
    response = exc.to_response(request_id)

    return JSONResponse(
        status_code=exc.status_code,
        content=response,
        headers=exc.headers,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTPException with standardized response format.

    This handler converts standard FastAPI HTTPExceptions to the standardized
    error response format.

    Args:
        request: FastAPI request object
        exc: HTTPException exception

    Returns:
        JSONResponse with standardized error format
    """
    request_id = _get_request_id_safe(request)

    # Map status codes to error codes
    code_map = {
        400: ErrorCodes.VALIDATION_ERROR,
        401: ErrorCodes.AUTHENTICATION_FAILED,
        403: ErrorCodes.AUTHORIZATION_FAILED,
        404: ErrorCodes.RESOURCE_NOT_FOUND,
        409: ErrorCodes.CONFLICT,
        429: ErrorCodes.RATE_LIMIT_EXCEEDED,
        500: ErrorCodes.INTERNAL_ERROR,
        502: ErrorCodes.EXTERNAL_SERVICE_ERROR,
        503: ErrorCodes.SERVICE_UNAVAILABLE,
        504: ErrorCodes.EXTERNAL_SERVICE_ERROR,
    }

    status_code = exc.status_code
    code = code_map.get(status_code, ErrorCodes.INTERNAL_ERROR)

    # Handle detail as string or dict
    message = str(exc.detail) if exc.detail else "An error occurred"
    details = []

    # If detail is a dict with more info, extract it
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", message)
        if "details" in exc.detail:
            for d in exc.detail["details"]:
                if isinstance(d, dict):
                    details.append(ErrorDetail(**d))
                elif isinstance(d, ErrorDetail):
                    details.append(d)

    response = ErrorResponse(
        error=ErrorInfo(
            code=code,
            message=message,
            details=details,
        ),
        request_id=request_id,
    ).model_dump()

    return JSONResponse(
        status_code=status_code,
        content=response,
        headers=exc.headers,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with standardized response format.

    This is a catch-all handler for any unhandled exceptions.

    Args:
        request: FastAPI request object
        exc: Exception instance

    Returns:
        JSONResponse with standardized error format (500)
    """
    request_id = _get_request_id_safe(request)

    # Log the actual error for debugging
    from shared.logging_config import get_logger

    logger = get_logger("sorce.api.errors")
    logger.exception(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
    )

    response = ErrorResponse(
        error=ErrorInfo(
            code=ErrorCodes.INTERNAL_ERROR,
            message="An unexpected error occurred. Please try again later.",
            details=[],
        ),
        request_id=request_id,
    ).model_dump()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response,
    )


# ---------------------------------------------------------------------------
# Registration Function
# ---------------------------------------------------------------------------


def register_exception_handlers(app: Any) -> None:
    """Register all exception handlers with a FastAPI application.

    This should be called during application startup to ensure all
    exceptions are handled with standardized error responses.

    Args:
        app: FastAPI application instance

    Example:
        from fastapi import FastAPI
        from shared.error_responses import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)
    """
    # Handle custom APIError
    app.add_exception_handler(APIError, api_error_handler)

    # Handle standard HTTPException
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Handle all other exceptions
    app.add_exception_handler(Exception, generic_exception_handler)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def create_error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: list[ErrorDetail] | None = None,
    request_id: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Create a standardized error response.

    Args:
        code: Standard error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional list of detailed errors
        request_id: Optional request tracking ID

    Returns:
        Tuple of (response_dict, status_code)

    Example:
        return create_error_response(
            ErrorCodes.VALIDATION_ERROR,
            "Invalid email format",
            400,
            [ErrorDetail(field="email", message="Must be a valid email")]
        )
    """
    response = ErrorResponse(
        error=ErrorInfo(
            code=code,
            message=message,
            details=details or [],
        ),
        request_id=request_id,
    ).model_dump()

    return response, status_code


def create_validation_error(
    message: str,
    field_errors: dict[str, str] | None = None,
    request_id: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Create a validation error response.

    Args:
        message: Human-readable error message
        field_errors: Dict of field names to error messages
        request_id: Optional request tracking ID

    Returns:
        Tuple of (response_dict, 400)
    """
    details = []
    if field_errors:
        for field, error_msg in field_errors.items():
            details.append(ErrorDetail(field=field, message=error_msg))

    return create_error_response(
        code=ErrorCodes.VALIDATION_ERROR,
        message=message,
        status_code=400,
        details=details,
        request_id=request_id,
    )


def create_not_found_error(
    resource: str,
    identifier: str | None = None,
    request_id: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Create a not found error response.

    Args:
        resource: Type of resource (e.g., "User", "Job")
        identifier: Optional resource identifier
        request_id: Optional request tracking ID

    Returns:
        Tuple of (response_dict, 404)
    """
    message = f"{resource} not found"
    if identifier:
        message = f"{resource} not found: {identifier}"

    return create_error_response(
        code=ErrorCodes.RESOURCE_NOT_FOUND,
        message=message,
        status_code=404,
        request_id=request_id,
    )


def create_auth_error(
    message: str = "Authentication failed",
    code: str = ErrorCodes.AUTHENTICATION_FAILED,
    request_id: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Create an authentication error response.

    Args:
        message: Human-readable error message
        code: Specific error code
        request_id: Optional request tracking ID

    Returns:
        Tuple of (response_dict, 401)
    """
    return create_error_response(
        code=code,
        message=message,
        status_code=401,
        request_id=request_id,
    )


def create_forbidden_error(
    message: str = "Access denied",
    request_id: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Create a forbidden error response.

    Args:
        message: Human-readable error message
        request_id: Optional request tracking ID

    Returns:
        Tuple of (response_dict, 403)
    """
    return create_error_response(
        code=ErrorCodes.AUTHORIZATION_FAILED,
        message=message,
        status_code=403,
        request_id=request_id,
    )


def create_rate_limit_error(
    message: str = "Rate limit exceeded. Please try again later.",
    retry_after: int | None = None,
    request_id: str | None = None,
) -> tuple[dict[str, Any], int, dict[str, str] | None]:
    """Create a rate limit error response.

    Args:
        message: Human-readable error message
        retry_after: Optional seconds until retry is allowed
        request_id: Optional request tracking ID

    Returns:
        Tuple of (response_dict, 429, headers)
    """
    details = []
    if retry_after is not None:
        details.append(
            ErrorDetail(
                field="retry_after",
                message=f"Try again in {retry_after} seconds",
            )
        )

    response, status_code = create_error_response(
        code=ErrorCodes.RATE_LIMIT_EXCEEDED,
        message=message,
        status_code=429,
        details=details,
        request_id=request_id,
    )

    headers = None
    if retry_after is not None:
        headers = {"Retry-After": str(retry_after)}

    return response, status_code, headers
