# Envío del one-pager por correo con Power Automate

El backend no envía correos directamente. Cuando el visitante deja sus datos, el backend llama a un **flujo de Power
Automate** por HTTP, y el flujo manda el correo con el PDF adjunto desde una cuenta de Readymind.

- Si el flujo no está configurado o falla, el lead **no se pierde**: queda en `/data/leads/outbox.jsonl`.
- Lo pendiente se reenvía con `python -m scripts.retry_outbox`.

## 1. Crear el flujo

1. Power Automate → **Crear** → **Flujo de nube instantáneo** → disparador **"When an HTTP request is received"**
   ("Cuando se recibe una solicitud HTTP"). Es un conector **premium**: requiere una licencia que lo incluya.
2. En **Who can trigger the flow**, para empezar: *Anyone*. La URL lleva una firma secreta y se guarda como secreto
   de Container Apps.
3. **Request Body JSON Schema** (lo que envía el backend):

```json
{
  "type": "object",
  "properties": {
    "nombre": { "type": "string" },
    "empresa": { "type": "string" },
    "correo": { "type": "string" },
    "cargo": { "type": "string" },
    "acepta_contacto": { "type": "boolean" },
    "titulo": { "type": "string" },
    "session_id": { "type": "string" },
    "pdf_url": { "type": "string" },
    "pdf_nombre": { "type": "string" },
    "pdf_base64": { "type": "string" }
  },
  "required": ["nombre", "correo", "titulo", "pdf_base64"]
}
```

4. Acción **Office 365 Outlook → Send an email (V2)**:
   - **To:** `correo`
   - **Subject:** `Tu one-pager de Readymind: @{triggerBody()?['titulo']}`
   - **Body:** saludo con `nombre`, una línea de contexto y la invitación al taller.
   - **Attachments:** Name = `pdf_nombre`, Content = `@{base64ToBinary(triggerBody()?['pdf_base64'])}`
5. Opcional:
   - Si `acepta_contacto` es verdadero, crear un lead en Dynamics 365 / el CRM, o avisar a comercial en Teams.
   - Guardar una copia en SharePoint.
6. Acción **Response** con status **202**. El backend considera enviado cualquier 2xx.

## 2. Conectar el flujo con la demo

```bash
azd env set POWER_AUTOMATE_URL "<URL del disparador HTTP>"
azd provision        # actualiza el secreto power-automate-url en Container Apps
```

Para correrlo en local: `POWER_AUTOMATE_URL=...` en `.env`.

## 3. Probar

- Correr una sesión, escanear el QR y dejar un correo propio.
- En la página del celular debe aparecer "Te enviaremos el one-pager…", y el correo debe llegar con el PDF.
- Si aparece "Recibimos tus datos. Puedes descargar el PDF ahora…", el flujo falló. Revisar el historial de
  ejecuciones del flujo y reenviar con `scripts.retry_outbox`.

> Si en el futuro prefieren no depender de Power Automate, el mismo contrato se puede implementar con Azure
> Communication Services Email. Basta con cambiar `send_power_automate` en `backend/app/onepager/leads.py`.
