"""Máquina de estados de la sesión del stand. Una sesión activa a la vez; reset en < 1 s."""

import asyncio
import contextlib
import logging
import time
import uuid

from . import telemetry
from .config import Settings
from .events import EventBus
from .guard import Guard
from .recorder import Recorder, latest_curated, replay
from .swarm.runner import SwarmRunner
from .voice.backends import make_backend
from .voice.interview import VoiceInterview
from .swarm.schemas import Brief

log = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, bus: EventBus, settings: Settings) -> None:
        self.bus = bus
        self.settings = settings
        self.recorder = Recorder(bus, settings.recordings_dir)
        self.guard = Guard(bus, settings)
        self.task: asyncio.Task | None = None
        self.state = "idle"
        self.session_id: str | None = None
        self.interview: VoiceInterview | None = None

    @property
    def busy(self) -> bool:
        return self.task is not None and not self.task.done()

    async def start(self, brief: Brief) -> str:
        await self.reset(announce=False)
        self.session_id = uuid.uuid4().hex[:10]
        self.bus.start_session(self.session_id)
        mode = self.settings.demo_mode
        if mode == "replay":
            self.task = asyncio.create_task(self._run_replay())
        else:
            self.bus.publish("session.started", session_id=self.session_id, mode=mode, brief=brief.model_dump())
            self.task = asyncio.create_task(self._run_swarm(brief))
        return self.session_id

    async def _run_swarm(self, brief: Brief) -> None:
        self.state = "swarm"
        t0 = time.monotonic()
        with telemetry.session_span(self.session_id or "", self.settings.demo_mode, brief.industria) as span:
            # Gobierno primero: Prompt Shields + tema. Un bloqueo también es parte del show.
            verdict = await self.guard.check(f"{brief.problema}\n{brief.datos}")
            if not verdict.allowed:
                span.set_attribute("demo.blocked", verdict.kind)
                self.state = "done"
                self.bus.publish("guard.blocked", kind=verdict.kind, reply=verdict.reply)
                self.bus.publish("session.ended", status="blocked", swarm_s=0, duration_s=round(time.monotonic() - t0, 1))
                return
            clock = asyncio.create_task(self._clock(t0))
            try:
                state = await SwarmRunner(self.bus, self.settings).run(brief)
                status = state.status
            finally:
                clock.cancel()
            span.set_attribute("demo.status", status)
            if self._should_failover(status, state.arquitectura is None):
                span.set_attribute("demo.failover", True)
                self.bus.publish("governance.event", kind="failover", severity="warning",
                                 title="Foundry no respondió", detail="Se reproduce una sesión grabada real para no detener la demo.")
                self.bus.publish("session.ended", status="failover", swarm_s=round(time.monotonic() - t0, 1), duration_s=round(time.monotonic() - t0, 1))
                await asyncio.sleep(2.5)  # que se alcance a leer el aviso
                await self._run_replay()
                return
        self.state = "done"
        swarm_s = round(time.monotonic() - t0, 1)
        self.bus.publish("session.ended", status=status, swarm_s=swarm_s, duration_s=swarm_s)

    def _should_failover(self, status: str, nothing_produced: bool) -> bool:
        return (
            self.settings.auto_failover
            and self.settings.demo_mode == "live"
            and status in ("error", "timeout")
            and nothing_produced
            and latest_curated(self.settings.recordings_dir) is not None  # siempre hay al menos la semilla
        )

    async def start_replay(self) -> None:
        """Atajo del operador (tecla P): reproduce ya la sesión curada más reciente."""
        await self.reset(announce=False)
        self.task = asyncio.create_task(self._run_replay())

    async def _run_replay(self) -> None:
        path = self.settings.recordings_dir / self.settings.replay_file if self.settings.replay_file else latest_curated(self.settings.recordings_dir)
        if path is None or not path.exists():
            self.bus.publish("governance.event", kind="error", severity="error", title="Sin grabaciones", detail="No hay sesiones curadas para replay.")
            return
        self.state = "replay"
        self.recorder.enabled = False
        try:
            await replay(self.bus, path)
        finally:
            self.recorder.enabled = True
            self.state = "done"

    async def _clock(self, t0: float) -> None:
        while True:
            self.bus.publish("clock", elapsed_s=round(time.monotonic() - t0, 1), budget_s=self.settings.display_budget_s)
            await asyncio.sleep(1)

    def new_interview(self) -> VoiceInterview:
        """Entrevista por voz; al confirmarse el brief arranca la sesión del enjambre."""
        if self.interview is not None:
            self.interview.stop()
        self.state = "interview"
        self.interview = VoiceInterview(self.bus, self.settings, make_backend(self.settings), self.start)
        return self.interview

    async def reset(self, announce: bool = True) -> None:
        if announce and self.interview is not None:
            self.interview.stop()
            self.interview = None
        if self.busy:
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await asyncio.wait_for(self.task, timeout=2)
        self.task = None
        self.state = "idle"
        if announce:
            self.bus.publish("session.reset")
            self.bus.start_session(None)
