import re
import sys
import time

from visidata import vd, BaseSheet, Path, VisiData

vd.replay_output_path = ''  # output path set by replay-reset, used by replay-output
vd.replay_line = 0  # current line number within a test
vd.replay_start_time = 0  # timestamp when current test started
vd.replay_allowed_errors = []  # set by allow-error, checked by status hook


@VisiData.before
def replayOne(vd, r):
    vd.replay_line += 1


@BaseSheet.api
def replay_reset(vs):  # noqa: ARG001
    'Initialize state for a new test.'
    p = vd.input("output path: ")
    vd.resetVisiData()
    vd.options.batch = True
    vd.replay_output_path = p
    vd.replay_line = 0
    vd.replay_start_time = time.time()
    vd.replay_allowed_errors = []
    vd.statusHistory.clear()  # clear for cross-test isolation


@BaseSheet.api
def replay_end(vs):  # noqa: ARG001
    'Reset state for next test (no output).'
    if vd.options.debug:
        print(f'{time.time() - vd.replay_start_time:.1f}s  {vd.replay_output_path}', file=sys.stderr)

_default_printStatus = VisiData.printStatus

@VisiData.api
def printStatus(vd, *args, priority=0, source=None):
    'Print labeled status during bulk replay; default stderr otherwise.'
    if priority > 0 and vd.replay_output_path:
        msg = str(args[0])
        allowed = any(re.search(p, msg) for p in vd.replay_allowed_errors)
        if not allowed:
            print(f'{vd.replay_output_path}:{vd.replay_line}: {msg}', file=sys.stderr)
        elif vd.options.debug:
            print(f'{vd.replay_output_path}:{vd.replay_line}: {msg} (expected)', file=sys.stderr)
    else:
        _default_printStatus(vd, *args, priority=priority, source=source)

@BaseSheet.api
def replay_output(vs):
    'Save current sheet to path from replay-reset and reset state for next test.'
    outpath = Path(vd.replay_output_path)
    vd.saveSheets(outpath, vs, confirm_overwrite=False)
    vd.sync()
    if vd.options.debug:
        print(f'{time.time() - vd.replay_start_time:.1f}s  {vd.replay_output_path}', file=sys.stderr)


@BaseSheet.api
def allow_error(vs, pattern:str):  # noqa: ARG001
    'suppress expected error messages matching regex pattern during batch replay'
    vd.replay_allowed_errors.append(pattern)


@BaseSheet.api
def replay_exit(vs):  # noqa: ARG001
    'Exit cleanly at end of batch replay.'
    vd.sheets.clear()


BaseSheet.addCommand('', 'replay-reset', 'replay_reset()', 'initialize test state for a test', testable=False)
BaseSheet.addCommand('', 'replay-end', 'replay_end()', 'reset state for test runner (no output)', testable=False)
BaseSheet.addCommand('', 'replay-output', 'replay_output()', 'save output and reset state for test runner', testable=False)
BaseSheet.addCommand('', 'replay-exit', 'replay_exit()', 'exit cleanly at end of batch replay', testable=False)
BaseSheet.addCommand('', 'allow-error', 'allow_error(vd.input("allow error: "))', 'suppress expected error messages matching regex pattern', testable=False)
