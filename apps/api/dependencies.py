from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import Cookie, Depends, Header, HTTPException

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.api.dependencies")


async def _check_session_revocation(jti: str, settings: Any) -> bool:
    """Check if a session token has been revoked.

    P0-2: In production, fail closed - reject request if Redis unavailable.

    Args:
        jti: JWT ID claim from the session token
        settings: Application settings

    Returns:
        True if token is revoked, False otherwise
    """
    if not settings.redis_url:
        if settings.env.value in ("prod", "staging"):
            logger.critical(
                "Redis not available in %s - cannot check session revocation. "
                "Rejecting request (fail closed). Set REDIS_URL.",
                settings.env.value,
            )
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable. Please try again.",
            )
        return False

    try:
        from shared.redis_client import get_redis

        r = await get_redis()
        key = f"auth:revoked_jti:{jti}"
        exists = await r.exists(key)
        return bool(exists)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Failed to check session token revocation: %s", e)
        if settings.env.value in ("prod", "staging"):
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable. Please try again.",
            )
        # Local/dev: allow auth to proceed when Redis is unavailable
        return False


class DatabasePoolManager:
    """Manages database pool lifecycle without global state."""

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None
        self._read_pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise HTTPException(status_code=503, detail="Database pool not available")
        return self._pool

    @property
    def read_pool(self) -> asyncpg.Pool:
        """Return the read replica pool if available, otherwise the primary pool."""
        if self._read_pool:
            return self._read_pool
        return self.pool

    async def initialize(self) -> None:
        """Initialize the database pool on startup."""
        s = get_settings()
        from packages.backend.blueprints.registry import load_default_blueprints

        enabled_raw = getattr(s, "enabled_blueprints", None) or ""
        enabled = [slug.strip() for slug in enabled_raw.split(",") if slug.strip()]
        load_default_blueprints(enabled_slugs=enabled or None)

        ssl_arg = self._get_ssl_config(s)

        from shared.db import resolve_dsn_ipv4

        db_dsn = resolve_dsn_ipv4(s.database_url)

        for attempt in range(1, 4):
            try:
                self._pool = await asyncpg.create_pool(
                    db_dsn,
                    min_size=s.db_pool_min,
                    max_size=s.db_pool_max,
                    ssl=ssl_arg,
                    statement_cache_size=0,
                    timeout=30.0,
                    command_timeout=60.0,
                )
                logger.info("Database pool created (env=%s)", s.env.value)
                break
            except asyncpg.PostgresError as exc:
                error_msg = str(exc)
                if (
                    "Tenant or user not found" in error_msg
                    or "password authentication failed" in error_msg
                ):
                    logger.warning(
                        "DB pool attempt %d/3 failed: %s. "
                        "This usually means DATABASE_URL credentials are incorrect. "
                        "Check that DB_USER, DB_PASSWORD, and DB_NAME match your Render PostgreSQL database.",
                        attempt,
                        exc,
                    )
                elif (
                    "connection refused" in error_msg.lower()
                    or "could not connect" in error_msg.lower()
                ):
                    logger.warning(
                        "DB pool attempt %d/3 failed: %s. "
                        "Check that the database host is accessible and the port is correct.",
                        attempt,
                        exc,
                    )
                else:
                    logger.warning("DB pool attempt %d/3 failed: %s", attempt, exc)
                if attempt < 3:
                    import asyncio

                    await asyncio.sleep(3 * attempt)
            except Exception as exc:
                logger.error("Unexpected error creating DB pool: %s", exc)
                raise
        else:
            logger.error(
                "Could not create DB pool after 3 attempts. "
                "The application will start in degraded mode without database connectivity. "
                "To fix this, verify your DATABASE_URL environment variable in Render dashboard."
            )

        await self._run_migrations()

        if s.read_replica_url and s.read_replica_url != s.database_url:
            read_dsn = resolve_dsn_ipv4(s.read_replica_url)

            try:
                self._read_pool = await asyncpg.create_pool(
                    read_dsn,
                    min_size=s.db_pool_min,
                    max_size=s.db_pool_max,
                    ssl=False,
                    statement_cache_size=0,
                    timeout=30.0,
                    command_timeout=60.0,
                )
                logger.info("Read replica pool initialized")
            except Exception as exc:
                logger.warning(
                    "Failed to initialize read replica (falling back to primary): %s",
                    exc,
                )

    async def _run_migrations(self) -> None:
        """Run auto-migrations if needed."""
        if self._pool is None:
            return

        try:
            async with self._pool.acquire() as conn:
                has_tenants = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='tenants')"
                )
                if not has_tenants:
                    logger.info("Running auto-migration (tenants table missing)...")
                    import pathlib

                    base = pathlib.Path(__file__).resolve().parent.parent
                    from packages.backend.domain.migrations import run_migrations

                    await run_migrations(conn, base)
        except asyncpg.PostgresError as exc:
            logger.warning("Auto-migration check failed (DB error): %s", exc)
        except Exception as exc:
            logger.warning("Auto-migration check failed: %s", exc)

    @staticmethod
    def _get_ssl_config(settings: Any) -> Any:
        """Get SSL config for database connection."""
        if getattr(settings, "db_ssl_ca_cert_path", None):
            import ssl

            ctx = ssl.create_default_context(cafile=settings.db_ssl_ca_cert_path)
            return ctx
        # Explicitly disable SSL if no cert path is configured.
        # This prevents "rejected SSL upgrade" errors in local dev with asyncpg.
        return False

    async def close(self) -> None:
        """Close the database pool on shutdown."""
        if self._pool:
            await self._pool.close()
            self._pool = None
        if self._read_pool:
            await self._read_pool.close()
            self._read_pool = None


