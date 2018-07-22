from visidata import Column, Sheet, LazyMapRow, asyncthread

import subprocess


Sheet.addCommand('z;', 'addcol-sh', 'cmd=input("sh$ ", type="sh"); addColumn(ColumnShell(cmd, source=sheet))')


class ColumnShell(Column):
    def __init__(self, name, cmd=None, **kwargs):
        super().__init__(name, **kwargs)
        self.expr = cmd or name

    @asyncthread
    def calcValue(self, row):
        args = self.expr.format_map(LazyMapRow(self.source, row)).split()
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        return p.communicate()[0]
