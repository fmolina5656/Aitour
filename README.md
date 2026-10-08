# Readymind · Microsoft AI Tour México — "Cuéntame tu problema y en 3 minutos te armo la solución"

Demo de stand. El visitante le cuenta **por voz** un problema de negocio a una recepcionista de IA (Microsoft Foundry
voice agent). Después, un **equipo de 4 agentes** (Microsoft Agent Framework + Microsoft Foundry) diseña la solución en
vivo y la discute entre sí: el Financiero objeta el costo y Riesgo objeta por datos personales y LFPDPPP. Al final
entrega un one-pager ejecutivo que el visitante recibe en PDF escaneando un QR.

Todo se ve en una escena 3D (Three.js) pensada para una pantalla de 1920×1080 vista de lejos.

> **Estado:** Fases 1 a 5 implementadas y probadas en modo simulado. Lo que necesita a Readymind o recursos de Azure
> reales está en **[PENDIENTES.md](PENDIENTES.md)**.
>
> - Operación del stand: [docs/CHECKLIST_EVENTO.md](docs/CHECKLIST_EVENTO.md)
> - Guion de 5 minutos: [docs/GUION_STAND.md](docs/GUION_STAND.md)
> - Correo con Power Automate: [docs/POWER_AUTOMATE.md](docs/POWER_AUTOMATE.md)

## Flujo de una sesión (meta: < 4 minutos)

| Tiempo | Qué pasa | Dónde vive |
|---|---|---|
| 0:00 | Pantalla en espera. El visitante presiona **V** (o el botón) | `frontend/src/App.tsx` |
| 0:00–1:15 | Entrevista por voz: máximo 3 preguntas, transcripción en el chat, núcleo 3D que late con la voz | `backend/app/voice/` |
| 1:15 | Tarjeta **"Esto entendí"**: confirma con la voz, con el botón o con Enter | `VoiceUI.tsx` |
| 1:15 | **Gobierno**: Prompt Shields + validación de tema. Un ataque se bloquea en pantalla antes de llegar a un modelo | `backend/app/guard.py` |
| 1:20–3:00 | **Enjambre**: Arquitecto → Financiero (objeta) → Arquitecto ajusta → Financiero aprueba → Riesgo (objeta) → Arquitecto ajusta → Redactor | `backend/app/swarm/` |
| 3:00 | Núcleo → one-pager con onda expansiva; **QR** en pantalla | `backend/app/onepager/` |
| 3:00–4:00 | El visitante escanea, deja sus datos con consentimiento y recibe el PDF | `/lead/{sesión}` |

## Arquitectura

```
 Pantalla 1920×1080 (React + Three.js)          Celular del visitante
   │ WS /ws/stage   ◄── eventos ──┐               │ HTTPS /lead/{sesión}?t=…  (QR firmado)
   │ WS /ws/voice   ⇄ PCM16 24kHz │               ▼
   ▼                              │   ┌──────── Backend FastAPI · Azure Container Apps (1 réplica, Managed Identity) ────────┐
 Micrófono (AudioWorklet)         └───┤ SessionManager: entrevista → guardia → enjambre → one-pager (timeouts, reset, failover) │
                                      │ EventBus ─► Recorder (JSONL, curado automático) ─► Replay con la misma UI              │
                                      │ Voz: relay ⇄ Foundry voice agent (gpt-realtime, es-MX, VAD multilingüe, ruido)        │
                                      │ Guardia: Prompt Shields (Content Safety, Entra ID) + clasificador de tema (nano)        │
                                      │ Enjambre MAF: GroupChatBuilder + director determinista · FoundryChatClient (Responses)  │
                                      │ Calculador de costos (pricing/*.json) · generador de arquitectura                     │
                                      │ One-pager: Jinja2 → Chromium → PDF · QR (segno) · leads CSV/JSONL · Power Automate     │
                                      └──── OpenTelemetry → Application Insights (conectado al proyecto: Tracing de Foundry) ─┘
```

**Decisiones clave**

- **Todo lo que se ve es un evento del bus** (`backend/app/events.py`). El grabador guarda esos eventos, así que el
  replay usa exactamente la misma pantalla.
- **El modelo no inventa números.** El Arquitecto devuelve componentes estructurados y Python calcula el costo con
  `backend/pricing/catalogo.json`. Arquitectura y costo siempre coinciden.
- **El debate es real.** El director (`backend/app/swarm/director.py`) le pasa al Financiero la tabla del calculador.
  - El Financiero objeta si un modelo premium concentra ≥ 40 % del costo o si se pasa del presupuesto.
  - Riesgo objeta si falta un control (PII, llaves, residencia de datos).
- **Presupuesto de tiempo duro.**
  - Entrevista: cierre suave a los 70 s y corte a los 95 s.
  - Enjambre: corta a los 110 s (en pantalla se muestran 120 s), con vigilancia de inactividad por turno.
  - Si algo falla, el one-pager se arma igual con lo último disponible.
- **Resiliencia.**
  - Si Foundry falla antes de que hable un agente, se reproduce una sesión grabada real.
  - La tecla **P** fuerza el replay.
  - Si no hay micrófono, se sigue por teclado.

### Versiones verificadas (octubre 2026)

| Paquete | Versión | Nota |
|---|---|---|
| `agent-framework-core` | 1.20.0 | GA |
| `agent-framework-foundry` | 1.14.0 | Reemplaza a `agent-framework-azure-ai` (congelado en rc6) |
| `agent-framework-orchestrations` | 1.3.0 | `GroupChatBuilder` |
| `azure-ai-projects[voice]` | 2.7.x | Voice agents (preview); `agent-framework-foundry` exige `<2.8` |
| `three` / `@react-three/fiber` / `drei` | 0.186.1 / 9.8.1 / 10.7.9 | `postprocessing` exige three `<0.187` |
| API de Prompt Shields | 2024-09-01 | `text:shieldPrompt` con token de Entra |
| Foundry en Bicep | `Microsoft.CognitiveServices/accounts@2025-06-01` | `kind: AIServices`, `allowProjectManagement` |

