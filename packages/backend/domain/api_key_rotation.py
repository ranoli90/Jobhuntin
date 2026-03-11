"""API Key Rotation — automatic key rotation, expiration, and grace period handling.

Features:
  - Scheduled automatic key rotation
  - Grace period for seamless key transitions
  - Key expiration and renewal
  - Audit logging for key operations
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.api_keys.rotation")


@dataclass
class APIKeyInfo:
    id: str
    tenant_id: str
    key_prefix: str
    name: str | None
    is_active: bool
    expires_at: datetime | None
    rotated_from: str | None
    rotated_to: str | None
    created_at: datetime
    last_used_at: datetime | None
    rate_limit_rpm: int
    monthly_quota: int
    calls_this_month: int

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def days_until_expiry(self) -> int | None:
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)


class APIKeyRotationManager:
    DEFAULT_KEY_LIFETIME_DAYS = 90
    ROTATION_WARNING_DAYS = 14
    GRACE_PERIOD_HOURS = 24

    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    @staticmethod
    def generate_api_key() -> tuple[str, str, str]:
        raw = "sk_live_" + secrets.token_hex(32)
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        prefix = raw[:16]
        return raw, key_hash, prefix

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    async def create_api_key(
        self,
        tenant_id: str,
        name: str | None = None,
        rate_limit_rpm: int = 60,
        monthly_quota: int = 0,
        lifetime_days: int | None = None,
    ) -> tuple[str, APIKeyInfo]:
        raw_key, key_hash, key_prefix = self.generate_api_key()
        lifetime = lifetime_days or self.DEFAULT_KEY_LIFETIME_DAYS
        expires_at = datetime.now(timezone.utc) + timedelta(days=lifetime)

        async with self._pool.acquire() as conn:
            key_id = await conn.fetchval(
                """
                INSERT INTO public.api_keys
                    (tenant_id, key_hash, key_prefix, name, is_active,
                     expires_at, rate_limit_rpm, monthly_quota, calls_this_month)
                VALUES ($1, $2, $3, $4, true, $5, $6, $7, 0)
                RETURNING id
                """,
                tenant_id,
                key_hash,
                key_prefix,
                name,
                expires_at,
                rate_limit_rpm,
                monthly_quota,
            )

            await self._record_audit(
                conn,
                tenant_id,
                "API_KEY_CREATED",
                "api_key",
                str(key_id),
                {
                    "key_prefix": key_prefix,
                    "name": name,
                    "expires_at": expires_at.isoformat(),
                },
            )

        incr("api_keys.created")
        logger.info("API key created: tenant=%s prefix=%s", tenant_id, key_prefix)

        return raw_key, APIKeyInfo(
            id=str(key_id),
            tenant_id=tenant_id,
            key_prefix=key_prefix,
            name=name,
            is_active=True,
            expires_at=expires_at,
            rotated_from=None,
            rotated_to=None,
            created_at=datetime.now(timezone.utc),
            last_used_at=None,
            rate_limit_rpm=rate_limit_rpm,
            monthly_quota=monthly_quota,
            calls_this_month=0,
        )

    async def rotate_api_key(
        self,
        key_id: str,
        grace_period_hours: int | None = None,
    ) -> tuple[str, APIKeyInfo]:
        grace_hours = grace_period_hours or self.GRACE_PERIOD_HOURS

        async with self._pool.acquire() as conn:
            old_key = await conn.fetchrow(
                """
                SELECT id, tenant_id, key_prefix, name, rate_limit_rpm, monthly_quota,
                       rotated_to, expires_at
                FROM public.api_keys
                WHERE id = $1 AND is_active = true
                """,
                key_id,
            )

            if not old_key:
                raise ValueError(f"API key {key_id} not found or inactive")

            if old_key["rotated_to"]:
                raise ValueError(f"API key {key_id} has already been rotated")

            raw_key, key_hash, key_prefix = self.generate_api_key()
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=self.DEFAULT_KEY_LIFETIME_DAYS
            )

            new_key_id = await conn.fetchval(
                """
                INSERT INTO public.api_keys
                    (tenant_id, key_hash, key_prefix, name, is_active, expires_at,
                     rate_limit_rpm, monthly_quota, calls_this_month, rotated_from)
                VALUES ($1, $2, $3, $4, true, $5, $6, $7, 0, $8)
                RETURNING id
                """,
                old_key["tenant_id"],
                key_hash,
                key_prefix,
                old_key["name"],
                expires_at,
                old_key["rate_limit_rpm"],
                old_key["monthly_quota"],
                key_id,
            )

            grace_expires = datetime.now(timezone.utc) + timedelta(hours=grace_hours)
            await conn.execute(
                """
                UPDATE public.api_keys
                SET rotated_to = $1,
                    rotated_at = now(),
                    grace_expires_at = $2
                WHERE id = $3
                """,
                str(new_key_id),
                grace_expires,
                key_id,
            )

            await self._record_audit(
                conn,
                old_key["tenant_id"],
                "API_KEY_ROTATED",
                "api_key",
                key_id,
                {
                    "old_key_prefix": old_key["key_prefix"],
                    "new_key_id": str(new_key_id),
                    "new_key_prefix": key_prefix,
                    "grace_hours": grace_hours,
                },
            )

        incr("api_keys.rotated")
        logger.info(
            "API key rotated: old=%s new=%s tenant=%s",
            old_key["key_prefix"],
            key_prefix,
            old_key["tenant_id"],
        )

        return raw_key, APIKeyInfo(
            id=str(new_key_id),
            tenant_id=old_key["tenant_id"],
            key_prefix=key_prefix,
            name=old_key["name"],
            is_active=True,
            expires_at=expires_at,
            rotated_from=key_id,
            rotated_to=None,
            created_at=datetime.now(timezone.utc),
            last_used_at=None,
            rate_limit_rpm=old_key["rate_limit_rpm"],
            monthly_quota=old_key["monthly_quota"],
            calls_this_month=0,
        )

    async def revoke_api_key(
        self,
        key_id: str,
        reason: str = "USER_REVOKED",
    ) -> bool:
        async with self._pool.acquire() as conn:
            key = await conn.fetchrow(
                """
                UPDATE public.api_keys
                SET is_active = false, revoked_at = now(), revoked_reason = $1
                WHERE id = $2 AND is_active = true
                RETURNING tenant_id, key_prefix
                """,
                reason,
                key_id,
            )

            if not key:
                return False

            await self._record_audit(
                conn,
                key["tenant_id"],
                "API_KEY_REVOKED",
                "api_key",
                key_id,
                {"key_prefix": key["key_prefix"], "reason": reason},
            )

        incr("api_keys.revoked", {"reason": reason.replace("_", "").lower()})
        logger.info("API key revoked: key=%s reason=%s", key["key_prefix"], reason)
        return True

    async def get_keys_near_expiry(
        self,
        days: int | None = None,
    ) -> list[APIKeyInfo]:
        warning_days = days or self.ROTATION_WARNING_DAYS
        threshold = datetime.now(timezone.utc) + timedelta(days=warning_days)

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, tenant_id, key_prefix, name, is_active, expires_at,
                       rotated_from, rotated_to, created_at, last_used_at,
                       rate_limit_rpm, monthly_quota, calls_this_month
                FROM public.api_keys
                WHERE is_active = true
                  AND expires_at IS NOT NULL
                  AND expires_at <= $1
                  AND expires_at > now()
                  AND rotated_to IS NULL
                ORDER BY expires_at ASC
                """,
                threshold,
            )

            return [self._row_to_key_info(row) for row in rows]

    async def get_expired_grace_keys(self) -> list[APIKeyInfo]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, tenant_id, key_prefix, name, is_active, expires_at,
                       rotated_from, rotated_to, created_at, last_used_at,
                       rate_limit_rpm, monthly_quota, calls_this_month
                FROM public.api_keys
                WHERE is_active = true
                  AND rotated_to IS NOT NULL
                  AND grace_expires_at IS NOT NULL
                  AND grace_expires_at < now()
                """,
            )

            return [self._row_to_key_info(row) for row in rows]

    async def cleanup_expired_grace_keys(self) -> int:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE public.api_keys
                SET is_active = false,
                    revoked_at = now(),
                    revoked_reason = 'GRACE_PERIOD_EXPIRED'
                WHERE is_active = true
                  AND rotated_to IS NOT NULL
                  AND grace_expires_at IS NOT NULL
                  AND grace_expires_at < now()
                """
            )
            count = int(result.split()[-1]) if result else 0

        incr("api_keys.grace_expired", None, count)
        logger.info("Cleaned up %d expired grace period keys", count)
        return count

    async def list_tenant_keys(
        self,
        tenant_id: str,
        include_inactive: bool = False,
    ) -> list[APIKeyInfo]:
        async with self._pool.acquire() as conn:
            if include_inactive:
                rows = await conn.fetch(
                    """
                    SELECT id, tenant_id, key_prefix, name, is_active, expires_at,
                           rotated_from, rotated_to, created_at, last_used_at,
                           rate_limit_rpm, monthly_quota, calls_this_month
                    FROM public.api_keys
                    WHERE tenant_id = $1
                    ORDER BY created_at DESC
                    """,
                    tenant_id,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, tenant_id, key_prefix, name, is_active, expires_at,
                           rotated_from, rotated_to, created_at, last_used_at,
                           rate_limit_rpm, monthly_quota, calls_this_month
                    FROM public.api_keys
                    WHERE tenant_id = $1 AND is_active = true
                    ORDER BY created_at DESC
                    """,
                    tenant_id,
                )

            return [self._row_to_key_info(row) for row in rows]

    async def get_key_info(self, key_id: str) -> APIKeyInfo | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, tenant_id, key_prefix, name, is_active, expires_at,
                       rotated_from, rotated_to, created_at, last_used_at,
                       rate_limit_rpm, monthly_quota, calls_this_month
                FROM public.api_keys
                WHERE id = $1
                """,
                key_id,
            )

            if not row:
                return None
            return self._row_to_key_info(row)

    async def reset_monthly_quotas(self) -> int:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE public.api_keys
                SET calls_this_month = 0
                WHERE calls_this_month > 0
                """
            )
            count = int(result.split()[-1]) if result else 0

        incr("api_keys.quotas_reset", None, count)
        logger.info("Reset monthly quotas for %d API keys", count)
        return count

    async def schedule_automatic_rotation(self) -> dict[str, int]:
        near_expiry = await self.get_keys_near_expiry()
        await self.get_expired_grace_keys()

        rotated = 0
        for key in near_expiry:
            try:
                await self.rotate_api_key(key.id)
                rotated += 1
            except Exception as e:
                logger.warning("Failed to auto-rotate key %s: %s", key.key_prefix, e)

        cleaned = await self.cleanup_expired_grace_keys()

        return {
            "rotated": rotated,
            "grace_cleaned": cleaned,
            "pending_rotation": len(near_expiry) - rotated,
        }

    async def _record_audit(
        self,
        conn: asyncpg.Connection,
        tenant_id: str,
        action: str,
        resource: str,
        resource_id: str,
        details: dict[str, Any],
    ) -> None:
        import json

        try:
            await conn.execute(
                """
                INSERT INTO public.audit_log
                    (tenant_id, action, resource, resource_id, details)
                VALUES ($1, $2, $3, $4, $5::jsonb)
                """,
                tenant_id,
                action,
                resource,
                resource_id,
                json.dumps(details),
            )
        except Exception as e:
            logger.warning("Failed to record audit: %s", e)

    def _row_to_key_info(self, row: asyncpg.Record) -> APIKeyInfo:
        return APIKeyInfo(
            id=str(row["id"]),
            tenant_id=str(row["tenant_id"]),
            key_prefix=row["key_prefix"],
            name=row["name"],
            is_active=row["is_active"],
            expires_at=row["expires_at"],
            rotated_from=str(row["rotated_from"]) if row["rotated_from"] else None,
            rotated_to=str(row["rotated_to"]) if row["rotated_to"] else None,
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
            rate_limit_rpm=row["rate_limit_rpm"] or 60,
            monthly_quota=row["monthly_quota"] or 0,
            calls_this_month=row["calls_this_month"] or 0,
        )


async def init_api_keys_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.api_keys (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            key_hash TEXT NOT NULL UNIQUE,
            key_prefix TEXT NOT NULL,
            name TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            expires_at TIMESTAMPTZ,
            last_used_at TIMESTAMPTZ,
            rate_limit_rpm INTEGER DEFAULT 60,
            monthly_quota INTEGER DEFAULT 0,
            calls_this_month INTEGER DEFAULT 0,
            rotated_from UUID REFERENCES public.api_keys(id) ON DELETE SET NULL,
            rotated_to UUID REFERENCES public.api_keys(id) ON DELETE SET NULL,
            rotated_at TIMESTAMPTZ,
            grace_expires_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            revoked_reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON public.api_keys(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON public.api_keys(key_hash);
        CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON public.api_keys(expires_at);
        """
    )

    try:
        await conn.execute(
            """
            ALTER TABLE public.api_keys
            ADD COLUMN IF NOT EXISTS rotated_from UUID REFERENCES public.api_keys(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS rotated_to UUID REFERENCES public.api_keys(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS rotated_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS grace_expires_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS revoked_reason TEXT
            """
        )
    except Exception:
        pass

    logger.info("API keys table initialized")
