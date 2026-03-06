import time

from visidata import vd, BaseSheet, Path, VisiData

vd.replay_output_path = ''  # output path set by replay-reset, used by replay-output
vd.replay_line = 0  # current line number within a test
vd.replay_start_time = 0  # timestamp when current test started


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


@BaseSheet.api
def replay_end(vs):  # noqa: ARG001
    'Reset state for next test (no output).'
    if vd.options.debug:
        print(f'{time.time() - vd.replay_start_time:.1f}s  {vd.replay_output_path}')

@VisiData.before
def status(vd, *args, priority=0):
    if priority > 0 and vd.replay_output_path:
        print(f'{vd.replay_output_path}:{vd.replay_line}: {args[0]}')

@BaseSheet.api
def replay_output(vs):
    'Save current sheet to path from replay-reset and reset state for next test.'
    outpath = Path(vd.replay_output_path)
    vd.saveSheets(outpath, vs, confirm_overwrite=False)
    vd.sync()
    if vd.options.debug:
        print(f'{time.time() - vd.replay_start_time:.1f}s  {vd.replay_output_path}')


@BaseSheet.api
def replay_exit(vs):  # noqa: ARG001
    'Exit cleanly at end of batch replay.'
    pass


BaseSheet.addCommand('', 'replay-reset', 'replay_reset()', 'initialize test state for a test')
BaseSheet.addCommand('', 'replay-end', 'replay_end()', 'reset state for test runner (no output)')
BaseSheet.addCommand('', 'replay-output', 'replay_output()', 'save output and reset state for test runner')
BaseSheet.addCommand('', 'replay-exit', 'replay_exit()', 'exit cleanly at end of batch replay')
