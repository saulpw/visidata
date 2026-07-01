#!/usr/bin/env bash
# Run perf tests and report wall time  #2369
source tests/testenv.sh

N=0
TIMES=""
for i in tests/*-perf.vd*; do
    testname=$(basename "$i" | sed 's/\.vd.*//')
    /usr/bin/time -f "%e" -o /tmp/vd_perf_time $VD --batch --play "$i" -o /dev/null
    TIMES="$TIMES${TIMES:+, }$testname: $(cat /tmp/vd_perf_time)s"
    N=$((N + 1))
done
echo "$TIMES; $N passed in $(elapsed)s"
