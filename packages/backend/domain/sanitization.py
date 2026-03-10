"""HTML sanitization utilities for user-generated content.

Prevents XSS attacks by sanitizing HTML content before storage or display.
"""

from __future__ import annotations

try:
    from bleach import clean

    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    import re

from shared.logging_config import get_logger

logger = get_logger("sorce.sanitization")


def sanitize_html(text: str, allowed_tags: list[str] | None = None) -> str:
    """Sanitize HTML content using bleach.

    Args:
        text: HTML string to sanitize
        allowed_tags: List of allowed HTML tags (default: no tags allowed)

    Returns:
        Sanitized text with HTML tags removed or filtered
    """
    if not text:
        return ""

    if BLEACH_AVAILABLE:
        # Use bleach for proper HTML sanitization
        if allowed_tags is None:
            allowed_tags = []  # No HTML tags allowed by default

        return clean(text, tags=allowed_tags, strip=True)
    else:
        # Fallback: Basic regex-based sanitization (less secure)
        logger.warning("bleach not installed, using basic HTML sanitization")
        if allowed_tags:
            # If tags are allowed, only remove script/style tags
            text = re.sub(
                r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL
            )
            text = re.sub(
                r"<style[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL
            )
            return text
        else:
            # Remove all HTML tags
            text = re.sub(r"<[^>]+>", "", text)
            # Decode HTML entities
            import html

            return html.unescape(text)


def sanitize_text_input(text: str, max_length: int | None = None) -> str:
    """Sanitize plain text input (no HTML).

    Args:
        text: Text to sanitize
        max_length: Optional maximum length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove HTML tags
    sanitized = sanitize_html(text, allowed_tags=[])

    # Trim whitespace
    sanitized = sanitized.strip()

    # Enforce max length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(f"Text input truncated to {max_length} characters")

    return sanitized
