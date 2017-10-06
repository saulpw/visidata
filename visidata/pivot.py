from visidata import *

globalCommand('W', 'vd.push(SheetPivot(sheet, [cursorCol]))', 'Pivot the current column into a new sheet')

# rowdef: (tuple(keyvalues), dict(variable_value -> list(rows)))
class SheetPivot(Sheet):
    'Summarize key columns in pivot table and display as new sheet.'
    commands = [
        Command('z'+ENTER, 'vs=copy(source); vs.name+="_%s"%cursorCol.aggvalue; vs.rows=cursorRow[1].get(cursorCol.aggvalue, []); vd.push(vs)',
                      'push sheet of source rows aggregated in this cell'),
        Command(ENTER, 'vs=copy(source); vs.name+="_%s"%"+".join(cursorRow[0]); vs.rows=sum(cursorRow[1].values(), []); vd.push(vs)',
                      'push sheet of source rows aggregated in this cell')
               ]
    def __init__(self, srcsheet, variableCols):
        super().__init__(srcsheet.name+'_pivot_'+''.join(c.name for c in variableCols), srcsheet)

        self.nonpivotKeyCols = []
        self.variableCols = variableCols
        for colnum, col in enumerate(srcsheet.keyCols):
            if col not in variableCols:
                newcol = Column(col.name, getter=lambda r, colnum=colnum: r[0][colnum])
                newcol.srccol = col
                self.nonpivotKeyCols.append(newcol)


    def reload(self):
        # two different threads for better interactive display
        self.reloadCols()
        self.reloadRows()

    @async
    def reloadCols(self):
        self.columns = copy(self.nonpivotKeyCols)
        self.nKeys = len(self.nonpivotKeyCols)
        aggcols = [(c, aggregator) for c in self.source.columns for aggregator in getattr(c, 'aggregators', [])]

        if not aggcols:
            aggcols = [(c, aggregators["count"]) for c in self.variableCols]

        for col in self.variableCols:
            for aggcol, aggregator in aggcols:
                aggname = '%s_%s' % (aggcol.name, aggregator.__name__)
                if aggregator.__name__ != 'count':  # already have count above
                    c = Column('Total_' + aggname,
                                type=aggregator.type or aggcol.type,
                                getter=lambda r,aggcol=aggcol: aggregator(aggcol, sum(r[1].values(), [])))
                    self.addColumn(c)

                allValues = set()
                for value in self.genProgress(col.getValues(self.source.rows), total=len(self.source.rows)):
                    if value not in allValues:
                        allValues.add(value)
                        c = Column(value+'_'+aggname,
                                type=aggregator.type or aggcol.type,
                                getter=lambda r,aggcol=aggcol,aggvalue=value: aggregator(aggcol, r[1].get(aggvalue, [])))
                        c.aggvalue = value
                        self.addColumn(c)

            c = Column('Total_count',
                        type=int,
                        getter=lambda r: len(sum(r[1].values(), [])))
            self.addColumn(c)


    @async
    def reloadRows(self):
        rowidx = {}
        self.rows = []
        for r in self.genProgress(self.source.rows):
            keys = tuple(keycol.srccol.getTypedValue(r) for keycol in self.nonpivotKeyCols)

            pivotrow = rowidx.get(keys)
            if pivotrow is None:
                pivotrow = (keys, {})
                rowidx[keys] = pivotrow
                self.addRow(pivotrow)

            for col in self.variableCols:
                varval = col.getTypedValue(r)
                matchingRows = pivotrow[1].get(varval)
                if matchingRows is None:
                    pivotrow[1][varval] = [r]
                else:
                    matchingRows.append(r)
