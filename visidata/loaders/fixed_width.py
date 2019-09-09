
from visidata import *

option('fixed_rows', 1000, 'number of rows to check for fixed width columns')
option('fixed_maxcols', 0, 'max number of fixed-width columns to create (0 is no max)')

def open_fixed(p):
    return FixedWidthColumnsSheet(p.name, source=p)

class FixedWidthColumn(Column):
    def __init__(self, name, i, j, **kwargs):
        super().__init__(name, **kwargs)
        self.i, self.j = i, j

    def calcValue(self, row):
        return row[0][self.i:self.j]

    def putValue(self, row, value):
        value = str(value)[:self.j-self.i]
        j = self.j or len(row)
        row[0] = row[0][:self.i] + '%-*s' % (j-self.i, value) + row[0][self.j:]

def columnize(rows):
    'Generate (i,j) indexes for fixed-width columns found in rows'

    ## find all character columns that are not spaces ever
    allNonspaces = set()
    for r in rows:
        for i, ch in enumerate(r):
            if not ch.isspace():
                allNonspaces.add(i)

    colstart = 0
    prev = 0

    # collapse fields
    for i in allNonspaces:
        if i > prev+1:
            yield colstart, i
            colstart = i
        prev = i

    yield colstart, None   # final column gets rest of line


class FixedWidthColumnsSheet(Sheet):
    rowtype = 'lines'  # rowdef: [line] (wrapping in list makes it unique and modifiable)
    columns = [ColumnItem('line', 0)]
    @asyncthread
    def reload(self):
        self.rows = []
        maxcols = options.fixed_maxcols
        for line in self.source:
            self.addRow([line])

        self.columns = []
        # compute fixed width columns
        for i, j in columnize(list(r[0] for r in self.rows[:options.fixed_rows])):
            if maxcols and self.nCols >= maxcols-1:
                self.addColumn(FixedWidthColumn('', i, None))
                break
            else:
                self.addColumn(FixedWidthColumn('', i, j))

        self.setColNames(self.rows[:options.header])
        self.rows = self.rows[options.header:]
