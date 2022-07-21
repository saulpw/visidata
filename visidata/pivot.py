import collections
from visidata import *


# discrete_keys = tuple of formatted discrete keys that group the row
# numeric_key is a range
# sourcerows is list(all source.rows in group)
# pivotrows is { pivot_values: list(source.rows in group with pivot_values) }
PivotGroupRow = collections.namedtuple('PivotGroupRow', 'discrete_keys numeric_key sourcerows pivotrows'.split())

def Pivot(source, groupByCols, pivotCols):
    return PivotSheet('',
            groupByCols,
            pivotCols,
            source=source)

def makeErrorKey(col):
    if col.type is date:
        return date.min # date('2000-01-01')
    else:
        return col.type()

def formatRange(col, numeric_key):
    a, b = numeric_key
    nankey = makeErrorKey(col)
    if a is nankey and b is nankey:
        return '#ERR'
    elif a == b:
        return col.format(a)
    return ' - '.join(col.format(x) for x in numeric_key)

class RangeColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formatter = 'range'

    def format_range(self, fmtstr):
        return self._format

    def _format(self, typedval, *args, **kwargs):
        if typedval is None:
            return None
        return formatRange(self.origcol, typedval)

class PivotSheet(Sheet):
    'Summarize key columns in pivot table and display as new sheet.'
    rowtype = 'grouped rows'  # rowdef: PivotGroupRow
    def __init__(self, name, groupByCols, pivotCols, **kwargs):
        super().__init__(name, **kwargs)

        self.pivotCols = pivotCols  # whose values become columns
        self.groupByCols = groupByCols  # whose values become rows

    def isNumericRange(self, col):
        return vd.isNumeric(col) and self.source.options.numeric_binning

    def initCols(self):
        self.columns = []

        # add key columns (grouped by)
        for colnum, c in enumerate(self.groupByCols):
            if c in self.pivotCols:
                continue

            if self.isNumericRange(c):
                newcol = RangeColumn(c.name, origcol=c, width=c.width and c.width*2, getter=lambda c,r: r.numeric_key)
            else:
                newcol = Column(c.name, width=c.width, fmtstr=c.fmtstr,
                                  type=c.type if c.type in vd.typemap else anytype,
                                  origcol=c,
                                  getter=lambda col,row,i=colnum: row.discrete_keys[i],
                                  setter=lambda col,row,val,i=colnum: setitem(row.discrete_keys, i, val) and col.origcol.setValues(row.sourcerows, val))

            self.addColumn(newcol)

        self.setKeys(self.columns)

    def openRow(self, row):
        'open sheet of source rows aggregated in current pivot row'
        vs = copy(self.source)
        vs.name += "_%s"%"+".join(map(str, row.discrete_keys))
        vs.rows = sum(row.pivotrows.values(), [])
        return vs

    def openCell(self, col, row):
        'open sheet of source rows aggregated in current pivot cell'
        vs = copy(self.source)
        vs.name += "_%s"%col.aggvalue
        vs.rows = row.pivotrows.get(col.aggvalue, [])
        return vs

    def reload(self):
        self.initCols()

        # two different threads for better interactive display
        self.addAggregateCols()
        self.groupRows()

    @asyncthread
    def addAggregateCols(self):
        # add aggregated columns
        aggcols = {  # [Column] -> list(aggregators)
            sourcecol: sourcecol.aggregators
                for sourcecol in self.source.visibleCols
                    if sourcecol.aggregators
        } or {  # if pivot given but no aggregators specified
            sourcecol: [vd.aggregators["count"]]
                for sourcecol in self.pivotCols
        }

        if not aggcols:
#            self.addColumn(ColumnAttr('count', 'sourcerows', type=vlen))
            return

        # aggregators without pivot
        if not self.pivotCols:
            for aggcol, aggregatorlist in aggcols.items():
                for aggregator in aggregatorlist:
                    aggname = '%s_%s' % (aggcol.name, aggregator.name)

                    c = Column(aggname,
                                type=aggregator.type or aggcol.type,
                                fmtstr=aggcol.fmtstr,
                                getter=lambda col,row,aggcol=aggcol,agg=aggregator: agg(aggcol, row.sourcerows))
                    self.addColumn(c)

        # add pivoted columns
        for pivotcol in self.pivotCols:
            allValues = set()
            for value in Progress(pivotcol.getValues(self.source.rows), 'pivoting', total=len(self.source.rows)):
                if value in allValues:
                    continue
                allValues.add(value)

                if len(self.pivotCols) > 1:
                    valname = '%s_%s' % (pivotcol.name, value)
                else:
                    valname = str(value)

                for aggcol, aggregatorlist in aggcols.items():
                    for aggregator in aggregatorlist:
                        if len(aggcols) > 1: #  if more than one aggregated column, include that column name in the new column name
                            aggname = '%s_%s' % (aggcol.name, aggregator.name)
                        else:
                            aggname = aggregator.name


                        if len(aggregatorlist) > 1 or len(aggcols) > 1:
                            colname = '%s_%s' % (aggname, valname)
                            if not self.name:
                                self.name = self.source.name+'_pivot_'+''.join(c.name for c in self.pivotCols)
                        else:
                            colname = valname
                            if not self.name:
                                self.name = self.source.name+'_pivot_'+''.join(c.name for c in self.pivotCols) + '_' + aggname

                        c = Column(colname,
                                    type=aggregator.type or aggcol.type,
                                    aggvalue=value,
                                    getter=lambda col,row,aggcol=aggcol,agg=aggregator: agg(aggcol, row.pivotrows.get(col.aggvalue, [])))
                        self.addColumn(c)

