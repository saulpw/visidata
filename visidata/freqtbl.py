import math
import collections

from visidata import *


theme('disp_histogram', '*', 'histogram element character')
option('disp_histolen', 50, 'width of histogram column')
option('histogram_bins', 0, 'number of bins for histogram of numeric columns')
option('numeric_binning', False, 'bin numeric columns into ranges', replay=True)


def valueNames(discrete_vals, numeric_vals):
    ret = [ '+'.join(str(x) for x in discrete_vals) ]
    if numeric_vals != (0, 0):
        ret.append('%s-%s' % numeric_vals)

    return '+'.join(ret)


class FreqTableSheet(PivotSheet):
    'Generate frequency-table sheet on currently selected column.'
    rowtype = 'bins'  # rowdef FreqRow(keys, sourcerows)

    def __init__(self, sheet, *groupByCols):
        fqcolname = '%s_%s_freq' % (sheet.name, '-'.join(col.name for col in groupByCols))
        super().__init__(fqcolname, groupByCols, [], source=sheet)
        self.largest = 1

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
                    ColumnAttr('count', 'sourcerows', type=vlen),
                    Column('percent', type=float, getter=lambda col,row: len(row.sourcerows)*100/col.sheet.source.nRows),
                    Column('histogram', type=str, getter=lambda col,row: options.disp_histogram*(options.disp_histolen*len(row.sourcerows)//col.sheet.largest), width=options.disp_histolen+2),
                    ]:
            self.addColumn(c)

        # two more threads
        vd.sync(self.addAggregateCols(),
                self.groupRows(self.updateLargest))

        if self.nCols > len(self.groupByCols)+3:  # hide percent/histogram if aggregations added
            self.column('percent').hide()
            self.column('histogram').hide()

        if not [c for c in self.groupByCols if vd.isNumeric(c)]:
            self.orderBy(self.column('count'), reverse=True)

    def openRow(self, row):
        'open copy of source sheet with rows that are grouped in current row'
        if row.sourcerows:
            vs = copy(self.source)
            vs.name += "_"+valueNames(row.discrete_keys, row.numeric_key)
            vs.rows=copy(row.sourcerows)
            return vs
        vd.warning("no source rows")

    def openCell(self, col, row):
        return Sheet.openCell(self, col, row)


class FreqTableSheetSummary(FreqTableSheet):
    'Append a PivotGroupRow to FreqTable with only selectedRows.'
    @asyncthread
    def reload(self):
        FreqTableSheet.reload.__wrapped__(self)
        self.addRow(PivotGroupRow(['Selected'], (0,0), self.source.selectedRows, {}))

Sheet.addCommand('F', 'freq-col', 'vd.push(FreqTableSheet(sheet, cursorCol))', 'open Frequency Table grouped on current column, with aggregations of other columns')
Sheet.addCommand('gF', 'freq-keys', 'vd.push(FreqTableSheet(sheet, *keyCols))', 'open Frequency Table grouped by all key columns on source sheet, with aggregations of other columns')
Sheet.addCommand('zF', 'freq-summary', 'vd.push(FreqTableSheetSummary(sheet, Column("Total", sheet=sheet, getter=lambda col, row: "Total")))', 'open one-line summary for all rows and selected rows')

ColumnsSheet.addCommand(ENTER, 'freq-row', 'vd.push(FreqTableSheet(source[0], cursorRow))', 'open a Frequency Table sheet grouped on column referenced in current row')

FreqTableSheet.addCommand('gu', 'unselect-rows', 'unselect(selectedRows)', 'unselect all source rows grouped in current row')
FreqTableSheet.addCommand('g'+ENTER, 'dive-rows', 'vs = copy(source); vs.name += "_several"; vs.rows=list(itertools.chain.from_iterable(row.sourcerows for row in selectedRows)); vd.push(vs)', 'open copy of source sheet with rows that are grouped in selected rows')
