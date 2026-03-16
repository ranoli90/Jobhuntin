"""SEO Content Repository - Manages generated SEO content.

Provides methods for storing, retrieving, and deduplicating SEO content
including topic-intent mapping and content hash tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.seo_content")


# Valid intent types from database CHECK constraint
VALID_INTENTS = frozenset(
    {"informational", "commercial", "transactional", "navigational"}
)


class SEOContentRepository:
    """Repository for managing SEO generated content."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        """Initialize the repository with a database connection.

        Args:
            conn: AsyncPG database connection.
        """
        self._conn = conn

    async def check_content_exists(self, url: str) -> bool:
        """Check if content exists for a given URL.

        Args:
            url: The URL to check.

        Returns:
            True if content exists, False otherwise.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT 1
                FROM seo_generated_content
                WHERE url = $1 AND deleted_at IS NULL
                """,
                url,
            )
            return row is not None
        except Exception as e:
            logger.error(
                "Failed to check content existence",
                extra={"url": url, "error": str(e)},
            )
            raise

    async def check_content_hash_exists(self, content_hash: str) -> bool:
        """Check if content with given hash already exists (deduplication).

        Args:
            content_hash: The content hash to check.

        Returns:
            True if duplicate content exists, False otherwise.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT 1
                FROM seo_generated_content
                WHERE content_hash = $1 AND deleted_at IS NULL
                """,
                content_hash,
            )
            return row is not None
        except Exception as e:
            logger.error(
                "Failed to check content hash existence",
                extra={"content_hash": content_hash, "error": str(e)},
            )
            raise

    async def record_generated_content(
        self,
        url: str,
        title: str,
        topic: str,
        intent: str,
        content_hash: str,
        competitor: Optional[str] = None,
        quality_score: Optional[float] = None,
    ) -> dict[str, Any]:
        """Record newly generated SEO content.

        Performs deduplication check before recording.

        Args:
            url: The URL of the content.
            title: The title of the content.
            topic: The topic of the content.
            intent: The search intent (informational, commercial, transactional, navigational).
            content_hash: Hash of content for deduplication.
            competitor: Optional competitor name.
            quality_score: Optional quality score (0-1).

        Returns:
            Created content data.

        Raises:
            ValueError: If intent is invalid or duplicate content exists.
        """
        # Validate intent
        if intent not in VALID_INTENTS:
            raise ValueError(
                f"Invalid intent: {intent}. Must be one of {VALID_INTENTS}"
            )

        # Check for duplicate URL
        if await self.check_content_exists(url):
            raise ValueError(f"Content already exists for URL: {url}")

        # Check for duplicate content hash
        if await self.check_content_hash_exists(content_hash):
            raise ValueError(f"Duplicate content detected with hash: {content_hash}")

        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO seo_generated_content (
                    url, title, topic, intent, competitor,
                    content_hash, quality_score, google_indexed
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, FALSE)
                RETURNING id, url, title, topic, intent, competitor,
                          content_hash, quality_score, google_indexed,
                          indexed_at, clicks, impressions, ctr, position,
                          last_updated, deleted_at, created_at, updated_at
                """,
                url,
                title,
                topic,
                intent,
                competitor,
                content_hash,
                quality_score,
            )

            logger.info(
                "Recorded SEO content",
                extra={"url": url, "topic": topic, "intent": intent},
            )

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to record SEO content",
                extra={
                    "url": url,
                    "topic": topic,
                    "intent": intent,
                    "error": str(e),
                },
            )
            raise

    async def get_content_by_topic_intent(
        self,
        topic: str,
        intent: str,
        competitor: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get content by topic and intent combination.

        Useful for finding similar content or checking coverage.

        Args:
            topic: The topic to search for.
            intent: The intent to filter by.
            competitor: Optional competitor to filter by.
            limit: Maximum number of results.

        Returns:
            List of content matching the criteria.
        """
        # Validate intent
        if intent not in VALID_INTENTS:
            raise ValueError(
                f"Invalid intent: {intent}. Must be one of {VALID_INTENTS}"
            )

        try:
            query = """
                SELECT id, url, title, topic, intent, competitor,
                       content_hash, quality_score, google_indexed,
                       indexed_at, clicks, impressions, ctr, position,
                       last_updated, deleted_at, created_at, updated_at
                FROM seo_generated_content
                WHERE topic = $1
                  AND intent = $2
                  AND deleted_at IS NULL
            """

            params: list[Any] = [topic, intent]
            param_index = 3

            if competitor:
                query += f" AND competitor = ${param_index}"
                params.append(competitor)
                param_index += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_index}"
            params.append(limit)

            rows = await self._conn.fetch(query, *params)

            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(
                "Failed to get content by topic intent",
                extra={"topic": topic, "intent": intent, "error": str(e)},
            )
            raise

    async def get_content_by_url(self, url: str) -> Optional[dict[str, Any]]:
        """Get content by URL.

        Args:
            url: The URL to search for.

        Returns:
            Content data or None if not found.
        """
        try:
            row = await self._conn.fetchrow(
                """
                SELECT id, url, title, topic, intent, competitor,
                       content_hash, quality_score, google_indexed,
                       indexed_at, clicks, impressions, ctr, position,
                       last_updated, deleted_at, created_at, updated_at
                FROM seo_generated_content
                WHERE url = $1 AND deleted_at IS NULL
                """,
                url,
            )

            if not row:
                return None

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to get content by URL",
                extra={"url": url, "error": str(e)},
            )
            raise

    async def update_google_indexing(
        self, url: str, indexed: bool = True
    ) -> Optional[dict[str, Any]]:
        """Update Google indexing status for content.

        Args:
            url: The URL of the content.
            indexed: Whether the content is indexed.

        Returns:
            Updated content data or None if not found.
        """
        try:
            row = await self._conn.fetchrow(
                """
                UPDATE seo_generated_content
                SET google_indexed = $2,
                    indexed_at = CASE WHEN $2 = TRUE THEN NOW() ELSE indexed_at END,
                    updated_at = NOW()
                WHERE url = $1 AND deleted_at IS NULL
                RETURNING id, url, title, topic, intent, competitor,
                          content_hash, quality_score, google_indexed,
                          indexed_at, clicks, impressions, ctr, position,
                          last_updated, deleted_at, created_at, updated_at
                """,
                url,
                indexed,
            )

            if not row:
                return None

            logger.info(
                "Updated Google indexing status",
                extra={"url": url, "indexed": indexed},
            )

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to update Google indexing",
                extra={"url": url, "indexed": indexed, "error": str(e)},
            )
            raise

    async def update_performance_metrics(
        self,
        url: str,
        clicks: Optional[int] = None,
        impressions: Optional[int] = None,
        ctr: Optional[float] = None,
        position: Optional[float] = None,
    ) -> Optional[dict[str, Any]]:
        """Update performance metrics for content.

        Args:
            url: The URL of the content.
            clicks: Number of clicks.
            impressions: Number of impressions.
            ctr: Click-through rate.
            position: Average search position.

        Returns:
            Updated content data or None if not found.
        """
        try:
            updates = ["updated_at = NOW()", "last_updated = NOW()"]
            params: list[Any] = [url]
            param_index = 2

            if clicks is not None:
                updates.append(f"clicks = ${param_index}")
                params.append(clicks)
                param_index += 1

            if impressions is not None:
                updates.append(f"impressions = ${param_index}")
                params.append(impressions)
                param_index += 1

            if ctr is not None:
                updates.append(f"ctr = ${param_index}")
                params.append(ctr)
                param_index += 1

            if position is not None:
                updates.append(f"position = ${param_index}")
                params.append(position)
                param_index += 1

            query = f"""
                UPDATE seo_generated_content
                SET {', '.join(updates)}
                WHERE url = $1 AND deleted_at IS NULL
                RETURNING id, url, title, topic, intent, competitor,
                          content_hash, quality_score, google_indexed,
                          indexed_at, clicks, impressions, ctr, position,
                          last_updated, deleted_at, created_at, updated_at
            """

            row = await self._conn.fetchrow(query, *params)

            if not row:
                return None

            return self._row_to_dict(row)
        except Exception as e:
            logger.error(
                "Failed to update performance metrics",
                extra={"url": url, "error": str(e)},
            )
            raise

    async def soft_delete_content(self, url: str) -> bool:
        """Soft delete content by URL.

        Args:
            url: The URL of the content to delete.

        Returns:
            True if content was deleted, False if not found.
        """
        try:
            result = await self._conn.execute(
                """
                UPDATE seo_generated_content
                SET deleted_at = NOW(), updated_at = NOW()
                WHERE url = $1 AND deleted_at IS NULL
                """,
                url,
            )

            deleted = result == "UPDATE 1"

            if deleted:
                logger.info(
                    "Soft deleted SEO content",
                    extra={"url": url},
                )

            return deleted
        except Exception as e:
            logger.error(
                "Failed to soft delete content",
                extra={"url": url, "error": str(e)},
            )
            raise

    async def get_content_by_topic(
        self, topic: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get all content for a specific topic.

        Args:
            topic: The topic to search for.
            limit: Maximum number of results.

        Returns:
            List of content matching the topic.
        """
        try:
            rows = await self._conn.fetch(
                """
                SELECT id, url, title, topic, intent, competitor,
                       content_hash, quality_score, google_indexed,
                       indexed_at, clicks, impressions, ctr, position,
                       last_updated, deleted_at, created_at, updated_at
                FROM seo_generated_content
                WHERE topic = $1 AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT $2
                """,
                topic,
                limit,
            )

            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(
                "Failed to get content by topic",
                extra={"topic": topic, "error": str(e)},
            )
            raise

    async def get_all_topics(self) -> list[str]:
        """Get all unique topics that have content.

        Returns:
            List of unique topics.
        """
        try:
            rows = await self._conn.fetch(
                """
                SELECT DISTINCT topic
                FROM seo_generated_content
                WHERE deleted_at IS NULL
                ORDER BY topic
                """
            )

            return [row["topic"] for row in rows]
        except Exception as e:
            logger.error(
                "Failed to get all topics",
                extra={"error": str(e)},
            )
            raise

    async def get_content_count(
        self, topic: Optional[str] = None, intent: Optional[str] = None
    ) -> int:
        """Get count of content entries.

        Args:
            topic: Optional topic filter.
            intent: Optional intent filter.

        Returns:
            Count of content entries.
        """
        try:
            query = "SELECT COUNT(*)::int as count FROM seo_generated_content WHERE deleted_at IS NULL"
            params: list[Any] = []

            if topic:
                params.append(topic)
                query += f" AND topic = ${len(params)}"

            if intent:
                if intent not in VALID_INTENTS:
                    raise ValueError(
                        f"Invalid intent: {intent}. Must be one of {VALID_INTENTS}"
                    )
                params.append(intent)
                query += f" AND intent = ${len(params)}"

            row = await self._conn.fetchrow(query, *params)

            return row["count"] if row else 0
        except Exception as e:
            logger.error(
                "Failed to get content count",
                extra={"topic": topic, "intent": intent, "error": str(e)},
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
            "url": row["url"],
            "title": row["title"],
            "topic": row["topic"],
            "intent": row["intent"],
            "competitor": row["competitor"],
            "content_hash": row["content_hash"],
            "quality_score": float(row["quality_score"]) if row["quality_score"] else None,
            "google_indexed": row["google_indexed"],
            "indexed_at": (
                row["indexed_at"].isoformat() if row["indexed_at"] else None
            ),
            "clicks": row["clicks"],
            "impressions": row["impressions"],
            "ctr": float(row["ctr"]) if row["ctr"] else None,
            "position": float(row["position"]) if row["position"] else None,
            "last_updated": (
                row["last_updated"].isoformat() if row["last_updated"] else None
            ),
            "deleted_at": (
                row["deleted_at"].isoformat() if row["deleted_at"] else None
            ),
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }
