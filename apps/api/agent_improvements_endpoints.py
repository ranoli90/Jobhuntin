"""
Phase 12.1 Agent Improvements API endpoints.
Enhanced button detection, OAuth/SSO handling, document types, concurrent usage tracking, DLQ management, screenshot capture.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from packages.backend.domain.agent_improvements import (
    AgentImprovementsManager,
    ButtonDetection,
    ConcurrentUsageSession,
    DLQItem,
    DocumentType,
    FormFieldDetection,
    OAuthCredentials,
    OAuthProvider,
    RetryResult,
    ScreenshotCapture,
)
from packages.backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.agent_improvements_api")

router = APIRouter(prefix="/agent-improvements", tags=["agent_improvements"])


async def get_tenant_context() -> TenantContext:
    raise NotImplementedError("Tenant context dependency not injected")


async def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


def get_agent_improvements_manager():
    raise NotImplementedError("Agent improvements manager dependency not injected")


# Pydantic models for API requests/responses


class ButtonDetectionRequest(BaseModel):
    page_source: str
    screenshot_data: Optional[str] = None  # Base64 encoded
    context: Optional[Dict[str, Any]] = None
    detection_strategies: List[str] = ["text", "attributes", "visual", "ml"]


class FormFieldDetectionRequest(BaseModel):
    page_source: str
    form_context: Optional[Dict[str, Any]] = None
    detection_strategies: List[str] = ["html", "custom", "dynamic"]


class OAuthFlowRequest(BaseModel):
    provider: OAuthProvider
    redirect_url: str
    context: Optional[Dict[str, Any]] = None


class ScreenshotCaptureRequest(BaseModel):
    application_id: str
    step_number: int
    step_description: str
    page_context: Optional[Dict[str, Any]] = None
    full_page: bool = False
    highlight_elements: Optional[List[str]] = None


class ConcurrentUsageSessionRequest(BaseModel):
    application_id: Optional[str] = None
    total_steps: int = 0


class DLQAddRequest(BaseModel):
    application_id: str
    failure_reason: str
    error_details: Dict[str, Any]
    payload: Dict[str, Any]
    max_retries: int = 3
    priority: int = 0


class RetryRequest(BaseModel):
    item_ids: List[str]
    force: bool = False


class BulkDeleteRequest(BaseModel):
    tenant_id: Optional[str] = None
    failure_reason: Optional[str] = None
    older_than_days: int = 7


# Button detection endpoints


@router.post("/detect-buttons")
async def detect_buttons(
    request: ButtonDetectionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> List[ButtonDetection]:
    """Detect buttons in a web page using multiple strategies."""
    try:
        # Decode screenshot data if provided
        screenshot_bytes = None
        if request.screenshot_data:
            import base64

            screenshot_bytes = base64.b64decode(request.screenshot_data)

        buttons = await agent_manager.detect_buttons(
            page_source=request.page_source,
            screenshot_data=screenshot_bytes,
            context=request.context,
        )

        # Store detection results for analytics
        await agent_manager._store_button_detection_results(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            buttons=buttons,
            detection_strategies=request.detection_strategies,
        )

        return buttons
    except Exception as e:
        logger.error("Failed to detect buttons: %s", e)
        raise HTTPException(status_code=500, detail="Failed to detect buttons")


# Form field detection endpoints


@router.post("/detect-form-fields")
async def detect_form_fields(
    request: FormFieldDetectionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> List[FormFieldDetection]:
    """Detect form fields in a web page."""
    try:
        fields = await agent_manager.detect_form_fields(
            page_source=request.page_source,
            form_context=request.form_context,
        )

        # Store detection results for analytics
        await agent_manager._store_form_field_detection_results(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            fields=fields,
        )

        return fields
    except Exception as e:
        logger.error("Failed to detect form fields: %s", e)
        raise HTTPException(status_code=500, detail="Failed to detect form fields")


# OAuth/SSO handling endpoints


@router.post("/oauth/start-flow")
async def start_oauth_flow(
    request: OAuthFlowRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, Any]:
    """Start OAuth/SSO flow for external service integration."""
    try:
        result = await agent_manager.handle_oauth_flow(
            provider=request.provider,
            redirect_url=request.redirect_url,
            tenant_id=ctx.tenant_id,
            context=request.context,
        )

        return result
    except Exception as e:
        logger.error("Failed to start OAuth flow: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start OAuth flow")


@router.get("/oauth/providers")
async def get_oauth_providers() -> Dict[str, Any]:
    """Get list of supported OAuth providers."""
    return {
        "providers": [
            {
                "provider": provider.value,
                "name": provider.value.title(),
                "description": f"OAuth integration with {provider.value.title()}",
            }
            for provider in OAuthProvider
        ]
    }


@router.get("/oauth/{tenant_id}/credentials")
async def get_oauth_credentials(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
    pool=Depends(_get_pool),
) -> List[OAuthCredentials]:
    """Get OAuth credentials for a tenant (admin only)."""
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from backend.domain.tenant import TenantScopeError, require_system_admin

    async with pool.acquire() as conn:
        try:
            await require_system_admin(conn, ctx.user_id)
        except TenantScopeError:
            if ctx.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this tenant"
                )

    try:
        credentials = await agent_manager._get_tenant_oauth_credentials(tenant_id)
        return credentials
    except Exception as e:
        logger.error("Failed to get OAuth credentials: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve OAuth credentials"
        )


# Screenshot capture endpoints


@router.post("/capture-screenshot")
async def capture_screenshot(
    request: ScreenshotCaptureRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
    pool=Depends(_get_pool),
) -> ScreenshotCapture:
    """Capture screenshot with metadata."""
    await _verify_application_ownership(
        request.application_id, ctx.tenant_id, ctx.user_id, pool
    )
    try:
        screenshot = await agent_manager.capture_screenshot(
            application_id=request.application_id,
            step_number=request.step_number,
            step_description=request.step_description,
            page_context=request.page_context,
            full_page=request.full_page,
            highlight_elements=request.highlight_elements,
        )

        return screenshot
    except Exception as e:
        logger.error("Failed to capture screenshot: %s", e)
        raise HTTPException(status_code=500, detail="Failed to capture screenshot")


async def _verify_application_ownership(
    application_id: str,
    tenant_id: str,
    user_id: str,
    pool,
) -> None:
    """Raise 404 if application does not belong to tenant/user (IDOR prevention)."""
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM public.applications WHERE id = $1 AND "
                "(tenant_id = $2 OR (tenant_id IS NULL AND user_id = $3))",
                application_id,
                tenant_id,
                user_id,
            )
            if not row:
                raise HTTPException(status_code=404, detail="Application not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to verify application ownership: %s", e)
        raise HTTPException(status_code=500, detail="Failed to verify application")


@router.get("/screenshots/{application_id}")
async def get_application_screenshots(
    application_id: str,
    limit: int = Query(50, ge=1, le=1000),
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
    pool=Depends(_get_pool),
) -> List[ScreenshotCapture]:
    """Get all screenshots for an application."""
    await _verify_application_ownership(
        application_id, ctx.tenant_id, ctx.user_id, pool
    )
    try:
        screenshots = await agent_manager._get_application_screenshots(
            application_id=application_id,
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            limit=limit,
        )

        return screenshots
    except Exception as e:
        logger.error("Failed to get screenshots: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve screenshots")


# Concurrent usage tracking endpoints


@router.post("/track-concurrent-usage")
async def track_concurrent_usage(
    request: ConcurrentUsageSessionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> ConcurrentUsageSession:
    """Start tracking a concurrent usage session."""
    try:
        session_data = {
            "user_id": ctx.user_id,
            "tenant_id": ctx.tenant_id,
            "application_id": request.application_id,
            "total_steps": request.total_steps,
        }

        session = await agent_manager.track_concurrent_usage(session_data)

        return session
    except Exception as e:
        logger.error("Failed to track concurrent usage: %s", e)
        raise HTTPException(status_code=500, detail="Failed to track concurrent usage")


@router.get("/concurrent-usage/sessions")
async def get_concurrent_usage_sessions(
    limit: int = Query(50, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> List[ConcurrentUsageSession]:
    """Get concurrent usage sessions."""
    try:
        sessions = await agent_manager._get_concurrent_usage_sessions(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            limit=limit,
            status=status,
        )

        return sessions
    except Exception as e:
        logger.error("Failed to get concurrent usage sessions: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve concurrent usage sessions"
        )


@router.put("/concurrent-usage/sessions/{session_id}")
async def update_concurrent_usage_session(
    session_id: str,
    status: Optional[str] = None,
    steps_completed: Optional[int] = None,
    error_count: Optional[int] = None,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, Any]:
    """Update a concurrent usage session."""
    try:
        success = await agent_manager._update_concurrent_session(
            session_id=session_id,
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            status=status,
            steps_completed=steps_completed,
            error_count=error_count,
        )

        return {"success": success}
    except Exception as e:
        logger.error("Failed to update concurrent usage session: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to update concurrent usage session"
        )


# DLQ management endpoints


@router.post("/dlq/add")
async def add_to_dlq(
    request: DLQAddRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> DLQItem:
    """Add failed application to Dead Letter Queue."""
    try:
        dlq_item = await agent_manager.add_to_dlq(
            application_id=request.application_id,
            tenant_id=ctx.tenant_id,
            failure_reason=request.failure_reason,
            error_details=request.error_details,
            payload=request.payload,
            max_retries=request.max_retries,
            priority=request.priority,
        )

        return dlq_item
    except Exception as e:
        logger.error("Failed to add to DLQ: %s", e)
        raise HTTPException(status_code=500, detail="Failed to add to DLQ")


@router.get("/dlq/items")
async def get_dlq_items(
    limit: int = Query(50, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, description="Filter by priority"),
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> List[DLQItem]:
    """Get DLQ items for the user's tenant."""
    try:
        items = await agent_manager._get_dlq_items(
            tenant_id=ctx.tenant_id,
            limit=limit,
            status=status,
            priority=priority,
        )

        return items
    except Exception as e:
        logger.error("Failed to get DLQ items: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve DLQ items")


