import os
import stat
import pwd
import grp
import subprocess
import contextlib

from visidata import Column, Sheet, LazyMapRow, asynccache, exceptionCaught, DeferredSetColumn
from visidata import Path, ENTER, date, asyncthread, confirm, fail, error, FileExistsError
from visidata import CellColorizer, RowColorizer


Sheet.addCommand('z;', 'addcol-sh', 'cmd=input("sh$ ", type="sh"); addShellColumns(cmd, sheet)')


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

    @asynccache(lambda col,row: (col, id(row)))
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
        DeferredSetColumn('directory',
            getter=lambda col,row: row.parent.relpath(col.sheet.source.resolve()),
            setter=lambda col,row,val: col.sheet.moveFile(row, val)),
        DeferredSetColumn('filename',
            getter=lambda col,row: row.name + row.ext,
            setter=lambda col,row,val: col.sheet.renameFile(row, val)),
        DeferredSetColumn('pathname', width=0,
            getter=lambda col,row: row.resolve(),
            setter=lambda col,row,val: os.rename(row.resolve(), val)),
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
        DeferredSetColumn('mode', width=0,
            getter=lambda col,row: '{:o}'.format(row.stat().st_mode),
            setter=lambda col,row,val: os.chmod(row.resolve(), int(val, 8))),
        Column('filetype', width=0, cache=True, getter=lambda col,row: subprocess.Popen(['file', '--brief', row.resolve()], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip()),
    ]
    colorizers = [
#        CellColorizer(4, None, lambda s,c,r,v: s.colorOwner(s,c,r,v)),
        CellColorizer(8, 'color_change_pending', lambda s,c,r,v: s.changed(c, r)),
        RowColorizer(9, 'color_delete_pending', lambda s,c,r,v: r in s.toBeDeleted),
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
            if getattr(col, '_modifiedValues', None) and id(row) in col._modifiedValues:
                del col._modifiedValues[id(row)]

        if row in self.toBeDeleted:
            self.toBeDeleted.remove(row)
        self.restat(row)

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
                col.realsetter(col, row, col._modifiedValues[id(row)])
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
DirSheet.addCommand('z^R', 'reload-row', 'undoMod(cursorRow)')
DirSheet.addCommand('gz^R', 'reload-rows', 'for r in self.selectedRows: undoMod(r)')
DirSheet.addCommand(None, 'delete-row', 'if cursorRow not in toBeDeleted: toBeDeleted.append(cursorRow); cursorRowIndex += 1')
DirSheet.addCommand(None, 'delete-selected', 'deleteFiles(selectedRows)')
