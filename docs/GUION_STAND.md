# Guion de 5 minutos · para quien atiende el stand

> Objetivo: que el visitante viva la demo **con su propio problema** y se vaya con un PDF y una conversación comercial
> abierta. Tú guías; la pantalla hace el trabajo.
>
> Para aprenderlo de forma visual, el mismo recorrido contado por Glitch está en `https://<app>/story`
> (flechas para avanzar, `A` para modo automático, `F` pantalla completa).
>
> Para mostrar experiencia real: `https://<app>/casos` tiene 5 proyectos de Readymind en producción (FinancialOCR,
> Smart Maintenance, Store Intelligence, la API documental de pensiones y SOC Classifier), con una muestra animada de
> cada solución. Sirve en una tablet en modo automático o para responder "¿y esto ya lo hicieron en algún lado?".
> **No se nombran clientes:** si preguntan, se habla de la industria y el país.
>
> Para que el visitante lo pruebe con sus manos: `https://<app>/ocr`. Dale una hoja del **kit de muestras** impreso
> (`/ocr/muestras`), que la ponga frente a la cámara y toque «Leer documento». La **factura B** tiene un error a propósito:
> *"Mira, se dio cuenta de que el total no cuadra"*. Si alguien quiere usar un documento propio, se puede: la imagen
> no se guarda y los datos personales salen ocultos, pero ofrece primero las muestras.
>
> **El stand se mide a sí mismo:** `https://<app>/vision` en la tablet del trípode. Señala el monitor: *"Esto es lo
> mismo que hicimos en tiendas de moda: con una cámara contamos cuánta gente hay, cuánto se queda y cuánto espera en la
> fila. No grabamos ni reconocemos caras: solo números."* Teclas: **Z** zonas, **H** mapa de calor, **F** pantalla completa,
> **D** diagnóstico (lo que ve el modelo y su confianza), **+ / −** umbral, **G** probar GPU o CPU.
>
> **Para un prospecto industrial:** `https://<app>/mantenimiento` muestra la plataforma real de Smart Maintenance en 6
> pasos, con capturas de producción: *"Esto no es un prototipo: así se ve la herramienta que usa hoy el equipo de
> mantenimiento"*. Sin nombrar al cliente: energía, Argentina.

## 0:00 – 0:30 · Enganche

> "¿Tienes algún proceso en tu empresa que sea lento, manual o caro? Cuéntaselo a nuestra recepcionista de IA y en tres
> minutos un equipo de agentes te arma la solución en Azure, con costo y riesgos incluidos."

- Presiona **V** (o el botón "Háblame de tu problema") y acerca el micrófono al visitante.
- Si se pone nervioso, ofrécele ejemplos: facturas, call center, expedientes, reportes, inventario.

## 0:30 – 1:30 · La entrevista (la recepcionista lleva la conversación)

- La recepcionista hace como máximo 3 preguntas: industria, volumen y datos disponibles.
- Señala la pantalla: *"Mira, el núcleo del centro reacciona a tu voz; a la derecha va la transcripción."*
- Si el ruido no deja escuchar: **T** y que el visitante teclee.
- Cuando aparezca **"Esto entendí"**, que lo confirme diciendo "sí" o con **Enter**.

## 1:30 – 3:00 · El equipo de agentes (el momento "wow")

Narra mientras pasa, señalando la escena:

1. *"Primero valida la seguridad: Prompt Shields revisa que no sea un ataque y que sea un tema de negocio"* (panel de
   gobierno, abajo a la derecha).
2. *"El **Arquitecto** propone una solución en Microsoft Foundry"* (orbe azul; abajo se arma la arquitectura por capas).
3. *"Ahora el **Financiero** revisa el costo… y **lo objeta**"* (cometa ámbar de regreso al Arquitecto): *"dice que el
   modelo premium es demasiado caro para clasificar."*
4. *"El Arquitecto **ajusta**: cambia a un modelo mini y el costo baja"* (abajo aparece "CAMBIÓ" y el nuevo total).
5. *"**Riesgo** detecta datos personales y cita la LFPDPPP: pide enmascarar PII"* → el Arquitecto agrega los controles
   (aparecen como "NUEVO").
6. *"El **Redactor** consolida todo en un one-pager ejecutivo."*

Datos para mencionar si preguntan:
- Son agentes reales coordinados con **Microsoft Agent Framework**, con modelos desplegados en **Microsoft Foundry**.
- Cada llamada queda trazada con **OpenTelemetry**: modelo, tokens, latencia y costo. *"Este análisis completo costó
  menos de 5 centavos de dólar."*
- Los costos los calcula una tabla de precios, no el modelo: no hay números inventados. Son estimaciones referenciales.

## 3:00 – 4:00 · Cierre y lead

> "Listo: este es tu one-pager. Escanea el QR, deja tu nombre y correo, y te lo mandamos en PDF."

- El visitante escanea el QR con su celular, acepta el aviso de privacidad y lo recibe.
- En la pantalla aparece "✓ ¡Recibido!" (sin mostrar sus datos).
- Sin QR: **O** para ver el one-pager y que le saque una foto.

## 4:00 – 5:00 · Conversación comercial

> "Esto lo armamos en tres minutos. En un taller de dos horas lo aterrizamos con tus datos reales, y en un piloto de
> cuatro semanas lo ves funcionando."

- Agenda el taller o toma la tarjeta.
- Presiona **R** para dejar la pantalla lista para el siguiente visitante.

## Si alguien intenta "romperla" (también es parte del show)

> "Adelante, intenta pedirle algo fuera de lugar o que ignore sus reglas."

- La pantalla bloquea la solicitud en ámbar ("Solicitud bloqueada · Prompt Shields"), responde con amabilidad y el
  panel muestra **0 llamadas a modelos**: el ataque nunca llegó al modelo.
- *"Esto es gobierno de IA en la práctica: guardrails de Microsoft Foundry y trazabilidad de cada decisión."*

## Si algo falla

| Pasa esto | Haz esto | Y dices |
|---|---|---|
| La voz no entiende | **T** para teclear | "Hay mucho ruido; escribámoslo." |
| Se cae la red | **P** (sesión grabada) | "Te muestro una sesión real que corrimos hoy." |
| Se traba | **R** y reiniciar | — |
