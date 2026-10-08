"""Cliente de chat simulado: recorre el MISMO camino de orquestación sin consumir Azure.

Las respuestas reaccionan al contexto (alertas del calculador, objeciones previas), así el modo mock
también ejercita la lógica real del director.
"""

import asyncio
import json
import random
import re
from collections.abc import Sequence
from typing import Any

from agent_framework import BaseChatClient, ChatResponseUpdate, Content, Message, ResponseStream, UsageDetails


def _brief_field(text: str, name: str, default: str) -> str:
    m = re.search(rf"- {name}: (.+)", text)
    return m.group(1).strip() if m else default


def _arquitecto(ctx: str, n_prev: int) -> dict:
    industria = _brief_field(ctx, "Industria", "su industria")
    riesgo_objeto = "sin enmascaramiento de PII" in ctx
    fin_objeto = "Cambiar el modelo" in ctx
    modelo = "foundry.gpt-5.4-mini" if fin_objeto else "foundry.gpt-5.4"
    comps = [
        {"id": "ingesta", "nombre": "Ingesta de documentos", "servicio": "storage.blob_hot", "cantidad": 0.5, "supuesto": "0.5 TB de documentos históricos"},
        {"id": "extraccion", "nombre": "Document Intelligence", "servicio": "doc_intelligence.prebuilt", "cantidad": 20, "supuesto": "20,000 páginas al mes"},
        {"id": "agente", "nombre": "Agente en Foundry", "servicio": modelo, "cantidad": 900, "supuesto": "≈900M tokens/mes para clasificar y validar"},
        {"id": "busqueda", "nombre": "AI Search (RAG)", "servicio": "ai_search.basic", "cantidad": 1, "supuesto": "1 unidad, índice < 15 GB"},
        {"id": "app", "nombre": "API en Container Apps", "servicio": "container_apps", "cantidad": 2, "supuesto": "2 réplicas para alta disponibilidad"},
        {"id": "monitoreo", "nombre": "App Insights", "servicio": "app_insights", "cantidad": 20, "supuesto": "20 GB de trazas al mes"},
    ]
    conns = [
        {"de": "ingesta", "a": "extraccion", "etiqueta": "documentos"},
        {"de": "extraccion", "a": "agente", "etiqueta": "campos"},
        {"de": "busqueda", "a": "agente", "etiqueta": "contexto"},
        {"de": "agente", "a": "app", "etiqueta": "resultado"},
        {"de": "app", "a": "monitoreo", "etiqueta": "trazas"},
    ]
    cambios = None
    burbuja = f"Propongo un agente en Foundry que lee, valida y clasifica la información de {industria} automáticamente."
    if fin_objeto:
        cambios = "Cambié GPT-5.4 por GPT-5.4 mini para clasificación; el modelo grande queda solo para excepciones."
        burbuja = "Tienes razón: paso a GPT-5.4 mini para el volumen y reservo el modelo grande para excepciones."
    if riesgo_objeto:
        comps += [
            {"id": "seguridad", "nombre": "Content Safety + PII", "servicio": "content_safety", "cantidad": 300, "supuesto": "300K registros revisados al mes"},
            {"id": "llaves", "nombre": "Key Vault (CMK)", "servicio": "key_vault", "cantidad": 50, "supuesto": "500K operaciones al mes"},
        ]
        conns += [{"de": "extraccion", "a": "seguridad", "etiqueta": "enmascarar PII"}, {"de": "seguridad", "a": "agente", "etiqueta": "datos limpios"}]
        cambios = "Agregué detección/enmascaramiento de PII y llaves administradas por el cliente."
        burbuja = "Agrego enmascaramiento de PII antes del modelo y cifrado con llaves del cliente. Listo para LFPDPPP."
    return {"burbuja": burbuja, "resumen": "Arquitectura de extracción + agente de validación con RAG.", "componentes": comps, "conexiones": conns, "cambios": cambios}


def _financiero(ctx: str, n_prev: int) -> dict:
    total = re.findall(r"TOTAL MENSUAL: USD ([\d,\.]+)", ctx)
    total_txt = total[-1] if total else "N/D"
    last_calc = ctx[ctx.rfind("[CALCULADOR"):] if "[CALCULADOR" in ctx else ""
    if "ALERTA:" in last_calc:
        return {
            "burbuja": f"Objeción: USD {total_txt}/mes y casi todo es el modelo premium. Para clasificar no hace falta.",
            "comentario": "El modelo grande domina el costo.",
            "supuestos": ["Precios de lista", "Volumen constante"],
            "objecion": {"para": "arquitecto", "motivo": "El modelo premium concentra la mayor parte del costo.", "propuesta": "Cambiar el modelo de clasificación a GPT-5.4 mini y usar el grande solo en excepciones."},
        }
    return {
        "burbuja": f"Ahora sí: USD {total_txt} al mes. Aprobado desde finanzas.",
        "comentario": "Costo razonable para el volumen.",
        "supuestos": ["Precios de lista", "Volumen constante", "Sin descuentos EA"],
        "objecion": None,
    }


