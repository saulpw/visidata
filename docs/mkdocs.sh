#!/bin/sh

set -e

VDDIR=~/git/visidata
MANDIR=$VDDIR/docs/man

export PYTHONPATH=$VDDIR:$VDDIR/visidata
export PATH=$VDDIR/bin:$PATH

$MANDIR/parse_options.py vd
$MANDIR/parse_options.py

soelim $MANDIR/vd-skel.1 > $MANDIR/vd-pre.1
preconv -e utf8 $MANDIR/vd-pre.1 > $MANDIR/vd.1
MAN_KEEP_FORMATTING=1 COLUMNS=100 man $MANDIR/vd.1 | ul | aha > $MANDIR/vd-man.html
