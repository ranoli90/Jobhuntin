"""AI Input Validation and Sanitization.

Provides comprehensive input validation for AI endpoints:
- Request size validation
- Prompt injection sanitization
- Rate limiting per user for AI operations
- Content validation for safety
"""

from __future__ import annotations

import hashlib
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from shared.logging_config import get_logger

logger = get_logger("sorce.ai_validation")


@dataclass
class ValidationResult:
    is_valid: bool
    sanitized_input: str | dict | None = None
    error_message: str | None = None
    error_code: str | None = None
    warnings: list[str] | None = None


class AIValidationConfig:
    MAX_PROFILE_SIZE = 50_000
    MAX_JOB_SIZE = 20_000
    MAX_TEXT_FIELD_SIZE = 10_000
    MAX_BATCH_SIZE = 20
    MIN_TEXT_LENGTH = 10

    PROMPT_INJECTION_PATTERNS = [
        (re.compile(r"\b(system|assistant|human|user)\s*:", re.I), "role_override"),
        (re.compile(r"###\s*(system|instruction)", re.I), "instruction_override"),
        (re.compile(r"##\s*(system|instruction)", re.I), "instruction_override"),
        (re.compile(r"#\s*(system|instruction)", re.I), "instruction_override"),
        (
            re.compile(r"ignore\s+(previous|prior|all)\s+(instruction|prompt)", re.I),
            "ignore_instruction",
        ),
        (
            re.compile(r"forget\s+(previous|prior|all)\s+(instruction|prompt)", re.I),
            "forget_instruction",
        ),
        (re.compile(r"disregard\s+(all|any|previous)", re.I), "disregard"),
        (re.compile(r"you\s+are\s+(now|a|an)\s+", re.I), "role_change"),
        (re.compile(r"act\s+as\s+(if|a|an)\s+", re.I), "act_as"),
        (re.compile(r"pretend\s+(to\s+be|you\s+are)\s+", re.I), "pretend"),
        (re.compile(r"output\s+(as|in)\s+json", re.I), "output_format"),
        (re.compile(r"respond\s+(as|in|with)\s+json", re.I), "output_format"),
        (re.compile(r"format\s+.*\s+json", re.I), "output_format"),
        (re.compile(r"execute\s+", re.I), "execute_command"),
        (re.compile(r"run\s+", re.I), "run_command"),
        (re.compile(r"\b(eval|exec|compile)\s*\(", re.I), "code_execution"),
        (re.compile(r"<\s*script", re.I), "script_injection"),
        (re.compile(r"javascript\s*:", re.I), "javascript_protocol"),
        (re.compile(r"on\w+\s*=", re.I), "event_handler"),
    ]

    SENSITIVE_DATA_PATTERNS = [
        (re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"), "email"),
        (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "phone"),
        (re.compile(r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b"), "ssn"),
        (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "credit_card"),
        (
            re.compile(
                r"\b(?:password|passwd|pwd|secret|api[_-]?key)\s*[=:]\s*\S+", re.I
            ),
            "credential",
        ),
    ]


def sanitize_for_ai(
    text: str, max_length: int = AIValidationConfig.MAX_TEXT_FIELD_SIZE
) -> ValidationResult:
    """Sanitize text input for AI processing.

    Removes or neutralizes prompt injection attempts and limits length.
    """
    if not isinstance(text, str):
        return ValidationResult(
            is_valid=False,
            error_message="Input must be a string",
            error_code="INVALID_TYPE",
        )

    warnings: list[str] = []

    if len(text) < AIValidationConfig.MIN_TEXT_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=f"Input too short. Minimum {AIValidationConfig.MIN_TEXT_LENGTH} characters.",
            error_code="INPUT_TOO_SHORT",
        )

    sanitized = text

    for pattern, pattern_type in AIValidationConfig.PROMPT_INJECTION_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            warnings.append(f"Detected potential {pattern_type} pattern")
            sanitized = pattern.sub("[REDACTED]", sanitized)

    if len(sanitized) > max_length:
        warnings.append(
            f"Input truncated from {len(sanitized)} to {max_length} characters"
        )
        sanitized = sanitized[:max_length] + "..."

    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)

    return ValidationResult(
        is_valid=True,
        sanitized_input=sanitized.strip(),
        warnings=warnings if warnings else None,
    )


def sanitize_dict_for_ai(
    data: dict[str, Any],
    max_size: int = AIValidationConfig.MAX_PROFILE_SIZE,
) -> ValidationResult:
    """Recursively sanitize all string values in a dictionary for AI processing."""
    if not isinstance(data, dict):
        return ValidationResult(
            is_valid=False,
            error_message="Input must be a dictionary",
            error_code="INVALID_TYPE",
        )

    import json

    try:
        data_size = len(json.dumps(data))
        if data_size > max_size:
            return ValidationResult(
                is_valid=False,
                error_message=f"Input too large ({data_size} bytes). Maximum {max_size} bytes.",
                error_code="INPUT_TOO_LARGE",
            )
    except (TypeError, ValueError) as e:
        return ValidationResult(
            is_valid=False,
            error_message=f"Input serialization failed: {e}",
            error_code="SERIALIZATION_ERROR",
        )

    warnings: list[str] = []

    def sanitize_value(value: Any, path: str = "") -> Any:
        nonlocal warnings

        if isinstance(value, str):
            result = sanitize_for_ai(value, AIValidationConfig.MAX_TEXT_FIELD_SIZE)
            if result.warnings:
                warnings.extend([f"{path}: {w}" for w in result.warnings])
            return (
                result.sanitized_input
                if result.is_valid
                else value[: AIValidationConfig.MAX_TEXT_FIELD_SIZE]
            )

        elif isinstance(value, dict):
            return {
                k: sanitize_value(v, f"{path}.{k}" if path else k)
                for k, v in value.items()
            }

        elif isinstance(value, list):
            return [
                sanitize_value(item, f"{path}[{i}]") for i, item in enumerate(value)
            ]

        else:
            return value

    sanitized = sanitize_value(data)

    return ValidationResult(
        is_valid=True,
        sanitized_input=sanitized,
        warnings=warnings if warnings else None,
    )


def validate_ai_request_size(
    profile: dict | None = None,
    job: dict | None = None,
    jobs: list[dict] | None = None,
    additional_text: str | None = None,
) -> ValidationResult:
    """Validate the total size of an AI request."""
    import json

    total_size = 0
    components: dict[str, int] = {}

    if profile:
        profile_size = len(json.dumps(profile))
        if profile_size > AIValidationConfig.MAX_PROFILE_SIZE:
            return ValidationResult(
                is_valid=False,
                error_message=f"Profile too large ({profile_size} bytes). Maximum {AIValidationConfig.MAX_PROFILE_SIZE} bytes.",
                error_code="PROFILE_TOO_LARGE",
            )
        components["profile"] = profile_size
        total_size += profile_size

    if job:
        job_size = len(json.dumps(job))
        if job_size > AIValidationConfig.MAX_JOB_SIZE:
            return ValidationResult(
                is_valid=False,
                error_message=f"Job data too large ({job_size} bytes). Maximum {AIValidationConfig.MAX_JOB_SIZE} bytes.",
                error_code="JOB_TOO_LARGE",
            )
        components["job"] = job_size
        total_size += job_size

    if jobs:
        if len(jobs) > AIValidationConfig.MAX_BATCH_SIZE:
            return ValidationResult(
                is_valid=False,
                error_message=f"Too many jobs in batch ({len(jobs)}). Maximum {AIValidationConfig.MAX_BATCH_SIZE}.",
                error_code="BATCH_TOO_LARGE",
            )

        for i, j in enumerate(jobs):
            job_size = len(json.dumps(j))
            if job_size > AIValidationConfig.MAX_JOB_SIZE:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Job {i} too large ({job_size} bytes). Maximum {AIValidationConfig.MAX_JOB_SIZE} bytes.",
                    error_code="JOB_TOO_LARGE",
                )
            total_size += job_size

        components["jobs"] = len(jobs)

    if additional_text:
        text_size = len(additional_text)
        if text_size > AIValidationConfig.MAX_TEXT_FIELD_SIZE:
            return ValidationResult(
                is_valid=False,
                error_message=f"Text field too large ({text_size} bytes). Maximum {AIValidationConfig.MAX_TEXT_FIELD_SIZE} bytes.",
                error_code="TEXT_TOO_LARGE",
            )
        components["text"] = text_size
        total_size += text_size

    return ValidationResult(
        is_valid=True,
        sanitized_input={"total_size": total_size, "components": components},
    )


