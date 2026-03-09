"""Cursor-based pagination utilities for consistent API pagination."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")

# Valid SQL identifier pattern (alphanumeric and underscore only)
VALID_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Whitelist of allowed cursor fields - extend as needed
ALLOWED_CURSOR_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "priority_score",
    "title",
    "company",
    "salary_min",
    "salary_max",
    "name",
    "email",
    "status",
    "last_used_at",
}


def validate_identifier(identifier: str) -> str:
    """Validate that an identifier is safe for SQL interpolation.

    Args:
        identifier: The SQL identifier to validate

    Returns:
        The identifier if valid

    Raises:
        ValueError: If the identifier contains invalid characters
    """
    if not VALID_IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    return identifier


def validate_cursor_field(cursor_field: str) -> str:
    """Validate cursor field against whitelist.

    Args:
        cursor_field: The cursor field to validate

    Returns:
        The cursor field if valid

    Raises:
        ValueError: If the cursor field is not in the whitelist
    """
    if cursor_field not in ALLOWED_CURSOR_FIELDS:
        raise ValueError(
            f"Invalid cursor field: {cursor_field}. "
            f"Must be one of: {', '.join(sorted(ALLOWED_CURSOR_FIELDS))}"
        )
    return cursor_field


@dataclass
class PageInfo:
    """Pagination metadata."""

    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None
    total_count: int | None = None


@dataclass
class PaginatedResult(Generic[T]):
    """Paginated result with items and page info."""

    items: list[T]
    page_info: PageInfo
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaginationParams:
    """Parameters for cursor-based pagination."""

    first: int | None = None  # Number of items from start
    after: str | None = None  # Cursor to start after
    last: int | None = None  # Number of items from end
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
        data: dict[str, Any] = json.loads(json_str)
        return data
    except Exception:
        return None


def create_cursor_from_row(row: dict[str, Any], sort_field: str = "id") -> str:
    """Create a cursor from a database row."""
    # Validate sort_field
    validate_cursor_field(sort_field)
    return encode_cursor(
        {
            "sort_value": str(row.get(sort_field, "")),
            "id": str(row.get("id", "")),
        }
    )


def _validate_cursor_field(
    cursor_field: str, allowed_cursor_fields: set[str] | None
) -> None:
    """Validate cursor field against whitelist."""
    valid_fields = ALLOWED_CURSOR_FIELDS | (allowed_cursor_fields or set())
    if cursor_field not in valid_fields:
        raise ValueError(
            f"Invalid cursor field: {cursor_field}. "
            f"Must be one of: {', '.join(sorted(valid_fields))}"
        )


def _get_cursor_info(
    params: PaginationParams, args: list[Any]
) -> tuple[str | None, str]:
    """Extract cursor value and build cursor condition."""
    if params.after:
        cursor_data = decode_cursor(params.after)
        if cursor_data:
            cursor_value = cursor_data.get("id")
            return cursor_value, f"AND {{cursor_field}} > ${len(args) + 1}"

    if params.before:
        cursor_data = decode_cursor(params.before)
        if cursor_data:
            cursor_value = cursor_data.get("id")
            return cursor_value, f"AND {{cursor_field}} < ${len(args) + 1}"

    return None, ""


def _build_query_args(
    args: list[Any], cursor_value: Any | None, page_size: int
) -> list[Any]:
    """Build the final query arguments list."""
    query_args = args.copy()
    if cursor_value:
        query_args.append(cursor_value)
    query_args.append(page_size + 1)
    return query_args


def _build_full_query(
    query: str,
    extra_conditions: str,
    cursor_condition: str,
    cursor_field: str,
    direction: str,
    limit_param: int,
) -> str:
    """Build the complete paginated query."""
    return f"""
        {query}
        {extra_conditions}
        {cursor_condition}
        ORDER BY {cursor_field} {direction}
        LIMIT ${limit_param}
    """


async def _get_total_count(conn, query: str, args: list[Any]) -> int | None:
    """Get total count for pagination."""
    count_query = f"SELECT COUNT(*) FROM ({query}) AS subq"
    try:
        total_result = await conn.fetchrow(count_query, *args)
        return total_result["count"] if total_result else None
    except Exception:
        return None


async def paginate_query(
    conn,
    query: str,
    params: PaginationParams,
    cursor_field: str = "id",
    extra_conditions: str = "",
    args: list[Any] | None = None,
    allowed_cursor_fields: set[str] | None = None,
) -> PaginatedResult[dict]:
    """Execute a paginated query.

    Args:
        conn: Database connection
        query: Base query (without ORDER BY and LIMIT)
        params: Pagination parameters
        cursor_field: Field to use for cursor (must be in whitelist)
        extra_conditions: Additional WHERE conditions (parameterized only)
        args: Query arguments
        allowed_cursor_fields: Optional additional allowed cursor fields

    Returns:
        PaginatedResult with items and page info

    Raises:
        ValueError: If cursor_field is not in whitelist
    """
    _validate_cursor_field(cursor_field, allowed_cursor_fields)

    args = args or []
    page_size = params.first or params.last or PaginationParams.DEFAULT_PAGE_SIZE

    cursor_value, cursor_template = _get_cursor_info(params, args)
    cursor_condition = (
        cursor_template.format(cursor_field=cursor_field) if cursor_value else ""
    )

    direction = "DESC" if params.last else "ASC"
    limit_param = len(args) + (2 if cursor_value else 1)

    full_query = _build_full_query(
        query, extra_conditions, cursor_condition, cursor_field, direction, limit_param
    )

    query_args = _build_query_args(args, cursor_value, page_size)
    rows = await conn.fetch(full_query, *query_args)

    has_next = len(rows) > page_size
    items = rows[:page_size] if has_next else rows

    if params.last or params.before:
        items = list(reversed(items))

    start_cursor = create_cursor_from_row(items[0], cursor_field) if items else None
    end_cursor = create_cursor_from_row(items[-1], cursor_field) if items else None

    total_count = await _get_total_count(conn, query, args)

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
