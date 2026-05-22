import os
import re
import shlex
import shutil
import stat
import subprocess
import contextlib
try:
    import pwd
    import grp
except ImportError:
    pass # pwd,grp modules not available on Windows

from visidata import Column, Sheet, LazyComputeRow, asynccache, BaseSheet, vd
from visidata import Path, asyncthread, VisiData
from visidata import modtime, filesize, vstat, Progress, TextSheet
from visidata.type_date import date


vd.option('dir_depth', 0, 'folder recursion depth on DirSheet')
vd.option('dir_hidden', False, 'load hidden files on DirSheet')
vd.option('active_procs', 10, 'number of concurrent processes on DirSheet')

vd.spawnedProcesses = []

def bytes_rstrip(*args, **kwargs): #3081
    return bytes.rstrip(*args, **kwargs)


@VisiData.api
def popen(vd, *args, **kwargs):
    p = subprocess.Popen(*args, **kwargs)
    vd.spawnedProcesses.append(p)
    return p


@VisiData.api
def killLeftoverProcesses(vd):
    for p in vd.spawnedProcesses:
        if p.returncode is None:
            p.kill()


@VisiData.api
def guess_dir(vd, p):
    if p.is_dir():
        return dict(filetype='dir', _likelihood=10)


@VisiData.lazy_property
def currentDirSheet(p):
    'Support opening the current DirSheet from the vdmenu'
    return DirSheet(Path('.').absolute().name, source=Path('.'))

@asyncthread
def exec_shell(*args):
    p = vd.popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err or out:
        lines = err.decode('utf8').splitlines() + out.decode('utf8').splitlines()
        vd.push(TextSheet(' '.join(args), source=lines))


@VisiData.api
def open_dir(vd, p):
    if p.is_dir():
        return DirSheet(p.base_stem, source=p)
    if p.is_file():
        vd.status(f'opening {p.given} as txt')
        return vd.open_txt(p)
    vd.warning(f'could not determine file type for {p.given}')
    return DirSheet(p.base_stem, source=p)

@VisiData.api
def open_fdir(vd, p):
    return FileListSheet(p.base_stem, source=p)

@VisiData.api
def addShellColumns(vd, cmd, sheet, curcol=None):
    shellcol = ColumnShell(cmd, source=sheet, width=0, curcol=curcol)
    sheet.addColumnAtCursor(
            Column(cmd+'_stdout', type=bytes_rstrip, srccol=shellcol, getter=lambda col,row: col.srccol.getValue(row)[0]),
            Column(cmd+'_stderr', type=bytes_rstrip, srccol=shellcol, getter=lambda col,row: col.srccol.getValue(row)[1]),
            shellcol)


SHELL_COLREF_RE = r'\$\{([^}]+)\}|\$(\w+)'


