"""One-pager de ejemplo (preflight y tests)."""

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
    "arquitectura": {
        "componentes": [
            {"id": "ingesta", "nombre": "Ingesta de facturas", "servicio": "storage.blob_hot"},
            {"id": "di", "nombre": "Extracción de campos", "servicio": "doc_intelligence.prebuilt"},
            {"id": "seg", "nombre": "Enmascarar PII", "servicio": "content_safety"},
            {"id": "agente", "nombre": "Agente de validación", "servicio": "foundry.gpt-5.4-mini"},
            {"id": "kv", "nombre": "Llaves del cliente", "servicio": "key_vault"},
        ],
        "conexiones": [
            {"de": "ingesta", "a": "di", "etiqueta": "facturas"},
            {"de": "di", "a": "seg", "etiqueta": "campos"},
            {"de": "seg", "a": "agente", "etiqueta": "datos limpios"},
        ],
    },
    "diagrama": {
        "titulo": "Del documento al resultado en Azure",
        "zonas": [{"nombre": "Ingesta", "componentes": ["ingesta", "di"]}, {"nombre": "Inteligencia", "componentes": ["seg", "agente"]}],
        "flujo": [
            {"de": "ingesta", "a": "di", "etiqueta": "facturas"},
            {"de": "di", "a": "seg", "etiqueta": "campos"},
            {"de": "seg", "a": "agente", "etiqueta": "datos limpios"},
        ],
        "pasos": ["Las facturas llegan a Blob Storage.", "Content Safety enmascara los datos personales.", "El agente en Foundry valida y concilia."],
    },
    "costo": {
        "total_usd": 1397.0,
        "disclaimer": "Estimación referencial.",
        "items": [
            {"id": "agente", "nombre": "Foundry · GPT-5.4 mini", "categoria": "IA", "costo_usd": 810.0},
            {"id": "di", "nombre": "Document Intelligence · modelos prebuilt (facturas, IDs)", "categoria": "Datos", "costo_usd": 200.0},
            {"id": "seg", "nombre": "Azure AI Content Safety", "categoria": "Gobierno", "costo_usd": 114.0},
            {"id": "ingesta", "nombre": "Azure Blob Storage · Hot", "categoria": "Datos", "costo_usd": 10.5},
            {"id": "kv", "nombre": "Azure Key Vault", "categoria": "Gobierno", "costo_usd": 0.4},
        ],
    },
    "riesgo": {"regulacion": [{"norma": "LFPDPPP (2025)", "aplica_por": "datos de proveedores"}]},
    "objeciones": [{"de": "financiero", "para": "arquitecto", "motivo": "Modelo premium caro", "propuesta": "Usar mini"}],
}
