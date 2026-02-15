"""
Vector embedding service for semantic job matching.

Uses OpenAI-compatible embeddings API (via OpenRouter) to generate
embeddings for job descriptions and candidate profiles.

Implements the "Precision Matcher" archetype from competitive analysis:
- Vector-based semantic matching (like ApplyPass)
- Replaces boolean keyword overlap with deep learning embeddings
- Enables matching based on actual competency, not buzzwords
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

import httpx
from shared.config import Settings
from shared.logging_config import get_logger

from shared.circuit_breaker import CircuitBreakerOpen, get_circuit_breaker
from shared.metrics import incr, observe

logger = get_logger("sorce.embeddings")

EMBEDDING_DIMENSION = 1536  # OpenAI text-embedding-3-small dimension
CACHE_VERSION = 1  # Increment if embedding model changes


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""

    pass


class EmbeddingClient:
    """
    Client for generating text embeddings via OpenAI-compatible API.

    Uses OpenRouter to access embedding models (text-embedding-3-small).
    Implements caching, rate limiting, and circuit breaker patterns.
    """

    def __init__(self, settings: Settings) -> None:
        self.api_base = settings.llm_api_base.rstrip("/")
        self.api_key = settings.llm_api_key
        self.model = "openai/text-embedding-3-small"
        self.timeout = 30
        self._circuit_breaker = get_circuit_breaker("embeddings")

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Input text to embed (max ~8000 tokens)

        Returns:
            List of floats representing the embedding vector

        Raises:
            EmbeddingError on failure
        """
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIMENSION

        text = text.strip()[:32000]  # Truncate to avoid token limits

        try:
            async with self._circuit_breaker:
                t0 = time.monotonic()
                embedding = await self._make_request(text)
                duration = time.monotonic() - t0
                observe("embeddings.latency_seconds", duration)
                incr("embeddings.calls.success")
                return embedding
        except CircuitBreakerOpen as exc:
            incr("embeddings.circuit_breaker.open")
            raise EmbeddingError(
                f"Embedding service unavailable (circuit breaker open). "
                f"Retry in {exc.retry_after:.0f}s"
            ) from exc

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in a single API call.

        More efficient than individual calls for bulk processing.

        Args:
            texts: List of texts to embed (max 2048 per batch)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Process in batches of 100 to avoid API limits
        batch_size = 100
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self._make_batch_request(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def _make_request(self, text: str) -> list[float]:
        """Make single embedding API request."""
        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if "openrouter.ai" in self.api_base:
            headers["HTTP-Referer"] = "https://jobhuntin.com"
            headers["X-Title"] = "JobHuntin AI"

        payload = {
            "model": self.model,
            "input": text,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()

        data = resp.json()
        try:
            return data["data"][0]["embedding"]
        except (KeyError, IndexError) as exc:
            raise EmbeddingError(f"Unexpected embedding response: {exc}") from exc

    async def _make_batch_request(self, texts: list[str]) -> list[list[float]]:
        """Make batch embedding API request."""
        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if "openrouter.ai" in self.api_base:
            headers["HTTP-Referer"] = "https://jobhuntin.com"
            headers["X-Title"] = "JobHuntin AI"

        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()

        data = resp.json()
        try:
            # Sort by index to ensure correct order
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_data]
        except (KeyError, IndexError) as exc:
            raise EmbeddingError(f"Unexpected batch embedding response: {exc}") from exc


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns value between -1 and 1, where 1 means identical.
    """
    if not a or not b or len(a) != len(b):
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def compute_text_hash(text: str) -> str:
    """Compute a hash for cache invalidation."""
    content = f"v{CACHE_VERSION}:{text}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def profile_to_searchable_text(profile: dict[str, Any]) -> str:
    """
    Convert a CanonicalProfile to searchable text for embedding.

    This is what gets embedded and compared against job embeddings.
    """
    parts: list[str] = []

    # Current role
    if profile.get("current_title"):
        parts.append(f"Current role: {profile['current_title']}")
    if profile.get("current_company"):
        parts.append(f"at {profile['current_company']}")

    # Summary
    if profile.get("summary"):
        parts.append(profile["summary"])

    # Skills
    skills = profile.get("skills", {})
    if skills.get("technical"):
        parts.append(f"Technical skills: {', '.join(skills['technical'][:20])}")
    if skills.get("soft"):
        parts.append(f"Soft skills: {', '.join(skills['soft'][:10])}")

    # Experience highlights
    for exp in profile.get("experience", [])[:5]:
        if exp.get("title"):
            parts.append(exp["title"])
        if exp.get("company"):
            parts.append(f"at {exp['company']}")
        if exp.get("responsibilities"):
            parts.extend(exp["responsibilities"][:3])

    # Education
    for edu in profile.get("education", [])[:3]:
        if edu.get("degree") and edu.get("field_of_study"):
            parts.append(f"{edu['degree']} in {edu['field_of_study']}")
        elif edu.get("degree"):
            parts.append(edu["degree"])

    # Certifications
    if profile.get("certifications"):
        parts.append(f"Certifications: {', '.join(profile['certifications'][:10])}")

    return " ".join(parts)


def job_to_searchable_text(job: dict[str, Any]) -> str:
    """
    Convert a job dict to searchable text for embedding.

    This is what gets embedded and compared against profile embeddings.
    """
    parts: list[str] = []

    if job.get("title"):
        parts.append(job["title"])
    if job.get("company"):
        parts.append(f"at {job['company']}")
    if job.get("location"):
        parts.append(f"Location: {job['location']}")
    if job.get("description"):
        # Truncate description to most relevant parts
        desc = job["description"][:2000]
        parts.append(desc)
    if job.get("category"):
        parts.append(f"Category: {job['category']}")

    return " ".join(parts)


# Singleton instance
_embedding_client: EmbeddingClient | None = None


def get_embedding_client(settings: Settings | None = None) -> EmbeddingClient:
    """Get or create the singleton embedding client."""
    global _embedding_client
    if _embedding_client is None:
        from shared.config import get_settings

        _embedding_client = EmbeddingClient(settings or get_settings())
    return _embedding_client
