"""
Content moderation service for LLM outputs.

Provides:
- Toxicity detection
- PII filtering
- Profanity filtering
- Content safety checks
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ContentCategory(str, Enum):
    """Categories of moderated content."""
    TOXIC = "toxic"
    PROFANITY = "profanity"
    PII = "pii"
    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    MISINFORMATION = "misinformation"


class ModerationAction(str, Enum):
    """Actions to take on moderated content."""
    ALLOW = "allow"
    FLAG = "flag"
    REDACT = "redact"
    BLOCK = "block"


@dataclass
class ModerationResult:
    """Result of content moderation."""
    is_safe: bool
    action: ModerationAction
    categories: list[ContentCategory] = field(default_factory=list)
    confidence: float = 0.0
    flagged_text: Optional[str] = None
    redacted_text: Optional[str] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "is_safe": self.is_safe,
            "action": self.action.value,
            "categories": [c.value for c in self.categories],
            "confidence": self.confidence,
            "flagged_text": self.flagged_text,
            "redacted_text": self.redacted_text,
            "reason": self.reason,
        }


# Common profanity patterns (basic list - extend as needed)
PROFANITY_PATTERNS = [
    r'\b(damn|hell|crap|ass|bastard)\b',
    # Add more patterns as needed - keeping this minimal for production
]

# PII patterns
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone_us": r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    "ssn": r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
    "credit_card": r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
    "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
}

# Toxicity indicators (simplified - in production use ML model)
TOXICITY_INDICATORS = [
    "hate", "kill", "die", "stupid", "idiot", "dumb", "loser",
    "worthless", "pathetic", "disgusting", "awful", "terrible",
]


class ContentModerator:
    """
    Content moderation for LLM outputs.
    
    Features:
    - Pattern-based detection
    - PII redaction
    - Profanity filtering
    - Configurable thresholds
    """
    
    def __init__(
        self,
        enable_profanity_filter: bool = True,
        enable_pii_filter: bool = True,
        enable_toxicity_check: bool = True,
        block_threshold: float = 0.8,
        flag_threshold: float = 0.5,
        custom_patterns: Optional[dict[str, list[str]]] = None,
    ):
        self.enable_profanity_filter = enable_profanity_filter
        self.enable_pii_filter = enable_pii_filter
        self.enable_toxicity_check = enable_toxicity_check
        self.block_threshold = block_threshold
        self.flag_threshold = flag_threshold
        self.custom_patterns = custom_patterns or {}
        
        # Compile patterns
        self._profanity_regex = [
            re.compile(p, re.IGNORECASE) for p in PROFANITY_PATTERNS
        ]
        self._pii_regex = {
            name: re.compile(pattern) 
            for name, pattern in PII_PATTERNS.items()
        }
    
    def moderate(self, text: str) -> ModerationResult:
        """
        Moderate content and return result.
        
        Args:
            text: Text to moderate
            
        Returns:
            ModerationResult with action and details
        """
        if not text:
            return ModerationResult(
                is_safe=True,
                action=ModerationAction.ALLOW,
            )
        
        categories: list[ContentCategory] = []
        flagged_parts: list[str] = []
        redacted_text = text
        confidence = 0.0
        
        # Check PII
        if self.enable_pii_filter:
            pii_found, redacted_text = self._check_pii(redacted_text)
            if pii_found:
                categories.append(ContentCategory.PII)
                flagged_parts.append("PII detected")
        
        # Check profanity
        if self.enable_profanity_filter:
            profanity_found, redacted_text = self._check_profanity(redacted_text)
            if profanity_found:
                categories.append(ContentCategory.PROFANITY)
                flagged_parts.append("Profanity detected")
                confidence = max(confidence, 0.6)
        
        # Check toxicity
        if self.enable_toxicity_check:
            toxicity_score = self._check_toxicity(text)
            if toxicity_score > self.flag_threshold:
                categories.append(ContentCategory.TOXIC)
                flagged_parts.append(f"Toxicity score: {toxicity_score:.2f}")
                confidence = max(confidence, toxicity_score)
        
        # Determine action
        if not categories:
            return ModerationResult(
                is_safe=True,
                action=ModerationAction.ALLOW,
            )
        
        if confidence >= self.block_threshold:
            action = ModerationAction.BLOCK
        elif ContentCategory.PII in categories:
            action = ModerationAction.REDACT
        elif confidence >= self.flag_threshold:
            action = ModerationAction.FLAG
        else:
            action = ModerationAction.ALLOW
        
        return ModerationResult(
            is_safe=action == ModerationAction.ALLOW or action == ModerationAction.REDACT,
            action=action,
            categories=categories,
            confidence=confidence,
            flagged_text=", ".join(flagged_parts),
            redacted_text=redacted_text if action == ModerationAction.REDACT else None,
            reason=self._get_reason(categories, action),
        )
    
    def _check_pii(self, text: str) -> tuple[bool, str]:
        """Check for PII and redact."""
        found = False
        redacted = text
        
        for name, pattern in self._pii_regex.items():
            matches = pattern.findall(redacted)
            if matches:
                found = True
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ""
                    redacted = redacted.replace(match, f"[{name.upper()}_REDACTED]")
        
        return found, redacted
    
    def _check_profanity(self, text: str) -> tuple[bool, str]:
        """Check for profanity and censor."""
        found = False
        censored = text
        
        for pattern in self._profanity_regex:
            matches = pattern.findall(censored)
            if matches:
                found = True
                for match in matches:
                    # Replace with asterisks except first letter
                    censored = censored.replace(match, match[0] + "*" * (len(match) - 1))
        
        return found, censored
    
    def _check_toxicity(self, text: str) -> float:
        """
        Check toxicity score (simplified heuristic).
        
        In production, use a proper ML model like:
        - Perspective API
        - OpenAI Moderation API
        - Local transformer model
        """
        text_lower = text.lower()
        matches = sum(1 for indicator in TOXICITY_INDICATORS if indicator in text_lower)
        
        # Normalize to 0-1 range
        # More matches = higher toxicity
        score = min(matches / 5.0, 1.0)
        
        return score
    
    def _get_reason(
        self, 
        categories: list[ContentCategory], 
        action: ModerationAction
    ) -> str:
        """Get human-readable reason for moderation action."""
        if action == ModerationAction.ALLOW:
            return "Content passed moderation"
        
        category_names = [c.value.replace("_", " ") for c in categories]
        
        if action == ModerationAction.BLOCK:
            return f"Content blocked due to: {', '.join(category_names)}"
        elif action == ModerationAction.REDACT:
            return f"Content redacted due to: {', '.join(category_names)}"
        else:
            return f"Content flagged for: {', '.join(category_names)}"
    
    def is_safe(self, text: str) -> bool:
        """Quick check if content is safe."""
        result = self.moderate(text)
        return result.is_safe
    
    def redact_pii(self, text: str) -> str:
        """Redact PII from text."""
        _, redacted = self._check_pii(text)
        return redacted
    
    def filter_profanity(self, text: str) -> str:
        """Filter profanity from text."""
        _, filtered = self._check_profanity(text)
        return filtered


class LLMModerator:
    """
    Specialized moderator for LLM outputs.
    
    Uses LLM-based moderation for more accurate detection.
    """
    
    def __init__(
        self,
        llm_client: "Any",
        use_llm_check: bool = True,
        fallback_to_patterns: bool = True,
    ):
        self.llm_client = llm_client
        self.use_llm_check = use_llm_check
        self.fallback_to_patterns = fallback_to_patterns
        self._pattern_moderator = ContentModerator()
    
    async def moderate_output(
        self,
        output: str,
        context: Optional[str] = None,
    ) -> ModerationResult:
        """
        Moderate LLM output.
        
        Args:
            output: LLM output to moderate
            context: Optional context for the output
            
        Returns:
            ModerationResult
        """
        # First, do pattern-based check
        pattern_result = self._pattern_moderator.moderate(output)
        
        # If pattern check blocks, return immediately
        if pattern_result.action == ModerationAction.BLOCK:
            return pattern_result
        
        # If LLM check enabled, do additional check
        if self.use_llm_check and self.llm_client:
            try:
                llm_result = await self._llm_moderate(output, context)
                
                # Combine results
                if llm_result.action == ModerationAction.BLOCK:
                    return llm_result
                
                # Merge categories
                all_categories = list(set(
                    pattern_result.categories + llm_result.categories
                ))
                
                # Take more restrictive action
                actions = [pattern_result.action, llm_result.action]
                if ModerationAction.BLOCK in actions:
                    final_action = ModerationAction.BLOCK
                elif ModerationAction.REDACT in actions:
                    final_action = ModerationAction.REDACT
                elif ModerationAction.FLAG in actions:
                    final_action = ModerationAction.FLAG
                else:
                    final_action = ModerationAction.ALLOW
                
                return ModerationResult(
                    is_safe=final_action == ModerationAction.ALLOW,
                    action=final_action,
                    categories=all_categories,
                    confidence=max(pattern_result.confidence, llm_result.confidence),
                    reason=f"Pattern check: {pattern_result.reason}; LLM check: {llm_result.reason}",
                )
            except Exception as e:
                logger.warning(f"LLM moderation failed: {e}")
                if self.fallback_to_patterns:
                    return pattern_result
                raise
        
        return pattern_result
    
    async def _llm_moderate(
        self,
        text: str,
        context: Optional[str] = None,
    ) -> ModerationResult:
        """Use LLM to moderate content."""
        prompt = f"""Analyze the following text for safety issues. Check for:
