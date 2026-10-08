"""API del stand: WebSocket para la pantalla, REST para iniciar/resetear sesiones."""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import get_settings
from .events import EventBus
from .session import SessionManager
from .swarm.schemas import Brief

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()
bus = EventBus()
sessions = SessionManager(bus, settings)


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


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "mode": settings.demo_mode, "state": sessions.state, "session_id": sessions.session_id}


@app.post("/api/session/text")
async def start_text_session(req: TextSessionRequest) -> dict:
    brief = Brief(problema=req.problema[:600], industria=req.industria[:80], volumen=req.volumen[:120], datos=req.datos[:200])
    session_id = await sessions.start(brief)
    return {"session_id": session_id, "mode": settings.demo_mode}


@app.post("/api/reset")
async def reset() -> dict:
    await sessions.reset()
    return {"ok": True}


@app.websocket("/ws/stage")
async def stage(ws: WebSocket) -> None:
    await ws.accept()
    q = bus.subscribe()
    try:
        await ws.send_json({"type": "hello", "data": {"mode": settings.demo_mode, "state": sessions.state}})
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
