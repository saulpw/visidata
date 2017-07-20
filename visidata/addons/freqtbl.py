import math

from visidata import *

command('F', 'vd.push(SheetFreqTable(sheet, cursorCol))', 'open frequency table from values in this column')
command('gF', 'vd.push(SheetFreqTable(sheet, combineColumns(columns[:nKeys])))', 'open frequency table for the combined key columns')

theme('disp_histogram', '*')
option('disp_histolen', 80, 'width of histogram column')
option('histogram_bins', 0, 'number of bins for histogram of numeric columns')
option('histogram_even_interval', False, 'if histogram bins should have even distribution of rows')


class SheetFreqTable(Sheet):
    'Generate frequency-table sheet on currently selected column.'
    def __init__(self, sheet, col):
        fqcolname = '%s_%s_freq' % (sheet.name, col.name)
        super().__init__(fqcolname, sheet)
        self.origCol = col
        self.largest = 100

        self.columns = [
            ColumnItem(col.name, 0, type=col.type, width=30),
            Column('num', int, lambda r: len(r[1])),
            Column('percent', float, lambda r: len(r[1])*100/self.source.nRows),
        ]
        self.nKeys = 1

        for c in self.source.visibleCols:
            if c.aggregator:
                self.columns.append(Column(c.aggregator.__name__+'_'+c.name,
                                           type=c.aggregator.type or c.type,
                                           getter=lambda r,c=c: c.aggregator(c.values(r[1]))))

        if len(self.columns) == 3:
            self.columns.append(Column('histogram', str, lambda r,s=self: options.disp_histogram*(options.disp_histolen*len(r[1])//s.largest), width=None))

        # redefine these commands only to change the helpstr
        self.command(' ', 'toggle([cursorRow]); cursorDown(1)', 'toggle these entries in the source sheet')
        self.command('s', 'select([cursorRow]); cursorDown(1)', 'select these entries in the source sheet')
        self.command('u', 'unselect([cursorRow]); cursorDown(1)', 'unselect these entries in the source sheet')

        self.command(ENTER, 'vd.push(source.copy("_"+cursorRow[0])).rows = cursorRow[1].copy()', 'push new sheet with only source rows for this value')
        self.command('w', 'options.histogram_even_interval = not options.histogram_even_interval; reload()', 'toggle histogram_even_interval option')

    def selectRow(self, row):
        self.source.select(row[1])     # select all entries in the bin on the source sheet
        return super().selectRow(row)  # then select the bin itself on this sheet

    def unselectRow(self, row):
        self.source.unselect(row[1])
        return super().unselectRow(row)

    @async
    def reload(self):
        'Generate histrow for each row and then reverse-sort by length.'
        rowidx = {}
        self.rows = []

        nbins = options.histogram_bins or int(len(self.source.rows) ** (1./2))

        if nbins and self.origCol.type in (int, float, currency):
            self.columns[0]._type = str

            # separate rows with errors at the column from those without errors
            errorbin = []
            allbin = []
            for row in self.genProgress(self.source.rows):
                v = self.origCol.getValue(row)
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

                binMaxDispVal = self.origCol.format(binMax)
                binMinDispVal = self.origCol.format(binMin)
                if binMinIdx == 0:
                    binName = '<=%s' % binMaxDispVal
                elif binMax == binPivots[-2]:
                    binName = '>=%s' % binMinDispVal
                else:
                    binName = '%s-%s' % (binMinDispVal, binMaxDispVal)

                self.rows.append((binName, binrows))
                binMinIdx += i
                binMin = binMax

            if errorbin:
                self.rows.insert(0, ('errors', errorbin))

            ntallied = sum(len(x[1]) for x in self.rows)
            assert ntallied == len(self.source.rows), (ntallied, len(self.source.rows))
        else:
            for r in self.genProgress(self.source.rows):
                v = str(self.origCol.getValue(r))
                histrow = rowidx.get(v)
                if histrow is None:
                    histrow = (v, [])
                    rowidx[v] = histrow
                    self.rows.append(histrow)
                histrow[1].append(r)

            self.rows.sort(key=lambda r: len(r[1]), reverse=True)  # sort by num reverse

        self.largest = len(self.rows[0][1])+1
