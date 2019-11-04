import itertools
import random

from copy import copy
from visidata import Sheet, Column, asyncthread, Progress, status, error
from visidata import *


option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
option('safe_error', '#ERR', 'error string to use while saving', replay=True)
option('header', 1, 'parse first N rows of certain formats as column names', replay=True)
option('filetype', '', 'specify file type', replay=True)


Sheet.addCommand(None, 'random-rows', 'nrows=int(input("random number to select: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vs.rows=random.sample(rows, nrows or nRows); vd.push(vs)')

Sheet.addCommand('a', 'add-row', 'addRows(1, cursorRowIndex); cursorDown(1)')
Sheet.addCommand('ga', 'add-rows', 'addRows(int(input("add rows: ", value=1)), cursorRowIndex)')
Sheet.addCommand('za', 'addcol-new', 'addColumn(SettableColumn(""), cursorColIndex+1)')
Sheet.addCommand('gza', 'addcol-bulk', 'for c in range(int(input("add columns: "))): addColumn(SettableColumn(""), cursorColIndex+1)')

Sheet.addCommand('f', 'fill-nulls', 'fillNullValues(cursorCol, selectedRows)')

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

@asyncthread
@Sheet.api
def addRows(sheet, n, idx):
    addedRows = {}
    for i in Progress(range(n), 'adding'):
        row = sheet.newRow()
        addedRows[sheet.rowid(row)] = row
        sheet.addRow(row, idx+1)

    @asyncthread
    def _removeRows():
        sheet.deleteBy(lambda r,sheet=sheet,addedRows=addedRows: sheet.rowid(r) in addedRows)

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
    for c in cols:
        if not c._name or overwrite:
            c.name = "\n".join(c.getDisplayValue(r) for r in rows)

Sheet.addCommand('^', 'rename-col', 'cursorCol.name = editCell(cursorVisibleColIndex, -1)')
Sheet.addCommand('z^', 'rename-col-selected', 'updateColNames(sheet, selectedRows or [cursorRow], [sheet.cursorCol], overwrite=True)')
Sheet.addCommand('g^', 'rename-cols-row', 'updateColNames(sheet, selectedRows or [cursorRow], sheet.visibleCols)')
Sheet.addCommand('gz^', 'rename-cols-selected', 'updateColNames(sheet, selectedRows or [cursorRow], sheet.visibleCols, overwrite=True)')
BaseSheet.addCommand(None, 'rename-sheet', 'sheet.name = input("rename sheet to: ", value=sheet.name)')

globalCommand('o', 'open-file', 'vd.push(openSource(inputFilename("open: ")))')
Sheet.addCommand('^S', 'save-sheet', 'saveSheets(inputPath("save to: ", value=getDefaultSaveName(sheet)), sheet, confirm_overwrite=options.confirm_overwrite)')
globalCommand('g^S', 'save-all', 'saveSheets(inputPath("save all sheets to: "), *vd.sheets, confirm_overwrite=options.confirm_overwrite)')
Sheet.addCommand('z^S', 'save-col', 'vs = copy(sheet); vs.columns = [cursorCol]; vs.rows = copy(rows); saveSheets(inputPath("save to: ", value=getDefaultSaveName(vs)), vs.confirm_overwrite=options.confirm_overwrite)')

Sheet.addCommand(None, 'show-expr', 'status(evalexpr(inputExpr("show expr="), cursorRow))')

Sheet.addCommand('gz=', 'setcol-range', 'cursorCol.setValues(selectedRows, *list(itertools.islice(eval(input("set column= ", "expr", completer=CompleteExpr())), len(selectedRows))))')

globalCommand('A', 'add-sheet', 'vd.push(vd.newSheet(int(input("num columns for new sheet: ")), name="unnamed"))')

# in VisiData, ^H refers to the man page
globalCommand('^H', 'sysopen-help', 'openManPage()')
BaseSheet.bindkey('KEY_F(1)', 'sysopen-help')
BaseSheet.bindkey('KEY_BACKSPACE', 'sysopen-help')
BaseSheet.bindkey('zKEY_F(1)', 'help-commands')
BaseSheet.bindkey('zKEY_BACKSPACE', 'help-commands')

def openManPage():
    from pkg_resources import resource_filename
    with SuspendCurses():
        os.system(' '.join(['man', resource_filename(__name__, 'man/vd.1')]))

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

def getDefaultSaveName(sheet):
    src = getattr(sheet, 'source', None)
    if isinstance(src, Path):
        return str(src)
    else:
        return sheet.name+'.'+getattr(sheet, 'filetype', options.save_filetype)

@VisiData.global_api
def saveSheets(vd, givenpath, *vsheets, confirm_overwrite=False):
    'Save all vsheets to givenpath'

    filetype = givenpath.ext or options.save_filetype

    if len(vsheets) > 1:
        if givenpath.exists() and confirm_overwrite:
            confirm("overwrite multiple? ")

        if not givenpath.given.endswith('/'):  # forcibly specify save individual files into directory by ending path with /
            savefunc = getGlobals().get('multisave_' + filetype, None)
            if savefunc:
                # use specific multisave function
                vd.execAsync(savefunc, givenpath, *vsheets)

        # more than one sheet; either no specific multisave for save filetype, or path ends with /

        # save as individual files in the givenpath directory
        try:
            os.makedirs(givenpath, exist_ok=True)
        except FileExistsError:
            pass

        assert givenpath.is_dir(), filetype + ' cannot save multiple sheets to non-dir'

        globalsavefunc = getGlobals().get('save_' + filetype)

        # get save function to call
        status('saving %s sheets to %s' % (len(vsheets), givenpath.given))
        for vs in vsheets:
            savefunc = getattr(vs, 'save_'+filetype, None)
            if not savefunc:
                savefunc = lambda p,vs=vs,f=globalsavefunc: f(p, vs)
            if savefunc:
                vd.execAsync(savefunc, givenpath.with_suffix('.'+filetype))
            else:
                warning('no function to save %s as type %s' % (vs, filetype))
    else:
        if givenpath.exists() and confirm_overwrite:
            confirm("%s already exists. overwrite? " % givenpath.given)

        # get save function to call
        savefunc = getattr(vsheets[0], 'save_'+filetype, None)
        if not savefunc:
            f = getGlobals().get('save_' + filetype) or fail('no function save_'+filetype)
            savefunc = lambda p,vs=vsheets[0],f=f: f(p, vs)

        status('saving to %s as %s' % (givenpath.given, filetype))
        vd.execAsync(savefunc, givenpath)


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
        return TextSheet(p.name, source=p)

def save_txt(p, *vsheets):
    with p.open_text(mode='w') as fp:
        for vs in vsheets:
            col = [vs.visibleCols[0]]
            for dispvals in genAllValues(vs.rows, [vs.visibleCols[0]]):
                fp.write(dispvals[0] or '')
                fp.write('\n')
    status('%s save finished' % p)

multisave_txt = save_txt


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
def deleteBy(self, func):
    'Delete rows for which func(row) is true.  Returns number of deleted rows.'
    oldrows = copy(self.rows)
    oldidx = self.cursorRowIndex
    ndeleted = 0

    row = None   # row to re-place cursor after
    while oldidx < len(oldrows):
        if not func(oldrows[oldidx]):
            row = self.rows[oldidx]
            break
        oldidx += 1

    self.rows.clear()
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
