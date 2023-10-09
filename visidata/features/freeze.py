import collections
from visidata import Column, Sheet, VisiData, ColumnItem, Progress, TypedExceptionWrapper, SettableColumn
from visidata import asyncthread, vd


@Column.api
def resetCache(col):
    col._cachedValues = collections.OrderedDict()
    vd.status("reset cache for " + col.name)


@Sheet.api
def freeze_col(sheet, col):
    frozencol = SettableColumn(col.name+'_frozen')
    state = col.__getstate__()
    state.pop('name')
    frozencol.__setstate__(state)
    frozencol.recalc(sheet)

    @asyncthread
    def calcRows_async(frozencol, rows, col):
        # no need to undo, addColumn undo is enough
        for r in Progress(rows, 'calculating'):
            try:
                frozencol.putValue(r, col.getTypedValue(r))
            except Exception as e:
                frozencol.putValue(r, e)

    calcRows_async(frozencol, sheet.rows, col)
    return frozencol


@VisiData.api
class StaticSheet(Sheet):
    'A copy of the source sheet with all cells frozen.'
    def __init__(self, source):
        super().__init__(source.name + "'", source=source)

    def resetCols(self):
        self.columns = []
        for i, col in enumerate(self.source.visibleCols):
            colcopy = ColumnItem(col.name)
            colcopy.__setstate__(col.__getstate__())
            colcopy.expr = i
            self.addColumn(colcopy)
            if col in self.source.keyCols:
                self.setKeys([colcopy])

    def iterload(self):
        for r in Progress(self.source.rows, 'calculating'):
            row = []
            yield row

            # now fill out row
            for col in self.source.visibleCols:
                val = col.getTypedValue(r)
                if isinstance(val, TypedExceptionWrapper):
                    row.append(None)
                else:
                    row.append(val)


Sheet.addCommand("'", 'freeze-col', 'sheet.addColumnAtCursor(freeze_col(cursorCol))', 'add a frozen copy of current column with all cells evaluated')
Sheet.addCommand("g'", 'freeze-sheet', 'vd.push(StaticSheet(sheet)); status("pushed frozen copy of "+name)', 'open a frozen copy of current sheet with all visible columns evaluated')
Sheet.addCommand("z'", 'cache-col', 'cursorCol.resetCache()', 'add/reset cache for current column')
Sheet.addCommand("gz'", 'cache-cols', 'for c in visibleCols: c.resetCache()', 'add/reset cache for all visible columns')

vd.addMenuItem('Column', 'Freeze', 'freeze-col')
vd.addMenuItem('File', 'Freeze', 'freeze-sheet')
