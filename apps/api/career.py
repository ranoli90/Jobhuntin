"""Career Path API endpoints — career progression suggestions."""

from __future__ import annotations

import re
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.domain.career_path import CareerPathAnalyzer, SkillGap
from backend.domain.repositories import ProfileRepo
from shared.logging_config import get_logger

logger = get_logger("sorce.api.career")

router = APIRouter(prefix="/career", tags=["career"])

_analyzer = CareerPathAnalyzer()


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_user_id() -> str:
    raise NotImplementedError("User ID dependency not injected")


def _parse_years_from_duration(
    duration: str | None, start_date: str = "", end_date: str = ""
) -> int:
    """Parse years from duration string or date range. Returns 1 if unparseable."""
    if duration:
        m = re.search(r"(\d+)\s*(?:year|yr)", str(duration), re.I)
        if m:
            return max(1, int(m.group(1)))
        m = re.search(r"(\d+)\s*month", str(duration), re.I)
        if m:
            return max(1, int(m.group(1)) // 12) if int(m.group(1)) >= 12 else 1
    if start_date and end_date:
        try:
            from datetime import datetime

            start = datetime.strptime(str(start_date)[:4], "%Y") if len(str(start_date)) >= 4 else None
            end = datetime.strptime(str(end_date)[:4], "%Y") if len(str(end_date)) >= 4 else None
            if start and end:
                return max(1, end.year - start.year)
        except (ValueError, TypeError):
            pass
    return 1


def _extract_skills(profile_data: dict) -> list[str]:
    """Extract flat list of skills from profile_data."""
    skills_raw = profile_data.get("skills")
    if not skills_raw:
        return []
    if isinstance(skills_raw, list):
        return [
            s.get("skill", s) if isinstance(s, dict) else str(s)
            for s in skills_raw
            if s
        ]
    if isinstance(skills_raw, dict):
        technical = skills_raw.get("technical", [])
        soft = skills_raw.get("soft", [])
        out = []
        for s in technical + soft:
            if isinstance(s, dict):
                name = s.get("skill", "")
                if name:
                    out.append(name)
            elif isinstance(s, str) and s:
                out.append(s)
        return out
    return []


def _extract_work_history(profile_data: dict) -> list[dict[str, Any]]:
    """Extract work_history for career API from profile experience."""
    exp = profile_data.get("experience", [])
    if not exp:
        return []
    out = []
    for x in exp:
        if not isinstance(x, dict):
            continue
        title = x.get("title", "")
        company = x.get("company", "")
        duration = x.get("duration", "")
        start_date = x.get("start_date", "")
        end_date = x.get("end_date", "")
        years = _parse_years_from_duration(duration, start_date, end_date)
        out.append({"title": title or "Unknown", "years": years, "company": company})
    return out


def _build_trajectory_from_experience(profile_data: dict) -> list[dict[str, Any]]:
    """Build trajectory (year, level, company, description) from experience."""
    exp = profile_data.get("experience", [])
    if not exp:
        return []
    out = []
    for x in exp:
        if not isinstance(x, dict):
            continue
        title = x.get("title", "Unknown")
        company = x.get("company", "")
        start_date = x.get("start_date", "")
        year = int(str(start_date)[:4]) if start_date and len(str(start_date)) >= 4 else 0
        if not year and x.get("end_date"):
            year = (
                int(str(x["end_date"])[:4])
                if len(str(x.get("end_date", ""))) >= 4
                else 0
            )
        highlights = x.get("highlights", x.get("responsibilities", []))
        desc = highlights[0] if highlights else ""
        out.append(
            {"year": year or 2000, "level": title, "company": company, "description": desc}
        )
    return sorted(out, key=lambda e: e["year"])


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


@router.get("/analysis")
async def get_career_analysis(
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Fetch user profile and return combined career analysis for the Career Path page.

    Requires profile with experience (e.g. from resume upload). Returns 404 when
    no work history is available.
    """
    async with db.acquire() as conn:
        profile_data = await ProfileRepo.get_profile_data(conn, user_id)

    if not profile_data:
        raise HTTPException(
            status_code=404,
            detail="No profile found. Add your resume to see personalized career insights.",
        )

    work_history = _extract_work_history(profile_data)
    current_skills = _extract_skills(profile_data)

    if not work_history:
        raise HTTPException(
            status_code=404,
            detail="No work history found. Add your resume to unlock career path analysis.",
        )

    # Analyze trajectory
    trajectory_result = _analyzer.analyze_career_trajectory(
        work_history=work_history,
        current_skills=current_skills,
    )
    if "error" in trajectory_result:
        raise HTTPException(status_code=400, detail=trajectory_result["error"])

    current_level = trajectory_result.get("current_level", "unknown")
    possible_next_roles = trajectory_result.get("possible_next_roles", [])
    target_role = possible_next_roles[0] if possible_next_roles else current_level
    current_role = work_history[0].get("title", current_level) if work_history else current_level

    # Get recommendation
    recommendation = None
    if possible_next_roles:
        recommendation = _analyzer.get_career_path_recommendation(
            current_role=current_role,
            target_role=target_role,
            current_skills=current_skills,
            years_experience=trajectory_result.get("total_experience_years", 0),
        )

    # Build learning path from recommendation skill gaps
    learning_path = {"total_weeks": 0, "milestones": [], "recommended_pace": "part_time"}
    if recommendation and recommendation.skill_gaps:
        lp_result = _analyzer.get_learning_path(recommendation.skill_gaps)
        learning_path = {
            "total_weeks": lp_result.get("weeks", 0),
            "milestones": [
                {
                    "title": m.get("skill", "Skill"),
                    "description": f"Develop {m.get('skill', '')}",
                    "estimated_weeks": m.get("end_week", 0) - m.get("start_week", 0),
                    "resources": m.get("resources", []),
                }
                for m in lp_result.get("milestones", [])
            ],
            "recommended_pace": lp_result.get("recommended_pace", "part_time"),
        }

    trajectory = _build_trajectory_from_experience(profile_data)

    return {
        "current_level": trajectory_result.get("current_level", "unknown"),
        "current_track": trajectory_result.get("current_track", "unknown"),
        "total_experience_years": trajectory_result.get("total_experience_years", 0),
        "career_progression_score": trajectory_result.get("career_progression_score", 0.0),
        "possible_next_roles": possible_next_roles,
        "current_skills": current_skills,
        "trajectory": trajectory,
        "recommendations": (
            {
                "current_role": recommendation.current_role,
                "target_role": recommendation.target_role,
                "path_type": recommendation.path_type,
                "steps": recommendation.steps,
                "estimated_timeline_months": recommendation.estimated_timeline_months,
                "potential_salary_increase_pct": recommendation.potential_salary_increase_pct,
                "confidence": recommendation.confidence,
                "skill_gaps": [
                    {
                        "skill": g.skill,
                        "importance": g.importance,
                        "acquisition_method": g.acquisition_method,
                        "resources": g.resources,
                    }
                    for g in recommendation.skill_gaps
                ],
            }
            if recommendation
            else {
                "current_role": current_role,
                "target_role": target_role,
                "path_type": "exploration",
                "steps": [],
                "estimated_timeline_months": 18,
                "potential_salary_increase_pct": 0,
                "confidence": 0.5,
                "skill_gaps": [],
            }
        ),
        "learning_path": learning_path,
    }
