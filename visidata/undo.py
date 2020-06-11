import itertools
from copy import copy

from visidata import vd, options, VisiData, BaseSheet, option

BaseSheet.init('undone', list)  # list of CommandLogRow for redo after undo

option('undo', True, 'enable undo/redo')

@VisiData.api
def addUndo(vd, undofunc, *args, **kwargs):
    'On undo of latest command, call undofunc()'
    if options.undo:
        r = vd.activeCommand
        if not r:
            return
        r.undofuncs.append((undofunc, args, kwargs))


@VisiData.api
def undo(vd, sheet):
    if not options.undo:
        vd.fail("options.undo not enabled")

    # don't allow undo of first command on a sheet, which is always the command that created the sheet.
    for cmdlogrow in sheet.cmdlog_sheet.rows[:0:-1]:
        if cmdlogrow.undofuncs:
            for undofunc, args, kwargs, in cmdlogrow.undofuncs:
                undofunc(*args, **kwargs)
            sheet.undone.append(cmdlogrow)
            sheet.cmdlog_sheet.rows.remove(cmdlogrow)

            vd.clearCaches()  # undofunc can invalidate the drawcache

            vd.moveToReplayContext(cmdlogrow)
            vd.status("%s undone" % cmdlogrow.longname)
            return

    vd.fail("nothing to undo on current sheet")


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
    oldvals = [(c, r, c.getValue(r)) for c,r in itertools.product(cols, vd.Progress(rows, gerund='doing'))]
    def _undo():
        for c, r, v in oldvals:
            c.setValue(r, v)
    vd.addUndo(_undo)

@VisiData.api
def addUndoColNames(vd, cols):
    oldnames = [(c, c.name) for c in cols]
    def _undo():
        for c, name in oldnames:
            c.name = name
    vd.addUndo(_undo)

@VisiData.api
def addUndoReload(vd, rows, cols):
    oldrows = rows
    oldcolumns = cols
    def _undo():
        sheet = oldcolumns[0].sheet
        sheet.rows = oldrows
        sheet.columns = oldcolumns
    vd.addUndo(_undo)

BaseSheet.addCommand('U', 'undo-last', 'vd.undo(sheet)', 'undo the most recent modification (requires enabled options.undo)')
BaseSheet.addCommand('R', 'redo-last', 'vd.redo(sheet)', 'redo the most recent undo (requires enabled options.undo)')
