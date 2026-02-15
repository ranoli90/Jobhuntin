"""
Job signal extraction for work style and growth matching.

This module extracts work style signals from job postings to enable
two-way compatibility matching between candidates and jobs.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .work_style import WorkStyleProfile, CareerTrajectory


class CompanyStage(str, Enum):
    """Company stage classification."""

    EARLY_STARTUP = "early_startup"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class WorkPace(str, Enum):
    """Work pace classification."""

    FAST = "fast"
    STEADY = "steady"
    METHODICAL = "methodical"


class AutonomyLevel(str, Enum):
    """Autonomy level classification."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GrowthPotential(str, Enum):
    """Growth potential classification."""

    IC_PATH = "ic_path"
    LEAD_PATH = "lead_path"
    MANAGER_PATH = "manager_path"
    LIMITED = "limited"


class TeamSize(str, Enum):
    """Team size classification."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class RemoteCulture(str, Enum):
    """Remote work culture classification."""

    ASYNC_FIRST = "async_first"
    HYBRID = "hybrid"
    ONSITE_CULTURE = "onsite_culture"


class JobSignals(BaseModel):
    """Extracted work style and growth signals from a job posting."""

    company_stage: CompanyStage | None = Field(
        default=None, description="Inferred company stage"
    )
    pace: WorkPace | None = Field(default=None, description="Inferred work pace")
    autonomy_level: AutonomyLevel | None = Field(
        default=None, description="Expected autonomy level"
    )
    growth_potential: GrowthPotential | None = Field(
        default=None, description="Career growth potential"
    )
    team_size: TeamSize | None = Field(default=None, description="Team size")
    remote_culture: RemoteCulture | None = Field(
        default=None, description="Remote work culture"
    )
    signals_detected: list[str] = Field(
        default_factory=list, description="Phrases that informed the classification"
    )


class JobSignalsResponse_V1(BaseModel):
    """LLM response for job signal extraction."""

    company_stage: str = Field(
        default="", description="early_startup, growth, or enterprise"
    )
    pace: str = Field(default="", description="fast, steady, or methodical")
    autonomy_level: str = Field(default="", description="high, medium, or low")
    growth_potential: str = Field(
        default="", description="ic_path, lead_path, manager_path, or limited"
    )
    team_size: str | None = Field(default=None, description="small, medium, or large")
    remote_culture: str | None = Field(
        default=None, description="async_first, hybrid, or onsite_culture"
    )
    signals_detected: list[str] = Field(
        default_factory=list, description="Key phrases found"
    )


JOB_SIGNALS_PROMPT = """You are a job posting analyzer. Extract work style and growth signals from this job posting.

## Job Title
{job_title}

## Company
{company}

## Job Description
{job_description}

## Instructions
Analyze the job posting and classify it on these dimensions. Return ONLY a JSON object:

{{
    "company_stage": "early_startup" | "growth" | "enterprise",
    "pace": "fast" | "steady" | "methodical",
    "autonomy_level": "high" | "medium" | "low",
    "growth_potential": "ic_path" | "lead_path" | "manager_path" | "limited",
    "team_size": "small" | "medium" | "large" | null,
    "remote_culture": "async_first" | "hybrid" | "onsite_culture" | null,
    "signals_detected": ["list of phrases that informed each decision"]
}}

## Classification Rules:

**company_stage**:
- "early_startup": Series A or earlier, "fast-paced", "wear many hats", "seed", "founding engineer"
- "growth": Series B+, "scaling", "growing team", "established product"
- "enterprise": Public company, Fortune 500, "large organization", structured processes

**pace**:
- "fast": "move fast", "ship quickly", "rapid iteration", "fast-paced environment"
- "steady": "sprint", "predictable", "work-life balance", sustainable pace"
- "methodical": "thorough", "quality-focused", "meticulous", "careful"

**autonomy_level**:
- "high": "self-directed", "own your projects", "minimal supervision", "entrepreneurial"
- "medium": "collaborative", "team-oriented", "regular check-ins"
- "low": "structured", "guided", "mentorship available", "junior-friendly"

**growth_potential**:
- "ic_path": "grow as engineer", "technical ladder", "staff engineer path"
- "lead_path": "tech lead", "lead engineer", "architect role"
- "manager_path": "management track", "people manager", "engineering manager"
- "limited": Fixed term, contract, or limited advancement mentioned

**team_size**:
- "small": 1-5 engineers, "small team", "close-knit"
- "medium": 6-20 engineers, "growing team"
- "large": 20+ engineers, "large engineering org"

**remote_culture**:
- "async_first": "async", "written communication", "distributed team", "flexible hours"
- "hybrid": "hybrid", "office X days", "in-person collaboration"
- "onsite_culture": "on-site", "in office", "collaborative workspace"

