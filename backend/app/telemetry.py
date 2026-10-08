"""OpenTelemetry → Application Insights (el mismo recurso que ve el tracing del proyecto de Foundry).

Agent Framework instrumenta solo las llamadas a modelos y agentes (spans GenAI). Aquí se configura el
exportador y se agrega un span propio por sesión del stand, para ver la demo completa en una traza.
"""

import logging
import os
from contextlib import contextmanager

from .config import Settings

log = logging.getLogger(__name__)
_configured = False


def setup(settings: Settings) -> bool:
    """Configura el exportador si hay connection string. Devuelve True si quedó activo."""
    global _configured
    if _configured:
        return True
    conn = settings.applicationinsights_connection_string or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    if not conn:
        log.info("Telemetría: sin APPLICATIONINSIGHTS_CONNECTION_STRING; solo el panel en vivo.")
        return False
    try:
        from agent_framework.observability import enable_instrumentation
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=conn, enable_live_metrics=True)
        # Prompts y respuestas NO se envían por defecto (datos de visitantes): solo métricas y metadatos.
        enable_instrumentation(enable_sensitive_data=settings.otel_sensitive_data)
        _configured = True
        log.info("Telemetría: OpenTelemetry → Application Insights activo.")
        return True
    except Exception:  # noqa: BLE001 — la telemetría nunca debe tumbar la demo
        log.exception("No se pudo configurar Application Insights")
        return False


@contextmanager
def session_span(session_id: str, mode: str, industria: str):
    """Span raíz de una sesión del stand (no-op si OpenTelemetry no está configurado)."""
    from opentelemetry import trace

    tracer = trace.get_tracer("readymind.aitour")
    with tracer.start_as_current_span("demo.session") as span:
        span.set_attribute("demo.session_id", session_id)
        span.set_attribute("demo.mode", mode)
        span.set_attribute("demo.industria", industria)
        yield span
