import random
import stat
import pwd
import grp
import subprocess
import contextlib

from visidata import *

option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
replayableOption('header', 1, 'parse first N rows of .csv/.tsv as column names')
replayableOption('delimiter', '\t', 'delimiter to use for tsv filetype')
replayableOption('filetype', '', 'specify file type')
replayableOption('save_filetype', 'tsv', 'specify default file type to save as')
replayableOption('tsv_safe_newline', '\u001e', 'replacement for tab character when saving to tsv')
replayableOption('tsv_safe_tab', '\u001f', 'replacement for newline character when saving to tsv')

option('color_change_pending', 'reverse yellow', 'color for file attributes pending modification')
option('color_delete_pending', 'red', 'color for files pending delete')


Sheet.addCommand('R', 'random-rows', 'nrows=int(input("random number to select: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vd.push(vs).rows=random.sample(rows, nrows or nRows)')

Sheet.addCommand('a', 'add-row', 'rows.insert(cursorRowIndex+1, newRow()); cursorDown(1)')
Sheet.addCommand('ga', 'add-rows', 'for r in range(int(input("add rows: "))): addRow(newRow(), cursorRowIndex+1)')
Sheet.addCommand('za', 'addcol-new', 'addColumn(SettableColumn(input("new column name: ")), cursorColIndex+1)')

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

Sheet.addCommand('z^', 'rename-col-cell', 'sheet.cursorCol.name = cursorDisplay')
Sheet.addCommand('g^', 'rename-cols-row', 'updateColNames(sheet, selectedRows or [cursorRow])')
Sheet.addCommand('gz^', 'rename-cols-selected', 'sheet.cursorCol.name = "_".join(sheet.cursorCol.getDisplayValue(r) for r in selectedRows or [cursorRow]) ')
# gz^ with no selectedRows is same as z^

globalCommand('o', 'open-file', 'vd.push(openSource(inputFilename("open: ")))')
Sheet.addCommand('^S', 'save-sheet', 'saveSheets(inputFilename("save to: ", value=getDefaultSaveName(sheet)), sheet, confirm_overwrite=options.confirm_overwrite)')
globalCommand('g^S', 'save-all', 'saveSheets(inputFilename("save all sheets to: "), *vd.sheets, confirm_overwrite=options.confirm_overwrite)')
Sheet.addCommand('z^S', 'save-col', 'vs = copy(sheet); vs.columns = [cursorCol]; vs.rows = selectedRows or rows; saveSheets(inputFilename("save to: ", value=getDefaultSaveName(vs)), vs, confirm_overwrite=options.confirm_overwrite)')

Sheet.addCommand('z=', 'show-expr', 'status(evalexpr(inputExpr("show expr="), cursorRow))')

