"""One-pager ejecutivo → HTML (marca Readymind) → PDF con Chromium (Playwright)."""

import base64
import datetime as dt
import logging
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import Settings

log = logging.getLogger(__name__)
HERE = Path(__file__).parent
LAYERS = ["Datos", "IA", "Voz", "Cómputo", "Integración", "Gobierno"]


@lru_cache
def _env() -> Environment:
    return Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html"]))


@lru_cache
def _logo_data_uri() -> str:
    data = (HERE / "assets" / "readymind-logo.png").read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode()


def short_name(n: str) -> str:
    parts = n.split(" · ")
    base = parts[1] if parts[0] == "Foundry" and len(parts) > 1 else parts[0]
    for prefix in ("Azure ", "Microsoft "):
        base = base.removeprefix(prefix)
    return base.split(" / ")[0]


def render_html(payload: dict) -> str:
    costo = payload.get("costo") or {}
    items = sorted(costo.get("items", []), key=lambda i: -i["costo_usd"])
    layers = [(cat, [short_name(i["nombre"]) for i in items if i["categoria"] == cat]) for cat in LAYERS]
    return _env().get_template("onepager.html").render(
        op=payload.get("onepager") or {},
        brief=payload.get("brief") or {},
        costo=costo,
        items=items[:7],
        layers=[(c, names) for c, names in layers if names],
        riesgo=payload.get("riesgo") or {},
        objeciones=payload.get("objeciones") or [],
        logo=_logo_data_uri(),
        fecha=dt.date.today().strftime("%d/%m/%Y"),
    )


async def render_pdf(payload: dict, out: Path, settings: Settings) -> Path:
    """Genera el PDF (una página carta). Idempotente: si ya existe, lo reutiliza."""
    if out.exists():
        return out
    from playwright.async_api import async_playwright

    html = render_html(payload)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=settings.chromium_path or None, args=["--no-sandbox"])
        try:
            page = await browser.new_page()
            await page.set_content(html, wait_until="load")
            tmp = out.with_suffix(".tmp")
            await page.pdf(path=str(tmp), format="Letter", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            tmp.replace(out)
        finally:
            await browser.close()
    return out
