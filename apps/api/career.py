"""
Career Path API endpoints — career progression suggestions.
"""

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.domain.career_path import CareerPathAnalyzer, SkillGap
from shared.logging_config import get_logger

logger = get_logger("sorce.api.career")

router = APIRouter(prefix="/career", tags=["career"])

_analyzer = CareerPathAnalyzer()


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_user_id() -> str:
    raise NotImplementedError("User ID dependency not injected")


class AnalyzeTrajectoryRequest(BaseModel):
    work_history: list[dict[str, Any]]
    current_skills: list[str]


class AnalyzeTrajectoryResponse(BaseModel):
    total_experience_years: int
    current_level: str
    current_track: str
    possible_next_roles: list[str]
    career_progression_score: float


class GetRecommendationRequest(BaseModel):
    current_role: str
    target_role: str
    current_skills: list[str]
    years_experience: int = 0


class SkillGapResponse(BaseModel):
    skill: str
    importance: str
    acquisition_method: str
    estimated_time_weeks: int
    resources: list[str]


class RecommendationResponse(BaseModel):
    current_role: str
    target_role: str
    path_type: str
    steps: list[dict[str, Any]]
    skill_gaps: list[SkillGapResponse]
    estimated_timeline_months: int
    potential_salary_increase_pct: float
    confidence: float


class NextMovesResponse(BaseModel):
    moves: list[dict[str, Any]]


class LearningPathResponse(BaseModel):
    total_weeks: int
    milestones: list[dict[str, Any]]
    recommended_pace: str


@router.post("/analyze", response_model=AnalyzeTrajectoryResponse)
async def analyze_career_trajectory(
    body: AnalyzeTrajectoryRequest,
) -> AnalyzeTrajectoryResponse:
    result = _analyzer.analyze_career_trajectory(
        work_history=body.work_history,
        current_skills=body.current_skills,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return AnalyzeTrajectoryResponse(
        total_experience_years=result.get("total_experience_years", 0),
        current_level=result.get("current_level", "unknown"),
        current_track=result.get("current_track", "unknown"),
        possible_next_roles=result.get("possible_next_roles", []),
        career_progression_score=result.get("career_progression_score", 0.0),
    )


@router.post("/recommendation", response_model=RecommendationResponse)
async def get_career_path_recommendation(
    body: GetRecommendationRequest,
) -> RecommendationResponse:
    recommendation = _analyzer.get_career_path_recommendation(
        current_role=body.current_role,
        target_role=body.target_role,
        current_skills=body.current_skills,
        years_experience=body.years_experience,
    )

    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail="Could not generate recommendation for this career path",
        )

    return RecommendationResponse(
        current_role=recommendation.current_role,
        target_role=recommendation.target_role,
        path_type=recommendation.path_type,
        steps=recommendation.steps,
        skill_gaps=[
            SkillGapResponse(
                skill=gap.skill,
                importance=gap.importance,
                acquisition_method=gap.acquisition_method,
                estimated_time_weeks=gap.estimated_time_weeks,
                resources=gap.resources,
            )
            for gap in recommendation.skill_gaps
        ],
        estimated_timeline_months=recommendation.estimated_timeline_months,
        potential_salary_increase_pct=recommendation.potential_salary_increase_pct,
        confidence=recommendation.confidence,
    )


@router.post("/next-moves", response_model=NextMovesResponse)
async def suggest_next_career_moves(
    body: AnalyzeTrajectoryRequest,
) -> NextMovesResponse:
    if not body.work_history:
        raise HTTPException(status_code=400, detail="Work history is required")

    current_title = body.work_history[0].get("title", "") if body.work_history else ""

    moves = _analyzer.suggest_next_career_moves(
        current_role=current_title,
        current_skills=body.current_skills,
    )

    return NextMovesResponse(moves=moves)


@router.post("/skill-gaps")
async def identify_skill_gaps(
    body: GetRecommendationRequest,
) -> list[SkillGapResponse]:
    gaps = _analyzer.identify_skill_gaps(
        current_role=body.current_role,
        target_role=body.target_role,
        current_skills=body.current_skills,
    )

    return [
        SkillGapResponse(
            skill=gap.skill,
            importance=gap.importance,
            acquisition_method=gap.acquisition_method,
            estimated_time_weeks=gap.estimated_time_weeks,
            resources=gap.resources,
        )
        for gap in gaps
    ]


@router.post("/learning-path", response_model=LearningPathResponse)
async def get_learning_path(
    body: list[SkillGapResponse],
) -> LearningPathResponse:
    skill_gaps = [
        SkillGap(
            skill=g.skill,
            importance=g.importance,
            acquisition_method=g.acquisition_method,
            estimated_time_weeks=g.estimated_time_weeks,
            resources=g.resources,
        )
        for g in body
    ]

    result = _analyzer.get_learning_path(skill_gaps)

    return LearningPathResponse(
        total_weeks=result.get("weeks", 0),
        milestones=result.get("milestones", []),
        recommended_pace=result.get("recommended_pace", "part_time"),
    )


@router.get("/roles")
async def list_career_roles() -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "title": role.title,
            "level": role.level.value,
            "track": role.track.value,
            "typical_years_experience": role.typical_years_experience,
            "typical_skills": role.typical_skills,
            "salary_range_usd": role.salary_range_usd,
            "growth_outlook": role.growth_outlook,
        }
        for key, role in _analyzer.roles.items()
    ]


@router.get("/transitions")
async def list_career_transitions() -> list[dict[str, Any]]:
    return [
        {
            "from_role": t.from_role,
            "to_role": t.to_role,
            "difficulty": t.difficulty,
            "skills_to_acquire": t.skills_to_acquire,
            "skills_transferable": t.skills_transferable,
            "typical_timeline_months": t.typical_timeline_months,
            "salary_change_pct": t.salary_change_pct,
        }
        for t in _analyzer.transitions
    ]
