#!/usr/bin/env bash
# Log startup time  #2216
source tests/testenv.sh
/usr/bin/time -f "%e" -o /tmp/vd_start_time $VD -b -N -p dev/quit.vdx
ms=$(python3 -c "print(int(float(open('/tmp/vd_start_time').read()) * 1000))")
echo "startup time: ${ms}ms ($(git rev-parse --short HEAD 2>/dev/null || echo unknown) py$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'))"
