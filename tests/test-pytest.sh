#!/usr/bin/env bash
# Run Python unit tests
source tests/testenv.sh
vd_testtmp
mkdir -p "$VD_TESTTMP/test-pytest"
TMPDIR="$VD_TESTTMP/test-pytest" $PYTHON -m pytest visidata/tests/ ${PYTEST_FLAGS:--q}