## Correrla en local sin Azure (modo simulado)

```bash
# Backend
cd backend
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m playwright install chromium     # para el PDF del one-pager
cp ../.env.example ../.env                          # DEMO_MODE=mock por defecto
.venv/bin/uvicorn app.main:app --port 8000

# Frontend
cd frontend && npm install && npm run build         # luego abrir http://localhost:8000
# (o `npm run dev` → http://localhost:5173 con proxy a :8000)
```

En modo `mock` todo funciona sin Azure:
- **Enjambre:** se recorre el mismo camino de orquestación de MAF, con respuestas simuladas.
- **Recepcionista:** es simulada. Responde a lo que escribes y, si hay micrófono, a ~3 s de audio por respuesta.
- **Guardia:** usa heurísticas locales en lugar de Prompt Shields.
- **Salida:** el PDF, el QR y los leads son reales.

### Teclas de la pantalla

| Tecla | Acción |
|---|---|
| `V` | Empezar la entrevista por voz |
| `T` | Escribir (durante la entrevista: responder por teclado) |
| `Enter` | Confirmar "Esto entendí" |
| `O` | Ver/ocultar el one-pager |
| `R` | Reset de la demo (< 1 s) |
| `P` | Operador: reproducir ya una sesión grabada (si se cae la red) |
| `F` | Pantalla completa |

### Modos (`DEMO_MODE`) y calidad gráfica

- `live`: Microsoft Foundry real. `mock`: sin Azure. `replay`: solo sesiones grabadas.
- El modo se cambia en caliente con `POST /api/mode`.
- La escena apaga bloom y estrellas sola si bajan los FPS. Para forzar la calidad: `?quality=high` o `?quality=low`.

## Despliegue en Azure (azd + Bicep)

`infra/` crea, con Managed Identity y sin keys:

- **Foundry:** cuenta `AIServices` con `disableLocalAuth`, el proyecto y los deployments de modelos.
- **Guardrail `readymind-stand`:** filtros de contenido más Prompt Shields directos e indirectos, en modo bloqueo.
- **Observabilidad:** Log Analytics y Application Insights, conectado al proyecto.
- **App:** Container Apps (una réplica siempre encendida, con WebSockets), ACR, y Azure Files montado en `/data`.
- **Roles:** Azure AI User y Cognitive Services User para la identidad de la app y para quien despliega.

```bash
azd auth login
azd env new readymind-aitour
azd env set AZURE_LOCATION eastus2          # región con voice agents (preview) y los modelos elegidos
# 1) Completar modelDeployments en infra/main.parameters.json (ver infra/models.example.json)
# 2) Opcional: azd env set POWER_AUTOMATE_URL "<URL del disparador HTTP>"
azd up                                       # provisiona, construye la imagen en ACR y despliega
```

- **Voice agent:** el hook `postprovision` lo crea con `python -m scripts.create_voice_agent`; también se puede correr
  a mano.
- **Revisar antes del evento:** `cd backend && python -m scripts.preflight` contra el entorno real (ver el checklist).
- **Imagen:** el `Dockerfile` de la raíz construye frontend + backend + Chromium en una sola imagen.

## Scripts de operación (`backend/scripts/`)

| Script | Para qué |
|---|---|
| `create_voice_agent` | Crea o versiona el voice agent recepcionista en el proyecto |
| `preflight` | Chequeo de punta a punta antes de abrir el stand (sale con 1 si algo crítico falla) |
| `loadtest --sessions 10` | Prueba de carga contra el backend en marcha (sin degradación ni crecimiento de memoria) |
| `retry_outbox` | Reenvía a Power Automate los leads que quedaron pendientes |

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q       # 28 tests
```

Cubren:
- **Enjambre:** debate completo, corte por tiempo, costos deterministas.
- **Guardia:** jailbreak, fuera de tema, llamada REST real simulada, respaldo local y bloqueo de la sesión.
- **Voz:** definición válida del agente, entrevista completa por WebSocket y corte duro.
- **Salida:** PDF real, QR firmado, consentimiento, outbox, Power Automate y límite de envíos.
- **Resiliencia:** failover real y reset a mitad del enjambre.

## Estructura

```
backend/app/         config, events (bus), session (estados), guard, telemetry, recorder (grabación y replay)
  swarm/             agentes, prompts, director, mock, runner (MAF)
  voice/             definición del voice agent, backends (Foundry / simulado), relay de la entrevista
  onepager/          render (HTML → PDF), store (QR firmado), leads (CSV/JSONL + Power Automate), plantillas
backend/scripts/     create_voice_agent, preflight, loadtest, retry_outbox
backend/pricing/     catálogo de precios configurable (referencial)
backend/knowledge/   base regulatoria MX para el agente de Riesgo (revisión legal pendiente)
backend/seed/        sesión semilla para el replay de respaldo
frontend/src/scene/  escena 3D (núcleo, orbes, cometas, satélites, cámara)
frontend/src/voice/  micrófono (AudioWorklet), reproducción y sesión de voz
frontend/src/branding.css   ÚNICO lugar con la paleta y la tipografía de Readymind
infra/               Bicep (azd) · azure.yaml · Dockerfile
docs/                checklist del evento, guion de 5 minutos, Power Automate
```
