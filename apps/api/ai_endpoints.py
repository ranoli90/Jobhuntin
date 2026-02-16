"""
AI Suggestion API endpoints for smart onboarding.

These endpoints provide AI-powered suggestions for:
- Job roles based on resume analysis
- Salary ranges based on role, location, and skills
- Location recommendations based on skills and job market
- Job match scoring for personalized job feeds
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from shared.ai_validation import (
    validate_and_sanitize_ai_input,
)
from shared.config import get_settings
from shared.logging_config import get_logger

from backend.domain.repositories import CoverLetterRepo, JobMatchCacheRepo, ProfileRepo
from backend.llm import LLMClient
from backend.llm.contracts import (
    JobMatchScore_V1,
    LocationSuggestionResponse_V1,
    OnboardingQuestionsResponse_V1,
    RoleSuggestionResponse_V1,
    SalarySuggestionResponse_V1,
    build_job_match_prompt,
    build_location_suggestion_prompt,
    build_onboarding_questions_prompt,
    build_role_suggestion_prompt,
    build_salary_suggestion_prompt,
)

logger = get_logger("sorce.api.ai")

# ---------------------------------------------------------------------------
# Singleton LLM client — avoids per-request instantiation overhead
# ---------------------------------------------------------------------------
_llm_client: LLMClient | None = None


def _get_llm_client() -> LLMClient:
    """Get or create the singleton LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class RoleSuggestionRequest(BaseModel):
    """Request for AI-powered role suggestions."""
    resume_text: str = Field(..., min_length=50, max_length=10000)
    skills: list[str] = Field(default_factory=list, max_items=50)
    experience_years: int = Field(default=0, ge=0, le=50)
    education_level: str = Field(default="bachelor", regex="^(high_school|bachelor|master|phd|other)$")


class SalarySuggestionRequest(BaseModel):
    """Request for AI-powered salary suggestions."""
    role: str = Field(..., min_length=2, max_length=100)
    location: str = Field(..., min_length=2, max_length=100)
    skills: list[str] = Field(default_factory=list, max_items=50)
    experience_years: int = Field(default=0, ge=0, le=50)
    education_level: str = Field(default="bachelor", regex="^(high_school|bachelor|master|phd|other)$")


class LocationSuggestionRequest(BaseModel):
    """Request for AI-powered location suggestions."""
    skills: list[str] = Field(..., min_items=1, max_items=50)
    role: str = Field(..., min_length=2, max_length=100)
    experience_years: int = Field(default=0, ge=0, le=50)
    remote_preference: bool = Field(default=True)


class JobMatchRequest(BaseModel):
    """Request for AI-powered job matching."""
    profile_id: str = Field(..., regex="^[a-zA-Z0-9_-]{1,50}$")
    job_ids: list[str] = Field(..., min_items=1, max_items=100)
    limit: int = Field(default=10, ge=1, le=50)


class OnboardingQuestionsRequest(BaseModel):
    """Request for AI-powered onboarding questions."""
    resume_text: str = Field(..., min_length=50, max_length=10000)
    current_step: str = Field(default="initial", regex="^(initial|skills|experience|preferences)$")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/roles/suggest", response_model=RoleSuggestionResponse_V1)
