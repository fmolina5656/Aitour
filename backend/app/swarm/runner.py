"""Ejecuta el enjambre (GroupChat de Microsoft Agent Framework) y traduce sus eventos al bus.

Garantías de stand: timeout global, watchdog de inactividad por turno y degradación elegante
(si algo falla, el one-pager se arma con lo que haya).
"""

import asyncio
import logging
import re
import time
from collections.abc import Awaitable, Callable

from agent_framework import Agent, AgentMiddleware, Message
from agent_framework_orchestrations import GroupChatBuilder, GroupChatRequestSentEvent, GroupChatResponseReceivedEvent

from .. import pricing
from ..config import Settings
from ..events import EventBus
from .clients import make_client, model_for
from .director import AGENTS, Director, SwarmState
from .prompts import instructions_for
from .schemas import OUTPUT_MODELS, Brief

log = logging.getLogger(__name__)

BUBBLE_RE = re.compile(r'"burbuja"\s*:\s*"((?:[^"\\]|\\.)*)')
AGENT_MAX_TOKENS = {"arquitecto": 1800, "financiero": 600, "riesgo": 900, "redactor": 1200}


class ContextInjector(AgentMiddleware):
    """Agrega al turno del agente el contexto calculado por el sistema (costos, versión final, etc.)."""

    def __init__(self, director: Director, agent: str) -> None:
        self.director = director
        self.agent = agent

    async def process(self, context, call_next: Callable[[], Awaitable[None]]) -> None:
        extra = self.director.context_for(self.agent)
        if extra:
            context.messages.append(Message(role="user", contents=[extra]))
        await call_next()


def build_agents(director: Director, settings: Settings) -> list[Agent]:
    agents = []
    for name in AGENTS:
        options: dict = {"max_tokens": AGENT_MAX_TOKENS[name], "store": False}
        if settings.demo_mode == "live":
            options["response_format"] = OUTPUT_MODELS[name]
            if settings.reasoning_effort != "none":
                options["reasoning"] = {"effort": settings.reasoning_effort}
        agents.append(
            Agent(
                make_client(name, settings),
                instructions_for(name),
                name=name,
                description=f"Agente {name}",
                default_options=options,
                middleware=[ContextInjector(director, name)],
            )
        )
    return agents


class _Turn:
    def __init__(self, agent: str, model: str) -> None:
        self.agent = agent
        self.model = model
        self.t0 = time.monotonic()
        self.text = ""
        self.last_bubble = ""
        self.input_tokens = 0
        self.output_tokens = 0


