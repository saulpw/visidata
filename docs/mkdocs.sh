#!/bin/sh

set -e

VDDIR=~/git/visidata
MANDIR=$VDDIR/docs/man

export PYTHONPATH=$VDDIR:$VDDIR/visidata
export PATH=$VDDIR/bin:$PATH

$MANDIR/parse_options.py vd
$MANDIR/parse_options.py

MAN_KEEP_FORMATTING=1 COLUMNS=80 man -E utf8 $MANDIR/vd-skel.1 | ul | aha > $MANDIR/vd-man.html
