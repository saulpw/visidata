#!/usr/bin/env bash
# Test startpos (+N, +col:row) CLI positioning  #2425
source tests/testenv.sh

set -e

VD="$VD --batch -O -"
FAIL=0

check() {
    local desc="$1" expected="$2"
    shift 2
    local result rc
    result=$($VD "$@") && rc=$? || rc=$?
    if [[ $rc -ne 0 ]]; then
        echo "FAIL: $desc (vd exited with $rc)"
        FAIL=1
    elif [[ "$result" != "$expected" ]]; then
        echo "FAIL: $desc (expected '$expected', got '$result')"
        FAIL=1
    fi
}

# default: no positioning, cursor at row 0 col 0
check "default position" "dept" sample_data/employees.sqlite
# +N: row positioning
check "+1 -> emp" "emp" sample_data/employees.sqlite +1
check "+2 -> emp_view" "emp_view" sample_data/employees.sqlite +2

# +col:row positioning (col 1 = 'rows' count column)
check "+1:0 -> 4 (dept rows)" "4" sample_data/employees.sqlite +1:0
check "+1:1 -> 14 (emp rows)" "14" sample_data/employees.sqlite +1:1

# per-file positioning: active sheet is first input
check "a +1 b -> a at row 1" "emp" sample_data/employees.sqlite +1 sample_data/benchmark.csv

# only preceding input gets positioned
check "a +1 b -> b unpositioned" "7/3/2018 1:47p" sample_data/benchmark.csv sample_data/employees.sqlite +1

# subsheet navigation (dept table: deptno=10,20,30,40; dname=ACCOUNTING,RESEARCH,SALES,OPERATIONS)
check "+0:0:: -> dept subsheet" "10" sample_data/employees.sqlite +0:0::
check "+0:dept:: -> dept by name" "10" sample_data/employees.sqlite +0:dept::
check "+0:0:1:0 -> dname col" "ACCOUNTING" sample_data/employees.sqlite +0:0:1:0
check "+0:0::1 -> row 1" "20" sample_data/employees.sqlite +0:0::1

if [[ $FAIL -eq 1 ]]; then
    echo "FAILED in $(elapsed)s"
    exit 1
fi
echo "all startpos tests passed in $(elapsed)s"
