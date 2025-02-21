# syntax=docker/dockerfile:1

FROM node:20-slim AS node-base
    ENV PNPM_HOME="/pnpm"
    ENV PATH="$PNPM_HOME:$PATH"

    # ensure running latest corepack: https://github.com/nodejs/corepack/issues/612
    RUN npm install --global corepack@latest
    RUN corepack enable

FROM golang:1.23-alpine AS go-base
    RUN go install github.com/a-h/templ/cmd/templ@latest
    RUN go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest

FROM node-base AS node-build
    WORKDIR /opt/hasty-paste

    COPY . .

    RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
    RUN pnpm run build

FROM go-base AS go-build
    WORKDIR /opt/hasty-paste

    COPY . .

    RUN sqlc generate
    RUN templ generate
    RUN CGO_ENABLED=0 GOOS=linux go build -o ./hasty-paste

FROM gcr.io/distroless/static-debian12
    WORKDIR /opt/hasty-paste

    COPY --from=node-build --link /opt/hasty-paste/dist /opt/hasty-paste/dist
    COPY --from=go-build --link /opt/hasty-paste/hasty-paste /opt/hasty-paste/hasty-paste

    ENV BIND__HOST=0.0.0.0
    ENV BIND__PORT=8080
    ENV DB_URI=sqlite:///opt/hasty-paste/data/db.sqlite
    ENV ATTACHMENTS_PATH=/opt/hasty-paste/data/attachments

    EXPOSE 8080
    VOLUME /opt/hasty-paste/data

    CMD [ "./hasty-paste" ]
