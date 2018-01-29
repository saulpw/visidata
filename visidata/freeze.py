from visidata import *
from copy import deepcopy

globalCommand("'", 'addColumn(StaticColumn(sheet.rows, cursorCol), cursorColIndex+1)', 'add a frozen copy of current column with all cells evaluated', 'column-freeze')
globalCommand("g'", 'vd.push(StaticSheet(sheet)); status("pushed frozen copy of "+name)', 'open a frozen copy of current sheet with all visible columns evaluated', 'sheet-freeze')
globalCommand("z'", 'resetCache(cursorCol)', 'add/reset cache for current column', 'column-cache-clear')
globalCommand("gz'", 'resetCache(*visibleCols)', 'add/reset cache for all visible columns', 'column-cache-clear-all')
globalCommand("zg'", "gz'")

def resetCache(self, *cols):
    for col in cols:
        col._cachedValues = collections.OrderedDict()
    status("reset cache for " + (cols[0].name if len(cols) == 1 else str(len(cols))+" columns"))
Sheet.resetCache = resetCache

def StaticColumn(rows, col):
    c = deepcopy(col)
    frozenData = {}
    @async
    def _calcRows(sheet):
        for r in Progress(rows):
            try:
                frozenData[id(r)] = col.getValue(r)
            except Exception as e:
                frozenData[id(r)] = e

    _calcRows(col.sheet)
    c.calcValue=lambda row,d=frozenData: d[id(row)]
    c.setter=lambda col,row,val,d=frozenData: setitem(d, id(row), val)
    c.name = c.name + '_frozen'
    return c


class StaticSheet(Sheet):
    'A copy of the source sheet with all cells frozen.'
    def __init__(self, source):
        super().__init__(source.name + "'", source=source)

        self.columns = []
        for i, col in enumerate(self.source.columns):
            colcopy = ColumnItem(col.name, i, width=col.width, type=col.type)
            self.columns.append(colcopy)
            if col in self.source.keyCols:
                self.keyCols.append(colcopy)

    @async
    def reload(self):
        self.rows = []
        for r in Progress(self.source.rows):
            self.addRow([col.getValue(r) for col in self.source.columns])
