#!/usr/bin/env bash
# Test option precedence: native default < visidatarc < CLI; --config selection;
# CLI options global without -g.
#
# Automates this former manual test (removed from dev/checklists/manual-tests.md):
#   12. Options
#       - local + global options should be set appropriately
#           - bin/vd -f tsv sample_data/sample.tsv -f csv sample_data/benchmark.csv
#           - bin/vd sample_data/y77d-th95.json.gz -f txt
#       - the order in which options should be applied is
#           - native_options -> cli_options for config/visidata_dir/imports -> plugin_imports -> visidatarc -> rest_of_cli
#           - check that cli overwrites visidatarc
#           - check that --config selects which visidatarc to load
#           - check that visidatarc can set plugin options
#       - -w and others should be set "globally" (work without -g option)
#       - bin/vd -f xlsx sample_data/sample-sales-reps.xlsx -f json sample_data/y77d-th95.json.gz
#           - the xlsx sheet should have filetype 'xlsx'
#       - bin/vd sample_data/sample-sales-reps.xlsx -n -f xlsx
#           - `o` another file; check that it loads; check it does not show 'xlsx' on its sheet-specific options
#
# Reads the resolved option via an expr column dumped with `-O -` (see
# test-options-config.sh). Every invocation loads an isolated --config so the
# result never depends on the developer's real ~/.visidatarc.
#
# The -f/filetype sub-cases above describe pre-#3139 behavior: since #3139, -f
# attaches to the source path, never as a sheet option, so the OptionsSheet no
# longer shows 'xlsx'. That per-path behavior is exercised by tests/test-filetype.sh
# (manual-tests.md item 13 "Filetype"), not here.
source tests/testenv.sh
FAIL=0

RCE=$(mktemp)   # empty (isolation only)
RCA=$(mktemp)   # default_width=33
RCB=$(mktemp)   # default_width=77
trap 'rm -f "$RCE" "$RCA" "$RCB"' EXIT
printf "options.motd_url=''\n" > "$RCE"
printf "options.motd_url=''\noptions.default_width=33\n" > "$RCA"
printf "options.motd_url=''\noptions.default_width=77\n" > "$RCB"

DIR="--visidata-dir tests/.visidata"
VDE="$PYTHON -m visidata --config $RCE $DIR"
VDA="$PYTHON -m visidata --config $RCA $DIR"
VDB="$PYTHON -m visidata --config $RCB $DIR"

CSV=sample_data/benchmark.csv
TSV=sample_data/sample.tsv

dw() { printf 'addcol-expr _t=options.default_width\n'; }

check() {
    local desc="$1" expected="$2" got="$3"
    if [[ "$got" != "$expected" ]]; then
        echo "FAIL: $desc (expected '$expected', got '$got')"
        FAIL=1
    fi
}

# native default (rc sets nothing): default_width builtin default is 20
check "native default" 20 "$($VDE --batch $CSV --play <(dw) -O -)"
# visidatarc sets the option
check "visidatarc value" 33 "$($VDA --batch $CSV --play <(dw) -O -)"
# --config selects which visidatarc loads (rcB)
check "--config selects rc" 77 "$($VDB --batch $CSV --play <(dw) -O -)"
# CLI overrides visidatarc (rcA's 33)
check "CLI overrides visidatarc" 99 "$($VDA --default-width 99 --batch $CSV --play <(dw) -O -)"
# CLI option is global without -g: a file opened at runtime inherits it
check "CLI global without -g" 99 \
    "$($VDE --default-width 99 --batch $CSV --play <(printf 'open-file %s\naddcol-expr _t=options.default_width\n' "$TSV") -O -)"
# sanity: without the CLI flag, the runtime-opened file is the native default
check "runtime file native default" 20 \
    "$($VDE --batch $CSV --play <(printf 'open-file %s\naddcol-expr _t=options.default_width\n' "$TSV") -O -)"

if [[ $FAIL -ne 0 ]]; then
    echo "FAILED in $(elapsed)s"
    exit 1
fi
echo "all option-precedence tests passed in $(elapsed)s"