def detect_pii(text: str) -> list[dict[str, Any]]:
    """Detect potential PII in text.

    Returns list of detected PII types with locations.
    """
    detected = []

    for pattern, pii_type in AIValidationConfig.SENSITIVE_DATA_PATTERNS:
        for match in pattern.finditer(text):
            detected.append(
                {
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "value_hash": hashlib.sha256(match.group().encode()).hexdigest()[
                        :8
                    ],
                }
            )

    return detected


def mask_pii(text: str) -> tuple[str, list[str]]:
    """Mask detected PII in text.

    Returns masked text and list of masked PII types.
    """
    masked_text = text
    masked_types: set[str] = set()

    for pattern, pii_type in AIValidationConfig.SENSITIVE_DATA_PATTERNS:
        if pattern.search(masked_text):
            masked_text = pattern.sub(f"[{pii_type.upper()}_REDACTED]", masked_text)
            masked_types.add(pii_type)

    return masked_text, list(masked_types)


class AIRateLimiter:
    """Per-user rate limiter for AI operations.

    Tracks:
    - Requests per minute
    - Requests per hour
    - Concurrent requests
    """

    def __init__(self) -> None:
        self._requests_per_minute: dict[str, list[float]] = defaultdict(list)
        self._requests_per_hour: dict[str, list[float]] = defaultdict(list)
        self._concurrent: dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def check_rate_limit(
        self,
        user_id: str,
        tier: str = "FREE",
        operation: str = "ai",
    ) -> tuple[bool, dict[str, Any]]:
        from shared.tenant_rate_limit import TenantTier, get_tier_limits

        tier_enum = TenantTier(tier.upper()) if isinstance(tier, str) else tier
        limits = get_tier_limits(tier_enum)

        now = time.monotonic()
        minute_key = f"{user_id}:{operation}:minute"
        hour_key = f"{user_id}:{operation}:hour"

        with self._lock:
            minute_cutoff = now - 60
            self._requests_per_minute[minute_key][:] = [
                t for t in self._requests_per_minute[minute_key] if t > minute_cutoff
            ]

            hour_cutoff = now - 3600
            self._requests_per_hour[hour_key][:] = [
                t for t in self._requests_per_hour[hour_key] if t > hour_cutoff
            ]

            minute_count = len(self._requests_per_minute[minute_key])
            hour_count = len(self._requests_per_hour[hour_key])

            if minute_count >= limits.requests_per_minute:
                return False, {
                    "reason": "minute_limit",
                    "limit": limits.requests_per_minute,
                    "current": minute_count,
                    "reset_in": 60,
                }

            if hour_count >= limits.requests_per_hour:
                return False, {
                    "reason": "hour_limit",
                    "limit": limits.requests_per_hour,
                    "current": hour_count,
                    "reset_in": 3600,
                }

            self._requests_per_minute[minute_key].append(now)
            self._requests_per_hour[hour_key].append(now)

            return True, {
                "minute_remaining": limits.requests_per_minute - minute_count - 1,
                "hour_remaining": limits.requests_per_hour - hour_count - 1,
            }

    def acquire_concurrent(self, user_id: str, tier: str = "FREE") -> tuple[bool, int]:
        from shared.tenant_rate_limit import TenantTier, get_tier_limits

        tier_enum = TenantTier(tier.upper()) if isinstance(tier, str) else tier
        limits = get_tier_limits(tier_enum)

        with self._lock:
            current = self._concurrent.get(user_id, 0)
            if current >= limits.concurrent_requests:
                return False, current

            self._concurrent[user_id] = current + 1
            return True, current + 1

    def release_concurrent(self, user_id: str) -> None:
        with self._lock:
            current = self._concurrent.get(user_id, 0)
            if current > 0:
                self._concurrent[user_id] = current - 1


