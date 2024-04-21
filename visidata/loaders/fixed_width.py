
from visidata import VisiData, vd, Sheet, Column, Progress, SequenceSheet, dispwidth


vd.option('fixed_rows', 1000, 'number of rows to check for fixed width columns')
vd.option('fixed_maxcols', 0, 'max number of fixed-width columns to create (0 is no max)')

@VisiData.api
def open_fixed(vd, p):
    return FixedWidthColumnsSheet(p.base_stem, source=p, headerlines=[])

@Column.api
def getMaxDataWidth(col, rows):  #2255 need real max width for fixed width saver
    '''Return the maximum length of any cell in column or its header,
    even if wider than window. (Slow for large cells!)'''

    w = 0
    nlen = dispwidth(col.name)
    if len(rows) > 0:
        w_max = 0
        for r in rows:
            row_w = dispwidth(col.getDisplayValue(r))
            if w_max < row_w:
                w_max = row_w
        w = w_max
    return max(w, nlen)

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
            yield colstart, prev+1 #2255
            colstart = i
        prev = i

    yield colstart, prev+1   # final column gets rest of line


class FixedWidthColumnsSheet(SequenceSheet):
    rowtype = 'lines'  # rowdef: [line] (wrapping in list makes it unique and modifiable)
    def addRow(self, row, index=None):
        Sheet.addRow(self, row, index=index)

    def iterload(self):
        itsource = iter(self.source)

        # compute fixed width columns from first fixed_rows lines
        maxcols = self.options.fixed_maxcols
        self.columns = []
        fixedRows = list([x] for x in self.optlines(itsource, 'fixed_rows'))
        for i, j in columnize(list(r[0] for r in fixedRows)):
            if maxcols and self.nCols >= maxcols-1:
                self.addColumn(FixedWidthColumn('', i, None))
                break
            else:
                self.addColumn(FixedWidthColumn('', i, j))

        yield from fixedRows

        self.setColNames(self.headerlines)

        yield from ([line] for line in itsource)

    def setCols(self, headerlines):
        self.headerlines = headerlines


@VisiData.api
def save_fixed(vd, p, *vsheets):
    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
        for sheet in vsheets:
            if len(vsheets) > 1:
                fp.write('%s\n\n' % sheet.name)

            widths = {}  # Column -> width:int
            # headers
            for col in Progress(sheet.visibleCols, gerund='sizing'):
                widths[col] = col.getMaxDataWidth(sheet.rows)  #1849 #2255
                fp.write(('{0:%s} ' % widths[col]).format(col.name))
            fp.write('\n')

            # rows
            with Progress(gerund='saving'):
                for dispvals in sheet.iterdispvals(format=True):
                    for col, val in dispvals.items():
                        fp.write(('{0:%s%s.%s} ' % ('>' if vd.isNumeric(col) else '<', widths[col], widths[col])).format(val))
                    fp.write('\n')
