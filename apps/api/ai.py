"""AI Suggestion API endpoints for smart onboarding.

These endpoints provide AI-powered suggestions for:
- Job roles based on resume analysis
- Salary ranges based on role, location, and skills
- Location recommendations based on skills and job market
- Job match scoring for personalized job feeds
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from packages.backend.domain.repositories import (
    CoverLetterRepo,
    JobMatchCacheRepo,
    ProfileRepo,
)
from packages.backend.llm import LLMClient
from packages.backend.llm.contracts import (
    CoverLetterResponse_V1,
    JobMatchScore_V1,
    LocationSuggestionResponse_V1,
    OnboardingQuestionsResponse_V1,
    RoleSuggestionResponse_V1,
    SalarySuggestionResponse_V1,
    build_cover_letter_prompt,
    build_job_match_prompt,
    build_location_suggestion_prompt,
    build_onboarding_questions_prompt,
    build_role_suggestion_prompt,
    build_salary_suggestion_prompt,
)
from shared.ai_validation import sanitize_for_ai, validate_and_sanitize_ai_input
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.api.ai")

# ---------------------------------------------------------------------------
# Per-user rate limiting for expensive AI endpoints (Redis when available)
# ---------------------------------------------------------------------------
_user_rate_limits: dict[str, list[float]] = defaultdict(list)


async def _check_user_rate_limit(
    user_id: str, action: str, max_per_hour: int = 20
) -> bool:
    """Check rate limit. Uses Redis when available for multi-instance support."""
    key = f"ai_rate:{user_id}:{action}"
    now = time.time()
    window = 3600  # 1 hour
    s = get_settings()
    if s.redis_url:
        try:
            from shared.redis_client import get_redis

            r = await get_redis()
            pipe = r.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            results = await pipe.execute()
            count = results[0]
            ttl = results[1]
            if ttl == -1:
                await r.expire(key, window)
            if count > max_per_hour:
                return False
            return True
        except Exception as e:
            logger.warning(
                "AI rate limit Redis check failed, falling back to in-memory: %s", e
            )
    # Fallback: in-memory (single-instance only)
    _user_rate_limits[key] = [t for t in _user_rate_limits[key] if now - t < window]
    if len(_user_rate_limits[key]) >= max_per_hour:
        return False
    _user_rate_limits[key].append(now)
    return True


# ---------------------------------------------------------------------------
# Singleton LLM client — avoids per-request instantiation overhead
# ---------------------------------------------------------------------------
_llm_client: LLMClient | None = None


def _get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(get_settings())
    return _llm_client


async def _get_pool() -> asyncpg.Pool:
    """Dependency override required."""
    raise NotImplementedError


async def _get_user_id() -> str:
    """Dependency override required."""
    raise NotImplementedError


async def _get_tenant_id() -> str | None:
    """Dependency override required."""
    raise NotImplementedError


router = APIRouter(prefix="/ai", tags=["AI Suggestions"])


# ---------------------------------------------------------------------------
# Input Sanitization for Prompt Injection Protection
# ---------------------------------------------------------------------------


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent prompt injection attacks.

    Removes or escapes potentially dangerous patterns that could manipulate LLM behavior.
    """
    if not isinstance(text, str):
        return str(text)

    # Remove or escape common prompt injection patterns
    dangerous_patterns = [
        # System prompt overrides
        r"\n(system|assistant|human|user):",
        r"\n### ",
        r"\n## ",
        r"\n# ",
        # Instruction overrides
        r"ignore (previous|prior|all) instructions",
        r"forget (previous|prior|all) instructions",
        r"do not follow",
        r"disregard",
        # Role changes
        r"you are (not|a)",
        r"act as",
        r"pretend to be",
        # Output format changes
        r"output (as|in) json",
        r"respond (as|in|with) json",
        r"format.*json",
        # Dangerous commands
        r"execute",
        r"run",
        r"system",
        r"command",
    ]

    sanitized = text

    # Remove dangerous patterns (case insensitive)
    import re

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    # Limit length to prevent extremely long inputs
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    # Escape remaining newlines that could break prompt structure
    sanitized = sanitized.replace("\n\n", "\n").replace("\n\n", "\n")

    return sanitized.strip()


