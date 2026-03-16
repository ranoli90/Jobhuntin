"""Tests for SEO Content Repository.

Tests for the SEOContentRepository class which manages generated SEO content
including content deduplication, topic-intent mapping, and content tracking.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import asyncpg


class TestSEOContentRepository:
    """Test suite for SEOContentRepository."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def repository(self, mock_conn):
        """Create SEOContentRepository with mock connection."""
        from packages.backend.domain.seo_content import SEOContentRepository
        return SEOContentRepository(mock_conn)

    @pytest.mark.asyncio
    async def test_check_content_exists_returns_false_when_not_found(self, repository, mock_conn):
        """Test that check_content_exists returns False when content is not found."""
        mock_conn.fetchrow = AsyncMock(return_value=None)

        result = await repository.check_content_exists("https://example.com/new-page")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_content_exists_returns_true_when_found(self, repository, mock_conn):
        """Test that check_content_exists returns True when content exists."""
        mock_conn.fetchrow = AsyncMock(return_value={"exists": True})

        result = await repository.check_content_exists("https://example.com/existing-page")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_content_hash_exists(self, repository, mock_conn):
        """Test that check_content_hash_exists checks for duplicate content."""
        mock_conn.fetchrow = AsyncMock(return_value={"exists": True})

        result = await repository.check_content_hash_exists("abc123hash")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_content_hash_exists_returns_false_when_not_found(self, repository, mock_conn):
        """Test that check_content_hash_exists returns False when hash not found."""
        mock_conn.fetchrow = AsyncMock(return_value=None)

        result = await repository.check_content_hash_exists("nonexistent-hash")

        assert result is False

    @pytest.mark.asyncio
    async def test_record_generated_content_inserts_new(self, repository, mock_conn):
        """Test that record_generated_content inserts new content successfully."""
        # The method makes 3 fetchrow calls: check_content_exists, check_content_hash_exists, then insert
        # First two return None (no duplicates), third returns inserted row
        inserted_row = {
            "id": 1,
            "url": "https://example.com/new-content",
            "title": "New Content Title",
            "topic": "job-search",
            "intent": "informational",
            "competitor": None,
            "content_hash": "new-hash-123",
            "quality_score": 0.85,
            "google_indexed": False,
            "indexed_at": None,
            "clicks": 0,
            "impressions": 0,
            "ctr": None,
            "position": None,
            "last_updated": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None,
            "created_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }

        # side_effect: URL check returns None (not found), hash check returns None (not found), insert returns row
        mock_conn.fetchrow = AsyncMock(side_effect=[None, None, inserted_row])

        result = await repository.record_generated_content(
            url="https://example.com/new-content",
            title="New Content Title",
            topic="job-search",
            intent="informational",
            content_hash="new-hash-123",
            quality_score=0.85,
        )

        assert result is not None
        assert result["url"] == "https://example.com/new-content"
        assert result["topic"] == "job-search"
        assert result["intent"] == "informational"
        assert result["quality_score"] == 0.85

    @pytest.mark.asyncio
    async def test_record_generated_content_rejects_duplicate_url(self, repository, mock_conn):
        """Test that record_generated_content raises error for duplicate URL."""
        # First call returns a row (URL exists), so duplicate
        mock_conn.fetchrow = AsyncMock(return_value={"exists": True})

        with pytest.raises(ValueError, match="Content already exists"):
            await repository.record_generated_content(
                url="https://example.com/duplicate",
                title="Duplicate Title",
                topic="job-search",
                intent="informational",
                content_hash="different-hash",
            )

    @pytest.mark.asyncio
    async def test_record_generated_content_rejects_duplicate_hash(self, repository, mock_conn):
        """Test that record_generated_content raises error for duplicate content hash."""
        # First call for URL check returns None (URL is new)
        # Second call for hash check returns a row (hash exists)
        mock_conn.fetchrow = AsyncMock(side_effect=[None, {"exists": True}])

        with pytest.raises(ValueError, match="Duplicate content detected"):
            await repository.record_generated_content(
                url="https://example.com/new-url",
                title="New Title",
                topic="job-search",
                intent="informational",
                content_hash="existing-hash",
            )

    @pytest.mark.asyncio
    async def test_record_generated_content_validates_intent(self, repository, mock_conn):
        """Test that record_generated_content validates intent values."""
        mock_conn.fetchrow = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Invalid intent"):
            await repository.record_generated_content(
                url="https://example.com/content",
                title="Title",
                topic="test",
                intent="invalid-intent",  # Invalid intent
                content_hash="hash123",
            )

    @pytest.mark.asyncio
    async def test_get_content_by_url_returns_data(self, repository, mock_conn):
        """Test that get_content_by_url returns content when found."""
        mock_row = {
            "id": 1,
            "url": "https://example.com/test-content",
            "title": "Test Content",
            "topic": "resume",
            "intent": "transactional",
            "competitor": None,
            "content_hash": "hash-abc",
            "quality_score": 0.9,
            "google_indexed": True,
            "indexed_at": datetime(2024, 1, 20, 0, 0, 0, tzinfo=timezone.utc),
            "clicks": 10,
            "impressions": 100,
            "ctr": 0.1,
            "position": 5.0,
            "last_updated": datetime(2024, 1, 25, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None,
            "created_at": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 25, 0, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        result = await repository.get_content_by_url("https://example.com/test-content")

        assert result is not None
        assert result["url"] == "https://example.com/test-content"
        assert result["topic"] == "resume"

    @pytest.mark.asyncio
    async def test_get_content_by_url_returns_none_when_not_found(self, repository, mock_conn):
        """Test that get_content_by_url returns None when not found."""
        mock_conn.fetchrow = AsyncMock(return_value=None)

        result = await repository.get_content_by_url("https://example.com/not-found")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_google_indexing(self, repository, mock_conn):
        """Test updating Google indexing status."""
        updated_row = {
            "id": 1,
            "url": "https://example.com/content",
            "title": "Content",
            "topic": "test",
            "intent": "informational",
            "competitor": None,
            "content_hash": "hash123",
            "quality_score": 0.8,
            "google_indexed": True,
            "indexed_at": datetime(2024, 1, 20, 0, 0, 0, tzinfo=timezone.utc),
            "clicks": 0,
            "impressions": 0,
            "ctr": None,
            "position": None,
            "last_updated": datetime(2024, 1, 20, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None,
            "created_at": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 20, 0, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=updated_row)

        result = await repository.update_google_indexing("https://example.com/content", indexed=True)

        assert result is not None
        assert result["google_indexed"] is True


class TestSEOContentRepositoryQueries:
    """Test query methods for SEOContentRepository."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def repository(self, mock_conn):
        """Create SEOContentRepository with mock connection."""
        from packages.backend.domain.seo_content import SEOContentRepository
        return SEOContentRepository(mock_conn)

    @pytest.mark.asyncio
    async def test_get_content_by_topic_intent(self, repository, mock_conn):
        """Test getting content by topic and intent."""
        mock_rows = [
            {
                "id": 1,
                "url": "https://example.com/content1",
                "title": "Content 1",
                "topic": "jobs",
                "intent": "informational",
                "competitor": None,
                "content_hash": "hash1",
                "quality_score": 0.8,
                "google_indexed": False,
                "indexed_at": None,
                "clicks": 0,
                "impressions": 0,
                "ctr": None,
                "position": None,
                "last_updated": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
                "deleted_at": None,
                "created_at": datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            },
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        result = await repository.get_content_by_topic_intent("jobs", "informational")

        assert len(result) == 1
        assert result[0]["topic"] == "jobs"
        assert result[0]["intent"] == "informational"

    @pytest.mark.asyncio
    async def test_get_content_by_topic(self, repository, mock_conn):
        """Test getting content by topic."""
        mock_rows = [
            {
                "id": 1,
                "url": "https://example.com/page1",
                "title": "Page 1",
                "topic": "career",
                "intent": "informational",
                "competitor": None,
                "content_hash": "hash1",
                "quality_score": 0.7,
                "google_indexed": False,
                "indexed_at": None,
                "clicks": 0,
                "impressions": 0,
                "ctr": None,
                "position": None,
                "last_updated": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
                "deleted_at": None,
                "created_at": datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            },
            {
                "id": 2,
                "url": "https://example.com/page2",
                "title": "Page 2",
                "topic": "career",
                "intent": "commercial",
                "competitor": None,
                "content_hash": "hash2",
                "quality_score": 0.8,
                "google_indexed": False,
                "indexed_at": None,
                "clicks": 0,
                "impressions": 0,
                "ctr": None,
                "position": None,
                "last_updated": datetime(2024, 1, 14, 0, 0, 0, tzinfo=timezone.utc),
                "deleted_at": None,
                "created_at": datetime(2024, 1, 9, 0, 0, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2024, 1, 14, 0, 0, 0, tzinfo=timezone.utc),
            },
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        result = await repository.get_content_by_topic("career")

        assert len(result) == 2
        assert all(r["topic"] == "career" for r in result)

    @pytest.mark.asyncio
    async def test_get_all_topics(self, repository, mock_conn):
        """Test getting all unique topics."""
        mock_rows = [
            {"topic": "jobs"},
            {"topic": "resume"},
            {"topic": "career"},
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        result = await repository.get_all_topics()

        assert len(result) == 3
        assert "jobs" in result
        assert "resume" in result
        assert "career" in result

    @pytest.mark.asyncio
    async def test_soft_delete_content(self, repository, mock_conn):
        """Test soft deleting content."""
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")

        result = await repository.soft_delete_content("https://example.com/to-delete")

        assert result is True
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_content_returns_false_when_not_found(self, repository, mock_conn):
        """Test soft delete returns False when content not found."""
        mock_conn.execute = AsyncMock(return_value="UPDATE 0")

        result = await repository.soft_delete_content("https://example.com/not-found")

        assert result is False


class TestSEOContentRepositoryValidIntents:
    """Test valid intent values."""

    def test_valid_intents_defined(self):
        """Test that valid intents are properly defined."""
        from packages.backend.domain.seo_content import VALID_INTENTS

        assert "informational" in VALID_INTENTS
        assert "commercial" in VALID_INTENTS
        assert "transactional" in VALID_INTENTS
        assert "navigational" in VALID_INTENTS
        assert len(VALID_INTENTS) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
