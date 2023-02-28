import os.path
import sh
import io

from visidata import *
from visidata import namedlist


class GitCmdLog(Sheet):
    rowtype = 'git commands'  # rowdef: GitCmd
    columns = [
        ColumnAttr('sheet'),
        ColumnAttr('command'),
        ColumnAttr('output.stdout'),
        ColumnAttr('output.stderr'),
    ]
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.rows = []


    def openRow(self, row):
        'open output of this command'
        return TextSheet(row[0], source=row[1])


@VisiData.lazy_property
def gitcmdlog(vd):
    return GitCmdLog('gitcmdlog')


class GitUndo:
    def __init__(self, *args):
        self.cmdargs = args
    def __enter__(self):
        return self
    def __exit__(self, exctype, exc, tb):
        out = git_all(*self.cmdargs)


BaseSheet.addCommand('gD', 'git-output', 'vd.push(vd.gitcmdlog)', 'show output of git commands this session')

