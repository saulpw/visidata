#!/bin/bash

# Usage: $0
#    builds sdist and wheel into dist/ with fresh man pages (run via `make dist`)
#    requires: python3 -m build, twine, groff, man-db

set -eu -o pipefail

cd "$(dirname $0)/.."

rm -rf dist build
rm -f visidata/man/vd.1 visidata/man/visidata.1 visidata/man/vd.txt
python3 -m build
chmod -R a+rX dist

for f in visidata/man/vd.1 visidata/man/vd.txt; do
    unzip -l dist/*.whl | grep -q "$f" || { echo "wheel is missing $f"; exit 1; }
    tar tzf dist/*.tar.gz | grep -q "$f" || { echo "sdist is missing $f"; exit 1; }
done

twine check dist/*
