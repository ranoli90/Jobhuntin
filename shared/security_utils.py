"""Shared security utilities for common validation and sanitization patterns.

This module provides reusable security functions that are used across multiple
modules to reduce code duplication and ensure consistent security behavior.

Key utilities:
- IP address validation (private/loopback detection)
- Email validation
- URL validation
- Input sanitization
- Common security patterns

Usage:
    from shared.security_utils import (
        is_private_ip,
        validate_email_format,
        validate_url_format,
        sanitize_input,
    )
"""

from __future__ import annotations

import ipaddress
import re
import socket
from typing import Optional

# Email validation regex pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# URL validation regex pattern (supports HTTP/HTTPS, localhost, IP addresses)
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?"  # domain
    r"|localhost|"  # localhost
    r"|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def is_private_ip(hostname: str) -> bool:
    """Check if a hostname resolves to a private or reserved IP address.

    This function performs DNS resolution and checks if the resulting IP
    is in any of the following categories:
    - Private IPs (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Loopback (127.0.0.0/8, ::1)
    - Link-local (169.254.0.0/16, fe80::/10)
    - Reserved IPs

    Args:
        hostname: The hostname to check (e.g., "example.com", "192.168.1.1")

    Returns:
        True if the hostname resolves to a private/reserved IP, False otherwise

    Example:
        >>> is_private_ip("192.168.1.1")
        True
        >>> is_private_ip("example.com")
        False
    """
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_reserved
            or ip.is_link_local
        )
    except (socket.gaierror, ValueError):
        # If we can't resolve, assume it's not private
        # The caller should handle the resolution failure separately
        return False


def is_safe_redirect_url(url: str, allowed_origins: list[str]) -> bool:
    """Validate that a URL is within allowed origins for redirect.

    This prevents open redirect attacks by ensuring the URL starts with
    an allowed origin.

    Args:
        url: The URL to validate
        allowed_origins: List of allowed origin URLs (e.g., ["https://example.com"])

    Returns:
        True if the URL is safe, False otherwise

    Example:
        >>> is_safe_redirect_url("https://example.com/dashboard", ["https://example.com"])
        True
        >>> is_safe_redirect_url("https://evil.com", ["https://example.com"])
        False
    """
    if not url or not allowed_origins:
        return False

    for origin in allowed_origins:
        # Exact match
        if url == origin:
            return True
        # Prefix match with path separator
        if url.startswith(origin) and len(url) > len(origin) and url[len(origin)] in (
            "/",
            "?",
        ):
            return True

    return False


def validate_email_format(email: str) -> bool:
    """Validate email format using a standard pattern.

    This is a lightweight validation that checks format only.
    For more comprehensive validation, use domain-specific validators.

    Args:
        email: The email address to validate

    Returns:
        True if the email format is valid, False otherwise

    Example:
        >>> validate_email_format("user@example.com")
        True
        >>> validate_email_format("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_PATTERN.match(email))


def validate_url_format(
    url: str,
    require_https: bool = True,
    allow_localhost: bool = True,
) -> bool:
    """Validate URL format using standard patterns.

    Args:
        url: The URL to validate
        require_https: If True, only HTTPS URLs are valid (default True)
        allow_localhost: If True, localhost URLs are valid (default True)

    Returns:
        True if the URL format is valid, False otherwise

    Example:
        >>> validate_url_format("https://example.com/path")
        True
        >>> validate_url_format("http://example.com", require_https=True)
        False
        >>> validate_url_format("http://localhost:8080", allow_localhost=True)
        True
    """
    if not url or not isinstance(url, str):
        return False

    # Check HTTPS requirement
    if require_https and not url.startswith("https://"):
        return False

    # Check localhost allowance
    if not allow_localhost and "localhost" in url.lower():
        return False

    return bool(URL_PATTERN.match(url))


def sanitize_input(value: str) -> str:
    """Sanitize input by removing dangerous characters.

    This provides basic sanitization for user input:
    - Removes null bytes
    - Normalizes whitespace
    - Removes control characters (except newlines and tabs)

    Args:
        value: The input string to sanitize

    Returns:
        The sanitized string

    Example:
        >>> sanitize_input("hello\\x00 world")
        'hello world'
    """
    if not value or not isinstance(value, str):
        return ""

    # Remove null bytes
    value = value.replace("\x00", "")

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value).strip()

    # Remove control characters except newlines and tabs
    value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

    return value


def check_injection_characters(value: str) -> bool:
    """Check for null bytes and other injection characters in a string.

    Args:
        value: The string to check

    Returns:
        True if dangerous characters are found, False otherwise

    Example:
        >>> check_injection_characters("safe\\x00string")
        True
        >>> check_injection_characters("safe string")
        False
    """
    # Null byte injection
    if "\x00" in value:
        return True

    # Newline and carriage return injection
    if "\n" in value or "\r" in value:
        return True

    # Check for other control characters (ASCII 0-31, except tab)
    for char in value:
        if ord(char) < 32 and char not in "\t":
            return True

    return False
