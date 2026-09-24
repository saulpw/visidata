#!/usr/bin/env bash

# Run cmdlog tests in parallel
# Usage: test-vdx.sh [-d] [-j N] [testname ...]
#   -d    debug mode: abort on first error, show diffs
#   -j N  number of parallel golden batch processes (default: nproc)

#set -e
shopt -s failglob

source tests/testenv.sh

cleanup_duckdb_fixtures() {
    $PYTHON - <<'PY'
from pathlib import Path

for p in (Path('tests/.visidata/benchmark.duckdb'), Path('tests/.visidata/duckdb_test.duckdb')):
    try:
        p.unlink()
    except FileNotFoundError:
        pass
PY
}

trap 'cleanup_duckdb_fixtures; echo SIGTERM; exit;' SIGTERM
trap 'cleanup_duckdb_fixtures; echo SIGINT; exit;' SIGINT
trap cleanup_duckdb_fixtures EXIT

export LC_NUMERIC="en_US.UTF-8" #2867
export LC_TIME="en_US.UTF-8"
export XDG_DATA_HOME=tests/xdg/data

PY311=$($PYTHON -c 'import sys; print(sys.version_info[:2] >= (3,11))')
PY310=$($PYTHON -c 'import sys; print(sys.version_info[:2] >= (3,10))')
HAS_DUCKDB=$($PYTHON -c 'import importlib.util; print(importlib.util.find_spec("duckdb") is not None)')

DEBUG=0
while getopts "dj:" opt; do
    case "$opt" in
        d) DEBUG=1 ;;
        j) NPROCS=$OPTARG ;;
    esac;
done
shift $((OPTIND - 1))

VD_OPTS="--batch --config tests/.visidatarc --visidata-dir tests/.visidata"

should_skip() {
    local i="$1"
    case "${i%.vd*}" in
        *-broken) echo "broken" ;;
        *-manual) echo "manual" ;;
        *-perf)   echo "perf" ;;
        *duckdb*)
            if [ "$PY310" != "True" ]; then
                echo "duckdb requires py310"
            elif [ "$HAS_DUCKDB" != "True" ]; then
                echo "duckdb missing"
            fi
            ;;
        *-nosave) return 1 ;;  # not skipped, just no golden comparison
        *-flaky)  return 1 ;;  # not skipped; failures reported but non-fatal
        *-n311)  [ "$PY311" == "True" ] && echo "n311" ;;
        *-311)   [ "$PY311" != "True" ] && echo "311" ;;
    esac
}

