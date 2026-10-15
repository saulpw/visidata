#!/usr/bin/env bash
# Test that DirSheet defers filesystem changes until commit-sheet (manual-tests.md #23).
#
# DirSheet has defer=True: editing a filename cell or deleting a row only stages
# the change; the real rename/unlink happens when commit-sheet runs (which calls
# confirmOverwrite, so -y is needed to clear its confirm in batch). Each case uses
# a fresh dir with a single file, so the cursor is unambiguously on that file.
source tests/testenv.sh
vd_testtmp
FAIL=0

VDB="$VD -y --batch"
T="$VD_TESTTMP/test-dirsheet"

# run <dir> <play-commands>: drive a DirSheet on <dir>; discard the batch
# active-sheet dump (unrelated to the filesystem side-effects under test).
run() {
    local dir="$1" cmds="$2"
    $VDB "$dir" --play <(printf '%b' "$cmds") >/dev/null 2>&1
}

check() {
    local desc="$1" expected="$2" got="$3"
    if [[ "$got" != "$expected" ]]; then
        echo "FAIL: $desc (expected '$expected', got '$got')"
        FAIL=1
    fi
}

# === rename is deferred: editing the filename cell does NOT rename on disk ===
mkdir -p "$T/ds-defer"; echo hi > "$T/ds-defer/orig.txt"
run "$T/ds-defer" 'col filename\nedit-cell renamed.txt\n'
check "edit filename without commit leaves file unrenamed" "orig.txt" "$(ls "$T/ds-defer")"

# === commit-sheet applies the rename ===
mkdir -p "$T/ds-rename"; echo hi > "$T/ds-rename/orig.txt"
run "$T/ds-rename" 'col filename\nedit-cell renamed.txt\ncommit-sheet\n'
check "commit-sheet renames file on disk" "renamed.txt" "$(ls "$T/ds-rename")"

# === delete-row is deferred: no commit leaves the file in place ===
mkdir -p "$T/ds-keep"; echo hi > "$T/ds-keep/keep.txt"
run "$T/ds-keep" 'delete-row\n'
check "delete-row without commit leaves file" "keep.txt" "$(ls "$T/ds-keep")"

# === commit-sheet applies the delete ===
mkdir -p "$T/ds-del"; echo hi > "$T/ds-del/victim.txt"
run "$T/ds-del" 'delete-row\ncommit-sheet\n'
check "commit-sheet removes file on disk" "" "$(ls "$T/ds-del")"

if [[ $FAIL -ne 0 ]]; then
    echo "FAILED in $(elapsed)s"
    exit 1
fi
echo "all dirsheet tests passed in $(elapsed)s"
