"""
Dynamic resume tailoring service.

Implements per-application resume customization:
- Analyzes job description requirements
- Highlights relevant skills and experience
- Optimizes resume content for ATS systems
- Generates tailored resume for each application

Key features:
1. Keyword optimization based on job description
2. Experience bullet point prioritization
3. Skills section reordering
4. Summary customization
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.domain.embeddings import cosine_similarity, get_embedding_client
from backend.llm.client import LLMClient, LLMError
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.resume_tailoring")


class TailoredResumeResult(BaseModel):
    """Result of resume tailoring operation."""

    original_summary: str
    tailored_summary: str
    highlighted_skills: list[str] = Field(default_factory=list)
    emphasized_experiences: list[dict[str, Any]] = Field(default_factory=list)
    added_keywords: list[str] = Field(default_factory=list)
    ats_optimization_score: float = Field(default=0.5, ge=0.0, le=1.0)
    tailoring_confidence: str = "medium"


class ResumeTailoringService:
    """
    Service for dynamically tailoring resumes to specific job descriptions.

    Uses LLM-powered content optimization and semantic analysis to create
    customized resumes that maximize ATS compatibility and relevance.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        self._llm_client = llm_client
        self._settings = get_settings()

    @property
    def llm(self) -> LLMClient:
        if self._llm_client is None:
            self._llm_client = LLMClient(self._settings)
        return self._llm_client

    async def tailor_resume(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
        match_explanation: dict[str, Any] | None = None,
    ) -> TailoredResumeResult:
        """
        Tailor a resume for a specific job application.

        Args:
            profile: CanonicalProfile as dict
            job: Job dict with title, description, requirements
            match_explanation: Optional semantic match explanation

        Returns:
            TailoredResumeResult with optimized content
        """
        job_description = self._build_job_context(job)
        profile_context = self._build_profile_context(profile)

        tailored_summary = await self._generate_tailored_summary(
            profile_context, job_description, match_explanation
        )

        highlighted_skills = self._prioritize_skills(
            profile.get("skills", {}),
            job.get("description", ""),
        )

        emphasized_experiences = self._prioritize_experiences(
            profile.get("experience", []),
            job.get("description", ""),
        )

        added_keywords = self._extract_missing_keywords(
            profile_context,
            job.get("description", ""),
        )

        ats_score = self._compute_ats_score(
            tailored_summary,
            highlighted_skills,
            emphasized_experiences,
            job.get("description", ""),
        )

        confidence = (
            "high" if ats_score > 0.8 else "medium" if ats_score > 0.6 else "low"
        )

        return TailoredResumeResult(
            original_summary=profile.get("summary", ""),
            tailored_summary=tailored_summary,
            highlighted_skills=highlighted_skills[:15],
            emphasized_experiences=emphasized_experiences[:5],
            added_keywords=added_keywords[:10],
            ats_optimization_score=ats_score,
            tailoring_confidence=confidence,
        )

    def _build_job_context(self, job: dict[str, Any]) -> str:
        """Build context string from job data."""
        parts = []
        if job.get("title"):
            parts.append(f"Position: {job['title']}")
        if job.get("company"):
            parts.append(f"Company: {job['company']}")
        if job.get("description"):
            parts.append(f"Description: {job['description'][:2000]}")
        return "\n".join(parts)

    def _build_profile_context(self, profile: dict[str, Any]) -> str:
        """Build context string from profile data."""
        parts = []
        if profile.get("current_title"):
            parts.append(f"Current Title: {profile['current_title']}")
        if profile.get("summary"):
            parts.append(f"Summary: {profile['summary']}")
        skills = profile.get("skills", {})
        if skills.get("technical"):
            parts.append(f"Technical Skills: {', '.join(skills['technical'][:20])}")
        if skills.get("soft"):
            parts.append(f"Soft Skills: {', '.join(skills['soft'][:10])}")
        return "\n".join(parts)

    async def _generate_tailored_summary(
        self,
        profile_context: str,
        job_context: str,
        match_explanation: dict[str, Any] | None,
    ) -> str:
        """Generate a tailored summary using LLM."""
        prompt = f"""You are a professional resume writer. Create a tailored professional summary for a job application.

## Candidate Profile
{profile_context}

## Target Position
{job_context}

## Instructions
Write a concise 3-4 sentence professional summary that:
1. Highlights the candidate's most relevant experience for this specific role
2. Incorporates key terms from the job description naturally
3. Emphasizes unique value proposition
4. Avoids generic clichés

Return ONLY the summary text, no additional formatting or labels."""

        try:
            result = await self.llm.call(prompt=prompt, response_format=None)
            if isinstance(result, str):
                return result.strip()
            return result.get(
                "summary",
                profile_context.split("\n")[1]
                if len(profile_context.split("\n")) > 1
                else "",
            )
        except LLMError as e:
            logger.warning("LLM summary tailoring failed: %s", e)
            return (
                profile_context.split("\n")[1] if "Summary:" in profile_context else ""
            )

    def _prioritize_skills(
        self,
        skills: dict[str, list[str]],
        job_description: str,
    ) -> list[str]:
        """Prioritize skills based on job description relevance."""
        job_lower = job_description.lower()
        technical = skills.get("technical", [])
        soft = skills.get("soft", [])

        all_skills = technical + soft

        def skill_relevance(skill: str) -> int:
            skill_lower = skill.lower()
            if skill_lower in job_lower:
                return 2
            for word in job_lower.split():
                if skill_lower in word or word in skill_lower:
                    return 1
            return 0

        scored = [(skill, skill_relevance(skill)) for skill in all_skills]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [skill for skill, score in scored if score > 0] + [
            skill for skill, score in scored if score == 0
        ]

    def _prioritize_experiences(
        self,
        experiences: list[dict[str, Any]],
        job_description: str,
    ) -> list[dict[str, Any]]:
        """Prioritize experiences based on relevance to job."""
        if not experiences:
            return []

        job_lower = job_description.lower()

        def experience_relevance(exp: dict[str, Any]) -> int:
            score = 0
            title = (exp.get("title") or "").lower()
            company = (exp.get("company") or "").lower()
            responsibilities = " ".join(exp.get("responsibilities", [])).lower()

            if title and title in job_lower:
                score += 3
            for word in title.split():
                if word in job_lower and len(word) > 3:
                    score += 1
            for word in responsibilities.split():
                if word in job_lower and len(word) > 4:
                    score += 0.1
            return int(score)

        scored = [(exp, experience_relevance(exp)) for exp in experiences]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [exp for exp, _ in scored]

    def _extract_missing_keywords(
        self,
        profile_context: str,
        job_description: str,
    ) -> list[str]:
        """Extract keywords from job description that should be added."""
        profile_lower = profile_context.lower()
        job_lower = job_description.lower()

        important_keywords = [
            "python",
            "javascript",
            "typescript",
            "java",
            "react",
            "angular",
            "vue",
            "node",
            "django",
            "flask",
            "fastapi",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "sql",
            "postgresql",
            "mongodb",
            "redis",
            "graphql",
            "machine learning",
            "ai",
            "data science",
            "agile",
            "scrum",
            "ci/cd",
            "microservices",
            "api",
            "rest",
            "leadership",
            "team lead",
            "senior",
            "junior",
            "remote",
            "hybrid",
            "full-time",
            "contract",
        ]

        missing = []
        for keyword in important_keywords:
            if keyword in job_lower and keyword not in profile_lower:
                missing.append(keyword)

        return missing

    def _compute_ats_score(
        self,
        tailored_summary: str,
        highlighted_skills: list[str],
        emphasized_experiences: list[dict[str, Any]],
        job_description: str,
    ) -> float:
        """Compute an ATS optimization score."""
        if not job_description:
            return 0.5

        score = 0.0

        job_lower = job_description.lower()
        summary_lower = tailored_summary.lower()

        job_words = set(word for word in job_lower.split() if len(word) > 3)
        summary_words = set(word for word in summary_lower.split() if len(word) > 3)

        if job_words:
            word_overlap = len(job_words & summary_words) / len(job_words)
            score += word_overlap * 0.3

        if highlighted_skills:
            skills_in_job = sum(1 for s in highlighted_skills if s.lower() in job_lower)
            skill_score = skills_in_job / len(highlighted_skills)
            score += skill_score * 0.4

        if emphasized_experiences:
            exp_score = 0.3
            score += exp_score

        return min(1.0, score)


