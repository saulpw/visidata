#!/usr/bin/env bash
# Run perf tests and report wall time  #2369
source tests/testenv.sh

for i in tests/*-perf.vd*; do
    testname=$(basename "$i" | sed 's/\.vd.*//')
    /usr/bin/time -f "%e" -o /tmp/vd_perf_time $VD --batch --play "$i" -o /dev/null
    echo "$testname: $(cat /tmp/vd_perf_time)s"
done
