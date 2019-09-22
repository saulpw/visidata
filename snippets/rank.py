'''
Adds `rank` command (no default binding) to add new rank column based on current column in sorted order.
Values are cached on the column, use `cache-col` command to reset.

To enable, add `from plugins.rank import *` to .visidatarc.
'''

from visidata import Column, Sheet, asyncthread


class RankColumn(Column):
    def __init__(self, col, **kwargs):
        super().__init__(col.name+'_rank', type=int, **kwargs)
        self.origCol = col
        self.srcValues = {}
        self.resetCache()

    def calcValue(self, row):
        return self.srcValues.get(self.sheet.rowid(row), None)

    @asyncthread
    def resetCache(self):
        valueRows = self.origCol.getValueRows(self.origCol.sheet.rows)
        sortedVals = sorted(valueRows, key=lambda r: r[0])
        self.srcValues = {}
        prevval = None
        previ = 0
        for i, (v, r) in enumerate(sortedVals):
            if prevval != v:
                prevval = v
                previ = i+1

            self.srcValues[self.origCol.sheet.rowid(r)] = previ


Sheet.addCommand(None, 'rank', 'addColumn(RankColumn(cursorCol), index=cursorVisibleColIndex+1)')
