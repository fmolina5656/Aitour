"""Diagrama de arquitectura en Azure → SVG (pantalla oscura y PDF claro).

El modelo nunca dibuja: el Arquitecto da componentes y conexiones, el Diagramador las agrupa en zonas, ordena
el flujo y lo explica, y aquí se calcula el layout. Si el Diagramador no llega (o devuelve ids inválidos), el
layout sale de las conexiones (niveles topológicos), así el diagrama está desde la primera propuesta.

Estilo de diagrama de referencia de Azure: zonas como carriles, nodos con ícono del servicio y color de capa,
flujo numerado (animado en pantalla) y los servicios de gobierno que no están en medio del flujo (Key Vault,
App Insights, Purview…) en una banda transversal abajo. Los íconos son trazos propios, sin archivos externos.
"""

from dataclasses import dataclass
from xml.sax.saxutils import escape

NODE_W, NODE_H = 244, 64
COL_GAP, ROW_GAP = 92, 34  # ROW_GAP con aire para las flechas entre nodos de la misma zona
PAD, LANE_PAD, TITLE_H = 16, 14, 34
BAND_NODE_H, BAND_TITLE_H = 40, 30
SKY = 34  # franja superior por donde pasan las flechas que saltan una zona entera
ICON = 38  # cuadro del ícono
CAT_RANK = {"Voz": 0, "Datos": 0, "IA": 1, "Cómputo": 2, "Integración": 2, "Gobierno": 1}

# Color por capa del catálogo (ícono, acento del nodo)
CAT_COLOR = {"IA": "#a78bfa", "Voz": "#f472b6", "Datos": "#60a5fa", "Cómputo": "#2dd4bf", "Integración": "#fbbf24", "Gobierno": "#4ade80"}
CAT_COLOR_LIGHT = {"IA": "#7c3aed", "Voz": "#db2777", "Datos": "#2563eb", "Cómputo": "#0d9488", "Integración": "#d97706", "Gobierno": "#16a34a"}
CAT_ZONE = {"Datos": "Datos", "IA": "IA · Foundry", "Voz": "Voz", "Cómputo": "Aplicación", "Integración": "Integración", "Gobierno": "Seguridad"}

THEMES = {
    "dark": {"lane": "#0d1829", "lane_stroke": "#1a2b45", "node": "#111f35", "stroke": "#26405f", "text": "#f3f6fa",
             "sub": "#8fa0b8", "title": "#7f93ad", "edge": "#2c4466", "flow": "#5b9bff", "badge": "#397ef6",
             "badge_text": "#ffffff", "pill": "#0a1424", "pill_stroke": "#26405f", "new": "#66de7f", "icon_bg": 0.16,
             "colors": CAT_COLOR, "animate": True},
    "light": {"lane": "#f5f8fc", "lane_stroke": "#e4e9f1", "node": "#ffffff", "stroke": "#d9e0ea", "text": "#11243e",
              "sub": "#5b6b80", "title": "#6b7a90", "edge": "#b4c0d0", "flow": "#2c68f5", "badge": "#2c68f5",
              "badge_text": "#ffffff", "pill": "#ffffff", "pill_stroke": "#d9e0ea", "new": "#16a34a", "icon_bg": 0.12,
              "colors": CAT_COLOR_LIGHT, "animate": False},
}

