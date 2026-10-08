"""Prueba de carga del stand: N sesiones seguidas contra el backend en marcha, sin degradación.

Uso:  cd backend && .venv/bin/python -m scripts.loadtest --url http://localhost:8000 --sessions 10
Criterios (requisitos del stand):
  - todas las sesiones terminan "ok" y el enjambre dura < 120 s,
  - las últimas 3 no son > 20 % más lentas que las primeras 3,
  - la memoria del backend no crece más de 150 MB.
"""

import argparse
import asyncio
import json
import statistics
import sys
import time

import httpx
import websockets

PROBLEMS = [
    ("Conciliamos a mano 5,000 facturas de proveedores al mes", "Manufactura", "5,000 facturas/mes", "CFDI en SharePoint"),
    ("El call center no da abasto con preguntas repetitivas", "Retail", "20,000 llamadas/mes", "Grabaciones y FAQs"),
    ("Revisar expedientes de crédito toma 3 días", "Servicios financieros", "1,200 solicitudes/mes", "PDF y CRM"),
    ("Los reportes de ventas se arman a mano cada lunes", "Consumo", "40 sucursales", "ERP y Excel"),
]


async def one_session(base: str, i: int) -> dict:
    ws_url = base.replace("http", "ws", 1) + "/ws/stage"
    async with websockets.connect(ws_url, max_size=2**22) as ws, httpx.AsyncClient(base_url=base, timeout=30) as http:
        p, ind, vol, dat = PROBLEMS[i % len(PROBLEMS)]
        t0 = time.monotonic()
        r = await http.post("/api/session/text", json={"problema": p, "industria": ind, "volumen": vol, "datos": dat})
        sid = r.json()["session_id"]
        status, swarm_s, events = "sin-fin", None, 0
        while time.monotonic() - t0 < 150:
            ev = json.loads(await asyncio.wait_for(ws.recv(), timeout=150))
            if ev.get("session_id") != sid:
                continue
            events += 1
            if ev["type"] == "session.ended":
                status, swarm_s = ev["data"]["status"], ev["data"]["swarm_s"]
                break
        health = (await http.get("/api/health")).json()
        return {"i": i + 1, "status": status, "swarm_s": swarm_s, "wall_s": round(time.monotonic() - t0, 1), "events": events, "rss_mb": health.get("rss_mb", 0)}


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--sessions", type=int, default=10)
    args = ap.parse_args()

    async with httpx.AsyncClient(base_url=args.url, timeout=10) as http:
        mode = (await http.get("/api/health")).json()["mode"]
    print(f"Backend en {args.url} · modo {mode} · {args.sessions} sesiones\n")
    rows = []
    for i in range(args.sessions):
        row = await one_session(args.url, i)
        rows.append(row)
        print(f"  #{row['i']:>2}  {row['status']:<8} enjambre {row['swarm_s']:>6}s  total {row['wall_s']:>6}s  eventos {row['events']:>3}  memoria {row['rss_mb']} MB")

    durations = [r["swarm_s"] or 999 for r in rows]
    first, last = statistics.mean(durations[:3]), statistics.mean(durations[-3:])
    mem_growth = rows[-1]["rss_mb"] - rows[0]["rss_mb"]
    checks = [
        ("todas terminan ok", all(r["status"] == "ok" for r in rows)),
        ("enjambre < 120 s en todas", max(durations) < 120),
        (f"sin degradación (últimas 3: {last:.1f}s vs primeras 3: {first:.1f}s)", last <= first * 1.2),
        (f"memoria estable (+{mem_growth:.0f} MB)", mem_growth < 150),
    ]
    print()
    for name, ok in checks:
        print(f"  {'✓' if ok else '✗'} {name}")
    passed = all(ok for _, ok in checks)
    print(f"\n{'PRUEBA DE CARGA OK' if passed else 'PRUEBA DE CARGA CON FALLAS'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
