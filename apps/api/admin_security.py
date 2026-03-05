"""Admin Security API endpoints — IP allowlisting and data residency."""

from __future__ import annotations

from typing import Any

import asyncpg
from backend.domain.data_residency import (
    REGION_CONFIGS,
    DataRegion,
    DataResidencyManager,
)
from backend.domain.ip_allowlist import IPAllowlistManager
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared.logging_config import get_logger

logger = get_logger("sorce.api.admin_security")

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_user_id() -> str:
    raise NotImplementedError("User ID dependency not injected")


async def _get_tenant_id() -> str:
    raise NotImplementedError("Tenant ID dependency not injected")


# ============ IP ALLOWLIST ============

ip_allowlist_router = APIRouter(prefix="/ip-allowlist", tags=["ip-allowlist"])


class AddIPEntryRequest(BaseModel):
    name: str
    cidr: str
    description: str | None = None


class IPEntryResponse(BaseModel):
    id: str
    name: str
    cidr: str
    description: str | None
    created_at: str
    is_active: bool


class CheckIPRequest(BaseModel):
    ip_address: str


class GenerateTempCodeRequest(BaseModel):
    ip_address: str
    duration_hours: int | None = None


class ValidateTempCodeRequest(BaseModel):
    code: str
    ip_address: str


