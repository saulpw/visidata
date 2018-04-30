import random
import stat
import pwd
import grp
import subprocess
import contextlib

from .vdtui import *

option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
replayableOption('header', 1, 'parse first N rows of .csv/.tsv as column names')
replayableOption('delimiter', '\t', 'delimiter to use for tsv filetype')
replayableOption('filetype', '', 'specify file type')
replayableOption('save_filetype', 'tsv', 'specify default file type to save as')
replayableOption('tsv_safe_char', '\u00b7', 'replacement for all tabs and newlines when saving to tsv')

option('color_change_pending', 'reverse yellow', 'color for file attributes pending modification')
option('color_delete_pending', 'red', 'color for files pending delete')

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
alias('KEY_SR', 'modify-move-column-left')
alias('kDN', 'modify-move-row-down')
alias('kUP', 'modify-move-row-up')
alias('KEY_SRIGHT', 'modify-move-column-right')
alias('KEY_SF', 'modify-move-column-right')

alias('gKEY_SLEFT', 'modify-move-column-leftmost')
alias('gkDN', 'modify-move-row-bottom')
alias('gkUP', 'modify-move-row-top')
alias('gKEY_SRIGHT', 'modify-move-column-rightmost')


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
        try:
            val = col.getValue(r)
        except Exception as e:
            val = e

        if nullfunc(val):
            if lastval:
                col.setValue(r, lastval)
                n += 1
        else:
            lastval = val

    status("filled %d values" % n)


def updateColNames(sheet, rows):
    for c in sheet.visibleCols:
        if not c._name:
            c.name = "_".join(c.getDisplayValue(r) for r in rows)

globalCommand('z^', 'sheet.cursorCol.name = cursorDisplay', 'set name of current column to current cell', 'column-name-cell')
globalCommand('g^', 'updateColNames(sheet, selectedRows or [cursorRow])', 'set names of all visible columns to contents of selected rows (or current row)', 'column-name-all-selected')
globalCommand('gz^', 'sheet.cursorCol.name = "_".join(sheet.cursorCol.getDisplayValue(r) for r in selectedRows or [cursorRow]) ', 'set current column name to combined contents of current cell in selected rows (or current row)', 'column-name-selected')
# gz^ with no selectedRows is same as z^

globalCommand('o', 'vd.push(openSource(inputFilename("open: ")))', 'open input in VisiData', 'sheet-open-path')
globalCommand('^S', 'saveSheets(inputFilename("save to: ", value=getDefaultSaveName(sheet)), sheet, confirm_overwrite=options.confirm_overwrite)', 'save current sheet to filename in format determined by extension (default .tsv)', 'sheet-save')
globalCommand('g^S', 'saveSheets(inputFilename("save all sheets to: "), *vd.sheets, confirm_overwrite=options.confirm_overwrite)', 'save all sheets to given file or directory)', 'sheet-save-all')
globalCommand('z^S', 'vs = copy(sheet); vs.columns = [cursorCol]; vs.rows = selectedRows or rows; saveSheets(inputFilename("save to: ", value=getDefaultSaveName(vs)), vs, confirm_overwrite=options.confirm_overwrite)', 'save current column to filename in format determined by extension', 'sheet-save-column')

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
        return sheet.name+'.'+getattr(sheet, 'filetype', options.save_filetype)

def saveSheets(fn, *vsheets, confirm_overwrite=False):
    'Save sheet `vs` with given filename `fn`.'
    givenpath = Path(fn)
    if givenpath.exists():
        if confirm_overwrite:
            confirm('%s already exists. overwrite? ' % fn)

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
                os.mkdir(givenpath.resolve())
            except FileExistsError:
                pass

        assert givenpath.is_dir(), filetype + ' cannot save multiple sheets to non-dir'

        # get save function to call
        if ('save_' + filetype) not in getGlobals():
            filetype = options.save_filetype
        savefunc = getGlobals().get('save_' + filetype)

        status('saving %s sheets to %s' % (len(vsheets), givenpath.fqpn))
        for vs in vsheets:
            p = Path(os.path.join(givenpath.fqpn, vs.name+'.'+filetype))
            savefunc(p, vs)
    else:
        # get save function to call
        if ('save_' + filetype) not in getGlobals():
            filetype = options.save_filetype
        savefunc = getGlobals().get('save_' + filetype)

        status('saving to ' + givenpath.fqpn)
        savefunc(givenpath, vsheets[0])


class DeferredSetColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, cache=True, **kwargs)
        self.realsetter = self.setter
        self.setter = self.deferredSet

    @staticmethod
    def deferredSet(col, row, val):
        col._cachedValues[id(row)] = val

    def changed(self, row):
        curval = self.calcValue(row)
        newval = self._cachedValues.get(id(row), curval)
        return self.type(newval) != self.type(curval)

