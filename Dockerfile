FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY .. .
RUN uv sync --frozen --no-dev


FROM python:3.13-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=apbs.settings \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app/apbs

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system django && \
    adduser --system --ingroup django --home /home/django django

RUN mkdir -p /home/django && \
    chown django:django /home/django

COPY --from=builder --chown=django:django /app/.venv /app/.venv
COPY --from=builder --chown=django:django /app /app

USER django

EXPOSE 8000

CMD ["gunicorn", "apbs.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "3", \
    "--threads", "2", \
    "--timeout", "60", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]