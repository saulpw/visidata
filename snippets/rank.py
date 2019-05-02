Sheet.addCommand(None, 'rank', 'addColumn(RankColumn(cursorCol), index=cursorVisibleColIndex+1)')

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

            self.srcValues[self.sheet.rowid(r)] = previ