class DirSheet(Sheet):
    'Sheet displaying directory, using ENTER to open a particular file.  Edited fields are applied to the filesystem.'
    rowtype = 'files' # rowdef: (Path, stat)
    commands = [
        Command(ENTER, 'vd.push(openSource(cursorRow[0]))', 'open current file as a new sheet', 'sheet-open-row'),
        Command('g'+ENTER, 'for r in selectedRows: vd.push(openSource(r[0].resolve()))', 'open selected files as new sheets', 'sheet-open-rows'),
        Command('^O', 'launchEditor(cursorRow[0].resolve())', 'open current file in external $EDITOR', 'edit-row-external'),
        Command('g^O', 'launchEditor(*(r[0].resolve() for r in selectedRows))', 'open selected files in external $EDITOR', 'edit-rows-external'),
        Command('^S', 'save()', 'apply all changes on all rows', 'sheet-specific-apply-edits'),
        Command('z^S', 'save(cursorRow)', 'apply changes to current row', 'sheet-specific-apply-edits'),
        Command('z^R', 'undoMod(cursorRow); restat(cursorRow)', 'undo pending changes to current row', 'sheet-specific-apply-edits'),
        Command('modify-delete-row', 'if cursorRow not in toBeDeleted: toBeDeleted.append(cursorRow); cursorRowIndex += 1'),
        Command('modify-delete-selected', 'deleteFiles(selectedRows)')
    ]
    columns = [
        # these setters all either raise or return None, so this is a non-idiomatic 'or' to squeeze in a restat
        DeferredSetColumn('directory',
            getter=lambda col,row: row[0].parent.relpath(col.sheet.source.resolve()),
            setter=lambda col,row,val: col.sheet.moveFile(row, val)),
        DeferredSetColumn('filename',
            getter=lambda col,row: row[0].name + row[0].ext,
            setter=lambda col,row,val: col.sheet.renameFile(row, val)),
        Column('ext', getter=lambda col,row: row[0].is_dir() and '/' or row[0].suffix),
        DeferredSetColumn('size', type=int,
            getter=lambda col,row: row[1].st_size,
            setter=lambda col,row,val: os.truncate(row[0].resolve(), int(val))),
        DeferredSetColumn('modtime', type=date,
            getter=lambda col,row: row[1].st_mtime,
            setter=lambda col,row,val: os.utime(row[0].resolve(), times=((row[1].st_atime, float(val))))),
        DeferredSetColumn('owner', width=0,
            getter=lambda col,row: pwd.getpwuid(row[1].st_uid).pw_name,
            setter=lambda col,row,val: os.chown(row[0].resolve(), pwd.getpwnam(val).pw_uid, -1)),
        DeferredSetColumn('group', width=0,
            getter=lambda col,row: grp.getgrgid(row[1].st_gid).gr_name,
            setter=lambda col,row,val: os.chown(row[0].resolve(), -1, grp.getgrnam(val).pw_gid)),
        DeferredSetColumn('mode', width=0, type=int, fmtstr='{:o}', getter=lambda col,row: row[1].st_mode),
        Column('filetype', width=40, cache=True, getter=lambda col,row: subprocess.Popen(['file', '--brief', row[0].resolve()], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip()),
    ]
    colorizers = [
        Colorizer('cell', 4, lambda s,c,r,v: s.colorOwner(s,c,r,v)),
        Colorizer('cell', 8, lambda s,c,r,v: options.color_change_pending if s.changed(c, r) else None),
        Colorizer('row', 9, lambda s,c,r,v: options.color_delete_pending if r in s.toBeDeleted else None),
    ]
    nKeys = 2

    @staticmethod
    def colorOwner(sheet, col, row, val):
        path, st = row
        mode = st.st_mode
        ret = ''
        if col.name == 'group':
            if mode & stat.S_IXGRP: ret = 'bold '
            if mode & stat.S_IWGRP: return ret + 'green'
            if mode & stat.S_IRGRP: return ret + 'yellow'
        elif col.name == 'owner':
            if mode & stat.S_IXUSR: ret = 'bold '
            if mode & stat.S_IWUSR: return ret + 'green'
            if mode & stat.S_IRUSR: return ret + 'yellow'

    def changed(self, col, row):
        return isinstance(col, DeferredSetColumn) and col.changed(row)

    def deleteFiles(self, rows):
        for r in rows:
            if r not in self.toBeDeleted:
                self.toBeDeleted.append(r)

    def moveFile(self, row, val):
        fn = row[0].name + row[0].ext
        newpath = os.path.join(val, fn)
        if not newpath.startswith('/'):
            newpath = os.path.join(self.source.resolve(), newpath)

        parent = Path(newpath).parent
        if parent.exists():
            if not parent.is_dir():
                error('destination %s not a directory' % parent)
        else:
            with contextlib.suppress(FileExistsError):
                os.makedirs(parent.resolve())

        os.rename(row[0].resolve(), newpath)
        row[0] = Path(newpath)
        self.restat(row)

    def renameFile(self, row, val):
        newpath = row[0].with_name(val)
        os.rename(row[0].resolve(), newpath.resolve())
        row[0] = newpath

    def removeFile(self, row):
        path, _ = row
        if path.is_dir():
            os.rmdir(path.resolve())
        else:
            os.remove(path.resolve())

    def undoMod(self, row):
        for col in self.visibleCols:
            if col._cachedValues and id(row) in col._cachedValues:
                del col._cachedValues[id(row)]

        if row in self.toBeDeleted:
            self.toBeDeleted.remove(row)

    def save(self, *rows):
        changes = []
        deletes = {}
        for r in list(rows or self.rows):  # copy list because elements may be removed
            if r in self.toBeDeleted:
                deletes[id(r)] = r
            else:
                for col in self.visibleCols:
                    if self.changed(col, r):
                        changes.append((col, r))

        if not changes and not deletes:
            error('nothing to save')

        cstr = ''
        if changes:
            cstr += 'change %d attributes' % len(changes)

        if deletes:
            if cstr: cstr += ' and '
            cstr += 'delete %d files' % len(deletes)

        confirm('really %s? ' % cstr)

        self._commit(changes, deletes)

    @async
    def _commit(self, changes, deletes):
        oldrows = self.rows
        self.rows = []
        for r in oldrows:
            try:
                if id(r) in deletes:
                    self.removeFile(r)
                else:
                    self.rows.append(r)
            except Exception as e:
                exceptionCaught(e)

        for col, row in changes:
            try:
                col.realsetter(col, row, col._cachedValues[id(row)])
                self.restat(r)
            except Exception as e:
                exceptionCaught(e)

    @async
    def reload(self):
        self.toBeDeleted = []
        self.rows = []
        basepath = self.source.resolve()
        for folder, subdirs, files in os.walk(basepath):
            subfolder = folder[len(basepath)+1:]
            if subfolder.startswith('.'): continue
            for fn in files:
                if fn.startswith('.'): continue
                p = Path(os.path.join(folder, fn))
                self.rows.append([p, p.stat()])
        self.rows.sort()

    def restat(self, row):
        row[1] = row[0].stat()


def openSource(p, filetype=None):
    'calls open_ext(Path) or openurl_scheme(UrlPath, filetype)'
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

@async
def save_txt(p, *vsheets):
    with p.open_text(mode='w') as fp:
        for vs in vsheets:
            col = vs.visibleCols[0]
            for r in Progress(vs.rows):
                fp.write(col.getValue(r))
                fp.write('\n')
    status('%s save finished' % p)

multisave_txt = save_txt

def _getTsvHeaders(fp, nlines):
    headers = []
    i = 0
    while i < nlines:
        try:
            L = next(fp)
        except StopIteration:  # not enough lines for headers
            return headers
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


def tsv_trdict(delim=None):
    # replace tabs and newlines
    delim = delim or options.delimiter
    replch = options.tsv_safe_char
    return {ord(delim): replch, 10: replch, 13: replch}


def save_tsv_header(p, vs):
    'Write tsv header for Sheet `vs` to Path `p`.'
    trdict = tsv_trdict()
    delim = options.delimiter

    with p.open_text(mode='w') as fp:
        colhdr = delim.join(col.name.translate(trdict) for col in vs.visibleCols) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)


