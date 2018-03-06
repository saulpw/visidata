import random

from .vdtui import *

option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
option('header', 1, 'parse first N rows of .csv/.tsv as column names')
option('delimiter', '\t', 'delimiter to use for tsv filetype')
option('filetype', '', 'specify file type')

# slide rows/columns around
globalCommand('H', 'moveVisibleCol(cursorVisibleColIndex, max(cursorVisibleColIndex-1, 0)); sheet.cursorVisibleColIndex -= 1', 'slide current column left', 'modify-move-column-left')
globalCommand('J', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, min(cursorRowIndex+1, nRows-1))', 'move current row down', 'modify-move-row-down')
globalCommand('K', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, max(cursorRowIndex-1, 0))', 'move current row up', 'modify-move-row-up')
globalCommand('L', 'moveVisibleCol(cursorVisibleColIndex, min(cursorVisibleColIndex+1, nVisibleCols-1)); sheet.cursorVisibleColIndex += 1', 'move current column right', 'modify-move-column-right')
globalCommand('gH', 'moveListItem(columns, cursorColIndex, 0)', 'slide current column all the way to the left of sheet', 'modify-move-column-leftmost')
globalCommand('gJ', 'moveListItem(rows, cursorRowIndex, nRows)', 'slide current row to the bottom of sheet', 'modify-move-row-bottom')
globalCommand('gK', 'moveListItem(rows, cursorRowIndex, 0)', 'slide current row all the way to the top of sheet', 'modify-move-row-top')
globalCommand('gL', 'moveListItem(columns, cursorColIndex, nCols)', 'slide current column all the way to the right of sheet', 'modify-move-column-rightmost')

globalCommand('c', 'searchColumnNameRegex(input("column name regex: ", type="regex-col", defaultLast=True), moveCursor=True)', 'move to the next column with name matching regex', 'view-go-column-regex')
globalCommand('r', 'moveRegex(sheet, regex=input("row key regex: ", type="regex-row", defaultLast=True), columns=keyCols or [visibleCols[0]])', 'move to the next row with key matching regex', 'view-go-row-regex')
globalCommand('zc', 'sheet.cursorVisibleColIndex = int(input("move to column number: "))', 'move to the given column number', 'view-go-column-number')
globalCommand('zr', 'sheet.cursorRowIndex = int(input("move to row number: "))', 'move to the given row number', 'view-go-row-number')

globalCommand('R', 'nrows=int(input("random number to select: ")); select(random.sample(rows, nrows))', 'open duplicate sheet with a random population subset of # rows', 'rows-select-random')

globalCommand('a', 'rows.insert(cursorRowIndex+1, newRow()); cursorDown(1)', 'append a blank row', 'modify-add-row-blank')
globalCommand('ga', 'for r in range(int(input("add rows: "))): addRow(newRow())', 'add N blank rows', 'modify-add-row-many')
globalCommand('za', 'addColumn(SettableColumn(""), cursorVisibleColIndex+1)', 'add an empty column', 'modify-add-column-blank')
globalCommand('gza', 'for c in range(int(input("add columns: "))): addColumn(SettableColumn(""), cursorVisibleColIndex+1)', 'add N empty columns', 'modify-add-column-manyblank')

globalCommand('f', 'fillNullValues(cursorCol, selectedRows or rows)', 'fills null cells in current column with contents of non-null cells up the current column', 'modify-fill-column')

alias('KEY_SLEFT', 'modify-move-column-left')
alias('kDN', 'J', 'modify-move-row-down')
alias('kUP', 'K', 'modify-move-row-up')
alias('KEY_SRIGHT', 'modify-move-column-right')

alias('gKEY_SLEFT', 'modify-move-column-leftmost')
alias('gkDN', 'gJ', 'modify-move-row-bottom')
alias('gkUP', 'gK', 'modify-move-row-top')
alias('gKEY_SRIGHT', 'modify-move-column-rightmost')


class SettableColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}

    def setValue(self, row, value):
        self.cache[id(row)] = self.type(value)

    def calcValue(self, row):
        return self.cache.get(id(row), '')


class SettableColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}

    def setValue(self, row, value):
        self.cache[id(row)] = self.type(value)

    def calcValue(self, row):
        return self.cache.get(id(row), '')

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

globalCommand('z^', 'sheet.cursorCol.name = cursorDisplay', 'set name of current column to current cell', 'column-name-cell')
globalCommand('g^', 'updateColNames(sheet)', 'set names of all visible columns to contents of selected rows (or current row)', 'column-name-all-selected')
globalCommand('gz^', 'sheet.cursorCol.name = "_".join(sheet.cursorCol.getDisplayValue(r) for r in selectedRows or [cursorRow]) ', 'set current column name to combined contents of current cell in selected rows (or current row)', 'column-name-selected')
# gz^ with no selectedRows is same as z^

globalCommand('o', 'vd.push(openSource(inputFilename("open: ")))', 'open input in VisiData', 'sheet-open-path')
globalCommand('^S', 'saveSheet(sheet, inputFilename("save to: ", value=getDefaultSaveName(sheet)), options.confirm_overwrite)', 'save current sheet to filename in format determined by extension (default .tsv)', 'sheet-save')

globalCommand('z=', 'cursorCol.setValue(cursorRow, evalexpr(inputExpr("set cell="), cursorRow))', 'set current cell to result of evaluated Python expression on current row', 'python-eval-row')

globalCommand('gz=', 'for r, v in zip(selectedRows or rows, eval(input("set column= ", "expr", completer=CompleteExpr()))): cursorCol.setValue(r, v)', 'set current column for selected rows to the items in result of Python sequence expression', 'modify-set-column-sequence')

globalCommand('A', 'vd.push(newSheet(int(input("num columns for new sheet: "))))', 'open new blank sheet with N columns', 'sheet-new')


globalCommand('gKEY_F(1)', 'info-commands')  # vdtui generic commands sheet
globalCommand('gz?', 'info-commands')  # vdtui generic commands sheet

# in VisiData, F1/z? refer to the man page
globalCommand('z?', 'openManPage()', 'launch VisiData manpage', 'info-manpage')
globalCommand('KEY_F(1)', 'z?')

def openManPage():
    from pkg_resources import resource_filename
    with SuspendCurses():
        os.system(' '.join(['man', resource_filename(__name__, 'man/vd.1')]))

def newSheet(ncols):
    return Sheet('unnamed', columns=[ColumnItem('', i, width=8) for i in range(ncols)])

def inputFilename(prompt, *args, **kwargs):
    return input(prompt, "filename", *args, completer=completeFilename, **kwargs)

def completeFilename(val, state):
    i = val.rfind('/')
    if i < 0:  # no /
        base = ''
        partial = val
    elif i == 0: # root /
        base = '/'
        partial = val[1:]
    else:
        base = val[:i]
        partial = val[i+1:]

    files = []
    for f in os.listdir(Path(base or '.').resolve()):
        if f.startswith(partial):
            files.append(os.path.join(base, f))

    files.sort()
    return files[state%len(files)]

def getDefaultSaveName(sheet):
    src = getattr(sheet, 'source', None)
    if isinstance(src, Path):
        return str(src)
    else:
        return sheet.name+'.'+getattr(sheet, 'filetype', 'tsv')

def saveSheet(vs, fn, confirm_overwrite=False):
    'Save sheet `vs` with given filename `fn`.'
    if Path(fn).exists():
        if confirm_overwrite:
            confirm('%s already exists. overwrite? ' % fn)

    basename, ext = os.path.splitext(fn)
    funcname = 'save_' + ext[1:]
    if funcname not in getGlobals():
        funcname = 'save_tsv'
    getGlobals().get(funcname)(vs, Path(fn).resolve())
    status('saving to ' + fn)


