# Prompt para un proyecto nuevo: Catálogo de agentes de Readymind presentado por Glitch

> Es un proyecto **independiente** del AI Tour. Antes de abrir la sesión: crear un repo nuevo y vacío en GitHub
> (por ejemplo `fmolina5656/catalogo-agentes`) y abrir la sesión sobre ese repo. Copiar todo lo que está debajo de la
> línea y pegarlo como primer mensaje.

---

Quiero construir desde cero, en este repo vacío, el **Catálogo de agentes de Readymind**: una web pública, presentada
por **Glitch** (la mascota de Readymind), user friendly, responsive para todos los dispositivos y **replicable**, con un
**back de administración** para cargar los agentes en un formato estandarizado, con imágenes.

## Qué es Readymind y quién es Glitch
- **Readymind** es partner de Microsoft y hace proyectos de IA y modernización en Latinoamérica.
- **Glitch** es la mascota: un personaje verde y redondo con un chip en la cabeza. En nuestras webs "habla" con una
  burbuja de texto que se escribe sola, letra por letra, con cursor parpadeante. Al hacer clic en la burbuja, el texto
  se completa. Glitch parpadea cada tantos segundos alternando dos imágenes (ojos abiertos / ojos cerrados) y flota
  suavemente con una animación sutil.
- **Tono de Glitch:** español de México, cercano, concreto y con algo de humor. Nunca de vendedor agresivo.

## Recursos de marca
Los archivos están en el repo `fmolina5656/Aitour`, carpeta `frontend/public/brand/`:
- `glitch-open.webp` (Glitch con los ojos abiertos)
- `glitch-blink.webp` (ojos cerrados, para el parpadeo)
- `readymind-logo-dark.png` (logo para fondo oscuro)
- `readymind-logo.png` (logo para fondo claro)

También está `frontend/public/favicon.svg`. Agrega ese repo a la sesión (solo lectura) y copia esos archivos a este
proyecto. **No copies nada más de ese repo:** es otro proyecto. Como referencia visual de cómo presentamos con Glitch,
puedes mirar `frontend/public/casos/index.html` de ese repo.

- **Paleta:**
  - verde `#66de7f`, teal `#53b6ad`, azul `#397ef6`;
  - degradado de marca `linear-gradient(90deg, #66de7f 0%, #53b6ad 50%, #397ef6 100%)`, para títulos destacados y
    botones primarios con texto oscuro `#04121b`;
  - fondo `#050a12`, tarjetas `#0c1626`, líneas `#1f3150` y `#2a4268`;
  - texto `#f3f6fa` (principal), `#b7c2d2` (secundario) y `#7d8ca2` (terciario);
  - alerta `#ffb547`, error `#ff7a7a`.
- **Estética:** oscura, con "aurora" de color difuminada en el fondo, tarjetas con bordes finos y esquinas de 14–20 px,
  y sombras suaves.
- **Tipografía:** Satoshi (Fontshare, pesos 400/500/700/900), con `Segoe UI` y `system-ui` de respaldo, y una mono
  (Cascadia Mono o Consolas) para los rótulos chicos en mayúsculas.
- **Colores por familia** (proponer otra combinación si queda mejor): App Modernization en azul, Microsoft 365 Copilot
  en teal y Copilot Studio en verde. Dentro de App Modernization, una etiqueta visible distingue "Agente con Foundry"
  de "Modernización".

## Contenido del catálogo
Dos familias de agentes:
1. **App Modernization (pro-code).** Es la familia **más importante y crítica** del catálogo. Abarca dos líneas, y las
   dos tienen que lucirse por igual:
   - **Agentes de IA a medida con Microsoft Foundry.** Es el corazón de la familia. Son agentes construidos con código
     sobre:
     - Foundry Agent Service y Microsoft Agent Framework (un agente solo o varios que colaboran entre sí);
     - modelos del catálogo de Foundry (GPT y otros);
     - conocimiento con Azure AI Search / Foundry IQ;
     - herramientas como Document Intelligence, Content Understanding, Vision y agentes de voz;
     - guardrails (Content Safety, Prompt Shields), evaluaciones y observabilidad con Application Insights;
     - integración con los sistemas del cliente (SAP, ERP, CRM, Teams, APIs).

     Ejemplos reales de Readymind, que hay que cargar **sin nombres de clientes**:

     | Agente | Qué hace | Piezas | Dato |
     |---|---|---|---|
     | Conciliación contable | Extractos PDF de 9 brokers a Excel para SAP HANA | Document Intelligence, GPT-4o, .NET, Cosmos DB | 10 semanas |
     | Planes de mantenimiento industrial | De manuales técnicos multiidioma al plan preventivo y los repuestos para SAP | Foundry, Document Intelligence, App Service | 13 semanas |
     | Visión en tiendas | Filas, atención y permanencia con las cámaras existentes | Azure AI Vision | 12 semanas |
     | API documental de trámites | Enruta cada documento a Document Intelligence prebuilt, Content Understanding o GPT-4o | .NET, 15 endpoints | 10 semanas |
     | Triage de alertas de seguridad | Clasifica alertas y escala lo crítico a Teams | GPT-4o, Python | 9 semanas |
     | Equipo de agentes que diseña soluciones | Recepcionista de voz y 5 agentes que debaten | Microsoft Agent Framework, gpt-5.4, Prompt Shields, Container Apps | Demo del AI Tour |

   - **Modernización de aplicaciones con IA.** Por ejemplo:
     - evaluación del portafolio;
     - migración de .NET Framework a .NET moderno y de versiones de Java con GitHub Copilot app modernization;
     - contenedorización hacia Azure Container Apps o AKS;
     - documentación de código legado y generación de pruebas;
     - migración de bases de datos a Azure SQL.
