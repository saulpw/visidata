#!/usr/bin/env bash
# Test postgres loader against a local database  #2203
# Setup: dev/setup-postgres.sh
source tests/testenv.sh

set -e

PGURL="postgres:///vdtest"
VDB="$VD --batch"
FAIL=0

# Skip if psycopg2 or database is not available
if ! $PYTHON -c "import psycopg2" 2>/dev/null; then
    echo "SKIP: psycopg2 not installed (pip install psycopg2-binary)"
    exit 0
fi
if ! psql -d vdtest -c "SELECT 1" > /dev/null 2>&1; then
    echo "SKIP: postgres not available (run dev/setup-postgres.sh)"
    exit 0
fi

mkdir -p $OUTDIR

# #282: open table directly from URL
$VDB "$PGURL/benchmark" -o $OUTDIR/pg-benchmark.tsv
header=$(head -1 $OUTDIR/pg-benchmark.tsv)
if [[ "$header" != "date	customer	sku	item	quantity	unit	paid" ]]; then
    echo "FAIL: direct table open: wrong header"
    echo "  got: '$header'"
    FAIL=1
fi
nrows=$(wc -l < $OUTDIR/pg-benchmark.tsv)
if [[ $nrows -ne 52 ]]; then  # 51 data rows + 1 header
    echo "FAIL: direct table open: expected 52 lines, got $nrows"
    FAIL=1
fi

# #727: second query works (no cascading transaction error)
$VDB "$PGURL/benchmark" -o $OUTDIR/pg-benchmark2.tsv
header2=$(head -1 $OUTDIR/pg-benchmark2.tsv)
if [[ "$header2" != "date	customer	sku	item	quantity	unit	paid" ]]; then
    echo "FAIL: second query failed (transaction cascade)"
    FAIL=1
fi

# tables sheet lists benchmark
$VDB "$PGURL" -o $OUTDIR/pg-tables.tsv
if ! grep -q benchmark $OUTDIR/pg-tables.tsv; then
    echo "FAIL: tables sheet doesn't list benchmark"
    cat $OUTDIR/pg-tables.tsv
    FAIL=1
fi

if [[ $FAIL -eq 1 ]]; then
    echo "FAILED"
    exit 1
fi
echo "all postgres tests passed"
