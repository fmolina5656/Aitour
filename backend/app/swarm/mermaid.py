"""Genera Mermaid válido a partir de la arquitectura estructurada (el LLM nunca escribe Mermaid)."""

import re

CATEGORY_CLASS = {"IA": "ia", "Voz": "ia", "Datos": "datos", "Cómputo": "comp", "Integración": "integ", "Gobierno": "gob"}


def _id(raw: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]", "_", raw or "x")
    return s if s[0].isalpha() else f"n_{s}"


def _label(raw: str) -> str:
    return (raw or "").replace('"', "'").replace("\n", " ")[:40]


def build(componentes: list[dict], conexiones: list[dict], categorias: dict[str, str] | None = None) -> str:
    categorias = categorias or {}
    lines = ["flowchart LR"]
    ids = set()
    for c in componentes:
        nid = _id(c["id"])
        ids.add(nid)
        cls = CATEGORY_CLASS.get(categorias.get(c["id"], ""), "comp")
        lines.append(f'  {nid}["{_label(c["nombre"])}"]:::{cls}')
    for e in conexiones:
        a, b = _id(e["de"]), _id(e["a"])
        if a in ids and b in ids:
            etiqueta = _label(e.get("etiqueta", ""))
            lines.append(f'  {a} -->|"{etiqueta}"| {b}' if etiqueta else f"  {a} --> {b}")
    return "\n".join(lines)
