#!/usr/bin/env bash
# Run test scripts with labeled output
# Usage: test-all.sh [test scripts...]

source tests/testenv.sh
export PYTHON VD NPROCS OUTDIR

FAILED=""
N=0

if [ $# -eq 0 ]; then
    set -- tests/test-*.sh
fi

for t in "$@"; do
    name=$(basename "$t" .sh)
    N=$((N + 1))
    "$t" 2>&1 | sed -u "s/^/$name: /"
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
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
