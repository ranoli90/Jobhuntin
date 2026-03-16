"""Tests for cursor-based pagination functionality.

Tests cover:
- Cursor encoding/decoding
- Pagination utility functions
- Edge cases (empty results, last page, invalid cursor)
"""

from __future__ import annotations

import pytest

from shared.pagination import (
    ALLOWED_CURSOR_FIELDS,
    decode_cursor,
    encode_cursor,
    validate_cursor_field,
    validate_identifier,
    create_cursor_from_row,
    PageInfo,
    PaginatedResult,
    PaginationParams,
    paginated_response,
)


class TestCursorEncoding:
    """Tests for cursor encoding and decoding functions."""

    def test_encode_cursor_simple(self):
        """Test encoding a simple cursor."""
        data = {"id": "123", "name": "test"}
        cursor = encode_cursor(data)
        
        assert isinstance(cursor, str)
        assert len(cursor) > 0
        
        # Verify it can be decoded
        decoded = decode_cursor(cursor)
        assert decoded == data

    def test_encode_cursor_with_special_characters(self):
        """Test encoding cursor with special characters."""
        data = {"id": "abc-123_456", "name": "test with spaces"}
        cursor = encode_cursor(data)
        
        decoded = decode_cursor(cursor)
        assert decoded == data

    def test_encode_cursor_with_unicode(self):
        """Test encoding cursor with unicode characters."""
        data = {"id": "123", "name": "日本語テスト"}
        cursor = encode_cursor(data)
        
        decoded = decode_cursor(cursor)
        assert decoded == data

    def test_decode_cursor_invalid_base64(self):
        """Test decoding invalid base64 cursor returns None."""
        result = decode_cursor("not-valid-base64!!!")
        assert result is None

    def test_decode_cursor_invalid_json(self):
        """Test decoding cursor with invalid JSON returns None."""
        import base64
        invalid_json = base64.urlsafe_b64encode(b"not json").decode()
        result = decode_cursor(invalid_json)
        assert result is None

    def test_decode_cursor_empty_string(self):
        """Test decoding empty cursor returns None."""
        result = decode_cursor("")
        assert result is None


class TestCursorValidation:
    """Tests for cursor field validation."""

    def test_validate_identifier_valid(self):
        """Test valid SQL identifiers pass validation."""
        valid_identifiers = ["id", "created_at", "updated_at", "user_id", "_private"]
        
        for identifier in valid_identifiers:
            result = validate_identifier(identifier)
            assert result == identifier

    def test_validate_identifier_invalid(self):
        """Test invalid SQL identifiers fail validation."""
        invalid_identifiers = ["123abc", "user-id", "name; DROP TABLE--", ""]
        
        for identifier in invalid_identifiers:
            with pytest.raises(ValueError):
                validate_identifier(identifier)

    def test_validate_cursor_field_allowed(self):
        """Test allowed cursor fields pass validation."""
        for field in ALLOWED_CURSOR_FIELDS:
            result = validate_cursor_field(field)
            assert result == field

    def test_validate_cursor_field_not_allowed(self):
        """Test non-whitelisted cursor fields fail validation."""
        with pytest.raises(ValueError) as exc_info:
            validate_cursor_field("malicious_field")
        
        assert "Invalid cursor field" in str(exc_info.value)


class TestCreateCursorFromRow:
    """Tests for creating cursors from database rows."""

    def test_create_cursor_from_row_default_field(self):
        """Test creating cursor from row with default sort field."""
        row = {"id": "123", "name": "test", "created_at": "2024-01-01"}
        cursor = create_cursor_from_row(row)
        
        decoded = decode_cursor(cursor)
        assert decoded["id"] == "123"
        assert decoded["sort_value"] == "123"

    def test_create_cursor_from_row_custom_field(self):
        """Test creating cursor from row with custom sort field."""
        row = {"id": "123", "name": "test", "created_at": "2024-01-01T00:00:00Z"}
        cursor = create_cursor_from_row(row, sort_field="created_at")
        
        decoded = decode_cursor(cursor)
        assert decoded["id"] == "123"
        assert decoded["sort_value"] == "2024-01-01T00:00:00Z"

    def test_create_cursor_from_row_invalid_field(self):
        """Test creating cursor with invalid sort field raises error."""
        row = {"id": "123"}
        
        with pytest.raises(ValueError):
            create_cursor_from_row(row, sort_field="invalid_field")


