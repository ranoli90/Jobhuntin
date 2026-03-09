"""
Cache Strategies for Phase 15.1 Database & Performance
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.cache_strategies")


class CacheStrategy:
    """Base cache strategy interface."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select a key to evict based on strategy."""
        raise NotImplementedError

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """Called when a key is accessed."""
        raise NotImplementedError

    async def on_eviction(self, key: str, entry: Any) -> None:
        """Called when a key is evicted."""
        raise NotImplementedError


class LRUStrategy(CacheStrategy):
    """Least Recently Used cache eviction strategy."""

    def __init__(self):
        super().__init__("lru", "Evicts least recently used entries first")
        self._access_order = []

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select LRU victim."""
        try:
            if not self._access_order:
                return None

            # Return the least recently used key
            return str(self._access_order[0]) if self._access_order else None

        except Exception as e:
            logger.error(f"LRU strategy error: {e}")
            return None

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """Update LRU access order."""
        try:
            # Move key to end of access order
            if key in self._access_order:
                self._access_order.remove(key)
                self._access_order.append(key)

        except Exception as e:
            logger.error(f"LRU access tracking error: {e}")

    async def on_eviction(self, key: str, entry: Any) -> None:
        """Remove key from LRU tracking."""
        try:
            if key in self._access_order:
                self._access_order.remove(key)

        except Exception as e:
            logger.error(f"LRU eviction tracking error: {e}")


class LFUStrategy(CacheStrategy):
    """Least Frequently Used cache eviction strategy."""

    def __init__(self):
        super().__init__("lfu", "Evicts least frequently used entries first")
        self._frequency = defaultdict(int)

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select LFU victim."""
        try:
            if not self._frequency:
                return None

            # Find the least frequently used key
            lfu_key = min(self._frequency.items(), key=lambda item: item[1])[0]

            return str(lfu_key) if lfu_key else None

        except Exception as e:
            logger.error(f"LFU strategy error: {e}")
            return None

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """Update LFU frequency."""
        try:
            self._frequency[key] += 1

        except Exception as e:
            logger.error(f"LFU access tracking error: {e}")

    async def on_eviction(self, key: str, entry: Any) -> None:
        """Remove key from LFU tracking."""
        try:
            if key in self._frequency:
                del self._frequency[key]

        except Exception as e:
            logger.error(f"LFU eviction tracking error: {e}")


class FIFOStrategy(CacheStrategy):
    """First In First Out cache eviction strategy."""

    def __init__(self):
        super().__init__("fifo", "Evicts oldest entries first")
        self._access_order = []

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select FIFO victim."""
        try:
            if not self._access_order:
                return None

            # Return the oldest key (first in access order)
            return str(self._access_order[0]) if self._access_order else None

        except Exception as e:
            logger.error(f"FIFO strategy error: {e}")
            return None

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """Update FIFO access order."""
        try:
            # Move key to end of access order
            if key in self._access_order:
                self._access_order.remove(key)
                self._access_order.append(key)

        except Exception as e:
            logger.error(f"FIFO access tracking error: {e}")

    async def on_eviction(self, key: str, entry: Any) -> None:
        """Remove key from FIFO tracking."""
        try:
            if key in self._access_order:
                self._access_order.remove(key)

        except Exception as e:
            logger.error(f"FIFO eviction tracking error: {e}")


class TTLStrategy(CacheStrategy):
    """Time To Live cache eviction strategy."""

    def __init__(self):
        super().__init__("ttl", "Evicts expired entries first")

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select TTL victim."""
        try:
            now = datetime.now(timezone.utc)

            # Find the entry with earliest expiration
            earliest_key = None
            earliest_time = now

            for key, entry in cache_data.items():
                if isinstance(entry, dict) and "expires_at" in entry:
                    expires_at = entry["expires_at"]
                    if expires_at < earliest_time:
                        earliest_time = expires_at
                        earliest_key = key

            return earliest_key

        except Exception as e:
            logger.error(f"TTL strategy error: {e}")
            return None

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """TTL strategy doesn't track access."""
        pass

    async def on_eviction(self, key: str, entry: Any) -> None:
        """TTL strategy doesn't track evictions."""
        pass


