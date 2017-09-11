#!/bin/sh

VDDIR=~/git/visidata

export PYTHONPATH=$VDDIR:$VDDIR/visidata
export PATH=$VDDIR/bin:$PATH

$VDDIR/docs/man/parse_options.py vd
$VDDIR/docs/man/parse_options.py
mv vd-cli.inc $VDDIR/docs/man
mv vd-menu.inc $VDDIR/docs/man
mv vdtui-cli.inc $VDDIR/docs/man
mv vdtui-menu.inc $VDDIR/docs/man
