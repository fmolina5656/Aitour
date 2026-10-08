"""Reenvía a Power Automate los leads que quedaron pendientes (sin URL configurada o con error).

Uso:  cd backend && .venv/bin/python -m scripts.retry_outbox
Los que se envían salen de data/leads/outbox.jsonl; los que fallan se quedan para el próximo intento.
"""

import asyncio
import json
from pathlib import Path

from app.config import get_settings
from app.onepager.leads import send_power_automate
from app.onepager.store import OnePagerStore


async def main() -> None:
    s = get_settings()
    if not s.power_automate_url:
        raise SystemExit("Falta POWER_AUTOMATE_URL en .env")
    outbox = Path(s.data_dir) / "leads" / "outbox.jsonl"
    if not outbox.exists():
        print("Bandeja de salida vacía.")
        return
    store = OnePagerStore(s)
    pending = [json.loads(line) for line in outbox.read_text(encoding="utf-8").splitlines() if line.strip()]
    left = []
    for msg in pending:
        status = await send_power_automate(s, msg, store.pdf_path(msg["session_id"]))
        print(f"{msg['correo']}: {status}")
        if status != "enviado":
            left.append(msg)
    outbox.write_text("".join(json.dumps(m, ensure_ascii=False) + "\n" for m in left), encoding="utf-8")
    print(f"Enviados {len(pending) - len(left)} de {len(pending)}.")


if __name__ == "__main__":
    asyncio.run(main())