class ColumnShell(Column):
    def __init__(self, name, cmd=None, curcol=None, **kwargs):
        super().__init__(name, **kwargs)
        self.expr = cmd or name
        self.curcol = curcol

    @asynccache(lambda col,row: (col, col.sheet.rowid(row)))
    def calcValue(self, row):
        try:
            context = LazyComputeRow(self.source, row, curcol=self.curcol)
            cmd = re.sub(SHELL_COLREF_RE,
                         lambda m: shlex.quote(str(context[m.group(1) or m.group(2)])),
                         self.expr)
            p = vd.popen([os.getenv('SHELL', 'bash'), '-c', cmd],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return p.communicate()
        except Exception as e:
            vd.exceptionCaught(e)


class DirSheet(Sheet):
    'Sheet displaying directory, using Enter to open a particular file.  Edited fields are applied to the filesystem.'
    guide = '''
        # Directory Sheet
        This is a list of files in the {sheet.displaySource} folder.

        - {help.commands.open_row_file}
        - {help.commands.open_rows}
        - {help.commands.open_dir_parent}
        - {help.commands.sysopen_row}
        - {help.commands.open_preview}

        ## Options (must reload to take effect)

        - {help.options.dir_depth}
        - {help.options.dir_hidden}
    '''
    rowtype = 'files' # rowdef: Path
    defer = True
    columns = [
        Column('directory',
            getter=lambda col,row: str(row.parent) if str(row.parent) in ('.', '/') else str(row.parent) + '/',
            setter=lambda col,row,val: col.sheet.moveFile(row, val)),
        Column('filename',
            getter=lambda col,row: row.name,
            setter=lambda col,row,val: col.sheet.renameFile(row, val)),
        Column('abspath', width=0, type=str,
            getter=lambda col,row: row,
            setter=lambda col,row,val: os.rename(row, val)),
        Column('ext', getter=lambda col,row: row.is_dir() and '/' or row.ext),
        Column('size', type=int,
            getter=lambda col,row: filesize(row),
            setter=lambda col,row,val: os.truncate(row, int(val))),
        Column('modtime', type=date,
            getter=lambda col,row: modtime(row),
            setter=lambda col,row,val: os.utime(row, times=((row.stat().st_atime, float(val))))),
        Column('owner', width=0,
            getter=lambda col,row: pwd.getpwuid(row.stat().st_uid).pw_name,
            setter=lambda col,row,val: os.chown(row, pwd.getpwnam(val).pw_uid, -1)),
        Column('group', width=0,
            getter=lambda col,row: grp.getgrgid(row.stat().st_gid).gr_name,
            setter=lambda col,row,val: os.chown(row, -1, grp.getgrnam(val).pw_gid)),
        Column('mode', width=0,
            getter=lambda col,row: '{:o}'.format(row.stat().st_mode),
            setter=lambda col,row,val: os.chmod(row, int(val, 8))),
        Column('filetype', width=0, cache='async', getter=lambda col,row: vd.popen(['file', '--brief', row], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip()),
        Column('preview', width=0, cache=True, getter=lambda col,row: col.sheet._openPreview(row)),
    ]
    nKeys = 2
    _ordering = [('modtime', True), ('filename', False)]  # sort by reverse modtime initially

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

    def moveFile(self, row, newparent):
        parent = Path(newparent)
        newpath = Path(parent/row.name)
        if parent.exists():
            if not parent.is_dir():
                vd.error('destination %s not a directory' % parent)
        else:
            with contextlib.suppress(FileExistsError):
                os.makedirs(parent)

        row.rename(newpath)
        row.given = newpath # modify visidata.Path
        self.restat()

    def renameFile(self, row, val):
        newpath = row.with_name(val)
        row.rename(newpath)
        row.given = newpath
        self.restat()

    def removeFile(self, path):
        if path.is_dir():
            if self.options.safety_first:
                os.rmdir(path)
            else:
                shutil.rmtree(path)  #1965
        else:
            path.unlink()

    def commitDeleteRow(self, r):
        self.removeFile(r)

    def newRow(self):
        vd.fail('new file not supported')

    def iterload(self):
        hidden_files = self.options.dir_hidden

        def _walkfiles(p, dir_depth:int=0):
            basepath = str(p)
            for folder, subdirs, files in os.walk(basepath):
                subfolder = folder[len(basepath)+1:]
                if not hidden_files and subfolder.startswith('.'): continue
                if subfolder in ['.', '..']: continue

                fpath = Path(folder)
                if str(fpath) != str(p):
                    yield fpath

                for fn in files:
                    yield fpath/fn

                if dir_depth < len(fpath.parents)-len(p.parents)+1:
                    for d in subdirs:
                        yield fpath/d
                    subdirs.clear()

        basepath = str(self.source)

        folders = set()

        for p in _walkfiles(self.source, self.options.dir_depth):
            if not hidden_files and p.name.startswith('.'):
                continue

            yield p

    def preloadHook(self):
        super().preloadHook()
        Path.stat.cache_clear()

    def restat(self):
        vstat.cache_clear()

    @asyncthread
    def putChanges(self):
        self.commitAdds()
        self.commitMods()
        self.commitDeletes()

        self._deferredDels.clear()
        self.reload()

    def getDefaultSaveName(sheet):
        return sheet.name + '.' + sheet.options.save_filetype


class FileListSheet(DirSheet):
    _ordering = []
    def iterload(self):
        for fn in self.source.open():
            yield Path(fn.rstrip())


@VisiData.api
def inputShell(vd):
    cmd = vd.input("sh$ ", type="sh")
    refs = [m.group(1) or m.group(2) for m in re.finditer(SHELL_COLREF_RE, cmd)]
    if not refs:
        vd.warning('no $column in command')
    else:
        colnames = [col.name for col in vd.sheet.columns]
        badnames = [name for name in refs if name not in colnames]
        if badnames:
            vd.fail(f'no such columns: {", ".join(badnames)}')
    return cmd

DirSheet.addCommand('`', 'open-dir-parent', 'vd.push(openSource(source.parent if source.resolve()!=Path(".").resolve() else os.path.dirname(source.resolve())))', 'open parent directory')  #1801
BaseSheet.addCommand('', 'open-dir-current', 'vd.push(vd.currentDirSheet)', 'open Directory Sheet: browse properties of files in current directory')

Sheet.addCommand('z;', 'addcol-shell', 'cmd=inputShell(); addShellColumns(cmd, sheet, curcol=cursorCol)', 'create new column from bash expression, with $columnNames as variables')

DirSheet.addCommand('Enter', 'open-row-file', 'vd.push(openSource(cursorRow or fail("no row"), filetype="dir" if cursorRow.is_dir() else LazyComputeRow(sheet, cursorRow).ext))', 'open current file as a new sheet')
DirSheet.addCommand('gEnter', 'open-rows', 'for r in selectedRows: vd.push(openSource(r))', 'open selected files as new sheets')
DirSheet.addCommand('Ctrl+O', 'sysopen-row', 'launchEditor(cursorRow)', 'open current file in external $EDITOR')
DirSheet.addCommand('gCtrl+O', 'sysopen-rows', 'launchEditor(*selectedRows)', 'open selected files in external $EDITOR')

DirSheet.addCommand('y', 'copy-row', 'copy_files([cursorRow], inputPath("copy to dest: "))', 'copy file to given directory *path*')
DirSheet.addCommand('gy', 'copy-selected', 'copy_files(selectedRows, inputPath("copy to dest: ", value=cursorRow.given))', 'copy selected files to given directory *path*')

DirSheet.addCommand('zEnter', 'open-row-filetype', 'ft = input("filetype: ", type="filetype", value=options.filetype or LazyComputeRow(sheet, cursorRow).ext); vd.push(openSource(cursorRow, filetype=ft) or fail(f"file {cursorDisplay} does not exist"))', 'open file in current row as input filetype')
DirSheet.addCommand('', 'open-preview', 'sheet.previewFile(cursorRow)', 'open split preview of file at cursor')


@DirSheet.api
def _openPreview(sheet, p):
    vs = vd.openSource(p, filetype="dir" if p.is_dir() else LazyComputeRow(sheet, p).ext)
    vs._dirpreview = True
    vs.ensureLoaded()
    return vs


@DirSheet.api
def previewFile(sheet, p):
    if not p: return
    vs = sheet.column('preview').getValue(p)
    if not isinstance(vs, BaseSheet):
        return  # still loading or error
    # remove old preview from pane 2
    for old in vd.sheetstack(2):
        if getattr(old, '_dirpreview', False):
            vd.sheets.remove(old)
    vd.push(vs, pane=2)
    vd.options.disp_splitwin_pct = vd.options.disp_splitwin_pct or 50
    sheet._previewing = True


@DirSheet.after
def checkCursor(sheet):
    if not getattr(sheet, '_previewing', False):
        return
    if not vd.options.disp_splitwin_pct:
        sheet._previewing = False
        return
    p = sheet.cursorRow
    if p and p != getattr(sheet, '_preview_path', None):
        sheet._preview_path = p
        sheet.previewFile(p)
    # preload previews for visible rows
    previewCol = sheet.column('preview')
    for row in sheet.rows[sheet.topRowIndex:sheet.topRowIndex + sheet.nScreenRows]:
        previewCol.getValue(row)


@DirSheet.api
@asyncthread
def copy_files(sheet, paths, dest):
    destdir = Path(dest)
    destdir.is_dir() or vd.fail('target must be directory')
    vd.status('copying %s %s to %s' % (len(paths), sheet.rowtype, destdir))
    os.makedirs(destdir, exist_ok=True)
    for srcpath in Progress(paths, gerund='copying'):
        try:
            destpath = destdir/str(srcpath._path.name)
            if srcpath.is_dir():
                shutil.copytree(srcpath, destpath)
            else:
                shutil.copyfile(srcpath, destpath)
        except Exception as e:
            vd.exceptionCaught(e)


vd.addGlobals(
    DirSheet=DirSheet,
    bytes_rstrip=bytes.rstrip,
)

vd.addMenuItems('''
    Column > Add column > shell > addcol-shell
    Row > Open file > open-row-filetype
    View > Preview file > open-preview
''')
