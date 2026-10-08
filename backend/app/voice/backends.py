"""Backends de voz: Foundry voice agent real (preview) o simulado para desarrollar sin Azure."""

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

from ..config import Settings

log = logging.getLogger(__name__)


def _as_dict(ev: Any) -> dict:
    if isinstance(ev, dict):
        return ev
    if hasattr(ev, "as_dict"):
        return ev.as_dict()
    return dict(ev)


class FoundryVoiceBackend:
    """Conexión realtime al voice agent vía azure-ai-projects (beta.voice_agents)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._credential = None
        self._client = None
        self._manager = None
        self.conn = None

    async def start(self) -> None:
        from azure.ai.projects.aio import AIProjectClient
        from azure.identity.aio import DefaultAzureCredential

        s = self.settings
        self._credential = DefaultAzureCredential()
        self._client = AIProjectClient(endpoint=s.foundry_project_endpoint, credential=self._credential, allow_preview=True)
        extra = {"x-agent-version-override": s.voice_agent_version} if s.voice_agent_version else None
        self._manager = self._client.beta.voice_agents.realtime.connect(agent_name=s.voice_agent_name, api_version="v1", extra_query=extra)
        self.conn = await self._manager.enter()

    async def send_audio(self, pcm: bytes) -> None:
        await self.conn.input_audio_buffer.append(audio=pcm)

    async def send_text(self, text: str) -> None:
        await self.conn.conversation.item.create(item={"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]})
        await self.conn.response.create()

    async def nudge(self, instruction: str) -> None:
        await self.conn.conversation.item.create(item={"type": "message", "role": "system", "content": [{"type": "input_text", "text": instruction}]})
        await self.conn.response.create()

    async def tool_result(self, call_id: str, output: str) -> None:
        await self.conn.conversation.item.create(item={"type": "function_call_output", "call_id": call_id, "output": output})
        await self.conn.response.create()

    async def events(self) -> AsyncIterator[dict]:
        async for ev in self.conn:
            yield _as_dict(ev)

    async def close(self) -> None:
        for closer in (lambda: self._manager.__aexit__(None, None, None) if self._manager else None,
                       lambda: self._client.close() if self._client else None,
                       lambda: self._credential.close() if self._credential else None):
            try:
                r = closer()
                if asyncio.iscoroutine(r):
                    await r
            except Exception:  # noqa: BLE001
                log.debug("Error cerrando voz", exc_info=True)


class MockVoiceBackend:
    """Recepcionista simulada: misma secuencia de eventos que el servicio real, sin audio.

    Responde a texto tecleado (o, si llega audio, simula que el visitante habló tras unos segundos).
    """

    QUESTIONS = [
        ("industria", "¡Qué buen reto! ¿De qué industria es tu empresa?"),
        ("volumen", "Perfecto. ¿Más o menos qué volumen manejan al mes?"),
        ("datos", "Última pregunta: ¿qué datos o sistemas tienen hoy?"),
    ]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.q: asyncio.Queue[dict] = asyncio.Queue()
        self.answers: dict[str, str] = {}
        self.step = -1  # -1 = esperando el problema
        self.audio_bytes = 0
        self._call = 0

    async def start(self) -> None:
        from .definition import GREETING

        await self._say(GREETING)

    async def _say(self, text: str) -> None:
        delay = 0.02 * self.settings.mock_speed
        acc = ""
        for word in text.split(" "):
            acc = f"{acc} {word}".strip()
            await self.q.put({"type": "response.output_audio_transcript.delta", "delta": (" " if acc != word else "") + word})
            await asyncio.sleep(delay)
        await self.q.put({"type": "response.output_audio_transcript.done", "transcript": text})

    async def send_audio(self, pcm: bytes) -> None:
        # En mock, ~3 s de audio (24 kHz · 2 bytes) cuentan como una respuesta hablada genérica.
        self.audio_bytes += len(pcm)
        if self.audio_bytes >= 24000 * 2 * 3:
            self.audio_bytes = 0
            sample = ["Conciliamos a mano miles de facturas de proveedores", "Manufactura", "Unas 5,000 facturas al mes", "CFDI en SharePoint y SAP", "Sí, es correcto"]
            text = sample[min(self.step + 1, len(sample) - 1)]
            await self.q.put({"type": "conversation.item.input_audio_transcription.completed", "transcript": text})
            await self.send_text(text)

    async def send_text(self, text: str) -> None:
        if self.step == -1:
            self.answers["problema"] = text
        elif self.step < len(self.QUESTIONS):
            self.answers[self.QUESTIONS[self.step][0]] = text
        elif re.search(r"\b(s[ií]|correcto|exacto|as[ií] es|adelante|dale|ok)\b", text, re.IGNORECASE):
            await self._function("confirmar_brief", {})
            await self._say("¡Perfecto! Mira la pantalla: mi equipo de agentes ya está trabajando.")
            return
        self.step += 1
        if self.step < len(self.QUESTIONS):
            await self._say(self.QUESTIONS[self.step][1])
        else:
            brief = {k: self.answers.get(k, "no especificado") for k in ("problema", "industria", "volumen", "datos")}
            await self._function("registrar_brief", brief)
            await self._say("Esto entendí, ¿es correcto?")

    async def nudge(self, instruction: str) -> None:
        if self.step < len(self.QUESTIONS):
            self.step = len(self.QUESTIONS) - 1
            await self.send_text(self.answers.get("datos", "no especificados"))

    async def tool_result(self, call_id: str, output: str) -> None:
        return None

    async def _function(self, name: str, args: dict) -> None:
        self._call += 1
        await self.q.put({"type": "response.function_call_arguments.done", "name": name, "call_id": f"call_{self._call}", "arguments": json.dumps(args, ensure_ascii=False)})

    async def events(self) -> AsyncIterator[dict]:
        while True:
            yield await self.q.get()

    async def close(self) -> None:
        return None


def make_backend(settings: Settings):
    return MockVoiceBackend(settings) if settings.demo_mode != "live" else FoundryVoiceBackend(settings)
