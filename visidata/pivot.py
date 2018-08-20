from visidata import *

Sheet.addCommand('W', 'pivot', 'vd.push(SheetPivot(sheet, [cursorCol]))')

# rowdef: (tuple(keyvalues), dict(variable_value -> list(rows)))
class SheetPivot(Sheet):
    'Summarize key columns in pivot table and display as new sheet.'
    rowtype = 'aggregated rows'
    def __init__(self, srcsheet, variableCols):
        self.variableCols = variableCols
        super().__init__(srcsheet.name+'_pivot_'+''.join(c.name for c in variableCols),
                         source=srcsheet)

    def reload(self):
        self.nonpivotKeyCols = []

        for colnum, col in enumerate(self.source.keyCols):
            if col not in self.variableCols:
                newcol = Column(col.name, origcol=col, width=col.width, type=col.type,
                                getter=lambda col,row,colnum=colnum: row[0][colnum])
                self.nonpivotKeyCols.append(newcol)

        # two different threads for better interactive display
        self.reloadCols()
        self.reloadRows()

    @asyncthread
    def reloadCols(self):
        self.columns = copy(self.nonpivotKeyCols)
        self.setKeys(self.columns)

        aggcols = [(c, aggregator) for c in self.source.visibleCols for aggregator in getattr(c, 'aggregators', [])]

        if not aggcols:
            aggcols = [(c, aggregators["count"]) for c in self.variableCols]

        for col in self.variableCols:
            for aggcol, aggregator in aggcols:
                aggname = '%s_%s' % (aggcol.name, aggregator.__name__)

                allValues = set()
                for value in Progress(col.getValues(self.source.rows), total=len(self.source.rows)):
                    if value not in allValues:
                        allValues.add(value)
                        c = Column('%s_%s' % (aggname, value),
                                type=aggregator.type or aggcol.type,
                                getter=lambda col,row,aggcol=aggcol,aggvalue=value,agg=aggregator: agg(aggcol, row[1].get(aggvalue, [])))
                        c.aggvalue = value
                        self.addColumn(c)

                if aggregator.__name__ != 'count':  # already have count above
                    c = Column('Total_' + aggname,
                                type=aggregator.type or aggcol.type,
                                getter=lambda col,row,aggcol=aggcol,agg=aggregator: agg(aggcol, sum(row[1].values(), [])))
                    self.addColumn(c)

            c = Column('Total_count',
                        type=int,
                        getter=lambda col,row: len(sum(row[1].values(), [])))
            self.addColumn(c)


    @asyncthread
    def reloadRows(self):
        rowidx = {}
        self.rows = []
        for r in Progress(self.source.rows):
            keys = tuple(forward(keycol.origcol.getTypedValue(r)) for keycol in self.nonpivotKeyCols)
            formatted_keys = tuple(wrapply(c.format, v) for v, c in zip(keys, self.nonpivotKeyCols))

            pivotrow = rowidx.get(formatted_keys)
            if pivotrow is None:
                pivotrow = (keys, {})
                rowidx[formatted_keys] = pivotrow
                self.addRow(pivotrow)

            for col in self.variableCols:
                varval = col.getTypedValueOrException(r)
                matchingRows = pivotrow[1].get(varval)
                if matchingRows is None:
                    pivotrow[1][varval] = [r]
                else:
                    matchingRows.append(r)

SheetPivot.addCommand('z'+ENTER, 'dive-cell', 'vs=copy(source); vs.name+="_%s"%cursorCol.aggvalue; vs.rows=cursorRow[1].get(cursorCol.aggvalue, []); vd.push(vs)')
SheetPivot.addCommand(ENTER, 'dive-row', 'vs=copy(source); vs.name+="_%s"%"+".join(cursorRow[0]); vs.rows=sum(cursorRow[1].values(), []); vd.push(vs)')