class TestPaginationParams:
    """Tests for PaginationParams dataclass."""

    def test_default_values(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        
        assert params.first == PaginationParams.DEFAULT_PAGE_SIZE
        assert params.after is None
        assert params.last is None
        assert params.before is None

    def test_clamp_max_page_size(self):
        """Test page size is clamped to max."""
        params = PaginationParams(first=1000)
        
        assert params.first == PaginationParams.MAX_PAGE_SIZE

    def test_clamp_last_page_size(self):
        """Test last page size is clamped to max."""
        params = PaginationParams(last=1000)
        
        assert params.last == PaginationParams.MAX_PAGE_SIZE


class TestPageInfo:
    """Tests for PageInfo dataclass."""

    def test_page_info_basic(self):
        """Test basic PageInfo creation."""
        page_info = PageInfo(
            has_next_page=True,
            has_previous_page=False,
            start_cursor="abc",
            end_cursor="def",
            total_count=100,
        )
        
        assert page_info.has_next_page is True
        assert page_info.has_previous_page is False
        assert page_info.start_cursor == "abc"
        assert page_info.end_cursor == "def"
        assert page_info.total_count == 100

    def test_page_info_optional_total(self):
        """Test PageInfo with optional total_count."""
        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        )
        
        assert page_info.total_count is None


class TestPaginatedResult:
    """Tests for PaginatedResult dataclass."""

    def test_paginated_result_basic(self):
        """Test basic PaginatedResult creation."""
        items = [{"id": "1"}, {"id": "2"}]
        page_info = PageInfo(
            has_next_page=True,
            has_previous_page=False,
            start_cursor="abc",
            end_cursor="def",
        )
        
        result = PaginatedResult(items=items, page_info=page_info)
        
        assert len(result.items) == 2
        assert result.page_info.has_next_page is True

    def test_paginated_result_with_extra(self):
        """Test PaginatedResult with extra metadata."""
        items = [{"id": "1"}]
        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="abc",
            end_cursor="def",
        )
        
        result = PaginatedResult(
            items=items,
            page_info=page_info,
            extra={"custom_field": "value"},
        )
        
        assert result.extra["custom_field"] == "value"


class TestPaginatedResponse:
    """Tests for paginated_response function."""

    def test_paginated_response_basic(self):
        """Test basic paginated response generation."""
        items = [{"id": "1"}, {"id": "2"}]
        page_info = PageInfo(
            has_next_page=True,
            has_previous_page=False,
            start_cursor="start",
            end_cursor="end",
            total_count=100,
        )
        result = PaginatedResult(items=items, page_info=page_info)
        
        response = paginated_response(result)
        
        assert response["items"] == items
        assert response["pagination"]["has_next_page"] is True
        assert response["pagination"]["has_previous_page"] is False
        assert response["pagination"]["start_cursor"] == "start"
        assert response["pagination"]["end_cursor"] == "end"
        assert response["pagination"]["total_count"] == 100

    def test_paginated_response_custom_item_key(self):
        """Test paginated response with custom item key."""
        items = [{"id": "1"}]
        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        )
        result = PaginatedResult(items=items, page_info=page_info)
        
        response = paginated_response(result, item_key="data")
        
        assert response["data"] == items
        assert "items" not in response

    def test_paginated_response_with_extra(self):
        """Test paginated response includes extra fields."""
        items = [{"id": "1"}]
        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        )
        result = PaginatedResult(
            items=items,
            page_info=page_info,
            extra={"aggregations": {"total": 100}},
        )
        
        response = paginated_response(result)
        
        assert response["aggregations"]["total"] == 100


