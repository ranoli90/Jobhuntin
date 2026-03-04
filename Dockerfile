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
    PYTHONUNBUFFERED=1

RUN groupadd -r sorce && useradd -r -g sorce -m sorce

# Install system dependencies for Pillow/OGP (fonts, etc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code in dependency order
# Shared packages first (most stable)
COPY packages/ ./packages/
# Also copy to root level for backward compatibility
COPY packages/shared/ ./shared/
COPY packages/backend/ ./backend/
COPY packages/blueprints/ ./blueprints/
COPY packages/partners/ ./partners/

# Applications
COPY apps/api/ ./api/
COPY apps/api_v2/ ./api_v2/
COPY apps/worker/ ./worker/

# Templates and config
COPY templates/ ./templates/
COPY infra/ ./infra/

# Remove any .env file that might have been copied
RUN rm -f .env

RUN chown -R sorce:sorce /app

# ============================================================
# Stage: worker – Agent with Playwright + Chromium
# ============================================================
FROM base AS worker

# Install Playwright system deps + browser
USER root
RUN pip install --no-cache-dir playwright \
    && python -m playwright install --with-deps chromium

USER sorce

CMD ["python", "-m", "worker.agent"]

# ============================================================
# Stage: api – FastAPI service (no Playwright)
# DEFAULT stage — this is what Render builds
# ============================================================
FROM base AS api

EXPOSE 8000

USER sorce

ENV PORT=8000

# Render handles health checks externally via http request to /health
# We remove the internal Docker HEALTHCHECK to avoid port mismatches
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2 --log-level info

# HEALTHCHECK for local Docker usage (Render uses external health checks)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