def sanitize_dict_input(data: dict) -> dict:
    """Recursively sanitize all string values in a dictionary."""
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_input(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_input(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class RoleSuggestionRequest(BaseModel):
    """Request body for role suggestions."""

    profile: dict = Field(..., description="Parsed resume profile data")


class SalarySuggestionRequest(BaseModel):
    """Request body for salary suggestions."""

    profile: dict = Field(..., description="Parsed resume profile data")
    target_role: str = Field(..., max_length=200, description="Target job role")
    location: str = Field(default="Remote", max_length=200, description="Preferred work location")


class LocationSuggestionRequest(BaseModel):
    """Request body for location suggestions."""

    profile: dict = Field(..., description="Parsed resume profile data")
    current_location: str = Field(default="", max_length=200, description="Current location if any")


class JobMatchRequest(BaseModel):
    """Request body for job match scoring."""

    profile: dict | None = Field(
        default=None, description="Profile from client; if empty, loaded server-side"
    )
    job: dict = Field(..., description="Job posting data")


class BatchJobMatchRequest(BaseModel):
    """Request body for batch job match scoring."""

    profile: dict | None = Field(
        default=None, description="Profile from client; if empty, loaded server-side"
    )
    jobs: list[dict] = Field(..., description="List of job postings to score")


class BatchJobMatchResponse(BaseModel):
    """Response for batch job match scoring."""

    matches: list[JobMatchScore_V1] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class CoverLetterTemplate(BaseModel):
    id: str
    name: str
    description: str
    category: str
    content: str
    variables: list[str]
    is_default: bool


class GeneratedCoverLetter(BaseModel):
    id: str
    job_id: str
    content: str
    template_used: str
    tone: str
    word_count: int
    quality_score: float
    suggestions: list[str]
    generated_at: str
    is_bookmarked: bool


class CoverLetterGenerationRequest(BaseModel):
    job_id: str = Field(..., min_length=36, max_length=36)
    template_id: str = Field(default="professional_standard", max_length=100)
    tone: str = Field(default="professional", max_length=50)
    length: str = Field(default="standard", max_length=50)
    focus_areas: list[str] = Field(default_factory=list, max_length=20)
    custom_instructions: str = Field(default="", max_length=2000)


class OnboardingQuestionsRequest(BaseModel):
    """Request body for onboarding calibration questions."""

    profile: dict = Field(..., description="Parsed resume profile data")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/onboarding-questions", response_model=OnboardingQuestionsResponse_V1)
async def generate_onboarding_questions(
    request: OnboardingQuestionsRequest, user_id: str = Depends(_get_user_id)
) -> OnboardingQuestionsResponse_V1:
    """Generate strategic calibration questions based on the candidate's profile."""
    validation_result = validate_and_sanitize_ai_input(
        profile=request.profile,
        user_id=user_id,
        tier="FREE",
    )
    if not validation_result.is_valid:
        raise HTTPException(status_code=400, detail=validation_result.error_message)

    if validation_result.warnings:
        logger.info(
            "Onboarding questions validation warnings: %s", validation_result.warnings
        )

    client = _get_llm_client()
    from packages.backend.domain.masking import strip_pii_for_llm

    sanitized_data = validation_result.sanitized_input
    sanitized_profile = strip_pii_for_llm(
        sanitized_data.get("profile", request.profile)
    )

    try:
        prompt = build_onboarding_questions_prompt(sanitized_profile)
        result = await client.call(
            prompt=prompt,
            response_format=OnboardingQuestionsResponse_V1,
        )
        logger.info("Onboarding questions generated")
        return result
    except Exception as exc:
        logger.error("Onboarding question generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


@router.post("/suggest-roles", response_model=RoleSuggestionResponse_V1)
async def suggest_roles(
    request: RoleSuggestionRequest, user_id: str = Depends(_get_user_id)
) -> RoleSuggestionResponse_V1:
    """Get AI-suggested job roles based on parsed resume profile.

    This analyzes the candidate's experience, skills, and career progression
    to suggest the most suitable job titles and experience level.
    """
    if not await _check_user_rate_limit(user_id, "suggest_roles", 20):
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    validation_result = validate_and_sanitize_ai_input(
        profile=request.profile,
        user_id=user_id,
        tier="FREE",
    )
    if not validation_result.is_valid:
        raise HTTPException(status_code=400, detail=validation_result.error_message)

    client = _get_llm_client()
    from packages.backend.domain.masking import strip_pii_for_llm

    sanitized_data = validation_result.sanitized_input
    sanitized_profile = strip_pii_for_llm(
        sanitized_data.get("profile", request.profile)
    )

    try:
        prompt = build_role_suggestion_prompt(sanitized_profile)
        result = await client.call(
            prompt=prompt,
            response_format=RoleSuggestionResponse_V1,
        )
        logger.info(
            "Role suggestion generated", extra={"confidence": result.confidence}
        )
        return result
    except Exception as exc:
        logger.error("Role suggestion failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI suggestions temporarily unavailable. Please try again.",
        )


@router.post("/suggest-salary", response_model=SalarySuggestionResponse_V1)
async def suggest_salary(
    request: SalarySuggestionRequest, user_id: str = Depends(_get_user_id)
) -> SalarySuggestionResponse_V1:
    """Get AI-suggested salary range based on role, location, and skills.

    This estimates a competitive salary range by analyzing the candidate's
    experience, skill rarity, and location market rates.
    """
    if not await _check_user_rate_limit(user_id, "suggest_salary", 20):
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    client = _get_llm_client()

    # Sanitize inputs and strip PII before sending to external LLM
    from packages.backend.domain.masking import strip_pii_for_llm

    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    sanitized_target_role = sanitize_input(request.target_role)
    sanitized_location = sanitize_input(request.location)

    try:
        prompt = build_salary_suggestion_prompt(
            sanitized_profile,
            sanitized_target_role,
            sanitized_location,
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
            },
        )
        return result
    except Exception as exc:
        logger.error("Salary suggestion failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI suggestions temporarily unavailable. Please try again.",
        )


@router.post("/suggest-locations", response_model=LocationSuggestionResponse_V1)
async def suggest_locations(
    request: LocationSuggestionRequest, user_id: str = Depends(_get_user_id)
) -> LocationSuggestionResponse_V1:
    """Get AI-suggested work locations based on skills and job market.

    This analyzes where the candidate's skills are most in-demand and
    evaluates remote work viability for their role type.
    """
    if not await _check_user_rate_limit(user_id, "suggest_locations", 20):
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    location = (request.current_location or "").strip()[:200]
    client = _get_llm_client()

    # Strip PII before sending to external LLM
    from packages.backend.domain.masking import strip_pii_for_llm

    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))

    try:
        prompt = build_location_suggestion_prompt(
            sanitized_profile,
            location,
        )
        result = await client.call(
            prompt=prompt,
            response_format=LocationSuggestionResponse_V1,
        )
        logger.info(
            "Location suggestion generated",
            extra={"remote_score": result.remote_friendly_score},
        )
        return result
    except Exception as exc:
        logger.error("Location suggestion failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI suggestions temporarily unavailable. Please try again.",
        )


