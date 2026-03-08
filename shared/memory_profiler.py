"""Memory profiling and leak detection utilities.

Provides:
- Memory usage monitoring
- Object lifecycle tracking
- Leak detection and cleanup
- Performance metrics collection

Usage:
    from shared.memory_profiler import MemoryProfiler

    profiler = MemoryProfiler()
    with profiler.profile():
        # Code to profile
        pass
"""

from __future__ import annotations

import gc
import sys
import time
import threading
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List
import weakref

from shared.logging_config import get_logger

logger = get_logger("sorce.memory")


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    rss_mb: float
    vms_mb: float
    shared_mb: float
    text_mb: float
    lib_mb: float
    data_mb: float
    dirty_mb: float
    percent: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class ObjectStats:
    """Object allocation statistics."""

    type_name: str
    count: int
    total_size_bytes: int
    avg_size_bytes: float
    sample_objects: List[Any] = field(default_factory=list)


class ObjectTracker:
    """Tracks object lifecycle for leak detection."""

    def __init__(self, max_tracked_objects: int = 10000):
        self.max_tracked_objects = max_tracked_objects
        self._objects: Dict[int, Dict[str, Any]] = {}
        self._type_counts: Dict[str, int] = defaultdict(int)
        self._weak_refs: Dict[int, weakref.ref] = {}
        self._lock = threading.Lock()

    def track_object(self, obj: Any, context: str = "") -> None:
        """Track an object for leak detection."""
        obj_id = id(obj)

        with self._lock:
            # Remove old objects if over limit
            while len(self._objects) >= self.max_tracked_objects:
                oldest_id = min(
                    self._objects.keys(),
                    key=lambda k: self._objects[k].get("created_at", 0),
                )
                self._remove_object(oldest_id)

            # Track object
            self._objects[obj_id] = {
                "type": type(obj).__name__,
                "created_at": time.time(),
                "context": context,
                "traceback": traceback.extract_stack()[-3:],  # Save recent frames
                "size": sys.getsizeof(obj),
            }

            self._type_counts[type(obj).__name__] += 1

            # Create weak reference to detect when object is garbage collected
            def callback(ref):
                with self._lock:
                    self._remove_object(obj_id)

            self._weak_refs[obj_id] = weakref.ref(obj, callback)

    def _remove_object(self, obj_id: int) -> None:
        """Remove object from tracking."""
        if obj_id in self._objects:
            obj_type = self._objects[obj_id]["type"]
            self._type_counts[obj_type] = max(0, self._type_counts[obj_type] - 1)
            del self._objects[obj_id]

        if obj_id in self._weak_refs:
            del self._weak_refs[obj_id]

    def get_leak_candidates(self, min_age_seconds: int = 300) -> List[Dict[str, Any]]:
        """Get objects that might be memory leaks."""
        current_time = time.time()
        candidates = []

        with self._lock:
            for obj_id, info in self._objects.items():
                age = current_time - info["created_at"]
                if age > min_age_seconds:
                    candidates.append(
                        {
                            "id": obj_id,
                            "type": info["type"],
                            "age_seconds": age,
                            "context": info["context"],
                            "size": info["size"],
                            "traceback": info["traceback"],
                        }
                    )

        # Sort by age (oldest first)
        candidates.sort(key=lambda x: x["age_seconds"], reverse=True)
        return candidates

    def get_type_stats(self) -> Dict[str, int]:
        """Get object type counts."""
        with self._lock:
            return dict(self._type_counts)

    def cleanup_dead_references(self) -> int:
        """Clean up dead weak references."""
        cleaned = 0

        with self._lock:
            dead_ids = [
                obj_id for obj_id, ref in self._weak_refs.items() if ref() is None
            ]

            for obj_id in dead_ids:
                self._remove_object(obj_id)
                cleaned += 1

        return cleaned


