"""LLM Model Monitoring Service.

Tracks per-model metrics for:
- Latency percentiles (p50, p95, p99)
- Error rates and types
- Token usage
- Cost estimation
- Model availability
"""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from shared.logging_config import get_logger

logger = get_logger("sorce.llm_monitoring")


@dataclass
class ModelMetrics:
    """Metrics for a single LLM model."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_latency_seconds: float = 0.0
    latencies: list[float] = field(default_factory=list)
    errors: dict[str, int] = field(default_factory=dict)
    last_success: datetime | None = None
    last_failure: datetime | None = None

    # Cost tracking (approximate, based on model pricing)
    estimated_cost_usd: float = 0.0

    def record_success(
        self,
        latency_seconds: float,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float = 0.0,
    ) -> None:
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency_seconds += latency_seconds
        self.total_tokens += prompt_tokens + completion_tokens
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.estimated_cost_usd += cost_usd
        self.last_success = datetime.now(timezone.utc)

        # Keep bounded latency history for percentiles
        self.latencies.append(latency_seconds)
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-500:]

    def record_failure(self, error_type: str) -> None:
        self.total_requests += 1
        self.failed_requests += 1
        self.errors[error_type] = self.errors.get(error_type, 0) + 1
        self.last_failure = datetime.now(timezone.utc)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def avg_latency_seconds(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_seconds / self.successful_requests

    def percentile_latency(self, p: float) -> float:
        """Calculate latency percentile (e.g., 0.95 for p95)."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * p)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 4),
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "avg_latency_seconds": round(self.avg_latency_seconds, 3),
            "p50_latency_seconds": round(self.percentile_latency(0.50), 3),
            "p95_latency_seconds": round(self.percentile_latency(0.95), 3),
            "p99_latency_seconds": round(self.percentile_latency(0.99), 3),
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "errors": dict(self.errors),
            "last_success": (
                self.last_success.isoformat() if self.last_success else None
            ),
            "last_failure": (
                self.last_failure.isoformat() if self.last_failure else None
            ),
        }


class LLMModelMonitor:
    """Singleton service for tracking LLM model performance.

    Usage:
        monitor = LLMModelMonitor.get_instance()

        # Record a successful call
        monitor.record_success(
            model="openrouter/free",
            latency_seconds=2.5,
            prompt_tokens=500,
            completion_tokens=200,
        )

        # Record a failure
        monitor.record_failure("openrouter/free", "timeout")

        # Get metrics
        metrics = monitor.get_model_metrics("openrouter/free")
        all_metrics = monitor.get_all_metrics()
    """

    _instance: LLMModelMonitor | None = None
    _lock = threading.Lock()
    _models: dict[str, ModelMetrics]
    _model_pricing: dict[str, dict[str, float]]

    def __new__(cls) -> LLMModelMonitor:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    object.__setattr__(inst, "_models", defaultdict(ModelMetrics))
                    object.__setattr__(inst, "_model_pricing", cls._default_pricing())
                    cls._instance = inst
        return cls._instance

    @classmethod
    def get_instance(cls) -> LLMModelMonitor:
        return cls()

    @staticmethod
    def _default_pricing() -> dict[str, dict[str, float]]:
        """Default pricing per 1K tokens (approximate)."""
        return {
            "openrouter/free": {"prompt": 0.0, "completion": 0.0},
            "openai/gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
            "openai/gpt-4o": {"prompt": 0.0025, "completion": 0.01},
            "openai/gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            "anthropic/claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
            "anthropic/claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "anthropic/claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        }

    def set_model_pricing(
        self,
        model: str,
        prompt_price_per_1k: float,
        completion_price_per_1k: float,
    ) -> None:
        """Set custom pricing for a model."""
        self._model_pricing[model] = {
            "prompt": prompt_price_per_1k,
            "completion": completion_price_per_1k,
        }

    def _estimate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate cost in USD for a request."""
        pricing = self._model_pricing.get(model, {"prompt": 0.0, "completion": 0.0})
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        return prompt_cost + completion_cost

    def record_success(
        self,
        model: str,
        latency_seconds: float,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Record a successful LLM call."""
        cost = self._estimate_cost(model, prompt_tokens, completion_tokens)
        self._models[model].record_success(
            latency_seconds=latency_seconds,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
        )

        logger.debug(
            "LLM call recorded",
            extra={
                "model": model,
                "latency_seconds": latency_seconds,
                "tokens": prompt_tokens + completion_tokens,
                "cost_usd": cost,
            },
        )

    def record_failure(self, model: str, error_type: str) -> None:
        """Record a failed LLM call."""
        self._models[model].record_failure(error_type)

        logger.warning(
            "LLM failure recorded",
            extra={"model": model, "error_type": error_type},
        )

    def get_model_metrics(self, model: str) -> dict[str, Any]:
        """Get metrics for a specific model."""
        if model not in self._models:
            return {"model": model, "total_requests": 0}
        return {"model": model, **self._models[model].to_dict()}

    def get_all_metrics(self) -> dict[str, Any]:
        """Get metrics for all models."""
        return {
            "models": {
                model: metrics.to_dict() for model, metrics in self._models.items()
            },
            "total_requests": sum(m.total_requests for m in self._models.values()),
            "total_tokens": sum(m.total_tokens for m in self._models.values()),
            "total_cost_usd": round(
                sum(m.estimated_cost_usd for m in self._models.values()), 4
            ),
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get health status for all monitored models."""
        unhealthy_models = []

        for model, metrics in self._models.items():
            # Consider unhealthy if:
            # - Success rate < 90% and at least 10 requests
            # - Last failure was in the last 5 minutes with no success since
            if metrics.total_requests >= 10 and metrics.success_rate < 0.9:
                unhealthy_models.append(
                    {
                        "model": model,
                        "reason": "low_success_rate",
                        "success_rate": round(metrics.success_rate, 3),
                    }
                )
            elif metrics.last_failure and (
                not metrics.last_success or metrics.last_failure > metrics.last_success
            ):
                age_seconds = (
                    datetime.now(timezone.utc) - metrics.last_failure
                ).total_seconds()
                if age_seconds < 300:  # 5 minutes
                    unhealthy_models.append(
                        {
                            "model": model,
                            "reason": "recent_failure",
                            "last_error": (
                                list(metrics.errors.keys())[-1]
                                if metrics.errors
                                else "unknown"
                            ),
                        }
                    )

        return {
            "healthy": len(unhealthy_models) == 0,
            "unhealthy_models": unhealthy_models,
            "monitored_models": list(self._models.keys()),
        }

    def reset_metrics(self, model: str | None = None) -> None:
        """Reset metrics for a specific model or all models."""
        if model:
            if model in self._models:
                del self._models[model]
        else:
            self._models.clear()


def get_llm_monitor() -> LLMModelMonitor:
    """Get the singleton LLM model monitor."""
    return LLMModelMonitor.get_instance()
