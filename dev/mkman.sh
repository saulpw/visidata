#!/bin/bash

# Usage: $0
#    builds vd(1) man page in src repo (to be checked in)

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

# build docs/man.md

manhtml="$VD"/docs/man.md
echo '---' > "$manhtml"
echo 'eleventyNavigation:' >> "$manhtml"
echo '  key: Quick Reference Guide' >> "$manhtml"
echo '  order: 2' >> "$manhtml"
echo 'permalink: /man/' >> "$manhtml"
echo '---' >> "$manhtml"
echo '<section><pre id="manpage" class="whitespace-pre-wrap text-xs">' >> "$manhtml"

MAN_KEEP_FORMATTING=1 COLUMNS=1000 man "$MAN"/vd.1 | ul | aha --no-header >> "$manhtml"
echo '</pre></section>' >> "$manhtml"

echo "Files are written to $BUILD"
