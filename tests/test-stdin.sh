#!/usr/bin/env bash
# Test stdin piping  #1978
source tests/testenv.sh
mkdir -p $OUTDIR
seq 10000 | $VD -f txt --overwrite=n --batch --output $OUTDIR/stdin.tsv
diff tests/golden/stdin.tsv $OUTDIR/stdin.tsv