#                    if aggregator.name != 'count':  # already have count above
#                        c = Column('Total_' + aggcol.name,
#                                    type=aggregator.type or aggcol.type,
#                                    getter=lambda col,row,aggcol=aggcol,agg=aggregator: agg(aggcol, row.sourcerows))
#                        self.addColumn(c)

    @asyncthread
    def groupRows(self, rowfunc=None):
        self.rows = []

        discreteCols = [c for c in self.groupByCols if not self.isNumericRange(c)]

        numericCols = [c for c in self.groupByCols if self.isNumericRange(c)]

        if len(numericCols) > 1:
            vd.fail('only one numeric column can be binned')

        numericBins = []
        degenerateBinning = False
        if numericCols:
            nbins = self.source.options.histogram_bins or int(len(self.source.rows) ** (1./2))
            vals = tuple(numericCols[0].getValues(self.source.rows))
            minval = min(vals)
            maxval = max(vals)
            width = (maxval - minval)/nbins

            if width == 0:
                # only one value (and maybe errors)
                numericBins = [(minval, maxval)]
            elif (numericCols[0].type in (int, vlen) and nbins > (maxval - minval)) or (width == 1):
                # (more bins than int vals) or (if bins are of width 1), just use the vals as bins
                degenerateBinning = True
                numericBins = [(val, val) for val in sorted(set(vals))]
                nbins = len(numericBins)
            else:
                numericBins = [(minval+width*i, minval+width*(i+1)) for i in range(nbins)]

        # group rows by their keys (groupByCols), and separate by their pivot values (pivotCols)
        groups = {}  # [formattedDiscreteKeys] -> (numericGroupRows:dict(formattedNumericKeyRange -> PivotGroupRow), groupRow:PivotGroupRow)  # groupRow is main/error row

        for sourcerow in Progress(self.source.iterrows(), 'grouping', total=self.source.nRows):
            discreteKeys = list(forward(origcol.getTypedValue(sourcerow)) for origcol in discreteCols)

            # wrapply will pass-through a key-able TypedWrapper
            formattedDiscreteKeys = tuple(wrapply(c.format, v) for v, c in zip(discreteKeys, discreteCols))

            numericGroupRows, groupRow = groups.get(formattedDiscreteKeys, (None, None))
            if numericGroupRows is None:
                # add new group rows
                numericGroupRows = {formatRange(numericCols[0], numRange): PivotGroupRow(discreteKeys, numRange, [], {}) for numRange in numericBins}
                groups[formattedDiscreteKeys] = (numericGroupRows, None)
                for r in numericGroupRows.values():
                    self.addRow(r)

            # find the grouprow this sourcerow belongs in, by numericbin
            if numericCols:
                try:
                    val = numericCols[0].getValue(sourcerow)
                    if val is not None:
                        val = numericCols[0].type(val)
                    if not width:
                        binidx = 0
                    elif degenerateBinning:
                        # in degenerate binning, each val has its own bin
                        binidx = numericBins.index((val, val))
                    else:
                        binidx = int((val-minval)//width)
                    groupRow = numericGroupRows[formatRange(numericCols[0], numericBins[min(binidx, nbins-1)])]
                except Exception as e:
                    # leave in main/error bin
                    pass

            # add the main bin if no numeric bin (error, or no numeric cols)
            if groupRow is None:
                nankey = makeErrorKey(numericCols[0]) if numericCols else 0
                groupRow = PivotGroupRow(discreteKeys, (nankey, nankey), [], {})
                groups[formattedDiscreteKeys] = (numericGroupRows, groupRow)
                self.addRow(groupRow)

            # add the sourcerow to its all bin
            groupRow.sourcerows.append(sourcerow)

            # separate by pivot value
            for col in self.pivotCols:
                varval = col.getTypedValue(sourcerow)
                matchingRows = groupRow.pivotrows.get(varval)
                if matchingRows is None:
                    matchingRows = groupRow.pivotrows[varval] = []
                matchingRows.append(sourcerow)

            if rowfunc:
                rowfunc(groupRow)

        # automatically add cache to all columns now that everything is binned
        for c in self.nonKeyVisibleCols:
            c.setCache(True)


Sheet.addCommand('W', 'pivot', 'vd.push(Pivot(sheet, keyCols, [cursorCol]))', 'open Pivot Table: group rows by key column and summarize current column')

vd.addGlobals({
    'Pivot': Pivot,
    'PivotGroupRow': PivotGroupRow,
})
