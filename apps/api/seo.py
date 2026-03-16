"""SEO Engine API endpoints.

Provides REST API for SEO operations including progress tracking,
content management, metrics collection, health monitoring, competitor
intelligence, and logging.

Mounted via _mount_sub_routers() in api/main.py.
"""

from __future__ import annotations

from typing import Any, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from api.deps import get_pool as _get_pool, get_tenant_context as _get_tenant_ctx
from packages.backend.domain.seo_competitor import SEOCompetitorRepository
from packages.backend.domain.seo_content import SEOContentRepository, VALID_INTENTS
from packages.backend.domain.seo_health import SEOHealthCheck
from packages.backend.domain.seo_logging import SEOLogger
from packages.backend.domain.seo_metrics import SEOMetricsCollector
from packages.backend.domain.seo_progress import SEOProgressRepository
from shared.logging_config import get_logger

logger = get_logger("sorce.api.seo")

router = APIRouter(tags=["seo"])


# ===================================================================
# Part 1: SEO Progress Endpoints
# ===================================================================


class SEOProgressResponse(BaseModel):
    """SEO progress data response."""

    id: int
    service_id: str
    last_index: Optional[int] = None
    last_submission_at: Optional[str] = None
    daily_quota_used: int
    daily_quota_reset: Optional[str] = None
    created_at: str
    updated_at: str


class SEOProgressUpdate(BaseModel):
    """Request model for updating SEO progress."""

    last_index: Optional[int] = None
    daily_quota_used: Optional[int] = None


