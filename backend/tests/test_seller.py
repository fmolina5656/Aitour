import json

from fastapi.testclient import TestClient

from app import seller
from app.config import Settings


def test_merge_sin_duplicados():
    qr = [{"fecha": "2026-10-22T10:00:00", "nombre": "Ana Ruiz", "empresa": "ACME", "correo": "Ana@acme.com", "industria": "Retail"}]
    fichas = [
        {"fecha": "2026-10-22T10:05:00", "nombre": "Ana R.", "correo": "ana@acme.com", "interes": "taller", "nota": "quiere piloto"},
        {"fecha": "2026-10-22T11:00:00", "nombre": "Luis Pérez", "empresa": "Banco X", "interes": "info"},
        {"fecha": "2026-10-22T11:30:00", "nombre": "luis  pérez", "empresa": "banco x", "nota": "segunda charla"},
    ]
    rows = seller.merge(qr, fichas)
    assert len(rows) == 2
    ana = next(r for r in rows if r["nombre"] == "Ana Ruiz")
    assert ana["origen"] == "QR + vendedor" and ana["interes"] == "taller" and ana["industria"] == "Retail"


def test_api_vendedor(tmp_path, monkeypatch):
    from app import main

    s = Settings(demo_mode="mock", data_dir=tmp_path, recordings_dir=tmp_path, seller_pin="4321")
    monkeypatch.setattr(main, "settings", s)
    (tmp_path / "leads").mkdir()
    (tmp_path / "leads" / "leads.jsonl").write_text(json.dumps({"fecha": "2099-01-01T09:00:00", "session_id": "abc", "nombre": "Ana Ruiz",
                                                                "empresa": "ACME", "correo": "ana@acme.com", "titulo": "Agente X"}) + "\n")
    with TestClient(main.app) as c:
        assert c.post("/api/vendedor/login", headers={"X-Seller-Pin": "0000"}).status_code == 401
        h = {"X-Seller-Pin": "4321"}
        assert c.post("/api/vendedor/login", headers=h).json() == {"ok": True}
        assert c.post("/api/vendedor/visita", headers=h, json={"nombre": "Luis Pérez", "correo": "malo"}).status_code == 422
        r = c.post("/api/vendedor/visita", headers=h, json={"nombre": "Ana", "correo": "ANA@acme.com", "interes": "piloto", "nota": "llamar"})
        assert r.status_code == 200
        todos = c.get("/api/vendedor/leads?hoy=false", headers=h).json()
        assert todos["total"] == 1 and todos["leads"][0]["interes"] == "piloto" and todos["leads"][0]["origen"] == "QR + vendedor"
        assert c.get("/api/vendedor/leads.csv?pin=4321").text.startswith("﻿fecha,origen,nombre")
        assert c.get("/api/vendedor/leads").status_code == 401


def test_sin_pin_no_expone_nada(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "settings", Settings(demo_mode="mock", data_dir=tmp_path, recordings_dir=tmp_path, seller_pin=""))
    with TestClient(main.app) as c:
        assert c.get("/api/vendedor/leads", headers={"X-Seller-Pin": ""}).status_code == 503
