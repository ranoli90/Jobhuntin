"""Job scoring engine — profile-based job ranking.

Scores jobs against a DeepProfile using weighted dimensions:
- Skill overlap (40%)
- Location match (15%)
- Salary fit (15%)
- Work culture signals (20%)
- Career trajectory alignment (10%)
"""

from __future__ import annotations

import re
from typing import Any

from .deep_profile import DealbreakerConfig, DeepProfile, RichSkill
from .work_style import CareerTrajectory, WorkStyleProfile


# ── Dealbreaker hard-filter ──────────────────────────────────

def apply_dealbreaker_filters(
    jobs: list[dict[str, Any]],
    dealbreakers: DealbreakerConfig,
) -> list[dict[str, Any]]:
    """Remove jobs that violate the user's hard dealbreakers."""
    filtered: list[dict[str, Any]] = []
    excluded_companies_lower = {c.lower() for c in dealbreakers.excluded_companies}
    excluded_keywords_lower = {k.lower() for k in dealbreakers.excluded_keywords}

    for job in jobs:
        company = (job.get("company") or "").lower()
        title = (job.get("title") or "").lower()
        description = (job.get("description") or "").lower()
        location = (job.get("location") or "").lower()

        # Excluded companies
        if company in excluded_companies_lower:
            continue

        # Excluded keywords (in title or description)
        if any(kw in title or kw in description for kw in excluded_keywords_lower):
            continue

        # Salary floor
        salary_max = job.get("salary_max")
        if (
            dealbreakers.min_salary is not None
            and salary_max is not None
            and salary_max < dealbreakers.min_salary
        ):
            continue

        # Remote-only filter
        if dealbreakers.remote_only:
            is_remote = job.get("is_remote", False)
            remote_in_loc = "remote" in location or "anywhere" in location
            if not is_remote and not remote_in_loc:
                continue

        # Onsite-only filter
        if dealbreakers.onsite_only:
            if "remote" in location or "anywhere" in location:
                continue

        filtered.append(job)

    return filtered


# ── Scoring functions ────────────────────────────────────────

def score_job_match(job: dict[str, Any], profile: DeepProfile) -> dict[str, Any]:
    """Score a single job against a DeepProfile. Returns the job dict with `match_score` added."""
    weights = {
        "skill": 0.40,
        "location": 0.15,
        "salary": 0.15,
        "culture": 0.20,
        "trajectory": 0.10,
    }

    skill_score = _compute_skill_overlap(
        job.get("requirements", []),
        job.get("title", ""),
        job.get("description", ""),
        profile.competency_graph,
    )
    location_score = _compute_location_match(
        job.get("location", ""),
        profile.dealbreakers,
        profile.preferences,
    )
    salary_score = _compute_salary_match(
        job.get("salary_min"),
        job.get("salary_max"),
        profile.dealbreakers.min_salary,
        profile.dealbreakers.max_salary,
    )
    culture_score = _compute_culture_match(
        job.get("description", ""),
        profile.work_style,
    )
    trajectory_score = _compute_trajectory_match(
        job.get("title", ""),
        job.get("description", ""),
        profile.trajectory,
    )

    raw = (
        skill_score * weights["skill"]
        + location_score * weights["location"]
        + salary_score * weights["salary"]
        + culture_score * weights["culture"]
        + trajectory_score * weights["trajectory"]
    )

    job["match_score"] = round(raw * 100)
    job["match_breakdown"] = {
        "skill": round(skill_score * 100),
        "location": round(location_score * 100),
        "salary": round(salary_score * 100),
        "culture": round(culture_score * 100),
        "trajectory": round(trajectory_score * 100),
    }
    return job


# ── Dimension scorers ────────────────────────────────────────

_SPLIT_RE = re.compile(r"[,;/\s]+")


def _compute_skill_overlap(
    requirements: list[str],
    title: str,
    description: str,
    competency_graph: list[RichSkill],
) -> float:
    """0-1 score based on overlap between job requirements and user skills."""
    if not competency_graph:
        return 0.0

    user_skills = {s.skill.lower() for s in competency_graph}
    user_skill_confidence = {s.skill.lower(): s.confidence for s in competency_graph}

    # Build requirement set
    req_skills: set[str] = set()
    for req in requirements:
        for token in _SPLIT_RE.split(req.lower().strip()):
            cleaned = token.strip("()[]{}.,")
            if len(cleaned) > 1:
                req_skills.add(cleaned)

    # Also extract skills from title
    for token in _SPLIT_RE.split(title.lower()):
        cleaned = token.strip("()[]{}.,")
        if len(cleaned) > 2:
            req_skills.add(cleaned)

    if not req_skills:
        # Fallback: check description for skill mentions
        desc_lower = description.lower()
        matches = sum(
            1 for skill in user_skills if skill in desc_lower
        )
        if len(user_skills) == 0:
            return 0.0
        return min(matches / max(len(user_skills) * 0.3, 1), 1.0)

    # Compute weighted overlap
    matched_score = 0.0
    for skill in user_skills:
        if skill in req_skills:
            confidence = user_skill_confidence.get(skill, 0.5)
            matched_score += confidence

    if not req_skills:
        return 0.0
    return min(matched_score / len(req_skills), 1.0)


