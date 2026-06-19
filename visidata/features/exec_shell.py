import os
import subprocess

from visidata import vd, VisiData, BaseSheet
from visidata.editor import SuspendCurses


@VisiData.api
def launchShell(vd):
    'Suspend display and drop into an interactive $SHELL, returning to VisiData on exit (Ctrl+D).'
    if vd.options.batch or vd.currentReplay is not None:
        vd.fail('exec-shell not available in batch/replay')
    shell = os.environ.get('SHELL') or vd.fail('$SHELL not set')
    with SuspendCurses():
        return subprocess.call([shell])


BaseSheet.addCommand('', 'exec-shell', 'launchShell()', 'suspend display and drop into an interactive $SHELL; return to VisiData on exit (Ctrl+D)')

vd.addMenuItems('''
    System > Open shell > exec-shell
''')