2. **Low code**, dividida en:
   - **Microsoft 365 Copilot:** agentes declarativos y escenarios dentro de Teams, Outlook, Word y Excel.
   - **Copilot Studio:** agentes de help desk de TI, RR. HH., onboarding, ventas o atención a clientes, con conectores
     y Power Automate.

## Lo que tiene que hacer

### 1. Catálogo público
- **Portada con Glitch.** Glitch presenta el catálogo en 2–3 frases y hay accesos rápidos a cada familia.
- **Filtros.** Chips de familia (con un subfiltro "Agentes con Foundry" / "Modernización" dentro de App
  Modernization), plataforma, industria y nivel de madurez (demo, piloto, en producción), más un buscador por texto.
  Los filtros se reflejan en la URL para poder compartir una vista filtrada.
- **Tarjetas.** Imagen, nombre, familia (con su color), una línea de valor y 2–3 etiquetas.
- **Detalle del agente** (URL propia, compartible):
  - Glitch lo presenta con su frase.
  - Problema → qué hace → cómo funciona (pasos numerados) → beneficios.
  - Tecnologías, integraciones, requisitos y licencias, seguridad y gobierno, y tiempo estimado de implementación.
  - Si la ficha tiene `arquitectura`, se muestra un **diagrama de arquitectura** generado desde esos datos:
    - columnas de entrada → IA → código → salida, con un color por tipo de pieza;
    - un recorrido paso a paso que se avanza con clic;
    - una ficha con el detalle al tocar cada pieza.
    En el back se carga con un editor simple de componentes y conexiones, con vista previa en vivo.
  - Galería de imágenes y un QR para abrirlo en el celular.
  - Botón de contacto (CTA).
- **Modo presentación.** Pantalla completa para una TV o tablet. Avanza **solo con clic, flechas o control remoto de
  presentaciones**: nada pasa solo.
- **Responsive real:** celular (390 px), tablet vertical y horizontal (820 / 1180 px), notebook y monitor (1600 px o
  más), sin scroll horizontal.
- **Accesible:** contraste AA, foco visible, textos alternativos, navegación con teclado y respeto de
  `prefers-reduced-motion`.

### 2. Back de administración
- **Acceso solo para el equipo.** De preferencia con **Microsoft Entra ID** (la autenticación integrada de Azure
  Container Apps, limitada a los usuarios de Readymind). Además, una variable `ADMIN_PIN` como alternativa para correrlo
  en local. Proponer cuál conviene.
- **Lista de agentes.** Con estado borrador/publicado, destacado, orden (subir y bajar), duplicar (para replicar uno
  rápido) y borrar con confirmación.
- **Formulario estandarizado.** Validado en el front y en el back, con **vista previa en vivo** de la tarjeta y del
  detalle tal como se verán publicados. Campos de lista (pasos, beneficios, tecnologías) editables, para agregar,
  quitar y reordenar.
- **Carga de imágenes.** Arrastrar y soltar o elegir archivo, también desde la cámara del celular. Solo JPG, PNG o WebP,
  hasta 8 MB:
  - en el servidor se valida que realmente sea una imagen;
  - se le quitan los metadatos (EXIF);
  - se reduce a 1600 px y se guarda como WebP, más una miniatura de 600 px.
  - Cada imagen lleva **texto alternativo** y una **etiqueta obligatoria**: "Captura real", "Captura anonimizada",
    "Imagen ilustrativa (IA)" o "Diagrama". La etiqueta se muestra sobre la imagen en el catálogo.
- **Exportar e importar** todo el catálogo en un JSON, con las imágenes empaquetadas en un ZIP, para copiarlo a otro
  entorno.