# Íconos de línea (viewBox 24×24, trazo redondeado), por servicio del catálogo
_I = {
    "sparkles": '<path d="M12 3l1.8 4.9L19 10l-5.2 2.1L12 17l-1.8-4.9L5 10l5.2-2.1z"/><path d="M19 15l.7 1.8L21.5 17.5l-1.8.7L19 20l-.7-1.8-1.8-.7 1.8-.7z"/>',
    "bot": '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M12 8V4.5"/><circle cx="12" cy="3.5" r="1"/><path d="M9 13.5v1.5M15 13.5v1.5"/>',
    "vector": '<circle cx="6" cy="6" r="2"/><circle cx="18" cy="7" r="2"/><circle cx="8" cy="18" r="2"/><circle cx="17" cy="17" r="2"/><path d="M8 6.5l8 .4M7.5 8l.4 8M10 17.8l5-.6M17.4 9l-.3 6"/>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/>',
    "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
    "db": '<ellipse cx="12" cy="5.5" rx="7" ry="2.8"/><path d="M5 5.5v13c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8v-13M5 12c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8"/>',
    "storage": '<rect x="3.5" y="5" width="17" height="5.5" rx="1.5"/><rect x="3.5" y="13.5" width="17" height="5.5" rx="1.5"/><path d="M7 7.75h.01M7 16.25h.01"/>',
    "layers": '<path d="M12 3l9 4.5-9 4.5-9-4.5z"/><path d="M3 12l9 4.5 9-4.5M3 16.5l9 4.5 9-4.5"/>',
    "cube": '<path d="M12 2.8l8 4.4v9.6l-8 4.4-8-4.4V7.2z"/><path d="M4 7.2l8 4.4 8-4.4M12 11.6V21"/>',
    "bolt": '<path d="M13 2.5L4.5 13.5H11l-1 8 8.5-11H12z"/>',
    "flow": '<rect x="3" y="4" width="7" height="6" rx="1.5"/><rect x="14" y="14" width="7" height="6" rx="1.5"/><path d="M6.5 10v3.5a3 3 0 0 0 3 3H14"/>',
    "gateway": '<rect x="3" y="6" width="18" height="12" rx="3"/><path d="M8 12h8M13 9l3 3-3 3"/>',
    "queue": '<rect x="3" y="7" width="4" height="10" rx="1"/><rect x="10" y="7" width="4" height="10" rx="1"/><rect x="17" y="7" width="4" height="10" rx="1"/>',
    "shield": '<path d="M12 21.5s7.5-3.6 7.5-9.5V5.5L12 2.8 4.5 5.5V12c0 5.9 7.5 9.5 7.5 9.5z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
    "pulse": '<path d="M3 12h4l2.5-6.5 5 13L17 12h4"/>',
    "key": '<circle cx="8" cy="15" r="4.5"/><path d="M11.2 11.8L20 3M16.5 6.5l2.5 2.5M14.5 8.5l1.8 1.8"/>',
    "eye": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    "app": '<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M3 8.5h18M7 6.25h.01M10 6.25h.01"/>',
}
_ICON_BY_KEY = [
    ("foundry.embeddings", "vector"), ("foundry.agent_service", "bot"), ("foundry.", "sparkles"), ("voice.", "mic"),
    ("speech.", "mic"), ("doc_intelligence.", "doc"), ("ai_search.", "search"), ("cosmosdb.", "db"), ("sql.", "db"),
    ("storage.", "storage"), ("fabric.", "layers"), ("container_apps", "cube"), ("functions.", "bolt"),
    ("app_service.", "app"), ("logic_apps.", "flow"), ("apim.", "gateway"), ("service_bus.", "queue"),
    ("content_safety", "shield"), ("app_insights", "pulse"), ("key_vault", "key"), ("purview", "eye"),
]
_ICON_BY_CAT = {"IA": "sparkles", "Voz": "mic", "Datos": "db", "Cómputo": "cube", "Integración": "flow", "Gobierno": "shield"}


