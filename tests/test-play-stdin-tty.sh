#!/usr/bin/env bash
# Test --play /dev/stdin works after duptty() redirects fd 0 to /dev/tty
source tests/testenv.sh
mkdir -p $OUTDIR
OUT=$OUTDIR/play-stdin-tty.tsv
rm -f $OUT
# script(1): controlling tty so duptty() actually redirects fd 0 (else bug masked)
# inner shell is /bin/sh (dash) under script -c, so use `<` not `<<<`
timeout 10 script -q -c "$VD tests/data1.tsv --play /dev/stdin --batch -N -o $OUT < dev/test-play-stdin-tty.vdx" /dev/null > /dev/null 2>&1
diff tests/golden/play-stdin-tty.tsv $OUT
