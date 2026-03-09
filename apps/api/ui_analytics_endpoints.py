"""
UI Analytics Endpoints for Phase 14.1 User Experience
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from apps.api.dependencies import get_current_user, get_db_pool, get_tenant_id
from packages.backend.domain.ui_analytics_manager import create_ui_analytics_manager

router = APIRouter(prefix="/ui-analytics", tags=["ui-analytics"])


@router.post("/track/page-view")
async def track_page_view(
    page_url: str,
    page_title: Optional[str] = None,
    referrer: Optional[str] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    device_type: str = "web",
    browser: Optional[str] = None,
    screen_resolution: Optional[str] = None,
    load_time: Optional[float] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Track a page view."""
    try:
        # Get session ID from user context or create new one
        session_id = current_user.get("session_id", str(current_user["id"]))

        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Track page view
        page_view = await analytics_manager.track_page_view(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            session_id=session_id,
            page_url=page_url,
            page_title=page_title,
            referrer=referrer,
            user_agent=user_agent,
            ip_address=ip_address,
            device_type=device_type,
            browser=browser,
            screen_resolution=screen_resolution,
            load_time=load_time,
        )

        return {
            "success": True,
            "page_view_id": page_view.id,
            "session_id": session_id,
            "tracked_at": page_view.timestamp.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track page view: {str(e)}"
        )


