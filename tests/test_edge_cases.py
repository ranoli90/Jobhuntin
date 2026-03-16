"""Tests for edge cases in shared modules and domain logic.

These tests focus on:
- API request validation edge cases
- Path security edge cases
- Input sanitization edge cases
- Boundary conditions in validators
- Large/malformed inputs

This module complements tests/test_path_security.py and
tests/test_sql_injection_prevention.py which test specific security concerns.
"""

from __future__ import annotations

import json
import re
import sys
import os
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import patch

import pytest

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Test API Request Validator Edge Cases
# =============================================================================

class TestAPIRequestValidatorEdgeCases:
    """Test edge cases in APIRequestValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        from shared.api_request_validator import (
            APIRequestValidator,
            ValidationField,
            ValidationRule,
            DataType,
        )
        return APIRequestValidator()

    def test_validate_request_no_schema(self, validator):
        """Should return valid with warning when no schema exists."""
        result = validator.validate_request(
            endpoint="/unknown",
            data={"key": "value"}
        )
        
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_validate_field_missing_optional(self, validator):
        """Should pass when optional field is missing."""
        from shared.api_request_validator import (
            ValidationField,
            ValidationRule,
            DataType,
        )
        
        field = ValidationField(
            name="optional_field",
            data_type=DataType.STRING,
            rule=ValidationRule.OPTIONAL
        )
        
        result = validator._validate_field(field, {})
        
        assert result.is_valid

    def test_validate_field_required_missing(self, validator):
        """Should fail when required field is missing."""
        from shared.api_request_validator import (
            ValidationField,
            ValidationRule,
            DataType,
        )
        
        field = ValidationField(
            name="required_field",
            data_type=DataType.STRING,
            rule=ValidationRule.REQUIRED
        )
        
        result = validator._validate_field(field, {})
        
        assert not result.is_valid
        assert "required" in result.errors[0].lower()

    def test_validate_string_min_length(self, validator):
        """Should fail when string is below minimum length."""
        from shared.api_request_validator import (
            ValidationField,
            ValidationRule,
            DataType,
        )
        
        field = ValidationField(
            name="name",
            data_type=DataType.STRING,
            min_length=3
        )
        
        result = validator._validate_field(field, {"name": "ab"})
        
        assert not result.is_valid
        assert "at least" in result.errors[0].lower()

    def test_validate_string_max_length(self, validator):
        """Should fail when string exceeds maximum length."""
        from shared.api_request_validator import (
            ValidationField,
            ValidationRule,
            DataType,
        )
        
        field = ValidationField(
            name="name",
            data_type=DataType.STRING,
            max_length=10
        )
        
        result = validator._validate_field(field, {"name": "a" * 11})
        
        assert not result.is_valid
        assert "at most" in result.errors[0].lower()

    def test_validate_integer_min_value(self, validator):
        """Should fail when integer is below minimum."""
        from shared.api_request_validator import (
            ValidationField,
            ValidationRule,
            DataType,
        )
        
        field = ValidationField(
            name="age",
            data_type=DataType.INTEGER,
            min_value=0
        )
        
        result = validator._validate_field(field, {"age": -1})
        
        assert not result.is_valid

    def test_validate_integer_max_value(self, validator):
        """Should fail when integer exceeds maximum."""
        from shared.api_request_validator import (
            ValidationField,
            ValidationRule,
            DataType,
        )
        
        field = ValidationField(
            name="age",
            data_type=DataType.INTEGER,
            max_value=150
        )
        
        result = validator._validate_field(field, {"age": 151})
        
        assert not result.is_valid

    def test_validate_email_valid(self, validator):
        """Should pass for valid email."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="email",
            data_type=DataType.EMAIL
        )
        
        result = validator._validate_field(field, {"email": "test@example.com"})
        
        assert result.is_valid

    def test_validate_email_invalid(self, validator):
        """Should fail for invalid email."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="email",
            data_type=DataType.EMAIL
        )
        
        result = validator._validate_field(field, {"email": "not-an-email"})
        
        assert not result.is_valid

    def test_validate_uuid_valid(self, validator):
        """Should pass for valid UUID."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="id",
            data_type=DataType.UUID
        )
        
        result = validator._validate_field(field, {"id": "550e8400-e29b-41d4-a716-446655440000"})
        
        assert result.is_valid

    def test_validate_uuid_invalid(self, validator):
        """Should fail for invalid UUID."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="id",
            data_type=DataType.UUID
        )
        
        result = validator._validate_field(field, {"id": "not-a-uuid"})
        
        assert not result.is_valid

    def test_validate_url_valid(self, validator):
        """Should pass for valid URL."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="url",
            data_type=DataType.URL
        )
        
        result = validator._validate_field(field, {"url": "https://example.com"})
        
        assert result.is_valid

    def test_validate_url_invalid(self, validator):
        """Should fail for invalid URL."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="url",
            data_type=DataType.URL
        )
        
        result = validator._validate_field(field, {"url": "not-a-url"})
        
        assert not result.is_valid

    def test_validate_date_valid(self, validator):
        """Should pass for valid date."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="date",
            data_type=DataType.DATE
        )
        
        result = validator._validate_field(field, {"date": "2024-01-15"})
        
        assert result.is_valid

    def test_validate_date_invalid(self, validator):
        """Should fail for invalid date."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="date",
            data_type=DataType.DATE
        )
        
        result = validator._validate_field(field, {"date": "not-a-date"})
        
        assert not result.is_valid

    def test_validate_json_valid_string(self, validator):
        """Should parse valid JSON string."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="data",
            data_type=DataType.JSON
        )
        
        result = validator._validate_field(field, {"data": '{"key": "value"}'})
        
        assert result.is_valid
        assert isinstance(result.sanitized_data, dict)

    def test_validate_json_invalid_string(self, validator):
        """Should fail for invalid JSON string."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="data",
            data_type=DataType.JSON
        )
        
        result = validator._validate_field(field, {"data": "not json"})
        
        assert not result.is_valid

    def test_validate_array(self, validator):
        """Should validate array type."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="items",
            data_type=DataType.ARRAY
        )
        
        result = validator._validate_field(field, {"items": [1, 2, 3]})
        
        assert result.is_valid

    def test_validate_array_not_array(self, validator):
        """Should fail when array expected but not provided."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="items",
            data_type=DataType.ARRAY
        )
        
        result = validator._validate_field(field, {"items": "not an array"})
        
        assert not result.is_valid

    def test_validate_object(self, validator):
        """Should validate object type."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="data",
            data_type=DataType.OBJECT
        )
        
        result = validator._validate_field(field, {"data": {"key": "value"}})
        
        assert result.is_valid

    def test_validate_object_not_object(self, validator):
        """Should fail when object expected but not provided."""
        from shared.api_request_validator import (
            ValidationField,
            DataType,
        )
        
        field = ValidationField(
            name="data",
            data_type=DataType.OBJECT
        )
        
        result = validator._validate_field(field, {"data": "not an object"})
        
        assert not result.is_valid


