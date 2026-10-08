"""Diagrama de arquitectura en Azure → SVG (pantalla oscura y PDF claro).

El modelo nunca dibuja: el Arquitecto da componentes y conexiones, el Diagramador las agrupa en zonas, ordena
el flujo y lo explica, y aquí se calcula el layout. Si el Diagramador no llega (o devuelve ids inválidos), el
layout sale de las conexiones (niveles topológicos), así el diagrama está desde la primera propuesta.

Los servicios de gobierno que no están en medio del flujo (Key Vault, App Insights, Purview…) van en una banda
transversal abajo, como en los diagramas de referencia de Azure.
"""

from dataclasses import dataclass
from xml.sax.saxutils import escape

NODE_W, NODE_H = 200, 58
COL_GAP, ROW_GAP = 74, 16
PAD, TITLE_H = 18, 30
BAND_NODE_H = 34
CAT_RANK = {"Voz": 0, "Datos": 0, "IA": 1, "Cómputo": 2, "Integración": 2, "Gobierno": 1}

# Color por categoría del catálogo (franja del nodo y leyenda)
CAT_COLOR = {"IA": "#8b5cf6", "Voz": "#ec4899", "Datos": "#3b82f6", "Cómputo": "#14b8a6", "Integración": "#f59e0b", "Gobierno": "#22c55e"}

THEMES = {
    "dark": {"node": "#0f1b2e", "stroke": "#24395a", "text": "#f3f6fa", "sub": "#8fa0b8", "title": "#8fa0b8",
             "edge": "#4b6488", "badge": "#397ef6", "badge_text": "#ffffff", "label_bg": "#050a12", "band": "#0b1424", "new": "#66de7f"},
    "light": {"node": "#ffffff", "stroke": "#d6dce5", "text": "#11243e", "sub": "#5b6b80", "title": "#6b7280",
              "edge": "#9aa8bb", "badge": "#2c68f5", "badge_text": "#ffffff", "label_bg": "#ffffff", "band": "#f4f6f8", "new": "#16a34a"},
}


def short_name(n: str) -> str:
    """"Azure AI Search · Basic" → "AI Search"; "Foundry · GPT-5.4 mini" → "GPT-5.4 mini"."""
    parts = n.split(" · ")
    base = parts[1] if parts[0] == "Foundry" and len(parts) > 1 else parts[0]
    for prefix in ("Azure ", "Microsoft "):
        base = base.removeprefix(prefix)
    return base.split(" / ")[0]


def _clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


@dataclass
class _Node:
    id: str
    servicio: str  # nombre del servicio en el catálogo ("Azure AI Search · Basic")
    nombre: str
    categoria: str
    x: float = 0
    y: float = 0
    w: float = NODE_W
    h: float = NODE_H


def _levels(ids: list[str], edges: list[tuple[str, str]], cats: dict[str, str]) -> dict[str, int]:
    """Nivel = camino más largo desde una fuente (tolera ciclos: relaja como mucho N veces)."""
    lvl = {i: 0 for i in ids}
    connected = {a for a, b in edges} | {b for a, b in edges}
    for _ in range(len(ids)):
        changed = False
        for a, b in edges:
            if lvl[b] < lvl[a] + 1 and lvl[a] + 1 < len(ids):
                lvl[b] = lvl[a] + 1
                changed = True
        if not changed:
            break
    # una fuente (sin entradas) va justo antes de lo que alimenta: AI Search al lado del modelo, no al inicio
    for i in ids:
        targets = [lvl[b] for a, b in edges if a == i]
        if targets and not any(b == i for a, b in edges):
            lvl[i] = max(min(targets) - 1, 0)
    top = max(lvl.values(), default=0)
    for i in ids:  # sin conexiones: por capa típica (datos al inicio, cómputo/integración al final)
        if i not in connected:
            lvl[i] = min(CAT_RANK.get(cats.get(i, ""), 1), top) if top else 0
    return lvl


CAT_ZONE = {"Datos": "Datos", "IA": "IA · Foundry", "Voz": "Voz", "Cómputo": "Aplicación", "Integración": "Integración", "Gobierno": "Seguridad"}


