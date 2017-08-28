
from visidata import *

option('fixed_rows', 1000, 'number of rows to check for fixed width columns')

def open_fixed(p):
    return FixedWidthColumnsSheet(p.name, p)

def FixedWidthColumn(name, i, j, **kwargs):
    return Column(name, getter=lambda r,i=i,j=j: r[i:j], **kwargs)

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
    def reload(self):
        self.columns = []
        self.rows = list(readlines(self.source.open_text()))

        # compute fixed width columns
        for i, j in columnize(self.rows[:options.fixed_rows]):
            c = FixedWidthColumn('', i, j)
            c.name = '_'.join(c.getValue(r) for r in self.rows[:options.headerlines])
            self.addColumn(c)

        # discard header rows
        self.rows = self.rows[options.headerlines:]
