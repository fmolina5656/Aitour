# Impacto y ROI de los casos de éxito: qué datos pedir

En `/casos`, cada caso tiene la tarjeta **📊 Impacto medible**. Cuando se cargan los datos de esta planilla, aparece
el botón **💰 Ver ROI y business case**, que calcula solo:
- el % de tiempo ahorrado;
- las horas liberadas y su equivalente en personas;
- el ahorro neto mensual;
- la recuperación de la inversión;
- el ROI a 12 meses y a 3 años.

Los datos se cargan en el bloque `IMPACTO`, al final de `frontend/public/casos/index.html`. Para ver el diseño con
datos **ficticios**, abre `/casos/?borrador`.

## Estado

| Caso | Business case |
|---|---|
| 1 · FinancialOCR | ✅ Cargado como **escenario ilustrativo** (24/11/2026), no validado por el cliente |
| 2 · Smart Maintenance | Pendiente |
| 3 · Store Intelligence | Pendiente |
| 4 · API documental | ✅ Cargado como **escenario ilustrativo** (24/11/2026), no validado por el cliente |
| 5 · SOC Classifier | Pendiente |

Un escenario ilustrativo (`ilustrativo: true`) se muestra con un aviso visible de que los datos son supuestos de
Readymind. Cuando el cliente valide los números, cambiar a `t: 'medido'`, quitar `ilustrativo` y actualizar la fuente.

## Reglas
- **Sin datos que identifiquen al cliente:** ni nombre, ni volúmenes que lo delaten si son muy conocidos.
- **Etiqueta de cada cifra.** "Medido" = sale de un registro del proyecto (sistema, reporte, acta). "Estimado" = un
  supuesto razonable acordado con el responsable. En la página, lo estimado se marca solo.
- **Todo en USD**, por mes, con los costos del cliente al momento del proyecto.
- **Mejor conservador que inflado:** en una feria alguien va a preguntar "¿de dónde sale ese número?".

## Los 9 datos por caso (iguales para los 5)

| # | Dato | Pregunta para el responsable del proyecto | ¿Medido o estimado? |
|---|---|---|---|
| 1 | Unidad | ¿Qué se procesa? (extractos, planes, trámites, alertas…) | — |
| 2 | Volumen por mes | ¿Cuántas de esas unidades por mes? | |
| 3 | Minutos por unidad **antes** | ¿Cuánto tardaba una persona en procesar una unidad a mano? | |
| 4 | Minutos por unidad **después** | ¿Cuánto tarda hoy una persona (revisar, aprobar, corregir)? | |
| 5 | Costo por hora | Costo cargado de una hora de esa persona (sueldo + cargas) | |
| 6 | Otros ahorros por mes | Errores o retrabajo evitados, multas, horas extra, tercerización (USD/mes) | |
| 7 | Inversión | Costo total de la implementación (una vez, USD) | |
| 8 | Operación por mes | Azure + licencias + soporte (USD/mes) | |
| 9 | Fuente y fecha | ¿De dónde salen los datos? (reporte, sistema, entrevista) y fecha | — |

**Cómo se calcula:**
- Horas liberadas por mes = volumen × (minutos antes − minutos después) ÷ 60
- Equivalente en personas = horas ÷ 160
- Ahorro neto por mes = horas × costo por hora + otros ahorros − operación
- Recuperación (meses) = inversión ÷ ahorro neto por mes
- ROI a N meses = (ahorro neto × N − inversión) ÷ inversión

## Qué ya está publicado (no hace falta pedirlo)

| Caso | Cifras que ya muestra la página |
|---|---|
| 1 · FinancialOCR | 9 brokers · 0 errores de ingreso · de horas a minutos por cierre · 10 semanas |
| 2 · Smart Maintenance | 10–30 s por plan (antes, semanas por equipo) · 15 tareas por plan · 13 semanas |
| 3 · Store Intelligence | Medición en tiempo real · cámaras existentes · 12 semanas |
| 4 · API documental | 3–15 documentos por trámite · 5 tipos de documento · 0 carga manual · 10 semanas |
| 5 · SOC Classifier | De horas a segundos por alerta · 0 alertas graves sin atender · 9 semanas |

## Preguntas puntuales por caso (además de los 9 datos)

1. **FinancialOCR:** ¿cuántos extractos por cierre y cuántos cierres por mes? ¿Cuántas horas de una persona llevaba
   cada cierre? ¿Hubo errores de importes o signos que costaran algo (ajustes, auditoría)?
2. **Smart Maintenance:** ¿cuántos equipos o manuales se procesaron? ¿Cuántas horas de un técnico o ingeniero llevaba
   armar un plan a mano? ¿Se evitó alguna parada no planificada? ¿Cuánto cuesta una hora de parada?
3. **Store Intelligence:** ¿cuántas tiendas y cámaras? ¿Cuánto bajó el tiempo de espera en caja? ¿Hubo efecto en
   ventas, conversión o abandono de fila? ¿Se reasignó personal entre turnos? Si no hay ahorro de horas directo, usar
   **otros ahorros** (ventas recuperadas, horas de staffing mejor asignadas).
4. **API documental:** ¿cuántos trámites por mes y cuántos documentos en promedio? ¿Cuántos minutos llevaba cargar un
   trámite a mano? ¿Cuántos errores de identidad había y cuánto costaba corregirlos?
5. **SOC Classifier:** ¿cuántas alertas por día? ¿Cuántos minutos llevaba leer y clasificar una? ¿Qué porcentaje son
   falsos positivos que ahora se filtran solos? ¿Cuánto bajó el tiempo de respuesta a lo crítico?

## Ejemplo de cómo queda cargado (con datos ficticios)

```js
c4: { semanas: 10, kpis: [...], roi: {
  unidad: 'trámites', volumen_mes: 1200, min_antes: 25, min_despues: 4, costo_hora_usd: 12,
  otros_ahorros_mes_usd: 800, inversion_usd: 45000, costo_mensual_usd: 900,
  fuente: 'Reporte de operación del cliente, 3 meses posteriores a la salida a producción', fecha: 'mayo 2026', t: 'medido' } },
```
