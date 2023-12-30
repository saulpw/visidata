import os
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
from visidata import Path, ENTER, asyncthread, VisiData
from visidata import modtime, filesize, vstat, Progress, TextSheet
from visidata.type_date import date


vd.option('dir_depth', 0, 'folder recursion depth on DirSheet')
vd.option('dir_hidden', False, 'load hidden files on DirSheet')


@VisiData.api
def guess_dir(vd, p):
    if p.is_dir():
        return dict(filetype='dir')


@VisiData.lazy_property
def currentDirSheet(p):
    'Support opening the current DirSheet from the vdmenu'
    return DirSheet(Path('.').absolute().name, source=Path('.'))

@asyncthread
def exec_shell(*args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err or out:
        lines = err.decode('utf8').splitlines() + out.decode('utf8').splitlines()
        vd.push(TextSheet(' '.join(args), source=lines))


@VisiData.api
def open_dir(vd, p):
    return DirSheet(p.base_stem, source=p)

@VisiData.api
def open_fdir(vd, p):
    return FileListSheet(p.base_stem, source=p)

@VisiData.api
def addShellColumns(vd, cmd, sheet):
    shellcol = ColumnShell(cmd, source=sheet, width=0)
    sheet.addColumnAtCursor(
            Column(cmd+'_stdout', type=bytes.rstrip, srccol=shellcol, getter=lambda col,row: col.srccol.getValue(row)[0]),
            Column(cmd+'_stderr', type=bytes.rstrip, srccol=shellcol, getter=lambda col,row: col.srccol.getValue(row)[1]),
            shellcol)


class ColumnShell(Column):
    def __init__(self, name, cmd=None, **kwargs):
        super().__init__(name, **kwargs)
        self.expr = cmd or name

    @asynccache(lambda col,row: (col, col.sheet.rowid(row)))
    def calcValue(self, row):
        try:
            import shlex
            args = []
            context = LazyComputeRow(self.source, row)
            for arg in shlex.split(self.expr):
                if arg.startswith('$'):
                    args.append(shlex.quote(str(context[arg[1:]])))
                else:
                    args.append(arg)

            p = subprocess.Popen([os.getenv('SHELL', 'bash'), '-c', ' '.join(args)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return p.communicate()
        except Exception as e:
            vd.exceptionCaught(e)


class DirSheet(Sheet):
    'Sheet displaying directory, using ENTER to open a particular file.  Edited fields are applied to the filesystem.'
    guide = '''
        # Directory Sheet
        This is a list of files in the {sheet.displaySource} folder.

        - {help.commands.open_row_file}
        - {help.commands.open_rows}
        - (`open-dir-parent`) to open parent directory
        - {help.commands.sysopen_row}

        ## Options (must reload to take effect)

        - {help.options.dir_depth}
            - [CLI] `-r` to include all files in all subfolders
        - {help.options.dir_hidden}
    '''
    rowtype = 'files' # rowdef: Path
    defer = True
    columns = [
        Column('directory',
            getter=lambda col,row: str(row.parent) if str(row.parent) == '.' else str(row.parent) + '/',
            setter=lambda col,row,val: col.sheet.moveFile(row, val)),
        Column('filename',
            getter=lambda col,row: row._path.name,
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
        Column('filetype', width=0, cache='async', getter=lambda col,row: subprocess.Popen(['file', '--brief', row], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip()),
    ]
    nKeys = 2
    _ordering = [('modtime', True)]  # sort by reverse modtime initially

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
        newpath = Path(parent/(row.name + row.suffix))
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
            if not hidden_files and str(p).startswith('.') and not str(p).startswith('..'):
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
    if '$' not in cmd:
        vd.warning('no $column in command')
    return cmd

DirSheet.addCommand('`', 'open-dir-parent', 'vd.push(openSource(source.parent if source.resolve()!=Path(".").resolve() else os.path.dirname(source.resolve())))', 'open parent directory')  #1801
BaseSheet.addCommand('', 'open-dir-current', 'vd.push(vd.currentDirSheet)', 'open Directory Sheet: browse properties of files in current directory')

Sheet.addCommand('z;', 'addcol-shell', 'cmd=inputShell(); addShellColumns(cmd, sheet)', 'create new column from bash expression, with $columnNames as variables')

DirSheet.addCommand(ENTER, 'open-row-file', 'vd.push(openSource(cursorRow or fail("no row"), filetype="dir" if cursorRow.is_dir() else LazyComputeRow(sheet, cursorRow).ext))', 'open current file as a new sheet')
DirSheet.addCommand('g'+ENTER, 'open-rows', 'for r in selectedRows: vd.push(openSource(r))', 'open selected files as new sheets')
DirSheet.addCommand('^O', 'sysopen-row', 'launchEditor(cursorRow)', 'open current file in external $EDITOR')
DirSheet.addCommand('g^O', 'sysopen-rows', 'launchEditor(*selectedRows)', 'open selected files in external $EDITOR')

DirSheet.addCommand('y', 'copy-row', 'copy_files([cursorRow], inputPath("copy to dest: "))', 'copy file to given directory')
DirSheet.addCommand('gy', 'copy-selected', 'copy_files(selectedRows, inputPath("copy to dest: ", value=cursorRow.given))', 'copy selected files to given directory')

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


vd.addGlobals({
    'DirSheet': DirSheet
})

vd.addMenuItems('''
    Column > Add column > shell > addcol-shell
''')
