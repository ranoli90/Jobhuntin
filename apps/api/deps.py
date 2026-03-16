"""Centralized dependency exports for API endpoints.

All endpoint files should import from this module rather than
defining local stub functions. This eliminates the need for
dependency_overrides in main.py and provides compile-time safety.

Usage:
    from api.deps import get_pool, get_tenant_context, get_current_user_id

Available dependencies:
    - get_pool: Database pool (asyncpg.Pool)
    - get_read_pool: Read replica pool or fallback to primary
    - get_current_user_id: Extract user ID from JWT token
    - require_admin_user_id: Validate user is system admin
    - get_tenant_id: Resolve tenant_id for current user
    - get_current_user: Return user as dict
    - get_tenant_context: Resolve TenantContext from JWT user_id
    - get_settings: Application settings
    - get_redis: Redis client (when available)
"""

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import Depends, HTTPException

# Import all dependencies from the main dependencies module
from api.dependencies import (
    DatabasePoolManager,
    _pool_manager,
    get_current_user,
    get_current_user_id,
    get_db_pool,
    get_pool,
    get_read_pool,
    get_tenant_id,
    require_admin_user_id,
)

# Re-export TenantContext for type hints
from packages.backend.domain.tenant import TenantContext, resolve_tenant_context
from shared.config import get_settings
from shared.error_responses import AuthenticationError, AuthorizationError, InternalError
from shared.logging_config import get_logger, LogContext

logger = get_logger("sorce.api.deps")


async def get_tenant_context(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> TenantContext:
    """Resolve TenantContext from JWT user_id.

    This is the centralized implementation that was previously in main.py.
    Auto-provisions FREE tenant if needed.

    Args:
        user_id: The authenticated user's ID from JWT
        db: Database pool connection

    Returns:
        TenantContext with tenant_id, user_id, and related info

    Raises:
        HTTPException: 401 if user not found, 403 if tenant scope error, 500 on other errors
    """
    from packages.backend.domain.tenant import TenantScopeError

    try:
        async with db.acquire() as conn:
            ctx = await resolve_tenant_context(conn, user_id)
        if ctx is None:
            logger.error(
                "[TENANT] resolve_tenant_context returned None for user_id: %s", user_id
            )
            raise InternalError("Failed to resolve tenant context")
        LogContext.set(tenant_id=ctx.tenant_id, user_id=ctx.user_id)
        return ctx
    except HTTPException:
        raise
    except TenantScopeError as exc:
        if "not found" in str(exc).lower() or "sign in again" in str(exc).lower():
            raise AuthenticationError(
                "User not found. Please sign in again.",
            )
        raise AuthorizationError(str(exc))
    except Exception as exc:
        logger.error("[TENANT] Error resolving tenant context: %s", exc, exc_info=True)
        raise InternalError("Failed to resolve tenant context")


async def get_redis() -> Any:
    """Get Redis client when available.

    Returns Redis client if configured, None otherwise.
    Used for caching, rate limiting, and session management.
    """
    from shared.redis_client import get_redis as _get_redis

    return await _get_redis()


# Convenience aliases for common naming patterns used across the codebase
# These allow endpoint files to use their preferred naming convention
get_tenant_ctx = get_tenant_context  # Alias for files using _get_tenant_ctx pattern


# Export all public symbols
__all__ = [
    # Core database dependencies
    "get_pool",
    "get_read_pool",
    "get_db_pool",
    "DatabasePoolManager",
    "_pool_manager",
    # Auth dependencies
    "get_current_user_id",
    "get_current_user",
    "require_admin_user_id",
    # Tenant dependencies
    "get_tenant_id",
    "get_tenant_context",
    "get_tenant_ctx",  # Alias
    "TenantContext",
    # Settings and utilities
    "get_settings",
    "get_redis",
]