def _compute_location_match(
    job_location: str,
    dealbreakers: DealbreakerConfig,
    preferences: dict[str, Any],
) -> float:
    """0-1 score for location alignment."""
    job_loc_lower = job_location.lower()
    pref_location = (preferences.get("location") or "").lower()

    # Remote jobs match everyone
    if "remote" in job_loc_lower or "anywhere" in job_loc_lower:
        return 1.0

    if not pref_location:
        return 0.5  # No preference = neutral

    # Check if user's preferred location is in the job's location
    if pref_location in job_loc_lower or job_loc_lower in pref_location:
        return 1.0

    # Check dealbreaker locations
    for loc in dealbreakers.locations:
        if loc.lower() in job_loc_lower:
            return 0.8

    return 0.2  # Location mismatch


def _compute_salary_match(
    job_min: float | None,
    job_max: float | None,
    user_min: int | None,
    user_max: int | None,
) -> float:
    """0-1 score for salary overlap."""
    if job_min is None and job_max is None:
        return 0.5  # Unknown salary = neutral

    if user_min is None and user_max is None:
        return 0.5  # No preference = neutral

    j_min = job_min or 0
    j_max = job_max or j_min * 1.3
    u_min = user_min or 0
    u_max = user_max or u_min * 1.5

    # Perfect overlap
    if j_min >= u_min and j_max <= u_max:
        return 1.0
    if j_max >= u_min and j_min <= u_max:
        # Partial overlap
        overlap = min(j_max, u_max) - max(j_min, u_min)
        total_range = max(j_max, u_max) - min(j_min, u_min)
        if total_range == 0:
            return 1.0
        return max(overlap / total_range, 0.0)

    # No overlap
    if j_max < u_min:
        gap = u_min - j_max
        return max(0, 1.0 - gap / max(u_min, 1))
    return 0.3


_CULTURE_KEYWORDS: dict[str, list[str]] = {
    "async": ["async", "remote-first", "flexible hours", "distributed", "no meetings"],
    "sync": ["in-person", "collaborative", "team meetings", "stand-ups", "pair programming"],
    "fast": ["fast-paced", "move fast", "ship quickly", "rapid", "agile", "startup"],
    "steady": ["structured", "process-driven", "predictable", "sprint planning"],
    "methodical": ["quality-focused", "thorough", "engineering excellence", "best practices"],
    "early_startup": ["early-stage", "founding team", "startup", "seed", "pre-series"],
    "growth": ["series a", "series b", "scaling", "growth stage", "hypergrowth"],
    "enterprise": ["enterprise", "fortune 500", "large scale", "established"],
}


def _compute_culture_match(
    description: str,
    work_style: WorkStyleProfile | None,
) -> float:
    """0-1 score for culture/environment fit based on description keywords."""
    if not work_style:
        return 0.5

    desc_lower = description.lower()
    if not desc_lower:
        return 0.5

    positive_signals = 0
    total_checks = 0

    # Check communication style
    comm_keywords = _CULTURE_KEYWORDS.get(work_style.communication_style, [])
    if comm_keywords:
        total_checks += 1
        if any(kw in desc_lower for kw in comm_keywords):
            positive_signals += 1

    # Check pace preference
    pace_keywords = _CULTURE_KEYWORDS.get(work_style.pace_preference, [])
    if pace_keywords:
        total_checks += 1
        if any(kw in desc_lower for kw in pace_keywords):
            positive_signals += 1

    # Check company stage
    stage_keywords = _CULTURE_KEYWORDS.get(work_style.company_stage_preference, [])
    if stage_keywords:
        total_checks += 1
        if any(kw in desc_lower for kw in stage_keywords):
            positive_signals += 1

    if total_checks == 0:
        return 0.5

    return 0.3 + (positive_signals / total_checks) * 0.7


_TRAJECTORY_KEYWORDS: dict[str, list[str]] = {
    "ic": ["individual contributor", "staff engineer", "principal", "senior engineer", "architect"],
    "tech_lead": ["tech lead", "team lead", "lead engineer", "lead developer"],
    "manager": ["engineering manager", "em role", "people manager", "director of engineering"],
    "founder": ["cto", "co-founder", "founding engineer", "head of engineering", "vp engineering"],
}


def _compute_trajectory_match(
    title: str,
    description: str,
    trajectory: CareerTrajectory,
) -> float:
    """0-1 score for career trajectory alignment."""
    if trajectory == CareerTrajectory.OPEN:
        return 0.7  # Open = slightly positive for everything

    combined = f"{title} {description}".lower()
    keywords = _TRAJECTORY_KEYWORDS.get(trajectory.value, [])
    if not keywords:
        return 0.5

    matches = sum(1 for kw in keywords if kw in combined)
    if matches >= 2:
        return 1.0
    if matches == 1:
        return 0.8
    return 0.4
