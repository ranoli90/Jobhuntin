"""Profile assembly — merge profile_data, user_skills, work_style into DeepProfile.

Unifies all profile signals for job matching:
- profiles.profile_data (skills, preferences, career_goals from onboarding)
- user_skills (explicit skills with confidence)
- work_style_profiles (behavioral calibration)
- user_preferences (location, salary_min, remote_only)

OPTIMIZATION: Uses a single batch query with LEFT JOINs and LATERAL json_agg
to fetch all related data in one round trip, avoiding N+1 query patterns.

CACHING: Profile data is cached with 15-minute TTL to reduce database load
for frequently accessed user profiles. Cache is invalidated on profile updates.
"""

from __future__ import annotations

from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.query_cache import PROFILE_TTL, cached, invalidate_cache
from shared.slow_query_monitor import monitor_query

logger = get_logger("sorce.profile_assembly")

from .deep_profile import (
    DealbreakerConfig,
    DeepProfile,
    RichSkill,
    calculate_completeness,
)
from .work_style import CareerTrajectory, WorkStyleProfile


# Optimized single-query profile assembly with batch fetching.
# Uses LATERAL join with json_agg to fetch related user_skills in the same query,
# avoiding N+1 queries when assembling multiple profiles.
PROFILE_ASSEMBLY_QUERY = """
SELECT
    p.profile_data,
    p.resume_url,
    -- User preferences (location, salary, remote preference)
    pref.location AS pref_location,
    pref.role_type AS pref_role_type,
    pref.salary_min AS pref_salary_min,
    pref.remote_only AS pref_remote_only,
    -- Work style profile (behavioral calibration)
    ws.autonomy_preference,
    ws.learning_style,
    ws.company_stage_preference,
    ws.communication_style,
    ws.pace_preference,
    ws.ownership_preference,
    ws.career_trajectory,
    -- Aggregated skills from user_skills table (LATERAL join for efficiency)
    COALESCE(skills.skill_rows, '[]'::json) AS skill_rows
FROM public.profiles p
LEFT JOIN public.user_preferences pref
    ON pref.user_id = p.user_id
LEFT JOIN public.work_style_profiles ws
    ON ws.user_id = p.user_id
LEFT JOIN LATERAL (
    SELECT json_agg(
        json_build_object(
            'skill', us.skill,
            'confidence', us.confidence,
            'years_actual', us.years_actual,
            'context', us.context,
            'last_used', us.last_used,
            'verified', us.verified,
            'source', us.source,
            'project_count', us.project_count
        )
        ORDER BY us.confidence DESC
    ) AS skill_rows
    FROM public.user_skills us
    WHERE us.user_id = p.user_id
) skills ON TRUE
WHERE p.user_id = $1
"""


def _build_profile_cache_key(user_id: str) -> str:
    """Build cache key for profile data."""
    return f"deep_profile:{user_id}"


async def _fetch_profile_raw(
    conn: asyncpg.Connection,
    user_id: str,
) -> dict[str, Any] | None:
    """Fetch raw profile row data from database.
    
    This is the uncached database query used by the cached wrapper.
    """
    async with monitor_query(PROFILE_ASSEMBLY_QUERY) as query_info:
        query_info["params"] = [user_id]
        profile_row = await conn.fetchrow(PROFILE_ASSEMBLY_QUERY, user_id)
    
    if not profile_row:
        return None
    # Convert Record to dict for JSON serialization
    return dict(profile_row)


