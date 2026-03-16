"""Secure path validation utilities to prevent path traversal attacks.

This module provides robust protection against path traversal vulnerabilities
including URL encoding, double encoding, and other bypass attempts.
"""

from pathlib import Path
import urllib.parse
from typing import Union

from shared.logging_config import get_logger

logger = get_logger("sorce.path_security")

# Characters that are never allowed in paths
NULL_BYTE = "\x00"


class SecurityError(ValueError):
    """Exception raised for security violations in path operations."""
    pass


class PathTraversalError(SecurityError):
    """Exception raised when a path traversal attempt is detected."""
    pass


def decode_path_fully(encoded_path: str, max_iterations: int = 5) -> str:
    """Decode a path that may contain multiple layers of URL encoding.
    
    Handles single, double, triple, and higher levels of URL encoding.
    
    Args:
        encoded_path: The potentially URL-encoded path
        max_iterations: Maximum decoding iterations to prevent infinite loops
        
    Returns:
        The fully decoded path
    """
    decoded = encoded_path
    for _ in range(max_iterations):
        new_decoded = urllib.parse.unquote(decoded)
        if new_decoded == decoded:
            break
        decoded = new_decoded
    return decoded


def _check_injection_characters(path: str) -> bool:
    """Check for null bytes and other injection characters in path.
    
    Args:
        path: The path to check
        
    Returns:
        True if dangerous characters are found, False otherwise
    """
    # Null byte injection - can truncate paths in some systems
    if NULL_BYTE in path:
        return True
    
    # Newline and carriage return injection
    if "\n" in path or "\r" in path:
        return True
    
    # Check for other control characters (ASCII 0-31)
    for char in path:
        if ord(char) < 32 and char not in "\t":
            return True
    
    return False


def secure_path(
    base_dir: Union[str, Path],
    user_path: str,
    allow_absolute: bool = False,
) -> Path:
    """Securely resolve and validate a path within an allowed base directory.
    
    This is the PRIMARY method for path security. It uses pathlib.Path.resolve()
    to resolve symlinks and relative paths, then validates the resolved path
    is within the allowed base directory.
    
    Args:
        base_dir: The base directory that all paths must be within
        user_path: The user-provided path to validate
        allow_absolute: If True, allow absolute paths (they will still be
                       validated to be within base_dir)
                       
    Returns:
        The validated, resolved Path object
        
    Raises:
        SecurityError: If the path contains injection attempts or is unsafe
        PathTraversalError: If the path attempts to escape the base directory
        ValueError: If the path is invalid for other reasons
    
    Example:
        >>> path = secure_path("/var/www/uploads", "user/file.pdf")
        >>> # Returns resolved Path within /var/www/uploads
        >>> # Raises SecurityError or PathTraversalError for attacks
    """
    if not user_path:
        raise ValueError("Path cannot be empty")
    
    # Step 1: Check for injection characters BEFORE any processing
    if _check_injection_characters(user_path):
        logger.warning(
            "Security violation: injection characters detected in path",
            extra={"user_path": repr(user_path[:100])}
        )
        raise SecurityError(
            "Path contains invalid characters: null bytes, newlines, or control characters"
        )
    
    # Step 2: Convert base_dir to Path and resolve to absolute
    base = Path(base_dir).resolve()
    
    # Step 3: Check for traversal patterns in the raw input (early detection)
    if contains_traversal_patterns(user_path):
        logger.warning(
            "Security violation: path traversal pattern detected in raw path",
            extra={"user_path": user_path[:100]}
        )
        raise PathTraversalError(
            "Path traversal detected: invalid characters in path"
        )
    
    # Step 4: Fully decode the path to catch encoded traversal attempts
    decoded_path = decode_path_fully(user_path)
    
    # Step 5: Check for traversal patterns in the decoded path
    if contains_traversal_patterns(decoded_path):
        logger.warning(
            "Security violation: path traversal pattern detected after decoding",
            extra={"user_path": user_path[:100]}
        )
        raise PathTraversalError(
            "Path traversal detected: encoded traversal attempt blocked"
        )
    
    # Step 6: Check for injection in decoded path
    if _check_injection_characters(decoded_path):
        logger.warning(
            "Security violation: injection characters detected after decoding",
            extra={"user_path": repr(decoded_path[:100])}
        )
        raise SecurityError(
            "Path contains invalid characters after decoding"
        )
    
    # Step 7: Check for absolute path if not allowed
    if not allow_absolute:
        decoded_path_obj = Path(decoded_path)
        if decoded_path_obj.is_absolute():
            logger.warning(
                "Security violation: absolute path not allowed",
                extra={"user_path": user_path[:100]}
            )
            raise PathTraversalError(
                "Absolute paths are not allowed"
            )
    
    # Step 8: Construct the full path and resolve it using Path.resolve()
    # This resolves symlinks and relative paths to absolute paths
    target = (base / decoded_path).resolve()
    
    # Step 9: CRITICAL - Verify the resolved path is within the base directory
    # Using Path.resolve() ensures we check the actual filesystem path
    # after all symlinks and relative components are resolved
    try:
        target.relative_to(base)
    except ValueError:
        logger.warning(
            "Security violation: path traversal attempt - resolved path outside base directory",
            extra={
                "base_dir": str(base),
                "user_path": user_path[:100],
                "resolved_path": str(target)
            }
        )
        raise PathTraversalError(
            f"Path traversal detected: resolved path '{target}' escapes base directory '{base}'"
        )
    
    return target


