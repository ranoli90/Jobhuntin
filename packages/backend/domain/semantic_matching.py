"""
Semantic job matching service using vector embeddings.

Implements the "Precision Matcher" archetype from competitive analysis:
- Vector-based semantic matching (like ApplyPass, JobRight)
- Explainable match scoring
- Filters for dealbreakers (salary, location, visa)

Key features:
1. Embeds job descriptions and candidate profiles
2. Computes cosine similarity for match scoring
3. Provides explainable reasoning for each match
4. Respects dealbreaker preferences
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import asyncpg
from pydantic import BaseModel, Field

from backend.domain.embeddings import (
    EmbeddingClient,
    cosine_similarity,
    get_embedding_client,
    job_to_searchable_text,
    profile_to_searchable_text,
    compute_text_hash,
)
from shared.logging_config import get_logger

logger = get_logger("sorce.matching")


class Dealbreakers(BaseModel):
    """User's non-negotiable job preferences."""

    min_salary: int | None = None
    max_salary: int | None = None
    locations: list[str] = Field(default_factory=list)
    remote_only: bool = False
    onsite_only: bool = False
    visa_sponsorship_required: bool = False
    excluded_companies: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)


class MatchExplanation(BaseModel):
    """Explanation for why a job matched."""

    score: float = Field(ge=0.0, le=1.0)
    semantic_similarity: float = Field(ge=0.0, le=1.0)
    skill_match_ratio: float = Field(ge=0.0, le=1.0)
    experience_alignment: float = Field(ge=0.0, le=1.0)
    location_compatible: bool = True
    salary_in_range: bool = True
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    reasoning: str = ""
    confidence: str = "medium"  # low, medium, high


class SemanticMatchResult(BaseModel):
    """Complete result of semantic matching."""

    job_id: str
    score: float = Field(ge=0.0, le=1.0)
    explanation: MatchExplanation
    passed_dealbreakers: bool = True
    dealbreaker_reasons: list[str] = Field(default_factory=list)


