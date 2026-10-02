import itertools
import contextlib
import threading
from copy import copy

from visidata import vd, VisiData, BaseSheet

class _UndoSuppressed(threading.local):
    'per-thread: overlapping async reloads must not clobber each other #3165'
    value = False

vd._undo_suppressed = _UndoSuppressed()

BaseSheet.init('undone', list)  # list of CommandLogRow for redo after undo

vd.option('undo', True, 'enable undo/redo')

nonUndo = '''commit open-file reload-sheet'''.split()

def isUndoableCommand(longname):
    for n in nonUndo:
        if longname.startswith(n):
            return False
    return True

@VisiData.api
@contextlib.contextmanager
def suppressUndo(vd):
    'Do not record undos in this thread within this block (e.g. while constructing a sheet).'
    old = vd._undo_suppressed.value
    vd._undo_suppressed.value = True
    try:
        yield
    finally:
        vd._undo_suppressed.value = old

@VisiData.api
def addUndo(vd, undofunc, *args, **kwargs):
    'On undo of latest command, call ``undofunc(*args, **kwargs)``.'
    if vd.options.undo and not vd._undo_suppressed.value:
        # occurs when VisiData is just starting up.
        # very early in startup, modifyCommand does not yet exist
        if not vd.activeCommand:
            return
        r = vd.modifyCommand
        if not r or not isUndoableCommand(r.longname):
            return
        # some special commands, like open-file, do not have an undofuncs set
        # do not set undofuncs for non-logged commands
        if not vd.isLoggableCommand(vd.activeCommand):
            return
        if not r.undofuncs:
            r.undofuncs = []
        r.undofuncs.append((undofunc, args, kwargs))


@VisiData.api
def undo(vd, sheet):
    if not vd.options.undo:
        vd.fail("options.undo not enabled")

    cmdlogrows = itertools.dropwhile(lambda r: r.longname == 'set-option', sheet.cmdlog_sheet.rows)
    # skip the first remaining command, to exclude it from undo,
    # because it is always the command that created the sheet, or for
    # replayed cmdlogs, a no-op placeholder row
    for i, cmdlogrow in enumerate(reversed(list(cmdlogrows)[1:])):
        if cmdlogrow.undofuncs:
            for undofunc, args, kwargs, in cmdlogrow.undofuncs[::-1]:
                undofunc(*args, **kwargs)
            sheet.undone.append(cmdlogrow)
            row_idx = len(sheet.cmdlog_sheet.rows)-1 - i
            del sheet.cmdlog_sheet.rows[row_idx]

            vd.clearCaches()  # undofunc can invalidate the drawcache

            vd.moveToReplayContext(cmdlogrow, sheet)
            vd.status("%s undone" % cmdlogrow.longname)
            return

    vd.fail("nothing to undo on current sheet")


def _refersTo(x, target, depth=4):
    'Return True if *x* is *target*, or contains it within *depth* levels of containers or closures.'
    if x is target:
        return True
    if depth <= 0:
        return False
    if isinstance(x, dict):
        x = list(x.values())
    if isinstance(x, (list, tuple, set)):
        if len(x) > 1000:  # e.g. a copy of some sheet's rows: only look at the top level
            return any(v is target for v in x)
        return any(_refersTo(v, target, depth-1) for v in x)
    if callable(x):
        if getattr(x, '__self__', None) is target:
            return True
        for cell in getattr(x, '__closure__', None) or ():
            try:
                if _refersTo(cell.cell_contents, target, depth-1):
                    return True
            except ValueError:  # empty cell
                pass
    return False


def _undoRefersTo(undo, vs):
    undofunc, args, kwargs = undo
    return _refersTo(undofunc, vs) or _refersTo(args, vs) or _refersTo(kwargs, vs)


@VisiData.api
def releaseUndos(vd, vs):
    'Drop undos that keep released sheet *vs* (or its rows) alive.'
    vs.undone.clear()
    if getattr(vs, '_cmdlog_sheet', None) is not None:  # lazy_property, maybe not created yet
        for r in vs._cmdlog_sheet.rows:  # same row objects as in vd.cmdlog
            if r.undofuncs:
                r.undofuncs = []

    cmdlogrows = list(vd.cmdlog.rows)
    if vd.activeCommand:
        cmdlogrows.append(vd.activeCommand)
    for r in cmdlogrows:
        if r.undofuncs and any(_undoRefersTo(u, vs) for u in r.undofuncs):
            # a partial undo would be wrong, and an empty one would make undo silently skip to an older command
            msg = f'cannot undo {r.longname}: sheet "{vs.name}" was released'
            r.undofuncs = [(vd.warning, (msg,), {})]


@VisiData.api
def redo(vd, sheet):
    sheet.undone or vd.fail("nothing to redo")
    cmdlogrow = sheet.undone.pop()
    vd.replayOne(cmdlogrow)
    vd.status("%s redone" % cmdlogrow.longname)

# undoers
def undoAttrFunc(objs, attrname):
    'Return closure that sets attrname on each obj to its former value.'
    oldvals = [(o, getattr(o, attrname)) for o in objs]
    def _undofunc():
        for o, v in oldvals:
            setattr(o, attrname, v)
    return _undofunc


class Fanout(list):
    'Fan out attribute changes to every element in a list.'
    def __getattr__(self, k):
        return Fanout([getattr(o, k) for o in self])

    def __setattr__(self, k, v):
        vd.addUndo(undoAttrFunc(self, k))
        for o in self:
            setattr(o, k, v)

    def __call__(self, *args, **kwargs):
        return Fanout([o(*args, **kwargs) for o in self])


def undoAttrCopyFunc(objs, attrname):
    'Return closure that sets attrname on each obj to its former value.'
    oldvals = [(o, copy(getattr(o, attrname))) for o in objs]
    def _undofunc():
        for o, v in oldvals:
            setattr(o, attrname, v)
    return _undofunc


@VisiData.api
def addUndoSetValues(vd, cols, rows):
    'Add undo function to reset values for *rows* in *cols*.'
    oldvals = [(c, r, c.getValue(r)) for c,r in itertools.product(cols, vd.Progress(rows, gerund='doing'))]
    def _undo():
        for c, r, v in oldvals:
            c.setValue(r, v, setModified=False)
    vd.addUndo(_undo)


BaseSheet.addCommand('U', 'undo-last', 'vd.undo(sheet)', 'Undo the most recent change (options.undo must be enabled)')
BaseSheet.addCommand('R', 'redo-last', 'vd.redo(sheet)', 'Redo the most recent undo (options.undo must be enabled)')

vd.addGlobals(
    undoAttrFunc=undoAttrFunc,
    Fanout=Fanout,
    undoAttrCopyFunc=undoAttrCopyFunc)

vd.addMenuItems('''
    Edit > Undo > undo-last
    Edit > Redo > redo-last
''')
