"""Shared validation utilities for API path parameters and request bodies.

This module provides common validation functions and helpers to reduce code duplication
across API endpoints.

Usage:
    from shared.validators import (
        validate_uuid,
        uuid_path,
        validate_required_fields,
        validate_email,
        validate_pagination,
    )

Example:
    @app.get("/users/{user_id}")
    async def get_user(user_id: str = uuid_path("user_id")):
        validate_uuid(user_id, "user_id")
        ...
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import HTTPException, Path

# Import shared security utilities for consistent validation patterns
from shared.security_utils import (
    EMAIL_PATTERN,
    URL_PATTERN,
    validate_email_format,
    validate_url_format,
)


# Email validation regex pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# URL validation regex pattern
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def validate_uuid(value: str, param_name: str = "id") -> str:
    """Validate that a string is a well-formed UUID. Returns the normalized string.

    Raises HTTPException(422) if the value is not a valid UUID format.
    """
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid UUID format for '{param_name}': {value!r}",
        )
    return value


def uuid_path(param_name: str = "id", **kwargs) -> Any:
    """FastAPI Path() with UUID format description for OpenAPI docs."""
    return Path(
        ...,
        description=f"UUID of the {param_name}",
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        **kwargs,
    )


def validate_required_fields(data: dict[str, Any], required_fields: list[str]) -> None:
    """Validate that all required fields are present in the data dictionary.

    Args:
        data: Dictionary containing the request data
        required_fields: List of required field names

    Raises HTTPException(422) if any required field is missing.

    Example:
        validate_required_fields(request.model_dump(), ["email", "name"])
    """
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required fields: {', '.join(missing)}",
        )


def validate_email(email: str, field_name: str = "email") -> str:
    """Validate that a string is a well-formed email address.

    Args:
        email: The email string to validate
        field_name: Name of the field for error messages

    Returns:
        The validated email string

    Raises HTTPException(422) if the email is invalid.
    """
    if not email or not isinstance(email, str):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: cannot be empty",
        )
    
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name} format: {email}",
        )
    return email


def validate_url(url: str, field_name: str = "url", require_https: bool = True) -> str:
    """Validate that a string is a well-formed URL.

    Args:
        url: The URL string to validate
        field_name: Name of the field for error messages
        require_https: Whether to require HTTPS (default True)

    Returns:
        The validated URL string

    Raises HTTPException(422) if the URL is invalid.
    """
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: cannot be empty",
        )
    
    if require_https and not url.startswith("https://"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: must use HTTPS",
        )
    
    if not URL_PATTERN.match(url):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name} format: {url}",
        )
    return url


def validate_pagination(
    skip: int | None = None,
    limit: int | None = None,
    default_limit: int = 50,
    max_limit: int = 1000,
) -> tuple[int, int]:
    """Validate and normalize pagination parameters.

    Args:
        skip: Number of items to skip (offset)
        limit: Maximum number of items to return
        default_limit: Default limit if not provided
        max_limit: Maximum allowed limit

    Returns:
        Tuple of (skip, limit) with normalized values

    Example:
        skip, limit = validate_pagination(
            request.query_params.get("skip"),
            request.query_params.get("limit"),
        )
    """
    # Parse and validate skip
    if skip is None:
        skip = 0
    else:
        try:
            skip = int(skip)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=422,
                detail="Invalid 'skip' parameter: must be an integer",
            )
        if skip < 0:
            raise HTTPException(
                status_code=422,
                detail="Invalid 'skip' parameter: must be >= 0",
            )

    # Parse and validate limit
    if limit is None:
        limit = default_limit
    else:
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=422,
                detail="Invalid 'limit' parameter: must be an integer",
            )
        if limit < 1:
            raise HTTPException(
                status_code=422,
                detail="Invalid 'limit' parameter: must be >= 1",
            )
        if limit > max_limit:
            limit = max_limit

    return skip, limit


def validate_string_length(
    value: str,
    field_name: str,
    min_length: int | None = None,
    max_length: int | None = None,
) -> str:
    """Validate string length constraints.

    Args:
        value: The string to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length (inclusive)
        max_length: Maximum allowed length (inclusive)

    Returns:
        The validated string

    Raises HTTPException(422) if validation fails.
    """
    if not isinstance(value, str):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: must be a string",
        )

    length = len(value)

    if min_length is not None and length < min_length:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must be at least {min_length} characters",
        )

    if max_length is not None and length > max_length:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must be at most {max_length} characters",
        )

    return value


def validate_enum(value: Any, allowed_values: list[Any], field_name: str) -> Any:
    """Validate that a value is one of the allowed values.

    Args:
        value: The value to validate
        allowed_values: List of allowed values
        field_name: Name of the field for error messages

    Returns:
        The validated value

    Raises HTTPException(422) if validation fails.
    """
    if value not in allowed_values:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: must be one of {allowed_values}",
        )
    return value


def validate_positive_int(value: Any, field_name: str) -> int:
    """Validate that a value is a positive integer.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages

    Returns:
        The validated integer

    Raises HTTPException(422) if validation fails.
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: must be an integer",
        )

    if int_value <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: must be a positive integer",
        )

    return int_value
