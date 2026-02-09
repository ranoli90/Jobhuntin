"""
OpenTelemetry integration for distributed tracing.

Configures:
- TracerProvider with Resource attributes (service name, env)
- OTLP Exporter (if endpoint provided)
- Console Exporter (optional for debugging)
- FastAPI Instrumentation
"""
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.telemetry")

def setup_telemetry(service_name: str, app=None) -> None:
    """
    Initialize OpenTelemetry for the application.
    
    Args:
        service_name: Name of the service (e.g. sorce-api, sorce-worker)
        app: FastAPI app instance (optional, for auto-instrumentation)
    """
    settings = get_settings()
    
    # Check if disabled (or no endpoint configured)
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otel_endpoint:
        logger.info("OpenTelemetry disabled: OTEL_EXPORTER_OTLP_ENDPOINT not set")
        return

    try:
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: "0.4.0",
            DEPLOYMENT_ENVIRONMENT: settings.env.value,
        })

        provider = TracerProvider(resource=resource)
        
        # OTLP Exporter (HTTP/Protobuf default)
        otlp_exporter = OTLPSpanExporter()
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        
        # Optional: Console exporter for local debug if strictly requested
        if os.getenv("OTEL_CONSOLE_EXPORTER") == "true":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI
        if app:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

        # Instrument HTTPX (for LLM/Adzuna calls)
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument(tracer_provider=provider)
        except ImportError:
            pass

        # Instrument AsyncPG (for DB calls)
        try:
            from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
            AsyncPGInstrumentor().instrument(tracer_provider=provider)
        except ImportError:
            pass
            
        logger.info(f"OpenTelemetry initialized for {service_name}")
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")

def get_tracer(name: str):
    return trace.get_tracer(name)
