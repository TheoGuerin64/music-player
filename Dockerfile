FROM python:3.13-slim AS base
WORKDIR /app

FROM base AS builder
RUN apt-get update &&\
    apt-get install -y git &&\
    rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-editable
COPY src/ src/
RUN uv sync --frozen --no-editable

FROM base
RUN apt-get update &&\
    apt-get install -y ffmpeg &&\
    rm -rf /var/lib/apt/lists/*
RUN groupadd -r -g 1000 app && useradd -r -u 1000 -g 1000 -m app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
USER app
CMD ["music_player"]
