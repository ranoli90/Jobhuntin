"""
Document Tracking API Endpoints for Phase 12.1 Agent Improvements
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from packages.backend.domain.agent_improvements import (
    AgentImprovementsManager,
    create_agent_improvements_manager,
)
from packages.backend.domain.tenant import TenantContext
from apps.api.dependencies import get_pool

router = APIRouter(prefix="/document-tracking", tags=["document-tracking"])


# Pydantic models
class DocumentTypeRequest(BaseModel):
    """Document type request."""

    file_name: str = Field(..., description="File name")
    content_type: str = Field(..., description="Content type")
    file_size: int = Field(..., description="File size in bytes")
    content_preview: Optional[str] = Field(None, description="Content preview")


class DocumentTypeResponse(BaseModel):
    """Document type response."""

    tracking_id: str
    file_name: str
    content_type: str
    file_size: int
    document_type: str
    confidence_score: float
    content_preview: Optional[str]
    metadata: Dict[str, Any]
    created_at: str


class DocumentListResponse(BaseModel):
    """Document list response."""

    documents: List[DocumentTypeResponse]
    total: int
    page: int
    per_page: int


# Dependency injection functions
def get_agent_improvements_manager():
    """Get agent improvements manager instance."""
    return create_agent_improvements_manager(get_pool())


@router.post("/track")
async def track_document_type(
    request: DocumentTypeRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> DocumentTypeResponse:
    """Track document type."""
    try:
        tracking = await manager.track_document_type(
            file_name=request.file_name,
            content_type=request.content_type,
            file_size=request.file_size,
            content_preview=request.content_preview,
        )

        return DocumentTypeResponse(
            tracking_id=tracking.tracking_id,
            file_name=tracking.file_name,
            content_type=tracking.content_type,
            file_size=tracking.file_size,
            document_type=tracking.document_type,
            confidence_score=tracking.confidence_score,
            content_preview=tracking.content_preview,
            metadata=tracking.metadata,
            created_at=tracking.created_at.isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track document type: {str(e)}"
        )


@router.get("/list")
async def list_tracked_documents(
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> DocumentListResponse:
    """List tracked documents."""
    try:
        documents = await manager.get_tracked_documents(
            document_type=document_type,
            limit=per_page,
            offset=(page - 1) * per_page,
        )

        return DocumentListResponse(
            documents=[
                DocumentTypeResponse(
                    tracking_id=d.tracking_id,
                    file_name=d.file_name,
                    content_type=d.content_type,
                    file_size=d.file_size,
                    document_type=d.document_type,
                    confidence_score=d.confidence_score,
                    content_preview=d.content_preview,
                    metadata=d.metadata,
                    created_at=d.created_at.isoformat(),
                )
                for d in documents
            ],
            total=len(documents),
            page=page,
            per_page=per_page,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{tracking_id}")
async def get_tracked_document(
    tracking_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> DocumentTypeResponse:
    """Get a tracked document."""
    try:
        document = await manager.get_tracked_document(tracking_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentTypeResponse(
            tracking_id=document.tracking_id,
            file_name=document.file_name,
            content_type=document.content_type,
            file_size=document.file_size,
            document_type=document.document_type,
            confidence_score=document.confidence_score,
            content_preview=document.content_preview,
            metadata=document.metadata,
            created_at=document.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.get("/types")
async def get_supported_document_types() -> Dict[str, Any]:
    """Get supported document types."""
    try:
        document_types = [
            {
                "type": "pdf",
                "name": "PDF Document",
                "description": "Portable Document Format",
                "mime_types": ["application/pdf"],
                "extensions": [".pdf"],
                "supported": True,
            },
            {
                "type": "docx",
                "name": "Word Document",
                "description": "Microsoft Word Document",
                "mime_types": [
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ],
                "extensions": [".docx"],
                "supported": True,
            },
            {
                "type": "doc",
                "name": "Legacy Word Document",
                "description": "Microsoft Word 97-2003 Document",
                "mime_types": ["application/msword"],
                "extensions": [".doc"],
                "supported": True,
            },
            {
                "type": "txt",
                "name": "Text Document",
                "description": "Plain Text Document",
                "mime_types": ["text/plain"],
                "extensions": [".txt"],
                "supported": True,
            },
            {
                "type": "rtf",
                "name": "Rich Text Format",
                "description": "Rich Text Format Document",
                "mime_types": ["application/rtf"],
                "extensions": [".rtf"],
                "supported": True,
            },
            {
                "type": "jpeg",
                "name": "JPEG Image",
                "description": "JPEG Image File",
                "mime_types": ["image/jpeg"],
                "extensions": [".jpg", ".jpeg"],
                "supported": True,
            },
            {
                "type": "png",
                "name": "PNG Image",
                "description": "PNG Image File",
                "mime_types": ["image/png"],
                "extensions": [".png"],
                "supported": True,
            },
            {
                "type": "tiff",
                "name": "TIFF Image",
                "description": "TIFF Image File",
                "mime_types": ["image/tiff"],
                "extensions": [".tiff", ".tif"],
                "supported": True,
            },
            {
                "type": "bmp",
                "name": "BMP Image",
                "description": "BMP Image File",
                "mime_types": ["image/bmp"],
                "extensions": [".bmp"],
                "supported": True,
            },
        ]

        return {
            "document_types": document_types,
            "total": len(document_types),
            "message": "Supported document types retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get document types: {str(e)}"
        )


@router.get("/stats")
async def get_document_tracking_stats(
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, Any]:
    """Get document tracking statistics."""
    try:
        stats = await manager.get_document_tracking_stats()

        return {
            "stats": stats,
            "message": "Document tracking statistics retrieved successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/{tracking_id}")
async def delete_tracked_document(
    tracking_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, str]:
    """Delete a tracked document."""
    try:
        success = await manager.delete_tracked_document(tracking_id)

        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "tracking_id": tracking_id,
            "message": "Document deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/batch-track")
async def batch_track_documents(
    documents: List[DocumentTypeRequest],
    ctx: TenantContext = Depends(get_tenant_context),
    manager: AgentImprovementsManager = Depends(get_agent_improvements_manager),
) -> Dict[str, Any]:
    """Batch track multiple documents."""
    try:
        results = []

        for doc in documents:
            try:
                tracking = await manager.track_document_type(
                    file_name=doc.file_name,
                    content_type=doc.content_type,
                    file_size=doc.file_size,
                    content_preview=doc.content_preview,
                )
                results.append(
                    {
                        "success": True,
                        "tracking_id": tracking.tracking_id,
                        "document_type": tracking.document_type,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "success": False,
                        "error": str(e),
                        "file_name": doc.file_name,
                    }
                )

        successful = sum(1 for r in results if r["success"])

        return {
            "results": results,
            "total": len(documents),
            "successful": successful,
            "failed": len(documents) - successful,
            "message": f"Batch tracking completed: {successful}/{len(documents)} successful",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to batch track documents: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for document tracking system."""
    return {
        "status": "healthy",
        "service": "document_tracking",
        "features": [
            "document_type_detection",
            "confidence_scoring",
            "metadata_extraction",
            "batch_tracking",
        ],
    }
