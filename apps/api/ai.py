"""
AI Suggestion API endpoints for smart onboarding.

These endpoints provide AI-powered suggestions for:
- Job roles based on resume analysis
- Salary ranges based on role, location, and skills
- Location recommendations based on skills and job market
- Job match scoring for personalized job feeds
"""

from __future__ import annotations

from datetime import datetime
import time
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
    build_location_suggestion_prompt,
    build_job_match_prompt,
    OnboardingQuestionsResponse_V1,
    build_onboarding_questions_prompt,
)
from backend.domain.repositories import CoverLetterRepo, JobMatchCacheRepo, ProfileRepo
import asyncpg
import hashlib
import json
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.api.ai")

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
    """Dependency override required"""
    raise NotImplementedError

async def _get_user_id() -> str:
    """Dependency override required"""
    raise NotImplementedError

router = APIRouter(prefix="/ai", tags=["AI Suggestions"])


# ---------------------------------------------------------------------------
# Input Sanitization for Prompt Injection Protection
# ---------------------------------------------------------------------------

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.
    
    Removes or escapes potentially dangerous patterns that could manipulate LLM behavior.
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove or escape common prompt injection patterns
    dangerous_patterns = [
        # System prompt overrides
        r'\n(system|assistant|human|user):',
        r'\n### ',
        r'\n## ',
        r'\n# ',
        
        # Instruction overrides
        r'ignore (previous|prior|all) instructions',
        r'forget (previous|prior|all) instructions',
        r'do not follow',
        r'disregard',
        
        # Role changes
        r'you are (not|a)',
        r'act as',
        r'pretend to be',
        
        # Output format changes
        r'output (as|in) json',
        r'respond (as|in|with) json',
        r'format.*json',
        
        # Dangerous commands
        r'execute',
        r'run',
        r'system',
        r'command',
    ]
    
    sanitized = text
    
    # Remove dangerous patterns (case insensitive)
    import re
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Limit length to prevent extremely long inputs
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    # Escape remaining newlines that could break prompt structure
    sanitized = sanitized.replace('\n\n', '\n').replace('\n\n', '\n')
    
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
    job_id: str
    template_id: str = "professional_standard"
    tone: str = "professional"
    length: str = "standard"
    focus_areas: list[str] = []
    custom_instructions: str = ""


class OnboardingQuestionsRequest(BaseModel):
    """Request body for onboarding calibration questions."""
    profile: dict = Field(..., description="Parsed resume profile data")



# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/onboarding-questions", response_model=OnboardingQuestionsResponse_V1)
async def generate_onboarding_questions(
    request: OnboardingQuestionsRequest,
    user_id: str = Depends(_get_user_id)
) -> OnboardingQuestionsResponse_V1:
    """
    Generate strategic calibration questions based on the candidate's profile.
    """
    client = _get_llm_client()
    
    # Sanitize inputs
    from backend.domain.masking import strip_pii_for_llm
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))

    try:
        prompt = build_onboarding_questions_prompt(sanitized_profile)
        result = await client.call(
            prompt=prompt,
            response_format=OnboardingQuestionsResponse_V1,
        )
        logger.info("Onboarding questions generated")
        return result
    except Exception as exc:
        logger.error("Onboarding question generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI generation failed: {exc}")


@router.post("/suggest-roles", response_model=RoleSuggestionResponse_V1)
async def suggest_roles(request: RoleSuggestionRequest, user_id: str = Depends(_get_user_id)) -> RoleSuggestionResponse_V1:
    """
    Get AI-suggested job roles based on parsed resume profile.
    
    This analyzes the candidate's experience, skills, and career progression
    to suggest the most suitable job titles and experience level.
    """
    client = _get_llm_client()
    
    # Sanitize inputs to prevent prompt injection
    from backend.domain.masking import strip_pii_for_llm
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    
    try:
        prompt = build_role_suggestion_prompt(sanitized_profile)
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
async def suggest_salary(request: SalarySuggestionRequest, user_id: str = Depends(_get_user_id)) -> SalarySuggestionResponse_V1:
    """
    Get AI-suggested salary range based on role, location, and skills.
    
    This estimates a competitive salary range by analyzing the candidate's
    experience, skill rarity, and location market rates.
    """
    client = _get_llm_client()
    
    # Sanitize inputs and strip PII before sending to external LLM
    from backend.domain.masking import strip_pii_for_llm
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
            }
        )
        return result
    except Exception as exc:
        logger.error("Salary suggestion failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {exc}")


