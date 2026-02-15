"""
Token usage tracking per tenant for LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from shared.logging_config import get_logger

logger = get_logger("sorce.tokens")


@dataclass
class TokenUsage:
    """Token usage record for a single API call."""
    tenant_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    timestamp: datetime
    endpoint: str
    request_id: str


class TokenTracker:
    """Tracks token usage per tenant with limits and alerts."""

    def __init__(self):
        self._usage: dict[str, list[TokenUsage]] = {}
        self._limits: dict[str, int] = {
            "free": 10_000,
            "pro": 100_000,
            "enterprise": 1_000_000,
        }

    def set_limit(self, tier: str, monthly_limit: int) -> None:
        """Set token limit for a tier."""
        self._limits[tier] = monthly_limit

    def record(
        self,
        tenant_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        endpoint: str = "",
        request_id: str = "",
    ) -> TokenUsage:
        """Record token usage for an API call."""
        usage = TokenUsage(
            tenant_id=tenant_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            timestamp=datetime.now(),
            endpoint=endpoint,
            request_id=request_id,
        )

        if tenant_id not in self._usage:
            self._usage[tenant_id] = []
        self._usage[tenant_id].append(usage)

        logger.info(
            "Token usage recorded",
            extra={
                "tenant_id": tenant_id,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": usage.total_tokens,
            },
        )

        return usage

    def get_monthly_usage(self, tenant_id: str) -> int:
        """Get total tokens used this month."""
        if tenant_id not in self._usage:
            return 0

        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)

        return sum(
            u.total_tokens
            for u in self._usage[tenant_id]
            if u.timestamp >= month_start
        )

    def get_usage_by_model(self, tenant_id: str) -> dict[str, int]:
        """Get token usage breakdown by model."""
        if tenant_id not in self._usage:
            return {}

        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)

        by_model: dict[str, int] = {}
        for u in self._usage[tenant_id]:
            if u.timestamp >= month_start:
                by_model[u.model] = by_model.get(u.model, 0) + u.total_tokens

        return by_model

    def get_usage_by_day(self, tenant_id: str) -> dict[str, int]:
        """Get token usage breakdown by day."""
        if tenant_id not in self._usage:
            return {}

        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)

        by_day: dict[str, int] = {}
        for u in self._usage[tenant_id]:
            if u.timestamp >= month_start:
                day = u.timestamp.strftime("%Y-%m-%d")
                by_day[day] = by_day.get(day, 0) + u.total_tokens

        return by_day

    def check_limit(self, tenant_id: str, tier: str) -> tuple[bool, int, int]:
        """
        Check if tenant is within token limit.
        
        Returns: (is_within_limit, current_usage, limit)
        """
        limit = self._limits.get(tier, 10_000)
        current = self.get_monthly_usage(tenant_id)
        return (current < limit, current, limit)

    def get_remaining(self, tenant_id: str, tier: str) -> int:
        """Get remaining tokens for the month."""
        limit = self._limits.get(tier, 10_000)
        current = self.get_monthly_usage(tenant_id)
        return max(0, limit - current)

    def cleanup_old_records(self, days: int = 90) -> int:
        """Remove records older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0

        for tenant_id in list(self._usage.keys()):
            before = len(self._usage[tenant_id])
            self._usage[tenant_id] = [
                u for u in self._usage[tenant_id]
                if u.timestamp >= cutoff
            ]
            removed += before - len(self._usage[tenant_id])

        return removed


# Global instance
_token_tracker = TokenTracker()


def get_token_tracker() -> TokenTracker:
    """Get the global token tracker instance."""
    return _token_tracker


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses simple heuristic: ~4 characters per token.
    """
    return len(text) // 4
