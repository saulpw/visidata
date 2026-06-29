#!/usr/bin/env bash
# Test loading data from an http URL (manual-tests.md #15) and following an html
# link via open-row (manual-tests.md #22).
#
# Served from a loopback http.server on an ephemeral port so CI never touches the
# external network (dev/TESTING.md: "Never fetch from the network in tests").
# This exercises the same code path as a real URL: scheme dispatch (openurl_http),
# urllib fetch with the default User-Agent, content-type/extension filetype guess,
# loader dispatch, and lxml link-resolution against the page URL.
#
# Fixtures live in tests/url/ (usage.tsv + page.html linking to it). The html
# subtest needs lxml; it is skipped (not failed) when lxml is absent.
source tests/testenv.sh
FAIL=0

DOCROOT=tests/url
PORTFILE=$(mktemp)
trap 'kill "$SRVPID" 2>/dev/null; rm -f "$PORTFILE"' EXIT

# loopback static file server; first stdout line is the bound ephemeral port
python3 - "$DOCROOT" <<'PY' >"$PORTFILE" 2>/dev/null &
import sys, http.server, socketserver
root = sys.argv[1]
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=root, **k)
    def log_message(self, *a): pass
httpd = socketserver.TCPServer(("127.0.0.1", 0), H)
print(httpd.server_address[1], flush=True)
httpd.serve_forever()
PY
SRVPID=$!

PORT=""
for _ in $(seq 1 50); do PORT=$(cat "$PORTFILE"); [[ -n "$PORT" ]] && break; sleep 0.1; done
[[ -n "$PORT" ]] || { echo "FAIL: loopback server did not start"; exit 1; }
BASE="http://127.0.0.1:$PORT"

mkdir -p "$OUTDIR"

diffcheck() {
    local desc="$1" expected="$2" got="$3"
    if ! diff -q "$expected" "$got" >/dev/null 2>&1; then
        echo "FAIL: $desc"
        diff "$expected" "$got" 2>&1 | head
        FAIL=1
    fi
}

# === #15: load a tsv directly from a URL ===
$VD --batch "$BASE/usage.tsv" -o "$OUTDIR/url-direct.tsv" 2>/dev/null
diffcheck "load tsv from http url" "$DOCROOT/usage.tsv" "$OUTDIR/url-direct.tsv"

# === #22: open an html page, dive into its links sheet, follow the link ===
# open-row (index -> links sheet), open-row (link row -> openSource the absolute
# url resolved from the relative href against the page URL -> loads usage.tsv).
if python3 -c 'import lxml' 2>/dev/null; then
    $VD --batch "$BASE/page.html" --play <(printf 'open-row\nopen-row\n') \
        -o "$OUTDIR/url-htmllink.tsv" 2>/dev/null
    diffcheck "open-row on html link loads linked tsv" "$DOCROOT/usage.tsv" "$OUTDIR/url-htmllink.tsv"
else
    echo "SKIP: open-row html-link subtest (lxml not installed)"
fi

if [[ $FAIL -ne 0 ]]; then
    echo "FAILED in $(elapsed)s"
    exit 1
fi
echo "all url tests passed in $(elapsed)s"
