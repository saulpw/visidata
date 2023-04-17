#!/usr/bin/env bash

# Usage: test.sh [testname]

set -e
shopt -s failglob

trap "echo aborted; exit;" SIGINT SIGTERM

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
            PYTHONPATH=. bin/vd --confirm-overwrite=False --play "$i" --batch --output "$goldfn" --config tests/.visidatarc --visidata-dir tests/.visidata
            echo "save: $goldfn"
        done
    fi
done

echo '=== git diffs for BUILD FAILURE ==='
git --no-pager diff --numstat tests/
git --no-pager diff --exit-code tests/
echo '=============================================='
