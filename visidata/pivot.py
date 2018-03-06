from visidata import *

globalCommand('W', 'vd.push(SheetPivot(sheet, [cursorCol]))', 'Pivot the current column into a new sheet', 'data-pivot')

# rowdef: (tuple(keyvalues), dict(variable_value -> list(rows)))
class SheetPivot(Sheet):
    'Summarize key columns in pivot table and display as new sheet.'
    rowtype = 'aggregated rows'
    commands = [
        Command('z'+ENTER, 'vs=copy(source); vs.name+="_%s"%cursorCol.aggvalue; vs.rows=cursorRow[1].get(cursorCol.aggvalue, []); vd.push(vs)',
                      'open sheet of source rows aggregated in current cell', 'open-source-cell'),
        Command(ENTER, 'vs=copy(source); vs.name+="_%s"%"+".join(cursorRow[0]); vs.rows=sum(cursorRow[1].values(), []); vd.push(vs)',
                      'open sheet of source rows aggregated in current cell', 'open-source-row')
               ]
    def __init__(self, srcsheet, variableCols):
        super().__init__(srcsheet.name+'_pivot_'+''.join(c.name for c in variableCols), source=srcsheet)

        self.nonpivotKeyCols = []
        self.variableCols = variableCols
        for colnum, col in enumerate(srcsheet.keyCols):
            if col not in variableCols:
                newcol = Column(col.name, getter=lambda col,row,colnum=colnum: row[0][colnum])
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
        aggcols = [(c, aggregator) for c in self.source.visibleCols for aggregator in getattr(c, 'aggregators', [])]

        if not aggcols:
            aggcols = [(c, aggregators["count"]) for c in self.variableCols]

        for col in self.variableCols:
            for aggcol, aggregator in aggcols:
                aggname = '%s_%s' % (aggcol.name, aggregator.__name__)
                if aggregator.__name__ != 'count':  # already have count above
                    c = Column('Total_' + aggname,
                                type=aggregator.type or aggcol.type,
                                getter=lambda col,row,aggcol=aggcol,agg=aggregator: agg(aggcol, sum(row[1].values(), [])))
                    self.addColumn(c)

                allValues = set()
                for value in Progress(col.getValues(self.source.rows), total=len(self.source.rows)):
                    if value not in allValues:
                        allValues.add(value)
                        c = Column('%s_%s' % (aggname, value),
                                type=aggregator.type or aggcol.type,
                                getter=lambda col,row,aggcol=aggcol,aggvalue=value,agg=aggregator: agg(aggcol, row[1].get(aggvalue, [])))
                        c.aggvalue = value
                        self.addColumn(c)

            c = Column('Total_count',
                        type=int,
                        getter=lambda col,row: len(sum(row[1].values(), [])))
            self.addColumn(c)


    @async
    def reloadRows(self):
        rowidx = {}
        self.rows = []
        for r in Progress(self.source.rows):
            keys = tuple(getValueOrError(keycol.srccol, r) for keycol in self.nonpivotKeyCols)

            pivotrow = rowidx.get(keys)
            if pivotrow is None:
                pivotrow = (keys, {})
                rowidx[keys] = pivotrow
                self.addRow(pivotrow)

            for col in self.variableCols:
                varval = col.getTypedValueNoExceptions(r)
                matchingRows = pivotrow[1].get(varval)
                if matchingRows is None:
                    pivotrow[1][varval] = [r]
                else:
                    matchingRows.append(r)
