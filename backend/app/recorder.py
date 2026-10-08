"""Grabación y replay de sesiones.

Cada sesión se graba como JSONL de eventos con su tiempo relativo. Las sesiones "buenas"
(completas, sin error y dentro del presupuesto) se copian a recordings/curated/ para el modo replay.
"""

import asyncio
import json
import logging
import shutil
from pathlib import Path

from .events import Event, EventBus

log = logging.getLogger(__name__)


class Recorder:
    def __init__(self, bus: EventBus, directory: Path, max_good_duration_s: float = 120.0) -> None:
        self.dir = directory
        self.curated = directory / "curated"
        self.curated.mkdir(parents=True, exist_ok=True)
        self.max_good = max_good_duration_s
        self._fh = None
        self._path: Path | None = None
        self._had_error = False
        self.enabled = True
        bus.add_listener(self._on_event)

    def _on_event(self, ev: Event) -> None:
        if not self.enabled or ev.type in ("agent.delta", "clock"):
            return
        if ev.type == "session.started":
            self._close()
            self._path = self.dir / f"{ev.session_id}.jsonl"
            self._fh = self._path.open("w", encoding="utf-8")
            self._had_error = False
        if self._fh is None:
            return
        if ev.type == "governance.event" and ev.data.get("kind") in ("error", "timeout"):
            self._had_error = True
        self._fh.write(ev.model_dump_json() + "\n")
        self._fh.flush()
        if ev.type == "session.ended":
            good = ev.data.get("status") == "ok" and not self._had_error and ev.data.get("swarm_s", 999) <= self.max_good
            path = self._path
            self._close()
            if good and path:
                shutil.copy(path, self.curated / path.name)
                log.info("Sesión curada para replay: %s", path.name)
        elif ev.type == "session.reset":
            self._close()

    def _close(self) -> None:
        if self._fh:
            self._fh.close()
        self._fh = None


SEED = Path(__file__).resolve().parent.parent / "seed" / "sesion-semilla.jsonl"


def latest_curated(directory: Path, allow_seed: bool = True) -> Path | None:
    """La sesión curada más reciente; si todavía no hay ninguna, la semilla incluida en el repo."""
    files = sorted((directory / "curated").glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if files:
        return files[-1]
    return SEED if allow_seed and SEED.exists() else None


def load_recording(path: Path) -> list[Event]:
    return [Event.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


async def replay(bus: EventBus, path: Path, speed: float = 1.0) -> None:
    """Re-emite una sesión grabada respetando los tiempos originales."""
    events = load_recording(path)
    if not events:
        return
    session_id = f"replay-{events[0].session_id}"
    bus.start_session(session_id)
    loop = asyncio.get_running_loop()
    t0 = loop.time()
    for ev in events:
        if ev.type in ("share.ready", "lead.received"):
            continue  # en replay no se ofrece el QR de una sesión ajena
        wait = ev.t / speed - (loop.time() - t0)
        if wait > 0:
            await asyncio.sleep(wait)
        data = dict(ev.data)
        if ev.type == "session.started":
            data["mode"] = "replay"
        bus.emit(Event(type=ev.type, data=data, session_id=session_id, t=ev.t))
