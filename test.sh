#!/usr/bin/env bash

# Usage $0
for i in tests/*.vd ; do
    echo "--- $i"
    outbase=${i##tests/}
    PYTHONPATH=. bin/vd --confirm-overwrite=False --play $i --batch --output tests/golden/${outbase%.vd}.tsv
done
echo '=== git diffs ==='
git --no-pager diff --exit-code --numstat tests/
