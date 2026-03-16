"""Tests for SEO Progress Repository.

Tests for the SEOProgressRepository class which manages SEO engine progress
and quota tracking.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

import asyncpg


class TestSEOProgressRepository:
    """Test suite for SEOProgressRepository."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def repository(self, mock_conn):
        """Create SEOProgressRepository with mock connection."""
        from packages.backend.domain.seo_progress import SEOProgressRepository
        return SEOProgressRepository(mock_conn)

    @pytest.mark.asyncio
    async def test_get_progress_returns_none_when_not_found(self, repository, mock_conn):
        """Test that get_progress returns None when service is not found."""
        # Setup mock to return no rows
        mock_conn.fetchrow = AsyncMock(return_value=None)

        result = await repository.get_progress("nonexistent-service")

        assert result is None
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_progress_returns_data_when_found(self, repository, mock_conn):
        """Test that get_progress returns data when service exists."""
        # Setup mock to return a row
        mock_row = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 50,
            "daily_quota_reset": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        result = await repository.get_progress("test-service")

        assert result is not None
        assert result["service_id"] == "test-service"
        assert result["last_index"] == 10
        assert result["daily_quota_used"] == 50

    @pytest.mark.asyncio
    async def test_update_progress_creates_new_if_not_exists(self, repository, mock_conn):
        """Test that update_progress creates a new record if it doesn't exist."""
        # Setup mock to return None (no existing record), then create new
        created_row = {
            "id": 2,
            "service_id": "new-service",
            "last_index": 5,
            "last_submission_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 0,
            "daily_quota_reset": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }

        # First call returns None (no existing record)
        # Second call is the insert (create)
        mock_conn.fetchrow = AsyncMock(side_effect=[None, created_row])

        result = await repository.update_progress("new-service", last_index=5)

        assert result is not None
        assert result["service_id"] == "new-service"
        assert result["last_index"] == 5

    @pytest.mark.asyncio
    async def test_update_progress_updates_existing(self, repository, mock_conn):
        """Test that update_progress updates an existing record."""
        updated_row = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 15,
            "last_submission_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 50,
            "daily_quota_reset": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=updated_row)

        result = await repository.update_progress("test-service", last_index=15)

        assert result is not None
        assert result["last_index"] == 15
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_daily_quota(self, repository, mock_conn):
        """Test that reset_daily_quota resets quota and updates reset time."""
        reset_row = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 0,
            "daily_quota_reset": datetime(2024, 1, 17, 0, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=reset_row)

        result = await repository.reset_daily_quota("test-service")

        assert result is not None
        assert result["daily_quota_used"] == 0
        # Verify the UPDATE query was called
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_daily_quota_creates_new_if_not_exists(self, repository, mock_conn):
        """Test that reset_daily_quota creates a new record if it doesn't exist."""
        created_row = {
            "id": 3,
            "service_id": "brand-new-service",
            "last_index": 0,
            "last_submission_at": None,
            "daily_quota_used": 0,
            "daily_quota_reset": datetime(2024, 1, 17, 0, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
        }

        # First call returns None (no existing record)
        # Second call creates new record
        mock_conn.fetchrow = AsyncMock(side_effect=[None, created_row])

        result = await repository.reset_daily_quota("brand-new-service")

        assert result is not None
        assert result["daily_quota_used"] == 0

    @pytest.mark.asyncio
    async def test_increment_quota(self, repository, mock_conn):
        """Test that increment_quota increases quota usage."""
        # Progress data with datetime objects (as the real method expects)
        # Use a future reset time so no auto-reset is triggered
        future_reset = datetime(2099, 12, 31, 0, 0, 0, tzinfo=timezone.utc)
        existing_progress = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 50,
            "daily_quota_reset": future_reset,  # Future date - no reset needed
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }

        incremented_row = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 51,
            "daily_quota_reset": future_reset,
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        }

        # The method calls: get_progress (1 fetchrow), then increment (1 fetchrow)
        mock_conn.fetchrow = AsyncMock(side_effect=[existing_progress, incremented_row])

        result = await repository.increment_quota("test-service", amount=1)

        assert result is not None
        assert result["daily_quota_used"] == 51

    @pytest.mark.asyncio
    async def test_increment_quota_auto_reset_when_expired(self, repository, mock_conn):
        """Test that quota auto-resets when past reset time."""
        # Progress with expired reset time (using datetime objects)
        expired_progress = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": datetime(2024, 1, 10, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 100,
            "daily_quota_reset": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),  # Past date
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 10, 10, 0, 0, tzinfo=timezone.utc),
        }

        reset_row = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": datetime(2024, 1, 10, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 0,  # Reset to 0
            "daily_quota_reset": datetime(2024, 1, 17, 0, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
        }

        incremented_row = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": datetime(2024, 1, 10, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 1,  # Incremented after reset
            "daily_quota_reset": datetime(2024, 1, 17, 0, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 16, 1, 0, 0, tzinfo=timezone.utc),
        }

        # Sequence: get_progress (returns expired), reset_daily_quota, get_progress again, increment
        mock_conn.fetchrow = AsyncMock(side_effect=[
            expired_progress,  # First get_progress call
            reset_row,  # Reset call
            reset_row,  # Second get_progress call (after reset)
            incremented_row,  # Increment call
        ])

        result = await repository.increment_quota("test-service", amount=1)

        assert result is not None
        # After reset and increment, should be 1
        assert result["daily_quota_used"] == 1


class TestSEOProgressRepositoryEdgeCases:
    """Test edge cases for SEOProgressRepository."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def repository(self, mock_conn):
        """Create SEOProgressRepository with mock connection."""
        from packages.backend.domain.seo_progress import SEOProgressRepository
        return SEOProgressRepository(mock_conn)

    @pytest.mark.asyncio
    async def test_get_progress_handles_null_timestamps(self, repository, mock_conn):
        """Test that get_progress handles NULL timestamps gracefully."""
        mock_row = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": None,  # NULL
            "daily_quota_used": 50,
            "daily_quota_reset": None,  # NULL
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        result = await repository.get_progress("test-service")

        assert result is not None
        assert result["last_submission_at"] is None
        assert result["daily_quota_reset"] is None

    @pytest.mark.asyncio
    async def test_update_progress_with_only_quota(self, repository, mock_conn):
        """Test updating only the quota without changing last_index."""
        updated_row = {
            "id": 1,
            "service_id": "test-service",
            "last_index": 10,
            "last_submission_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "daily_quota_used": 75,
            "daily_quota_reset": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=updated_row)

        result = await repository.update_progress("test-service", daily_quota_used=75)

        assert result is not None
        assert result["daily_quota_used"] == 75
        # last_index should remain unchanged
        assert result["last_index"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
