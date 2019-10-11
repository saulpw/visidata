import itertools
from copy import copy

from visidata import vd, VisiData, options

@VisiData.api
def addUndo(vd, undofunc, *args, **kwargs):
    'On undo of latest command, call undofunc()'
    if options.undo:
        r = vd.activeCommand
        if not r:
            return
        if r.undofuncs is None:
            r.undofuncs = []
        r.undofuncs.append((undofunc, args, kwargs))


# undoers
def undoAttrFunc(objs, attrname):
    'Return closure that sets attrname on each obj to its former value.'
    oldvals = [(o, getattr(o, attrname)) for o in objs]
    def _undofunc():
        for o, v in oldvals:
            setattr(o, attrname, v)
    return _undofunc


class Fanout(list):
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
