# Pendientes · para retomar

**Estado al cierre de la sesión (8-oct-2026):** las Fases 1 a 5 están implementadas, con 28 tests en verde y
commiteadas en `claude/readymind-aitour-demo`.

**Probado de punta a punta en modo simulado:**
- Voz con micrófono real (dispositivo de prueba de Chromium).
- Bloqueo de jailbreak.
- Enjambre con debate.
- PDF, QR, formulario y leads.
- Failover a replay.
- Prueba de carga de 10 sesiones.

**Nunca se corrió contra Azure real.** Lo de abajo necesita a Readymind, ordenado por prioridad.

## 1. Azure (bloquea todo lo "live")

- [ ] **Suscripción y región**, y decidir si se crea un proyecto de Foundry nuevo (lo hace `azd up`) o se usa uno
      existente.
  - La región debe tener **voice agents (preview)** y los modelos.
  - Candidatas: `eastus2` o `swedencentral`. Spain Central y Poland Central no tienen voice agents.
- [ ] **Acceso a la preview de voice agents** habilitado en la suscripción.
- [ ] **Modelos**: confirmar en el catálogo de la región el nombre, la versión y la cuota de cada deployment, y
      completar `infra/main.parameters.json → modelDeployments` (plantilla en `infra/models.example.json`).
  - Hoy: Arquitecto `gpt-5.4`; Financiero, Riesgo y Redactor `gpt-5.4-mini`; guardia `gpt-5.4-nano`.
  - Voz: `gpt-realtime-2.1` administrado.
- [ ] `azd up`. Es la primera vez que se despliega: el Bicep compila con sus tipos, pero **no se probó contra ARM**. Lo
      más probable de ajustar: las propiedades del guardrail (`raiPolicies`) y la conexión de App Insights.
- [ ] Verificar que el hook creó el voice agent (`python -m scripts.create_voice_agent`).
  - Si la voz HD `es-MX-Ximena:DragonHDLatestNeural` no está en la región: `VOICE_NAME=es-MX-DaliaNeural`.

## 2. Validación en vivo (después de `azd up`)

- [ ] `python -m scripts.preflight` en verde.
- [ ] Una sesión real completa. Puntos a mirar, porque solo se probaron en simulado:
  - [ ] **Salidas estructuradas** (`response_format`) y `reasoning` con los modelos `gpt-5.4*` en la Responses API.
  - [ ] **Tiempos**: el enjambre real completo debe cerrar en menos de 120 s. Si se pasa: bajar `REASONING_EFFORT`,
        usar modelos más chicos o `MAX_DEBATE_ROUNDS=1`.
  - [ ] **El debate**: que el Financiero realmente objete. Depende de qué componentes proponga el Arquitecto; ajustar
        `OBJECTION_COMPONENT_SHARE` si hace falta.
  - [ ] **Voz**:
    - nombres de eventos y flujo de `registrar_brief` / `confirmar_brief` contra el servicio real;
    - corte de la voz cuando el visitante habla encima (barge-in);
    - calidad del reconocimiento con el ruido del stand.
  - [ ] **Prompt Shields** con Entra ID sobre el endpoint de la cuenta de Foundry.
  - [ ] **Trazas** visibles en *Tracing* del proyecto de Foundry.
- [ ] `python -m scripts.loadtest --url https://<app> --sessions 10` contra Foundry real.
- [ ] Grabar **3 sesiones reales buenas** para el replay de respaldo. Hoy solo está la semilla simulada.

## 3. Correo (al final, como pediste)

- [ ] Crear el flujo de Power Automate siguiendo [docs/POWER_AUTOMATE.md](docs/POWER_AUTOMATE.md). El disparador HTTP
      es **premium** (licencia).
- [ ] `azd env set POWER_AUTOMATE_URL "<url>"` y `azd provision`.

## 4. Legal y contenido

- [ ] **Aviso de privacidad**: razón social, domicilio, contacto ARCO y URL del aviso integral (`PRIVACY_*`). El texto
      está en `backend/app/onepager/templates/privacidad.html`.
- [ ] Revisión de `backend/knowledge/regulacion_mx.md`. Es lo único que el agente de Riesgo puede citar.
- [ ] **Precios** de `backend/pricing/catalogo.json` y `runtime.json` con la Azure Pricing Calculator. Hoy son
      referenciales.
- [ ] Política de retención de grabaciones y leads (las grabaciones contienen lo que cuentan los visitantes).

## 5. Marca

- [ ] `Satoshi-Variable.woff2` en `frontend/public/fonts/`, para no depender de Fontshare en el stand.
- [ ] **Logo negativo oficial en SVG** para la pantalla oscura. El actual es un PNG de 40 px recoloreado por mí.

## 6. Hardware del stand

- [ ] Micrófono direccional o de diadema, y una bocina orientada hacia el visitante.
- [ ] Laptop con GPU decente. Si no, usar `?quality=low`.

## Decisiones que tomé por mi cuenta (revisar)

- **Replay**: se marca con "Sesión grabada" en el encabezado, por transparencia con el visitante.
- **Failover automático**: solo si Foundry falla **antes** de que hable algún agente. Si ya habló, se termina con lo
  que haya.
- **Una sola réplica** en Container Apps, siempre encendida: la sesión del stand vive en memoria.
- **QR firmado con HMAC**: si `LEAD_SECRET` cambia, los QR viejos dejan de valer.
- **La pantalla nunca muestra datos personales** (solo "¡Recibido!").
- **El one-pager no se abre solo** al terminar: queda el QR en el chat y se abre con `O`.

## Limitaciones conocidas

- La imagen Docker no se pudo construir en este entorno (no hay daemon de Docker). La valida `azd up`, que la
  construye en ACR (`remoteBuild: true`).
- Los turnos del enjambre son secuenciales (así se ve el debate). El tiempo total depende de la latencia del modelo
  del Arquitecto.
