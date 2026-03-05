"""Centralized LLM client with retry, timeout, and response validation.

Usage:
    from backend.llm import LLMClient
    from backend.llm.contracts import ResumeParseResponse_V1

    client = LLMClient(settings)
    result = await client.call(
        model="gpt-4o-mini",
        prompt="...",
        response_format=ResumeParseResponse_V1,
    )
"""

from __future__ import annotations

import json
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from shared.circuit_breaker import CircuitBreakerOpen, get_circuit_breaker
from shared.config import Settings
from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.llm")

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when an LLM call fails after all retries."""

    pass


class LLMValidationError(LLMError):
    """Raised when the LLM response doesn't match the expected schema."""

    pass


class LLMClient:
    """Typed LLM client that:
    - Calls the OpenAI-compatible chat completions API
    - Retries on transient errors (5xx, timeouts, connection errors)
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

    async def call(
        self,
        *,
        prompt: str,
        model: str | None = None,
        response_format: type[T] | None = None,
        max_tokens: int | None = None,
    ) -> T | dict:
        """Send a prompt to the LLM and return a validated response.

        If response_format is provided, the JSON response is parsed into
        that Pydantic model. Otherwise returns a raw dict.

        Raises LLMError on persistent failures, LLMValidationError on
        schema mismatch.
        """
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens

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

                if response_format is not None:
                    return self._validate(raw_json, response_format)
                return raw_json

            except (
                httpx.HTTPStatusError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as exc:
                duration = time.monotonic() - t0
                observe("llm.latency_seconds", duration, {"model": model})
                incr("llm.calls.error", {"model": model, "attempt": str(attempt)})
                last_error = exc

                if (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response.status_code < 500
                ):
                    # Client errors (4xx) are not retryable
                    break

                logger.warning(
                    "LLM call attempt %d/%d failed: %s",
                    attempt,
                    self.retry_count + 1,
                    exc,
                )

            except LLMValidationError:
                # Schema validation failures are not retryable
                raise

            except Exception as exc:
                incr("llm.calls.error", {"model": model, "attempt": str(attempt)})
                last_error = exc
                logger.warning(
                    "LLM call attempt %d/%d unexpected error: %s",
                    attempt,
                    self.retry_count + 1,
                    exc,
                )

        raise LLMError(
            f"LLM call failed after {self.retry_count + 1} attempts: {last_error}"
        ) from last_error

    async def _request(self, payload: dict) -> dict:
        """Make the HTTP request with circuit breaker protection."""
        try:
            async with self._circuit_breaker:
                data = await self._make_http_request(payload)
                content = self._extract_content(data)
                cleaned_content = self._clean_content(content)
                return self._parse_json(cleaned_content)
        except CircuitBreakerOpen as exc:
            incr("llm.circuit_breaker.open", {})
            raise LLMError(
                f"LLM service unavailable (circuit breaker open). Retry in {exc.retry_after:.0f}s"
            ) from exc
        return {}  # Fallback for type checker

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
