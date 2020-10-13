'''
[plugin]: experimental undo using fork()

Usage: `import plugins.undofork` in .visidatarc

Add two commands:
- `checkpoint-save` (`m`) to mark a checkpoint
- `checkpoint-undo` (`zm`) to exit back to it.  Use ^L to redraw after.
'''

import os
import time
from visidata import globalCommand, vd, error, isLoggableCommand, status, VisiData


globalCommand('m', 'checkpoint-save', 'vd.checkpoint()')
globalCommand('zm', 'checkpoint-undo', 'vd.undo()')

vd.undoPids = []

@VisiData.api
def checkpoint(vd):
    vd.undoPids.append(os.getpid())
    pid = os.fork()
    if pid > 0:  # parent, halt until undo
        before = time.time()
        pid, st = os.wait()
        if st == 42: # undo
            vd.scr.clear()
            vd.undoPids.remove(os.getpid())
            raise Exception('undid %ss' % int(time.time()-before))

@VisiData.api
def undo(vd):
    vd.undoPids or error('cannot undo')
    os._exit(42)

@VisiData.api
def quit_sheet(vd, *sheets):
    for vs in sheets:
        vd.sheets.remove(vs)
    if not vd.sheets:
        for pid in vd.undoPids:
            os.kill(pid, signal.SIGKILL)
