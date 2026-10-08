"""Cálculo determinista de costos. El LLM propone cantidades; los números los calcula Python."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .config import get_settings


@dataclass
class CostLine:
    id: str
    servicio: str
    nombre: str
    categoria: str
    cantidad: float
    unidad: str
    precio_unitario: float
    costo_usd: float
    supuesto: str
    premium: bool = False


@lru_cache
def load_catalog(path: Path | None = None) -> dict:
    p = path or get_settings().pricing_dir / "catalogo.json"
    return json.loads(Path(p).read_text(encoding="utf-8"))


@lru_cache
def load_runtime_prices(path: Path | None = None) -> dict:
    p = path or get_settings().pricing_dir / "runtime.json"
    return json.loads(Path(p).read_text(encoding="utf-8"))["modelos"]


def estimate(componentes: list[dict]) -> dict:
    """Recibe los componentes del Arquitecto y devuelve el desglose mensual."""
    cat = load_catalog()
    items = cat["items"]
    lines: list[CostLine] = []
    unknown: list[str] = []
    for c in componentes:
        servicio = c.get("servicio", "")
        ref = items.get(servicio)
        if ref is None:
            unknown.append(servicio)
            continue
        cantidad = max(float(c.get("cantidad") or 0), 0.0)
        lines.append(
            CostLine(
                id=c.get("id", servicio),
                servicio=servicio,
                nombre=ref["nombre"],
                categoria=ref["categoria"],
                cantidad=cantidad,
                unidad=ref["unidad"],
                precio_unitario=ref["precio_usd"],
                costo_usd=round(cantidad * ref["precio_usd"], 2),
                supuesto=c.get("supuesto", ""),
                premium=bool(ref.get("premium", False)),
            )
        )
    total = round(sum(line.costo_usd for line in lines), 2)
    top = max(lines, key=lambda line: line.costo_usd, default=None)
    return {
        "items": [line.__dict__ for line in lines],
        "total_usd": total,
        "top_item": top.id if top else None,
        "top_share": round(top.costo_usd / total, 3) if top and total else 0.0,
        "desconocidos": unknown,
        "disclaimer": cat["disclaimer"],
        "vigencia": cat["vigencia"],
    }


def runtime_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = load_runtime_prices()
    p = prices.get(model) or prices["default"]
    return round(input_tokens / 1e6 * p["input"] + output_tokens / 1e6 * p["output"], 6)


def catalog_for_prompt() -> str:
    """Lista compacta de servicios válidos para el prompt del Arquitecto."""
    items = load_catalog()["items"]
    return "\n".join(f"- {k}: {v['nombre']} (unidad: {v['unidad']})" for k, v in items.items())
