import os
import sentry_sdk
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from app.pkg.logger.optional_import import _optional_import


FastAPIInstrumentor = _optional_import(
    "opentelemetry.instrumentation.fastapi", "FastAPIInstrumentor"
)
SQLAlchemyInstrumentor = _optional_import(
    "opentelemetry.instrumentation.sqlalchemy", "SQLAlchemyInstrumentor"
)
RedisInstrumentor = _optional_import(
    "opentelemetry.instrumentation.redis", "RedisInstrumentor"
)
LoggingInstrumentor = _optional_import(
    "opentelemetry.instrumentation.logging", "LoggingInstrumentor"
)


def _setup_otlp_tracing(
    app,
    service_name: str,
    service_version: str = "1.0.0",
    endpoint: str = "127.0.0.1:4317",
):
    """
    Полная настройка OpenTelemetry для FastAPI-приложения.
    """
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    provider = TracerProvider(resource=resource)
    otlp_exporter = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=endpoint, insecure=True)
    )

    provider.add_span_processor(otlp_exporter)
    trace.set_tracer_provider(provider)

    # --- Инструментация ---
    if FastAPIInstrumentor:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        FastAPIInstrumentor().instrument()

    if SQLAlchemyInstrumentor:
        SQLAlchemyInstrumentor().instrument()

    if RedisInstrumentor:
        RedisInstrumentor().instrument()

    if LoggingInstrumentor:
        LoggingInstrumentor().instrument(set_logging_format=True)

    return provider, app


def _setup_sentry_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    sentry_dsn: str | None = None,
    environment: str | None = None,
):
    """
    Настройка Sentry для ошибок и performance tracing.
    """
    if not sentry_dsn:
        return

    sentry_sdk.init(
        dsn=sentry_dsn,
        release=f"{service_name}@{service_version}",
        environment=environment,
        server_name=service_name,
        send_default_pii=True,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0
    )


def setup_tracing(
    app,
    service_name: str,
    service_version: str = "1.0.0",
    otlp_endpoint: str | None = None,
    sentry_dsn: str | None = None,
    environment: str | None = None,
):
    """
    Общая настройка OTEL + Sentry.
    """
    provider = None
    if otlp_endpoint:
        provider, app = _setup_otlp_tracing(app, service_name, service_version, otlp_endpoint)
    if sentry_dsn:
        _setup_sentry_tracing(service_name, service_version, sentry_dsn, environment)
    return provider, app
