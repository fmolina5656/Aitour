"""Bus de eventos tipados. Todo lo que se ve en pantalla es un evento de este bus.

El grabador persiste estos mismos eventos, así el replay reutiliza la UI por construcción.
"""

import asyncio
import time
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

# Tipos de evento que consume el frontend (ver frontend/src/types.ts)
EVENT_TYPES = {
    "session.started",  # {session_id, mode, brief}
    "session.ended",  # {status: ok|timeout|error|reset, duration_s}
    "session.reset",  # {}
    "agent.thinking",  # {agent}
    "agent.delta",  # {agent, burbuja}  (burbuja parcial mientras streamea)
    "agent.message",  # {agent, burbuja, detalle, round}
    "agent.objection",  # {de, para, motivo, propuesta}
    "trace.span",  # {agent, model, input_tokens, output_tokens, latency_ms, cost_usd, session_cost_usd}
    "governance.event",  # {kind, severity, title, detail}
    "guard.blocked",  # {kind: jailbreak|off_topic, reply}
    "voice.started",  # {mode}
    "voice.user",  # {text}  transcripción de lo que dijo el visitante
    "voice.agent",  # {text, final}  lo que dice la recepcionista
    "voice.state",  # {value}
    "voice.ended",  # {confirmed}
    "brief.proposed",  # {brief}  "esto entendí"
    "brief.confirmed",  # {brief, via}
    "share.ready",  # {session_id, qr_url}  QR para dejar los datos y recibir el PDF
    "mode.changed",  # {mode}
    "lead.received",  # {envio}  sin datos personales: es la pantalla pública
    "artifact.diagram",  # {mermaid, version}
    "artifact.cost",  # {items, total_usd, supuestos, disclaimer}
    "artifact.risk",  # {datos_sensibles, regulacion, mitigaciones}
    "artifact.onepager",  # {...}
    "clock",  # {elapsed_s, budget_s}
}


class Event(BaseModel):
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None
    ts: float = Field(default_factory=time.time)
    # segundos desde el inicio de la sesión (lo usa el replay para respetar los tiempos)
    t: float = 0.0


Subscriber = Callable[[Event], Any]


class EventBus:
    """Pub/sub en memoria. Guarda los eventos de la sesión actual para clientes que se conectan tarde."""

    def __init__(self) -> None:
        self._queues: set[asyncio.Queue[Event]] = set()
        self._listeners: list[Subscriber] = []
        self.history: list[Event] = []
        self.session_id: str | None = None
        self._t0 = time.monotonic()

    def start_session(self, session_id: str) -> None:
        self.session_id = session_id
        self.history = []
        self._t0 = time.monotonic()

    def add_listener(self, fn: Subscriber) -> None:
        self._listeners.append(fn)

    def subscribe(self) -> asyncio.Queue[Event]:
        q: asyncio.Queue[Event] = asyncio.Queue(maxsize=2000)
        self._queues.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[Event]) -> None:
        self._queues.discard(q)

    def publish(self, type: str, session_id: str | None = None, t: float | None = None, **data: Any) -> Event:
        if type not in EVENT_TYPES:
            raise ValueError(f"Tipo de evento desconocido: {type}")
        ev = Event(
            type=type,
            data=data,
            session_id=session_id or self.session_id,
            t=round(time.monotonic() - self._t0 if t is None else t, 3),
        )
        self.emit(ev)
        return ev

    def emit(self, ev: Event) -> None:
        if ev.type != "agent.delta":  # los deltas no hacen falta para reconstruir el estado
            self.history.append(ev)
        for q in list(self._queues):
            try:
                q.put_nowait(ev)
            except asyncio.QueueFull:  # cliente lento: se descarta, no bloquea la demo
                pass
        for fn in self._listeners:
            fn(ev)
