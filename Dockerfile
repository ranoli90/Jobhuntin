# Part 2: Deployment and Runtime Topology
#
# Multi-stage Dockerfile with two targets:
#   docker build --target api -t sorce-api .
#   docker build --target worker -t sorce-worker .
#
# The API image is lightweight (no Playwright).
# The worker image includes Playwright + Chromium.

# ============================================================
# Stage: base – shared Python deps
# ============================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/apps:/app:/app/packages

RUN groupadd -r sorce && useradd -r -g sorce -m sorce

# Install system dependencies for Pillow/OGP (fonts, etc) and Tesseract for OCR
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    fonts-dejavu-core \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy root markers for find_repo_root to correctly identify /app as the root
COPY pyproject.toml render.yaml ./

# Copy application code in dependency order
# Shared packages first (most stable). Use packages/ to preserve packages.backend import path.
COPY shared/ ./shared/
COPY packages/ ./packages/

# Copy root API shim (redirects to apps/api for backward compatibility)
COPY api/ ./api/

# Applications. Use apps/ to preserve apps.api, apps.worker import paths.
COPY apps/ ./apps/

# Templates and config
COPY templates/ ./templates/
COPY infra/ ./infra/

# Remove any .env file that might have been copied and fix ownership (DL3059)
RUN rm -f .env && chown -R sorce:sorce /app

# ============================================================
# Stage: worker – Agent with Playwright + Chromium
# ============================================================
FROM base AS worker

# Install Playwright system deps + browser (DL3013: pin version)
USER root
RUN pip install --no-cache-dir "playwright>=1.43,<2" \
    && python -m playwright install --with-deps chromium

USER sorce

CMD ["python", "-m", "apps.worker.agent"]

# ============================================================
# Stage: api – FastAPI service (no Playwright)
# DEFAULT stage — this is what Render builds
# ============================================================
FROM base AS api

EXPOSE 10000

USER sorce

ENV PORT=10000
ENV PYTHONPATH=/app/apps:/app:/app/packages

# Render handles health checks externally via http request to /health
# We remove the internal Docker HEALTHCHECK to avoid port mismatches
# DL3025: Use exec form; shell needed for $PORT expansion
CMD ["sh", "-c", "cd /app && python -c 'import apps.api.main; print(\"Import successful\")' && uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --log-level debug --timeout-keep-alive 30"]

# HEALTHCHECK for local Docker usage (Render uses external health checks)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1
