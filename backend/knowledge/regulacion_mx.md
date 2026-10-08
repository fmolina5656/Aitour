# Base de referencia regulatoria (México) para el agente de Riesgo/Compliance

> ⚠️ PENDIENTE DE REVISIÓN POR EL ÁREA LEGAL DE READYMIND antes del evento.
> El agente SOLO debe citar normas de esta lista. No es asesoría legal.

## Datos personales (aplica casi siempre)
- **LFPDPPP (nueva ley, publicada en el DOF el 20-mar-2025)**: Ley Federal de Protección de Datos Personales en Posesión de los Particulares. Exige aviso de privacidad, consentimiento (expreso y por escrito para datos sensibles, patrimoniales o financieros), finalidades, derechos ARCO, medidas de seguridad y control de transferencias. La autoridad garante ya no es el INAI (extinto); la función pasó a la Secretaría Anticorrupción y Buen Gobierno.
- **Datos personales sensibles**: salud, origen étnico, creencias, preferencia sexual, datos biométricos, afiliación sindical, entre otros. Requieren consentimiento expreso y medidas de seguridad reforzadas.

## Sector financiero
- **Ley para Regular las Instituciones de Tecnología Financiera (Ley Fintech)** y disposiciones de la CNBV sobre uso de nube y proveedores de cómputo (requieren notificación/autorización y planes de continuidad).
- **Secreto bancario/financiero** (Ley de Instituciones de Crédito): restricciones para compartir información de clientes.
- **PLD/FT (prevención de lavado de dinero)**: conservación de expedientes e identificación de clientes (KYC).

## Salud
- **NOM-004-SSA3-2012** (expediente clínico) y **NOM-024-SSA3-2012** (sistemas de información de registro electrónico para la salud): confidencialidad, integridad y trazabilidad del expediente.

## Fiscal
- **Código Fiscal de la Federación (art. 30)**: conservación de la contabilidad y CFDI por 5 años, generalmente.
- **CFDI 4.0 (SAT)**: los datos fiscales del receptor (RFC, régimen) son datos personales también.

## Laboral
- **Ley Federal del Trabajo**: datos de colaboradores (expedientes, nómina) y monitoreo de empleados con aviso previo.

## Buenas prácticas de IA (no regulación vinculante en México a la fecha)
- Supervisión humana en decisiones que afecten a personas (crédito, contratación, salud).
- Transparencia: avisar cuando el usuario interactúa con una IA.
- Evaluación de sesgos y registro de trazas (trazabilidad).

## Mitigaciones técnicas en Azure que el agente puede proponer
- Residencia de datos: deployments *Data Zone* o regionales, cifrado en reposo con llaves administradas por el cliente (Key Vault).
- Redes privadas (Private Endpoints) y Managed Identity, sin llaves en código.
- Guardrails de Microsoft Foundry: Prompt Shields, filtros de contenido y detección de PII.
- Enmascaramiento o anonimización de PII antes de enviarla a modelos.
- Microsoft Purview para clasificación y linaje de datos.
- Trazabilidad con Application Insights y retención de logs acorde a la política del cliente.
