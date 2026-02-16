"""
Tests for the semantic matching and embedding services.

Validates the "Precision Matcher" archetype implementation.
"""

from __future__ import annotations

import pytest

from backend.domain.embeddings import (
    compute_text_hash,
    cosine_similarity,
    job_to_searchable_text,
    profile_to_searchable_text,
)
from backend.domain.semantic_matching import (
    Dealbreakers,
    MatchExplanation,
    SemanticMatchingService,
    SemanticMatchResult,
)


class TestCosineSimilarity:
    """Tests for cosine similarity computation."""

    def test_identical_vectors(self) -> None:
        """Identical vectors should have similarity 1.0."""
        vec = [1.0, 2.0, 3.0, 4.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0, rel=1e-6)

    def test_orthogonal_vectors(self) -> None:
        """Orthogonal vectors should have similarity 0.0."""
        vec_a = [1.0, 0.0]
        vec_b = [0.0, 1.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(0.0, rel=1e-6)

    def test_opposite_vectors(self) -> None:
        """Opposite vectors should have similarity -1.0."""
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(-1.0, rel=1e-6)

    def test_zero_vector(self) -> None:
        """Zero vector should return 0.0 similarity."""
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec_a, vec_b) == 0.0
        assert cosine_similarity(vec_b, vec_a) == 0.0

    def test_empty_vectors(self) -> None:
        """Empty vectors should return 0.0."""
        assert cosine_similarity([], []) == 0.0
        assert cosine_similarity([1.0], []) == 0.0

    def test_different_lengths(self) -> None:
        """Vectors of different lengths should return 0.0."""
        assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0


class TestProfileToSearchableText:
    """Tests for profile text conversion."""

    def test_basic_profile(self) -> None:
        """Basic profile should produce searchable text."""
        profile = {
            "current_title": "Software Engineer",
            "current_company": "TechCorp",
            "summary": "Experienced developer",
            "skills": {"technical": ["Python", "JavaScript"]},
        }
        text = profile_to_searchable_text(profile)
        assert "Software Engineer" in text
        assert "TechCorp" in text
        assert "Python" in text
        assert "JavaScript" in text

    def test_empty_profile(self) -> None:
        """Empty profile should produce empty text."""
        text = profile_to_searchable_text({})
        assert text.strip() == ""

    def test_profile_with_experience(self) -> None:
        """Profile with experience should include job details."""
        profile = {
            "experience": [
                {"title": "Senior Developer", "company": "BigCo"},
            ],
        }
        text = profile_to_searchable_text(profile)
        assert "Senior Developer" in text
        assert "BigCo" in text


class TestJobToSearchableText:
    """Tests for job text conversion."""

    def test_basic_job(self) -> None:
        """Basic job should produce searchable text."""
        job = {
            "title": "Python Developer",
            "company": "StartupXYZ",
            "location": "San Francisco, CA",
            "description": "Build scalable systems",
        }
        text = job_to_searchable_text(job)
        assert "Python Developer" in text
        assert "StartupXYZ" in text
        assert "San Francisco" in text
        assert "scalable systems" in text

    def test_job_truncates_description(self) -> None:
        """Long descriptions should be truncated."""
        job = {
            "title": "Engineer",
            "description": "x" * 5000,
        }
        text = job_to_searchable_text(job)
        # Description truncated to 2000 chars
        assert len(text) < 3000


class TestTextHash:
    """Tests for text hash computation."""

    def test_same_text_same_hash(self) -> None:
        """Same text should produce same hash."""
        hash1 = compute_text_hash("test content")
        hash2 = compute_text_hash("test content")
        assert hash1 == hash2

    def test_different_text_different_hash(self) -> None:
        """Different text should produce different hash."""
        hash1 = compute_text_hash("content A")
        hash2 = compute_text_hash("content B")
        assert hash1 != hash2

    def test_hash_length(self) -> None:
        """Hash should be 32 characters."""
        h = compute_text_hash("test")
        assert len(h) == 32


class TestDealbreakers:
    """Tests for dealbreaker model."""

    def test_default_values(self) -> None:
        """Default dealbreakers should be permissive."""
        d = Dealbreakers()
        assert d.min_salary is None
        assert d.max_salary is None
        assert d.locations == []
        assert d.remote_only is False
        assert d.visa_sponsorship_required is False

    def test_custom_values(self) -> None:
        """Custom values should be stored."""
        d = Dealbreakers(
            min_salary=100000,
            locations=["San Francisco", "New York"],
            remote_only=True,
        )
        assert d.min_salary == 100000
        assert len(d.locations) == 2
        assert d.remote_only is True


