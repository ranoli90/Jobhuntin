"""Shared validation utilities for API path parameters and request bodies."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, Path


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


def uuid_path(param_name: str = "id", **kwargs) -> Path:
    """FastAPI Path() with UUID format description for OpenAPI docs."""
    return Path(
        ...,
        description=f"UUID of the {param_name}",
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        **kwargs,
    )
