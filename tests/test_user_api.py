"""Tests for user-facing web API (api.user).

Covers status mapping and response shapes without requiring a live DB.
"""

from __future__ import annotations
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from pydantic import BaseModel


class MockApplication(BaseModel):
    id: str
    status: str
    job_title: str
    company_name: str
    location: str
    salary_min: int | None = None
    salary_max: int | None = None
    remote: bool = False


def test_status_to_web_mapping() -> None:
    """Map backend application_status to web status for list_applications."""
    from api.user import _status_to_web

    assert _status_to_web("QUEUED") == "APPLYING"
    assert _status_to_web("PROCESSING") == "APPLYING"
    assert _status_to_web("REQUIRES_INPUT") == "HOLD"
    assert _status_to_web("APPLIED") == "APPLIED"
    assert _status_to_web("SUBMITTED") == "APPLIED"
    assert _status_to_web("COMPLETED") == "APPLIED"
    assert _status_to_web("FAILED") == "FAILED"
    assert _status_to_web("REGISTERED") == "APPLIED"
    assert _status_to_web("UNKNOWN") == "FAILED"


def test_status_to_web_edge_cases() -> None:
    """Test edge cases for status mapping."""
    from api.user import _status_to_web

    # Test None and empty string
    with pytest.raises((AttributeError, TypeError)):
        _status_to_web(None)  # type: ignore
    
    with pytest.raises((AttributeError, TypeError)):
        _status_to_web("")  # type: ignore


def test_application_response_shape() -> None:
    """Test that application responses have the expected shape."""
    from api.user import _format_application_response
    
    mock_app = MockApplication(
        id="123",
        status="APPLIED",
        job_title="Software Engineer",
        company_name="Tech Corp",
        location="San Francisco, CA",
        salary_min=80000,
        salary_max=120000,
        remote=True
    )
    
    response = _format_application_response(mock_app)
    
    # Verify required fields
    assert "id" in response
    assert "status" in response
    assert "job_title" in response
    assert "company_name" in response
    assert "location" in response
    assert "salary_min" in response
    assert "salary_max" in response
    assert "remote" in response
    
    # Verify values
    assert response["id"] == "123"
    assert response["status"] == "APPLIED"
    assert response["job_title"] == "Software Engineer"
    assert response["remote"] is True


def test_salary_validation() -> None:
    """Test salary field validation and formatting."""
    from api.user import _format_salary_range
    
    # Test normal salary range
    salary = _format_salary_range(80000, 120000)
    assert salary == "$80,000 - $120,000"
    
    # Test only minimum salary
    salary = _format_salary_range(80000, None)
    assert salary == "$80,000+"
    
    # Test no salary info
    salary = _format_salary_range(None, None)
    assert salary == "Salary not specified"
    
    # Test equal min/max
    salary = _format_salary_range(100000, 100000)
    assert salary == "$100,000"


def test_location_formatting() -> None:
    """Test location field formatting."""
    from api.user import _format_location
    
    # Test normal location
    location = _format_location("San Francisco, CA")
    assert location == "San Francisco, CA"
    
    # Test remote location
    location = _format_location("Remote")
    assert location == "Remote"
    
    # Test hybrid location
    location = _format_location("Hybrid - San Francisco, CA")
    assert location == "Hybrid - San Francisco, CA"
    
    # Test empty location
    location = _format_location("")
    assert location == "Location not specified"


if __name__ == "__main__":
    pytest.main([__file__])