class TestSemanticMatchingService:
    """Tests for semantic matching service."""

    @pytest.fixture
    def service(self) -> SemanticMatchingService:
        """Create service without embedding client for unit tests."""
        return SemanticMatchingService(embedding_client=None)

    def test_experience_alignment_senior(
        self, service: SemanticMatchingService
    ) -> None:
        """Senior roles should align with experienced candidates."""
        alignment = service._compute_experience_alignment(7, "Senior Python Developer")
        assert alignment >= 0.8

    def test_experience_alignment_junior(
        self, service: SemanticMatchingService
    ) -> None:
        """Junior roles should align with less experienced candidates."""
        alignment = service._compute_experience_alignment(1, "Junior Developer")
        assert alignment >= 0.8

    def test_experience_alignment_mid(self, service: SemanticMatchingService) -> None:
        """Mid roles should align with moderate experience."""
        alignment = service._compute_experience_alignment(3, "Mid-level Engineer")
        assert alignment >= 0.5

    def test_check_dealbreakers_salary(self, service: SemanticMatchingService) -> None:
        """Jobs below minimum salary should fail."""
        job = {"salary_max": 80000}
        dealbreakers = Dealbreakers(min_salary=100000)
        passed, reasons = service._check_dealbreakers(job, dealbreakers)
        assert passed is False
        assert any("salary" in r.lower() for r in reasons)

    def test_check_dealbreakers_location(
        self, service: SemanticMatchingService
    ) -> None:
        """Jobs in wrong location should fail."""
        job = {"location": "New York, NY"}
        dealbreakers = Dealbreakers(locations=["San Francisco", "Seattle"])
        passed, reasons = service._check_dealbreakers(job, dealbreakers)
        assert passed is False
        assert any("location" in r.lower() for r in reasons)

    def test_check_dealbreakers_remote(self, service: SemanticMatchingService) -> None:
        """Non-remote jobs should fail remote_only filter."""
        job = {"location": "On-site in Austin, TX"}
        dealbreakers = Dealbreakers(remote_only=True)
        passed, reasons = service._check_dealbreakers(job, dealbreakers)
        assert passed is False

    def test_check_dealbreakers_excluded_company(
        self, service: SemanticMatchingService
    ) -> None:
        """Excluded companies should be filtered."""
        job = {"company": "BadCorp Inc"}
        dealbreakers = Dealbreakers(excluded_companies=["BadCorp"])
        passed, reasons = service._check_dealbreakers(job, dealbreakers)
        assert passed is False

    def test_check_dealbreakers_passes(self, service: SemanticMatchingService) -> None:
        """Jobs meeting all criteria should pass."""
        job = {
            "location": "Remote",
            "salary_min": 120000,
            "company": "GoodCorp",
        }
        dealbreakers = Dealbreakers(
            min_salary=100000,
            locations=["Remote"],
        )
        passed, reasons = service._check_dealbreakers(job, dealbreakers)
        assert passed is True
        assert reasons == []

    def test_generate_reasoning_high_score(
        self, service: SemanticMatchingService
    ) -> None:
        """High scores should indicate strong match."""
        reasoning = service._generate_reasoning(
            score=0.85,
            semantic_sim=0.9,
            skill_match_ratio=0.8,
            matched_skills=["Python", "Django"],
            missing_skills=[],
        )
        assert "Strong" in reasoning or "strong" in reasoning

    def test_generate_reasoning_with_gaps(
        self, service: SemanticMatchingService
    ) -> None:
        """Gaps should be mentioned in reasoning."""
        reasoning = service._generate_reasoning(
            score=0.6,
            semantic_sim=0.7,
            skill_match_ratio=0.5,
            matched_skills=["Python"],
            missing_skills=["Kubernetes", "AWS"],
        )
        assert "Kubernetes" in reasoning or "AWS" in reasoning


class TestMatchExplanation:
    """Tests for match explanation model."""

    def test_valid_scores(self) -> None:
        """Scores should be between 0 and 1."""
        exp = MatchExplanation(
            score=0.75,
            semantic_similarity=0.8,
            skill_match_ratio=0.6,
            experience_alignment=0.7,
        )
        assert 0 <= exp.score <= 1
        assert 0 <= exp.semantic_similarity <= 1

    def test_confidence_levels(self) -> None:
        """Confidence should be valid level."""
        for level in ["low", "medium", "high"]:
            exp = MatchExplanation(
                score=0.5,
                semantic_similarity=0.5,
                skill_match_ratio=0.5,
                experience_alignment=0.5,
                confidence=level,
            )
            assert exp.confidence == level


class TestSemanticMatchResult:
    """Tests for semantic match result model."""

    def test_result_structure(self) -> None:
        """Result should have all required fields."""
        result = SemanticMatchResult(
            job_id="test-job-id",
            score=0.8,
            explanation=MatchExplanation(
                score=0.8,
                semantic_similarity=0.85,
                skill_match_ratio=0.75,
                experience_alignment=0.8,
                reasoning="Good match",
            ),
        )
        assert result.job_id == "test-job-id"
        assert result.passed_dealbreakers is True
        assert result.dealbreaker_reasons == []
