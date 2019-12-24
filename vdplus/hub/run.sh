#!/bin/sh

export TERM=xterm
/app/bin/gotty -w -p 8181 vd /app/data &

. $HOME/.poetry/env
poetry run \
  gunicorn \
  --worker-class aiohttp.GunicornWebWorker \
  -w ${GUNICORN_WORKERS:-4} \
  --bind 0.0.0.0 \
  app:create_app
