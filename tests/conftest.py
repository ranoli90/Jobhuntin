import os
import sys

import asyncpg
import pytest
import pytest_asyncio

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "apps"))
sys.path.insert(0, os.path.join(_REPO_ROOT, "packages"))

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

@pytest_asyncio.fixture(scope="function")
async def db_pool():
    """
    Provides a database connection pool.
    Skips the test if the database is unreachable.
    """
    try:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, timeout=2.0, command_timeout=2.0)
        yield pool
        await pool.close()
    except (OSError, asyncpg.PostgresError, TimeoutError) as e:
        pytest.skip(f"Database unavailable (DATABASE_URL={DATABASE_URL}), skipping test. Error: {e}")


@pytest_asyncio.fixture(scope="function")
async def clean_db(db_pool):
    """
    Cleans test data before/after each test.
    """
    if db_pool is None:
        yield
        return
    
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE public.application_events CASCADE")
        await conn.execute("TRUNCATE TABLE public.application_inputs CASCADE")
        await conn.execute("TRUNCATE TABLE public.applications CASCADE")
        await conn.execute("TRUNCATE TABLE public.profiles CASCADE")
        await conn.execute("TRUNCATE TABLE public.jobs CASCADE")
        await conn.execute("TRUNCATE TABLE public.answer_memory CASCADE")
        await conn.execute("TRUNCATE TABLE public.tenant_members CASCADE")
        await conn.execute("TRUNCATE TABLE public.users CASCADE")
        await conn.execute("TRUNCATE TABLE public.tenants CASCADE")
        await conn.execute("TRUNCATE TABLE public.job_match_cache CASCADE")
        await conn.execute("TRUNCATE TABLE public.billing_customers CASCADE")
    
    yield
    
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE public.application_events CASCADE")
        await conn.execute("TRUNCATE TABLE public.application_inputs CASCADE")
        await conn.execute("TRUNCATE TABLE public.applications CASCADE")
        await conn.execute("TRUNCATE TABLE public.profiles CASCADE")
        await conn.execute("TRUNCATE TABLE public.jobs CASCADE")
        await conn.execute("TRUNCATE TABLE public.answer_memory CASCADE")
        await conn.execute("TRUNCATE TABLE public.tenant_members CASCADE")
        await conn.execute("TRUNCATE TABLE public.users CASCADE")
        await conn.execute("TRUNCATE TABLE public.tenants CASCADE")
        await conn.execute("TRUNCATE TABLE public.job_match_cache CASCADE")
        await conn.execute("TRUNCATE TABLE public.billing_customers CASCADE")
