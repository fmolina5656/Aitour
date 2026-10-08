# Readymind · Microsoft AI Tour México — "Cuéntame tu problema y en 3 minutos te armo la solución"

Demo de stand: un visitante cuenta un problema de negocio y un **equipo de agentes de IA** (Microsoft Agent Framework +
Microsoft Foundry) diseña en vivo la solución, la cuestiona entre sí (costo, riesgo regulatorio) y entrega un one-pager
ejecutivo. Pantalla pensada para 1920×1080, vista de lejos.

> **Estado: Fase 1 lista** (orquestación multiagente por texto + UI del grafo, con modo mock y replay básicos).
> Ver [Roadmap](#roadmap).

## Arquitectura

```
Pantalla (React + Vite) ──WS /ws/stage──► FastAPI (Python 3.12, Azure Container Apps)
                                            ├─ SessionManager (estado, timeouts, reset)
                                            ├─ EventBus ─► Recorder (JSONL) ─► Replay
                                            ├─ Enjambre MAF: GroupChatBuilder + selection_func determinista
                                            │    Arquitecto · Financiero · Riesgo · Redactor  (FoundryChatClient)
                                            ├─ Calculador de costos (pricing/catalogo.json) + generador Mermaid
                                            └─ [Fase 3] Recepcionista: Microsoft Foundry voice agent (preview)
```

Decisiones clave:

- **Todo lo que se ve es un evento del bus** (`backend/app/events.py`). El grabador persiste esos eventos, por eso el
  **replay usa exactamente la misma UI**.
- **El LLM no inventa números ni dibuja**: el Arquitecto devuelve componentes estructurados; Python calcula el costo con
  `backend/pricing/catalogo.json` y genera el Mermaid. Diagrama y costo siempre son consistentes.
- **El debate es real**: el director (`backend/app/swarm/director.py`) inyecta al Financiero la tabla del calculador; si un
  modelo premium concentra ≥ 40 % del costo (o se pasa el presupuesto) el Financiero objeta y el Arquitecto ajusta.
  Riesgo objeta si falta un control (PII, llaves, residencia). Máximo de rondas configurable.
- **Presupuesto de tiempo**: timeout global del enjambre (110 s internos, 120 s en pantalla), watchdog de inactividad por
  turno y degradación elegante (si algo falla, el one-pager se arma con la última versión disponible).

### Versiones verificadas (oct-2026)

| Paquete | Versión | Nota |
|---|---|---|
| `agent-framework-core` | 1.20.0 | GA |
| `agent-framework-foundry` | 1.14.0 | Reemplaza a `agent-framework-azure-ai` (congelado en rc6) |
| `agent-framework-orchestrations` | 1.3.0 | `GroupChatBuilder` |
| `azure-ai-projects[voice]` | 2.7.x | `agent-framework-foundry` exige `<2.8`; voice agents disponibles desde 2.7 |

## Cómo correrla (desarrollo, sin Azure)

```bash
# Backend
cd backend
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
cp ../.env.example ../.env            # DEMO_MODE=mock por defecto
.venv/bin/uvicorn app.main:app --port 8000

# Frontend (otra terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173 (proxy a :8000)
```

O sirviendo el build desde el backend: `cd frontend && npm run build` y abrir `http://localhost:8000`.

### Pantalla

Minimalista y legible de lejos. La izquierda muestra la **conversación en carriles**: una fila por participante, los
turnos avanzan de izquierda a derecha y cada tarjeta dice qué hizo el agente (propone, objeta, ajusta, aprueba) y qué
produjo (costo, versión, norma). Las objeciones son flechas punteadas. Debajo, el turno actual en letra grande. A la
derecha, el resultado en construcción: arquitectura, costo y gobierno.

### Atajos de teclado (pantalla)

| Tecla | Acción |
|---|---|
| `T` | Escribir el problema (fallback a teclado) |
| `R` | Reset de la demo (< 1 s) |
| `O` | Ver/ocultar el one-pager |
| `F` | Pantalla completa |
| `Esc` | Cerrar el formulario |

### Modos (`DEMO_MODE`)

- `mock`: mismo camino de orquestación MAF con un cliente simulado (`backend/app/swarm/mock.py`). Sin costo.
- `live`: Microsoft Foundry real vía `FoundryChatClient` (Responses API) con `DefaultAzureCredential`.
- `replay`: reproduce la sesión curada más reciente de `recordings/curated/` (o `REPLAY_FILE`). La pantalla muestra
  "● Sesión grabada".

Las sesiones completas, sin errores y dentro del presupuesto se curan automáticamente en `recordings/curated/`.

### Tests

```bash
cd backend && .venv/bin/python -m pytest -q
```

## Pendientes conocidos

- **Paleta de marca**: `frontend/src/branding.css` tiene valores provisorios. `www.readymind.ms` está bloqueado por la
  política de red del entorno de desarrollo; reemplazar los tokens (y `VITE_BRAND_LOGO_URL`) con la paleta oficial.
- **Precios**: `backend/pricing/*.json` son referenciales y deben validarse con la Azure Pricing Calculator antes del evento.
- **Regulación**: `backend/knowledge/regulacion_mx.md` debe revisarlo el área legal de Readymind.

## Roadmap

1. ✅ **Fase 1** — Enjambre multiagente por texto + UI del grafo (incluye mock, grabación y replay básicos).
2. **Fase 2** — Panel de gobierno: OpenTelemetry → Application Insights del proyecto Foundry, Prompt Shields previos al
   enjambre, clasificador de tema, eventos de guardrails/content filter en pantalla.
3. **Fase 3** — Voz con **Microsoft Foundry voice agents** (preview, `kind: voice`): recepcionista en es-MX
   (`es-MX-Ximena:DragonHDLatestNeural`), `azure_semantic_vad_multilingual`, `azure_deep_noise_suppression`, herramienta
   de función `cerrar_entrevista`, confirmación del brief y fallback a teclado.
4. **Fase 4** — One-pager → PDF, QR, formulario de leads con aviso de privacidad (LFPDPPP), CSV/JSONL.
5. **Fase 5** — Endurecimiento: failover automático a replay, prueba de carga (10 sesiones), Bicep/azd para
   Azure Container Apps + Managed Identity, checklist del evento y guion de 5 minutos.
6. **Al final** — Envío del PDF por mail vía **Power Automate** (flujo con disparador HTTP).
