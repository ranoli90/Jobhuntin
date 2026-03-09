"""Work style profile and behavioral calibration questions.

This module defines:
1. WorkStyleProfile - The user's behavioral preferences
2. BEHAVIORAL_QUESTIONS - Static questions that map to profile traits
3. Career trajectory options
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class CareerTrajectory(StrEnum):
    """User's desired career direction in 3 years."""

    IC = "ic"  # Individual contributor (deep expertise)
    TECH_LEAD = "tech_lead"  # Team influence
    MANAGER = "manager"  # People leadership
    FOUNDER = "founder"  # Company building
    OPEN = "open"  # Open to multiple paths


class WorkStyleProfile(BaseModel):
    """User's work style preferences extracted from behavioral questions."""

    autonomy_preference: Literal["high", "medium", "low"] = Field(
        default="medium", description="Preference for autonomous vs guided work"
    )
    learning_style: Literal["docs", "building", "pairing", "courses"] = Field(
        default="building", description="Preferred learning approach"
    )
    company_stage_preference: Literal[
        "early_startup", "growth", "enterprise", "flexible"
    ] = Field(default="flexible", description="Preferred company stage")
    communication_style: Literal["async", "sync", "mixed", "flexible"] = Field(
        default="mixed", description="Preferred communication style"
    )
    pace_preference: Literal["fast", "steady", "methodical", "flexible"] = Field(
        default="steady", description="Preferred work pace"
    )
    ownership_preference: Literal["solo", "team", "lead", "flexible"] = Field(
        default="team", description="Preferred ownership style"
    )
    career_trajectory: CareerTrajectory = Field(
        default=CareerTrajectory.OPEN, description="Career direction in 3 years"
    )


class BehavioralQuestion(BaseModel):
    """A single behavioral calibration question."""

    id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="The question text")
    options: list[str] = Field(..., description="Available answer options")
    maps_to: str = Field(..., description="Profile field this question maps to")
    value_map: dict[str, str] = Field(
        ..., description="Maps option text to profile value"
    )


BEHAVIORAL_QUESTIONS: list[dict] = [
    {
        "id": "blocked_dependency",
        "question": "Your team is blocked by a dependency. You:",
        "options": [
            "Build a workaround and move forward",
            "Escalate to get unblocked",
            "Document the blocker and wait",
            "Pick up other work while waiting",
        ],
        "maps_to": "autonomy_preference",
        "value_map": {
            "Build a workaround and move forward": "high",
            "Escalate to get unblocked": "medium",
            "Document the blocker and wait": "low",
            "Pick up other work while waiting": "medium",
        },
    },
    {
        "id": "learning_new_tech",
        "question": "Best way to learn a new technology:",
        "options": [
            "Read docs thoroughly first",
            "Build something small immediately",
            "Pair with someone experienced",
            "Take a structured course",
        ],
        "maps_to": "learning_style",
        "value_map": {
            "Read docs thoroughly first": "docs",
            "Build something small immediately": "building",
            "Pair with someone experienced": "pairing",
            "Take a structured course": "courses",
        },
    },
    {
        "id": "company_stage",
        "question": "Which environment do you thrive in?",
        "options": [
            "Early-stage startup (chaos, ownership)",
            "Growth-stage company (scaling, process)",
            "Enterprise (stability, specialization)",
            "No strong preference",
        ],
        "maps_to": "company_stage_preference",
        "value_map": {
            "Early-stage startup (chaos, ownership)": "early_startup",
            "Growth-stage company (scaling, process)": "growth",
            "Enterprise (stability, specialization)": "enterprise",
            "No strong preference": "flexible",
        },
    },
    {
        "id": "communication_style",
        "question": "Preferred way to collaborate:",
        "options": [
            "Async (Slack, docs, PRs)",
            "Real-time (meetings, pairing)",
            "Mixed depending on urgency",
            "Whatever the team prefers",
        ],
        "maps_to": "communication_style",
        "value_map": {
            "Async (Slack, docs, PRs)": "async",
            "Real-time (meetings, pairing)": "sync",
            "Mixed depending on urgency": "mixed",
            "Whatever the team prefers": "flexible",
        },
    },
    {
        "id": "work_pace",
        "question": "Ideal work pace:",
        "options": [
            "Fast (ship fast, iterate)",
            "Steady (predictable sprints)",
            "Methodical (thorough before shipping)",
            "Varies by project",
        ],
        "maps_to": "pace_preference",
        "value_map": {
            "Fast (ship fast, iterate)": "fast",
            "Steady (predictable sprints)": "steady",
            "Methodical (thorough before shipping)": "methodical",
            "Varies by project": "flexible",
        },
    },
    {
        "id": "ownership_style",
        "question": "How do you prefer to own work?",
        "options": [
            "Solo (end-to-end ownership)",
            "Team (collaborative ownership)",
            "Lead (guide others, delegate)",
            "Mix depending on scope",
        ],
        "maps_to": "ownership_preference",
        "value_map": {
            "Solo (end-to-end ownership)": "solo",
            "Team (collaborative ownership)": "team",
            "Lead (guide others, delegate)": "lead",
            "Mix depending on scope": "flexible",
        },
    },
]


TRAJECTORY_QUESTION: dict = {
    "id": "career_trajectory",
    "question": "In 3 years, what's your ideal role?",
    "options": [
        {"value": "ic", "label": "Individual contributor (deep expertise)"},
        {"value": "tech_lead", "label": "Tech lead (team influence)"},
        {"value": "manager", "label": "Engineering manager (people leadership)"},
        {"value": "founder", "label": "Founder/CTO (company building)"},
        {"value": "open", "label": "Open to multiple paths"},
    ],
    "maps_to": "career_trajectory",
}


def compute_work_style_from_answers(answers: dict[str, str]) -> WorkStyleProfile:
    """Compute a WorkStyleProfile from user's answers to behavioral questions.

    Args:
        answers: Dict mapping question_id to selected option text

    Returns:
        WorkStyleProfile with computed preferences

    """
    profile_data: dict[str, str] = {}

    for q in BEHAVIORAL_QUESTIONS:
        qid = q["id"]
        if qid in answers:
            selected = answers[qid]
            field_name = q["maps_to"]
            value_map = q["value_map"]
            if selected in value_map:
                profile_data[field_name] = value_map[selected]

    # Handle career trajectory separately
    if "career_trajectory" in answers:
        trajectory = answers["career_trajectory"]
        if trajectory in ["ic", "tech_lead", "manager", "founder", "open"]:
            profile_data["career_trajectory"] = trajectory

    # Type cast to satisfy mypy - the dict values are validated to match Literal types
    return WorkStyleProfile(**profile_data)  # type: ignore[arg-type]


def get_all_questions() -> list[dict]:
    """Get all behavioral questions including trajectory question."""
    questions = list(BEHAVIORAL_QUESTIONS)
    questions.append(TRAJECTORY_QUESTION)
    return questions