@router.post("/match-job", response_model=JobMatchScore_V1)
async def match_job(
    request: JobMatchRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> JobMatchScore_V1:
    """Get AI-generated match score between candidate and a single job.

    Returns a 0-100 score with detailed breakdowns for skill match,
    experience match, location compatibility, and any red flags.
    Profile can be omitted; server loads from DB when empty.
    """
    if not await _check_user_rate_limit(user_id, "match_job", 20):
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    # Sanitize inputs and strip PII before sending to external LLM
    from packages.backend.domain.deep_profile import deep_profile_to_llm_dict
    from packages.backend.domain.masking import strip_pii_for_llm
    from packages.backend.domain.profile_assembly import assemble_profile

    profile_dict = request.profile
    if not profile_dict or not isinstance(profile_dict, dict):
        async with db.acquire() as conn:
            deep_profile = await assemble_profile(conn, user_id)
        if deep_profile:
            profile_dict = deep_profile_to_llm_dict(deep_profile)
        else:
            profile_dict = {}
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(profile_dict))
    sanitized_job = sanitize_dict_input(request.job)

    # Check cache
    job_id = sanitized_job.get("id")
    profile_hash = hashlib.sha256(
        json.dumps(sanitized_profile, sort_keys=True).encode()
    ).hexdigest()

    if job_id:
        async with db.acquire() as conn:
            cached = await JobMatchCacheRepo.get(conn, str(job_id), profile_hash)
            if cached:
                logger.info("Job match cache hit", extra={"job_id": job_id})
                return JobMatchScore_V1(**cached)

    client = _get_llm_client()

    try:
        prompt = build_job_match_prompt(sanitized_profile, sanitized_job)
        result = await client.call(
            prompt=prompt,
            response_format=JobMatchScore_V1,
        )
        logger.info(
            "Job match scored",
            extra={"score": result.score, "summary": result.summary[:50]},
        )

        # Cache result
        if job_id:
            async with db.acquire() as conn:
                await JobMatchCacheRepo.put(
                    conn, str(job_id), profile_hash, result.model_dump(mode="json")
                )

        return result
    except Exception as exc:
        logger.error("Job match scoring failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


@router.post("/match-jobs-batch", response_model=BatchJobMatchResponse)
async def match_jobs_batch(
    request: BatchJobMatchRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> BatchJobMatchResponse:
    """Score multiple jobs against a candidate profile in batch.

    This is more efficient than calling match-job repeatedly.
    Jobs are processed sequentially to avoid rate limits.
    Maximum 20 jobs per batch.
    Profile can be omitted; server loads from DB when empty.
    """
    if len(request.jobs) > 20:
        raise HTTPException(
            status_code=400, detail="Maximum 20 jobs per batch. Split your request."
        )

    client = _get_llm_client()

    # Sanitize inputs and strip PII before sending to external LLM
    from packages.backend.domain.deep_profile import deep_profile_to_llm_dict
    from packages.backend.domain.masking import strip_pii_for_llm
    from packages.backend.domain.profile_assembly import assemble_profile

    profile_dict = request.profile
    if not profile_dict or not isinstance(profile_dict, dict):
        async with db.acquire() as conn:
            deep_profile = await assemble_profile(conn, user_id)
        if deep_profile:
            profile_dict = deep_profile_to_llm_dict(deep_profile)
        else:
            profile_dict = {}
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(profile_dict))
    sanitized_jobs = [sanitize_dict_input(job) for job in request.jobs]
    profile_hash = hashlib.sha256(
        json.dumps(sanitized_profile, sort_keys=True).encode()
    ).hexdigest()

    matches: list[JobMatchScore_V1] = []
    errors: list[str] = []

    # Use single connection for all cache operations (prevents N+1)
    async with db.acquire() as conn:
        for i, job in enumerate(sanitized_jobs):
            job_id = job.get("id")

            # Check cache first
            if job_id:
                cached = await JobMatchCacheRepo.get(conn, str(job_id), profile_hash)
                if cached:
                    matches.append(JobMatchScore_V1(**cached))
                    continue

            try:
                prompt = build_job_match_prompt(sanitized_profile, job)
                result = await client.call(
                    prompt=prompt,
                    response_format=JobMatchScore_V1,
                )
                matches.append(result)

                # Cache result
                if job_id:
                    await JobMatchCacheRepo.put(
                        conn, str(job_id), profile_hash, result.model_dump(mode="json")
                    )

            except Exception as exc:
                job_label = job_id or f"job_{i}"
                errors.append(f"{job_label}: matching failed")
                logger.warning("Batch job match failed for %s: %s", job_label, exc)

    logger.info(
        "Batch job matching complete",
        extra={"matched": len(matches), "errors": len(errors)},
    )

    return BatchJobMatchResponse(matches=matches, errors=errors)


# ---------------------------------------------------------------------------
# Semantic Matching with Vector Embeddings
# ---------------------------------------------------------------------------


class SemanticMatchRequest(BaseModel):
    """Request for semantic job matching."""

    profile: dict[str, Any] = Field(..., description="Candidate profile")
    job: dict[str, Any] = Field(..., description="Job to match against")
    min_salary: int | None = Field(
        default=None, description="Minimum salary requirement"
    )
    max_salary: int | None = Field(
        default=None, description="Maximum salary expectation"
    )
    preferred_locations: list[str] = Field(
        default_factory=list, description="Preferred work locations"
    )
    remote_only: bool = Field(default=False, description="Only match remote jobs")


class SemanticMatchResponse(BaseModel):
    """Response with semantic match score and explanation."""

    job_id: str
    score: float = Field(ge=0.0, le=1.0, description="Overall match score 0-1")
    semantic_similarity: float = Field(
        ge=0.0, le=1.0, description="Vector embedding similarity"
    )
    skill_match_ratio: float = Field(
        ge=0.0, le=1.0, description="Ratio of matched skills"
    )
    experience_alignment: float = Field(
        ge=0.0, le=1.0, description="Experience level alignment"
    )
    matched_skills: list[str] = Field(
        default_factory=list, description="Skills found in both profile and job"
    )
    missing_skills: list[str] = Field(
        default_factory=list, description="Skills required by job but not in profile"
    )
    reasoning: str = Field(..., description="Human-readable explanation")
    confidence: str = Field(..., description="Confidence level: low, medium, high")
    passed_dealbreakers: bool = Field(
        default=True, description="Whether job passes all dealbreakers"
    )
    dealbreaker_reasons: list[str] = Field(
        default_factory=list, description="Reasons for failing dealbreakers"
    )


@router.post("/semantic-match", response_model=SemanticMatchResponse)
async def semantic_match_job(
    request: SemanticMatchRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> SemanticMatchResponse:
    """Compute semantic match score using vector embeddings.

    This is the "Precision Matcher" implementation that:
    - Uses text embeddings for semantic similarity
    - Applies skill matching heuristics
    - Checks dealbreaker constraints (salary, location)
    - Returns explainable reasoning for each match

    This endpoint provides higher accuracy than keyword-based
    matching and matches the capabilities of ApplyPass/JobRight.
    """
    from packages.backend.domain.masking import strip_pii_for_llm
    from packages.backend.domain.semantic_matching import (
        Dealbreakers,
        get_matching_service,
    )

    # Strip PII from profile before processing
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    sanitized_job = sanitize_dict_input(request.job)

    # Build dealbreakers from request
    dealbreakers = Dealbreakers(
        min_salary=request.min_salary,
        max_salary=request.max_salary,
        locations=request.preferred_locations,
        remote_only=request.remote_only,
    )

    # Get matching service
    service = get_matching_service()

    try:
        # HIGH: Pass db connection for embedding cache
        async with db.acquire() as conn:
            result = await service.compute_match_score(
                profile=sanitized_profile,
                job=sanitized_job,
                dealbreakers=dealbreakers,
                db_conn=conn,
            )

        logger.info(
            "Semantic match computed",
            extra={
                "job_id": result.job_id,
                "score": result.score,
                "passed": result.passed_dealbreakers,
            },
        )

        return SemanticMatchResponse(
            job_id=result.job_id,
            score=result.score,
            semantic_similarity=result.explanation.semantic_similarity,
            skill_match_ratio=result.explanation.skill_match_ratio,
            experience_alignment=result.explanation.experience_alignment,
            matched_skills=result.explanation.matched_skills,
            missing_skills=result.explanation.missing_skills,
            reasoning=result.explanation.reasoning,
            confidence=result.explanation.confidence,
            passed_dealbreakers=result.passed_dealbreakers,
            dealbreaker_reasons=result.dealbreaker_reasons,
        )
    except Exception as exc:
        logger.error("Semantic matching failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


class BatchSemanticMatchRequest(BaseModel):
    """Request for batch semantic matching."""

    profile: dict[str, Any] = Field(..., description="Candidate profile")
    jobs: list[dict[str, Any]] = Field(
        ..., max_length=20, description="Jobs to match (max 20)"
    )
    dealbreakers: dict[str, Any] = Field(
        default_factory=dict, description="Dealbreaker preferences"
    )


class BatchSemanticMatchResult(BaseModel):
    """Result for a single job in batch matching."""

    job_id: str
    score: float = Field(ge=0.0, le=1.0)
    explanation: dict[str, Any]
    passed_dealbreakers: bool = True
    dealbreaker_reasons: list[str] = Field(default_factory=list)


class BatchSemanticMatchFailedItem(BaseModel):
    """A job that failed to match in batch."""

    job_id: str
    error: str


class BatchSemanticMatchResponse(BaseModel):
    """Response for batch semantic matching."""

    results: list[BatchSemanticMatchResult]
    failed: list[BatchSemanticMatchFailedItem] = Field(default_factory=list)


@router.post("/semantic-match/batch", response_model=BatchSemanticMatchResponse)
async def semantic_match_batch(
    request: BatchSemanticMatchRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> BatchSemanticMatchResponse:
    """Batch semantic matching for multiple jobs.

    Processes up to 20 jobs in a single request for efficiency.
    Returns match scores with explanations for each job.
    """
    from packages.backend.domain.masking import strip_pii_for_llm
    from packages.backend.domain.semantic_matching import (
        Dealbreakers,
        get_matching_service,
    )

    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))

    dealbreaker_prefs = request.dealbreakers or {}
    dealbreakers = Dealbreakers(
        min_salary=dealbreaker_prefs.get("min_salary"),
        max_salary=dealbreaker_prefs.get("max_salary"),
        locations=dealbreaker_prefs.get("locations", []),
        remote_only=dealbreaker_prefs.get("remote_only", False),
        onsite_only=dealbreaker_prefs.get("onsite_only", False),
        visa_sponsorship_required=dealbreaker_prefs.get(
            "visa_sponsorship_required", False
        ),
        excluded_companies=dealbreaker_prefs.get("excluded_companies", []),
        excluded_keywords=dealbreaker_prefs.get("excluded_keywords", []),
    )

    service = get_matching_service()
    results: list[BatchSemanticMatchResult] = []
    failed_items: list[dict[str, str]] = []

    # HIGH: Acquire db connection once for embedding cache in batch processing
    async with db.acquire() as conn:
        for job in request.jobs[:20]:
            sanitized_job = sanitize_dict_input(job)
            job_id = str(job.get("id", ""))
            try:
                result = await service.compute_match_score(
                    profile=sanitized_profile,
                    job=sanitized_job,
                    dealbreakers=dealbreakers,
                    db_conn=conn,
                )
                results.append(
                    BatchSemanticMatchResult(
                        job_id=result.job_id,
                        score=result.score,
                        explanation={
                            "score": result.explanation.score,
                            "semantic_similarity": result.explanation.semantic_similarity,
                            "skill_match_ratio": result.explanation.skill_match_ratio,
                            "experience_alignment": result.explanation.experience_alignment,
                            "location_compatible": result.explanation.location_compatible,
                            "salary_in_range": result.explanation.salary_in_range,
                            "matched_skills": result.explanation.matched_skills,
                            "missing_skills": result.explanation.missing_skills,
                            "reasoning": result.explanation.reasoning,
                            "confidence": result.explanation.confidence,
                        },
                        passed_dealbreakers=result.passed_dealbreakers,
                        dealbreaker_reasons=result.dealbreaker_reasons,
                    )
                )
            except Exception as exc:
                logger.warning("Failed to match job %s: %s", job_id, exc)
                failed_items.append({"job_id": job_id, "error": str(exc)})

    logger.info(
        "Batch semantic match completed",
        extra={
            "user_id": user_id,
            "jobs_matched": len(results),
            "failed": len(failed_items),
        },
    )

    return BatchSemanticMatchResponse(
        results=results,
        failed=[BatchSemanticMatchFailedItem(**f) for f in failed_items],
    )


# ---------------------------------------------------------------------------
# Cover Letter Templates and Storage
# ---------------------------------------------------------------------------


@router.get("/cover-letters/templates", response_model=list[CoverLetterTemplate])
async def list_cover_letter_templates(
    user_id: str = Depends(_get_user_id),
) -> list[CoverLetterTemplate]:
    """Get available cover letter templates."""
    # For now, return hardcoded templates
    # In production, this would fetch from database
    templates = [
        CoverLetterTemplate(
            id="professional_standard",
            name="Professional Standard",
            description="Classic professional cover letter template",
            category="professional",
            content="""[Your Name]
[Your Address]
[City, State, ZIP Code]
[Email Address]
[Phone Number]
[Date]

[Hiring Manager's Name]
[Company Name]
[Company Address]
[City, State, ZIP Code]

Dear [Hiring Manager's Name],

I am writing to express my interest in the [Job Title] position at [Company Name], as advertised. With my background in [Your Field/Industry] and experience in [Key Skills/Experience], I am excited about the opportunity to contribute to your team.

[Body paragraph 1 - Highlight relevant experience and achievements]

[Body paragraph 2 - Explain why you're interested in the company/role]

[Body paragraph 3 - Call to action and closing]

Sincerely,
[Your Name]""",
            variables=[
                "hiring_manager_name",
                "company_name",
                "job_title",
                "your_field",
                "key_skills",
            ],
            is_default=True,
        ),
        CoverLetterTemplate(
            id="creative_modern",
            name="Creative Modern",
            description="Modern, creative cover letter template",
            category="creative",
            content="""[Your Name] | [Your Email] | [Your Phone] | [Your LinkedIn/Portfolio]

[Date]

[Hiring Manager's Name]
[Job Title]
[Company Name]
[Company Address]

Dear [Hiring Manager's Name],

What if I told you that [hook - interesting fact about your experience]?

That's the kind of innovative thinking I bring to [Company Name] as a candidate for the [Job Title] role. With [X years] of experience in [Your Field], I've developed a unique perspective on [relevant topic].

[Body - Tell your story and connect it to the role]

I'm particularly drawn to [Company Name] because [why this company/role excites you].

Let's connect and explore how my [key strength] can drive [company goal/outcome].

Best regards,
[Your Name]""",
            variables=[
                "hook",
                "job_title",
                "company_name",
                "years_experience",
                "your_field",
                "relevant_topic",
                "key_strength",
                "company_goal",
            ],
            is_default=False,
        ),
        CoverLetterTemplate(
            id="executive_senior",
            name="Executive Senior",
            description="Executive-level cover letter for senior positions",
            category="executive",
            content="""[Your Name]
[Your Title] | [Your Email] | [Your Phone] | [Your LinkedIn]
[Date]

[Hiring Manager's Name]
[Company Name]
[Company Address]

Dear [Hiring Manager's Name],

I am writing to express my strong interest in the [Job Title] position at [Company Name]. As a [Your Current Role] with [X] years of executive experience in [Your Industry], I have a proven track record of [key achievement 1] and [key achievement 2].

Throughout my career, I have demonstrated expertise in [key area 1], [key area 2], and [key area 3]. Notably, I led [specific project] that resulted in [quantifiable result], and spearheaded [initiative] that improved [metric] by [percentage].

I am particularly drawn to [Company Name] because of your reputation for [company strength] and your commitment to [company value]. The opportunity to [specific opportunity] aligns perfectly with my professional goals.

I would welcome the opportunity to discuss how my leadership experience and strategic vision can contribute to your team's success.

Thank you for your time and consideration.

Sincerely,
[Your Name]""",
            variables=[
                "your_title",
                "your_current_role",
                "years_experience",
                "your_industry",
                "key_achievement_1",
                "key_achievement_2",
                "key_area_1",
                "key_area_2",
                "key_area_3",
                "specific_project",
                "quantifiable_result",
                "initiative",
                "metric",
                "percentage",
                "company_strength",
                "company_value",
                "specific_opportunity",
                "professional_goals",
            ],
            is_default=False,
        ),
        CoverLetterTemplate(
            id="technical_developer",
            name="Technical Developer",
            description="Technical developer cover letter with focus on skills",
            category="technical",
            content="""[Your Name]
[Your Email] | [Your Phone] | [Your GitHub/Portfolio]
[Date]

[Hiring Manager's Name]
[Technical Lead]
[Company Name]
[Company Address]

Dear [Hiring Manager's Name],

I am writing to apply for the [Job Title] position at [Company Name]. As a [Your Current Role] with [X] years of experience in software development, I have extensive expertise in [primary technology stack] and a strong background in [secondary technologies].

My technical expertise includes:
- [Programming Language 1]: [experience level] years
- [Programming Language 2]: [experience level] years
- [Framework/Platform]: [experience level] years
- [Database Technology]: [experience level] years
- [Cloud Platform]: [experience level] years

In my current role at [Current Company], I have successfully [key technical achievement 1] and [key technical achievement 2]. Notably, I [specific technical project] that improved [technical metric] by [percentage] and [another technical project] that enhanced [business outcome].

I am particularly interested in [Company Name] because of your [technical innovation/tech stack] and your work in [specific technical area]. The opportunity to [technical challenge] aligns perfectly with my skills and career aspirations.

I would be excited to discuss how my technical background and problem-solving abilities can contribute to your engineering team.

Thank you for considering my application.

Best regards,
[Your Name]""",
            variables=[
                "primary_technology_stack",
                "secondary_technologies",
                "framework_platform",
                "database_technology",
                "cloud_platform",
                "experience_level",
                "current_company",
                "key_technical_achievement_1",
                "key_technical_achievement_2",
                "specific_technical_project",
                "technical_metric",
                "percentage",
                "another_technical_project",
                "business_outcome",
                "technical_innovation",
                "tech_stack",
                "specific_technical_area",
                "technical_challenge",
                "skills",
                "career_aspirations",
            ],
            is_default=False,
        ),
        CoverLetterTemplate(
            id="entry_level",
            name="Entry Level",
            description="Entry-level cover letter for recent graduates",
            category="entry",
            content="""[Your Name]
[Your Email] | [Your Phone] | [Your LinkedIn/Portfolio]
[Date]

[Hiring Manager's Name]
[Hiring Manager]
[Company Name]
[Company Address]

Dear [Hiring Manager's Name],

I am writing to express my strong interest in the [Job Title] position at [Company Name]. As a recent [Your Degree] graduate from [Your University], I am eager to begin my professional career and contribute my fresh perspective and enthusiasm to your team.

During my studies, I developed strong skills in [relevant skill 1], [relevant skill 2], and [relevant skill 3]. I also gained practical experience through [internship/project 1] and [internship/project 2], where I [specific achievement 1] and [specific achievement 2].

I am particularly excited about [Company Name] because of your [company reputation] and your commitment to [company value]. The opportunity to [entry-level opportunity] would allow me to apply my academic knowledge and learn from experienced professionals like you.

I am a quick learner, highly motivated, and ready to contribute my energy and fresh ideas to your team. I would be grateful for the chance to discuss how my educational background and enthusiasm can benefit [Company Name].

Thank you for considering my application.

Sincerely,
[Your Name]""",
            variables=[
                "your_degree",
                "your_university",
                "relevant_skill_1",
                "relevant_skill_2",
                "relevant_skill_3",
                "internship_project_1",
                "internship_project_2",
                "specific_achievement_1",
                "specific_achievement_2",
                "company_reputation",
                "company_value",
                "entry_level_opportunity",
                "academic_knowledge",
                "experienced_professionals",
                "company_name",
            ],
            is_default=False,
        ),
        CoverLetterTemplate(
            id="career_change",
            name="Career Change",
            description="Career change cover letter for transitioning professionals",
            category="professional",
            content="""[Your Name]
[Your Address]
[City, State, ZIP Code]
[Email Address]
[Phone Number]
[Date]

[Hiring Manager's Name]
[Hiring Manager]
[Company Name]
[Company Address]

Dear [Hiring Manager's Name],

I am writing to express my interest in the [Job Title] position at [Company Name]. While my background has been in [Previous Industry], I am actively transitioning to [New Industry] and bring valuable transferable skills from my [X] years of professional experience.

Throughout my career in [Previous Industry], I have developed strong skills in [transferable skill 1], [transferable skill 2], and [transferable skill 3]. These skills, combined with my experience in [relevant experience area], have prepared me well for success in [New Industry].

I have been actively upskilling through [training/certification 1] and [training/certification 2], and I am passionate about [new industry passion]. My unique perspective, combining [previous industry insight] with [new industry knowledge], allows me to approach challenges with [unique approach].

I am particularly drawn to [Company Name] because of your [company innovation/industry leadership] and your commitment to [company value]. The opportunity to [career change opportunity] would allow me to apply my diverse experience while learning from your team.

I would be excited to discuss how my transferable skills and fresh perspective can contribute to your team's success.

Thank you for considering my application.

Sincerely,
[Your Name]""",
            variables=[
                "previous_industry",
                "new_industry",
                "x_years",
                "transferable_skill_1",
                "transferable_skill_2",
                "transferable_skill_3",
                "relevant_experience_area",
                "training/certification_1",
                "training/certification_2",
                "new_industry_passion",
                "previous_industry_insight",
                "new_industry_knowledge",
                "unique_approach",
                "company_innovation",
                "industry_leadership",
                "company_value",
                "career_change_opportunity",
                "diverse_experience",
                "learning_from_your_team",
            ],
            is_default=False,
        ),
    ]
    return templates


@router.get("/cover-letters", response_model=list[GeneratedCoverLetter])
async def list_generated_cover_letters(
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[GeneratedCoverLetter]:
    """Get user's generated cover letters."""
    async with db.acquire() as conn:
        rows = await CoverLetterRepo.list_by_user(conn, user_id)

    return [
        GeneratedCoverLetter(
            id=str(r["id"]),
            job_id=str(r["job_id"]) if r["job_id"] else "",
            content=r["content"],
            template_used=r["template_id"] or "",
            tone=r["tone"] or "",
            word_count=len(r["content"].split()),
            quality_score=r["quality_score"] or 0.0,
            suggestions=json.loads(r["suggestions"]) if r["suggestions"] else [],
            generated_at=(
                r["created_at"].isoformat()
                if r["created_at"]
                else datetime.now().isoformat()
            ),
            is_bookmarked=r.get("is_bookmarked", False),
        )
        for r in rows
    ]


@router.post("/cover-letters/generate", response_model=GeneratedCoverLetter)
async def generate_cover_letter_enhanced(
    request: CoverLetterGenerationRequest,
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> GeneratedCoverLetter:
    """Generate a personalized cover letter (enhanced endpoint)."""
    if not await _check_user_rate_limit(user_id, "generate_cover_letter", 10):
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    # Validate and sanitize user-controlled prompt inputs
    allowed_tone = {"professional", "enthusiastic", "creative"}
    tone = (request.tone or "professional").strip().lower()
    if tone not in allowed_tone:
        tone = "professional"
    allowed_length = {"short", "standard", "long"}
    length = (request.length or "standard").strip().lower()
    if length not in allowed_length:
        length = "standard"
    focus_areas = [
        sanitize_input(fa)[:80]
        for fa in (request.focus_areas or [])[:10]
        if isinstance(fa, str) and fa.strip()
    ]
    focus_areas_str = ", ".join(focus_areas) if focus_areas else "technical skills, experience, fit"
    client = _get_llm_client()

    try:
        # Fetch the user's actual profile for personalized cover letter generation
        # Strip PII (email, phone, URLs) before building the LLM prompt
        from packages.backend.domain.masking import strip_pii_for_llm

        profile_summary = "No profile available"
        async with db.acquire() as conn:
            profile_data = await ProfileRepo.get_profile_data(conn, user_id)
        if profile_data:
            profile_data = strip_pii_for_llm(profile_data)
            contact = profile_data.get("contact", {})
            experience = profile_data.get("experience", [])
            skills = profile_data.get("skills", [])
            education = profile_data.get("education", [])
            summary_parts = []
            if contact.get("full_name"):
                summary_parts.append(f"Name: {contact['full_name']}")
            if experience:
                exp_strs = []
                for exp in experience[:3]:
                    title = exp.get("title", "")
                    company = exp.get("company", "")
                    if title and company:
                        exp_strs.append(f"{title} at {company}")
                    elif title:
                        exp_strs.append(title)
                if exp_strs:
                    summary_parts.append(f"Experience: {'; '.join(exp_strs)}")
            if skills:
                summary_parts.append(f"Skills: {', '.join(skills[:15])}")
            if education:
                edu_strs = []
                for edu in education[:2]:
                    degree = edu.get("degree", "")
                    school = edu.get("institution", edu.get("school", ""))
                    if degree and school:
                        edu_strs.append(f"{degree} from {school}")
                if edu_strs:
                    summary_parts.append(f"Education: {'; '.join(edu_strs)}")
            if summary_parts:
                profile_summary = ". ".join(summary_parts)

        # Use a simple template for now
        template_content = """[Your Name]
[Your Address]
[City, State, ZIP Code]
[Email Address]
[Date]

[Hiring Manager]
[Company Name]
[Company Address]
[City, State, ZIP Code]

Dear Hiring Manager,

I am excited to apply for the [Job Title] position at [Company Name]. With my background in software development and experience building scalable applications, I am confident I can contribute to your team's success.  # noqa: E501

[Personalized content based on job and profile]

I would welcome the opportunity to discuss how my skills and experience align with [Company Name]'s needs.  # noqa: E501

Sincerely,
[Your Name]"""

        # Fetch comprehensive job details to include in the prompt
        job_details = "Job details not available"
        if request.job_id:
            try:
                from packages.backend.domain.repositories import JobRepo

                async with db.acquire() as conn:
                    job_data = await JobRepo.get_by_id(conn, request.job_id)
                    if job_data:
                        job_details = f"""
                        Title: {job_data.get("title", "Unknown")}
                        Company: {job_data.get("company_name", job_data.get("company", "Unknown"))}
                        Location: {job_data.get("location", "Unknown")}
                        Remote: {job_data.get("remote", False)}
                        Salary: ${job_data.get("salary_min", "Not specified")} - ${job_data.get("salary_max", "Not specified")}
                        Job Type: {job_data.get("job_type", "Not specified")}
                        Description: {job_data.get("description", "No description available")}
                        Requirements: {job_data.get("requirements", [])}
                        Responsibilities: {job_data.get("responsibilities", [])}
                        Qualifications: {job_data.get("qualifications", [])}
                        Benefits: {job_data.get("benefits", [])}
                        Company Size: {job_data.get("company_size", "Unknown")}
                        Industry: {job_data.get("company_industry", "Unknown")}
                        Company Culture: {job_data.get("company_culture", "Not specified")}
                        """.strip()
                    else:
                        job_details = f"Job with ID {request.job_id} not found"
            except Exception as e:
                job_details = f"Error loading job details: {str(e)}"
                logger.error(f"Error fetching job details for cover letter: {e}")

        prompt = f"""Generate a personalized cover letter using this template:

{template_content}

Job details:
{job_details}

User profile: {profile_summary}
Tone: {tone}
Length: {length}

Focus areas: {focus_areas_str}

Make it specific to the job and company. Include relevant skills and experience from the profile that match the job requirements. Keep it professional and concise."""

        result = await client.call(
            prompt=prompt,
            response_format=CoverLetterResponse_V1,
        )

        # Create enhanced response
        # Save to DB
        async with db.acquire() as conn:
            saved = await CoverLetterRepo.create(
                conn,
                user_id=user_id,
                job_id=request.job_id,  # Assume valid UUID or strict string
                content=result.content,
                template_id=request.template_id,
                tone=tone,
                quality_score=0.85,
                suggestions=[
                    "Consider adding more specific metrics",
                    "Tailor the closing paragraph",
                ],
            )

        return GeneratedCoverLetter(
            id=str(saved["id"]),
            job_id=str(saved["job_id"]),
            content=saved["content"],
            template_used=saved["template_id"],
            tone=saved["tone"],
            word_count=len(saved["content"].split()),
            quality_score=saved["quality_score"],
            suggestions=(
                json.loads(saved["suggestions"]) if saved["suggestions"] else []
            ),
            generated_at=saved["created_at"].isoformat(),
            is_bookmarked=saved["is_bookmarked"],
        )
    except Exception as exc:
        logger.error("Enhanced cover letter generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


# ---------------------------------------------------------------------------
# Cover Letter Generation
# ---------------------------------------------------------------------------


class CoverLetterRequest(BaseModel):
    """Request body for cover letter generation."""

    profile: dict = Field(..., description="Parsed resume profile data")
    job: dict = Field(..., description="Job posting data")
    tone: str = Field(
        default="professional", description="Tone: professional, enthusiastic, creative"
    )


@router.post("/generate-cover-letter", response_model=CoverLetterResponse_V1)
async def generate_cover_letter(
    request: CoverLetterRequest, user_id: str = Depends(_get_user_id)
) -> CoverLetterResponse_V1:
    """Generate a personalized cover letter for a specific job."""
    if not await _check_user_rate_limit(user_id, "generate_cover_letter", 10):
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    allowed_tone = {"professional", "enthusiastic", "creative"}
    tone = (request.tone or "professional").strip().lower()
    if tone not in allowed_tone:
        tone = "professional"
    client = _get_llm_client()

    # Sanitize and strip PII before sending to external LLM
    from packages.backend.domain.masking import strip_pii_for_llm

    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    sanitized_job = sanitize_dict_input(request.job)

    try:
        prompt = build_cover_letter_prompt(
            sanitized_profile, sanitized_job, tone
        )
        result = await client.call(
            prompt=prompt,
            response_format=CoverLetterResponse_V1,
        )
        logger.info("Cover letter generated")
        return result
    except Exception as exc:
        logger.error("Cover letter generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


class TailorResumeRequest(BaseModel):
    """Request body for resume tailoring."""

    profile: dict = Field(..., description="Parsed resume profile data")
    job: dict = Field(..., description="Job posting data")
    match_explanation: dict | None = Field(
        default=None, description="Optional semantic match explanation"
    )


class TailorResumeResponse(BaseModel):
    """Response for resume tailoring."""

    original_summary: str
    tailored_summary: str
    highlighted_skills: list[str]
    emphasized_experiences: list[dict]
    added_keywords: list[str]
    ats_optimization_score: float
    tailoring_confidence: str


@router.post("/tailor-resume", response_model=TailorResumeResponse)
async def tailor_resume(
    request: TailorResumeRequest, user_id: str = Depends(_get_user_id)
) -> TailorResumeResponse:
    """Dynamically tailor a resume for a specific job application.

    This endpoint:
    1. Analyzes job requirements
    2. Prioritizes relevant skills and experience
    3. Generates a tailored summary
    4. Computes ATS optimization score
    """
    if not await _check_user_rate_limit(user_id, "tailor_resume", 10):
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    from packages.backend.domain.masking import strip_pii_for_llm
    from packages.backend.domain.resume_tailoring import get_tailoring_service

    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    sanitized_job = sanitize_dict_input(request.job)

    try:
        service = get_tailoring_service()
        result = await service.tailor_resume(
            profile=sanitized_profile,
            job=sanitized_job,
            match_explanation=request.match_explanation,
        )
        logger.info("Resume tailored for job: %s", sanitized_job.get("id", "unknown"))
        return TailorResumeResponse(
            original_summary=result.original_summary,
            tailored_summary=result.tailored_summary,
            highlighted_skills=result.highlighted_skills,
            emphasized_experiences=result.emphasized_experiences,
            added_keywords=result.added_keywords,
            ats_optimization_score=result.ats_optimization_score,
            tailoring_confidence=result.tailoring_confidence,
        )
    except Exception as exc:
        logger.error("Resume tailoring failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


class ATSScoreRequest(BaseModel):
    """Request body for ATS scoring."""

    resume_text: str = Field(..., description="Plain text resume content")
    job_description: str = Field(..., description="Job posting description")


class ATSScoreResponse(BaseModel):
    """Response for ATS scoring."""

    overall_score: float
    metrics: dict[str, float]
    recommendations: list[str]


@router.post("/ats-score", response_model=ATSScoreResponse)
async def compute_ats_score(
    request: ATSScoreRequest, user_id: str = Depends(_get_user_id)
) -> ATSScoreResponse:
    """Compute comprehensive ATS score for a resume against a job description.

    Implements 23 scoring metrics for ATS optimization analysis.
    """
    if not await _check_user_rate_limit(user_id, "ats_score", 20):
        raise HTTPException(429, "Rate limit exceeded. Please try again later.")
    # Sanitize to prevent prompt injection in downstream LLM/analysis
    resume_result = sanitize_for_ai(
        request.resume_text, max_length=10000, min_length=None
    )
    job_result = sanitize_for_ai(
        request.job_description, max_length=5000, min_length=None
    )
    if not resume_result.is_valid:
        raise HTTPException(400, resume_result.error_message or "Invalid resume text")
    if not job_result.is_valid:
        raise HTTPException(400, job_result.error_message or "Invalid job description")
    sanitized_resume = resume_result.sanitized_input or request.resume_text[:10000]
    sanitized_job = job_result.sanitized_input or request.job_description[:5000]
    from packages.backend.domain.resume_tailoring import ATSScorer

    try:
        scores = await ATSScorer.score_resume(
            resume_text=sanitized_resume,
            job_description=sanitized_job,
        )
        overall = ATSScorer.compute_overall_score(scores)

        recommendations = []
        if scores.get("keyword_match", 1.0) < 0.5:
            recommendations.append("Add more keywords from the job description")
        if scores.get("skills_relevance", 1.0) < 0.5:
            recommendations.append("Highlight relevant technical skills")
        if scores.get("experience_alignment", 1.0) < 0.5:
            recommendations.append("Emphasize relevant work experience")
        if scores.get("quantifiable_achievements", 1.0) < 0.5:
            recommendations.append("Add quantifiable achievements with metrics")

        logger.info("ATS score computed: %.2f", overall)
        return ATSScoreResponse(
            overall_score=overall,
            metrics=scores,
            recommendations=recommendations,
        )
    except Exception as exc:
        logger.error("ATS scoring failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


# ---------------------------------------------------------------------------
# Match Weights Configuration
# ---------------------------------------------------------------------------


class MatchWeightsRequest(BaseModel):
    """Request to configure match scoring weights."""

    semantic_similarity: float = Field(default=0.5, ge=0.0, le=1.0)
    skill_match: float = Field(default=0.3, ge=0.0, le=1.0)
    experience_alignment: float = Field(default=0.2, ge=0.0, le=1.0)


class MatchWeightsResponse(BaseModel):
    """Response with current match weights."""

    semantic_similarity: float
    skill_match: float
    experience_alignment: float
    normalized: bool


# Global match weights storage (per-tenant in production)
_match_weights_cache: dict[str, MatchWeightsRequest] = {}


@router.get("/match-weights", response_model=MatchWeightsResponse)
async def get_match_weights(
    tenant_id: str | None = Depends(_get_tenant_id),
) -> MatchWeightsResponse:
    """Get the current match scoring weights.

    Weights control how different factors contribute to the overall match score:
    - semantic_similarity: Weight for vector embedding similarity (default 0.5)
    - skill_match: Weight for skill keyword matching (default 0.3)
    - experience_alignment: Weight for experience level alignment (default 0.2)
    """
    from packages.backend.domain.semantic_matching import MatchWeights

    key = tenant_id or "default"
    if key in _match_weights_cache:
        weights = _match_weights_cache[key]
        return MatchWeightsResponse(
            semantic_similarity=weights.semantic_similarity,
            skill_match=weights.skill_match,
            experience_alignment=weights.experience_alignment,
            normalized=False,
        )

    # Return defaults
    defaults = MatchWeights.default()
    return MatchWeightsResponse(
        semantic_similarity=defaults.semantic_similarity,
        skill_match=defaults.skill_match,
        experience_alignment=defaults.experience_alignment,
        normalized=True,
    )


@router.post("/match-weights", response_model=MatchWeightsResponse)
async def set_match_weights(
    request: MatchWeightsRequest,
    tenant_id: str | None = Depends(_get_tenant_id),
    user_id: str = Depends(_get_user_id),
) -> MatchWeightsResponse:
    """Configure match scoring weights.

    Weights are automatically normalized to sum to 1.0.
    Requires admin privileges in production.
    """
    from packages.backend.domain.semantic_matching import (
        MatchWeights,
        get_matching_service,
    )

    # Normalize weights
    weights = MatchWeights(
        semantic_similarity=request.semantic_similarity,
        skill_match=request.skill_match,
        experience_alignment=request.experience_alignment,
    ).normalize()

    # Store in cache (would persist to DB in production)
    key = tenant_id or "default"
    _match_weights_cache[key] = MatchWeightsRequest(
        semantic_similarity=weights.semantic_similarity,
        skill_match=weights.skill_match,
        experience_alignment=weights.experience_alignment,
    )

    # Update service instance
    service = get_matching_service()
    service.weights = weights

    logger.info(
        "Match weights updated",
        extra={
            "tenant_id": tenant_id,
            "user_id": user_id,
            "weights": weights.model_dump(),
        },
    )

    return MatchWeightsResponse(
        semantic_similarity=weights.semantic_similarity,
        skill_match=weights.skill_match,
        experience_alignment=weights.experience_alignment,
        normalized=True,
    )


# ---------------------------------------------------------------------------
# Match Feedback Endpoints
# ---------------------------------------------------------------------------


class MatchFeedbackRequest(BaseModel):
    """Request to submit match feedback."""

    job_id: str
    rating: int = Field(..., ge=-1, le=1, description="1 = thumbs up, -1 = thumbs down")
    match_score: float = Field(..., ge=0.0, le=1.0)
    semantic_similarity: float | None = None
    skill_match_ratio: float | None = None
    feedback_text: str | None = None
    feedback_tags: list[str] = Field(default_factory=list)


class MatchFeedbackResponseAPI(BaseModel):
    """API response after submitting feedback."""

    id: str
    job_id: str
    rating: int
    created_at: datetime


class MatchFeedbackSummaryResponse(BaseModel):
    """Response with feedback summary stats."""

    total_feedback: int
    total_thumbs_up: int
    total_thumbs_down: int
    unique_users: int
    unique_jobs: int
    avg_match_score: float | None
    satisfaction_rate: float | None


@router.post("/match-feedback", response_model=MatchFeedbackResponseAPI)
async def submit_match_feedback(
    request: MatchFeedbackRequest,
    user_id: str = Depends(_get_user_id),
    tenant_id: str | None = Depends(_get_tenant_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> MatchFeedbackResponseAPI:
    """Submit feedback on a job match result.

    Users can rate matches with thumbs up (1) or thumbs down (-1).
    This feedback is used to improve future match recommendations.

    Optional feedback tags:
    - good_skills_match, bad_skills_match
    - good_location, bad_location
    - salary_too_low, salary_good
    - interesting_role, not_interested
    - remote_friendly, not_remote
    - visa_sponsored, no_visa
    """
    from packages.backend.domain.match_feedback import (
        MatchFeedbackCreate,
        MatchFeedbackRepo,
        validate_feedback_tags,
    )

    validated_tags = validate_feedback_tags(request.feedback_tags)

    feedback = MatchFeedbackCreate(
        job_id=request.job_id,
        rating=request.rating,
        match_score=request.match_score,
        semantic_similarity=request.semantic_similarity,
        skill_match_ratio=request.skill_match_ratio,
        feedback_text=request.feedback_text,
        feedback_tags=validated_tags,
        match_type="semantic",
    )

    try:
        async with db.acquire() as conn:
            result = await MatchFeedbackRepo.submit(
                conn=conn,
                user_id=user_id,
                tenant_id=tenant_id,
                feedback=feedback,
            )

        logger.info(
            "Match feedback submitted",
            extra={
                "job_id": request.job_id,
                "rating": request.rating,
                "user_id": user_id,
            },
        )

        return MatchFeedbackResponseAPI(
            id=result.id,
            job_id=result.job_id,
            rating=result.rating,
            created_at=result.created_at,
        )
    except Exception as exc:
        logger.error("Failed to submit match feedback: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


@router.get("/match-feedback/summary", response_model=MatchFeedbackSummaryResponse)
async def get_match_feedback_summary(
    days: int = 30,
    tenant_id: str | None = Depends(_get_tenant_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> MatchFeedbackSummaryResponse:
    """Get aggregate feedback summary for analytics.

    Returns overall satisfaction metrics for the specified time period.
    """
    from packages.backend.domain.match_feedback import MatchFeedbackRepo

    try:
        async with db.acquire() as conn:
            summary = await MatchFeedbackRepo.get_feedback_summary(
                conn=conn,
                tenant_id=tenant_id,
                days=days,
            )

        return MatchFeedbackSummaryResponse(**summary)
    except Exception as exc:
        logger.error("Failed to get feedback summary: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


@router.get("/match-feedback/job/{job_id}/stats")
async def get_job_feedback_stats(
    job_id: str,
    db: asyncpg.Pool = Depends(_get_pool),
):
    """Get aggregate feedback statistics for a specific job.

    Useful for understanding how users perceive match quality for a job.
    """
    from packages.backend.domain.match_feedback import MatchFeedbackRepo

    try:
        async with db.acquire() as conn:
            stats = await MatchFeedbackRepo.get_job_stats(conn=conn, job_id=job_id)

        if not stats:
            return {"message": "No feedback for this job", "job_id": job_id}

        return stats.model_dump()
    except Exception as exc:
        logger.error("Failed to get job feedback stats: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


# ---------------------------------------------------------------------------
# LLM Model Monitoring Endpoints
# ---------------------------------------------------------------------------


@router.get("/llm/metrics")
async def get_llm_metrics(
    user_id: str = Depends(_get_user_id),  # SECURITY: Require authentication
):
    """Get LLM model performance metrics.

    Returns latency percentiles, error rates, token usage, and cost estimates
    for all monitored models.
    """
    from packages.backend.domain.llm_monitoring import get_llm_monitor

    try:
        monitor = get_llm_monitor()
        return monitor.get_all_metrics()
    except Exception as exc:
        logger.error("Failed to get LLM metrics: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


@router.get("/llm/metrics/{model}")
async def get_llm_model_metrics(
    model: str,
    user_id: str = Depends(_get_user_id),  # SECURITY: Require authentication
):
    """Get performance metrics for a specific LLM model."""
    from packages.backend.domain.llm_monitoring import get_llm_monitor

    try:
        monitor = get_llm_monitor()
        return monitor.get_model_metrics(model)
    except Exception as exc:
        logger.error("Failed to get model metrics: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


@router.get("/llm/health")
async def get_llm_health(
    user_id: str = Depends(_get_user_id),  # SECURITY: Require authentication
):
    """Get health status of all LLM models.

    Identifies models with low success rates or recent failures.
    """
    from packages.backend.domain.llm_monitoring import get_llm_monitor

    try:
        monitor = get_llm_monitor()
        return monitor.get_health_status()
    except Exception as exc:
        logger.error("Failed to get LLM health: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )


@router.get("/llm/semantic-cache/stats")
async def get_semantic_cache_stats(
    user_id: str = Depends(_get_user_id),  # SECURITY: Require authentication
):
    """Get semantic cache statistics.

    Returns cache size, hit counts, and configuration.
    """
    from packages.backend.domain.semantic_cache import get_semantic_cache

    try:
        cache = get_semantic_cache()
        return cache.stats()
    except Exception as exc:
        logger.error("Failed to get semantic cache stats: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again.",
        )
