# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.14-slim
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.8.5
FROM ${UV_IMAGE} AS uv
FROM ${PYTHON_IMAGE} AS builder
COPY --from=uv /uv /bin/uv
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv UV_LINK_MODE=copy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-libmysqlclient-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM ${PYTHON_IMAGE} AS runtime-base
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MALLOC_ARENA_MAX=2 \
    PATH="/app/.venv/bin:$PATH" STATIC_ROOT=/app/staticfiles MEDIA_ROOT=/media_cdn TZ=Asia/Kolkata

FROM runtime-base AS assets
COPY --from=builder /app/.venv /app/.venv
COPY . .
# Collect without production secrets or access to a real database. Keep the PWA
# service worker at its configured source path after removing duplicate assets.
RUN DEBUG=True SECRET_KEY=build-only DATABASE_URL=sqlite:///:memory: python manage.py collectstatic --noinput \
    && cp static/sw/serviceworker.js /tmp/serviceworker.js \
    && rm -rf static && mkdir -p static/sw \
    && mv /tmp/serviceworker.js static/sw/serviceworker.js

FROM runtime-base AS runtime
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app \
    && mkdir -p /media_cdn /data && chown 10001:10001 /media_cdn /data
COPY --from=assets /app /app
USER 10001:10001
EXPOSE 8004
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=5 CMD ["python", "/app/baani/healthcheck.py"]
CMD ["gunicorn", "baani.wsgi:application", "--bind", "0.0.0.0:8004", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
