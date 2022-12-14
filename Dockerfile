# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION}-slim as build-deps

    WORKDIR /app

    COPY requirements.txt .

    RUN python -m venv .venv
    ENV PATH="/app/.venv/bin:$PATH"

    RUN --mount=type=cache,target=/root/.cache pip install -r requirements.txt

    # ensure that data folder gets created with nobody user
    RUN mkdir /app/data && chown -R nobody /app/data

# reduce layers created in final image
FROM scratch as build-content

    WORKDIR /app

    COPY --from=build-deps --link /app /app

    COPY paste_bin paste_bin

    COPY scripts/* ./

FROM python:${PYTHON_VERSION}-alpine

    WORKDIR /app

    USER nobody:nobody

    EXPOSE 8000
    ENV PATH="/app/.venv/bin:$PATH"
    ENV PASTE_ROOT="/app/data"

    COPY --from=build-content --link /app /app

    ENTRYPOINT ["/bin/sh", "entrypoint.sh"]

    HEALTHCHECK --interval=1m --start-period=10s \
        CMD /bin/sh health-check.sh
