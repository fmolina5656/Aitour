# Prompt para la nueva sesión: Catálogo de agentes presentado por Glitch

> Copiar todo lo que está debajo de la línea y pegarlo como primer mensaje de la sesión nueva.

---

Trabajamos en el repo `fmolina5656/Aitour`, rama `claude/readymind-aitour-demo`. Es la demo del stand de Readymind
para el Microsoft AI Tour México: backend FastAPI (`backend/app`) y frontend React/Vite con páginas estáticas en
`frontend/public/*/index.html`. Corre en Azure Container Apps (1 réplica), con un volumen de Azure Files montado en
`/data` (`DATA_DIR`), y se despliega con `azd deploy` (build remoto en ACR). Antes de empezar, lee el `README.md` y mira
`frontend/public/casos/index.html`, `frontend/public/arquitectura/index.html`, `frontend/public/vendedor/` y
`backend/app/seller.py`. Son la referencia de estilo, de cómo habla Glitch y de cómo protegemos un back con PIN.

## El desafío

Crear un **catálogo de agentes de Readymind**, presentado por **Glitch** (nuestra mascota), user friendly, responsive
para todos los dispositivos y **replicable**. Tiene dos familias:

1. **App Modernization**: agentes que modernizan aplicaciones. Por ejemplo, evaluación del portafolio, migración de
   .NET Framework a .NET moderno y de Java, contenedorización hacia Azure Container Apps o AKS, documentación de código
   legado, generación de pruebas, migración de bases de datos a Azure SQL, y uso de GitHub Copilot app modernization.
2. **Low code**: dividida en **Microsoft 365 Copilot** (agentes declarativos, prompts y flujos dentro de M365) y
   **Copilot Studio** (por ejemplo, help desk de TI, RR. HH., onboarding, ventas o atención a clientes, con conectores y
   Power Automate).

Tiene que tener un **back (panel de administración)** donde el equipo cargue agentes nuevos con un **formato
estandarizado**, incluyendo **imágenes**.

## Lo que quiero ver funcionando

### 1. Catálogo público: `/catalogo`
- **Entrada con Glitch.** Glitch presenta el catálogo con su burbuja de texto que se escribe sola, la misma mecánica que
  /casos.
- **Filtros.** Chips de familia (App Modernization, M365 Copilot, Copilot Studio), industria, nivel de madurez
  (demo, piloto, en producción) y un buscador por texto.
- **Tarjetas.** Imagen, nombre, familia, una línea de valor y 2–3 etiquetas.
- **Detalle de cada agente** (`/catalogo/#<slug>`, que se pueda compartir):
  - Glitch lo presenta con su propia frase.
  - Problema → qué hace → cómo funciona (pasos) → beneficios.
  - Tecnologías, requisitos y licencias, integraciones, seguridad y gobierno.
  - Tiempo estimado de implementación.
  - Galería de imágenes y un QR para abrirlo en el celular (ya existe `/api/qr-link.svg`).
- **Modo stand.** Pantalla completa en una tablet o TV que se navega **solo con clic o con las flechas**: nada pasa solo.
- **Responsive.** Probado en celular (390 px), tablet vertical y horizontal (820 / 1180 px) y PC (1600 px), sin scroll
  horizontal.
- **Accesibilidad.** Contraste correcto, foco visible, textos alternativos y que funcione con teclado.

### 2. Back: `/catalogo/admin`
- **Protección.** PIN del equipo en `CATALOG_ADMIN_PIN`, con el mismo patrón que `SELLER_PIN`:
  - sin PIN configurado responde 503;
  - compara con `hmac.compare_digest`;
  - bloquea tras varios intentos fallidos.
- **Lista de agentes.** Con estado borrador/publicado, orden (subir y bajar), destacado, duplicar (para replicar uno
  rápido) y borrar con confirmación.
- **Formulario estandarizado.** Validado en el front y en el back (Pydantic), con **vista previa en vivo** de la tarjeta
  y del detalle tal como se verán.
- **Carga de imágenes.** Arrastrar y soltar o elegir archivo, también desde la cámara del celular. Solo JPG, PNG o WebP,
  hasta 8 MB:
  - en el back se valida que realmente sea una imagen;
  - se le quitan los metadatos (EXIF);
  - se reduce a 1600 px y se guarda como WebP, más una miniatura de 600 px.
  - Cada imagen lleva una **etiqueta obligatoria**: "Captura real", "Captura anonimizada", "Imagen ilustrativa (IA)" o
    "Diagrama".
