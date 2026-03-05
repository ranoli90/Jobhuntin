"""Tests for AI suggestion endpoints.

Tests the fixed function signatures and prompt building logic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

# Import the modules we fixed
from backend.llm.contracts import (
    JobMatchScore_V1,
    LocationSuggestionResponse_V1,
    OnboardingQuestionsResponse_V1,
    RoleSuggestionResponse_V1,
    SalarySuggestionResponse_V1,
    build_job_match_prompt,
    build_location_suggestion_prompt,
    build_onboarding_questions_prompt,
    build_role_suggestion_prompt,
    build_salary_suggestion_prompt,
)


class TestPromptBuilders:
    """Test the fixed prompt builder functions."""

    def test_build_role_suggestion_prompt(self) -> None:
        """Test role suggestion prompt builder with correct signature."""
        resume_text = "Experienced software engineer with 5 years experience..."
        skills = ["Python", "JavaScript", "React"]
        experience_years = 5
        education_level = "bachelor"

        prompt = build_role_suggestion_prompt(
            resume_text=resume_text,
            skills=skills,
            experience_years=experience_years,
            education_level=education_level,
        )

        # Verify prompt contains expected content
        assert resume_text in prompt
        assert "Python" in prompt
        assert "JavaScript" in prompt
        assert "React" in prompt
        assert "5" in prompt
        assert "bachelor" in prompt
        assert "suggested_roles" in prompt
        assert "primary_role" in prompt
        assert "confidence" in prompt

    def test_build_salary_suggestion_prompt(self) -> None:
        """Test salary suggestion prompt builder with correct signature."""
        skills = ["Python", "React", "AWS"]
        experience_years = 5
        education_level = "bachelor"
        target_role = "Software Engineer"
        location = "San Francisco, CA"

        prompt = build_salary_suggestion_prompt(
            skills=skills,
            experience_years=experience_years,
            education_level=education_level,
            target_role=target_role,
            location=location,
        )

        # Verify prompt contains expected content
        assert "Python" in prompt
        assert "React" in prompt
        assert "AWS" in prompt
        assert "5" in prompt
        assert "bachelor" in prompt
        assert "Software Engineer" in prompt
        assert "San Francisco" in prompt
        assert "min_salary" in prompt
        assert "max_salary" in prompt
        assert "market_median" in prompt

    def test_build_location_suggestion_prompt(self) -> None:
        """Test location suggestion prompt builder with correct signature."""
        skills = ["Python", "React"]
        role = "Software Engineer"
        experience_years = 3
        remote_preference = True

        prompt = build_location_suggestion_prompt(
            skills=skills,
            role=role,
            experience_years=experience_years,
            remote_preference=remote_preference,
        )

        # Verify prompt contains expected content
        assert "Python" in prompt
        assert "React" in prompt
        assert "Software Engineer" in prompt
        assert "3" in prompt
        assert "True" in prompt
        assert "suggested_locations" in prompt
        assert "remote_friendly_score" in prompt

    def test_build_job_match_prompt(self) -> None:
        """Test job match prompt builder with correct signature."""
        profile = {
            "id": "user123",
            "skills": ["Python", "React"],
            "experience_years": 5,
            "location": "San Francisco",
        }
        job = {
            "id": "job456",
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "requirements": ["Python", "React", "5+ years"],
            "location": "San Francisco",
        }

        prompt = build_job_match_prompt(profile, job)

        # Verify prompt contains expected content
        assert "Python" in prompt
        assert "React" in prompt
        assert "Senior Software Engineer" in prompt
        assert "Tech Corp" in prompt
        assert "score" in prompt
        assert "skill_match" in prompt
        assert "experience_match" in prompt

    def test_build_onboarding_questions_prompt(self) -> None:
        """Test onboarding questions prompt builder with correct signature."""
        resume_text = "Experienced software engineer..."
        current_step = "skills"

        prompt = build_onboarding_questions_prompt(
            resume_text=resume_text, current_step=current_step
        )

        # Verify prompt contains expected content
        assert resume_text in prompt
        assert "skills" in prompt
        assert "questions" in prompt
        assert "calibration" in prompt


class TestAIEndpointResponses:
    """Test AI endpoint response models."""

    def test_role_suggestion_response_validation(self) -> None:
        """Test RoleSuggestionResponse_V1 validation."""
        # Valid response
        valid_data = {
            "suggested_roles": ["Software Engineer", "Senior Developer"],
            "primary_role": "Software Engineer",
            "experience_level": "senior",
            "confidence": 0.85,
            "reasoning": "Strong match for software engineering roles",
        }

        response = RoleSuggestionResponse_V1(**valid_data)
        assert response.primary_role == "Software Engineer"
        assert response.confidence == 0.85
        assert len(response.suggested_roles) == 2

    def test_salary_suggestion_response_validation(self) -> None:
        """Test SalarySuggestionResponse_V1 validation."""
        valid_data = {
            "min_salary": 120000,
            "max_salary": 180000,
            "market_median": 150000,
            "currency": "USD",
            "confidence": 0.75,
            "factors": ["5+ years experience", "High COL location"],
            "reasoning": "Market rate for SF Bay Area",
        }

        response = SalarySuggestionResponse_V1(**valid_data)
        assert response.min_salary == 120000
        assert response.max_salary == 180000
        assert response.currency == "USD"

    def test_location_suggestion_response_validation(self) -> None:
        """Test LocationSuggestionResponse_V1 validation."""
        valid_data = {
            "suggested_locations": ["San Francisco", "New York", "Remote"],
            "remote_friendly_score": 0.9,
            "top_markets": ["San Francisco", "Seattle"],
            "reasoning": "Strong tech markets for software engineers",
        }

        response = LocationSuggestionResponse_V1(**valid_data)
        assert len(response.suggested_locations) == 3
        assert response.remote_friendly_score == 0.9
        assert "Remote" in response.suggested_locations

    def test_job_match_score_validation(self) -> None:
        """Test JobMatchScore_V1 validation."""
        valid_data = {
            "score": 85,
            "skill_match": 0.9,
            "experience_match": 0.8,
            "location_match": 1.0,
            "culture_signals": ["startup environment"],
            "red_flags": [],
            "summary": "Strong match with 4/5 required skills",
        }

        response = JobMatchScore_V1(**valid_data)
        assert response.score == 85
        assert response.skill_match == 0.9
        assert len(response.red_flags) == 0

    def test_onboarding_questions_response_validation(self) -> None:
        """Test OnboardingQuestionsResponse_V1 validation."""
        valid_data = {
            "questions": [
                {
                    "id": "visa_sponsorship",
                    "text": "Do you require visa sponsorship?",
                    "type": "yes_no",
                    "options": [],
                },
                {
                    "id": "relocation",
                    "text": "Are you willing to relocate?",
                    "type": "yes_no",
                    "options": [],
                },
            ]
        }

        response = OnboardingQuestionsResponse_V1(**valid_data)
        assert len(response.questions) == 2
        assert response.questions[0].id == "visa_sponsorship"
        assert response.questions[0].type == "yes_no"


class TestAIEndpointIntegration:
    """Test AI endpoint integration scenarios."""

    @pytest.mark.asyncio
    async def test_role_suggestion_flow(self) -> None:
        """Test complete role suggestion flow."""
        # Mock the LLM client
        with patch("apps.api.ai_endpoints._get_llm_client") as mock_llm:
            mock_client = AsyncMock()
            mock_llm.return_value = mock_client

            # Mock LLM response
            mock_response = {
                "suggested_roles": ["Software Engineer", "Full Stack Developer"],
                "primary_role": "Software Engineer",
                "experience_level": "mid",
                "confidence": 0.8,
                "reasoning": "Strong technical background",
            }
            mock_client.complete.return_value = json.dumps(mock_response)

            # Test the flow
            from apps.api.ai_endpoints import RoleSuggestionRequest

            request = RoleSuggestionRequest(
                resume_text="Experienced software engineer...",
                skills=["Python", "React"],
                experience_years=5,
                education_level="bachelor",
            )

            # This would normally require a database connection
            # For testing, we'll just verify the prompt building
            prompt = build_role_suggestion_prompt(
                resume_text=request.resume_text,
                skills=request.skills,
                experience_years=request.experience_years,
                education_level=request.education_level,
            )

            assert "Python" in prompt
            assert "React" in prompt
            assert "5" in prompt
            assert "bachelor" in prompt

    def test_error_handling(self) -> None:
        """Test error handling in AI endpoints."""
        # Test invalid resume text
        with pytest.raises(ValueError):
            RoleSuggestionRequest(
                resume_text="",  # Too short
                skills=["Python"],
                experience_years=5,
                education_level="bachelor",
            )

        # Test invalid experience years
        with pytest.raises(ValueError):
            RoleSuggestionRequest(
                resume_text="Valid resume text..." * 10,
                skills=["Python"],
                experience_years=-1,  # Invalid
                education_level="bachelor",
            )


if __name__ == "__main__":
    pytest.main([__file__])
