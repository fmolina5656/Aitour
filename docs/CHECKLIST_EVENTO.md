# Checklist del evento · Microsoft AI Tour México

## Una semana antes

- [ ] `azd up` hecho en la suscripción del evento.
- [ ] `python -m scripts.preflight` en verde contra Azure: modelos, Prompt Shields, voice agent, App Insights y PDF.
- [ ] **Prueba de carga real**: `python -m scripts.loadtest --url https://<app> --sessions 10 --salas pc,tablet1,tablet2`,
      en verde (PC y tablets en paralelo).
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
- [ ] Abrir `https://<app>/accesos` en una tablet o un celular del equipo: tiene todos los links del stand y su QR.
- [ ] <a id="pin-del-vendedor"></a>**PIN del vendedor** (una vez, sin redeploy): definir un PIN de 6+ dígitos y cargarlo en la app:
  ```
  az containerapp update -n <app> -g <grupo> --set-env-vars SELLER_PIN=<pin>
  ```
  Cada vendedor abre `https://<app>/vendedor` en su celular, pone el PIN y su nombre. El PIN no se escribe en el repo
  ni se comparte por chat abierto. Al cerrar cada día: pestaña **Leads → Descargar Excel (CSV)**.
- [ ] En cada tablet: tocar **💼** (abajo a la derecha), poner el PIN y el nombre de quien atiende. Queda guardado en la
  tablet; desde ahí cualquiera del equipo carga un lead en 30 segundos sin salir de la demo.
- [ ] **Navegador:**
  - Chrome con `https://<app>/?quality=high` y luego `F` para pantalla completa.
  - Tablets: `https://<app>/?sala=tablet1` y `https://<app>/?sala=tablet2` (cada una con su propia sesión).
    El encabezado de la PC dice "Sala pc"; si una pantalla dice "Sala desconocida", revisar el `?sala=`.
  - Si se traba, usar `?quality=low`.
- [ ] Dar permiso del micrófono **una vez**: presionar `V`, aceptar y luego `R`.
- [ ] **Sesión de prueba completa por voz**: el one-pager sale, el QR abre en un celular, el formulario llega y el
      correo llega.
- [ ] **Lector de documentos** (`/ocr`): kit de `/ocr/muestras` impreso (y la credencial recortada); permiso de cámara
      dado una vez en cada tablet; leer la factura A (cuadra) y la B (no cuadra).
- [ ] **Visión del stand** (`/vision`):
  - Tablet en trípode alto (más de 2 m), mirando el stand en diagonal hacia abajo y con buena luz.
  - Webcam USB con **hub USB-C con carga** (si no, la tablet no carga en todo el día). En Android, confirmar que la
    webcam aparece en el selector de cámara; si no, usar la cámara trasera de la tablet.
  - Dibujar las zonas (**Z**): la fila de la demo (con nombre que empiece por «Fila»), la pantalla principal y Glitch.
  - Tocar **↺ Nuevo día** al abrir el stand, y pegar el letrero impreso (`/vision/letrero`) junto a la cámara.
- [ ] **Las 3 salas a la vez**: arrancar una sesión en la PC y en las dos tablets; `R` en una tablet no corta las otras.
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
