"""Centralized LLM client with retry, timeout, fallback models, and response validation.

Usage:
    from backend.llm import LLMClient
    from backend.llm.contracts import ResumeParseResponse_V1

    client = LLMClient(settings)
    result = await client.call(
        model="gpt-4o-mini",
        prompt="...",
        response_format=ResumeParseResponse_V1,
    )

    # Automatic fallback to secondary models if primary fails:
    # Set LLM_FALLBACK_MODELS=openai/gpt-3.5-turbo,anthropic/claude-3-haiku
"""

from __future__ import annotations

import json
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError
from shared.config import Settings
from shared.logging_config import get_logger

from packages.backend.domain.llm_monitoring import get_llm_monitor
from shared.circuit_breaker import CircuitBreakerOpenError, get_circuit_breaker
from shared.metrics import incr, observe

logger = get_logger("sorce.llm")

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when an LLM call fails after all retries and fallbacks."""

    pass


class LLMValidationError(LLMError):
    """Raised when the LLM response doesn't match the expected schema."""

    pass


class LLMClient:
    """Typed LLM client that:
    - Calls the OpenAI-compatible chat completions API
    - Retries on transient errors (5xx, timeouts, connection errors)
    - Falls back to secondary models if primary fails completely
    - Validates the JSON response against a Pydantic model T
    - Tracks latency and error metrics.
    """

    def __init__(self, settings: Settings) -> None:
        self.api_base = settings.llm_api_base.rstrip("/")
        self.api_key = settings.llm_api_key
        self.default_model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.retry_count = settings.llm_retry_count
        self.timeout = settings.llm_timeout_seconds
        self._circuit_breaker = get_circuit_breaker("llm")

        # Parse fallback models from comma-separated string
        fallback_str = getattr(settings, "llm_fallback_models", "") or ""
        self.fallback_models = [m.strip() for m in fallback_str.split(",") if m.strip()]

    async def call(
        self,
        *,
        prompt: str,
        model: str | None = None,
        response_format: type[T] | None = None,
        max_tokens: int | None = None,
    ) -> T:
        """Send a prompt to the LLM and return a validated response.

        If response_format is provided, the JSON response is parsed into
        that Pydantic model. Otherwise returns a raw dict.

        If the primary model fails after all retries, fallback models are tried
        in order until one succeeds or all fail.

        Raises LLMError on persistent failures across all models, LLMValidationError on
        schema mismatch.
        """
        primary_model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens

        # Build list of models to try: primary first, then fallbacks
        models_to_try = [primary_model] + self.fallback_models
        all_errors: list[tuple[str, Exception]] = []

        for current_model in models_to_try:
            try:
                result = await self._call_with_retry(
                    prompt=prompt,
                    model=current_model,
                    response_format=response_format,
                    max_tokens=max_tokens,
                )

                # Log if we used a fallback
                if current_model != primary_model:
                    logger.info(
                        "LLM call succeeded with fallback model",
                        extra={
                            "primary_model": primary_model,
                            "fallback_model": current_model,
                        },
                    )
                    incr("llm.fallback.success", {"model": current_model})

                return result

            except (LLMError, LLMValidationError) as exc:
                all_errors.append((current_model, exc))
                logger.warning(
                    "LLM model %s failed: %s, trying next model",
                    current_model,
                    exc,
                )
                incr("llm.fallback.failure", {"model": current_model})

                # Don't try fallbacks for validation errors (they'd likely fail the same way)
                if isinstance(exc, LLMValidationError):
                    raise

        # All models failed
        error_summary = "; ".join(f"{m}: {e}" for m, e in all_errors)
        raise LLMError(f"All LLM models failed. Errors: {error_summary}")

    async def _call_with_retry(
        self,
        *,
        prompt: str,
        model: str,
        response_format: type[T] | None,
        max_tokens: int,
    ) -> T:
        """Execute LLM call with retries for a single model."""
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.0,
        }

        last_error: Exception | None = None

        for attempt in range(
            1, self.retry_count + 2
        ):  # retry_count retries + 1 initial
            t0 = time.monotonic()
            try:
                raw_json = await self._request(payload)
                duration = time.monotonic() - t0
                observe("llm.latency_seconds", duration, {"model": model})
                incr("llm.calls.success", {"model": model})

                # Record success in model monitor
                prompt_tokens = len(str(messages)) // 4  # Rough estimate
                completion_tokens = len(str(raw_json)) // 4
                get_llm_monitor().record_success(
                    model=model,
                    latency_seconds=duration,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

                if response_format is not None:
                    validated: T = self._validate(raw_json, response_format)
                    return validated
                return raw_json  # type: ignore[return-value]

            except (
                httpx.HTTPStatusError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as exc:
                duration = time.monotonic() - t0
                observe("llm.latency_seconds", duration, {"model": model})
                incr("llm.calls.error", {"model": model, "attempt": str(attempt)})
                last_error = exc

                # Record failure in model monitor
                error_type = type(exc).__name__
                get_llm_monitor().record_failure(model, error_type)

                if (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response.status_code < 500
                ):
                    # Client errors (4xx) are not retryable
                    break

                logger.warning(
                    "LLM call attempt %d/%d failed for model %s: %s",
                    attempt,
                    self.retry_count + 1,
                    model,
                    exc,
                )

            except LLMValidationError:
                # Schema validation failures are not retryable
                get_llm_monitor().record_failure(model, "validation_error")
                raise

            except Exception as exc:
                incr("llm.calls.error", {"model": model, "attempt": str(attempt)})
                last_error = exc
                get_llm_monitor().record_failure(model, type(exc).__name__)
                logger.warning(
                    "LLM call attempt %d/%d unexpected error for model %s: %s",
                    attempt,
                    self.retry_count + 1,
                    model,
                    exc,
                )

        raise LLMError(
            f"LLM call to {model} failed after {self.retry_count + 1} attempts: {last_error}"
        ) from last_error

    async def _request(self, payload: dict) -> dict:
        """Make the HTTP request with circuit breaker protection."""
        try:
            async with self._circuit_breaker:
                data = await self._make_http_request(payload)
                content = self._extract_content(data)
                cleaned_content = self._clean_content(content)
                return self._parse_json(cleaned_content)
        except CircuitBreakerOpenError as exc:
            incr("llm.circuit_breaker.open", {})
            raise LLMError(
                f"LLM service unavailable (circuit breaker open). Retry in {exc.retry_after:.0f}s"
            ) from exc

    async def _make_http_request(self, payload: dict) -> dict:
        """Execute the raw HTTP POST."""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Add OpenRouter-specific headers if using OpenRouter
        if "openrouter.ai" in self.api_base:
            headers["HTTP-Referer"] = "https://jobhuntin.com"
            headers["X-Title"] = "JobHuntin AI"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
        return resp.json()

    def _extract_content(self, data: dict) -> str:
        """Extract content string from OpenAI response."""
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected LLM response structure: {exc}") from exc

    def _clean_content(self, content: str) -> str:
        """Strip markdown fences and whitespace."""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)
        return content

    def _parse_json(self, content: str) -> dict:
        """Parse JSON string."""
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError(
                f"LLM returned invalid JSON: {exc}\nContent: {content[:500]}"
            ) from exc

    @staticmethod
    def _validate(raw: dict, model_cls: type[T]) -> T:
        """Validate raw JSON dict against a Pydantic model."""
        try:
            return model_cls.model_validate(raw)
        except ValidationError as exc:
            raise LLMValidationError(
                f"LLM response failed schema validation for {model_cls.__name__}: {exc}"
            ) from exc
