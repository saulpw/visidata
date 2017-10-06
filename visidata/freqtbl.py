import math

from visidata import *
globalCommand('F', 'vd.push(SheetFreqTable(sheet, cursorCol))', 'open Frequency Table grouped on current column')
globalCommand('gF', 'vd.push(SheetFreqTable(sheet, *keyCols))', 'open Frequency Table grouped by all key columns on the source sheet')
globalCommand('zF', 'vd.push(SheetFreqTable(sheet, Column("Total", getter=lambda r: "Total")))', 'open a one-line summary for all selected rows')

theme('disp_histogram', '*', 'histogram element character')
option('disp_histolen', 80, 'width of histogram column')
#option('histogram_bins', 0, 'number of bins for histogram of numeric columns')
#option('histogram_even_interval', False, 'if histogram bins should have even distribution of rows')

ColumnsSheet.commands += [
    Command(ENTER, 'vd.push(SheetFreqTable(source, cursorRow))', 'open a Frequency Table grouped on column referenced in current row')
]

def getValueOrError(c, r):
    try:
        return c.getValue(r)
    except EscapeException:
        raise
    except Exception as e:
        return 'error: %s' % e


def valueNames(vals):
    return '-'.join(str(v) for v in vals)

# rowdef: ([bin_values], source_rows)
class SheetFreqTable(Sheet):
    'Generate frequency-table sheet on currently selected column.'
    commands = [
        # redefine these commands only to change the helpstr
        Command('t', 'toggle([cursorRow]); cursorDown(1)', 'toggle these entries in source sheet'),
        Command('s', 'select([cursorRow]); cursorDown(1)', 'select these entries in source sheet'),
        Command('u', 'unselect([cursorRow]); cursorDown(1)', 'unselect these entries in source sheet'),

        Command(ENTER, 'vs = copy(source); vs.name += "_"+valueNames(cursorRow[0]); vs.rows=copy(cursorRow[1]); vd.push(vs)', 'push new sheet with only source rows for this value'),
#        Command('w', 'options.histogram_even_interval = not options.histogram_even_interval; reload()', 'toggle histogram_even_interval option')
    ]

    def __init__(self, sheet, *columns):
        fqcolname = '%s_%s_freq' % (sheet.name, '-'.join(col.name for col in columns))
        super().__init__(fqcolname, sheet)
        self.origCols = columns
        self.largest = 100

        self.nKeys = len(self.origCols)

        self.columns = [
            Column(col.name, type=col.type, width=col.width, getter=lambda r,i=i: r[0][i]) for i, col in enumerate(self.origCols)
        ]

        self.columns.extend([
            Column('count', type=int, getter=lambda r: len(r[1])),
            Column('percent', type=float, getter=lambda r: len(r[1])*100/self.source.nRows),
            Column('histogram', type=str, getter=lambda r,s=self: options.disp_histogram*(options.disp_histolen*len(r[1])//s.largest), width=None),
        ])

        aggregatedCols = [Column(aggregator.__name__+'_'+c.name,
                                 type=aggregator.type or c.type,
                                 getter=lambda r,c=c,aggr=aggregator: aggr(c, r[1]))
                             for c in self.source.visibleCols
                                for aggregator in getattr(c, 'aggregators', [])
                         ]
        self.columns.extend(aggregatedCols)

        if aggregatedCols:  # hide percent/histogram if aggregations added
            for c in self.columns[self.nKeys+1:self.nKeys+3]:
                c.width = 0


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
        for row in self.genProgress(self.source.rows):
            v = origCol.getTypedValue(row)
            if not v:
                errorbin.append(row)
            else:
                allbin.append((v, row))

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
        for r in self.genProgress(self.source.rows):
            v = tuple(getValueOrError(c, r) for c in self.origCols)
            histrow = rowidx.get(v)
            if histrow is None:
                histrow = (v, [])
                rowidx[v] = histrow
                self.addRow(histrow)
            histrow[1].append(r)
            self.largest = max(self.largest, len(histrow[1]))

        self.rows.sort(key=lambda r: len(r[1]), reverse=True)  # sort by num reverse


    @async
    def reload(self):
        'Generate histrow for each row and then reverse-sort by length.'
        self.rows = []

#        if len(self.origCols) == 1 and self.origCols[0].type in (int, float, currency):
#            self.numericBinning()
#        else:
        self.discreteBinning()

        # automatically add cache to all columns now that everything is binned
        for c in self.visibleCols:
            c._cachedValues = collections.OrderedDict()


