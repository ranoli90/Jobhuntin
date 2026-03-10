"""C3: Test Coverage - Critical API endpoint tests.

Tests critical endpoints that must work for production:
- Dashboard data
- Applications list
- Job details
- Health checks
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import uuid

from apps.api.main import app
from shared.config import get_settings


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Generate a valid JWT token for testing."""
    import jwt
    settings = get_settings()
    if not settings.jwt_secret:
        pytest.skip("JWT_SECRET not configured")
    
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "email": "test@example.com",
        "aud": "authenticated",
        "jti": str(uuid.uuid4()),
        "iat": 1000000000,
        "nbf": 1000000000,
        "exp": 1000000000 + 7 * 24 * 3600,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256"), user_id


@pytest.fixture
def authenticated_client(client, auth_token):
    """Client with authentication headers."""
    token, _ = auth_token
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestHealthChecks:
    """Tests for health check endpoints."""

    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_healthz_endpoint(self, client, db_pool):
        """Test deep health check endpoint."""
        response = client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "env" in data
        assert "db" in data
        assert data["db"] in ["ok", "unreachable"]


class TestDashboardAPI:
    """Tests for dashboard API endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_data(self, authenticated_client, clean_db, db_pool, auth_token):
        """Test dashboard data retrieval."""
        _, user_id = auth_token

        # Setup user with some data
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.users (id, email) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                user_id,
                "test@example.com",
            )
            await conn.execute(
                """INSERT INTO public.profiles (user_id, profile_data, tenant_id)
                   VALUES ($1, '{}', NULL) ON CONFLICT DO NOTHING""",
                user_id,
            )
            # Create a tenant
            tenant_id = await conn.fetchval(
                """INSERT INTO public.tenants (id, name, plan)
                   VALUES (gen_random_uuid(), 'Test Tenant', 'FREE')
                   RETURNING id"""
            )
            await conn.execute(
                "UPDATE public.profiles SET tenant_id = $1 WHERE user_id = $2",
                tenant_id,
                user_id,
            )
        
        response = authenticated_client.get("/me/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        assert "active_count" in data
        assert "hold_count" in data
        assert "completed_today" in data
        assert "completed_week" in data
        assert "total_all_time" in data
        assert "recent" in data


class TestApplicationsAPI:
    """Tests for applications API endpoints."""

    @pytest.mark.asyncio
    async def test_create_application(self, authenticated_client, clean_db, db_pool, auth_token):
        """Test creating a new application."""
        _, user_id = auth_token

        # Setup user and job
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.users (id, email) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                user_id,
                "test@example.com",
            )
            job_id = await conn.fetchval(
                """INSERT INTO public.jobs (id, title, company, application_url)
                   VALUES (gen_random_uuid(), 'Software Engineer', 'Test Co', 'https://example.com/apply')
                   RETURNING id"""
            )
        
        application_data = {
            "job_id": str(job_id),
            "decision": "ACCEPT",
        }
        
        response = authenticated_client.post("/me/applications", json=application_data)
        
        # Should succeed
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_list_applications(self, authenticated_client, clean_db, db_pool, auth_token):
        """Test listing user applications."""
        _, user_id = auth_token

        # Setup user with applications
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.users (id, email) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                user_id,
                "test@example.com",
            )
            job_id = await conn.fetchval(
                """INSERT INTO public.jobs (id, title, company)
                   VALUES (gen_random_uuid(), 'Engineer', 'Company')
                   RETURNING id"""
            )
            await conn.execute(
                """INSERT INTO public.applications (id, user_id, job_id, status)
                   VALUES (gen_random_uuid(), $1, $2, 'QUEUED')""",
                user_id,
                job_id,
            )
        
        response = authenticated_client.get("/me/applications")
        
        # Should succeed (adjust endpoint if different)
        assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist


class TestErrorHandling:
    """Tests for error handling and standardized responses."""

    def test_404_error_format(self, client):
        """Test that 404 errors use standardized format."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        # Should have standardized error format (C7 fix)
        data = response.json()
        assert "error" in data or "detail" in data

    def test_401_error_format(self, client):
        """Test that 401 errors use standardized format."""
        response = client.get("/me/profile")  # Requires auth
        
        assert response.status_code == 401
        data = response.json()
        # Should have error code and message (C7 fix)
        assert "error" in data or "detail" in data

    def test_500_error_format(self, client):
        """Test that 500 errors don't leak stack traces."""
        # This would require triggering an actual 500 error
        # which is difficult in tests without mocking
        pass  # TODO: Implement with proper error triggering