- **Exportar e importar** todo el catálogo en JSON, para copiarlo a otro entorno o a otro evento.

### 3. Estandarización (el corazón de "replicable")
- Un **esquema único** de ficha de agente, en un modelo Pydantic y documentado. Campos mínimos:

  | Grupo | Campos |
  |---|---|
  | Identificación | `slug`, `nombre`, `familia`, `subfamilia`, `tagline` |
  | Narrativa | `glitch_dice` (la frase de Glitch), `problema`, `que_hace`, `pasos[]` |
  | Público | `para_quien` (roles), `industrias[]` |
  | Valor | `beneficios[]`, cada uno con `{texto, tipo: medido \| estimado}` |
  | Técnica | `tecnologias[]`, `integraciones[]`, `requisitos_licencias`, `seguridad_gobierno` |
  | Entrega | `tiempo_implementacion`, `madurez`, `demo_url` (opcional) |
  | Imágenes | `imagenes[]`, cada una con `{archivo, alt, etiqueta}` |
  | Publicación | `cta`, `estado`, `orden`, `destacado`, `actualizado` |

- **Datos.** Se guardan en `/data/catalogo/agentes.json` con escritura atómica y copia de respaldo en cada cambio. Las
  imágenes van en `/data/catalogo/img/`. Así sobreviven a los redeploys.
- **Plantilla y semilla.** Una plantilla vacía y un archivo semilla con **3 agentes de ejemplo por familia**, marcados
  claramente como ejemplos a validar.
- **Marca configurable.** Todo lo de marca (paleta, logo, textos de Glitch y nombre del catálogo) sale de un solo lugar,
  para replicar el catálogo para otro evento o cliente cambiando solo eso.

## Marca y estilo (respetar)
- **Paleta:**
  - verde `#66de7f`, teal `#53b6ad`, azul `#397ef6`;
  - degradado `linear-gradient(90deg, #66de7f, #53b6ad, #397ef6)`;
  - fondo `#050a12`, tarjetas `#0c1626`, líneas `#1f3150` y `#2a4268`;
  - texto `#f3f6fa`, `#b7c2d2` y `#7d8ca2`;
  - alerta `#ffb547`.
  - Color por familia: App Modernization en azul, M365 Copilot en teal y Copilot Studio en verde, o proponer otra
    combinación coherente.
- **Tipografía:** Satoshi (Fontshare), mono para los rótulos.
- **Glitch y logo:** `/brand/glitch-open.webp` y `/brand/glitch-blink.webp` (parpadeo), y el logo
  `/brand/readymind-logo-dark.png`.
- **Tono:** español de México, cercano y concreto, como en /casos y /story.

## Reglas que no se negocian
- **Sin nombres de clientes** en textos, imágenes ni ejemplos. Si una captura los tiene, se anonimiza.
- **Etiquetas honestas.** Imagen generada con IA = "Imagen ilustrativa (IA)". Cifras no medidas = "estimado".
- **Las páginas públicas no exponen datos del back:** solo agentes publicados.
- **Seguridad de la carga de archivos.** Nombres de archivo generados por el servidor (nunca el del usuario), sin path
  traversal y con límite de tamaño.
- **Dependencias nuevas.** Se pueden agregar (`Pillow` para las imágenes y `python-multipart` para la carga) en
  `backend/pyproject.toml`, verificando que el `Dockerfile` las instale.

## Cómo trabajar
1. **Primero un plan corto:** el esquema de la ficha, las rutas del API, las pantallas y el estilo. Que se pueda
   aprobar antes de construir.
2. **Mientras construyes:**
   - pruebas con pytest para el API: PIN, validación, carga de imágenes válidas e inválidas, export/import, y que lo no
     publicado no se vea;
   - capturas con Playwright en 390, 820, 1180 y 1600 px para revisar el diseño;
   - Chromium ya está instalado en `/opt/pw-browsers`.
3. **Integración con el resto de la demo:**
   - una tarjeta del catálogo en `/accesos`;
   - un link desde `/vendedor` (pestaña Foundry) y desde `/casos`;
   - la variable `CATALOG_ADMIN_PIN` en `.env.example`, en la infraestructura (`infra/`, como secreto opcional, igual
     que `SELLER_PIN`) y en el README.
4. **Al final:**
   - commit y push a `claude/readymind-aitour-demo`;
   - decirme exactamente cómo cargar el PIN en Azure sin redeploy (`az containerapp update ... --set-env-vars`) y luego
     `git pull` + `azd deploy`.
