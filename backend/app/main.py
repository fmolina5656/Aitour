"""API del stand: WebSocket para la pantalla, REST para iniciar/resetear sesiones.

Cada pantalla (PC y tablets) es una sala con su propio bus y su propia sesión: se elige con ?sala=<nombre>.
"""

import asyncio
import contextlib
import logging
import mimetypes
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import ocr as ocr_mod
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

# /vision carga MediaPipe como módulo ES + WASM: el navegador exige estos tipos exactos
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("application/wasm", ".wasm")

settings = get_settings()
telemetry.setup(settings)
store = OnePagerStore(settings)
leads = lead_mod.LeadStore(settings)
_pdf_tasks: set = set()


@dataclass
class Sala:
    name: str
    bus: EventBus
    sessions: SessionManager


def _make_sala(name: str) -> Sala:
    bus = EventBus()
    sala = Sala(name, bus, SessionManager(bus, settings, sala=name))
    bus.add_listener(lambda ev: _on_event(sala, ev))
    return sala


salas: dict[str, Sala] = {}
_sesion_sala: dict[str, str] = {}  # session_id → sala, para avisar en la pantalla correcta cuando llega un lead


def _on_event(sala: Sala, ev: Event) -> None:
    """Al terminar el enjambre: se guarda el one-pager, se pre-genera el PDF y se ofrece el QR."""
    if ev.type != "artifact.onepager" or not ev.session_id or ev.session_id.startswith("replay-"):
        return
    sid = ev.session_id
    _sesion_sala[sid] = sala.name
    store.save(sid, ev.data)
    task = asyncio.get_running_loop().create_task(_pregen_pdf(sid))
    _pdf_tasks.add(task)
    task.add_done_callback(_pdf_tasks.discard)
    sala.bus.publish("share.ready", session_id=sid, qr_url=f"/api/qr/{sid}.svg?t={store.token(sid)}")


async def _pregen_pdf(sid: str) -> None:
    try:
        await render_pdf(store.get(sid) or {}, store.pdf_path(sid), settings)
    except Exception:  # noqa: BLE001 — se reintenta al pedirlo
        logging.getLogger(__name__).exception("No se pudo pre-generar el PDF de %s", sid)


for _name in settings.sala_names:
    salas[_name] = _make_sala(_name)


def _sala(sala: str | None) -> Sala:
    """La sala pedida; sin nombre, la primera (la PC del stand)."""
    if not sala:
        return next(iter(salas.values()))
    found = salas.get(sala.strip().lower())
    if found is None:
        raise HTTPException(404, f"Sala desconocida: {sala}")
    return found


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await asyncio.gather(*(s.sessions.reset(announce=False) for s in salas.values()))


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
async def health(sala: str | None = None) -> dict:
    s = _sala(sala)
    return {
        "ok": True, "mode": settings.demo_mode, "sala": s.name, "state": s.sessions.state, "session_id": s.sessions.session_id,
        "salas": {n: x.sessions.state for n, x in salas.items()}, "rss_mb": _rss_mb(),
    }


class ModeRequest(BaseModel):
    mode: str


@app.post("/api/mode")
async def set_mode(req: ModeRequest) -> dict:
    """Cambia el modo en caliente (operador del stand): live | mock | replay."""
    if req.mode not in ("live", "mock", "replay"):
        raise HTTPException(422, "Modo inválido")
    # el modo es del backend completo: se reinician todas las salas y todas se enteran
    await asyncio.gather(*(s.sessions.reset() for s in salas.values()))
    settings.demo_mode = req.mode
    for s in salas.values():
        s.bus.publish("mode.changed", mode=req.mode)
    return {"ok": True, "mode": req.mode}


@app.post("/api/replay")
async def play_recorded(sala: str | None = None) -> dict:
    """Tecla P: reproduce de inmediato la sesión grabada más reciente (si se cae la red)."""
    await _sala(sala).sessions.start_replay()
    return {"ok": True}


@app.post("/api/session/text")
async def start_text_session(req: TextSessionRequest, sala: str | None = None) -> dict:
    s = _sala(sala)
    brief = Brief(problema=req.problema[:600], industria=req.industria[:80], volumen=req.volumen[:120], datos=req.datos[:200])
    session_id = await s.sessions.start(brief)
    return {"session_id": session_id, "mode": settings.demo_mode, "sala": s.name}


class OcrRequest(BaseModel):
    image: str  # data URL (image/jpeg|png|webp;base64)


@app.post("/api/ocr")
async def ocr(req: OcrRequest) -> dict:
    """Lector de documentos de /ocr: clasifica, extrae y valida. La imagen no se guarda en ningún lado."""
    try:
        return await ocr_mod.leer_documento(req.image, settings)
    except ocr_mod.OcrError as exc:
        raise HTTPException(exc.status, exc.mensaje) from None


@app.post("/api/reset")
async def reset(sala: str | None = None) -> dict:
    await _sala(sala).sessions.reset()
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
    if (s := salas.get(_sesion_sala.get(sid, ""))) is not None and s.sessions.session_id == sid:
        s.bus.publish("lead.received", envio=envio)  # solo si esa pantalla sigue mostrando la sesión
    return {"ok": True, "envio": envio}


async def _ws_sala(ws: WebSocket, sala: str | None) -> Sala | None:
    """Acepta el WebSocket de una sala; si no existe, lo cierra con 4404 (el frontend deja de reintentar)."""
    await ws.accept()  # se acepta antes de cerrar para que el código 4404 llegue al navegador
    try:
        return _sala(sala)
    except HTTPException:
        await ws.close(code=4404, reason="Sala desconocida")
        return None


@app.websocket("/ws/voice")
async def voice(ws: WebSocket, sala: str | None = None) -> None:
    """Micrófono de la sala ⇄ recepcionista (Foundry voice agent o simulada)."""
    s = await _ws_sala(ws, sala)
    if s is None:
        return
    await s.sessions.reset()
    interview = s.sessions.new_interview()
    try:
        await interview.run(ws)
    finally:
        with contextlib.suppress(Exception):
            await ws.close()


@app.websocket("/ws/stage")
async def stage(ws: WebSocket, sala: str | None = None) -> None:
    s = await _ws_sala(ws, sala)
    if s is None:
        return
    bus = s.bus
    q = bus.subscribe()
    try:
        models = {a: getattr(settings, f"model_{a}") for a in ("arquitecto", "financiero", "riesgo", "diagramador", "redactor")}
        await ws.send_json({"type": "hello", "data": {
            "mode": settings.demo_mode, "state": s.sessions.state, "models": models, "sala": s.name, "salas": list(salas)}})
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
