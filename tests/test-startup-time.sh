#!/usr/bin/env bash
# Test startup time less than 400ms  #2216
source tests/testenv.sh
/usr/bin/time -f "%U" -o /tmp/vd_start_time $VD -b -N -p dev/quit.vdx
echo "startup time: $(cat /tmp/vd_start_time)s"
$PYTHON -c 'assert float(open("/tmp/vd_start_time").read()) < 0.40, "startup should be under 400ms"'
