from visidata import *

globalCommand("'", 'addColumn(StaticColumn(sheet, cursorCol), cursorColIndex+1)', 'add a frozen copy of this column')
globalCommand("g'", 'vd.push(StaticSheet(sheet))', 'push a frozen copy of this sheet')


def StaticColumn(sheet, col):
    c = col.copy()
    frozenData = {}
    for r in sheet.rows:
        frozenData[id(r)] = c.getValue(r)
    c.getter=lambda r,d=frozenData: d[id(r)]
    c.setter=lambda s,c,r,v,d=frozenData: setitem(d, id(r), v)
    c.name = c.name + '_frozen'
    return c


class StaticSheet(Sheet):
    'A copy of the source sheet with all cells frozen.'
    def __init__(self, source):
        super().__init__(source.name + "'", source)

        self.columns = [ColumnItem(col.name, i, width=col.width, type=col.type) for i,col in enumerate(self.source.columns)]

    @async
    def reload(self):
        self.rows = []
        for r in self.genProgress(self.source.rows):
            self.addRow([col.getValue(r) for col in self.source.columns])
