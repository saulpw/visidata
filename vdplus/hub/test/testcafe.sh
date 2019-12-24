#!/bin/bash
set -e

PROJECT_ROOT=$(git rev-parse --show-toplevel)

pushd $PROJECT_ROOT/hub
./spa/node_modules/.bin/testcafe \
  chrome:headless \
  --screenshots $PROJECT_ROOT/hub/test/screenshots \
  --screenshots-on-fails \
  test/integration
popd
