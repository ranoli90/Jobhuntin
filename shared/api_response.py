"""Standard API response wrapper system.

This module provides standardized response formats for all API endpoints:
- SuccessResponse: `{"success": true, "data": {...}, "meta": {"version": "1.0", "timestamp": "ISO8601"}}`
- ErrorResponse: `{"success": false, "error": {"code": "ERROR_CODE", "message": "...", "details": [...], "request_id": "..."}}`

Usage:
    from shared.api_response import SuccessResponse, ErrorResponse, success_response, error_response

    # Success case
    return success_response({"user": {"id": "123", "name": "John"}})

    # Error case
    return error_response("NOT_FOUND", "User not found", status_code=404)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from fastapi import Request
from pydantic import BaseModel, Field

from shared.middleware import get_request_id

# API Version constant
API_VERSION = "1.0"

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class ResponseMeta(BaseModel):
    """Metadata included in every API response."""

    version: str = Field(default=API_VERSION, description="API version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO8601 timestamp",
    )
    request_id: str | None = Field(default=None, description="Request tracking ID")


class ErrorDetail(BaseModel):
    """Detailed error information for debugging."""

    field: str | None = Field(default=None, description="Field that caused the error")
    message: str = Field(default="", description="Error message for this detail")


class ErrorInfo(BaseModel):
    """Error information structure."""

    code: str = Field(description="Standard error code")
    message: str = Field(description="Human-readable error message")
    details: list[ErrorDetail] = Field(default_factory=list, description="Detailed error list")
    request_id: str | None = Field(default=None, description="Request tracking ID")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response format.

    Format: {"success": true, "data": {...}, "meta": {"version": "1.0", "timestamp": "ISO8601", "request_id": "..."}}
    """

    success: bool = Field(default=True, description="Always true for success responses")
    data: T = Field(description="Response payload")
    meta: ResponseMeta = Field(
        default_factory=ResponseMeta,
        description="Response metadata including version, timestamp, and request_id",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "John"},
                "meta": {
                    "version": "1.0",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "request_id": "abc-123",
                },
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format.

    Format: {"success": false, "error": {"code": "ERROR_CODE", "message": "...", "details": [...], "request_id": "..."}}
    """

    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorInfo = Field(description="Error information")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": [{"field": "email", "message": "Invalid email format"}],
                    "request_id": "abc-123",
                },
            }
        }


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def create_meta(request_id: str | None = None) -> ResponseMeta:
    """Create response metadata with timestamp and optional request ID.

    Args:
        request_id: Optional request tracking ID

    Returns:
        ResponseMeta instance with timestamp and request_id
    """
    return ResponseMeta(
        version=API_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=request_id,
    )


def success_response(
    data: Any,
    request: Request | None = None,
    request_id: str | None = None,
) -> SuccessResponse[Any]:
    """Create a standardized success response.

    Args:
        data: The response payload
        request: Optional FastAPI request for extracting request_id
        request_id: Optional explicit request_id

    Returns:
        SuccessResponse with standardized format

    Example:
        return success_response({"user": {"id": "123"}})
    """
    # Get request_id from request state if available
    if request_id is None and request is not None:
        request_id = get_request_id(request)

    return SuccessResponse(
        success=True,
        data=data,
        meta=create_meta(request_id),
    )


def error_response(
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
    request: Request | None = None,
    request_id: str | None = None,
    status_code: int = 400,
) -> tuple[ErrorResponse, int]:
    """Create a standardized error response.

    Args:
        code: Standard error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Human-readable error message
        details: Optional list of detailed errors
        request: Optional FastAPI request for extracting request_id
        request_id: Optional explicit request_id
        status_code: HTTP status code to return

    Returns:
        Tuple of (ErrorResponse, status_code)

    Example:
        return error_response("NOT_FOUND", "User not found", status_code=404)
    """
    # Get request_id from request state if available
    if request_id is None and request is not None:
        request_id = get_request_id(request)

    error_info = ErrorInfo(
        code=code,
        message=message,
        details=details or [],
        request_id=request_id,
    )

    return (
        ErrorResponse(
            success=False,
            error=error_info,
        ),
        status_code,
    )


def validation_error(
    message: str,
    field_errors: dict[str, str] | None = None,
    request: Request | None = None,
    request_id: str | None = None,
) -> tuple[ErrorResponse, int]:
    """Create a validation error response.

    Args:
        message: Human-readable error message
        field_errors: Dict of field names to error messages
        request: Optional FastAPI request for extracting request_id
        request_id: Optional explicit request_id

    Returns:
        Tuple of (ErrorResponse, 400)

    Example:
        return validation_error("Invalid input", {"email": "Invalid email format"})
    """
    details = []
    if field_errors:
        for field, error_msg in field_errors.items():
            details.append(ErrorDetail(field=field, message=error_msg))

    return error_response(
        code="VALIDATION_ERROR",
        message=message,
        details=details,
        request=request,
        request_id=request_id,
        status_code=400,
    )


def not_found_error(
    resource: str,
    identifier: str | None = None,
    request: Request | None = None,
    request_id: str | None = None,
) -> tuple[ErrorResponse, int]:
    """Create a not found error response.

    Args:
        resource: Type of resource (e.g., "User", "Job")
        identifier: Optional resource identifier
        request: Optional FastAPI request for extracting request_id
        request_id: Optional explicit request_id

    Returns:
        Tuple of (ErrorResponse, 404)

    Example:
        return not_found_error("User", "123")
    """
    message = f"{resource} not found"
    if identifier:
        message = f"{resource} not found: {identifier}"

    return error_response(
        code="NOT_FOUND",
        message=message,
        request=request,
        request_id=request_id,
        status_code=404,
    )


def unauthorized_error(
    message: str = "Authentication required",
    request: Request | None = None,
    request_id: str | None = None,
) -> tuple[ErrorResponse, int]:
    """Create an unauthorized error response.

    Args:
        message: Human-readable error message
        request: Optional FastAPI request for extracting request_id
        request_id: Optional explicit request_id

    Returns:
        Tuple of (ErrorResponse, 401)

    Example:
        return unauthorized_error("Invalid token")
    """
    return error_response(
        code="AUTH_ERROR",
        message=message,
        request=request,
        request_id=request_id,
        status_code=401,
    )


def forbidden_error(
    message: str = "Access denied",
    request: Request | None = None,
    request_id: str | None = None,
) -> tuple[ErrorResponse, int]:
    """Create a forbidden error response.

    Args:
        message: Human-readable error message
        request: Optional FastAPI request for extracting request_id
        request_id: Optional explicit request_id

    Returns:
        Tuple of (ErrorResponse, 403)

    Example:
        return forbidden_error("Insufficient permissions")
    """
    return error_response(
        code="FORBIDDEN",
        message=message,
        request=request,
        request_id=request_id,
        status_code=403,
    )


def rate_limit_error(
    message: str = "Rate limit exceeded. Please try again later.",
    retry_after: int | None = None,
    request: Request | None = None,
    request_id: str | None = None,
) -> tuple[ErrorResponse, int]:
    """Create a rate limit error response.

    Args:
        message: Human-readable error message
        retry_after: Seconds until retry is allowed
        request: Optional FastAPI request for extracting request_id
        request_id: Optional explicit request_id

    Returns:
        Tuple of (ErrorResponse, 429)
    """
    details = []
    if retry_after is not None:
        details.append(ErrorDetail(field="retry_after", message=f"Try again in {retry_after} seconds"))

    return error_response(
        code="RATE_LIMIT_EXCEEDED",
        message=message,
        details=details,
        request=request,
        request_id=request_id,
        status_code=429,
    )


def internal_error(
    message: str = "An internal error occurred",
    request: Request | None = None,
    request_id: str | None = None,
) -> tuple[ErrorResponse, int]:
    """Create an internal server error response.

    Args:
        message: Human-readable error message
        request: Optional FastAPI request for extracting request_id
        request_id: Optional explicit request_id

    Returns:
        Tuple of (ErrorResponse, 500)

    Example:
        return internal_error("Database connection failed")
    """
    return error_response(
        code="INTERNAL_ERROR",
        message=message,
        request=request,
        request_id=request_id,
        status_code=500,
    )