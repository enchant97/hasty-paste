#!/bin/sh

if [ $# -eq 0 ]
then
    # Runs the web app
    BIND="${HOST:-0.0.0.0}:${PORT:-8000}"
    args="--bind $BIND --workers ${WORKERS:-1} --log-level ${LOG_LEVEL:-INFO}"

    if [ -n "$CERT_FILE" ] && [ -n "$KEY_FILE" ]
    then
        args="$args --certfile $CERT_FILE --keyfile $KEY_FILE"
    fi

    exec hypercorn 'paste_bin.main:create_app()' $args
else
    # Runs management CLI app
    exec python -m 'paste_bin.cli' $@
fi
