"""Standardized pagination models and utilities."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Standardized pagination metadata."""

    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")
    has_more: bool = Field(..., description="Whether more items are available")
    next_offset: int | None = Field(None, description="Offset for next page")
    prev_offset: int | None = Field(None, description="Offset for previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated response format.

    All endpoints should use this format for consistency.
    """

    items: list[T] = Field(..., description="Items in current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


def create_pagination_meta(
    total: int,
    limit: int,
    offset: int,
) -> PaginationMeta:
    """Create pagination metadata.

    Args:
        total: Total number of items
        limit: Items per page
        offset: Current offset

    Returns:
        PaginationMeta with calculated values
    """
    has_more = offset + limit < total
    next_offset = offset + limit if has_more else None
    prev_offset = max(0, offset - limit) if offset > 0 else None

    return PaginationMeta(
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more,
        next_offset=next_offset,
        prev_offset=prev_offset,
    )
