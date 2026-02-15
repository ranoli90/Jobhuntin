"""
Log aggregation configuration for structured logging.

Supports multiple backends:
- Local file (development)
- Logtail/Better Stack (production)
- Datadog (enterprise)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from typing import Any

from shared.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "extra") and record.extra:
            log_data["extra"] = record.extra

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add tenant ID if available
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id

        return json.dumps(log_data)


class LogtailHandler(logging.Handler):
    """Handler for Logtail/Better Stack logging."""

    def __init__(self, source_token: str):
        super().__init__()
        self.source_token = source_token
        self._buffer: list[dict] = []
        self._flush_size = 100

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_data = {
                "dt": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
            }

            if hasattr(record, "extra"):
                log_data.update(record.extra)

            self._buffer.append(log_data)

            if len(self._buffer) >= self._flush_size:
                self._flush()
        except Exception:
            self.handleError(record)

    def _flush(self) -> None:
        """Send buffered logs to Logtail."""
        import httpx

        if not self._buffer:
            return

        try:
            httpx.post(
                "https://in.logtail.com",
                headers={
                    "Authorization": f"Bearer {self.source_token}",
                    "Content-Type": "application/json",
                },
                json=self._buffer,
                timeout=5.0,
            )
            self._buffer = []
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to send logs to Logtail: {e}")


def setup_logging() -> None:
    """Configure logging based on environment."""
    settings = get_settings()

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Remove existing handlers
    root_logger.handlers = []

    # JSON formatter for production
    if settings.log_json:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root_logger.addHandler(handler)
    else:
        # Human-readable format for development
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            )
        )
        root_logger.addHandler(handler)

    # Add Logtail handler if configured
    logtail_token = getattr(settings, "logtail_token", None)
    if logtail_token:
        logtail_handler = LogtailHandler(logtail_token)
        logtail_handler.setLevel(logging.INFO)
        root_logger.addHandler(logtail_handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding context to logs."""

    def __init__(self, **kwargs: Any):
        self.context = kwargs
        self._old_factory = None

    def __enter__(self):
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        self._old_factory = old_factory
        return self

    def __exit__(self, *args):
        if self._old_factory:
            logging.setLogRecordFactory(self._old_factory)