def _riesgo(ctx: str, n_prev: int) -> dict:
    tiene_pii = "content_safety" in ctx[ctx.rfind('"componentes"'):] if '"componentes"' in ctx else False
    obj = None if tiene_pii or "[SISTEMA] Ya no hay tiempo" in ctx else {
        "para": "arquitecto",
        "motivo": "Se procesan datos personales (RFC, nombres) sin enmascaramiento de PII ni llaves del cliente.",
        "propuesta": "Agregar detección de PII antes del modelo y cifrado con llaves administradas (Key Vault).",
    }
    return {
        "burbuja": "Ojo: hay datos personales (RFC, nombres). Aplica la LFPDPPP; pido enmascarar PII antes del modelo." if obj else "Datos personales cubiertos: PII enmascarada, cifrado con llaves del cliente. Aprobado.",
        "datos_sensibles": ["RFC y razón social", "Nombres y correos de contactos", "Datos bancarios de proveedores"],
        "regulacion": [
            {"norma": "LFPDPPP (2025)", "aplica_por": "Tratamiento de datos personales de proveedores y contactos"},
            {"norma": "Código Fiscal de la Federación, art. 30", "aplica_por": "Conservación de CFDI por 5 años"},
        ],
        "mitigaciones": ["Enmascarar PII antes de enviarla al modelo", "Cifrado con llaves del cliente (Key Vault)", "Guardrails de Foundry con Prompt Shields"],
        "objecion": obj,
    }


def _diagramador(ctx: str, n_prev: int) -> dict:
    m = re.search(r"componentes: (\[.*\])", ctx)
    ids = {c["id"] for c in json.loads(m.group(1))} if m else set()
    entrada = [i for i in ("ingesta", "extraccion") if i in ids]
    inteligencia = [i for i in ("seguridad", "busqueda", "agente") if i in ids]
    entrega = [i for i in ("app",) if i in ids]
    flujo = [
        ("ingesta", "extraccion", "facturas"), ("extraccion", "seguridad", "campos"), ("seguridad", "agente", "datos limpios"),
        ("busqueda", "agente", "contexto"), ("agente", "app", "resultado"),
    ]
    if "seguridad" not in ids:
        flujo = [("ingesta", "extraccion", "facturas"), ("extraccion", "agente", "campos"), ("busqueda", "agente", "contexto"), ("agente", "app", "resultado")]
    return {
        "burbuja": "Así queda en Azure: de la factura al resultado en cuatro pasos. Lo dejo en el one-pager.",
        "titulo": "Del documento al resultado en Azure",
        "zonas": [{"nombre": "Ingesta", "componentes": entrada}, {"nombre": "Inteligencia", "componentes": inteligencia}, {"nombre": "Entrega", "componentes": entrega}],
        "flujo": [{"de": a, "a": b, "etiqueta": t} for a, b, t in flujo if a in ids and b in ids],
        "pasos": [
            "Los documentos llegan a Blob Storage y Document Intelligence extrae los campos.",
            "Content Safety enmascara los datos personales antes de que los vea el modelo.",
            "El agente en Foundry valida y clasifica, con contexto de AI Search.",
            "La API en Container Apps entrega el resultado a los sistemas del cliente.",
        ],
    }


def _redactor(ctx: str, n_prev: int) -> dict:
    industria = _brief_field(ctx, "Industria", "la empresa")
    problema = _brief_field(ctx, "Problema", "un proceso manual")
    return {
        "burbuja": "Listo: tu one-pager ejecutivo está generado. Escanea el QR para recibirlo.",
        "titulo": f"Agente inteligente para {industria}",
        "problema": problema,
        "solucion": "Un agente en Microsoft Foundry que extrae, valida y clasifica la información automáticamente, con supervisión humana en excepciones.",
        "beneficios": ["Reducción de 70% del trabajo manual", "Respuesta en minutos en lugar de días", "Trazabilidad completa de cada decisión"],
        "riesgos_y_mitigaciones": ["Datos personales → enmascaramiento de PII", "Fugas de información → llaves del cliente", "Prompt injection → Prompt Shields"],
        "siguientes_pasos": ["Taller de 2 horas con Readymind", "Piloto de 4 semanas con datos reales", "Decisión de escalamiento"],
    }


SCRIPTS = {"arquitecto": _arquitecto, "financiero": _financiero, "riesgo": _riesgo, "diagramador": _diagramador, "redactor": _redactor}
FAKE_LATENCY_S = {"arquitecto": 4.0, "financiero": 2.5, "riesgo": 3.0, "diagramador": 2.5, "redactor": 3.5}


class MockChatClient(BaseChatClient):
    OTEL_PROVIDER_NAME = "mock"

    def __init__(self, agent: str, model: str, speed: float = 1.0) -> None:
        super().__init__()
        self.agent = agent
        self.model = model
        self.speed = speed
        self.calls = 0

    def _inner_get_response(self, *, messages: Sequence[Message], stream: bool, options: dict[str, Any], **kwargs: Any):
        self.calls += 1
        ctx = "\n".join(m.text or "" for m in messages)
        payload = json.dumps(SCRIPTS[self.agent](ctx, self.calls - 1), ensure_ascii=False)
        in_tokens = max(len(ctx) // 4, 50)
        out_tokens = max(len(payload) // 4, 20)
        latency = FAKE_LATENCY_S[self.agent] * self.speed * random.uniform(0.8, 1.2)

        async def gen():
            await asyncio.sleep(latency * 0.35)  # "tiempo de razonamiento"
            chunks = [payload[i : i + 12] for i in range(0, len(payload), 12)]
            for chunk in chunks:
                await asyncio.sleep(latency * 0.65 / len(chunks))
                yield ChatResponseUpdate(role="assistant", contents=[Content.from_text(chunk)], model=self.model)
            usage = UsageDetails(input_token_count=in_tokens, output_token_count=out_tokens)
            yield ChatResponseUpdate(role="assistant", contents=[Content.from_usage(usage)], model=self.model)

        if stream:
            return ResponseStream(gen(), finalizer=lambda updates: self._finalize_response_updates(updates))

        async def full():
            return self._finalize_response_updates([u async for u in gen()])

        return full()
