"""Leads del stand: JSONL + CSV locales y envío del one-pager con Power Automate.

Los datos personales se guardan solo con consentimiento explícito (aviso de privacidad, LFPDPPP).
Si Power Automate no está configurado o falla, el lead queda en la bandeja de salida (outbox.jsonl)
y se reenvía con `python -m scripts.retry_outbox`.
"""

import asyncio
import base64
import csv
import datetime as dt
import json
import logging
import re
from pathlib import Path

import httpx
from pydantic import BaseModel, Field, field_validator

from ..config import Settings

log = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)
CSV_FIELDS = ["fecha", "session_id", "nombre", "empresa", "correo", "cargo", "acepta_contacto", "titulo", "envio"]


class LeadIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    empresa: str = Field(min_length=1, max_length=100)
    correo: str = Field(max_length=120)
    cargo: str = Field(default="", max_length=80)
    acepta_privacidad: bool
    acepta_contacto: bool = False

    @field_validator("correo")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_RE.match(v):
            raise ValueError("Correo inválido")
        return v

    @field_validator("acepta_privacidad")
    @classmethod
    def _consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Se requiere aceptar el aviso de privacidad")
        return v


class LeadStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.dir = Path(settings.data_dir) / "leads"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def add(self, session_id: str, lead: LeadIn, titulo: str, envio: str) -> dict:
        row = {
            "fecha": dt.datetime.now().isoformat(timespec="seconds"),
            "session_id": session_id,
            "nombre": lead.nombre.strip(),
            "empresa": lead.empresa.strip(),
            "correo": lead.correo,
            "cargo": lead.cargo.strip(),
            "acepta_contacto": lead.acepta_contacto,
            "titulo": titulo,
            "envio": envio,
        }
        async with self._lock:
            with (self.dir / "leads.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            csv_path = self.dir / "leads.csv"
            new = not csv_path.exists()
            with csv_path.open("a", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                if new:
                    w.writeheader()
                w.writerow(row)
        return row

    async def to_outbox(self, payload: dict) -> None:
        async with self._lock:
            with (self.dir / "outbox.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def count_for(self, session_id: str) -> int:
        p = self.dir / "leads.jsonl"
        if not p.exists():
            return 0
        return sum(1 for line in p.read_text(encoding="utf-8").splitlines() if f'"session_id": "{session_id}"' in line)


async def send_power_automate(settings: Settings, payload: dict, pdf: Path | None) -> str:
    """Dispara el flujo de Power Automate (que manda el correo con el PDF adjunto).

    Contrato del flujo (disparador "When an HTTP request is received"), JSON:
      {nombre, empresa, correo, cargo, titulo, session_id, pdf_url, pdf_nombre, pdf_base64}
    Devuelve "enviado", "pendiente" (sin URL configurada) o "error".
    """
    if not settings.power_automate_url:
        return "pendiente"
    body = dict(payload)
    if pdf and pdf.exists():
        body["pdf_nombre"] = pdf.name
        body["pdf_base64"] = base64.b64encode(pdf.read_bytes()).decode()
    try:
        async with httpx.AsyncClient(timeout=settings.power_automate_timeout_s) as client:
            r = await client.post(settings.power_automate_url, json=body)
            r.raise_for_status()
        return "enviado"
    except Exception as exc:  # noqa: BLE001 — el lead nunca se pierde: queda en outbox
        log.warning("Power Automate falló: %s", exc)
        return "error"
