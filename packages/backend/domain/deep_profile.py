"""Deep Profile Aggregation.

This module aggregates all profile signals into a unified "digital twin"
for matching: skills, work style, trajectory, preferences, and completeness.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .work_style import CareerTrajectory, WorkStyleProfile


class RichSkill(BaseModel):
    """A skill with confidence, context, and metadata."""

    skill: str
    confidence: float = 0.5
    years_actual: float | None = None
    context: str = ""
    last_used: str | None = None
    verified: bool = False
    related_to: list[str] = Field(default_factory=list)
    source: str = "resume"
    project_count: int = 0


class DealbreakerConfig(BaseModel):
    """Dealbreaker filters for job matching."""

    min_salary: int | None = None
    max_salary: int | None = None
    locations: list[str] = Field(default_factory=list)
    remote_only: bool = False
    onsite_only: bool = False
    visa_sponsorship_required: bool = False
    excluded_companies: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)


class DeepProfile(BaseModel):
    """Complete aggregated user profile for matching.

    This is the "digital twin" - all signals needed to compute
    a comprehensive match score with any job.
    """

    user_id: str

    # Core competency data
    competency_graph: list[RichSkill] = Field(
        default_factory=list, description="Skills with confidence and context"
    )

    # Work style preferences
    work_style: WorkStyleProfile | None = Field(
        default=None, description="Behavioral profile from calibration"
    )

    # Career direction
    trajectory: CareerTrajectory = Field(
        default=CareerTrajectory.OPEN, description="Career direction in 3 years"
    )

    # Dealbreakers and preferences
    dealbreakers: DealbreakerConfig = Field(
        default_factory=DealbreakerConfig, description="Hard filters for job matching"
    )

    preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="Job preferences (location, salary, remote, etc.)",
    )

    # Career goals from onboarding
    career_goals: dict[str, Any] = Field(
        default_factory=dict,
        description="Career goals (experience_level, urgency, primary_goal, why_leaving)",
    )
    industry_preferences: list[str] = Field(
        default_factory=list, description="Preferred industries"
    )
    company_size_preference: str = Field(
        default="any", description="Preferred company size"
    )
    notice_period: str | None = Field(
        default=None, description="Notice period before starting"
    )

    # Metadata
    completeness_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Profile completeness percentage"
    )
    computed_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this profile was computed"
    )

    # Source data references
    resume_url: str | None = None
    has_resume: bool = False
    has_verified_email: bool = False


def calculate_completeness(profile: DeepProfile) -> float:
    """Calculate profile completeness percentage.

    Weights:
    - Resume uploaded: 20%
    - Contact verified: 15%
    - Preferences set: 15%
    - Skills reviewed: 20%
    - Work style calibrated: 20%
    - Career trajectory set: 10%
    """
    score = 0.0

    # Resume uploaded (20%)
    if profile.has_resume or profile.resume_url:
        score += 20

    # Contact verified (15%)
    if profile.has_verified_email:
        score += 15

    # Preferences set (15%)
    if profile.preferences:
        if profile.preferences.get("location"):
            score += 5
        if profile.preferences.get("role_type"):
            score += 5
        if profile.preferences.get("salary_min") or profile.preferences.get(
            "salary_max"
        ):
            score += 5

    # Skills reviewed (20%)
    if len(profile.competency_graph) >= 3:
        # Check if skills have been reviewed (not just extracted)
        reviewed_skills = [
            s for s in profile.competency_graph if s.source == "manual" or s.verified
        ]
        if len(reviewed_skills) >= 1:
            score += 20
        elif len(profile.competency_graph) >= 5:
            score += 15  # Give partial credit for many skills
        else:
            score += 10
    elif len(profile.competency_graph) >= 1:
        score += 10

    # Work style calibrated (20%)
    if profile.work_style:
        score += 20

    # Career trajectory set (10%)
    if profile.trajectory != CareerTrajectory.OPEN:
        score += 10

    return min(score, 100.0)


def get_top_skills(
    profile: DeepProfile, min_confidence: float = 0.5, limit: int = 10
) -> list[RichSkill]:
    """Get top skills by confidence score."""
    skills = [s for s in profile.competency_graph if s.confidence >= min_confidence]
    return sorted(skills, key=lambda s: s.confidence, reverse=True)[:limit]


def get_skill_confidence_summary(profile: DeepProfile) -> dict[str, int]:
    """Get count of skills by confidence level."""
    high = sum(1 for s in profile.competency_graph if s.confidence >= 0.8)
    medium = sum(1 for s in profile.competency_graph if 0.5 <= s.confidence < 0.8)
    low = sum(1 for s in profile.competency_graph if s.confidence < 0.5)

    return {
        "high": high,
        "medium": medium,
        "low": low,
        "total": len(profile.competency_graph),
    }


def profile_to_dict(profile: DeepProfile) -> dict[str, Any]:
    """Convert DeepProfile to dictionary for storage/caching."""
    return {
        "user_id": profile.user_id,
        "competency_graph": [s.model_dump() for s in profile.competency_graph],
        "work_style": profile.work_style.model_dump() if profile.work_style else None,
        "trajectory": profile.trajectory.value,
        "dealbreakers": profile.dealbreakers.model_dump(),
        "preferences": profile.preferences,
        "career_goals": profile.career_goals,
        "industry_preferences": profile.industry_preferences,
        "company_size_preference": profile.company_size_preference,
        "notice_period": profile.notice_period,
        "completeness_score": profile.completeness_score,
        "computed_at": profile.computed_at.isoformat(),
        "resume_url": profile.resume_url,
        "has_resume": profile.has_resume,
        "has_verified_email": profile.has_verified_email,
    }


def dict_to_profile(data: dict[str, Any]) -> DeepProfile:
    """Convert dictionary back to DeepProfile."""
    competency_graph = [RichSkill(**s) for s in data.get("competency_graph", [])]

    work_style = None
    if data.get("work_style"):
        work_style = WorkStyleProfile(**data["work_style"])

    trajectory = CareerTrajectory(data.get("trajectory", "open"))

    dealbreakers = DealbreakerConfig(**data.get("dealbreakers", {}))

    computed_at = data.get("computed_at")
    if isinstance(computed_at, str):
        computed_at = datetime.fromisoformat(computed_at)
    else:
        computed_at = datetime.utcnow()

    return DeepProfile(
        user_id=data["user_id"],
        competency_graph=competency_graph,
        work_style=work_style,
        trajectory=trajectory,
        dealbreakers=dealbreakers,
        preferences=data.get("preferences", {}),
        career_goals=data.get("career_goals", {}),
        industry_preferences=data.get("industry_preferences", []),
        company_size_preference=data.get("company_size_preference", "any"),
        notice_period=data.get("notice_period"),
        completeness_score=data.get("completeness_score", 0),
        computed_at=computed_at,
        resume_url=data.get("resume_url"),
        has_resume=data.get("has_resume", False),
        has_verified_email=data.get("has_verified_email", False),
    )
