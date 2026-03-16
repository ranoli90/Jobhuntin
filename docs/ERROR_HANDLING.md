# Error Handling & Response Format

This document describes the standardized error handling system in the JobHuntin API.

## Overview

The [`shared/error_responses.py`](shared/error_responses.py) module provides:
- Standard error codes for consistent error handling
- Custom exception classes for different error types
- FastAPI exception handlers for automatic error formatting
- Helper functions for creating standardized error responses

## Error Response Format

All API errors follow a consistent JSON format:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": [
            {
                "field": "email",
                "message": "Invalid email format"
            }
        ]
    },
    "request_id": "abc-123",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Codes

Standard error codes are defined in the `ErrorCodes` class:

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `INVALID_INPUT` | 400 | Invalid input data |
| `MISSING_FIELD` | 400 | Required field missing |
| `INVALID_FORMAT` | 400 | Invalid format |
| `AUTHENTICATION_FAILED` | 401 | Authentication failed |
| `INVALID_TOKEN` | 401 | Invalid or malformed token |
| `TOKEN_EXPIRED` | 401 | Token has expired |
| `MISSING_CREDENTIALS` | 401 | No credentials provided |
| `AUTHORIZATION_FAILED` | 403 | Authorization failed |
| `ACCESS_DENIED` | 403 | Access denied |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks permissions |
| `TENANT_ACCESS_DENIED` | 403 | Tenant scope violation |
| `RESOURCE_NOT_FOUND` | 404 | Resource not found |
| `USER_NOT_FOUND` | 404 | User not found |
| `JOB_NOT_FOUND` | 404 | Job not found |
| `APPLICATION_NOT_FOUND` | 404 | Application not found |
| `CONFLICT` | 409 | Resource conflict |
| `DUPLICATE_RESOURCE` | 409 | Duplicate entry |
| `INVALID_STATE` | 409 | Invalid state transition |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `EXTERNAL_SERVICE_ERROR` | 502 | External service failed |
| `CONFIGURATION_ERROR` | 500 | Configuration error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Custom Exceptions

### APIError

Base exception for all API errors.

```python
from shared.error_responses import APIError, ErrorCodes

raise APIError(
    code=ErrorCodes.VALIDATION_ERROR,
    message="Invalid input",
    details=[ErrorDetail(field="email", message="Invalid format")]
)
```

### ValidationError

For validation errors (400 Bad Request).

```python
from shared.error_responses import ValidationError, ErrorDetail

# With field errors dict
raise ValidationError(
    message="Validation failed",
    field_errors={"email": "Invalid format", "name": "Required"}
)

# With details list
raise ValidationError(
    message="Validation failed",
    details=[ErrorDetail(field="email", message="Invalid format")]
)
```

### AuthenticationError

For authentication errors (401 Unauthorized).

```python
from shared.error_responses import AuthenticationError

raise AuthenticationError("Invalid credentials")
raise AuthenticationError("Token expired", code="TOKEN_EXPIRED")
```

### AuthorizationError

For authorization errors (403 Forbidden).

```python
from shared.error_responses import AuthorizationError

raise AuthorizationError("Admin access required")
```

### NotFoundError

For resource not found errors (404 Not Found).

```python
from shared.error_responses import NotFoundError

raise NotFoundError("User", "123")  # "User not found: 123"
raise NotFoundError("Job")          # "Job not found"
```

### ConflictError

For conflict errors (409 Conflict).

```python
from shared.error_responses import ConflictError

raise ConflictError("Email already registered")
```

### RateLimitError

For rate limiting (429 Too Many Requests).

```python
from shared.error_responses import RateLimitError

raise RateLimitError(retry_after=60)
```

### InternalError

For internal server errors (500 Internal Server Error).

```python
from shared.error_responses import InternalError

raise InternalError("Database connection failed")
```

### ConfigurationError

For server configuration errors (500).

```python
from shared.error_responses import ConfigurationError

raise ConfigurationError("Redis not configured")
```

### ServiceUnavailableError

For service unavailable (503).

```python
from shared.error_responses import ServiceUnavailableError

raise ServiceUnavailableError(retry_after=30)
```

## Registering Exception Handlers

In your FastAPI application, register the exception handlers:

```python
from fastapi import FastAPI
from shared.error_responses import register_exception_handlers

app = FastAPI()

# Register custom exception handlers
register_exception_handlers(app)
```

This enables automatic standardized error responses for all exceptions.

## Usage in Endpoints

### Basic Usage

```python
from fastapi import APIRouter
from shared.error_responses import NotFoundError, ValidationError

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await fetch_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user

@router.post("/users")
async def create_user(user_data: UserCreate):
    if not user_data.email:
        raise ValidationError(
            message="Email is required",
            field_errors={"email": "Required"}
        )
    return await create_user(user_data)
```

### With Error Detail

```python
from shared.error_responses import ValidationError, ErrorDetail

@router.post("/jobs")
async def create_job(job_data: JobCreate):
    errors = []
    
    if not job_data.title:
        errors.append(ErrorDetail(field="title", message="Title is required"))
    if job_data.salary_min and job_data.salary_max:
        if job_data.salary_min > job_data.salary_max:
            errors.append(ErrorDetail(
                field="salary",
                message="Min salary cannot exceed max salary"
            ))
    
    if errors:
        raise ValidationError(
            message="Job validation failed",
            details=errors
        )
```

## Response Models

### ErrorResponse

Main error response model:

```python
from shared.error_responses import ErrorResponse, ErrorInfo, ErrorDetail

response = ErrorResponse(
    error=ErrorInfo(
        code="VALIDATION_ERROR",
        message="Invalid input",
        details=[
            ErrorDetail(field="email", message="Invalid format")
        ]
    ),
    request_id="abc-123"
)
# Returns:
# {
#     "error": {
#         "code": "VALIDATION_ERROR",
#         "message": "Invalid input",
#         "details": [{"field": "email", "message": "Invalid format"}]
#     },
#     "request_id": "abc-123",
#     "timestamp": "2024-01-15T10:30:00Z"
# }
```

### APIError.to_response()

Convert an exception to response dict:

```python
exc = ValidationError("Invalid input")
response = exc.to_response(request_id="abc-123")
```

## Best Practices

### DO
- ✅ Use appropriate exception classes for different error types
- ✅ Provide meaningful error messages
- ✅ Include field-level details for validation errors
- ✅ Use standardized error codes
- ✅ Register exception handlers in main.py

### DON'T
- ❌ Return raw HTTPException with string detail
- ❌ Use inconsistent error formats
- ❌ Expose internal error details to users
- ❌ Hardcode error messages in endpoints (use constants)
- ❌ Forget to handle database/redis connection errors

## Testing

Run error response tests:

```bash
PYTHONPATH=apps:packages:. pytest tests/test_error_responses.py -v
```

## Related Documentation

- [Production Auth & CSRF](PRODUCTION_AUTH_CSRF.md) - Authentication error handling
- [API Versioning](API_VERSIONING.md) - Version-specific error handling
- [Pagination](shared/pagination.py) - Pagination error handling
