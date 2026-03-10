#!/usr/bin/env bash
# Test replaying input from stdin
source tests/testenv.sh
mkdir -p $OUTDIR
printf '{"a":1}\n{"a":2}\n' | $VD -f jsonl -p dev/test-stdin-replay.vdx --batch -N -o $OUTDIR/stdin-replay.tsv
diff tests/golden/stdin-replay.tsv $OUTDIR/stdin-replay.tsv