### 3. Estandarización (lo que lo hace replicable)
- Un **esquema único de ficha**, definido una sola vez (modelo Pydantic o equivalente) y documentado en el README.
  Campos mínimos:

  | Grupo | Campos |
  |---|---|
  | Identificación | `slug`, `nombre`, `familia`, `subfamilia`, `tagline` |
  | Narrativa | `glitch_dice` (la frase con la que Glitch lo presenta), `problema`, `que_hace`, `pasos[]` |
  | Público | `para_quien` (roles), `industrias[]` |
  | Valor | `beneficios[]`, cada uno con `{texto, tipo: "medido" \| "estimado"}` |
  | Técnica | `plataforma` (Microsoft Foundry, GitHub Copilot, M365 Copilot o Copilot Studio), `tecnologias[]`, `integraciones[]`, `requisitos_licencias`, `seguridad_gobierno` |
  | IA (para los agentes de Foundry) | `modelos[]`, `tipo_agente` (uno solo / varios que colaboran), `conocimiento[]` (fuentes y búsqueda), `herramientas[]`, `guardrails[]`, `evaluacion_observabilidad` |
  | Arquitectura (opcional, muy recomendada en pro-code) | `arquitectura`: `{componentes: [{id, nombre, tipo: entrada \| ia \| codigo \| datos \| salida \| persona \| seguridad, detalle}], conexiones: [[desde, hasta]], pasos: [{texto, componentes[]}]}` |
  | Entrega | `tiempo_implementacion`, `madurez`, `demo_url` (opcional) |
  | Imágenes | `imagenes[]`, cada una con `{archivo, alt, etiqueta}` |
  | Publicación | `cta`, `estado`, `orden`, `destacado`, `creado`, `actualizado`, `actualizado_por` |

- **Marca en un solo archivo de configuración:** nombre del catálogo, paleta, logo, textos de Glitch de la portada,
  familias y sus colores, y datos de contacto. Replicar el catálogo para otra unidad, evento o cliente tiene que ser
  cambiar ese archivo y cargar otros agentes.
- **Semilla.**
  - Los **6 agentes de Foundry** de la tabla de arriba, con su arquitectura cargada.
  - **2 o 3 ejemplos** de modernización, M365 Copilot y Copilot Studio.
  - Los ejemplos inventados llevan un aviso visible "Ejemplo: validar con el equipo" hasta que alguien los edite. Los
    6 de Foundry son proyectos reales: no llevan ese aviso, pero sí la madurez y el tiempo de implementación.

## Stack sugerido (proponer cambios si hay algo mejor)
- **Backend:** Python 3.12 + FastAPI + Pydantic, con Pillow para las imágenes.
- **Frontend:** React + Vite + TypeScript, servido por el mismo contenedor.
- **Infraestructura en Azure:**
  - Azure Container Apps;
  - Azure Blob Storage para las imágenes y el JSON del catálogo, con control de concurrencia por ETag para que dos
    personas editando no se pisen;
  - identidad administrada (sin llaves en el código);
  - Application Insights.
  - Todo en Bicep, desplegable con `azd up` la primera vez y `azd deploy` después, con build remoto en Azure Container
    Registry (sin Docker local).
- **Desarrollo local sin Azure:** guardar en disco, con `npm run dev` + `uvicorn` y un README claro.

## Reglas que no se negocian
- **Sin nombres de clientes** en textos, imágenes ni ejemplos. Si una captura los tiene, se anonimiza antes de cargarla.
- **Honestidad.** Imagen generada con IA = "Imagen ilustrativa (IA)". Cifras no medidas = "estimado".
- **Lo público solo ve lo publicado.** El API público nunca expone borradores ni datos del back.
- **Seguridad de la carga de archivos:**
  - nombres de archivo generados por el servidor, nunca el del usuario;
  - sin path traversal;
  - límite de tamaño;
  - validación del contenido real.

## Cómo trabajar
1. **Primero un plan corto para que lo apruebe:**
   - estructura del repo;
   - esquema de la ficha;
   - rutas del API;
   - pantallas, con un boceto en texto de cada una;
   - decisión de autenticación y de almacenamiento.
2. **Después construir por etapas, mostrándome capturas en cada una:**
   1. el esquema y el API con sus pruebas;
   2. el catálogo público;
   3. el back;
   4. la infraestructura y el despliegue.
3. **Pruebas:**
   - automáticas del API: acceso, validación, imágenes válidas e inválidas, export/import, y que lo no publicado no se
     vea;
   - capturas con Playwright en 390, 820, 1180 y 1600 px para revisar el diseño.
4. **Al final:**
   - README con cómo correrlo en local, cómo desplegarlo en Azure (con los comandos para Windows cmd) y cómo replicarlo
     para otro catálogo;
   - commit y push.