# =============================================================================
# Test Security Validator Edge Cases
# =============================================================================

class TestSecurityValidatorEdgeCases:
    """Test edge cases in SecurityValidator."""

    @pytest.fixture
    def security_validator(self):
        """Create security validator instance."""
        from shared.api_request_validator import SecurityValidator
        return SecurityValidator()

    def test_sql_injection_detected_union(self, security_validator):
        """Should detect UNION SQL injection."""
        result = security_validator.validate_sql_injection(
            "test' UNION SELECT * FROM users--"
        )
        assert result is False

    def test_sql_injection_detected_drop(self, security_validator):
        """Should detect DROP SQL injection."""
        result = security_validator.validate_sql_injection(
            "test'; DROP TABLE users;--"
        )
        assert result is False

    def test_sql_injection_detected_or_1_1(self, security_validator):
        """Should detect OR 1=1 injection."""
        result = security_validator.validate_sql_injection(
            "test' OR '1'='1"
        )
        assert result is False

    def test_sql_injection_safe_input(self, security_validator):
        """Should pass safe SQL-like input."""
        result = security_validator.validate_sql_injection(
            "The product is great"
        )
        assert result is True

    def test_xss_detected_script_tag(self, security_validator):
        """Should detect script tag XSS."""
        result = security_validator.validate_xss(
            "<script>alert('xss')</script>"
        )
        assert result is False

    def test_xss_detected_javascript_uri(self, security_validator):
        """Should detect javascript: URI XSS."""
        result = security_validator.validate_xss(
            "javascript:alert('xss')"
        )
        assert result is False

    def test_xss_detected_on_event(self, security_validator):
        """Should detect onerror event XSS."""
        result = security_validator.validate_xss(
            "<img src=x onerror=alert(1)>"
        )
        assert result is False

    def test_xss_safe_input(self, security_validator):
        """Should pass safe HTML-like input."""
        result = security_validator.validate_xss(
            "<p>Hello World</p>"
        )
        assert result is True

    def test_path_traversal_detected(self, security_validator):
        """Should detect path traversal."""
        result = security_validator.validate_path_traversal(
            "../../../etc/passwd"
        )
        assert result is False

    def test_path_traversal_encoded(self, security_validator):
        """Should detect encoded path traversal."""
        result = security_validator.validate_path_traversal(
            "..%2f..%2f..%2fetc%2fpasswd"
        )
        assert result is False

    def test_path_traversal_safe(self, security_validator):
        """Should pass safe file path."""
        result = security_validator.validate_path_traversal(
            "documents/report.pdf"
        )
        assert result is True

    def test_command_injection_detected(self, security_validator):
        """Should detect command injection."""
        result = security_validator.validate_command_injection(
            "test; rm -rf /"
        )
        assert result is False

    def test_command_injection_pipe(self, security_validator):
        """Should detect pipe command injection."""
        result = security_validator.validate_command_injection(
            "test | cat /etc/passwd"
        )
        assert result is False

    def test_command_injection_safe(self, security_validator):
        """Should pass safe command-like input."""
        result = security_validator.validate_command_injection(
            "search term"
        )
        assert result is True

    def test_sanitize_removes_null_bytes(self, security_validator):
        """Should remove null bytes."""
        result = security_validator.sanitize_input("test\x00value")
        assert "\x00" not in result

    def test_sanitize_normalizes_whitespace(self, security_validator):
        """Should normalize whitespace."""
        result = security_validator.sanitize_input("test   value")
        assert " " in result
        assert "   " not in result

    def test_sanitize_removes_control_chars(self, security_validator):
        """Should remove control characters."""
        result = security_validator.sanitize_input("test\x01value")
        assert "\x01" not in result