- Toxicity or harassment
- Hate speech
- Sexual content
- Violence
- Self-harm references
- Misinformation

{"Context: " + context if context else ""}

Text to analyze:
{text[:1000]}

Respond in JSON format:
{{
  "is_safe": true/false,
  "categories": ["list of issue categories found"],
  "confidence": 0.0-1.0,
  "reason": "explanation"
}}"""

        try:
            response = await self.llm_client.call(prompt)
            
            # Parse response
            import json
            result = json.loads(response)
            
            categories = [
                ContentCategory(c) 
                for c in result.get("categories", [])
                if c in [e.value for e in ContentCategory]
            ]
            
            confidence = result.get("confidence", 0.5)
            
            if result.get("is_safe", True):
                return ModerationResult(
                    is_safe=True,
                    action=ModerationAction.ALLOW,
                    categories=categories,
                    confidence=confidence,
                    reason=result.get("reason", "LLM check passed"),
                )
            else:
                action = ModerationAction.BLOCK if confidence > 0.8 else ModerationAction.FLAG
                return ModerationResult(
                    is_safe=False,
                    action=action,
                    categories=categories,
                    confidence=confidence,
                    reason=result.get("reason", "LLM detected issues"),
                )
        
        except Exception as e:
            logger.error(f"LLM moderation parse error: {e}")
            # Return safe result on error
            return ModerationResult(
                is_safe=True,
                action=ModerationAction.ALLOW,
                reason=f"LLM check failed: {e}",
            )


# Global moderator instance
_moderator: Optional[ContentModerator] = None


def get_moderator() -> ContentModerator:
    """Get the global content moderator."""
    global _moderator
    if _moderator is None:
        _moderator = ContentModerator()
    return _moderator


def moderate_content(text: str) -> ModerationResult:
    """Convenience function to moderate content."""
    return get_moderator().moderate(text)


def is_content_safe(text: str) -> bool:
    """Quick check if content is safe."""
    return get_moderator().is_safe(text)


def redact_pii(text: str) -> str:
    """Redact PII from text."""
    return get_moderator().redact_pii(text)
