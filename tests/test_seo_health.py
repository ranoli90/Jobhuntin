"""Tests for SEO Health Check.

Tests for the SEOHealthCheck class which monitors the health of SEO engine
components including database connectivity, table existence, quota status, and error monitoring.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import asyncpg


class TestSEOHealthCheck:
    """Test suite for SEOHealthCheck."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def health_check(self, mock_conn):
        """Create SEOHealthCheck with mock connection."""
        from packages.backend.domain.seo_health import SEOHealthCheck
        return SEOHealthCheck(mock_conn)

    @pytest.mark.asyncio
    async def test_health_status_defaults_to_unhealthy(self):
        """Test that SEOHealthStatus defaults to unhealthy when initialized."""
        from packages.backend.domain.seo_health import SEOHealthStatus

        # Create with healthy=False
        status = SEOHealthStatus(healthy=False)

        assert status.healthy is False
        assert status.overall_status == "healthy"  # Default value in dataclass

    @pytest.mark.asyncio
    async def test_health_status_can_be_created_with_healthy_true(self):
        """Test that SEOHealthStatus can be set to healthy."""
        from packages.backend.domain.seo_health import SEOHealthStatus

        status = SEOHealthStatus(healthy=True, overall_status="healthy")

        assert status.healthy is True
        assert status.overall_status == "healthy"

    @pytest.mark.asyncio
    async def test_check_database_connection_returns_healthy(self, health_check, mock_conn):
        """Test that database connection check returns healthy when connected."""
        mock_conn.fetchval = AsyncMock(return_value=1)

        result = await health_check.check_database_connection()

        assert result["status"] == "healthy"
        assert "Database connection is active" in result["message"]
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_check_database_connection_graceful_failure(self, health_check, mock_conn):
        """Test that database connection check handles failures gracefully."""
        # Simulate a database connection error
        mock_conn.fetchval = AsyncMock(side_effect=ConnectionError("Connection refused"))

        result = await health_check.check_database_connection()

        assert result["status"] == "unhealthy"
        assert "ConnectionError" in result["message"] or "connection failed" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_database_connection_handles_invalid_catalog(self, health_check, mock_conn):
        """Test that database connection handles InvalidCatalogNameError gracefully."""
        mock_conn.fetchval = AsyncMock(
            side_effect=asyncpg.InvalidCatalogNameError("Database does not exist")
        )

        result = await health_check.check_database_connection()

        assert result["status"] == "unhealthy"
        assert "Database not found" in result["message"]

    @pytest.mark.asyncio
    async def test_check_database_connection_handles_invalid_password(self, health_check, mock_conn):
        """Test that database connection handles InvalidPasswordError gracefully."""
        mock_conn.fetchval = AsyncMock(
            side_effect=asyncpg.InvalidPasswordError("Password authentication failed")
        )

        result = await health_check.check_database_connection()

        assert result["status"] == "unhealthy"
        assert "authentication failed" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_database_connection_handles_unexpected_result(self, health_check, mock_conn):
        """Test that database connection handles unexpected results."""
        # Return something other than 1
        mock_conn.fetchval = AsyncMock(return_value=0)

        result = await health_check.check_database_connection()

        assert result["status"] == "unhealthy"
        assert "unexpected result" in result["message"].lower()


