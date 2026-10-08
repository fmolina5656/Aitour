"""Director determinista del group chat.

Decide quién habla según el guion flexible:
  Arquitecto → Financiero ⇄ Arquitecto (objeciones, máx. N rondas) → Riesgo [→ Arquitecto] → Redactor
Las objeciones son reales: las dispara el calculador (umbral de costo) o el agente de Riesgo.
Además parsea cada turno, actualiza el estado compartido y publica los artefactos en el bus.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from agent_framework import Message
from agent_framework_orchestrations import GroupChatState

from .. import pricing
from ..config import Settings
from ..events import EventBus
from . import mermaid
from .schemas import OUTPUT_MODELS, Brief

log = logging.getLogger(__name__)

AGENTS = ["arquitecto", "financiero", "riesgo", "redactor"]


def parse_json(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


@dataclass
class SwarmState:
    brief: Brief
    arquitectura: dict | None = None
    arquitectura_version: int = 0
    costo: dict | None = None
    riesgo: dict | None = None
    onepager: dict | None = None
    debate_rounds: int = 0
    riesgo_done: bool = False
    pending_reply_to: str | None = None  # quién objetó al Arquitecto
    financiero_validated: bool = False
    turns: list[str] = field(default_factory=list)
    objeciones: list[dict] = field(default_factory=list)
    status: str = "running"

    def cost_alert(self, settings: Settings) -> str | None:
        if not self.costo:
            return None
        reasons = []
        top = next((i for i in self.costo["items"] if i["id"] == self.costo["top_item"]), None)
        if top and top["premium"] and self.costo["top_share"] >= settings.objection_component_share:
            reasons.append(f"el modelo premium '{top['nombre']}' concentra {self.costo['top_share']:.0%} del costo")
        if self.costo["total_usd"] > settings.objection_monthly_budget_usd:
            reasons.append(f"el total supera el presupuesto de referencia de USD {settings.objection_monthly_budget_usd:,.0f}")
        return "; ".join(reasons) or None


class Director:
    def __init__(self, state: SwarmState, bus: EventBus, settings: Settings) -> None:
        self.state = state
        self.bus = bus
        self.settings = settings

    # --- selección -------------------------------------------------------------------------
    def select(self, gc: GroupChatState) -> str:
        last = gc.conversation[-1] if gc.conversation else None
        speaker = last.author_name if last is not None and last.role == "assistant" else None
        if speaker:
            self._ingest(speaker, last)
        nxt = self._next(speaker, gc.current_round)
        self.state.turns.append(nxt)
        return nxt

    def is_done(self, conversation: list[Message]) -> bool:
        """termination_condition: el group chat termina cuando habla el Redactor."""
        last = conversation[-1] if conversation else None
        if last is not None and last.role == "assistant" and last.author_name == "redactor":
            if self.state.onepager is None:
                self._ingest("redactor", last)
            return True
        return False

    def _next(self, speaker: str | None, round_idx: int) -> str:
        s = self.state
        # siempre dejar lugar para el redactor
        if round_idx >= self.settings.swarm_max_rounds - 1 and speaker != "redactor":
            return "redactor"
        if speaker is None:
            return "arquitecto"
        if speaker == "arquitecto":
            replying_to, s.pending_reply_to = s.pending_reply_to, None
            if replying_to == "riesgo":
                return "redactor"
            if not s.financiero_validated:
                return "financiero"
            return "riesgo" if not s.riesgo_done else "redactor"
        if speaker == "financiero":
            if s.pending_reply_to == "financiero":
                return "arquitecto"
            s.financiero_validated = True
            return "riesgo"
        if speaker == "riesgo":
            return "arquitecto" if s.pending_reply_to == "riesgo" else "redactor"
        return "redactor"

    # --- ingesta de cada turno ----------------------------------------------------------------
    def _ingest(self, agent: str, msg: Message) -> None:
        data = parse_json(msg.text)
        if data is None:
            log.warning("Salida no-JSON de %s: %.200s", agent, msg.text)
            self.bus.publish("agent.message", agent=agent, burbuja=(msg.text or "")[:140], detalle={})
            return
        model = OUTPUT_MODELS[agent]
        try:
            data = model.model_validate(data).model_dump()
        except Exception as exc:  # noqa: BLE001 — se tolera salida parcial, pero se registra
            log.warning("Salida inválida de %s: %s", agent, exc)
        self.bus.publish("agent.message", agent=agent, burbuja=data.get("burbuja", "")[:160], detalle=data)
        getattr(self, f"_on_{agent}")(data)

    def _maybe_objection(self, agent: str, data: dict) -> None:
        obj = data.get("objecion")
        if obj and self.state.debate_rounds < self.settings.max_debate_rounds + (1 if agent == "riesgo" else 0):
            self.state.debate_rounds += 1
            self.state.pending_reply_to = agent
            self.state.objeciones.append({"de": agent, **obj})
            self.bus.publish("agent.objection", de=agent, para="arquitecto", motivo=obj.get("motivo", ""), propuesta=obj.get("propuesta", ""))

    def _on_arquitecto(self, data: dict) -> None:
        s = self.state
        s.arquitectura = data
        s.arquitectura_version += 1
        if s.pending_reply_to == "financiero":
            s.financiero_validated = False  # el financiero vuelve a revisar el ajuste
        s.costo = pricing.estimate(data.get("componentes", []))
        cats = {i["id"]: i["categoria"] for i in s.costo["items"]}
        self.bus.publish(
            "artifact.diagram",
            mermaid=mermaid.build(data.get("componentes", []), data.get("conexiones", []), cats),
            version=s.arquitectura_version,
            cambios=data.get("cambios"),
        )
        self.bus.publish("artifact.cost", **s.costo, version=s.arquitectura_version)

    def _on_financiero(self, data: dict) -> None:
        self._maybe_objection("financiero", data)

    def _on_riesgo(self, data: dict) -> None:
        self.state.riesgo = data
        self.state.riesgo_done = True
        self.bus.publish(
            "artifact.risk",
            datos_sensibles=data.get("datos_sensibles", []),
            regulacion=data.get("regulacion", []),
            mitigaciones=data.get("mitigaciones", []),
        )
        self._maybe_objection("riesgo", data)

    def _on_redactor(self, data: dict) -> None:
        self.state.onepager = data

    # --- contexto que se inyecta a cada agente -------------------------------------------------
    def context_for(self, agent: str) -> str | None:
        s = self.state
        if agent == "financiero" and s.costo:
            alert = s.cost_alert(self.settings)
            if s.debate_rounds >= self.settings.max_debate_rounds:
                alert = None  # ya no hay rondas de debate: el financiero cierra
            tabla = "\n".join(
                f"- {i['nombre']}: {i['cantidad']:g} × {i['unidad']} × USD {i['precio_unitario']} = USD {i['costo_usd']:,.2f} ({i['supuesto']})"
                for i in s.costo["items"]
            )
            return (
                f"[CALCULADOR · arquitectura v{s.arquitectura_version}]\n{tabla}\nTOTAL MENSUAL: USD {s.costo['total_usd']:,.2f}\n"
                + (f"ALERTA: {alert}. Presenta una objeción al arquitecto." if alert else "SIN ALERTAS: da tu visto bueno, objecion = null.")
            )
        if agent == "riesgo" and s.debate_rounds > self.settings.max_debate_rounds:
            return "[SISTEMA] Ya no hay tiempo para más ajustes: objecion = null."
        if agent == "redactor" and s.arquitectura:
            comps = ", ".join(c["nombre"] for c in s.arquitectura.get("componentes", []))
            total = s.costo["total_usd"] if s.costo else 0
            return f"[SISTEMA · versión final] Componentes: {comps}. Costo mensual estimado: USD {total:,.2f}."
        return None
