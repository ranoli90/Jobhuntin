"""
API Pagination System

Comprehensive pagination support with cursor-based, offset-based, and custom strategies.
Includes metadata generation, performance optimization, and flexible configuration.
"""

import base64
import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel

from shared.logging_config import get_logger

logger = get_logger("sorce.api_pagination")

T = TypeVar("T")


class PaginationType(Enum):
    """Supported pagination strategies."""

    OFFSET = "offset"
    CURSOR = "cursor"
    PAGE = "page"
    SEARCH = "search"


class SortOrder(Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class PaginationConfig:
    """Configuration for pagination behavior."""

    default_limit: int = 20
    max_limit: int = 100
    default_type: PaginationType = PaginationType.OFFSET
    allow_cursor: bool = True
    allow_offset: bool = True
    allow_page: bool = True
    enable_metadata: bool = True
    enable_total_count: bool = True
    cache_ttl_seconds: int = 300
    cursor_salt: str = "pagination_cursor"


@dataclass
class PaginationParams:
    """Pagination parameters extracted from request."""

    type: PaginationType
    limit: int
    offset: Optional[int] = None
    page: Optional[int] = None
    cursor: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.ASC
    search: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize parameters."""
        if self.limit <= 0:
            self.limit = 20
        if self.offset is not None and self.offset < 0:
            self.offset = 0
        if self.page is not None and self.page < 1:
            self.page = 1


@dataclass
class PaginationMetadata:
    """Metadata for paginated responses."""

    total_count: Optional[int] = None
    limit: int = 20
    offset: Optional[int] = None
    page: Optional[int] = None
    total_pages: Optional[int] = None
    has_next: bool = False
    has_previous: bool = False
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    next_url: Optional[str] = None
    previous_url: Optional[str] = None
    first_url: Optional[str] = None
    last_url: Optional[str] = None
    current_url: Optional[str] = None
    request_time: datetime = field(default_factory=lambda: datetime.now(UTC))


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard response format for paginated data."""

    data: List[T]
    metadata: PaginationMetadata
    success: bool = True
    message: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class CursorManager:
    """Manages cursor creation and parsing for cursor-based pagination."""

    def __init__(self, salt: str = "pagination_cursor"):
        self.salt = salt

    def create_cursor(
        self,
        value: Union[str, int, datetime],
        sort_by: str,
        sort_order: SortOrder,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create an encoded cursor."""
        cursor_data = {
            "value": str(value),
            "sort_by": sort_by,
            "sort_order": sort_order.value,
            "filters": filters or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Create hash for integrity
        cursor_json = json.dumps(cursor_data, sort_keys=True)
        hash_input = f"{cursor_json}:{self.salt}"
        cursor_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        # Combine data and hash
        cursor_combined = f"{cursor_json}:{cursor_hash}"
        cursor_encoded = base64.urlsafe_b64encode(cursor_combined.encode()).decode()

        return cursor_encoded

    def parse_cursor(self, cursor: str) -> Dict[str, Any]:
        """Parse and validate an encoded cursor."""
        try:
            # Decode cursor
            cursor_decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
            cursor_json, cursor_hash = cursor_decoded.rsplit(":", 1)

            # Verify hash
            hash_input = f"{cursor_json}:{self.salt}"
            expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

            if cursor_hash != expected_hash:
                raise ValueError("Invalid cursor hash")

            # Parse data
            cursor_data = json.loads(cursor_json)

            # Check timestamp (optional expiry)
            cursor_time = datetime.fromisoformat(cursor_data["timestamp"])
            if datetime.now(UTC) - cursor_time > timedelta(hours=24):
                raise ValueError("Cursor expired")

            return cursor_data

        except Exception as e:
            logger.error(f"Failed to parse cursor: {e}")
            raise ValueError("Invalid cursor format")


class PaginationManager:
    """Main pagination manager with support for multiple strategies."""

    def __init__(self, config: Optional[PaginationConfig] = None):
        self.config = config or PaginationConfig()
        self.cursor_manager = CursorManager(self.config.cursor_salt)

    def extract_params(
        self, request: Request, allowed_sort_fields: Optional[List[str]] = None
    ) -> PaginationParams:
        """Extract pagination parameters from request."""
        query_params = request.query_params

        # Get pagination type
        pagination_type_str = query_params.get("type", self.config.default_type.value)
        try:
            pagination_type = PaginationType(pagination_type_str)
        except ValueError:
            pagination_type = self.config.default_type

        # Validate type is allowed
        if pagination_type == PaginationType.CURSOR and not self.config.allow_cursor:
            pagination_type = PaginationType.OFFSET
        elif pagination_type == PaginationType.OFFSET and not self.config.allow_offset:
            pagination_type = PaginationType.PAGE
        elif pagination_type == PaginationType.PAGE and not self.config.allow_page:
            pagination_type = PaginationType.OFFSET

        # Get limit
        limit = min(
            int(query_params.get("limit", self.config.default_limit)),
            self.config.max_limit,
        )

        # Get type-specific parameters
        offset = None
        page = None
        cursor = None

        if pagination_type == PaginationType.OFFSET:
            offset = int(query_params.get("offset", 0))
        elif pagination_type == PaginationType.PAGE:
            page = int(query_params.get("page", 1))
        elif pagination_type == PaginationType.CURSOR:
            cursor = query_params.get("cursor")

        # Get sort parameters
        sort_by = query_params.get("sort_by")
        if sort_by and allowed_sort_fields and sort_by not in allowed_sort_fields:
            sort_by = allowed_sort_fields[0] if allowed_sort_fields else None

        sort_order_str = query_params.get("sort_order", "asc")
        try:
            sort_order = SortOrder(sort_order_str.lower())
        except ValueError:
            sort_order = SortOrder.ASC

        # Get search term
        search = query_params.get("search")

        # Extract filters (non-pagination parameters)
        filters = {}
        reserved_params = {
            "type",
            "limit",
            "offset",
            "page",
            "cursor",
            "sort_by",
            "sort_order",
            "search",
        }

        for param, value in query_params.items():
            if param not in reserved_params:
                filters[param] = value

        return PaginationParams(
            type=pagination_type,
            limit=limit,
            offset=offset,
            page=page,
            cursor=cursor,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )

    def create_response(
        self,
        data: List[T],
        params: PaginationParams,
        total_count: Optional[int] = None,
        request: Optional[Request] = None,
    ) -> PaginatedResponse[T]:
        """Create a paginated response with metadata."""
        metadata = self._create_metadata(data, params, total_count, request)

        return PaginatedResponse[T](data=data, metadata=metadata)

    def _create_metadata(
        self,
        data: List[T],
        params: PaginationParams,
        total_count: Optional[int],
        request: Optional[Request],
    ) -> PaginationMetadata:
        """Create pagination metadata."""
        metadata = PaginationMetadata(
            limit=params.limit,
            offset=params.offset,
            page=params.page,
            total_count=total_count,
        )

        # Calculate derived values
        if total_count is not None:
            metadata.total_pages = math.ceil(total_count / params.limit)

            if params.type == PaginationType.OFFSET:
                metadata.has_next = params.offset + params.limit < total_count
                metadata.has_previous = params.offset > 0
            elif params.type == PaginationType.PAGE:
                metadata.has_next = params.page < metadata.total_pages
                metadata.has_previous = params.page > 1

        # Generate navigation URLs if request is provided
        if request:
            metadata.current_url = str(request.url)
            metadata = self._generate_navigation_urls(metadata, params, request)

        return metadata

    def _generate_navigation_urls(
        self, metadata: PaginationMetadata, params: PaginationParams, request: Request
    ) -> PaginationMetadata:
        """Generate navigation URLs for pagination."""
        str(request.url)
        query_params = dict(request.query_params)

        # Helper to build URL with modified parameters
        def build_url(**overrides):
            new_params = query_params.copy()
            new_params.update(overrides)
            # Remove pagination-specific params that don't apply
            if params.type != PaginationType.OFFSET:
                new_params.pop("offset", None)
            if params.type != PaginationType.PAGE:
                new_params.pop("page", None)
            if params.type != PaginationType.CURSOR:
                new_params.pop("cursor", None)

            # Remove empty parameters
            new_params = {
                k: v for k, v in new_params.items() if v is not None and v != ""
            }

            return str(request.url.replace_query_params(**new_params))

        if params.type == PaginationType.OFFSET:
            if metadata.has_next:
                metadata.next_url = build_url(offset=params.offset + params.limit)
            if metadata.has_previous:
                metadata.previous_url = build_url(
                    offset=max(0, params.offset - params.limit)
                )
            metadata.first_url = build_url(offset=0)
            if metadata.total_pages:
                last_offset = (metadata.total_pages - 1) * params.limit
                metadata.last_url = build_url(offset=last_offset)

        elif params.type == PaginationType.PAGE:
            if metadata.has_next:
                metadata.next_url = build_url(page=params.page + 1)
            if metadata.has_previous:
                metadata.previous_url = build_url(page=params.page - 1)
            metadata.first_url = build_url(page=1)
            if metadata.total_pages:
                metadata.last_url = build_url(page=metadata.total_pages)

        return metadata

    def apply_cursor_to_query(
        self, query: Any, params: PaginationParams, cursor_field: str = "id"
    ) -> Any:
        """Apply cursor filtering to a database query."""
        if params.type != PaginationType.CURSOR or not params.cursor:
            return query

        try:
            cursor_data = self.cursor_manager.parse_cursor(params.cursor)
            cursor_value = cursor_data["value"]

            # Apply cursor filter based on sort order
            if params.sort_order == SortOrder.ASC:
                query = query.filter(
                    getattr(query.column_described(cursor_field)) > cursor_value
                )
            else:
                query = query.filter(
                    getattr(query.column_described(cursor_field)) < cursor_value
                )

            return query

        except Exception as e:
            logger.error(f"Failed to apply cursor: {e}")
            raise HTTPException(status_code=400, detail="Invalid cursor")

    def create_cursor_from_item(
        self, item: Dict[str, Any], params: PaginationParams
    ) -> Optional[str]:
        """Create a cursor from the last item in a result set."""
        if params.type != PaginationType.CURSOR or not item:
            return None

        # Use sort_by field or default to 'id'
        cursor_field = params.sort_by or "id"
        cursor_value = item.get(cursor_field)

        if cursor_value is None:
            return None

        return self.cursor_manager.create_cursor(
            cursor_value, cursor_field, params.sort_order, params.filters
        )


class OffsetPaginationHelper:
    """Helper for offset-based pagination."""

    @staticmethod
    def apply_offset_limit(query: Any, offset: int, limit: int) -> Any:
        """Apply offset and limit to a query."""
        return query.offset(offset).limit(limit)

    @staticmethod
    def calculate_offset(page: int, limit: int) -> int:
        """Calculate offset from page number."""
        return (page - 1) * limit


class CursorPaginationHelper:
    """Helper for cursor-based pagination."""

    @staticmethod
    def build_cursor_condition(
        field_name: str, cursor_value: Any, sort_order: SortOrder
    ) -> str:
        """Build SQL condition for cursor pagination."""
        if sort_order == SortOrder.ASC:
            return f"{field_name} > '{cursor_value}'"
        else:
            return f"{field_name} < '{cursor_value}'"


class SearchPaginationHelper:
    """Helper for search-based pagination with relevance scoring."""

    @staticmethod
    def apply_search_filters(
        query: Any, search_term: str, search_fields: List[str]
    ) -> Any:
        """Apply search filters to a query."""
        if not search_term or not search_fields:
            return query

        # Build search conditions
        search_conditions = []
        for search_field in search_fields:
            search_conditions.append(
                getattr(query.column_described(search_field)).ilike(f"%{search_term}%")
            )

        # Combine with OR
        from sqlalchemy import or_

        return query.filter(or_(*search_conditions))


# Utility functions for FastAPI dependency injection
def get_pagination_params(
    request: Request,
    type: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: Optional[int] = Query(default=None, ge=0),
    page: Optional[int] = Query(default=None, ge=1),
    cursor: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default=None),
    sort_order: Optional[str] = Query(default="asc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(default=None),
    config: Optional[PaginationConfig] = None,
) -> PaginationParams:
    """FastAPI dependency for pagination parameters."""
    manager = PaginationManager(config)

    # Build query params dict
    query_params = {}
    if type is not None:
        query_params["type"] = type
    if limit is not None:
        query_params["limit"] = limit
    if offset is not None:
        query_params["offset"] = offset
    if page is not None:
        query_params["page"] = page
    if cursor is not None:
        query_params["cursor"] = cursor
    if sort_by is not None:
        query_params["sort_by"] = sort_by
    if sort_order is not None:
        query_params["sort_order"] = sort_order
    if search is not None:
        query_params["search"] = search

    # Create a mock request with the query params
    from unittest.mock import Mock

    mock_request = Mock()
    mock_request.query_params = query_params

    return manager.extract_params(mock_request)


def paginate_query(
    query: Any, params: PaginationParams, manager: Optional[PaginationManager] = None
) -> tuple[Any, Optional[str]]:
    """Apply pagination to a database query."""
    if manager is None:
        manager = PaginationManager()

    # Apply cursor filtering if needed
    if params.type == PaginationType.CURSOR:
        query = manager.apply_cursor_to_query(query, params)

    # Apply offset/limit
    if params.type == PaginationType.OFFSET:
        query = OffsetPaginationHelper.apply_offset_limit(
            query, params.offset, params.limit
        )
    elif params.type == PaginationType.PAGE:
        offset = OffsetPaginationHelper.calculate_offset(params.page, params.limit)
        query = OffsetPaginationHelper.apply_offset_limit(query, offset, params.limit)
    else:  # CURSOR
        query = query.limit(
            params.limit + 1
        )  # Get one extra to check if there's a next page

    return query, None


def create_paginated_response(
    data: List[T],
    params: PaginationParams,
    total_count: Optional[int] = None,
    request: Optional[Request] = None,
    manager: Optional[PaginationManager] = None,
    last_item: Optional[Dict[str, Any]] = None,
) -> PaginatedResponse[T]:
    """Create a paginated response with proper metadata."""
    if manager is None:
        manager = PaginationManager()

    # Handle cursor next page detection
    if (
        params.type == PaginationType.CURSOR
        and last_item
        and len(data) == params.limit + 1
    ):
        # Remove the extra item
        data = data[:-1]
        # Create next cursor
        next_cursor = manager.create_cursor_from_item(last_item, params)
        metadata = manager._create_metadata(data, params, total_count, request)
        metadata.next_cursor = next_cursor
        metadata.has_next = True
    else:
        metadata = manager._create_metadata(data, params, total_count, request)

    return PaginatedResponse[T](data=data, metadata=metadata)


# Global instances
default_pagination_manager = PaginationManager()

# Configuration presets
API_PAGINATION_CONFIG = PaginationConfig(
    default_limit=20,
    max_limit=100,
    allow_cursor=True,
    allow_offset=True,
    allow_page=True,
    enable_metadata=True,
    enable_total_count=True,
)

SEARCH_PAGINATION_CONFIG = PaginationConfig(
    default_limit=10,
    max_limit=50,
    default_type=PaginationType.OFFSET,
    allow_cursor=False,  # Cursor not suitable for search
    allow_offset=True,
    allow_page=True,
    enable_metadata=True,
    enable_total_count=True,
)

ADMIN_PAGINATION_CONFIG = PaginationConfig(
    default_limit=50,
    max_limit=200,
    allow_cursor=True,
    allow_offset=True,
    allow_page=True,
    enable_metadata=True,
    enable_total_count=True,
)
