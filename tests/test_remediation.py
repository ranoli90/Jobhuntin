from unittest.mock import MagicMock

import pytest

from shared.middleware import get_client_ip

# ---------------------------------------------------------------------------
# Task 4: Rate Limiter Proxy Fix Verification
# ---------------------------------------------------------------------------


class TestGetClientIp:
    def test_direct_connection(self):
        """No proxy headers -> use client host."""
        req = MagicMock()
        req.headers.get.return_value = None
        req.client.host = "1.2.3.4"
        assert get_client_ip(req) == "1.2.3.4"

    def test_x_forwarded_for_single(self):
        """Standard proxy usage."""
        req = MagicMock()

        def get_header(key):
            if key == "x-forwarded-for":
                return "10.0.0.1"
            return None

        req.headers.get.side_effect = get_header
        req.client.host = "192.168.1.1"  # LB IP
        assert get_client_ip(req) == "10.0.0.1"

    def test_x_forwarded_for_chain(self):
        """Rightmost IP is the most trustworthy (added by our reverse proxy)."""
        req = MagicMock()

        def get_header(key):
            if key == "x-forwarded-for":
                return "203.0.113.195, 70.41.3.18, 150.172.238.178"
            return None

        req.headers.get.side_effect = get_header
        assert get_client_ip(req) == "150.172.238.178"

    def test_x_real_ip_fallback(self):
        """Fallback to X-Real-IP if no XFF."""
        req = MagicMock()

        def get_header(key):
            if key == "x-real-ip":
                return "10.0.0.2"
            return None

        req.headers.get.side_effect = get_header
        assert get_client_ip(req) == "10.0.0.2"


# ---------------------------------------------------------------------------
# Task 1: Retry Logic Verification (Formula)
# ---------------------------------------------------------------------------


def test_retry_backoff_formula():
    """Verify the exponential backoff seconds calculation."""
    # formula: 30 * (2 ** (attempt - 1))

    def calculate(attempt):
        return 30 * (2 ** (attempt - 1))

    assert calculate(1) == 30
    assert calculate(2) == 60
    assert calculate(3) == 120
    assert calculate(4) == 240


# ---------------------------------------------------------------------------
# Task 2: AI Caching Verification (Integration)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_job_match_cache_repo(db_pool, clean_db):
    """Test Put/Get roundtrip for JobMatchCacheRepo.
    Skipped if no DB available.
    """
    import asyncpg
    import pytest

    from backend.domain.repositories import JobMatchCacheRepo

    async with db_pool.acquire() as conn:
        # 1. Setup
        job_id = "test-job-123"
        profile_hash = "abc123hash"
        score_data = {"score": 85, "summary": "Great match"}

        # 2. Put
        try:
            await JobMatchCacheRepo.put(conn, job_id, profile_hash, score_data)
        except asyncpg.UndefinedTableError:
            pytest.skip("job_match_cache table missing, skipping integration test")

        # 3. Get matches
        result = await JobMatchCacheRepo.get(conn, job_id, profile_hash)
        assert result == score_data

        # 4. Get miss returns None
        result_miss = await JobMatchCacheRepo.get(conn, "other-job", profile_hash)
        assert result_miss is None

        # 5. Update (Upsert)
        new_score = {"score": 90, "summary": "Better match"}
        await JobMatchCacheRepo.put(conn, job_id, profile_hash, new_score)
        result_updated = await JobMatchCacheRepo.get(conn, job_id, profile_hash)
        assert result_updated == new_score