import threading

_ai_rate_limiter: AIRateLimiter | None = None
_ai_rate_limiter_lock = threading.Lock()


def get_ai_rate_limiter() -> AIRateLimiter:
    global _ai_rate_limiter

    with _ai_rate_limiter_lock:
        if _ai_rate_limiter is None:
            _ai_rate_limiter = AIRateLimiter()
        return _ai_rate_limiter


def validate_and_sanitize_ai_input(
    profile: dict | None = None,
    job: dict | None = None,
    jobs: list[dict] | None = None,
    text_fields: dict[str, str] | None = None,
    user_id: str | None = None,
    tier: str = "FREE",
) -> ValidationResult:
    """Comprehensive validation and sanitization for AI inputs.

    Performs:
    1. Size validation
    2. Prompt injection detection and sanitization
    3. PII detection and masking
    4. Rate limiting check

    Returns sanitized inputs ready for AI processing.
    """
    size_result = validate_ai_request_size(profile, job, jobs)
    if not size_result.is_valid:
        return size_result

    warnings: list[str] = []
    sanitized_data: dict[str, Any] = {}

    if profile:
        profile_result = sanitize_dict_for_ai(
            profile, AIValidationConfig.MAX_PROFILE_SIZE
        )
        if not profile_result.is_valid:
            return profile_result
        sanitized_data["profile"] = profile_result.sanitized_input
        if profile_result.warnings:
            warnings.extend(profile_result.warnings)

    if job:
        job_result = sanitize_dict_for_ai(job, AIValidationConfig.MAX_JOB_SIZE)
        if not job_result.is_valid:
            return job_result
        sanitized_data["job"] = job_result.sanitized_input
        if job_result.warnings:
            warnings.extend(job_result.warnings)

    if jobs:
        sanitized_jobs = []
        for i, j in enumerate(jobs):
            job_result = sanitize_dict_for_ai(j, AIValidationConfig.MAX_JOB_SIZE)
            if not job_result.is_valid:
                job_result.error_message = f"Job {i}: {job_result.error_message}"
                return job_result
            sanitized_jobs.append(job_result.sanitized_input)
            if job_result.warnings:
                warnings.extend([f"Job {i}: {w}" for w in job_result.warnings])
        sanitized_data["jobs"] = sanitized_jobs

    if text_fields:
        sanitized_texts = {}
        for field_name, text in text_fields.items():
            text_result = sanitize_for_ai(text)
            if not text_result.is_valid:
                text_result.error_message = (
                    f"Field '{field_name}': {text_result.error_message}"
                )
                return text_result
            sanitized_texts[field_name] = text_result.sanitized_input
            if text_result.warnings:
                warnings.extend([f"{field_name}: {w}" for w in text_result.warnings])
        sanitized_data["text_fields"] = sanitized_texts

    if user_id:
        rate_limiter = get_ai_rate_limiter()
        allowed, rate_info = rate_limiter.check_rate_limit(user_id, tier, "ai")
        if not allowed:
            return ValidationResult(
                is_valid=False,
                error_message=f"Rate limit exceeded: {rate_info.get('reason', 'unknown')}. Try again in {rate_info.get('reset_in', 60)} seconds.",
                error_code="RATE_LIMIT_EXCEEDED",
            )
        sanitized_data["rate_limit_info"] = rate_info

    return ValidationResult(
        is_valid=True,
        sanitized_input=sanitized_data,
        warnings=warnings if warnings else None,
    )
