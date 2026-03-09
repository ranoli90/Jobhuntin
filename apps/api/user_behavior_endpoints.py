"""
User Behavior Analyzer Endpoints for Phase 14.1 User Experience
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.api.dependencies import get_current_user, get_db_pool, get_tenant_id
from packages.backend.domain.user_behavior_analyzer import (
    BehaviorPattern,
    BehaviorType,
    create_user_behavior_analyzer,
)

router = APIRouter(prefix="/user-behavior", tags=["user-behavior"])


class BehaviorEventRequest(BaseModel):
    """Behavior event request model."""

    event_type: str
    event_name: str
    page_url: str
    duration_ms: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


@router.post("/track-event")
async def track_behavior_event(
    event: BehaviorEventRequest,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Track a user behavior event."""
    try:
        # Create behavior analyzer
        analyzer = create_user_behavior_analyzer(db_pool)

        # Get session ID from user context
        session_id = current_user.get("session_id", str(current_user["id"]))

        # Track event
        behavior_event = await analyzer.track_behavior_event(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            session_id=session_id,
            event_type=event.event_type,
            event_name=event.event_name,
            page_url=event.page_url,
            duration_ms=event.duration_ms,
            properties=event.properties,
            context=event.context,
        )

        return {
            "success": True,
            "event_id": behavior_event.id,
            "session_id": session_id,
            "tracked_at": behavior_event.timestamp.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track behavior event: {str(e)}"
        )


@router.post("/analyze-user")
async def analyze_user_behavior(
    user_id: Optional[str] = None,
    time_period_days: int = Query(default=30, ge=1, le=365),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Analyze user behavior and create profile."""
    try:
        # Use current user if no user_id provided
        target_user_id = user_id or current_user["id"]

        # Create behavior analyzer
        analyzer = create_user_behavior_analyzer(db_pool)

        # Analyze behavior
        profile = await analyzer.analyze_user_behavior(
            user_id=target_user_id,
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        return {
            "user_id": target_user_id,
            "profile": {
                "id": profile.id,
                "behavior_type": profile.behavior_type.value,
                "behavior_pattern": profile.behavior_pattern.value,
                "confidence_score": profile.confidence_score,
                "characteristics": profile.characteristics,
                "metrics": profile.metrics,
                "session_count": profile.session_count,
                "total_time_spent": profile.total_time_spent,
                "last_updated": profile.last_updated.isoformat(),
                "created_at": profile.created_at.isoformat(),
            },
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze user behavior: {str(e)}"
        )


@router.get("/insights")
async def get_behavior_insights(
    time_period_days: int = Query(default=30, ge=1, le=365),
    behavior_type: Optional[str] = Query(
        None,
        regex="^(navigation|interaction|conversion|retention|engagement|frustration|efficiency|exploration)$",
    ),
    behavior_pattern: Optional[str] = Query(
        None,
        regex="^(linear_navigation|nonlinear_navigation|task_oriented|exploratory|power_user|casual_user|frustrated|satisfied|efficient|inefficient)$",
    ),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive behavior insights."""
    try:
        # Create behavior analyzer
        analyzer = create_user_behavior_analyzer(db_pool)

        # Convert string to enum if provided
        behavior_type_enum = None
        if behavior_type:
            behavior_type_enum = BehaviorType(behavior_type)

        behavior_pattern_enum = None
        if behavior_pattern:
            behavior_pattern_enum = BehaviorPattern(behavior_pattern)

        # Get insights
        insights = await analyzer.get_behavior_insights(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            behavior_type=behavior_type_enum,
            behavior_pattern=behavior_pattern_enum,
        )

        return insights

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get behavior insights: {str(e)}"
        )


