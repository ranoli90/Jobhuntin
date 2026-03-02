"""Cursor-based pagination utilities for consistent API pagination."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class PageInfo:
    """Pagination metadata."""

    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None
    total_count: int | None = None


@dataclass
class PaginatedResult[T]:
    """Paginated result with items and page info."""

    items: list[T]
    page_info: PageInfo
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaginationParams:
    """Parameters for cursor-based pagination."""

    first: int | None = None  # Number of items from start
    after: str | None = None  # Cursor to start after
    last: int | None = None   # Number of items from end
    before: str | None = None  # Cursor to start before

    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    def __post_init__(self):
        # Normalize to forward pagination
        if self.first is None and self.last is None:
            self.first = self.DEFAULT_PAGE_SIZE

        # Clamp to max
        if self.first and self.first > self.MAX_PAGE_SIZE:
            self.first = self.MAX_PAGE_SIZE
        if self.last and self.last > self.MAX_PAGE_SIZE:
            self.last = self.MAX_PAGE_SIZE


def encode_cursor(data: dict[str, Any]) -> str:
    """Encode cursor data to base64 string."""
    json_str = json.dumps(data, sort_keys=True)
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> dict[str, Any] | None:
    """Decode cursor string to data."""
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        return json.loads(json_str)
    except Exception:
        return None


def create_cursor_from_row(row: dict[str, Any], sort_field: str = "id") -> str:
    """Create a cursor from a database row."""
    return encode_cursor({
        "sort_value": str(row.get(sort_field, "")),
        "id": str(row.get("id", "")),
    })


async def paginate_query(
    conn,
    query: str,
    params: PaginationParams,
    cursor_field: str = "id",
    extra_conditions: str = "",
    args: list[Any] | None = None,
) -> PaginatedResult[dict]:
    """Execute a paginated query.

    Args:
        conn: Database connection
        query: Base query (without ORDER BY and LIMIT)
        params: Pagination parameters
        cursor_field: Field to use for cursor
        extra_conditions: Additional WHERE conditions
        args: Query arguments

    Returns:
        PaginatedResult with items and page info

    """
    args = args or []
    page_size = params.first or params.last or PaginationParams.DEFAULT_PAGE_SIZE

    # Build cursor condition
    cursor_condition = ""
    cursor_value = None

    if params.after:
        cursor_data = decode_cursor(params.after)
        if cursor_data:
            cursor_value = cursor_data.get("id")
            cursor_condition = f"AND {cursor_field} > ${{cursor_val}}"

    if params.before:
        cursor_data = decode_cursor(params.before)
        if cursor_data:
            cursor_value = cursor_data.get("id")
            cursor_condition = f"AND {cursor_field} < ${{cursor_val}}"

    # Build full query
    direction = "DESC" if params.last else "ASC"
    full_query = f"""
        {query}
        {extra_conditions}
        {cursor_condition}
        ORDER BY {cursor_field} {direction}
        LIMIT {page_size + 1}
    """

    # Execute query
    if cursor_value:
        full_query = full_query.replace("${cursor_val}", f"${len(args) + 1}")
        args.append(cursor_value)

    rows = await conn.fetch(full_query, *args)

    # Determine if there's a next page
    has_next = len(rows) > page_size
    items = rows[:page_size] if has_next else rows

    # Reverse if paginating backwards
    if params.last or params.before:
        items = list(reversed(items))

    # Build page info
    start_cursor = create_cursor_from_row(items[0], cursor_field) if items else None
    end_cursor = create_cursor_from_row(items[-1], cursor_field) if items else None

    # Get total count (optional)
    count_query = f"SELECT COUNT(*) FROM ({query}) AS subq"
    try:
        total_result = await conn.fetchrow(count_query, *args[:args.index(cursor_value) if cursor_value in args else len(args)])
        total_count = total_result["count"] if total_result else None
    except Exception:
        total_count = None

    return PaginatedResult(
        items=[dict(row) for row in items],
        page_info=PageInfo(
            has_next_page=has_next,
            has_previous_page=params.after is not None,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
            total_count=total_count,
        ),
    )


def paginated_response(result: PaginatedResult, item_key: str = "items") -> dict:
    """Convert PaginatedResult to API response dict."""
    return {
        item_key: result.items,
        "pagination": {
            "has_next_page": result.page_info.has_next_page,
            "has_previous_page": result.page_info.has_previous_page,
            "start_cursor": result.page_info.start_cursor,
            "end_cursor": result.page_info.end_cursor,
            "total_count": result.page_info.total_count,
        },
        **result.extra,
    }