@router.get(
    "/api/v1/seo/progress/{service_id}",
    response_model=SEOProgressResponse,
)
async def get_seo_progress(
    service_id: str = Path(..., description="The service identifier"),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> SEOProgressResponse:
    """Get SEO progress for a specific service."""
    async with pool.acquire() as conn:
        repo = SEOProgressRepository(conn)
        progress = await repo.get_progress(service_id)

        if not progress:
            raise HTTPException(
                status_code=404,
                detail=f"No SEO progress found for service: {service_id}",
            )

        return SEOProgressResponse(**progress)


@router.put(
    "/api/v1/seo/progress/{service_id}",
    response_model=SEOProgressResponse,
)
async def update_seo_progress(
    service_id: str = Path(..., description="The service identifier"),
    data: SEOProgressUpdate = ...,
    pool: asyncpg.Pool = Depends(_get_pool),
) -> SEOProgressResponse:
    """Update SEO progress for a specific service."""
    async with pool.acquire() as conn:
        repo = SEOProgressRepository(conn)
        try:
            progress = await repo.update_progress(
                service_id=service_id,
                last_index=data.last_index,
                daily_quota_used=data.daily_quota_used,
            )
            return SEOProgressResponse(**progress)
        except Exception as e:
            logger.error(
                "Failed to update SEO progress",
                extra={"service_id": service_id, "error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update SEO progress: {str(e)}",
            )


@router.post("/api/v1/seo/quota/reset", response_model=SEOProgressResponse)
async def reset_seo_quota(
    service_id: str = Query(..., description="The service identifier"),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> SEOProgressResponse:
    """Reset daily quota for a specific service."""
    async with pool.acquire() as conn:
        repo = SEOProgressRepository(conn)
        try:
            progress = await repo.reset_daily_quota(service_id)
            logger.info(
                "Daily quota reset via API",
                extra={"service_id": service_id},
            )
            return SEOProgressResponse(**progress)
        except Exception as e:
            logger.error(
                "Failed to reset daily quota",
                extra={"service_id": service_id, "error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reset quota: {str(e)}",
            )


# ===================================================================
# Part 2: SEO Content Endpoints
# ===================================================================


class SEOContentResponse(BaseModel):
    """SEO generated content response."""

    id: int
    url: str
    title: str
    topic: str
    intent: str
    competitor: Optional[str] = None
    content_hash: str
    quality_score: Optional[float] = None
    google_indexed: bool
    indexed_at: Optional[str] = None
    clicks: Optional[int] = None
    impressions: Optional[int] = None
    ctr: Optional[float] = None
    position: Optional[float] = None
    last_updated: Optional[str] = None
    created_at: str
    updated_at: str


class SEOContentCreate(BaseModel):
    """Request model for recording new SEO content."""

    url: str = Field(..., description="The URL of the content")
    title: str = Field(..., description="The title of the content")
    topic: str = Field(..., description="The topic of the content")
    intent: str = Field(..., description="Search intent (informational, commercial, transactional, navigational)")
    content_hash: str = Field(..., description="Hash of content for deduplication")
    competitor: Optional[str] = Field(None, description="Optional competitor name")
    quality_score: Optional[float] = Field(None, description="Quality score (0-1)", ge=0, le=1)


class SEOContentListResponse(BaseModel):
    """Response for content list."""

    content: list[dict[str, Any]]
    count: int


@router.get("/api/v1/seo/content", response_model=SEOContentListResponse)
async def list_seo_content(
    topic: Optional[str] = Query(None, description="Filter by topic"),
    intent: Optional[str] = Query(None, description="Filter by intent type"),
    competitor: Optional[str] = Query(None, description="Filter by competitor"),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> SEOContentListResponse:
    """List generated SEO content with optional filters."""
    async with pool.acquire() as conn:
        repo = SEOContentRepository(conn)

        try:
            if topic and intent:
                # Use topic-intent query
                content = await repo.get_content_by_topic_intent(
                    topic=topic,
                    intent=intent,
                    competitor=competitor,
                    limit=limit,
                )
            elif topic:
                # Use topic query
                content = await repo.get_content_by_topic(topic, limit=limit)
            else:
                # Get all content (limited)
                rows = await conn.fetch(
                    """
                    SELECT id, url, title, topic, intent, competitor,
                           content_hash, quality_score, google_indexed,
                           indexed_at, clicks, impressions, ctr, position,
                           last_updated, deleted_at, created_at, updated_at
                    FROM seo_generated_content
                    WHERE deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT $1
                    """,
                    limit,
                )
                content = [repo._row_to_dict(row) for row in rows]

            return SEOContentListResponse(content=content, count=len(content))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(
                "Failed to list SEO content",
                extra={"error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list content: {str(e)}",
            )


@router.post("/api/v1/seo/content", response_model=SEOContentResponse)
async def create_seo_content(
    data: SEOContentCreate = ...,
    pool: asyncpg.Pool = Depends(_get_pool),
) -> SEOContentResponse:
    """Record newly generated SEO content."""
    async with pool.acquire() as conn:
        repo = SEOContentRepository(conn)

        try:
            content = await repo.record_generated_content(
                url=data.url,
                title=data.title,
                topic=data.topic,
                intent=data.intent,
                content_hash=data.content_hash,
                competitor=data.competitor,
                quality_score=data.quality_score,
            )
            return SEOContentResponse(**content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(
                "Failed to record SEO content",
                extra={"url": data.url, "error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to record content: {str(e)}",
            )


# ===================================================================
# Part 3: SEO Metrics Endpoints
# ===================================================================


class SEOMetricsResponse(BaseModel):
    """SEO metrics response."""

    id: int
    total_generated: Optional[int] = None
    total_submitted: Optional[int] = None
    success_rate: Optional[float] = None
    average_generation_time_ms: Optional[float] = None
    average_submission_time_ms: Optional[float] = None
    api_calls_today: Optional[int] = None
    quota_used_today: Optional[int] = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: str


@router.get("/api/v1/seo/metrics", response_model=list[SEOMetricsResponse])
async def get_seo_metrics(
    days: int = Query(30, description="Number of days to retrieve", ge=1, le=365),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> list[SEOMetricsResponse]:
    """Get SEO metrics for the specified number of days."""
    async with pool.acquire() as conn:
        collector = SEOMetricsCollector(conn)

        try:
            metrics = await collector.get_metrics(days=days)
            return [SEOMetricsResponse(**m) for m in metrics]
        except Exception as e:
            logger.error(
                "Failed to get SEO metrics",
                extra={"days": days, "error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get metrics: {str(e)}",
            )


# ===================================================================
# Part 4: SEO Health Check Endpoints
# ===================================================================


class SEOHealthResponse(BaseModel):
    """SEO health check response."""

    healthy: bool
    checks: dict[str, dict[str, Any]]
    overall_status: str
    recommendations: list[str] = Field(default_factory=list)


@router.get("/api/v1/seo/health", response_model=SEOHealthResponse)
async def get_seo_health(
    service_id: Optional[str] = Query(None, description="Optional service ID for quota check"),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> SEOHealthResponse:
    """Run SEO engine health checks."""
    async with pool.acquire() as conn:
        health_check = SEOHealthCheck(conn)

        try:
            result = await health_check.run_all_checks(service_id=service_id)
            return SEOHealthResponse(
                healthy=result.healthy,
                checks=result.checks,
                overall_status=result.overall_status,
                recommendations=result.recommendations,
            )
        except Exception as e:
            logger.error(
                "Failed to run SEO health check",
                extra={"error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to run health check: {str(e)}",
            )


# ===================================================================
# Part 5: SEO Competitor Endpoints
# ===================================================================


class SEOCompetitorResponse(BaseModel):
    """SEO competitor intelligence response."""

    id: int
    competitor_name: str
    search_volume: Optional[int] = None
    difficulty_score: Optional[int] = None
    intent: Optional[str] = None
    keywords: Optional[dict[str, Any]] = None
    content_gaps: Optional[list[str]] = None
    weaknesses: Optional[list[str]] = None
    last_updated: Optional[str] = None
    created_at: str


@router.get("/api/v1/seo/competitors", response_model=list[SEOCompetitorResponse])
async def list_seo_competitors(
    limit: int = Query(100, description="Maximum number of results", ge=1, le=500),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> list[SEOCompetitorResponse]:
    """List all SEO competitor intelligence entries."""
    async with pool.acquire() as conn:
        repo = SEOCompetitorRepository(conn)

        try:
            competitors = await repo.get_all_competitors(limit=limit)
            return [SEOCompetitorResponse(**c) for c in competitors]
        except Exception as e:
            logger.error(
                "Failed to list SEO competitors",
                extra={"error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list competitors: {str(e)}",
            )


# ===================================================================
# Part 6: SEO Logging Endpoints
# ===================================================================


class SEOLogResponse(BaseModel):
    """SEO log entry response."""

    id: int
    level: str
    message: str
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: str


@router.get("/api/v1/seo/logs", response_model=list[SEOLogResponse])
async def get_seo_logs(
    level: Optional[str] = Query(None, description="Filter by log level (debug, info, warn, error)"),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=1000),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> list[SEOLogResponse]:
    """Get recent SEO operation logs."""
    async with pool.acquire() as conn:
        logger_obj = SEOLogger(conn)

        try:
            logs = await logger_obj.get_recent_logs(level=level, limit=limit)
            return [SEOLogResponse(**log) for log in logs]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(
                "Failed to get SEO logs",
                extra={"level": level, "error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get logs: {str(e)}",
            )
