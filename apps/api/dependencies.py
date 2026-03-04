from __future__ import annotations

import asyncpg
from fastapi import (
    Cookie,
    Header,
    HTTPException,
)
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.api.dependencies")

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
        from backend.blueprints.registry import load_default_blueprints

        enabled = [
            slug.strip() for slug in s.enabled_blueprints.split(",") if slug.strip()
        ]
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
    def _get_ssl_config(settings: any) -> any:
        """Get SSL config for database connection."""
        if settings.db_ssl_ca_cert_path:
            import ssl
            ctx = ssl.create_default_context(cafile=settings.db_ssl_ca_cert_path)
            return ctx
        return None

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

    NOTE: Token replay protection (jti check) is handled at the /auth/verify-magic
    endpoint level only. We do NOT check jti here because the httpOnly auth cookie
    reuses the same JWT for the entire session — consuming the jti on the first
    API call would block all subsequent calls.
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
        user_id: str = payload["sub"]
        return user_id
    except pyjwt.PyJWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as exc:
        logger.warning("Token processing error: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

