import os
import stat
import subprocess
import contextlib
try:
    import pwd
    import grp
except ImportError:
    pass # pwd,grp modules not available on Windows

from visidata import Column, Sheet, LazyComputeRow, asynccache, exceptionCaught, options, option
from visidata import Path, ENTER, date, asyncthread, confirm, fail, FileExistsError
from visidata import CellColorizer, RowColorizer, undoAddCols, undoBlocked, modtime, filesize

option('dir_recurse', False, 'walk source path recursively on DirSheet')
option('dir_hidden', False, 'load hidden files on DirSheet')

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
            context = LazyComputeRow(self.source, row)
            for arg in shlex.split(self.expr):
                if arg.startswith('$'):
                    args.append(str(context[arg[1:]]))
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
        Column('directory', getter=lambda col,row: row.parent if str(row.parent) == '.' else str(row.parent) + '/'),
        Column('filename', getter=lambda col,row: row.name + row.suffix),
        Column('abspath', width=0, type=str),
        Column('ext', getter=lambda col,row: row.is_dir() and '/' or row.ext),
        Column('size', type=int, getter=lambda col,row: filesize(row)),
        Column('modtime', type=date, getter=lambda col,row: modtime(row)),
        Column('owner', width=0, getter=lambda col,row: pwd.getpwuid(row.stat().st_uid).pw_name),
        Column('group', width=0, getter=lambda col,row: grp.getgrgid(row.stat().st_gid).gr_name),
        Column('mode', width=0, getter=lambda col,row: '{:o}'.format(row.stat().st_mode)),
        Column('filetype', width=0, cache=True, getter=lambda col,row: subprocess.Popen(['file', '--brief', row], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip()),
    ]
    nKeys = 2

    @asyncthread
    def reload(self):
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


        self.rows = []
        basepath = str(self.source)

        folders = set()
        f = _walkfiles if options.dir_recurse else _listfiles

        hidden_files = options.dir_hidden
        for p in f(self.source):
            if hidden_files and p.name.startswith('.'):
                continue

            self.addRow(p)

        # sort by modtime initially
        self.rows.sort(key=modtime, reverse=True)


DirSheet.addCommand(ENTER, 'open-row', 'vd.push(openSource(cursorRow or fail("no row")))')
DirSheet.addCommand('g'+ENTER, 'open-rows', 'for r in selectedRows: vd.push(openSource(r))')
DirSheet.addCommand('^O', 'sysopen-row', 'launchEditor(cursorRow)')
DirSheet.addCommand('g^O', 'sysopen-rows', 'launchEditor(*selectedRows)')
