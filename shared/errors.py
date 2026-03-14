"""Standardized error codes and exception classes.

This module provides a comprehensive set of error codes and exception classes
for consistent error handling across the API. Integrates with api_response.py
to provide standardized error responses.

Usage:
    from shared.errors import ErrorCode, AppException, ValidationException, NotFoundException

    # Raise specific exceptions
    raise ValidationException("Invalid email", field="email")
    raise NotFoundException("User", "123")

    # Use error codes
    if error_code == ErrorCode.VALIDATION_ERROR:
        ...
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Standard error codes for the API.

    These codes are used across all endpoints to provide consistent error identification.
    """

    # Validation errors (4xx - Client errors)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Authentication/Authorization errors
    AUTH_ERROR = "AUTH_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # Business logic errors
    INVALID_OPERATION = "INVALID_OPERATION"
    INVALID_STATE = "INVALID_STATE"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"

    # Generic
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class AppException(Exception):
    """Base application exception with structured error information.

    Attributes:
        code: Standard error code from ErrorCode enum
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        field: Optional field that caused the error
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.field = field

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary format for API responses."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "field": self.field,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code.value}, message={self.message}, status_code={self.status_code})"


# ---------------------------------------------------------------------------
# Validation Errors
# ---------------------------------------------------------------------------


class ValidationException(AppException):
    """Input validation error.

    Raised when request data fails validation rules.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details,
            field=field,
        )


class InvalidInputException(AppException):
    """Invalid input format or type.

    Raised when input data is of wrong type or format.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details,
            field=field,
        )


class MissingFieldException(AppException):
    """Missing required field.

    Raised when a required field is not provided.
    """

    def __init__(
        self,
        field: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=f"Missing required field: {field}",
            code=ErrorCode.MISSING_REQUIRED_FIELD,
            status_code=400,
            details=details,
            field=field,
        )


# ---------------------------------------------------------------------------
# Authentication/Authorization Errors
# ---------------------------------------------------------------------------


class AuthenticationException(AppException):
    """Authentication error.

    Raised when authentication fails (invalid credentials, missing token, etc.).
    """

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            details=details,
        )


class TokenExpiredException(AppException):
    """Token expired error.

    Raised when an authentication token has expired.
    """

    def __init__(
        self,
        message: str = "Token has expired",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.TOKEN_EXPIRED,
            status_code=401,
            details=details,
        )


class TokenInvalidException(AppException):
    """Token invalid error.

    Raised when an authentication token is invalid or malformed.
    """

    def __init__(
        self,
        message: str = "Invalid token",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.TOKEN_INVALID,
            status_code=401,
            details=details,
        )


class AuthorizationException(AppException):
    """Authorization error.

    Raised when user lacks permission to perform an action.
    """

    def __init__(
        self,
        message: str = "Access denied",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=403,
            details=details,
        )


class InsufficientPermissionsException(AuthorizationException):
    """Insufficient permissions error.

    Raised when user doesn't have required permissions.
    """

    def __init__(
        self,
        required_permission: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=f"Insufficient permissions: {required_permission}",
            details=details or {"required_permission": required_permission},
        )
        self.code = ErrorCode.INSUFFICIENT_PERMISSIONS


# ---------------------------------------------------------------------------
# Resource Errors
# ---------------------------------------------------------------------------


class NotFoundException(AppException):
    """Resource not found error.

    Raised when a requested resource doesn't exist.
    """

    def __init__(
        self,
        resource: str,
        identifier: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} not found: {identifier}"

        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            status_code=404,
            details=details or {"resource": resource, "identifier": identifier},
        )
        self.resource = resource
        self.identifier = identifier


class AlreadyExistsException(AppException):
    """Resource already exists error.

    Raised when attempting to create a duplicate resource.
    """

    def __init__(
        self,
        resource: str,
        identifier: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        message = f"{resource} already exists"
        if identifier:
            message = f"{resource} already exists: {identifier}"

        super().__init__(
            message=message,
            code=ErrorCode.ALREADY_EXISTS,
            status_code=409,
            details=details or {"resource": resource, "identifier": identifier},
        )


class ConflictException(AppException):
    """Resource conflict error.

    Raised when there's a conflict with current state of the resource.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            status_code=409,
            details=details,
        )


# ---------------------------------------------------------------------------
# Rate Limiting Errors
# ---------------------------------------------------------------------------


class RateLimitException(AppException):
    """Rate limit exceeded error.

    Raised when rate limit is exceeded.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details or ({"retry_after": retry_after} if retry_after else {}),
        )
        self.retry_after = retry_after


class QuotaExceededException(AppException):
    """Quota exceeded error.

    Raised when user quota is exceeded.
    """

    def __init__(
        self,
        quota_type: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=f"Quota exceeded: {quota_type}",
            code=ErrorCode.QUOTA_EXCEEDED,
            status_code=429,
            details=details or {"quota_type": quota_type},
        )


# ---------------------------------------------------------------------------
# Server Errors
# ---------------------------------------------------------------------------


class InternalException(AppException):
    """Internal server error.

    Raised when an unexpected internal error occurs.
    """

    def __init__(
        self,
        message: str = "An internal error occurred",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            details=details,
        )


class ServiceUnavailableException(AppException):
    """Service unavailable error.

    Raised when a required service is temporarily unavailable.
    """

    def __init__(
        self,
        service: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=f"Service unavailable: {service}",
            code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            details=details or {"service": service},
        )


class DatabaseException(AppException):
    """Database error.

    Raised when a database operation fails.
    """

    def __init__(
        self,
        message: str = "Database operation failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details=details,
        )


class ExternalServiceException(AppException):
    """External service error.

    Raised when an external service call fails.
    """

    def __init__(
        self,
        service: str,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message or f"External service error: {service}",
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=502,
            details=details or {"service": service},
        )


# ---------------------------------------------------------------------------
# Business Logic Errors
# ---------------------------------------------------------------------------


class InvalidOperationException(AppException):
    """Invalid operation error.

    Raised when an operation cannot be performed due to business rules.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_OPERATION,
            status_code=400,
            details=details,
        )


class InvalidStateException(AppException):
    """Invalid state error.

    Raised when the resource is in an invalid state for the operation.
    """

    def __init__(
        self,
        resource: str,
        current_state: str,
        expected_state: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        message = f"Invalid state for {resource}: {current_state}"
        if expected_state:
            message += f". Expected: {expected_state}"

        super().__init__(
            message=message,
            code=ErrorCode.INVALID_STATE,
            status_code=400,
            details=details
            or {
                "resource": resource,
                "current_state": current_state,
                "expected_state": expected_state,
            },
        )


class BusinessRuleException(AppException):
    """Business rule violation error.

    Raised when a business rule is violated.
    """

    def __init__(
        self,
        message: str,
        rule: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.BUSINESS_RULE_VIOLATION,
            status_code=400,
            details=details or ({"rule": rule} if rule else {}),
        )
        self.rule = rule


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------


def get_error_code(http_status: int) -> ErrorCode:
    """Map HTTP status code to ErrorCode.

    Args:
        http_status: HTTP status code

    Returns:
        Corresponding ErrorCode
    """
    mapping = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    return mapping.get(http_status, ErrorCode.UNKNOWN_ERROR)


def format_exception(exc: Exception) -> tuple[str, int, dict[str, Any]]:
    """Format an exception for API response.

    Args:
        exc: Exception to format

    Returns:
        Tuple of (message, status_code, details)
    """
    if isinstance(exc, AppException):
        return exc.message, exc.status_code, exc.details
    return str(exc), 500, {}
