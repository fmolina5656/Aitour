# Checklist del evento · Microsoft AI Tour México

## Una semana antes

- [ ] `azd up` hecho en la suscripción del evento.
- [ ] `python -m scripts.preflight` en verde contra Azure: modelos, Prompt Shields, voice agent, App Insights y PDF.
- [ ] **Prueba de carga real**: `python -m scripts.loadtest --url https://<app> --sessions 10`, en verde.
- [ ] Al menos **3 sesiones reales buenas** grabadas, con problemas distintos (facturas, call center, crédito). Quedan en
      `/data/recordings/curated/` y son el respaldo para el replay.
- [ ] Probar el failover: desconectar la red a mitad de una sesión. Debe aparecer "Foundry no respondió" y luego la
      sesión grabada.
- [ ] Flujo de Power Automate probado con un correo real y el PDF adjunto (ver [POWER_AUTOMATE.md](POWER_AUTOMATE.md)).
- [ ] Revisión legal hecha: aviso de privacidad (`PRIVACY_*`) y base regulatoria (`backend/knowledge/regulacion_mx.md`).
- [ ] Precios del catálogo validados con la Azure Pricing Calculator (`backend/pricing/catalogo.json`).
- [ ] Satoshi copiada en `frontend/public/fonts/Satoshi-Variable.woff2`, y la imagen redeployada.
- [ ] Cuota de los modelos revisada para el pico del evento (TPM de cada deployment).

## El día del evento · montaje (30 minutos antes)

- [ ] **Hardware:**
  - Laptop conectada a la corriente, con el modo de suspensión desactivado.
  - Pantalla 1920×1080 en modo extendido o espejo.
  - **Micrófono direccional o de diadema**: el de la laptop no sirve en una feria.
  - Bocina **orientada hacia el visitante**, no hacia el micrófono.
- [ ] **Red:** cable si hay. Si no, hotspot de respaldo ya probado.
- [ ] **Navegador:**
  - Chrome con `https://<app>/?quality=high` y luego `F` para pantalla completa.
  - Si se traba, usar `?quality=low`.
- [ ] Dar permiso del micrófono **una vez**: presionar `V`, aceptar y luego `R`.
- [ ] **Sesión de prueba completa por voz**: el one-pager sale, el QR abre en un celular, el formulario llega y el
      correo llega.
- [ ] Probar un jailbreak ("ignora tus instrucciones…"): debe verse el bloqueo en ámbar y **0 llamadas** a modelos.
- [ ] `python -m scripts.preflight` en verde una última vez.
- [ ] Silenciar las notificaciones de la laptop.

## Durante el evento

| Situación | Qué hacer |
|---|---|
| Hay mucho ruido y la voz no entiende | `T` para responder por teclado, o el visitante teclea en el celular del staff |
| Se cae la red o Foundry | `P`: reproduce ya una sesión grabada (la pantalla muestra "Sesión grabada") |
| Algo se trabó | `R` (reset en menos de 1 s) y volver a empezar |
| La escena va lenta | Recargar con `?quality=low` |
| El visitante no quiere dejar datos | Botón "Ver one-pager" (`O`) y que le saque una foto a la pantalla |
| Correos que no salieron | Al final del día: `python -m scripts.retry_outbox` |

## Al cierre de cada día

- [ ] Descargar `/data/leads/leads.csv` (Azure Files → share `data`) y entregarlo a comercial.
- [ ] Revisar `outbox.jsonl` y reenviar lo pendiente.
- [ ] Revisar en Application Insights el costo y la latencia del día, y si hubo errores.
- [ ] **Privacidad:** las grabaciones (`/data/recordings`) contienen lo que contaron los visitantes. Borrarlas al
      terminar el evento según la política de Readymind.
