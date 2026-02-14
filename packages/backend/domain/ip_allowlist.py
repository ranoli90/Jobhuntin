"""
IP Allowlisting — enterprise tenant network security.

Features:
  - Per-tenant IP allowlists for API access
  - CIDR notation support for network ranges
  - IPv4 and IPv6 support
  - Temporary access codes for emergency access
  - Audit logging for allowed/blocked requests
"""

from __future__ import annotations

import ipaddress
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.ip_allowlist")


@dataclass
class IPAllowlistEntry:
    id: str
    tenant_id: str
    name: str
    cidr: str
    description: str | None
    created_by: str | None
    created_at: datetime
    is_active: bool = True


@dataclass
class TemporaryAccessCode:
    code: str
    tenant_id: str
    user_id: str
    ip_address: str
    expires_at: datetime
    used: bool = False
    used_at: datetime | None = None


class IPAllowlistManager:
    MAX_ENTRIES_PER_TENANT = 100
    TEMP_CODE_LENGTH = 16
    TEMP_CODE_DURATION_HOURS = 4

    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    @staticmethod
    def parse_cidr(cidr: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
        try:
            if "/" in cidr:
                return ipaddress.ip_network(cidr, strict=False)
            return ipaddress.ip_network(f"{cidr}/32", strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation: {cidr}") from e

    @staticmethod
    def is_ip_in_cidr(ip: str, cidr: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            network = IPAllowlistManager.parse_cidr(cidr)
            return ip_obj in network
        except ValueError:
            return False

    @staticmethod
    def is_ip_in_allowlist(ip: str, allowlist: list[str]) -> bool:
        if not allowlist:
            return True

        for cidr in allowlist:
            if IPAllowlistManager.is_ip_in_cidr(ip, cidr):
                return True
        return False

    async def add_entry(
        self,
        tenant_id: str,
        name: str,
        cidr: str,
        description: str | None = None,
        created_by: str | None = None,
    ) -> IPAllowlistEntry:
        network = self.parse_cidr(cidr)

        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*)::int FROM public.tenant_ip_allowlist
                WHERE tenant_id = $1 AND is_active = true
                """,
                tenant_id,
            )

            if count >= self.MAX_ENTRIES_PER_TENANT:
                raise ValueError(
                    f"Maximum {self.MAX_ENTRIES_PER_TENANT} entries allowed per tenant"
                )

            entry_id = await conn.fetchval(
                """
                INSERT INTO public.tenant_ip_allowlist
                    (tenant_id, name, cidr, description, created_by, is_active)
                VALUES ($1, $2, $3, $4, $5, true)
                RETURNING id
                """,
                tenant_id,
                name,
                str(network),
                description,
                created_by,
            )

            await self._record_audit(
                conn,
                tenant_id,
                created_by,
                "IP_ALLOWLIST_ADDED",
                "ip_allowlist_entry",
                str(entry_id),
                {"name": name, "cidr": str(network)},
            )

        incr("ip_allowlist.entry_added")
        logger.info(
            "IP allowlist entry added: tenant=%s cidr=%s", tenant_id, str(network)
        )

        return IPAllowlistEntry(
            id=str(entry_id),
            tenant_id=tenant_id,
            name=name,
            cidr=str(network),
            description=description,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )

    async def remove_entry(
        self,
        tenant_id: str,
        entry_id: str,
        removed_by: str | None = None,
    ) -> bool:
        async with self._pool.acquire() as conn:
            entry = await conn.fetchrow(
                """
                UPDATE public.tenant_ip_allowlist
                SET is_active = false, removed_at = now(), removed_by = $1
                WHERE id = $2 AND tenant_id = $3 AND is_active = true
                RETURNING name, cidr
                """,
                removed_by,
                entry_id,
                tenant_id,
            )

            if not entry:
                return False

            await self._record_audit(
                conn,
                tenant_id,
                removed_by,
                "IP_ALLOWLIST_REMOVED",
                "ip_allowlist_entry",
                entry_id,
                {"name": entry["name"], "cidr": entry["cidr"]},
            )

        incr("ip_allowlist.entry_removed")
        return True

    async def get_tenant_allowlist(self, tenant_id: str) -> list[IPAllowlistEntry]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, tenant_id, name, cidr, description, created_by, created_at, is_active
                FROM public.tenant_ip_allowlist
                WHERE tenant_id = $1 AND is_active = true
                ORDER BY created_at DESC
                """,
                tenant_id,
            )

            return [
                IPAllowlistEntry(
                    id=str(r["id"]),
                    tenant_id=str(r["tenant_id"]),
                    name=r["name"],
                    cidr=r["cidr"],
                    description=r["description"],
                    created_by=str(r["created_by"]) if r["created_by"] else None,
                    created_at=r["created_at"],
                    is_active=r["is_active"],
                )
                for r in rows
            ]

    async def get_allowlist_cidrs(self, tenant_id: str) -> list[str]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT cidr FROM public.tenant_ip_allowlist
                WHERE tenant_id = $1 AND is_active = true
                """,
                tenant_id,
            )
            return [r["cidr"] for r in rows]

    async def check_ip_access(
        self,
        tenant_id: str,
        ip_address: str,
    ) -> tuple[bool, str | None]:
        allowlist = await self.get_allowlist_cidrs(tenant_id)

        if not allowlist:
            return True, None

        if self.is_ip_in_allowlist(ip_address, allowlist):
            incr("ip_allowlist.access_allowed")
            return True, None

        incr("ip_allowlist.access_blocked")
        return False, f"IP {ip_address} not in allowlist"

    async def generate_temporary_access_code(
        self,
        tenant_id: str,
        user_id: str,
        ip_address: str,
        duration_hours: int | None = None,
    ) -> str:
        code = secrets.token_urlsafe(self.TEMP_CODE_LENGTH)
        duration = duration_hours or self.TEMP_CODE_DURATION_HOURS
        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration)

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.tenant_temp_access_codes
                    (code, tenant_id, user_id, ip_address, expires_at, used)
                VALUES ($1, $2, $3, $4, $5, false)
                """,
                code,
                tenant_id,
                user_id,
                ip_address,
                expires_at,
            )

            await self._record_audit(
                conn,
                tenant_id,
                user_id,
                "TEMP_ACCESS_CODE_GENERATED",
                "temp_access_code",
                code[:8],
                {"ip_address": ip_address, "expires_at": expires_at.isoformat()},
            )

        incr("ip_allowlist.temp_code_generated")
        logger.info(
            "Temporary access code generated: tenant=%s ip=%s", tenant_id, ip_address
        )
        return code

    async def validate_temporary_access_code(
        self,
        code: str,
        tenant_id: str,
        ip_address: str,
    ) -> tuple[bool, str | None]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT code, tenant_id, user_id, ip_address, expires_at, used
                FROM public.tenant_temp_access_codes
                WHERE code = $1 AND tenant_id = $2
                """,
                code,
                tenant_id,
            )

            if not row:
                return False, "Invalid access code"

            if row["used"]:
                return False, "Access code already used"

            if datetime.now(timezone.utc) > row["expires_at"]:
                return False, "Access code expired"

            if row["ip_address"] and row["ip_address"] != ip_address:
                return False, "Access code is IP-restricted"

            await conn.execute(
                """
                UPDATE public.tenant_temp_access_codes
                SET used = true, used_at = now()
                WHERE code = $1
                """,
                code,
            )

            await self._record_audit(
                conn,
                tenant_id,
                row["user_id"],
                "TEMP_ACCESS_CODE_USED",
                "temp_access_code",
                code[:8],
                {"ip_address": ip_address},
            )

        incr("ip_allowlist.temp_code_used")
        return True, None

    async def cleanup_expired_codes(self) -> int:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM public.tenant_temp_access_codes
                WHERE expires_at < now() - INTERVAL '7 days'
                """
            )
            count = int(result.split()[-1])

        incr("ip_allowlist.temp_codes_cleaned", None, count)
        return count

    async def enable_ip_allowlisting(
        self,
        tenant_id: str,
        enabled_by: str | None = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.tenants
                SET ip_allowlist_enabled = true
                WHERE id = $1
                """,
                tenant_id,
            )

            await self._record_audit(
                conn,
                tenant_id,
                enabled_by,
                "IP_ALLOWLIST_ENABLED",
                "tenant",
                tenant_id,
                {},
            )

        incr("ip_allowlist.enabled")
        logger.info("IP allowlisting enabled: tenant=%s", tenant_id)

    async def disable_ip_allowlisting(
        self,
        tenant_id: str,
        disabled_by: str | None = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.tenants
                SET ip_allowlist_enabled = false
                WHERE id = $1
                """,
                tenant_id,
            )

            await self._record_audit(
                conn,
                tenant_id,
                disabled_by,
                "IP_ALLOWLIST_DISABLED",
                "tenant",
                tenant_id,
                {},
            )

        incr("ip_allowlist.disabled")
        logger.info("IP allowlisting disabled: tenant=%s", tenant_id)

    async def is_ip_allowlisting_enabled(self, tenant_id: str) -> bool:
        async with self._pool.acquire() as conn:
            return (
                await conn.fetchval(
                    """
                SELECT ip_allowlist_enabled FROM public.tenants
                WHERE id = $1
                """,
                    tenant_id,
                )
                or False
            )

    async def _record_audit(
        self,
        conn: asyncpg.Connection,
        tenant_id: str,
        user_id: str | None,
        action: str,
        resource: str,
        resource_id: str,
        details: dict[str, Any],
    ) -> None:
        try:
            await conn.execute(
                """
                INSERT INTO public.audit_log
                    (tenant_id, user_id, action, resource, resource_id, details)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                """,
                tenant_id,
                user_id,
                action,
                resource,
                resource_id,
                json.dumps(details),
            )
        except Exception as e:
            logger.warning("Failed to record audit: %s", e)


async def init_ip_allowlist_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.tenant_ip_allowlist (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            cidr TEXT NOT NULL,
            description TEXT,
            created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT true,
            removed_at TIMESTAMPTZ,
            removed_by UUID REFERENCES public.users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS public.tenant_temp_access_codes (
            code TEXT PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            ip_address TEXT,
            expires_at TIMESTAMPTZ NOT NULL,
            used BOOLEAN NOT NULL DEFAULT false,
            used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_ip_allowlist_tenant_id
            ON public.tenant_ip_allowlist(tenant_id);

        CREATE INDEX IF NOT EXISTS idx_temp_codes_tenant_id
            ON public.tenant_temp_access_codes(tenant_id);

        CREATE INDEX IF NOT EXISTS idx_temp_codes_expires_at
            ON public.tenant_temp_access_codes(expires_at);
        """
    )

    try:
        await conn.execute(
            """
            ALTER TABLE public.tenants
            ADD COLUMN IF NOT EXISTS ip_allowlist_enabled BOOLEAN DEFAULT false
            """
        )
    except Exception:
        pass

    logger.info("IP allowlist tables initialized")
