
from visidata import *

command('F', 'vd.push(SheetFreqTable(sheet, cursorCol))', 'open frequency table from values in this column')

class SheetFreqTable(Sheet):
    def __init__(self, sheet, col):
        fqcolname = '%s_%s_freq' % (sheet.name, col.name)
        super().__init__(fqcolname, sheet)
        self.origCol = col

        self.columns = [
            ColumnItem(col.name, 0, type=col.type),
            Column('num', int, lambda r: len(r[1])),
            Column('percent', float, lambda r: len(r[1])*100/self.source.nRows),
            Column('histogram', str, lambda r,s=self: options.ch_Histogram*int(len(r[1])*80/s.largest), width=80)
        ]
        self.nKeys = 1
        self.command(' ', 'source.toggle(cursorRow[1]); toggle([cursorRow]); cursorDown(1)', 'toggle these entries in the source sheet')
        self.command('s', 'source.select(cursorRow[1]); select([cursorRow]); cursorDown(1)', 'toggle these entries in the source sheet')
        self.command('u', 'source.unselect(cursorRow[1]); unselect([cursorRow]); cursorDown(1)', 'toggle these entries in the source sheet')
        self.command('^J', 'vd.push(source.copy("_"+cursorRow[0])).rows = cursorRow[1].copy()', 'push new sheet with only source rows for this value')

    @async
    def reload(self):
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