_pool_manager = DatabasePoolManager()


async def get_pool() -> asyncpg.Pool:
    """Dependency for getting the primary database pool."""
    return _pool_manager.pool


async def get_read_pool() -> asyncpg.Pool:
    """Dependency for getting a read-replica pool if available."""
    return _pool_manager.read_pool


async def get_current_user_id(
    authorization: str | None = Header(None, alias="Authorization"),
    jobhuntin_auth: str | None = Cookie(None),
) -> str:
    """Decode a JWT and return the `sub` claim as user_id.
    S1: Accepts token from Authorization header OR jobhuntin_auth httpOnly cookie.

    SECURITY: Now checks for revoked session tokens via Redis blacklist.
    This prevents session token replay attacks even if a token is stolen.
    """
    import jwt as pyjwt

    s = get_settings()
    if not s.jwt_secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")

    token: str | None = None
    if jobhuntin_auth:
        token = jobhuntin_auth
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")

    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication")

    try:
        payload = pyjwt.decode(
            token, s.jwt_secret, algorithms=["HS256"], audience="authenticated"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401, detail="Invalid token: missing subject"
            )
        jti = payload.get("jti")
        payload.get("session_id")  # M2: Extract session_id for tracking

        # Require jti for revocation check; tokens without jti bypass revocation (reject)
        if not jti:
            logger.warning(
                "Token missing jti claim - rejecting (cannot verify revocation)"
            )
            raise HTTPException(status_code=401, detail="Invalid token: missing jti")

        # Check if session token has been revoked (C1: Session Token Replay Fix)
        revoked = await _check_session_revocation(jti, s)
        if revoked:
            logger.warning(
                "Revoked session token attempted: jti=%s, user_id=%s",
                jti,
                user_id,
            )
            raise HTTPException(
                status_code=401, detail="Session revoked. Please sign in again."
            )

        # M2: session_id is stored in JWT payload and extracted by sessions.py
        # endpoints directly from the cookie for session management

        return user_id
    except HTTPException:
        raise
    except pyjwt.PyJWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as exc:
        logger.warning("Token processing error: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def require_admin_user_id(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> str:
    """Return user_id only if user is system admin.
    Item 23: Admin RBAC — any authenticated user could access admin endpoints.
    Raises 403 if not admin.
    """
    from packages.backend.domain.tenant import (
        TenantScopeError,
        require_system_admin,
    )

    async with db.acquire() as conn:
        # System admin: users.is_system_admin
        # Note: ctx.is_admin is for tenant-specific routes only, not system admin routes
        try:
            await require_system_admin(conn, user_id)
            return user_id
        except TenantScopeError:
            pass

    logger.warning("Admin access denied for user %s", user_id)
    raise HTTPException(status_code=403, detail="Admin access required")


# Aliases for modules expecting get_current_user (dict), get_db_pool, get_tenant_id
get_db_pool = get_pool


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return current user as dict for modules expecting {id, session_id}."""
    return {"id": user_id}


async def get_tenant_id(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> str:
    """Resolve tenant_id for current user."""
    from packages.backend.domain.tenant import resolve_tenant_context

    async with db.acquire() as conn:
        ctx = await resolve_tenant_context(conn, user_id)
        return ctx.tenant_id


async def _is_admin(
    user_id: str = Depends(get_current_user_id),
    db: asyncpg.Pool = Depends(get_pool),
) -> bool:
    """Return True if current user is admin (tenant or system)."""
    from packages.backend.domain.tenant import (
        TenantScopeError,
        require_system_admin,
        resolve_tenant_context,
    )

    async with db.acquire() as conn:
        ctx = await resolve_tenant_context(conn, user_id)
        if ctx.is_admin:
            return True
        try:
            await require_system_admin(conn, user_id)
            return True
        except TenantScopeError:
            return False
