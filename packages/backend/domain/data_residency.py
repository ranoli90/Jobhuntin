"""Data Residency — region-specific data storage for compliance.

Features:
  - Region-specific data storage selection
  - Data residency verification
  - Cross-region data transfer logging
  - Compliance with EU GDPR, UK DPA, etc.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timezone, UTC, datetime
from enum import StrEnum
from typing import Any

import asyncpg
from shared.logging_config import get_logger

from shared.metrics import incr

logger = get_logger("sorce.data_residency")


class DataRegion(StrEnum):
    US_EAST = "us-east"
    US_WEST = "us-west"
    EU_WEST = "eu-west"
    EU_CENTRAL = "eu-central"
    UK_SOUTH = "uk-south"
    AP_SOUTHEAST = "ap-southeast"
    AP_NORTHEAST = "ap-northeast"


@dataclass
class RegionConfig:
    region: DataRegion
    display_name: str
    compliance_frameworks: list[str]
    storage_endpoint: str | None = None
    database_host: str | None = None
    is_active: bool = True


REGION_CONFIGS: dict[DataRegion, RegionConfig] = {
    DataRegion.US_EAST: RegionConfig(
        region=DataRegion.US_EAST,
        display_name="United States (East)",
        compliance_frameworks=["SOC2", "HIPAA", "CCPA"],
        storage_endpoint="storage.us-east.jobhuntin.com",
        database_host="db.us-east.render.com",
    ),
    DataRegion.US_WEST: RegionConfig(
        region=DataRegion.US_WEST,
        display_name="United States (West)",
        compliance_frameworks=["SOC2", "HIPAA", "CCPA"],
        storage_endpoint="storage.us-west.jobhuntin.com",
        database_host="db.us-west.render.com",
    ),
    DataRegion.EU_WEST: RegionConfig(
        region=DataRegion.EU_WEST,
        display_name="Europe (Ireland)",
        compliance_frameworks=["GDPR", "SOC2"],
        storage_endpoint="storage.eu-west.jobhuntin.com",
        database_host="db.eu-west.render.com",
    ),
    DataRegion.EU_CENTRAL: RegionConfig(
        region=DataRegion.EU_CENTRAL,
        display_name="Europe (Frankfurt)",
        compliance_frameworks=["GDPR", "SOC2"],
        storage_endpoint="storage.eu-central.jobhuntin.com",
        database_host="db.eu-central.render.com",
    ),
    DataRegion.UK_SOUTH: RegionConfig(
        region=DataRegion.UK_SOUTH,
        display_name="United Kingdom (London)",
        compliance_frameworks=["GDPR", "UK_DPA", "SOC2"],
        storage_endpoint="storage.uk-south.jobhuntin.com",
        database_host="db.uk-south.render.com",
    ),
    DataRegion.AP_SOUTHEAST: RegionConfig(
        region=DataRegion.AP_SOUTHEAST,
        display_name="Asia Pacific (Singapore)",
        compliance_frameworks=["SOC2", "PDPA_SG"],
        storage_endpoint="storage.ap-southeast.jobhuntin.com",
        database_host="db.ap-southeast.render.com",
    ),
    DataRegion.AP_NORTHEAST: RegionConfig(
        region=DataRegion.AP_NORTHEAST,
        display_name="Asia Pacific (Tokyo)",
        compliance_frameworks=["SOC2", "APPI"],
        storage_endpoint="storage.ap-northeast.jobhuntin.com",
        database_host="db.ap-northeast.render.com",
    ),
}


@dataclass
class TenantDataResidency:
    tenant_id: str
    primary_region: DataRegion
    backup_region: DataRegion | None
    enforced_at: datetime
    data_types: list[str]
    cross_region_transfer_allowed: bool = False
    last_audit_at: datetime | None = None


class DataResidencyManager:
    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    @staticmethod
    def get_available_regions() -> list[dict[str, Any]]:
        return [
            {
                "region": config.region.value,
                "display_name": config.display_name,
                "compliance_frameworks": config.compliance_frameworks,
                "is_active": config.is_active,
            }
            for config in REGION_CONFIGS.values()
            if config.is_active
        ]

    @staticmethod
    def get_region_config(region: DataRegion) -> RegionConfig | None:
        return REGION_CONFIGS.get(region)

    @staticmethod
    def get_compliance_for_region(region: DataRegion) -> list[str]:
        config = REGION_CONFIGS.get(region)
        return config.compliance_frameworks if config else []

    async def set_tenant_data_residency(
        self,
        tenant_id: str,
        primary_region: DataRegion,
        backup_region: DataRegion | None = None,
        data_types: list[str] | None = None,
        cross_region_transfer_allowed: bool = False,
    ) -> TenantDataResidency:
        if primary_region not in REGION_CONFIGS:
            raise ValueError(f"Invalid region: {primary_region}")

        if backup_region and backup_region not in REGION_CONFIGS:
            raise ValueError(f"Invalid backup region: {backup_region}")

        types = data_types or ["users", "profiles", "applications", "jobs", "analytics"]

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.tenant_data_residency
                    (tenant_id, primary_region, backup_region, enforced_at,
                     data_types, cross_region_transfer_allowed)
                VALUES ($1, $2, $3, now(), $4::text[], $5)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    primary_region = $2,
                    backup_region = $3,
                    enforced_at = now(),
                    data_types = $4::text[],
                    cross_region_transfer_allowed = $5
                """,
                tenant_id,
                primary_region.value,
                backup_region.value if backup_region else None,
                types,
                cross_region_transfer_allowed,
            )

            await self._record_audit(
                conn,
                tenant_id,
                "DATA_RESIDENCY_SET",
                "tenant",
                tenant_id,
                {
                    "primary_region": primary_region.value,
                    "backup_region": backup_region.value if backup_region else None,
                    "data_types": types,
                },
            )

        incr("data_residency.set")
        logger.info(
            "Data residency set: tenant=%s region=%s",
            tenant_id,
            primary_region.value,
        )

        return TenantDataResidency(
            tenant_id=tenant_id,
            primary_region=primary_region,
            backup_region=backup_region,
            enforced_at=datetime.now(timezone.utc),
            data_types=types,
            cross_region_transfer_allowed=cross_region_transfer_allowed,
        )

    async def get_tenant_data_residency(
        self,
        tenant_id: str,
    ) -> TenantDataResidency | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT tenant_id, primary_region, backup_region, enforced_at,
                       data_types, cross_region_transfer_allowed, last_audit_at
                FROM public.tenant_data_residency
                WHERE tenant_id = $1
                """,
                tenant_id,
            )

            if not row:
                return None

            return TenantDataResidency(
                tenant_id=str(row["tenant_id"]),
                primary_region=DataRegion(row["primary_region"]),
                backup_region=DataRegion(row["backup_region"])
                if row["backup_region"]
                else None,
                enforced_at=row["enforced_at"],
                data_types=list(row["data_types"]) if row["data_types"] else [],
                cross_region_transfer_allowed=row["cross_region_transfer_allowed"],
                last_audit_at=row["last_audit_at"],
            )

    async def verify_data_residency(
        self,
        tenant_id: str,
        data_type: str,
        actual_region: str,
    ) -> tuple[bool, str | None]:
        residency = await self.get_tenant_data_residency(tenant_id)

        if not residency:
            return True, None

        if data_type not in residency.data_types:
            return True, None

        if actual_region == residency.primary_region.value:
            return True, None

        if residency.backup_region and actual_region == residency.backup_region.value:
            return True, None

        if residency.cross_region_transfer_allowed:
            return True, "Cross-region transfer allowed but logged"

        incr("data_residency.violation")
        return (
            False,
            f"Data residency violation: {data_type} stored in {actual_region}, expected {residency.primary_region.value}",
        )

    async def log_cross_region_transfer(
        self,
        tenant_id: str,
        data_type: str,
        source_region: str,
        destination_region: str,
        bytes_transferred: int,
        reason: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.cross_region_transfers
                    (tenant_id, data_type, source_region, destination_region,
                     bytes_transferred, reason)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                tenant_id,
                data_type,
                source_region,
                destination_region,
                bytes_transferred,
                reason,
            )

            await self._record_audit(
                conn,
                tenant_id,
                "CROSS_REGION_TRANSFER",
                "data_transfer",
                None,
                {
                    "data_type": data_type,
                    "source": source_region,
                    "destination": destination_region,
                    "bytes": bytes_transferred,
                },
            )

        incr("data_residency.cross_region_transfer")

    async def get_transfer_history(
        self,
        tenant_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT data_type, source_region, destination_region,
                       bytes_transferred, reason, created_at
                FROM public.cross_region_transfers
                WHERE tenant_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                tenant_id,
                limit,
            )

            return [dict(r) for r in rows]

    async def get_residency_compliance_report(
        self,
        tenant_id: str,
    ) -> dict[str, Any]:
        residency = await self.get_tenant_data_residency(tenant_id)

        if not residency:
            return {
                "compliant": True,
                "message": "No data residency restrictions configured",
            }

        region_config = REGION_CONFIGS.get(residency.primary_region)

        return {
            "compliant": True,
            "primary_region": {
                "region": residency.primary_region.value,
                "display_name": region_config.display_name if region_config else None,
                "compliance_frameworks": region_config.compliance_frameworks
                if region_config
                else [],
            },
            "backup_region": residency.backup_region.value
            if residency.backup_region
            else None,
            "data_types_covered": residency.data_types,
            "cross_region_transfer_allowed": residency.cross_region_transfer_allowed,
            "enforced_at": residency.enforced_at.isoformat(),
            "last_audit_at": residency.last_audit_at.isoformat()
            if residency.last_audit_at
            else None,
        }

    async def _record_audit(
        self,
        conn: asyncpg.Connection,
        tenant_id: str,
        action: str,
        resource: str,
        resource_id: str | None,
        details: dict[str, Any],
    ) -> None:
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


async def init_data_residency_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.tenant_data_residency (
            tenant_id UUID PRIMARY KEY REFERENCES public.tenants(id) ON DELETE CASCADE,
            primary_region TEXT NOT NULL,
            backup_region TEXT,
            enforced_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            data_types TEXT[] NOT NULL DEFAULT '{}',
            cross_region_transfer_allowed BOOLEAN NOT NULL DEFAULT false,
            last_audit_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS public.cross_region_transfers (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            data_type TEXT NOT NULL,
            source_region TEXT NOT NULL,
            destination_region TEXT NOT NULL,
            bytes_transferred BIGINT NOT NULL DEFAULT 0,
            reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_data_residency_tenant_id
            ON public.tenant_data_residency(tenant_id);

        CREATE INDEX IF NOT EXISTS idx_cross_region_tenant_id
            ON public.cross_region_transfers(tenant_id);

        CREATE INDEX IF NOT EXISTS idx_cross_region_created_at
            ON public.cross_region_transfers(created_at);
        """
    )
    logger.info("Data residency tables initialized")
