"""Entrevista por voz: relay navegador ⇄ backend ⇄ Microsoft Foundry voice agent.

Protocolo con el navegador (WebSocket /ws/voice):
  navegador → backend : binario = PCM16 mono 24 kHz · JSON {"type":"text","text"} (respuesta tecleada),
                        {"type":"confirm"} (botón "sí"), {"type":"stop"}
  backend → navegador : binario = PCM16 24 kHz de la recepcionista · JSON {"type":"interrupt"} (cortar
                        reproducción), {"type":"state","value":...}, {"type":"closed"}
Lo que ve la pantalla grande va por el bus: voice.started / voice.user / voice.agent / brief.proposed / voice.ended.

Presupuesto: a los INTERVIEW_SOFT_LIMIT_S se le pide a la recepcionista cerrar; a los HARD se arma el brief
con lo transcrito y se arranca igual. El enjambre nunca espera a la voz.
"""

import asyncio
import base64
import contextlib
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from fastapi import WebSocket, WebSocketDisconnect

from ..config import Settings
from ..events import EventBus
from ..swarm.schemas import Brief

log = logging.getLogger(__name__)

OnConfirmed = Callable[[Brief], Awaitable[None]]


class VoiceBackend(Protocol):
    async def start(self) -> None: ...
    async def send_audio(self, pcm: bytes) -> None: ...
    async def send_text(self, text: str) -> None: ...
    async def nudge(self, instruction: str) -> None: ...
    async def tool_result(self, call_id: str, output: str) -> None: ...
    def events(self) -> Any: ...  # AsyncIterator[dict]
    async def close(self) -> None: ...


class VoiceInterview:
    def __init__(self, bus: EventBus, settings: Settings, backend: VoiceBackend, on_confirmed: OnConfirmed) -> None:
        self.bus = bus
        self.settings = settings
        self.backend = backend
        self.on_confirmed = on_confirmed
        self.brief: Brief | None = None
        self.user_lines: list[str] = []
        self.done = asyncio.Event()
        self._agent_text = ""
        self._confirmed = False
        self._ws: WebSocket | None = None

    # --- ciclo de vida -----------------------------------------------------------------------------
    async def run(self, ws: WebSocket) -> None:
        self._ws = ws
        self.bus.publish("voice.started", mode=self.settings.demo_mode)
        await self.backend.start()
        tasks = [
            asyncio.create_task(self._from_browser(ws)),
            asyncio.create_task(self._from_agent()),
            asyncio.create_task(self._budget()),
        ]
        try:
            await self.done.wait()
        finally:
            for t in tasks:
                t.cancel()
            with contextlib.suppress(Exception):
                await self.backend.close()
            with contextlib.suppress(Exception):
                await ws.send_json({"type": "closed"})
            self.bus.publish("voice.ended", confirmed=self._confirmed)

    def stop(self) -> None:
        self.done.set()

    # --- navegador → agente ------------------------------------------------------------------------
    async def _from_browser(self, ws: WebSocket) -> None:
        try:
            while not self.done.is_set():
                msg = await ws.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if msg.get("bytes"):
                    await self.backend.send_audio(msg["bytes"])
                elif msg.get("text"):
                    data = json.loads(msg["text"])
                    if data.get("type") == "text" and data.get("text", "").strip():
                        text = data["text"].strip()[:600]
                        self._user_said(text)
                        await self.backend.send_text(text)
                    elif data.get("type") == "confirm":
                        await self._confirm("botón")
                    elif data.get("type") == "stop":
                        break
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            self.done.set()

    # --- agente → navegador y pantalla ----------------------------------------------------------------
    async def _from_agent(self) -> None:
        try:
            async for ev in self.backend.events():
                await self._handle(ev)
                if self.done.is_set():
                    break
        except Exception as exc:  # noqa: BLE001 — si la voz cae, la pantalla ofrece el teclado
            log.exception("Voice agent desconectado")
            self.bus.publish("governance.event", kind="voice_error", severity="warning",
                             title="Voz no disponible", detail=f"Usa el teclado (T) · {str(exc)[:120]}")
            self.done.set()

    async def _handle(self, ev: dict) -> None:
        t = ev.get("type", "")
        if t == "response.output_audio.delta" and self._ws is not None:
            await self._ws.send_bytes(base64.b64decode(ev["delta"]))
        elif t == "response.output_audio_transcript.delta":
            self._agent_text += ev.get("delta", "")
            self.bus.publish("voice.agent", text=self._agent_text, final=False)
        elif t == "response.output_audio_transcript.done":
            text = ev.get("transcript") or self._agent_text
            self._agent_text = ""
            self.bus.publish("voice.agent", text=text, final=True)
        elif t == "conversation.item.input_audio_transcription.completed":
            if ev.get("transcript", "").strip():
                self._user_said(ev["transcript"].strip())
        elif t == "input_audio_buffer.speech_started":
            # barge-in: el visitante habló encima; cortar la reproducción local
            if self._ws is not None:
                await self._ws.send_json({"type": "interrupt"})
            self.bus.publish("voice.state", value="listening")
        elif t == "response.function_call_arguments.done":
            await self._tool(ev.get("name", ""), ev.get("call_id", ""), ev.get("arguments") or "{}")
        elif t == "error":
            err = ev.get("error") or {}
            self.bus.publish("governance.event", kind="voice_error", severity="warning",
                             title="Voice agent: error", detail=str(err.get("message", err))[:160])

    def _user_said(self, text: str) -> None:
        self.user_lines.append(text)
        self.bus.publish("voice.user", text=text)

    # --- herramientas del voice agent -------------------------------------------------------------------
    async def _tool(self, name: str, call_id: str, arguments: str) -> None:
        if name == "registrar_brief":
            try:
                self.brief = Brief.model_validate({**json.loads(arguments), "empresa": None})
            except Exception:  # noqa: BLE001
                self.brief = self._fallback_brief()
            self.bus.publish("brief.proposed", brief=self.brief.model_dump())
            await self.backend.tool_result(call_id, "Mostrado en pantalla. Pregunta en una frase si es correcto.")
        elif name == "confirmar_brief":
            await self.backend.tool_result(call_id, "Confirmado. Despídete en una frase: el equipo de agentes ya trabaja.")
            await self._confirm("voz")

    async def _confirm(self, via: str) -> None:
        if self._confirmed:
            return
        brief = self.brief or self._fallback_brief()
        self._confirmed = True
        self.bus.publish("brief.confirmed", brief=brief.model_dump(), via=via)
        await self.on_confirmed(brief)
        # se deja terminar la frase de despedida y se cierra la voz
        await asyncio.sleep(self.settings.voice_goodbye_s)
        self.done.set()

    def _fallback_brief(self) -> Brief:
        said = " ".join(self.user_lines)[-600:] or "Problema de negocio contado por voz"
        return Brief(problema=said, industria="no especificada", volumen="no especificado", datos="no especificados")

    # --- presupuesto de tiempo ----------------------------------------------------------------------------
    async def _budget(self) -> None:
        t0 = time.monotonic()
        await asyncio.sleep(self.settings.interview_soft_limit_s)
        if not self.brief:
            await self.backend.nudge("Se acabó el tiempo de preguntas: llama YA a registrar_brief con lo que tengas.")
        await asyncio.sleep(max(self.settings.interview_hard_limit_s - (time.monotonic() - t0), 0))
        if not self._confirmed:
            self.bus.publish("governance.event", kind="interview_timeout", severity="info",
                             title="Entrevista cerrada por tiempo", detail="Se continúa con lo entendido hasta ahora.")
            await self._confirm("tiempo")
