import os
import pytest
import pytest_asyncio
import asyncpg

# Use local DB by default for tests
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

@pytest_asyncio.fixture(scope="function")
async def db_pool():
    """
    Provides a database connection pool.
    Skips the test if the database is unreachable.
    """
    try:
        # Set a short timeout to fail fast if DB is down
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, timeout=2.0, command_timeout=2.0)
        yield pool
        await pool.close()
    except (OSError, asyncpg.PostgresError, TimeoutError) as e:
        pytest.skip(f"Database unavailable (DATABASE_URL={DATABASE_URL}), skipping test. Error: {e}")
