import os
import io
import sys
import stat
import locale
import subprocess
import contextlib
try:
    import pwd
    import grp
except ImportError:
    pass # pwd,grp modules not available on Windows

from visidata import Column, Sheet, LazyComputeRow, asynccache, options, option, globalCommand
from visidata import Path, ENTER, date, asyncthread, confirm, fail, FileExistsError, VisiData
from visidata import CellColorizer, RowColorizer, modtime, filesize, vstat


option('dir_recurse', False, 'walk source path recursively on DirSheet')
option('dir_hidden', False, 'load hidden files on DirSheet')


@VisiData.lazy_property
def currentDirSheet(p):
    'Support opening the current DirSheet from the vdmenu'
    return DirSheet('.', source=Path('.'))

@asyncthread
def exec_shell(*args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err or out:
        lines = err.decode('utf8').splitlines() + out.decode('utf8').splitlines()
        vd.push(TextSheet(' '.join(args), source=lines))


def open_dir(p):
    return DirSheet(p.name, source=p)

def open_fdir(p):
    return FileListSheet(p.name, source=p)

def addShellColumns(cmd, sheet):
    shellcol = ColumnShell(cmd, source=sheet, width=0)
    sheet.addColumnAtCursor(
            shellcol,
            Column(cmd+'_stdout', srccol=shellcol, getter=lambda col,row: col.srccol.getValue(row)[0]),
            Column(cmd+'_stderr', srccol=shellcol, getter=lambda col,row: col.srccol.getValue(row)[1]))


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
                    args.append(str(context[arg[1:]]))
                else:
                    args.append(arg)

            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return p.communicate()
        except Exception as e:
            vd.exceptionCaught(e)


class DirSheet(Sheet):
    'Sheet displaying directory, using ENTER to open a particular file.  Edited fields are applied to the filesystem.'
    rowtype = 'files' # rowdef: Path
    defer = True
    columns = [
        Column('directory',
            getter=lambda col,row: str(row.parent) if str(row.parent) == '.' else str(row.parent) + '/',
            setter=lambda col,row,val: col.sheet.moveFile(row, val)),
        Column('filename',
            getter=lambda col,row: row.name + row.suffix,
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
            os.rmdir(path)
        else:
            path.unlink()

    def deleteSourceRow(self, rowidx):
        self.removeFile(self.rows[rowidx])
        self.rows.pop(rowidx)

    def iterload(self):
        def _walkfiles(p):
            basepath = str(p)
            for folder, subdirs, files in os.walk(basepath):
                subfolder = folder[len(basepath)+1:]
                if subfolder in ['.', '..']: continue

                fpath = Path(folder)
                yield fpath

                for fn in files:
                    yield fpath/fn

        def _listfiles(p):
            basepath = str(p)
            for fn in os.listdir(basepath):
                yield p/fn


        basepath = str(self.source)

        folders = set()
        f = _walkfiles if self.options.dir_recurse else _listfiles

        hidden_files = options.dir_hidden
        for p in f(self.source):
            if hidden_files and p.name.startswith('.'):
                continue

            yield p

    def preloadHook(self):
        super().preloadHook()
        Path.stat.cache_clear()

    def restat(self):
        vstat.cache_clear()


class FileListSheet(DirSheet):
    _ordering = []
    def iterload(self):
        for fn in self.source.open_text():
            yield Path(fn.rstrip())

globalCommand('', 'open-dir-current', 'vd.push(vd.currentDirSheet)', 'open Directory Sheet: browse properties of files in current directory')

Sheet.addCommand('z;', 'addcol-sh', 'cmd=input("sh$ ", type="sh"); addShellColumns(cmd, sheet)', 'create new column from bash expression, with $columnNames as variables')

DirSheet.addCommand(ENTER, 'open-row', 'vd.push(openSource(cursorRow or fail("no row"), filetype="dir" if cursorRow.is_dir() else LazyComputeRow(sheet, cursorRow).ext))', 'open current file as a new sheet')
DirSheet.addCommand('g'+ENTER, 'open-rows', 'for r in selectedRows: vd.push(openSource(r))', 'open selected files as new sheets')
DirSheet.addCommand('^O', 'sysopen-row', 'launchEditor(cursorRow)', 'open current file in external $EDITOR')
DirSheet.addCommand('g^O', 'sysopen-rows', 'launchEditor(*selectedRows)', 'open selected files in external $EDITOR')