Include 3-8 phrases in signals_detected that informed your classifications.
"""


def build_job_signals_prompt(job_title: str, company: str, job_description: str) -> str:
    """Build prompt for job signal extraction."""
    return JOB_SIGNALS_PROMPT.format(
        job_title=job_title,
        company=company,
        job_description=job_description[:6000]
        if len(job_description) > 6000
        else job_description,
    )


def parse_job_signals_response(response: JobSignalsResponse_V1) -> JobSignals:
    """Parse LLM response into JobSignals model."""
    signals = JobSignals(signals_detected=response.signals_detected)

    if response.company_stage in ["early_startup", "growth", "enterprise"]:
        signals.company_stage = CompanyStage(response.company_stage)

    if response.pace in ["fast", "steady", "methodical"]:
        signals.pace = WorkPace(response.pace)

    if response.autonomy_level in ["high", "medium", "low"]:
        signals.autonomy_level = AutonomyLevel(response.autonomy_level)

    if response.growth_potential in ["ic_path", "lead_path", "manager_path", "limited"]:
        signals.growth_potential = GrowthPotential(response.growth_potential)

    if response.team_size in ["small", "medium", "large"]:
        signals.team_size = TeamSize(response.team_size)

    if response.remote_culture in ["async_first", "hybrid", "onsite_culture"]:
        signals.remote_culture = RemoteCulture(response.remote_culture)

    return signals


def compute_work_style_fit(
    work_style: dict[str, str], job_signals: JobSignals
) -> float:
    """
    Compute compatibility score between candidate work style and job signals.

    Args:
        work_style: Dict with keys like autonomy_preference, pace_preference, etc.
        job_signals: JobSignals model

    Returns a score from 0.0 to 1.0.
    """
    scores: list[float] = []

    # Company stage match
    pref = work_style.get("company_stage_preference", "flexible")
    if pref != "flexible" and job_signals.company_stage:
        stage_map = {
            "early_startup": CompanyStage.EARLY_STARTUP,
            "growth": CompanyStage.GROWTH,
            "enterprise": CompanyStage.ENTERPRISE,
        }
        expected = stage_map.get(pref)
        scores.append(1.0 if expected == job_signals.company_stage else 0.5)

    # Pace match
    pace_pref = work_style.get("pace_preference", "flexible")
    if pace_pref != "flexible" and job_signals.pace:
        pace_map = {
            "fast": WorkPace.FAST,
            "steady": WorkPace.STEADY,
            "methodical": WorkPace.METHODICAL,
        }
        expected = pace_map.get(pace_pref)
        scores.append(1.0 if expected == job_signals.pace else 0.6)

    # Autonomy match
    auto_pref = work_style.get("autonomy_preference", "medium")
    if auto_pref != "medium" and job_signals.autonomy_level:
        autonomy_map = {
            "high": AutonomyLevel.HIGH,
            "medium": AutonomyLevel.MEDIUM,
            "low": AutonomyLevel.LOW,
        }
        expected = autonomy_map.get(auto_pref)
        scores.append(1.0 if expected == job_signals.autonomy_level else 0.5)

    # Communication style match (if remote culture detected)
    comm_pref = work_style.get("communication_style", "flexible")
    if comm_pref != "flexible" and job_signals.remote_culture:
        if (
            comm_pref == "async"
            and job_signals.remote_culture == RemoteCulture.ASYNC_FIRST
        ):
            scores.append(1.0)
        elif (
            comm_pref == "sync"
            and job_signals.remote_culture == RemoteCulture.ONSITE_CULTURE
        ):
            scores.append(1.0)
        elif (
            comm_pref == "mixed" and job_signals.remote_culture == RemoteCulture.HYBRID
        ):
            scores.append(1.0)
        else:
            scores.append(0.6)

    return sum(scores) / len(scores) if scores else 0.7


def compute_trajectory_alignment(trajectory: str, job_signals: JobSignals) -> float:
    """
    Compute alignment between candidate's career trajectory and job's growth potential.

    Args:
        trajectory: One of "ic", "tech_lead", "manager", "founder", "open"
        job_signals: JobSignals model

    Returns a score from 0.0 to 1.0.
    """
    if trajectory == "open":
        return 0.7  # Open to anything is moderate fit

    if not job_signals.growth_potential:
        return 0.6  # Unknown growth is slightly below average

    # Perfect matches
    perfect_matches = {
        ("ic", GrowthPotential.IC_PATH),
        ("tech_lead", GrowthPotential.LEAD_PATH),
        ("manager", GrowthPotential.MANAGER_PATH),
    }

    if (trajectory, job_signals.growth_potential) in perfect_matches:
        return 1.0

    # Good matches (adjacent paths)
    good_matches = {
        ("ic", GrowthPotential.LEAD_PATH),
        ("tech_lead", GrowthPotential.IC_PATH),
        ("tech_lead", GrowthPotential.MANAGER_PATH),
        ("manager", GrowthPotential.LEAD_PATH),
    }

    if (trajectory, job_signals.growth_potential) in good_matches:
        return 0.7

    # Limited growth is bad for ambitious trajectories
    if job_signals.growth_potential == GrowthPotential.LIMITED:
        if trajectory in ["tech_lead", "manager", "founder"]:
            return 0.3
        return 0.5

    return 0.5
