#!/usr/bin/env bash
# Bash-driven checks for v3.4 features that are not golden-output shaped:
#   d) `z Ctrl+S` on the Options Sheet saves edited options to the config file (#2206)
#   e) `--profile` dumps a main-thread profile (vd.pyprof)
#
# Both use an isolated --config/--visidata-dir under a temp dir so they never
# touch the developer's real ~/.visidatarc, and clean up on exit.
source tests/testenv.sh
FAIL=0

ROOT=$PWD
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

RC="$WORK/visidatarc"
: > "$RC"   # empty config to append into
VDW="$PYTHON -m visidata --config $RC --visidata-dir $WORK/vd"

check() {
    local desc="$1" expected="$2" got="$3"
    if [[ "$got" != "$expected" ]]; then
        echo "FAIL: $desc (expected '$expected', got '$got')"
        FAIL=1
    fi
}

# === d) commit-sheet (z Ctrl+S) on the Options Sheet writes overrides to config ===
# set one option non-default via CLI, open the global options sheet, commit (-y
# clears commit's confirm), then confirm the option was appended to the config.
$VDW -y --default-width=99 --batch tests/newcmds-nums.csv \
    --play <(printf 'options-global\ncommit-sheet\n') >/dev/null 2>&1
if grep -q '^options.default_width=99$' "$RC"; then
    saved=yes
else
    saved=no
fi
check "z Ctrl+S saves edited option to config file" "yes" "$saved"

# === e) --profile dumps a profile file (vd.pyprof) to the cwd ===
# run inside the temp dir so the dump lands there, not in the repo root
( cd "$WORK" && $VDW --profile --batch "$ROOT/tests/newcmds-nums.csv" -o out.tsv >/dev/null 2>&1 )
check "--profile produces vd.pyprof" "yes" "$([[ -s "$WORK/vd.pyprof" ]] && echo yes || echo no)"

if [[ $FAIL -ne 0 ]]; then
    echo "FAILED in $(elapsed)s"
    exit 1
fi
echo "all newfeatures tests passed in $(elapsed)s"
