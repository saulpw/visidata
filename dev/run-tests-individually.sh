#!/usr/bin/env bash
# usage: ./dev/run-tests-individually.sh [<tests/name.vd> […]]
#
# Runs each test in its own vd process, for full isolation.
# Slower than `dev/test.sh` (which batches all tests into one process),
# but useful for debugging cross-test contamination.
#
# The stdout and stderr of each test is saved in tests/log/<name>.log.
# Test output goes to tests/output/ (gitignored), golden files are not modified.
#
set -euo pipefail
shopt -s nullglob

main() {
    local test_file test_name
    local -a test_files failures

    test_files=("$@")
    failures=()

    if [[ ${#test_files[@]} -eq 0 ]]; then
        test_files=(tests/*.vd)
    fi

    # Clean logs
    mkdir -p tests/log/
    rm -f tests/log/*.log

    # Run each test file separately
    trap 'exit 130' SIGINT

    for test_file in "${test_files[@]}"; do
        test_name="$(basename "$test_file" .vd)"

        if ./dev/test.sh "$test_name" >tests/log/"$test_name".log 2>&1; then
            pass "$test_name"
        else
            fail "$test_name"
            failures+=("$test_file")
        fi
    done

    if [[ ${#failures[@]} -ne 0 ]]; then
        printf "\n" >&2
        printf "%d failed tests:\n" "${#failures[@]}" >&2
        printf "  %s\n" "${failures[@]}" >&2
    fi
}

pass() {
    echo "$(colorize "green bold" "    ok")" "$@"
}

fail() {
    echo "$(colorize "red   bold" "not ok")" "$@"
}

colorize() {
    git config --get-color "" "$1"
    echo -n "$2"
    git config --get-color "" reset
}

main "$@"
