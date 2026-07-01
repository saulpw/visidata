#!/usr/bin/env bash
# Test .visidatarc option loading: numeric/boolean/string, global + sheet-specific.
#
# Automates this former manual test (removed from dev/checklists/manual-tests.md):
#   8. .visidatarc
#       - numerical, boolean and string option
#       - sheet-specific and global
#       - motd_url                          <- STILL MANUAL: network fetch, interactive-only
#
# Mechanism: open a data file in batch, add an expr column that evaluates the
# resolved option in sheet scope (options.NAME), and dump the cursor cell with
# `-O -`. addcol-expr lands the cursor on the new column, so no movement needed.
# stderr passes through (visible); $() captures only the stdout value.
source tests/testenv.sh
FAIL=0

RC=$(mktemp)
trap 'rm -f "$RC"' EXIT
cat > "$RC" <<'EOF'
options.motd_url = ''
options.default_width = 33
options.clean_names = True
options.disp_currency_fmt = '#%.02f'
CsvSheet.options.default_width = 44
EOF

VDC="$PYTHON -m visidata --config $RC --visidata-dir tests/.visidata"

CSV=sample_data/benchmark.csv
TSV=sample_data/sample.tsv

# resolve EXPR FILE -> resolved value of python expr (sheet scope) at cursor
resolve() {
    $VDC --batch "$2" --play <(printf 'addcol-expr _t=%s\n' "$1") -O -
}

check() {
    local desc="$1" expected="$2" got="$3"
    if [[ "$got" != "$expected" ]]; then
        echo "FAIL: $desc (expected '$expected', got '$got')"
        FAIL=1
    fi
}

# numeric option, global value resolves on a non-csv sheet
check "numeric global" 33 "$(resolve options.default_width $TSV)"
# numeric option, sheet-specific override (CsvSheet) wins on a csv sheet
check "numeric sheet-specific override" 44 "$(resolve options.default_width $CSV)"
# boolean option, global
check "boolean global" True "$(resolve options.clean_names $TSV)"
# string option, global
check "string global" '#%.02f' "$(resolve options.disp_currency_fmt $TSV)"

if [[ $FAIL -ne 0 ]]; then
    echo "FAILED in $(elapsed)s"
    exit 1
fi
echo "all .visidatarc option tests passed in $(elapsed)s"
