"""Guardia antes del enjambre: Prompt Shields + clasificador de tema.

Es parte del show: cada chequeo se publica en el panel de gobierno (también cuando pasa), y los
bloqueos se ven en pantalla con una respuesta amable. En modo live usa Azure AI Content Safety
(Prompt Shields) con Microsoft Entra ID; en mock usa heurísticas locales equivalentes.
"""

import json
import logging
import re
import time
from dataclasses import dataclass

import httpx

from .config import Settings
from .events import EventBus

log = logging.getLogger(__name__)

SHIELD_API_VERSION = "2024-09-01"
COGNITIVE_SCOPE = "https://cognitiveservices.azure.com/.default"

REPLY_JAILBREAK = (
    "Buen intento 😉 Este equipo de agentes solo trabaja en problemas de negocio. "
    "Cuéntame un reto real de tu empresa y lo resolvemos en 3 minutos."
)
REPLY_OFF_TOPIC = (
    "Me encantaría platicar de eso, pero aquí solo diseñamos soluciones de IA para negocios. "
    "¿Qué proceso de tu empresa te gustaría mejorar?"
)

# Heurísticas para modo mock (y red de seguridad si Prompt Shields no responde)
JAILBREAK_PATTERNS = [
    r"ignora(r)? (todas )?(tus|las) (instrucciones|reglas)",
    r"ignore (all |your |previous )*(instructions|rules)",
    r"olvida (tus|las) (instrucciones|reglas)",
    r"system prompt|prompt del sistema|tus instrucciones (internas|ocultas)",
    r"\bDAN\b|modo desarrollador|developer mode|jailbreak",
    r"act[uú]a como (si no tuvieras|sin) (reglas|restricciones|filtros)",
    r"revela(r)? (tu|el) (prompt|configuraci[oó]n)",
]
BUSINESS_HINTS = re.compile(
    r"empresa|clientes?|proceso|ventas|factur|inventario|operaci|datos|reporte|costo|proveedor|"
    r"empleados?|soporte|atenci[oó]n|contrat|cr[eé]dito|log[ií]stica|producci|calidad|negocio|"
    r"automatiz|document|correo|call center|pedido|cobranza|n[oó]mina|riesgo|cumplimiento|"
    r"manufactura|retail|banco|seguros?|salud|hospital|escuela|gobierno|ERP|CRM|SAP",
    re.IGNORECASE,
)
OFF_TOPIC_HINTS = re.compile(
    r"f[uú]tbol|partido|chiste|receta|hor[oó]scopo|pol[ií]tic|elecci|religi|novia|novio|"
    r"canci[oó]n|poema|pel[ií]cula|qui[eé]n gan[oó]|cu[eé]ntame algo gracioso",
    re.IGNORECASE,
)


@dataclass
class GuardResult:
    allowed: bool
    kind: str = "ok"  # ok | jailbreak | off_topic
    reply: str = ""


class Guard:
    def __init__(self, bus: EventBus, settings: Settings) -> None:
        self.bus = bus
        self.settings = settings
        self._credential = None

    async def check(self, text: str) -> GuardResult:
        shield = await self._prompt_shield(text)
        if not shield.allowed:
            return shield
        return await self._topic(text)

    # --- Prompt Shields --------------------------------------------------------------------------
    async def _prompt_shield(self, text: str) -> GuardResult:
        t0 = time.monotonic()
        source = "Azure AI Content Safety"
        attack: bool | None = None
        if self.settings.demo_mode == "live" and self.settings.content_safety_endpoint:
            try:
                attack = await self._shield_rest(text)
            except Exception as exc:  # noqa: BLE001 — si el servicio falla, se sigue con la heurística
                log.warning("Prompt Shields no disponible: %s", exc)
                self.bus.publish("governance.event", kind="shield_unavailable", severity="warning",
                                 title="Prompt Shields no disponible", detail="Se aplica la validación local de respaldo.")
        if attack is None:
            source = "validación local" if self.settings.demo_mode == "live" else "Prompt Shields (simulado)"
            attack = any(re.search(p, text, re.IGNORECASE) for p in JAILBREAK_PATTERNS)
        ms = int((time.monotonic() - t0) * 1000)
        if attack:
            self.bus.publish("governance.event", kind="jailbreak", severity="error",
                             title="Prompt Shields: ataque detectado",
                             detail=f"Intento de cambiar las reglas del sistema · bloqueado antes de llegar al modelo · {source} · {ms} ms")
            return GuardResult(False, "jailbreak", REPLY_JAILBREAK)
        self.bus.publish("governance.event", kind="shield_ok", severity="info",
                         title="Prompt Shields: sin ataques", detail=f"{source} · {ms} ms")
        return GuardResult(True)

    async def _shield_rest(self, text: str) -> bool:
        token = await self._token()
        url = f"{self.settings.content_safety_endpoint.rstrip('/')}/contentsafety/text:shieldPrompt"
        async with httpx.AsyncClient(timeout=self.settings.guard_timeout_s) as client:
            r = await client.post(
                url,
                params={"api-version": SHIELD_API_VERSION},
                headers={"Authorization": f"Bearer {token}"},
                json={"userPrompt": text[:9000], "documents": []},
            )
            r.raise_for_status()
            return bool(r.json()["userPromptAnalysis"]["attackDetected"])

    async def _token(self) -> str:
        if self._credential is None:
            from azure.identity.aio import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
        return (await self._credential.get_token(COGNITIVE_SCOPE)).token

    # --- Tema: solo problemas de negocio ------------------------------------------------------------
    async def _topic(self, text: str) -> GuardResult:
        t0 = time.monotonic()
        on_topic: bool | None = None
        if self.settings.demo_mode == "live":
            try:
                on_topic = await self._topic_llm(text)
            except Exception as exc:  # noqa: BLE001
                log.warning("Clasificador de tema no disponible: %s", exc)
        if on_topic is None:
            on_topic = bool(BUSINESS_HINTS.search(text)) or not OFF_TOPIC_HINTS.search(text)
        ms = int((time.monotonic() - t0) * 1000)
        if not on_topic:
            self.bus.publish("governance.event", kind="off_topic", severity="warning",
                             title="Fuera de alcance", detail=f"El sistema solo atiende problemas de negocio · respuesta amable · {ms} ms")
            return GuardResult(False, "off_topic", REPLY_OFF_TOPIC)
        self.bus.publish("governance.event", kind="topic_ok", severity="info",
                         title="Tema validado: problema de negocio", detail=f"{ms} ms")
        return GuardResult(True)

    async def _topic_llm(self, text: str) -> bool:
        from agent_framework import Agent

        from .swarm.clients import make_client_for_model

        agent = Agent(
            make_client_for_model(self.settings.model_guard, self.settings),
            "Clasifica si el texto describe un problema o reto de una empresa u organización que podría resolverse "
            'con tecnología. Responde SOLO JSON: {"negocio": true|false}.',
            name="guardia",
            default_options={"max_tokens": 20, "store": False},
        )
        resp = await agent.run(text[:2000])
        m = re.search(r"\{.*\}", resp.text or "", re.DOTALL)
        return bool(json.loads(m.group(0))["negocio"]) if m else True