def _icon(clave: str, categoria: str) -> str:
    for prefix, name in _ICON_BY_KEY:
        if clave.startswith(prefix):
            return _I[name]
    return _I[_ICON_BY_CAT.get(categoria, "cube")]


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
    clave: str = ""  # clave del catálogo ("ai_search.basic"): elige el ícono
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
    nodes = {
        c["id"]: _Node(c["id"], c.get("servicio", ""), c.get("nombre", c["id"]), cats.get(c["id"], ""), c.get("clave", ""))
        for c in componentes if c.get("id")
    }
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
                titles.append(_clip(z.get("nombre", ""), 24))
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

    col_of = {n.id: k for k, col in enumerate(cols) for n in col}
    skips = any(abs(col_of[a] - col_of[b]) >= 2 for a, b, _ in main_edges)
    rows = max((len(c) for c in cols), default=1)
    body_h = rows * NODE_H + (rows - 1) * ROW_GAP
    lane_top = PAD + (SKY if skips else 0)
    nodes_top = lane_top + TITLE_H
    for k, col in enumerate(cols):
        x = PAD + LANE_PAD + k * (NODE_W + COL_GAP)
        offset = (body_h - (len(col) * NODE_H + (len(col) - 1) * ROW_GAP)) / 2
        for r, n in enumerate(col):
            n.x, n.y = x, nodes_top + offset + r * (NODE_H + ROW_GAP)
    lane_h = TITLE_H + body_h + LANE_PAD
    width = PAD * 2 + LANE_PAD * 2 + len(cols) * NODE_W + max(len(cols) - 1, 0) * COL_GAP

    height = lane_top + lane_h + PAD
    band_y = height
    if band:
        inner = width - PAD * 2 - LANE_PAD * 2
        bw = min(200, (inner - (len(band) - 1) * 12) / len(band))
        for k, n in enumerate(band):
            n.w, n.h = bw, BAND_NODE_H
            n.x, n.y = PAD + LANE_PAD + k * (bw + 12), band_y + BAND_TITLE_H
        height = band_y + BAND_TITLE_H + BAND_NODE_H + LANE_PAD + PAD
    width = max(width, PAD * 2 + LANE_PAD * 2 + len(band) * 150)
    return nodes, cols, titles, main_edges, band, band_y, lane_top, lane_h, width, height


def _bezier(p0, p1, p2, p3, t=0.5):
    u = 1 - t
    return tuple(u**3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t**3 * d for a, b, c, d in zip(p0, p1, p2, p3, strict=True))


