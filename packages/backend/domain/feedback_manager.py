"""
Feedback Manager for Phase 14.1 User Experience
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from shared.logging_config import get_logger

logger = get_logger("sorce.feedback_manager")


@dataclass
class FeedbackResponse:
    """User feedback response data."""

    id: str
    user_id: str
    tenant_id: str
    feedback_type: str
    rating: int
    sentiment_score: float
    category: str
    title: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_url: Optional[str] = None
    session_id: Optional[str] = None
    is_public: bool = False
    status: str = "pending"  # pending, reviewed, resolved, rejected
    admin_notes: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class FeedbackCategory:
    """Feedback category definition."""

    id: str
    name: str
    description: str
    is_active: bool = True
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class NPSResponse:
    """Net Promoter Score response data."""

    id: str
    user_id: str
    tenant_id: str
    score: int
    promoter_type: str  # promoter, passive, detractor
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class FeedbackAnalysis:
    """Feedback analysis results."""

    id: str
    tenant_id: str
    analysis_type: str
    period_days: int
    total_responses: int
    average_rating: float
    sentiment_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    nps_score: Optional[int]
    nps_distribution: Dict[str, int]
    key_themes: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = datetime.now(timezone.utc)


class FeedbackManager:
    """Advanced feedback management system with sentiment analysis."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._sentiment_analyzer = self._initialize_sentiment_analyzer()
        self._feedback_categories = self._initialize_feedback_categories()
        self._nps_thresholds = {"promoter": 9, "detractor": 6}

    async def collect_feedback(
        self,
        user_id: str,
        tenant_id: str,
        feedback_type: str,
        rating: int,
        category: str,
        title: str,
        message: str,
        page_url: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False,
    ) -> FeedbackResponse:
        """Collect user feedback with sentiment analysis."""
        try:
            # Analyze sentiment
            sentiment_score = await self._analyze_sentiment(message)

            # Create feedback response
            feedback = FeedbackResponse(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                feedback_type=feedback_type,
                rating=rating,
                sentiment_score=sentiment_score,
                category=category,
                title=title,
                message=message,
                metadata=metadata or {},
                page_url=page_url,
                session_id=session_id,
                is_public=is_public,
            )

            # Save to database
            await self._save_feedback(feedback)

            # Trigger real-time analysis if needed
            await self._trigger_feedback_analysis(tenant_id)

            logger.info(
                f"Collected feedback: {title} (rating: {rating}, sentiment: {sentiment_score:.2f})"
            )
            return feedback

        except Exception as e:
            logger.error(f"Failed to collect feedback: {e}")
            raise

    async def collect_nps_feedback(
        self,
        user_id: str,
        tenant_id: str,
        score: int,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NPSResponse:
        """Collect Net Promoter Score feedback."""
        try:
            # Determine promoter type
            if score >= 9:
                promoter_type = "promoter"
            elif score >= 7:
                promoter_type = "passive"
            else:
                promoter_type = "detractor"

            # Create NPS response
            nps_response = NPSResponse(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                score=score,
                promoter_type=promoter_type,
                reason=reason,
                metadata=metadata or {},
            )

            # Save to database
            await self._save_nps_response(nps_response)

            # Trigger NPS analysis
            await self._trigger_nps_analysis(tenant_id)

            logger.info(f"Collected NPS feedback: {score} ({promoter_type})")
            return nps_response

        except Exception as e:
            logger.error(f"Failed to collect NPS feedback: {e}")
            raise

    async def get_feedback_summary(
        self,
        tenant_id: str,
        time_period_days: int = 30,
        feedback_type: Optional[str] = None,
        category: Optional[str] = None,
        rating_range: Optional[Tuple[int, int]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get feedback summary with analytics."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get feedback statistics
            stats = await self._get_feedback_statistics(
                tenant_id, cutoff_time, feedback_type, category, rating_range, user_id
            )

            # Get sentiment analysis
            sentiment_stats = await self._get_sentiment_statistics(
                tenant_id, cutoff_time, feedback_type, category, user_id
            )

            # Get NPS statistics
            nps_stats = await self._get_nps_statistics(tenant_id, cutoff_time, user_id)

            # Get category breakdown
            category_breakdown = await self._get_category_breakdown(
                tenant_id, cutoff_time, feedback_type, user_id
            )

            # Get recent feedback
            recent_feedback = await self._get_recent_feedback(
                tenant_id,
                limit=10,
                feedback_type=feedback_type,
                category=category,
                user_id=user_id,
            )

            summary = {
                "period_days": time_period_days,
                "feedback_statistics": stats,
                "sentiment_statistics": sentiment_stats,
                "nps_statistics": nps_stats,
                "category_breakdown": category_breakdown,
                "recent_feedback": recent_feedback,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get feedback summary: {e}")
            return {}

    async def analyze_feedback_trends(
        self,
        tenant_id: str,
        time_period_days: int = 30,
        feedback_type: Optional[str] = None,
    ) -> FeedbackAnalysis:
        """Analyze feedback trends and patterns."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get feedback data for analysis
            feedback_data = await self._get_feedback_data_for_analysis(
                tenant_id, cutoff_time, feedback_type
            )

            # Calculate statistics
            total_responses = len(feedback_data)
            average_rating = (
                sum(f.rating for f in feedback_data) / total_responses
                if total_responses > 0
                else 0
            )

            # Sentiment distribution
            sentiment_counts = {}
            for feedback in feedback_data:
                sentiment = self._classify_sentiment(feedback.sentiment_score)
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

            # Category distribution
            category_counts = {}
            for feedback in feedback_data:
                category_counts[feedback.category] = (
                    category_counts.get(feedback.category, 0) + 1
                )

            # Calculate NPS if available
            nps_data = await self._get_nps_data_for_analysis(tenant_id, cutoff_time)
            nps_score = self._calculate_nps_score(nps_data) if nps_data else None
            nps_distribution = (
                self._calculate_nps_distribution(nps_data) if nps_data else {}
            )

            # Extract key themes from feedback
            key_themes = await self._extract_key_themes(feedback_data)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                feedback_data, sentiment_counts, category_counts
            )

            # Create analysis
            analysis = FeedbackAnalysis(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                analysis_type="trend_analysis",
                period_days=time_period_days,
                total_responses=total_responses,
                average_rating=average_rating,
                sentiment_distribution=sentiment_counts,
                category_distribution=category_counts,
                nps_score=nps_score,
                nps_distribution=nps_distribution,
                key_themes=key_themes,
                recommendations=recommendations,
                created_at=datetime.now(timezone.utc),
            )

            # Save analysis
            await self._save_feedback_analysis(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze feedback trends: {e}")
            raise

    async def get_feedback_categories(
        self,
        tenant_id: str,
        active_only: bool = True,
    ) -> List[FeedbackCategory]:
        """Get feedback categories."""
        try:
            query = """
                SELECT * FROM feedback_categories
                WHERE tenant_id = $1
            """
            params = [tenant_id]

            if active_only:
                query += " AND is_active = true"

            query += " ORDER BY name"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                categories = []
                for row in results:
                    category = FeedbackCategory(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        is_active=row[3],
                        created_at=row[4],
                        updated_at=row[5],
                    )
                    categories.append(category)

                return categories

        except Exception as e:
            logger.error(f"Failed to get feedback categories: {e}")
            return []

    async def create_feedback_category(
        self,
        tenant_id: str,
        name: str,
        description: str,
        is_active: bool = True,
    ) -> FeedbackCategory:
        """Create a new feedback category."""
        try:
            category = FeedbackCategory(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                is_active=is_active,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # Save to database
            await self._save_feedback_category(category)

            logger.info(f"Created feedback category: {name}")
            return category

        except Exception as e:
            logger.error(f"Failed to create feedback category: {e}")
            raise

    async def update_feedback_status(
        self,
        feedback_id: str,
        status: str,
        admin_notes: Optional[str] = None,
    ) -> bool:
        """Update feedback status."""
        try:
            query = """
                UPDATE feedback_responses
                SET status = $1, admin_notes = $2, updated_at = NOW()
                WHERE id = $3
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(query, status, admin_notes, feedback_id)

                return result == "UPDATE 1"

        except Exception as e:
            logger.error(f"Failed to update feedback status: {e}")
            return False

    async def get_feedback_by_id(
        self, feedback_id: str, tenant_id: str
    ) -> Optional[FeedbackResponse]:
        """Get feedback by ID."""
        try:
            query = """
                SELECT * FROM feedback_responses
                WHERE id = $1 AND tenant_id = $2
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, feedback_id, tenant_id)

                if result:
                    return FeedbackResponse(
                        id=result[0],
                        user_id=result[1],
                        tenant_id=result[2],
                        feedback_type=result[3],
                        rating=result[4],
                        sentiment_score=result[5],
                        category=result[6],
                        title=result[7],
                        message=result[8],
                        metadata=result[9] or {},
                        page_url=result[10],
                        session_id=result[11],
                        is_public=result[12],
                        status=result[13],
                        admin_notes=result[14],
                        created_at=result[15],
                        updated_at=result[16],
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to get feedback by ID: {e}")
            return None

    async def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text."""
        try:
            # Simple sentiment analysis based on keywords
            positive_words = [
                "excellent",
                "amazing",
                "great",
                "good",
                "fantastic",
                "wonderful",
                "love",
                "like",
                "helpful",
                "useful",
                "perfect",
                "outstanding",
                "brilliant",
                "awesome",
                "superb",
                "marvelous",
                "exceptional",
            ]

            negative_words = [
                "terrible",
                "awful",
                "bad",
                "poor",
                "horrible",
                "disappointing",
                "frustrating",
                "confusing",
                "difficult",
                "hard",
                "annoying",
                "useless",
                "broken",
                "wrong",
                "issue",
                "problem",
                "concern",
            ]

            # Convert to lowercase for comparison
            text_lower = text.lower()

            # Count positive and negative words
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            # Calculate sentiment score (-1 to 1)
            if positive_count == 0 and negative_count == 0:
                return 0.0  # Neutral

            total_words = positive_count + negative_count
            sentiment_score = (positive_count - negative_count) / total_words

            return max(-1.0, min(1.0, sentiment_score))

        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return 0.0  # Default to neutral

    def _classify_sentiment(self, score: float) -> str:
        """Classify sentiment based on score."""
        if score > 0.3:
            return "positive"
        elif score < -0.3:
            return "negative"
        else:
            return "neutral"

    async def _initialize_sentiment_analyzer(self) -> Dict[str, Any]:
        """Initialize sentiment analyzer."""
        return {
            "positive_words": [
                "excellent",
                "amazing",
                "great",
                "good",
                "fantastic",
                "wonderful",
                "love",
                "like",
                "helpful",
                "useful",
                "perfect",
                "outstanding",
                "brilliant",
                "awesome",
                "superb",
                "marvelous",
                "exceptional",
            ],
            "negative_words": [
                "terrible",
                "awful",
                "bad",
                "poor",
                "horrible",
                "disappointing",
                "frustrating",
                "confusing",
                "difficult",
                "hard",
                "annoying",
                "useless",
                "broken",
                "wrong",
                "issue",
                "problem",
                "concern",
            ],
            "neutral_words": [
                "okay",
                "fine",
                "average",
                "normal",
                "standard",
                "typical",
                "regular",
                "ordinary",
                "common",
                "expected",
                "usual",
            ],
        }

    def _initialize_feedback_categories(self) -> Dict[str, FeedbackCategory]:
        """Initialize default feedback categories."""
        return {
            "general": FeedbackCategory(
                id=str(uuid.uuid4()),
                name="General",
                description="General feedback about the platform",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            "ui_ux": FeedbackCategory(
                id=str(uuid.uuid4()),
                name="UI/UX",
                description="User interface and user experience feedback",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            "features": FeedbackCategory(
                id=str(uuid.uuid4()),
                name="Features",
                description="Feature requests and feedback",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            "bugs": FeedbackCategory(
                id=str(uuid.uuid4()),
                name="Bugs",
                description="Bug reports and issues",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            "performance": FeedbackCategory(
                id=str(uuid.uuid4()),
                name="Performance",
                description="Performance-related feedback",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            "support": FeedbackCategory(
                id=str(uuid.uuid4()),
                name="Support",
                description="Customer support feedback",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        }

    async def _trigger_feedback_analysis(self, tenant_id: str) -> None:
        """Trigger background feedback analysis."""
        try:
            # This would normally trigger a background job
            # For now, we'll just log it
            logger.info(f"Triggering feedback analysis for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to trigger feedback analysis: {e}")

    async def _trigger_nps_analysis(self, tenant_id: str) -> None:
        """Trigger background NPS analysis."""
        try:
            # This would normally trigger a background job
            # For now, we'll just log it
            logger.info(f"Triggering NPS analysis for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to trigger NPS analysis: {e}")

    async def _get_feedback_statistics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        feedback_type: Optional[str] = None,
        category: Optional[str] = None,
        rating_range: Optional[Tuple[int, int]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get feedback statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_responses,
                    AVG(rating) as average_rating,
                    COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_ratings,
                    COUNT(CASE WHEN rating <= 2 THEN 1 END) as negative_ratings,
                    COUNT(CASE WHEN rating = 3 THEN 1 END) as neutral_ratings
                FROM feedback_responses
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if feedback_type:
                query += " AND feedback_type = $3"
                params.append(feedback_type)

            if category:
                query += " AND category = $3"
                params.append(category)

            if rating_range:
                query += " AND rating >= $3 AND rating <= $4"
                params.extend(rating_range)

            if user_id:
                query += " AND user_id = $5"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    total_responses = result[0]
                    return {
                        "total_responses": total_responses,
                        "average_rating": float(result[1]) if result[1] else 0,
                        "positive_ratings": result[2],
                        "negative_ratings": result[3],
                        "neutral_ratings": result[4],
                        "positive_rate": (result[2] / total_responses)
                        if total_responses > 0
                        else 0,
                        "negative_rate": (result[3] / total_responses)
                        if total_responses > 0
                        else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get feedback statistics: {e}")
            return {}

    async def _get_sentiment_statistics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        feedback_type: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get sentiment statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_responses,
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(CASE WHEN sentiment_score > 0.3 THEN 1 END) as positive_sentiments,
                    COUNT(CASE WHEN sentiment_score < -0.3 THEN 1 END) as negative_sentiments,
                    COUNT(CASE WHEN sentiment_score >= -0.3 AND sentiment_score <= 0.3 THEN 1 END) as neutral_sentiments
                FROM feedback_responses
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if feedback_type:
                query += " AND feedback_type = $3"
                params.append(feedback_type)

            if category:
                query += " AND category = $3"
                params.append(category)

            if user_id:
                query += " AND user_id = $4"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    total_responses = result[0]
                    return {
                        "total_responses": total_responses,
                        "avg_sentiment": float(result[1]) if result[1] else 0,
                        "positive_sentiments": result[2],
                        "negative_sentiments": result[3],
                        "neutral_sentiments": result[4],
                        "positive_rate": (result[2] / total_responses)
                        if total_responses > 0
                        else 0,
                        "negative_rate": (result[3] / total_responses)
                        if total_responses > 0
                        else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get sentiment statistics: {e}")
            return {}

    async def _get_nps_statistics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get NPS statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_responses,
                    AVG(score) as avg_score,
                    COUNT(CASE WHEN promoter_type = 'promoter' THEN 1 END) as promoters,
                    COUNT(CASE WHEN promoter_type = 'passive' THEN 1 END) as passives,
                    COUNT(CASE WHEN promoter_type = 'detractor' THEN 1 END) as detractors
                FROM nps_responses
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    total_responses = result[0]
                    promoters = result[3]
                    passives = result[4]
                    detractors = result[5]

                    nps_score = (
                        (promoters - detractors) / total_responses * 100
                        if total_responses > 0
                        else 0
                    )

                    return {
                        "total_responses": total_responses,
                        "avg_score": float(result[1]) if result[1] else 0,
                        "promoters": promoters,
                        "passives": passives,
                        "detractors": detractors,
                        "nps_score": nps_score,
                        "promoter_rate": (promoters / total_responses) * 100
                        if total_responses > 0
                        else 0,
                        "detractor_rate": (detractors / total_responses) * 100
                        if total_responses > 0
                        else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get NPS statistics: {e}")
            return {}

    async def _get_category_breakdown(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        feedback_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """Get category breakdown."""
        try:
            query = """
                SELECT category, COUNT(*) as count
                FROM feedback_responses
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if feedback_type:
                query += " AND feedback_type = $3"
                params.append(feedback_type)

            if user_id:
                query += " AND user_id = $4"
                params.append(user_id)

            query += " GROUP BY category ORDER BY count DESC"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                breakdown = {}
                for row in results:
                    breakdown[row[0]] = row[1]

                return breakdown

        except Exception as e:
            logger.error(f"Failed to get category breakdown: {e}")
            return {}

    async def _get_recent_feedback(
        self,
        tenant_id: str,
        limit: int = 10,
        feedback_type: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[FeedbackResponse]:
        """Get recent feedback responses."""
        try:
            query = """
                SELECT * FROM feedback_responses
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, datetime.now(timezone.utc) - timedelta(days=7)]

            if feedback_type:
                query += " AND feedback_type = $3"
                params.append(feedback_type)

            if category:
                query += " AND category = $3"
                params.append(category)

            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)

            query += " ORDER BY created_at DESC LIMIT $4"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                feedback_list = []
                for row in results:
                    feedback = FeedbackResponse(
                        id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        feedback_type=row[3],
                        rating=row[4],
                        sentiment_score=row[5],
                        category=row[6],
                        title=row[7],
                        message=row[8],
                        metadata=row[9] or {},
                        page_url=row[10],
                        session_id=row[11],
                        is_public=row[12],
                        status=row[13],
                        admin_notes=row[14],
                        created_at=row[15],
                        updated_at=row[16],
                    )
                    feedback_list.append(feedback)

                return feedback_list

        except Exception as e:
            logger.error(f"Failed to get recent feedback: {e}")
            return []

    async def _get_feedback_data_for_analysis(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        feedback_type: Optional[str] = None,
    ) -> List[FeedbackResponse]:
        """Get feedback data for analysis."""
        try:
            query = """
                SELECT * FROM feedback_responses
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if feedback_type:
                query += " AND feedback_type = $3"
                params.append(feedback_type)

            query += " ORDER BY created_at ASC"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                feedback_list = []
                for row in results:
                    feedback = FeedbackResponse(
                        id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        feedback_type=row[3],
                        rating=row[4],
                        sentiment_score=row[5],
                        category=row[6],
                        title=row[7],
                        message=row[8],
                        metadata=row[9] or {},
                        page_url=row[10],
                        session_id=row[11],
                        is_public=row[12],
                        status=row[13],
                        admin_notes=row[14],
                        created_at=row[15],
                        updated_at=row[16],
                    )
                    feedback_list.append(feedback)

                return feedback_list

        except Exception as e:
            logger.error(f"Failed to get feedback data for analysis: {e}")
            return []

    async def _get_nps_data_for_analysis(
        self,
        tenant_id: str,
        cutoff_time: datetime,
    ) -> List[NPSResponse]:
        """Get NPS data for analysis."""
        try:
            query = """
                SELECT * FROM nps_responses
                WHERE tenant_id = $1 AND created_at > $2
                ORDER BY created_at ASC
            """
            params = [tenant_id, cutoff_time]

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                nps_list = []
                for row in results:
                    nps = NPSResponse(
                        id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        score=row[3],
                        promoter_type=row[4],
                        reason=row[5],
                        metadata=row[6] or {},
                        created_at=row[7],
                    )
                    nps_list.append(nps)

                return nps_list

        except Exception as e:
            logger.error(f"Failed to get NPS data for analysis: {e}")
            return []

    def _calculate_nps_score(self, nps_data: List[NPSResponse]) -> Optional[int]:
        """Calculate NPS score from NPS data."""
        try:
            if not nps_data:
                return None

            promoters = len(
                [nps for nps in nps_data if nps.promoter_type == "promoter"]
            )
            detractors = len(
                [nps for nps in nps_data if nps.promoter_type == "detractor"]
            )
            total = len(nps_data)

            if total == 0:
                return None

            nps_score = (promoters - detractors) / total * 100
            return int(round(nps_score))

        except Exception as e:
            logger.error(f"Failed to calculate NPS score: {e}")
            return None

    def _calculate_nps_distribution(
        self, nps_data: List[NPSResponse]
    ) -> Dict[str, int]:
        """Calculate NPS distribution."""
        try:
            distribution = {
                "promoter": 0,
                "passive": 0,
                "detractor": 0,
            }

            for nps in nps_data:
                distribution[nps.promoter_type] += 1

            return distribution

        except Exception as e:
            logger.error(f"Failed to calculate NPS distribution: {e}")
            return {}

    async def _extract_key_themes(
        self, feedback_data: List[FeedbackResponse]
    ) -> List[Dict[str, Any]]:
        """Extract key themes from feedback text."""
        try:
            themes = {}

            # Simple keyword extraction
            for feedback in feedback_data:
                words = feedback.message.lower().split()

                # Count word frequency
                word_count = {}
                for word in words:
                    if len(word) > 3:  # Only consider words longer than 3 characters
                        word_count[word] = word_count.get(word, 0) + 1

                # Get top words for this feedback
                top_words = sorted(
                    word_count.items(), key=lambda x: x[1], reverse=True
                )[:5]

                if top_words:
                    themes[feedback.title] = top_words

            # Convert to list and sort by frequency
            theme_list = []
            for title, words in themes.items():
                theme_list.append(
                    {
                        "theme": title,
                        "frequency": sum(words.values()),
                        "keywords": words,
                    }
                )

            # Sort by frequency
            theme_list.sort(key=lambda x: x["frequency"], reverse=True)

            return theme_list[:10]  # Top 10 themes

        except Exception as e:
            logger.error(f"Failed to extract key themes: {e}")
            return []

    async def _generate_recommendations(
        self,
        feedback_data: List[FeedbackResponse],
        sentiment_counts: Dict[str, int],
        category_counts: Dict[str, int],
    ) -> List[str]:
        """Generate recommendations based on feedback analysis."""
        try:
            recommendations = []

            # Low average rating recommendation
            avg_rating = (
                sum(f.rating for f in feedback_data) / len(feedback_data)
                if feedback_data
                else 0
            )

            if avg_rating < 3.0:
                recommendations.append(
                    "Focus on improving user experience and addressing common issues"
                )

            # High negative sentiment recommendation
            total_negative = sentiment_counts.get("negative", 0)
            total_feedback = sum(sentiment_counts.values())
            negative_rate = total_negative / total_feedback if total_feedback > 0 else 0

            if negative_rate > 0.3:
                recommendations.append(
                    "Investigate sources of user dissatisfaction and implement improvements"
                )

            # Category-specific recommendations
            for category, count in category_counts.items():
                if count > 5:
                    recommendations.append(f"Focus on improving {category} experience")

            # Actionable recommendations
            recommendations.extend(
                [
                    "Implement regular feedback collection and analysis",
                    "Create action plans based on feedback insights",
                    "Share feedback insights with product team",
                    "Monitor feedback trends and patterns over time",
                ]
            )

            # Remove duplicates
            return list(set(recommendations))[:10]

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []

    async def _save_feedback(self, feedback: FeedbackResponse) -> None:
        """Save feedback to database."""
        try:
            query = """
                INSERT INTO feedback_responses (
                    id, user_id, tenant_id, feedback_type, rating, sentiment_score,
                    category, title, message, metadata, page_url, session_id,
                    is_public, status, admin_notes, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """

            params = [
                feedback.id,
                feedback.user_id,
                feedback.tenant_id,
                feedback.feedback_type,
                feedback.rating,
                feedback.sentiment_score,
                feedback.category,
                feedback.title,
                feedback.message,
                feedback.metadata,
                feedback.page_url,
                feedback.session_id,
                feedback.is_public,
                feedback.status,
                feedback.admin_notes,
                feedback.created_at,
                feedback.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")

    async def _save_nps_response(self, nps_response: NPSResponse) -> None:
        """Save NPS response to database."""
        try:
            query = """
                INSERT INTO nps_responses (
                    id, user_id, tenant_id, score, promoter_type, reason,
                    metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """

            params = [
                nps_response.id,
                nps_response.user_id,
                nps_response.tenant_id,
                nps_response.score,
                nps_response.promoter_type,
                nps_response.reason,
                nps_response.metadata,
                nps_response.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save NPS response: {e}")

    async def _save_feedback_analysis(self, analysis: FeedbackAnalysis) -> None:
        """Save feedback analysis to database."""
        try:
            query = """
                INSERT INTO feedback_analyses (
                    id, tenant_id, analysis_type, period_days, total_responses,
                    average_rating, sentiment_distribution, category_distribution,
                    nps_score, nps_distribution, key_themes, recommendations, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """

            params = [
                analysis.id,
                analysis.tenant_id,
                analysis.analysis_type,
                analysis.period_days,
                analysis.total_responses,
                analysis.average_rating,
                analysis.sentiment_distribution,
                analysis.category_distribution,
                analysis.nps_score,
                analysis.nps_distribution,
                json.dumps(analysis.key_themes),
                json.dumps(analysis.recommendations),
                analysis.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save feedback analysis: {e}")

    async def _save_feedback_category(self, category: FeedbackCategory) -> None:
        """Save feedback category to database."""
        try:
            query = """
                INSERT INTO feedback_categories (
                    id, name, description, is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5)
            """

            params = [
                category.id,
                category.name,
                category.description,
                category.is_active,
                category.created_at,
                category.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save feedback category: {e}")


# Factory function
def create_feedback_manager(db_pool) -> FeedbackManager:
    """Create feedback manager instance."""
    return FeedbackManager(db_pool)
