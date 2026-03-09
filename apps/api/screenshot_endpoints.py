"""
Screenshot Capture API Endpoints for Phase 12.1 Agent Improvements
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.dependencies import get_pool
from packages.backend.domain.agent_improvements import (
    AgentImprovementsManager,
    create_agent_improvements_manager,
)
from packages.backend.domain.tenant import TenantContext

router = APIRouter(prefix="/screenshots", tags=["screenshots"])


async def get_tenant_context() -> TenantContext:
    """Stub; inject tenant context via Depends in main app."""
    raise NotImplementedError("Tenant context dependency not injected")


# Pydantic models
class ScreenshotCaptureRequest(BaseModel):
    """Screenshot capture request."""

    application_id: str = Field(..., description="Application ID")
    step_number: int = Field(..., description="Step number")
    step_description: str = Field(..., description="Step description")
    viewport: Optional[Dict[str, int]] = Field(None, description="Viewport size")
    full_page: bool = Field(default=False, description="Capture full page")
    highlight_elements: List[str] = Field(
        default=[], description="Elements to highlight"
    )


class ScreenshotResponse(BaseModel):
    """Screenshot capture response."""

    capture_id: str
    application_id: str
    step_number: int
    step_description: str
    screenshot_path: str
    thumbnail_path: str
    viewport_size: Dict[str, int]
    full_page: bool
    elements_highlighted: List[str]
    error_detected: bool
    error_message: Optional[str]
    created_at: str


class ScreenshotListResponse(BaseModel):
    """Screenshot list response."""

    screenshots: List[ScreenshotResponse]
    total: int
    page: int
    per_page: int


# Dependency injection functions
def get_agent_improvements_manager():
    """Get agent improvements manager instance."""
    return create_agent_improvements_manager(get_pool())


@router.post("/capture")
async def capture_screenshot(
    request: ScreenshotCaptureRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> ScreenshotResponse:
    """Capture a screenshot."""
    try:
        capture = await manager.capture_screenshot(
            application_id=request.application_id,
            step_number=request.step_number,
            step_description=request.step_description,
            page_context={
                "viewport": request.viewport or {"width": 1920, "height": 1080},
            },
            full_page=request.full_page,
            highlight_elements=request.highlight_elements,
        )

        return ScreenshotResponse(
            capture_id=capture.capture_id,
            application_id=capture.application_id,
            step_number=capture.step_number,
            step_description=capture.step_description,
            screenshot_path=capture.screenshot_path,
            thumbnail_path=capture.thumbnail_path or "",
            viewport_size=capture.viewport_size,
            full_page=capture.full_page,
            elements_highlighted=capture.elements_highlighted,
            error_detected=capture.error_detected,
            error_message=capture.error_message,
            created_at=capture.created_at.isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to capture screenshot: {str(e)}"
        )


@router.get("/list")
async def list_screenshots(
    application_id: str = Query(..., description="Application ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> ScreenshotListResponse:
    """List screenshots for an application."""
    try:
        screenshots = await manager.get_screenshots_for_application(
            application_id=application_id,
            limit=per_page,
            offset=(page - 1) * per_page,
        )

        return ScreenshotListResponse(
            screenshots=[
                ScreenshotResponse(
                    capture_id=s.capture_id,
                    application_id=s.application_id,
                    step_number=s.step_number,
                    step_description=s.step_description,
                    screenshot_path=s.screenshot_path,
                    thumbnail_path=s.thumbnail_path or "",
                    viewport_size=s.viewport_size,
                    full_page=s.full_page,
                    elements_highlighted=s.elements_highlighted,
                    error_detected=s.error_detected,
                    error_message=s.error_message,
                    created_at=s.created_at.isoformat(),
                )
                for s in screenshots
            ],
            total=len(screenshots),
            page=page,
            per_page=per_page,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list screenshots: {str(e)}"
        )


@router.get("/{capture_id}")
async def get_screenshot(
    capture_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> ScreenshotResponse:
    """Get a specific screenshot."""
    try:
        screenshot = await manager.get_screenshot(capture_id)

        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        return ScreenshotResponse(
            capture_id=screenshot.capture_id,
            application_id=screenshot.application_id,
            step_number=screenshot.step_number,
            step_description=screenshot.step_description,
            screenshot_path=screenshot.screenshot_path,
            thumbnail_path=screenshot.thumbnail_path or "",
            viewport_size=screenshot.viewport_size,
            full_page=screenshot.full_page,
            elements_highlighted=screenshot.elements_highlighted,
            error_detected=screenshot.error_detected,
            error_message=screenshot.error_message,
            created_at=screenshot.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get screenshot: {str(e)}"
        )


@router.post("/{capture_id}/download")
async def download_screenshot(
    capture_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, str]:
    """Download screenshot image."""
    try:
        screenshot = await manager.get_screenshot(capture_id)

        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        return {
            "download_url": f"/api/screenshots/{capture_id}/image",
            "filename": f"screenshot-{capture_id}.png",
            "content_type": "image/png",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download screenshot: {str(e)}"
        )


@router.get("/{capture_id}/image")
async def get_screenshot_image(
    capture_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> bytes:
    """Get screenshot image data."""
    try:
        screenshot = await manager.get_screenshot(capture_id)

        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # In a real implementation, this would return the actual image data
        # For now, we'll return a placeholder
        return b"PLACEHOLDER_IMAGE_DATA"

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get screenshot image: {str(e)}"
        )


@router.delete("/{capture_id}")
async def delete_screenshot(
    capture_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, str]:
    """Delete a screenshot."""
    try:
        success = await manager.delete_screenshot(capture_id)

        if not success:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        return {
            "capture_id": capture_id,
            "message": "Screenshot deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete screenshot: {str(e)}"
        )


@router.get("/stats")
async def get_screenshot_stats(
    application_id: Optional[str] = Query(None, description="Application ID"),
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, Any]:
    """Get screenshot statistics."""
    try:
        if application_id:
            stats = await manager.get_application_screenshot_stats(application_id)
        else:
            stats = await manager.get_screenshot_stats()

        return {
            "stats": stats,
            "message": "Screenshot statistics retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get screenshot stats: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for screenshot capture system."""
    return {
        "status": "healthy",
        "service": "screenshot_capture",
        "features": [
            "screenshot_capture",
            "thumbnail_generation",
            "element_highlighting",
            "error_detection",
        ],
    }