@router.post("/dlq/retry/{item_id}")
async def retry_dlq_item(
    item_id: str,
    force: bool = Query(False, description="Force retry even if max retries exceeded"),
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> RetryResult:
    """Retry a DLQ item."""
    try:
        result = await agent_manager.retry_dlq_item(
            dlq_item_id=item_id,
            force_retry=force,
        )

        return result
    except Exception as e:
        logger.error("Failed to retry DLQ item: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retry DLQ item")


@router.post("/dlq/bulk-retry")
async def bulk_retry_dlq_items(
    request: RetryRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> List[RetryResult]:
    """Bulk retry multiple DLQ items."""
    try:
        results = []
        for item_id in request.item_ids:
            result = await agent_manager.retry_dlq_item(
                dlq_item_id=item_id,
                force_retry=request.force,
            )
            results.append(result)

        return results
    except Exception as e:
        logger.error("Failed to bulk retry DLQ items: %s", e)
        raise HTTPException(status_code=500, detail="Failed to bulk retry DLQ items")


@router.delete("/dlq/items/{item_id}")
async def delete_dlq_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, str]:
    """Delete a DLQ item."""
    try:
        success = await agent_manager._remove_dlq_item(item_id)

        if success:
            return {"message": "DLQ item deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="DLQ item not found")
    except Exception as e:
        logger.error("Failed to delete DLQ item: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete DLQ item")


# Document type tracking endpoints


@router.post("/track-document")
async def track_document_type(
    application_id: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    document_type: DocumentType,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
    pool=Depends(_get_pool),
) -> Dict[str, Any]:
    """Track document type for uploaded files."""
    await _verify_application_ownership(
        application_id, ctx.tenant_id, ctx.user_id, pool
    )
    try:
        tracking_id = await agent_manager._track_document_type(
            application_id=application_id,
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            document_type=document_type,
        )

        return {"tracking_id": tracking_id, "status": "tracked"}
    except Exception as e:
        logger.error("Failed to track document type: %s", e)
        raise HTTPException(status_code=500, detail="Failed to track document type")


@router.get("/document-tracking/{application_id}")
async def get_document_tracking(
    application_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
    pool=Depends(_get_pool),
) -> List[Dict[str, Any]]:
    """Get document tracking for an application."""
    await _verify_application_ownership(
        application_id, ctx.tenant_id, ctx.user_id, pool
    )
    try:
        tracking = await agent_manager._get_document_tracking(
            application_id=application_id,
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
        )

        return tracking
    except Exception as e:
        logger.error("Failed to get document tracking: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve document tracking"
        )


# Performance metrics endpoints


@router.get("/performance-metrics/{application_id}")
async def get_performance_metrics(
    application_id: str,
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    limit: int = Query(100, ge=1, le=1000),
    ctx: TenantContext = Depends(get_tenant_context),
    agent_manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
    pool=Depends(_get_pool),
) -> List[Dict[str, Any]]:
    """Get performance metrics for an application."""
    await _verify_application_ownership(
        application_id, ctx.tenant_id, ctx.user_id, pool
    )
    try:
        metrics = await agent_manager._get_performance_metrics(
            application_id=application_id,
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            metric_type=metric_type,
            limit=limit,
        )

        return metrics
    except Exception as e:
        logger.error("Failed to get performance metrics: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve performance metrics"
        )


# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for agent improvements system."""
    return {
        "status": "healthy",
        "service": "agent_improvements",
        "features": [
            "button_detection",
            "form_field_detection",
            "oauth_handling",
            "screenshot_capture",
            "concurrent_usage_tracking",
            "dlq_management",
            "document_type_tracking",
            "performance_metrics",
        ],
    }