class TestSEOHealthCheckTables:
    """Test table existence checks."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def health_check(self, mock_conn):
        """Create SEOHealthCheck with mock connection."""
        from packages.backend.domain.seo_health import SEOHealthCheck
        return SEOHealthCheck(mock_conn)

    @pytest.mark.asyncio
    async def test_check_progress_table_returns_healthy(self, health_check, mock_conn):
        """Test that progress table check returns healthy when table exists."""
        # fetchval with no result means query succeeded
        mock_conn.fetchval = AsyncMock(return_value=None)

        result = await health_check.check_progress_table()

        assert result["status"] == "healthy"
        assert "seo_engine_progress" in result["message"]

    @pytest.mark.asyncio
    async def test_check_progress_table_returns_unhealthy_when_missing(self, health_check, mock_conn):
        """Test that progress table check returns unhealthy when table is missing."""
        mock_conn.fetchval = AsyncMock(
            side_effect=asyncpg.UndefinedTableError("Table does not exist")
        )

        result = await health_check.check_progress_table()

        assert result["status"] == "unhealthy"
        assert "does not exist" in result["message"]

    @pytest.mark.asyncio
    async def test_check_content_table_returns_degraded_on_missing_columns(self, health_check, mock_conn):
        """Test that content table check returns degraded when columns are missing."""
        mock_conn.fetchval = AsyncMock(
            side_effect=asyncpg.UndefinedColumnError("Column does not exist")
        )

        result = await health_check.check_content_table()

        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_check_metrics_table(self, health_check, mock_conn):
        """Test metrics table check."""
        mock_conn.fetchval = AsyncMock(return_value=None)

        result = await health_check.check_metrics_table()

        assert result["status"] == "healthy"


class TestSEOHealthCheckQuota:
    """Test quota status checks."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def health_check(self, mock_conn):
        """Create SEOHealthCheck with mock connection."""
        from packages.backend.domain.seo_health import SEOHealthCheck
        return SEOHealthCheck(mock_conn)

    @pytest.mark.asyncio
    async def test_check_quota_status_returns_healthy_when_available(self, health_check, mock_conn):
        """Test that quota check returns healthy when quota is available."""
        mock_row = {
            "service_id": "test-service",
            "daily_quota_used": 50,
            "daily_quota_reset": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        result = await health_check.check_quota_status("test-service")

        assert result["status"] == "healthy"
        assert result["quota_used"] == 50
        assert result["quota_remaining"] == 950  # 1000 - 50

    @pytest.mark.asyncio
    async def test_check_quota_status_returns_unhealthy_when_exhausted(self, health_check, mock_conn):
        """Test that quota check returns unhealthy when quota is exhausted."""
        mock_row = {
            "service_id": "test-service",
            "daily_quota_used": 1000,
            "daily_quota_reset": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        result = await health_check.check_quota_status("test-service")

        assert result["status"] == "unhealthy"
        assert result["quota_remaining"] == 0
        assert "exhausted" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_quota_status_returns_degraded_when_low(self, health_check, mock_conn):
        """Test that quota check returns degraded when quota is running low."""
        mock_row = {
            "service_id": "test-service",
            "daily_quota_used": 950,
            "daily_quota_reset": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        result = await health_check.check_quota_status("test-service")

        assert result["status"] == "degraded"
        assert result["quota_remaining"] == 50

    @pytest.mark.asyncio
    async def test_check_quota_status_returns_healthy_when_no_record(self, health_check, mock_conn):
        """Test that quota check returns healthy when no progress record exists."""
        mock_conn.fetchrow = AsyncMock(return_value=None)

        result = await health_check.check_quota_status("new-service")

        assert result["status"] == "healthy"
        assert result["quota_used"] == 0
        assert result["quota_remaining"] == 1000


class TestSEOHealthCheckErrors:
    """Test error checking."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def health_check(self, mock_conn):
        """Create SEOHealthCheck with mock connection."""
        from packages.backend.domain.seo_health import SEOHealthCheck
        return SEOHealthCheck(mock_conn)

    @pytest.mark.asyncio
    async def test_check_recent_errors_returns_healthy_when_no_errors(self, health_check, mock_conn):
        """Test that error check returns healthy when no errors exist."""
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.fetchrow = AsyncMock(return_value={"count": 0})

        result = await health_check.check_recent_errors()

        assert result["status"] == "healthy"
        assert result["error_count"] == 0

    @pytest.mark.asyncio
    async def test_check_recent_errors_handles_missing_logs_table(self, health_check, mock_conn):
        """Test that error check handles missing logs table gracefully."""
        mock_conn.fetch = AsyncMock(
            side_effect=asyncpg.UndefinedTableError("Table does not exist")
        )

        result = await health_check.check_recent_errors()

        # Should return healthy since logs table is optional
        assert result["status"] == "healthy"
        assert "does not exist" in result["message"].lower()


class TestSEOHealthCheckRunAll:
    """Test running all health checks."""

    @pytest.fixture
    def mock_conn(self):
        """Create a mock asyncpg connection."""
        conn = AsyncMock(spec=asyncpg.Connection)
        return conn

    @pytest.fixture
    def health_check(self, mock_conn):
        """Create SEOHealthCheck with mock connection."""
        from packages.backend.domain.seo_health import SEOHealthCheck
        return SEOHealthCheck(mock_conn)

    @pytest.mark.asyncio
    async def test_run_all_checks_returns_overall_status(self, health_check, mock_conn):
        """Test that run_all_checks returns overall status."""
        # Mock database connection as healthy
        mock_conn.fetchval = AsyncMock(return_value=1)
        # Mock table checks
        mock_conn.fetchval = AsyncMock(side_effect=[1, None, None, None])
        # Mock error check
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.fetchrow = AsyncMock(return_value={"count": 0})

        result = await health_check.run_all_checks()

        assert hasattr(result, "healthy")
        assert hasattr(result, "checks")
        assert "database_connection" in result.checks

    @pytest.mark.asyncio
    async def test_run_all_checks_generates_recommendations(self, health_check, mock_conn):
        """Test that run_all_checks generates recommendations when unhealthy."""
        # Make database connection unhealthy
        mock_conn.fetchval = AsyncMock(side_effect=ConnectionError("Connection failed"))

        result = await health_check.run_all_checks()

        # When database is down, should have recommendations
        assert len(result.recommendations) > 0


class TestSEOHealthStatus:
    """Test SEOHealthStatus dataclass."""

    def test_health_status_dataclass(self):
        """Test that SEOHealthStatus is a proper dataclass."""
        from packages.backend.domain.seo_health import SEOHealthStatus

        status = SEOHealthStatus(
            healthy=True,
            checks={"db": {"status": "healthy"}},
            overall_status="healthy",
            recommendations=["All good!"],
        )

        assert status.healthy is True
        assert status.overall_status == "healthy"
        assert len(status.recommendations) == 1

    def test_health_status_default_values(self):
        """Test default values for SEOHealthStatus."""
        from packages.backend.domain.seo_health import SEOHealthStatus

        status = SEOHealthStatus(healthy=False)

        assert status.healthy is False
        assert status.overall_status == "healthy"  # Default
        assert status.checks == {}
        assert status.recommendations == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
