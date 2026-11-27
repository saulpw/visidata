#!/usr/bin/env bash
# Rebuild sample_data/petshop/ from the canonical tables, regenerate the goldens
# of every test that opens it, and list which outputs and goldens changed.
# Usage: dev/regen-petshop.sh

set -e
cd "$(dirname "$0")/.."

source tests/testenv.sh
vd_testtmp

export LC_NUMERIC="en_US.UTF-8"
export LC_TIME="en_US.UTF-8"
export XDG_DATA_HOME=tests/xdg/data

$PYTHON dev/mkpetshop.py

for t in $(grep -l 'sample_data/petshop/' tests/*.vd tests/*.vdj tests/*.vdx 2>/dev/null); do
    testname=$(basename "${t%.vd*}")
    for golden in tests/golden/"$testname".*; do
        [ -e "$golden" ] || continue
        $VD --play "$t" --batch --output "$golden" || echo "FAIL: $t"
    done
done

git status --short -- sample_data/petshop tests/golden
