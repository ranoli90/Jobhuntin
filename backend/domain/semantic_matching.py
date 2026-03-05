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

    def _extract_profile_skills(
        self, profile: dict[str, Any]
    ) -> tuple[set[str], list[dict]]:
        """Extract skills from profile, handling both old and new formats."""
        profile_skills: set[str] = set()
        rich_skills: list[dict] = []
        skills_data = profile.get("skills", {})

        tech_skills = skills_data.get("technical", [])
        if tech_skills and isinstance(tech_skills[0], dict):
            rich_skills = tech_skills + skills_data.get("soft", [])
            profile_skills = {
                s.get("skill", "").lower() for s in rich_skills if s.get("skill")
            }
        else:
            profile_skills.update(
                tech_skills if isinstance(tech_skills[0], str) else []
            )
            profile_skills.update(skills_data.get("soft", []))

        return {s.lower() for s in profile_skills if s}, rich_skills

    def _match_skills_against_job(
        self, profile_skills: set[str], job_text_lower: str
    ) -> tuple[list[str], list[str]]:
        """Match profile skills against common skills found in job text."""
        matched: list[str] = []
        missing: list[str] = []

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
                    matched.append(skill)
                else:
                    missing.append(skill)

        return matched, missing

    def _compute_skill_match_ratio(
        self,
        matched_skills: list[str],
        missing_skills: list[str],
        rich_skills: list[dict],
    ) -> tuple[float, dict[str, int]]:
        """Compute skill match ratio with confidence weighting."""
        skill_confidence_summary: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

        if not matched_skills and not missing_skills:
            return 0.5, skill_confidence_summary

        if not rich_skills:
            total = len(matched_skills) + len(missing_skills)
            return (
                len(matched_skills) / total if total > 0 else 0.5
            ), skill_confidence_summary

        skill_confidence_map = {
            s.get("skill", "").lower(): s.get("confidence", 0.5) for s in rich_skills
        }
        weighted_match = sum(skill_confidence_map.get(s, 0.5) for s in matched_skills)
        total_possible = len(matched_skills) + len(missing_skills)
        ratio = weighted_match / total_possible if total_possible > 0 else 0.5

        for s in rich_skills:
            conf = s.get("confidence", 0.5)
            if conf >= 0.8:
                skill_confidence_summary["high"] += 1
            elif conf >= 0.5:
                skill_confidence_summary["medium"] += 1
            else:
                skill_confidence_summary["low"] += 1

        return ratio, skill_confidence_summary

    def _compute_job_signal_scores(
        self, profile: dict[str, Any], job_signals: dict[str, Any] | None
    ) -> tuple[float, str, float, str]:
        """Compute work style fit and trajectory alignment from job signals."""
        work_style_fit, work_style_reasoning = 0.7, ""
        trajectory_alignment, trajectory_reasoning = 0.7, ""

        if job_signals:
            work_style = profile.get("work_style")
            if work_style:
                work_style_fit, work_style_reasoning = self._compute_work_style_fit(
                    work_style, job_signals
                )

            trajectory = profile.get("trajectory", "open")
            trajectory_alignment, trajectory_reasoning = (
                self._compute_trajectory_alignment(trajectory, job_signals)
            )

        return (
            work_style_fit,
            work_style_reasoning,
            trajectory_alignment,
            trajectory_reasoning,
        )

    def _build_match_result(
        self,
        job: dict[str, Any],
        score: float,
        semantic_sim: float,
        skill_match_ratio: float,
        exp_alignment: float,
        work_style_fit: float,
        trajectory_alignment: float,
        matched_skills: list[str],
        missing_skills: list[str],
        skill_confidence_summary: dict[str, int],
        work_style_reasoning: str,
        trajectory_reasoning: str,
        reasoning: str,
        passed: bool,
        reasons: list[str],
    ) -> SemanticMatchResult:
        """Build the final semantic match result."""
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

    async def compute_match_score(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
        dealbreakers: Dealbreakers | None = None,
        weights: MatchWeights | None = None,
        job_signals: dict[str, Any] | None = None,
    ) -> SemanticMatchResult:
        """Compute semantic match score between profile and job."""
        dealbreakers = dealbreakers or Dealbreakers()
        effective_weights = (weights or self._weights).normalize()

        profile_text = profile_to_searchable_text(profile)
        job_text = job_to_searchable_text(job)

        profile_embedding = await self.embeddings.embed_text(profile_text)
        job_embedding = await self.embeddings.embed_text(job_text)

        semantic_sim = cosine_similarity(profile_embedding, job_embedding)

        profile_skills, rich_skills = self._extract_profile_skills(profile)
        job_text_lower = job_text.lower()
        matched_skills, missing_skills = self._match_skills_against_job(
            profile_skills, job_text_lower
        )

        skill_match_ratio, skill_confidence_summary = self._compute_skill_match_ratio(
            matched_skills, missing_skills, rich_skills
        )

        years_exp = profile.get("years_experience", 0) or 0
        exp_alignment = self._compute_experience_alignment(years_exp, job_text)

        (
            work_style_fit,
            work_style_reasoning,
            trajectory_alignment,
            trajectory_reasoning,
        ) = self._compute_job_signal_scores(profile, job_signals)

        score = (
            semantic_sim * effective_weights.semantic_similarity
            + skill_match_ratio * effective_weights.skill_match
            + exp_alignment * effective_weights.experience_alignment
            + work_style_fit * effective_weights.work_style_fit
            + trajectory_alignment * effective_weights.trajectory_alignment
        )

        passed, reasons = self._check_dealbreakers(job, dealbreakers)

        reasoning = self._generate_reasoning(
            score=score,
            semantic_sim=semantic_sim,
            skill_match_ratio=skill_match_ratio,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            work_style_reasoning=work_style_reasoning,
            trajectory_reasoning=trajectory_reasoning,
        )

        return self._build_match_result(
            job=job,
            score=score,
            semantic_sim=semantic_sim,
            skill_match_ratio=skill_match_ratio,
            exp_alignment=exp_alignment,
            work_style_fit=work_style_fit,
            trajectory_alignment=trajectory_alignment,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            skill_confidence_summary=skill_confidence_summary,
            work_style_reasoning=work_style_reasoning,
            trajectory_reasoning=trajectory_reasoning,
            reasoning=reasoning,
            passed=passed,
            reasons=reasons,
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

    def _check_salary_dealbreaker(
        self, job: dict[str, Any], min_salary: int | None
    ) -> str | None:
        """Check if job salary meets minimum requirement."""
        if not min_salary:
            return None
        job_max = job.get("salary_max") or job.get("salary_min", 0)
        if job_max and job_max < min_salary:
            return f"Salary below minimum: {job_max} < {min_salary}"
        return None

    def _check_location_dealbreaker(
        self, job: dict[str, Any], dealbreakers: Dealbreakers
    ) -> str | None:
        """Check if job location matches preferences."""
        if not dealbreakers.locations:
            return None
        job_location = (job.get("location") or "").lower()
        if any(loc.lower() in job_location for loc in dealbreakers.locations):
            return None
        if "remote" in job_location and dealbreakers.remote_only is False:
            return None
        return f"Location not in preferred: {job_location}"

    def _check_remote_onsite_dealbreaker(
        self, job: dict[str, Any], dealbreakers: Dealbreakers
    ) -> str | None:
        """Check remote/onsite preferences."""
        job_location = (job.get("location") or "").lower()
        if dealbreakers.remote_only and "remote" not in job_location:
            return "Job is not remote"
        if dealbreakers.onsite_only and "remote" in job_location:
            return "Job is remote-only"
        return None

    def _check_excluded_companies(
        self, job: dict[str, Any], excluded_companies: list[str]
    ) -> str | None:
        """Check if company is in excluded list."""
        if not excluded_companies:
            return None
        company = (job.get("company") or "").lower()
        for excluded in excluded_companies:
            if excluded.lower() in company:
                return f"Company excluded: {company}"
        return None

    def _check_excluded_keywords(
        self, job: dict[str, Any], excluded_keywords: list[str]
    ) -> str | None:
        """Check if job contains excluded keywords."""
        if not excluded_keywords:
            return None
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        for keyword in excluded_keywords:
            if keyword.lower() in job_text:
                return f"Contains excluded keyword: {keyword}"
        return None

    def _check_dealbreakers(
        self,
        job: dict[str, Any],
        dealbreakers: Dealbreakers,
    ) -> tuple[bool, list[str]]:
        """Check if job passes all dealbreaker constraints."""
        reasons: list[str] = []

        checks = [
            self._check_salary_dealbreaker(job, dealbreakers.min_salary),
            self._check_location_dealbreaker(job, dealbreakers),
            self._check_remote_onsite_dealbreaker(job, dealbreakers),
            self._check_excluded_companies(job, dealbreakers.excluded_companies),
            self._check_excluded_keywords(job, dealbreakers.excluded_keywords),
        ]

        for reason in checks:
            if reason:
                reasons.append(reason)

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