class MemoryProfiler:
    """Memory profiling and leak detection."""

    def __init__(self, enable_object_tracking: bool = False):
        self.enable_object_tracking = enable_object_tracking
        self.object_tracker = ObjectTracker() if enable_object_tracking else None
        self._stats_history: deque[MemoryStats] = deque(maxlen=1000)
        self._profile_stack: List[str] = []
        self._lock = threading.Lock()

        # Try to import psutil for detailed memory stats
        self.psutil = None
        try:
            import psutil

            self.psutil = psutil
        except ImportError:
            logger.warning("psutil not available - limited memory profiling")

    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        if self.psutil:
            try:
                process = self.psutil.Process()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()

                return MemoryStats(
                    rss_mb=memory_info.rss / 1024 / 1024,
                    vms_mb=memory_info.vms / 1024 / 1024,
                    shared_mb=getattr(memory_info, "shared", 0) / 1024 / 1024,
                    text_mb=getattr(memory_info, "text", 0) / 1024 / 1024,
                    lib_mb=getattr(memory_info, "lib", 0) / 1024 / 1024,
                    data_mb=getattr(memory_info, "data", 0) / 1024 / 1024,
                    dirty_mb=getattr(memory_info, "dirty", 0) / 1024 / 1024,
                    percent=memory_percent,
                )
            except Exception as e:
                logger.warning(f"Failed to get memory stats: {e}")

        # Fallback to basic memory info
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        return MemoryStats(
            rss_mb=usage.ru_maxrss / 1024,  # ru_maxrss is in KB on Linux
            vms_mb=0,  # Not available without psutil
            shared_mb=0,
            text_mb=0,
            lib_mb=0,
            data_mb=0,
            dirty_mb=0,
            percent=0,
        )

    def track_object(self, obj: Any, context: str = "") -> None:
        """Track an object if tracking is enabled."""
        if self.object_tracker:
            self.object_tracker.track_object(obj, context)

    def get_object_stats(self, top_n: int = 20) -> List[ObjectStats]:
        """Get object allocation statistics."""
        if not self.object_tracker:
            return []

        type_counts = self.object_tracker.get_type_stats()
        stats = []

        for type_name, count in sorted(
            type_counts.items(), key=lambda x: x[1], reverse=True
        )[:top_n]:
            # Estimate size based on type
            try:
                # Get a sample object to estimate size
                sample_objects = [
                    obj
                    for obj_id, info in self.object_tracker._objects.items()
                    if info["type"] == type_name
                ][:5]  # Sample first 5 objects

                if sample_objects:
                    avg_size = sum(sys.getsizeof(obj) for obj in sample_objects) / len(
                        sample_objects
                    )
                    total_size = avg_size * count
                else:
                    avg_size = 0
                    total_size = 0
            except Exception:
                avg_size = 0
                total_size = 0

            stats.append(
                ObjectStats(
                    type_name=type_name,
                    count=count,
                    total_size_bytes=total_size,
                    avg_size_bytes=avg_size,
                )
            )

        return stats

    def detect_leaks(self, min_age_seconds: int = 300) -> List[Dict[str, Any]]:
        """Detect potential memory leaks."""
        if not self.object_tracker:
            return []

        return self.object_tracker.get_leak_candidates(min_age_seconds)

    def cleanup_dead_references(self) -> int:
        """Clean up dead weak references."""
        if self.object_tracker:
            return self.object_tracker.cleanup_dead_references()
        return 0

    def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and return stats."""
        before_stats = self.get_memory_stats()

        # Run garbage collection
        collected = gc.collect()

        after_stats = self.get_memory_stats()

        # Clean up dead references
        dead_refs = self.cleanup_dead_references()

        return {
            "collected_objects": collected,
            "dead_references_cleaned": dead_refs,
            "memory_before_mb": before_stats.rss_mb,
            "memory_after_mb": after_stats.rss_mb,
            "memory_freed_mb": before_stats.rss_mb - after_stats.rss_mb,
        }

    def record_stats(self) -> None:
        """Record current memory statistics."""
        stats = self.get_memory_stats()
        with self._lock:
            self._stats_history.append(stats)

    def get_memory_trend(self, minutes: int = 60) -> List[MemoryStats]:
        """Get memory usage trend over time."""
        cutoff_time = time.time() - (minutes * 60)

        with self._lock:
            return [
                stats for stats in self._stats_history if stats.timestamp >= cutoff_time
            ]

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory summary."""
        current_stats = self.get_memory_stats()
        object_stats = self.get_object_stats()
        leak_candidates = self.detect_leaks()

        # Calculate memory trend
        recent_stats = self.get_memory_trend(30)  # Last 30 minutes
        if len(recent_stats) > 1:
            memory_trend = recent_stats[-1].rss_mb - recent_stats[0].rss_mb
            avg_memory = sum(s.rss_mb for s in recent_stats) / len(recent_stats)
        else:
            memory_trend = 0
            avg_memory = current_stats.rss_mb

        return {
            "current_memory_mb": current_stats.rss_mb,
            "memory_percent": current_stats.percent,
            "memory_trend_mb_30min": memory_trend,
            "avg_memory_mb_30min": avg_memory,
            "top_object_types": [
                {
                    "type": stat.type_name,
                    "count": stat.count,
                    "total_size_mb": stat.total_size_bytes / 1024 / 1024,
                }
                for stat in object_stats[:10]
            ],
            "potential_leaks": [
                {
                    "type": leak["type"],
                    "age_minutes": leak["age_seconds"] / 60,
                    "context": leak["context"],
                    "size_kb": leak["size"] / 1024,
                }
                for leak in leak_candidates[:5]
            ],
            "gc_stats": {
                "collection_count": gc.get_count(),
                "collection_threshold": gc.get_threshold(),
                "tracked_objects": len(gc.get_objects()) if self.object_tracker else 0,
            },
        }

    class ProfileContext:
        """Context manager for profiling a block of code."""

        def __init__(self, profiler: "MemoryProfiler", context: str = ""):
            self.profiler = profiler
            self.context = context
            self.start_stats = None
            self.end_stats = None

        def __enter__(self):
            self.start_stats = self.profiler.get_memory_stats()
            self.profiler.record_stats()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_stats = self.profiler.get_memory_stats()
            self.profiler.record_stats()

            # Log memory usage
            if self.start_stats and self.end_stats:
                memory_delta = self.end_stats.rss_mb - self.start_stats.rss_mb
                logger.info(
                    f"Memory profile [{self.context}]: "
                    f"start={self.start_stats.rss_mb:.1f}MB, "
                    f"end={self.end_stats.rss_mb:.1f}MB, "
                    f"delta={memory_delta:+.1f}MB"
                )

    def profile(self, context: str = "") -> ProfileContext:
        """Create a profiling context manager."""
        return self.ProfileContext(self, context)


