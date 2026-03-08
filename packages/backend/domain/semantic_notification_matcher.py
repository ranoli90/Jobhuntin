"""
Semantic Notification Matcher for Phase 13.1 Communication System
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field

from shared.logging_config import get_logger

logger = get_logger("sorce.semantic_notification_matcher")


@dataclass
class SemanticTag:
    """Semantic tag for notifications."""

    id: str
    notification_id: str
    tag: str
    category: str
    confidence_score: float
    context: Dict[str, Any] = field(default_factory=dict)
    tenant_id: str
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class UserInterest:
    """User interest profile."""

    id: str
    user_id: str
    tenant_id: str
    interest_category: str
    interest_keywords: List[str]
    interest_score: float
    is_active: bool = True
    last_updated: datetime = datetime.now(timezone.utc)
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class RelevanceScore:
    """Relevance scoring result."""

    notification_id: str
    user_id: str
    relevance_score: float
    category_scores: Dict[str, float]
    keyword_matches: List[str]
    semantic_factors: Dict[str, float]
    calculated_at: datetime = datetime.now(timezone.utc)


class SemanticNotificationMatcher:
    """AI-powered semantic notification matching system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._category_weights = {
            "job_match": 0.8,
            "application_status": 0.9,
            "security": 1.0,
            "marketing": 0.3,
            "usage_limits": 0.7,
            "reminders": 0.6,
        }
        self._keyword_weights = {
            "exact_match": 1.0,
            "partial_match": 0.7,
            "semantic_match": 0.5,
        }
        self._factors = {
            "recency": 0.2,
            "frequency": 0.3,
            "engagement": 0.5,
        }

    async def calculate_relevance(
        self,
        notification_id: str,
        user_id: str,
        tenant_id: str,
        notification_content: Dict[str, Any],
    ) -> RelevanceScore:
        """Calculate relevance score for notification-user pair."""
        try:
            # Get user interests
            user_interests = await self._get_user_interests(user_id, tenant_id)

            # Get notification semantic tags
            notification_tags = await self._get_notification_tags(
                notification_id, tenant_id
            )

            # Calculate category relevance
            category_scores = await self._calculate_category_relevance(
                user_interests, notification_tags
            )

            # Calculate keyword matches
            keyword_matches, keyword_score = await self._calculate_keyword_matches(
                user_interests, notification_content
            )

            # Calculate semantic factors
            semantic_factors = await self._calculate_semantic_factors(
                user_id, tenant_id, notification_content
            )

            # Calculate overall relevance score
            relevance_score = await self._calculate_overall_score(
                category_scores, keyword_score, semantic_factors
            )

            # Create result
            result = RelevanceScore(
                notification_id=notification_id,
                user_id=user_id,
                relevance_score=relevance_score,
                category_scores=category_scores,
                keyword_matches=keyword_matches,
                semantic_factors=semantic_factors,
            )

            # Save result
            await self._save_relevance_score(result)

            logger.info(
                f"Calculated relevance score: {relevance_score:.3f} for user {user_id}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to calculate relevance: {e}")
            # Return default score
            return RelevanceScore(
                notification_id=notification_id,
                user_id=user_id,
                relevance_score=0.5,
                category_scores={},
                keyword_matches=[],
                semantic_factors={},
            )

    async def match_notifications(
        self,
        user_id: str,
        tenant_id: str,
        notifications: List[Dict[str, Any]],
        threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Match notifications to user with relevance scoring."""
        try:
            matched_notifications = []

            for notification in notifications:
                # Calculate relevance
                relevance = await self.calculate_relevance(
                    notification_id=notification.get("id"),
                    user_id=user_id,
                    tenant_id=tenant_id,
                    notification_content=notification,
                )

                # Check if meets threshold
                if relevance.relevance_score >= threshold:
                    matched_notifications.append(
                        {
                            **notification,
                            "relevance_score": relevance.relevance_score,
                            "category_scores": relevance.category_scores,
                            "keyword_matches": relevance.keyword_matches,
                            "semantic_factors": relevance.semantic_factors,
                        }
                    )

            # Sort by relevance score
            matched_notifications.sort(key=lambda x: x["relevance_score"], reverse=True)

            logger.info(
                f"Matched {len(matched_notifications)} notifications for user {user_id}"
            )
            return matched_notifications

        except Exception as e:
            logger.error(f"Failed to match notifications: {e}")
            return []

    async def update_user_profile(
        self,
        user_id: str,
        tenant_id: str,
        interactions: List[Dict[str, Any]],
    ) -> bool:
        """Update user interest profile based on interactions."""
        try:
            # Analyze interactions to extract interests
            interest_updates = await self._analyze_interactions(interactions)

            # Update user interests
            for category, keywords in interest_updates.items():
                await self._update_user_interest(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    interest_category=category,
                    keywords=keywords,
                )

            logger.info(
                f"Updated user profile for {user_id} based on {len(interactions)} interactions"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False

    async def extract_semantic_tags(
        self,
        notification_id: str,
        tenant_id: str,
        title: str,
        message: str,
        category: str,
    ) -> List[SemanticTag]:
        """Extract semantic tags from notification content."""
        try:
            tags = []

            # Extract keywords from title and message
            content = f"{title} {message}".lower()

            # Category-specific keyword extraction
            category_keywords = await self._get_category_keywords(category)

            for keyword in category_keywords:
                if keyword in content:
                    # Calculate confidence based on frequency and position
                    confidence = await self._calculate_tag_confidence(keyword, content)

                    tag = SemanticTag(
                        id=str(uuid.uuid4()),
                        notification_id=notification_id,
                        tag=keyword,
                        category=category,
                        confidence_score=confidence,
                        context={
                            "position": content.find(keyword),
                            "frequency": content.count(keyword),
                        },
                        tenant_id=tenant_id,
                    )

                    tags.append(tag)
                    await self._save_semantic_tag(tag)

            logger.info(
                f"Extracted {len(tags)} semantic tags for notification {notification_id}"
            )
            return tags

        except Exception as e:
            logger.error(f"Failed to extract semantic tags: {e}")
            return []

    async def get_user_interests(
        self,
        user_id: str,
        tenant_id: str,
    ) -> List[UserInterest]:
        """Get user interest profile."""
        try:
            return await self._get_user_interests(user_id, tenant_id)
        except Exception as e:
            logger.error(f"Failed to get user interests: {e}")
            return []

    async def update_interest_score(
        self,
        user_id: str,
        tenant_id: str,
        interest_category: str,
        score_adjustment: float,
    ) -> bool:
        """Adjust interest score for a category."""
        try:
            # Get current interest
            interests = await self._get_user_interests(user_id, tenant_id)

            for interest in interests:
                if interest.interest_category == interest_category:
                    # Adjust score
                    new_score = max(
                        0.0, min(1.0, interest.interest_score + score_adjustment)
                    )

                    # Update database
                    query = """
                        UPDATE user_interests 
                        SET interest_score = $1, updated_at = NOW()
                        WHERE user_id = $2 AND tenant_id = $3 AND interest_category = $4
                    """

                    async with self.db_pool.acquire() as conn:
                        await conn.execute(
                            query, new_score, user_id, tenant_id, interest_category
                        )

                    logger.info(
                        f"Updated interest score for {interest_category}: {new_score:.3f}"
                    )
                    return True

            # Interest not found, create new one
            new_interest = UserInterest(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                interest_category=interest_category,
                interest_keywords=[],
                interest_score=max(0.0, min(1.0, score_adjustment)),
            )

            await self._save_user_interest(new_interest)

            logger.info(
                f"Created new interest {interest_category} with score {score_adjustment:.3f}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update interest score: {e}")
            return False

    async def _get_user_interests(
        self, user_id: str, tenant_id: str
    ) -> List[UserInterest]:
        """Get user interests from database."""
        try:
            query = """
                SELECT * FROM user_interests 
                WHERE user_id = $1 AND tenant_id = $2 AND is_active = true
                ORDER BY interest_score DESC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, user_id, tenant_id)

                interests = []
                for row in results:
                    interest = UserInterest(
                        id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        interest_category=row[3],
                        interest_keywords=row[4] or [],
                        interest_score=row[5],
                        is_active=row[6],
                        last_updated=row[7],
                        created_at=row[8],
                        updated_at=row[9],
                    )
                    interests.append(interest)

                return interests

        except Exception as e:
            logger.error(f"Failed to get user interests: {e}")
            return []

    async def _get_notification_tags(
        self, notification_id: str, tenant_id: str
    ) -> List[SemanticTag]:
        """Get semantic tags for notification."""
        try:
            query = """
                SELECT * FROM notification_semantic_tags 
                WHERE notification_id = $1 AND tenant_id = $2
                ORDER BY confidence_score DESC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, notification_id, tenant_id)

                tags = []
                for row in results:
                    tag = SemanticTag(
                        id=row[0],
                        notification_id=row[1],
                        tag=row[2],
                        category=row[3],
                        confidence_score=row[4],
                        context=row[5] or {},
                        tenant_id=row[6],
                        created_at=row[7],
                    )
                    tags.append(tag)

                return tags

        except Exception as e:
            logger.error(f"Failed to get notification tags: {e}")
            return []

    async def _calculate_category_relevance(
        self,
        user_interests: List[UserInterest],
        notification_tags: List[SemanticTag],
    ) -> Dict[str, float]:
        """Calculate category relevance scores."""
        category_scores = {}

        # Group user interests by category
        user_categories = {}
        for interest in user_interests:
            if interest.interest_category not in user_categories:
                user_categories[interest.interest_category] = []
            user_categories[interest.interest_category].append(interest)

        # Group notification tags by category
        notification_categories = {}
        for tag in notification_tags:
            if tag.category not in notification_categories:
                notification_categories[tag.category] = []
            notification_categories[tag.category].append(tag)

        # Calculate relevance for each category
        for category in set(user_categories.keys()) | set(
            notification_categories.keys()
        ):
            user_score = 0.0
            notification_score = 0.0

            # User interest score for category
            if category in user_categories:
                user_score = max(
                    interest.interest_score for interest in user_categories[category]
                )

            # Notification tag score for category
            if category in notification_categories:
                notification_score = max(
                    tag.confidence_score for tag in notification_categories[category]
                )

            # Combined relevance
            category_scores[category] = (
                user_score * notification_score
            ) * self._category_weights.get(category, 0.5)

        return category_scores

    async def _calculate_keyword_matches(
        self,
        user_interests: List[UserInterest],
        notification_content: Dict[str, Any],
    ) -> Tuple[List[str], float]:
        """Calculate keyword matches."""
        matches = []
        total_score = 0.0

        # Combine all user keywords
        user_keywords = set()
        for interest in user_interests:
            user_keywords.update(interest.interest_keywords)

        # Get notification text
        title = notification_content.get("title", "").lower()
        message = notification_content.get("message", "").lower()
        content = f"{title} {message}"

        # Find matches
        for keyword in user_keywords:
            if keyword.lower() in content:
                matches.append(keyword)

                # Calculate match score based on type
                if keyword.lower() == title:  # Exact title match
                    score = self._keyword_weights["exact_match"]
                elif keyword.lower() in title:  # Partial title match
                    score = self._keyword_weights["partial_match"]
                elif keyword.lower() in message:  # Content match
                    score = self._keyword_weights["semantic_match"]
                else:
                    score = 0.0

                total_score += score

        # Normalize score
        if user_keywords:
            total_score = total_score / len(user_keywords)

        return matches, total_score

    async def _calculate_semantic_factors(
        self,
        user_id: str,
        tenant_id: str,
        notification_content: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate semantic factors for relevance."""
        factors = {}

        # Recency factor (how recently user interacted with similar content)
        factors["recency"] = await self._calculate_recency_factor(
            user_id, tenant_id, notification_content
        )

        # Frequency factor (how often user engages with this category)
        factors["frequency"] = await self._calculate_frequency_factor(
            user_id, tenant_id, notification_content
        )

        # Engagement factor (user's historical engagement with similar notifications)
        factors["engagement"] = await self._calculate_engagement_factor(
            user_id, tenant_id, notification_content
        )

        return factors

    async def _calculate_overall_score(
        self,
        category_scores: Dict[str, float],
        keyword_score: float,
        semantic_factors: Dict[str, float],
    ) -> float:
        """Calculate overall relevance score."""
        # Weighted combination of scores
        category_weight = 0.4
        keyword_weight = 0.3
        semantic_weight = 0.3

        # Category score (average of all category scores)
        category_score = (
            sum(category_scores.values()) / len(category_scores)
            if category_scores
            else 0.0
        )

        # Semantic factor score (weighted average)
        semantic_score = (
            semantic_factors.get("recency", 0.0) * self._factors["recency"]
            + semantic_factors.get("frequency", 0.0) * self._factors["frequency"]
            + semantic_factors.get("engagement", 0.0) * self._factors["engagement"]
        )

        # Overall score
        overall_score = (
            category_score * category_weight
            + keyword_score * keyword_weight
            + semantic_score * semantic_weight
        )

        return min(1.0, max(0.0, overall_score))

    async def _get_category_keywords(self, category: str) -> List[str]:
        """Get keywords for a category."""
        keywords = {
            "job_match": [
                "job",
                "career",
                "opportunity",
                "position",
                "role",
                "salary",
                "company",
            ],
            "application_status": [
                "application",
                "status",
                "submitted",
                "reviewed",
                "accepted",
                "rejected",
            ],
            "security": [
                "security",
                "password",
                "login",
                "authentication",
                "safety",
                "protect",
            ],
            "marketing": [
                "offer",
                "promotion",
                "discount",
                "deal",
                "sale",
                "marketing",
            ],
            "usage_limits": [
                "limit",
                "quota",
                "usage",
                "exceeded",
                "reached",
                "remaining",
            ],
            "reminders": [
                "reminder",
                "follow",
                "complete",
                "finish",
                "deadline",
                "schedule",
            ],
        }

        return keywords.get(category, [])

    async def _calculate_tag_confidence(self, keyword: str, content: str) -> float:
        """Calculate confidence score for a tag."""
        try:
            # Base confidence on frequency and position
            frequency = content.count(keyword)
            position = content.find(keyword)

            # Higher confidence for multiple occurrences
            frequency_score = min(1.0, frequency / 3.0)

            # Higher confidence for early position (title vs content)
            position_score = 1.0 - (position / len(content)) if position >= 0 else 0.0

            # Combined confidence
            confidence = (frequency_score * 0.6) + (position_score * 0.4)

            return min(1.0, max(0.0, confidence))

        except Exception:
            return 0.5  # Default confidence

    async def _analyze_interactions(
        self, interactions: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Analyze user interactions to extract interests."""
        interest_updates = {}

        for interaction in interactions:
            # Extract keywords from interaction content
            content = interaction.get("content", "").lower()
            category = interaction.get("category", "general")

            # Simple keyword extraction (could be enhanced with NLP)
            keywords = content.split()
            keywords = [kw for kw in keywords if len(kw) > 3]  # Filter short words

            if category not in interest_updates:
                interest_updates[category] = []

            interest_updates[category].extend(keywords)

        # Remove duplicates and limit keywords per category
        for category in interest_updates:
            interest_updates[category] = list(set(interest_updates[category]))[:10]

        return interest_updates

    async def _update_user_interest(
        self,
        user_id: str,
        tenant_id: str,
        interest_category: str,
        keywords: List[str],
    ) -> None:
        """Update user interest in database."""
        try:
            # Check if interest exists
            existing = await self._get_user_interests(user_id, tenant_id)

            for interest in existing:
                if interest.interest_category == interest_category:
                    # Update existing interest
                    combined_keywords = list(set(interest.interest_keywords + keywords))

                    query = """
                        UPDATE user_interests 
                        SET interest_keywords = $1, updated_at = NOW()
                        WHERE user_id = $2 AND tenant_id = $3 AND interest_category = $4
                    """

                    async with self.db_pool.acquire() as conn:
                        await conn.execute(
                            query,
                            combined_keywords,
                            user_id,
                            tenant_id,
                            interest_category,
                        )

                    return

            # Create new interest
            new_interest = UserInterest(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                interest_category=interest_category,
                interest_keywords=keywords,
                interest_score=0.5,  # Default score
            )

            await self._save_user_interest(new_interest)

        except Exception as e:
            logger.error(f"Failed to update user interest: {e}")

    async def _calculate_recency_factor(
        self, user_id: str, tenant_id: str, notification_content: Dict[str, Any]
    ) -> float:
        """Calculate recency factor based on recent interactions."""
        try:
            # This would analyze recent user interactions with similar content
            # For now, return a default value
            return 0.5
        except Exception:
            return 0.5

    async def _calculate_frequency_factor(
        self, user_id: str, tenant_id: str, notification_content: Dict[str, Any]
    ) -> float:
        """Calculate frequency factor based on engagement patterns."""
        try:
            # This would analyze user's historical engagement with this category
            # For now, return a default value
            return 0.5
        except Exception:
            return 0.5

    async def _calculate_engagement_factor(
        self, user_id: str, tenant_id: str, notification_content: Dict[str, Any]
    ) -> float:
        """Calculate engagement factor based on user's engagement history."""
        try:
            # This would analyze user's click/read rates for similar notifications
            # For now, return a default value
            return 0.5
        except Exception:
            return 0.5

    async def _save_semantic_tag(self, tag: SemanticTag) -> None:
        """Save semantic tag to database."""
        try:
            query = """
                INSERT INTO notification_semantic_tags (
                    id, notification_id, tag, category, confidence_score, 
                    context, tenant_id, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO UPDATE SET
                    confidence_score = EXCLUDED.confidence_score,
                    context = EXCLUDED.context
            """

            params = [
                tag.id,
                tag.notification_id,
                tag.tag,
                tag.category,
                tag.confidence_score,
                tag.context,
                tag.tenant_id,
                tag.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save semantic tag: {e}")

    async def _save_user_interest(self, interest: UserInterest) -> None:
        """Save user interest to database."""
        try:
            query = """
                INSERT INTO user_interests (
                    id, user_id, tenant_id, interest_category, interest_keywords, 
                    interest_score, is_active, last_updated, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (user_id, tenant_id, interest_category) DO UPDATE SET
                    interest_keywords = EXCLUDED.interest_keywords,
                    interest_score = EXCLUDED.interest_score,
                    is_active = EXCLUDED.is_active,
                    last_updated = EXCLUDED.last_updated,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                interest.id,
                interest.user_id,
                interest.tenant_id,
                interest.interest_category,
                interest.interest_keywords,
                interest.interest_score,
                interest.is_active,
                interest.last_updated,
                interest.created_at,
                interest.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save user interest: {e}")

    async def _save_relevance_score(self, score: RelevanceScore) -> None:
        """Save relevance score to database."""
        try:
            query = """
                INSERT INTO notification_relevance_scores (
                    notification_id, user_id, relevance_score, category_scores, 
                    keyword_matches, semantic_factors, calculated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (notification_id, user_id) DO UPDATE SET
                    relevance_score = EXCLUDED.relevance_score,
                    category_scores = EXCLUDED.category_scores,
                    keyword_matches = EXCLUDED.keyword_matches,
                    semantic_factors = EXCLUDED.semantic_factors,
                    calculated_at = EXCLUDED.calculated_at
            """

            params = [
                score.notification_id,
                score.user_id,
                score.relevance_score,
                score.category_scores,
                score.keyword_matches,
                score.semantic_factors,
                score.calculated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save relevance score: {e}")


# Factory function
def create_semantic_notification_matcher(db_pool) -> SemanticNotificationMatcher:
    """Create semantic notification matcher instance."""
    return SemanticNotificationMatcher(db_pool)
