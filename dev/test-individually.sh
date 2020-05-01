#!/usr/bin/env bash
# usage: ./dev/test-individually.sh [<tests/name.vd> […]]
#
# Runs tests/*.vd or the given test files individually and summarize failures
# at the end.
#
# The stdout and stderr of each test is saved in tests/log/<name>.log.  Files
# in tests/golden/ which are rewritten by tests are not saved.
#
# Your repository must be clean: no uncommitted changes or untracked files are
# allowed.  The working dir is restored after each test, and this policy
# prevents you from losing your changes.  It also prevents such changes from
# accidentally perturbing test results.
#
set -euo pipefail
shopt -s nullglob

if [[ -n $(git status --porcelain --untracked-files=all) ]]; then
    echo "repo is dirty; aborting" >&2
    exit 1
fi

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

        # Restore working dir to a pristine state.
        git restore .
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