@ip_allowlist_router.post("/entries", response_model=IPEntryResponse)
async def add_ip_entry(
    body: AddIPEntryRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> IPEntryResponse:
    manager = IPAllowlistManager(db)

    try:
        entry = await manager.add_entry(
            tenant_id=tenant_id,
            name=body.name,
            cidr=body.cidr,
            description=body.description,
            created_by=user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return IPEntryResponse(
        id=entry.id,
        name=entry.name,
        cidr=entry.cidr,
        description=entry.description,
        created_at=entry.created_at.isoformat(),
        is_active=entry.is_active,
    )


@ip_allowlist_router.get("/entries", response_model=list[IPEntryResponse])
async def list_ip_entries(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> list[IPEntryResponse]:
    manager = IPAllowlistManager(db)

    entries = await manager.get_tenant_allowlist(tenant_id)

    return [
        IPEntryResponse(
            id=e.id,
            name=e.name,
            cidr=e.cidr,
            description=e.description,
            created_at=e.created_at.isoformat(),
            is_active=e.is_active,
        )
        for e in entries
    ]


@ip_allowlist_router.delete("/entries/{entry_id}")
async def remove_ip_entry(
    entry_id: str,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = IPAllowlistManager(db)

    success = await manager.remove_entry(
        tenant_id=tenant_id,
        entry_id=entry_id,
        removed_by=user_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"status": "removed"}


@ip_allowlist_router.post("/check")
async def check_ip_access(
    body: CheckIPRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = IPAllowlistManager(db)

    allowed, reason = await manager.check_ip_access(tenant_id, body.ip_address)

    return {
        "allowed": allowed,
        "reason": reason,
    }


@ip_allowlist_router.post("/temp-codes")
async def generate_temp_code(
    body: GenerateTempCodeRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = IPAllowlistManager(db)

    code = await manager.generate_temporary_access_code(
        tenant_id=tenant_id,
        user_id=user_id,
        ip_address=body.ip_address,
        duration_hours=body.duration_hours,
    )

    return {
        "code": code,
        "expires_in_hours": body.duration_hours or 4,
    }


@ip_allowlist_router.post("/temp-codes/validate")
async def validate_temp_code(
    body: ValidateTempCodeRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = IPAllowlistManager(db)

    valid, reason = await manager.validate_temporary_access_code(
        code=body.code,
        tenant_id=tenant_id,
        ip_address=body.ip_address,
    )

    return {
        "valid": valid,
        "reason": reason,
    }


@ip_allowlist_router.post("/enable")
async def enable_ip_allowlisting(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = IPAllowlistManager(db)

    await manager.enable_ip_allowlisting(tenant_id, enabled_by=user_id)

    return {"status": "enabled"}


@ip_allowlist_router.post("/disable")
async def disable_ip_allowlisting(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = IPAllowlistManager(db)

    await manager.disable_ip_allowlisting(tenant_id, disabled_by=user_id)

    return {"status": "disabled"}


@ip_allowlist_router.get("/status")
async def get_ip_allowlist_status(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = IPAllowlistManager(db)

    enabled = await manager.is_ip_allowlisting_enabled(tenant_id)
    entries = await manager.get_tenant_allowlist(tenant_id)

    return {
        "enabled": enabled,
        "entries_count": len(entries),
    }


# ============ DATA RESIDENCY ============

data_residency_router = APIRouter(prefix="/data-residency", tags=["data-residency"])


class SetRegionRequest(BaseModel):
    primary_region: str
    backup_region: str | None = None
    data_types: list[str] | None = None
    cross_region_transfer_allowed: bool = False


class DataLocationResponse(BaseModel):
    primary_region: str
    backup_region: str | None
    data_types: list[str]
    enforced_at: str | None


@data_residency_router.put("/region")
async def set_data_residency(
    body: SetRegionRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    manager = DataResidencyManager(db)

    try:
        primary_region = DataRegion(body.primary_region.lower())
    except ValueError:
        valid_regions = [r.value for r in DataRegion]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region. Valid regions: {valid_regions}",
        )

    backup_region = None
    if body.backup_region:
        try:
            backup_region = DataRegion(body.backup_region.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid backup region")

    await manager.set_tenant_data_residency(
        tenant_id=tenant_id,
        primary_region=primary_region,
        backup_region=backup_region,
        data_types=body.data_types,
        cross_region_transfer_allowed=body.cross_region_transfer_allowed,
    )

    return {
        "status": "configured",
        "primary_region": primary_region.value,
        "backup_region": backup_region.value if backup_region else None,
    }


@data_residency_router.get("/region", response_model=DataLocationResponse)
async def get_data_residency(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> DataLocationResponse:
    manager = DataResidencyManager(db)

    residency = await manager.get_tenant_data_residency(tenant_id)

    if not residency:
        return DataLocationResponse(
            primary_region="us-east",
            backup_region=None,
            data_types=[],
            enforced_at=None,
        )

    return DataLocationResponse(
        primary_region=residency.primary_region.value,
        backup_region=(
            residency.backup_region.value if residency.backup_region else None
        ),
        data_types=residency.data_types,
        enforced_at=residency.enforced_at.isoformat(),
    )


@data_residency_router.get("/available-regions")
async def list_available_regions() -> list[dict[str, Any]]:
    return [
        {
            "code": config.region.value,
            "name": config.display_name,
            "compliance": config.compliance_frameworks,
        }
        for config in REGION_CONFIGS.values()
        if config.is_active
    ]


@data_residency_router.get("/audit-log")
async def get_transfer_history(
    limit: int = 50,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> list[dict[str, Any]]:
    manager = DataResidencyManager(db)

    entries = await manager.get_transfer_history(tenant_id, limit)

    return entries


@data_residency_router.get("/compliance-report")
async def get_residency_compliance_report(
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = DataResidencyManager(db)

    report = await manager.get_residency_compliance_report(tenant_id)

    return report


@data_residency_router.post("/verify")
async def verify_data_residency(
    data_type: str,
    actual_region: str,
    db: asyncpg.Pool = Depends(_get_pool),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, Any]:
    manager = DataResidencyManager(db)

    compliant, message = await manager.verify_data_residency(
        tenant_id=tenant_id,
        data_type=data_type,
        actual_region=actual_region,
    )

    return {
        "compliant": compliant,
        "message": message,
    }


def _get_region_name(region: DataRegion) -> str:
    config = REGION_CONFIGS.get(region)
    return config.display_name if config else region.value


def _get_region_compliance(region: DataRegion) -> list[str]:
    config = REGION_CONFIGS.get(region)
    return config.compliance_frameworks if config else []


# Register sub-routers
router.include_router(ip_allowlist_router)
router.include_router(data_residency_router)
