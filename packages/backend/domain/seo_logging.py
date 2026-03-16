"""SEO Logger - Database logging for SEO operations.

Provides Winston-style logging levels (debug, info, warn, error) with
database persistence for SEO operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.seo_logging")


class SEOLogLevel(Enum):
    """Winston-style log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class SEOLogger:
    """Database logger for SEO operations with Winston-style levels."""

    # Valid log levels
    VALID_LEVELS = frozenset(level.value for level in SEOLogLevel)

    def __init__(self, conn: asyncpg.Connection) -> None:
        """Initialize the logger with a database connection.

        Args:
            conn: AsyncPG database connection.
        """
        self._conn = conn

    async def log(
        self,
        level: str,
        message: str,
        meta: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Log a message at the specified level.

        Args:
            level: Log level (debug, info, warn, error).
            message: The log message.
            meta: Optional metadata dictionary.

        Returns:
            Created log entry.

        Raises:
            ValueError: If level is invalid.
        """
        # Validate level
        if level not in self.VALID_LEVELS:
            raise ValueError(
                f"Invalid log level: {level}. Must be one of {self.VALID_LEVELS}"
            )

        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO seo_logs (level, message, meta)
                VALUES ($1, $2, $3)
                RETURNING id, level, message, meta, created_at
                """,
                level,
                message,
                meta,
            )

            # Also log to standard logger for visibility
            log_func = getattr(logger, level, logger.info)
            log_func(
                f"[SEO] {message}",
                extra={"seo_log_meta": meta} if meta else None,
            )

            return {
                "id": row["id"],
                "level": row["level"],
                "message": row["message"],
                "meta": dict(row["meta"]) if row["meta"] else {},
                "created_at": row["created_at"].isoformat(),
            }
        except Exception as e:
            # Don't raise - logging should never break the app
            logger.error(
                "Failed to write SEO log to database",
                extra={"level": level, "message": message, "error": str(e)},
            )
            # Return a fallback log entry
            return {
                "id": 0,
                "level": level,
                "message": message,
                "meta": meta or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "error": "Failed to persist to database",
            }

    async def debug(self, message: str, meta: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Log a debug message.

        Args:
            message: The log message.
            meta: Optional metadata dictionary.

        Returns:
            Created log entry.
        """
        return await self.log(SEOLogLevel.DEBUG.value, message, meta)

    async def info(self, message: str, meta: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Log an info message.

        Args:
            message: The log message.
            meta: Optional metadata dictionary.

        Returns:
            Created log entry.
        """
        return await self.log(SEOLogLevel.INFO.value, message, meta)

    async def warn(self, message: str, meta: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Log a warning message.

        Args:
            message: The log message.
            meta: Optional metadata dictionary.

        Returns:
            Created log entry.
        """
        return await self.log(SEOLogLevel.WARN.value, message, meta)

    async def error(self, message: str, meta: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Log an error message.

        Args:
            message: The log message.
            meta: Optional metadata dictionary.

        Returns:
            Created log entry.
        """
        return await self.log(SEOLogLevel.ERROR.value, message, meta)

    async def get_recent_logs(
        self,
        level: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get recent log entries.

        Args:
            level: Optional log level filter.
            limit: Maximum number of results.

        Returns:
            List of log entries.
        """
        try:
            query = """
                SELECT id, level, message, meta, created_at
                FROM seo_logs
                WHERE 1=1
            """
            params: list[Any] = []
            param_index = 1

            if level:
                if level not in self.VALID_LEVELS:
                    raise ValueError(
                        f"Invalid log level: {level}. Must be one of {self.VALID_LEVELS}"
                    )
                query += f" AND level = ${param_index}"
                params.append(level)
                param_index += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_index}"
            params.append(limit)

            rows = await self._conn.fetch(query, *params)

            return [
                {
                    "id": row["id"],
                    "level": row["level"],
                    "message": row["message"],
                    "meta": dict(row["meta"]) if row["meta"] else {},
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(
                "Failed to get recent logs",
                extra={"level": level, "error": str(e)},
            )
            raise

    async def get_logs_by_level(
        self,
        level: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get logs filtered by level.

        Args:
            level: The log level to filter by.
            limit: Maximum number of results.

        Returns:
            List of log entries.
        """
        if level not in self.VALID_LEVELS:
            raise ValueError(
                f"Invalid log level: {level}. Must be one of {self.VALID_LEVELS}"
            )

        return await self.get_recent_logs(level=level, limit=limit)

    async def get_error_logs(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get all error logs.

        Args:
            limit: Maximum number of results.

        Returns:
            List of error log entries.
        """
        return await self.get_recent_logs(level=SEOLogLevel.ERROR.value, limit=limit)

    async def search_logs(
        self,
        search_term: str,
        level: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Search logs by message content.

        Args:
            search_term: The search term to look for.
            level: Optional log level filter.
            limit: Maximum number of results.

        Returns:
            List of matching log entries.
        """
        try:
            query = """
                SELECT id, level, message, meta, created_at
                FROM seo_logs
                WHERE message ILIKE $1
            """
            params: list[Any] = [f"%{search_term}%"]
            param_index = 2

            if level:
                if level not in self.VALID_LEVELS:
                    raise ValueError(
                        f"Invalid log level: {level}. Must be one of {self.VALID_LEVELS}"
                    )
                query += f" AND level = ${param_index}"
                params.append(level)
                param_index += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_index}"
            params.append(limit)

            rows = await self._conn.fetch(query, *params)

            return [
                {
                    "id": row["id"],
                    "level": row["level"],
                    "message": row["message"],
                    "meta": dict(row["meta"]) if row["meta"] else {},
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(
                "Failed to search logs",
                extra={"search_term": search_term, "error": str(e)},
            )
            raise

    async def get_logs_by_timerange(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        level: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get logs within a time range.

        Args:
            start_time: Start of the time range.
            end_time: End of the time range (defaults to now).
            level: Optional log level filter.
            limit: Maximum number of results.

        Returns:
            List of log entries.
        """
        try:
            end_time = end_time or datetime.now(timezone.utc)

            query = """
                SELECT id, level, message, meta, created_at
                FROM seo_logs
                WHERE created_at BETWEEN $1 AND $2
            """
            params: list[Any] = [start_time, end_time]
            param_index = 3

            if level:
                if level not in self.VALID_LEVELS:
                    raise ValueError(
                        f"Invalid log level: {level}. Must be one of {self.VALID_LEVELS}"
                    )
                query += f" AND level = ${param_index}"
                params.append(level)
                param_index += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_index}"
            params.append(limit)

            rows = await self._conn.fetch(query, *params)

            return [
                {
                    "id": row["id"],
                    "level": row["level"],
                    "message": row["message"],
                    "meta": dict(row["meta"]) if row["meta"] else {},
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(
                "Failed to get logs by time range",
                extra={"start_time": start_time, "end_time": end_time, "error": str(e)},
            )
            raise

    async def get_log_count(self, level: Optional[str] = None) -> int:
        """Get total count of log entries.

        Args:
            level: Optional log level filter.

        Returns:
            Total count of log entries.
        """
        try:
            query = "SELECT COUNT(*)::int as count FROM seo_logs"
            params: list[Any] = []

            if level:
                if level not in self.VALID_LEVELS:
                    raise ValueError(
                        f"Invalid log level: {level}. Must be one of {self.VALID_LEVELS}"
                    )
                query += " WHERE level = $1"
                params.append(level)

            row = await self._conn.fetchrow(query, *params)

            return row["count"] if row else 0
        except Exception as e:
            logger.error(
                "Failed to get log count",
                extra={"level": level, "error": str(e)},
            )
            raise

    async def clear_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days.

        Args:
            days: Number of days to retain.

        Returns:
            Number of deleted log entries.
        """
        try:
            result = await self._conn.execute(
                """
                DELETE FROM seo_logs
                WHERE created_at < NOW() - INTERVAL '1 day' * $1
                """,
                days,
            )

            # Parse the result to get delete count
            deleted = int(result.split()[-1]) if result else 0

            logger.info(
                "Cleared old SEO logs",
                extra={"days": days, "deleted": deleted},
            )

            return deleted
        except Exception as e:
            logger.error(
                "Failed to clear old logs",
                extra={"days": days, "error": str(e)},
            )
            raise