# Global profiler instance
_profiler: MemoryProfiler | None = None


def get_memory_profiler() -> MemoryProfiler:
    """Get global memory profiler instance."""
    global _profiler
    if _profiler is None:
        raise RuntimeError(
            "Memory profiler not initialized. Call init_memory_profiler() first."
        )
    return _profiler


def init_memory_profiler(enable_object_tracking: bool = False) -> MemoryProfiler:
    """Initialize global memory profiler."""
    global _profiler
    _profiler = MemoryProfiler(enable_object_tracking)
    return _profiler


def profile_memory(context: str = ""):
    """Decorator for profiling function memory usage."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            profiler = get_memory_profiler()
            with profiler.profile(f"{func.__name__}:{context}"):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


# Periodic memory monitoring
def start_memory_monitoring(interval_seconds: int = 60) -> threading.Thread:
    """Start background memory monitoring."""

    def monitor():
        profiler = get_memory_profiler()
        while True:
            try:
                profiler.record_stats()

                # Check for potential leaks
                leaks = profiler.detect_leaks(min_age_seconds=600)  # 10 minutes
                if leaks:
                    logger.warning(f"Found {len(leaks)} potential memory leaks")

                # Cleanup dead references
                cleaned = profiler.cleanup_dead_references()
                if cleaned > 0:
                    logger.debug(f"Cleaned up {cleaned} dead references")

                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(interval_seconds)

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    return thread
