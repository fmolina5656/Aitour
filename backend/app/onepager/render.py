"""One-pager ejecutivo → HTML (marca Readymind) → PDF con Chromium (Playwright)."""

import base64
import datetime as dt
import logging
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import Settings
from ..swarm import diagram

log = logging.getLogger(__name__)
HERE = Path(__file__).parent
MAX_COST_ROWS = 6

# Ajusta la escala del contenido hasta que entre en la hoja: nunca se corta, como mucho se achica un poco.
FIT_JS = """() => {
  const page = document.getElementById('page'), fit = document.getElementById('fit');
  let z = 1;
  while (page.scrollHeight > page.clientHeight + 1 && z > 0.62) {
    z = Math.round((z - 0.02) * 100) / 100;
    fit.style.setProperty('--z', z);
  }
  return z;
}"""


def usd(x: float | None) -> str:
    """USD 1,234 · y "< USD 1" para los servicios de consumo que casi no cuestan (antes salía "USD 0")."""
    x = x or 0
    if x == 0:
        return "Incluido"  # p. ej. Foundry Agent Service: se paga por el modelo y las herramientas
    return "< USD 1" if x < 1 else f"USD {x:,.0f}"


def _clip(s: str | None, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip(" ,.;") + "…"


@lru_cache
def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html"]))
    env.filters["usd"] = usd
    return env


@lru_cache
def _logo_data_uri() -> str:
    data = (HERE / "assets" / "readymind-logo.png").read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode()


def render_html(payload: dict) -> str:
    costo = payload.get("costo") or {}
    items = sorted(costo.get("items", []), key=lambda i: -i["costo_usd"])
    brief = payload.get("brief") or {}
    op = dict(payload.get("onepager") or {})
    # los textos del modelo pueden venir largos: se acotan para que la hoja respire
    op["titulo"] = _clip(op.get("titulo"), 80)
    op["problema"] = _clip(op.get("problema"), 360)
    op["solucion"] = _clip(op.get("solucion"), 380)
    arq = payload.get("arquitectura") or {}
    diagrama = payload.get("diagrama")
    svg = diagram.build(arq.get("componentes", []), arq.get("conexiones", []), items, spec=diagrama, theme="light") if arq.get("componentes") else ""
    resto = items[MAX_COST_ROWS:]
    return _env().get_template("onepager.html").render(
        op=op,
        subtitulo=" · ".join(p for p in (_clip(brief.get("industria"), 40), _clip(brief.get("volumen"), 60)) if p),
        costo=costo,
        items=items[:MAX_COST_ROWS],
        resto={"n": len(resto), "costo": sum(i["costo_usd"] for i in resto)} if resto else None,
        diagram_svg=svg,
        diagrama=diagrama,
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
            page = await browser.new_page(viewport={"width": 816, "height": 1056})  # carta a 96 dpi
            await page.set_content(html, wait_until="load")
            z = await page.evaluate(FIT_JS)
            if z < 1:
                log.info("One-pager ajustado a escala %.2f para que entre en una hoja", z)
            tmp = out.with_suffix(".tmp")
            await page.pdf(path=str(tmp), format="Letter", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            tmp.replace(out)
        finally:
            await browser.close()
    return out
