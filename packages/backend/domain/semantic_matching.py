"""Semantic job matching service using vector embeddings.

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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.domain.vectordb import VectorDB

import asyncpg
from pydantic import BaseModel, Field

from backend.domain.embeddings import (
    EmbeddingClient,
    cosine_similarity,
    get_embedding_client,
    job_to_searchable_text,
    profile_to_searchable_text,
)
from shared.logging_config import get_logger

logger = get_logger("sorce.matching")


class MatchWeights(BaseModel):
    """Configurable weights for match scoring components."""

    semantic_similarity: float = Field(default=0.30, ge=0.0, le=1.0)
    skill_match: float = Field(default=0.25, ge=0.0, le=1.0)
    experience_alignment: float = Field(default=0.15, ge=0.0, le=1.0)
    work_style_fit: float = Field(default=0.18, ge=0.0, le=1.0)
    trajectory_alignment: float = Field(default=0.12, ge=0.0, le=1.0)

    def normalize(self) -> MatchWeights:
        """Normalize weights to sum to 1.0."""
        total = (
            self.semantic_similarity
            + self.skill_match
            + self.experience_alignment
            + self.work_style_fit
            + self.trajectory_alignment
        )
        if total == 0:
            return MatchWeights()
        return MatchWeights(
            semantic_similarity=self.semantic_similarity / total,
            skill_match=self.skill_match / total,
            experience_alignment=self.experience_alignment / total,
            work_style_fit=self.work_style_fit / total,
            trajectory_alignment=self.trajectory_alignment / total,
        )

    @classmethod
    def default(cls) -> MatchWeights:
        return cls(
            semantic_similarity=0.30,
            skill_match=0.25,
            experience_alignment=0.15,
            work_style_fit=0.18,
            trajectory_alignment=0.12,
        )


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
    work_style_fit: float = Field(default=0.7, ge=0.0, le=1.0)
    trajectory_alignment: float = Field(default=0.7, ge=0.0, le=1.0)
    location_compatible: bool = True
    salary_in_range: bool = True
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    skill_confidence_summary: dict[str, int] = Field(default_factory=dict)
    work_style_reasoning: str = ""
    trajectory_reasoning: str = ""
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
    """Service for semantic job-candidate matching.

    Uses vector embeddings to compute semantic similarity between
    job descriptions and candidate profiles, then applies dealbreaker
    filters and generates explainable scores.
    """

    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        weights: MatchWeights | None = None,
    ):
        self._embedding_client = embedding_client
        self._weights = weights or MatchWeights.default()

    @property
    def embeddings(self) -> EmbeddingClient:
        if self._embedding_client is None:
            self._embedding_client = get_embedding_client()
        return self._embedding_client

    @property
    def weights(self) -> MatchWeights:
        return self._weights

    @weights.setter
    def weights(self, value: MatchWeights) -> None:
        self._weights = value.normalize()

    async def compute_match_score(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
        dealbreakers: Dealbreakers | None = None,
        weights: MatchWeights | None = None,
        job_signals: dict[str, Any] | None = None,
        db_conn: asyncpg.Connection | None = None,
    ) -> SemanticMatchResult:
        """Compute semantic match score between profile and job.

        This is the core matching function that:
        1. Generates embeddings for profile and job
        2. Computes cosine similarity
        3. Applies skill matching with confidence weighting
        4. Computes work style fit (if signals available)
        5. Computes trajectory alignment (if signals available)
        6. Checks dealbreaker constraints
        7. Generates explainable reasoning

        Args:
            profile: CanonicalProfile or DeepProfile as dict
            job: Job dict with title, description, etc.
            dealbreakers: Optional user preferences
            weights: Optional custom weights (overrides instance weights)
            job_signals: Optional job signals from extraction

        Returns:
            SemanticMatchResult with score and explanation

        """
        dealbreakers = dealbreakers or Dealbreakers()
        effective_weights = (weights or self._weights).normalize()

        # Generate embeddings with cache integration
        profile_text = profile_to_searchable_text(profile)
        job_text = job_to_searchable_text(job)

        # HIGH: Integrate embedding cache to avoid regenerating embeddings
        import hashlib

        profile_text_hash = hashlib.sha256(profile_text.encode()).hexdigest()
        job_text_hash = hashlib.sha256(job_text.encode()).hexdigest()

        # Try to get cached embeddings if db connection is available
        profile_embedding = None
        job_embedding = None
        user_id = profile.get("user_id") or profile.get("id")
        job_id = job.get("id") or job.get("job_id")

        if db_conn:
            # Try to get cached job embedding
            if job_id:
                cached_job_embedding = await EmbeddingCacheRepo.get_job_embedding(
                    db_conn, job_id
                )
                if cached_job_embedding:
                    job_embedding = cached_job_embedding
                    logger.debug(f"Using cached job embedding for job {job_id}")

            # Try to get cached profile embedding
            if user_id and not profile_embedding:
                cached_profile_embedding = (
                    await EmbeddingCacheRepo.get_profile_embedding(db_conn, user_id)
                )
                if cached_profile_embedding:
                    profile_embedding = cached_profile_embedding
                    logger.debug(f"Using cached profile embedding for user {user_id}")

        # Generate embeddings if not cached
        if not profile_embedding:
            profile_embedding = await self.embeddings.embed_text(profile_text)
            # Cache profile embedding if db connection available
            if db_conn and user_id:
                try:
                    await EmbeddingCacheRepo.save_profile_embedding(
                        db_conn, user_id, profile_embedding, profile_text_hash
                    )
                except Exception as cache_error:
                    logger.warning(f"Failed to cache profile embedding: {cache_error}")

        if not job_embedding:
            job_embedding = await self.embeddings.embed_text(job_text)
            # Cache job embedding if db connection available
            if db_conn and job_id:
                try:
                    await EmbeddingCacheRepo.save_job_embedding(
                        db_conn, job_id, job_embedding, job_text_hash
                    )
                except Exception as cache_error:
                    logger.warning(f"Failed to cache job embedding: {cache_error}")

        # Compute semantic similarity
        semantic_sim = cosine_similarity(profile_embedding, job_embedding)

        # Extract skills from profile (handle both old and new format)
        profile_skills: set[str] = set()
        rich_skills: list[dict] = []
        skills_data = profile.get("skills", {})

        # Check if rich skills format (list of dicts)
        tech_skills = skills_data.get("technical", [])
        if tech_skills and isinstance(tech_skills[0], dict):
            # Rich skills format
            rich_skills = tech_skills + skills_data.get("soft", [])
            profile_skills = {
                s.get("skill", "").lower() for s in rich_skills if s.get("skill")
            }
        else:
            # Old format (list of strings). F005: guard against empty tech_skills
            if tech_skills and isinstance(tech_skills[0], str):
                profile_skills.update(tech_skills)
            profile_skills.update(skills_data.get("soft", []))
        profile_skills = {s.lower() for s in profile_skills if s}

        # Extract skills from job description
        job_text_lower = job_text.lower()
        matched_skills: list[str] = []
        missing_skills: list[str] = []
        skill_confidence_summary: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

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

        # Compute skill match ratio with confidence weighting
        skill_match_ratio = 0.5
        if matched_skills or missing_skills:
            # If we have rich skills, weight by confidence
            if rich_skills:
                skill_confidence_map = {
                    s.get("skill", "").lower(): s.get("confidence", 0.5)
                    for s in rich_skills
                }
                weighted_match = sum(
                    skill_confidence_map.get(s, 0.5) for s in matched_skills
                )
                total_possible = len(matched_skills) + len(missing_skills)
                skill_match_ratio = (
                    weighted_match / total_possible if total_possible > 0 else 0.5
                )

                # Count skills by confidence level
                for s in rich_skills:
                    conf = s.get("confidence", 0.5)
                    if conf >= 0.8:
                        skill_confidence_summary["high"] += 1
                    elif conf >= 0.5:
                        skill_confidence_summary["medium"] += 1
                    else:
                        skill_confidence_summary["low"] += 1
            else:
                skill_match_ratio = len(matched_skills) / len(
                    matched_skills + missing_skills
                )

        # Experience alignment (based on years)
        years_exp = profile.get("years_experience", 0) or 0
        exp_alignment = self._compute_experience_alignment(years_exp, job_text)

        # Work style fit (if job signals available)
        work_style_fit = 0.7
        work_style_reasoning = ""
        if job_signals:
            work_style = profile.get("work_style")
            if work_style:
                work_style_fit, work_style_reasoning = self._compute_work_style_fit(
                    work_style, job_signals
                )

        # Trajectory alignment (if job signals available)
        trajectory_alignment = 0.7
        trajectory_reasoning = ""
        if job_signals:
            trajectory = profile.get("trajectory", "open")
            trajectory_alignment, trajectory_reasoning = (
                self._compute_trajectory_alignment(trajectory, job_signals)
            )

        # Compute final score using configurable weights
        score = (
            semantic_sim * effective_weights.semantic_similarity
            + skill_match_ratio * effective_weights.skill_match
            + exp_alignment * effective_weights.experience_alignment
            + work_style_fit * effective_weights.work_style_fit
            + trajectory_alignment * effective_weights.trajectory_alignment
        )

        # Check dealbreakers
        passed, reasons = self._check_dealbreakers(job, dealbreakers)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            score=score,
            semantic_sim=semantic_sim,
            skill_match_ratio=skill_match_ratio,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            work_style_reasoning=work_style_reasoning,
            trajectory_reasoning=trajectory_reasoning,
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
                work_style_fit=work_style_fit,
                trajectory_alignment=trajectory_alignment,
                location_compatible=len(reasons) == 0
                or "location" not in " ".join(reasons).lower(),
                salary_in_range=len(reasons) == 0
                or "salary" not in " ".join(reasons).lower(),
                matched_skills=matched_skills[:10],
                missing_skills=missing_skills[:5],
                skill_confidence_summary=skill_confidence_summary,
                work_style_reasoning=work_style_reasoning,
                trajectory_reasoning=trajectory_reasoning,
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

    def _compute_work_style_fit(
        self,
        work_style: dict[str, Any],
        job_signals: dict[str, Any],
    ) -> tuple[float, str]:
        """Compute compatibility between candidate work style and job signals."""
        scores: list[float] = []
        reasoning_parts: list[str] = []

        # Company stage match
        pref = work_style.get("company_stage_preference", "flexible")
        if pref != "flexible" and job_signals.get("company_stage"):
            if pref == job_signals.get("company_stage"):
                scores.append(1.0)
                reasoning_parts.append(f"Company stage ({pref}) matches preference")
            else:
                scores.append(0.5)
                reasoning_parts.append("Company stage differs from preference")

        # Pace match
        pace_pref = work_style.get("pace_preference", "flexible")
        if pace_pref != "flexible" and job_signals.get("pace"):
            if pace_pref == job_signals.get("pace"):
                scores.append(1.0)
                reasoning_parts.append(f"Work pace ({pace_pref}) matches preference")
            else:
                scores.append(0.6)
                reasoning_parts.append("Work pace differs from preference")

        # Autonomy match
        auto_pref = work_style.get("autonomy_preference", "medium")
        if auto_pref != "medium" and job_signals.get("autonomy_level"):
            if auto_pref == job_signals.get("autonomy_level"):
                scores.append(1.0)
                reasoning_parts.append("Autonomy level matches preference")
            else:
                scores.append(0.5)

        # Communication style match (if remote culture detected)
        comm_pref = work_style.get("communication_style", "flexible")
        if comm_pref != "flexible" and job_signals.get("remote_culture"):
            matches = {
                ("async", "async_first"),
                ("sync", "onsite_culture"),
                ("mixed", "hybrid"),
            }
            if (comm_pref, job_signals.get("remote_culture")) in matches:
                scores.append(1.0)
                reasoning_parts.append("Communication style fits role")
            else:
                scores.append(0.6)

        score = sum(scores) / len(scores) if scores else 0.7
        reasoning = (
            "; ".join(reasoning_parts)
            if reasoning_parts
            else "No specific work style signals detected"
        )

        return score, reasoning

    def _compute_trajectory_alignment(
        self,
        trajectory: str,
        job_signals: dict[str, Any],
    ) -> tuple[float, str]:
        """Compute alignment between candidate's career trajectory and job's growth potential."""
        if trajectory == "open":
            return 0.7, "Open to any career path"

        growth = job_signals.get("growth_potential")
        if not growth:
            return 0.6, "Growth potential unclear"

        # Perfect matches
        perfect_matches = {
            ("ic", "ic_path"),
            ("tech_lead", "lead_path"),
            ("manager", "manager_path"),
        }

        if (trajectory, growth) in perfect_matches:
            return (
                1.0,
                f"Role offers {growth.replace('_', ' ')} matching your trajectory",
            )

        # Good matches (adjacent paths)
        good_matches = {
            ("ic", "lead_path"),
            ("tech_lead", "ic_path"),
            ("tech_lead", "manager_path"),
            ("manager", "lead_path"),
        }

        if (trajectory, growth) in good_matches:
            return 0.7, "Role offers growth toward your trajectory"

        # Limited growth is bad for ambitious trajectories
        if growth == "limited":
            if trajectory in ["tech_lead", "manager", "founder"]:
                return 0.3, "Limited growth potential for your trajectory"
            return 0.5, "Limited growth potential"

        return 0.5, "Trajectory alignment unclear"

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
        work_style_reasoning: str = "",
        trajectory_reasoning: str = "",
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

        if work_style_reasoning:
            parts.append(work_style_reasoning)

        if trajectory_reasoning:
            parts.append(trajectory_reasoning)

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


class VectorMatchRepo:
    """Repository for vector-based job matching using pgvector or external vector DB.

    This addresses recommendation #15: Use vector database for efficient
    similarity search instead of JSON-based storage.
    """

    def __init__(self, vectordb: VectorDB | None = None) -> None:
        self._vectordb = vectordb

    async def _get_vectordb(self, conn: asyncpg.Connection | None = None) -> VectorDB:
        """Get or initialize the vector database."""
        if self._vectordb is None:
            from backend.domain.vectordb import get_vectordb

            self._vectordb = await get_vectordb(conn=conn)
        return self._vectordb

    async def index_job(
        self,
        job_id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        """Index a job embedding for similarity search."""
        vectordb = await self._get_vectordb(conn)
        await vectordb.upsert(
            id=f"job:{job_id}",
            embedding=embedding,
            metadata=metadata or {},
            namespace="jobs",
        )

    async def index_profile(
        self,
        user_id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        """Index a profile embedding for similarity search."""
        vectordb = await self._get_vectordb(conn)
        await vectordb.upsert(
            id=f"profile:{user_id}",
            embedding=embedding,
            metadata=metadata or {},
            namespace="profiles",
        )

    async def find_similar_jobs(
        self,
        profile_embedding: list[float],
        top_k: int = 50,
        filters: dict[str, Any] | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        """Find jobs similar to a profile embedding."""
        vectordb = await self._get_vectordb(conn)
        results = await vectordb.search(
            query_embedding=profile_embedding,
            top_k=top_k,
            filters=filters,
            namespace="jobs",
        )
        # Strip "job:" prefix from IDs
        return [
            {
                "job_id": r["id"].replace("job:", "", 1),
                "score": r["score"],
                "metadata": r["metadata"],
            }
            for r in results
        ]

    async def find_similar_profiles(
        self,
        job_embedding: list[float],
        top_k: int = 50,
        filters: dict[str, Any] | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        """Find profiles similar to a job embedding."""
        vectordb = await self._get_vectordb(conn)
        results = await vectordb.search(
            query_embedding=job_embedding,
            top_k=top_k,
            filters=filters,
            namespace="profiles",
        )
        # Strip "profile:" prefix from IDs
        return [
            {
                "user_id": r["id"].replace("profile:", "", 1),
                "score": r["score"],
                "metadata": r["metadata"],
            }
            for r in results
        ]

    async def remove_job(
        self,
        job_id: str,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        """Remove a job from the vector index."""
        vectordb = await self._get_vectordb(conn)
        await vectordb.delete(id=f"job:{job_id}", namespace="jobs")

    async def remove_profile(
        self,
        user_id: str,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        """Remove a profile from the vector index."""
        vectordb = await self._get_vectordb(conn)
        await vectordb.delete(id=f"profile:{user_id}", namespace="profiles")


# Singleton service
_matching_service: SemanticMatchingService | None = None
_vector_match_repo: VectorMatchRepo | None = None


def get_matching_service() -> SemanticMatchingService:
    """Get or create the singleton matching service."""
    global _matching_service
    if _matching_service is None:
        _matching_service = SemanticMatchingService()
    return _matching_service


def get_vector_match_repo() -> VectorMatchRepo:
    """Get or create the singleton vector match repository."""
    global _vector_match_repo
    if _vector_match_repo is None:
        _vector_match_repo = VectorMatchRepo()
    return _vector_match_repo
