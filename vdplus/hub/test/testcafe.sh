#!/bin/bash
set -e

PROJECT_ROOT=$(git rev-parse --show-toplevel)

pushd $PROJECT_ROOT/hub

version=$(
  cat spa/package.json \
    | grep 'testcafe"' \
    | cut -d ":" -f2 \
    | sed 's/"//g' | sed 's/\^//g' | sed 's/,//g' \
    | xargs
  )

yarn add testcafe@$version

node_modules/.bin/testcafe \
  chrome:headless \
  --screenshots $PROJECT_ROOT/hub/test/screenshots \
  --screenshots-on-fails \
  test/integration
popd
