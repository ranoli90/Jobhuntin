"""SEO Competitor Intelligence Repository - Competitor analysis data.

Provides methods for managing competitor intelligence data including
keywords, content gaps, and weakness analysis.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.seo_competitor")


class SEOCompetitorRepository:
    """Repository for managing SEO competitor intelligence."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        """Initialize the repository with a database connection.

        Args:
            conn: AsyncPG database connection.
        """
        self._conn = conn

    async def get_competitor(
        self, competitor_name: str
    ) -> Optional[dict[str, Any]]:
        """Get competitor intelligence by name.

        Args:
            competitor_name: The name of the competitor.

        Returns:
            Competitor data or None if not found.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT
                    id,
                    competitor_name,
                    search_volume,
                    difficulty_score,
                    intent,
                    keywords,
                    content_gaps,
                    weaknesses,
                    last_updated,
                    created_at
                FROM seo_competitor_intelligence
                WHERE competitor_name = $1
                """,
                competitor_name,
            )

            if not row:
                return None

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to get competitor",
                extra={"competitor_name": competitor_name, "error": str(e)},
            )
            raise

    async def update_competitor(
        self,
        competitor_name: str,
        search_volume: Optional[int] = None,
        difficulty_score: Optional[int] = None,
        intent: Optional[str] = None,
        keywords: Optional[dict[str, Any]] = None,
        content_gaps: Optional[list[str]] = None,
        weaknesses: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Update competitor intelligence data.

        Args:
            competitor_name: The name of the competitor.
            search_volume: Optional search volume.
            difficulty_score: Optional difficulty score (0-100).
            intent: Optional primary intent.
            keywords: Optional keywords dictionary.
            content_gaps: Optional list of content gaps.
            weaknesses: Optional list of competitor weaknesses.

        Returns:
            Updated competitor data.
        """
        try:
            # Build dynamic update query
            updates = ["last_updated = NOW()"]
            params: list[Any] = [competitor_name]
            param_index = 2

            if search_volume is not None:
                updates.append(f"search_volume = ${param_index}")
                params.append(search_volume)
                param_index += 1

            if difficulty_score is not None:
                updates.append(f"difficulty_score = ${param_index}")
                params.append(difficulty_score)
                param_index += 1

            if intent is not None:
                updates.append(f"intent = ${param_index}")
                params.append(intent)
                param_index += 1

            if keywords is not None:
                updates.append(f"keywords = ${param_index}")
                params.append(keywords)
                param_index += 1

            if content_gaps is not None:
                updates.append(f"content_gaps = ${param_index}")
                params.append(content_gaps)
                param_index += 1

            if weaknesses is not None:
                updates.append(f"weaknesses = ${param_index}")
                params.append(weaknesses)
                param_index += 1

            query = f"""
                UPDATE seo_competitor_intelligence
                SET {', '.join(updates)}
                WHERE competitor_name = $1
                RETURNING id, competitor_name, search_volume, difficulty_score,
                          intent, keywords, content_gaps, weaknesses,
                          last_updated, created_at
            """

            row = await self._conn.fetchrow(query, *params)

            if not row:
                # Create new record if it doesn't exist
                return await self.create_competitor(
                    competitor_name=competitor_name,
                    search_volume=search_volume,
                    difficulty_score=difficulty_score,
                    intent=intent,
                    keywords=keywords,
                    content_gaps=content_gaps,
                    weaknesses=weaknesses,
                )

            logger.info(
                "Updated competitor intelligence",
                extra={"competitor_name": competitor_name},
            )

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to update competitor",
                extra={"competitor_name": competitor_name, "error": str(e)},
            )
            raise

    async def create_competitor(
        self,
        competitor_name: str,
        search_volume: Optional[int] = None,
        difficulty_score: Optional[int] = None,
        intent: Optional[str] = None,
        keywords: Optional[dict[str, Any]] = None,
        content_gaps: Optional[list[str]] = None,
        weaknesses: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Create a new competitor intelligence entry.

        Args:
            competitor_name: The name of the competitor.
            search_volume: Optional search volume.
            difficulty_score: Optional difficulty score.
            intent: Optional primary intent.
            keywords: Optional keywords dictionary.
            content_gaps: Optional list of content gaps.
            weaknesses: Optional list of weaknesses.

        Returns:
            Created competitor data.
        """
        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO seo_competitor_intelligence (
                    competitor_name, search_volume, difficulty_score,
                    intent, keywords, content_gaps, weaknesses
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, competitor_name, search_volume, difficulty_score,
                          intent, keywords, content_gaps, weaknesses,
                          last_updated, created_at
                """,
                competitor_name,
                search_volume,
                difficulty_score,
                intent,
                keywords,
                content_gaps,
                weaknesses,
            )

            logger.info(
                "Created competitor intelligence",
                extra={"competitor_name": competitor_name},
            )

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to create competitor",
                extra={"competitor_name": competitor_name, "error": str(e)},
            )
            raise

    async def get_all_competitors(
        self, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get all competitor intelligence entries.

        Args:
            limit: Maximum number of results.

        Returns:
            List of all competitors.
        """
        try:
            rows = await self._conn.fetch(
                """
                SELECT id, competitor_name, search_volume, difficulty_score,
                       intent, keywords, content_gaps, weaknesses,
                       last_updated, created_at
                FROM seo_competitor_intelligence
                ORDER BY search_volume DESC NULLS LAST, competitor_name
                LIMIT $1
                """,
                limit,
            )

            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(
                "Failed to get all competitors",
                extra={"error": str(e)},
            )
            raise

    async def delete_competitor(self, competitor_name: str) -> bool:
        """Delete a competitor intelligence entry.

        Args:
            competitor_name: The name of the competitor to delete.

        Returns:
            True if deleted, False if not found.
        """
        try:
            result = await self._conn.execute(
                """
                DELETE FROM seo_competitor_intelligence
                WHERE competitor_name = $1
                """,
                competitor_name,
            )

            deleted = result == "DELETE 1"

            if deleted:
                logger.info(
                    "Deleted competitor intelligence",
                    extra={"competitor_name": competitor_name},
                )

            return deleted
        except Exception as e:
            logger.error(
                "Failed to delete competitor",
                extra={"competitor_name": competitor_name, "error": str(e)},
            )
            raise

    async def get_competitors_by_difficulty(
        self, max_difficulty: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get competitors filtered by maximum difficulty score.

        Useful for finding low-competition opportunities.

        Args:
            max_difficulty: Maximum difficulty score.
            limit: Maximum number of results.

        Returns:
            List of competitors below the difficulty threshold.
        """
        try:
            rows = await self._conn.fetch(
                """
                SELECT id, competitor_name, search_volume, difficulty_score,
                       intent, keywords, content_gaps, weaknesses,
                       last_updated, created_at
                FROM seo_competitor_intelligence
                WHERE difficulty_score <= $1
                ORDER BY difficulty_score ASC, search_volume DESC
                LIMIT $2
                """,
                max_difficulty,
                limit,
            )

            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(
                "Failed to get competitors by difficulty",
                extra={"max_difficulty": max_difficulty, "error": str(e)},
            )
            raise

    async def get_competitors_by_intent(
        self, intent: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get competitors filtered by search intent.

        Args:
            intent: The search intent to filter by.
            limit: Maximum number of results.

        Returns:
            List of competitors with the specified intent.
        """
        try:
            rows = await self._conn.fetch(
                """
                SELECT id, competitor_name, search_volume, difficulty_score,
                       intent, keywords, content_gaps, weaknesses,
                       last_updated, created_at
                FROM seo_competitor_intelligence
                WHERE intent = $1
                ORDER BY search_volume DESC NULLS LAST
                LIMIT $2
                """,
                intent,
                limit,
            )

            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(
                "Failed to get competitors by intent",
                extra={"intent": intent, "error": str(e)},
            )
            raise

    async def get_content_gaps(
        self, competitor_name: str
    ) -> Optional[list[str]]:
        """Get content gaps for a specific competitor.

        Args:
            competitor_name: The name of the competitor.

        Returns:
            List of content gaps or None if not found.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT content_gaps
                FROM seo_competitor_intelligence
                WHERE competitor_name = $1
                """,
                competitor_name,
            )

            if not row or not row["content_gaps"]:
                return None

            return list(row["content_gaps"])
        except Exception as e:
            logger.error(
                "Failed to get content gaps",
                extra={"competitor_name": competitor_name, "error": str(e)},
            )
            raise

    async def get_competitor_weaknesses(
        self, competitor_name: str
    ) -> Optional[list[str]]:
        """Get weaknesses for a specific competitor.

        Args:
            competitor_name: The name of the competitor.

        Returns:
            List of weaknesses or None if not found.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT weaknesses
                FROM seo_competitor_intelligence
                WHERE competitor_name = $1
                """,
                competitor_name,
            )

            if not row or not row["weaknesses"]:
                return None

            return list(row["weaknesses"])
        except Exception as e:
            logger.error(
                "Failed to get competitor weaknesses",
                extra={"competitor_name": competitor_name, "error": str(e)},
            )
            raise

    async def add_content_gap(
        self, competitor_name: str, content_gap: str
    ) -> Optional[dict[str, Any]]:
        """Add a content gap to a competitor.

        Args:
            competitor_name: The name of the competitor.
            content_gap: The content gap to add.

        Returns:
            Updated competitor data or None if not found.
        """
        try:
            # Get current content gaps
            current_gaps = await self.get_content_gaps(competitor_name)
            gaps_list = current_gaps if current_gaps else []

            # Add new gap if not already present
            if content_gap not in gaps_list:
                gaps_list.append(content_gap)

                return await self.update_competitor(
                    competitor_name=competitor_name,
                    content_gaps=gaps_list,
                )

            # Return current data if gap already exists
            return await self.get_competitor(competitor_name)
        except Exception as e:
            logger.error(
                "Failed to add content gap",
                extra={
                    "competitor_name": competitor_name,
                    "content_gap": content_gap,
                    "error": str(e),
                },
            )
            raise

    async def add_weakness(
        self, competitor_name: str, weakness: str
    ) -> Optional[dict[str, Any]]:
        """Add a weakness to a competitor.

        Args:
            competitor_name: The name of the competitor.
            weakness: The weakness to add.

        Returns:
            Updated competitor data or None if not found.
        """
        try:
            # Get current weaknesses
            current_weaknesses = await self.get_competitor_weaknesses(competitor_name)
            weaknesses_list = current_weaknesses if current_weaknesses else []

            # Add new weakness if not already present
            if weakness not in weaknesses_list:
                weaknesses_list.append(weakness)

                return await self.update_competitor(
                    competitor_name=competitor_name,
                    weaknesses=weaknesses_list,
                )

            # Return current data if weakness already exists
            return await self.get_competitor(competitor_name)
        except Exception as e:
            logger.error(
                "Failed to add weakness",
                extra={
                    "competitor_name": competitor_name,
                    "weakness": weakness,
                    "error": str(e),
                },
            )
            raise

    async def get_competitor_count(self) -> int:
        """Get total count of competitors.

        Returns:
            Total count of competitors.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT COUNT(*)::int as count
                FROM seo_competitor_intelligence
                """
            )

            return row["count"] if row else 0
        except Exception as e:
            logger.error(
                "Failed to get competitor count",
                extra={"error": str(e)},
            )
            raise

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> dict[str, Any]:
        """Convert a database row to a dictionary.

        Args:
            row: The database record.

        Returns:
            Dictionary representation of the row.
        """
        return {
            "id": row["id"],
            "competitor_name": row["competitor_name"],
            "search_volume": row["search_volume"],
            "difficulty_score": row["difficulty_score"],
            "intent": row["intent"],
            "keywords": dict(row["keywords"]) if row["keywords"] else {},
            "content_gaps": list(row["content_gaps"]) if row["content_gaps"] else [],
            "weaknesses": list(row["weaknesses"]) if row["weaknesses"] else [],
            "last_updated": (
                row["last_updated"].isoformat() if row["last_updated"] else None
            ),
            "created_at": row["created_at"].isoformat(),
        }
