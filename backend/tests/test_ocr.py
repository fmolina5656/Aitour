import base64
from datetime import date

from fastapi.testclient import TestClient

from app import ocr
from app.config import Settings
from app.ocr import Campo, Lectura

JPEG = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 64).decode()


def lectura(**kw) -> Lectura:
    base = dict(tipo="otro", confianza=0.9, resumen="x", campos=[], rfc=None, curp=None, subtotal=None, iva=None,
                total=None, fecha_emision=None, vigencia=None, es_muestra=True)
    return Lectura(**{**base, **kw})


def test_curp_rfc_validation():
    curp17 = "GORA850312MDFMZN0"
    assert ocr.validar_curp(curp17 + str(ocr.curp_check_digit(curp17)))
    assert not ocr.validar_curp(curp17 + str((ocr.curp_check_digit(curp17) + 1) % 10))
    assert ocr.validar_rfc("SEJ190312AB4") and ocr.validar_rfc("GORA850312H31")
    assert not ocr.validar_rfc("SEJ191312AB4")  # mes 13


def test_validaciones_factura_y_vigencia():
    hoy = date(2026, 10, 19)
    ok = ocr.validaciones(lectura(tipo="factura_cfdi", subtotal=10000, iva=1600, total=11600), hoy)
    assert ok == [{"ok": True, "texto": "Los importes cuadran: subtotal + IVA = total"}]
    mal = ocr.validaciones(lectura(tipo="factura_cfdi", subtotal=10000, iva=1600, total=12600), hoy)
    assert not mal[0]["ok"] and "no cuadran" in mal[0]["texto"]
    assert not ocr.validaciones(lectura(vigencia="2025-01-31"), hoy)[0]["ok"]
    assert not ocr.validaciones(lectura(tipo="comprobante_domicilio", fecha_emision="2026-05-01"), hoy)[0]["ok"]


def test_datos_sensibles_salen_enmascarados():
    lec = lectura(campos=[Campo(etiqueta="Nombre", valor="Ana Ruiz Gómez", sensible=True),
                          Campo(etiqueta="CLABE", valor="012180001234567897", sensible=True),
                          Campo(etiqueta="Banco", valor="Banco Ejemplo", sensible=False)])
    out = ocr.resultado_publico(lec, 100, "m")
    vals = [c["valor"] for c in out["campos"]]
    assert vals == ["A••• R••• G•••", "0121••••••••", "Banco Ejemplo"]
    assert "Ruiz" not in str(out) and "1234567897" not in str(out)


def test_api_ocr_mock_y_errores(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "settings", Settings(demo_mode="mock", mock_speed=0.01))
    with TestClient(main.app) as client:
        r = client.post("/api/ocr", json={"image": JPEG})
        assert r.status_code == 200
        body = r.json()
        assert body["tipo"] == "factura_cfdi" and body["validaciones"][-1]["ok"]
        assert all("Ruiz" not in c["valor"] for c in body["campos"])
        assert client.post("/api/ocr", json={"image": "data:application/pdf;base64,AAAA"}).status_code == 422
        assert client.post("/api/ocr", json={"image": "data:image/png;base64,@@@"}).status_code == 422
