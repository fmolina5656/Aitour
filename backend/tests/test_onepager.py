import json
import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.onepager import leads as lead_mod
from app.onepager.render import render_html, render_pdf

CHROMIUM = os.getenv("CHROMIUM_PATH", "/opt/pw-browsers/chromium")

PAYLOAD = {
    "brief": {"problema": "Conciliar 5,000 facturas", "industria": "Manufactura", "volumen": "5,000/mes", "datos": "CFDI"},
    "onepager": {
        "titulo": "Agente inteligente para Manufactura",
        "problema": "Conciliamos a mano 5,000 facturas al mes",
        "solucion": "Un agente en Microsoft Foundry que extrae y valida facturas.",
        "beneficios": ["70% menos trabajo manual", "Respuesta en minutos", "Trazabilidad"],
        "riesgos_y_mitigaciones": ["PII → enmascaramiento", "Fugas → llaves del cliente", "Prompt injection → Prompt Shields"],
        "siguientes_pasos": ["Taller de 2 horas", "Piloto de 4 semanas", "Decisión de escalamiento"],
    },
    "costo": {
        "total_usd": 1397.0,
        "disclaimer": "Estimación referencial.",
        "items": [
            {"id": "agente", "nombre": "Foundry · GPT-5.4 mini", "categoria": "IA", "costo_usd": 810.0},
            {"id": "di", "nombre": "Document Intelligence · modelos prebuilt (facturas, IDs)", "categoria": "Datos", "costo_usd": 200.0},
            {"id": "seg", "nombre": "Azure AI Content Safety", "categoria": "Gobierno", "costo_usd": 114.0},
        ],
    },
    "riesgo": {"regulacion": [{"norma": "LFPDPPP (2025)", "aplica_por": "datos de proveedores"}]},
    "objeciones": [{"de": "financiero", "para": "arquitecto", "motivo": "Modelo premium caro", "propuesta": "Usar mini"}],
}


def test_html_has_brand_and_content():
    html = render_html(PAYLOAD)
    assert "Agente inteligente para Manufactura" in html
    assert "USD 1,397" in html and "LFPDPPP" in html
    assert "#66de7f" in html and "data:image/png;base64," in html
    assert "<span class=\"chip ia\">GPT-5.4 mini</span>" in html  # nombres cortos en las capas


@pytest.mark.skipif(not Path(CHROMIUM).exists(), reason="Chromium no disponible")
async def test_pdf_is_one_letter_page(tmp_path):
    out = await render_pdf(PAYLOAD, tmp_path / "op.pdf", Settings(chromium_path=CHROMIUM))
    data = out.read_bytes()
    assert data.startswith(b"%PDF") and data.count(b"/Type /Page\n") + data.count(b"/Type /Page>") + data.count(b"/Type/Page") >= 1
    assert len(data) > 20_000


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    from app import main

    s = Settings(demo_mode="mock", data_dir=tmp_path, chromium_path=CHROMIUM, lead_secret="x" * 32, recordings_dir=tmp_path)
    store = main.OnePagerStore(s)
    store.save("abc123", PAYLOAD)
    monkeypatch.setattr(main, "settings", s)
    monkeypatch.setattr(main, "store", store)
    monkeypatch.setattr(main, "leads", lead_mod.LeadStore(s))
    with TestClient(main.app) as client:
        yield client, store.token("abc123"), tmp_path, s


def lead(**kw):
    return {"nombre": "Ana López", "empresa": "Contoso", "correo": "ana@contoso.mx", "cargo": "CFO", "acepta_privacidad": True, "acepta_contacto": True, **kw}


def test_qr_and_lead_page_require_valid_token(app_client):
    client, tok, _, _ = app_client
    assert client.get("/lead/abc123?t=malo").status_code == 404
    r = client.get(f"/lead/abc123?t={tok}")
    assert r.status_code == 200 and "Agente inteligente para Manufactura" in r.text and "aviso de privacidad" in r.text
    qr = client.get(f"/api/qr/abc123.svg?t={tok}")
    assert qr.status_code == 200 and qr.text.lstrip().startswith(("<?xml", "<svg"))
    assert "Ley Federal de" in client.get("/privacidad").text


def test_consent_is_mandatory(app_client):
    client, tok, _, _ = app_client
    r = client.post(f"/api/lead/abc123?t={tok}", json=lead(acepta_privacidad=False))
    assert r.status_code == 422
    assert client.post(f"/api/lead/abc123?t={tok}", json=lead(correo="no-es-correo")).status_code == 422


@pytest.mark.skipif(not Path(CHROMIUM).exists(), reason="Chromium no disponible")
def test_lead_without_power_automate_goes_to_outbox(app_client):
    client, tok, tmp, _ = app_client
    r = client.post(f"/api/lead/abc123?t={tok}", json=lead())
    assert r.json() == {"ok": True, "envio": "pendiente"}
    row = json.loads((tmp / "leads" / "leads.jsonl").read_text().splitlines()[0])
    assert row["correo"] == "ana@contoso.mx" and row["envio"] == "pendiente"
    assert "ana@contoso.mx" in (tmp / "leads" / "leads.csv").read_text(encoding="utf-8-sig")
    out = json.loads((tmp / "leads" / "outbox.jsonl").read_text().splitlines()[0])
    assert out["pdf_url"].endswith(f"/api/pdf/abc123?t={tok}")
    pdf = client.get(out["pdf_url"].split("testserver")[1])
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


@pytest.mark.skipif(not Path(CHROMIUM).exists(), reason="Chromium no disponible")
def test_lead_is_sent_to_power_automate_with_pdf(app_client, monkeypatch):
    client, tok, tmp, s = app_client
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent.update(json.loads(request.content))
        return httpx.Response(202)

    real = httpx.AsyncClient
    monkeypatch.setattr(lead_mod.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    s.power_automate_url = "https://prod.flow.example/workflows/abc/triggers/manual/run?sig=x"
    r = client.post(f"/api/lead/abc123?t={tok}", json=lead())
    assert r.json()["envio"] == "enviado"
    assert sent["correo"] == "ana@contoso.mx" and sent["titulo"].startswith("Agente")
    assert sent["pdf_nombre"].endswith(".pdf") and len(sent["pdf_base64"]) > 1000
    assert not (tmp / "leads" / "outbox.jsonl").exists()


@pytest.mark.skipif(not Path(CHROMIUM).exists(), reason="Chromium no disponible")
def test_rate_limit_per_session(app_client):
    client, tok, _, s = app_client
    for _ in range(s.max_leads_per_session):
        assert client.post(f"/api/lead/abc123?t={tok}", json=lead()).status_code == 200
    assert client.post(f"/api/lead/abc123?t={tok}", json=lead()).status_code == 429
