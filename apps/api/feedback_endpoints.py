"""
Feedback Endpoints for Phase 14.1 User Experience
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from apps.api.dependencies import get_current_user, get_db_pool, get_tenant_id
from packages.backend.domain.feedback_manager import create_feedback_manager

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    """Feedback request model."""

    feedback_type: str
    rating: int
    category: str
    title: str
    message: str
    page_url: Optional[str] = None
    is_public: bool = False
    
    @field_validator('title', 'message')
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """MEDIUM: Sanitize HTML in user input to prevent XSS."""
        from packages.backend.domain.sanitization import sanitize_text_input
        return sanitize_text_input(v)


class NPSRequest(BaseModel):
    """NPS feedback request model."""

    score: int
    reason: Optional[str] = None


@router.post("/collect")
async def collect_feedback(
    feedback: FeedbackRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Collect user feedback."""
    try:
        # Validate rating
        if not 1 <= feedback.rating <= 5:
            raise HTTPException(
                status_code=400, detail="Rating must be between 1 and 5"
            )

        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Get session ID from user context
        session_id = current_user.get("session_id", str(current_user["id"]))

        # Collect feedback
        feedback_response = await feedback_manager.collect_feedback(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            feedback_type=feedback.feedback_type,
            rating=feedback.rating,
            category=feedback.category,
            title=feedback.title,
            message=feedback.message,
            page_url=feedback.page_url,
            session_id=session_id,
            is_public=feedback.is_public,
        )

        return {
            "success": True,
            "feedback_id": feedback_response.id,
            "sentiment_score": feedback_response.sentiment_score,
            "status": feedback_response.status,
            "created_at": feedback_response.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to collect feedback: {str(e)}"
        )


@router.post("/nps")
async def collect_nps_feedback(
    nps_request: NPSRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Collect Net Promoter Score feedback."""
    try:
        # Validate score
        if not 0 <= nps_request.score <= 10:
            raise HTTPException(
                status_code=400, detail="NPS score must be between 0 and 10"
            )

        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Collect NPS feedback
        nps_response = await feedback_manager.collect_nps_feedback(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            score=nps_request.score,
            reason=nps_request.reason,
        )

        return {
            "success": True,
            "nps_id": nps_response.id,
            "promoter_type": nps_response.promoter_type,
            "score": nps_response.score,
            "created_at": nps_response.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to collect NPS feedback: {str(e)}"
        )


@router.get("/summary")
async def get_feedback_summary(
    time_period_days: int = Query(default=30, ge=1, le=365),
    feedback_type: Optional[str] = None,
    category: Optional[str] = None,
    rating_min: Optional[int] = Query(None, ge=1, le=5),
    rating_max: Optional[int] = Query(None, ge=1, le=5),
    user_id: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get feedback summary with analytics."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Build rating range
        rating_range = None
        if rating_min is not None and rating_max is not None:
            rating_range = (rating_min, rating_max)

        # Get feedback summary
        summary = await feedback_manager.get_feedback_summary(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            feedback_type=feedback_type,
            category=category,
            rating_range=rating_range,
            user_id=user_id,
        )

        return summary

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get feedback summary: {str(e)}"
        )


@router.get("/trends")
async def analyze_feedback_trends(
    time_period_days: int = Query(default=30, ge=1, le=365),
    feedback_type: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Analyze feedback trends and patterns."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Analyze trends
        analysis = await feedback_manager.analyze_feedback_trends(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            feedback_type=feedback_type,
        )

        return {
            "analysis_id": analysis.id,
            "period_days": analysis.period_days,
            "total_responses": analysis.total_responses,
            "average_rating": analysis.average_rating,
            "sentiment_distribution": analysis.sentiment_distribution,
            "category_distribution": analysis.category_distribution,
            "nps_score": analysis.nps_score,
            "nps_distribution": analysis.nps_distribution,
            "key_themes": analysis.key_themes,
            "recommendations": analysis.recommendations,
            "created_at": analysis.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze feedback trends: {str(e)}"
        )


@router.get("/categories")
async def get_feedback_categories(
    active_only: bool = Query(default=True),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get feedback categories."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Get categories
        categories = await feedback_manager.get_feedback_categories(
            tenant_id=tenant_id,
            active_only=active_only,
        )

        return {
            "categories": [
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "is_active": category.is_active,
                    "created_at": category.created_at.isoformat(),
                    "updated_at": category.updated_at.isoformat(),
                }
                for category in categories
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get feedback categories: {str(e)}"
        )


@router.post("/categories")
async def create_feedback_category(
    name: str,
    description: str,
    is_active: bool = True,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Create a new feedback category."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Create category
        category = await feedback_manager.create_feedback_category(
            tenant_id=tenant_id,
            name=name,
            description=description,
            is_active=is_active,
        )

        return {
            "success": True,
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "is_active": category.is_active,
                "created_at": category.created_at.isoformat(),
                "updated_at": category.updated_at.isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create feedback category: {str(e)}"
        )


@router.put("/feedback/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    status: str,
    admin_notes: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Update feedback status."""
    try:
        # Validate status
        valid_statuses = ["pending", "reviewed", "resolved", "rejected"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}",
            )

        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Update status
        success = await feedback_manager.update_feedback_status(
            feedback_id=feedback_id,
            status=status,
            admin_notes=admin_notes,
        )

        return {
            "success": success,
            "feedback_id": feedback_id,
            "status": status,
            "admin_notes": admin_notes,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update feedback status: {str(e)}"
        )


