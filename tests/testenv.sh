# Common test environment — source this from test-*.sh scripts
# Usage: source tests/testenv.sh

PYTHON=${PYTHON:-python3}
VD="${VD:-$PYTHON -m visidata --config tests/.visidatarc --visidata-dir tests/.visidata}"
NPROCS=${NPROCS:-$(nproc)}
OUTDIR=${OUTDIR:-tests/output}
export NO_COLOR=1
