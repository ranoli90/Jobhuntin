"""
User Interest Profiler for Phase 13.1 Communication System
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from shared.logging_config import get_logger

logger = get_logger("sorce.user_interest_profiler")


@dataclass
class UserInterestProfile:
    """User interest profile."""

    id: str
    user_id: str
    tenant_id: str
    interests: Dict[str, float] = field(default_factory=dict)
    keywords: Dict[str, List[str]] = field(default_factory=dict)
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = datetime.now(timezone.utc)
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class InterestCategory:
    """Interest category definition."""

    name: str
    keywords: List[str]
    weight: float = 1.0
    decay_rate: float = 0.1
    boost_rate: float = 0.2


@dataclass
class UserInteraction:
    """User interaction data."""

    id: str
    user_id: str
    tenant_id: str
    interaction_type: str
    content: str
    category: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class UserInterestProfiler:
    """AI-powered user interest profiling system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._categories = self._initialize_categories()
        self._decay_hours = 24 * 7  # 1 week decay
        self._min_interactions = 3
        self._profile_cache: Dict[str, UserInterestProfile] = {}

    async def analyze_user_interactions(
        self,
        user_id: str,
        tenant_id: str,
        interactions: List[Dict[str, Any]],
    ) -> UserInterestProfile:
        """Analyze user interactions to build interest profile."""
        try:
            # Get existing profile
            profile = await self._get_user_profile(user_id, tenant_id)

            # Process new interactions
            for interaction_data in interactions:
                interaction = UserInteraction(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tenant_id=tenant_id,
                    interaction_type=interaction_data.get("type", "view"),
                    content=interaction_data.get("content", ""),
                    category=interaction_data.get("category", "general"),
                    timestamp=datetime.fromisoformat(
                        interaction_data.get("timestamp", datetime.now().isoformat())
                    ),
                    metadata=interaction_data.get("metadata", {}),
                )

                # Update profile based on interaction
                await self._update_profile_from_interaction(profile, interaction)

                # Save interaction
                await self._save_interaction(interaction)

            # Apply time decay to old interests
            await self._apply_time_decay(profile)

            # Update profile
            profile.last_updated = datetime.now(timezone.utc)
            profile.updated_at = datetime.now(timezone.utc)
            await self._save_profile(profile)

            # Update cache
            self._profile_cache[f"{user_id}:{tenant_id}"] = profile

            logger.info(f"Analyzed {len(interactions)} interactions for user {user_id}")
            return profile

        except Exception as e:
            logger.error(f"Failed to analyze user interactions: {e}")
            raise

    async def get_user_profile(
        self, user_id: str, tenant_id: str
    ) -> UserInterestProfile:
        """Get user interest profile."""
        try:
            cache_key = f"{user_id}:{tenant_id}"

            # Check cache first
            if cache_key in self._profile_cache:
                profile = self._profile_cache[cache_key]
                # Check if cache is fresh (less than 1 hour old)
                if datetime.now(timezone.utc) - profile.updated_at < timedelta(hours=1):
                    return profile

            # Load from database
            profile = await self._get_user_profile(user_id, tenant_id)

            # Update cache
            self._profile_cache[cache_key] = profile

            return profile

        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            # Return default profile
            return UserInterestProfile(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
            )

    async def update_interest_score(
        self,
        user_id: str,
        tenant_id: str,
        category: str,
        score_adjustment: float,
        keywords: Optional[List[str]] = None,
    ) -> UserInterestProfile:
        """Update interest score for a category."""
        try:
            profile = await self.get_user_profile(user_id, tenant_id)

            # Update interest score
            current_score = profile.interests.get(category, 0.0)
            new_score = max(0.0, min(1.0, current_score + score_adjustment))
            profile.interests[category] = new_score

            # Update keywords
            if keywords:
                if category not in profile.keywords:
                    profile.keywords[category] = []
                profile.keywords[category].extend(keywords)
                # Remove duplicates
                profile.keywords[category] = list(set(profile.keywords[category]))

            # Update timestamps
            profile.last_updated = datetime.now(timezone.utc)
            profile.updated_at = datetime.now(timezone.utc)

            # Save profile
            await self._save_profile(profile)

            # Update cache
            self._profile_cache[f"{user_id}:{tenant_id}"] = profile

            logger.info(f"Updated interest score for {category}: {new_score:.3f}")
            return profile

        except Exception as e:
            logger.error(f"Failed to update interest score: {e}")
            raise

    async def get_top_interests(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 10,
        min_score: float = 0.1,
    ) -> List[Tuple[str, float]]:
        """Get user's top interests."""
        try:
            profile = await self.get_user_profile(user_id, tenant_id)

            # Filter and sort interests
            filtered_interests = [
                (category, score)
                for category, score in profile.interests.items()
                if score >= min_score
            ]

            filtered_interests.sort(key=lambda x: x[1], reverse=True)

            return filtered_interests[:limit]

        except Exception as e:
            logger.error(f"Failed to get top interests: {e}")
            return []

    async def get_interest_keywords(
        self,
        user_id: str,
        tenant_id: str,
        category: str,
    ) -> List[str]:
        """Get keywords for a specific interest category."""
        try:
            profile = await self.get_user_profile(user_id, tenant_id)
            return profile.keywords.get(category, [])
        except Exception as e:
            logger.error(f"Failed to get interest keywords: {e}")
            return []

    async def calculate_similarity(
        self,
        user_id: str,
        tenant_id: str,
        content: str,
        category: str,
    ) -> float:
        """Calculate similarity between content and user interests."""
        try:
            profile = await self.get_user_profile(user_id, tenant_id)

            # Get user interest score for category
            user_score = profile.interests.get(category, 0.0)

            # Get user keywords for category
            user_keywords = set(profile.keywords.get(category, []))

            # Extract keywords from content
            content_keywords = set(self._extract_keywords(content))

            # Calculate keyword overlap
            if user_keywords and content_keywords:
                overlap = len(user_keywords.intersection(content_keywords))
                union = len(user_keywords.union(content_keywords))
                keyword_similarity = overlap / union if union > 0 else 0.0
            else:
                keyword_similarity = 0.0

            # Combine interest score and keyword similarity
            similarity = (user_score * 0.6) + (keyword_similarity * 0.4)

            return similarity

        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0

    async def recommend_content(
        self,
        user_id: str,
        tenant_id: str,
        content_pool: List[Dict[str, Any]],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Recommend content based on user interests."""
        try:
            recommendations = []

            for content_item in content_pool:
                similarity = await self.calculate_similarity(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    content=content_item.get("content", ""),
                    category=content_item.get("category", "general"),
                )

                if similarity > 0.1:  # Minimum similarity threshold
                    recommendations.append(
                        {
                            **content_item,
                            "similarity_score": similarity,
                        }
                    )

            # Sort by similarity and limit
            recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Failed to recommend content: {e}")
            return []

    async def get_profile_summary(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive profile summary."""
        try:
            profile = await self.get_user_profile(user_id, tenant_id)

            # Calculate statistics
            total_interests = len(profile.interests)
            avg_interest_score = (
                sum(profile.interests.values()) / total_interests
                if total_interests > 0
                else 0.0
            )
            total_keywords = sum(
                len(keywords) for keywords in profile.keywords.values()
            )
            interaction_count = len(profile.interaction_history)

            # Get top interests
            top_interests = await self.get_top_interests(user_id, tenant_id, limit=5)

            # Get interest distribution
            interest_distribution = {}
            for category, score in profile.interests.items():
                if score >= 0.1:
                    interest_distribution[category] = score

            return {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "total_interests": total_interests,
                "average_interest_score": round(avg_interest_score, 3),
                "total_keywords": total_keywords,
                "interaction_count": interaction_count,
                "last_updated": profile.last_updated.isoformat(),
                "top_interests": top_interests,
                "interest_distribution": interest_distribution,
                "keywords_by_category": profile.keywords,
            }

        except Exception as e:
            logger.error(f"Failed to get profile summary: {e}")
            return {}

    async def _get_user_profile(
        self, user_id: str, tenant_id: str
    ) -> UserInterestProfile:
        """Get user profile from database."""
        try:
            query = """
                SELECT * FROM user_interest_profiles 
                WHERE user_id = $1 AND tenant_id = $2
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, user_id, tenant_id)

                if result:
                    return UserInterestProfile(
                        id=result[0],
                        user_id=result[1],
                        tenant_id=result[2],
                        interests=result[3] or {},
                        keywords=result[4] or {},
                        interaction_history=result[5] or [],
                        last_updated=result[6],
                        created_at=result[7],
                        updated_at=result[8],
                    )

                # Create default profile
                return UserInterestProfile(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tenant_id=tenant_id,
                )

        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return UserInterestProfile(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
            )

    async def _update_profile_from_interaction(
        self,
        profile: UserInterestProfile,
        interaction: UserInteraction,
    ) -> None:
        """Update profile based on user interaction."""
        try:
            # Get category definition
            category_def = self._categories.get(interaction.category)
            if not category_def:
                return

            # Extract keywords from interaction content
            content_keywords = self._extract_keywords(interaction.content)

            # Update interest score
            current_score = profile.interests.get(interaction.category, 0.0)

            # Calculate score adjustment based on interaction type
            interaction_weights = {
                "click": 0.1,
                "view": 0.05,
                "share": 0.15,
                "like": 0.08,
                "comment": 0.12,
                "bookmark": 0.2,
                "apply": 0.25,
            }

            weight = interaction_weights.get(interaction.interaction_type, 0.05)
            score_adjustment = weight * category_def.boost_rate

            new_score = min(1.0, current_score + score_adjustment)
            profile.interests[interaction.category] = new_score

            # Update keywords
            if interaction.category not in profile.keywords:
                profile.keywords[interaction.category] = []

            profile.keywords[interaction.category].extend(content_keywords)
            # Remove duplicates and limit to top 20 keywords
            profile.keywords[interaction.category] = list(
                set(profile.keywords[interaction.category])
            )[:20]

            # Add to interaction history
            profile.interaction_history.append(
                {
                    "type": interaction.interaction_type,
                    "category": interaction.category,
                    "content": interaction.content[:100],  # Truncate for storage
                    "timestamp": interaction.timestamp.isoformat(),
                    "keywords": content_keywords[:5],  # Store top 5 keywords
                }
            )

            # Limit history size
            if len(profile.interaction_history) > 100:
                profile.interaction_history = profile.interaction_history[-100:]

        except Exception as e:
            logger.error(f"Failed to update profile from interaction: {e}")

    async def _apply_time_decay(self, profile: UserInterestProfile) -> None:
        """Apply time decay to old interests."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=self._decay_hours
            )

            for category in list(profile.interests.keys()):
                # Get recent interactions for this category
                recent_interactions = [
                    interaction
                    for interaction in profile.interaction_history
                    if interaction["category"] == category
                    and datetime.fromisoformat(interaction["timestamp"]) > cutoff_time
                ]

                if len(recent_interactions) < self._min_interactions:
                    # Apply decay
                    category_def = self._categories.get(category)
                    if category_def:
                        current_score = profile.interests[category]
                        decayed_score = current_score * (1 - category_def.decay_rate)

                        # Remove interest if score is too low
                        if decayed_score < 0.05:
                            del profile.interests[category]
                            if category in profile.keywords:
                                del profile.keywords[category]
                        else:
                            profile.interests[category] = decayed_score

        except Exception as e:
            logger.error(f"Failed to apply time decay: {e}")

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        try:
            # Simple keyword extraction
            import re

            # Convert to lowercase and split
            words = re.findall(r"\b\w+\b", content.lower())

            # Filter out common words
            stop_words = {
                "the",
                "is",
                "at",
                "which",
                "on",
                "and",
                "a",
                "an",
                "as",
                "are",
                "was",
                "were",
                "been",
                "be",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "must",
                "can",
                "this",
                "that",
                "these",
                "those",
                "i",
                "you",
                "he",
                "she",
                "it",
                "we",
                "they",
                "what",
                "where",
                "when",
                "why",
                "how",
                "all",
                "each",
                "every",
                "both",
                "few",
                "more",
                "most",
                "other",
                "some",
                "such",
                "no",
                "nor",
                "not",
                "only",
                "own",
                "same",
                "so",
                "than",
                "too",
                "very",
                "just",
                "for",
                "of",
                "with",
                "by",
                "from",
                "up",
                "about",
                "into",
                "through",
                "during",
                "before",
                "after",
                "above",
                "below",
                "between",
                "under",
                "along",
                "following",
                "behind",
                "beyond",
                "plus",
                "except",
                "but",
                "yet",
                "or",
                "if",
                "because",
                "as",
                "until",
                "while",
                "where",
                "when",
                "though",
                "since",
                "unless",
                "whether",
                "although",
                "however",
                "otherwise",
                "therefore",
                "accordingly",
                "consequently",
                "nevertheless",
                "nonetheless",
                "notwithstanding",
                "herein",
                "hereby",
                "hereinbefore",
                "hereinafter",
                "hereinunder",
                "heretofore",
                "herewith",
                "thereby",
                "therein",
                "therefrom",
                "thereof",
                "thereon",
                "thereto",
                "thereunder",
                "heretofore",
                "wheresoever",
                "whatsoever",
                "wheresoever",
                "whenever",
                "whereas",
                "wherein",
                "whereof",
                "whereby",
                "wherewith",
                "wherewithal",
                "hereafter",
                "hereat",
                "hereby",
                "herein",
                "hereof",
                "hereto",
                "heretofore",
                "heretofore",
                "heretofore",
                "heretofore",
                "heretofore",
                "heretofore",
            }

            # Filter and return keywords
            keywords = [
                word for word in words if len(word) > 2 and word not in stop_words
            ]

            # Return top 10 most frequent keywords
            from collections import Counter

            keyword_counts = Counter(keywords)

            return [word for word, count in keyword_counts.most_common(10)]

        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []

    def _initialize_categories(self) -> Dict[str, InterestCategory]:
        """Initialize interest categories."""
        return {
            "technology": InterestCategory(
                name="technology",
                keywords=[
                    "software",
                    "programming",
                    "development",
                    "coding",
                    "tech",
                    "computer",
                    "data",
                    "ai",
                    "machine learning",
                    "web",
                    "mobile",
                    "cloud",
                    "devops",
                    "security",
                    "database",
                    "api",
                    "frontend",
                    "backend",
                ],
                weight=1.2,
                decay_rate=0.05,
                boost_rate=0.25,
            ),
            "healthcare": InterestCategory(
                name="healthcare",
                keywords=[
                    "health",
                    "medical",
                    "doctor",
                    "nurse",
                    "hospital",
                    "patient",
                    "medicine",
                    "treatment",
                    "care",
                    "clinical",
                    "pharmacy",
                    "diagnosis",
                    "therapy",
                    "surgery",
                    "wellness",
                ],
                weight=1.0,
                decay_rate=0.08,
                boost_rate=0.2,
            ),
            "finance": InterestCategory(
                name="finance",
                keywords=[
                    "money",
                    "bank",
                    "investment",
                    "financial",
                    "accounting",
                    "credit",
                    "loan",
                    "insurance",
                    "tax",
                    "wealth",
                    "portfolio",
                    "stock",
                    "bond",
                    "fund",
                    "trading",
                    "economics",
                ],
                weight=1.1,
                decay_rate=0.06,
                boost_rate=0.22,
            ),
            "education": InterestCategory(
                name="education",
                keywords=[
                    "education",
                    "school",
                    "university",
                    "college",
                    "student",
                    "teacher",
                    "learning",
                    "course",
                    "degree",
                    "academic",
                    "research",
                    "study",
                    "training",
                    "knowledge",
                    "skill",
                ],
                weight=1.0,
                decay_rate=0.07,
                boost_rate=0.2,
            ),
            "marketing": InterestCategory(
                name="marketing",
                keywords=[
                    "marketing",
                    "advertising",
                    "brand",
                    "promotion",
                    "campaign",
                    "social",
                    "media",
                    "content",
                    "seo",
                    "sem",
                    "analytics",
                    "conversion",
                    "engagement",
                    "audience",
                    "customer",
                ],
                weight=0.9,
                decay_rate=0.1,
                boost_rate=0.18,
            ),
            "design": InterestCategory(
                name="design",
                keywords=[
                    "design",
                    "creative",
                    "art",
                    "graphic",
                    "ui",
                    "ux",
                    "interface",
                    "user",
                    "experience",
                    "visual",
                    "layout",
                    "color",
                    "typography",
                    "illustration",
                    "animation",
                ],
                weight=1.0,
                decay_rate=0.08,
                boost_rate=0.2,
            ),
            "business": InterestCategory(
                name="business",
                keywords=[
                    "business",
                    "company",
                    "corporate",
                    "enterprise",
                    "startup",
                    "entrepreneur",
                    "management",
                    "strategy",
                    "operations",
                    "sales",
                    "revenue",
                    "profit",
                    "market",
                    "industry",
                ],
                weight=1.0,
                decay_rate=0.06,
                boost_rate=0.2,
            ),
            "science": InterestCategory(
                name="science",
                keywords=[
                    "science",
                    "research",
                    "experiment",
                    "study",
                    "analysis",
                    "data",
                    "hypothesis",
                    "theory",
                    "discovery",
                    "innovation",
                    "laboratory",
                    "scientific",
                    "method",
                    "evidence",
                ],
                weight=1.1,
                decay_rate=0.05,
                boost_rate=0.25,
            ),
            "sports": InterestCategory(
                name="sports",
                keywords=[
                    "sport",
                    "athletic",
                    "fitness",
                    "exercise",
                    "training",
                    "competition",
                    "game",
                    "match",
                    "team",
                    "player",
                    "coach",
                    "performance",
                    "health",
                    "wellness",
                ],
                weight=0.8,
                decay_rate=0.12,
                boost_rate=0.15,
            ),
            "travel": InterestCategory(
                name="travel",
                keywords=[
                    "travel",
                    "trip",
                    "vacation",
                    "holiday",
                    "destination",
                    "flight",
                    "hotel",
                    "tourism",
                    "adventure",
                    "explore",
                    "journey",
                    "culture",
                    "international",
                    "passport",
                ],
                weight=0.8,
                decay_rate=0.1,
                boost_rate=0.18,
            ),
        }

    async def _save_profile(self, profile: UserInterestProfile) -> None:
        """Save profile to database."""
        try:
            query = """
                INSERT INTO user_interest_profiles (
                    id, user_id, tenant_id, interests, keywords, 
                    interaction_history, last_updated, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (user_id, tenant_id) DO UPDATE SET
                    interests = EXCLUDED.interests,
                    keywords = EXCLUDED.keywords,
                    interaction_history = EXCLUDED.interaction_history,
                    last_updated = EXCLUDED.last_updated,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                profile.id,
                profile.user_id,
                profile.tenant_id,
                profile.interests,
                profile.keywords,
                profile.interaction_history,
                profile.last_updated,
                profile.created_at,
                profile.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save profile: {e}")

    async def _save_interaction(self, interaction: UserInteraction) -> None:
        """Save interaction to database."""
        try:
            query = """
                INSERT INTO user_interactions (
                    id, user_id, tenant_id, interaction_type, content, 
                    category, timestamp, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """

            params = [
                interaction.id,
                interaction.user_id,
                interaction.tenant_id,
                interaction.interaction_type,
                interaction.content,
                interaction.category,
                interaction.timestamp,
                interaction.metadata,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")


# Factory function
def create_user_interest_profiler(db_pool) -> UserInterestProfiler:
    """Create user interest profiler instance."""
    return UserInterestProfiler(db_pool)
