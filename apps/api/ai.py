"""
AI Suggestion API endpoints for smart onboarding.

These endpoints provide AI-powered suggestions for:
- Job roles based on resume analysis
- Salary ranges based on role, location, and skills
- Location recommendations based on skills and job market
- Job match scoring for personalized job feeds
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.llm import LLMClient
from backend.llm.contracts import (
    RoleSuggestionResponse_V1,
    SalarySuggestionResponse_V1,
    LocationSuggestionResponse_V1,
    JobMatchScore_V1,
    build_role_suggestion_prompt,
    build_salary_suggestion_prompt,
    build_location_suggestion_prompt,
    build_job_match_prompt,
)
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.api.ai")

router = APIRouter(prefix="/ai", tags=["AI Suggestions"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class RoleSuggestionRequest(BaseModel):
    """Request body for role suggestions."""
    profile: dict = Field(..., description="Parsed resume profile data")


class SalarySuggestionRequest(BaseModel):
    """Request body for salary suggestions."""
    profile: dict = Field(..., description="Parsed resume profile data")
    target_role: str = Field(..., description="Target job role")
    location: str = Field(default="Remote", description="Preferred work location")


class LocationSuggestionRequest(BaseModel):
    """Request body for location suggestions."""
    profile: dict = Field(..., description="Parsed resume profile data")
    current_location: str = Field(default="", description="Current location if any")


class JobMatchRequest(BaseModel):
    """Request body for job match scoring."""
    profile: dict = Field(..., description="Parsed resume profile data")
    job: dict = Field(..., description="Job posting data")


class BatchJobMatchRequest(BaseModel):
    """Request body for batch job match scoring."""
    profile: dict = Field(..., description="Parsed resume profile data")
    jobs: list[dict] = Field(..., description="List of job postings to score")


class BatchJobMatchResponse(BaseModel):
    """Response for batch job match scoring."""
    matches: list[JobMatchScore_V1] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/suggest-roles", response_model=RoleSuggestionResponse_V1)
async def suggest_roles(request: RoleSuggestionRequest) -> RoleSuggestionResponse_V1:
    """
    Get AI-suggested job roles based on parsed resume profile.
    
    This analyzes the candidate's experience, skills, and career progression
    to suggest the most suitable job titles and experience level.
    """
    settings = get_settings()
    client = LLMClient(settings)
    
    try:
        prompt = build_role_suggestion_prompt(request.profile)
        result = await client.call(
            prompt=prompt,
            response_format=RoleSuggestionResponse_V1,
        )
        logger.info("Role suggestion generated", extra={"confidence": result.confidence})
        return result
    except Exception as exc:
        logger.error("Role suggestion failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {exc}")


@router.post("/suggest-salary", response_model=SalarySuggestionResponse_V1)
async def suggest_salary(request: SalarySuggestionRequest) -> SalarySuggestionResponse_V1:
    """
    Get AI-suggested salary range based on role, location, and skills.
    
    This estimates a competitive salary range by analyzing the candidate's
    experience, skill rarity, and location market rates.
    """
    settings = get_settings()
    client = LLMClient(settings)
    
    try:
        prompt = build_salary_suggestion_prompt(
            request.profile,
            request.target_role,
            request.location,
        )
        result = await client.call(
            prompt=prompt,
            response_format=SalarySuggestionResponse_V1,
        )
        logger.info(
            "Salary suggestion generated",
            extra={
                "min": result.min_salary,
                "max": result.max_salary,
                "confidence": result.confidence,
            }
        )
        return result
    except Exception as exc:
        logger.error("Salary suggestion failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {exc}")


@router.post("/suggest-locations", response_model=LocationSuggestionResponse_V1)
async def suggest_locations(request: LocationSuggestionRequest) -> LocationSuggestionResponse_V1:
    """
    Get AI-suggested work locations based on skills and job market.
    
    This analyzes where the candidate's skills are most in-demand and
    evaluates remote work viability for their role type.
    """
    settings = get_settings()
    client = LLMClient(settings)
    
    try:
        prompt = build_location_suggestion_prompt(
            request.profile,
            request.current_location,
        )
        result = await client.call(
            prompt=prompt,
            response_format=LocationSuggestionResponse_V1,
        )
        logger.info(
            "Location suggestion generated",
            extra={"remote_score": result.remote_friendly_score}
        )
        return result
    except Exception as exc:
        logger.error("Location suggestion failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {exc}")


@router.post("/match-job", response_model=JobMatchScore_V1)
async def match_job(request: JobMatchRequest) -> JobMatchScore_V1:
    """
    Get AI-generated match score between candidate and a single job.
    
    Returns a 0-100 score with detailed breakdowns for skill match,
    experience match, location compatibility, and any red flags.
    """
    settings = get_settings()
    client = LLMClient(settings)
    
    try:
        prompt = build_job_match_prompt(request.profile, request.job)
        result = await client.call(
            prompt=prompt,
            response_format=JobMatchScore_V1,
        )
        logger.info(
            "Job match scored",
            extra={"score": result.score, "summary": result.summary[:50]}
        )
        return result
    except Exception as exc:
        logger.error("Job match scoring failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {exc}")


@router.post("/match-jobs-batch", response_model=BatchJobMatchResponse)
async def match_jobs_batch(request: BatchJobMatchRequest) -> BatchJobMatchResponse:
    """
    Score multiple jobs against a candidate profile in batch.
    
    This is more efficient than calling match-job repeatedly.
    Jobs are processed sequentially to avoid rate limits.
    Maximum 20 jobs per batch.
    """
    if len(request.jobs) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 jobs per batch. Split your request."
        )
    
    settings = get_settings()
    client = LLMClient(settings)
    
    matches: list[JobMatchScore_V1] = []
    errors: list[str] = []
    
    for i, job in enumerate(request.jobs):
        try:
            prompt = build_job_match_prompt(request.profile, job)
            result = await client.call(
                prompt=prompt,
                response_format=JobMatchScore_V1,
            )
            matches.append(result)
        except Exception as exc:
            job_id = job.get("id", f"job_{i}")
            errors.append(f"{job_id}: {exc}")
            logger.warning("Batch job match failed for %s: %s", job_id, exc)
    
    logger.info(
        "Batch job matching complete",
        extra={"matched": len(matches), "errors": len(errors)}
    )
    
    return BatchJobMatchResponse(matches=matches, errors=errors)


# ---------------------------------------------------------------------------
# Cover Letter Generation
# ---------------------------------------------------------------------------

class CoverLetterRequest(BaseModel):
    """Request body for cover letter generation."""
    profile: dict = Field(..., description="Parsed resume profile data")
    job: dict = Field(..., description="Job posting data")
    tone: str = Field(default="professional", description="Tone: professional, enthusiastic, creative")


from backend.llm.contracts import (
    CoverLetterResponse_V1,
    build_cover_letter_prompt,
)

@router.post("/generate-cover-letter", response_model=CoverLetterResponse_V1)
async def generate_cover_letter(request: CoverLetterRequest) -> CoverLetterResponse_V1:
    """
    Generate a personalized cover letter for a specific job.
    """
    settings = get_settings()
    client = LLMClient(settings)
    
    try:
        prompt = build_cover_letter_prompt(
            request.profile,
            request.job,
            request.tone
        )
        result = await client.call(
            prompt=prompt,
            response_format=CoverLetterResponse_V1,
        )
        logger.info("Cover letter generated")
        return result
    except Exception as exc:
        logger.error("Cover letter generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI generation failed: {exc}")

