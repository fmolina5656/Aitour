import asyncio

from fastapi.testclient import TestClient

from app.config import Settings
from app.events import EventBus
from app.voice.backends import MockVoiceBackend
from app.voice.definition import build_definition
from app.voice.interview import VoiceInterview


def test_voice_agent_definition_is_valid():
    d = build_definition(Settings(voice_rai_policy="readymind-stand")).as_dict()
    assert d["kind"] == "voice"
    assert d["audio"]["input"]["turn_detection"]["type"] == "azure_semantic_vad_multilingual"
    assert d["audio"]["input"]["transcription"]["language"] == "es-MX"
    assert d["audio"]["output"]["voice"].startswith("es-MX-")
    assert {t.get("name") for t in d["tools"]} >= {"registrar_brief", "confirmar_brief"}
    assert d["rai_config"]["rai_policy_name"] == "readymind-stand"


def test_voice_interview_end_to_end_over_websocket(tmp_path, monkeypatch):
    from app import main

    fast = Settings(demo_mode="mock", mock_speed=0.01, recordings_dir=tmp_path, voice_goodbye_s=0.05)
    monkeypatch.setattr(main.sessions, "settings", fast)
    seen: list = []
    main.bus.add_listener(seen.append)
    with TestClient(main.app) as client, client.websocket_connect("/ws/voice") as ws:
        for answer in ["Conciliamos a mano 5,000 facturas al mes", "Manufactura", "5,000 facturas", "CFDI en SharePoint", "Sí, correcto"]:
            ws.send_json({"type": "text", "text": answer})
        assert ws.receive_json()["type"] == "closed"
    types = [e.type for e in seen]
    assert types.index("brief.proposed") < types.index("brief.confirmed") < types.index("session.started")
    proposed = next(e for e in seen if e.type == "brief.proposed").data["brief"]
    assert proposed["industria"] == "Manufactura" and "facturas" in proposed["problema"]
    assert sum(1 for t in types if t == "voice.user") == 5


async def test_interview_hard_limit_starts_swarm_anyway(tmp_path):
    bus = EventBus()
    seen: list = []
    bus.add_listener(seen.append)
    settings = Settings(demo_mode="mock", mock_speed=0.01, recordings_dir=tmp_path, interview_soft_limit_s=0.05, interview_hard_limit_s=0.1, voice_goodbye_s=0.01)
    confirmed: list = []

    async def on_confirmed(brief):
        confirmed.append(brief)

    iv = VoiceInterview(bus, settings, MockVoiceBackend(settings), on_confirmed)

    class FakeWS:
        async def receive(self):
            await asyncio.sleep(10)

        async def send_json(self, _):
            return None

        async def send_bytes(self, _):
            return None

    await asyncio.wait_for(iv.run(FakeWS()), timeout=3)
    assert confirmed, "el corte duro debe arrancar el enjambre aunque no haya brief"
    assert any(e.type == "governance.event" and e.data["kind"] == "interview_timeout" for e in seen)
