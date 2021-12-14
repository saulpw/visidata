
from visidata import VisiData, vd, Sheet, Column, Progress, SequenceSheet


vd.option('fixed_rows', 1000, 'number of rows to check for fixed width columns')
vd.option('fixed_maxcols', 0, 'max number of fixed-width columns to create (0 is no max)')

@VisiData.api
def open_fixed(vd, p):
    return FixedWidthColumnsSheet(p.name, source=p, headerlines=[])

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
    with p.open_text(mode='w', encoding=vsheets[0].options.encoding) as fp:
        for sheet in vsheets:
            if len(vsheets) > 1:
                fp.write('%s\n\n' % sheet.name)

            widths = {}  # Column -> width:int
            # headers
            for col in Progress(sheet.visibleCols, gerund='sizing'):
                widths[col] = col.width or sheet.options.default_width or col.getMaxWidth(sheet.rows)
                fp.write(('{0:%s} ' % widths[col]).format(col.name))
            fp.write('\n')

            # rows
            with Progress(gerund='saving'):
                for dispvals in sheet.iterdispvals(format=True):
                    for col, val in dispvals.items():
                        fp.write(('{0:%s%s.%s} ' % ('>' if vd.isNumeric(col) else '<', widths[col], widths[col])).format(val))
                    fp.write('\n')

            vd.status('%s save finished' % p)
