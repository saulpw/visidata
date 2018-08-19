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
    frozencol = SettableColumn(col.name+'_frozen', width=col.width, type=col.type, fmtstr=col.fmtstr)

    @asyncthread
    def calcRows_async(frozencol, rows, col):
        for r in Progress(rows):
            try:
                frozencol.setValue(r, col.getTypedValue(r))
            except Exception as e:
                frozencol.setValue(r, e)

    calcRows_async(frozencol, rows, col)
    return frozencol


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
