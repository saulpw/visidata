from visidata import Column, Sheet, LazyMapRow, asynccache, exceptionCaught

import subprocess


Sheet.addCommand('z;', 'addcol-sh', 'cmd=input("sh$ ", type="sh"); addShellColumns(cmd, sheet)')


def addShellColumns(cmd, sheet):
    c = ColumnShell(cmd, source=sheet, width=0)
    sheet.addColumn(c)
    sheet.addColumn(Column(cmd+'_stdout', srccol=c, getter=lambda col,row: col.srccol.getValue(row)[0]))
    sheet.addColumn(Column(cmd+'_stderr', srccol=c, getter=lambda col,row: col.srccol.getValue(row)[1]))


class ColumnShell(Column):
    def __init__(self, name, cmd=None, **kwargs):
        super().__init__(name, **kwargs)
        self.expr = cmd or name

    @asynccache
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