class RandomStrategy(CacheStrategy):
    """Random cache eviction strategy."""

    def __init__(self):
        super().__init__("random", "Evicts random entries")

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select random victim."""
        try:
            if not cache_data:
                return None

            import random

            return random.choice(list(cache_data.keys()))

        except Exception as e:
            logger.error(f"Random strategy error: {e}")
            return None

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """Random strategy doesn't track access."""
        pass

    async def on_eviction(self, key: str, entry: Any) -> None:
        """Random strategy doesn't track evictions."""
        pass


class SizeBasedStrategy(CacheStrategy):
    """Size-based cache eviction strategy."""

    def __init__(self, max_size_mb: int = 100):
        super().__init__(
            "size_based", f"Evicts largest entries first (max: {max_size_mb}MB)"
        )
        self.max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        self._size_order: List[str] = []

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select largest entry for eviction."""
        try:
            if not cache_data:
                return None

            # Find the largest entry
            largest_key = max(
                cache_data.items(),
                key=lambda item: (
                    len(str(item[1])) if isinstance(item[1], (dict, str, bytes)) else 0
                ),
            )[0]

            return largest_key

        except Exception as e:
            logger.error(f"Size-based strategy error: {e}")
            return None

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """Update size-based access order."""
        try:
            # Sort by size (largest first)
            sorted_entries = sorted(
                cache_data.items(),
                key=lambda item: (
                    len(str(item[1])) if isinstance(item[1], (dict, str, bytes)) else 0
                ),
                reverse=True,
            )

            # Update access order
            access_order = [key for key, _ in sorted_entries]
            self._size_order = access_order

        except Exception as e:
            logger.error(f"Size-based access tracking error: {e}")

    async def on_eviction(self, key: str, entry: Any) -> None:
        """Remove from size-based tracking."""
        try:
            if key in self._size_order:
                self._size_order.remove(key)

        except Exception as e:
            logger.error(f"Size-based eviction tracking error: {e}")


class HybridStrategy(CacheStrategy):
    """Hybrid cache strategy combining multiple strategies."""

    def __init__(
        self,
        primary_strategy: Optional[CacheStrategy] = None,
        secondary_strategy: Optional[CacheStrategy] = None,
        primary_weight: float = 0.7,
        secondary_weight: float = 0.3,
    ):
        self.primary_strategy = primary_strategy or LRUStrategy()
        self.secondary_strategy = secondary_strategy or TTLStrategy()
        self.primary_weight = primary_weight
        self.secondary_weight = secondary_weight

        super().__init__(
            "hybrid",
            f"Hybrid strategy: {self.primary_strategy.name} + {self.secondary_strategy.name}",
        )

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select victim using hybrid strategy."""
        try:
            # Try primary strategy first
            victim = await self.primary_strategy.select_victim(cache_data)
            if victim:
                return victim

            # Fall back to secondary strategy
            return await self.secondary_strategy.select_victim(cache_data)

        except Exception as e:
            logger.error(f"Hybrid strategy error: {e}")
            return None

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """Update both strategies on access."""
        try:
            # Update primary strategy
            await self.primary_strategy.on_access(key, cache_data)

            # Update secondary strategy
            await self.secondary_strategy.on_access(key, cache_data)

        except Exception as e:
            logger.error(f"Hybrid strategy access tracking error: {e}")

    async def on_eviction(self, key: str, entry: Any) -> None:
        """Update both strategies on eviction."""
        try:
            # Update primary strategy
            await self.primary_strategy.on_eviction(key, entry)

            # Update secondary strategy
            await self.secondary_strategy.on_eviction(key, entry)

        except Exception as e:
            logger.error(f"Hybrid strategy eviction tracking error: {e}")


