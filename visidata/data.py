import itertools
import random

from visidata import *

option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
replayableOption('safe_error', '#ERR', 'error string to use while saving')
replayableOption('header', 1, 'parse first N rows of certain formats as column names')
replayableOption('delimiter', '\t', 'delimiter to use for tsv filetype')
replayableOption('filetype', '', 'specify file type')
replayableOption('save_filetype', 'tsv', 'specify default file type to save as')
replayableOption('tsv_safe_newline', '\u001e', 'replacement for tab character when saving to tsv')
replayableOption('tsv_safe_tab', '\u001f', 'replacement for newline character when saving to tsv')

option('color_change_pending', 'reverse yellow', 'color for file attributes pending modification')
option('color_delete_pending', 'red', 'color for files pending delete')


Sheet.addCommand('R', 'random-rows', 'nrows=int(input("random number to select: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vd.push(vs).rows=random.sample(rows, nrows or nRows)')

Sheet.addCommand('a', 'add-row', 'rows.insert(cursorRowIndex+1, newRow()); cursorDown(1)')
Sheet.addCommand('ga', 'add-rows', 'addRows(sheet, int(input("add rows: ")), cursorRowIndex+1)')
Sheet.addCommand('za', 'addcol-new', 'c=addColumn(SettableColumn("", width=options.default_width), cursorColIndex+1); draw(vd.scr); cursorVisibleColIndex=visibleCols.index(c); c.name=editCell(cursorVisibleColIndex, -1); c.width=None')
Sheet.addCommand('gza', 'addcol-bulk', 'for c in range(int(input("add columns: "))): addColumn(SettableColumn(""), cursorColIndex+1)')

Sheet.addCommand('f', 'fill-nulls', 'fillNullValues(cursorCol, selectedRows or rows)')

bindkey('KEY_SLEFT', 'slide-left')
bindkey('KEY_SR', 'slide-left')
bindkey('kDN', 'slide-down')
bindkey('kUP', 'slide-up')
bindkey('KEY_SRIGHT', 'slide-right')
bindkey('KEY_SF', 'slide-right')

bindkey('gKEY_SLEFT', 'slide-leftmost')
bindkey('gkDN', 'slide-bottom')
bindkey('gkUP', 'slide-top')
bindkey('gKEY_SRIGHT', 'slide-rightmost')


class SettableColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}

    def setValue(self, row, value):
        self.cache[id(row)] = value

    def calcValue(self, row):
        return self.cache.get(id(row), None)

Sheet._coltype = SettableColumn

@asyncthread
def addRows(sheet, n, idx):
    for i in Progress(range(n), 'adding'):
        sheet.addRow(sheet.newRow(), idx+1)

@asyncthread
def fillNullValues(col, rows):
    'Fill null cells in col with the previous non-null value'
    lastval = None
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
                col.setValue(r, lastval)
                n += 1
        else:
            lastval = val

    col.recalc()
    status("filled %d values" % n)


def updateColNames(sheet, rows, cols, overwrite=False):
    for c in cols:
        if not c._name or overwrite:
            c.name = "_".join(c.getDisplayValue(r) for r in rows)


Sheet.addCommand('^', 'rename-col', 'cursorCol.name = editCell(cursorVisibleColIndex, -1)'),
Sheet.addCommand('z^', 'rename-col-selected', 'updateColNames(sheet, selectedRows or [cursorRow], [sheet.cursorCol], overwrite=True)')
Sheet.addCommand('g^', 'rename-cols-row', 'updateColNames(sheet, selectedRows or [cursorRow], sheet.visibleCols)')
Sheet.addCommand('gz^', 'rename-cols-selected', 'updateColNames(sheet, selectedRows or [cursorRow], sheet.visibleCols, overwrite=True)')
BaseSheet.addCommand(None, 'rename-sheet', 'sheet.name = input("rename sheet to: ", value=sheet.name)')
# gz^ with no selectedRows is same as z^

globalCommand('o', 'open-file', 'vd.push(openSource(inputFilename("open: ")))')
Sheet.addCommand('^S', 'save-sheet', 'saveSheets(inputFilename("save to: ", value=getDefaultSaveName(sheet)), sheet, confirm_overwrite=options.confirm_overwrite)')
globalCommand('g^S', 'save-all', 'saveSheets(inputFilename("save all sheets to: "), *vd.sheets, confirm_overwrite=options.confirm_overwrite)')
Sheet.addCommand('z^S', 'save-col', 'vs = copy(sheet); vs.columns = [cursorCol]; vs.rows = selectedRows or rows; saveSheets(inputFilename("save to: ", value=getDefaultSaveName(vs)), vs, confirm_overwrite=options.confirm_overwrite)')

