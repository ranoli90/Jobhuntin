"""
Batch LLM processing service.

Optimizes LLM calls with:
- Concurrent request batching
- Rate limit management
- Retry with exponential backoff
- Cost tracking per batch
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchResult(Generic[R]):
    """Result of a batch LLM operation."""
    success: bool
    result: R | None = None
    error: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


@dataclass
class BatchSummary(Generic[R]):
    """Summary of a batch processing run."""
    total_items: int = 0
    successful: int = 0
    failed: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    results: list[BatchResult[R]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_items == 0:
            return 0.0
        return self.successful / self.total_items

    @property
    def avg_latency_ms(self) -> float:
        if self.total_items == 0:
            return 0.0
        return self.total_latency_ms / self.total_items


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    tokens_per_minute: int = 150000
    max_concurrent: int = 10
    retry_attempts: int = 3
    retry_base_delay_ms: float = 1000.0
    retry_max_delay_ms: float = 30000.0


class BatchLLMProcessor(Generic[T, R]):
    """
    Batch processor for LLM operations.
    
    Features:
    - Concurrent processing with configurable parallelism
    - Rate limit management
    - Automatic retry with exponential backoff
    - Cost and token tracking
    """

    def __init__(
        self,
        process_fn: "Callable[[T], Awaitable[R]]",
        config: RateLimitConfig | None = None,
        token_counter: "Callable[[T], int] | None" = None,
        cost_calculator: "Callable[[int], float] | None" = None,
    ):
        """
        Initialize batch processor.
        
        Args:
            process_fn: Async function to process each item
            config: Rate limit configuration
            token_counter: Function to estimate tokens for an item
            cost_calculator: Function to calculate cost from tokens
        """
        self._process_fn = process_fn
        self._config = config or RateLimitConfig()
        self._token_counter = token_counter or (lambda _: 0)
        self._cost_calculator = cost_calculator or (lambda _: 0.0)

        # Rate limiting state
        self._request_times: list[float] = []
        self._token_usage: list[tuple[float, int]] = []
        self._semaphore = asyncio.Semaphore(self._config.max_concurrent)
        self._lock = asyncio.Lock()

    async def _check_rate_limits(self, estimated_tokens: int = 0) -> None:
        """Check and wait for rate limits if necessary."""
        async with self._lock:
            now = time.time()
            minute_ago = now - 60.0

            # Clean old entries
            self._request_times = [t for t in self._request_times if t > minute_ago]
            self._token_usage = [(t, tok) for t, tok in self._token_usage if t > minute_ago]

            # Check request rate
            if len(self._request_times) >= self._config.requests_per_minute:
                wait_time = self._request_times[0] - minute_ago + 0.1
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s for request slot")
                await asyncio.sleep(wait_time)

            # Check token rate
            current_tokens = sum(tok for _, tok in self._token_usage)
            if current_tokens + estimated_tokens > self._config.tokens_per_minute:
                # Find when oldest tokens will expire
                wait_time = self._token_usage[0][0] - minute_ago + 0.1
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s for token budget")
                await asyncio.sleep(wait_time)

            # Record this request
            self._request_times.append(time.time())
            if estimated_tokens > 0:
                self._token_usage.append((time.time(), estimated_tokens))

    async def _process_with_retry(
        self,
        item: T,
        item_id: str | int = "unknown",
    ) -> BatchResult[R]:
        """Process a single item with retry logic."""
        estimated_tokens = self._token_counter(item)

        for attempt in range(self._config.retry_attempts):
            try:
                async with self._semaphore:
                    await self._check_rate_limits(estimated_tokens)

                    start_time = time.time()
                    result = await self._process_fn(item)
                    latency = (time.time() - start_time) * 1000

                    # Calculate actual cost (would need actual token count from response)
                    cost = self._cost_calculator(estimated_tokens)

                    return BatchResult(
                        success=True,
                        result=result,
                        tokens_used=estimated_tokens,
                        cost_usd=cost,
                        latency_ms=latency,
                    )

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Batch item {item_id} attempt {attempt + 1} failed: {error_msg}"
                )

                if attempt < self._config.retry_attempts - 1:
                    # Exponential backoff
                    delay = min(
                        self._config.retry_base_delay_ms * (2 ** attempt) / 1000.0,
                        self._config.retry_max_delay_ms / 1000.0,
                    )
                    await asyncio.sleep(delay)
                else:
                    return BatchResult(
                        success=False,
                        error=error_msg,
                    )

        return BatchResult(success=False, error="Max retries exceeded")

    async def process_batch(
        self,
        items: list[T],
        fail_fast: bool = False,
    ) -> BatchSummary[R]:
        """
        Process a batch of items concurrently.
        
        Args:
            items: List of items to process
            fail_fast: If True, stop on first error
            
        Returns:
            BatchSummary with results and statistics
        """
        summary = BatchSummary[R](total_items=len(items))

        if not items:
            return summary

        # Create tasks for all items
        tasks = [
            self._process_with_retry(item, i)
            for i, item in enumerate(items)
        ]

        # Process concurrently
        if fail_fast:
            # Process with early termination on first failure
            for coro in asyncio.as_completed(tasks):
                result = await coro
                summary.results.append(result)

                if result.success:
                    summary.successful += 1
                    summary.total_tokens += result.tokens_used
                    summary.total_cost_usd += result.cost_usd
                    summary.total_latency_ms += result.latency_ms
                else:
                    summary.failed += 1
                    # Cancel remaining tasks
                    for task in tasks:
                        if asyncio.isfuture(task) and not task.done():
                            task.cancel()
                    break
        else:
            # Process all items
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    summary.results.append(BatchResult(
                        success=False,
                        error=str(result),
                    ))
                    summary.failed += 1
                else:
                    summary.results.append(result)
                    if result.success:
                        summary.successful += 1
                        summary.total_tokens += result.tokens_used
                        summary.total_cost_usd += result.cost_usd
                        summary.total_latency_ms += result.latency_ms
                    else:
                        summary.failed += 1

        logger.info(
            f"Batch processed: {summary.successful}/{summary.total_items} successful, "
            f"{summary.total_tokens} tokens, ${summary.total_cost_usd:.4f}"
        )

        return summary

    async def process_stream(
        self,
        items: list[T],
        callback: "Callable[[int, BatchResult[R]], Awaitable[None]]",
    ) -> BatchSummary[R]:
        """
        Process items and stream results via callback.
        
        Args:
            items: List of items to process
            callback: Async callback for each result (index, result)
            
        Returns:
            BatchSummary with final statistics
        """
        summary = BatchSummary[R](total_items=len(items))

        async def process_and_callback(i: int, item: T) -> None:
            result = await self._process_with_retry(item, i)
            summary.results.append(result)

            if result.success:
                summary.successful += 1
                summary.total_tokens += result.tokens_used
                summary.total_cost_usd += result.cost_usd
                summary.total_latency_ms += result.latency_ms
            else:
                summary.failed += 1

            await callback(i, result)

        # Process all items concurrently
        await asyncio.gather(*[
            process_and_callback(i, item)
            for i, item in enumerate(items)
        ])

        return summary


# Default token estimation functions
def estimate_tokens_text(text: str) -> int:
    """Estimate tokens for text (rough: 4 chars per token)."""
    return len(text) // 4


def estimate_tokens_messages(messages: list[dict]) -> int:
    """Estimate tokens for chat messages."""
    total = 0
    for msg in messages:
        total += 4  # Message overhead
        if "content" in msg:
            total += estimate_tokens_text(str(msg["content"]))
        if "role" in msg:
            total += 1
    return total


# Default cost calculators (approximate, as of 2024)
def calculate_cost_gpt4(tokens: int) -> float:
    """Calculate cost for GPT-4 (approximate)."""
    return tokens * 0.00003  # $0.03 per 1K tokens


def calculate_cost_gpt35(tokens: int) -> float:
    """Calculate cost for GPT-3.5 (approximate)."""
    return tokens * 0.0000015  # $0.0015 per 1K tokens


def calculate_cost_claude(tokens: int) -> float:
    """Calculate cost for Claude (approximate)."""
    return tokens * 0.000008  # $0.008 per 1K tokens


# Convenience function for common use case
async def batch_process_llm_requests(
    items: list[T],
    process_fn: "Callable[[T], Awaitable[R]]",
    max_concurrent: int = 10,
    requests_per_minute: int = 60,
) -> BatchSummary[R]:
    """
    Convenience function for batch LLM processing.
    
    Args:
        items: Items to process
        process_fn: Async processing function
        max_concurrent: Maximum concurrent requests
        requests_per_minute: Rate limit
        
    Returns:
        BatchSummary with results
    """
    config = RateLimitConfig(
        max_concurrent=max_concurrent,
        requests_per_minute=requests_per_minute,
    )
    processor = BatchLLMProcessor(process_fn, config)
    return await processor.process_batch(items)
