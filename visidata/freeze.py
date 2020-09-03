from visidata import *
from copy import deepcopy


def resetCache(self):
    self._cachedValues = collections.OrderedDict()
    vd.status("reset cache for " + self.name)

Column.resetCache = resetCache


@Sheet.api
def StaticColumn(sheet, col, pos):
    frozencol = SettableColumn(col.name+'_frozen', width=col.width, type=col.type, fmtstr=col._fmtstr)
    sheet.addColumn(frozencol, pos)

    @asyncthread
    def calcRows_async(frozencol, rows, col):
        # no need to undo, addColumn undo is enough
        for r in Progress(rows, 'calculating'):
            try:
                frozencol.setValue(r, col.getTypedValue(r))
            except Exception as e:
                frozencol.setValue(r, e)

    calcRows_async(frozencol, sheet.rows, col)
    return frozencol


class StaticSheet(Sheet):
    'A copy of the source sheet with all cells frozen.'
    def __init__(self, source):
        super().__init__(source.name + "'", source=source)

        self.columns = []
        for i, col in enumerate(self.source.visibleCols):
            colcopy = ColumnItem(col.name, i, width=col.width, type=col.type, fmtstr=col._fmtstr)
            self.addColumn(colcopy)
            if col in self.source.keyCols:
                self.setKeys([colcopy])

    @asyncthread
    def reload(self):
        self.rows = []
        for r in Progress(self.source.rows, 'calculating'):
            row = []
            self.addRow(row)
            for col in self.source.visibleCols:
                try:
                    row.append(col.getTypedValue(r))
                except Exception as e:
                    row.append(None)


Sheet.addCommand("'", 'freeze-col', 'StaticColumn(cursorCol, cursorColIndex+1)', 'add a frozen copy of current column with all cells evaluated')
Sheet.addCommand("g'", 'freeze-sheet', 'vd.push(StaticSheet(sheet)); status("pushed frozen copy of "+name)', 'open a frozen copy of current sheet with all visible columns evaluated')
Sheet.addCommand("z'", 'cache-col', 'cursorCol.resetCache()', 'add/reset cache for current column')
Sheet.addCommand("gz'", 'cache-cols', 'for c in visibleCols: c.resetCache()', 'add/reset cache for all visible columns')
