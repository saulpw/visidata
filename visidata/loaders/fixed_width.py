
from visidata import VisiData, vd, Sheet, Column, Progress, SequenceSheet, dispwidth
from visidata import WritableColumn


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
    nlen = dispwidth(col.name, literal=True)
    if len(rows) > 0:
        w_max = 0
        for r in rows:
            row_w = dispwidth(col.getDisplayValue(r), literal=True)
            if w_max < row_w:
                w_max = row_w
        w = w_max
    return max(w, nlen)

class FixedWidthColumn(WritableColumn):
    def __init__(self, name, i, j, **kwargs):
        super().__init__(name, **kwargs)
        self.i, self.j = i, j

    def calcValue(self, row):
        return row[0][self.i:self.j]

    def putValue(self, row, value):
        j = self.j or len(row[0])
        value = str(value)[:j-self.i]
        row[0] = row[0][:self.i] + '%-*s' % (j-self.i, value) + row[0][j:]

def columnize(rows, has_header=True):
    'Generate (i,j) indexes for fixed-width columns found in rows'

    if not rows:
        return

    # Use first row (header) to determine column positions  #2265
    # This prevents data with internal spaces from creating false column splits
    # With no header (header=0), find columns where ALL rows have spaces  #2265
    if has_header:
        detect_rows = [rows[0]]
    else:
        detect_rows = rows

    colstarts = []
    maxlen = max(len(r) for r in detect_rows)
    for i in range(maxlen):
        all_space = all(i >= len(r) or r[i].isspace() for r in detect_rows)
        if not all_space:
            if i == 0 or all(i-1 >= len(r) or r[i-1].isspace() for r in detect_rows):
                colstarts.append(i)

    if not colstarts:
        return

    # find actual end of each column using all rows  #2255
    allNonspaces = set()
    for r in rows:
        for i, ch in enumerate(r):
            if not ch.isspace():
                allNonspaces.add(i)
    for idx, start in enumerate(colstarts):
        if idx + 1 < len(colstarts):
            # column ends at last non-space position before next column start
            nextstart = colstarts[idx + 1]
            end = start
            for pos in range(start, nextstart):
                if pos in allNonspaces:
                    end = pos + 1
            yield start, end  #2255
        else:
            # final column: find last non-space position
            end = start
            for pos in allNonspaces:
                if pos >= start and pos + 1 > end:
                    end = pos + 1
            yield start, end


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
        for i, j in columnize(list(r[0] for r in fixedRows), has_header=bool(self.options.header)):
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

FixedWidthColumnsSheet.options.null_value = ''    # the file format cannot contain None, so use empty string instead