@router.get("/feedback/{feedback_id}")
async def get_feedback_by_id(
    feedback_id: str,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get feedback by ID."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Get feedback
        feedback = await feedback_manager.get_feedback_by_id(feedback_id, tenant_id)

        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")

        return {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "tenant_id": feedback.tenant_id,
            "feedback_type": feedback.feedback_type,
            "rating": feedback.rating,
            "sentiment_score": feedback.sentiment_score,
            "category": feedback.category,
            "title": feedback.title,
            "message": feedback.message,
            "metadata": feedback.metadata,
            "page_url": feedback.page_url,
            "session_id": feedback.session_id,
            "is_public": feedback.is_public,
            "status": feedback.status,
            "admin_notes": feedback.admin_notes,
            "created_at": feedback.created_at.isoformat(),
            "updated_at": feedback.updated_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")


@router.get("/recent")
async def get_recent_feedback(
    limit: int = Query(default=10, ge=1, le=100),
    feedback_type: Optional[str] = None,
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get recent feedback."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Get recent feedback
        recent_feedback = await feedback_manager.get_feedback_summary(
            tenant_id=tenant_id,
            time_period_days=7,  # Last 7 days
            feedback_type=feedback_type,
            category=category,
            user_id=user_id,
        )

        return {
            "recent_feedback": recent_feedback.get("recent_feedback", []),
            "filters": {
                "feedback_type": feedback_type,
                "category": category,
                "user_id": user_id,
                "limit": limit,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent feedback: {str(e)}"
        )


@router.get("/nps/statistics")
async def get_nps_statistics(
    time_period_days: int = Query(default=30, ge=1, le=365),
    user_id: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get NPS statistics."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Get feedback summary (includes NPS stats)
        summary = await feedback_manager.get_feedback_summary(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            user_id=user_id,
        )

        nps_stats = summary.get("nps_statistics", {})

        return {
            "period_days": time_period_days,
            "nps_statistics": nps_stats,
            "generated_at": summary.get("generated_at"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get NPS statistics: {str(e)}"
        )


@router.get("/sentiment/analysis")
async def get_sentiment_analysis(
    time_period_days: int = Query(default=30, ge=1, le=365),
    feedback_type: Optional[str] = None,
    category: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get sentiment analysis."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Get feedback summary (includes sentiment stats)
        summary = await feedback_manager.get_feedback_summary(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            feedback_type=feedback_type,
            category=category,
        )

        sentiment_stats = summary.get("sentiment_statistics", {})

        return {
            "period_days": time_period_days,
            "sentiment_statistics": sentiment_stats,
            "generated_at": summary.get("generated_at"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get sentiment analysis: {str(e)}"
        )


@router.get("/dashboard")
async def get_feedback_dashboard(
    time_period_days: int = Query(default=30, ge=1, le=365),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive feedback dashboard data."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Get feedback summary
        summary = await feedback_manager.get_feedback_summary(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        # Get trends analysis
        trends = await feedback_manager.analyze_feedback_trends(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        # Get categories
        categories = await feedback_manager.get_feedback_categories(
            tenant_id=tenant_id,
            active_only=True,
        )

        return {
            "period_days": time_period_days,
            "feedback_statistics": summary.get("feedback_statistics", {}),
            "sentiment_statistics": summary.get("sentiment_statistics", {}),
            "nps_statistics": summary.get("nps_statistics", {}),
            "category_breakdown": summary.get("category_breakdown", {}),
            "recent_feedback": summary.get("recent_feedback", []),
            "trends_analysis": {
                "total_responses": trends.total_responses,
                "average_rating": trends.average_rating,
                "sentiment_distribution": trends.sentiment_distribution,
                "key_themes": trends.key_themes,
                "recommendations": trends.recommendations,
            },
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "description": cat.description,
                }
                for cat in categories
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get feedback dashboard: {str(e)}"
        )


@router.get("/export/feedback")
async def export_feedback(
    format: str = Query(default="json", regex="^(json|csv)$"),
    time_period_days: int = Query(default=30, ge=1, le=365),
    feedback_type: Optional[str] = None,
    category: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Any:
    """Export feedback data."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Get feedback summary
        summary = await feedback_manager.get_feedback_summary(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            feedback_type=feedback_type,
            category=category,
        )

        if format == "json":
            return JSONResponse(
                content=summary,
                headers={
                    "Content-Disposition": f"attachment; filename=feedback_{time_period_days}days.json"
                },
            )
        elif format == "csv":
            # Convert to CSV format
            csv_data = _convert_feedback_to_csv(summary)

            from fastapi.responses import Response

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=feedback_{time_period_days}days.csv"
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export feedback: {str(e)}"
        )


def _convert_feedback_to_csv(data: Dict[str, Any]) -> str:
    """Convert feedback data to CSV format."""
    try:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Metric", "Value", "Category"])

        # Write feedback statistics
        if "feedback_statistics" in data:
            feedback_stats = data["feedback_statistics"]
            writer.writerow(
                [
                    "Total Responses",
                    feedback_stats.get("total_responses", 0),
                    "Feedback",
                ]
            )
            writer.writerow(
                ["Average Rating", feedback_stats.get("average_rating", 0), "Feedback"]
            )
            writer.writerow(
                [
                    "Positive Ratings",
                    feedback_stats.get("positive_ratings", 0),
                    "Feedback",
                ]
            )
            writer.writerow(
                [
                    "Negative Ratings",
                    feedback_stats.get("negative_ratings", 0),
                    "Feedback",
                ]
            )

        # Write sentiment statistics
        if "sentiment_statistics" in data:
            sentiment_stats = data["sentiment_statistics"]
            writer.writerow(
                [
                    "Positive Sentiments",
                    sentiment_stats.get("positive_sentiments", 0),
                    "Sentiment",
                ]
            )
            writer.writerow(
                [
                    "Negative Sentiments",
                    sentiment_stats.get("negative_sentiments", 0),
                    "Sentiment",
                ]
            )
            writer.writerow(
                [
                    "Neutral Sentiments",
                    sentiment_stats.get("neutral_sentiments", 0),
                    "Sentiment",
                ]
            )

        # Write NPS statistics
        if "nps_statistics" in data:
            nps_stats = data["nps_statistics"]
            writer.writerow(["NPS Score", nps_stats.get("nps_score", 0), "NPS"])
            writer.writerow(["Promoters", nps_stats.get("promoters", 0), "NPS"])
            writer.writerow(["Detractors", nps_stats.get("detractors", 0), "NPS"])

        # Write category breakdown
        if "category_breakdown" in data:
            category_breakdown = data["category_breakdown"]
            for category, count in category_breakdown.items():
                writer.writerow([f"Category: {category}", count, "Categories"])

        return output.getvalue()

    except Exception as e:
        return f"Error converting to CSV: {str(e)}"


@router.get("/health")
async def health_check(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Health check for feedback system."""
    try:
        # Create feedback manager
        feedback_manager = create_feedback_manager(db_pool)

        # Test database connection
        try:
            async with db_pool.acquire() as conn:
                await conn.fetch("SELECT 1")
                db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Test feedback categories
        try:
            categories = await feedback_manager.get_feedback_categories(tenant_id, True)
            categories_status = "healthy" if categories else "no_categories"
        except Exception:
            categories_status = "unhealthy"

        return {
            "status": "healthy"
            if db_status == "healthy" and categories_status == "healthy"
            else "unhealthy",
            "database": db_status,
            "categories": categories_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
