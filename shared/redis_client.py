import redis.asyncio as redis

from shared.config import Environment, get_settings


class RedisManager:
    """Singleton manager for Redis connection pool."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def get_client(self) -> redis.Redis:
        """Get or create the Redis client.

        P0-2: In production, REDIS_URL is required. No fallback to localhost.
        """
        if self._client is None:
            s = get_settings()
            redis_url = s.redis_url
            if not redis_url:
                if s.env in (Environment.PROD, Environment.STAGING):
                    raise RuntimeError(
                        "REDIS_URL is required in production and staging. "
                        "Set REDIS_URL for token replay protection and session revocation."
                    )
                redis_url = s.local_redis_url
            self._client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                health_check_interval=30,
            )
        return self._client

    async def close(self) -> None:
        """Close the Redis client connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Global instance
_redis_manager = RedisManager()


async def get_redis() -> redis.Redis:
    """Get the global Redis client instance."""
    return await _redis_manager.get_client()


async def close_redis() -> None:
    """Close the global Redis client."""
    await _redis_manager.close()
