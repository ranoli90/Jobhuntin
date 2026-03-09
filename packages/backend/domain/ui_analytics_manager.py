"""
UI Analytics Manager for Phase 14.1 User Experience
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.ui_analytics_manager")


@dataclass
class PageView:
    """Page view tracking data."""

    id: str
    user_id: str
    tenant_id: str
    session_id: str
    page_url: str
    page_title: Optional[str]
    referrer: Optional[str]
    user_agent: Optional[str]
    ip_address: Optional[str]
    device_type: str
    browser: Optional[str]
    screen_resolution: Optional[str]
    load_time: Optional[float]
    timestamp: datetime = datetime.now(timezone.utc)
    time_on_page: Optional[int] = None
    scroll_depth: Optional[float] = None
    clicks: int = 0
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class UserAction:
    """User action tracking data for UI analytics."""

    id: str
    user_id: str
    tenant_id: str
    session_id: str
    page_url: str
    action_type: str
    action_name: str
    element_selector: Optional[str]
    element_text: Optional[str]
    element_attributes: Dict[str, Any] = field(default_factory=dict)
    coordinates: Optional[Dict[str, int]] = None
    timestamp: datetime = datetime.now(timezone.utc)
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class ConversionEvent:
    """Conversion event tracking data."""

    id: str
    user_id: str
    tenant_id: str
    session_id: str
    event_type: str
    event_name: str
    page_url: str
    conversion_value: Optional[float]
    conversion_currency: Optional[str]
    funnel_step: Optional[int]
    funnel_name: Optional[str]
    properties: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = datetime.now(timezone.utc)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class FunnelAnalysis:
    """Funnel analysis data."""

    id: str
    tenant_id: str
    funnel_name: str
    total_users: int
    step_analytics: List[Dict[str, Any]] = field(default_factory=list)
    conversion_rate: float
    abandonment_rate: float
    avg_time_to_convert: Optional[int]
    created_at: datetime = datetime.now(timezone.utc)


class UIAnalyticsManager:
    """Advanced UI analytics management system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._conversion_funnels = self._initialize_conversion_funnels()
        self._page_view_cache: Dict[str, List[PageView]] = {}
        self._action_cache: Dict[str, List[UserAction]] = {}

    async def track_page_view(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        page_url: str,
        page_title: Optional[str] = None,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_type: str = "web",
        browser: Optional[str] = None,
        screen_resolution: Optional[str] = None,
        load_time: Optional[float] = None,
    ) -> PageView:
        """Track a page view."""
        try:
            # Create page view record
            page_view = PageView(
                id=str(uuid.uuid4()),
                user_id=user_id,
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

            # Save to database
            await self._save_page_view(page_view)

            # Update cache
            if session_id not in self._page_view_cache:
                self._page_view_cache[session_id] = []
            self._page_view_cache[session_id].append(page_view)

            logger.info(f"Tracked page view: {page_url} for session {session_id}")
            return page_view

        except Exception as e:
            logger.error(f"Failed to track page view: {e}")
            raise

    async def track_user_action(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
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
    ) -> UserAction:
        """Track a user action."""
        try:
            # Create action record
            action = UserAction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                page_url=page_url,
                action_type=action_type,
                action_name=action_name,
                element_selector=element_selector,
                element_text=element_text,
                element_attributes=element_attributes or {},
                coordinates=coordinates,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata=metadata or {},
            )

            # Save to database
            await self._save_user_action(action)

            # Update cache
            if session_id not in self._action_cache:
                self._action_cache[session_id] = []
            self._action_cache[session_id].append(action)

            logger.info(f"Tracked user action: {action_name} on {page_url}")
            return action

        except Exception as e:
            logger.error(f"Failed to track user action: {e}")
            raise

    async def track_conversion_event(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        event_type: str,
        event_name: str,
        page_url: str,
        conversion_value: Optional[float] = None,
        conversion_currency: Optional[str] = None,
        funnel_step: Optional[int] = None,
        funnel_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> ConversionEvent:
        """Track a conversion event."""
        try:
            # Create conversion event
            conversion = ConversionEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                event_type=event_type,
                event_name=event_name,
                page_url=page_url,
                conversion_value=conversion_value,
                conversion_currency=conversion_currency,
                funnel_step=funnel_step,
                funnel_name=funnel_name,
                properties=properties or {},
            )

            # Save to database
            await self._save_conversion_event(conversion)

            logger.info(f"Tracked conversion event: {event_name} ({conversion_value})")
            return conversion

        except Exception as e:
            logger.error(f"Failed to track conversion event: {e}")
            raise

    async def get_analytics_summary(
        self,
        tenant_id: str,
        time_period_days: int = 7,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive analytics summary."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get page view statistics
            page_stats = await self._get_page_view_statistics(
                tenant_id, cutoff_time, user_id
            )

            # Get action statistics
            action_stats = await self._get_action_statistics(
                tenant_id, cutoff_time, user_id
            )

            # Get conversion statistics
            conversion_stats = await self._get_conversion_statistics(
                tenant_id, cutoff_time, user_id
            )

            # Get funnel analysis
            funnel_stats = await self._get_funnel_statistics(
                tenant_id, cutoff_time, user_id
            )

            # Get performance metrics
            performance_stats = await self._get_performance_metrics(
                tenant_id, cutoff_time, user_id
            )

            summary = {
                "period_days": time_period_days,
                "page_view_statistics": page_stats,
                "action_statistics": action_stats,
                "conversion_statistics": conversion_stats,
                "funnel_statistics": funnel_stats,
                "performance_metrics": performance_stats,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {}

    async def get_conversion_funnel(
        self,
        tenant_id: str,
        funnel_name: str,
        time_period_days: int = 30,
    ) -> FunnelAnalysis:
        """Get conversion funnel analysis."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get funnel definition
            funnel_def = self._conversion_funnels.get(funnel_name)
            if not funnel_def:
                raise Exception(f"Funnel {funnel_name} not found")

            # Calculate funnel analysis
            funnel_analysis = await self._calculate_funnel_analysis(
                tenant_id, funnel_name, funnel_def, cutoff_time
            )

            return funnel_analysis

        except Exception as e:
            logger.error(f"Failed to get conversion funnel: {e}")
            raise

    async def get_user_behavior_patterns(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        time_period_days: int = 7,
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get behavior patterns
            patterns = await self._analyze_behavior_patterns(
                tenant_id, cutoff_time, user_id
            )

            return patterns

        except Exception as e:
            logger.error(f"Failed to get user behavior patterns: {e}")
            return {}

    async def get_page_performance_metrics(
        self,
        tenant_id: str,
        page_url: Optional[str] = None,
        time_period_days: int = 7,
    ) -> Dict[str, Any]:
        """Get page performance metrics."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get performance metrics
            metrics = await self._get_page_performance_metrics(
                tenant_id, page_url, cutoff_time
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to get page performance metrics: {e}")
            return {}

    async def update_page_view_time(
        self,
        page_view_id: str,
        time_on_page: int,
        scroll_depth: Optional[float] = None,
    ) -> bool:
        """Update page view with time on page and scroll depth."""
        try:
            query = """
                UPDATE page_views
                SET time_on_page = $1, scroll_depth = $2, updated_at = NOW()
                WHERE id = $3
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    query, time_on_page, scroll_depth, page_view_id
                )

                # Update cache
                for session_views in self._page_view_cache.values():
                    for view in session_views:
                        if view.id == page_view_id:
                            view.time_on_page = time_on_page
                            view.scroll_depth = scroll_depth
                            break

                return result == "UPDATE 1"

        except Exception as e:
            logger.error(f"Failed to update page view time: {e}")
            return False

    def _initialize_conversion_funnels(self) -> Dict[str, Dict[str, Any]]:
        """Initialize conversion funnel definitions."""
        return {
            "job_application": {
                "name": "Job Application Funnel",
                "steps": [
                    {"name": "search_jobs", "description": "Search for jobs"},
                    {"name": "view_job_details", "description": "View job details"},
                    {"name": "apply_to_job", "description": "Apply to job"},
                    {"name": "upload_resume", "description": "Upload resume"},
                    {"name": "submit_application", "description": "Submit application"},
                ],
                "conversion_events": ["submit_application"],
            },
            "user_registration": {
                "name": "User Registration Funnel",
                "steps": [
                    {"name": "visit_signup", "description": "Visit signup page"},
                    {"name": "create_account", "description": "Create account"},
                    {"name": "verify_email", "description": "Verify email"},
                    {"name": "complete_profile", "description": "Complete profile"},
                ],
                "conversion_events": ["complete_profile"],
            },
            "job_search": {
                "name": "Job Search Funnel",
                "steps": [
                    {"name": "search_jobs", "description": "Search for jobs"},
                    {"name": "filter_results", "description": "Filter results"},
                    {"name": "view_job_details", "description": "View job details"},
                    {"name": "save_job", "description": "Save job"},
                ],
                "conversion_events": ["save_job"],
            },
            "resume_upload": {
                "name": "Resume Upload Funnel",
                "steps": [
                    {"name": "visit_upload", "description": "Visit upload page"},
                    {"name": "select_file", "description": "Select file"},
                    {"name": "upload_file", "description": "Upload file"},
                    {"name": "process_resume", "description": "Process resume"},
                ],
                "conversion_events": ["process_resume"],
            },
        }

    async def _calculate_funnel_analysis(
        self,
        tenant_id: str,
        funnel_name: str,
        funnel_def: Dict[str, Any],
        cutoff_time: datetime,
    ) -> FunnelAnalysis:
        """Calculate funnel analysis."""
        try:
            steps = funnel_def["steps"]
            funnel_def["conversion_events"]

            # Get funnel data
            funnel_data = await self._get_funnel_data(
                tenant_id, funnel_name, steps, cutoff_time
            )

            # Calculate step analytics
            step_analytics = []
            total_users = funnel_data.get("total_users", 0)

            for i, step in enumerate(steps):
                step_name = step["name"]
                step_data = funnel_data.get("steps", {}).get(step_name, {})

                step_analytics.append(
                    {
                        "step_name": step_name,
                        "step_description": step["description"],
                        "step_number": i + 1,
                        "users_at_step": step_data.get("users", 0),
                        "drop_off_rate": step_data.get("drop_off_rate", 0),
                        "conversion_rate": step_data.get("conversion_rate", 0),
                        "avg_time_on_step": step_data.get("avg_time", 0),
                    }
                )

            # Calculate overall metrics
            conversion_rate = funnel_data.get("conversion_rate", 0)
            abandonment_rate = 1.0 - conversion_rate
            avg_time_to_convert = funnel_data.get("avg_time_to_convert")

            # Create funnel analysis
            funnel_analysis = FunnelAnalysis(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                funnel_name=funnel_name,
                total_users=total_users,
                step_analytics=step_analytics,
                conversion_rate=conversion_rate,
                abandonment_rate=abandonment_rate,
                avg_time_to_convert=avg_time_to_convert,
                created_at=datetime.now(timezone.utc),
            )

            await self._save_funnel_analysis(funnel_analysis)

            return funnel_analysis

        except Exception as e:
            logger.error(f"Failed to calculate funnel analysis: {e}")
            raise

    async def _get_page_view_statistics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get page view statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_views,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT page_url) as unique_pages,
                    AVG(load_time) as avg_load_time,
                    AVG(time_on_page) as avg_time_on_page,
                    AVG(scroll_depth) as avg_scroll_depth
                FROM page_views
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_views": result[0],
                        "unique_users": result[1],
                        "unique_pages": result[2],
                        "avg_load_time": float(result[3]) if result[3] else 0,
                        "avg_time_on_page": float(result[4]) if result[4] else 0,
                        "avg_scroll_depth": float(result[5]) if result[5] else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get page view statistics: {e}")
            return {}

    async def _get_action_statistics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get action statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT action_type) as unique_action_types,
                    COUNT(DISTINCT action_name) as unique_actions,
                    AVG(duration_ms) as avg_duration,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful_actions
                FROM user_actions
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    total_actions = result[0]
                    successful_actions = result[5]

                    return {
                        "total_actions": total_actions,
                        "unique_users": result[1],
                        "unique_action_types": result[2],
                        "unique_actions": result[3],
                        "avg_duration": float(result[4]) if result[4] else 0,
                        "successful_actions": successful_actions,
                        "success_rate": (successful_actions / total_actions)
                        if total_actions > 0
                        else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get action statistics: {e}")
            return {}

    async def _get_conversion_statistics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get conversion statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_conversions,
                    COUNT(DISTINCT user_id) as converting_users,
                    SUM(conversion_value) as total_value,
                    AVG(conversion_value) as avg_value,
                    COUNT(DISTINCT funnel_name) as unique_funnels
                FROM conversion_events
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_conversions": result[0],
                        "converting_users": result[1],
                        "total_value": float(result[2]) if result[2] else 0,
                        "avg_value": float(result[3]) if result[3] else 0,
                        "unique_funnels": result[4],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get conversion statistics: {e}")
            return {}

    async def _get_funnel_statistics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get funnel statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_funnels,
                    AVG(conversion_rate) as avg_conversion_rate,
                    AVG(abandonment_rate) as avg_abandonment_rate
                FROM funnel_analyses
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_funnels": result[0],
                        "avg_conversion_rate": float(result[1]) if result[1] else 0,
                        "avg_abandonment_rate": float(result[2]) if result[2] else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get funnel statistics: {e}")
            return {}

    async def _get_performance_metrics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics."""
        try:
            query = """
                SELECT
                    AVG(load_time) as avg_load_time,
                    AVG(time_on_page) as avg_time_on_page,
                    AVG(scroll_depth) as avg_scroll_depth,
                    COUNT(CASE WHEN load_time > 3 THEN 1 END) as slow_pages,
                    COUNT(CASE WHEN time_on_page < 5 THEN 1 END) as bounce_pages
                FROM page_views
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    total_pages = await conn.fetchval(
                        "SELECT COUNT(*) FROM page_views WHERE tenant_id = $1 AND timestamp > $2",
                        *params,
                    )

                    return {
                        "avg_load_time": float(result[0]) if result[0] else 0,
                        "avg_time_on_page": float(result[1]) if result[1] else 0,
                        "avg_scroll_depth": float(result[2]) if result[2] else 0,
                        "slow_pages": result[3],
                        "bounce_pages": result[4],
                        "slow_page_rate": (result[3] / total_pages)
                        if total_pages > 0
                        else 0,
                        "bounce_rate": (result[4] / total_pages)
                        if total_pages > 0
                        else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}

    async def _get_funnel_data(
        self,
        tenant_id: str,
        funnel_name: str,
        steps: List[Dict[str, Any]],
        cutoff_time: datetime,
    ) -> Dict[str, Any]:
        """Get funnel data for analysis."""
        try:
            # Get users who entered the funnel
            first_step = steps[0]["name"]
            query = """
                SELECT COUNT(DISTINCT user_id) as total_users
                FROM conversion_events ce
                JOIN user_actions ua ON ce.session_id = ua.session_id
                WHERE ce.tenant_id = $1 AND ce.funnel_name = $2
                AND ce.timestamp > $3 AND ce.event_name = $4
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    query, tenant_id, funnel_name, cutoff_time, first_step
                )
                total_users = result[0] if result else 0

            # Get step data
            steps_data = {}
            for step in steps:
                step_name = step["name"]

                # Get users at this step
                step_query = """
                    SELECT COUNT(DISTINCT user_id) as users
                    FROM conversion_events ce
                    WHERE ce.tenant_id = $1 AND ce.funnel_name = $2
                    AND ce.timestamp > $3 AND ce.event_name = $4
                """

                step_result = await conn.fetchrow(
                    step_query, tenant_id, funnel_name, cutoff_time, step_name
                )
                users_at_step = step_result[0] if step_result else 0

                # Calculate conversion rate for this step
                step_conversion = users_at_step / total_users if total_users > 0 else 0

                # Calculate drop-off rate
                prev_step_users = total_users
                for prev_step in steps[: steps.index(step)]:
                    prev_step_data = steps_data.get(prev_step["name"], {})
                    prev_step_users = prev_step_data.get("users", total_users)
                    break

                drop_off_rate = (
                    (prev_step_users - users_at_step) / prev_step_users
                    if prev_step_users > 0
                    else 0
                )

                steps_data[step_name] = {
                    "users": users_at_step,
                    "conversion_rate": step_conversion,
                    "drop_off_rate": drop_off_rate,
                }

            # Calculate overall conversion rate
            conversion_events = self._conversion_funnels[funnel_name][
                "conversion_events"
            ]
            if conversion_events:
                conversion_query = """
                    SELECT COUNT(DISTINCT user_id) as conversions
                    FROM conversion_events
                    WHERE tenant_id = $1 AND funnel_name = $2
                    AND timestamp > $3 AND event_name = ANY($4)
                """

                conversion_result = await conn.fetchrow(
                    conversion_query,
                    tenant_id,
                    funnel_name,
                    cutoff_time,
                    conversion_events,
                )
                conversions = conversion_result[0] if conversion_result else 0

                overall_conversion_rate = (
                    conversions / total_users if total_users > 0 else 0
                )
            else:
                overall_conversion_rate = 0

            # Calculate average time to convert
            time_query = """
                SELECT AVG(EXTRACT(EPOCH FROM (ce.timestamp - (
                    SELECT MIN(timestamp) FROM conversion_events ce2
                    WHERE ce2.user_id = ce.user_id AND ce2.funnel_name = ce.funnel_name
                ))) / 60) as avg_minutes
                FROM conversion_events ce
                WHERE ce.tenant_id = $1 AND ce.funnel_name = $2
                AND ce.timestamp > $3 AND event_name = ANY($4)
            """

            time_result = await conn.fetchrow(
                time_query, tenant_id, funnel_name, cutoff_time, conversion_events
            )
            avg_time_to_convert = (
                int(time_result[0]) if time_result and time_result[0] else None
            )

            return {
                "total_users": total_users,
                "steps": steps_data,
                "conversion_rate": overall_conversion_rate,
                "avg_time_to_convert": avg_time_to_convert,
            }

        except Exception as e:
            logger.error(f"Failed to get funnel data: {e}")
            return {}

    async def _analyze_behavior_patterns(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        try:
            # Get page view patterns
            page_patterns = await self._analyze_page_patterns(
                tenant_id, cutoff_time, user_id
            )

            # Get action patterns
            action_patterns = await self._analyze_action_patterns(
                tenant_id, cutoff_time, user_id
            )

            # Get time-based patterns
            time_patterns = await self._analyze_time_patterns(
                tenant_id, cutoff_time, user_id
            )

            return {
                "page_patterns": page_patterns,
                "action_patterns": action_patterns,
                "time_patterns": time_patterns,
            }

        except Exception as e:
            logger.error(f"Failed to analyze behavior patterns: {e}")
            return {}

    async def _analyze_page_patterns(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze page view patterns."""
        try:
            query = """
                SELECT page_url, COUNT(*) as views, COUNT(DISTINCT user_id) as unique_users,
                       AVG(time_on_page) as avg_time_on_page, AVG(scroll_depth) as avg_scroll_depth
                FROM page_views
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            query += " GROUP BY page_url ORDER BY views DESC LIMIT 20"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                patterns = []
                for row in results:
                    patterns.append(
                        {
                            "page_url": row[0],
                            "views": row[1],
                            "unique_users": row[2],
                            "avg_time_on_page": float(row[3]) if row[3] else 0,
                            "avg_scroll_depth": float(row[4]) if row[4] else 0,
                        }
                    )

                return {"top_pages": patterns}

        except Exception as e:
            logger.error(f"Failed to analyze page patterns: {e}")
            return {}

    async def _analyze_action_patterns(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze action patterns."""
        try:
            query = """
                SELECT action_name, COUNT(*) as actions, COUNT(DISTINCT user_id) as unique_users,
                       AVG(duration_ms) as avg_duration
                FROM user_actions
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            query += " GROUP BY action_name ORDER BY actions DESC LIMIT 20"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                patterns = []
                for row in results:
                    patterns.append(
                        {
                            "action_name": row[0],
                            "actions": row[1],
                            "unique_users": row[2],
                            "avg_duration": float(row[3]) if row[3] else 0,
                        }
                    )

                return {"top_actions": patterns}

        except Exception as e:
            logger.error(f"Failed to analyze action patterns: {e}")
            return {}

    async def _analyze_time_patterns(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze time-based patterns."""
        try:
            # Get hourly patterns
            hourly_query = """
                SELECT EXTRACT(HOUR FROM timestamp) as hour, COUNT(*) as views
                FROM page_views
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                hourly_query += " AND user_id = $3"
                params.append(user_id)

            hourly_query += " GROUP BY EXTRACT(HOUR FROM timestamp) ORDER BY hour"

            async with self.db_pool.acquire() as conn:
                hourly_results = await conn.fetch(hourly_query, *params)

                hourly_patterns = []
                for row in hourly_results:
                    hourly_patterns.append(
                        {
                            "hour": row[0],
                            "views": row[1],
                        }
                    )

                # Get daily patterns
                daily_query = """
                    SELECT EXTRACT(DAY FROM timestamp) as day, COUNT(*) as views
                    FROM page_views
                    WHERE tenant_id = $1 AND timestamp > $2
                """
                params = [tenant_id, cutoff_time]

                if user_id:
                    daily_query += " AND user_id = $3"
                    params.append(user_id)

                daily_query += " GROUP BY EXTRACT(DAY FROM timestamp) ORDER BY day"

                daily_results = await conn.fetch(daily_query, *params)

                daily_patterns = []
                for row in daily_results:
                    daily_patterns.append(
                        {
                            "day": row[0],
                            "views": row[1],
                        }
                    )

                return {
                    "hourly_patterns": hourly_patterns,
                    "daily_patterns": daily_patterns,
                }

        except Exception as e:
            logger.error(f"Failed to analyze time patterns: {e}")
            return {}

    async def _get_page_performance_metrics(
        self, tenant_id: str, page_url: Optional[str], cutoff_time: datetime
    ) -> Dict[str, Any]:
        """Get page performance metrics."""
        try:
            query = """
                SELECT
                    AVG(load_time) as avg_load_time,
                    AVG(time_on_page) as avg_time_on_page,
                    AVG(scroll_depth) as avg_scroll_depth,
                    COUNT(*) as total_views,
                    COUNT(CASE WHEN load_time > 3 THEN 1 END) as slow_pages
                FROM page_views
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if page_url:
                query += " AND page_url = $3"
                params.append(page_url)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    total_views = result[4]
                    slow_pages = result[5]

                    return {
                        "avg_load_time": float(result[0]) if result[0] else 0,
                        "avg_time_on_page": float(result[1]) if result[1] else 0,
                        "avg_scroll_depth": float(result[2]) if result[2] else 0,
                        "total_views": total_views,
                        "slow_pages": slow_pages,
                        "slow_page_rate": (slow_pages / total_views)
                        if total_views > 0
                        else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get page performance metrics: {e}")
            return {}

    async def _save_page_view(self, page_view: PageView) -> None:
        """Save page view to database."""
        try:
            query = """
                INSERT INTO page_views (
                    id, user_id, tenant_id, session_id, page_url, page_title,
                    referrer, user_agent, ip_address, device_type, browser,
                    screen_resolution, load_time, timestamp, clicks, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            """

            params = [
                page_view.id,
                page_view.user_id,
                page_view.tenant_id,
                page_view.session_id,
                page_view.page_url,
                page_view.page_title,
                page_view.referrer,
                page_view.user_agent,
                page_view.ip_address,
                page_view.device_type,
                page_view.browser,
                page_view.screen_resolution,
                page_view.load_time,
                page_view.timestamp,
                page_view.clicks,
                page_view.created_at,
                page_view.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save page view: {e}")

    async def _save_user_action(self, action: UserAction) -> None:
        """Save user action to database."""
        try:
            query = """
                INSERT INTO user_actions (
                    id, user_id, tenant_id, session_id, page_url, action_type, action_name,
                    element_selector, element_text, element_attributes, coordinates,
                    timestamp, duration_ms, success, error_message, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """

            params = [
                action.id,
                action.user_id,
                action.tenant_id,
                action.session_id,
                action.page_url,
                action.action_type,
                action.action_name,
                action.element_selector,
                action.element_text,
                action.element_attributes,
                action.coordinates,
                action.timestamp,
                action.duration_ms,
                action.success,
                action.error_message,
                action.metadata,
                action.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save user action: {e}")

    async def _save_conversion_event(self, conversion: ConversionEvent) -> None:
        """Save conversion event to database."""
        try:
            query = """
                INSERT INTO conversion_events (
                    id, user_id, tenant_id, session_id, event_type, event_name,
                    page_url, conversion_value, conversion_currency, funnel_step,
                    funnel_name, properties, timestamp, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """

            params = [
                conversion.id,
                conversion.user_id,
                conversion.tenant_id,
                conversion.session_id,
                conversion.event_type,
                conversion.event_name,
                conversion.page_url,
                conversion.conversion_value,
                conversion.conversion_currency,
                conversion.funnel_step,
                conversion.funnel_name,
                conversion.properties,
                conversion.timestamp,
                conversion.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save conversion event: {e}")

    async def _save_funnel_analysis(self, funnel: FunnelAnalysis) -> None:
        """Save funnel analysis to database."""
        try:
            query = """
                INSERT INTO funnel_analyses (
                    id, tenant_id, funnel_name, total_users, step_analytics,
                    conversion_rate, abandonment_rate, avg_time_to_convert, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """

            params = [
                funnel.id,
                funnel.tenant_id,
                funnel.funnel_name,
                funnel.total_users,
                funnel.step_analytics,
                funnel.conversion_rate,
                funnel.abandonment_rate,
                funnel.avg_time_to_convert,
                funnel.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save funnel analysis: {e}")


# Factory function
def create_ui_analytics_manager(db_pool) -> UIAnalyticsManager:
    """Create UI analytics manager instance."""
    return UIAnalyticsManager(db_pool)
