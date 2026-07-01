#!/usr/bin/env bash
# Run test scripts with labeled output
# Usage: test-all.sh [test scripts...]

source tests/testenv.sh
# PYTHONFAULTHANDLER: SIGABRT → all-thread traceback dump
export PYTHON VD NPROCS OUTDIR PYTHONFAULTHANDLER=1

TEST_TIMEOUT=${TEST_TIMEOUT:-120}

FAILED=""
N=0

if [ $# -eq 0 ]; then
    set -- tests/test-*.sh
fi

for t in "$@"; do
    name=$(basename "$t" .sh)
    N=$((N + 1))
    timeout --signal=ABRT --kill-after=5 "$TEST_TIMEOUT" "$t" 2>&1 | sed -u "s/^/$name: /"
    rc=${PIPESTATUS[0]}
    if [ $rc -eq 124 ] || [ $rc -eq 137 ]; then
        echo "FAIL: $name (timed out after ${TEST_TIMEOUT}s)"
        FAILED="$FAILED $name"
    elif [ $rc -ne 0 ]; then
        echo "FAIL: $name"
        FAILED="$FAILED $name"
    fi
done

NF=$(echo $FAILED | wc -w)
NP=$((N - NF))
if [ -n "$FAILED" ]; then
    echo ""
    echo "FAILED:$FAILED"
    echo "FAIL: $NP/$N tests passed"
    exit 1
else
    echo "PASS: $NP/$N tests passed"
fi
