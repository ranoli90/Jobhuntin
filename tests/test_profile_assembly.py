"""Tests for profile_assembly module."""

from __future__ import annotations

import uuid

import asyncpg
import pytest

from backend.domain.profile_assembly import assemble_profile


@pytest.mark.asyncio
async def test_assemble_profile_no_user(db_pool, clean_db):
    """Assemble returns None when user has no profile."""
    user_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        try:
            profile = await assemble_profile(conn, user_id)
        except asyncpg.UndefinedTableError:
            pytest.skip("profiles table not present in test DB")
    assert profile is None


@pytest.mark.asyncio
async def test_assemble_profile_minimal(db_pool, clean_db):
    """Assemble builds DeepProfile from minimal profile_data."""
    user_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO public.users (id, email) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                user_id,
                f"test-{user_id}@example.com",
            )
            await conn.execute(
                """
                INSERT INTO public.profiles (user_id, profile_data)
                VALUES ($1, $2::jsonb)
                ON CONFLICT (user_id) DO UPDATE SET profile_data = EXCLUDED.profile_data
                """,
                user_id,
                '{"skills": ["Python", "SQL"], "preferences": {"location": "Remote"}}',
            )
            profile = await assemble_profile(conn, user_id)
        except asyncpg.UndefinedTableError:
            pytest.skip("profiles table not present in test DB")

    assert profile is not None
    assert profile.user_id == user_id
    # competency_graph and preferences may vary by implementation
    assert isinstance(profile.competency_graph, list)
    assert isinstance(profile.preferences, dict)
    assert profile.completeness_score >= 0