class SemanticMatchingService:
    """
    Service for semantic job-candidate matching.

    Uses vector embeddings to compute semantic similarity between
    job descriptions and candidate profiles, then applies dealbreaker
    filters and generates explainable scores.
    """

    def __init__(self, embedding_client: EmbeddingClient | None = None):
        self._embedding_client = embedding_client

    @property
    def embeddings(self) -> EmbeddingClient:
        if self._embedding_client is None:
            self._embedding_client = get_embedding_client()
        return self._embedding_client

    async def compute_match_score(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
        dealbreakers: Dealbreakers | None = None,
    ) -> SemanticMatchResult:
        """
        Compute semantic match score between profile and job.

        This is the core matching function that:
        1. Generates embeddings for profile and job
        2. Computes cosine similarity
        3. Applies skill matching heuristics
        4. Checks dealbreaker constraints
        5. Generates explainable reasoning

        Args:
            profile: CanonicalProfile as dict
            job: Job dict with title, description, etc.
            dealbreakers: Optional user preferences

        Returns:
            SemanticMatchResult with score and explanation
        """
        dealbreakers = dealbreakers or Dealbreakers()

        # Generate embeddings
        profile_text = profile_to_searchable_text(profile)
        job_text = job_to_searchable_text(job)

        profile_embedding = await self.embeddings.embed_text(profile_text)
        job_embedding = await self.embeddings.embed_text(job_text)

        # Compute semantic similarity
        semantic_sim = cosine_similarity(profile_embedding, job_embedding)

        # Extract skills from profile
        profile_skills = set()
        skills_data = profile.get("skills", {})
        profile_skills.update(skills_data.get("technical", []))
        profile_skills.update(skills_data.get("soft", []))
        profile_skills = {s.lower() for s in profile_skills}

        # Extract skills from job description (simple keyword extraction)
        job_text_lower = job_text.lower()
        matched_skills: list[str] = []
        missing_skills: list[str] = []

        # Common tech skills to look for
        common_skills = [
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "c#",
            "react",
            "vue",
            "angular",
            "node",
            "django",
            "flask",
            "fastapi",
            "sql",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "machine learning",
            "ai",
            "data science",
            "analytics",
            "agile",
            "scrum",
            "git",
            "ci/cd",
            "leadership",
            "communication",
            "project management",
        ]

        for skill in common_skills:
            if skill in job_text_lower:
                if skill in profile_skills:
                    matched_skills.append(skill)
                else:
                    missing_skills.append(skill)

        skill_match_ratio = (
            len(matched_skills) / len(matched_skills + missing_skills)
            if (matched_skills or missing_skills)
            else 0.5
        )

        # Experience alignment (based on years)
        years_exp = profile.get("years_experience", 0) or 0
        exp_alignment = self._compute_experience_alignment(years_exp, job_text)

        # Compute final score (weighted combination)
        score = semantic_sim * 0.5 + skill_match_ratio * 0.3 + exp_alignment * 0.2

        # Check dealbreakers
        passed, reasons = self._check_dealbreakers(job, dealbreakers)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            score=score,
            semantic_sim=semantic_sim,
            skill_match_ratio=skill_match_ratio,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )

        # Determine confidence
        confidence = "high" if score > 0.8 else "medium" if score > 0.6 else "low"

        return SemanticMatchResult(
            job_id=str(job.get("id", "")),
            score=min(1.0, max(0.0, score)),
            explanation=MatchExplanation(
                score=score,
                semantic_similarity=semantic_sim,
                skill_match_ratio=skill_match_ratio,
                experience_alignment=exp_alignment,
                location_compatible=len(reasons) == 0
                or "location" not in " ".join(reasons).lower(),
                salary_in_range=len(reasons) == 0
                or "salary" not in " ".join(reasons).lower(),
                matched_skills=matched_skills[:10],
                missing_skills=missing_skills[:5],
                reasoning=reasoning,
                confidence=confidence,
            ),
            passed_dealbreakers=passed,
            dealbreaker_reasons=reasons,
        )

    def _compute_experience_alignment(self, years: int, job_text: str) -> float:
        """Compute how well candidate experience aligns with job requirements."""
        job_lower = job_text.lower()

        # Look for experience requirements
        if "senior" in job_lower or "lead" in job_lower or "principal" in job_lower:
            return 1.0 if years >= 5 else 0.5 if years >= 3 else 0.2
        elif "mid" in job_lower or "intermediate" in job_lower:
            return 1.0 if years >= 3 else 0.5 if years >= 1 else 0.3
        elif "junior" in job_lower or "entry" in job_lower or "graduate" in job_lower:
            return 1.0 if years <= 3 else 0.6
        else:
            return 0.7  # Default moderate alignment

    def _check_dealbreakers(
        self,
        job: dict[str, Any],
        dealbreakers: Dealbreakers,
    ) -> tuple[bool, list[str]]:
        """Check if job passes all dealbreaker constraints."""
        reasons: list[str] = []

        # Salary check
        if dealbreakers.min_salary:
            job_max = job.get("salary_max") or job.get("salary_min", 0)
            if job_max and job_max < dealbreakers.min_salary:
                reasons.append(
                    f"Salary below minimum: {job_max} < {dealbreakers.min_salary}"
                )

        # Location check
        if dealbreakers.locations:
            job_location = (job.get("location") or "").lower()
            if not any(loc.lower() in job_location for loc in dealbreakers.locations):
                if not ("remote" in job_location and dealbreakers.remote_only is False):
                    reasons.append(f"Location not in preferred: {job_location}")

        # Remote/onsite check
        job_location = (job.get("location") or "").lower()
        if dealbreakers.remote_only and "remote" not in job_location:
            reasons.append("Job is not remote")
        if dealbreakers.onsite_only and "remote" in job_location:
            reasons.append("Job is remote-only")

        # Excluded companies
        if dealbreakers.excluded_companies:
            company = (job.get("company") or "").lower()
            for excluded in dealbreakers.excluded_companies:
                if excluded.lower() in company:
                    reasons.append(f"Company excluded: {company}")
                    break

        # Excluded keywords
        if dealbreakers.excluded_keywords:
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            for keyword in dealbreakers.excluded_keywords:
                if keyword.lower() in job_text:
                    reasons.append(f"Contains excluded keyword: {keyword}")
                    break

        return len(reasons) == 0, reasons

    def _generate_reasoning(
        self,
        score: float,
        semantic_sim: float,
        skill_match_ratio: float,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> str:
        """Generate human-readable reasoning for the match score."""
        parts: list[str] = []

        if score >= 0.8:
            parts.append("Strong semantic match")
        elif score >= 0.6:
            parts.append("Good semantic match")
        else:
            parts.append("Moderate semantic match")

        if matched_skills:
            skills_str = ", ".join(matched_skills[:5])
            parts.append(f"matched skills: {skills_str}")

        if missing_skills and len(missing_skills) <= 3:
            parts.append(f"missing: {', '.join(missing_skills)}")

        return ". ".join(parts) + "."


class EmbeddingCacheRepo:
    """Repository for caching embeddings in the database."""

    @staticmethod
    async def get_job_embedding(
        conn: asyncpg.Connection,
        job_id: str,
    ) -> list[float] | None:
        """Retrieve cached job embedding."""
        row = await conn.fetchrow(
            "SELECT embedding FROM public.job_embeddings WHERE job_id = $1",
            job_id,
        )
        if row and row["embedding"]:
            return json.loads(row["embedding"])
        return None

    @staticmethod
    async def save_job_embedding(
        conn: asyncpg.Connection,
        job_id: str,
        embedding: list[float],
        text_hash: str,
    ) -> None:
        """Cache job embedding."""
        await conn.execute(
            """
            INSERT INTO public.job_embeddings (job_id, embedding, text_hash, created_at)
            VALUES ($1, $2::jsonb, $3, now())
            ON CONFLICT (job_id) DO UPDATE SET
                embedding = $2::jsonb,
                text_hash = $3,
                created_at = now()
            """,
            job_id,
            json.dumps(embedding),
            text_hash,
        )

    @staticmethod
    async def get_profile_embedding(
        conn: asyncpg.Connection,
        user_id: str,
    ) -> list[float] | None:
        """Retrieve cached profile embedding."""
        row = await conn.fetchrow(
            "SELECT embedding FROM public.profile_embeddings WHERE user_id = $1",
            user_id,
        )
        if row and row["embedding"]:
            return json.loads(row["embedding"])
        return None

    @staticmethod
    async def save_profile_embedding(
        conn: asyncpg.Connection,
        user_id: str,
        embedding: list[float],
        text_hash: str,
    ) -> None:
        """Cache profile embedding."""
        await conn.execute(
            """
            INSERT INTO public.profile_embeddings (user_id, embedding, text_hash, created_at)
            VALUES ($1, $2::jsonb, $3, now())
            ON CONFLICT (user_id) DO UPDATE SET
                embedding = $2::jsonb,
                text_hash = $3,
                created_at = now()
            """,
            user_id,
            json.dumps(embedding),
            text_hash,
        )


# Singleton service
_matching_service: SemanticMatchingService | None = None


def get_matching_service() -> SemanticMatchingService:
    """Get or create the singleton matching service."""
    global _matching_service
    if _matching_service is None:
        _matching_service = SemanticMatchingService()
    return _matching_service