def _process_profile_row(
    profile_row: dict[str, Any],
    user_id: str,
) -> DeepProfile:
    """Process raw profile row data into a DeepProfile object.
    
    This function contains all the transformation logic, separated from
    the database fetch for easier testing and caching.
    """
    profile_data: dict[str, Any] = {}
    if profile_row["profile_data"]:
        pd = profile_row["profile_data"]
        profile_data = pd if isinstance(pd, dict) else {}

    resume_url = profile_row.get("resume_url")
    has_resume = bool(resume_url)

    # Skills are already aggregated from the LATERAL subquery
    skill_rows = profile_row.get("skill_rows") or []

    competency_graph: list[RichSkill] = []
    seen_skills: set[str] = set()

    # Add user_skills first (explicit, higher fidelity)
    # These rows were already fetched in the main query above
    for row in skill_rows:
        skill_name = (row["skill"] or "").strip()
        if not skill_name or skill_name.lower() in seen_skills:
            continue
        seen_skills.add(skill_name.lower())
        competency_graph.append(
            RichSkill(
                skill=skill_name,
                confidence=float(row["confidence"] or 0.5),
                years_actual=float(row["years_actual"])
                if row["years_actual"]
                else None,
                context=row["context"] or "",
                last_used=row["last_used"],
                verified=bool(row["verified"]),
                source=row["source"] or "resume",
                project_count=int(row["project_count"] or 0),
            )
        )

    # Merge skills from profile_data.skills (onboarding / resume parse)
    # Skills can be: list of str/dict, or dict { technical: [...], soft: [...] }
    pd_skills = profile_data.get("skills") or []
    skills_to_merge: list[str | dict] = []
    if isinstance(pd_skills, list):
        skills_to_merge = pd_skills
    elif isinstance(pd_skills, dict):
        for key in ("technical", "soft", "skills"):
            arr = pd_skills.get(key)
            if isinstance(arr, list):
                skills_to_merge.extend(arr)

    for s in skills_to_merge:
        if isinstance(s, str):
            skill_name = s.strip()
        elif isinstance(s, dict):
            skill_name = (s.get("name") or s.get("skill") or "").strip()
        else:
            continue
        if not skill_name or skill_name.lower() in seen_skills:
            continue
        seen_skills.add(skill_name.lower())
        conf = 0.6
        if isinstance(s, dict) and "confidence" in s:
            conf = float(s.get("confidence", 0.6))
        competency_graph.append(
            RichSkill(
                skill=skill_name,
                confidence=conf,
                source="profile",
            )
        )

    # Work style from work_style_profiles table (already fetched in main query)
    work_style: WorkStyleProfile | None = None
    if any(
        profile_row.get(field) is not None
        for field in (
            "autonomy_preference",
            "learning_style",
            "company_stage_preference",
            "communication_style",
            "pace_preference",
            "ownership_preference",
            "career_trajectory",
        )
    ):
        work_style = WorkStyleProfile(
            autonomy_preference=profile_row["autonomy_preference"] or "medium",
            learning_style=profile_row["learning_style"] or "building",
            company_stage_preference=profile_row["company_stage_preference"]
            or "flexible",
            communication_style=profile_row["communication_style"] or "mixed",
            pace_preference=profile_row["pace_preference"] or "steady",
            ownership_preference=profile_row["ownership_preference"] or "team",
            career_trajectory=CareerTrajectory(
                (profile_row["career_trajectory"] or "open").lower()
            ),
        )
    elif profile_data.get("work_style"):
        try:
            ws_data = profile_data["work_style"]
            if isinstance(ws_data, dict):
                work_style = WorkStyleProfile(**ws_data)
        except Exception as e:
            logger.warning("Failed to parse work_style from profile_data: %s", e)

    # Career trajectory
    trajectory = CareerTrajectory.OPEN
    if work_style:
        trajectory = work_style.career_trajectory

    # User preferences (already fetched in main query)
    preferences: dict[str, Any] = dict(profile_data.get("preferences") or {})
    if profile_row["pref_location"]:
        preferences["location"] = profile_row["pref_location"]
    if profile_row["pref_role_type"]:
        preferences["role_type"] = profile_row["pref_role_type"]
    if profile_row["pref_salary_min"] is not None:
        preferences["salary_min"] = profile_row["pref_salary_min"]
    if profile_row["pref_remote_only"] is not None:
        preferences["remote_only"] = profile_row["pref_remote_only"]

    # Dealbreakers from preferences (coerce salary from form strings)
    def _to_int(v: Any) -> int | None:
        if v is None:
            return None
        if isinstance(v, int):
            return v
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    dealbreakers = DealbreakerConfig(
        min_salary=_to_int(preferences.get("salary_min")),
        max_salary=_to_int(preferences.get("salary_max")),
        locations=[preferences["location"]] if preferences.get("location") else [],
        remote_only=bool(preferences.get("remote_only")),
        onsite_only=False,
    )

    # Check verified email (simplified — no users.email_verified in schema, assume True if profile exists)
    has_verified_email = True

    profile = DeepProfile(
        user_id=user_id,
        competency_graph=competency_graph,
        work_style=work_style,
        trajectory=trajectory,
        dealbreakers=dealbreakers,
        preferences=preferences,
        resume_url=resume_url,
        has_resume=has_resume,
        has_verified_email=has_verified_email,
    )
    profile.completeness_score = calculate_completeness(profile)
    return profile


@cached(prefix="deep_profile", ttl=PROFILE_TTL)
async def _get_cached_profile_raw(
    conn: asyncpg.Connection,
    user_id: str,
) -> dict[str, Any] | None:
    """Cached wrapper for raw profile data fetch.
    
    Note: The conn parameter is included in the cache key hash, but since
    we only care about user_id for caching, we use a custom key builder
    in the outer function.
    """
    return await _fetch_profile_raw(conn, user_id)


async def assemble_profile(
    conn: asyncpg.Connection,
    user_id: str,
    *,
    use_cache: bool = True,
) -> DeepProfile | None:
    """Load and merge all profile sources into a DeepProfile.

    Returns None if user has no profile row (e.g. never onboarded).

    OPTIMIZATION: Fetches profile, preferences, work_style, and skills in a
    single query using LEFT JOINs and LATERAL json_agg. This eliminates the
    N+1 query pattern where each related table required a separate round trip.
    
    CACHING: Profile data is cached for 15 minutes by default. Set use_cache=False
    to bypass cache (e.g., immediately after profile updates).
    """
    from shared.query_cache import get_cached, set_cached
    
    cache_key = _build_profile_cache_key(user_id)
    
    if use_cache:
        # Try to get from cache first
        cached_row = await get_cached(cache_key)
        if cached_row is not None:
            logger.debug(f"Cache hit for profile {user_id}")
            return _process_profile_row(cached_row, user_id)
    
    # Fetch from database
    profile_row = await _fetch_profile_raw(conn, user_id)
    if not profile_row:
        return None
    
    # Cache the raw data
    if use_cache:
        await set_cached(cache_key, profile_row, PROFILE_TTL)
        logger.debug(f"Cache set for profile {user_id}")
    
    return _process_profile_row(profile_row, user_id)


async def invalidate_profile_cache(user_id: str) -> bool:
    """Invalidate cached profile data for a user.
    
    Call this after any profile update operation:
    - Profile data changes
    - User skills updates
    - Work style changes
    - Preference updates
    """
    cache_key = _build_profile_cache_key(user_id)
    result = await invalidate_cache(cache_key)
    if result:
        logger.debug(f"Invalidated cache for profile {user_id}")
    return result
