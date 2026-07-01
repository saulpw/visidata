#!/usr/bin/env bash
# Test stdin handling: data, replay from file, replay via /dev/stdin under tty
source tests/testenv.sh
set -e
mkdir -p $OUTDIR

# a) data via stdin: #1978
seq 10000 | $VD -f txt --overwrite=n --batch --output $OUTDIR/stdin.tsv
diff tests/golden/stdin.tsv $OUTDIR/stdin.tsv

# b) data via stdin, replay from file
printf '{"a":1}\n{"a":2}\n' | $VD -f jsonl -p dev/test-stdin-replay.vdx --batch -N -o $OUTDIR/stdin-replay.tsv
diff tests/golden/stdin-replay.tsv $OUTDIR/stdin-replay.tsv

# c) replay via /dev/stdin under tty: script(1) gives a controlling tty so
# duptty() actually redirects fd 0 (else bug is masked)
# inner shell is /bin/sh under script -c, so use `<` not `<<<`
rm -f $OUTDIR/play-stdin-tty.tsv
timeout 10 script -q -c "$VD tests/data1.tsv --play /dev/stdin --batch -N -o $OUTDIR/play-stdin-tty.tsv < dev/test-play-stdin-tty.vdx" /dev/null > /dev/null
diff tests/golden/play-stdin-tty.tsv $OUTDIR/play-stdin-tty.tsv

echo "all stdin tests passed in $(elapsed)s"
