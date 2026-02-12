"""
Tests for the resume tailoring service.

Validates dynamic resume customization and ATS scoring.
"""

from __future__ import annotations

import pytest

from backend.domain.resume_tailoring import (
    ATSScorer,
    ResumeTailoringService,
    TailoredResumeResult,
)


class TestResumeTailoringService:
    """Tests for resume tailoring service."""

    @pytest.fixture
    def service(self) -> ResumeTailoringService:
        """Create service without LLM client for unit tests."""
        return ResumeTailoringService(llm_client=None)

    def test_prioritize_skills_match(self, service: ResumeTailoringService) -> None:
        """Skills in job description should be prioritized."""
        skills = {
            "technical": ["Python", "JavaScript", "Docker", "PostgreSQL"],
            "soft": ["Leadership", "Communication"],
        }
        job_description = "Looking for a Python developer with Docker experience"
        result = service._prioritize_skills(skills, job_description)

        assert "python" in [s.lower() for s in result[:2]]
        assert "docker" in [s.lower() for s in result[:2]]

    def test_prioritize_skills_no_match(self, service: ResumeTailoringService) -> None:
        """Skills not in job should still be included."""
        skills = {
            "technical": ["Rust", "Go"],
            "soft": ["Teamwork"],
        }
        job_description = "Looking for a Python developer"
        result = service._prioritize_skills(skills, job_description)

        assert "Rust" in result
        assert "Go" in result

    def test_prioritize_experiences_relevant(
        self, service: ResumeTailoringService
    ) -> None:
        """Experiences relevant to job should be prioritized."""
        experiences = [
            {"title": "Senior Python Developer", "company": "TechCorp"},
            {"title": "Marketing Intern", "company": "AdAgency"},
        ]
        job_description = "Senior Python Engineer role"
        result = service._prioritize_experiences(experiences, job_description)

        assert result[0].get("title") == "Senior Python Developer"

    def test_prioritize_experiences_empty(
        self, service: ResumeTailoringService
    ) -> None:
        """Empty experience list should return empty."""
        result = service._prioritize_experiences([], "job description")
        assert result == []

    def test_extract_missing_keywords(self, service: ResumeTailoringService) -> None:
        """Keywords in job but not profile should be identified."""
        profile_context = "Python developer with Django experience"
        job_description = "Python developer with Django and Kubernetes experience"
        result = service._extract_missing_keywords(profile_context, job_description)

        assert "kubernetes" in result

    def test_compute_ats_score_high_match(
        self, service: ResumeTailoringService
    ) -> None:
        """High relevance should yield high ATS score."""
        summary = "Senior Python Developer with Django, AWS, and Docker expertise"
        skills = ["Python", "Django", "AWS", "Docker", "PostgreSQL"]
        experiences = [{"title": "Senior Developer"}]
        job_description = "Looking for Senior Python Developer with AWS and Docker"

        score = service._compute_ats_score(
            summary, skills, experiences, job_description
        )
        assert score >= 0.5

    def test_compute_ats_score_low_match(self, service: ResumeTailoringService) -> None:
        """Low relevance should yield lower ATS score."""
        summary = "Marketing professional with brand strategy expertise"
        skills = ["Marketing", "Branding", "Social Media"]
        experiences = [{"title": "Marketing Manager"}]
        job_description = "Senior Python Developer with AWS and Kubernetes"

        score = service._compute_ats_score(
            summary, skills, experiences, job_description
        )
        assert score < 0.7

    def test_build_job_context(self, service: ResumeTailoringService) -> None:
        """Job context should include key fields."""
        job = {
            "title": "Python Developer",
            "company": "TechCorp",
            "description": "Build scalable systems",
        }
        result = service._build_job_context(job)

        assert "Python Developer" in result
        assert "TechCorp" in result
        assert "scalable systems" in result

    def test_build_profile_context(self, service: ResumeTailoringService) -> None:
        """Profile context should include key fields."""
        profile = {
            "current_title": "Software Engineer",
            "summary": "Experienced developer",
            "skills": {"technical": ["Python", "Django"]},
        }
        result = service._build_profile_context(profile)

        assert "Software Engineer" in result
        assert "Python" in result


class TestTailoredResumeResult:
    """Tests for tailored resume result model."""

    def test_default_values(self) -> None:
        """Default values should be set correctly."""
        result = TailoredResumeResult(
            original_summary="Original",
            tailored_summary="Tailored",
        )
        assert result.highlighted_skills == []
        assert result.emphasized_experiences == []
        assert result.added_keywords == []
        assert result.ats_optimization_score >= 0
        assert result.tailoring_confidence == "medium"

    def test_custom_values(self) -> None:
        """Custom values should be stored."""
        result = TailoredResumeResult(
            original_summary="Original",
            tailored_summary="Tailored",
            highlighted_skills=["Python", "Django"],
            emphasized_experiences=[{"title": "Senior Dev"}],
            added_keywords=["AWS"],
            ats_optimization_score=0.85,
            tailoring_confidence="high",
        )
        assert result.highlighted_skills == ["Python", "Django"]
        assert result.ats_optimization_score == 0.85
        assert result.tailoring_confidence == "high"


class TestATSScorer:
    """Tests for ATS scoring system."""

    @pytest.mark.asyncio
    async def test_score_resume_basic(self) -> None:
        """Basic ATS score should be computed."""
        resume = """
        John Doe
        Senior Python Developer
        
        Experience:
        - Developed web applications using Python and Django
        - Managed AWS infrastructure
        - Led team of 5 developers
        
        Skills: Python, Django, AWS, Docker, PostgreSQL
        """
        job = "Looking for Python Developer with AWS and Django experience"

        scores = await ATSScorer.score_resume(resume, job)

        assert "keyword_match" in scores
        assert "skills_relevance" in scores
        assert 0 <= scores["keyword_match"] <= 1

    @pytest.mark.asyncio
    async def test_score_resume_empty(self) -> None:
        """Empty resume should return default scores."""
        scores = await ATSScorer.score_resume("", "job description")

        assert scores["keyword_match"] >= 0
        assert scores["skills_relevance"] >= 0

    def test_compute_overall_score(self) -> None:
        """Overall score should be weighted average."""
        metric_scores = {
            "keyword_match": 0.8,
            "skills_relevance": 0.9,
            "experience_alignment": 0.7,
            "format_compatibility": 0.9,
        }
        for metric in ATSScorer.METRICS:
            if metric not in metric_scores:
                metric_scores[metric] = 0.5

        overall = ATSScorer.compute_overall_score(metric_scores)

        assert 0 <= overall <= 1

    def test_metrics_count(self) -> None:
        """Should have 23 metrics."""
        assert len(ATSScorer.METRICS) == 23

    @pytest.mark.asyncio
    async def test_keyword_matching(self) -> None:
        """Keywords from job should be detected."""
        resume = "Python JavaScript React AWS Docker"
        job = "Python Developer with React and AWS"

        scores = await ATSScorer.score_resume(resume, job)

        assert scores["keyword_match"] > 0.3

    @pytest.mark.asyncio
    async def test_skills_detection(self) -> None:
        """Technical skills should be detected."""
        resume = "Skills: Python, JavaScript, Docker, AWS"
        job = "Looking for Python, Docker, AWS skills"

        scores = await ATSScorer.score_resume(resume, job)

        assert scores["skills_relevance"] > 0.5
