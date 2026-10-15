#!/usr/bin/env bash
# Log startup time  #2216
source tests/testenv.sh
vd_testtmp
TIMEFILE="$VD_TESTTMP/test-startup-time"
/usr/bin/time -f "%e" -o "$TIMEFILE" $VD -b -N -p dev/quit.vdx
ms=$($PYTHON -c 'import sys; print(int(float(open(sys.argv[1]).read()) * 1000))' "$TIMEFILE")
echo "startup: ${ms}ms ($(git rev-parse --short HEAD 2>/dev/null || echo unknown) py$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')); 1 passed in $(elapsed)s"