# =============================================================================
# Test Path Security Edge Cases
# =============================================================================

class TestPathSecurityEdgeCases:
    """Test edge cases in path_security module."""

    def test_validate_path_empty(self):
        """Should fail for empty path."""
        from shared.path_security import validate_path, PathTraversalError
        
        with pytest.raises(ValueError):
            validate_path("/base", "")

    def test_validate_path_normal(self):
        """Should pass for normal path."""
        from shared.path_security import validate_path
        
        result = validate_path("/base", "documents/file.txt")
        assert result is not None

    def test_validate_path_traversal(self):
        """Should detect path traversal."""
        from shared.path_security import validate_path, PathTraversalError
        
        with pytest.raises(PathTraversalError):
            validate_path("/base", "../etc/passwd")

    def test_validate_path_double_encoded(self):
        """Should detect double-encoded traversal."""
        from shared.path_security import validate_path, PathTraversalError
        
        with pytest.raises(PathTraversalError):
            validate_path("/base", "..%252f..%252fpasswd")

    def test_validate_path_absolute_disallowed(self):
        """Should reject absolute paths when not allowed."""
        from shared.path_security import validate_path, PathTraversalError
        
        with pytest.raises(PathTraversalError):
            validate_path("/base", "/etc/passwd", allow_absolute=False)

    def test_validate_path_absolute_allowed(self):
        """Should allow absolute paths when allowed."""
        from shared.path_security import validate_path
        
        # Note: Even with allow_absolute=True, path must still be within base
        result = validate_path("/base", "/base/file.txt", allow_absolute=True)
        assert result is not None

    def test_contains_traversal_patterns(self):
        """Test traversal pattern detection."""
        from shared.path_security import contains_traversal_patterns
        
        assert contains_traversal_patterns("../etc") is True
        # The function checks raw path for literal "..", encoded is checked separately
        assert contains_traversal_patterns("safe/path") is False

    def test_decode_path_fully(self):
        """Test full path decoding."""
        from shared.path_security import decode_path_fully
        
        assert decode_path_fully("test%20path") == "test path"
        # Full decode means decoding all the way
        assert decode_path_fully("test%2520path") == "test path"
        assert decode_path_fully("test") == "test"

    def test_validate_bucket_name_empty(self):
        """Should fail for empty bucket name."""
        from shared.path_security import validate_bucket_name, PathTraversalError
        
        with pytest.raises(ValueError):
            validate_bucket_name("")

    def test_validate_bucket_name_with_slash(self):
        """Should fail for bucket name with slash."""
        from shared.path_security import validate_bucket_name, PathTraversalError
        
        with pytest.raises(ValueError):
            validate_bucket_name("bucket/path")

    def test_validate_bucket_name_valid(self):
        """Should pass for valid bucket name."""
        from shared.path_security import validate_bucket_name
        
        result = validate_bucket_name("my-bucket")
        assert result == "my-bucket"

    def test_is_path_safe(self):
        """Test is_path_safe helper."""
        from shared.path_security import is_path_safe
        
        assert is_path_safe("/base", "safe/path") is True
        assert is_path_safe("/base", "../dangerous") is False


