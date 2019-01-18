import math
import collections

from visidata import *

Sheet.addCommand('F', 'freq-col', 'vd.push(SheetFreqTable(sheet, cursorCol))')
Sheet.addCommand('gF', 'freq-keys', 'vd.push(SheetFreqTable(sheet, *keyCols))')
globalCommand('zF', 'freq-rows', 'vd.push(SheetFreqTable(sheet, Column("Total", getter=lambda col,row: "Total")))')

theme('disp_histogram', '*', 'histogram element character')
option('disp_histolen', 50, 'width of histogram column')
option('histogram_bins', 0, 'number of bins for histogram of numeric columns')

ColumnsSheet.addCommand(ENTER, 'freq-row', 'vd.push(SheetFreqTable(source[0], cursorRow))')

def valueNames(vals):
    return '-'.join(str(v) for v in vals)


FreqRow = collections.namedtuple('FreqRow', ['keys', 'numrange', 'sourcerows'])

class SheetFreqTable(Sheet):
    'Generate frequency-table sheet on currently selected column.'
    rowtype = 'bins'  # rowdef FreqRow(keys, sourcerows)

    def __init__(self, sheet, *columns):
        fqcolname = '%s_%s_freq' % (sheet.name, '-'.join(col.name for col in columns))
        super().__init__(fqcolname, source=sheet)
        self.origCols = columns
        self.largest = 100

        self.columns = [
            Column(c.name, type=c.type if c.type in typemap else anytype, width=c.width, fmtstr=c.fmtstr,
                        getter=lambda col,row,i=i: row.keys[i],
                        setter=lambda col,row,v,i=i,origCol=c: setitem(row.keys, i, v) and origCol.setValues(row.sourcerows, v))
                for i, c in enumerate(self.origCols) if not isNumeric(c)
        ]
        for origCol in self.origCols:
            if isNumeric(origCol):
                self.addColumn(Column(origCol.name, width=origCol.width*2, getter=lambda c,r,origCol=origCol: ' - '.join(origCol.format(x) for x in r.numrange)))

        self.setKeys(self.columns)  # origCols are now key columns
        nkeys = len(self.keyCols)

        self.columns.extend([
            Column('count', type=int, getter=lambda col,row: len(row.sourcerows), sql='COUNT(*)'),
            Column('percent', type=float, getter=lambda col,row: len(row.sourcerows)*100/col.sheet.source.nRows, sql=''),
            Column('histogram', type=str, getter=lambda col,row: options.disp_histogram*(options.disp_histolen*len(row.sourcerows)//col.sheet.largest), width=options.disp_histolen+2, sql=''),
        ])

        aggregatedCols = [Column(aggregator.__name__+'_'+c.name,
                                 type=aggregator.type or c.type,
                                 getter=lambda col,row,origcol=c,aggr=aggregator: aggr(origcol, row.sourcerows),
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
        self.source.select(row.sourcerows)     # select all entries in the bin on the source sheet
        return super().selectRow(row)  # then select the bin itself on this sheet

    def unselectRow(self, row):
        self.source.unselect(row.sourcerows)
        return super().unselectRow(row)

    @asyncthread
    def reload(self):
        'Generate FreqRow(s) for each row and then reverse-sort by length.'
        self.rows = []

        numericCols = [c for c in self.origCols if isNumeric(c)]
        discreteCols = [c for c in self.origCols if not isNumeric(c)]
        if len(numericCols) > 1:
            error('only one numeric column can be binned')

        if numericCols:
            nbins = options.histogram_bins or int(len(self.source.rows) ** (1./2))
            vals = tuple(numericCols[0].getValues(self.source.rows))
            minval = min(vals)
            maxval = max(vals)
            width = (maxval - minval)/nbins
            buckets = [(minval+width*i, minval+width*(i+1)) for i in range(nbins)]
        else:
            buckets = []

        rowidx = {}  # [formatted_keys] -> FreqRow(keys, numrange, sourcerows)
        for r in Progress(self.source.rows, 'binning'):
            keys = tuple(forward(c.getTypedValue(r)) for c in discreteCols)
            # wrapply will pass-through a key-able TypedWrapper
            formatted_keys = tuple(wrapply(c.format, c.getTypedValue(r)) for c in discreteCols)
            histrows, mainrow = rowidx.get(formatted_keys, (None, None))
            if histrows is None:
                mainrow = FreqRow(keys, None, [])
                histrows = [FreqRow(keys, b, []) for b in buckets]
                rowidx[formatted_keys] = (histrows, mainrow)
                for histrow in histrows:
                    self.addRow(histrow)
                self.addRow(mainrow)

            freqrow = mainrow  # error row if numericCols

            if numericCols:
                val = numericCols[0].getTypedValue(r)
                if minval <= val <= maxval:  # within range (not
                    b = int((val-minval)//width)
                    freqrow = histrows[min(b, nbins-1)]

            freqrow.sourcerows.append(r)
            self.largest = max(self.largest, len(freqrow.sourcerows))

        if not numericCols:
            self.rows.sort(key=lambda r: len(r.sourcerows), reverse=True)  # sort by num reverse

        # automatically add cache to all columns now that everything is binned
        for c in self.nonKeyVisibleCols:
            c._cachedValues = collections.OrderedDict()


SheetFreqTable.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)')
SheetFreqTable.addCommand('s', 'select-row', 'select([cursorRow]); cursorDown(1)')
SheetFreqTable.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)')

SheetFreqTable.addCommand(ENTER, 'dup-row', 'vs = copy(source); vs.name += "_"+valueNames(cursorRow.keys); vs.rows=copy(cursorRow.sourcerows or error("no source rows")); vd.push(vs)')
