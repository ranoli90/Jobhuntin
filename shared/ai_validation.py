from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ValidationResult:
    """Result of AI input validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    sanitized_input: dict[str, Any] = field(default_factory=dict)


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.

    Removes or escapes potentially dangerous patterns that could manipulate LLM behavior.
    """
    if not isinstance(text, str):
        return str(text)

    # Remove or escape common prompt injection patterns
    dangerous_patterns = [
        # System prompt overrides
        r"\n(system|assistant|human|user):",
        r"\n### ",
        r"\n## ",
        r"\n# ",
        # Instruction overrides
        r"ignore (previous|prior|all) instructions",
        r"forget (previous|prior|all) instructions",
        r"do not follow",
        r"disregard",
        # Role changes
        r"you are (not|a)",
        r"act as",
        r"pretend to be",
        # Output format changes
        r"output (as|in) json",
        r"respond (as|in|with) json",
        r"format.*json",
        # Dangerous commands
        r"execute",
        r"run",
        r"system",
        r"command",
    ]

    sanitized = text

    # Remove dangerous patterns (case insensitive)
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    # Limit length to prevent extremely long inputs
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    # Escape remaining newlines that could break prompt structure
    sanitized = sanitized.replace("\n\n", "\n").replace("\n\n", "\n")

    return sanitized.strip()


def validate_and_sanitize_ai_input(*args: Any, **kwargs: Any) -> Any:
    """
    Polymorphic validation function to handle inconsistent usage across the codebase.
    
    Usage 1: validate_and_sanitize_ai_input(text_string) -> str
    Usage 2: validate_and_sanitize_ai_input(profile=..., user_id=...) -> ValidationResult
    """
    # Case 1: Single string argument (sanitization only)
    if len(args) == 1 and isinstance(args[0], str):
        return sanitize_input(args[0])
    
    if len(args) == 1 and args[0] is None:
        return ""

    # Case 2: Profile validation (kwargs)
    if "profile" in kwargs:
        profile = kwargs["profile"]
        # Basic validation logic (placeholder)
        if not isinstance(profile, dict):
             return ValidationResult(is_valid=False, error_message="Profile must be a dictionary")
        
        # Pass through as valid for now to unblock
        return ValidationResult(
            is_valid=True,
            sanitized_input=kwargs
        )

    # Fallback
    return args[0] if args else None