def contains_traversal_patterns(path: str) -> bool:
    """Check if a path contains any path traversal patterns.
    
    This checks the raw path string for common traversal patterns
    before any decoding occurs. It specifically looks for ".." as a
    path segment (preceded or followed by path separators).
    
    Args:
        path: The path to check
        
    Returns:
        True if traversal patterns are detected, False otherwise
    """
    # Normalize to lowercase for case-insensitive matching
    lower_path = path.lower()
    
    # Check for ".." as a path segment (not part of a filename like "file...pdf")
    # We check for .. at start, or preceded/followed by path separators
    import re
    
    # Pattern matches:
    # - ../ at start
    # - /../ anywhere
    # - ..\ at start (Windows)
    # - \..\ anywhere (Windows)
    # - .. at end
    traversal_segment_pattern = r'(?:^|[\\/])\.\.(?:[\\/]|$)'
    if re.search(traversal_segment_pattern, lower_path):
        return True
    
    # Check for various encodings of ".." that could be used for traversal
    # These are always suspicious regardless of context
    traversal_indicators = [
        "%2e%2e",       # URL encoded ..
        "%2e.",         # Partially encoded
        ".%2e",         # Partially encoded
        "%252e",        # Double encoded .
        "%252e%252e",   # Double encoded ..
        "%c0%ae",       # Overlong UTF-8 encoding of .
        "%c1%9c",       # Overlong UTF-8 encoding of \
        "%c0%af",       # Overlong UTF-8 encoding of /
        "%e0%80%af",    # Overlong UTF-8 encoding of /
        "%c0%2e",       # Mixed encoding
    ]
    
    for indicator in traversal_indicators:
        if indicator in lower_path:
            return True
    
    return False


