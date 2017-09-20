#!/bin/sh

set -e

VDDIR=~/git/visidata
MANDIR=$VDDIR/docs/man

export PYTHONPATH=$VDDIR:$VDDIR/visidata
export PATH=$VDDIR/bin:$PATH

$MANDIR/parse_options.py vd
$MANDIR/parse_options.py

#groff -s -mandoc -Thtml $MANDIR/vd-skel.1
MAN_KEEP_FORMATTING=1 COLUMNS=80 man $MANDIR/vd-skel.1 | ul | aha > $MANDIR/vd-man.html
