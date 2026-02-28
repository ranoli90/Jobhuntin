"""
Analytics sub-router — event sink, user feedback, agent performance,
experiment readout, and debug bundles.

Mounted via _mount_sub_routers() in api/main.py.
"""

from __future__ import annotations

import json
from datetime import UTC
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from shared.logging_config import get_logger

from backend.domain.analytics_events import ALL_EVENT_TYPES
from backend.domain.eval_queries import get_agent_performance_summary
from backend.domain.evaluations import record_user_feedback
from backend.domain.experiment_readout import get_experiment_results
from backend.domain.m1_metrics import get_m1_dashboard, refresh_dashboard_views
from backend.domain.m2_metrics import get_m2_dashboard, refresh_m2_views
from backend.domain.m3_metrics import get_m3_dashboard, refresh_m3_views
from backend.domain.m4_metrics import get_m4_dashboard, refresh_m4_views
from shared.metrics import incr

logger = get_logger("sorce.api.analytics")

router = APIRouter(tags=["analytics"])

# ---------------------------------------------------------------------------
# Dependency stubs — injected by api/main.py at mount time
# ---------------------------------------------------------------------------

def _get_pool() -> asyncpg.Pool:
    return (_ for _ in ()).throw(  # type: ignore[return-value]
    RuntimeError("analytics._get_pool not wired")
)
def _get_tenant_ctx() -> Any:
    return (_ for _ in ()).throw(
    RuntimeError("analytics._get_tenant_ctx not wired")
)
def _get_admin_user_id() -> Any:
    return (_ for _ in ()).throw(
    RuntimeError("analytics._get_admin_user_id not wired")
)


# ===================================================================
# Part 1: Event Sink — POST /analytics/events
# ===================================================================

class AnalyticsEventIn(BaseModel):
    """Incoming analytics event."""
    event_type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None
    created_at: str | None = None


class EventBatchRequest(BaseModel):
    events: list[AnalyticsEventIn] = Field(..., max_length=100)


class EventBatchResponse(BaseModel):
    """Response for event batch ingestion."""
    accepted: int
    rejected: int


@router.post("/analytics/events", response_model=EventBatchResponse)
async def ingest_events(
    body: EventBatchRequest,
    db: asyncpg.Pool = Depends(_get_pool),
) -> EventBatchResponse:
    """
    Batch-insert analytics events from the client.

    Validates event_type against the known taxonomy but still accepts
    unknown types (for forward compatibility) — they are just counted
    as 'rejected' in the response.
    """
    accepted = 0
    rejected = 0

    async with db.acquire() as conn:
        for evt in body.events:
            if evt.event_type not in ALL_EVENT_TYPES:
                rejected += 1
                continue
            await conn.execute(
                """
                INSERT INTO public.analytics_events
                    (tenant_id, user_id, session_id, event_type, properties, created_at)
                VALUES ($1, $2, $3, $4, $5::jsonb, COALESCE($6::timestamptz, now()))
                """,
                evt.tenant_id,
                evt.user_id,
                evt.session_id,
                evt.event_type,
                json.dumps(evt.properties),
                evt.created_at,
            )
            accepted += 1

    incr("analytics.events_ingested", value=accepted)
    if rejected:
        incr("analytics.events_rejected", value=rejected)

    return EventBatchResponse(accepted=accepted, rejected=rejected)


# ===================================================================
# Part 2: User Feedback — POST /applications/{id}/feedback
# ===================================================================

class FeedbackRequest(BaseModel):
    label: str = Field(..., pattern="^(SUCCESS|PARTIAL|FAILURE)$")
    comment: str | None = None


class FeedbackResponse(BaseModel):
    """Response for user feedback submission."""
    evaluation_id: str
    message: str


