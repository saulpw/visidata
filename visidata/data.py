import random

from .vdtui import *

option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
option('headerlines', 1, 'parse first N rows of .csv/.tsv as column names')
option('skiplines', 0, 'skip first N lines of text input')
option('filetype', '', 'specify file type')

# slide rows/columns around
globalCommand('H', 'moveVisibleCol(cursorVisibleColIndex, max(cursorVisibleColIndex-1, 0)); sheet.cursorVisibleColIndex -= 1', 'slides current column left')
globalCommand('J', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, min(cursorRowIndex+1, nRows-1))', 'moves current row down')
globalCommand('K', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, max(cursorRowIndex-1, 0))', 'moves current row up')
globalCommand('L', 'moveVisibleCol(cursorVisibleColIndex, min(cursorVisibleColIndex+1, nVisibleCols-1)); sheet.cursorVisibleColIndex += 1', 'moves current column right')
globalCommand('gH', 'moveListItem(columns, cursorColIndex, nKeys)', 'slides current column all the way to the left of sheet')
globalCommand('gJ', 'moveListItem(rows, cursorRowIndex, nRows)', 'slides current row to the bottom of sheet')
globalCommand('gK', 'moveListItem(rows, cursorRowIndex, 0)', 'slides current row all the way to the top of sheet')
globalCommand('gL', 'moveListItem(columns, cursorColIndex, nCols)', 'slides current column all the way to the right of sheet')

globalCommand('c', 'searchColumnNameRegex(input("column name regex: ", "regex"), moveCursor=True)', 'moves to the next column with name matching regex')
globalCommand('r', 'moveRegex(regex=input("row key regex: ", "regex"), columns=keyCols or [visibleCols[0]])', 'moves to the next row with key matching regex')
globalCommand('zc', 'sheet.cursorVisibleColIndex = int(input("column number: "))', 'moves to the given column number')
globalCommand('zr', 'sheet.cursorRowIndex = int(input("row number: "))', 'moves to the given row number')

globalCommand('P', 'nrows=int(input("random population size: ")); vs=vd.push(copy(sheet)); vs.name+="_sample"; vs.rows=random.sample(rows, nrows)', 'opens duplicate sheet with a random population subset of # rows')

globalCommand('a', 'rows.insert(cursorRowIndex+1, newRow()); cursorDown(1)', 'appends a blank row')
globalCommand('f', 'fillNullValues(cursorCol, selectedRows or rows)', 'fills null cells in current column with previous non-null value')

def fillNullValues(col, rows):
    'Fill null cells in col with the previous non-null value'
    lastval = None
    nullfunc = isNullFunc()
    n = 0
    for r in rows:
        val = col.getValue(r)
        if nullfunc(val):
            if lastval:
                col.setValue(r, lastval)
                n += 1
        else:
            lastval = val

    status("filled %d values" % n)


def updateColNames(sheet):
    for c in sheet.visibleCols:
        if not c._name:
            c.name = "_".join(c.getDisplayValue(r) for r in sheet.selectedRows or [sheet.cursorRow])

globalCommand('z^', 'sheet.cursorCol.name = cursorDisplay', 'sets current column name to value in current cell')
globalCommand('g^', 'updateColNames(sheet)', 'sets visible column names to values in selected rows (or current row)')
globalCommand('gz^', 'sheet.cursorCol.name = "_".join(sheet.cursorCol.getDisplayValue(r) for r in selectedRows or [cursorRow]) ', 'sets current column name to combined values in selected rows (or current row)')
# gz^ with no selectedRows is same as z^

globalCommand('o', 'vd.push(openSource(input("open: ", "filename")))', 'opens input in VisiData')
globalCommand('^S', 'saveSheet(sheet, input("save to: ", "filename", value=getDefaultSaveName(sheet)), options.confirm_overwrite)', 'saves current sheet to filename in format determined by extension (default .tsv)')

globalCommand('z=', 'status(evalexpr(input("status=", "expr"), cursorRow))', 'evaluates Python expression on current row and displays result on status line')

globalCommand('A', 'vd.push(newSheet(int(input("num columns for new sheet: "))))', 'opens new blank sheet with number columns')

globalCommand('gKEY_F(1)', 'help-commands')  # vdtui generic commands sheet
globalCommand('gz?', 'help-commands')  # vdtui generic commands sheet

# in VisiData, F1/z? refer to the man page
globalCommand('z?', 'with SuspendCurses(): os.system("man vd")', 'launches VisiData manpage')
globalCommand('KEY_F(1)', 'z?')

def newSheet(ncols):
    return Sheet('unnamed', columns=[ColumnItem('', i, width=8) for i in range(ncols)])

def readlines(linegen):
    'Generate lines from linegen, skipping first options.skiplines lines and stripping trailing newline'
    skiplines = options.skiplines
    for i, line in enumerate(linegen):
        if i < skiplines:
            continue
        yield line[:-1]

def getDefaultSaveName(sheet):
    if isinstance(sheet.source, Path):
        return str(sheet.source)
    else:
        return sheet.name+".tsv"

