# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION}-slim as builder

    WORKDIR /app

    COPY requirements.txt .

    RUN python -m venv .venv
    ENV PATH="/app/.venv/bin:$PATH"

    RUN --mount=type=cache,target=/root/.cache pip install -r requirements.txt

FROM python:${PYTHON_VERSION}-alpine

    WORKDIR /app
    EXPOSE 8000
    ENV PATH="/app/.venv/bin:$PATH"
    ENV WORKERS=1
    ENV LOG_LEVEL="INFO"
    ENV HOST="0.0.0.0"
    ENV PORT="8000"
    ENV PASTE_ROOT="/app/data"

    COPY --from=builder --link /app/.venv .venv

    COPY paste_bin paste_bin

    COPY scripts/* ./

    CMD /bin/sh run.sh

    HEALTHCHECK --interval=1m --start-period=15s \
        CMD /bin/sh health-check.sh