def _zone_names(cols: list[list[_Node]]) -> list[str]:
    """Nombres por defecto (antes de que el Diagramador ponga los suyos): entrada, capa dominante, resultado."""
    n = len(cols)
    names: list[str] = []
    for k, col in enumerate(cols):
        if n == 1:
            name = "Solución"
        elif k == 0:
            name = "Entrada"
        elif k == n - 1:
            name = "Resultado"
        else:
            dominant = max({c.categoria for c in col}, key=lambda cat: (sum(c.categoria == cat for c in col), cat == "IA"))
            name = CAT_ZONE.get(dominant, "Procesamiento")
        names.append(name if name not in names else f"{name} ({k + 1})")
    return names


def layout(componentes: list[dict], conexiones: list[dict], cats: dict[str, str], spec: dict | None = None):
    nodes = {c["id"]: _Node(c["id"], c.get("servicio", ""), c.get("nombre", c["id"]), cats.get(c["id"], "")) for c in componentes if c.get("id")}
    flujo = (spec or {}).get("flujo") or conexiones
    edges = [(e["de"], e["a"], e.get("etiqueta", "")) for e in flujo if e.get("de") in nodes and e.get("a") in nodes and e["de"] != e["a"]]
    if spec and not edges:  # el Diagramador inventó ids: se usan las conexiones del Arquitecto
        edges = [(e["de"], e["a"], e.get("etiqueta", "")) for e in conexiones if e.get("de") in nodes and e.get("a") in nodes and e["de"] != e["a"]]

    ins = {i: 0 for i in nodes}
    outs = {i: 0 for i in nodes}
    for a, b, _ in edges:
        outs[a] += 1
        ins[b] += 1
    # gobierno en medio del flujo (p. ej. enmascarar PII antes del modelo) va en el flujo; el resto, a la banda
    band = [n for n in nodes.values() if n.categoria == "Gobierno" and not (ins[n.id] and outs[n.id])]
    main_ids = [i for i in nodes if nodes[i] not in band]
    main_edges = [(a, b, t) for a, b, t in edges if a in main_ids and b in main_ids]

    cols: list[list[_Node]] = []
    titles: list[str] = []
    zonas = [z for z in (spec or {}).get("zonas") or [] if z.get("componentes")]
    if zonas:
        placed: set[str] = set()
        for z in zonas:
            col = [nodes[i] for i in z["componentes"] if i in main_ids and i not in placed]
            placed.update(n.id for n in col)
            if col:
                cols.append(col)
                titles.append(_clip(z.get("nombre", ""), 26))
        leftovers = [nodes[i] for i in main_ids if i not in placed]
        if leftovers and cols:
            cols[len(cols) // 2].extend(leftovers)
        elif leftovers:
            cols, titles = [leftovers], ["Solución"]
    if not cols:
        lv = _levels(main_ids, [(a, b) for a, b, _ in main_edges], {i: nodes[i].categoria for i in main_ids})
        for k in sorted(set(lv.values())):
            cols.append([nodes[i] for i in main_ids if lv[i] == k])
        titles = _zone_names(cols)

    rows = max((len(c) for c in cols), default=1)
    width = PAD * 2 + len(cols) * NODE_W + max(len(cols) - 1, 0) * COL_GAP
    body_h = rows * NODE_H + (rows - 1) * ROW_GAP
    for k, col in enumerate(cols):
        x = PAD + k * (NODE_W + COL_GAP)
        offset = (body_h - (len(col) * NODE_H + (len(col) - 1) * ROW_GAP)) / 2
        for r, n in enumerate(col):
            n.x, n.y = x, PAD + TITLE_H + offset + r * (NODE_H + ROW_GAP)

    height = PAD + TITLE_H + body_h + PAD
    band_y = height
    if band:
        bw = min(170, (width - PAD * 2 - (len(band) - 1) * 10) / len(band))
        for k, n in enumerate(band):
            n.w, n.h = bw, BAND_NODE_H
            n.x, n.y = PAD + k * (bw + 10), band_y + 26
        height = band_y + 26 + BAND_NODE_H + PAD
    width = max(width, PAD * 2 + len(band) * 130)
    return nodes, cols, titles, main_edges, band, band_y, width, height


def _bezier(p0, p1, p2, p3, t=0.5):
    u = 1 - t
    return tuple(u**3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t**3 * d for a, b, c, d in zip(p0, p1, p2, p3, strict=True))


def build_svg(componentes: list[dict], conexiones: list[dict], cats: dict[str, str], *, spec: dict | None = None,
              nuevos: set[str] | None = None, theme: str = "dark") -> str:
    th = THEMES[theme]
    nuevos = nuevos or set()
    if not componentes:
        return ""
    nodes, cols, titles, edges, band, band_y, width, height = layout(componentes, conexiones, cats, spec)
    font = "Satoshi, 'Segoe UI', Arial, sans-serif"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" font-family="{font}" role="img" aria-label="Arquitectura en Azure">',
        f'<defs><marker id="ah-{theme}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{th["edge"]}"/></marker></defs>',
    ]
    for k, col in enumerate(cols):
        x = col[0].x
        out.append(f'<text x="{x:.0f}" y="{PAD + 14}" font-size="12" font-weight="700" letter-spacing="1.2" fill="{th["title"]}">{escape(titles[k].upper())}</text>')

    # ida y vuelta entre el mismo par (agente ⇄ ERP): una sola flecha con doble punta
    index: dict[tuple[str, str], int] = {}
    drawn: list[list] = []  # [de, a, etiqueta, bidireccional]
    for a, b, label in edges:
        if (b, a) in index:
            drawn[index[(b, a)]][3] = True
        elif (a, b) not in index:
            index[(a, b)] = len(drawn)
            drawn.append([a, b, label, False])
    # puertos: cada flecha sale y entra por un punto distinto del borde, ordenado por la altura del otro
    # extremo, así no se amontonan las que salen del mismo nodo
    outs: dict[str, list[int]] = {}
    ins: dict[str, list[int]] = {}
    for i, (a, b, _, _) in enumerate(drawn):
        if nodes[b].x > nodes[a].x:
            outs.setdefault(a, []).append(i)
            ins.setdefault(b, []).append(i)

    def port_y(n: _Node, group: list[int], i: int, other: int) -> float:
        order = sorted(group, key=lambda j: nodes[drawn[j][other]].y)
        return n.y + n.h * (order.index(i) + 1) / (len(group) + 1)

    # flechas (debajo de los nodos), numeradas en el orden del flujo
    badges = []
    for step, (a, b, label, both) in enumerate(drawn, start=1):
        na, nb = nodes[a], nodes[b]
        if nb.x > na.x:
            p0 = (na.x + na.w + (3 if both else 0), port_y(na, outs[a], step - 1, 1))
            p3 = (nb.x - 2, port_y(nb, ins[b], step - 1, 0))
            dx = (p3[0] - p0[0]) * 0.45
            p1, p2 = (p0[0] + dx, p0[1]), (p3[0] - dx, p3[1])
        elif nb.x < na.x:  # flujo de regreso: por debajo
            p0, p3 = (na.x + na.w / 2, na.y + na.h), (nb.x + nb.w / 2, nb.y + nb.h + 2)
            p1, p2 = (p0[0], p0[1] + 40), (p3[0], p3[1] + 40)
        else:  # misma columna
            top, bot = (na, nb) if na.y < nb.y else (nb, na)
            p0, p3 = (top.x + top.w * 0.82, top.y + top.h), (bot.x + bot.w * 0.82, bot.y - 2)
            if top is nb:
                p0, p3 = p3, p0
            p1, p2 = p0, p3
        out.append(
            f'<path d="M{p0[0]:.1f},{p0[1]:.1f} C{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}" '
            f'fill="none" stroke="{th["edge"]}" stroke-width="1.8" marker-end="url(#ah-{theme})"'
            + (f' marker-start="url(#ah-{theme})"/>' if both else "/>")
        )
        # en flechas que saltan columnas, el número va cerca del destino para no pisar los de en medio
        span = max(round(abs(nb.x - na.x) / (NODE_W + COL_GAP)), 1)
        mx, my = _bezier(p0, p1, p2, p3, 0.5 if span == 1 else 1 - 0.5 / span)
        badges.append((step, mx, my, _clip(label, 22)))
    def node_svg(n: _Node, compact: bool = False) -> None:
        color = CAT_COLOR.get(n.categoria, "#64748b")
        is_new = n.id in nuevos
        stroke = th["new"] if is_new else th["stroke"]
        out.append(f'<rect x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" rx="9" fill="{th["node"]}" stroke="{stroke}" stroke-width="{2 if is_new else 1.2}"/>')
        out.append(f'<rect x="{n.x:.1f}" y="{n.y + 8:.1f}" width="4" height="{n.h - 16:.1f}" rx="2" fill="{color}"/>')
        servicio = escape(_clip(short_name(n.servicio), 24 if not compact else max(int(n.w / 7.4), 8)))
        if compact:
            out.append(f'<text x="{n.x + 13:.1f}" y="{n.y + n.h / 2 + 4.5:.1f}" font-size="12.5" font-weight="600" fill="{th["text"]}">{servicio}</text>')
        else:
            out.append(f'<text x="{n.x + 14:.1f}" y="{n.y + 25:.1f}" font-size="14" font-weight="700" fill="{th["text"]}">{servicio}</text>')
            # debajo: el rol del componente; si solo repite el servicio, la capa
            sub = n.nombre if short_name(n.servicio).lower() not in n.nombre.lower() else CAT_ZONE.get(n.categoria, "")
            out.append(f'<text x="{n.x + 14:.1f}" y="{n.y + 44:.1f}" font-size="11.5" fill="{th["sub"]}">{escape(_clip(sub, 30))}</text>')
        if is_new:
            out.append(f'<text x="{n.x + n.w - 8:.1f}" y="{n.y + 14:.1f}" font-size="9" font-weight="800" letter-spacing="0.8" text-anchor="end" fill="{th["new"]}">NUEVO</text>')

    for col in cols:
        for n in col:
            node_svg(n)
    if band:
        out.append(f'<rect x="{PAD / 2:.0f}" y="{band_y + 4:.0f}" width="{width - PAD:.0f}" height="{height - band_y - PAD / 2:.0f}" rx="10" fill="{th["band"]}"/>')
        out.append(f'<text x="{PAD:.0f}" y="{band_y + 19:.0f}" font-size="11" font-weight="700" letter-spacing="1.2" fill="{th["title"]}">SEGURIDAD Y GOBIERNO · TRANSVERSAL</text>')
        for n in band:
            node_svg(n, compact=True)
    # números y etiquetas del flujo encima de todo (una flecha larga puede pasar por detrás de un nodo)
    for step, mx, my, label in badges:
        if label:
            w = len(label) * 6.2 + 10
            out.append(f'<rect x="{mx - w / 2:.1f}" y="{my + 9:.1f}" width="{w:.1f}" height="15" rx="4" fill="{th["label_bg"]}" opacity="0.92"/>')
            out.append(f'<text x="{mx:.1f}" y="{my + 20:.1f}" font-size="10.5" text-anchor="middle" fill="{th["sub"]}">{escape(label)}</text>')
        out.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="9" fill="{th["badge"]}"/>')
        out.append(f'<text x="{mx:.1f}" y="{my + 3.8:.1f}" font-size="11" font-weight="700" text-anchor="middle" fill="{th["badge_text"]}">{step}</text>')
    out.append("</svg>")
    return "".join(out)


def build(componentes: list[dict], conexiones: list[dict], costo_items: list[dict], **kw) -> str:
    """Atajo: toma nombre del servicio y categoría del desglose de costos (catálogo)."""
    by_id = {i["id"]: i for i in costo_items}
    comps = []
    for c in componentes:
        item = by_id.get(c.get("id"))
        comps.append({**c, "servicio": item["nombre"] if item else c.get("servicio", "")})
    cats = {i["id"]: i["categoria"] for i in costo_items}
    return build_svg(comps, conexiones, cats, **kw)