Sheet.addCommand('gz=', 'setcol-range', 'cursorCol.setValues(selectedRows or rows, *list(eval(input("set column= ", "expr", completer=CompleteExpr()))))')

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
    rowtype = 'files' # rowdef: Path
    columns = [
        # these setters all either raise or return None, so this is a non-idiomatic 'or' to squeeze in a restat
        DeferredSetColumn('directory',
            getter=lambda col,row: row.parent.relpath(col.sheet.source.resolve()),
            setter=lambda col,row,val: col.sheet.moveFile(row, val)),
        DeferredSetColumn('filename',
            getter=lambda col,row: row.name + row.ext,
            setter=lambda col,row,val: col.sheet.renameFile(row, val)),
        Column('ext', getter=lambda col,row: row.is_dir() and '/' or row.suffix),
        DeferredSetColumn('size', type=int,
            getter=lambda col,row: row.stat().st_size,
            setter=lambda col,row,val: os.truncate(row.resolve(), int(val))),
        DeferredSetColumn('modtime', type=date,
            getter=lambda col,row: row.stat().st_mtime,
            setter=lambda col,row,val: os.utime(row.resolve(), times=((row.stat().st_atime, float(val))))),
        DeferredSetColumn('owner', width=0,
            getter=lambda col,row: pwd.getpwuid(row.stat().st_uid).pw_name,
            setter=lambda col,row,val: os.chown(row.resolve(), pwd.getpwnam(val).pw_uid, -1)),
        DeferredSetColumn('group', width=0,
            getter=lambda col,row: grp.getgrgid(row.stat().st_gid).gr_name,
            setter=lambda col,row,val: os.chown(row.resolve(), -1, grp.getgrnam(val).pw_gid)),
        DeferredSetColumn('mode', width=0, type=int, fmtstr='{:o}',
            getter=lambda col,row: row.stat().st_mode,
            setter=lambda col,row,val: os.chmod(row.resolve(), val),
            ),
        Column('filetype', width=0, cache=True, getter=lambda col,row: subprocess.Popen(['file', '--brief', row.resolve()], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip()),
    ]
    colorizers = [
#        Colorizer('cell', 4, lambda s,c,r,v: s.colorOwner(s,c,r,v)),
        Colorizer('cell', 8, lambda s,c,r,v: options.color_change_pending if s.changed(c, r) else None),
        Colorizer('row', 9, lambda s,c,r,v: options.color_delete_pending if r in s.toBeDeleted else None),
    ]
    nKeys = 2

    @staticmethod
    def colorOwner(sheet, col, row, val):
        ret = ''
        if col.name == 'group':
            mode = row.stat().st_mode
            if mode & stat.S_IXGRP: ret = 'bold '
            if mode & stat.S_IWGRP: return ret + 'green'
            if mode & stat.S_IRGRP: return ret + 'yellow'
        elif col.name == 'owner':
            mode = row.stat().st_mode
            if mode & stat.S_IXUSR: ret = 'bold '
            if mode & stat.S_IWUSR: return ret + 'green'
            if mode & stat.S_IRUSR: return ret + 'yellow'

    def changed(self, col, row):
        try:
            return isinstance(col, DeferredSetColumn) and col.changed(row)
        except Exception:
            return False

    def deleteFiles(self, rows):
        for r in rows:
            if r not in self.toBeDeleted:
                self.toBeDeleted.append(r)

    def moveFile(self, row, val):
        fn = row.name + row.ext
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

        os.rename(row.resolve(), newpath)
        row.fqpn = newpath
        self.restat(row)

    def renameFile(self, row, val):
        newpath = row.with_name(val)
        os.rename(row.resolve(), newpath.resolve())
        row.fqpn = newpath
        self.restat(row)

    def removeFile(self, path):
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
            fail('nothing to save')

        cstr = ''
        if changes:
            cstr += 'change %d attributes' % len(changes)

        if deletes:
            if cstr: cstr += ' and '
            cstr += 'delete %d files' % len(deletes)

        confirm('really %s? ' % cstr)

        self._commit(changes, deletes)

    @asyncthread
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

    @asyncthread
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
                self.rows.append(p)

        # sort by modtime initially
        self.rows.sort(key=lambda row: row.stat().st_mtime, reverse=True)

    def restat(self, row):
        row.stat(force=True)

DirSheet.addCommand(ENTER, 'open-row', 'vd.push(openSource(cursorRow))')
DirSheet.addCommand('g'+ENTER, 'open-rows', 'for r in selectedRows: vd.push(openSource(r.resolve()))')
DirSheet.addCommand('^O', 'sysopen-row', 'launchEditor(cursorRow.resolve())')
DirSheet.addCommand('g^O', 'sysopen-rows', 'launchEditor(*(r.resolve() for r in selectedRows))')
DirSheet.addCommand('^S', 'save-sheet', 'save()')
DirSheet.addCommand('z^S', 'save-row', 'save(cursorRow)')
DirSheet.addCommand('z^R', 'reload-row', 'undoMod(cursorRow); restat(cursorRow)')
DirSheet.addCommand(None, 'delete-row', 'if cursorRow not in toBeDeleted: toBeDeleted.append(cursorRow); cursorRowIndex += 1')
DirSheet.addCommand(None, 'delete-selected', 'deleteFiles(selectedRows)')

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
            filetype = options.filetype or p.suffix or 'txt'

        if os.path.isdir(p.resolve()):
            vs = DirSheet(p.name, source=p)
            filetype = 'dir'
        else:
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
            col = vs.visibleCols[0]
            for r in Progress(vs.rows):
                fp.write(col.getValue(r))
                fp.write('\n')
    status('%s save finished' % p)

multisave_txt = save_txt


def loadInternalSheet(klass, p, **kwargs):
    'Load internal sheet of given klass.  Internal sheets are always tsv.'
    vs = klass(p.name, source=p, **kwargs)
    if p.exists():
        vs.reload.__wrapped__(vs)
    return vs
