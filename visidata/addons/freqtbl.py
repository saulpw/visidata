
from visidata import *

command('F', 'vd.push(SheetFreqTable(sheet, cursorCol))', 'open frequency table from values in this column')

class SheetFreqTable(Sheet):
    def __init__(self, sheet, col):
        fqcolname = '%s_%s_freq' % (sheet.name, col.name)
        super().__init__(fqcolname, sheet)

        self.origCol = col
        self.values = collections.defaultdict(list)
        for r in sheet.rows:
            self.values[str(col.getValue(r))].append(r)

    def reload(self):
        self.rows = sorted(self.values.items(), key=lambda r: len(r[1]), reverse=True)  # sort by num reverse
        self.largest = len(self.rows[0][1])+1

        self.columns = [
            ColumnItem(self.origCol.name, 0, type=self.origCol.type),
            Column('num', int, lambda r: len(r[1])),
            Column('percent', float, lambda r: len(r[1])*100/self.source.nRows),
            Column('histogram', str, lambda r,s=self: options.ch_Histogram*int(len(r[1])*80/s.largest), width=80)
        ]
        self.nKeys = 1

        self.command(' ', 'source.toggle(cursorRow[1])', 'toggle these entries')
        self.command('s', 'source.select(cursorRow[1])', 'select these entries')
        self.command('u', 'source.unselect(cursorRow[1])', 'unselect these entries')
        self.command('^J', 'vd.push(source.copy()).rows = values[str(columns[0].getValue(cursorRow))]', 'push new sheet with only this value')

