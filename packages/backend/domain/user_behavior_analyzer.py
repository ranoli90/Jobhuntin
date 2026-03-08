"""
User Behavior Analyzer for Phase 14.1 User Experience
"""

from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict

from shared.logging_config import get_logger

logger = get_logger("sorce.user_behavior_analyzer")


class BehaviorType(Enum):
    """Types of user behavior patterns."""

    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    CONVERSION = "conversion"
    RETENTION = "retention"
    ENGAGEMENT = "engagement"
    FRUSTRATION = "frustration"
    EFFICIENCY = "efficiency"
    EXPLORATION = "exploration"


class BehaviorPattern(Enum):
    """Specific behavior patterns."""

    LINEAR_NAVIGATION = "linear_navigation"
    NONLINEAR_NAVIGATION = "nonlinear_navigation"
    TASK_ORIENTED = "task_oriented"
    EXPLORATORY = "exploratory"
    POWER_USER = "power_user"
    CASUAL_USER = "casual_user"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    EFFICIENT = "efficient"
    INEFFICIENT = "inefficient"


@dataclass
class UserBehaviorProfile:
    """User behavior profile data."""

    id: str
    user_id: str
    tenant_id: str
    behavior_type: BehaviorType
    behavior_pattern: BehaviorPattern
    confidence_score: float
    characteristics: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    session_count: int = 0
    total_time_spent: int = 0
    last_updated: datetime = datetime.now(timezone.utc)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class BehaviorEvent:
    """User behavior event data."""

    id: str
    user_id: str
    tenant_id: str
    session_id: str
    event_type: str
    event_name: str
    page_url: str
    timestamp: datetime = datetime.now(timezone.utc)
    duration_ms: Optional[int] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class BehaviorAnalysis:
    """Behavior analysis results."""

    id: str
    tenant_id: str
    analysis_type: str
    period_days: int
    total_users: int
    behavior_patterns: Dict[str, int]
    behavior_metrics: Dict[str, float]
    insights: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = datetime.now(timezone.utc)


