#!/usr/bin/env bash

# Usage: test.sh [-j n_jobs] [-v] [testname]

#set -e
shopt -s failglob

trap "echo SIGTERM; exit;" SIGTERM
trap "echo SIGINT; exit;" SIGINT

export LC_NUMERIC="en_US.UTF-8" #2867
export LC_TIME="en_US.UTF-8"

PYTHON=${PYTHON:-python}
PY311=$($PYTHON -c 'import sys; print(sys.version_info[:2] >= (3,11))')

MAX_PARALLEL_JOBS=1
VERBOSE=0
while getopts "j:v" opt; do
    case "$opt" in
        j) MAX_PARALLEL_JOBS="$OPTARG" ;;
        v) VERBOSE=1 ;;
    esac;
done
shift $((OPTIND - 1))

run_test() {
  testname="$1"
  shift
  output=$("$@" 2>&1)  # Captures ALL stdout and stderr
  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo ""
    echo "FAIL: $testname (exit $exit_code)"
    echo "$output" | tail -20
    return $exit_code
  fi
}

should_skip() {
    local i="$1"
    case "${i%.vd*}" in
        *-broken) echo "broken" ;;
        *-nosave) return 1 ;;  # not skipped, just no golden comparison
        *-n311)  [ "$PY311" == "True" ] && echo "n311" ;;
        *-311)   [ "$PY311" != "True" ] && echo "311" ;;
    esac
}

if [ -z "$1" ] ; then
    # test.sh; run all .vd/.vdj/.vdx in tests/
    TESTS="tests/*.vd*"
else
    # test.sh testname; run tests/testname.vd*
    TESTS="tests/$1.vd*"
fi

N_TESTS=0
N_SKIPPED=0
ANY_FAILED=0

for i in $TESTS ; do
    outbase=${i##tests/}
    testname=${outbase%.vd*}

    skip_reason=$(should_skip "$i")
    if [ -n "$skip_reason" ]; then
        N_SKIPPED=$((N_SKIPPED + 1))
        echo "SKIP: $testname ($skip_reason)"
        continue
    fi

    N_TESTS=$((N_TESTS + 1))
    if [ $VERBOSE -eq 1 ]; then
        echo "--- $testname"
    else
        printf "."
    fi

    while (( $(jobs -p | wc -l) >= MAX_PARALLEL_JOBS )); do
        #-n means wait until any of the background processes finish
        wait -n || ANY_FAILED=1
    done

    # it should be safe to run tests in parallel, as long as no tests try to write to the same file simultaneously
    if [ "${i%-nosave.vd*}-nosave" != "${i%.vd*}" ]; then
        for goldfn in tests/golden/"$testname".*; do
            run_test "$testname" env PYTHONPATH=. bin/vd --overwrite=n --play "$i" --batch --output "$goldfn" --config tests/.visidatarc --visidata-dir tests/.visidata &
        done
    else
        run_test "$testname" env PYTHONPATH=. bin/vd --play "$i" --batch --config tests/.visidatarc --visidata-dir tests/.visidata &
    fi
done

N_TESTS=$((N_TESTS + 1))
run_test "stdin-guesser" env PYTHONPATH=. bin/vd <(seq 10000) --overwrite=n --batch --output tests/golden/stdin-guesser.tsv --config tests/.visidatarc --visidata-dir tests/.visidata  #1978

[ $VERBOSE -eq 0 ] && echo ""
#wait for any remaining background jobs to finish
wait -n 2>/dev/null || ANY_FAILED=1
wait

diff_output=$(git --no-pager diff tests/)
if [ -n "$diff_output" ]; then
    echo "$diff_output"
    echo ""
    echo "FAIL: golden output changed (see diff above)"
    ANY_FAILED=1
fi

# summary
[ $N_SKIPPED -gt 0 ] && SKIP_MSG=", $N_SKIPPED skipped" || SKIP_MSG=""

if [ "$ANY_FAILED" -ne 0 ]; then
    echo "FAILED ($N_TESTS tests${SKIP_MSG})"
    exit 1
else
    echo "PASS ($N_TESTS tests${SKIP_MSG})"
fi