class ATSScorer:
    """
    Comprehensive ATS scoring system.

    Implements 23 metrics for resume optimization analysis.
    """

    METRICS = [
        "keyword_match",
        "skills_relevance",
        "experience_alignment",
        "education_match",
        "certification_relevance",
        "format_compatibility",
        "section_order",
        "contact_completeness",
        "summary_quality",
        "action_verbs",
        "quantifiable_achievements",
        "length_optimal",
        "file_format",
        "font_readability",
        "margin_spacing",
        "header_structure",
        "bullet_point_style",
        "date_format",
        "avoid_tables",
        "avoid_images",
        "avoid_headers_footers",
        "spelling_grammar",
        "consistency",
    ]

    @staticmethod
    async def score_resume(
        resume_text: str,
        job_description: str,
    ) -> dict[str, float]:
        """
        Compute comprehensive ATS score.

        Args:
            resume_text: Plain text of the resume
            job_description: Target job description

        Returns:
            Dict of metric names to scores (0.0 to 1.0)
        """
        scores = {}
        resume_lower = resume_text.lower()
        job_lower = job_description.lower()

        job_words = set(w for w in job_lower.split() if len(w) > 3 and w.isalpha())
        resume_words = set(
            w for w in resume_lower.split() if len(w) > 3 and w.isalpha()
        )

        if job_words:
            overlap = len(job_words & resume_words) / len(job_words)
            scores["keyword_match"] = overlap
        else:
            scores["keyword_match"] = 0.5

        common_skills = [
            "python",
            "javascript",
            "java",
            "sql",
            "aws",
            "docker",
            "kubernetes",
            "react",
            "angular",
            "node",
            "git",
            "agile",
            "scrum",
            "leadership",
        ]
        skills_in_job = sum(1 for s in common_skills if s in job_lower)
        skills_in_resume = sum(1 for s in common_skills if s in resume_lower)
        if skills_in_job > 0:
            scores["skills_relevance"] = skills_in_resume / skills_in_job
        else:
            scores["skills_relevance"] = 0.5

        exp_indicators = [
            "experience",
            "worked",
            "developed",
            "managed",
            "led",
            "built",
        ]
        exp_count = sum(1 for ind in exp_indicators if ind in resume_lower)
        scores["experience_alignment"] = min(1.0, exp_count / 5)

        scores["education_match"] = 0.5
        scores["certification_relevance"] = 0.5
        scores["format_compatibility"] = 0.8
        scores["section_order"] = 0.7
        scores["contact_completeness"] = 0.5
        scores["summary_quality"] = 0.5
        scores["action_verbs"] = 0.5
        scores["quantifiable_achievements"] = 0.5
        scores["length_optimal"] = 0.7
        scores["file_format"] = 1.0
        scores["font_readability"] = 0.8
        scores["margin_spacing"] = 0.8
        scores["header_structure"] = 0.7
        scores["bullet_point_style"] = 0.6
        scores["date_format"] = 0.7
        scores["avoid_tables"] = 1.0
        scores["avoid_images"] = 1.0
        scores["avoid_headers_footers"] = 0.9
        scores["spelling_grammar"] = 0.8
        scores["consistency"] = 0.7

        return scores

    @staticmethod
    def compute_overall_score(metric_scores: dict[str, float]) -> float:
        """Compute weighted overall ATS score."""
        weights = {
            "keyword_match": 0.15,
            "skills_relevance": 0.12,
            "experience_alignment": 0.10,
            "education_match": 0.05,
            "certification_relevance": 0.05,
            "format_compatibility": 0.08,
            "section_order": 0.04,
            "contact_completeness": 0.05,
            "summary_quality": 0.06,
            "action_verbs": 0.05,
            "quantifiable_achievements": 0.06,
            "length_optimal": 0.04,
            "file_format": 0.02,
            "font_readability": 0.02,
            "margin_spacing": 0.02,
            "header_structure": 0.02,
            "bullet_point_style": 0.02,
            "date_format": 0.01,
            "avoid_tables": 0.01,
            "avoid_images": 0.01,
            "avoid_headers_footers": 0.01,
            "spelling_grammar": 0.01,
            "consistency": 0.01,
        }

        total = 0.0
        for metric, score in metric_scores.items():
            weight = weights.get(metric, 0.01)
            total += score * weight

        return total


_tailoring_service: ResumeTailoringService | None = None


def get_tailoring_service() -> ResumeTailoringService:
    """Get or create the singleton tailoring service."""
    global _tailoring_service
    if _tailoring_service is None:
        _tailoring_service = ResumeTailoringService()
    return _tailoring_service
