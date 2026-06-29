#!/usr/bin/env bash
# Test save overwrite semantics and multi-sheet save targets.
#
# Automates these former manual tests (see dev/checklists/manual-tests.md):
#   19. Save to a non-existent format.
#       - Saves to save-filetype by default
#       - If save-filetype is a non-existent format, blocks
#       - test overwrite=y,n,c
#   20. Save multiple sheets to a single non-embeddable format
#       - save name makes sense
#       - fails if not offered a directory
#       - succeeds if offered a directory
#
# The #19 "fallback to save_filetype + confirm" half is covered by
# tests/test-filetype.sh (the ft-out.xyz cases, #2286). This script covers the
# overwrite=c/n/y matrix and the #20 multi-sheet targets.
#
# Batch `-o` saves only the active sheet via saveSheets(..., confirm_overwrite=
# not couldOverwrite()): overwrite=c/y silently overwrite; overwrite=n (readonly)
# refuses (#2286, "[batch] honor --readonly for -o"). Multi-sheet save needs the
# interactive `save-all` command, driven here through a --play file.
#
# The interactive y/n/c confirm *prompt* for overwrite=c is not reachable in
# batch (couldOverwrite short-circuits it) and stays a manual check.
source tests/testenv.sh
FAIL=0

VDB="$VD --batch"
T=$OUTDIR
mkdir -p "$T"
rm -rf "$T"/sv-* 2>/dev/null
# save-all creates a scratch dir (sv-dir) under tests/output; remove all sv-*
# on exit so the vdx golden harness's `rm -f` cleanup does not warn on it
trap 'rm -rf "$T"/sv-*' EXIT

CSV1="$T/sv1.csv"
CSV2="$T/sv2.csv"
printf 'a,b\n1,2\n' > "$CSV1"
printf 'x,y\n9,8\n' > "$CSV2"

check() {
    local desc="$1" expected="$2" got="$3"
    if [[ "$got" != "$expected" ]]; then
        echo "FAIL: $desc (expected '$expected', got '$got')"
        FAIL=1
    fi
}

# === #19 overwrite matrix (batch -o onto an existing file) ===

# overwrite=c (default): silently overwrites the existing target
printf 'PRE\n' > "$T/sv-c.tsv"
$VDB "$CSV1" -o "$T/sv-c.tsv" 2>/dev/null
check "overwrite=c overwrites existing -o" $'a\tb' "$(head -1 "$T/sv-c.tsv" | tr -d '\r')"

# overwrite=y: also overwrites
printf 'PRE\n' > "$T/sv-y.tsv"
$VDB --overwrite=y "$CSV1" -o "$T/sv-y.tsv" 2>/dev/null
check "overwrite=y overwrites existing -o" $'a\tb' "$(head -1 "$T/sv-y.tsv" | tr -d '\r')"

# overwrite=n / --readonly: refuses; existing file is left untouched
printf 'PRE\n' > "$T/sv-n.tsv"
$VDB --readonly "$CSV1" -o "$T/sv-n.tsv" 2>/dev/null
check "--readonly refuses to overwrite existing -o" "PRE" "$(head -1 "$T/sv-n.tsv" | tr -d '\r')"
# overwrite=n spelled out is the same alias target
printf 'PRE\n' > "$T/sv-n2.tsv"
$VDB --overwrite=n "$CSV1" -o "$T/sv-n2.tsv" 2>/dev/null
check "overwrite=n refuses to overwrite existing -o" "PRE" "$(head -1 "$T/sv-n2.tsv" | tr -d '\r')"

# readonly still writes a brand-new file (overwrite check only guards existing)
rm -f "$T/sv-new.tsv"
$VDB --readonly "$CSV1" -o "$T/sv-new.tsv" 2>/dev/null
check "--readonly still creates a new -o file" $'a\tb' "$(head -1 "$T/sv-new.tsv" 2>/dev/null | tr -d '\r')"

# === #20 save multiple sheets (save-all, via --play) ===
# These runs give no -o, so batch dumps the active sheet to the piped stdout;
# that dump is unrelated to the save-all file side-effects, so discard it.

# to a directory (trailing /): one file per sheet, named after each sheet
rm -rf "$T/sv-dir"
$VDB "$CSV1" "$CSV2" --play <(printf 'save-all %s/sv-dir/\n' "$T") >/dev/null 2>&1
check "save-all to dir: file per sheet, sensible names" "sv1.tsv sv2.tsv" \
    "$(ls "$T/sv-dir" 2>/dev/null | sort | tr '\n' ' ' | sed 's/ $//')"
check "save-all to dir: sv1 content correct" $'a\tb' "$(head -1 "$T/sv-dir/sv1.tsv" 2>/dev/null | tr -d '\r')"

# to a single non-embeddable file (.tsv): fails, writes nothing
rm -f "$T/sv-multi.tsv"
$VDB "$CSV1" "$CSV2" --play <(printf 'save-all %s/sv-multi.tsv\n' "$T") >/dev/null 2>&1
check "save-all multi to non-dir tsv fails (no file)" "no" \
    "$([[ -e "$T/sv-multi.tsv" ]] && echo yes || echo no)"

# to a single embeddable file (.html): succeeds, one table per sheet
rm -f "$T/sv-all.html"
$VDB "$CSV1" "$CSV2" --play <(printf 'save-all %s/sv-all.html\n' "$T") >/dev/null 2>&1
check "save-all multi to embeddable html: 2 tables" "2" \
    "$(grep -c '<table' "$T/sv-all.html" 2>/dev/null)"

if [[ $FAIL -ne 0 ]]; then
    echo "FAILED in $(elapsed)s"
    exit 1
fi
echo "all save tests passed in $(elapsed)s"
