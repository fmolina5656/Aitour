"""Máquina de estados de la sesión del stand. Una sesión activa a la vez; reset en < 1 s."""

import asyncio
import contextlib
import logging
import time
import uuid

from .config import Settings
from .events import EventBus
from .recorder import Recorder, latest_curated, replay
from .swarm.runner import SwarmRunner
from .swarm.schemas import Brief

log = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, bus: EventBus, settings: Settings) -> None:
        self.bus = bus
        self.settings = settings
        self.recorder = Recorder(bus, settings.recordings_dir)
        self.task: asyncio.Task | None = None
        self.state = "idle"
        self.session_id: str | None = None

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
        clock = asyncio.create_task(self._clock(t0))
        try:
            state = await SwarmRunner(self.bus, self.settings).run(brief)
            status = state.status
        finally:
            clock.cancel()
        self.state = "done"
        swarm_s = round(time.monotonic() - t0, 1)
        self.bus.publish("session.ended", status=status, swarm_s=swarm_s, duration_s=swarm_s)

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

    async def reset(self, announce: bool = True) -> None:
        if self.busy:
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await asyncio.wait_for(self.task, timeout=2)
        self.task = None
        self.state = "idle"
        if announce:
            self.bus.publish("session.reset")
            self.bus.start_session(None)