class SwarmRunner:
    def __init__(self, bus: EventBus, settings: Settings) -> None:
        self.bus = bus
        self.settings = settings
        self.session_cost = 0.0

    async def run(self, brief: Brief) -> SwarmState:
        state = SwarmState(brief=brief)
        director = Director(state, self.bus, self.settings)
        workflow = GroupChatBuilder(
            participants=build_agents(director, self.settings),
            selection_func=director.select,
            termination_condition=director.is_done,
            max_rounds=self.settings.swarm_max_rounds,
            intermediate_output_from="all_other",
        ).build()

        status = "ok"
        try:
            async with asyncio.timeout(self.settings.swarm_timeout_s):
                await self._consume(workflow.run(brief.as_prompt(), stream=True))
        except TimeoutError:
            status = "timeout"
            self.bus.publish("governance.event", kind="timeout", severity="warning", title="Presupuesto de tiempo agotado", detail="El enjambre se cortó a tiempo; el one-pager usa la última versión disponible.")
        except Exception as exc:  # noqa: BLE001 — en el stand nunca se cae la sesión
            if is_content_filter(exc):
                status = "filtered"
                self.bus.publish("governance.event", kind="content_filter", severity="error",
                                 title="Guardrail de Foundry: contenido bloqueado",
                                 detail="El filtro de contenido del deployment detuvo una respuesta; el one-pager usa la última versión segura.")
            else:
                status = "error"
                log.exception("Error en el enjambre")
                self.bus.publish("governance.event", kind="error", severity="error", title="Error en el enjambre", detail=str(exc)[:200])

        if state.onepager is None:
            state.onepager = fallback_onepager(state)
        state.status = status
        self.bus.publish("artifact.onepager", status=status, **build_onepager_payload(state))
        return state

    async def _consume(self, stream) -> None:
        turn: _Turn | None = None
        idle = self.settings.turn_idle_timeout_s
        it = stream.__aiter__()
        while True:
            try:
                ev = await asyncio.wait_for(it.__anext__(), timeout=idle)
            except StopAsyncIteration:
                break
            except TimeoutError as exc:
                raise TimeoutError(f"Sin actividad en {idle}s") from exc

            if ev.type == "group_chat" and isinstance(ev.data, GroupChatRequestSentEvent):
                name = ev.data.participant_name
                turn = _Turn(name, model_for(name, self.settings))
                self.bus.publish("agent.thinking", agent=name, round=ev.data.round_index)
            elif ev.type == "group_chat" and isinstance(ev.data, GroupChatResponseReceivedEvent):
                if turn is not None:
                    self._close_turn(turn)
                    turn = None
            elif ev.type == "intermediate" and turn is not None:
                self._on_update(turn, ev.data)
            elif ev.type == "failed":
                raise RuntimeError(str(getattr(ev, "details", "workflow failed")))

    def _on_update(self, turn: _Turn, update) -> None:
        for c in getattr(update, "contents", None) or []:
            if c.type == "text" and c.text:
                turn.text += c.text
                m = BUBBLE_RE.search(turn.text)
                if m and m.group(1) != turn.last_bubble:
                    turn.last_bubble = m.group(1)
                    self.bus.publish("agent.delta", agent=turn.agent, burbuja=turn.last_bubble.replace('\\"', '"'))
            elif c.type == "usage" and c.usage_details:
                turn.input_tokens += c.usage_details.get("input_token_count") or 0
                turn.output_tokens += c.usage_details.get("output_token_count") or 0

    def _close_turn(self, turn: _Turn) -> None:
        cost = pricing.runtime_cost(turn.model, turn.input_tokens, turn.output_tokens)
        self.session_cost += cost
        self.bus.publish(
            "trace.span",
            agent=turn.agent,
            model=turn.model,
            input_tokens=turn.input_tokens,
            output_tokens=turn.output_tokens,
            latency_ms=int((time.monotonic() - turn.t0) * 1000),
            cost_usd=cost,
            session_cost_usd=round(self.session_cost, 6),
        )


def is_content_filter(exc: BaseException) -> bool:
    """Los guardrails de Foundry rechazan con code=content_filter (o ResponsibleAIPolicyViolation)."""
    seen: set[int] = set()
    e: BaseException | None = exc
    while e is not None and id(e) not in seen:
        seen.add(id(e))
        text = f"{type(e).__name__} {e} {getattr(e, 'code', '')}"
        if "content_filter" in text or "ResponsibleAIPolicyViolation" in text or "content management policy" in text:
            return True
        e = e.__cause__ or e.__context__
    return False


def fallback_onepager(state: SwarmState) -> dict:
    b = state.brief
    return {
        "titulo": f"Propuesta de IA para {b.industria}",
        "problema": b.problema,
        "solucion": (state.arquitectura or {}).get("resumen", "Solución de IA con Microsoft Foundry a validar en un taller con Readymind."),
        "beneficios": ["Automatización del proceso", "Decisiones más rápidas", "Trazabilidad y gobierno"],
        "riesgos_y_mitigaciones": (state.riesgo or {}).get("mitigaciones", ["Guardrails de Foundry", "Managed Identity", "Cifrado de datos"])[:3],
        "siguientes_pasos": ["Taller con Readymind", "Piloto de 4 semanas", "Decisión de escalamiento"],
        "generado_por": "plantilla",
    }


def build_onepager_payload(state: SwarmState) -> dict:
    from . import mermaid

    arq = state.arquitectura or {"componentes": [], "conexiones": []}
    cats = {i["id"]: i["categoria"] for i in (state.costo or {}).get("items", [])}
    return {
        "brief": state.brief.model_dump(),
        "onepager": state.onepager,
        "mermaid": mermaid.build(arq.get("componentes", []), arq.get("conexiones", []), cats),
        "costo": state.costo,
        "riesgo": state.riesgo,
        "objeciones": state.objeciones,
    }
