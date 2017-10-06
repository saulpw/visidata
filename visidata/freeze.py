from visidata import *
from copy import deepcopy

globalCommand("'", 'addColumn(StaticColumn(sheet.rows, cursorCol), cursorColIndex+1)', 'add a frozen copy of current column with all cells evaluated')
globalCommand("g'", 'vd.push(StaticSheet(sheet)); status("pushed frozen copy of "+name)', 'open a frozen copy of current sheet with all visible columns evaluated')
globalCommand("z'", 'cursorCol._cachedValues = collections.OrderedDict(); status("added cache to " + cursorCol.name)', 'add/reset cache for this column')
globalCommand("gz'", 'for c in visibleCols: c._cachedValues = collections.OrderedDict()', 'add/reset cache for all visible columns')
globalCommand("zg'", "gz'")


def StaticColumn(rows, col):
    c = deepcopy(col)
    frozenData = {id(r):col.getValue(r) for r in rows}
    c.calcValue=lambda r,d=frozenData: d[id(r)]
    c.setter=lambda s,c,r,v,d=frozenData: setitem(d, id(r), v)
    c.name = c.name + '_frozen'
    return c


class StaticSheet(Sheet):
    'A copy of the source sheet with all cells frozen.'
    def __init__(self, source):
        super().__init__(source.name + "'", source)

        self.columns = [ColumnItem(col.name, i, width=col.width, type=col.type) for i,col in enumerate(self.source.columns)]
        self.nKeys = source.nKeys

    @async
    def reload(self):
        self.rows = []
        for r in self.genProgress(self.source.rows):
            self.addRow([col.getValue(r) for col in self.source.columns])