def validate_path(
    base_dir: Union[str, Path],
    user_path: str,
    allow_absolute: bool = False
) -> Path:
    """Validate that a user-provided path is within a base directory.
    
    This function provides robust protection against path traversal attacks
    by resolving the absolute path and verifying it's within the base directory.
    
    Args:
        base_dir: The base directory that all paths must be within
        user_path: The user-provided path to validate
        allow_absolute: If True, allow absolute paths (they will still be
                       validated to be within base_dir)
                       
    Returns:
        The validated, resolved Path object
        
    Raises:
        PathTraversalError: If the path attempts to escape the base directory
        ValueError: If the path is invalid for other reasons
    """
    if not user_path:
        raise ValueError("Path cannot be empty")
    
    # Convert base_dir to Path and resolve to absolute
    base = Path(base_dir).resolve()
    
    # Check for traversal patterns in the raw input
    if contains_traversal_patterns(user_path):
        logger.warning(
            "Path traversal pattern detected in raw path",
            extra={"user_path": user_path[:100]}  # Truncate for logging
        )
        raise PathTraversalError(
            "Path traversal detected: invalid characters in path"
        )
    
    # Fully decode the path to catch encoded traversal attempts
    decoded_path = decode_path_fully(user_path)
    
    # Check for traversal patterns in the decoded path
    if contains_traversal_patterns(decoded_path):
        logger.warning(
            "Path traversal pattern detected after decoding",
            extra={"user_path": user_path[:100]}
        )
        raise PathTraversalError(
            "Path traversal detected: invalid characters in path"
        )
    
    # Check for absolute path if not allowed
    if not allow_absolute:
        decoded_path_obj = Path(decoded_path)
        if decoded_path_obj.is_absolute():
            raise PathTraversalError(
                "Absolute paths are not allowed"
            )
    
    # Construct the full path and resolve it
    # We join with base to ensure we're checking within the base directory
    target = (base / decoded_path).resolve()
    
    # Verify the resolved path is within the base directory
    # Using relative_to which raises ValueError if not a subpath
    try:
        target.relative_to(base)
    except ValueError:
        logger.warning(
            "Path traversal attempt: resolved path outside base directory",
            extra={
                "base_dir": str(base),
                "user_path": user_path[:100],
                "resolved_path": str(target)
            }
        )
        raise PathTraversalError(
            f"Path traversal detected: path escapes base directory"
        )
    
    return target


def validate_bucket_name(bucket: str) -> str:
    """Validate a bucket/container name for safety.
    
    Bucket names should be simple identifiers without path separators
    or traversal patterns.
    
    Args:
        bucket: The bucket name to validate
        
    Returns:
        The validated bucket name
        
    Raises:
        ValueError: If the bucket name is invalid
    """
    if not bucket:
        raise ValueError("Bucket name cannot be empty")
    
    # Check for path separators
    if "/" in bucket or "\\" in bucket:
        raise ValueError("Bucket name cannot contain path separators")
    
    # Check for traversal patterns
    if contains_traversal_patterns(bucket):
        raise PathTraversalError("Invalid bucket name: path traversal detected")
    
    # Check for other dangerous characters
    dangerous_chars = ["\x00", "\n", "\r"]
    for char in dangerous_chars:
        if char in bucket:
            raise ValueError("Bucket name contains invalid characters")
    
    return bucket


def validate_storage_path(
    base_dir: Union[str, Path],
    bucket: str,
    path: str
) -> Path:
    """Validate a storage path consisting of bucket and path components.
    
    This is a convenience function that validates both the bucket name
    and the path, then returns the full validated path.
    
    Args:
        base_dir: The base storage directory
        bucket: The bucket/container name
        path: The path within the bucket
        
    Returns:
        The validated, resolved Path object
        
    Raises:
        PathTraversalError: If path traversal is detected
        ValueError: If bucket or path is invalid
    """
    # Validate bucket name first
    validate_bucket_name(bucket)
    
    # Validate the full path
    full_base = Path(base_dir) / bucket
    return validate_path(full_base, path)


def is_path_safe(base_dir: Union[str, Path], user_path: str) -> bool:
    """Check if a path is safe without raising an exception.
    
    This is a convenience function for cases where you want a boolean
    result rather than exception handling.
    
    Args:
        base_dir: The base directory that all paths must be within
        user_path: The user-provided path to validate
        
    Returns:
        True if the path is safe, False otherwise
    """
    try:
        validate_path(base_dir, user_path)
        return True
    except (PathTraversalError, ValueError):
        return False
