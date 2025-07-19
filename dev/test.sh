#!/usr/bin/env bash

# Usage: test.sh [-j n_jobs] [testname]

#set -e
shopt -s failglob

trap "echo aborted; exit;" SIGINT SIGTERM

MAX_PARALLEL_JOBS=1
while getopts "j:" opt; do
    case "$opt" in
        j)
            MAX_PARALLEL_JOBS="$OPTARG"
            ;;
    esac;
done
shift $((OPTIND - 1))
echo "Using MAX_PARALLEL_JOBS=$MAX_PARALLEL_JOBS"

run_silent_unless_error() {
  output=$(PYTHONPATH="$PYTHONPATH" "$@" 2>&1)  # Captures ALL stdout and stderr
  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    # output everything in a single echo command instead of multiple. Perhaps that will
    # help avoid mixing of output from simultaneous invocations of run_silent_unless_error
    echo "TEST FAILED:" "$@" "\n" "$output"
    exit 1
  fi
  return $exit_code
}

if [ -z "$1" ] ; then
    # test.sh; run all .vd/.vdj in tests/
    TESTS="tests/*.vd*"
else
    # test.sh testname; run tests/testname.vd
    TESTS="tests/$1.vd*"
fi

for i in $TESTS ; do
    echo "--- $i"
    # remove tests/ prefix
    outbase=${i##tests/}
    if [ "${i%-nosave.vd*}-nosave" == "${i%.vd*}" ];
    then
        TEST=false
    elif [ "${i%-n312.vd*}-n312" == "${i%.vd*}" ];
    then
        if [ "$(python -c 'import sys; print(sys.version_info[:2] >= (3,12))')" == "True" ];
        then
            TEST=false
        else
            TEST=true
        fi

    elif [ "${i%-311.vd*}-311" == "${i%.vd*}" ];
    then
        if [ "$(python -c 'import sys; print(sys.version_info[:2] >= (3,11))')" == "True" ];
        then
            TEST=true
        else
            TEST=false
        fi

    else
        TEST=true
    fi
    while (( $(jobs -p | wc -l) >= MAX_PARALLEL_JOBS )); do
        #-n means wait until any of the background processes finish
        wait -n
    done
    # it should be safe to run tests in parallel, as long as no tests try to write to the same file simultaneously
    if [ "$TEST" == true ];
    then
        for goldfn in tests/golden/"${outbase%.vd*}".*; do
            PYTHONPATH=. run_silent_unless_error bin/vd --overwrite=False --play "$i" --batch --output "$goldfn" --config tests/.visidatarc --visidata-dir tests/.visidata &
        done
    else
        PYTHONPATH=. run_silent_unless_error bin/vd --play "$i" --batch --config tests/.visidatarc --visidata-dir tests/.visidata &
    fi
done

PYTHONPATH=. run_silent_unless_error bin/vd <(seq 10000) --overwrite=False --batch --output tests/golden/stdin-guesser.tsv --config tests/.visidatarc --visidata-dir tests/.visidata  #1978

#wait for any remaining background jobs to finish
wait

echo '=== git diffs for BUILD FAILURE ==='
git --no-pager diff --numstat tests/
git --no-pager diff --exit-code tests/; git_diff_exit_code="$?"
echo '=============================================='
exit "$git_diff_exit_code"