class DirSheet(Sheet):
    'Sheet displaying directory, using ENTER to open a particular file.'
    rowtype = 'files'
    commands = [
        Command(ENTER, 'vd.push(openSource(cursorRow[0]))', 'open current row', 'sheet-open-row')  # path, filename
    ]
    columns = [
        Column('filename', getter=lambda col,row: row[0].name + row[0].ext),
        Column('type', getter=lambda col,row: row[0].is_dir() and '/' or row[0].suffix),
        Column('size', type=int, getter=lambda col,row: row[1].st_size),
        Column('mtime', type=date, getter=lambda col,row: row[1].st_mtime)
    ]

    def reload(self):
        self.rows = [(p, p.stat()) for p in self.source.iterdir()]  #  if not p.name.startswith('.')]


def openSource(p, filetype=None):
    'calls open_ext(Path) or openurl_scheme(UrlPath, filetype)'
    if isinstance(p, str):
        if '://' in p:
            return openSource(UrlPath(p), filetype)  # convert to Path and recurse
        else:
            return openSource(Path(p), filetype)  # convert to Path and recurse
    elif isinstance(p, UrlPath):
        openfunc = 'openurl_' + p.scheme
        return getGlobals()[openfunc](p, filetype=filetype)
    elif isinstance(p, Path):
        if not filetype:
            filetype = options.filetype or p.suffix

        if os.path.isdir(p.resolve()):
            vs = DirSheet(p.name, source=p)
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

def open_txt(p):
    'Create sheet from `.txt` file at Path `p`, checking whether it is TSV.'
    with p.open_text() as fp:
        if options.delimiter in next(fp):    # peek at the first line
            return open_tsv(p)  # TSV often have .txt extension
        return TextSheet(p.name, p)

def _getTsvHeaders(fp, nlines):
    headers = []
    i = 0
    while i < nlines:
        L = next(fp)
        L = L.rstrip('\n')
        if L:
            headers.append(L.split(options.delimiter))
            i += 1

    return headers

def open_tsv(p, vs=None):
    'Parse contents of Path `p` and populate columns.'

    if vs is None:
        vs = TsvSheet(p.name, source=p)

    return vs

class TsvSheet(Sheet):
    @async
    def reload(self):
        header_lines = int(options.header)

        with self.source.open_text() as fp:
            headers = _getTsvHeaders(fp, header_lines or 1)  # get one data line if no headers

            if header_lines == 0:
                self.columns = ArrayColumns(len(headers[0]))
            else:
                # columns ideally reflect the max number of fields over all rows
                # but that's a lot of work for a large dataset
                self.columns = ArrayNamedColumns('\\n'.join(x) for x in zip(*headers[:header_lines]))

        self.recalc()

        reload_tsv_sync(self)

def reload_tsv_sync(vs, **kwargs):
    'Perform synchronous loading of TSV file, discarding header lines.'
    header_lines = kwargs.get('header', options.header)

    delim = options.delimiter
    vs.rows = []
    with vs.source.open_text() as fp:
        _getTsvHeaders(fp, header_lines)  # discard header lines

        with Progress(total=vs.source.filesize) as prog:
            while True:
                try:
                    L = next(fp)
                except StopIteration:
                    break
                L = L.rstrip('\n')
                if L:
                    vs.addRow(L.split(delim))
                prog.addProgress(len(L))

    status('loaded %s' % vs.name)


@async
def save_tsv(vs, fn):
    'Write sheet to file `fn` as TSV.'

    # replace tabs and newlines
    delim = options.delimiter
    replch = options.disp_oddspace
    trdict = {ord(delim): replch, 10: replch, 13: replch}

    with Path(fn).open_text(mode='w') as fp:
        colhdr = delim.join(col.name.translate(trdict) for col in vs.visibleCols) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)
        for r in Progress(vs.rows):
            fp.write(delim.join(col.getDisplayValue(r).translate(trdict) for col in vs.visibleCols) + '\n')
    status('%s save finished' % fn)

