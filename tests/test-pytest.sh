#!/usr/bin/env bash
# Run Python unit tests
source tests/testenv.sh
$PYTHON -m pytest visidata/tests/ ${PYTEST_FLAGS:--q}
