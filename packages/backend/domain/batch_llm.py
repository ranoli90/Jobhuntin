"""
Batch LLM Processing — optimize LLM calls with batching and parallelization.

Provides:
- Parallel LLM calls with rate limiting
- Request batching for similar queries
- Result caching for repeated queries
- Cost tracking per batch
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from shared.logging_config import get_logger

from shared.metrics import incr, observe

logger = get_logger("sorce.batch_llm")

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchRequest(Generic[T]):
    id: str
    payload: T
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BatchResult(Generic[R]):
    request_id: str
    success: bool
    result: R | None = None
    error: str | None = None
    tokens_used: int = 0
    latency_ms: float = 0.0


class BatchProcessor(Generic[T, R]):
    def __init__(
        self,
        process_fn,
        max_batch_size: int = 10,
        max_concurrent: int = 5,
        rate_limit_per_minute: int = 60,
    ):
        self.process_fn = process_fn
        self.max_batch_size = max_batch_size
        self.max_concurrent = max_concurrent
        self.rate_limit_per_minute = rate_limit_per_minute
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._request_times: list[float] = []

    async def process_single(self, request: BatchRequest[T]) -> BatchResult[R]:
        async with self._semaphore:
            await self._rate_limit()

            start = asyncio.get_event_loop().time()
            try:
                result = await self.process_fn(request.payload)
                latency = (asyncio.get_event_loop().time() - start) * 1000

                incr("batch_llm.success")
                observe("batch_llm.latency_ms", latency)

                return BatchResult(
                    request_id=request.id,
                    success=True,
                    result=result,
                    latency_ms=latency,
                )
            except Exception as e:
                latency = (asyncio.get_event_loop().time() - start) * 1000
                incr("batch_llm.error")
                logger.error("Batch request %s failed: %s", request.id, e)
                return BatchResult(
                    request_id=request.id,
                    success=False,
                    error=str(e),
                    latency_ms=latency,
                )

    async def process_batch(
        self, requests: list[BatchRequest[T]]
    ) -> list[BatchResult[R]]:
        sorted_requests = sorted(requests, key=lambda r: -r.priority)

        tasks = [self.process_single(req) for req in sorted_requests]
        results = await asyncio.gather(*tasks)

        total_tokens = sum(r.tokens_used for r in results)
        success_count = sum(1 for r in results if r.success)

        incr("batch_llm.batch_processed", value=len(requests))
        observe("batch_llm.batch_size", len(requests))

        logger.info(
            "Batch processed: %d/%d successful, %d tokens",
            success_count,
            len(requests),
            total_tokens,
        )

        return list(results)

    async def _rate_limit(self):
        import time

        now = time.time()
        self._request_times = [t for t in self._request_times if now - t < 60]

        if len(self._request_times) >= self.rate_limit_per_minute:
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self._request_times.append(now)


async def batch_process_embeddings(
    texts: list[str],
    embed_fn,
    batch_size: int = 20,
) -> list[list[float] | None]:
    processor = BatchProcessor[str, list[float]](
        process_fn=embed_fn,
        max_batch_size=batch_size,
        max_concurrent=3,
    )

    requests = [BatchRequest(id=str(i), payload=text) for i, text in enumerate(texts)]

    results = await processor.process_batch(requests)

    return [r.result for r in results]


async def batch_process_matches(
    profiles: list[dict[str, Any]],
    job: dict[str, Any],
    match_fn,
) -> list[dict[str, Any] | None]:
    processor = BatchProcessor[dict, dict](
        process_fn=lambda p: match_fn(p, job),
        max_batch_size=10,
        max_concurrent=5,
    )

    requests = [
        BatchRequest(
            id=str(i),
            payload=profile,
            metadata={"user_id": profile.get("user_id")},
        )
        for i, profile in enumerate(profiles)
    ]

    results = await processor.process_batch(requests)

    return [r.result for r in results]


async def batch_process_resume_tailoring(
    resumes: list[tuple[str, dict[str, Any]]],
    job: dict[str, Any],
    tailor_fn,
) -> list[str | None]:
    processor = BatchProcessor[tuple, str](
        process_fn=lambda r: tailor_fn(r[0], r[1], job),
        max_batch_size=5,
        max_concurrent=3,
    )

    requests = [
        BatchRequest(
            id=str(i),
            payload=(resume, profile),
            priority=profile.get("priority", 0),
        )
        for i, (resume, profile) in enumerate(resumes)
    ]

    results = await processor.process_batch(requests)

    return [r.result for r in results]


class BatchQueue:
    def __init__(self, max_size: int = 100, flush_interval: float = 1.0):
        self.max_size = max_size
        self.flush_interval = flush_interval
        self._queue: list[BatchRequest] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None

    async def add(self, request: BatchRequest) -> str:
        async with self._lock:
            self._queue.append(request)
            if len(self._queue) >= self.max_size:
                await self._flush()
        return request.id

    async def _flush(self) -> list[BatchRequest]:
        items = self._queue.copy()
        self._queue.clear()
        return items

    async def get_pending(self) -> list[BatchRequest]:
        async with self._lock:
            return self._queue.copy()


async def process_with_retry(
    process_fn,
    payload: Any,
    max_retries: int = 3,
    backoff_base: float = 1.0,
) -> tuple[bool, Any]:
    import asyncio

    for attempt in range(max_retries):
        try:
            result = await process_fn(payload)
            return True, result
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error("Process failed after %d retries: %s", max_retries, e)
                return False, str(e)

            backoff = backoff_base * (2**attempt)
            logger.warning(
                "Process failed (attempt %d/%d), retrying in %.1fs: %s",
                attempt + 1,
                max_retries,
                backoff,
                e,
            )
            await asyncio.sleep(backoff)

    return False, "Max retries exceeded"
