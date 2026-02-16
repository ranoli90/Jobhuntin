"""
AI Input Validation and Sanitization Module.

This module provides comprehensive validation and sanitization for all AI inputs
to prevent prompt injection, malicious content, and ensure data quality.
"""

from __future__ import annotations

import re
from typing import Any

from shared.logging_config import get_logger

logger = get_logger("sorce.api.ai_validation")


class AIValidationError(Exception):
    """Raised when AI input validation fails."""
    pass


class AIInputValidator:
    """Validates and sanitizes AI inputs."""
    
    # Patterns for detecting malicious content
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'eval\s*\(',  # eval() calls
        r'exec\s*\(',  # exec() calls
        r'system\s*\(',  # system() calls
        r'__import__',  # Python imports
        r'from\s+\w+\s+import',  # Python imports
        r'open\s*\(',  # File operations
        r'file\s*\(',  # File operations
        r'os\.',  # OS module calls
        r'subprocess\.',  # Subprocess calls
        r'pickle\.',  # Pickle operations
        r'base64',  # Base64 encoding
        r'rot13',  # ROT13 encoding
        r'caesar\s+cipher',  # Caesar cipher
        r'sql\s+injection',  # SQL injection
        r'union\s+select',  # SQL union
        r'drop\s+table',  # SQL drop
        r'insert\s+into',  # SQL insert
        r'update\s+set',  # SQL update
        r'delete\s+from',  # SQL delete
        r'<iframe[^>]*>',  # Iframe tags
        r'<object[^>]*>',  # Object tags
        r'<embed[^>]*>',  # Embed tags
        r'<link[^>]*>',  # Link tags
        r'<meta[^>]*>',  # Meta tags
        r'content-security-policy',  # CSP bypass
        r'cross-origin',  # CORS bypass
        r'access-control',  # CORS headers
        r'cookie\s*=',  # Cookie manipulation
        r'document\.cookie',  # Cookie access
        r'localStorage\.',  # LocalStorage access
        r'sessionStorage\.',  # SessionStorage access
        r'window\.',  # Window object access
        r'document\.',  # Document object access
        r'location\.',  # Location object access
        r'navigator\.',  # Navigator object access
    ]
    
    # Allowed characters for text input
    ALLOWED_CHARS = re.compile(r'^[a-zA-Z0-9\s\.,;:!?\'"()\-_\n\r@#$%&*+=/\\<>[\]{}|`~^]+$')
    
    # Length limits for different input types
    LENGTH_LIMITS = {
        'resume_text': 10000,
        'skills': 1000,
        'role': 100,
        'location': 100,
        'job_title': 100,
        'job_description': 5000,
        'company_name': 100,
        'question': 500,
        'answer': 1000,
        'general_text': 1000,
    }
    
    def __init__(self):
        self.malicious_pattern = re.compile(
            '|'.join(self.MALICIOUS_PATTERNS),
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
    
    def validate_and_sanitize(self, input_text: str, input_type: str = 'general_text') -> str:
        """
        Validate and sanitize AI input text.
        
        Args:
            input_text: The input text to validate
            input_type: Type of input for length validation
            
        Returns:
            Sanitized text
            
        Raises:
            AIValidationError: If validation fails
        """
        if not isinstance(input_text, str):
            raise AIValidationError("Input must be a string")
        
        # Check length limits
        max_length = self.LENGTH_LIMITS.get(input_type, self.LENGTH_LIMITS['general_text'])
        if len(input_text) > max_length:
            raise AIValidationError(f"Input too long for {input_type}. Max length: {max_length}")
        
        if len(input_text) == 0:
            raise AIValidationError("Input cannot be empty")
        
        # Check for malicious patterns
        if self.malicious_pattern.search(input_text):
            logger.warning(f"Malicious pattern detected in {input_type} input")
            raise AIValidationError("Input contains potentially malicious content")
        
        # Check for allowed characters
        if not self.ALLOWED_CHARS.fullmatch(input_text):
            logger.warning(f"Invalid characters detected in {input_type} input")
            # Sanitize by removing disallowed characters
            sanitized = re.sub(r'[^a-zA-Z0-9\s\.,;:!?\'"()\-_\n\r@#$%&*+=/\\<>[\]{}|`~^]', '', input_text)
            if len(sanitized) == 0:
                raise AIValidationError("Input contains only invalid characters")
            return sanitized
        
        # Normalize whitespace
        sanitized = self._normalize_whitespace(input_text)
        
        # Additional sanitization
        sanitized = self._sanitize_html(sanitized)
        sanitized = self._sanitize_urls(sanitized)
        sanitized = self._sanitize_code_like_content(sanitized)
        
        return sanitized
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML-like content."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z0-9#]+;', '', text)
        return text
    
    def _sanitize_urls(self, text: str) -> str:
        """Sanitize URLs and links."""
        # Remove http/https URLs
        text = re.sub(r'https?://[^\s]+', '', text)
        # Remove www URLs
        text = re.sub(r'www\.[^\s]+', '', text)
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        return text
    
    def _sanitize_code_like_content(self, text: str) -> str:
        """Sanitize code-like content."""
        # Remove common programming constructs
        text = re.sub(r'\bdef\s+\w+\s*\([^)]*\)\s*:', '', text)  # Function definitions
        text = re.sub(r'\bclass\s+\w+\s*:', '', text)  # Class definitions
        text = re.sub(r'\bimport\s+\w+', '', text)  # Import statements
        text = re.sub(r'\bfrom\s+\w+\s+import', '', text)  # From imports
        text = re.sub(r'\bprint\s*\(', '', text)  # Print statements
        text = re.sub(r'\breturn\s+', '', text)  # Return statements
        text = re.sub(r'\bif\s+.*:', '', text)  # If statements
        text = re.sub(r'\bfor\s+.*:', '', text)  # For loops
        text = re.sub(r'\bwhile\s+.*:', '', text)  # While loops
        text = re.sub(r'\btry\s*:', '', text)  # Try blocks
        text = re.sub(r'\bexcept\s+.*:', '', text)  # Except blocks
        text = re.sub(r'\bfinally\s*:', '', text)  # Finally blocks
        text = re.sub(r'\bwith\s+.*:', '', text)  # With statements
        return text
    
    def validate_email(self, email: str) -> str:
        """Validate and sanitize email address."""
        if not isinstance(email, str):
            raise AIValidationError("Email must be a string")
        
        email = email.strip().lower()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise AIValidationError("Invalid email format")
        
        # Check for suspicious domains
        suspicious_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[-1]
        if domain in suspicious_domains:
            raise AIValidationError("Suspicious email domain detected")
        
        return email
    
    def validate_skills_list(self, skills: list[str]) -> list[str]:
        """Validate and sanitize a list of skills."""
        if not isinstance(skills, list):
            raise AIValidationError("Skills must be a list")
        
        if len(skills) > 50:
            raise AIValidationError("Too many skills provided (max 50)")
        
        validated_skills = []
        for skill in skills:
            if not isinstance(skill, str):
                continue
            
            skill = skill.strip()
            if len(skill) == 0 or len(skill) > 50:
                continue
            
            # Validate and sanitize each skill
            try:
                sanitized_skill = self.validate_and_sanitize(skill, 'general_text')
                validated_skills.append(sanitized_skill)
            except AIValidationError:
                logger.warning(f"Invalid skill skipped: {skill}")
                continue
        
        return validated_skills
    
    def validate_job_ids_list(self, job_ids: list[str]) -> list[str]:
        """Validate and sanitize a list of job IDs."""
        if not isinstance(job_ids, list):
            raise AIValidationError("Job IDs must be a list")
        
        if len(job_ids) > 100:
            raise AIValidationError("Too many job IDs provided (max 100)")
        
        validated_ids = []
        for job_id in job_ids:
            if not isinstance(job_id, str):
                continue
            
            job_id = job_id.strip()
            if len(job_id) == 0 or len(job_id) > 50:
                continue
            
            # Check for valid ID format (alphanumeric with some special chars)
            if not re.match(r'^[a-zA-Z0-9_-]+$', job_id):
                logger.warning(f"Invalid job ID format skipped: {job_id}")
                continue
            
            validated_ids.append(job_id)
        
        return validated_ids
    
    def validate_experience_years(self, years: int) -> int:
        """Validate experience years."""
        if not isinstance(years, int):
            raise AIValidationError("Experience years must be an integer")
        
        if years < 0 or years > 50:
            raise AIValidationError("Experience years must be between 0 and 50")
        
        return years
    
    def validate_education_level(self, level: str) -> str:
        """Validate education level."""
        if not isinstance(level, str):
            raise AIValidationError("Education level must be a string")
        
        valid_levels = ['high_school', 'bachelor', 'master', 'phd', 'other']
        level = level.strip().lower()
        
        if level not in valid_levels:
            raise AIValidationError(f"Invalid education level. Must be one of: {', '.join(valid_levels)}")
        
        return level
    
    def validate_remote_preference(self, preference: bool) -> bool:
        """Validate remote preference."""
        if not isinstance(preference, bool):
            raise AIValidationError("Remote preference must be a boolean")
        
        return preference


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def validate_and_sanitize_ai_input(input_text: str, input_type: str = 'general_text') -> str:
    """
    Convenience function to validate and sanitize AI input.
    
    Args:
        input_text: The input text to validate
        input_type: Type of input for validation rules
        
    Returns:
        Sanitized text
        
    Raises:
        AIValidationError: If validation fails
    """
    validator = AIInputValidator()
    return validator.validate_and_sanitize(input_text, input_type)


def validate_ai_request_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate an entire AI request data dictionary.
    
    Args:
        data: Dictionary containing request data
        
    Returns:
        Validated and sanitized data dictionary
        
    Raises:
        AIValidationError: If validation fails
    """
    validator = AIInputValidator()
    validated_data = {}
    
    # Validate common fields
    if 'resume_text' in data:
        validated_data['resume_text'] = validator.validate_and_sanitize(data['resume_text'], 'resume_text')
    
    if 'skills' in data:
        validated_data['skills'] = validator.validate_skills_list(data['skills'])
    
    if 'role' in data:
        validated_data['role'] = validator.validate_and_sanitize(data['role'], 'role')
    
    if 'location' in data:
        validated_data['location'] = validator.validate_and_sanitize(data['location'], 'location')
    
    if 'experience_years' in data:
        validated_data['experience_years'] = validator.validate_experience_years(data['experience_years'])
    
    if 'education_level' in data:
        validated_data['education_level'] = validator.validate_education_level(data['education_level'])
    
    if 'remote_preference' in data:
        validated_data['remote_preference'] = validator.validate_remote_preference(data['remote_preference'])
    
    if 'job_ids' in data:
        validated_data['job_ids'] = validator.validate_job_ids_list(data['job_ids'])
    
    if 'email' in data:
        validated_data['email'] = validator.validate_email(data['email'])
    
    # Copy other fields without validation
    for key, value in data.items():
        if key not in validated_data:
            validated_data[key] = value
    
    return validated_data
