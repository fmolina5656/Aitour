"""Persistencia del one-pager de cada sesión + link firmado para el QR."""

import hashlib
import hmac
import json
import logging
import secrets
from pathlib import Path

from ..config import Settings

log = logging.getLogger(__name__)


class OnePagerStore:
    def __init__(self, settings: Settings) -> None:
        self.dir = Path(settings.data_dir) / "onepagers"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir = Path(settings.data_dir) / "pdf"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        if not settings.lead_secret:
            log.warning("LEAD_SECRET vacío: los QR dejan de valer si el backend se reinicia.")
        self._secret = (settings.lead_secret or secrets.token_hex(32)).encode()

    def token(self, session_id: str) -> str:
        return hmac.new(self._secret, session_id.encode(), hashlib.sha256).hexdigest()[:20]

    def valid(self, session_id: str, token: str) -> bool:
        return hmac.compare_digest(self.token(session_id), token or "")

    def save(self, session_id: str, payload: dict) -> None:
        (self.dir / f"{_safe(session_id)}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def get(self, session_id: str) -> dict | None:
        p = self.dir / f"{_safe(session_id)}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def pdf_path(self, session_id: str) -> Path:
        return self.pdf_dir / f"readymind-onepager-{_safe(session_id)}.pdf"


def _safe(session_id: str) -> str:
    return "".join(c for c in session_id if c.isalnum() or c in "-_")[:64]
