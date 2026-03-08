"""Batch loading utilities to fix N+1 query issues.

This module provides efficient batch loading functions to prevent N+1 queries
by fetching related data in bulk rather than one-by-one per item.

Usage:
    from shared.batch_loader import BatchLoader

    loader = BatchLoader(pool)
    users = await loader.load_users(user_ids)
    applications = await loader.load_user_applications(user_ids)
"""

from __future__ import annotations

from typing import Any, Dict, List, TypeVar
import asyncpg

T = TypeVar("T")


class BatchLoader:
    """Efficient batch loading utilities for preventing N+1 queries."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def load_users(self, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Load multiple users by their IDs in a single query."""
        if not user_ids:
            return {}

        unique_ids = list(set(user_ids))
        query = """
            SELECT id, email, full_name, headline, bio, resume_url, 
                   has_completed_onboarding, created_at, updated_at,
                   preferences, contact, role
            FROM users 
            WHERE id = ANY($1)
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, unique_ids)
            return {row["id"]: dict(row) for row in rows}

    async def load_user_profiles(
        self, user_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Load multiple user profiles by user IDs in a single query."""
        if not user_ids:
            return {}

        unique_ids = list(set(user_ids))
        query = """
            SELECT user_id, profile_data, resume_url, preferences,
                   created_at, updated_at
            FROM profiles 
            WHERE user_id = ANY($1)
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, unique_ids)
            return {row["user_id"]: dict(row) for row in rows}

    async def load_user_applications(
        self, user_ids: List[str], limit: int = 50, include_job_details: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Load applications for multiple users in a single query."""
        if not user_ids:
            return {}

        unique_ids = list(set(user_ids))

        if include_job_details:
            query = """
                SELECT 
                    a.id, a.user_id, a.job_id, a.status, a.created_at, a.updated_at,
                    a.application_url, a.submitted_at,
                    j.title as job_title, j.company as job_company, j.location as job_location,
                    j.salary_min, j.salary_max, j.remote, j.job_type
                FROM applications a
                LEFT JOIN jobs j ON a.job_id = j.id
                WHERE a.user_id = ANY($1)
                ORDER BY a.created_at DESC
                LIMIT $2
            """
        else:
            query = """
                SELECT id, user_id, job_id, status, created_at, updated_at,
                       application_url, submitted_at
                FROM applications 
                WHERE user_id = ANY($1)
                ORDER BY created_at DESC
                LIMIT $2
            """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, unique_ids, limit)

            # Group by user_id
            result: Dict[str, List[Dict[str, Any]]] = {}
            for row in rows:
                user_id = row["user_id"]
                if user_id not in result:
                    result[user_id] = []
                result[user_id].append(dict(row))

            return result

    async def load_job_details(self, job_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Load multiple job details in a single query."""
        if not job_ids:
            return {}

        unique_ids = list(set(job_ids))
        query = """
            SELECT 
                id, title, company, location, remote, salary_min, salary_max,
                job_type, description, requirements, responsibilities,
                qualifications, benefits, status, created_at, updated_at,
                job_level, experience_years_min, experience_years_max,
                education_required, skills_required, industry_focus,
                remote_option, visa_sponsorship, deadline, team_size,
                team_structure, reporting_to, tags
            FROM jobs 
            WHERE id = ANY($1)
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, unique_ids)
            return {row["id"]: dict(row) for row in rows}

    async def load_saved_jobs(
        self, user_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Load saved jobs for multiple users in a single query."""
        if not user_ids:
            return {}

        unique_ids = list(set(user_ids))
        query = """
            SELECT id, user_id, job_id, saved_at
            FROM saved_jobs 
            WHERE user_id = ANY($1)
            ORDER BY saved_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, unique_ids)

            # Group by user_id
            result: Dict[str, List[Dict[str, Any]]] = {}
            for row in rows:
                user_id = row["user_id"]
                if user_id not in result:
                    result[user_id] = []
                result[user_id].append(dict(row))

            return result

    async def load_cover_letters(
        self, user_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Load cover letters for multiple users in a single query."""
        if not user_ids:
            return {}

        unique_ids = list(set(user_ids))
        query = """
            SELECT id, user_id, job_id, content, created_at, updated_at
            FROM cover_letters 
            WHERE user_id = ANY($1)
            ORDER BY created_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, unique_ids)

            # Group by user_id
            result: Dict[str, List[Dict[str, Any]]] = {}
            for row in rows:
                user_id = row["user_id"]
                if user_id not in result:
                    result[user_id] = []
                result[user_id].append(dict(row))

            return result

    async def load_analytics_events(
        self,
        user_ids: List[str],
        event_types: List[str] | None = None,
        limit: int = 100,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Load analytics events for multiple users in a single query."""
        if not user_ids:
            return {}

        unique_ids = list(set(user_ids))

        if event_types:
            query = """
                SELECT id, user_id, event_type, properties, created_at
                FROM analytics_events 
                WHERE user_id = ANY($1) AND event_type = ANY($2)
                ORDER BY created_at DESC
                LIMIT $3
            """
            params = [unique_ids, event_types, limit]
        else:
            query = """
                SELECT id, user_id, event_type, properties, created_at
                FROM analytics_events 
                WHERE user_id = ANY($1)
                ORDER BY created_at DESC
                LIMIT $2
            """
            params = [unique_ids, limit]

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            # Group by user_id
            result: Dict[str, List[Dict[str, Any]]] = {}
            for row in rows:
                user_id = row["user_id"]
                if user_id not in result:
                    result[user_id] = []
                result[user_id].append(dict(row))

            return result

    async def load_user_preferences(
        self, user_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Load user preferences for multiple users in a single query."""
        if not user_ids:
            return {}

        unique_ids = list(set(user_ids))
        query = """
            SELECT user_id, min_salary, max_salary, preferred_locations,
                   remote_only, job_types, industries, created_at, updated_at
            FROM user_preferences 
            WHERE user_id = ANY($1)
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, unique_ids)
            return {row["user_id"]: dict(row) for row in rows}

    async def load_profile_embeddings(
        self, user_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Load profile embeddings for multiple users in a single query."""
        if not user_ids:
            return {}

        unique_ids = list(set(user_ids))
        query = """
            SELECT user_id, embedding, text_hash, created_at
            FROM profile_embeddings 
            WHERE user_id = ANY($1)
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, unique_ids)
            return {row["user_id"]: dict(row) for row in rows}


class DataLoader:
    """Generic data loader with caching to prevent duplicate queries."""

    def __init__(self, pool: asyncpg.Pool, cache_ttl_seconds: int = 300) -> None:
        self.pool = pool
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, tuple[float, Any]] = {}

    async def load_users(self, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Load users with caching."""
        cache_key = f"users:{','.join(sorted(user_ids))}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        loader = BatchLoader(self.pool)
        result = await loader.load_users(user_ids)
        self._set_cached(cache_key, result)
        return result

    async def load_applications_with_jobs(
        self, user_ids: List[str], limit: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Load applications with job details included."""
        cache_key = f"apps_with_jobs:{','.join(sorted(user_ids))}:{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        loader = BatchLoader(self.pool)

        # First load applications with job details
        applications_by_user = await loader.load_user_applications(
            user_ids, limit, include_job_details=True
        )

        # Extract unique job IDs for additional data loading if needed
        job_ids = set()
        for apps in applications_by_user.values():
            for app in apps:
                if app.get("job_id"):
                    job_ids.add(app["job_id"])

        self._set_cached(cache_key, applications_by_user)
        return applications_by_user

    def _get_cached(self, key: str) -> Any | None:
        """Get cached value if not expired."""
        if key not in self._cache:
            return None

        timestamp, value = self._cache[key]
        import time

        if time.time() - timestamp > self.cache_ttl:
            del self._cache[key]
            return None

        return value

    def _set_cached(self, key: str, value: Any) -> None:
        """Set cached value with timestamp."""
        import time

        self._cache[key] = (time.time(), value)

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
