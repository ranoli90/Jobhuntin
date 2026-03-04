"""Log aggregation - DEPRECATED: Use shared.logging_config instead.

This module is kept for backward compatibility. All new code should use
shared.logging_config which provides better structured logging with
contextvars-based correlation.
"""

from __future__ import annotations

import logging
import warnings

# Re-export from logging_config to avoid duplication
from shared.logging_config import (
    JSONFormatter,
    LogContext,
    get_logger,
    sanitize_for_log,
    setup_logging,
)

warnings.warn(
    "shared.log_aggregation is deprecated. Use shared.logging_config instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "JSONFormatter",
    "LogContext",
    "get_logger",
    "sanitize_for_log",
    "setup_logging",
]


class LogtailHandler(logging.Handler):
    """Handler for Logtail/Better Stack logging.

    DEPRECATED: Use external log shipping (e.g., Fluentd, Vector) instead.
    """

    def __init__(self, source_token: str):
        super().__init__()
        self.source_token = source_token
        self._logger = logging.getLogger(__name__)
        self._logger.warning(
            "LogtailHandler is deprecated. Use external log shipping instead."
        )

    def emit(self, record: logging.LogRecord) -> None:
        # No-op: log shipping should be handled by external agents
        pass
