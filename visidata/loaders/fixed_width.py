
from visidata import *

option('fixed_rows', 1000, 'number of rows to check for fixed width columns')

def open_fixed(p):
    return FixedWidthColumnsSheet(p.name, source=p)

class FixedWidthColumn(Column):
    def __init__(self, name, i, j, **kwargs):
        super().__init__(name, **kwargs)
        self.i, self.j = i, j

    def getValue(self, row):
        return row[0][self.i:self.j]

    def setValue(self, row, value):
        row[0] = row[:self.i] + '%*s' % (self.j-self.i, value) + row[self.j:]

def columnize(rows):
    'Generate (i,j) indexes for fixed-width columns found in rows'

    ## find all character columns that are not spaces
    allNonspaces = set()
    allNonspaces.add(max(len(r) for r in rows)+1)
    for r in rows:
        for i, ch in enumerate(r):
            if not ch.isspace():
                allNonspaces.add(i)

    colstart = 0
    prev = 0

    # collapse fields
    for i in allNonspaces:
        if i > prev+1:
            yield colstart, prev+1
            colstart = i
        prev = i

class FixedWidthColumnsSheet(Sheet):
    rowtype = 'lines'
    columns = [ColumnItem('line', 0)]
    @async
    def reload(self):
        self.rows = []
        for line in self.source:
            self.addRow([line])

        self.columns = []
        # compute fixed width columns
        for i, j in columnize(list(r[0] for r in self.rows[:options.fixed_rows])):
            c = FixedWidthColumn('', i, j)
            c.name = '_'.join(c.getValue(r) for r in self.rows[:options.header])
            self.addColumn(c)

        # discard header rows
        self.rows = self.rows[options.header:]