@async
def save_tsv(p, vs):
    'Write sheet to file `fn` as TSV.'
    delim = options.delimiter
    trdict = tsv_trdict()

    save_tsv_header(p, vs)

    with p.open_text(mode='a') as fp:
        if trdict:
            for r in Progress(vs.rows):
                fp.write(delim.join(col.getDisplayValue(r).translate(trdict) for col in vs.visibleCols) + '\n')
        else:
            for r in Progress(vs.rows):
                fp.write(delim.join(col.getDisplayValue(r) for col in vs.visibleCols) + '\n')

    status('%s save finished' % p)


def append_tsv_row(vs, row):
    'Append `row` to vs.source, creating file with correct headers if necessary. For internal use only.'
    if not vs.source.exists():
        with contextlib.suppress(FileExistsError):
            parentdir = vs.source.parent.resolve()
            if parentdir:
                os.makedirs(parentdir)

        save_tsv_header(vs.source, vs)

    trdict = tsv_trdict(delim='\t')

    with vs.source.open_text(mode='a') as fp:
        fp.write('\t'.join(col.getDisplayValue(row) for col in vs.visibleCols) + '\n')


def loadInternalSheet(klass, p, **kwargs):
    'Load internal sheet of given klass.  Internal sheets are always tsv.'
    vs = klass(p.name, source=p, **kwargs)
    if p.exists():
        vs.reload.__wrapped__(vs)
    return vs
