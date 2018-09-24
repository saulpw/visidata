#!/bin/bash

# Usage: $0
#    builds vd(1) man page in src repo (to be checked in)

# TODO:
#   - BUILD should be tmpdir and cleaned up afterwards
#   - parse_options should be moved to bin/

set -e

VD=~/git/visidata
MAN=$VD/visidata/man
BUILD=$VD/_build   # should be tmpdir

export PYTHONPATH=$VD:$VD/visidata
export PATH=$VD/bin:$PATH

cp $MAN/* $BUILD/
$MAN/parse_options.py $BUILD/vd-cli.inc $BUILD/vd-opts.inc

soelim -rt -I $BUILD $BUILD/vd.inc > $BUILD/vd-pre.1
preconv -r -e utf8 $BUILD/vd-pre.1 > $MAN/vd.1
