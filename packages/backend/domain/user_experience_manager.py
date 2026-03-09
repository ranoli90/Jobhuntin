"""
User Experience Manager for Phase 14.1 User Experience
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.user_experience_manager")


@dataclass
class UserSession:
    """User session tracking data."""

    id: str
    user_id: str
    tenant_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    device_type: str = "web"
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    landing_page: Optional[str] = None
    exit_page: Optional[str] = None
    pages_visited: List[str] = field(default_factory=list)
    actions_performed: int = 0
    is_active: bool = True
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class UserJourney:
    """User journey mapping data."""

    id: str
    user_id: str
    tenant_id: str
    journey_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    completion_rate: float = 0.0
    conversion_events: List[Dict[str, Any]] = field(default_factory=list)
    abandonment_point: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class UXScore:
    """User experience score data."""

    id: str
    user_id: str
    tenant_id: str
    session_id: str
    overall_score: float
    usability_score: float
    performance_score: float
    accessibility_score: float
    engagement_score: float
    satisfaction_score: float
    factors: Dict[str, float] = field(default_factory=dict)
    calculated_at: datetime = datetime.now(timezone.utc)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class UserAction:
    """User action tracking data."""

    id: str
    user_id: str
    tenant_id: str
    session_id: str
    action_type: str
    action_name: str
    page_url: str
    element_selector: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = datetime.now(timezone.utc)
    duration_seconds: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)


class UserExperienceManager:
    """Advanced user experience management system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._active_sessions: Dict[str, UserSession] = {}
        self._journey_templates = self._initialize_journey_templates()
        self._ux_score_weights = {
            "usability": 0.3,
            "performance": 0.25,
            "accessibility": 0.15,
            "engagement": 0.2,
            "satisfaction": 0.1,
        }

    async def track_user_session(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        device_type: str = "web",
        browser: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        landing_page: Optional[str] = None,
    ) -> UserSession:
        """Track a new user session."""
        try:
            # End any existing active session for this user
            await self._end_active_sessions(user_id, tenant_id)

            # Create new session
            session = UserSession(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                start_time=datetime.now(timezone.utc),
                device_type=device_type,
                browser=browser,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                landing_page=landing_page,
                pages_visited=[landing_page] if landing_page else [],
            )

            # Save to database
            await self._save_session(session)

            # Track in memory
            self._active_sessions[session_id] = session

            logger.info(f"Started user session: {session_id} for user {user_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to track user session: {e}")
            raise

    async def track_page_view(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        page_url: str,
        page_title: Optional[str] = None,
        referrer: Optional[str] = None,
        load_time: Optional[float] = None,
    ) -> UserSession:
        """Track a page view within a session."""
        try:
            # Get session
            session = await self._get_session_by_session_id(session_id, tenant_id)
            if not session:
                # Create new session if not found
                session = await self.track_user_session(user_id, tenant_id, session_id)

            # Update session
            if page_url not in session.pages_visited:
                session.pages_visited.append(page_url)

            session.exit_page = page_url
            session.actions_performed += 1
            session.updated_at = datetime.now(timezone.utc)

            # Save to database
            await self._save_session(session)

            # Update memory
            if session_id in self._active_sessions:
                self._active_sessions[session_id] = session

            logger.info(f"Tracked page view: {page_url} for session {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to track page view: {e}")
            raise

    async def track_user_action(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        action_type: str,
        action_name: str,
        page_url: str,
        element_selector: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_seconds: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> UserAction:
        """Track a user action within a session."""
        try:
            # Create action record
            action = UserAction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                action_type=action_type,
                action_name=action_name,
                page_url=page_url,
                element_selector=element_selector,
                metadata=metadata or {},
                duration_seconds=duration_seconds,
                success=success,
                error_message=error_message,
            )

            # Save to database
            await self._save_action(action)

            # Update session
            session = await self._get_session_by_session_id(session_id, tenant_id)
            if session:
                session.actions_performed += 1
                session.updated_at = datetime.now(timezone.utc)
                await self._save_session(session)

                if session_id in self._active_sessions:
                    self._active_sessions[session_id] = session

            logger.info(f"Tracked user action: {action_name} for session {session_id}")
            return action

        except Exception as e:
            logger.error(f"Failed to track user action: {e}")
            raise

    async def calculate_ux_score(
        self,
        user_id: str,
        tenant_id: str,
        session_id: Optional[str] = None,
        time_period_hours: int = 24,
    ) -> List[UXScore]:
        """Calculate UX scores for user sessions."""
        try:
            # Get sessions within time period
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            query = """
                SELECT * FROM user_sessions
                WHERE user_id = $1 AND tenant_id = $2
                AND created_at > $3
                ORDER BY created_at DESC
            """

            params = [user_id, tenant_id, cutoff_time]

            if session_id:
                query += " AND session_id = $4"
                params.append(session_id)

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                scores = []
                for row in results:
                    session_data = self._row_to_session(row)
                    score = await self._calculate_session_ux_score(session_data)
                    scores.append(score)

                return scores

        except Exception as e:
            logger.error(f"Failed to calculate UX scores: {e}")
            return []

    async def get_user_journey(
        self,
        user_id: str,
        tenant_id: str,
        journey_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[UserJourney]:
        """Get user journey data."""
        try:
            query = """
                SELECT * FROM user_journeys
                WHERE user_id = $1 AND tenant_id = $2
            """
            params: list[Any] = [user_id, tenant_id]

            if journey_name:
                query += " AND journey_name = $3"
                params.append(journey_name)

            query += " ORDER BY created_at DESC LIMIT $4"
            params.append(limit)

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                journeys = []
                for row in results:
                    journey = self._row_to_journey(row)
                    journeys.append(journey)

                return journeys

        except Exception as e:
            logger.error(f"Failed to get user journey: {e}")
            return []

    async def get_ux_insights(
        self,
        tenant_id: str,
        time_period_days: int = 7,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive UX insights."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get session statistics
            session_stats = await self._get_session_statistics(
                tenant_id, cutoff_time, user_id
            )

            # Get action statistics
            action_stats = await self._get_action_statistics(
                tenant_id, cutoff_time, user_id
            )

            # Get journey statistics
            journey_stats = await self._get_journey_statistics(
                tenant_id, cutoff_time, user_id
            )

            # Get UX score statistics
            score_stats = await self._get_ux_score_statistics(
                tenant_id, cutoff_time, user_id
            )

            insights = {
                "session_statistics": session_stats,
                "action_statistics": action_stats,
                "journey_statistics": journey_stats,
                "ux_score_statistics": score_stats,
                "time_period_days": time_period_days,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return insights

        except Exception as e:
            logger.error(f"Failed to get UX insights: {e}")
            return {}

    async def end_session(
        self,
        session_id: str,
        tenant_id: str,
        end_reason: str = "manual",
    ) -> UserSession:
        """End a user session."""
        try:
            # Get session
            session = await self._get_session_by_session_id(session_id, tenant_id)
            if not session:
                raise Exception(f"Session {session_id} not found")

            # End session
            session.end_time = datetime.now(timezone.utc)
            session.duration_seconds = int(
                (session.end_time - session.start_time).total_seconds()
            )
            session.is_active = False
            session.updated_at = datetime.now(timezone.utc)

            # Save to database
            await self._save_session(session)

            # Remove from active sessions
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]

            logger.info(f"Ended session: {session_id} (reason: {end_reason})")
            return session

        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            raise

    async def _calculate_session_ux_score(self, session: UserSession) -> UXScore:
        """Calculate UX score for a session."""
        try:
            # Get session actions
            actions = await self._get_session_actions(session.id)

            # Calculate individual scores
            usability_score = await self._calculate_usability_score(session, actions)
            performance_score = await self._calculate_performance_score(
                session, actions
            )
            accessibility_score = await self._calculate_accessibility_score(
                session, actions
            )
            engagement_score = await self._calculate_engagement_score(session, actions)
            satisfaction_score = await self._calculate_satisfaction_score(
                session, actions
            )

            # Calculate overall score
            overall_score = (
                usability_score * self._ux_score_weights["usability"]
                + performance_score * self._ux_score_weights["performance"]
                + accessibility_score * self._ux_score_weights["accessibility"]
                + engagement_score * self._ux_score_weights["engagement"]
                + satisfaction_score * self._ux_score_weights["satisfaction"]
            )

            # Create UX score
            ux_score = UXScore(
                id=str(uuid.uuid4()),
                user_id=session.user_id,
                tenant_id=session.tenant_id,
                session_id=session.session_id,
                overall_score=overall_score,
                usability_score=usability_score,
                performance_score=performance_score,
                accessibility_score=accessibility_score,
                engagement_score=engagement_score,
                satisfaction_score=satisfaction_score,
                factors={
                    "pages_visited": len(session.pages_visited),
                    "actions_performed": session.actions_performed,
                    "session_duration": session.duration_seconds or 0,
                },
            )

            await self._save_ux_score(ux_score)

            return ux_score

        except Exception as e:
            logger.error(f"Failed to calculate UX score: {e}")
            raise

    async def _calculate_usability_score(
        self, session: UserSession, actions: List[UserAction]
    ) -> float:
        """Calculate usability score."""
        try:
            # Base score from session duration and actions
            duration_score = min(
                1.0, (session.duration_seconds or 0) / 300
            )  # 5 minutes = full score
            action_score = min(1.0, len(actions) / 10)  # 10 actions = full score

            # Error rate penalty
            error_rate = len([a for a in actions if not a.success]) / max(
                len(actions), 1
            )
            error_penalty = error_rate * 0.3

            # Page variety bonus
            page_variety = min(
                1.0, len(session.pages_visited) / 5
            )  # 5 pages = full score

            usability_score = (
                duration_score * 0.3 + action_score * 0.4 + page_variety * 0.3
            ) - error_penalty

            return max(0.0, min(1.0, usability_score))

        except Exception as e:
            logger.error(f"Failed to calculate usability score: {e}")
            return 0.5  # Default score

    async def _calculate_performance_score(
        self, session: UserSession, actions: List[UserAction]
    ) -> float:
        """Calculate performance score."""
        try:
            # Average action duration
            durations = [
                a.duration_seconds for a in actions if a.duration_seconds is not None
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0

            # Performance score based on action speed
            duration_score = max(0.0, 1.0 - (avg_duration / 10))  # 10 seconds = 0 score

            # Error rate penalty
            error_rate = len([a for a in actions if not a.success]) / max(
                len(actions), 1
            )
            error_penalty = error_rate * 0.5

            performance_score = duration_score - error_penalty

            return max(0.0, min(1.0, performance_score))

        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return 0.5  # Default score

    async def _calculate_accessibility_score(
        self, session: UserSession, actions: List[UserAction]
    ) -> float:
        """Calculate accessibility score."""
        try:
            # Check for accessibility-related actions
            accessibility_actions = [
                a for a in actions if "accessibility" in a.action_name.lower()
            ]

            # Base score
            base_score = 0.7  # Default score

            # Bonus for accessibility actions
            accessibility_bonus = min(0.3, len(accessibility_actions) * 0.1)

            # Device type consideration
            device_bonus = 0.1 if session.device_type == "mobile" else 0.0

            accessibility_score = base_score + accessibility_bonus + device_bonus

            return min(1.0, accessibility_score)

        except Exception as e:
            logger.error(f"Failed to calculate accessibility score: {e}")
            return 0.7  # Default score

    async def _calculate_engagement_score(
        self, session: UserSession, actions: List[UserAction]
    ) -> float:
        """Calculate engagement score."""
        try:
            # Engagement based on actions and time
            action_density = len(actions) / max(
                (session.duration_seconds or 1) / 60, 1
            )  # Actions per minute
            page_engagement = len(session.pages_visited) / max(
                session.actions_performed, 1
            )

            # Calculate engagement score
            engagement_score = min(
                1.0, (action_density / 2) * 0.6 + page_engagement * 0.4
            )

            return max(0.0, engagement_score)

        except Exception as e:
            logger.error(f"Failed to calculate engagement score: {e}")
            return 0.5  # Default score

    async def _calculate_satisfaction_score(
        self, session: UserSession, actions: List[UserAction]
    ) -> float:
        """Calculate satisfaction score."""
        try:
            # Check for satisfaction-related actions
            [
                a for a in actions if "satisfaction" in a.action_name.lower()
            ]

            # Base score
            base_score = 0.8  # Default score

            # Bonus for positive actions
            positive_actions = [
                a
                for a in actions
                if a.action_name in ["like", "share", "bookmark", "favorite"]
            ]
            positive_bonus = min(0.2, len(positive_actions) * 0.05)

            # Penalty for negative actions
            negative_actions = [
                a for a in actions if a.action_name in ["dislike", "complain", "report"]
            ]
            negative_penalty = min(0.3, len(negative_actions) * 0.1)

            satisfaction_score = base_score + positive_bonus - negative_penalty

            return max(0.0, min(1.0, satisfaction_score))

        except Exception as e:
            logger.error(f"Failed to calculate satisfaction score: {e}")
            return 0.8  # Default score

    def _initialize_journey_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize journey templates."""
        return {
            "job_application": {
                "name": "Job Application Journey",
                "steps": [
                    {"name": "search_jobs", "required": True},
                    {"name": "view_job_details", "required": True},
                    {"name": "apply_to_job", "required": True},
                    {"name": "upload_resume", "required": False},
                    {"name": "submit_application", "required": True},
                ],
                "conversion_events": ["submit_application"],
            },
            "onboarding": {
                "name": "User Onboarding Journey",
                "steps": [
                    {"name": "create_profile", "required": True},
                    {"name": "upload_resume", "required": True},
                    {"name": "set_preferences", "required": False},
                    {"name": "complete_onboarding", "required": True},
                ],
                "conversion_events": ["complete_onboarding"],
            },
            "job_search": {
                "name": "Job Search Journey",
                "steps": [
                    {"name": "search_jobs", "required": True},
                    {"name": "filter_results", "required": False},
                    {"name": "view_job_details", "required": True},
                    {"name": "save_job", "required": False},
                ],
                "conversion_events": ["save_job"],
            },
        }

    async def _get_session_by_session_id(
        self, session_id: str, tenant_id: str
    ) -> Optional[UserSession]:
        """Get session by session ID."""
        try:
            # Check memory first
            if session_id in self._active_sessions:
                return self._active_sessions[session_id]

            # Check database
            query = """
                SELECT * FROM user_sessions
                WHERE session_id = $1 AND tenant_id = $2 AND is_active = true
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, session_id, tenant_id)

                if result:
                    session = self._row_to_session(result)
                    self._active_sessions[session_id] = session
                    return session

                return None

        except Exception as e:
            logger.error(f"Failed to get session by session ID: {e}")
            return None

    async def _end_active_sessions(self, user_id: str, tenant_id: str) -> None:
        """End all active sessions for a user."""
        try:
            # Get active sessions for user
            query = """
                SELECT * FROM user_sessions
                WHERE user_id = $1 AND tenant_id = $2 AND is_active = true
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, user_id, tenant_id)

                for row in results:
                    session = self._row_to_session(row)
                    await self.end_session(session.session_id, tenant_id, "new_session")

        except Exception as e:
            logger.error(f"Failed to end active sessions: {e}")

    async def _get_session_actions(self, session_id: str) -> List[UserAction]:
        """Get all actions for a session."""
        try:
            query = """
                SELECT * FROM user_actions
                WHERE session_id = $1
                ORDER BY timestamp ASC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, session_id)

                actions = []
                for row in results:
                    action = UserAction(
                        id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        session_id=row[3],
                        action_type=row[4],
                        action_name=row[5],
                        page_url=row[6],
                        element_selector=row[7],
                        metadata=row[8] or {},
                        timestamp=row[9],
                        duration_seconds=row[10],
                        success=row[11],
                        error_message=row[12],
                        created_at=row[13],
                    )
                    actions.append(action)

                return actions

        except Exception as e:
            logger.error(f"Failed to get session actions: {e}")
            return []

    async def _get_session_statistics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get session statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN duration_seconds IS NOT NULL THEN 1 END) as completed_sessions,
                    AVG(duration_seconds) as avg_duration,
                    AVG(actions_performed) as avg_actions,
                    COUNT(CASE WHEN device_type = 'mobile' THEN 1 END) as mobile_sessions,
                    COUNT(CASE WHEN device_type = 'desktop' THEN 1 END) as desktop_sessions
                FROM user_sessions
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
                        "total_sessions": result[0],
                        "completed_sessions": result[1],
                        "avg_duration": float(result[2]) if result[2] else 0,
                        "avg_actions": float(result[3]) if result[3] else 0,
                        "mobile_sessions": result[4],
                        "desktop_sessions": result[5],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            return {}

    async def _get_action_statistics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get action statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_actions,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful_actions,
                    AVG(duration_seconds) as avg_duration,
                    COUNT(DISTINCT action_type) as unique_action_types
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
                    return {
                        "total_actions": result[0],
                        "successful_actions": result[1],
                        "avg_duration": float(result[2]) if result[2] else 0,
                        "unique_action_types": result[3],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get action statistics: {e}")
            return {}

    async def _get_journey_statistics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get journey statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_journeys,
                    COUNT(CASE WHEN completion_rate > 0.8 THEN 1 END) as successful_journeys,
                    AVG(completion_rate) as avg_completion_rate,
                    AVG(duration_seconds) as avg_duration
                FROM user_journeys
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
                        "total_journeys": result[0],
                        "successful_journeys": result[1],
                        "avg_completion_rate": float(result[2]) if result[2] else 0,
                        "avg_duration": float(result[3]) if result[3] else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get journey statistics: {e}")
            return {}

    async def _get_ux_score_statistics(
        self, tenant_id: str, cutoff_time: datetime, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get UX score statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_scores,
                    AVG(overall_score) as avg_overall_score,
                    AVG(usability_score) as avg_usability_score,
                    AVG(performance_score) as avg_performance_score,
                    AVG(accessibility_score) as avg_accessibility_score,
                    AVG(engagement_score) as avg_engagement_score,
                    AVG(satisfaction_score) as avg_satisfaction_score
                FROM ux_scores
                WHERE tenant_id = $1 AND calculated_at > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_scores": result[0],
                        "avg_overall_score": float(result[1]) if result[1] else 0,
                        "avg_usability_score": float(result[2]) if result[2] else 0,
                        "avg_performance_score": float(result[3]) if result[3] else 0,
                        "avg_accessibility_score": float(result[4]) if result[4] else 0,
                        "avg_engagement_score": float(result[5]) if result[5] else 0,
                        "avg_satisfaction_score": float(result[6]) if result[6] else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get UX score statistics: {e}")
            return {}

    def _row_to_session(self, row) -> UserSession:
        """Convert database row to UserSession."""
        return UserSession(
            id=row[0],
            user_id=row[1],
            tenant_id=row[2],
            session_id=row[3],
            start_time=row[4],
            end_time=row[5],
            duration_seconds=row[6],
            device_type=row[7],
            browser=row[8],
            ip_address=row[9],
            user_agent=row[10],
            referrer=row[11],
            landing_page=row[12],
            exit_page=row[13],
            pages_visited=row[14] or [],
            actions_performed=row[15],
            is_active=row[16],
            created_at=row[17],
            updated_at=row[18],
        )

    def _row_to_journey(self, row) -> UserJourney:
        """Convert database row to UserJourney."""
        return UserJourney(
            id=row[0],
            user_id=row[1],
            tenant_id=row[2],
            journey_name=row[3],
            start_time=row[4],
            end_time=row[5],
            duration_seconds=row[6],
            steps=row[7] or [],
            completion_rate=row[8],
            conversion_events=row[9] or [],
            abandonment_point=row[10],
            created_at=row[11],
            updated_at=row[12],
        )

    async def _save_session(self, session: UserSession) -> None:
        """Save session to database."""
        try:
            query = """
                INSERT INTO user_sessions (
                    id, user_id, tenant_id, session_id, start_time, end_time,
                    duration_seconds, device_type, browser, ip_address, user_agent,
                    referrer, landing_page, exit_page, pages_visited,
                    actions_performed, is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                ON CONFLICT (id) DO UPDATE SET
                    end_time = EXCLUDED.end_time,
                    duration_seconds = EXCLUDED.duration_seconds,
                    exit_page = EXCLUDED.exit_page,
                    pages_visited = EXCLUDED.pages_visited,
                    actions_performed = EXCLUDED.actions_performed,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                session.id,
                session.user_id,
                session.tenant_id,
                session.session_id,
                session.start_time,
                session.end_time,
                session.duration_seconds,
                session.device_type,
                session.browser,
                session.ip_address,
                session.user_agent,
                session.referrer,
                session.landing_page,
                session.exit_page,
                session.pages_visited,
                session.actions_performed,
                session.is_active,
                session.created_at,
                session.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    async def _save_action(self, action: UserAction) -> None:
        """Save action to database."""
        try:
            query = """
                INSERT INTO user_actions (
                    id, user_id, tenant_id, session_id, action_type, action_name,
                    page_url, element_selector, metadata, timestamp, duration_seconds,
                    success, error_message, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """

            params = [
                action.id,
                action.user_id,
                action.tenant_id,
                action.session_id,
                action.action_type,
                action.action_name,
                action.page_url,
                action.element_selector,
                action.metadata,
                action.timestamp,
                action.duration_seconds,
                action.success,
                action.error_message,
                action.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save action: {e}")

    async def _save_ux_score(self, ux_score: UXScore) -> None:
        """Save UX score to database."""
        try:
            query = """
                INSERT INTO ux_scores (
                    id, user_id, tenant_id, session_id, overall_score, usability_score,
                    performance_score, accessibility_score, engagement_score,
                    satisfaction_score, factors, calculated_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """

            params = [
                ux_score.id,
                ux_score.user_id,
                ux_score.tenant_id,
                ux_score.session_id,
                ux_score.overall_score,
                ux_score.usability_score,
                ux_score.performance_score,
                ux_score.accessibility_score,
                ux_score.engagement_score,
                ux_score.satisfaction_score,
                ux_score.factors,
                ux_score.calculated_at,
                ux_score.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save UX score: {e}")


# Factory function
def create_user_experience_manager(db_pool) -> UserExperienceManager:
    """Create user experience manager instance."""
    return UserExperienceManager(db_pool)
