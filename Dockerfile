FROM python:3.13-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       gcc \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry --user

COPY pyproject.toml poetry.lock* ./

ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

RUN /root/.local/bin/poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.13-slim-bookworm

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       libpq5 \
       ca-certificates \
       curl \
  && rm -rf /var/lib/apt/lists/* \
  && adduser --disabled-password --gecos "" appuser

WORKDIR /app

COPY --from=builder /build/.venv /.venv
ENV PATH="/.venv/bin:$PATH"

COPY app/ ./app/
COPY tasks/ ./tasks/
COPY main.py ./
COPY config/ ./config/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default to uvicorn for development, but allow override for production
CMD ["/.venv/bin/python", "-m", "uvicorn", "app:create_app", "--host", "0.0.0.0", "--port", "8000"]