def saveSheet(vs, fn, confirm_overwrite=False):
    'Save sheet `vs` with given filename `fn`.'
    if Path(fn).exists():
        if options.confirm_overwrite:
            confirm('%s already exists. overwrite? ' % fn)

    basename, ext = os.path.splitext(fn)
    funcname = 'save_' + ext[1:]
    if funcname not in getGlobals():
        funcname = 'save_tsv'
    getGlobals().get(funcname)(vs, fn)
    status('saving to ' + fn)


class DirSheet(Sheet):
    'Sheet displaying directory, using ENTER to open a particular file.'
    commands = [
        Command(ENTER, 'vd.push(openSource(cursorRow[0]))', 'open file')  # path, filename
    ]
    columns = [
        Column('filename', getter=lambda r: r[0].name + r[0].ext),
        Column('type', getter=lambda r: r[0].is_dir() and '/' or r[0].suffix),
        Column('size', type=int, getter=lambda r: r[1].st_size),
        Column('mtime', type=date, getter=lambda r: r[1].st_mtime)
    ]

    def reload(self):
        self.rows = [(p, p.stat()) for p in self.source.iterdir()]  #  if not p.name.startswith('.')]


def openSource(p, filetype=None):
    'calls open_ext(Path) or openurl_scheme(UrlPath)'
    if isinstance(p, str):
        if '://' in p:
            p = UrlPath(p)
            filetype = filetype or p.scheme
            openfunc = 'openurl_' + p.scheme
            vs = getGlobals()[openfunc](p)
        else:
            return openSource(Path(p), filetype)  # convert to Path and recurse
    elif isinstance(p, Path):
        if not filetype:
            filetype = options.filetype or p.suffix

        if os.path.isdir(p.resolve()):
            vs = DirSheet(p.name, p)
            filetype = 'dir'
        else:
            openfunc = 'open_' + filetype.lower()
            if openfunc not in getGlobals():
                status('no %s function' % openfunc)
                filetype = 'txt'
                openfunc = 'open_txt'
            vs = getGlobals()[openfunc](p)
    else:  # some other object
        status('unknown object type %s' % type(p))
        vs = None

    if vs:
        status('opening %s as %s' % (p.name, filetype))

    return vs

#### enable external addons
def open_vd(p):
    'Opens a .vd file as a .tsv file'
    vs = open_tsv(p)
    vs.reload()
    return vs

def open_py(p):
    'Load a .py addon into the global context.'
    contents = p.read_text()
    exec(contents, getGlobals())
    status('executed %s' % p)

def open_txt(p):
    'Create sheet from `.txt` file at Path `p`, checking whether it is TSV.'
    with p.open_text() as fp:
        if '\t' in next(fp):    # peek at the first line
            return open_tsv(p)  # TSV often have .txt extension
        return TextSheet(p.name, p)

def _getTsvHeaders(fp, nlines):
    headers = []
    i = 0
    while i < nlines:
        L = next(fp)
        L = L[:-1]
        if L:
            headers.append(L.split('\t'))
            i += 1

    return headers

def open_tsv(p, vs=None):
    'Parse contents of Path `p` and populate columns.'

    if vs is None:
        vs = Sheet(p.name, p)
        vs.loader = lambda vs=vs: reload_tsv(vs)

    header_lines = int(options.headerlines)

    with vs.source.open_text() as fp:
        headers = _getTsvHeaders(fp, header_lines or 1)  # get one data line if no headers

        if header_lines == 0:
            vs.columns = ArrayColumns(len(headers[0]))
        else:
            # columns ideally reflect the max number of fields over all rows
            # but that's a lot of work for a large dataset
            vs.columns = ArrayNamedColumns('\\n'.join(x) for x in zip(*headers[:header_lines]))

    vs.recalc()
    return vs

@async
def reload_tsv(vs):
    'Asynchronous wrapper for `reload_tsv_sync`.'
    reload_tsv_sync(vs)

def reload_tsv_sync(vs):
    'Perform synchronous loading of TSV file, discarding header lines.'
    header_lines = int(options.headerlines)

    vs.rows = []
    with vs.source.open_text() as fp:
        _getTsvHeaders(fp, header_lines)  # discard header lines

        with Progress(vs, vs.source.filesize) as prog:
            while True:
                try:
                    L = next(fp)
                except StopIteration:
                    break
                L = L[:-1]
                if L:
                    vs.addRow(L.split('\t'))
                prog.addProgress(len(L))

    status('loaded %s' % vs.name)


@async
def save_tsv(vs, fn):
    'Write sheet to file `fn` as TSV.'

    # replace tabs and newlines
    replch = options.disp_oddspace
    trdict = {9: replch, 10: replch, 13: replch}

    with open(fn, 'w', encoding=options.encoding, errors=options.encoding_errors) as fp:
        colhdr = '\t'.join(col.name.translate(trdict) for col in vs.visibleCols) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)
        for r in vs.genProgress(vs.rows):
            fp.write('\t'.join(col.getDisplayValue(r).translate(trdict) for col in vs.visibleCols) + '\n')
    status('%s save finished' % fn)

