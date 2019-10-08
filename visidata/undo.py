import itertools

from visidata import VisiData

# undoers
def undoAttr(objs, attrname):
    'Returns a string that on eval() returns a closure that will set attrname on each obj to its former value as reference.'
    return '''lambda oldvals=[(o, getattr(o, "{attrname}")) for o in {objs}] : list(setattr(o, "{attrname}", v) for o, v in oldvals)'''.format(attrname=attrname, objs=objs)

def undoAttrFunc(objs, attrname):
    'Return closure that sets attrname on each obj to its former value.'
    oldvals = [(o, getattr(o, attrname)) for o in objs]
    def _undofunc():
        for o, v in oldvals:
            setattr(o, attrname, v)
    return _undofunc


class Fanout(list):
    def __init__(self, sheet, objs):
        self.__dict__['_sheet'] = sheet
        super().__init__(objs)

    def __getattr__(self, k):
        return Fanout(self._sheet, [getattr(o, k) for o in self])

    def __setattr__(self, k, v):
        self._sheet.addUndo(undoAttrFunc(self, k))
        for o in self:
            setattr(o, k, v)

    def __call__(self, *args, **kwargs):
        return Fanout(self._sheet, [o(*args, **kwargs) for o in self])


def undoAttrCopy(objs, attrname):
    'Returns a string that on eval() returns a closure that will set attrname on each obj to its former value which is copied.'
    return '''lambda oldvals=[ (o, copy(getattr(o, "{attrname}"))) for o in {objs} ] : list(setattr(o, "{attrname}", v) for o, v in oldvals)'''.format(attrname=attrname, objs=objs)

@VisiData.api
def addUndoSetValues(vd, rows, cols):
    oldvals = [(c, r, c.getValue(r)) for c,r in itertools.product(cols, rows)]
    def _undo():
        for c, r, v in oldvals:
            c.setValue(r, v)
    vd.cmdlog.onUndo(_undo)

def undoSetValues(rowstr='[cursorRow]', colstr='[cursorCol]'):
    return 'lambda oldvals=[(c, r, c.getValue(r)) for c,r in itertools.product({colstr}, {rowstr})]: list(c.setValue(r, v) for c, r, v in oldvals)'.format(rowstr=rowstr, colstr=colstr)

def undoRows(sheetstr):
    return undoAttrCopy('[%s]'%sheetstr, 'rows')

undoBlocked = 'lambda: error("cannot undo")'
undoSheetRows = undoRows('sheet')
undoSheetCols = 'lambda sheet=sheet,oldcols=[copy(c) for c in columns]: setattr(sheet, "columns", oldcols)'
undoAddCols = undoAttrCopy('[sheet]', 'columns')
undoEditCell = undoSetValues('[cursorRow]', '[cursorCol]')
undoEditCells = undoSetValues('selectedRows', '[cursorCol]')
