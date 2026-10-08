import asyncio

import pytest
from fastapi.testclient import TestClient

from app import pricing
from app.config import Settings
from app.events import EventBus
from app.recorder import Recorder, load_recording, replay
from app.swarm import mermaid
from app.swarm.runner import SwarmRunner
from app.swarm.schemas import Brief

BRIEF = Brief(problema="Conciliar 5,000 facturas al mes a mano", industria="manufactura", volumen="5,000 facturas/mes", datos="CFDI en SharePoint")


def fast_settings(tmp_path, **kw) -> Settings:
    return Settings(**{"demo_mode": "mock", "mock_speed": 0.02, "recordings_dir": tmp_path, **kw})


def collect(bus: EventBus) -> list:
    events = []
    bus.add_listener(events.append)
    return events


async def test_swarm_debate_flow(tmp_path):
    bus = EventBus()
    bus.start_session("t")
    events = collect(bus)
    state = await SwarmRunner(bus, fast_settings(tmp_path)).run(BRIEF)

    assert state.status == "ok"
    assert state.turns == ["arquitecto", "financiero", "arquitecto", "financiero", "riesgo", "arquitecto", "diagramador", "redactor"]
    objections = [e.data["de"] for e in events if e.type == "agent.objection"]
    assert objections == ["financiero", "riesgo"]
    costs = [e.data["total_usd"] for e in events if e.type == "artifact.cost"]
    assert costs[0] > costs[1]  # el ajuste del arquitecto baja el costo
    spans = [e for e in events if e.type == "trace.span"]
    assert len(spans) == 8 and spans[-1].data["session_cost_usd"] > 0
    # el diagrama está desde la primera propuesta y la última versión es la del Diagramador
    diagrams = [e.data for e in events if e.type == "artifact.diagram"]
    assert [d["por"] for d in diagrams] == ["arquitecto"] * 3 + ["diagramador"]
    assert all(d["svg"].startswith("<svg") for d in diagrams)
    assert "NUEVO" in diagrams[2]["svg"]  # lo que agregó el ajuste por la objeción de Riesgo
    assert diagrams[-1]["pasos"] and "INGESTA" in diagrams[-1]["svg"]
    onepager = next(e for e in events if e.type == "artifact.onepager")
    assert onepager.data["onepager"]["titulo"]
    assert onepager.data["mermaid"].startswith("flowchart LR")
    assert onepager.data["diagrama"]["zonas"] and onepager.data["arquitectura"]["componentes"]


def test_diagram_survives_invented_ids_and_puts_governance_in_band():
    from app.swarm import diagram

    comps = [{"id": "a", "nombre": "Ingesta", "servicio": "Azure Blob Storage · Hot"},
             {"id": "b", "nombre": "Agente", "servicio": "Foundry · GPT-5.4 mini"},
             {"id": "kv", "nombre": "Llaves", "servicio": "Azure Key Vault"}]
    cats = {"a": "Datos", "b": "IA", "kv": "Gobierno"}
    spec = {"zonas": [{"nombre": "X", "componentes": ["zzz"]}], "flujo": [{"de": "zzz", "a": "b", "etiqueta": "?"}]}
    svg = diagram.build_svg(comps, [{"de": "a", "a": "b", "etiqueta": "<datos>"}], cats, spec=spec)
    assert svg.startswith("<svg") and "zzz" not in svg
    assert "&lt;datos&gt;" in svg  # texto del modelo escapado
    assert "SEGURIDAD Y GOBIERNO" in svg and "Key Vault" in svg  # Key Vault va en la banda transversal


async def test_swarm_timeout_degrades_gracefully(tmp_path):
    bus = EventBus()
    events = collect(bus)
    state = await SwarmRunner(bus, fast_settings(tmp_path, mock_speed=1.0, swarm_timeout_s=0.5)).run(BRIEF)
    assert state.status == "timeout"
    assert any(e.type == "governance.event" and e.data["kind"] == "timeout" for e in events)
    assert any(e.type == "artifact.onepager" for e in events)  # siempre hay one-pager


def test_estimate_is_deterministic():
    out = pricing.estimate([
        {"id": "a", "servicio": "foundry.gpt-5.4-mini", "cantidad": 100, "supuesto": "x"},
        {"id": "b", "servicio": "container_apps", "cantidad": 2, "supuesto": "y"},
        {"id": "c", "servicio": "no.existe", "cantidad": 1},
    ])
    assert out["total_usd"] == 100 * 0.9 + 2 * 70.0
    assert out["desconocidos"] == ["no.existe"]
    assert out["disclaimer"]


def test_mermaid_sanitizes_and_drops_unknown_edges():
    mm = mermaid.build(
        [{"id": "1-x", "nombre": 'A "quoted"'}, {"id": "b", "nombre": "B"}],
        [{"de": "1-x", "a": "b", "etiqueta": "ok"}, {"de": "b", "a": "zzz", "etiqueta": ""}],
    )
    assert 'n_1_x["A \'quoted\'"]' in mm
    assert "zzz" not in mm


async def test_record_and_replay_roundtrip(tmp_path):
    bus = EventBus()
    Recorder(bus, tmp_path)
    bus.start_session("rec1")
    bus.publish("session.started", mode="mock", brief={})
    bus.publish("agent.message", agent="arquitecto", burbuja="hola", detalle={})
    bus.publish("session.ended", status="ok", swarm_s=10)
    curated = tmp_path / "curated" / "rec1.jsonl"
    assert curated.exists()
    assert [e.type for e in load_recording(curated)] == ["session.started", "agent.message", "session.ended"]

    bus2 = EventBus()
    seen = collect(bus2)
    await replay(bus2, curated, speed=100)
    assert [e.type for e in seen] == ["session.started", "agent.message", "session.ended"]
    assert seen[0].data["mode"] == "replay"


def test_api_text_session_and_reset(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main.sessions, "settings", fast_settings(tmp_path))
    with TestClient(main.app) as client:
        r = client.post("/api/session/text", json={"problema": "Atender 2,000 correos de clientes al día"})
        assert r.status_code == 200
        with client.websocket_connect("/ws/stage") as ws:
            assert ws.receive_json()["type"] == "hello"
            assert ws.receive_json()["type"] == "session.started"
        assert client.post("/api/reset").json() == {"ok": True}
        assert client.get("/api/health").json()["state"] == "idle"
