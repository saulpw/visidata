#!/usr/bin/env bash
set -e
source tests/testenv.sh
vd_testtmp

RC="$VD_TESTTMP/test-setenv.py"
DATA="$VD_TESTTMP/test-setenv.tsv"
CMDLOG="$VD_TESTTMP/test-setenv.vdj"
RESULT="$VD_TESTTMP/test-setenv-result.tsv"

printf '%s\n' "vd.setEnvvar('LC_NUMERIC', 'en_US.UTF-8')" > "$RC"
printf 'result\n1,234.5\n' > "$DATA"

env LC_ALL= LC_NUMERIC=C $VD --config "$RC" --batch "$DATA" --play <(printf '%s\n' \
    'type-floatlocale' \
    'cmdlog-sheet') --output "$CMDLOG"

$PYTHON - "$CMDLOG" <<'PY'
import json
import sys

with open(sys.argv[1]) as fp:
    rows = [json.loads(line) for line in fp if not line.startswith('#')]
envrows = [r for r in rows if r['longname'] == 'set-envvar']
assert len(envrows) == 1, envrows
assert rows[0] == envrows[0], rows
assert not envrows[0].get('sheet'), envrows
assert envrows[0]['input'] == 'LC_NUMERIC=en_US.UTF-8', envrows
PY

env LC_ALL= LC_NUMERIC=C $VD --batch --play "$CMDLOG" --output "$RESULT"
diff -u tests/golden/issue3195.tsv "$RESULT"
SESSION="$VD_TESTTMP/test-setenv-reopened.vdx"
printf '%s\n' "vd.setEnvvar('LC_NUMERIC', 'C')" > "$RC"
printf '%s\n' \
    'open-new' \
    "open-file $DATA" \
    'quit-sheet' \
    'set-envvar LC_NUMERIC=en_US.UTF-8' \
    'jump-sheet test-setenv' \
    'type-floatlocale' > "$SESSION"

env LC_ALL= LC_NUMERIC=C $VD --config "$RC" --batch --play "$SESSION" --output "$RESULT"
diff -u tests/golden/issue3195.tsv "$RESULT"
printf '%s\n' 'cmdlog-sheet' >> "$SESSION"
env LC_ALL= LC_NUMERIC=C $VD --config "$RC" --batch --play "$SESSION" --output "$CMDLOG"
env LC_ALL= LC_NUMERIC=C $VD --batch --play "$CMDLOG" --output "$RESULT"
diff -u tests/golden/issue3195.tsv "$RESULT"

$PYTHON - "$CMDLOG" <<'PY'
import json
import sys

with open(sys.argv[1]) as fp:
    rows = [json.loads(line) for line in fp if not line.startswith('#')]
envrows = [r for r in rows if r['longname'] == 'set-envvar']
assert [r['input'] for r in envrows] == ['LC_NUMERIC=C', 'LC_NUMERIC=en_US.UTF-8'], envrows
assert all(not r.get('sheet') for r in envrows), envrows
PY

echo "rc and reopened-sheet locales saved and replayed in $(elapsed)s"
