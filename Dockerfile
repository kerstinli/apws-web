FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv

ARG SECRET_KEY
ARG DEBUG
ARG ALLOWED_HOSTS
ARG OPENSEARCH_HOST
ARG OPENSEARCH_PORT
ARG OPENSEARCH_USER
ARG OPENSEARCH_PASSWORD
ARG OPENSEARCH_USE_SSL
ARG OPENSEARCH_SSL_VERIFY
ARG CAMERA_HOST
ARG CAMERA_PORT

ENV SECRET_KEY=$SECRET_KEY \
    DEBUG=$DEBUG \
    ALLOWED_HOSTS=$ALLOWED_HOSTS \
    OPENSEARCH_HOST=$OPENSEARCH_HOST \
    OPENSEARCH_PORT=$OPENSEARCH_PORT \
    OPENSEARCH_USER=$OPENSEARCH_USER \
    OPENSEARCH_PASSWORD=$OPENSEARCH_PASSWORD \
    OPENSEARCH_USE_SSL=$OPENSEARCH_USE_SSL \
    OPENSEARCH_SSL_VERIFY=$OPENSEARCH_SSL_VERIFY \
    CAMERA_HOST=$CAMERA_HOST \
    CAMERA_PORT=$CAMERA_PORT

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
COPY .. .

RUN uv sync --frozen --no-install-project --no-dev

WORKDIR /app/apws

RUN uv run python3 manage.py collectstatic --noinput
RUN uv run python3 manage.py compilemessages

FROM python:3.13-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=apws.settings \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libxcb1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system django && \
    adduser --system --ingroup django --home /home/django django

RUN mkdir -p /home/django && \
    chown django:django /home/django

COPY --from=builder --chown=django:django /app/.venv /app/.venv
COPY --from=builder --chown=django:django /app /app

USER django

EXPOSE 8000

WORKDIR /app/apws

CMD ["gunicorn", "apws.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "3", \
    "--threads", "2", \
    "--timeout", "60", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]