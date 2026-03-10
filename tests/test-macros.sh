#!/usr/bin/env bash
# Test replaying macros  #1652
source tests/testenv.sh
mkdir -p $OUTDIR
XDG_DATA_HOME=tests/xdg/data XDG_CONFIG_HOME=tests/xdg/config \
    $VD --batch -p tests/macros/test_macro.vd --output $OUTDIR/test_macro.tsv
diff tests/macros/golden/test_macro.tsv $OUTDIR/test_macro.tsv
