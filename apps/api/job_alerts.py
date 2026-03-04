"""Job Alerts API endpoints.

Provides REST API for managing job alerts and a worker endpoint for processing.
"""

from __future__ import annotations

from typing import Any

import asyncpg
from packages.backend.domain.job_alerts import (
    AlertFrequency,
    JobAlert,
    JobAlertService,
)
from fastapi import APIRouter, Depends, HTTPException
from shared.logging_config import get_logger

from packages.backend.domain.tenant import TenantContext, get_tenant_context
from shared.metrics import incr

logger = get_logger("sorce.api.job_alerts")
router = APIRouter(prefix="/v1/alerts", tags=["Job Alerts"])


class CreateAlertRequest:
    name: str = "Job Alert"
    keywords: list[str] = []
    locations: list[str] = []
    salary_min: int | None = None
    salary_max: int | None = None
    companies_include: list[str] = []
    companies_exclude: list[str] = []
    job_types: list[str] = []
    remote_only: bool = False
    frequency: str = "daily"


class AlertResponse:
    id: str
    name: str
    keywords: list[str]
    locations: list[str]
    frequency: str
    is_active: bool
    last_sent_at: str | None


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


def get_alert_service(pool: asyncpg.Pool = Depends(_get_pool)) -> JobAlertService:
    return JobAlertService(pool)


@router.post("", response_model=dict[str, Any])
async def create_alert(
    request: CreateAlertRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    service: JobAlertService = Depends(get_alert_service),
) -> dict[str, Any]:
    incr("api.job_alerts.create", tags={"tenant_id": ctx.tenant_id})

    alert = JobAlert(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        name=request.name,
        keywords=request.keywords,
        locations=request.locations,
        salary_min=request.salary_min,
        salary_max=request.salary_max,
        companies_include=request.companies_include,
        companies_exclude=request.companies_exclude,
        job_types=request.job_types,
        remote_only=request.remote_only,
        frequency=AlertFrequency(request.frequency),
    )

    alert_id = await service.create_alert(alert)

    return {
        "id": alert_id,
        "name": alert.name,
        "frequency": alert.frequency.value,
        "is_active": True,
    }


@router.get("", response_model=list[dict[str, Any]])
async def list_alerts(
    ctx: TenantContext = Depends(get_tenant_context),
    service: JobAlertService = Depends(get_alert_service),
) -> list[dict[str, Any]]:
    incr("api.job_alerts.list", tags={"tenant_id": ctx.tenant_id})
    alerts = await service.get_user_alerts(ctx.user_id)

    return [
        {
            "id": a.id,
            "name": a.name,
            "keywords": a.keywords,
            "locations": a.locations,
            "frequency": a.frequency.value,
            "is_active": a.is_active,
            "last_sent_at": a.last_sent_at.isoformat() if a.last_sent_at else None,
        }
        for a in alerts
    ]


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    service: JobAlertService = Depends(get_alert_service),
) -> dict[str, str]:
    incr("api.job_alerts.delete", tags={"tenant_id": ctx.tenant_id})
    success = await service.delete_alert(alert_id, ctx.user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"status": "deleted"}


@router.post("/process/{frequency}")
async def process_alerts(
    frequency: str,
    pool: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, int]:
    incr("api.job_alerts.process", tags={"frequency": frequency})

    try:
        freq = AlertFrequency(frequency)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid frequency. Use 'daily' or 'weekly'"
        )

    service = JobAlertService(pool)
    result = await service.process_alerts(freq)

    return result