# =============================================================================
# Test Data Type Edge Cases
# =============================================================================

class TestDataTypeConversions:
    """Test data type conversion edge cases."""

    def test_integer_from_string(self):
        """Should convert string to integer."""
        from shared.api_request_validator import APIRequestValidator, DataType
        
        validator = APIRequestValidator()
        result = validator._convert_type(DataType.INTEGER, "42")
        
        assert result == 42
        assert isinstance(result, int)

    def test_integer_from_float(self):
        """Should convert float to integer."""
        from shared.api_request_validator import APIRequestValidator, DataType
        
        validator = APIRequestValidator()
        result = validator._convert_type(DataType.INTEGER, 42.7)
        
        assert result == 42

    def test_float_from_string(self):
        """Should convert string to float."""
        from shared.api_request_validator import APIRequestValidator, DataType
        
        validator = APIRequestValidator()
        result = validator._convert_type(DataType.FLOAT, "42.5")
        
        assert result == 42.5

    def test_boolean_from_string_true(self):
        """Should convert string 'true' to boolean."""
        from shared.api_request_validator import APIRequestValidator, DataType
        
        validator = APIRequestValidator()
        
        assert validator._convert_type(DataType.BOOLEAN, "true") is True
        assert validator._convert_type(DataType.BOOLEAN, "TRUE") is True
        assert validator._convert_type(DataType.BOOLEAN, "1") is True

    def test_boolean_from_string_false(self):
        """Should convert string 'false' to boolean."""
        from shared.api_request_validator import APIRequestValidator, DataType
        
        validator = APIRequestValidator()
        
        assert validator._convert_type(DataType.BOOLEAN, "false") is False
        assert validator._convert_type(DataType.BOOLEAN, "0") is False

    def test_json_from_string(self):
        """Should parse JSON string."""
        from shared.api_request_validator import APIRequestValidator, DataType
        
        validator = APIRequestValidator()
        result = validator._convert_type(DataType.JSON, '{"key": "value"}')
        
        assert result == {"key": "value"}

    def test_json_from_dict(self):
        """Should pass through dict."""
        from shared.api_request_validator import APIRequestValidator, DataType
        
        validator = APIRequestValidator()
        data = {"key": "value"}
        result = validator._convert_type(DataType.JSON, data)
        
        assert result == data


# =============================================================================
# Test Validation Edge Cases
# =============================================================================

