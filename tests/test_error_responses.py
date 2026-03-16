"""Tests for standardized error response format.

These tests verify that:
- Error response format is consistent across all endpoints
- Error codes are correct for different error types
- HTTP status codes are appropriate
- Request IDs are included for debugging
- Timestamps are included in all error responses
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from shared.error_responses import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ConfigurationError,
    ErrorCodes,
    ErrorDetail,
    ErrorInfo,
    ErrorResponse,
    InternalError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
    create_error_response,
    create_not_found_error,
    create_validation_error,
    register_exception_handlers,
)


# Create a test FastAPI app
def create_test_app() -> FastAPI:
    """Create a test FastAPI application with error handlers registered."""
    app = FastAPI()

    # Register exception handlers
    register_exception_handlers(app)

    @app.get("/test-validation")
    async def test_validation():
        raise ValidationError("Invalid input", field_errors={"email": "Invalid email format"})

    @app.get("/test-auth")
    async def test_auth():
        raise AuthenticationError("Invalid token")

    @app.get("/test-auth-expired")
    async def test_auth_expired():
        raise AuthenticationError("Token expired", code=ErrorCodes.TOKEN_EXPIRED)

    @app.get("/test-auth-missing-credentials")
    async def test_auth_missing_credentials():
        raise AuthenticationError(
            "Missing authentication",
            code=ErrorCodes.MISSING_CREDENTIALS,
        )

    @app.get("/test-forbidden")
    async def test_forbidden():
        raise AuthorizationError("Access denied")

    @app.get("/test-not-found")
    async def test_not_found():
        raise NotFoundError("User", "123")

    @app.get("/test-conflict")
    async def test_conflict():
        raise ConflictError("Resource already exists")

    @app.get("/test-rate-limit")
    async def test_rate_limit():
        raise RateLimitError("Too many requests", retry_after=60)

    @app.get("/test-internal")
    async def test_internal():
        raise InternalError("Something went wrong")

    @app.get("/test-service-unavailable")
    async def test_service_unavailable():
        raise ServiceUnavailableError("Service down", retry_after=30)

    @app.get("/test-config")
    async def test_config():
        raise ConfigurationError("JWT_SECRET missing")

    @app.get("/test-http-exception")
    async def test_http_exception():
        raise HTTPException(status_code=400, detail="Bad request")

    @app.get("/test-custom-error")
    async def test_custom_error():
        raise APIError(
            code="CUSTOM_ERROR",
            message="Custom error message",
            status_code=422,
            details=[ErrorDetail(field="field1", message="Field error")],
        )

    @app.get("/test-not-found-helper")
    async def test_not_found_helper():
        response, status_code = create_not_found_error("Job", "456")
        return response, status_code

    @app.get("/test-validation-helper")
    async def test_validation_helper():
        response, status_code = create_validation_error(
            "Validation failed",
            field_errors={"name": "Name is required"},
        )
        return response, status_code

    @app.get("/test-generic-error")
    async def test_generic_error():
        raise Exception("Something went wrong")

    return app


# Create test client
app = create_test_app()
client = TestClient(app, raise_server_exceptions=False)


class TestErrorResponseFormat:
    """Test that error responses follow the standardized format."""

    def test_error_response_has_required_fields(self):
        """Error response should have error, request_id, and timestamp fields."""
        response = client.get("/test-validation")
        assert response.status_code == 400
        data = response.json()

        assert "error" in data
        assert "request_id" in data
        assert "timestamp" in data

    def test_error_info_has_required_fields(self):
        """Error info should have code and message fields."""
        response = client.get("/test-validation")
        assert response.status_code == 400
        data = response.json()

        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]

    def test_timestamp_is_iso_format(self):
        """Timestamp should be in ISO 8601 format."""
        response = client.get("/test-validation")
        data = response.json()

        timestamp = data.get("timestamp")
        assert timestamp is not None

        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None


class TestErrorCodes:
    """Test that correct error codes are used."""

    def test_validation_error_code(self):
        """Validation errors should use VALIDATION_ERROR code."""
        response = client.get("/test-validation")
        assert response.status_code == 400
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.VALIDATION_ERROR

    def test_authentication_error_code(self):
        """Authentication errors should use AUTHENTICATION_FAILED code."""
        response = client.get("/test-auth")
        assert response.status_code == 401
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.AUTHENTICATION_FAILED

    def test_token_expired_code(self):
        """Expired token should use TOKEN_EXPIRED code."""
        response = client.get("/test-auth-expired")
        assert response.status_code == 401
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.TOKEN_EXPIRED

    def test_missing_credentials_code(self):
        """Missing auth should use MISSING_CREDENTIALS code."""
        response = client.get("/test-auth-missing-credentials")
        assert response.status_code == 401
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.MISSING_CREDENTIALS

    def test_authorization_error_code(self):
        """Authorization errors should use AUTHORIZATION_FAILED code."""
        response = client.get("/test-forbidden")
        assert response.status_code == 403
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.AUTHORIZATION_FAILED

    def test_not_found_error_code(self):
        """Not found errors should use RESOURCE_NOT_FOUND code."""
        response = client.get("/test-not-found")
        assert response.status_code == 404
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.RESOURCE_NOT_FOUND

    def test_conflict_error_code(self):
        """Conflict errors should use CONFLICT code."""
        response = client.get("/test-conflict")
        assert response.status_code == 409
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.CONFLICT

    def test_rate_limit_error_code(self):
        """Rate limit errors should use RATE_LIMIT_EXCEEDED code."""
        response = client.get("/test-rate-limit")
        assert response.status_code == 429
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.RATE_LIMIT_EXCEEDED

    def test_internal_error_code(self):
        """Internal errors should use INTERNAL_ERROR code."""
        response = client.get("/test-internal")
        assert response.status_code == 500
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.INTERNAL_ERROR

    def test_service_unavailable_error_code(self):
        """Service unavailable should use SERVICE_UNAVAILABLE code."""
        response = client.get("/test-service-unavailable")
        assert response.status_code == 503
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.SERVICE_UNAVAILABLE

    def test_configuration_error_code(self):
        """Configuration errors should use CONFIGURATION_ERROR code."""
        response = client.get("/test-config")
        assert response.status_code == 500
        data = response.json()

        assert data["error"]["code"] == ErrorCodes.CONFIGURATION_ERROR


class TestHttpStatusCodes:
    """Test that HTTP status codes are appropriate."""

    def test_validation_returns_400(self):
        """Validation errors should return 400 Bad Request."""
        response = client.get("/test-validation")
        assert response.status_code == 400

    def test_auth_returns_401(self):
        """Authentication errors should return 401 Unauthorized."""
        response = client.get("/test-auth")
        assert response.status_code == 401

    def test_forbidden_returns_403(self):
        """Authorization errors should return 403 Forbidden."""
        response = client.get("/test-forbidden")
        assert response.status_code == 403

    def test_not_found_returns_404(self):
        """Not found errors should return 404 Not Found."""
        response = client.get("/test-not-found")
        assert response.status_code == 404

    def test_conflict_returns_409(self):
        """Conflict errors should return 409 Conflict."""
        response = client.get("/test-conflict")
        assert response.status_code == 409

    def test_rate_limit_returns_429(self):
        """Rate limit errors should return 429 Too Many Requests."""
        response = client.get("/test-rate-limit")
        assert response.status_code == 429

    def test_internal_returns_500(self):
        """Internal errors should return 500 Internal Server Error."""
        response = client.get("/test-internal")
        assert response.status_code == 500

    def test_service_unavailable_returns_503(self):
        """Service unavailable should return 503 Service Unavailable."""
        response = client.get("/test-service-unavailable")
        assert response.status_code == 503


class TestErrorDetails:
    """Test that error details are properly included."""

    def test_validation_error_details(self):
        """Validation errors should include field-specific details."""
        response = client.get("/test-validation")
        data = response.json()

        details = data["error"]["details"]
        assert len(details) > 0
        assert details[0]["field"] == "email"
        assert details[0]["message"] == "Invalid email format"

    def test_not_found_error_message(self):
        """Not found errors should include resource and identifier."""
        response = client.get("/test-not-found")
        data = response.json()

        # Should contain "User" and "123" in the message
        assert "User" in data["error"]["message"]
        assert "123" in data["error"]["message"]

    def test_rate_limit_retry_after(self):
        """Rate limit errors should include retry information."""
        response = client.get("/test-rate-limit")
        data = response.json()

        details = data["error"]["details"]
        assert len(details) > 0
        assert details[0]["field"] == "retry_after"

    def test_custom_error_details(self):
        """Custom API errors should preserve details."""
        response = client.get("/test-custom-error")
        data = response.json()

        assert data["error"]["code"] == "CUSTOM_ERROR"
        assert len(data["error"]["details"]) > 0
        assert data["error"]["details"][0]["field"] == "field1"


class TestHelperFunctions:
    """Test helper functions for creating error responses."""

    def test_create_not_found_error(self):
        """Test create_not_found_error helper."""
        response, status_code = create_not_found_error("Job", "456")

        assert status_code == 404
        assert response["error"]["code"] == ErrorCodes.RESOURCE_NOT_FOUND
        assert "Job" in response["error"]["message"]
        assert "456" in response["error"]["message"]

    def test_create_validation_error(self):
        """Test create_validation_error helper."""
        response, status_code = create_validation_error(
            "Validation failed",
            field_errors={"name": "Name is required"},
        )

        assert status_code == 400
        assert response["error"]["code"] == ErrorCodes.VALIDATION_ERROR
        assert len(response["error"]["details"]) > 0
        assert response["error"]["details"][0]["field"] == "name"


class TestHttpExceptionHandling:
    """Test that standard HTTPExceptions are converted to standardized format."""

    def test_http_exception_converted(self):
        """Standard HTTPException should be converted to standardized format."""
        response = client.get("/test-http-exception")
        assert response.status_code == 400
        data = response.json()

        # Should have standardized format
        assert "error" in data
        assert "request_id" in data
        assert "timestamp" in data


class TestGenericExceptionHandling:
    """Test that generic exceptions are handled properly."""

    def test_generic_exception_returns_500(self):
        """Generic exceptions should return 500 with standardized format."""
        response = client.get("/test-generic-error")
        assert response.status_code == 500
        data = response.json()

        # Should have standardized format
        assert "error" in data
        assert data["error"]["code"] == ErrorCodes.INTERNAL_ERROR
        assert "request_id" in data
        assert "timestamp" in data


class TestRequestId:
    """Test that request IDs are included in error responses."""

    def test_request_id_present(self):
        """Request ID should be present in error responses."""
        response = client.get("/test-validation")
        data = response.json()

        # Request ID should be present (even if None in test environment)
        assert "request_id" in data


class TestErrorResponseModel:
    """Test the ErrorResponse Pydantic model."""

    def test_error_response_model(self):
        """ErrorResponse should serialize correctly."""
        response = ErrorResponse(
            error=ErrorInfo(
                code="TEST_ERROR",
                message="Test error",
                details=[ErrorDetail(field="test", message="Test detail")],
            ),
            request_id="test-123",
        )

        data = response.model_dump()
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["request_id"] == "test-123"
        assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
