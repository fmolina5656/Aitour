# Readymind · Microsoft AI Tour México — "Cuéntame tu problema y en 3 minutos te armo la solución"

Demo de stand. El visitante le cuenta **por voz** un problema de negocio a una recepcionista de IA (Microsoft Foundry
voice agent) y **Glitch**, la mascota de Readymind, lo escucha en el centro de la pantalla. Después, un **equipo de 5
agentes** (Microsoft Agent Framework + Microsoft Foundry) diseña la solución en Azure en vivo y la discute entre sí: el
Financiero objeta el costo, Riesgo objeta por datos personales y LFPDPPP, el Diagramador dibuja la arquitectura y el
Redactor arma un one-pager ejecutivo que el visitante recibe en PDF escaneando un QR.

Todo se ve en una escena 3D (Three.js) pensada para una pantalla de 1920×1080 vista de lejos.

> **Estado:** desplegado y funcionando en Azure (modo `live`). Lo que todavía necesita a Readymind está en
> **[PENDIENTES.md](PENDIENTES.md)**.
>
> - **Para redeployar un cambio:** [Cómo redeployar](#cómo-redeployar).
> - Operación del stand: [docs/CHECKLIST_EVENTO.md](docs/CHECKLIST_EVENTO.md)
> - Guion de 5 minutos: [docs/GUION_STAND.md](docs/GUION_STAND.md)
> - Correo con Power Automate: [docs/POWER_AUTOMATE.md](docs/POWER_AUTOMATE.md)

## Entorno en Azure

| | |
|---|---|
| **URL de la demo** | https://rm-aitour-mwsx5jmp.redmushroom-a798eb0d.eastus2.azurecontainerapps.io |
| **Suscripción** | App Legales |
| **Región** | `eastus2` |
| **Grupo de recursos** | `rg-readymind-aitour` |
| **Entorno de azd** | `readymind-aitour` (ya configurado en esta máquina) |
| **Proyecto de Foundry** | `rm-foundry-mwsx5jmpqpqlm` / `aitour` |
| **Voice agent** | `readymind-recepcionista` (versión 5: voz `es-MX-Valeria:MAI-Voice-2.1-Flash`) |

## Cómo redeployar

Todo se corre desde la raíz del proyecto, en **PowerShell**. Si `azd` pide autenticación: `azd auth login`.
Después de cualquier despliegue, en la pantalla del stand recargar con **Ctrl+Shift+R** y presionar **R**.

### 1. Cambios de código (lo más común)

Backend, frontend, PDF del one-pager, prompts o instrucciones de los agentes del enjambre:

```powershell
azd deploy
```

Construye la imagen en Azure Container Registry (no hace falta Docker local) y la publica en Container Apps.
Tarda unos 3–4 minutos y no toca la infraestructura. Durante el cambio de revisión puede tardar unos segundos más en
responder.

### 2. Cambios de infraestructura

Archivos de `infra/`, variables de entorno de la app, modelos o deployments:

```powershell
azd up          # actualiza los recursos y despliega el código (≈ 5–6 min)
azd provision   # solo infraestructura, sin desplegar código
```

### 3. Cambios en la recepcionista de voz

La recepcionista vive en Foundry, no en la app: si cambias `backend/app/voice/definition.py` (instrucciones, voz,
saludo, turnos) hay que publicar una **versión nueva del voice agent**. Queda activa al instante, sin redeploy:

```powershell
cd backend
azd env get-values | ForEach-Object { if ($_ -match '^([A-Z_]+)="(.*)"$') { Set-Item "env:$($matches[1])" $matches[2] } }
$env:DEMO_MODE = 'live'
.\.venv\Scripts\python.exe -m scripts.create_voice_agent
```

Para cambiar la voz sin tocar código, antes del script: `$env:VOICE_NAME = 'es-MX-Alejo:MAI-Voice-2.1-Flash'`.

Para fijar la app a una versión anterior del voice agent (sin redeploy de código):

```powershell
az containerapp update -n rm-aitour-mwsx5jmp -g rg-readymind-aitour --set-env-vars VOICE_AGENT_VERSION=<n>
```

Sin esa variable, la app usa la versión más reciente.

### Revisar que todo funcione

Desde `backend`, con las mismas variables cargadas que en el punto 3:

```powershell
.\.venv\Scripts\python.exe -m scripts.preflight
```

Prueba de punta a punta contra Azure: credencial, los 5 modelos, Prompt Shields, voice agent, Chromium para el PDF y
Application Insights. Sale con código 1 si algo crítico falla.

### Ver los logs de la app

```powershell
az containerapp logs show -n rm-aitour-mwsx5jmp -g rg-readymind-aitour --tail 50
```

Los logs también quedan en Log Analytics (`rm-logs-mwsx5jmpqpqlm`, tabla `ContainerAppConsoleLogs_CL`) y las trazas de
los agentes en **Tracing** del proyecto de Foundry.

### Avisos esperables

- `PowerShell 7 (pwsh) commands found in project…`: es inofensivo. El hook de `azure.yaml` que crea el voice agent
  usa `pwsh`; si no está instalado, el voice agent se crea a mano con el punto 3.
- `az containerapp logs show` puede fallar en Windows con `UnicodeEncodeError` por caracteres como "→" en los
  logs. En ese caso, consultar Log Analytics.

## Flujo de una sesión (meta: < 4 minutos)

| Tiempo | Qué pasa | Dónde vive |
|---|---|---|
| 0:00 | Pantalla en espera con Glitch flotando. El visitante presiona **V** (o el botón) | `frontend/src/App.tsx` |
| 0:00–1:15 | Entrevista por voz con la recepcionista: máximo 3 preguntas, transcripción en el chat. Glitch rebota con la voz y se inclina cuando habla el visitante | `backend/app/voice/` · `scene/Core.tsx` |
| 1:15 | Tarjeta **"Esto entendí"**: se confirma con la voz, con el botón o con Enter | `VoiceUI.tsx` |
| 1:15 | **Gobierno**: Prompt Shields + validación de tema. Un ataque se bloquea en pantalla antes de llegar a un modelo | `backend/app/guard.py` |
| 1:20–2:20 | **Enjambre**: Arquitecto → Financiero ⇄ Arquitecto → Riesgo ⇄ Arquitecto → Diagramador → Redactor. El agente que piensa crece y los demás (y Glitch) se achican | `backend/app/swarm/` · `scene/AgentOrb.tsx` |
| 1:20– | **Diagrama de arquitectura en Azure** en pantalla desde la primera propuesta; se redibuja con cada ajuste y al final queda el del Diagramador | `swarm/diagram.py` · `ArchitecturePanel.tsx` |
| ~2:20 | Glitch pone cara feliz, onda expansiva y **QR** en pantalla | `backend/app/onepager/` |
| hasta 4:00 | El visitante escanea, deja sus datos con consentimiento y recibe el PDF | `/lead/{sesión}` |

En Foundry real el enjambre completo tarda ~60 s (medido: 57 y 59 s); el corte duro es a los 110 s.

## Los agentes

| Agente | Color | Modelo | Qué hace |
|---|---|---|---|
| Recepcionista | (voz) | `gpt-realtime-2.1` (voice agent) | Entrevista al visitante y arma el brief |
| Arquitecto | azul | `gpt-5.4` | Propone 4–7 servicios de Azure con cantidades; ajusta ante objeciones |
| Financiero | rosa | `gpt-5.4-mini` | Lee la tabla del calculador y objeta si el costo no cierra |
| Riesgo | coral | `gpt-5.4-mini` | Datos personales y normas MX (solo cita `backend/knowledge/`) |
| Diagramador | amarillo | `gpt-5.4-mini` | Agrupa la arquitectura final en zonas, ordena el flujo y lo explica en pasos |
| Redactor | violeta | `gpt-5.4-mini` | Escribe el one-pager con la versión final |
| Guardia | — | `gpt-5.4-nano` | Clasificador de tema (junto con Prompt Shields) |

Los colores están en `frontend/src/branding.css` (`--who-*`). Ninguno es verde (Glitch, recepcionista y "terminado")
ni ámbar (objeciones).

## Arquitectura

```
 Pantalla 1920×1080 (React + Three.js)          Celular del visitante
   │ WS /ws/stage   ◄── eventos ──┐               │ HTTPS /lead/{sesión}?t=…  (QR firmado)
   │ WS /ws/voice   ⇄ PCM16 24kHz │               ▼
   ▼                              │   ┌──────── Backend FastAPI · Azure Container Apps (1 réplica, Managed Identity) ────────┐
 Micrófono (AudioWorklet)         └───┤ SessionManager: entrevista → guardia → enjambre → one-pager (timeouts, reset, failover) │
 Reproducción con colchón anti-trabas │ EventBus ─► Recorder (JSONL, curado automático) ─► Replay con la misma UI              │
                                      │ Voz: relay ⇄ Foundry voice agent (gpt-realtime-2.1 + MAI-Voice es-MX, VAD multilingüe) │
                                      │ Guardia: Prompt Shields (Content Safety, Entra ID) + clasificador de tema (nano)        │
                                      │ Enjambre MAF: GroupChatBuilder + director determinista · FoundryChatClient (Responses)  │
                                      │ Calculador de costos (pricing/*.json) · diagrama SVG (diagram.py)                     │
                                      │ One-pager: Jinja2 → Chromium → PDF (auto-ajuste a 1 hoja) · QR · leads · Power Automate │
                                      └──── OpenTelemetry → Application Insights (conectado al proyecto: Tracing de Foundry) ─┘
```

**Decisiones clave**

- **Todo lo que se ve es un evento del bus** (`backend/app/events.py`). El grabador guarda esos eventos, así que el
  replay usa exactamente la misma pantalla.
- **El modelo no inventa números ni dibuja.**
  - El Arquitecto devuelve componentes estructurados y Python calcula el costo con `backend/pricing/catalogo.json`.
  - El Diagramador devuelve zonas, flujo y pasos; `backend/app/swarm/diagram.py` calcula el layout y genera el SVG
    (tema oscuro para la pantalla, claro para el PDF). Si el Diagramador no llega o inventa ids, el diagrama sale de
    las conexiones del Arquitecto.
- **El debate es real.** El director (`backend/app/swarm/director.py`) le pasa al Financiero la tabla del calculador.
  - El Financiero objeta si un modelo premium concentra ≥ 40 % del costo o si se pasa del presupuesto.
  - Riesgo objeta si falta un control (PII, llaves, residencia de datos).
  - Lo que agrega un ajuste se marca como **NUEVO** en el diagrama.
- **Presupuesto de tiempo duro.**
  - Entrevista: cierre suave a los 70 s y corte a los 95 s.
  - Enjambre: corta a los 110 s (en pantalla se muestran 120 s), con vigilancia de inactividad por turno.
  - Si no queda tiempo para el Diagramador, cierra el Redactor y el diagrama automático queda igual.
  - Si algo falla, el one-pager se arma igual con lo último disponible.
- **Resiliencia.**
  - Si Foundry falla antes de que hable un agente, se reproduce una sesión grabada real.
  - La tecla **P** fuerza el replay.
  - Si no hay micrófono, se sigue por teclado.
- **El PDF nunca se corta.** `render_pdf` reduce la escala lo justo para que el contenido entre en una hoja carta.

### La voz

- **Voz:** `es-MX-Valeria:MAI-Voice-2.1-Flash` (Azure TTS expresiva, baja latencia, acento mexicano real). Alternativa
  masculina: `es-MX-Alejo:MAI-Voice-2.1-Flash`. Se cambia con `VOICE_NAME` (y opcionalmente `VOICE_STYLE`, p. ej.
  `joyful`) al publicar una versión nueva del voice agent.
- Lo que aprendimos al probar contra Foundry real:
  - `es-MX-Ximena` no existe: Ximena es una voz de España (`es-ES`).
  - Con voces nativas del modelo (`VOICE_TYPE=openai`, p. ej. `marin`), el saludo fijo y las frases de espera no están
    permitidos, y el audio cuenta como tokens de salida.
  - `max_output_tokens` bajo cortaba las respuestas a la mitad: está en 4096 y la brevedad la dan las instrucciones.
  - El guardrail del voice agent se pasa con su **ID ARM completo** (`VOICE_RAI_POLICY`), no con el nombre.
- El navegador reproduce con un colchón de ~300 ms: si la red se traba, hace una pausa limpia en vez de entrecortarse.

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

En Windows (PowerShell):

```powershell
# Backend
cd backend
uv venv --python 3.12 .venv; uv pip install --python .venv\Scripts\python.exe -e ".[dev]"
.\.venv\Scripts\python.exe -m playwright install chromium     # para el PDF del one-pager
Copy-Item ..\.env.example ..\.env                             # DEMO_MODE=mock por defecto
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

# Frontend (otra terminal)
cd frontend; npm install; npx vite --port 5173                # http://localhost:5173 con proxy a :8000
# (o `npm run build` y abrir http://localhost:8000)
```

En macOS/Linux, lo mismo con `.venv/bin/python`.

En modo `mock` todo funciona sin Azure:
- **Enjambre:** se recorre el mismo camino de orquestación de MAF (los 5 agentes), con respuestas simuladas.
- **Recepcionista:** es simulada. Responde a lo que escribes y, si hay micrófono, a ~3 s de audio por respuesta.
- **Guardia:** usa heurísticas locales en lugar de Prompt Shields.
- **Salida:** el diagrama, el PDF, el QR y los leads son reales.

Para probar en local **contra Foundry real**, cargar las variables de azd como en
[Cómo redeployar → punto 3](#3-cambios-en-la-recepcionista-de-voz) y arrancar el backend con `DEMO_MODE=live`.

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

## Despliegue desde cero (otro entorno)

`infra/` crea, con Managed Identity y sin keys:

- **Foundry:** cuenta `AIServices` con `disableLocalAuth`, el proyecto y los deployments de modelos.
- **Guardrail `readymind-stand`:** filtros de contenido más Prompt Shields directos e indirectos, en modo bloqueo.
- **Observabilidad:** Log Analytics y Application Insights, conectado al proyecto.
- **App:** Container Apps (una réplica siempre encendida, con WebSockets), ACR, y Azure Files montado en `/data`.
- **Roles:** Foundry User y Cognitive Services User para la identidad de la app y para quien despliega.

```powershell
azd auth login
azd env new <nombre> --subscription <id> --location eastus2   # región con voice agents (preview) y los modelos
# 1) Revisar modelDeployments en infra/main.parameters.json: versión y cuota de cada modelo en la región
#    (az cognitiveservices model list --location eastus2)
# 2) Firma de los QR, fija por entorno (si cambia, los QR ya mostrados dejan de valer):
azd env set LEAD_SECRET (python -c "import secrets; print(secrets.token_urlsafe(32))")
# 3) Opcional: azd env set POWER_AUTOMATE_URL "<URL del disparador HTTP>"
azd up
# 4) Crear el voice agent (ver "Cómo redeployar", punto 3) y correr el preflight
```

Hace falta rol **Owner** (o Contributor + User Access Administrator) en la suscripción, porque el Bicep asigna roles.

## Scripts de operación (`backend/scripts/`)

| Script | Para qué |
|---|---|
| `create_voice_agent` | Crea una versión nueva del voice agent recepcionista en el proyecto |
| `preflight` | Chequeo de punta a punta antes de abrir el stand (sale con 1 si algo crítico falla) |
| `loadtest --sessions 10` | Prueba de carga contra el backend en marcha (sin degradación ni crecimiento de memoria) |
| `retry_outbox` | Reenvía a Power Automate los leads que quedaron pendientes |

## Tests

```powershell
cd backend; .\.venv\Scripts\python.exe -m pytest -q       # 29 tests
cd frontend; npx tsc -b                                    # tipos del frontend
```

Cubren:
- **Enjambre:** debate completo con Diagramador, corte por tiempo, costos deterministas.
- **Diagrama:** una versión por cada ajuste + la del Diagramador, marca de lo nuevo, ids inventados, texto escapado.
- **Guardia:** jailbreak, fuera de tema, llamada REST real simulada, respaldo local y bloqueo de la sesión.
- **Voz:** definición válida del agente (voz es-MX, saludo, límite de tokens), entrevista completa y corte duro.
- **Salida:** PDF real en una hoja, QR firmado, consentimiento, outbox, Power Automate y límite de envíos.
- **Resiliencia:** failover real y reset a mitad del enjambre.

## Estructura

```
backend/app/         config, events (bus), session (estados), guard, telemetry, recorder (grabación y replay)
  swarm/             agentes, prompts, director, diagram (SVG), mock, runner (MAF)
  voice/             definición del voice agent, backends (Foundry / simulado), relay de la entrevista
  onepager/          render (HTML → PDF), store (QR firmado), leads (CSV/JSONL + Power Automate), plantillas
backend/scripts/     create_voice_agent, preflight, loadtest, retry_outbox
backend/pricing/     catálogo de precios configurable (referencial)
backend/knowledge/   base regulatoria MX para el agente de Riesgo (revisión legal pendiente)
backend/seed/        sesión semilla para el replay de respaldo
frontend/src/scene/  escena 3D: Glitch (Core), mini-Glitchs de los agentes (AgentOrb), cometas, satélites, cámara
frontend/src/voice/  micrófono (AudioWorklet), reproducción con colchón y sesión de voz
frontend/src/branding.css   ÚNICO lugar con la paleta y la tipografía de Readymind
frontend/public/brand/      logo y Glitch (ojos abiertos / cerrados)
infra/               Bicep (azd) · azure.yaml · Dockerfile
docs/                checklist del evento, guion de 5 minutos, Power Automate
```