class CacheStrategyManager:
    """Manages cache strategies and provides strategy selection."""

    def __init__(self):
        self._strategies: Dict[str, CacheStrategy] = {}
        self._default_strategy = LRUStrategy()

        # Initialize default strategies
        self._initialize_default_strategies()

    def register_strategy(self, name: str, strategy: CacheStrategy) -> bool:
        """Register a cache strategy."""
        try:
            self._strategies[name] = strategy
            logger.info(f"Registered cache strategy: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register strategy {name}: {e}")
            return False

    def get_strategy(self, name: str) -> Optional[CacheStrategy]:
        """Get a cache strategy by name."""
        return self._strategies.get(name)

    def get_default_strategy(self) -> CacheStrategy:
        """Get default cache strategy."""
        return self._default_strategy  # type: ignore[no-any-return]

    def set_default_strategy(self, strategy: CacheStrategy) -> None:
        """Set default cache strategy."""
        self._default_strategy = strategy
        logger.info(f"Set default cache strategy to: {strategy.name}")

    def get_available_strategies(self) -> List[str]:
        """Get list of available strategy names."""
        return list(self._strategies.keys())

    def create_hybrid_strategy(
        self,
        primary_name: str,
        secondary_name: str,
        primary_weight: float = 0.7,
        secondary_weight: float = 0.3,
    ) -> Optional[HybridStrategy]:
        """Create a hybrid strategy from two existing strategies."""
        try:
            primary = self._strategies.get(primary_name)
            secondary = self._strategies.get(secondary_name)

            if not primary or not secondary:
                logger.error(f"Strategy not found: {primary_name} or {secondary_name}")
                return None

            return HybridStrategy(
                primary_strategy=primary,
                secondary_strategy=secondary,
                primary_weight=primary_weight,
                secondary_weight=secondary_weight,
            )

        except Exception as e:
            logger.error(f"Failed to create hybrid strategy: {e}")
            return None  # type: ignore[no-any-return]

    def get_strategy_recommendation(
        self,
        cache_size: int,
        access_pattern: str = "mixed",
        performance_requirements: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get strategy recommendation based on cache characteristics."""
        try:
            cache_size_mb = cache_size / (1024 * 1024)  # Convert to MB

            if cache_size_mb < 1:
                return "memory"
            elif cache_size_mb < 10:
                return "lru"
            elif cache_size_mb < 100:
                return "hybrid"
            elif access_pattern == "write_heavy":
                return "lfu"
            elif access_pattern == "read_heavy":
                return "lru"
            elif access_pattern == "mixed":
                return "hybrid"
            else:
                return "lru"

        except Exception as e:
            logger.error(f"Failed to get strategy recommendation: {e}")
            return "lru"


class AdaptiveStrategy(CacheStrategy):
    """Adaptive cache strategy that adjusts based on performance."""

    def __init__(self):
        super().__init__("adaptive", "Adaptive strategy based on performance metrics")
        self._performance_history: List[Dict[str, Any]] = []
        self._current_strategy = LRUStrategy()
        self._strategy_performance: Dict[str, Dict[str, float]] = {}
        self._strategy_performance["lru"] = {"hit_rate": 0.8, "avg_time_ms": 50.0}
        self._strategy_performance["lfu"] = {"hit_rate": 0.85, "avg_time_ms": 45.0}
        self._strategy_performance["fifo"] = {"hit_rate": 0.75, "avg_time_ms": 60.0}
        self._strategy_performance["ttl"] = {"hit_rate": 0.7, "avg_time_ms": 55.0}

        self._strategy_performance["random"] = {"hit_rate": 0.6, "avg_time_ms": 70.0}

    async def select_victim(self, cache_data: Dict[str, Any]) -> Optional[str]:
        """Select victim based on current strategy performance."""
        try:
            # Use current strategy
            result = await self._current_strategy.select_victim(cache_data)
            return str(result) if result else None

        except Exception as e:
            logger.error(f"Adaptive strategy error: {e}")
            return None

    async def update_performance(
        self,
        strategy_name: str,
        hit_rate: float,
        avg_time_ms: float,
    ) -> None:
        """Update performance metrics for a strategy."""
        try:
            self._strategy_performance[strategy_name] = {
                "hit_rate": hit_rate,
                "avg_time_ms": avg_time_ms,
            }

            # Update performance history
            self._performance_history.append(
                {
                    "strategy": strategy_name,
                    "hit_rate": hit_rate,
                    "avg_time_ms": avg_time_ms,
                    "timestamp": datetime.now(timezone.utc).timestamp(),
                }
            )

            # Keep only last 100 entries
            if len(self._performance_history) > 100:
                self._performance_history = self._performance_history[-100:]

            # Consider strategy change based on performance
            await self._evaluate_strategy_change()

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")

    async def _evaluate_strategy_change(self) -> None:
        """Evaluate if strategy change is needed."""
        try:
            if len(self._performance_history) < 10:
                return  # Not enough data

            # Calculate average performance for current strategy
            current_perf = self._strategy_performance.get(self._current_strategy.name)
            if not current_perf:
                return

            current_hit_rate = current_perf["hit_rate"]
            current_avg_time = current_perf["avg_time_ms"]

            # Compare with other strategies
            better_strategies = [
                name
                for name, perf in self._strategy_performance.items()
                if perf["hit_rate"] > current_hit_rate * 1.1
                and perf["avg_time_ms"] < current_avg_time * 0.9
            ]

            if better_strategies:
                best_strategy = better_strategies[0]
                logger.info(
                    f"Switching from {self._current_strategy.name} to {best_strategy}"
                )
                # Create strategy instance from factory
                from shared.cache_strategies import CacheStrategyFactory
                new_strategy = CacheStrategyFactory.create_strategy(best_strategy)
                if new_strategy:
                    self._current_strategy = new_strategy

        except Exception as e:
            logger.error(f"Failed to evaluate strategy change: {e}")

    async def on_access(self, key: str, cache_data: Dict[str, Any]) -> None:
        """Update adaptive strategy on access."""
        try:
            await self._current_strategy.on_access(key, cache_data)

        except Exception as e:
            logger.error(f"Adaptive strategy access tracking error: {e}")

    async def on_eviction(self, key: str, entry: Any) -> None:
        """Update adaptive strategy on eviction."""
        try:
            await self._current_strategy.on_eviction(key, entry)

        except Exception as e:
            logger.error(f"Adaptive strategy eviction tracking error: {e}")


class CacheStrategyFactory:
    """Factory for creating cache strategies."""

    _strategies: Dict[str, type] = {
        "lru": LRUStrategy,
        "lfu": LFUStrategy,
        "fifo": FIFOStrategy,
        "ttl": TTLStrategy,
        "random": RandomStrategy,
        "size_based": SizeBasedStrategy,
        "hybrid": HybridStrategy,
        "adaptive": AdaptiveStrategy,
    }

    @classmethod
    def create_strategy(cls, strategy_name: str, **kwargs) -> Optional[CacheStrategy]:
        """Create a cache strategy by name."""
        strategy_class = cls._strategies.get(strategy_name)
        if strategy_class:
            return strategy_class(**kwargs)  # type: ignore[no-any-return]
        return None

    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """Get list of available strategy names."""
        return list(cls._strategies.keys())

    @classmethod
    def create_hybrid(
        cls,
        primary_name: str,
        secondary_name: str,
        primary_weight: float = 0.7,
        secondary_weight: float = 0.3,
    ) -> Optional[HybridStrategy]:
        """Create a hybrid strategy."""
        primary_class = cls._strategies.get(primary_name)
        secondary_class = cls._strategies.get(secondary_name)

        if primary_class and secondary_class:
            primary = primary_class()
            secondary = secondary_class() if secondary_class else None
            return HybridStrategy(
                primary_strategy=primary,
                secondary_strategy=secondary,
                primary_weight=primary_weight,
                secondary_weight=secondary_weight,
            )

        return None


# Factory function
def get_cache_strategy_manager() -> CacheStrategyManager:
    """Get cache strategy manager instance."""
    return CacheStrategyManager()


def get_cache_strategy(name: str, **kwargs) -> Optional[CacheStrategy]:
    """Get cache strategy by name."""
    return CacheStrategyFactory.create_strategy(name, **kwargs)
