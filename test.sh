#!/usr/bin/env bash

trap "echo aborted; exit;" SIGINT SIGTERM

# Usage $0
for i in tests/*.vd ; do
    echo "--- $i"
    outbase=${i##tests/}
    if [ "${i%-notest.vd}-notest" == "${i%.vd}" ]
    then
        PYTHONPATH=. bin/vd --play $i --batch
    else
        PYTHONPATH=. bin/vd --confirm-overwrite=False --play $i --batch --output tests/golden/${outbase%.vd}.tsv
    fi
done
echo '=== git diffs ==='
git --no-pager diff --exit-code --numstat tests/
