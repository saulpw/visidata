from visidata import *
from copy import deepcopy

Sheet.addCommand("'", 'freeze-col', 'addColumn(StaticColumn(sheet.rows, cursorCol), cursorColIndex+1)')
Sheet.addCommand("g'", 'freeze-sheet', 'vd.push(StaticSheet(sheet)); status("pushed frozen copy of "+name)')
Sheet.addCommand("z'", 'cache-col', 'cursorCol.resetCache()')
Sheet.addCommand("gz'", 'cache-cols', 'for c in visibleCols: c.resetCache()')

def resetCache(self):
    self._cachedValues = collections.OrderedDict()
    status("reset cache for " + self.name)

Column.resetCache = resetCache

def StaticColumn(rows, col):
    c = deepcopy(col)
    frozenData = {}
    @asyncthread
    def _calcRows(sheet):
        for r in Progress(rows):
            try:
                frozenData[id(r)] = col.getTypedValueOrException(r)
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
            colcopy = ColumnItem(col.name, i, width=col.width, type=col.type, fmtstr=col.fmtstr)
            self.addColumn(colcopy)
            if col in self.source.keyCols:
                self.setKeys([colcopy])

    @asyncthread
    def reload(self):
        self.rows = []
        for r in Progress(self.source.rows):
            row = []
            self.rows.append(row)
            for col in self.source.columns:
                try:
                    row.append(col.getTypedValueOrException(r))
                except Exception as e:
                    row.append(None)
