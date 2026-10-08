# Imagen única del stand: frontend compilado + backend FastAPI + Chromium (PDF del one-pager).
# Se despliega en Azure Container Apps con Managed Identity (ver infra/).

# --- 1) Frontend --------------------------------------------------------------------------
FROM node:22-slim AS web
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- 2) Backend -----------------------------------------------------------------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    DATA_DIR=/data RECORDINGS_DIR=/data/recordings
WORKDIR /app/backend
COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY backend/scripts ./scripts
COPY backend/pricing ./pricing
COPY backend/knowledge ./knowledge
COPY backend/seed ./seed
RUN pip install . \
 && python -m playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/*
COPY --from=web /src/frontend/dist /app/frontend/dist

# Una sola réplica: el bus de eventos y la sesión del stand viven en memoria.
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
