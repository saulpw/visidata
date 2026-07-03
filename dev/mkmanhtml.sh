#!/bin/bash

# Usage: $0
#    builds docs/man.md for visidata.org from visidata/man/vd.1 (run via `make man-html`)
#    requires: man, ul, aha; run `make man` first

set -eu -o pipefail

VD=$(dirname $0)/..
MAN=$VD/visidata/man

manhtml="$VD"/docs/man.md
echo '---' > "$manhtml"
echo 'eleventyNavigation:' >> "$manhtml"
echo '  key: Quick Reference Guide' >> "$manhtml"
echo '  order: 2' >> "$manhtml"
echo 'permalink: /man/' >> "$manhtml"
echo '---' >> "$manhtml"
echo '<section><pre id="manpage" class="whitespace-pre-wrap text-xs">' >> "$manhtml"

# GROFF_NO_SGR: ul chokes on SGR escapes from newer groff
GROFF_NO_SGR=1 MAN_KEEP_FORMATTING=1 COLUMNS=1000 man "$MAN"/vd.1 | ul | aha --no-header >> "$manhtml"
echo '</pre></section>' >> "$manhtml"

echo "Wrote $manhtml"