class TestPaginationEdgeCases:
    """Tests for pagination edge cases."""

    def test_empty_results(self):
        """Test pagination with empty results."""
        items = []
        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
            total_count=0,
        )
        result = PaginatedResult(items=items, page_info=page_info)
        
        response = paginated_response(result)
        
        assert response["items"] == []
        assert response["pagination"]["has_next_page"] is False
        assert response["pagination"]["total_count"] == 0

    def test_single_item(self):
        """Test pagination with single item."""
        items = [{"id": "1"}]
        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor="cursor1",
            end_cursor="cursor1",
            total_count=1,
        )
        result = PaginatedResult(items=items, page_info=page_info)
        
        response = paginated_response(result)
        
        assert len(response["items"]) == 1
        assert response["pagination"]["start_cursor"] == response["pagination"]["end_cursor"]

    def test_last_page(self):
        """Test pagination on last page."""
        items = [{"id": "91"}, {"id": "92"}]
        page_info = PageInfo(
            has_next_page=False,
            has_previous_page=True,
            start_cursor="cursor91",
            end_cursor="cursor92",
            total_count=92,
        )
        result = PaginatedResult(items=items, page_info=page_info)
        
        response = paginated_response(result)
        
        assert response["pagination"]["has_next_page"] is False
        assert response["pagination"]["has_previous_page"] is True

    def test_cursor_roundtrip_preserves_data(self):
        """Test that cursor encoding/decoding preserves all data."""
        original_data = {
            "id": "abc-123",
            "updated_at": "2024-01-15T10:30:00Z",
            "custom_field": "value",
        }
        
        cursor = encode_cursor(original_data)
        decoded = decode_cursor(cursor)
        
        assert decoded == original_data


class TestPaginationIntegration:
    """Integration tests for pagination with simulated database results."""

    def test_simulated_pagination_flow(self):
        """Test a complete pagination flow simulation."""
        # Simulate a page of results
        items = [
            {"id": f"item-{i}", "name": f"Item {i}"} for i in range(1, 21)
        ]
        
        # Create cursors for first and last items
        start_cursor = create_cursor_from_row(items[0], sort_field="id")
        end_cursor = create_cursor_from_row(items[-1], sort_field="id")
        
        # Create page info
        page_info = PageInfo(
            has_next_page=True,
            has_previous_page=False,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
            total_count=100,
        )
        
        # Create result
        result = PaginatedResult(items=items, page_info=page_info)
        response = paginated_response(result)
        
        # Verify response structure
        assert len(response["items"]) == 20
        assert response["pagination"]["has_next_page"] is True
        assert response["pagination"]["total_count"] == 100
        
        # Verify we can decode the end cursor for next page
        next_cursor_data = decode_cursor(response["pagination"]["end_cursor"])
        assert next_cursor_data["id"] == "item-20"

    def test_simulated_second_page(self):
        """Test second page pagination simulation."""
        # Simulate receiving a cursor from previous page
        prev_cursor = encode_cursor({"id": "item-20", "sort_value": "item-20"})
        
        # Decode to get starting point
        cursor_data = decode_cursor(prev_cursor)
        assert cursor_data["id"] == "item-20"
        
        # Simulate fetching next page (items 21-40)
        items = [
            {"id": f"item-{i}", "name": f"Item {i}"} for i in range(21, 41)
        ]
        
        start_cursor = create_cursor_from_row(items[0], sort_field="id")
        end_cursor = create_cursor_from_row(items[-1], sort_field="id")
        
        page_info = PageInfo(
            has_next_page=True,
            has_previous_page=True,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
            total_count=100,
        )
        
        result = PaginatedResult(items=items, page_info=page_info)
        response = paginated_response(result)
        
        assert response["pagination"]["has_previous_page"] is True
        assert response["pagination"]["has_next_page"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
