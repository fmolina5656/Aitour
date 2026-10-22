"""Copiloto del vendedor (/vendedor): fichas rápidas de visitantes y la lista de leads del día.

- Solo para el equipo: todas las rutas piden el PIN del stand (SELLER_PIN) en el encabezado X-Seller-Pin.
  Sin SELLER_PIN configurado, las rutas responden 503 y no exponen nada.
- Une dos fuentes sin duplicados (por correo, o por nombre + empresa): los leads que dejó el visitante con el QR
  (onepager/leads.py) y las fichas que carga el vendedor. Se descarga como CSV para Excel y el CRM.
- Las fichas guardan datos personales de los visitantes: quedan en el mismo volumen que los leads del QR.
"""

import asyncio
import csv
import datetime as dt
import hmac
import io
import json
import time
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from .config import Settings
from .onepager.leads import EMAIL_RE

INTERESES = ("taller", "piloto", "propuesta", "info", "curioso")
CSV_FIELDS = ["fecha", "origen", "nombre", "empresa", "correo", "cargo", "industria", "interes", "acepta_contacto",
              "solucion", "nota", "vendedor"]


class Visita(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    empresa: str = Field(default="", max_length=100)
    correo: str = Field(default="", max_length=120)
    cargo: str = Field(default="", max_length=80)
    industria: str = Field(default="", max_length=60)
    interes: Literal["taller", "piloto", "propuesta", "info", "curioso"] = "info"
    nota: str = Field(default="", max_length=600)
    vendedor: str = Field(default="", max_length=60)

    @field_validator("correo")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip()
        if v and not EMAIL_RE.match(v):
            raise ValueError("Correo inválido")
        return v


def _key(row: dict) -> str:
    correo = (row.get("correo") or "").strip().lower()
    if correo:
        return "c:" + correo
    return "n:" + " ".join((row.get("nombre") or "").lower().split()) + "|" + " ".join((row.get("empresa") or "").lower().split())


def merge(qr: list[dict], fichas: list[dict]) -> list[dict]:
    """Un registro por persona: la ficha del vendedor completa los datos del QR (industria, interés, nota)."""
    out: dict[str, dict] = {}
    for r in qr:
        out.setdefault(_key(r), {**r, "origen": "QR"})
    for f in fichas:
        k = _key(f)
        if k in out:
            base = out[k]
            for campo in ("industria", "interes", "nota", "vendedor", "cargo", "empresa"):
                if f.get(campo) and not base.get(campo):
                    base[campo] = f[campo]
            if f.get("nota") and base.get("nota") and f["nota"] not in base["nota"]:
                base["nota"] = base["nota"] + " · " + f["nota"]
            base["origen"] = "QR + vendedor"
        else:
            out[k] = {**f, "origen": "vendedor"}
    return sorted(out.values(), key=lambda r: r.get("fecha", ""), reverse=True)


class SellerStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.dir = Path(settings.data_dir) / "vendedor"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def add(self, v: Visita) -> dict:
        row = {"fecha": dt.datetime.now().isoformat(timespec="seconds"), **v.model_dump()}
        row = {k: (val.strip() if isinstance(val, str) else val) for k, val in row.items()}
        async with self._lock:
            with (self.dir / "fichas.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def fichas(self) -> list[dict]:
        return _read_jsonl(self.dir / "fichas.jsonl")


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def build_router(get_settings, get_onepagers) -> APIRouter:
    """Recibe funciones (no objetos) para leer siempre la configuración y el OnePagerStore vigentes; del segundo se
    toman la industria y la solución de cada lead del QR."""
    router = APIRouter(prefix="/api/vendedor")
    stores: dict[str, SellerStore] = {}

    def seller_store() -> SellerStore:
        s = get_settings()
        key = str(s.data_dir)
        if key not in stores:
            stores[key] = SellerStore(s)
        return stores[key]
    fails: dict[str, list[float]] = {}

    def check(pin: str | None, request: Request) -> None:
        client = request.client.host if request.client else "?"
        settings = get_settings()
        if not settings.seller_pin:
            raise HTTPException(503, "Falta configurar SELLER_PIN en la app")
        recent = [t for t in fails.get(client, []) if time.time() - t < 300]
        if len(recent) >= 10:
            raise HTTPException(429, "Demasiados intentos: espera unos minutos")
        if not pin or not hmac.compare_digest(pin.strip(), settings.seller_pin):
            fails[client] = recent + [time.time()]
            raise HTTPException(401, "PIN incorrecto")

    def qr_leads() -> list[dict]:
        rows = []
        for r in _read_jsonl(Path(get_settings().data_dir) / "leads" / "leads.jsonl"):
            payload = get_onepagers().get(r.get("session_id", "")) or {}
            r = {**r, "industria": (payload.get("brief") or {}).get("industria", ""),
                 "solucion": r.get("titulo") or (payload.get("onepager") or {}).get("titulo", "")}
            rows.append(r)
        return rows

    def all_leads(solo_hoy: bool) -> list[dict]:
        rows = merge(qr_leads(), seller_store().fichas())
        if solo_hoy:
            hoy = dt.date.today().isoformat()
            rows = [r for r in rows if str(r.get("fecha", "")).startswith(hoy)]
        return rows

    @router.post("/login")
    async def login(request: Request, x_seller_pin: str | None = Header(default=None)) -> dict:
        check(x_seller_pin, request)
        return {"ok": True}

    @router.post("/visita")
    async def visita(v: Visita, request: Request, x_seller_pin: str | None = Header(default=None)) -> dict:
        check(x_seller_pin, request)
        return {"ok": True, "ficha": await seller_store().add(v)}

    @router.get("/leads")
    async def leads(request: Request, hoy: bool = True, x_seller_pin: str | None = Header(default=None)) -> dict:
        check(x_seller_pin, request)
        rows = all_leads(hoy)
        return {"total": len(rows), "leads": [{k: r.get(k, "") for k in CSV_FIELDS} for r in rows]}

    @router.get("/leads.csv")
    async def leads_csv(request: Request, hoy: bool = False, pin: str = "", x_seller_pin: str | None = Header(default=None)) -> Response:
        check(x_seller_pin or pin, request)  # el link de descarga lleva el PIN en la URL (no hay encabezados en una descarga)
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in all_leads(hoy):
            row = {k: r.get(k, "") for k in CSV_FIELDS}
            if isinstance(row["acepta_contacto"], bool):
                row["acepta_contacto"] = "sí" if row["acepta_contacto"] else "no"
            w.writerow(row)
        name = f"leads-aitour-{dt.date.today().isoformat()}.csv"
        return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})

    return router
