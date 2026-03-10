"""Batch operations optimization for processing multiple jobs.

Implements streaming/chunking for large batch operations to avoid
memory issues and timeouts when processing >20 jobs.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from shared.logging_config import get_logger

logger = get_logger("sorce.batch")

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchConfig:
    """Configuration for batch operations."""

    chunk_size: int = 20
    max_concurrent: int = 5
    timeout_seconds: float = 30.0
    retry_count: int = 2
    fail_fast: bool = False


@dataclass
class BatchResult:
    """Result of a batch operation."""

    successful: list[Any]
    failed: list[tuple[Any, Exception]]
    total: int
    duration_seconds: float


async def process_in_chunks(
    items: list,
    processor: Callable[[Any], Any],
    config: BatchConfig | None = None,
) -> BatchResult:
    """Process items in chunks with controlled concurrency.

    Args:
        items: List of items to process
        processor: Async function to process each item
        config: Batch configuration

    Returns:
        BatchResult with successful and failed results

    """
    import time

    cfg = config or BatchConfig()
    start_time = time.time()
    successful: list[Any] = []
    failed: list[tuple[Any, Exception]] = []

    async def process_with_timeout(item: Any) -> Any:
        """Process single item with timeout and retry."""
        for attempt in range(cfg.retry_count + 1):
            try:
                return await asyncio.wait_for(
                    processor(item), timeout=cfg.timeout_seconds
                )
            except asyncio.TimeoutError:
                if attempt == cfg.retry_count:
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))
        raise RuntimeError("Unreachable")

    # Process in chunks
    for i in range(0, len(items), cfg.chunk_size):
        chunk = items[i : i + cfg.chunk_size]

        # Process chunk with limited concurrency
        semaphore = asyncio.Semaphore(cfg.max_concurrent)

        async def process_item(item: Any) -> tuple[Any, Any | None, Exception | None]:
            async with semaphore:
                try:
                    result = await process_with_timeout(item)
                    return (item, result, None)
                except Exception as e:
                    return (item, None, e)

        # Gather results for this chunk
        tasks = [process_item(item) for item in chunk]
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in chunk_results:
            if isinstance(result, Exception):
                failed.append((chunk[0], result))
                if cfg.fail_fast:
                    break
            elif isinstance(result, tuple):
                item, output, error = result
                if error:
                    failed.append((item, error))
                    if cfg.fail_fast:
                        break
                else:
                    successful.append(output)

        if cfg.fail_fast and failed:
            break

    duration = time.time() - start_time

    logger.info(
        "Batch processing complete",
        extra={
            "total": len(items),
            "successful": len(successful),
            "failed": len(failed),
            "duration_seconds": duration,
        },
    )

    return BatchResult(
        successful=successful,
        failed=failed,
        total=len(items),
        duration_seconds=duration,
    )


async def stream_items(
    items: list,
    chunk_size: int = 20,
) -> AsyncIterator[list]:
    """Stream items in chunks for memory-efficient processing.

    Usage:
        async for chunk in stream_items(jobs, chunk_size=10):
            await process_chunk(chunk)
    """
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


class BatchProcessor:
    """Stateful batch processor for managing concurrent operations."""

    def __init__(self, config: BatchConfig | None = None):
        self.config = config or BatchConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._results: list[Any] = []
        self._errors: list[tuple[Any, Exception]] = []

    async def submit(self, item: Any, processor: Callable[[Any], Any]) -> asyncio.Task:
        """Submit an item for processing."""

        async def wrapped() -> Any:
            async with self._semaphore:
                try:
                    result = await asyncio.wait_for(
                        processor(item), timeout=self.config.timeout_seconds
                    )
                    self._results.append(result)
                    return result
                except Exception as e:
                    self._errors.append((item, e))
                    raise

        return asyncio.create_task(wrapped())

    @property
    def results(self) -> list[Any]:
        """Get successful results."""
        return self._results.copy()

    @property
    def errors(self) -> list[tuple[Any, Exception]]:
        """Get errors."""
        return self._errors.copy()

    def reset(self) -> None:
        """Clear all results and errors."""
        self._results.clear()
        self._errors.clear()
