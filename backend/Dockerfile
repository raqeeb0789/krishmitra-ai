# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.13

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS base

ENV PYTHONUNBUFFERED=1

# ============================================================
# BUILD STAGE
# ============================================================

FROM base AS build

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache locations
ENV HOME=/app
ENV XDG_CACHE_HOME=/app/.cache
ENV UV_CACHE_DIR=/app/.cache/uv
ENV HF_HOME=/app/.cache/huggingface
ENV HUGGINGFACE_HUB_CACHE=/app/.cache/huggingface/hub

# Copy dependency files
COPY pyproject.toml uv.lock ./

# IMPORTANT:
# uv sync expects the src directory because
# pyproject.toml defines a src-based package.
RUN mkdir -p /app/src

# Install dependencies
RUN uv sync --locked

# Now copy the actual source code
COPY . .

# Download LiveKit models/files
RUN uv run src/agent.py download-files

# ============================================================
# PRODUCTION STAGE
# ============================================================

FROM base

WORKDIR /app

ARG UID=10001

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Copy everything including:
# .venv
# source code
# downloaded LiveKit models
# cache
COPY --from=build --chown=appuser:appuser /app /app

# Runtime cache locations
ENV HOME=/app
ENV XDG_CACHE_HOME=/app/.cache
ENV UV_CACHE_DIR=/app/.cache/uv
ENV HF_HOME=/app/.cache/huggingface
ENV HUGGINGFACE_HUB_CACHE=/app/.cache/huggingface/hub

# Ensure permissions
RUN chown -R appuser:appuser /app

USER appuser

CMD ["uv", "run", "--no-project", "src/agent.py", "start"]