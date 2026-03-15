"""
API Request Validator

Comprehensive request validation middleware for API endpoints.
Provides input validation, sanitization, and security checks.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ValidationRule(Enum):
    """Validation rule types."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    TYPE_CHECK = "type_check"
    RANGE_CHECK = "range_check"
    LENGTH_CHECK = "length_check"
    PATTERN_CHECK = "pattern_check"
    ENUM_CHECK = "enum_check"
    CUSTOM_CHECK = "custom_check"


class DataType(Enum):
    """Supported data types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    EMAIL = "email"
    URL = "url"
    UUID = "uuid"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ValidationField:
    """Field validation configuration."""

    name: str
    data_type: DataType
    rule: ValidationRule = ValidationRule.REQUIRED
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable[[Any], bool]] = None
    error_message: Optional[str] = None
    sanitize: bool = True
    default_value: Optional[Any] = None


@dataclass
class ValidationResult:
    """Validation result."""

    is_valid: bool
    errors: List[str]
    sanitized_data: (
        Dict[str, Any] | Any
    )  # Can be dict for full validation or single value for field validation
    warnings: List[str]


class SecurityValidator:
    """Security-focused validation for common attacks."""

    @staticmethod
    def validate_sql_injection(value: str) -> bool:
        """Check for SQL injection patterns."""
        sql_patterns = [
            r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(\-\-|\#|\/\*|\*\/)",
            r"(\b(XOR|LIKE|REGEXP|RLIKE)\b)",
            r"(\b(LOAD_FILE|INTO\s+OUTFILE|DUMPFILE)\b)",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        return True

    @staticmethod
    def validate_xss(value: str) -> bool:
        """Check for XSS patterns."""
        xss_patterns = [
            r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
            r"javascript\s*:",
            r"on\w+\s*=",
            r"<\s*iframe[^>]*>",
            r"<\s*object[^>]*>",
            r"<\s*embed[^>]*>",
            r"<\s*link[^>]*>",
            r"<\s*meta[^>]*>",
            r"<\s*img[^>]*on\w+",
            r"<\s*svg[^>]*>",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        return True

    @staticmethod
    def validate_path_traversal(value: str) -> bool:
        """Check for path traversal patterns."""
        traversal_patterns = [
            r"\.\.[\\/]",
            r"\.\.[\\/]\.\.[\\/]",
            r"%2e%2e[\\/]",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            r"\.\.%2f",
            r"\.\.%5c",
        ]

        for pattern in traversal_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        return True

    @staticmethod
    def validate_command_injection(value: str) -> bool:
        """Check for command injection patterns."""
        command_patterns = [
            r"[;&|`$(){}[\]]",
            r"\b(curl|wget|nc|netcat|telnet|ssh|ftp)\b",
            r"\b(rm|mv|cp|chmod|chown|kill|ps|top)\b",
            r"\b(python|perl|ruby|bash|sh|cmd|powershell)\b",
            r"\b(echo|cat|type|more|less)\b",
        ]

        for pattern in command_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        return True

    @staticmethod
    def sanitize_input(value: str) -> str:
        """Sanitize input by removing dangerous characters."""
        # Remove null bytes
        value = value.replace("\x00", "")

        # Normalize whitespace
        value = re.sub(r"\s+", " ", value).strip()

        # Remove control characters except newlines and tabs
        value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

        return value


class APIRequestValidator:
    """Comprehensive API request validator."""

    def __init__(self):
        self.security_validator = SecurityValidator()
        self.validation_schemas: Dict[str, List[ValidationField]] = {}
        self.global_validators: List[Callable] = []
        self.rate_limit_tracker: Dict[str, List[datetime]] = {}

    def register_schema(self, endpoint: str, fields: List[ValidationField]) -> None:
        """Register validation schema for an endpoint."""
        self.validation_schemas[endpoint] = fields
        logger.info(f"Registered validation schema for {endpoint}")

    def add_global_validator(self, validator: Callable) -> None:
        """Add global validator function."""
        self.global_validators.append(validator)

    def validate_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        method: str = "POST",
    ) -> ValidationResult:
        """Validate API request data."""
        errors: List[str] = []
        warnings: List[str] = []
        sanitized_data: Dict[str, Any] = {}

        try:
            # Get validation schema
            schema = self.validation_schemas.get(endpoint)
            if not schema:
                warnings.append(f"No validation schema found for {endpoint}")
                return ValidationResult(True, errors, data, warnings)

            # Validate each field
            for field in schema:
                field_result = self._validate_field(field, data)
                errors.extend(field_result.errors)
                warnings.extend(field_result.warnings)

                if field_result.is_valid and field_result.sanitized_data:
                    # For single field validation, sanitized_data contains the validated value
                    if isinstance(field_result.sanitized_data, dict):
                        sanitized_data.update(field_result.sanitized_data)
                    else:
                        sanitized_data[field.name] = field_result.sanitized_data

            # Apply global validators
            for validator in self.global_validators:
                try:
                    validator_result = validator(data, ip_address, user_agent)
                    if isinstance(validator_result, dict):
                        errors.extend(validator_result.get("errors", []))
                        warnings.extend(validator_result.get("warnings", []))
                except Exception as e:
                    logger.error(f"Global validator error: {e}")
                    errors.append("Validation system error")

            # Security checks
            security_errors = self._validate_security(data)
            errors.extend(security_errors)

            # Rate limiting check
            if ip_address:
                rate_limit_error = self._check_rate_limit(ip_address, endpoint)
                if rate_limit_error:
                    errors.append(rate_limit_error)

            is_valid = len(errors) == 0

            return ValidationResult(is_valid, errors, sanitized_data, warnings)

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(False, ["Validation system error"], {}, warnings)

    def _validate_field(
        self, field: ValidationField, data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate a single field."""
        errors = []
        warnings = []
        value = data.get(field.name)

        # Check if field exists
        if value is None:
            if field.rule == ValidationRule.REQUIRED:
                if field.default_value is not None:
                    value = field.default_value
                    warnings.append(f"Using default value for {field.name}")
                else:
                    return ValidationResult(
                        False, [f"{field.name} is required"], {}, warnings
                    )
            elif field.rule == ValidationRule.OPTIONAL:
                return ValidationResult(True, [], {}, warnings)
            else:
                return ValidationResult(True, [], {}, warnings)

        # Type validation
        type_error = self._validate_type(field, value)
        if type_error:
            return ValidationResult(False, [type_error], {}, warnings)

        # Convert to correct type
        try:
            value = self._convert_type(field.data_type, value)
        except Exception as e:
            return ValidationResult(
                False, [f"Invalid {field.name}: {str(e)}"], {}, warnings
            )

        # String-specific validations
        if field.data_type == DataType.STRING and isinstance(value, str):
            # Length validation
            if field.min_length and len(value) < field.min_length:
                errors.append(
                    f"{field.name} must be at least {field.min_length} characters"
                )

            if field.max_length and len(value) > field.max_length:
                errors.append(
                    f"{field.name} must be at most {field.max_length} characters"
                )

            # Pattern validation
            if field.pattern and not re.match(field.pattern, value):
                error_msg = field.error_message or f"{field.name} format is invalid"
                errors.append(error_msg)

            # Sanitization
            if field.sanitize:
                value = self.security_validator.sanitize_input(value)

        # Numeric range validation
        if isinstance(value, (int, float)):
            if field.min_value is not None and value < field.min_value:
                errors.append(f"{field.name} must be at least {field.min_value}")

            if field.max_value is not None and value > field.max_value:
                errors.append(f"{field.name} must be at most {field.max_value}")

        # Enum validation
        if field.enum_values and value not in field.enum_values:
            errors.append(
                f"{field.name} must be one of: {', '.join(map(str, field.enum_values))}"
            )

        # Custom validation
        if field.custom_validator:
            try:
                if not field.custom_validator(value):
                    error_msg = field.error_message or f"{field.name} validation failed"
                    errors.append(error_msg)
            except Exception as e:
                errors.append(f"Custom validation error for {field.name}: {str(e)}")

        return ValidationResult(len(errors) == 0, errors, value, warnings)  # type: ignore[arg-type]

    def _validate_type(self, field: ValidationField, value: Any) -> Optional[str]:
        """Validate field type."""
        if field.data_type == DataType.STRING:
            if not isinstance(value, str):
                return f"{field.name} must be a string"

        elif field.data_type == DataType.INTEGER:
            if not isinstance(value, int):
                try:
                    int(value)
                except (ValueError, TypeError):
                    return f"{field.name} must be an integer"

        elif field.data_type == DataType.FLOAT:
            if not isinstance(value, (int, float)):
                try:
                    float(value)
                except (ValueError, TypeError):
                    return f"{field.name} must be a number"

        elif field.data_type == DataType.BOOLEAN:
            if not isinstance(value, bool):
                if isinstance(value, str):
                    if value.lower() not in ["true", "false", "1", "0"]:
                        return f"{field.name} must be true or false"
                elif not isinstance(value, int):
                    return f"{field.name} must be a boolean"

        elif field.data_type == DataType.EMAIL:
            if not isinstance(value, str) or not self._is_valid_email(value):
                return f"{field.name} must be a valid email"

        elif field.data_type == DataType.URL:
            if not isinstance(value, str) or not self._is_valid_url(value):
                return f"{field.name} must be a valid URL"

        elif field.data_type == DataType.UUID:
            if not isinstance(value, str) or not self._is_valid_uuid(value):
                return f"{field.name} must be a valid UUID"

        elif field.data_type == DataType.DATE:
            if not isinstance(value, str) or not self._is_valid_date(value):
                return f"{field.name} must be a valid date (YYYY-MM-DD)"

        elif field.data_type == DataType.DATETIME:
            if not isinstance(value, str) or not self._is_valid_datetime(value):
                return f"{field.name} must be a valid datetime"

        elif field.data_type == DataType.JSON:
            if not isinstance(value, (str, dict, list)):
                return f"{field.name} must be valid JSON"
            if isinstance(value, str):
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    return f"{field.name} must be valid JSON"

        elif field.data_type == DataType.ARRAY:
            if not isinstance(value, list):
                return f"{field.name} must be an array"

        elif field.data_type == DataType.OBJECT:
            if not isinstance(value, dict):
                return f"{field.name} must be an object"

        return None

    def _convert_type(self, data_type: DataType, value: Any) -> Any:
        """Convert value to correct type."""
        if data_type == DataType.INTEGER:
            return int(value) if not isinstance(value, int) else value

        elif data_type == DataType.FLOAT:
            return float(value) if not isinstance(value, (int, float)) else value

        elif data_type == DataType.BOOLEAN:
            if isinstance(value, str):
                return value.lower() in ["true", "1"]
            elif isinstance(value, int):
                return bool(value)
            return value

        elif data_type == DataType.JSON:
            if isinstance(value, str):
                return json.loads(value)
            return value

        return value

    def _validate_security(self, data: Dict[str, Any]) -> List[str]:
        """Validate security constraints."""
        errors = []

        for key, value in data.items():
            if isinstance(value, str):
                # SQL Injection
                if not self.security_validator.validate_sql_injection(value):
                    errors.append(f"Potential SQL injection in {key}")

                # XSS
                if not self.security_validator.validate_xss(value):
                    errors.append(f"Potential XSS in {key}")

                # Path Traversal
                if not self.security_validator.validate_path_traversal(value):
                    errors.append(f"Potential path traversal in {key}")

                # Command Injection
                if not self.security_validator.validate_command_injection(value):
                    errors.append(f"Potential command injection in {key}")

        return errors

    def _check_rate_limit(self, ip_address: str, endpoint: str) -> Optional[str]:
        """Check rate limiting for IP address."""
        now = datetime.now()
        key = f"{ip_address}:{endpoint}"

        # Clean old entries (older than 1 hour)
        if key in self.rate_limit_tracker:
            self.rate_limit_tracker[key] = [
                timestamp
                for timestamp in self.rate_limit_tracker[key]
                if now - timestamp < timedelta(hours=1)
            ]
        else:
            self.rate_limit_tracker[key] = []

        # Check limit (100 requests per hour per IP per endpoint)
        if len(self.rate_limit_tracker[key]) >= 100:
            return "Rate limit exceeded"

        # Add current request
        self.rate_limit_tracker[key].append(now)

        return None

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _is_valid_uuid(self, uuid_str: str) -> bool:
        """Validate UUID format."""
        try:
            import uuid as uuid_lib

            uuid_lib.UUID(uuid_str)
            return True
        except ValueError:
            return False

    def _is_valid_date(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _is_valid_datetime(self, datetime_str: str) -> bool:
        """Validate datetime format (ISO 8601)."""
        try:
            datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False


# Common validation schemas
class CommonSchemas:
    """Common validation schemas for typical API endpoints."""

    @staticmethod
    def user_registration() -> List[ValidationField]:
        """User registration schema."""
        return [
            ValidationField(
                name="email",
                data_type=DataType.EMAIL,
                rule=ValidationRule.REQUIRED,
                max_length=255,
            ),
            ValidationField(
                name="password",
                data_type=DataType.STRING,
                rule=ValidationRule.REQUIRED,
                min_length=8,
                max_length=128,
                pattern=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]",
                error_message =
    "Password must contain at least 8 characters, including uppercase, lowercase, number, and special character",
            ),
            ValidationField(
                name="first_name",
                data_type=DataType.STRING,
                rule=ValidationRule.REQUIRED,
                min_length=1,
                max_length=50,
                pattern=r"^[a-zA-Z\s-']+$",
            ),
            ValidationField(
                name="last_name",
                data_type=DataType.STRING,
                rule=ValidationRule.REQUIRED,
                min_length=1,
                max_length=50,
                pattern=r"^[a-zA-Z\s-']+$",
            ),
        ]

    @staticmethod
    def user_login() -> List[ValidationField]:
        """User login schema."""
        return [
            ValidationField(
                name="email", data_type=DataType.EMAIL, rule=ValidationRule.REQUIRED
            ),
            ValidationField(
                name="password",
                data_type=DataType.STRING,
                rule=ValidationRule.REQUIRED,
                min_length=1,
            ),
        ]

    @staticmethod
    def job_application() -> List[ValidationField]:
        """Job application schema."""
        return [
            ValidationField(
                name="job_id", data_type=DataType.UUID, rule=ValidationRule.REQUIRED
            ),
            ValidationField(
                name="resume_url",
                data_type=DataType.URL,
                rule=ValidationRule.OPTIONAL,
                max_length=2048,
            ),
            ValidationField(
                name="cover_letter",
                data_type=DataType.STRING,
                rule=ValidationRule.OPTIONAL,
                max_length=5000,
            ),
            ValidationField(
                name="answers", data_type=DataType.JSON, rule=ValidationRule.OPTIONAL
            ),
        ]

    @staticmethod
    def profile_update() -> List[ValidationField]:
        """Profile update schema."""
        return [
            ValidationField(
                name="first_name",
                data_type=DataType.STRING,
                rule=ValidationRule.OPTIONAL,
                min_length=1,
                max_length=50,
                pattern=r"^[a-zA-Z\s-']+$",
            ),
            ValidationField(
                name="last_name",
                data_type=DataType.STRING,
                rule=ValidationRule.OPTIONAL,
                min_length=1,
                max_length=50,
                pattern=r"^[a-zA-Z\s-']+$",
            ),
            ValidationField(
                name="phone",
                data_type=DataType.STRING,
                rule=ValidationRule.OPTIONAL,
                max_length=20,
                pattern=r"^\+?[\d\s-()]+$",
            ),
            ValidationField(
                name="location",
                data_type=DataType.STRING,
                rule=ValidationRule.OPTIONAL,
                max_length=255,
            ),
            ValidationField(
                name="bio",
                data_type=DataType.STRING,
                rule=ValidationRule.OPTIONAL,
                max_length=2000,
            ),
        ]


# Global instance
api_validator = APIRequestValidator()

# Register common schemas
api_validator.register_schema("/auth/register", CommonSchemas.user_registration())
api_validator.register_schema("/auth/login", CommonSchemas.user_login())
api_validator.register_schema("/applications/submit", CommonSchemas.job_application())
api_validator.register_schema("/profile/update", CommonSchemas.profile_update())
