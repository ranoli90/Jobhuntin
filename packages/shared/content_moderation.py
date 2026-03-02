"""Content Moderation — LLM output filtering and safety checks.

Provides:
- PII detection and redaction
- Harmful content filtering
- Profanity detection
- Spam/abuse detection
- Configurable rules per tenant
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.content_moderation")


class ModerationCategory(StrEnum):
    PII = "pii"
    PROFANITY = "profanity"
    HARMFUL = "harmful"
    SPAM = "spam"
    DISCRIMINATION = "discrimination"
    SEXUAL = "sexual"
    VIOLENCE = "violence"


class ModerationResult(BaseModel):
    is_clean: bool
    categories: list[ModerationCategory] = []
    score: float = 0.0
    redacted_text: str | None = None
    flagged_segments: list[dict[str, Any]] = []


class ModerationConfig(BaseModel):
    enabled: bool = True
    block_pii: bool = True
    block_profanity: bool = True
    block_harmful: bool = True
    block_spam: bool = True
    redact_instead_of_block: bool = True
    max_score_threshold: float = 0.7


PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+?1[-.]?)?\(?[0-9]{3}\)?[-.]?[0-9]{3}[-.]?[0-9]{4}\b",
    "ssn": r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-.\s]?){3}\d{4}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "address": r"\b\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct)\b",
}

PROFANITY_WORDS = {
    "damn",
    "hell",
    "crap",
    "ass",
    "bastard",
    "bitch",
}

HARMFUL_PATTERNS = [
    r"\b(?:kill|murder|assassinate|destroy)\s+(?:you|yourself|them)\b",
    r"\b(?:bomb|explosive|terrorist)\b",
    r"\b(?:suicide|self-harm|cut yourself)\b",
]


def redact_pii(text: str, replacement: str = "[REDACTED]") -> tuple[str, list[dict]]:
    redacted = text
    matches = []

    for pii_type, pattern in PII_PATTERNS.items():
        for m in re.finditer(pattern, text, re.IGNORECASE):
            matches.append(
                {
                    "type": pii_type,
                    "value": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                }
            )
            redacted = redacted[: m.start()] + replacement + redacted[m.end() :]

    return redacted, matches


def detect_profanity(text: str) -> list[dict]:
    words = text.lower().split()
    detected = []

    for i, word in enumerate(words):
        clean_word = re.sub(r"[^\w\s]", "", word)
        if clean_word in PROFANITY_WORDS:
            detected.append(
                {
                    "type": "profanity",
                    "word": clean_word,
                    "position": i,
                }
            )

    return detected


def detect_harmful_content(text: str) -> list[dict]:
    detected = []

    for pattern in HARMFUL_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            detected.append(
                {
                    "type": "harmful",
                    "match": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                }
            )

    return detected


def detect_spam(text: str) -> list[dict]:
    spam_indicators = []
    lower_text = text.lower()

    spam_phrases = [
        "click here",
        "free money",
        "act now",
        "limited time",
        "congratulations",
        "you've won",
        "no obligation",
    ]

    for phrase in spam_phrases:
        if phrase in lower_text:
            spam_indicators.append(
                {
                    "type": "spam",
                    "phrase": phrase,
                }
            )

    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if caps_ratio > 0.7 and len(text) > 20:
        spam_indicators.append(
            {
                "type": "spam",
                "indicator": "excessive_caps",
                "ratio": round(caps_ratio, 2),
            }
        )

    if text.count("!") > 5:
        spam_indicators.append(
            {
                "type": "spam",
                "indicator": "excessive_exclamation",
                "count": text.count("!"),
            }
        )

    return spam_indicators


async def moderate_content(
    text: str,
    config: ModerationConfig | None = None,
) -> ModerationResult:
    if config is None:
        config = ModerationConfig()

    if not config.enabled:
        return ModerationResult(is_clean=True)

    categories: list[ModerationCategory] = []
    flagged_segments: list[dict[str, Any]] = []
    redacted_text = text
    total_score = 0.0

    if config.block_pii:
        redacted_text, pii_matches = redact_pii(text)
        if pii_matches:
            categories.append(ModerationCategory.PII)
            flagged_segments.extend(pii_matches)
            total_score += 0.3

    if config.block_profanity:
        profanity = detect_profanity(text)
        if profanity:
            categories.append(ModerationCategory.PROFANITY)
            flagged_segments.extend(profanity)
            total_score += 0.2

    if config.block_harmful:
        harmful = detect_harmful_content(text)
        if harmful:
            categories.append(ModerationCategory.HARMFUL)
            flagged_segments.extend(harmful)
            total_score += 0.5

    if config.block_spam:
        spam = detect_spam(text)
        if spam:
            categories.append(ModerationCategory.SPAM)
            flagged_segments.extend(spam)
            total_score += 0.2

    is_clean = total_score < config.max_score_threshold and len(categories) == 0

    if categories:
        incr(
            "content_moderation.flagged",
            {"categories": ",".join(c.value for c in categories)},
        )

    return ModerationResult(
        is_clean=is_clean,
        categories=categories,
        score=min(1.0, total_score),
        redacted_text=redacted_text if config.redact_instead_of_block else None,
        flagged_segments=flagged_segments,
    )


async def moderate_llm_output(
    output: str,
    context: str = "general",
) -> tuple[bool, str]:
    config = ModerationConfig(
        enabled=True,
        block_pii=True,
        block_profanity=True,
        block_harmful=True,
        block_spam=False,
        redact_instead_of_block=True,
    )

    result = await moderate_content(output, config)

    if result.is_clean:
        return True, output

    if result.redacted_text:
        logger.info(
            "LLM output redacted: %s categories detected",
            [c.value for c in result.categories],
        )
        return True, result.redacted_text

    logger.warning(
        "LLM output blocked: %s categories detected",
        [c.value for c in result.categories],
    )
    return False, "[Content blocked by moderation]"


async def moderate_user_input(
    text: str,
) -> tuple[bool, str, list[str]]:
    config = ModerationConfig(
        enabled=True,
        block_pii=False,
        block_profanity=True,
        block_harmful=True,
        block_spam=True,
        redact_instead_of_block=False,
    )

    result = await moderate_content(text, config)

    warnings = []
    if result.categories:
        warnings = [f"Content flagged for: {c.value}" for c in result.categories]

    return result.is_clean, text, warnings
