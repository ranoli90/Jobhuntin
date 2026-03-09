"""Batch LLM processing service.

Optimizes LLM calls with:
- Concurrent request batching
- Rate limit management
- Retry with exponential backoff
- Cost tracking per batch
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchResult:
    """Result of a batch LLM operation."""

    success: bool
    result: Any | None = None
    error: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


@dataclass
class BatchSummary:
    """Summary of a batch processing run."""

    total_items: int = 0
    successful: int = 0
    failed: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    results: list[BatchResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_items == 0:
            return 0.0
        return self.successful / self.total_items


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    max_concurrent: int = 5
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    timeout_seconds: float = 30.0
    rate_limit_per_minute: int = 60


class BatchProcessor:
    """Process items in batches with controlled concurrency and rate limiting."""

    def __init__(self, config: BatchConfig | None = None):
        self.config = config or BatchConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._rate_limit_tokens: float = float(self.config.rate_limit_per_minute)
        self._last_refill = time.time()

    async def _acquire_rate_limit(self) -> bool:
        """Acquire a rate limit token, waiting if necessary."""
        now = time.time()
        elapsed = now - self._last_refill
        # Refill tokens based on elapsed time
        tokens_to_add = elapsed * (self.config.rate_limit_per_minute / 60.0)
        self._rate_limit_tokens = min(
            float(self.config.rate_limit_per_minute),
            self._rate_limit_tokens + tokens_to_add,
        )
        self._last_refill = now

        if self._rate_limit_tokens >= 1:
            self._rate_limit_tokens -= 1
            return True
        return False

    async def _wait_for_rate_limit(self):
        """Wait until a rate limit token is available."""
        while not await self._acquire_rate_limit():
            await asyncio.sleep(0.1)

    async def process_item(
        self,
        item: Any,
        processor: Callable[[Any], Awaitable[Any]],
    ) -> BatchResult:
        """Process a single item with retry logic."""
        start_time = time.time()

        async with self._semaphore:
            await self._wait_for_rate_limit()

            for attempt in range(self.config.max_retries + 1):
                try:
                    result = await asyncio.wait_for(
                        processor(item), timeout=self.config.timeout_seconds
                    )
                    latency_ms = (time.time() - start_time) * 1000
                    return BatchResult(
                        success=True, result=result, latency_ms=latency_ms
                    )
                except asyncio.TimeoutError:
                    latency_ms = (time.time() - start_time) * 1000
                    if attempt == self.config.max_retries:
                        return BatchResult(
                            success=False,
                            error=f"Timeout after {self.config.timeout_seconds}s",
                            latency_ms=latency_ms,
                        )
                    await asyncio.sleep(
                        min(
                            self.config.base_delay * (2**attempt), self.config.max_delay
                        )
                    )
                except Exception as e:
                    latency_ms = (time.time() - start_time) * 1000
                    if attempt == self.config.max_retries:
                        return BatchResult(
                            success=False, error=str(e), latency_ms=latency_ms
                        )
                    logger.warning(f"Attempt {attempt + 1} failed for item: {e}")
                    await asyncio.sleep(
                        min(
                            self.config.base_delay * (2**attempt), self.config.max_delay
                        )
                    )

        # Should never reach here
        return BatchResult(success=False, error="Unknown error")

    async def process_batch(
        self,
        items: list,
        processor: Callable[[Any], Awaitable[Any]],
    ) -> BatchSummary:
        """Process a batch of items concurrently."""
        summary = BatchSummary(total_items=len(items))

        # Create tasks for all items
        tasks = [self.process_item(item, processor) for item in items]

        # Process all tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for raw in results:
            if isinstance(raw, BaseException):
                summary.failed += 1
                summary.results.append(BatchResult(success=False, error=str(raw)))
            else:
                result: BatchResult = raw
                summary.results.append(result)
                if result.success:
                    summary.successful += 1
                else:
                    summary.failed += 1
                summary.total_tokens += result.tokens_used
                summary.total_cost_usd += result.cost_usd
                summary.total_latency_ms += result.latency_ms

        return summary


async def batch_process_llm_requests(
    items: list,
    process_fn: Callable[[Any], Awaitable[Any]],
    config: BatchConfig | None = None,
) -> BatchSummary:
    """High-level function to batch process LLM requests.

    Args:
        items: List of items to process
        process_fn: Async function to process each item
        config: Optional batch configuration

    Returns:
        BatchSummary with results and statistics
    """
    processor = BatchProcessor(config)
    return await processor.process_batch(items, process_fn)