@router.post("/track/user-action")
async def track_user_action(
    page_url: str,
    action_type: str,
    action_name: str,
    element_selector: Optional[str] = None,
    element_text: Optional[str] = None,
    element_attributes: Optional[Dict[str, Any]] = None,
    coordinates: Optional[Dict[str, int]] = None,
    duration_ms: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Track a user action."""
    try:
        # Get session ID from user context
        session_id = current_user.get("session_id", str(current_user["id"]))

        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Track user action
        action = await analytics_manager.track_user_action(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            session_id=session_id,
            page_url=page_url,
            action_type=action_type,
            action_name=action_name,
            element_selector=element_selector,
            element_text=element_text,
            element_attributes=element_attributes,
            coordinates=coordinates,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata,
        )

        return {
            "success": True,
            "action_id": action.id,
            "session_id": session_id,
            "tracked_at": action.timestamp.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track user action: {str(e)}"
        )


@router.post("/track/conversion")
async def track_conversion_event(
    event_type: str,
    event_name: str,
    page_url: str,
    conversion_value: Optional[float] = None,
    conversion_currency: Optional[str] = None,
    funnel_step: Optional[int] = None,
    funnel_name: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Track a conversion event."""
    try:
        # Get session ID from user context
        session_id = current_user.get("session_id", str(current_user["id"]))

        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Track conversion event
        conversion = await analytics_manager.track_conversion_event(
            user_id=current_user["id"],
            tenant_id=tenant_id,
            session_id=session_id,
            event_type=event_type,
            event_name=event_name,
            page_url=page_url,
            conversion_value=conversion_value,
            conversion_currency=conversion_currency,
            funnel_step=funnel_step,
            funnel_name=funnel_name,
            properties=properties,
        )

        return {
            "success": True,
            "conversion_id": conversion.id,
            "session_id": session_id,
            "tracked_at": conversion.timestamp.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track conversion event: {str(e)}"
        )


@router.put("/update-page-view-time")
async def update_page_view_time(
    page_view_id: str,
    time_on_page: int,
    scroll_depth: Optional[float] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Update page view with time on page and scroll depth."""
    try:
        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Update page view
        success = await analytics_manager.update_page_view_time(
            page_view_id=page_view_id,
            time_on_page=time_on_page,
            scroll_depth=scroll_depth,
        )

        return {
            "success": success,
            "page_view_id": page_view_id,
            "time_on_page": time_on_page,
            "scroll_depth": scroll_depth,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update page view time: {str(e)}"
        )


@router.get("/summary")
async def get_analytics_summary(
    time_period_days: int = Query(default=7, ge=1, le=90),
    user_id: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive analytics summary."""
    try:
        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Get analytics summary
        summary = await analytics_manager.get_analytics_summary(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            user_id=user_id,
        )

        return summary

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics summary: {str(e)}"
        )


@router.get("/conversion-funnel/{funnel_name}")
async def get_conversion_funnel(
    funnel_name: str,
    time_period_days: int = Query(default=30, ge=1, le=90),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get conversion funnel analysis."""
    try:
        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Get conversion funnel
        funnel = await analytics_manager.get_conversion_funnel(
            tenant_id=tenant_id,
            funnel_name=funnel_name,
            time_period_days=time_period_days,
        )

        return {
            "funnel_name": funnel_name,
            "total_users": funnel.total_users,
            "conversion_rate": funnel.conversion_rate,
            "abandonment_rate": funnel.abandonment_rate,
            "avg_time_to_convert": funnel.avg_time_to_convert,
            "step_analytics": funnel.step_analytics,
            "created_at": funnel.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get conversion funnel: {str(e)}"
        )


@router.get("/behavior-patterns")
async def get_behavior_patterns(
    time_period_days: int = Query(default=7, ge=1, le=90),
    user_id: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Analyze user behavior patterns."""
    try:
        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Get behavior patterns
        patterns = await analytics_manager.get_user_behavior_patterns(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
            user_id=user_id,
        )

        return patterns

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get behavior patterns: {str(e)}"
        )


@router.get("/page-performance")
async def get_page_performance_metrics(
    page_url: Optional[str] = None,
    time_period_days: int = Query(default=7, ge=1, le=90),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get page performance metrics."""
    try:
        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Get page performance metrics
        metrics = await analytics_manager.get_page_performance_metrics(
            tenant_id=tenant_id,
            page_url=page_url,
            time_period_days=time_period_days,
        )

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get page performance metrics: {str(e)}"
        )


@router.get("/page-views")
async def get_page_views(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    page_url: Optional[str] = None,
    user_id: Optional[str] = None,
    time_period_hours: int = Query(default=24, ge=1, le=720),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get page views with filtering."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_period_hours)

        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Build query
        query = """
            SELECT * FROM page_views
            WHERE tenant_id = $1 AND timestamp > $2
        """
        params = [tenant_id, cutoff_time]

        if page_url:
            query += " AND page_url = $3"
            params.append(page_url)

        if user_id:
            query += " AND user_id = $4"
            params.append(user_id)

        query += " ORDER BY timestamp DESC LIMIT $5 OFFSET $6"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            page_views = []
            for row in results:
                page_view = {
                    "id": row[0],
                    "user_id": row[1],
                    "tenant_id": row[2],
                    "session_id": row[3],
                    "page_url": row[4],
                    "page_title": row[5],
                    "referrer": row[6],
                    "device_type": row[7],
                    "browser": row[8],
                    "screen_resolution": row[9],
                    "load_time": row[10],
                    "timestamp": row[11].isoformat(),
                    "time_on_page": row[12],
                    "scroll_depth": row[13],
                    "clicks": row[14],
                    "created_at": row[15].isoformat(),
                }
                page_views.append(page_view)

        return {
            "page_views": page_views,
            "total_count": len(page_views),
            "limit": limit,
            "offset": offset,
            "filters": {
                "page_url": page_url,
                "user_id": user_id,
                "time_period_hours": time_period_hours,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get page views: {str(e)}"
        )


@router.get("/user-actions")
async def get_user_actions(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    page_url: Optional[str] = None,
    action_type: Optional[str] = None,
    user_id: Optional[str] = None,
    time_period_hours: int = Query(default=24, ge=1, le=720),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get user actions with filtering."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_period_hours)

        # Build query
        query = """
            SELECT * FROM user_actions
            WHERE tenant_id = $1 AND timestamp > $2
        """
        params = [tenant_id, cutoff_time]

        if page_url:
            query += " AND page_url = $3"
            params.append(page_url)

        if action_type:
            query += " AND action_type = $4"
            params.append(action_type)

        if user_id:
            query += " AND user_id = $5"
            params.append(user_id)

        query += " ORDER BY timestamp DESC LIMIT $6 OFFSET $7"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            user_actions = []
            for row in results:
                action = {
                    "id": row[0],
                    "user_id": row[1],
                    "tenant_id": row[2],
                    "session_id": row[3],
                    "page_url": row[4],
                    "action_type": row[5],
                    "action_name": row[6],
                    "element_selector": row[7],
                    "element_text": row[8],
                    "element_attributes": json.loads(row[9]) if row[9] else {},
                    "coordinates": json.loads(row[10]) if row[10] else {},
                    "timestamp": row[11].isoformat(),
                    "duration_ms": row[12],
                    "success": row[13],
                    "error_message": row[14],
                    "metadata": json.loads(row[15]) if row[15] else {},
                    "created_at": row[16].isoformat(),
                }
                user_actions.append(action)

        return {
            "user_actions": user_actions,
            "total_count": len(user_actions),
            "limit": limit,
            "offset": offset,
            "filters": {
                "page_url": page_url,
                "action_type": action_type,
                "user_id": user_id,
                "time_period_hours": time_period_hours,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user actions: {str(e)}"
        )


@router.get("/conversion-events")
async def get_conversion_events(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    event_type: Optional[str] = None,
    funnel_name: Optional[str] = None,
    user_id: Optional[str] = None,
    time_period_hours: int = Query(default=24, ge=1, le=720),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get conversion events with filtering."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_period_hours)

        # Build query
        query = """
            SELECT * FROM conversion_events
            WHERE tenant_id = $1 AND timestamp > $2
        """
        params = [tenant_id, cutoff_time]

        if event_type:
            query += " AND event_type = $3"
            params.append(event_type)

        if funnel_name:
            query += " AND funnel_name = $4"
            params.append(funnel_name)

        if user_id:
            query += " AND user_id = $5"
            params.append(user_id)

        query += " ORDER BY timestamp DESC LIMIT $6 OFFSET $7"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)

            conversion_events = []
            for row in results:
                event = {
                    "id": row[0],
                    "user_id": row[1],
                    "tenant_id": row[2],
                    "session_id": row[3],
                    "event_type": row[4],
                    "event_name": row[5],
                    "page_url": row[6],
                    "conversion_value": row[7],
                    "conversion_currency": row[8],
                    "funnel_step": row[9],
                    "funnel_name": row[10],
                    "properties": json.loads(row[11]) if row[11] else {},
                    "timestamp": row[12].isoformat(),
                    "created_at": row[13].isoformat(),
                }
                conversion_events.append(event)

        return {
            "conversion_events": conversion_events,
            "total_count": len(conversion_events),
            "limit": limit,
            "offset": offset,
            "filters": {
                "event_type": event_type,
                "funnel_name": funnel_name,
                "user_id": user_id,
                "time_period_hours": time_period_hours,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get conversion events: {str(e)}"
        )


@router.get("/funnel-definitions")
async def get_funnel_definitions(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get available funnel definitions."""
    try:
        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Get funnel definitions
        funnels = analytics_manager._conversion_funnels

        return {
            "funnels": [
                {
                    "name": name,
                    "description": funnel["name"],
                    "steps": funnel["steps"],
                    "conversion_events": funnel["conversion_events"],
                }
                for name, funnel in funnels.items()
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get funnel definitions: {str(e)}"
        )


@router.get("/top-pages")
async def get_top_pages(
    limit: int = Query(default=10, ge=1, le=100),
    time_period_hours: int = Query(default=24, ge=1, le=720),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get top pages by views."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_period_hours)

        query = """
            SELECT
                page_url,
                COUNT(*) as views,
                COUNT(DISTINCT user_id) as unique_users,
                AVG(time_on_page) as avg_time_on_page,
                AVG(scroll_depth) as avg_scroll_depth
            FROM page_views
            WHERE tenant_id = $1 AND timestamp > $2
            GROUP BY page_url
            ORDER BY views DESC
            LIMIT $3
        """

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, tenant_id, cutoff_time, limit)

            top_pages = []
            for row in results:
                page = {
                    "page_url": row[0],
                    "views": row[1],
                    "unique_users": row[2],
                    "avg_time_on_page": float(row[3]) if row[3] else 0,
                    "avg_scroll_depth": float(row[4]) if row[4] else 0,
                }
                top_pages.append(page)

        return {
            "top_pages": top_pages,
            "period_hours": time_period_hours,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get top pages: {str(e)}"
        )


@router.get("/top-actions")
async def get_top_actions(
    limit: int = Query(default=10, ge=1, le=100),
    time_period_hours: int = Query(default=24, ge=1, le=720),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get top user actions."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_period_hours)

        query = """
            SELECT
                action_name,
                COUNT(*) as actions,
                COUNT(DISTINCT user_id) as unique_users,
                AVG(duration_ms) as avg_duration,
                COUNT(CASE WHEN success = true THEN 1 END) as successful_actions
            FROM user_actions
            WHERE tenant_id = $1 AND timestamp > $2
            GROUP BY action_name
            ORDER BY actions DESC
            LIMIT $3
        """

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, tenant_id, cutoff_time, limit)

            top_actions = []
            for row in results:
                action = {
                    "action_name": row[0],
                    "actions": row[1],
                    "unique_users": row[2],
                    "avg_duration": float(row[3]) if row[3] else 0,
                    "successful_actions": row[4],
                    "success_rate": (row[4] / row[1]) if row[1] > 0 else 0,
                }
                top_actions.append(action)

        return {
            "top_actions": top_actions,
            "period_hours": time_period_hours,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get top actions: {str(e)}"
        )


@router.get("/real-time-stats")
async def get_real_time_stats(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get real-time statistics."""
    try:
        # Get last hour stats
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)

        # Page views in last hour
        page_views_query = """
            SELECT COUNT(*) as views, COUNT(DISTINCT user_id) as unique_users
            FROM page_views
            WHERE tenant_id = $1 AND timestamp > $2
        """

        # User actions in last hour
        actions_query = """
            SELECT COUNT(*) as actions, COUNT(CASE WHEN success = true THEN 1 END) as successful
            FROM user_actions
            WHERE tenant_id = $1 AND timestamp > $2
        """

        # Conversions in last hour
        conversions_query = """
            SELECT COUNT(*) as conversions, SUM(conversion_value) as total_value
            FROM conversion_events
            WHERE tenant_id = $1 AND timestamp > $2
        """

        async with db_pool.acquire() as conn:
            page_views_result = await conn.fetchrow(
                page_views_query, tenant_id, cutoff_time
            )
            actions_result = await conn.fetchrow(actions_query, tenant_id, cutoff_time)
            conversions_result = await conn.fetchrow(
                conversions_query, tenant_id, cutoff_time
            )

        stats = {
            "page_views": {
                "total": page_views_result[0],
                "unique_users": page_views_result[1],
            },
            "user_actions": {
                "total": actions_result[0],
                "successful": actions_result[1],
                "success_rate": (actions_result[1] / actions_result[0])
                if actions_result[0] > 0
                else 0,
            },
            "conversions": {
                "total": conversions_result[0],
                "total_value": float(conversions_result[1])
                if conversions_result[1]
                else 0,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get real-time stats: {str(e)}"
        )


@router.get("/export/analytics")
async def export_analytics(
    format: str = Query(default="json", regex="^(json|csv)$"),
    time_period_days: int = Query(default=7, ge=1, le=90),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Any:
    """Export analytics data."""
    try:
        # Create analytics manager
        analytics_manager = create_ui_analytics_manager(db_pool)

        # Get analytics summary
        summary = await analytics_manager.get_analytics_summary(
            tenant_id=tenant_id,
            time_period_days=time_period_days,
        )

        if format == "json":
            return JSONResponse(
                content=summary,
                headers={
                    "Content-Disposition": f"attachment; filename=analytics_{time_period_days}days.json"
                },
            )
        elif format == "csv":
            # Convert to CSV format
            csv_data = _convert_to_csv(summary)

            from fastapi.responses import Response

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=analytics_{time_period_days}days.csv"
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export analytics: {str(e)}"
        )


def _convert_to_csv(data: Dict[str, Any]) -> str:
    """Convert analytics data to CSV format."""
    try:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Metric", "Value", "Category"])

        # Write page view statistics
        if "page_view_statistics" in data:
            page_stats = data["page_view_statistics"]
            writer.writerow(
                ["Total Views", page_stats.get("total_views", 0), "Page Views"]
            )
            writer.writerow(
                ["Unique Users", page_stats.get("unique_users", 0), "Page Views"]
            )
            writer.writerow(
                ["Average Load Time", page_stats.get("avg_load_time", 0), "Page Views"]
            )

        # Write action statistics
        if "action_statistics" in data:
            action_stats = data["action_statistics"]
            writer.writerow(
                ["Total Actions", action_stats.get("total_actions", 0), "User Actions"]
            )
            writer.writerow(
                ["Success Rate", action_stats.get("success_rate", 0), "User Actions"]
            )

        # Write conversion statistics
        if "conversion_statistics" in data:
            conv_stats = data["conversion_statistics"]
            writer.writerow(
                [
                    "Total Conversions",
                    conv_stats.get("total_conversions", 0),
                    "Conversions",
                ]
            )
            writer.writerow(
                ["Total Value", conv_stats.get("total_value", 0), "Conversions"]
            )

        return output.getvalue()

    except Exception as e:
        return f"Error converting to CSV: {str(e)}"
