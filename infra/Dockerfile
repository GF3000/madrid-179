# Imagen de producción de Madrid 179: API FastAPI + app React compilada + prototipo, en un solo contenedor.
# El modelo se entrena y se prueba DENTRO del build (Linux): si los tests fallan, no hay imagen.
#
# Construir desde la raíz del repo:
#   docker build -f infra/Dockerfile --build-arg COMMIT=$(git rev-parse --short HEAD) -t madrid179 .
#   docker run --rm -p 8080:8080 madrid179        → http://localhost:8080
# Cloud Run inyecta PORT; la clave del asistente llega como variable de entorno (Secret Manager).

# --- 1. App React (MapLibre + deck.gl) ---
FROM node:22-slim AS app
WORKDIR /src/frontend/app
COPY frontend/app/package.json frontend/app/package-lock.json ./
RUN npm ci
COPY frontend/app/ ./
RUN npm run build

# --- 2. Base Python con las dependencias de la API ---
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/srv/backend
WORKDIR /srv
COPY backend/requirements-api.txt backend/
RUN pip install -r backend/requirements-api.txt
# madrid179 va por PYTHONPATH (no instalado): config.RAIZ se calcula desde la ruta del paquete y debe ser /srv
COPY backend/madrid179 backend/madrid179
COPY backend/api backend/api

# --- 3. Entrenar el artefacto y pasar los tests (equivalencia con los CSV versionados, preferencias, API) ---
FROM base AS modelo
ARG COMMIT=sin-git
ENV MADRID179_COMMIT=${COMMIT}
RUN pip install pytest==9.1.1
COPY backend/pyproject.toml backend/
COPY backend/pipeline/entrenar.py backend/pipeline/
COPY backend/tests backend/tests
COPY data/processed data/processed
# El GA²M se reentrena en otra máquina que las salidas versionadas: CI=1 activa la tolerancia al ruido de coma
# flotante de test_equivalencia.py (sin ella la comparación es exacta y falla o pasa según el procesador)
RUN python backend/pipeline/entrenar.py && CI=1 python -m pytest backend/tests -q -p no:cacheprovider

# --- 4. Imagen final: solo lo que sirve la API ---
FROM base
COPY data/processed/dataset_bn_municipios.csv data/processed/municipios.geojson \
     data/processed/wikipedia_municipios.json data/processed/ayudas_oficiales.csv \
     data/processed/convocatorias_abiertas.csv data/processed/
COPY --from=modelo /srv/data/processed/modelo.joblib data/processed/
COPY frontend/prototipo frontend/prototipo
COPY --from=app /src/frontend/app/dist frontend/app/dist
RUN useradd --system --no-create-home madrid179
USER madrid179
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn api.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