# Resolve test arguments to file list
if [ $# -eq 0 ] ; then
    TESTS="tests/*.vd*"
else
    TESTS=""
    for arg in "$@"; do
        if [ -f "$arg" ] ; then
            TESTS+=" $arg"
        else
            arg="${arg#tests/}"
            TESTS+=" tests/$arg.vd*"
        fi
    done
fi

mkdir -p tests/output

N_TESTS=0
N_SKIPPED=0
declare -a EXPECTED_OUTPUTS  # output files we expect to be created
declare -A FAILED_TESTS
declare -A FLAKY_TESTS

# Clean output directory before running tests
rm -f tests/output/*

needs_duckdb_fixtures=0
for i in $TESTS ; do
    case "${i%.vd*}" in
        *duckdb*)
            needs_duckdb_fixtures=1
            break
            ;;
    esac
done

if [ "$HAS_DUCKDB" = "True" ] && [ "$needs_duckdb_fixtures" -eq 1 ]; then
    $PYTHON - <<'PY'
from pathlib import Path
import duckdb

fixture_dir = Path('tests/.visidata')
benchmark_db = fixture_dir / 'benchmark.duckdb'
test_db = fixture_dir / 'duckdb_test.duckdb'

for p in (benchmark_db, test_db):
    try:
        p.unlink()
    except FileNotFoundError:
        pass

con = duckdb.connect(str(benchmark_db))
con.execute("""
    CREATE TABLE benchmark AS
    SELECT *
    FROM read_csv('sample_data/benchmark.csv', header=true, all_varchar=true)
""")
con.close()

con = duckdb.connect(str(test_db))
con.execute('CREATE SCHEMA other')
con.execute('CREATE TABLE departments (deptno INTEGER PRIMARY KEY, dname VARCHAR, loc VARCHAR)')
con.executemany('INSERT INTO departments VALUES (?, ?, ?)', [
    (10, 'ACCOUNTING', 'NEW YORK'),
    (20, '\u7814\u53d1', '\u6771\u4eac'),
])
con.execute('CREATE VIEW dept_view AS SELECT * FROM departments ORDER BY deptno')

con.execute('CREATE TABLE edit_pk (id INTEGER PRIMARY KEY, note VARCHAR, amount DECIMAL(10,2))')
con.executemany('INSERT INTO edit_pk VALUES (?, ?, ?)', [
    (1, 'na\u00efve caf\u00e9', 1.25),
    (2, '\u6771\u4eac', 2.50),
])

con.execute('CREATE TABLE edit_no_pk (id INTEGER, note VARCHAR)')
con.executemany('INSERT INTO edit_no_pk VALUES (?, ?)', [
    (1, 'alpha'),
    (2, 'bravo'),
])

con.execute('CREATE TABLE shared_rows (id INTEGER PRIMARY KEY, note VARCHAR)')
con.executemany('INSERT INTO shared_rows VALUES (?, ?)', [
    (1, 'main one'),
    (2, 'main two'),
])

con.execute('CREATE TABLE other."edit composite" ("key one" INTEGER, "key""two" VARCHAR, note VARCHAR, PRIMARY KEY ("key one", "key""two"))')
con.executemany('INSERT INTO other."edit composite" VALUES (?, ?, ?)', [
    (1, 'a', 'alpha'),
    (1, 'b', 'bravo'),
    (2, 'c', 'charlie'),
])

con.execute('CREATE TABLE other.shared_rows (id INTEGER PRIMARY KEY, note VARCHAR)')
con.executemany('INSERT INTO other.shared_rows VALUES (?, ?)', [
    (1, 'other one'),
    (2, 'other two'),
])
con.close()
PY
fi

# Build parallel golden batches and a nosave batch
declare -a GOLDEN_TESTS
NOSAVE_BATCH=""

for i in $TESTS ; do
    outbase=${i##tests/}
    testname=${outbase%.vd*}

    skip_reason=$(should_skip "$i")
    if [ -n "$skip_reason" ]; then
        N_SKIPPED=$((N_SKIPPED + 1))
        [ $DEBUG -eq 1 ] && echo "SKIP: $testname ($skip_reason)"
        continue
    fi

    N_TESTS=$((N_TESTS + 1))
    if [ "${i%-nosave.vd*}-nosave" != "${i%.vd*}" ]; then
        GOLDEN_TESTS+=("$i")
    else
        NOSAVE_BATCH+="replay-reset $testname"$'\n'
        NOSAVE_BATCH+="$(< "$i")"$'\n'
        NOSAVE_BATCH+="replay-end"$'\n'
    fi
done

# Chunk golden tests into NPROCS sequential batches (keeps similar imports together)
N_GOLDEN=${#GOLDEN_TESTS[@]}
CHUNK=$(( (N_GOLDEN + NPROCS - 1) / NPROCS ))
declare -a BATCHES
for (( idx=0; idx<N_GOLDEN; idx++ )); do
    i="${GOLDEN_TESTS[$idx]}"
    BATCH_IDX=$(( idx / CHUNK ))
    testname=${i##tests/}
    testname=${testname%.vd*}
    for goldfn in tests/golden/"$testname".*; do
        outfn="tests/output/$(basename "$goldfn")"
        BATCHES[$BATCH_IDX]+="replay-reset $outfn"$'\n'
        if [ $DEBUG -eq 0 ]; then
            BATCHES[$BATCH_IDX]+="option global replay_ignore_errors True"$'\n'
        fi
        BATCHES[$BATCH_IDX]+="$(< "$i")"$'\n'
        BATCHES[$BATCH_IDX]+="replay-output"$'\n'
        EXPECTED_OUTPUTS+=("$outfn")
    done
done

# Launch nosave in background, golden in foreground

# nosave tests run without replay_ignore_errors so assert-expr failures are caught
NOSAVE_PID=""
if [ -n "$NOSAVE_BATCH" ]; then
    NOSAVE_BATCH+="replay-exit"$'\n'
    env PYTHONPATH=. bin/vd --play - $VD_OPTS <<< "$NOSAVE_BATCH" > /tmp/vd-nosave-output.txt &
    NOSAVE_PID=$!
fi

# golden batches run in parallel
declare -a GOLDEN_PIDS
for idx in "${!BATCHES[@]}"; do
    if [ -n "${BATCHES[$idx]}" ]; then
        BATCHES[$idx]+="replay-exit"$'\n'
        env PYTHONPATH=. bin/vd --play - $VD_OPTS <<< "${BATCHES[$idx]}" &
        GOLDEN_PIDS+=($!)
    fi
done

# wait for golden batches
for pid in "${GOLDEN_PIDS[@]}"; do
    wait $pid
done

# wait for background jobs
if [ -n "$NOSAVE_PID" ]; then
    wait $NOSAVE_PID
    nosave_exit=$?
    if [ $nosave_exit -ne 0 ]; then
        cat /tmp/vd-nosave-output.txt >&2
        # extract failing test name from error output
        failing_test=$(grep -oP '^\S+-nosave' /tmp/vd-nosave-output.txt | head -1)
        if [ -n "$failing_test" ]; then
            FAILED_TESTS[$failing_test]=1
        else
            FAILED_TESTS["nosave-batch"]=1
        fi
    fi
fi

record_failure() {
    local testname="$1" msg="$2"
    case "$testname" in
        *-flaky)
            echo "FLAKY: $testname ($msg)"
            FLAKY_TESTS[$testname]=1
            ;;
        *)
            echo "DIFF: $testname ($msg)"
            FAILED_TESTS[$testname]=1
            ;;
    esac
}

# Check for expected output files that were never created (batch aborted mid-run)
for outfn in "${EXPECTED_OUTPUTS[@]}"; do
    if [ ! -f "$outfn" ]; then
        testname=$(basename "$outfn" | sed 's/\.[^.]*$//')
        record_failure "$testname" "no output: $outfn"
    fi
done

for outfn in tests/output/*; do
    [ "$outfn" = "tests/output/.gitignore" ] && continue
    [ -f "$outfn" ] || continue
    goldfn="tests/golden/$(basename "$outfn")"
    if [ ! -f "$goldfn" ]; then
        testname=$(basename "$outfn" | sed 's/\.[^.]*$//')
        record_failure "$testname" "no golden file: $goldfn"
    elif ! diff -q "$goldfn" "$outfn"; then
        testname=$(basename "$outfn" | sed 's/\.[^.]*$//')
        record_failure "$testname" "$outfn"
        if [ $DEBUG -eq 1 ]; then
            diff "$goldfn" "$outfn"
            break
        fi
    fi
done
N_FAILED=${#FAILED_TESTS[@]}
N_FLAKY=${#FLAKY_TESTS[@]}
if [ $N_FAILED -gt 0 ]; then
    echo ""
    echo "$N_FAILED tests failed: ${!FAILED_TESTS[*]}"
fi

# summary
N_PASSED=$((N_TESTS - N_FAILED - N_FLAKY))
[ $N_SKIPPED -gt 0 ] && SKIP_MSG=", $N_SKIPPED skipped" || SKIP_MSG=""
[ $N_FLAKY -gt 0 ] && FLAKY_MSG=", $N_FLAKY flaky" || FLAKY_MSG=""

if [ $N_FAILED -gt 0 ]; then
    echo "FAIL: $N_PASSED/$N_TESTS passed in $(elapsed)s${FLAKY_MSG}${SKIP_MSG}"
    exit 1
else
    echo "$N_PASSED passed in $(elapsed)s${FLAKY_MSG}${SKIP_MSG}"
fi
