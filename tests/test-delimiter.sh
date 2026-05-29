#!/usr/bin/env bash
# Test delimiter handling across formats and CLI args  #2727
source tests/testenv.sh

set -e

VDB="$VD --batch"
FAIL=0

check() {
    local desc="$1" expected="$2"
    shift 2
    local result rc
    result=$($VDB "$@" -O -) && rc=$? || rc=$?
    if [[ $rc -ne 0 ]]; then
        echo "FAIL: $desc (vd exited with $rc)"
        FAIL=1
    elif [[ "$result" != "$expected" ]]; then
        echo "FAIL: $desc"
        echo "  expected: '$expected'"
        echo "  got:      '$result'"
        FAIL=1
    fi
}

save_check() {
    local desc="$1" infile="$2" outfile="$3"
    shift 3
    $VDB "$@" "$infile" -o "$outfile"
    if ! diff "$infile" "$outfile" > /dev/null 2>&1; then
        echo "FAIL: $desc"
        diff "$infile" "$outfile" | head -5
        FAIL=1
    fi
}

mkdir -p $OUTDIR

# Create test fixtures
printf 'a|b|c\n1|2|3\n4|5|6\n' > $OUTDIR/test.psv
printf 'a;b;c\n1;2;3\n4;5;6\n' > $OUTDIR/test-semi.csv
printf 'a|b|c\n1|2|3\n4|5|6\n' > $OUTDIR/pipe.txt

# === Basic format loading ===
check "tsv: first cell" "2016-01-06" sample_data/sample.tsv
check "csv: first cell" "7/3/2018 1:47p" sample_data/benchmark.csv
check "psv: first cell" "1" $OUTDIR/test.psv
check "psv: second col" "2" $OUTDIR/test.psv +1:0
check "usv: first cell" "d" sample_data/test.usv

# === -d (generic delimiter) for TSV-family ===
check "-d pipe on .txt" "1" $OUTDIR/pipe.txt -d "|"
check "-d pipe on .txt col1" "2" $OUTDIR/pipe.txt -d "|" +1:0

# === -d for CSV (#2727) ===
check "-d semicolon on .csv" "1" $OUTDIR/test-semi.csv -f csv -d ";"
check "-d semicolon on .csv col1" "2" $OUTDIR/test-semi.csv -f csv -d ";" +1:0

# === --csv-delimiter ===
check "--csv-delimiter semicolon" "1" $OUTDIR/test-semi.csv --csv-delimiter ";"

# === Roundtrip saves (same file format) ===
save_check "tsv roundtrip" sample_data/sample.tsv $OUTDIR/roundtrip.tsv
save_check "psv roundtrip" $OUTDIR/test.psv $OUTDIR/roundtrip.psv
save_check "usv roundtrip" sample_data/test.usv $OUTDIR/roundtrip.usv

# CSV roundtrip (header check — csv may normalize quoting)
$VDB sample_data/benchmark.csv -o $OUTDIR/roundtrip.csv
diff <(head -1 sample_data/benchmark.csv) <(head -1 $OUTDIR/roundtrip.csv) || { echo "FAIL: csv roundtrip header"; FAIL=1; }

# -d roundtrip: load with -d, save, verify delimiter in output
$VDB $OUTDIR/pipe.txt -d "|" -o $OUTDIR/pipe-rt.txt
grep -q '|' $OUTDIR/pipe-rt.txt || { echo "FAIL: -d pipe roundtrip save"; FAIL=1; }

# Semicolon CSV roundtrip via -d
$VDB $OUTDIR/test-semi.csv -f csv -d ";" -o $OUTDIR/semi-rt.csv
grep -q ';' $OUTDIR/semi-rt.csv || { echo "FAIL: -d semicolon csv roundtrip"; FAIL=1; }

# === Save-as to new file (different path string) ===
# save_psv should set delimiter on new output path
$VDB $OUTDIR/test.psv -o $OUTDIR/new-output.psv
grep -q '|' $OUTDIR/new-output.psv || { echo "FAIL: save-as new .psv"; FAIL=1; }

# === Cross-format save ===
# PSV loaded, saved as CSV — should use csv defaults, not pipe
$VDB $OUTDIR/test.psv -o $OUTDIR/cross.csv
head -1 $OUTDIR/cross.csv | grep -q ',' || { echo "FAIL: psv->csv uses comma"; FAIL=1; }
head -1 $OUTDIR/cross.csv | grep -qv '|' || { echo "FAIL: psv->csv no pipes"; FAIL=1; }

if [[ $FAIL -eq 1 ]]; then
    echo "FAILED in $(elapsed)s"
    exit 1
fi
echo "all delimiter tests passed in $(elapsed)s"
