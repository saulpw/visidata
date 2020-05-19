import itertools
import random

from copy import copy
from visidata import Sheet, Column, asyncthread, Progress, status, error
from visidata import *


option('filetype', '', 'specify file type', replay=True)


vd.filetypes = {}


class SettableColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}

    def putValue(self, row, value):
        self.cache[self.sheet.rowid(row)] = value

    def calcValue(self, row):
        return self.cache.get(self.sheet.rowid(row), None)

Sheet._coltype = SettableColumn

@Sheet.api
@asyncthread
def addNewRows(sheet, n, idx):
    addedRows = {}
    for i in Progress(range(n), 'adding'):
        row = sheet.newRow()
        addedRows[sheet.rowid(row)] = row
        sheet.addRow(row, idx+1)

        if sheet.defer:
            sheet.rowAdded(row)

    @asyncthread
    def _removeRows():
        sheet.deleteBy(lambda r,sheet=sheet,addedRows=addedRows: sheet.rowid(r) in addedRows, commit=True)

    vd.addUndo(_removeRows)


@asyncthread
def fillNullValues(col, rows):
    'Fill null cells in col with the previous non-null value'
    lastval = None
    oldvals = [] # for undo
    nullfunc = isNullFunc()
    n = 0
    rowsToFill = list(rows)
    for r in Progress(col.sheet.rows, 'filling'):  # loop over all rows
        try:
            val = col.getValue(r)
        except Exception as e:
            val = e

        if nullfunc(val) and r in rowsToFill:
            if lastval:
                oldvals.append((col,r,val))
                col.setValue(r, lastval)
                n += 1
        else:
            lastval = val

    def _undo():
        for c, r, v in oldvals:
            c.setValue(r, v)
    vd.addUndo(_undo)

    col.recalc()
    status("filled %d values" % n)


def updateColNames(sheet, rows, cols, overwrite=False):
    vd.addUndoColNames(cols)
    for c in cols:
        if not c._name or overwrite:
            c.name = "\n".join(c.getDisplayValue(r) for r in rows)


@VisiData.api
def newSheet(vd, ncols, name='', **kwargs):
    return Sheet(name, columns=[ColumnItem('', i, width=8) for i in range(ncols)], **kwargs)

def inputFilename(prompt, *args, **kwargs):
    return vd.input(prompt, "filename", *args, completer=completeFilename, **kwargs)

def inputPath(*args, **kwargs):
    return Path(inputFilename(*args, **kwargs))

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
    for f in os.listdir(Path(base or '.')):
        if f.startswith(partial):
            files.append(os.path.join(base, f))

    files.sort()
    return files[state%len(files)]

@VisiData.api
def filetype(vd, ext, constructor):
    'Add constructor to handle the given file type/extension.'
    vd.filetypes[ext] = constructor


@VisiData.api
def openPath(vd, p, filetype=None):
    'Call vd.filetypes[ext](path.name, source=path) or open_ext(Path) or openurl_scheme(Path, filetype).  Return constructed but unloaded sheet of appropriate type.'
    if p.scheme and not p.fp: # isinstance(p, UrlPath):
        openfunc = 'openurl_' + p.scheme
        return getGlobals()[openfunc](p, filetype=filetype)

    if p.is_dir():
        filetype = 'dir'

    if not filetype:
        filetype = p.ext or 'txt'

    if not p.exists():
        warning('%s does not exist, creating new sheet' % p)
        return vd.newSheet(1, name=p.name, source=p)

    filetype = filetype.lower()

    openfunc = vd.filetypes.get(filetype.lower())
    if openfunc:
        return openfunc(p.name, source=p)

    openfunc = getGlobals().get('open_' + filetype)
    if not openfunc:
        warning('unknown "%s" filetype' % filetype)
        filetype = 'txt'
        openfunc = getGlobals().get('open_txt')

    vd.status('opening %s as %s' % (p.given, filetype))
    return openfunc(p)


@VisiData.global_api
def openSource(vd, p, filetype=None):
    if not filetype:
        filetype = options.filetype

    if isinstance(p, str):
        if '://' in p:
            return vd.openPath(Path(p), filetype=filetype)  # convert to Path and recurse
        elif p == '-':
            return vd.openPath(Path('-', fp=vd._stdin), filetype=filetype)
        else:
            return vd.openPath(Path(p), filetype=filetype)  # convert to Path and recurse

    vs = vd.openPath(p, filetype=filetype)
    return vs


#### enable external addons
def open_txt(p):
    'Create sheet from `.txt` file at Path `p`, checking whether it is TSV.'
    with p.open_text() as fp:
        if options.delimiter in next(fp):    # peek at the first line
            return open_tsv(p)  # TSV often have .txt extension
        return TextSheet(p.name, source=p)

