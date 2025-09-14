# syntax=docker/dockerfile:1

# --- Builder stage ---
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt README.md /app/
COPY aegis /app/aegis

RUN python -m pip install --upgrade pip setuptools wheel && \
    pip wheel --wheel-dir /wheels -r requirements.txt && \
    pip wheel --wheel-dir /wheels -e .

# --- Runtime stage ---
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Create non-root user
RUN useradd -u 10001 -m appuser && mkdir -p /app && chown -R appuser:appuser /app

COPY --from=builder /wheels /wheels
RUN python -m pip install --upgrade pip && \
    pip install --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

COPY --chown=appuser:appuser aegis /app/aegis
COPY --chown=appuser:appuser README.md /app/README.md

USER 10001

EXPOSE 8000

# Gunicorn with Uvicorn workers for prod
ENV GUNICORN_WORKERS=2 \
    GUNICORN_BIND=0.0.0.0:8000 \
    GUNICORN_TIMEOUT=60

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys,urllib.request;\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\ntry:\n    r=urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)\n    sys.exit(0 if r.status==200 else 1)\nexcept Exception:\n    sys.exit(1)"]

CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w ${GUNICORN_WORKERS:-2} -b ${GUNICORN_BIND:-0.0.0.0:8000} --timeout ${GUNICORN_TIMEOUT:-60} aegis.api:app"]
