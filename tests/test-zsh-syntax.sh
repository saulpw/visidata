#!/usr/bin/env bash
# Ensure VisiData can generate zsh completions, and that option specs with
# apostrophe-bearing defaults (e.g. http_req_headers) stay a single shell word.
source tests/testenv.sh
set -e

COMPFILE=$(mktemp)
trap 'rm -f "$COMPFILE"' EXIT

$PYTHON dev/zsh-completion.py "$COMPFILE"

# Regression check: the http_req_headers spec must parse as exactly one shell
# argument. Its default value contains single quotes, which previously split
# the spec into multiple words and produced an invalid zsh option definition.
$PYTHON - "$COMPFILE" <<'PYEOF'
import shlex
import sys

compfile = sys.argv[1]

spec = None
with open(compfile) as f:
    for line in f:
        stripped = line.strip()
        # Each flag sits on its own template line; alias specs start with "{".
        if stripped.startswith("--http_req_headers"):
            # Drop the trailing line-continuation backslash if present.
            spec = stripped[:-1].rstrip() if stripped.endswith("\\") else stripped
            break

assert spec is not None, "no --http_req_headers spec found in generated completion"

args = shlex.split(spec)
assert len(args) == 1, f"expected 1 shell word, got {len(args)}: {args!r}"
# The dict-valued default must survive intact through the shell quoting.
assert "'User-Agent'" in args[0], f"dict default not preserved: {args[0]!r}"

print("http_req_headers spec parses as a single argument")
PYEOF

echo "1 passed in $(elapsed)s"