@router.post("/applications/{application_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    application_id: str = Path(...),
    body: FeedbackRequest = ...,
    ctx: Any = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> FeedbackResponse:
    """Record user feedback on an application's agent performance."""
    from shared.validators import validate_uuid
    validate_uuid(application_id, "application_id")
    async with db.acquire() as conn:
        # Verify the application belongs to this user/tenant
        app_row = await conn.fetchrow(
            """
            SELECT id, user_id, tenant_id FROM public.applications
            WHERE id = $1 AND user_id = $2
              AND tenant_id = $3
            """,
            application_id,
            ctx.user_id,
            ctx.tenant_id,
        )
        if app_row is None:
            raise HTTPException(status_code=404, detail="Application not found")

        eval_id = await record_user_feedback(
            conn,
            application_id=application_id,
            user_id=ctx.user_id,
            label=body.label,
            comment=body.comment,
            tenant_id=ctx.tenant_id,
        )

    incr("analytics.user_feedback", tags={"label": body.label})
    return FeedbackResponse(
        evaluation_id=eval_id,
        message="Feedback recorded. Thank you!",
    )


# ===================================================================
# Part 2: Agent Performance — GET /admin/agent-performance
# ===================================================================

@router.get("/admin/agent-performance")
async def agent_performance(
    tenant_id: str | None = Query(None),
    blueprint_key: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Return aggregated agent performance metrics (admin only)."""
    async with db.acquire() as conn:
        return await get_agent_performance_summary(
            conn,
            tenant_id=tenant_id,
            blueprint_key=blueprint_key,
            date_from=date_from,
            date_to=date_to,
        )


# ===================================================================
# Part 3: Experiment Readout — GET /admin/experiments/{key}/results
# ===================================================================

@router.get("/admin/experiments/{experiment_key}/results")
async def experiment_results(
    experiment_key: str = Path(...),
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Return per-variant performance stats for an experiment (admin only)."""
    async with db.acquire() as conn:
        results = await get_experiment_results(conn, experiment_key)
    if not results:
        raise HTTPException(status_code=404, detail="Experiment not found or no data")
    return {"experiment_key": experiment_key, "variants": results}


# ===================================================================
# Part 4: Debug Bundle — GET /admin/debug-bundle/{application_id}
# ===================================================================

@router.get("/admin/debug-bundle/{application_id}")
async def debug_bundle(
    application_id: str = Path(...),
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """
    Return a comprehensive debug bundle for a single application.

    Includes: application row, events, inputs, evaluations, analytics
    events for the user/session, and experiment assignments.
    PII is redacted via masking.py.
    """
    from shared.validators import validate_uuid
    validate_uuid(application_id, "application_id")
    from backend.domain.debug import build_debug_bundle
    async with db.acquire() as conn:
        bundle = await build_debug_bundle(conn, application_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="Application not found")
        return bundle


# ===================================================================
# Part 5: M1 Dashboard — GET /admin/m1-dashboard
# ===================================================================

@router.get("/admin/m1-dashboard")
async def m1_dashboard(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Return the M1 closed-beta monitoring dashboard payload."""
    async with db.acquire() as conn:
        return await get_m1_dashboard(conn)


@router.post("/admin/m1-dashboard/refresh")
async def m1_dashboard_refresh(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Refresh materialized views for the M1 dashboard."""
    async with db.acquire() as conn:
        await refresh_dashboard_views(conn)
    return {"status": "refreshed"}


# ===================================================================
# Part 6: M2 Dashboard — GET /admin/m2-dashboard
# ===================================================================

@router.get("/admin/m2-dashboard")
async def m2_dashboard(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Return the M2 open-beta dashboard (funnel + cohorts + referrals + sources)."""
    async with db.acquire() as conn:
        return await get_m2_dashboard(conn)


@router.post("/admin/m2-dashboard/refresh")
async def m2_dashboard_refresh(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Refresh all M1 + M2 materialized views."""
    async with db.acquire() as conn:
        await refresh_m2_views(conn)
    return {"status": "refreshed"}


# ===================================================================
# Part 7: M3 Dashboard — GET /admin/m3-dashboard
# ===================================================================

@router.get("/admin/m3-dashboard")
async def m3_dashboard(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Return the M3 team + vertical expansion dashboard."""
    async with db.acquire() as conn:
        return await get_m3_dashboard(conn)


@router.post("/admin/m3-dashboard/refresh")
async def m3_dashboard_refresh(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Refresh all M1 + M2 + M3 materialized views."""
    async with db.acquire() as conn:
        await refresh_m3_views(conn)
    return {"status": "refreshed"}


# ===================================================================
# Part 8: M4 Dashboard — GET /admin/m4-dashboard
# ===================================================================

@router.get("/admin/m4-dashboard")
async def m4_dashboard(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Return the M4 enterprise analytics dashboard (LTV:CAC, NRR, churn prediction, pipeline)."""
    async with db.acquire() as conn:
        return await get_m4_dashboard(conn)


@router.post("/admin/m4-dashboard/refresh")
async def m4_dashboard_refresh(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Refresh all M1–M4 materialized views."""
    async with db.acquire() as conn:
        await refresh_m4_views(conn)
    return {"status": "refreshed"}


# ===================================================================
# Part 9: Automated Alerts — GET /admin/alerts
# ===================================================================

@router.get("/admin/alerts")
async def get_alerts(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Run all automated alert checks and return triggered alerts."""
    from backend.domain.observability import run_all_alerts
    async with db.acquire() as conn:
        alerts = await run_all_alerts(conn)
    return {"alerts": alerts, "total": len(alerts)}


# ===================================================================
# Part 10: M5 Dashboard + Investor Metrics + Alerting v2
# ===================================================================

@router.get("/admin/m5-dashboard")
async def m5_dashboard(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Full M5 revenue intelligence dashboard (P&L, LTV:CAC, cohort retention, marketplace)."""
    from backend.domain.m5_metrics import get_m5_dashboard
    async with db.acquire() as conn:
        return await get_m5_dashboard(conn)


@router.post("/admin/m5-dashboard/refresh")
async def m5_dashboard_refresh(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Refresh all M1–M5 materialized views."""
    from backend.domain.m5_metrics import refresh_m5_views
    async with db.acquire() as conn:
        await refresh_m5_views(conn)
    return {"status": "refreshed"}


@router.get("/investors/metrics")
async def investor_metrics(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Series A metrics export — clean JSON for pitch deck."""
    from datetime import datetime

    from backend.domain.m5_metrics import get_investor_metrics
    async with db.acquire() as conn:
        data = await get_investor_metrics(conn)
        # Fill marketplace blueprint count
        bp_count = await conn.fetchval(
            "SELECT COUNT(*)::int FROM public.marketplace_blueprints WHERE approval_status = 'approved'"
        )
        data["product"]["marketplace_blueprints"] = bp_count or 0
    data["generated_at"] = datetime.now(UTC).isoformat()
    return data


@router.get("/investors/metrics.csv")
async def investor_metrics_csv(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> Any:
    """Series A metrics as CSV for spreadsheet/pitch deck import."""

    from backend.domain.m5_metrics import get_investor_metrics
    async with db.acquire() as conn:
        data = await get_investor_metrics(conn)

    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["MRR ($)", data["financials"]["mrr"]])
    writer.writerow(["ARR ($)", data["financials"]["arr"]])
    writer.writerow(["MRR Growth MoM (%)", data["financials"]["mrr_growth_mom_pct"]])
    writer.writerow(["Gross Margin (%)", data["financials"]["gross_margin_pct"]])
    writer.writerow(["Paying Subscribers", data["customers"]["paying_subscribers"]])
    writer.writerow(["PRO", data["customers"]["pro"]])
    writer.writerow(["TEAM", data["customers"]["team"]])
    writer.writerow(["ENTERPRISE", data["customers"]["enterprise"]])
    writer.writerow(["ARPU ($)", data["unit_economics"]["arpu"]])
    writer.writerow(["LTV ($)", data["unit_economics"]["ltv"]])
    writer.writerow(["CAC ($)", data["unit_economics"]["cac"]])
    writer.writerow(["LTV:CAC Ratio", data["unit_economics"]["ltv_cac_ratio"]])
    writer.writerow(["Monthly Churn (%)", data["unit_economics"]["monthly_churn_pct"]])
    writer.writerow(["Payback Months", data["unit_economics"]["payback_months"]])
    writer.writerow(["Agent Success Rate (%)", data["product"]["agent_success_rate_pct"]])

    from fastapi.responses import Response as FastAPIResponse
    return FastAPIResponse(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sorce_series_a_metrics.csv"},
    )


@router.post("/admin/alerting-cycle")
async def run_alerting_cycle_endpoint(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Run full alerting cycle: alerts + auto-rollback + experiment graduation + PagerDuty/Slack dispatch."""
    from backend.domain.alerting_v2 import run_alerting_cycle
    async with db.acquire() as conn:
        return await run_alerting_cycle(conn)


# ===================================================================
# Part 11: M6 Platform Dashboard + Investor Data Room + Renewals
# ===================================================================

@router.get("/admin/m6-platform")
async def m6_platform_dashboard(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Full M6 platform dashboard: ARR by vertical, API usage, integrators, staffing, university, marketplace."""
    from backend.domain.m6_metrics import get_m6_dashboard
    async with db.acquire() as conn:
        return await get_m6_dashboard(conn)


@router.post("/admin/m6-platform/refresh")
async def m6_platform_refresh(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Refresh all M1–M6 materialized views."""
    from backend.domain.m6_metrics import refresh_m6_views
    async with db.acquire() as conn:
        await refresh_m6_views(conn)
    return {"status": "refreshed"}


@router.get("/investors/full-metrics")
async def investor_full_metrics(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Complete Series A data room — comprehensive diligence package (JSON)."""
    from backend.domain.m6_metrics import get_full_investor_metrics
    async with db.acquire() as conn:
        return await get_full_investor_metrics(conn)


@router.get("/investors/full-metrics.csv")
async def investor_full_metrics_csv(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> Any:
    """Series A data room as CSV for spreadsheet import."""
    from backend.domain.m6_metrics import get_full_investor_metrics
    async with db.acquire() as conn:
        data = await get_full_investor_metrics(conn)

    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Section", "Metric", "Value"])
    fin = data.get("financials", {})
    for k, v in fin.items():
        w.writerow(["Financials", k, v])
    cust = data.get("customers", {})
    for k, v in cust.items():
        w.writerow(["Customers", k, v])
    ue = data.get("unit_economics", {})
    for k, v in ue.items():
        w.writerow(["Unit Economics", k, v])
    prod = data.get("product", {})
    for k, v in prod.items():
        w.writerow(["Product", k, v])
    plat = data.get("platform", {})
    for k, v in plat.items():
        w.writerow(["Platform", k, v])
    for vert in data.get("verticals", []):
        w.writerow(["Vertical", vert.get("vertical", ""), f"MRR={vert.get('mrr', 0)} ARR={vert.get('arr', 0)} tenants={vert.get('tenant_count', 0)}"])

    from fastapi.responses import Response as FastAPIResponse
    return FastAPIResponse(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sorce_series_a_data_room.csv"},
    )


@router.post("/admin/renewal-cycle")
async def run_renewal_cycle_endpoint(
    _admin: str = Depends(_get_admin_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Run contract renewal cycle: scan upcoming renewals + send 90/60/30-day notifications."""
    from backend.domain.renewals import run_renewal_cycle
    async with db.acquire() as conn:
        return await run_renewal_cycle(conn)