@router.post("/suggest-locations", response_model=LocationSuggestionResponse_V1)
async def suggest_locations(request: LocationSuggestionRequest, user_id: str = Depends(_get_user_id)) -> LocationSuggestionResponse_V1:
    """
    Get AI-suggested work locations based on skills and job market.
    
    This analyzes where the candidate's skills are most in-demand and
    evaluates remote work viability for their role type.
    """
    client = _get_llm_client()
    
    # Strip PII before sending to external LLM
    from backend.domain.masking import strip_pii_for_llm
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    
    try:
        prompt = build_location_suggestion_prompt(
            sanitized_profile,
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
async def match_job(
    request: JobMatchRequest, 
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> JobMatchScore_V1:
    """
    Get AI-generated match score between candidate and a single job.
    
    Returns a 0-100 score with detailed breakdowns for skill match,
    experience match, location compatibility, and any red flags.
    """
    # Sanitize inputs and strip PII before sending to external LLM
    from backend.domain.masking import strip_pii_for_llm
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    sanitized_job = sanitize_dict_input(request.job)

    # Check cache
    job_id = sanitized_job.get("id")
    profile_hash = hashlib.sha256(json.dumps(sanitized_profile, sort_keys=True).encode()).hexdigest()
    
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
            extra={"score": result.score, "summary": result.summary[:50]}
        )
        
        # Cache result
        if job_id:
            async with db.acquire() as conn:
                await JobMatchCacheRepo.put(conn, str(job_id), profile_hash, result.model_dump(mode="json"))

        return result
    except Exception as exc:
        logger.error("Job match scoring failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {exc}")


@router.post("/match-jobs-batch", response_model=BatchJobMatchResponse)
async def match_jobs_batch(
    request: BatchJobMatchRequest, 
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> BatchJobMatchResponse:
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
    
    client = _get_llm_client()
    
    # Sanitize inputs and strip PII before sending to external LLM
    from backend.domain.masking import strip_pii_for_llm
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    sanitized_jobs = [sanitize_dict_input(job) for job in request.jobs]
    profile_hash = hashlib.sha256(json.dumps(sanitized_profile, sort_keys=True).encode()).hexdigest()
    
    matches: list[JobMatchScore_V1] = []
    errors: list[str] = []
    
    for i, job in enumerate(sanitized_jobs):
        job_id = job.get("id")
        
        # Check cache first
        if job_id:
            async with db.acquire() as conn:
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
                async with db.acquire() as conn:
                    await JobMatchCacheRepo.put(conn, str(job_id), profile_hash, result.model_dump(mode="json"))

        except Exception as exc:
            job_label = job_id or f"job_{i}"
            errors.append(f"{job_label}: {exc}")
            logger.warning("Batch job match failed for %s: %s", job_label, exc)
    
    logger.info(
        "Batch job matching complete",
        extra={"matched": len(matches), "errors": len(errors)}
    )
    
    return BatchJobMatchResponse(matches=matches, errors=errors)


# ---------------------------------------------------------------------------
# Cover Letter Templates and Storage
# ---------------------------------------------------------------------------

@router.get("/cover-letters/templates", response_model=list[CoverLetterTemplate])
async def list_cover_letter_templates(user_id: str = Depends(_get_user_id)) -> list[CoverLetterTemplate]:
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
            variables=["hiring_manager_name", "company_name", "job_title", "your_field", "key_skills"],
            is_default=True
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
            variables=["hook", "job_title", "company_name", "years_experience", "your_field", "relevant_topic", "key_strength", "company_goal"],
            is_default=False
        )
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
            generated_at=r["created_at"].isoformat() if r["created_at"] else datetime.now().isoformat(),
            is_bookmarked=r.get("is_bookmarked", False)
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
    client = _get_llm_client()
    
    try:
        # Fetch the user's actual profile for personalized cover letter generation
        # Strip PII (email, phone, URLs) before building the LLM prompt
        from backend.domain.masking import strip_pii_for_llm
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

I am excited to apply for the [Job Title] position at [Company Name]. With my background in software development and experience building scalable applications, I am confident I can contribute to your team's success.

[Personalized content based on job and profile]

I would welcome the opportunity to discuss how my skills and experience align with [Company Name]'s needs.

Sincerely,
[Your Name]"""

        prompt = f"""Generate a personalized cover letter using this template:

{template_content}

Job details: {request.job_id}
User profile: {profile_summary}
Tone: {request.tone}
Length: {request.length}

Focus areas: {', '.join(request.focus_areas) if request.focus_areas else 'technical skills, experience, fit'}

Make it specific to the job and company. Keep it professional and concise."""

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
                tone=request.tone,
                quality_score=0.85,
                suggestions=["Consider adding more specific metrics", "Tailor the closing paragraph"],
            )

        return GeneratedCoverLetter(
            id=str(saved["id"]),
            job_id=str(saved["job_id"]),
            content=saved["content"],
            template_used=saved["template_id"],
            tone=saved["tone"],
            word_count=len(saved["content"].split()),
            quality_score=saved["quality_score"],
            suggestions=json.loads(saved["suggestions"]) if saved["suggestions"] else [],
            generated_at=saved["created_at"].isoformat(),
            is_bookmarked=saved["is_bookmarked"]
        )
    except Exception as exc:
        logger.error("Enhanced cover letter generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI generation failed: {exc}")


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
async def generate_cover_letter(request: CoverLetterRequest, user_id: str = Depends(_get_user_id)) -> CoverLetterResponse_V1:
    """
    Generate a personalized cover letter for a specific job.
    """
    client = _get_llm_client()
    
    # Sanitize and strip PII before sending to external LLM
    from backend.domain.masking import strip_pii_for_llm
    sanitized_profile = strip_pii_for_llm(sanitize_dict_input(request.profile))
    sanitized_job = sanitize_dict_input(request.job)
    
    try:
        prompt = build_cover_letter_prompt(
            sanitized_profile,
            sanitized_job,
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

