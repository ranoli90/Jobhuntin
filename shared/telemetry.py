"""OpenTelemetry integration for distributed tracing.

Configures:
- TracerProvider with Resource attributes (service name, env)
- OTLP Exporter (if endpoint provided)
- Console Exporter (optional for debugging)
- FastAPI Instrumentation
- Helper decorators for manual tracing
"""

import functools
import os
from collections.abc import Callable
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositeHTTPPropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_NAME,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.telemetry")

_tracer_initialized = False


def setup_telemetry(service_name: str, app=None) -> None:
    """Initialize OpenTelemetry for the application.

    Args:
        service_name: Name of the service (e.g. sorce-api, sorce-worker)
        app: FastAPI app instance (optional, for auto-instrumentation)

    """
    global _tracer_initialized
    settings = get_settings()

    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otel_endpoint:
        logger.info("OpenTelemetry disabled: OTEL_EXPORTER_OTLP_ENDPOINT not set")
        return

    if _tracer_initialized:
        logger.debug("OpenTelemetry already initialized")
        return

    try:
        resource = Resource.create(
            {
                SERVICE_NAME: service_name,
                SERVICE_VERSION: "0.4.0",
                DEPLOYMENT_ENVIRONMENT: settings.env.value,
            }
        )

        provider = TracerProvider(resource=resource)

        otlp_exporter = OTLPSpanExporter()
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

        if os.getenv("OTEL_CONSOLE_EXPORTER") == "true":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)

        # M4: Distributed Tracing - Set up W3C Trace Context propagation
        # This enables trace context propagation across service boundaries
        propagator = CompositeHTTPPropagator([TraceContextTextMapPropagator()])
        set_global_textmap(propagator)
        logger.info("W3C Trace Context propagation enabled")

        if app:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            # M4: Enhanced FastAPI instrumentation with custom attributes
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=provider,
                excluded_urls="health,healthz,/metrics",  # Exclude health checks
            )

        # M4: Instrument HTTP clients for distributed tracing
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

            HTTPXClientInstrumentor().instrument(tracer_provider=provider)
            logger.info("HTTPX client instrumentation enabled")
        except ImportError:
            logger.warning("HTTPX instrumentation not available (httpx not installed)")

        # M4: Instrument database queries for distributed tracing
        try:
            from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

            AsyncPGInstrumentor().instrument(tracer_provider=provider)
            logger.info("AsyncPG database instrumentation enabled")
        except ImportError:
            logger.warning("AsyncPG instrumentation not available")

        # M4: Instrument Redis for distributed tracing
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor

            RedisInstrumentor().instrument(tracer_provider=provider)
            logger.info("Redis instrumentation enabled")
        except ImportError:
            logger.debug("Redis instrumentation not available (optional)")

        _tracer_initialized = True
        logger.info(f"OpenTelemetry initialized for {service_name} (distributed tracing + metrics)")

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")


def get_tracer(name: str):
    """Get a tracer instance for manual span creation."""
    return trace.get_tracer(name)


def traced(
    name: str | None = None,
    attributes: dict[str, str] | None = None,
) -> Callable:
    """Decorator to trace a function with OpenTelemetry.

    Usage:
        @traced("my_operation")
        async def my_function():
            ...

        @traced(attributes={"operation.type": "database"})
        async def db_query():
            ...
    """

    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class SpanContext:
    """Context manager for manual span creation."""

    def __init__(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        tracer_name: str | None = None,
    ):
        self.name = name
        self.attributes = attributes or {}
        self.tracer_name = tracer_name
        self.span = None

    def __enter__(self):
        tracer = get_tracer(self.tracer_name or __name__)
        self.span = tracer.start_span(self.name)
        self.span.__enter__()
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
        else:
            self.span.set_status(Status(StatusCode.OK))
        return self.span.__exit__(exc_type, exc_val, exc_tb)

    def set_attribute(self, key: str, value: Any) -> None:
        if self.span:
            self.span.set_attribute(key, value)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        if self.span:
            self.span.add_event(name, attributes or {})
