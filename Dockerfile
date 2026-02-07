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

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY backend/ ./backend/
COPY api/ ./api/
COPY api_v2/ ./api_v2/
COPY blueprints/ ./blueprints/
COPY partners/ ./partners/
COPY worker/ ./worker/

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
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2 --log-level info
