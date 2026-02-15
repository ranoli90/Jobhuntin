"""
Batch operations optimization for processing multiple jobs.

Implements streaming/chunking for large batch operations to avoid
memory issues and timeouts when processing >20 jobs.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, TypeVar

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
    items: list[T],
    processor: Callable[[T], Awaitable[R]],
    config: BatchConfig | None = None,
) -> BatchResult:
    """
    Process items in chunks with controlled concurrency.
    
    Args:
        items: List of items to process
        processor: Async function to process each item
        config: Batch configuration
    
    Returns:
        BatchResult with successful and failed results
    """
    import time

    config = config or BatchConfig()
    start_time = time.monotonic()

    successful: list[R] = []
    failed: list[tuple[T, Exception]] = []

    # Process in chunks
    for chunk_start in range(0, len(items), config.chunk_size):
        chunk = items[chunk_start:chunk_start + config.chunk_size]

        # Process chunk with semaphore for concurrency control
        semaphore = asyncio.Semaphore(config.max_concurrent)

        async def process_with_semaphore(item: T) -> R:
            async with semaphore:
                for attempt in range(config.retry_count + 1):
                    try:
                        return await asyncio.wait_for(
                            processor(item),
                            timeout=config.timeout_seconds,
                        )
                    except Exception as e:
                        if attempt == config.retry_count:
                            raise
                        logger.warning(
                            "Batch item failed, retrying",
                            extra={"attempt": attempt + 1, "error": str(e)},
                        )
                        await asyncio.sleep(0.5 * (attempt + 1))
                raise RuntimeError("Unreachable")

        # Run chunk concurrently
        tasks = [process_with_semaphore(item) for item in chunk]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for item, result in zip(chunk, results):
            if isinstance(result, Exception):
                failed.append((item, result))
                if config.fail_fast:
                    raise result
            else:
                successful.append(result)

    duration = time.monotonic() - start_time

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
    items: list[T],
    chunk_size: int = 20,
) -> AsyncIterator[list[T]]:
    """
    Stream items in chunks for memory-efficient processing.
    
    Usage:
        async for chunk in stream_items(jobs, chunk_size=10):
            await process_chunk(chunk)
    """
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


class BatchProcessor:
    """Stateful batch processor for managing concurrent operations."""

    def __init__(self, config: BatchConfig | None = None):
        self.config = config or BatchConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._active_tasks: set[asyncio.Task] = set()

    async def submit(self, item: T, processor: Callable[[T], Awaitable[R]]) -> asyncio.Task[R]:
        """Submit an item for processing."""
        async def process():
            async with self._semaphore:
                return await processor(item)

        task = asyncio.create_task(process())
        self._active_tasks.add(task)
        task.add_done_callback(self._active_tasks.discard)
        return task

    async def wait_all(self) -> list[Any]:
        """Wait for all submitted tasks to complete."""
        return await asyncio.gather(*self._active_tasks, return_exceptions=True)

    @property
    def pending_count(self) -> int:
        """Number of pending tasks."""
        return len(self._active_tasks)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        # Wait for all tasks to complete
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)


async def batch_match_jobs(
    jobs: list[dict[str, Any]],
    profile: dict[str, Any],
    match_func: Callable[[dict, dict], Awaitable[dict]],
    config: BatchConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Batch match multiple jobs against a profile.
    
    Optimized for >20 jobs with streaming and concurrency control.
    """
    config = config or BatchConfig(chunk_size=20, max_concurrent=5)

    async def process_job(job: dict) -> dict:
        result = await match_func(job, profile)
        return {**job, "match_result": result}

    result = await process_in_chunks(jobs, process_job, config)

    # Log failed matches
    for job, error in result.failed:
        logger.warning(
            "Job match failed",
            extra={"job_id": job.get("id"), "error": str(error)},
        )

    return result.successful


# Convenience type alias for async callable
from typing import Awaitable