async def suggest_roles(
    request: RoleSuggestionRequest,
    db: asyncpg.Connection = Depends(get_db_connection),
) -> RoleSuggestionResponse_V1:
    """Get AI-powered role suggestions based on resume analysis."""
    try:
        # Validate and sanitize input
        sanitized_text = validate_and_sanitize_ai_input(request.resume_text)
        
        # Get LLM client
        llm = _get_llm_client()
        
        # Build prompt
        prompt = build_role_suggestion_prompt(
            resume_text=sanitized_text,
            skills=request.skills,
            experience_years=request.experience_years,
            education_level=request.education_level,
        )
        
        # Get AI response
        response = await llm.complete(prompt)
        
        # Parse and validate response
        result = RoleSuggestionResponse_V1.parse_raw(response)
        
        # Log analytics
        await emit_analytics_event(
            "ai_role_suggestion_completed",
            {
                "skills_count": len(request.skills),
                "experience_years": request.experience_years,
                "education_level": request.education_level,
                "suggestions_count": len(result.suggestions),
            },
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in role suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate role suggestions")


@router.post("/salary/suggest", response_model=SalarySuggestionResponse_V1)
async def suggest_salary(
    request: SalarySuggestionRequest,
    db: asyncpg.Connection = Depends(get_db_connection),
) -> SalarySuggestionResponse_V1:
    """Get AI-powered salary suggestions."""
    try:
        # Validate and sanitize input
        sanitized_role = validate_and_sanitize_ai_input(request.role)
        sanitized_location = validate_and_sanitize_ai_input(request.location)
        
        # Get LLM client
        llm = _get_llm_client()
        
        # Build prompt
        prompt = build_salary_suggestion_prompt(
            role=sanitized_role,
            location=sanitized_location,
            skills=request.skills,
            experience_years=request.experience_years,
            education_level=request.education_level,
        )
        
        # Get AI response
        response = await llm.complete(prompt)
        
        # Parse and validate response
        result = SalarySuggestionResponse_V1.parse_raw(response)
        
        # Log analytics
        await emit_analytics_event(
            "ai_salary_suggestion_completed",
            {
                "role": sanitized_role,
                "location": sanitized_location,
                "skills_count": len(request.skills),
                "experience_years": request.experience_years,
            },
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in salary suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate salary suggestions")


@router.post("/locations/suggest", response_model=LocationSuggestionResponse_V1)
async def suggest_locations(
    request: LocationSuggestionRequest,
    db: asyncpg.Connection = Depends(get_db_connection),
) -> LocationSuggestionResponse_V1:
    """Get AI-powered location suggestions."""
    try:
        # Validate and sanitize input
        sanitized_skills = [validate_and_sanitize_ai_input(skill) for skill in request.skills]
        sanitized_role = validate_and_sanitize_ai_input(request.role)
        
        # Get LLM client
        llm = _get_llm_client()
        
        # Build prompt
        prompt = build_location_suggestion_prompt(
            skills=sanitized_skills,
            role=sanitized_role,
            experience_years=request.experience_years,
            remote_preference=request.remote_preference,
        )
        
        # Get AI response
        response = await llm.complete(prompt)
        
        # Parse and validate response
        result = LocationSuggestionResponse_V1.parse_raw(response)
        
        # Log analytics
        await emit_analytics_event(
            "ai_location_suggestion_completed",
            {
                "skills_count": len(request.skills),
                "role": sanitized_role,
                "experience_years": request.experience_years,
                "remote_preference": request.remote_preference,
            },
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in location suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate location suggestions")


@router.post("/jobs/match", response_model=JobMatchScore_V1)
async def match_jobs(
    request: JobMatchRequest,
    db: asyncpg.Connection = Depends(get_db_connection),
) -> JobMatchScore_V1:
    """Get AI-powered job matching scores."""
    try:
        # Validate profile exists
        profile_repo = ProfileRepo(db)
        profile = await profile_repo.get_by_id(request.profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Check cache first
        cache_repo = JobMatchCacheRepo(db)
        cache_key = _generate_cache_key(request.profile_id, request.job_ids)
        cached_result = await cache_repo.get(cache_key)
        if cached_result:
            return JobMatchScore_V1.parse_raw(cached_result)
        
        # Get LLM client
        llm = _get_llm_client()
        
        # Build prompt for each job
        matches = []
        for job_id in request.job_ids[:request.limit]:
            try:
                # Get job details (implement this based on your job repository)
                job_details = await _get_job_details(db, job_id)
                if not job_details:
                    continue
                
                prompt = build_job_match_prompt(
                    profile=profile,
                    job=job_details,
                )
                
                # Get AI response
                response = await llm.complete(prompt)
                match_score = JobMatchScore_V1.parse_raw(response)
                matches.append(match_score)
                
            except Exception as e:
                logger.warning(f"Error processing job {job_id}: {e}")
                continue
        
        # Cache results
        result = JobMatchScore_V1(matches=matches)
        await cache_repo.set(cache_key, result.json(), ttl=3600)  # 1 hour cache
        
        # Log analytics
        await emit_analytics_event(
            "ai_job_matching_completed",
            {
                "profile_id": request.profile_id,
                "jobs_processed": len(matches),
                "cache_hit": False,
            },
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in job matching: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate job matches")


@router.post("/onboarding/questions", response_model=OnboardingQuestionsResponse_V1)
async def generate_onboarding_questions(
    request: OnboardingQuestionsRequest,
    db: asyncpg.Connection = Depends(get_db_connection),
) -> OnboardingQuestionsResponse_V1:
    """Get AI-powered onboarding questions."""
    try:
        # Validate and sanitize input
        sanitized_text = validate_and_sanitize_ai_input(request.resume_text)
        sanitized_step = validate_and_sanitize_ai_input(request.current_step)
        
        # Get LLM client
        llm = _get_llm_client()
        
        # Build prompt
        prompt = build_onboarding_questions_prompt(
            resume_text=sanitized_text,
            current_step=sanitized_step,
        )
        
        # Get AI response
        response = await llm.complete(prompt)
        
        # Parse and validate response
        result = OnboardingQuestionsResponse_V1.parse_raw(response)
        
        # Log analytics
        await emit_analytics_event(
            "ai_onboarding_questions_completed",
            {
                "current_step": request.current_step,
                "questions_count": len(result.questions),
            },
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in onboarding questions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate onboarding questions")


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _generate_cache_key(profile_id: str, job_ids: list[str]) -> str:
    """Generate a cache key for job matching results."""
    job_ids_str = ",".join(sorted(job_ids))
    content = f"{profile_id}:{job_ids_str}"
    return hashlib.md5(content.encode()).hexdigest()


async def _get_job_details(db: asyncpg.Connection, job_id: str) -> dict[str, Any]:
    """Get job details for matching."""
    # This should be implemented based on your job repository
    # For now, return a placeholder
    return {
        "id": job_id,
        "title": "Software Engineer",
        "description": "Develop and maintain software applications",
        "requirements": ["Python", "JavaScript", "SQL"],
        "location": "Remote",
        "salary_range": "$80,000 - $120,000",
    }


async def get_db_connection() -> asyncpg.Connection:
    """Get database connection."""
    from shared.db import get_db_pool
    pool = get_db_pool()
    return await pool.acquire()


async def emit_analytics_event(event_name: str, data: dict[str, Any]) -> None:
    """Emit analytics event."""
    try:
        from backend.domain.analytics_events import emit_analytics_event
        await emit_analytics_event(event_name, data)
    except Exception as e:
        logger.warning(f"Failed to emit analytics event {event_name}: {e}")
