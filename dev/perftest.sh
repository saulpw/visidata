#!/usr/bin/env bash

# Usage: perftest.sh [testname ...]
# Runs -perf tests sequentially, each in its own process, reporting wall time.

VD_OPTS="--batch --config tests/.visidatarc --visidata-dir tests/.visidata"

if [ $# -eq 0 ]; then
    TESTS=tests/*-perf.vd*
else
    TESTS=""
    for arg in "$@"; do
        if [ -f "$arg" ]; then
            TESTS+=" $arg"
        else
            arg="${arg#tests/}"
            TESTS+=" tests/$arg.vd*"
        fi
    done
fi

for i in $TESTS; do
    testname=$(basename "$i" | sed 's/\.vd.*//')
    start=$SECONDS
    env PYTHONPATH=. bin/vd --play "$i" $VD_OPTS > /dev/null 2>&1
    elapsed=$((SECONDS - start))
    echo "${elapsed}s  $testname"
done
