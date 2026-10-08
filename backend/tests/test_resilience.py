import time

from app.config import Settings
from app.events import EventBus
from app.recorder import Recorder
from app.session import SessionManager
from app.swarm.schemas import Brief

BRIEF = Brief(problema="Conciliar 5,000 facturas al mes", industria="manufactura", volumen="5,000/mes", datos="CFDI")


async def _record_good_session(tmp_path):
    """Graba una sesión real (mock) para que exista algo curado."""
    bus = EventBus()
    sm = SessionManager(bus, Settings(demo_mode="mock", mock_speed=0.01, recordings_dir=tmp_path))
    await sm.start(BRIEF)
    await sm.task
    assert list((tmp_path / "curated").glob("*.jsonl"))


async def test_failover_to_replay_when_foundry_is_down(tmp_path, monkeypatch):
    await _record_good_session(tmp_path)
    from app.swarm import runner

    def broken_client(agent, settings):
        raise ConnectionError("Foundry no responde")

    monkeypatch.setattr(runner, "make_client", broken_client)
    monkeypatch.setattr("app.session.asyncio.sleep", _fast_sleep)
    bus = EventBus()
    seen = []
    bus.add_listener(seen.append)
    live = Settings(demo_mode="live", recordings_dir=tmp_path, foundry_project_endpoint="https://x/api/projects/p")
    sm = SessionManager(bus, live)
    monkeypatch.setattr(sm.guard, "check", _allow)
    await sm.start(BRIEF)
    await sm.task
    kinds = [e.data.get("kind") for e in seen if e.type == "governance.event"]
    assert "failover" in kinds
    replayed = [e for e in seen if e.type == "session.started" and e.data.get("mode") == "replay"]
    assert replayed, "debe reproducirse la sesión grabada"
    assert any(e.type == "artifact.onepager" for e in seen[seen.index(replayed[0]):])


async def test_failover_rules(tmp_path):
    from app.recorder import SEED, latest_curated

    assert latest_curated(tmp_path) == SEED  # sin grabaciones propias se usa la semilla del repo
    sm = SessionManager(EventBus(), Settings(demo_mode="live", recordings_dir=tmp_path))
    assert sm._should_failover("error", True)
    assert not sm._should_failover("error", False)  # si algún agente ya habló, se sigue con lo que hay
    sm2 = SessionManager(EventBus(), Settings(demo_mode="mock", recordings_dir=tmp_path))
    assert not sm2._should_failover("error", True)


async def test_reset_is_fast_even_mid_swarm(tmp_path):
    bus = EventBus()
    sm = SessionManager(bus, Settings(demo_mode="mock", mock_speed=1.0, recordings_dir=tmp_path))
    await sm.start(BRIEF)
    t0 = time.monotonic()
    await sm.reset()
    assert time.monotonic() - t0 < 1.0  # requisito: < 5 s
    assert sm.state == "idle" and bus.history == []


async def _fast_sleep(_):
    return None


async def _allow(_):
    from app.guard import GuardResult

    return GuardResult(True)
