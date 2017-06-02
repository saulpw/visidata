
from visidata import *

command('F', 'vd.push(SheetFreqTable(sheet, cursorCol))', 'open frequency table from values in this column')
command('gF', 'vd.push(SheetFreqTable(sheet, combineColumns(columns[:nKeys])))', 'open frequency table for the combined key columns')

theme('disp_histogram', '*')

class SheetFreqTable(Sheet):
    """Generate frequency-table sheet on currently selected column."""
    def __init__(self, sheet, col):
        fqcolname = '%s_%s_freq' % (sheet.name, col.name)
        super().__init__(fqcolname, sheet)
        self.origCol = col
        self.largest = 100

        self.columns = [
            ColumnItem(col.name, 0, type=col.type, width=30),
            Column('num', int, lambda r: len(r[1])),
            Column('percent', float, lambda r: len(r[1])*100/self.source.nRows),
            Column('histogram', str, lambda r,s=self: options.disp_histogram*int(len(r[1])*80/s.largest), width=80)
        ]

        for c in self.source.visibleCols:
            if c.aggregator:
                self.columns.append(Column(c.aggregator.__name__+'_'+c.name,
                                           type=c.aggregator.type or c.type,
                                           getter=lambda r,c=c: c.aggregator(c.values(r[1]))))

        self.nKeys = 1

        # redefine these commands only to change the helpstr
        self.command(' ', 'toggle([cursorRow]); cursorDown(1)', 'toggle these entries in the source sheet')
        self.command('s', 'select([cursorRow]); cursorDown(1)', 'select these entries in the source sheet')
        self.command('u', 'unselect([cursorRow]); cursorDown(1)', 'unselect these entries in the source sheet')

        self.command('^J', 'vd.push(source.copy("_"+cursorRow[0])).rows = cursorRow[1].copy()', 'push new sheet with only source rows for this value')

    def selectRow(self, row):
        self.source.select(row[1])
        return super().selectRow(row)

    def unselectRow(self, row):
        self.source.unselect(row[1])
        return super().unselectRow(row)

    @async
    def reload(self):
        """Generate histrow for each row and then reverse-sort by length."""
        rowidx = {}
        self.rows = []
        self.progressTotal = len(self.source.rows)
        for r in self.source.rows:
            self.progressMade += 1
            v = str(self.origCol.getValue(r))
            histrow = rowidx.get(v)
            if histrow is None:
                histrow = (v, [])
                rowidx[v] = histrow
                self.rows.append(histrow)
            histrow[1].append(r)

        self.rows.sort(key=lambda r: len(r[1]), reverse=True)  # sort by num reverse
        self.largest = len(self.rows[0][1])+1
