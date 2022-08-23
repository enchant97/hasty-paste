#!/bin/sh

if [ $# -eq 0 ]
then
    # Runs the web app
    BIND="$HOST:$PORT"
    args="--bind $BIND --workers $WORKERS --log-level $LOG_LEVEL"

    if [ -n "$CERT_FILE" ] && [ -n "$KEY_FILE" ]
    then
        args="$args --certfile $CERT_FILE --keyfile $KEY_FILE"
    fi

    exec hypercorn 'paste_bin.main:create_app()' $args
else
    # Runs management CLI app
    exec python -m 'paste_bin.cli' $@
fi
