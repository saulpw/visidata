#!/usr/bin/env bash
# Run perf tests and report wall time  #2369
source tests/testenv.sh
vd_testtmp
TIMEFILE="$VD_TESTTMP/test-perf-time"

N=0
TIMES=""
for i in tests/*-perf.vd*; do
    testname=$(basename "$i" | sed 's/\.vd.*//')
    /usr/bin/time -f "%e" -o "$TIMEFILE" $VD --batch --play "$i" -o /dev/null
    TIMES="$TIMES${TIMES:+, }$testname: $(cat "$TIMEFILE")s"
    N=$((N + 1))
done
echo "$TIMES; $N passed in $(elapsed)s"
