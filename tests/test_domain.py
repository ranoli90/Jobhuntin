"""Unit tests for backend domain models, normalize_profile, and LLM client.

No database or network required – pure logic tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domain.models import (
    ApplicationStatus,
    CanonicalProfile,
    ErrorDetail,
    ErrorResponse,
    LLMMapping,
    normalize_profile,
)
from backend.llm.contracts import (
    DomMappingResponse_V1,
    ResumeParseResponse_V1,
    build_dom_mapping_prompt,
    build_resume_parse_prompt,
)

# ===================================================================
# normalize_profile tests
# ===================================================================

class TestNormalizeProfile:
    """Test the canonical profile normalizer."""

    def test_full_profile(self):
        raw = {
            "contact": {
                "full_name": "Alice Smith",
                "email": "alice@example.com",
                "phone": "555-0100",
                "location": "San Francisco, CA",
                "linkedin_url": "https://linkedin.com/in/alice",
                "portfolio_url": "",
            },
            "education": [
                {
                    "institution": "MIT",
                    "degree": "B.S.",
                    "field_of_study": "Computer Science",
                    "start_date": "2014",
                    "end_date": "2018",
                    "gpa": "3.8",
                }
            ],
            "experience": [
                {
                    "company": "TechCorp",
                    "title": "Senior Engineer",
                    "start_date": "2020",
                    "end_date": "present",
                    "location": "SF",
                    "responsibilities": ["Led backend architecture"],
                }
            ],
            "skills": {"technical": ["Python", "TypeScript"], "soft": ["Leadership"]},
            "certifications": ["AWS Solutions Architect"],
            "languages": ["English"],
            "summary": "Experienced engineer",
            "years_experience": 6,
        }

        profile = normalize_profile(raw)
        assert isinstance(profile, CanonicalProfile)
        assert profile.contact.full_name == "Alice Smith"
        assert profile.contact.first_name == "Alice"
        assert profile.contact.last_name == "Smith"
        assert profile.contact.email == "alice@example.com"
        assert len(profile.education) == 1
        assert profile.education[0].institution == "MIT"
        assert len(profile.experience) == 1
        assert profile.experience[0].company == "TechCorp"
        assert profile.current_title == "Senior Engineer"
        assert profile.current_company == "TechCorp"
        assert profile.skills.technical == ["Python", "TypeScript"]
        assert profile.years_experience == 6

    def test_empty_profile(self):
        profile = normalize_profile({})
        assert profile.contact.full_name == ""
        assert profile.contact.email == ""
        assert profile.education == []
        assert profile.experience == []
        assert profile.current_title == ""
        assert profile.years_experience is None

    def test_extra_fields_ignored(self):
        """Forward compatibility: unknown keys should not cause errors."""
        raw = {
            "contact": {
                "full_name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "",
                "location": "",
                "linkedin_url": "",
                "portfolio_url": "",
                "twitter_handle": "@jane",  # extra field
            },
            "education": [],
            "experience": [],
            "skills": {"technical": [], "soft": [], "languages": ["Python"]},  # extra key
            "certifications": [],
            "languages": [],
            "summary": "",
            "new_top_level_key": "should be ignored",
        }

        profile = normalize_profile(raw)
        assert profile.contact.full_name == "Jane Doe"
        assert profile.contact.email == "jane@example.com"
        # Extra keys in contact should be dropped by Pydantic
        assert not hasattr(profile.contact, "twitter_handle")

    def test_name_splitting_from_full_name(self):
        """When first_name/last_name are absent, split from full_name."""
        raw = {"contact": {"full_name": "Bob Jones"}}
        profile = normalize_profile(raw)
        assert profile.contact.first_name == "Bob"
        assert profile.contact.last_name == "Jones"

    def test_explicit_first_last_name_preserved(self):
        """When first_name/last_name are explicitly provided, use them."""
        raw = {
            "contact": {
                "full_name": "Robert A. Jones",
                "first_name": "Robert",
                "last_name": "Jones",
            }
        }
        profile = normalize_profile(raw)
        assert profile.contact.first_name == "Robert"
        assert profile.contact.last_name == "Jones"


# ===================================================================
# LLMMapping model tests
# ===================================================================

class TestLLMMapping:

    def test_from_dict_full(self):
        raw = {
            "field_values": {"#name": "Alice", "#email": "a@b.com"},
            "unresolved_required_fields": [
                {"selector": "#clearance", "question": "What is your clearance?"}
            ],
        }
        mapping = LLMMapping.from_dict(raw)
        assert mapping.field_values == {"#name": "Alice", "#email": "a@b.com"}
        assert len(mapping.unresolved_required_fields) == 1
        assert mapping.unresolved_required_fields[0].selector == "#clearance"

    def test_from_dict_empty(self):
        mapping = LLMMapping.from_dict({})
        assert mapping.field_values == {}
        assert mapping.unresolved_required_fields == []


# ===================================================================
# Error envelope tests
# ===================================================================

class TestErrorResponse:

    def test_serialization(self):
        err = ErrorResponse(
            error=ErrorDetail(code="HTTP_404", message="Not found")
        )
        d = err.model_dump()
        assert d["error"]["code"] == "HTTP_404"
        assert d["error"]["message"] == "Not found"
        assert d["error"]["details"] is None


# ===================================================================
# LLM contract tests
# ===================================================================

class TestResumeParseContract:

    def test_response_model_accepts_valid(self):
        raw = {
            "contact": {"full_name": "Alice", "email": "a@b.com"},
            "education": [],
            "experience": [],
            "skills": {"technical": ["Python"], "soft": []},
            "certifications": [],
            "languages": ["English"],
            "summary": "Engineer",
        }
        result = ResumeParseResponse_V1.model_validate(raw)
        assert result.contact.full_name == "Alice"
        assert result.skills.technical == ["Python"]

    def test_response_model_defaults(self):
        """Empty dict should produce defaults, not fail."""
        result = ResumeParseResponse_V1.model_validate({})
        assert result.contact.full_name == ""
        assert result.education == []

    def test_prompt_builder(self):
        prompt = build_resume_parse_prompt("Some resume text here")
        assert "Some resume text here" in prompt
        assert "json only" in prompt.lower()


class TestDomMappingContract:

    def test_response_model_accepts_valid(self):
        raw = {
            "field_values": {"#name": "Alice"},
            "unresolved_required_fields": [
                {"selector": "#clearance", "question": "Clearance level?"}
            ],
        }
        result = DomMappingResponse_V1.model_validate(raw)
        assert result.field_values["#name"] == "Alice"
        assert len(result.unresolved_required_fields) == 1

    def test_response_model_defaults(self):
        result = DomMappingResponse_V1.model_validate({})
        assert result.field_values == {}
        assert result.unresolved_required_fields == []

    def test_prompt_builder(self):
        profile = {"contact": {"full_name": "Alice"}}
        fields = [{"selector": "#name", "label": "Name", "type": "text"}]
        prompt = build_dom_mapping_prompt(profile, fields)
        assert "Alice" in prompt
        assert "#name" in prompt


# ===================================================================
# LLM Client tests (mocked HTTP)
# ===================================================================

class TestLLMClient:

    @pytest.mark.asyncio
    async def test_successful_call_with_response_format(self):
        """LLMClient should parse response into Pydantic model."""
        from shared.config import Settings

        from backend.llm.client import LLMClient

        settings = Settings(
            llm_api_base="https://api.openai.com/v1",
            llm_api_key="test-key",
            llm_retry_count=0,
            llm_timeout_seconds=5,
        )
        client = LLMClient(settings)

        mock_response = {
            "field_values": {"#name": "Alice"},
            "unresolved_required_fields": [],
        }

        # Mock the _request method
        client._request = AsyncMock(return_value=mock_response)

        result = await client.call(
            prompt="test prompt",
            response_format=DomMappingResponse_V1,
        )
        assert isinstance(result, DomMappingResponse_V1)
        assert result.field_values["#name"] == "Alice"

    @pytest.mark.asyncio
    async def test_raw_dict_return_without_response_format(self):
        """Without response_format, should return raw dict."""
        from shared.config import Settings

        from backend.llm.client import LLMClient

        settings = Settings(
            llm_api_base="https://api.openai.com/v1",
            llm_api_key="test-key",
            llm_retry_count=0,
        )
        client = LLMClient(settings)
        client._request = AsyncMock(return_value={"foo": "bar"})

        result = await client.call(prompt="test")
        assert result == {"foo": "bar"}

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Should retry on server errors then succeed."""
        import httpx
        from shared.config import Settings

        from backend.llm.client import LLMClient

        settings = Settings(
            llm_api_base="https://api.openai.com/v1",
            llm_api_key="test-key",
            llm_retry_count=2,
        )
        client = LLMClient(settings)

        call_count = 0

        async def flaky_request(payload):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                mock_resp = MagicMock()
                mock_resp.status_code = 503
                raise httpx.HTTPStatusError("503", request=MagicMock(), response=mock_resp)
            return {
                "choices": [{
                    "message": {
                        "content": '{"result": "ok"}'
                    }
                }]
            }

        client._make_http_request = flaky_request

        result = await client.call(prompt="test")
        assert result == {"result": "ok"}
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_validation_error_not_retried(self):
        """Schema validation failures should not be retried."""
        from shared.config import Settings

        from backend.llm.client import LLMClient, LLMValidationError

        settings = Settings(
            llm_api_base="https://api.openai.com/v1",
            llm_api_key="test-key",
            llm_retry_count=2,
        )
        client = LLMClient(settings)

        # Return data that doesn't match ResumeParseResponse_V1 contact shape
        # Actually, ResumeParseResponse_V1 has all defaults, so let's use a model
        # with required fields. We'll test with a custom model.
        from pydantic import BaseModel

        class StrictModel(BaseModel):
            required_field: str  # no default → required

        mock_openai_resp = {
            "choices": [{
                "message": {
                    "content": '{"wrong_field": "value"}'
                }
            }]
        }
        client._make_http_request = AsyncMock(return_value=mock_openai_resp)

        with pytest.raises(LLMValidationError):
            await client.call(prompt="test", response_format=StrictModel)


# ===================================================================
# ApplicationStatus enum tests
# ===================================================================

class TestApplicationStatus:

    def test_values(self):
        assert ApplicationStatus.QUEUED.value == "QUEUED"
        assert ApplicationStatus.PROCESSING.value == "PROCESSING"
        assert ApplicationStatus.REQUIRES_INPUT.value == "REQUIRES_INPUT"
        assert ApplicationStatus.APPLIED.value == "APPLIED"
        assert ApplicationStatus.FAILED.value == "FAILED"

    def test_string_comparison(self):
        assert ApplicationStatus.QUEUED == "QUEUED"
