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

def valueNames(*vals):
    return '-'.join(str(v) for v in vals)


class SheetFreqTable(SheetPivot):
    'Generate frequency-table sheet on currently selected column.'
    rowtype = 'bins'  # rowdef FreqRow(keys, sourcerows)

    def __init__(self, sheet, *groupByCols):
        fqcolname = '%s_%s_freq' % (sheet.name, '-'.join(col.name for col in groupByCols))
        super().__init__(fqcolname, groupByCols, [], source=sheet)
        self.largest = 100

    def selectRow(self, row):
        self.source.select(row.sourcerows)     # select all entries in the bin on the source sheet
        return super().selectRow(row)  # then select the bin itself on this sheet

    def unselectRow(self, row):
        self.source.unselect(row.sourcerows)
        return super().unselectRow(row)

    def updateLargest(self, grouprow):
        self.largest = max(self.largest, len(grouprow.sourcerows))

    @asyncthread
    def reload(self):
        'Generate frequency table then reverse-sort by length.'
        super().initCols()

        # add default bonus columns
        for c in [
                    ColumnAttr('count', 'sourcerows', type=len),
                    Column('percent', type=float, getter=lambda col,row: len(row.sourcerows)*100/col.sheet.source.nRows),
                    Column('histogram', type=str, getter=lambda col,row: options.disp_histogram*(options.disp_histolen*len(row.sourcerows)//col.sheet.largest), width=options.disp_histolen+2),
                    ]:
            self.addColumn(c)

        # two more threads
        self.addAggregateCols()
        self.groupRows(self.updateLargest)

        sync(1)

        if self.nCols > 4:  # hide percent/histogram if aggregations added
            self.column('percent').hide()
            self.column('histogram').hide()

        self.orderBy(self.column('count'), reverse=True)

SheetFreqTable.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)')
SheetFreqTable.addCommand('s', 'select-row', 'select([cursorRow]); cursorDown(1)')
SheetFreqTable.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)')

SheetFreqTable.addCommand(ENTER, 'dup-row', 'vs = copy(source); vs.name += "_"+valueNames(*cursorRow.discrete_keys, cursorRow.numeric_key); vs.rows=copy(cursorRow.sourcerows or error("no source rows")); vd.push(vs)')
