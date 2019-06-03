import os
import stat
import pwd
import grp
import subprocess
import contextlib

from visidata import Column, Sheet, LazyMapRow, asynccache, exceptionCaught
from visidata import Path, ENTER, date, asyncthread, confirm, fail, error, FileExistsError
from visidata import CellColorizer, RowColorizer, undoAddCols, undoBlocked


Sheet.addCommand('z;', 'addcol-sh', 'cmd=input("sh$ ", type="sh"); addShellColumns(cmd, sheet)', undo=undoAddCols)


@asyncthread
def exec_shell(*args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err or out:
        lines = err.decode('utf8').splitlines() + out.decode('utf8').splitlines()
        vd.push(TextSheet(' '.join(args), lines))


def open_dir(p):
    return DirSheet(p.name, source=p)

def addShellColumns(cmd, sheet):
    shellcol = ColumnShell(cmd, source=sheet, width=0)
    for i, c in enumerate([
            shellcol,
            Column(cmd+'_stdout', srccol=shellcol, getter=lambda col,row: col.srccol.getValue(row)[0]),
            Column(cmd+'_stderr', srccol=shellcol, getter=lambda col,row: col.srccol.getValue(row)[1]),
            ]):
        sheet.addColumn(c, index=sheet.cursorColIndex+i+1)


class ColumnShell(Column):
    def __init__(self, name, cmd=None, **kwargs):
        super().__init__(name, **kwargs)
        self.expr = cmd or name

    @asynccache(lambda col,row: (col, col.sheet.rowid(row)))
    def calcValue(self, row):
        try:
            import shlex
            args = []
            lmr = LazyMapRow(self.source, row)
            for arg in shlex.split(self.expr):
                if arg.startswith('$'):
                    args.append(str(lmr[arg[1:]]))
                else:
                    args.append(arg)

            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return p.communicate()
        except Exception as e:
            exceptionCaught(e)


class DirSheet(Sheet):
    'Sheet displaying directory, using ENTER to open a particular file.  Edited fields are applied to the filesystem.'
    rowtype = 'files' # rowdef: Path
    columns = [
        Column('directory',
            getter=lambda col,row: row.parent.relpath(col.sheet.source),
            setter=lambda col,row,val: col.sheet.moveFile(row, val)),
        Column('filename',
            getter=lambda col,row: row.name + row.ext,
            setter=lambda col,row,val: col.sheet.renameFile(row, val)),
        Column('pathname', width=0,
            getter=lambda col,row: row.resolve(),
            setter=lambda col,row,val: os.rename(row.resolve(), val)),
        Column('ext', getter=lambda col,row: row.is_dir() and '/' or row.suffix),
        Column('size', type=int,
            getter=lambda col,row: row.stat().st_size,
            setter=lambda col,row,val: os.truncate(row.resolve(), int(val))),
        Column('modtime', type=date,
            getter=lambda col,row: row.stat().st_mtime,
            setter=lambda col,row,val: os.utime(row.resolve(), times=((row.stat().st_atime, float(val))))),
        Column('owner', width=0,
            getter=lambda col,row: pwd.getpwuid(row.stat().st_uid).pw_name,
            setter=lambda col,row,val: os.chown(row.resolve(), pwd.getpwnam(val).pw_uid, -1)),
        Column('group', width=0,
            getter=lambda col,row: grp.getgrgid(row.stat().st_gid).gr_name,
            setter=lambda col,row,val: os.chown(row.resolve(), -1, grp.getgrnam(val).pw_gid)),
        Column('mode', width=0,
            getter=lambda col,row: '{:o}'.format(row.stat().st_mode),
            setter=lambda col,row,val: os.chmod(row.resolve(), int(val, 8))),
        Column('filetype', width=0, cache=True, getter=lambda col,row: subprocess.Popen(['file', '--brief', row.resolve()], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip()),
    ]
#        CellColorizer(4, None, lambda s,c,r,v: s.colorOwner(s,c,r,v)),
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

    @asyncthread
    def commit(self, adds, changes, deletes):
        oldrows = self.rows
        self.rows.clear()
        for r in oldrows:
            try:
                if self.rowid(r) in deletes:
                    self.removeFile(r)
                else:
                    self.rows.append(r)
            except Exception as e:
                exceptionCaught(e)

        for row, cols in changes.values():
            for col in cols:
                try:
                    col.putValue(row, col._modifiedValues[self.rowid(row)])
                    self.restat(row)
                except Exception as e:
                    exceptionCaught(e)

        for row in adds.values():
            self.restat(row)

    @asyncthread
    def reload(self):
        self.reset()  # reset deferred caches
        self.rows = []
        basepath = self.source.resolve()

        folders = set()
        for folder, subdirs, files in os.walk(basepath):
            subfolder = folder[len(basepath)+1:]
            if subfolder in ['.', '..']: continue

            if folder not in folders:
                self.rows.append(Path(folder))

            for fn in files:
#                if fn.startswith('.'): continue
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
