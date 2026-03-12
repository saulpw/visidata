#!/usr/bin/env bash
# Test format round-trip: load file, save it, reload saved version, save again.
# Verifies that VisiData's save is idempotent for each format.
# Usage: test-roundtrip.sh [format ...]
#   With no args, tests all formats with roundtrip set in dev/formats.jsonl

source tests/testenv.sh
mkdir -p $OUTDIR

FAILED=0
PASSED=0
SKIPPED=0

test_roundtrip() {
    local fmt="$1" src="$2"
    local out1="$OUTDIR/roundtrip1.$fmt"
    local out2="$OUTDIR/roundtrip2.$fmt"

    if [ ! -f "$src" ]; then
        echo "SKIP: $fmt (missing $src)"
        SKIPPED=$((SKIPPED + 1))
        return
    fi

    rm -f "$out1" "$out2"

    # First pass: load source, save as format
    $VD "$src" --batch -o "$out1"
    if [ ! -f "$out1" ]; then
        echo "FAIL: $fmt (no output from first pass)"
        FAILED=$((FAILED + 1))
        return
    fi

    # Second pass: reload saved version, save again
    $VD "$out1" --batch -o "$out2"
    if [ ! -f "$out2" ]; then
        echo "FAIL: $fmt (no output from second pass)"
        FAILED=$((FAILED + 1))
        return
    fi

    # Compare: second save should match first (idempotent round-trip)
    if diff -q "$out1" "$out2" >/dev/null 2>&1; then
        PASSED=$((PASSED + 1))
    else
        echo "DIFF: roundtrip $fmt"
        diff "$out1" "$out2"
        FAILED=$((FAILED + 1))
    fi
}

# Find a sample file for a given format
find_source() {
    local fmt="$1"
    for dir in sample_data tests; do
        for prefix in benchmark sample test small; do
            local f="$dir/$prefix.$fmt"
            if [ -f "$f" ]; then
                echo "$f"
                return
            fi
        done
    done
}

if [ $# -gt 0 ]; then
    for fmt in "$@"; do
        src=$(find_source "$fmt")
        test_roundtrip "$fmt" "$src"
    done
else
    while IFS= read -r line; do
        read -r fmt src < <($PYTHON -c "
import sys, json
d = json.loads(sys.argv[1])
if d.get('roundtrip'):
    print(d['filetype'], d.get('roundtrip_source', ''))
" "$line" 2>/dev/null)
        [ -z "$fmt" ] && continue
        [ -z "$src" ] && src=$(find_source "$fmt")
        test_roundtrip "$fmt" "$src"
    done < dev/formats.jsonl
fi

[ $SKIPPED -gt 0 ] && SKIP_MSG=", $SKIPPED skipped" || SKIP_MSG=""
if [ $FAILED -gt 0 ]; then
    echo "FAIL: $PASSED passed, $FAILED failed${SKIP_MSG}"
    exit 1
else
    echo "PASS: $PASSED passed${SKIP_MSG}"
fi
