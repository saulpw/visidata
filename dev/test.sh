#!/usr/bin/env bash

# Usage: test.sh [testname]

#set -e
shopt -s failglob

trap "echo aborted; exit;" SIGINT SIGTERM

run_silent_unless_error() {
  output=$(eval "$@" 2>&1)  # Captures ALL stdout and stderr
  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo "TEST FAILED: $@"
    echo "$output"
    exit 1
  fi
  return $exit_code
}

if [ -z "$1" ] ; then
    # test.sh; run all .vd/.vdj in tests/
    TESTS="tests/*.vd*"
else
    # test.sh testname; run tests/testname.vd
    TESTS=tests/$1.vd*
fi

for i in $TESTS ; do
    echo "--- $i"
    outbase=${i##tests/}
    if [ "${i%-nosave.vd*}-nosave" == "${i%.vd*}" ];
    then
        TEST=false
    elif [ "${i%-n312.vd*}-n312" == "${i%.vd*}" ];
    then
        if [ `python -c 'import sys; print(sys.version_info[:2] >= (3,12))'` == "True" ];
        then
            TEST=false
        else
            TEST=true
        fi

    elif [ "${i%-311.vd*}-311" == "${i%.vd*}" ];
    then
        if [ `python -c 'import sys; print(sys.version_info[:2] >= (3,11))'` == "True" ];
        then
            TEST=true
        else
            TEST=false
        fi

    else
        TEST=true
    fi
    if $TEST == true;
    then
        for goldfn in tests/golden/${outbase%.vd*}.*; do
            run_silent_unless_error "PYTHONPATH=. bin/vd --overwrite=False --play "$i" --batch --output "$goldfn" --config tests/.visidatarc --visidata-dir tests/.visidata"
        done
    else
        run_silent_unless_error "PYTHONPATH=. bin/vd --play "$i" --batch --config tests/.visidatarc --visidata-dir tests/.visidata"
    fi
done

run_silent_unless_error "PYTHONPATH=. bin/vd <(seq 10000) --overwrite=False --batch --output tests/golden/stdin-guesser.tsv --config tests/.visidatarc --visidata-dir tests/.visidata"  #1978

echo '=== git diffs for BUILD FAILURE ==='
git --no-pager diff --numstat tests/
git --no-pager diff --exit-code tests/; git_diff_exit_code="$?"
echo '=============================================='
exit "$git_diff_exit_code"
