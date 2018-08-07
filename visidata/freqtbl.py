import math

from visidata import *

Sheet.addCommand('F', 'freq-col', 'vd.push(SheetFreqTable(sheet, cursorCol))')
Sheet.addCommand('gF', 'freq-keys', 'vd.push(SheetFreqTable(sheet, *keyCols))')
globalCommand('zF', 'freq-rows', 'vd.push(SheetFreqTable(sheet, Column("Total", getter=lambda col,row: "Total")))')

theme('disp_histogram', '*', 'histogram element character')
option('disp_histolen', 50, 'width of histogram column')
#option('histogram_bins', 0, 'number of bins for histogram of numeric columns')
#option('histogram_even_interval', False, 'if histogram bins should have even distribution of rows')

ColumnsSheet.addCommand(ENTER, 'freq-row', 'vd.push(SheetFreqTable(source[0], cursorRow))')

def valueNames(vals):
    return '-'.join(str(v) for v in vals)


# rowdef: (keys, source_rows)
class SheetFreqTable(Sheet):
    'Generate frequency-table sheet on currently selected column.'
    rowtype = 'bins'
    def __init__(self, sheet, *columns):
        fqcolname = '%s_%s_freq' % (sheet.name, '-'.join(col.name for col in columns))
        super().__init__(fqcolname, source=sheet)
        self.origCols = columns
        self.largest = 100

        self.columns = [
            Column(c.name, type=c.type if c.type in typemap else anytype, width=c.width, fmtstr=c.fmtstr,
                        getter=lambda col,row,i=i: row[0][i],
                        setter=lambda col,row,v,i=i,origCol=c: setitem(row[0], i, v) and origCol.setValues(row[1], v))
                for i, c in enumerate(self.origCols)
        ]
        self.setKeys(self.columns)  # origCols are now key columns
        nkeys = len(self.keyCols)

        self.columns.extend([
            Column('count', type=int, getter=lambda col,row: len(row[1]), sql='COUNT(*)'),
            Column('percent', type=float, getter=lambda col,row: len(row[1])*100/col.sheet.source.nRows, sql=''),
            Column('histogram', type=str, getter=lambda col,row: options.disp_histogram*(options.disp_histolen*len(row[1])//col.sheet.largest), width=options.disp_histolen+2, sql=''),
        ])

        aggregatedCols = [Column(aggregator.__name__+'_'+c.name,
                                 type=aggregator.type or c.type,
                                 getter=lambda col,row,origcol=c,aggr=aggregator: aggr(origcol, row[1]),
                                 sql='%s(%s)' % (aggregator, c.name) )
                             for c in self.source.visibleCols
                                for aggregator in getattr(c, 'aggregators', [])
                         ]
        self.columns.extend(aggregatedCols)

        if aggregatedCols:  # hide percent/histogram if aggregations added
            for c in self.columns[nkeys+1:nkeys+3]:
                c.hide()

        self.groupby = columns
        self.orderby = [(self.columns[nkeys], -1)]  # count desc

    def selectRow(self, row):
        self.source.select(row[1])     # select all entries in the bin on the source sheet
        return super().selectRow(row)  # then select the bin itself on this sheet

    def unselectRow(self, row):
        self.source.unselect(row[1])
        return super().unselectRow(row)

    def numericBinning(self):
        nbins = options.histogram_bins or int(len(self.source.rows) ** (1./2))

        origCol = self.origCols[0]
        self.columns[0].type = str

        # separate rows with errors at the column from those without errors
        errorbin = []
        allbin = []
        for row in Progress(self.source.rows):
            try:
                v = origCol.getTypedValue(row)
                allbin.append((v, row))
            except Exception as e:
                errorbin.append((e, row))

        # find bin pivots from non-error values
        binPivots = []
        sortedValues = sorted(allbin, key=lambda x: x[0])

        if options.histogram_even_interval:
            binsize = len(sortedValues)/nbins
            pivotIdx = 0
            for i in range(math.ceil(len(sortedValues)/binsize)):
                firstVal = sortedValues[int(pivotIdx)][0]
                binPivots.append(firstVal)
                pivotIdx += binsize

        else:
            minval, maxval = sortedValues[0][0], sortedValues[-1][0]
            binWidth = (maxval - minval)/nbins
            binPivots = list((minval + binWidth*i) for i in range(0, nbins))

        binPivots.append(None)

        # put rows into bins (as self.rows) based on values
        binMinIdx = 0
        binMin = 0

        for binMax in binPivots[1:-1]:
            binrows = []
            for i, (v, row) in enumerate(sortedValues[binMinIdx:]):
                if binMax != binPivots[-2] and v > binMax:
                    break
                binrows.append(row)

            binMaxDispVal = origCol.format(binMax)
            binMinDispVal = origCol.format(binMin)
            if binMinIdx == 0:
                binName = '<=%s' % binMaxDispVal
            elif binMax == binPivots[-2]:
                binName = '>=%s' % binMinDispVal
            else:
                binName = '%s-%s' % (binMinDispVal, binMaxDispVal)

            self.addRow((binName, binrows))
            binMinIdx += i
            binMin = binMax

        if errorbin:
            self.rows.insert(0, ('errors', errorbin))

        ntallied = sum(len(x[1]) for x in self.rows)
        assert ntallied == len(self.source.rows), (ntallied, len(self.source.rows))

    def discreteBinning(self):
        rowidx = {}
        for r in Progress(self.source.rows):
            keys = list(forward(c.getTypedValue(r)) for c in self.origCols)

            # wrapply will pass-through a key-able TypedWrapper
            formatted_keys = tuple(wrapply(c.format, c.getTypedValue(r)) for c in self.origCols)
            histrow = rowidx.get(formatted_keys)
            if histrow is None:
                histrow = (keys, [])
                rowidx[formatted_keys] = histrow
                self.addRow(histrow)
            histrow[1].append(r)
            self.largest = max(self.largest, len(histrow[1]))

        self.rows.sort(key=lambda r: len(r[1]), reverse=True)  # sort by num reverse


    @asyncthread
    def reload(self):
        'Generate histrow for each row and then reverse-sort by length.'
        self.rows = []

#        if len(self.origCols) == 1 and self.origCols[0].type in (int, float, currency):
#            self.numericBinning()
#        else:
        self.discreteBinning()

        # automatically add cache to all columns now that everything is binned
        for c in self.nonKeyVisibleCols:
            c._cachedValues = collections.OrderedDict()

SheetFreqTable.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)')
SheetFreqTable.addCommand('s', 'select-row', 'select([cursorRow]); cursorDown(1)')
SheetFreqTable.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)')

SheetFreqTable.addCommand(ENTER, 'dup-row', 'vs = copy(source); vs.name += "_"+valueNames(cursorRow[0]); vs.rows=copy(cursorRow[1]); vd.push(vs)')
#        Command('v', 'options.histogram_even_interval = not options.histogram_even_interval; reload()', 'toggle histogram_even_interval option')
