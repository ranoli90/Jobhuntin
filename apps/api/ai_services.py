"""AI Service layer - business logic for AI-powered features.

This module contains the core business logic for AI operations,
separating it from the API endpoints for better maintainability.
"""

from __future__ import annotations

import asyncio
from typing import Any

import asyncpg

from backend.domain.repositories import JobMatchCacheRepo, ProfileRepo
from backend.llm import LLMClient
from backend.llm.contracts import (
    JobMatchScore_V1,
    LocationSuggestionResponse_V1,
    OnboardingQuestionsResponse_V1,
    RoleSuggestionResponse_V1,
    SalarySuggestionResponse_V1,
)
from shared.ai_validation import sanitize_for_ai
from shared.logging_config import get_logger
from shared.redis_client import get_redis

logger = get_logger("sorce.api.ai_services")


class AIService:
    """Service class for AI-powered features."""

    def __init__(self, db: asyncpg.Connection):
        self.db = db
        self.llm_client = LLMClient()
        self.profile_repo = ProfileRepo(db)
        self.cache_repo = JobMatchCacheRepo(db)

    async def get_role_suggestions(
        self,
        resume_text: str,
        skills: list[str],
        experience_years: int,
        education_level: str,
    ) -> RoleSuggestionResponse_V1:
        """Get AI-powered role suggestions with caching."""
        try:
            # Generate cache key
            cache_key = self._generate_role_cache_key(
                resume_text, skills, experience_years, education_level
            )

            # Check cache first
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return RoleSuggestionResponse_V1.parse_raw(cached_result)

            # Validate and sanitize input (prevent prompt injection)
            text_result = sanitize_for_ai(resume_text, max_length=10000, min_length=None)
            if not text_result.is_valid:
                raise ValueError(text_result.error_message or "Invalid resume text")
            sanitized_text = text_result.sanitized_input or resume_text[:10000]
            sanitized_skills = []
            for skill in skills[:20]:
                if isinstance(skill, str) and skill.strip():
                    r = sanitize_for_ai(skill[:100], max_length=100, min_length=None)
                    if r.is_valid and r.sanitized_input:
                        sanitized_skills.append(r.sanitized_input)

            # Get AI response
            prompt = self._build_role_suggestion_prompt(
                resume_text=sanitized_text,
                skills=sanitized_skills,
                experience_years=experience_years,
                education_level=education_level,
            )

            result = await self.llm_client.call(
                prompt=prompt, response_format=RoleSuggestionResponse_V1
            )

            # Cache result
            await self._cache_result(cache_key, result.json(), ttl=3600)

            return result

        except Exception as e:
            logger.error(f"Error in role suggestions: {e}")
            raise

    async def get_salary_suggestions(
        self,
        role: str,
        location: str,
        skills: list[str],
        experience_years: int,
        education_level: str,
    ) -> SalarySuggestionResponse_V1:
        """Get AI-powered salary suggestions with market data."""
        try:
            # Generate cache key
            cache_key = self._generate_salary_cache_key(
                role, location, skills, experience_years, education_level
            )

            # Check cache first
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return SalarySuggestionResponse_V1.parse_raw(cached_result)

            # Validate and sanitize input (prevent prompt injection)
            r_role = sanitize_for_ai(role[:200], max_length=200, min_length=None)
            sanitized_role = r_role.sanitized_input or role[:200] if r_role.is_valid else role[:200]
            r_loc = sanitize_for_ai(location[:200], max_length=200, min_length=None)
            sanitized_location = r_loc.sanitized_input or location[:200] if r_loc.is_valid else location[:200]
            sanitized_skills = []
            for skill in skills[:20]:
                if isinstance(skill, str) and skill.strip():
                    r = sanitize_for_ai(skill[:100], max_length=100, min_length=None)
                    if r.is_valid and r.sanitized_input:
                        sanitized_skills.append(r.sanitized_input)

            # Get AI response
            prompt = self._build_salary_suggestion_prompt(
                role=sanitized_role,
                location=sanitized_location,
                skills=sanitized_skills,
                experience_years=experience_years,
                education_level=education_level,
            )

            result = await self.llm_client.call(
                prompt=prompt, response_format=SalarySuggestionResponse_V1
            )

            # Cache result
            await self._cache_result(
                cache_key, result.json(), ttl=7200
            )  # 2 hours cache

            return result

        except Exception as e:
            logger.error(f"Error in salary suggestions: {e}")
            raise

    async def get_location_suggestions(
        self,
        skills: list[str],
        role: str,
        experience_years: int,
        remote_preference: bool,
    ) -> LocationSuggestionResponse_V1:
        """Get AI-powered location suggestions."""
        try:
            # Generate cache key
            cache_key = self._generate_location_cache_key(
                skills, role, experience_years, remote_preference
            )

            # Check cache first
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return LocationSuggestionResponse_V1.parse_raw(cached_result)

            # Validate and sanitize input (prevent prompt injection)
            sanitized_skills = []
            for skill in skills[:20]:
                if isinstance(skill, str) and skill.strip():
                    r = sanitize_for_ai(skill[:100], max_length=100, min_length=None)
                    if r.is_valid and r.sanitized_input:
                        sanitized_skills.append(r.sanitized_input)
            r_role = sanitize_for_ai(role[:200], max_length=200, min_length=None)
            sanitized_role = r_role.sanitized_input or role[:200] if r_role.is_valid else role[:200]

            # Get AI response
            prompt = self._build_location_suggestion_prompt(
                skills=sanitized_skills,
                role=sanitized_role,
                experience_years=experience_years,
                remote_preference=remote_preference,
            )

            result = await self.llm_client.call(
                prompt=prompt, response_format=LocationSuggestionResponse_V1
            )

            # Cache result
            await self._cache_result(cache_key, result.json(), ttl=3600)

            return result

        except Exception as e:
            logger.error(f"Error in location suggestions: {e}")
            raise

    async def get_job_matches(
        self,
        profile_id: str,
        job_ids: list[str],
        limit: int = 10,
    ) -> JobMatchScore_V1:
        """Get AI-powered job matching with batch processing."""
        try:
            # Validate profile exists
            profile = await self.profile_repo.get_by_id(profile_id)
            if not profile:
                raise ValueError(f"Profile {profile_id} not found")

            # Check cache first
            cache_key = self._generate_job_match_cache_key(profile_id, job_ids)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return JobMatchScore_V1.parse_raw(cached_result)

            # Process jobs in batches
            matches = []
            batch_size = 5  # Process 5 jobs at a time

            for i in range(0, min(len(job_ids), limit), batch_size):
                batch_job_ids = job_ids[i : i + batch_size]
                batch_matches = await self._process_job_batch(profile, batch_job_ids)
                matches.extend(batch_matches)

                # Small delay between batches to avoid rate limiting
                if i + batch_size < min(len(job_ids), limit):
                    await asyncio.sleep(0.1)

            result = JobMatchScore_V1(matches=matches)

            # Cache result
            await self._cache_result(
                cache_key, result.json(), ttl=1800
            )  # 30 minutes cache

            return result

        except Exception as e:
            logger.error(f"Error in job matching: {e}")
            raise

    async def get_onboarding_questions(
        self,
        resume_text: str,
        current_step: str,
    ) -> OnboardingQuestionsResponse_V1:
        """Get AI-powered onboarding questions."""
        try:
            # Generate cache key
            cache_key = self._generate_onboarding_cache_key(resume_text, current_step)

            # Check cache first
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return OnboardingQuestionsResponse_V1.parse_raw(cached_result)

            # Validate and sanitize input (prevent prompt injection)
            text_result = sanitize_for_ai(resume_text, max_length=10000, min_length=None)
            if not text_result.is_valid:
                raise ValueError(text_result.error_message or "Invalid resume text")
            sanitized_text = text_result.sanitized_input or resume_text[:10000]
            step_result = sanitize_for_ai(current_step[:500], max_length=500, min_length=None)
            sanitized_step = step_result.sanitized_input or current_step[:500] if step_result.is_valid else current_step[:500]

            # Get AI response
            prompt = self._build_onboarding_questions_prompt(
                resume_text=sanitized_text,
                current_step=sanitized_step,
            )

            result = await self.llm_client.call(
                prompt=prompt, response_format=OnboardingQuestionsResponse_V1
            )

            # Cache result
            await self._cache_result(cache_key, result.json(), ttl=1800)

            return result

        except Exception as e:
            logger.error(f"Error in onboarding questions: {e}")
            raise

    # ---------------------------------------------------------------------------
    # Private Helper Methods
    # ---------------------------------------------------------------------------

    async def _process_job_batch(
        self,
        profile: dict[str, Any],
        job_ids: list[str],
    ) -> list[JobMatchScore_V1]:
        """Process a batch of jobs for matching."""
        matches = []

        for job_id in job_ids:
            try:
                # Get job details
                job_details = await self._get_job_details(job_id)
                if not job_details:
                    continue

                # Build prompt
                prompt = self._build_job_match_prompt(profile, job_details)

                # Get AI response
                match_score = await self.llm_client.call(
                    prompt=prompt, response_format=JobMatchScore_V1
                )
                matches.append(match_score)

            except Exception as e:
                logger.warning(f"Error processing job {job_id}: {e}")
                continue

        return matches

    async def _get_job_details(self, job_id: str) -> dict[str, Any] | None:
        """Get comprehensive job details from database."""
        try:
            from backend.domain.repositories import JobRepo

            job_details = await JobRepo.get_by_id(self.db, job_id)
            if not job_details:
                return {
                    "id": job_id,
                    "title": "Unknown Job",
                    "description": "Job details not available",
                    "requirements": [],
                    "location": "Unknown",
                    "salary_range": "Not specified",
                    "error": "Job not found",
                }
            return job_details
        except Exception as e:
            logger.error(f"Error fetching job details for {job_id}: {e}")
            return {
                "id": job_id,
                "title": "Error Loading Job",
                "description": "Failed to load job details",
                "requirements": [],
                "location": "Unknown",
                "salary_range": "Not specified",
                "error": str(e),
            }

    _AI_CACHE_PREFIX = "ai:cache:"

    def _generate_cache_key(self, *args) -> str:
        """Generate a cache key from arguments. Prefixed to avoid collisions."""
        import hashlib

        content = ":".join(str(arg) for arg in args)
        digest = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
        return f"{self._AI_CACHE_PREFIX}{digest}"

    def _generate_role_cache_key(
        self,
        resume_text: str,
        skills: list[str],
        experience_years: int,
        education_level: str,
    ) -> str:
        """Generate cache key for role suggestions."""
        return self._generate_cache_key(
            "role_suggestion",
            hash(resume_text[:100]),  # First 100 chars of resume
            ",".join(sorted(skills)),
            experience_years,
            education_level,
        )

    def _generate_salary_cache_key(
        self,
        role: str,
        location: str,
        skills: list[str],
        experience_years: int,
        education_level: str,
    ) -> str:
        """Generate cache key for salary suggestions."""
        return self._generate_cache_key(
            "salary_suggestion",
            role.lower(),
            location.lower(),
            ",".join(sorted(skills)),
            experience_years,
            education_level,
        )

    def _generate_location_cache_key(
        self,
        skills: list[str],
        role: str,
        experience_years: int,
        remote_preference: bool,
    ) -> str:
        """Generate cache key for location suggestions."""
        return self._generate_cache_key(
            "location_suggestion",
            ",".join(sorted(skills)),
            role.lower(),
            experience_years,
            str(remote_preference),
        )

    def _generate_job_match_cache_key(self, profile_id: str, job_ids: list[str]) -> str:
        """Generate cache key for job matching."""
        return self._generate_cache_key(
            "job_match",
            profile_id,
            ",".join(sorted(job_ids)),
        )

    def _generate_onboarding_cache_key(
        self, resume_text: str, current_step: str
    ) -> str:
        """Generate cache key for onboarding questions."""
        return self._generate_cache_key(
            "onboarding_questions",
            hash(resume_text[:100]),
            current_step.lower(),
        )

    async def _get_cached_result(self, cache_key: str) -> str | None:
        """Get cached result from Redis."""
        try:
            r = await get_redis()
            result = await r.get(cache_key)
            if result is None:
                return None
            # Redis client uses decode_responses=True, so result is str
            return result if isinstance(result, str) else result.decode("utf-8")
        except Exception as e:
            logger.warning(f"Error getting cached result for {cache_key}: {e}")
            return None

    async def _cache_result(self, cache_key: str, result: str, ttl: int) -> None:
        """Cache result in Redis."""
        try:
            r = await get_redis()
            await r.setex(cache_key, ttl, result)
        except Exception as e:
            logger.warning(f"Error caching result for {cache_key}: {e}")

    # ---------------------------------------------------------------------------
    # Prompt Building Methods (moved from contracts)
    # ---------------------------------------------------------------------------

    def _build_role_suggestion_prompt(
        self,
        resume_text: str,
        skills: list[str],
        experience_years: int,
        education_level: str,
    ) -> str:
        """Build prompt for role suggestions."""
        return f"""
Based on the following resume information, suggest 5-7 suitable job roles:

Resume Text:
{resume_text}

Key Skills: {", ".join(skills)}

Experience: {experience_years} years
Education: {education_level}

Please suggest roles that match the candidate's profile. For each role, provide:
1. Job title
2. Match score (0-100)
3. Key requirements
4. Salary range estimate
5. Career growth potential

Format as JSON according to the RoleSuggestionResponse schema.
"""

    def _build_salary_suggestion_prompt(
        self,
        role: str,
        location: str,
        skills: list[str],
        experience_years: int,
        education_level: str,
    ) -> str:
        """Build prompt for salary suggestions."""
        return f"""
Provide salary range estimates for the following position:

Role: {role}
Location: {location}
Key Skills: {", ".join(skills)}
Experience: {experience_years} years
Education: {education_level}

Consider:
- Local market rates
- Industry standards
- Experience level
- Skill demand
- Location cost of living

Provide:
1. Base salary range
2. Total compensation range
3. Market confidence score
4. Negotiation tips
5. Market trends

Format as JSON according to the SalarySuggestionResponse schema.
"""

    def _build_location_suggestion_prompt(
        self,
        skills: list[str],
        role: str,
        experience_years: int,
        remote_preference: bool,
    ) -> str:
        """Build prompt for location suggestions."""
        return f"""
Suggest 5-7 optimal locations for job seekers with:

Skills: {", ".join(skills)}
Target Role: {role}
Experience: {experience_years} years
Remote Preference: {remote_preference}

Consider:
- Job market demand
- Cost of living
- Quality of life
- Industry hubs
- Remote work opportunities

For each location, provide:
1. City/Region name
2. Match score (0-100)
3. Average salary range
4. Cost of living index
5. Remote work percentage
6. Pros and cons

Format as JSON according to the LocationSuggestionResponse schema.
"""

    def _build_job_match_prompt(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
    ) -> str:
        """Build prompt for job matching."""
        return f"""
Calculate match score between candidate profile and job:

Candidate Profile:
- Skills: {profile.get("skills", [])}
- Experience: {profile.get("experience_years", 0)} years
- Education: {profile.get("education_level", "")}
- Location Preference: {profile.get("location_preference", "")}
- Salary Expectation: {profile.get("salary_expectation", "")}

Job Details:
- Title: {job.get("title", "")}
- Description: {job.get("description", "")}
- Requirements: {job.get("requirements", [])}
- Location: {job.get("location", "")}
- Salary Range: {job.get("salary_range", "")}

Calculate match score (0-100) based on:
- Skills alignment
- Experience match
- Education requirements
- Location compatibility
- Salary alignment

Provide:
1. Overall match score
2. Skills match score
3. Experience match score
4. Location match score
5. Salary match score
6. Strengths
7. Gaps
8. Recommendations

Format as JSON according to the JobMatchScore schema.
"""

    def _build_onboarding_questions_prompt(
        self,
        resume_text: str,
        current_step: str,
    ) -> str:
        """Build prompt for onboarding questions."""
        return f"""
Generate 3-5 personalized onboarding questions for the current step based on:

Resume Text:
{resume_text}

Current Step: {current_step}

Questions should:
1. Be relevant to the current step
2. Help gather missing information
3. Be engaging and conversational
4. Guide the user through onboarding
5. Be specific and actionable

For each question, provide:
1. Question text
2. Question type (text|choice|rating)
3. Options (if choice type)
4. Required status
5. Help text

Format as JSON according to the OnboardingQuestionsResponse schema.
"""