Sheet.addCommand('z=', 'show-expr', 'status(evalexpr(inputExpr("show expr="), cursorRow))')

Sheet.addCommand('gz=', 'setcol-range', 'cursorCol.setValues(selectedRows or rows, *list(itertools.islice(eval(input("set column= ", "expr", completer=CompleteExpr())), len(selectedRows or rows))))')

globalCommand('A', 'add-sheet', 'vd.push(newSheet(int(input("num columns for new sheet: "))))')

# in VisiData, ^H refers to the man page
globalCommand('^H', 'sysopen-help', 'openManPage()')
bindkey('KEY_F(1)', 'sysopen-help')
bindkey('KEY_BACKSPACE', 'sysopen-help')
bindkey('zKEY_F(1)', 'help-commands')
bindkey('zKEY_BACKSPACE', 'help-commands')

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
        return sheet.name+'.'+getattr(sheet, 'filetype', options.save_filetype)

def saveSheets(fn, *vsheets, confirm_overwrite=False):
    'Save sheet `vs` with given filename `fn`.'
    givenpath = Path(fn)

    # determine filetype to save as
    filetype = ''
    basename, ext = os.path.splitext(fn)
    if ext:
        filetype = ext[1:]

    filetype = filetype or options.save_filetype

    if len(vsheets) > 1:
        if not fn.endswith('/'):  # forcibly specify save individual files into directory by ending path with /
            savefunc = getGlobals().get('multisave_' + filetype, None)
            if savefunc:
                # use specific multisave function
                return savefunc(givenpath, *vsheets)

        # more than one sheet; either no specific multisave for save filetype, or path ends with /

        # save as individual files in the givenpath directory
        if not givenpath.exists():
            try:
                os.makedirs(givenpath.resolve(), exist_ok=True)
            except FileExistsError:
                pass

        assert givenpath.is_dir(), filetype + ' cannot save multiple sheets to non-dir'

        # get save function to call
        savefunc = getGlobals().get('save_' + filetype) or fail('no function save_'+filetype)

        if givenpath.exists():
            if confirm_overwrite:
                confirm('%s already exists. overwrite? ' % fn)

        status('saving %s sheets to %s' % (len(vsheets), givenpath.fqpn))
        for vs in vsheets:
            p = Path(os.path.join(givenpath.fqpn, vs.name+'.'+filetype))
            savefunc(p, vs)
    else:
        # get save function to call
        savefunc = getGlobals().get('save_' + filetype) or fail('no function save_'+filetype)

        if givenpath.exists():
            if confirm_overwrite:
                confirm('%s already exists. overwrite? ' % fn)

        status('saving to %s as %s' % (givenpath.fqpn, filetype))
        savefunc(givenpath, vsheets[0])


class DeferredSetColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.realsetter = self.setter
        self.setter = self.deferredSet
        self._modifiedValues = {}

    @staticmethod
    def deferredSet(col, row, val):
        if col.getValue(row) != val:
            col._modifiedValues[id(row)] = val

    def changed(self, row):
        curval = self.calcValue(row)
        newval = self._modifiedValues.get(id(row), curval)
        return self.type(newval) != self.type(curval)

    def getValue(self, row):
        if id(row) in self._modifiedValues:
            return self._modifiedValues.get(id(row))  # overrides cache
        return Column.getValue(self, row)

    def __copy__(self):
        ret = Column.__copy__(self)
        ret._modifiedValues = collections.OrderedDict()  # force a new, unrelated modified set
        return ret


def openSource(p, filetype=None):
    'calls open_ext(Path) or openurl_scheme(UrlPath, filetype)'
    if not filetype:
        filetype = options.filetype
    if isinstance(p, str):
        if '://' in p:
            return openSource(UrlPath(p), filetype)  # convert to Path and recurse
        elif p == '-':
            return openSource(PathFd('-', vd().stdin), filetype)
        else:
            return openSource(Path(p), filetype)  # convert to Path and recurse
    elif isinstance(p, UrlPath):
        openfunc = 'openurl_' + p.scheme
        return getGlobals()[openfunc](p, filetype=filetype)
    elif isinstance(p, Path):
        if not filetype:
            filetype = p.suffix or 'txt'

        if os.path.isdir(p.resolve()):
            filetype = 'dir'

        openfunc = 'open_' + filetype.lower()
        if openfunc not in getGlobals():
            warning('no %s function' % openfunc)
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

@asyncthread
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