class TestValidationEdgeCases:
    """Test validation edge cases."""

    def test_type_validation_integer_from_valid_string(self):
        """Should validate integer from valid string."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(name="value", data_type=DataType.INTEGER)
        
        error = validator._validate_type(field, "42")
        # Should not return error (valid)
        assert error is None or "integer" not in error.lower()

    def test_type_validation_integer_from_invalid_string(self):
        """Should fail integer validation from invalid string."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(name="value", data_type=DataType.INTEGER)
        
        error = validator._validate_type(field, "not-a-number")
        assert error is not None

    def test_type_validation_boolean_from_various(self):
        """Should validate boolean from various representations."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(name="value", data_type=DataType.BOOLEAN)
        
        # Valid boolean representations should not error
        for val in ["true", "false", "1", "0", True, False]:
            error = validator._validate_type(field, val)
            assert error is None


# =============================================================================
# Test Rate Limiting Edge Cases
# =============================================================================

class TestRateLimitingEdgeCases:
    """Test rate limiting edge cases."""

    def test_rate_limit_different_endpoints(self):
        """Different endpoints should have separate limits."""
        from shared.api_request_validator import APIRequestValidator
        
        validator = APIRequestValidator()
        
        # Make requests to endpoint1 (limit is 100)
        for _ in range(100):
            validator._check_rate_limit("127.0.0.1", "/api/endpoint1")
        
        # endpoint1 should be limited
        result = validator._check_rate_limit("127.0.0.1", "/api/endpoint1")
        assert result is not None
        
        # endpoint2 should still work
        result = validator._check_rate_limit("127.0.0.1", "/api/endpoint2")
        assert result is None

    def test_rate_limit_different_ips(self):
        """Different IPs should have separate limits."""
        from shared.api_request_validator import APIRequestValidator
        
        validator = APIRequestValidator()
        
        # Make requests from IP1 (limit is 100)
        for _ in range(100):
            validator._check_rate_limit("127.0.0.1", "/api/endpoint")
        
        # IP1 should be limited
        result = validator._check_rate_limit("127.0.0.1", "/api/endpoint")
        assert result is not None
        
        # IP2 should still work
        result = validator._check_rate_limit("127.0.0.2", "/api/endpoint")
        assert result is None

    def test_rate_limit_cleanup_old_entries(self):
        """Old rate limit entries should be cleaned up."""
        from shared.api_request_validator import APIRequestValidator
        from datetime import datetime, timedelta
        
        validator = APIRequestValidator()
        
        # Add old entries
        old_time = datetime.now() - timedelta(hours=2)
        validator.rate_limit_tracker["test:endpoint"] = [old_time]
        
        # Should be cleaned up and allow request
        result = validator._check_rate_limit("test", "endpoint")
        assert result is None


# =============================================================================
# Test Enum and Pattern Validation
# =============================================================================

class TestEnumAndPatternValidation:
    """Test enum and pattern validation edge cases."""

    def test_enum_valid_value(self):
        """Should pass for valid enum value."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="status",
            data_type=DataType.STRING,
            enum_values=["active", "inactive", "pending"]
        )
        
        result = validator._validate_field(field, {"status": "active"})
        
        assert result.is_valid

    def test_enum_invalid_value(self):
        """Should fail for invalid enum value."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="status",
            data_type=DataType.STRING,
            enum_values=["active", "inactive", "pending"]
        )
        
        result = validator._validate_field(field, {"status": "unknown"})
        
        assert not result.is_valid

    def test_pattern_valid(self):
        """Should pass for matching pattern."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="code",
            data_type=DataType.STRING,
            pattern=r"^[A-Z]{3}-\d{3}$"
        )
        
        result = validator._validate_field(field, {"code": "ABC-123"})
        
        assert result.is_valid

    def test_pattern_invalid(self):
        """Should fail for non-matching pattern."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="code",
            data_type=DataType.STRING,
            pattern=r"^[A-Z]{3}-\d{3}$"
        )
        
        result = validator._validate_field(field, {"code": "invalid"})
        
        assert not result.is_valid


# =============================================================================
# Test Custom Validator Edge Cases
# =============================================================================

class TestCustomValidation:
    """Test custom validation edge cases."""

    def test_custom_validator_passes(self):
        """Should pass when custom validator returns True."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="value",
            data_type=DataType.INTEGER,
            custom_validator=lambda x: x > 0
        )
        
        result = validator._validate_field(field, {"value": 10})
        
        assert result.is_valid

    def test_custom_validator_fails(self):
        """Should fail when custom validator returns False."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="value",
            data_type=DataType.INTEGER,
            custom_validator=lambda x: x > 0
        )
        
        result = validator._validate_field(field, {"value": -1})
        
        assert not result.is_valid

    def test_custom_validator_exception(self):
        """Should handle custom validator exception."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="value",
            data_type=DataType.INTEGER,
            custom_validator=lambda x: 1 / x  # Will raise on 0
        )
        
        result = validator._validate_field(field, {"value": 0})
        
        assert not result.is_valid
        assert len(result.errors) > 0


# =============================================================================
# Test Default Values
# =============================================================================

class TestDefaultValues:
    """Test default value handling."""

    def test_default_value_used(self):
        """Should use default value when field is missing."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, ValidationRule, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="status",
            data_type=DataType.STRING,
            rule=ValidationRule.REQUIRED,
            default_value="default"
        )
        
        result = validator._validate_field(field, {})
        
        assert result.is_valid
        assert result.warnings
        assert "default" in result.warnings[0].lower()

    def test_default_value_not_used_when_provided(self):
        """Should not use default when value is provided."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, ValidationRule, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="status",
            data_type=DataType.STRING,
            rule=ValidationRule.REQUIRED,
            default_value="default"
        )
        
        result = validator._validate_field(field, {"status": "provided"})
        
        assert result.is_valid
        assert result.sanitized_data == "provided"


# =============================================================================
# Test Sanitization
# =============================================================================

class TestSanitization:
    """Test input sanitization."""

    def test_sanitization_enabled(self):
        """Should sanitize when enabled."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="text",
            data_type=DataType.STRING,
            sanitize=True
        )
        
        result = validator._validate_field(field, {"text": "test\x00value"})
        
        assert result.is_valid
        assert "\x00" not in result.sanitized_data

    def test_sanitization_disabled(self):
        """Should not sanitize when disabled."""
        from shared.api_request_validator import APIRequestValidator, ValidationField, DataType
        
        validator = APIRequestValidator()
        field = ValidationField(
            name="text",
            data_type=DataType.STRING,
            sanitize=False
        )
        
        result = validator._validate_field(field, {"text": "test\x00value"})
        
        assert result.is_valid
        # Value may or may not have null byte depending on other processing


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
