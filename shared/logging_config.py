"""Part 3: Observability – Structured Logging.

Provides:
  - setup_logging(env, log_level, log_json): configures root logger
  - JSON formatter for staging/prod, human-readable for local
  - LogContext: contextvars-based correlation (application_id, job_id, user_id, env)
  - get_logger(name): returns a logger that auto-injects context
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Correlation context (async-safe via contextvars)
# ---------------------------------------------------------------------------

_ctx_application_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "application_id", default=None
)
_ctx_job_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "job_id", default=None
)
_ctx_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_id", default=None
)
_ctx_tenant_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tenant_id", default=None
)
_ctx_env: contextvars.ContextVar[str] = contextvars.ContextVar("env", default="local")


class LogContext:
    """Set/clear correlation identifiers for the current async task."""

    @staticmethod
    def set(
        *,
        application_id: str | None = None,
        job_id: str | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
        env: str | None = None,
    ) -> None:
        if application_id is not None:
            _ctx_application_id.set(application_id)
        if job_id is not None:
            _ctx_job_id.set(job_id)
        if user_id is not None:
            _ctx_user_id.set(user_id)
        if tenant_id is not None:
            _ctx_tenant_id.set(tenant_id)
        if env is not None:
            _ctx_env.set(env)

    @staticmethod
    def clear() -> None:
        _ctx_application_id.set(None)
        _ctx_job_id.set(None)
        _ctx_user_id.set(None)
        _ctx_tenant_id.set(None)

    @staticmethod
    def as_dict() -> dict[str, Any]:
        d: dict[str, Any] = {"env": _ctx_env.get()}
        tenant_id = _ctx_tenant_id.get()
        if tenant_id:
            d["tenant_id"] = tenant_id
        app_id = _ctx_application_id.get()
        if app_id:
            d["application_id"] = app_id
        job_id = _ctx_job_id.get()
        if job_id:
            d["job_id"] = job_id
        user_id = _ctx_user_id.get()
        if user_id:
            d["user_id"] = user_id
        return d


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line with correlation context.

    Automatically sanitizes PII from the ``extra`` dict attached to log records
    so that callers don't need to remember to call ``sanitize_for_log()``
    manually.
    
    M4: Enhanced with OpenTelemetry trace context for distributed tracing.
    """

    def format(self, record: logging.LogRecord) -> str:
        # M4: Add OpenTelemetry trace context to logs
        trace_context = {}
        try:
            from opentelemetry import trace
            
            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                span_ctx = span.get_span_context()
                trace_context = {
                    "trace_id": format(span_ctx.trace_id, "032x"),
                    "span_id": format(span_ctx.span_id, "016x"),
                }
        except Exception:
            pass  # OpenTelemetry not available or not initialized
        
        log_entry: dict[str, Any] = {
            **trace_context,  # M4: Include trace context in logs
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        log_entry.update(LogContext.as_dict())

        # Auto-sanitize any extra dict attached via logger.info(..., extra={...})
        if hasattr(record, "__dict__"):
            extra = {
                k: v
                for k, v in record.__dict__.items()
                if k not in _LOG_RECORD_BUILTIN_ATTRS and not k.startswith("_")
            }
            if extra:
                log_entry["extra"] = _sanitize_nested(extra)

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


# Built-in LogRecord attributes that should not appear in ``extra``
_LOG_RECORD_BUILTIN_ATTRS = frozenset(
    {
        "name",
        "msg",
        "args",
        "created",
        "relativeCreated",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "pathname",
        "filename",
        "module",
        "levelno",
        "levelname",
        "thread",
        "threadName",
        "process",
        "processName",
        "msecs",
        "message",
        "taskName",
    }
)


# ---------------------------------------------------------------------------
# Human-readable formatter (local dev)
# ---------------------------------------------------------------------------


class HumanFormatter(logging.Formatter):
    """Readable format with context prefix for local development."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = LogContext.as_dict()
        ctx_str = " ".join(f"{k}={v}" for k, v in ctx.items() if v)
        prefix = f"[{ctx_str}] " if ctx_str else ""
        base = super().format(record)
        return f"{prefix}{base}"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def setup_logging(
    env: str = "local",
    log_level: str = "INFO",
    log_json: bool = False,
) -> None:
    """Configure the root logger for the process."""
    LogContext.set(env=env)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if log_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            HumanFormatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (context is injected automatically by the formatter)."""
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# PII sanitization for log payloads
# ---------------------------------------------------------------------------

_PII_KEYS = frozenset(
    {
        "full_name",
        "first_name",
        "last_name",
        "email",
        "phone",
        "location",
        "linkedin_url",
        "portfolio_url",
        "address",
        "answer",  # hold-question answers may contain PII
    }
)


def _sanitize_nested(data: Any) -> Any:
    """Recursively sanitize PII keys in dicts. Used by the JSON formatter."""
    if isinstance(data, dict):
        return sanitize_for_log(data)
    if isinstance(data, (list, tuple)):
        return [_sanitize_nested(item) for item in data]
    return data


def sanitize_for_log(data: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of `data` with PII-bearing keys replaced by '[REDACTED]'.
    Recurses into nested dicts but not lists (for performance).
    """
    result: dict[str, Any] = {}
    for k, v in data.items():
        if k in _PII_KEYS:
            result[k] = "[REDACTED]"
        elif isinstance(v, dict):
            result[k] = sanitize_for_log(v)
        else:
            result[k] = v
    return result
