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

# #2989: exec-sql opens a sheet of query results
rm -f $OUTDIR/pg-exec-sql.tsv
cat > $OUTDIR/pg-exec-sql.vdx <<EOF2
open-file postgres:///vdtest
exec-sql SELECT customer, count(*) AS n FROM benchmark GROUP BY customer ORDER BY customer LIMIT 2
save-sheet $OUTDIR/pg-exec-sql.tsv
EOF2
$VDB -p $OUTDIR/pg-exec-sql.vdx
expected=$'customer\tn\nDavid Attenborough\t4\nDouglas "Dougie" Powers\t3'
if [[ "$(cat $OUTDIR/pg-exec-sql.tsv)" != "$expected" ]]; then
    echo "FAIL: exec-sql results"
    cat $OUTDIR/pg-exec-sql.tsv
    FAIL=1
fi

# quotes in schema, table, and column names
$VDB --postgres-schema="it's" 'postgres:///vdtest/we"ird' -o $OUTDIR/pg-quoted.tsv
expected=$'a"b\tc\'d\n1\tx\n2\ty'
if [[ "$(cat $OUTDIR/pg-quoted.tsv)" != "$expected" ]]; then
    echo "FAIL: quoted identifiers"
    cat $OUTDIR/pg-quoted.tsv
    FAIL=1
fi

if [[ $FAIL -eq 1 ]]; then
    echo "FAILED"
    exit 1
fi
echo "all postgres tests passed"
