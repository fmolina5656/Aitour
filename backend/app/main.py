"""API del stand: WebSocket para la pantalla, REST para iniciar/resetear sesiones."""

import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import telemetry
from .config import get_settings
from .events import Event, EventBus
from .onepager import leads as lead_mod
from .onepager.render import HERE as ONEPAGER_DIR
from .onepager.render import _env as templates
from .onepager.render import render_pdf
from .onepager.store import OnePagerStore
from .session import SessionManager
from .swarm.schemas import Brief

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# El SDK de Azure loguea en INFO cada request (incluidos los envíos de telemetría, que a su vez se exportan
# a Application Insights): tapa los logs útiles y suma costo en Log Analytics.
for _noisy in ("azure.core.pipeline.policies.http_logging_policy", "azure.monitor.opentelemetry.exporter", "azure.identity"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

settings = get_settings()
telemetry.setup(settings)
bus = EventBus()
sessions = SessionManager(bus, settings)
store = OnePagerStore(settings)
leads = lead_mod.LeadStore(settings)
_pdf_tasks: set = set()


def _on_event(ev: Event) -> None:
    """Al terminar el enjambre: se guarda el one-pager, se pre-genera el PDF y se ofrece el QR."""
    if ev.type != "artifact.onepager" or not ev.session_id or ev.session_id.startswith("replay-"):
        return
    sid = ev.session_id
    store.save(sid, ev.data)
    task = asyncio.get_running_loop().create_task(_pregen_pdf(sid))
    _pdf_tasks.add(task)
    task.add_done_callback(_pdf_tasks.discard)
    bus.publish("share.ready", session_id=sid, qr_url=f"/api/qr/{sid}.svg?t={store.token(sid)}")


async def _pregen_pdf(sid: str) -> None:
    try:
        await render_pdf(store.get(sid) or {}, store.pdf_path(sid), settings)
    except Exception:  # noqa: BLE001 — se reintenta al pedirlo
        logging.getLogger(__name__).exception("No se pudo pre-generar el PDF de %s", sid)


bus.add_listener(_on_event)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await sessions.reset(announce=False)


app = FastAPI(title="Readymind · AI Tour demo", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class TextSessionRequest(BaseModel):
    problema: str
    industria: str = "no especificada"
    volumen: str = "no especificado"
    datos: str = "no especificados"


def _rss_mb() -> float:
    try:
        pages = int(open("/proc/self/statm").read().split()[1])
        return round(pages * os.sysconf("SC_PAGE_SIZE") / 1e6, 1)
    except Exception:  # noqa: BLE001 — no-Linux
        return 0.0


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "mode": settings.demo_mode, "state": sessions.state, "session_id": sessions.session_id, "rss_mb": _rss_mb()}


class ModeRequest(BaseModel):
    mode: str


@app.post("/api/mode")
async def set_mode(req: ModeRequest) -> dict:
    """Cambia el modo en caliente (operador del stand): live | mock | replay."""
    if req.mode not in ("live", "mock", "replay"):
        raise HTTPException(422, "Modo inválido")
    await sessions.reset()
    settings.demo_mode = req.mode
    bus.publish("mode.changed", mode=req.mode)
    return {"ok": True, "mode": req.mode}


@app.post("/api/replay")
async def play_recorded() -> dict:
    """Tecla P: reproduce de inmediato la sesión grabada más reciente (si se cae la red)."""
    await sessions.start_replay()
    return {"ok": True}


@app.post("/api/session/text")
async def start_text_session(req: TextSessionRequest) -> dict:
    brief = Brief(problema=req.problema[:600], industria=req.industria[:80], volumen=req.volumen[:120], datos=req.datos[:200])
    session_id = await sessions.start(brief)
    return {"session_id": session_id, "mode": settings.demo_mode}


@app.post("/api/reset")
async def reset() -> dict:
    await sessions.reset()
    return {"ok": True}


def _check(sid: str, t: str) -> dict:
    payload = store.get(sid)
    if payload is None or not store.valid(sid, t):
        raise HTTPException(404, "No encontrado")
    return payload


def _base_url(request: Request) -> str:
    return settings.public_base_url.rstrip("/") or str(request.base_url).rstrip("/")


@app.get("/api/qr/{sid}.svg")
async def qr(sid: str, t: str, request: Request) -> Response:
    import io

    import segno

    _check(sid, t)
    buf = io.BytesIO()
    segno.make(f"{_base_url(request)}/lead/{sid}?t={t}", error="m").save(buf, kind="svg", scale=10, border=2, dark="#11243e", light="#ffffff")
    return Response(buf.getvalue(), media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/lead/{sid}", response_class=HTMLResponse)
async def lead_page(sid: str, t: str) -> HTMLResponse:
    payload = _check(sid, t)
    costo = (payload.get("costo") or {}).get("total_usd")
    html = templates().get_template("lead.html").render(
        titulo=(payload.get("onepager") or {}).get("titulo", "Tu solución de IA"),
        costo=f"USD {costo:,.0f} / mes" if costo else "",
        post_url=f"/api/lead/{sid}?t={t}",
        pdf_url=f"/api/pdf/{sid}?t={t}",
    )
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


@app.get("/lead-assets/logo.png")
async def lead_logo() -> FileResponse:
    return FileResponse(ONEPAGER_DIR / "assets" / "readymind-logo.png")


@app.get("/privacidad", response_class=HTMLResponse)
async def privacidad() -> HTMLResponse:
    return HTMLResponse(templates().get_template("privacidad.html").render(
        responsable=settings.privacy_responsable, contacto=settings.privacy_contacto, aviso_integral=settings.privacy_aviso_integral))


@app.get("/api/pdf/{sid}")
async def pdf(sid: str, t: str) -> FileResponse:
    payload = _check(sid, t)
    path = await render_pdf(payload, store.pdf_path(sid), settings)
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.post("/api/lead/{sid}")
async def lead_submit(sid: str, t: str, lead: lead_mod.LeadIn, request: Request) -> dict:
    payload = _check(sid, t)
    if leads.count_for(sid) >= settings.max_leads_per_session:
        raise HTTPException(429, "Ya recibimos los datos de esta sesión")
    titulo = (payload.get("onepager") or {}).get("titulo", "")
    path = await render_pdf(payload, store.pdf_path(sid), settings)
    message = {
        "nombre": lead.nombre.strip(), "empresa": lead.empresa.strip(), "correo": lead.correo, "cargo": lead.cargo.strip(),
        "acepta_contacto": lead.acepta_contacto, "titulo": titulo, "session_id": sid,
        "pdf_url": f"{_base_url(request)}/api/pdf/{sid}?t={t}",
    }
    envio = await lead_mod.send_power_automate(settings, message, path)
    await leads.add(sid, lead, titulo, envio)
    if envio != "enviado":
        await leads.to_outbox(message)
    bus.publish("lead.received", envio=envio)
    return {"ok": True, "envio": envio}


@app.websocket("/ws/voice")
async def voice(ws: WebSocket) -> None:
    """Micrófono del stand ⇄ recepcionista (Foundry voice agent o simulada)."""
    await ws.accept()
    await sessions.reset()
    interview = sessions.new_interview()
    try:
        await interview.run(ws)
    finally:
        with contextlib.suppress(Exception):
            await ws.close()


@app.websocket("/ws/stage")
async def stage(ws: WebSocket) -> None:
    await ws.accept()
    q = bus.subscribe()
    try:
        models = {a: getattr(settings, f"model_{a}") for a in ("arquitecto", "financiero", "riesgo", "diagramador", "redactor")}
        await ws.send_json({"type": "hello", "data": {"mode": settings.demo_mode, "state": sessions.state, "models": models}})
        for ev in list(bus.history):  # estado actual para clientes que se conectan tarde
            await ws.send_text(ev.model_dump_json())
        while True:
            ev = await q.get()
            await ws.send_text(ev.model_dump_json())
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        bus.unsubscribe(q)
        with contextlib.suppress(Exception):
            await ws.close()


if settings.frontend_dist.exists():
    app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")
