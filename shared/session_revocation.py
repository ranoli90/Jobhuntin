"""Session token revocation via Redis blacklist.

Used by auth (logout, session revoke) and session_manager (eviction).
"""

from __future__ import annotations

from shared.logging_config import get_logger

logger = get_logger("sorce.session_revocation")


async def revoke_jti_in_redis(jti: str, redis_url: str | None, env: str) -> None:
    """Add JTI to Redis blacklist so the session token is immediately invalid.

    Args:
        jti: JWT ID claim from the session token
        redis_url: Redis connection URL (None to skip)
        env: Environment (prod, staging, local)
    """
    if not redis_url:
        if env in ("prod", "staging"):
            logger.critical(
                "Redis not available in %s - session token revocation disabled. "
                "Set REDIS_URL environment variable.",
                env,
            )
            raise RuntimeError(
                f"Redis required for {env} session token revocation. "
                "Set REDIS_URL environment variable."
            )
        logger.warning(
            "Redis not available - session token revocation disabled."
        )
        return

    try:
        from shared.redis_client import get_redis

        r = await get_redis()
        SESSION_TTL_SECONDS = 7 * 24 * 3600
        key = f"auth:revoked_jti:{jti}"
        await r.set(key, "1", ex=SESSION_TTL_SECONDS)
        logger.debug("Session token revoked: %s", jti)
    except Exception as e:
        logger.error("Failed to revoke session token: %s", e)
        if env in ("prod", "staging"):
            raise RuntimeError(
                "Failed to revoke session token. Redis may be unavailable."
            ) from e