class UserBehaviorAnalyzer:
    """Advanced user behavior analysis system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._behavior_profiles: Dict[str, UserBehaviorProfile] = {}
        self._behavior_events: Dict[str, List[BehaviorEvent]] = {}
        self._analysis_cache: Dict[str, BehaviorAnalysis] = {}
        self._behavior_patterns = self._initialize_behavior_patterns()
        self._analysis_thresholds = self._initialize_analysis_thresholds()

        # Start background analysis task
        asyncio.create_task(self._start_background_analysis())

    async def track_behavior_event(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        event_type: str,
        event_name: str,
        page_url: str,
        duration_ms: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> BehaviorEvent:
        """Track a user behavior event."""
        try:
            # Create behavior event
            event = BehaviorEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                event_type=event_type,
                event_name=event_name,
                page_url=page_url,
                duration_ms=duration_ms,
                properties=properties or {},
                context=context or {},
            )

            # Save event
            await self._save_behavior_event(event)

            # Update cache
            if session_id not in self._behavior_events:
                self._behavior_events[session_id] = []
            self._behavior_events[session_id].append(event)

            # Trigger profile update if needed
            await self._trigger_profile_update(user_id, tenant_id)

            logger.info(f"Tracked behavior event: {event_name} for user {user_id}")
            return event

        except Exception as e:
            logger.error(f"Failed to track behavior event: {e}")
            raise

    async def analyze_user_behavior(
        self,
        user_id: str,
        tenant_id: str,
        time_period_days: int = 30,
    ) -> UserBehaviorProfile:
        """Analyze user behavior and create profile."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get user behavior events
            events = await self._get_user_behavior_events(
                user_id, tenant_id, cutoff_time
            )

            if not events:
                # Create default profile
                profile = UserBehaviorProfile(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tenant_id=tenant_id,
                    behavior_type=BehaviorType.NAVIGATION,
                    behavior_pattern=BehaviorPattern.CASUAL_USER,
                    confidence_score=0.5,
                    session_count=0,
                    total_time_spent=0,
                )
            else:
                # Analyze behavior patterns
                behavior_type, behavior_pattern = await self._analyze_behavior_patterns(
                    events
                )

                # Calculate metrics
                metrics = await self._calculate_behavior_metrics(events)

                # Determine characteristics
                characteristics = await self._determine_behavior_characteristics(events)

                # Calculate confidence score
                confidence_score = await self._calculate_confidence_score(
                    events, behavior_type, behavior_pattern
                )

                # Create profile
                profile = UserBehaviorProfile(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tenant_id=tenant_id,
                    behavior_type=behavior_type,
                    behavior_pattern=behavior_pattern,
                    confidence_score=confidence_score,
                    characteristics=characteristics,
                    metrics=metrics,
                    session_count=len(set(event.session_id for event in events)),
                    total_time_spent=sum(event.duration_ms or 0 for event in events),
                )

            # Save profile
            await self._save_behavior_profile(profile)

            # Update cache
            self._behavior_profiles[f"{user_id}:{tenant_id}"] = profile

            logger.info(
                f"Analyzed user behavior: {user_id} -> {behavior_pattern.value}"
            )
            return profile

        except Exception as e:
            logger.error(f"Failed to analyze user behavior: {e}")
            raise

    async def get_behavior_insights(
        self,
        tenant_id: str,
        time_period_days: int = 30,
        behavior_type: Optional[BehaviorType] = None,
        behavior_pattern: Optional[BehaviorPattern] = None,
    ) -> BehaviorAnalysis:
        """Get comprehensive behavior insights."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get behavior statistics
            stats = await self._get_behavior_statistics(
                tenant_id, cutoff_time, behavior_type, behavior_pattern
            )

            # Get pattern distribution
            pattern_dist = await self._get_pattern_distribution(
                tenant_id, cutoff_time, behavior_type
            )

            # Get behavior metrics
            metrics = await self._get_behavior_metrics_summary(
                tenant_id, cutoff_time, behavior_type
            )

            # Generate insights
            insights = await self._generate_behavior_insights(
                stats, pattern_dist, metrics
            )

            # Generate recommendations
            recommendations = await self._generate_behavior_recommendations(
                insights, pattern_dist
            )

            # Create analysis
            analysis = BehaviorAnalysis(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                analysis_type="comprehensive_analysis",
                period_days=time_period_days,
                total_users=stats.get("total_users", 0),
                behavior_patterns=pattern_dist,
                behavior_metrics=metrics,
                insights=insights,
                recommendations=recommendations,
                created_at=datetime.now(timezone.utc),
            )

            # Save analysis
            await self._save_behavior_analysis(analysis)

            # Update cache
            cache_key = (
                f"{tenant_id}:{time_period_days}:{behavior_type}:{behavior_pattern}"
            )
            self._analysis_cache[cache_key] = analysis

            return analysis

        except Exception as e:
            logger.error(f"Failed to get behavior insights: {e}")
            raise

    async def get_user_behavior_trends(
        self,
        user_id: str,
        tenant_id: str,
        time_period_days: int = 30,
    ) -> Dict[str, Any]:
        """Get user behavior trends over time."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get behavior events
            events = await self._get_user_behavior_events(
                user_id, tenant_id, cutoff_time
            )

            # Group events by day
            daily_events = defaultdict(list)
            for event in events:
                day_key = event.timestamp.date()
                daily_events[day_key].append(event)

            # Calculate daily metrics
            daily_metrics = []
            for day, day_events in sorted(daily_events.items()):
                day_metrics = {
                    "date": day.isoformat(),
                    "event_count": len(day_events),
                    "total_duration": sum(
                        event.duration_ms or 0 for event in day_events
                    ),
                    "unique_pages": len(set(event.page_url for event in day_events)),
                    "avg_session_time": self._calculate_avg_session_time(day_events),
                }
                daily_metrics.append(day_metrics)

            # Calculate trends
            trends = {
                "daily_metrics": daily_metrics,
                "overall_trend": self._calculate_overall_trend(daily_metrics),
                "peak_activity_day": self._find_peak_activity_day(daily_metrics),
                "behavior_consistency": self._calculate_behavior_consistency(
                    daily_metrics
                ),
            }

            return trends

        except Exception as e:
            logger.error(f"Failed to get user behavior trends: {e}")
            return {}

    async def get_behavior_segments(
        self,
        tenant_id: str,
        time_period_days: int = 30,
    ) -> Dict[str, Any]:
        """Get user behavior segments."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get all user profiles
            profiles = await self._get_all_behavior_profiles(tenant_id, cutoff_time)

            # Segment users by behavior pattern
            segments = defaultdict(list)
            for profile in profiles:
                segments[profile.behavior_pattern.value].append(profile)

            # Calculate segment metrics
            segment_metrics = {}
            for pattern, segment_profiles in segments.items():
                metrics = {
                    "user_count": len(segment_profiles),
                    "avg_confidence": sum(p.confidence_score for p in segment_profiles)
                    / len(segment_profiles),
                    "avg_session_count": sum(p.session_count for p in segment_profiles)
                    / len(segment_profiles),
                    "avg_time_spent": sum(p.total_time_spent for p in segment_profiles)
                    / len(segment_profiles),
                    "characteristics": self._aggregate_characteristics(
                        segment_profiles
                    ),
                }
                segment_metrics[pattern] = metrics

            # Calculate segment distribution
            total_users = len(profiles)
            segment_distribution = {
                pattern: {
                    "count": len(segment_profiles),
                    "percentage": (len(segment_profiles) / total_users) * 100,
                    "metrics": segment_metrics[pattern],
                }
                for pattern, segment_profiles in segments.items()
            }

            return {
                "total_users": total_users,
                "segments": segment_distribution,
                "dominant_pattern": max(
                    segment_distribution.keys(),
                    key=lambda x: segment_distribution[x]["count"],
                ),
                "segment_insights": await self._generate_segment_insights(
                    segment_distribution
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get behavior segments: {e}")
            return {}

    def _initialize_behavior_patterns(self) -> Dict[BehaviorPattern, Dict[str, Any]]:
        """Initialize behavior pattern definitions."""
        return {
            BehaviorPattern.LINEAR_NAVIGATION: {
                "description": "Users who navigate through pages in a linear, predictable manner",
                "characteristics": [
                    "sequential_page_visits",
                    "low_bounce_rate",
                    "task_completion",
                ],
                "metrics": [
                    "page_sequence_consistency",
                    "navigation_efficiency",
                    "goal_completion_rate",
                ],
            },
            BehaviorPattern.NONLINEAR_NAVIGATION: {
                "description": "Users who navigate in a non-linear, exploratory manner",
                "characteristics": [
                    "random_page_visits",
                    "high_exploration",
                    "multiple_entry_points",
                ],
                "metrics": [
                    "exploration_rate",
                    "page_diversity",
                    "return_visit_frequency",
                ],
            },
            BehaviorPattern.TASK_ORIENTED: {
                "description": "Users focused on completing specific tasks efficiently",
                "characteristics": [
                    "goal_directed",
                    "minimal_exploration",
                    "quick_completion",
                ],
                "metrics": [
                    "task_completion_time",
                    "efficiency_score",
                    "goal_success_rate",
                ],
            },
            BehaviorPattern.EXPLORATORY: {
                "description": "Users who explore the platform extensively",
                "characteristics": [
                    "high_page_diversity",
                    "long_sessions",
                    "feature_discovery",
                ],
                "metrics": [
                    "exploration_score",
                    "feature_usage_diversity",
                    "session_duration",
                ],
            },
            BehaviorPattern.POWER_USER: {
                "description": "Advanced users with deep platform knowledge",
                "characteristics": [
                    "advanced_feature_usage",
                    "high_engagement",
                    "frequent_visits",
                ],
                "metrics": [
                    "feature_adoption_rate",
                    "engagement_score",
                    "visit_frequency",
                ],
            },
            BehaviorPattern.CASUAL_USER: {
                "description": "Users with basic, occasional platform usage",
                "characteristics": [
                    "basic_feature_usage",
                    "infrequent_visits",
                    "short_sessions",
                ],
                "metrics": [
                    "usage_frequency",
                    "session_duration",
                    "feature_usage_breadth",
                ],
            },
            BehaviorPattern.FRUSTRATED: {
                "description": "Users showing signs of frustration",
                "characteristics": [
                    "high_error_rate",
                    "repeated_actions",
                    "abandoned_sessions",
                ],
                "metrics": [
                    "error_frequency",
                    "action_repetition",
                    "session_abandonment_rate",
                ],
            },
            BehaviorPattern.SATISFIED: {
                "description": "Users showing high satisfaction",
                "characteristics": [
                    "low_error_rate",
                    "smooth_navigation",
                    "goal_completion",
                ],
                "metrics": ["success_rate", "navigation_smoothness", "completion_rate"],
            },
            BehaviorPattern.EFFICIENT: {
                "description": "Users who complete tasks efficiently",
                "characteristics": [
                    "quick_task_completion",
                    "minimal_clicks",
                    "direct_navigation",
                ],
                "metrics": [
                    "efficiency_score",
                    "task_completion_time",
                    "click_efficiency",
                ],
            },
            BehaviorPattern.INEFFICIENT: {
                "description": "Users who struggle with task completion",
                "characteristics": [
                    "long_task_completion",
                    "excessive_clicks",
                    "navigation_errors",
                ],
                "metrics": ["inefficiency_score", "task_completion_time", "error_rate"],
            },
        }

    def _initialize_analysis_thresholds(self) -> Dict[str, float]:
        """Initialize analysis thresholds."""
        return {
            "min_events_for_analysis": 10,
            "min_sessions_for_profile": 3,
            "confidence_threshold": 0.7,
            "behavior_change_threshold": 0.3,
            "segment_size_threshold": 5,
        }

    async def _start_background_analysis(self) -> None:
        """Start background analysis task."""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour
                await self._perform_background_analysis()

        except Exception as e:
            logger.error(f"Background analysis task failed: {e}")

    async def _perform_background_analysis(self) -> None:
        """Perform background analysis of user behavior."""
        try:
            # Get active tenants
            tenants = await self._get_active_tenants()

            for tenant_id in tenants:
                try:
                    # Analyze recent behavior
                    await self.analyze_tenant_behavior(tenant_id)

                except Exception as e:
                    logger.error(f"Failed to analyze tenant {tenant_id}: {e}")

        except Exception as e:
            logger.error(f"Background analysis failed: {e}")

    async def _analyze_behavior_patterns(
        self,
        events: List[BehaviorEvent],
    ) -> Tuple[BehaviorType, BehaviorPattern]:
        """Analyze behavior patterns from events."""
        try:
            # Calculate pattern scores
            pattern_scores = {}

            for pattern in BehaviorPattern:
                score = await self._calculate_pattern_score(events, pattern)
                pattern_scores[pattern] = score

            # Find best pattern
            best_pattern = max(pattern_scores.keys(), key=lambda x: pattern_scores[x])
            best_score = pattern_scores[best_pattern]

            # Determine behavior type
            behavior_type = self._determine_behavior_type(best_pattern)

            return behavior_type, best_pattern

        except Exception as e:
            logger.error(f"Failed to analyze behavior patterns: {e}")
            return BehaviorType.NAVIGATION, BehaviorPattern.CASUAL_USER

    async def _calculate_pattern_score(
        self,
        events: List[BehaviorEvent],
        pattern: BehaviorPattern,
    ) -> float:
        """Calculate score for a specific behavior pattern."""
        try:
            pattern_def = self._behavior_patterns[pattern]
            characteristics = pattern_def["characteristics"]

            score = 0.0
            total_checks = 0

            for characteristic in characteristics:
                if characteristic == "sequential_page_visits":
                    score += self._check_sequential_navigation(events)
                elif characteristic == "low_bounce_rate":
                    score += self._check_bounce_rate(events)
                elif characteristic == "task_completion":
                    score += self._check_task_completion(events)
                elif characteristic == "random_page_visits":
                    score += self._check_random_navigation(events)
                elif characteristic == "high_exploration":
                    score += self._check_exploration(events)
                elif characteristic == "goal_directed":
                    score += self._check_goal_directed(events)
                elif characteristic == "minimal_exploration":
                    score += self._check_minimal_exploration(events)
                elif characteristic == "quick_completion":
                    score += self._check_quick_completion(events)
                elif characteristic == "advanced_feature_usage":
                    score += self._check_advanced_features(events)
                elif characteristic == "basic_feature_usage":
                    score += self._check_basic_features(events)
                elif characteristic == "high_error_rate":
                    score += self._check_error_rate(events)
                elif characteristic == "low_error_rate":
                    score += self._check_low_error_rate(events)
                elif characteristic == "smooth_navigation":
                    score += self._check_smooth_navigation(events)
                elif characteristic == "minimal_clicks":
                    score += self._check_minimal_clicks(events)
                elif characteristic == "excessive_clicks":
                    score += self._check_excessive_clicks(events)

                total_checks += 1

            return score / total_checks if total_checks > 0 else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate pattern score: {e}")
            return 0.0

    def _determine_behavior_type(self, pattern: BehaviorPattern) -> BehaviorType:
        """Determine behavior type from pattern."""
        try:
            pattern_type_mapping = {
                BehaviorPattern.LINEAR_NAVIGATION: BehaviorType.NAVIGATION,
                BehaviorPattern.NONLINEAR_NAVIGATION: BehaviorType.NAVIGATION,
                BehaviorPattern.TASK_ORIENTED: BehaviorType.CONVERSION,
                BehaviorPattern.EXPLORATORY: BehaviorType.EXPLORATION,
                BehaviorPattern.POWER_USER: BehaviorType.ENGAGEMENT,
                BehaviorPattern.CASUAL_USER: BehaviorType.ENGAGEMENT,
                BehaviorPattern.FRUSTRATED: BehaviorType.FRUSTRATION,
                BehaviorPattern.SATISFIED: BehaviorType.ENGAGEMENT,
                BehaviorPattern.EFFICIENT: BehaviorType.EFFICIENCY,
                BehaviorPattern.INEFFICIENT: BehaviorType.FRUSTRATION,
            }

            return pattern_type_mapping.get(pattern, BehaviorType.NAVIGATION)

        except Exception as e:
            logger.error(f"Failed to determine behavior type: {e}")
            return BehaviorType.NAVIGATION

    async def _calculate_behavior_metrics(
        self, events: List[BehaviorEvent]
    ) -> Dict[str, float]:
        """Calculate behavior metrics from events."""
        try:
            metrics = {}

            # Basic metrics
            metrics["total_events"] = len(events)
            metrics["unique_pages"] = len(set(event.page_url for event in events))
            metrics["total_duration"] = sum(event.duration_ms or 0 for event in events)
            metrics["avg_event_duration"] = (
                metrics["total_duration"] / len(events) if events else 0
            )

            # Navigation metrics
            metrics["navigation_efficiency"] = self._calculate_navigation_efficiency(
                events
            )
            metrics["exploration_score"] = self._calculate_exploration_score(events)
            metrics["bounce_rate"] = self._calculate_bounce_rate(events)

            # Engagement metrics
            metrics["engagement_score"] = self._calculate_engagement_score(events)
            metrics["session_frequency"] = self._calculate_session_frequency(events)
            metrics["feature_usage_diversity"] = self._calculate_feature_diversity(
                events
            )

            # Performance metrics
            metrics["error_rate"] = self._calculate_error_rate(events)
            metrics["success_rate"] = self._calculate_success_rate(events)
            metrics["efficiency_score"] = self._calculate_efficiency_score(events)

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate behavior metrics: {e}")
            return {}

    async def _determine_behavior_characteristics(
        self,
        events: List[BehaviorEvent],
    ) -> Dict[str, Any]:
        """Determine behavior characteristics from events."""
        try:
            characteristics = {}

            # Navigation characteristics
            characteristics["navigation_pattern"] = self._analyze_navigation_pattern(
                events
            )
            characteristics["page_preferences"] = self._analyze_page_preferences(events)
            characteristics["time_patterns"] = self._analyze_time_patterns(events)

            # Interaction characteristics
            characteristics["interaction_style"] = self._analyze_interaction_style(
                events
            )
            characteristics["feature_usage"] = self._analyze_feature_usage(events)
            characteristics["device_usage"] = self._analyze_device_usage(events)

            # Behavioral characteristics
            characteristics["goal_orientation"] = self._analyze_goal_orientation(events)
            characteristics["exploration_tendency"] = (
                self._analyze_exploration_tendency(events)
            )
            characteristics["frustration_indicators"] = (
                self._analyze_frustration_indicators(events)
            )

            return characteristics

        except Exception as e:
            logger.error(f"Failed to determine behavior characteristics: {e}")
            return {}

    async def _calculate_confidence_score(
        self,
        events: List[BehaviorEvent],
        behavior_type: BehaviorType,
        behavior_pattern: BehaviorPattern,
    ) -> float:
        """Calculate confidence score for behavior analysis."""
        try:
            # Base confidence from event count
            event_confidence = min(1.0, len(events) / 50)  # 50 events = full confidence

            # Pattern consistency confidence
            pattern_confidence = await self._calculate_pattern_consistency(
                events, behavior_pattern
            )

            # Time period confidence
            time_confidence = self._calculate_time_confidence(events)

            # Overall confidence
            overall_confidence = (
                event_confidence + pattern_confidence + time_confidence
            ) / 3

            return min(1.0, max(0.0, overall_confidence))

        except Exception as e:
            logger.error(f"Failed to calculate confidence score: {e}")
            return 0.5

    def _check_sequential_navigation(self, events: List[BehaviorEvent]) -> float:
        """Check for sequential navigation pattern."""
        try:
            if len(events) < 2:
                return 0.0

            # Calculate page transition consistency
            transitions = []
            for i in range(len(events) - 1):
                if (
                    events[i].event_type == "page_view"
                    and events[i + 1].event_type == "page_view"
                ):
                    transitions.append((events[i].page_url, events[i + 1].page_url))

            # Check for common transitions
            common_transitions = {}
            for transition in transitions:
                common_transitions[transition] = (
                    common_transitions.get(transition, 0) + 1
                )

            # Calculate consistency score
            if not transitions:
                return 0.0

            most_common = max(common_transitions.values())
            consistency = most_common / len(transitions)

            return min(1.0, consistency * 2)  # Scale up for better scoring

        except Exception as e:
            logger.error(f"Failed to check sequential navigation: {e}")
            return 0.0

    def _check_bounce_rate(self, events: List[BehaviorEvent]) -> float:
        """Check for low bounce rate."""
        try:
            # Group events by session
            sessions = defaultdict(list)
            for event in events:
                sessions[event.session_id].append(event)

            # Calculate bounce rate
            single_page_sessions = 0
            for session_events in sessions.values():
                unique_pages = len(set(event.page_url for event in session_events))
                if unique_pages == 1:
                    single_page_sessions += 1

            if not sessions:
                return 0.0

            bounce_rate = single_page_sessions / len(sessions)

            # Return low bounce rate score (inverse of bounce rate)
            return 1.0 - bounce_rate

        except Exception as e:
            logger.error(f"Failed to check bounce rate: {e}")
            return 0.0

    def _check_task_completion(self, events: List[BehaviorEvent]) -> float:
        """Check for task completion."""
        try:
            # Look for completion events
            completion_events = [
                event
                for event in events
                if event.event_type == "conversion"
                or "complete" in event.event_name.lower()
            ]

            if not events:
                return 0.0

            completion_rate = len(completion_events) / len(events)

            return min(1.0, completion_rate * 5)  # Scale up for better scoring

        except Exception as e:
            logger.error(f"Failed to check task completion: {e}")
            return 0.0

    def _check_random_navigation(self, events: List[BehaviorEvent]) -> float:
        """Check for random navigation pattern."""
        try:
            if len(events) < 3:
                return 0.0

            # Calculate page transition randomness
            page_views = [event for event in events if event.event_type == "page_view"]

            if len(page_views) < 3:
                return 0.0

            # Check for repeated visits to same pages
            page_counts = defaultdict(int)
            for event in page_views:
                page_counts[event.page_url] += 1

            # Calculate diversity score
            unique_pages = len(page_counts)
            total_views = len(page_views)

            diversity = unique_pages / total_views

            return diversity

        except Exception as e:
            logger.error(f"Failed to check random navigation: {e}")
            return 0.0

    def _check_exploration(self, events: List[BehaviorEvent]) -> float:
        """Check for high exploration."""
        try:
            # Calculate exploration metrics
            unique_pages = len(set(event.page_url for event in events))
            unique_events = len(set(event.event_name for event in events))

            # Calculate exploration score
            exploration_score = (unique_pages + unique_events) / (2 * len(events))

            return min(1.0, exploration_score * 2)  # Scale up for better scoring

        except Exception as e:
            logger.error(f"Failed to check exploration: {e}")
            return 0.0

    def _check_goal_directed(self, events: List[BehaviorEvent]) -> float:
        """Check for goal-directed behavior."""
        try:
            # Look for goal-related events
            goal_events = [
                event
                for event in events
                if "goal" in event.event_name.lower()
                or "target" in event.event_name.lower()
            ]

            if not events:
                return 0.0

            goal_rate = len(goal_events) / len(events)

            return min(1.0, goal_rate * 3)  # Scale up for better scoring

        except Exception as e:
            logger.error(f"Failed to check goal-directed behavior: {e}")
            return 0.0

    def _check_minimal_exploration(self, events: List[BehaviorEvent]) -> float:
        """Check for minimal exploration."""
        try:
            # Calculate exploration metrics
            unique_pages = len(set(event.page_url for event in events))

            # Minimal exploration = low page diversity
            if len(events) == 0:
                return 0.0

            exploration_ratio = unique_pages / len(events)

            # Return inverse score (low exploration = high score for this pattern)
            return 1.0 - exploration_ratio

        except Exception as e:
            logger.error(f"Failed to check minimal exploration: {e}")
            return 0.0

    def _check_quick_completion(self, events: List[BehaviorEvent]) -> float:
        """Check for quick task completion."""
        try:
            # Calculate average session duration
            sessions = defaultdict(list)
            for event in events:
                sessions[event.session_id].append(event)

            if not sessions:
                return 0.0

            session_durations = []
            for session_events in sessions.values():
                if len(session_events) >= 2:
                    start_time = min(event.timestamp for event in session_events)
                    end_time = max(event.timestamp for event in session_events)
                    duration = (end_time - start_time).total_seconds()
                    session_durations.append(duration)

            if not session_durations:
                return 0.0

            avg_duration = sum(session_durations) / len(session_durations)

            # Quick completion = short sessions (under 2 minutes)
            quick_completion_rate = len(
                [d for d in session_durations if d < 120]
            ) / len(session_durations)

            return quick_completion_rate

        except Exception as e:
            logger.error(f"Failed to check quick completion: {e}")
            return 0.0

    def _check_advanced_features(self, events: List[BehaviorEvent]) -> float:
        """Check for advanced feature usage."""
        try:
            # Define advanced features
            advanced_features = [
                "export",
                "import",
                "analytics",
                "settings",
                "admin",
                "advanced",
                "custom",
                "integration",
                "api",
                "automation",
            ]

            # Count advanced feature usage
            advanced_usage = 0
            for event in events:
                if any(
                    feature in event.event_name.lower() for feature in advanced_features
                ):
                    advanced_usage += 1

            if not events:
                return 0.0

            advanced_rate = advanced_usage / len(events)

            return min(1.0, advanced_rate * 5)  # Scale up for better scoring

        except Exception as e:
            logger.error(f"Failed to check advanced features: {e}")
            return 0.0

    def _check_basic_features(self, events: List[BehaviorEvent]) -> float:
        """Check for basic feature usage."""
        try:
            # Define basic features
            basic_features = [
                "view",
                "click",
                "navigate",
                "search",
                "filter",
                "sort",
                "page",
            ]

            # Count basic feature usage
            basic_usage = 0
            for event in events:
                if any(
                    feature in event.event_name.lower() for feature in basic_features
                ):
                    basic_usage += 1

            if not events:
                return 0.0

            basic_rate = basic_usage / len(events)

            return basic_rate

        except Exception as e:
            logger.error(f"Failed to check basic features: {e}")
            return 0.0

    def _check_error_rate(self, events: List[BehaviorEvent]) -> float:
        """Check for high error rate."""
        try:
            # Count error events
            error_events = [
                event
                for event in events
                if "error" in event.event_name.lower() or event.event_type == "error"
            ]

            if not events:
                return 0.0

            error_rate = len(error_events) / len(events)

            return error_rate

        except Exception as e:
            logger.error(f"Failed to check error rate: {e}")
            return 0.0

    def _check_low_error_rate(self, events: List[BehaviorEvent]) -> float:
        """Check for low error rate."""
        try:
            error_rate = self._check_error_rate(events)

            # Return inverse score (low error rate = high score)
            return 1.0 - error_rate

        except Exception as e:
            logger.error(f"Failed to check low error rate: {e}")
            return 0.0

    def _check_smooth_navigation(self, events: List[BehaviorEvent]) -> float:
        """Check for smooth navigation."""
        try:
            # Look for navigation events
            nav_events = [
                event
                for event in events
                if event.event_type == "navigation"
                or "navigate" in event.event_name.lower()
            ]

            if not nav_events:
                return 0.0

            # Check for successful navigation
            successful_nav = [
                event for event in nav_events if event.properties.get("success", True)
            ]

            smoothness = len(successful_nav) / len(nav_events)

            return smoothness

        except Exception as e:
            logger.error(f"Failed to check smooth navigation: {e}")
            return 0.0

    def _check_minimal_clicks(self, events: List[BehaviorEvent]) -> float:
        """Check for minimal clicks."""
        try:
            # Count click events
            click_events = [
                event
                for event in events
                if event.event_type == "click" or "click" in event.event_name.lower()
            ]

            if not events:
                return 0.0

            click_ratio = len(click_events) / len(events)

            # Minimal clicks = low click ratio
            return 1.0 - click_ratio

        except Exception as e:
            logger.error(f"Failed to check minimal clicks: {e}")
            return 0.0

    def _check_excessive_clicks(self, events: List[BehaviorEvent]) -> float:
        """Check for excessive clicks."""
        try:
            # Count click events
            click_events = [
                event
                for event in events
                if event.event_type == "click" or "click" in event.event_name.lower()
            ]

            if not events:
                return 0.0

            click_ratio = len(click_events) / len(events)

            # Excessive clicks = high click ratio
            return min(1.0, click_ratio * 2)  # Scale up for better scoring

        except Exception as e:
            logger.error(f"Failed to check excessive clicks: {e}")
            return 0.0

    def _calculate_navigation_efficiency(self, events: List[BehaviorEvent]) -> float:
        """Calculate navigation efficiency."""
        try:
            # Calculate direct vs indirect navigation
            page_views = [event for event in events if event.event_type == "page_view"]

            if len(page_views) < 2:
                return 0.0

            # Check for back navigation (inefficient)
            back_navigation = 0
            for i in range(1, len(page_views)):
                if page_views[i].properties.get("navigation_type") == "back":
                    back_navigation += 1

            efficiency = 1.0 - (back_navigation / len(page_views))

            return max(0.0, efficiency)

        except Exception as e:
            logger.error(f"Failed to calculate navigation efficiency: {e}")
            return 0.0

    def _calculate_exploration_score(self, events: List[BehaviorEvent]) -> float:
        """Calculate exploration score."""
        try:
            unique_pages = len(set(event.page_url for event in events))
            unique_events = len(set(event.event_name for event in events))

            if not events:
                return 0.0

            exploration_score = (unique_pages + unique_events) / (2 * len(events))

            return min(1.0, exploration_score * 2)

        except Exception as e:
            logger.error(f"Failed to calculate exploration score: {e}")
            return 0.0

    def _calculate_bounce_rate(self, events: List[BehaviorEvent]) -> float:
        """Calculate bounce rate."""
        try:
            sessions = defaultdict(list)
            for event in events:
                sessions[event.session_id].append(event)

            if not sessions:
                return 0.0

            single_page_sessions = 0
            for session_events in sessions.values():
                unique_pages = len(set(event.page_url for event in session_events))
                if unique_pages == 1:
                    single_page_sessions += 1

            bounce_rate = single_page_sessions / len(sessions)

            return bounce_rate

        except Exception as e:
            logger.error(f"Failed to calculate bounce rate: {e}")
            return 0.0

    def _calculate_engagement_score(self, events: List[BehaviorEvent]) -> float:
        """Calculate engagement score."""
        try:
            # Engagement metrics
            interaction_events = [
                event
                for event in events
                if event.event_type in ["click", "interaction", "engagement"]
            ]

            if not events:
                return 0.0

            engagement_rate = len(interaction_events) / len(events)

            return min(1.0, engagement_rate * 3)

        except Exception as e:
            logger.error(f"Failed to calculate engagement score: {e}")
            return 0.0

    def _calculate_session_frequency(self, events: List[BehaviorEvent]) -> float:
        """Calculate session frequency."""
        try:
            sessions = len(set(event.session_id for event in events))

            if not events:
                return 0.0

            # Calculate sessions per day
            if events:
                time_span = (
                    max(event.timestamp for event in events)
                    - min(event.timestamp for event in events)
                ).days
                time_span = max(1, time_span)  # Avoid division by zero

                frequency = sessions / time_span

                return min(1.0, frequency / 10)  # 10 sessions per day = full score

            return 0.0

        except Exception as e:
            logger.error(f"Failed to calculate session frequency: {e}")
            return 0.0

    def _calculate_feature_diversity(self, events: List[BehaviorEvent]) -> float:
        """Calculate feature usage diversity."""
        try:
            unique_features = len(set(event.event_name for event in events))

            if not events:
                return 0.0

            diversity = unique_features / len(events)

            return min(1.0, diversity * 2)

        except Exception as e:
            logger.error(f"Failed to calculate feature diversity: {e}")
            return 0.0

    def _calculate_error_rate(self, events: List[BehaviorEvent]) -> float:
        """Calculate error rate."""
        try:
            error_events = [
                event
                for event in events
                if "error" in event.event_name.lower() or event.event_type == "error"
            ]

            if not events:
                return 0.0

            error_rate = len(error_events) / len(events)

            return error_rate

        except Exception as e:
            logger.error(f"Failed to calculate error rate: {e}")
            return 0.0

    def _calculate_success_rate(self, events: List[BehaviorEvent]) -> float:
        """Calculate success rate."""
        try:
            success_events = [
                event for event in events if event.properties.get("success", True)
            ]

            if not events:
                return 0.0

            success_rate = len(success_events) / len(events)

            return success_rate

        except Exception as e:
            logger.error(f"Failed to calculate success rate: {e}")
            return 0.0

    def _calculate_efficiency_score(self, events: List[BehaviorEvent]) -> float:
        """Calculate efficiency score."""
        try:
            # Efficiency based on task completion time and error rate
            error_rate = self._calculate_error_rate(events)
            success_rate = self._calculate_success_rate(events)

            efficiency = success_rate - error_rate

            return max(0.0, min(1.0, efficiency))

        except Exception as e:
            logger.error(f"Failed to calculate efficiency score: {e}")
            return 0.0

    def _analyze_navigation_pattern(self, events: List[BehaviorEvent]) -> str:
        """Analyze navigation pattern."""
        try:
            page_views = [event for event in events if event.event_type == "page_view"]

            if len(page_views) < 2:
                return "insufficient_data"

            # Check for linear vs non-linear navigation
            linear_score = self._check_sequential_navigation(page_views)

            if linear_score > 0.7:
                return "linear"
            elif linear_score < 0.3:
                return "nonlinear"
            else:
                return "mixed"

        except Exception as e:
            logger.error(f"Failed to analyze navigation pattern: {e}")
            return "unknown"

    def _analyze_page_preferences(self, events: List[BehaviorEvent]) -> Dict[str, int]:
        """Analyze page preferences."""
        try:
            page_counts = defaultdict(int)
            for event in events:
                if event.event_type == "page_view":
                    page_counts[event.page_url] += 1

            # Return top pages
            sorted_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)

            return dict(sorted_pages[:10])  # Top 10 pages

        except Exception as e:
            logger.error(f"Failed to analyze page preferences: {e}")
            return {}

    def _analyze_time_patterns(self, events: List[BehaviorEvent]) -> Dict[str, Any]:
        """Analyze time patterns."""
        try:
            if not events:
                return {}

            # Extract hours and days
            hours = [event.timestamp.hour for event in events]
            days = [event.timestamp.weekday() for event in events]

            # Calculate most active times
            hour_counts = defaultdict(int)
            day_counts = defaultdict(int)

            for hour in hours:
                hour_counts[hour] += 1

            for day in days:
                day_counts[day] += 1

            # Find peak times
            peak_hour = max(hour_counts.keys(), key=lambda x: hour_counts[x])
            peak_day = max(day_counts.keys(), key=lambda x: day_counts[x])

            return {
                "peak_hour": peak_hour,
                "peak_day": peak_day,
                "hour_distribution": dict(hour_counts),
                "day_distribution": dict(day_counts),
            }

        except Exception as e:
            logger.error(f"Failed to analyze time patterns: {e}")
            return {}

    def _analyze_interaction_style(self, events: List[BehaviorEvent]) -> str:
        """Analyze interaction style."""
        try:
            # Categorize interaction types
            click_events = len([e for e in events if e.event_type == "click"])
            scroll_events = len([e for e in events if e.event_type == "scroll"])
            form_events = len([e for e in events if e.event_type == "form"])

            total_interactions = click_events + scroll_events + form_events

            if total_interactions == 0:
                return "passive"

            click_ratio = click_events / total_interactions

            if click_ratio > 0.7:
                return "click_heavy"
            elif scroll_events > click_events:
                return "scroll_heavy"
            else:
                return "balanced"

        except Exception as e:
            logger.error(f"Failed to analyze interaction style: {e}")
            return "unknown"

    def _analyze_feature_usage(self, events: List[BehaviorEvent]) -> Dict[str, int]:
        """Analyze feature usage."""
        try:
            feature_counts = defaultdict(int)
            for event in events:
                feature_counts[event.event_name] += 1

            # Return top features
            sorted_features = sorted(
                feature_counts.items(), key=lambda x: x[1], reverse=True
            )

            return dict(sorted_features[:10])  # Top 10 features

        except Exception as e:
            logger.error(f"Failed to analyze feature usage: {e}")
            return {}

    def _analyze_device_usage(self, events: List[BehaviorEvent]) -> Dict[str, int]:
        """Analyze device usage."""
        try:
            device_counts = defaultdict(int)
            for event in events:
                device = event.context.get("device_type", "unknown")
                device_counts[device] += 1

            return dict(device_counts)

        except Exception as e:
            logger.error(f"Failed to analyze device usage: {e}")
            return {}

    def _analyze_goal_orientation(self, events: List[BehaviorEvent]) -> str:
        """Analyze goal orientation."""
        try:
            # Look for goal-related events
            goal_events = [
                event
                for event in events
                if "goal" in event.event_name.lower()
                or "target" in event.event_name.lower()
            ]

            if not events:
                return "unknown"

            goal_ratio = len(goal_events) / len(events)

            if goal_ratio > 0.3:
                return "highly_goal_oriented"
            elif goal_ratio > 0.1:
                return "moderately_goal_oriented"
            else:
                return "exploratory"

        except Exception as e:
            logger.error(f"Failed to analyze goal orientation: {e}")
            return "unknown"

    def _analyze_exploration_tendency(self, events: List[BehaviorEvent]) -> str:
        """Analyze exploration tendency."""
        try:
            exploration_score = self._calculate_exploration_score(events)

            if exploration_score > 0.7:
                return "high_explorer"
            elif exploration_score > 0.3:
                return "moderate_explorer"
            else:
                return "low_explorer"

        except Exception as e:
            logger.error(f"Failed to analyze exploration tendency: {e}")
            return "unknown"

    def _analyze_frustration_indicators(self, events: List[BehaviorEvent]) -> List[str]:
        """Analyze frustration indicators."""
        try:
            indicators = []

            # Check for error events
            error_events = [e for e in events if "error" in e.event_name.lower()]
            if len(error_events) > 3:
                indicators.append("high_error_rate")

            # Check for repeated actions
            action_counts = defaultdict(int)
            for event in events:
                action_counts[event.event_name] += 1

            repeated_actions = [
                action for action, count in action_counts.items() if count > 5
            ]
            if repeated_actions:
                indicators.append("repeated_actions")

            # Check for long sessions without completion
            sessions = defaultdict(list)
            for event in events:
                sessions[event.session_id].append(event)

            long_sessions = []
            for session_events in sessions.values():
                if len(session_events) > 20:
                    long_sessions.append(session_events)

            if long_sessions:
                indicators.append("long_sessions")

            return indicators

        except Exception as e:
            logger.error(f"Failed to analyze frustration indicators: {e}")
            return []

    def _calculate_avg_session_time(self, events: List[BehaviorEvent]) -> float:
        """Calculate average session time."""
        try:
            if len(events) < 2:
                return 0.0

            start_time = min(event.timestamp for event in events)
            end_time = max(event.timestamp for event in events)

            duration = (
                end_time - start_time
            ).total_seconds() / 1000  # Convert to milliseconds

            return duration

        except Exception as e:
            logger.error(f"Failed to calculate average session time: {e}")
            return 0.0

    def _calculate_overall_trend(self, daily_metrics: List[Dict[str, Any]]) -> str:
        """Calculate overall trend."""
        try:
            if len(daily_metrics) < 2:
                return "insufficient_data"

            # Compare first and last periods
            first_period = daily_metrics[: len(daily_metrics) // 2]
            last_period = daily_metrics[len(daily_metrics) // 2 :]

            first_avg = sum(m["event_count"] for m in first_period) / len(first_period)
            last_avg = sum(m["event_count"] for m in last_period) / len(last_period)

            if last_avg > first_avg * 1.1:
                return "increasing"
            elif last_avg < first_avg * 0.9:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"Failed to calculate overall trend: {e}")
            return "unknown"

    def _find_peak_activity_day(
        self, daily_metrics: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Find peak activity day."""
        try:
            if not daily_metrics:
                return None

            peak_day = max(daily_metrics, key=lambda x: x["event_count"])

            return peak_day["date"]

        except Exception as e:
            logger.error(f"Failed to find peak activity day: {e}")
            return None

    def _calculate_behavior_consistency(
        self, daily_metrics: List[Dict[str, Any]]
    ) -> float:
        """Calculate behavior consistency."""
        try:
            if len(daily_metrics) < 2:
                return 0.0

            event_counts = [m["event_count"] for m in daily_metrics]

            # Calculate coefficient of variation
            mean = sum(event_counts) / len(event_counts)
            variance = sum((x - mean) ** 2 for x in event_counts) / len(event_counts)
            std_dev = variance**0.5

            # Consistency = 1 - coefficient of variation
            consistency = 1.0 - (std_dev / mean) if mean > 0 else 0.0

            return max(0.0, min(1.0, consistency))

        except Exception as e:
            logger.error(f"Failed to calculate behavior consistency: {e}")
            return 0.0

    def _aggregate_characteristics(
        self, profiles: List[UserBehaviorProfile]
    ) -> Dict[str, Any]:
        """Aggregate characteristics from multiple profiles."""
        try:
            aggregated = {}

            # Aggregate all characteristics
            all_characteristics = defaultdict(list)
            for profile in profiles:
                for key, value in profile.characteristics.items():
                    all_characteristics[key].append(value)

            # Calculate aggregates
            for key, values in all_characteristics.items():
                if isinstance(values[0], (int, float)):
                    aggregated[key] = sum(values) / len(values)
                elif isinstance(values[0], str):
                    # Find most common string
                    counts = defaultdict(int)
                    for value in values:
                        counts[value] += 1
                    aggregated[key] = max(counts.keys(), key=lambda x: counts[x])
                elif isinstance(values[0], dict):
                    # Aggregate dictionaries
                    aggregated[key] = self._aggregate_characteristics(values)

            return aggregated

        except Exception as e:
            logger.error(f"Failed to aggregate characteristics: {e}")
            return {}

    async def _generate_segment_insights(
        self, segment_distribution: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from segment distribution."""
        try:
            insights = []

            # Find dominant segment
            dominant_segment = max(
                segment_distribution.keys(),
                key=lambda x: segment_distribution[x]["count"],
            )
            dominant_percentage = segment_distribution[dominant_segment]["percentage"]

            if dominant_percentage > 50:
                insights.append(
                    f"Most users ({dominant_percentage:.1f}%) are {dominant_segment}"
                )

            # Check for balanced distribution
            segments = list(segment_distribution.values())
            if all(10 <= s["percentage"] <= 30 for s in segments):
                insights.append("User behavior is well-distributed across patterns")

            # Check for power users
            if "power_user" in segment_distribution:
                power_user_percentage = segment_distribution["power_user"]["percentage"]
                if power_user_percentage > 20:
                    insights.append(
                        f"High power user adoption ({power_user_percentage:.1f}%)"
                    )

            # Check for frustrated users
            if "frustrated" in segment_distribution:
                frustrated_percentage = segment_distribution["frustrated"]["percentage"]
                if frustrated_percentage > 15:
                    insights.append(
                        f"High frustration rate ({frustrated_percentage:.1f}%) - needs attention"
                    )

            return insights

        except Exception as e:
            logger.error(f"Failed to generate segment insights: {e}")
            return []

    async def _trigger_profile_update(self, user_id: str, tenant_id: str) -> None:
        """Trigger profile update for user."""
        try:
            # Check if profile needs update
            cache_key = f"{user_id}:{tenant_id}"
            if cache_key in self._behavior_profiles:
                profile = self._behavior_profiles[cache_key]

                # Update if last update was more than 24 hours ago
                if datetime.now(timezone.utc) - profile.last_updated > timedelta(
                    hours=24
                ):
                    await self.analyze_user_behavior(user_id, tenant_id)

        except Exception as e:
            logger.error(f"Failed to trigger profile update: {e}")

    async def _save_behavior_event(self, event: BehaviorEvent) -> None:
        """Save behavior event to database."""
        try:
            query = """
                INSERT INTO behavior_events (
                    id, user_id, tenant_id, session_id, event_type, event_name, 
                    page_url, timestamp, duration_ms, properties, context, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """

            params = [
                event.id,
                event.user_id,
                event.tenant_id,
                event.session_id,
                event.event_type,
                event.event_name,
                event.page_url,
                event.timestamp,
                event.duration_ms,
                event.properties,
                event.context,
                event.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save behavior event: {e}")

    async def _save_behavior_profile(self, profile: UserBehaviorProfile) -> None:
        """Save behavior profile to database."""
        try:
            query = """
                INSERT INTO behavior_profiles (
                    id, user_id, tenant_id, behavior_type, behavior_pattern, 
                    confidence_score, characteristics, metrics, session_count, 
                    total_time_spent, last_updated, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (user_id, tenant_id) DO UPDATE SET
                    behavior_type = EXCLUDED.behavior_type,
                    behavior_pattern = EXCLUDED.behavior_pattern,
                    confidence_score = EXCLUDED.confidence_score,
                    characteristics = EXCLUDED.characteristics,
                    metrics = EXCLUDED.metrics,
                    session_count = EXCLUDED.session_count,
                    total_time_spent = EXCLUDED.total_time_spent,
                    last_updated = EXCLUDED.last_updated
            """

            params = [
                profile.id,
                profile.user_id,
                profile.tenant_id,
                profile.behavior_type,
                profile.behavior_pattern,
                profile.confidence_score,
                profile.characteristics,
                profile.metrics,
                profile.session_count,
                profile.total_time_spent,
                profile.last_updated,
                profile.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save behavior profile: {e}")

    async def _save_behavior_analysis(self, analysis: BehaviorAnalysis) -> None:
        """Save behavior analysis to database."""
        try:
            query = """
                INSERT INTO behavior_analyses (
                    id, tenant_id, analysis_type, period_days, total_users, 
                    behavior_patterns, behavior_metrics, insights, recommendations, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """

            params = [
                analysis.id,
                analysis.tenant_id,
                analysis.analysis_type,
                analysis.period_days,
                analysis.total_users,
                analysis.behavior_patterns,
                analysis.behavior_metrics,
                json.dumps(analysis.insights),
                json.dumps(analysis.recommendations),
                analysis.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save behavior analysis: {e}")


# Factory function
def create_user_behavior_analyzer(db_pool) -> UserBehaviorAnalyzer:
    """Create user behavior analyzer instance."""
    return UserBehaviorAnalyzer(db_pool)
