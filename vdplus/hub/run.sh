#!/bin/sh

. $HOME/.poetry/env

poetry run \
  gunicorn \
  --worker-class eventlet \
  -w 1 \
  --bind 0.0.0.0 \
  app:app