def loadInternalSheet(klass, p, **kwargs):
    'Load internal sheet of given klass.  Internal sheets are always tsv.'
    vs = klass(p.name, source=p, **kwargs)
    options._set('encoding', 'utf8', vs)
    if p.exists():
        vd.sheets.insert(0, vs)
        vs.reload.__wrapped__(vs)
        vd.sheets.pop(0)
    return vs

@Sheet.api
def deleteBy(self, func, commit=False):
    'Delete rows for which func(row) is true.  Returns number of deleted rows.'
    oldrows = copy(self.rows)
    oldidx = self.cursorRowIndex
    ndeleted = 0

    row = None   # row to re-place cursor after
    # if commit is True, commit to delete, even if defer is True
    if self.defer and not commit:
        ndeleted = 0
        for r in self.gatherBy(func, 'deleting'):
            self.rowDeleted(r)
            ndeleted += 1
        return ndeleted

    while oldidx < len(oldrows):
        if not func(oldrows[oldidx]):
            row = self.rows[oldidx]
            break
        oldidx += 1

    self.rows.clear() # must delete from the existing rows object
    for r in Progress(oldrows, 'deleting'):
        if not func(r):
            self.rows.append(r)
            if r is row:
                self.cursorRowIndex = len(self.rows)-1
        else:
            ndeleted += 1

    vd.addUndo(setattr, self, 'rows', oldrows)

    status('deleted %s %s' % (ndeleted, self.rowtype))

    return ndeleted


IndexSheet.options.header = 0
IndexSheet.options.skip = 0

Sheet.addCommand(None, 'random-rows', 'nrows=int(input("random number to select: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vs.rows=random.sample(rows, nrows or nRows); vd.push(vs)', 'open duplicate sheet with a random population subset of N rows')

Sheet.addCommand('a', 'add-row', 'addNewRows(1, cursorRowIndex); cursorDown(1)', 'append a blank row')
Sheet.addCommand('ga', 'add-rows', 'addNewRows(int(input("add rows: ", value=1)), cursorRowIndex)', 'append N blank rows')
Sheet.addCommand('za', 'addcol-new', 'addColumn(SettableColumn(""), cursorColIndex+1)', 'append an empty column')
Sheet.addCommand('gza', 'addcol-bulk', 'for c in range(int(input("add columns: "))): addColumn(SettableColumn(""), cursorColIndex+1)', 'append N empty columns')

Sheet.addCommand('f', 'setcol-fill', 'fillNullValues(cursorCol, selectedRows)', 'fills null cells in selected rows of current column with contents of non-null cells up the current column')

BaseSheet.bindkey('KEY_SLEFT', 'slide-left')
BaseSheet.bindkey('KEY_SR', 'slide-left')
BaseSheet.bindkey('kDN', 'slide-down')
BaseSheet.bindkey('kUP', 'slide-up')
BaseSheet.bindkey('KEY_SRIGHT', 'slide-right')
BaseSheet.bindkey('KEY_SF', 'slide-right')

BaseSheet.bindkey('gKEY_SLEFT', 'slide-leftmost')
BaseSheet.bindkey('gkDN', 'slide-bottom')
BaseSheet.bindkey('gkUP', 'slide-top')
BaseSheet.bindkey('gKEY_SRIGHT', 'slide-rightmost')

Sheet.addCommand('^', 'rename-col', 'vd.addUndoColNames([cursorCol]); cursorCol.name = editCell(cursorVisibleColIndex, -1)', 'edit name of current column')
Sheet.addCommand('z^', 'rename-col-selected', 'updateColNames(sheet, selectedRows or [cursorRow], [sheet.cursorCol], overwrite=True)', 'set name of current column to combined contents of current cell in selected rows (or current row)')
Sheet.addCommand('g^', 'rename-cols-row', 'updateColNames(sheet, selectedRows or [cursorRow], sheet.visibleCols)', 'set names of all unnamed visible columns to contents of selected rows (or current row)')
Sheet.addCommand('gz^', 'rename-cols-selected', 'updateColNames(sheet, selectedRows or [cursorRow], sheet.visibleCols, overwrite=True)', 'set names of all visible columns to combined contents of selected rows (or current row)')
BaseSheet.addCommand(None, 'rename-sheet', 'sheet.name = input("rename sheet to: ", value=sheet.name)', 'rename current sheet to input')

globalCommand('o', 'open-file', 'vd.push(openSource(inputFilename("open: ")))', 'open input in VisiData')
Sheet.addCommand(None, 'show-expr', 'status(evalexpr(inputExpr("show expr="), cursorRow))', 'evaluate Python expression on current row and show result on status line')

Sheet.addCommand('gz=', 'setcol-range', 'cursorCol.setValues(selectedRows, *list(itertools.islice(eval(input("set column= ", "expr", completer=CompleteExpr())), len(selectedRows))))', 'set current column for selected rows to the items in result of Python sequence expression')

globalCommand('A', 'add-sheet', 'vd.push(vd.newSheet(int(input("num columns for new sheet: ")), name="unnamed"))', 'open new blank sheet with N columns')
