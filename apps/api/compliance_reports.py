"""Compliance Reports API — GDPR/CCPA compliance reporting endpoints.

This module provides admin endpoints for:
- GET /compliance/overview - Dashboard with consent rates, data processing stats
- GET /compliance/consent-report - Detailed consent report by type/date
- GET /compliance/data-processing - List of data processing activities
- GET /compliance/export - Generate downloadable compliance report (CSV/JSON)
- GET /compliance/audit-log - Searchable audit log for compliance

All endpoints require admin authentication.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from packages.backend.domain import compliance_tracker
from shared.logging_config import get_logger

logger = get_logger("sorce.compliance_reports")

router = APIRouter(prefix="/compliance", tags=["compliance"])


# Dependency placeholder - will be overridden in main.py
async def _get_admin_user_id() -> str:
    """Get admin user ID - overridden in main.py."""
    raise NotImplementedError("Auth dependency not injected")


async def _get_pool() -> asyncpg.Pool:
    """Get database pool - overridden in main.py."""
    raise NotImplementedError("DB pool not injected")


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class ConsentRate(BaseModel):
    opted_in: int
    opted_out: int
    total: int
    rate: float


class ConsentRatesResponse(BaseModel):
    marketing: ConsentRate
    analytics: ConsentRate
    cookies: ConsentRate
    functional: ConsentRate
    essential: ConsentRate


class DataVolumeMetrics(BaseModel):
    count: int
    latest_record: str | None


class DataVolumeResponse(BaseModel):
    profiles: DataVolumeMetrics
    applications: DataVolumeMetrics
    resumes: DataVolumeMetrics


class DeletionRequestsResponse(BaseModel):
    total_requests: int
    completed: int
    pending: int
    in_progress: int
    failed: int
    earliest_request: str | None
    latest_request: str | None


class RetentionCompliance(BaseModel):
    record_count: int
    retention_days: int
    compliant: bool


class RetentionComplianceResponse(BaseModel):
    applications: RetentionCompliance
    application_events: RetentionCompliance
    analytics_events: RetentionCompliance


class ProcessingActivity(BaseModel):
    id: str
    name: str
    purpose: str
    data_categories: list[str]
    legal_basis: str
    retention_period: str
    recipients: list[str]


class ComplianceEvent(BaseModel):
    id: str
    type: str
    action: str
    details: str
    timestamp: str


class ComplianceOverviewResponse(BaseModel):
    consent_rates: dict[str, Any]
    data_volume: dict[str, Any]
    deletion_requests: dict[str, Any]
    retention_compliance: dict[str, Any]
    generated_at: str


class ConsentHistoryItem(BaseModel):
    date: str
    consent_type: str
    opted_in: int
    opted_out: int


class ConsentReportResponse(BaseModel):
    consent_rates: dict[str, Any]
    consent_history: list[ConsentHistoryItem]


class DataProcessingResponse(BaseModel):
    activities: list[ProcessingActivity]


class AuditLogEntry(BaseModel):
    id: str
    type: str
    action: str
    details: str
    timestamp: str


class AuditLogResponse(BaseModel):
    events: list[AuditLogEntry]
    total: int


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


async def get_overview(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> ComplianceOverviewResponse:
    """Get compliance dashboard overview.

    Returns consent rates, data volume, deletion requests,
    and retention compliance status.
    """
    async with db.acquire() as conn:
        consent_rates = await compliance_tracker.get_consent_rates(conn)
        data_volume = await compliance_tracker.get_data_volume_metrics(conn)
        deletion_requests = await compliance_tracker.get_deletion_requests(conn)
        retention_compliance = await compliance_tracker.get_data_retention_compliance(conn)

    return ComplianceOverviewResponse(
        consent_rates=consent_rates,
        data_volume=data_volume,
        deletion_requests=deletion_requests,
        retention_compliance=retention_compliance,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


async def get_consent_report(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
    consent_type: str | None = Query(
        None,
        description="Filter by consent type (marketing, analytics, cookies, functional, essential)",
    ),
    days: int = Query(30, description="Number of days to look back"),
) -> ConsentReportResponse:
    """Get detailed consent report.

    Includes current consent rates and historical consent data
    filtered by type and time period.
    """
    if days > 365:
        raise HTTPException(status_code=400, detail="Maximum 365 days allowed")

    async with db.acquire() as conn:
        consent_rates = await compliance_tracker.get_consent_rates(conn)
        consent_history = await compliance_tracker.get_consent_history(
            conn,
            consent_type=consent_type,
            days=days,
        )

    return ConsentReportResponse(
        consent_rates=consent_rates,
        consent_history=[ConsentHistoryItem(**item) for item in consent_history],
    )


async def get_data_processing(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> DataProcessingResponse:
    """Get list of data processing activities.

    Returns GDPR Article 30 compliant records of processing activities.
    """
    async with db.acquire() as conn:
        activities = await compliance_tracker.get_data_processing_activities(conn)

    return DataProcessingResponse(
        activities=[ProcessingActivity(**activity) for activity in activities],
    )


async def get_export(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
    format: str = Query("json", description="Export format: json or csv"),
    start_date: str | None = Query(
        None,
        description="Start date for report period (ISO format)",
    ),
    end_date: str | None = Query(
        None,
        description="End date for report period (ISO format)",
    ),
) -> dict[str, Any]:
    """Generate and export compliance report.

    Returns a comprehensive compliance report that can be used
    for GDPR Article 30 audits. Supports JSON and CSV export formats.
    """
    # Parse dates if provided
    parsed_start = None
    parsed_end = None

    if start_date:
        try:
            parsed_start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use ISO format (e.g., 2024-01-01)",
            )

    if end_date:
        try:
            parsed_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use ISO format (e.g., 2024-12-31)",
            )

    async with db.acquire() as conn:
        report = await compliance_tracker.generate_compliance_report(
            conn,
            start_date=parsed_start,
            end_date=parsed_end,
        )

    if format == "csv":
        # Convert to CSV format
        output = io.StringIO()

        # Consent rates
        output.write("Section: Consent Rates\n")
        output.write("Type,Opted In,Opted Out,Total,Rate (%)\n")
        for consent_type, data in report["consent_rates"].items():
            output.write(
                f"{consent_type},{data['opted_in']},{data['opted_out']},"
                f"{data['total']},{data['rate']}\n"
            )

        # Data processing activities
        output.write("\nSection: Data Processing Activities\n")
        output.write("ID,Name,Purpose,Data Categories,Legal Basis,Retention,Recipients\n")
        for activity in report["processing_activities"]:
            output.write(
                f"{activity['id']},{activity['name']},{activity['purpose']},"
                f"{';'.join(activity['data_categories'])},{activity['legal_basis']},"
                f"{activity['retention_period']},{';'.join(activity['recipients'])}\n"
            )

        # Deletion requests
        output.write("\nSection: Deletion Requests\n")
        dr = report["deletion_requests"]
        output.write(f"Total,{dr['total_requests']}\n")
        output.write(f"Completed,{dr['completed']}\n")
        output.write(f"Pending,{dr['pending']}\n")
        output.write(f"In Progress,{dr['in_progress']}\n")
        output.write(f"Failed,{dr['failed']}\n")

        csv_content = output.getvalue()
        return {
            "format": "csv",
            "content": csv_content,
            "filename": f"compliance_report_{datetime.now().strftime('%Y%m%d')}.csv",
        }

    # Default to JSON
    return {
        "format": "json",
        "content": report,
        "filename": f"compliance_report_{datetime.now().strftime('%Y%m%d')}.json",
    }


async def get_audit_log(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of events"),
    event_type: str | None = Query(
        None,
        description="Filter by event type (consent, deletion)",
    ),
    offset: int = Query(0, description="Pagination offset"),
) -> AuditLogResponse:
    """Get compliance audit log.

    Returns searchable audit trail for compliance events including
    consent changes and data deletion requests.
    """
    if days > 365:
        raise HTTPException(status_code=400, detail="Maximum 365 days allowed")
    if limit > 500:
        raise HTTPException(status_code=400, detail="Maximum 500 events per request")

    async with db.acquire() as conn:
        events = await compliance_tracker.get_compliance_events(
            conn,
            days=days,
            limit=limit + offset,
        )

    # Filter by event type if specified
    if event_type:
        events = [e for e in events if e["type"] == event_type]

    # Paginate
    total = len(events)
    paginated_events = events[offset : offset + limit]

    return AuditLogResponse(
        events=[AuditLogEntry(**event) for event in paginated_events],
        total=total,
    )