def build_svg(componentes: list[dict], conexiones: list[dict], cats: dict[str, str], *, spec: dict | None = None,
              nuevos: set[str] | None = None, theme: str = "dark") -> str:
    th = THEMES[theme]
    colors = th["colors"]
    nuevos = nuevos or set()
    if not componentes:
        return ""
    nodes, cols, titles, edges, band, band_y, lane_top, lane_h, width, height = layout(componentes, conexiones, cats, spec)
    font = "Satoshi, 'Segoe UI', Arial, sans-serif"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" font-family="{font}" role="img" aria-label="Arquitectura en Azure">',
        f'<defs><marker id="ah-{theme}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
        f'<path d="M1,1 L9,5 L1,9 z" fill="{th["flow"]}"/></marker></defs>',
    ]
    if th["animate"]:
        # flujo en movimiento: puntitos que viajan en el sentido del proceso (solo pantalla; el PDF es estático)
        out.append("<style>.rm-flow{stroke-dasharray:2 10;animation:rm-flow 1.1s linear infinite}"
                   "@keyframes rm-flow{to{stroke-dashoffset:-24}}.rm-new{animation:rm-new 1.6s ease-in-out infinite}"
                   "@keyframes rm-new{50%{stroke-opacity:.35}}</style>")

    # carriles (zonas) con su título adentro
    for k, col in enumerate(cols):
        x = col[0].x - LANE_PAD
        out.append(f'<rect x="{x:.1f}" y="{lane_top:.1f}" width="{NODE_W + LANE_PAD * 2:.1f}" height="{lane_h:.1f}" rx="16" '
                   f'fill="{th["lane"]}" stroke="{th["lane_stroke"]}"/>')
        out.append(f'<text x="{x + LANE_PAD:.1f}" y="{lane_top + 22:.1f}" font-size="11.5" font-weight="700" letter-spacing="1.6" '
                   f'fill="{th["title"]}">{escape(titles[k].upper())}</text>')
    if band:
        out.append(f'<rect x="{PAD:.0f}" y="{band_y:.0f}" width="{width - PAD * 2:.0f}" height="{height - band_y - PAD:.0f}" rx="16" '
                   f'fill="{th["lane"]}" stroke="{th["lane_stroke"]}" stroke-dasharray="5 5"/>')
        out.append(f'<text x="{PAD + LANE_PAD:.0f}" y="{band_y + 20:.0f}" font-size="11" font-weight="700" letter-spacing="1.6" '
                   f'fill="{th["title"]}">SEGURIDAD Y GOBIERNO · TRANSVERSAL</text>')

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

    badges = []
    for step, (a, b, label, both) in enumerate(drawn, start=1):
        na, nb = nodes[a], nodes[b]
        span = max(round(abs(nb.x - na.x) / (NODE_W + COL_GAP)), 1)
        skip = nb.x > na.x and span >= 2
        if skip:  # salta zonas: sube por el hueco, cruza por arriba de los carriles y baja al destino
            p0 = (na.x + na.w + (4 if both else 1), port_y(na, outs[a], step - 1, 1))
            p3 = (nb.x - 3, port_y(nb, ins[b], step - 1, 0))
            p1, p2 = (p0[0] + COL_GAP * 0.9, PAD - 30), (p3[0] - COL_GAP * 0.9, PAD - 30)
        elif nb.x > na.x:
            p0 = (na.x + na.w + (4 if both else 1), port_y(na, outs[a], step - 1, 1))
            p3 = (nb.x - 3, port_y(nb, ins[b], step - 1, 0))
            dx = (p3[0] - p0[0]) * 0.5
            p1, p2 = (p0[0] + dx, p0[1]), (p3[0] - dx, p3[1])
        elif nb.x < na.x:  # flujo de regreso: por debajo
            p0, p3 = (na.x + na.w / 2, na.y + na.h + 1), (nb.x + nb.w / 2, nb.y + nb.h + 3)
            p1, p2 = (p0[0], p0[1] + 42), (p3[0], p3[1] + 42)
        else:  # misma columna: flecha vertical corta, del lado derecho
            top, bot = (na, nb) if na.y < nb.y else (nb, na)
            p0, p3 = (top.x + top.w - 34, top.y + top.h + 1), (bot.x + bot.w - 34, bot.y - 3)
            if top is nb:
                p0, p3 = p3, p0
            p1, p2 = p0, p3
        d = f"M{p0[0]:.1f},{p0[1]:.1f} C{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}"
        ends = f' marker-end="url(#ah-{theme})"' + (f' marker-start="url(#ah-{theme})"' if both else "")
        out.append(f'<path d="{d}" fill="none" stroke="{th["edge"]}" stroke-width="2.4" stroke-linecap="round"/>')
        out.append(f'<path d="{d}" fill="none" stroke="{th["flow"]}" stroke-width="2.4" stroke-linecap="round"'
                   f'{" class=\"rm-flow\"" if th["animate"] else " stroke-opacity=\"0.55\""}{ends}/>')
        mx, my = _bezier(p0, p1, p2, p3, 0.5)
        # etiqueta: al costado en flechas verticales, a la derecha en los puentes, debajo en el resto
        badges.append((step, mx, my, _clip(label, 22), "left" if nb.x == na.x else "right" if skip else "below"))

    def node_svg(n: _Node, compact: bool = False) -> None:
        color = colors.get(n.categoria, "#94a3b8")
        is_new = n.id in nuevos
        out.append(f'<rect x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" rx="12" fill="{th["node"]}" '
                   f'stroke="{th["stroke"]}" stroke-width="1.2"/>')
        if is_new:
            out.append(f'<rect x="{n.x - 2:.1f}" y="{n.y - 2:.1f}" width="{n.w + 4:.1f}" height="{n.h + 4:.1f}" rx="14" fill="none" '
                       f'stroke="{th["new"]}" stroke-width="2"{" class=\"rm-new\"" if th["animate"] else ""}/>')
        size = 26 if compact else ICON
        ix, iy = n.x + (7 if compact else 12), n.y + (n.h - size) / 2
        out.append(f'<rect x="{ix:.1f}" y="{iy:.1f}" width="{size}" height="{size}" rx="{8 if not compact else 6}" '
                   f'fill="{color}" fill-opacity="{th["icon_bg"]}"/>')
        scale = (size - (12 if not compact else 8)) / 24
        out.append(f'<g transform="translate({ix + (size - 24 * scale) / 2:.1f},{iy + (size - 24 * scale) / 2:.1f}) scale({scale:.3f})" '
                   f'fill="none" stroke="{color}" stroke-width="{1.9 / scale * 0.85:.2f}" stroke-linecap="round" stroke-linejoin="round">'
                   f'{_icon(n.clave, n.categoria)}</g>')
        tx = ix + size + (8 if compact else 11)
        avail = n.x + n.w - tx - 8
        servicio = short_name(n.servicio)
        if compact:
            out.append(f'<text x="{tx:.1f}" y="{n.y + n.h / 2 + 4.5:.1f}" font-size="12.5" font-weight="600" fill="{th["text"]}">'
                       f'{escape(_clip(servicio, max(int(avail / 7), 6)))}</text>')
        else:
            # arriba el servicio de Azure, abajo el rol del componente (o la capa, si solo repetiría el servicio)
            sub = n.nombre if servicio.lower() not in n.nombre.lower() else CAT_ZONE.get(n.categoria, "")
            out.append(f'<text x="{tx:.1f}" y="{n.y + 28:.1f}" font-size="14.5" font-weight="700" fill="{th["text"]}">'
                       f'{escape(_clip(servicio, max(int(avail / 8.2), 8)))}</text>')
            out.append(f'<text x="{tx:.1f}" y="{n.y + 46:.1f}" font-size="11.5" fill="{th["sub"]}">{escape(_clip(sub, max(int(avail / 6.3), 8)))}</text>')
        if is_new:
            w = 44
            out.append(f'<rect x="{n.x + n.w - w - 8:.1f}" y="{n.y - 9:.1f}" width="{w}" height="17" rx="8.5" fill="{th["new"]}"/>')
            out.append(f'<text x="{n.x + n.w - w / 2 - 8:.1f}" y="{n.y + 3:.1f}" font-size="9" font-weight="800" letter-spacing="0.8" '
                       f'text-anchor="middle" fill="{th["node"]}">NUEVO</text>')

    for col in cols:
        for n in col:
            node_svg(n)
    for n in band:
        node_svg(n, compact=True)

    # números y etiquetas del flujo encima de todo (una flecha larga puede pasar por detrás de un nodo)
    for step, mx, my, label, where in badges:
        if label:
            w = len(label) * 6.1 + 18
            lx, ly = {"left": (mx - 14 - w / 2, my - 9.5), "right": (mx + 14 + w / 2, my - 9.5), "below": (mx, my + 12)}[where]
            out.append(f'<rect x="{lx - w / 2:.1f}" y="{ly:.1f}" width="{w:.1f}" height="19" rx="9.5" fill="{th["pill"]}" '
                       f'stroke="{th["pill_stroke"]}"/>')
            out.append(f'<text x="{lx:.1f}" y="{ly + 13:.1f}" font-size="10.5" font-weight="500" text-anchor="middle" fill="{th["sub"]}">{escape(label)}</text>')
        out.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="10.5" fill="{th["badge"]}" stroke="{th["lane"]}" stroke-width="3"/>')
        out.append(f'<text x="{mx:.1f}" y="{my + 4:.1f}" font-size="11.5" font-weight="800" text-anchor="middle" fill="{th["badge_text"]}">{step}</text>')
    out.append("</svg>")
    return "".join(out)


def build(componentes: list[dict], conexiones: list[dict], costo_items: list[dict], **kw) -> str:
    """Atajo: toma nombre del servicio y categoría del desglose de costos (catálogo)."""
    by_id = {i["id"]: i for i in costo_items}
    comps = []
    for c in componentes:
        item = by_id.get(c.get("id"))
        clave = item.get("servicio", "") if item else c.get("servicio", "")
        comps.append({**c, "clave": clave, "servicio": item["nombre"] if item else c.get("servicio", "")})
    cats = {i["id"]: i["categoria"] for i in costo_items}
    return build_svg(comps, conexiones, cats, **kw)
