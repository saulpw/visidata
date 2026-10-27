#!/bin/bash

# Usage: $0
#    builds vd(1) man page in src repo (run via `make man`)
#    requires: soelim, preconv (groff), man

# TODO:
#   - parse_options should be moved to bin/

# -e - exit on error
# -u - exit on undefined
# -o pipefail - exit on error in a pipe
set -eu -o pipefail

VD=$(dirname $0)/..
MAN=$VD/visidata/man
BUILD=/tmp/visidata_manpages

echo "Cleaning up $BUILD"
rm -rf "$BUILD"
mkdir "$BUILD"

export PYTHONPATH=$VD:$VD/visidata
export PATH=$VD/bin:$PATH

cp $MAN/* $BUILD/
$MAN/parse_options.py $BUILD/vd-cli.inc $BUILD/vd-opts.inc

soelim -rt -I $BUILD $BUILD/vd.inc > $BUILD/vd-pre.1
preconv -r -e utf8 $BUILD/vd-pre.1 > $MAN/vd.1
preconv -r -e utf8 $BUILD/vd-pre.1 > $MAN/visidata.1
MANWIDTH=80 man $MAN/vd.1 > $MAN/vd.txt

echo "Man pages written to $MAN"
