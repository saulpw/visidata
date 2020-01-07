#!/usr/bin/env bash
set -e

export PORT=8000
export CONTAINER_NAME=vdhub-test

is_http_up() {
  [ $(curl -LI localhost:$PORT -o /dev/null -w '%{http_code}\n' -s) == "200" ]
}
export -f is_http_up

wait_until_ready() {
  echo "Waiting for $CONTAINER_NAME to come up..."
  until is_http_up; do sleep 0.1; done
  echo "$CONTAINER_NAME is up"
}
export -f wait_until_ready

clean_up() {
  echo "Cleaning up..."
  docker rm -f $CONTAINER_NAME
  echo "$CONTAINER_NAME container removed"
}
trap clean_up EXIT

docker run --rm \
  -e GOTTY_PORT=8181 \
  -v $(pwd):/app/data \
  --user 1000:1000 \
  --net host \
  vdwww > vdwww.logs 2>&1 &

# Run Hub DB migrations
docker run --rm \
  -e CI='true' \
  -e POSTGRES_HOST='localhost' \
  -e POSTGRES_PASSWORD='postgres' \
  -e POSTGRES_USER='postgres' \
  --net host \
  vdhub \
  bash -c 'source $HOME/.poetry/env && cd /app/api && poetry run pw_migrate migrate'

# Run the Hub
docker run \
  --name $CONTAINER_NAME \
  -v $(pwd)/hub/spa:/app/data \
  -e CI='true' \
  -e POSTGRES_HOST='localhost' \
  -e POSTGRES_PASSWORD='postgres' \
  -e POSTGRES_USER='postgres' \
  --net host \
  vdhub > vdhub.logs 2>&1 &

if timeout --preserve-status 10 bash -c wait_until_ready; then
  hub/test/testcafe.sh
else
  echo "Timed out waiting for $CONTAINER_NAME container to start"
  exit 1
fi