@router.get("/trends")
async def get_user_behavior_trends(
    user_id: Optional[str] = None,
    time_period_days: int = Query(default=30, ge=1, le=365),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get user behavior trends over time."""
    try:
        # Use current user if no user_id provided
        target_user_id = user_id or current_user["id"]

        # Create behavior analyzer
        analyzer = create_user_behavior_analyzer(db_pool)

        # Get trends
        trends = await analyzer.get_user_behavior_trends(
            user_id=target_user_id,
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        return trends

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user behavior trends: {str(e)}"
        )


@router.get("/segments")
async def get_behavior_segments(
    time_period_days: int = Query(default=30, ge=1, le=365),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get user behavior segments."""
    try:
        # Create behavior analyzer
        analyzer = create_user_behavior_analyzer(db_pool)

        # Get segments
        segments = await analyzer.get_behavior_segments(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        return segments

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get behavior segments: {str(e)}"
        )


@router.get("/events")
async def get_behavior_events(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    page_url: Optional[str] = None,
    time_period_hours: int = Query(default=24, ge=1, le=720),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get behavior events with filtering."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_period_hours)

        # Build query
        query = """
            SELECT * FROM behavior_events
            WHERE tenant_id = $1 AND timestamp > $2
        """
        params = [tenant_id, cutoff_time]

        if user_id:
            query += " AND user_id = $3"
            params.append(user_id)

        if event_type:
            query += " AND event_type = $4"
            params.append(event_type)

        if page_url:
            query += " AND page_url = $5"
            params.append(page_url)

        query += " ORDER BY timestamp DESC LIMIT $6 OFFSET $7"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            events = []
            for row in results:
                event = {
                    "id": row[0],
                    "user_id": row[1],
                    "tenant_id": row[2],
                    "session_id": row[3],
                    "event_type": row[4],
                    "event_name": row[5],
                    "page_url": row[6],
                    "timestamp": row[7].isoformat(),
                    "duration_ms": row[8],
                    "properties": json.loads(row[9]) if row[9] else {},
                    "context": json.loads(row[10]) if row[10] else {},
                    "created_at": row[11].isoformat(),
                }
                events.append(event)

        return {
            "events": events,
            "total_count": len(events),
            "limit": limit,
            "offset": offset,
            "filters": {
                "user_id": user_id,
                "event_type": event_type,
                "page_url": page_url,
                "time_period_hours": time_period_hours,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get behavior events: {str(e)}"
        )


@router.get("/profiles")
async def get_behavior_profiles(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    behavior_type: Optional[str] = None,
    behavior_pattern: Optional[str] = None,
    time_period_days: int = Query(default=30, ge=1, le=365),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get behavior profiles with filtering."""
    try:
        # Build query
        query = """
            SELECT * FROM behavior_profiles
            WHERE tenant_id = $1 AND last_updated > $2
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)
        params = [tenant_id, cutoff_time]

        if behavior_type:
            query += " AND behavior_type = $3"
            params.append(behavior_type)

        if behavior_pattern:
            query += " AND behavior_pattern = $4"
            params.append(behavior_pattern)

        query += " ORDER BY last_updated DESC LIMIT $5 OFFSET $6"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            profiles = []
            for row in results:
                profile = {
                    "id": row[0],
                    "user_id": row[1],
                    "tenant_id": row[2],
                    "behavior_type": row[3],
                    "behavior_pattern": row[4],
                    "confidence_score": row[5],
                    "characteristics": json.loads(row[6]) if row[6] else {},
                    "metrics": json.loads(row[7]) if row[7] else {},
                    "session_count": row[8],
                    "total_time_spent": row[9],
                    "last_updated": row[10].isoformat(),
                    "created_at": row[11].isoformat(),
                }
                profiles.append(profile)

        return {
            "profiles": profiles,
            "total_count": len(profiles),
            "limit": limit,
            "offset": offset,
            "filters": {
                "behavior_type": behavior_type,
                "behavior_pattern": behavior_pattern,
                "time_period_days": time_period_days,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get behavior profiles: {str(e)}"
        )


@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get behavior profile for a specific user."""
    try:
        # Get profile
        query = """
            SELECT * FROM behavior_profiles
            WHERE user_id = $1 AND tenant_id = $2
            ORDER BY last_updated DESC
            LIMIT 1
        """

        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, user_id, tenant_id)

            if not result:
                raise HTTPException(
                    status_code=404, detail="Behavior profile not found"
                )

            profile = {
                "id": result[0],
                "user_id": result[1],
                "tenant_id": result[2],
                "behavior_type": result[3],
                "behavior_pattern": result[4],
                "confidence_score": result[5],
                "characteristics": json.loads(result[6]) if result[6] else {},
                "metrics": json.loads(result[7]) if result[7] else {},
                "session_count": result[8],
                "total_time_spent": result[9],
                "last_updated": result[10].isoformat(),
                "created_at": result[11].isoformat(),
            }

        return profile

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user profile: {str(e)}"
        )


@router.get("/patterns/types")
async def get_behavior_pattern_types(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get available behavior pattern types."""
    try:
        return {
            "behavior_types": [
                {
                    "value": bt.value,
                    "name": bt.value.replace("_", " ").title(),
                }
                for bt in BehaviorType
            ],
            "behavior_patterns": [
                {
                    "value": bp.value,
                    "name": bp.value.replace("_", " ").title(),
                }
                for bp in BehaviorPattern
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get behavior pattern types: {str(e)}"
        )


@router.get("/dashboard")
async def get_behavior_dashboard(
    time_period_days: int = Query(default=30, ge=1, le=365),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive behavior dashboard."""
    try:
        # Create behavior analyzer
        analyzer = create_user_behavior_analyzer(db_pool)

        # Get insights
        insights = await analyzer.get_behavior_insights(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        # Get segments
        segments = await analyzer.get_behavior_segments(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        # Get current user's trends
        user_trends = await analyzer.get_user_behavior_trends(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        # Get current user's profile
        try:
            profile_query = """
                SELECT * FROM behavior_profiles
                WHERE user_id = $1 AND tenant_id = $2
                ORDER BY last_updated DESC
                LIMIT 1
            """

            async with db_pool.acquire() as conn:
                profile_result = await conn.fetchrow(
                    profile_query, current_user["id"], tenant_id
                )

                user_profile = None
                if profile_result:
                    user_profile = {
                        "id": profile_result[0],
                        "behavior_type": profile_result[3],
                        "behavior_pattern": profile_result[4],
                        "confidence_score": profile_result[5],
                        "session_count": profile_result[8],
                        "total_time_spent": profile_result[9],
                        "last_updated": profile_result[10].isoformat(),
                    }
        except Exception:
            user_profile = None

        return {
            "period_days": time_period_days,
            "insights": insights,
            "segments": segments,
            "user_trends": user_trends,
            "user_profile": user_profile,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get behavior dashboard: {str(e)}"
        )


@router.get("/export/behavior")
async def export_behavior_data(
    format: str = Query(default="json", regex="^(json|csv)$"),
    time_period_days: int = Query(default=30, ge=1, le=365),
    behavior_type: Optional[str] = None,
    behavior_pattern: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Any:
    """Export behavior data."""
    try:
        # Create behavior analyzer
        analyzer = create_user_behavior_analyzer(db_pool)

        # Convert string to enum if provided
        behavior_type_enum = None
        if behavior_type:
            behavior_type_enum = BehaviorType(behavior_type)

        behavior_pattern_enum = None
        if behavior_pattern:
            behavior_pattern_enum = BehaviorPattern(behavior_pattern)

        # Get insights
        insights = await analyzer.get_behavior_insights(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            behavior_type=behavior_type_enum,
            behavior_pattern=behavior_pattern_enum,
        )

        if format == "json":
            return JSONResponse(
                content=insights,
                headers={
                    "Content-Disposition": f"attachment; filename=behavior_{time_period_days}days.json"
                },
            )
        elif format == "csv":
            # Convert to CSV format
            csv_data = _convert_behavior_to_csv(insights)

            from fastapi.responses import Response

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=behavior_{time_period_days}days.csv"
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export behavior data: {str(e)}"
        )


def _convert_behavior_to_csv(data: Dict[str, Any]) -> str:
    """Convert behavior data to CSV format."""
    try:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Metric", "Value", "Category"])

        # Write behavior patterns
        if "behavior_patterns" in data:
            patterns = data["behavior_patterns"]
            for pattern, count in patterns.items():
                writer.writerow([f"Pattern: {pattern}", count, "Behavior Patterns"])

        # Write behavior metrics
        if "behavior_metrics" in data:
            metrics = data["behavior_metrics"]
            for metric, value in metrics.items():
                writer.writerow([f"Metric: {metric}", value, "Behavior Metrics"])

        # Write insights
        if "insights" in data:
            insights = data["insights"]
            for i, insight in enumerate(insights):
                writer.writerow(
                    [f"Insight {i + 1}", insight.get("message", ""), "Insights"]
                )

        # Write recommendations
        if "recommendations" in data:
            recommendations = data["recommendations"]
            for i, recommendation in enumerate(recommendations):
                writer.writerow(
                    [f"Recommendation {i + 1}", recommendation, "Recommendations"]
                )

        return output.getvalue()

    except Exception as e:
        return f"Error converting to CSV: {str(e)}"


@router.get("/health")
async def health_check(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Health check for user behavior analyzer."""
    try:
        # Create behavior analyzer
        analyzer = create_user_behavior_analyzer(db_pool)

        # Test database connection
        try:
            async with db_pool.acquire() as conn:
                await conn.fetch("SELECT 1")
                db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Test behavior events
        try:
            query = "SELECT COUNT(*) FROM behavior_events WHERE tenant_id = $1"
            async with db_pool.acquire() as conn:
                await conn.fetchval(query, tenant_id)
                events_status = "healthy"
        except Exception:
            events_status = "unhealthy"

        # Test behavior profiles
        try:
            query = "SELECT COUNT(*) FROM behavior_profiles WHERE tenant_id = $1"
            async with db_pool.acquire() as conn:
                await conn.fetchval(query, tenant_id)
                profiles_status = "healthy"
        except Exception:
            profiles_status = "unhealthy"

        return {
            "status": "healthy"
            if all(s == "healthy" for s in [db_status, events_status, profiles_status])
            else "unhealthy",
            "database": db_status,
            "events": events_status,
            "profiles": profiles_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
