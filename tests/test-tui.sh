#!/usr/bin/env bash
# Interactive smoke: open common prompts in a real terminal (tmux)
# budget: ~0.4s per case, 10 max; one per input code path, not per command
source tests/testenv.sh
command -v tmux >/dev/null || { echo "SKIP: tmux not installed; 0 passed in $(elapsed)s"; exit 0; }

TM="tmux -L vdtest$$ -f /dev/null"
SCREEN=$(mktemp)
trap '$TM kill-server 2>/dev/null; rm -f "$SCREEN"' EXIT
NPASS=0
FAILED=""

# waitfor <session> <grep args>: poll the screen up to 10s; fail on an error
waitfor() {
    local s=$1; shift
    for _ in $(seq 50); do
        $TM capture-pane -p -t "$s" > "$SCREEN"
        grep -qE "[A-Za-z]+Error: " "$SCREEN" && return 1
        grep -q "$@" "$SCREEN" && return 0
        sleep 0.2
    done
    return 1
}

# smoke <name> <expected text> <vd args> <keys...>
# no --debug: its debug statuses hide the help sidebar
smoke() {
    local name=$1 want=$2 args=$3; shift 3
    $TM new-session -d -s "$name" -x 120 -y 30 "$VD -N $args; sleep 60"
    if waitfor "$name" -E '[0-9]+ (rows|files)' && $TM send-keys -t "$name" "$@" && waitfor "$name" -F -- "$want"; then
        NPASS=$((NPASS + 1))
    else
        echo "FAIL: $name: '$want' not on screen"
        grep -v '^\s*$' "$SCREEN" | tail -20
        FAILED="$FAILED $name"
    fi
    $TM kill-session -t "$name"
}

smoke exec-longname   'command name:'       tests/data1.tsv Space
smoke regex-subst     'search:'             tests/data1.tsv '*'
smoke select-regex    'select regex:'       tests/data1.tsv '|'
smoke macro-record    'bind macro to:'      tests/data1.tsv m = 'Key + "-x"' Enter m
smoke sidebar-cycle   '[2/3]'               tests/ Space C-g

echo "$NPASS passed in $(elapsed)s"
[ -z "$FAILED" ]
