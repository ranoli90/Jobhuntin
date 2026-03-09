"""Profile assembly — merge profile_data, user_skills, work_style into DeepProfile.

Unifies all profile signals for job matching:
- profiles.profile_data (skills, preferences, career_goals from onboarding)
- user_skills (explicit skills with confidence)
- work_style_profiles (behavioral calibration)
- user_preferences (location, salary_min, remote_only)
"""

from __future__ import annotations

from typing import Any

import asyncpg

from .deep_profile import (
    DealbreakerConfig,
    DeepProfile,
    RichSkill,
    calculate_completeness,
)
from .work_style import CareerTrajectory, WorkStyleProfile


async def assemble_profile(
    conn: asyncpg.Connection,
    user_id: str,
) -> DeepProfile | None:
    """Load and merge all profile sources into a DeepProfile.

    Returns None if user has no profile row (e.g. never onboarded).
    """
    # Load profile_data
    profile_row = await conn.fetchrow(
        "SELECT profile_data, resume_url FROM public.profiles WHERE user_id = $1",
        user_id,
    )
    if not profile_row:
        return None

    profile_data: dict[str, Any] = {}
    if profile_row["profile_data"]:
        pd = profile_row["profile_data"]
        profile_data = pd if isinstance(pd, dict) else {}

    resume_url = profile_row.get("resume_url")
    has_resume = bool(resume_url)

    # Load user_skills
    skill_rows = await conn.fetch(
        """
        SELECT skill, confidence, years_actual, context, last_used, verified, source, project_count
        FROM public.user_skills
        WHERE user_id = $1
        ORDER BY confidence DESC
        """,
        user_id,
    )

    competency_graph: list[RichSkill] = []
    seen_skills: set[str] = set()

    # Add user_skills first (explicit, higher fidelity)
    for row in skill_rows:
        skill_name = (row["skill"] or "").strip()
        if not skill_name or skill_name.lower() in seen_skills:
            continue
        seen_skills.add(skill_name.lower())
        competency_graph.append(
            RichSkill(
                skill=skill_name,
                confidence=float(row["confidence"] or 0.5),
                years_actual=float(row["years_actual"]) if row["years_actual"] else None,
                context=row["context"] or "",
                last_used=row["last_used"],
                verified=bool(row["verified"]),
                source=row["source"] or "resume",
                project_count=int(row["project_count"] or 0),
            )
        )

    # Merge skills from profile_data.skills (onboarding / resume parse)
    pd_skills = profile_data.get("skills") or []
    if isinstance(pd_skills, list):
        for s in pd_skills:
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

    # Load work_style from work_style_profiles table (preferred) or profile_data
    work_style: WorkStyleProfile | None = None
    ws_row = await conn.fetchrow(
        "SELECT autonomy_preference, learning_style, company_stage_preference, "
        "communication_style, pace_preference, ownership_preference, career_trajectory "
        "FROM public.work_style_profiles WHERE user_id = $1",
        user_id,
    )
    if ws_row:
        work_style = WorkStyleProfile(
            autonomy_preference=ws_row["autonomy_preference"] or "medium",
            learning_style=ws_row["learning_style"] or "building",
            company_stage_preference=ws_row["company_stage_preference"] or "flexible",
            communication_style=ws_row["communication_style"] or "mixed",
            pace_preference=ws_row["pace_preference"] or "steady",
            ownership_preference=ws_row["ownership_preference"] or "team",
            career_trajectory=CareerTrajectory(
                (ws_row["career_trajectory"] or "open").lower()
            ),
        )
    elif profile_data.get("work_style"):
        try:
            ws_data = profile_data["work_style"]
            if isinstance(ws_data, dict):
                work_style = WorkStyleProfile(**ws_data)
        except Exception:
            pass

    # Career trajectory
    trajectory = CareerTrajectory.OPEN
    if work_style:
        trajectory = work_style.career_trajectory

    # Load user_preferences
    prefs_row = await conn.fetchrow(
        "SELECT location, role_type, salary_min, remote_only FROM public.user_preferences WHERE user_id = $1",
        user_id,
    )
    preferences: dict[str, Any] = dict(profile_data.get("preferences") or {})
    if prefs_row:
        if prefs_row["location"]:
            preferences["location"] = prefs_row["location"]
        if prefs_row["role_type"]:
            preferences["role_type"] = prefs_row["role_type"]
        if prefs_row["salary_min"] is not None:
            preferences["salary_min"] = prefs_row["salary_min"]
        if prefs_row["remote_only"] is not None:
            preferences["remote_only"] = prefs_row["remote_only"]

    # Dealbreakers from preferences
    dealbreakers = DealbreakerConfig(
        min_salary=preferences.get("salary_min"),
        max_salary=preferences.get("salary_max"),
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
