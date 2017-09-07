#!/usr/bin/env bash

# Usage $0

for i in tests/*.vd ; do
    echo "--- $i"
    PYTHONPATH=. bin/vd --confirm-overwrite=False --play $i -- --output=${i%.vd}.tsv
done

git --no-pager diff --exit-code --numstat tests/
