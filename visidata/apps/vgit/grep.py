from visidata import vd, VisiData, Path, ColumnItem, ESC

from .gitsheet import GitSheet


@VisiData.api
def git_grep(vd, args):
    return GitGrep(args[0], regex=args[0], source=Path('.'))


class GitGrep(GitSheet):
    rowtype = 'results' # rowdef: list(file, line, line_contents)
    columns = [
        ColumnItem('file', 0),
        ColumnItem('line', 1),
        ColumnItem('text', 2),
    ]

    def iterload(self):
        tmp = (self.topRowIndex, self.cursorRowIndex)
        for line in self.git_lines('grep', '--no-color', '-z', '--line-number', '--ignore-case', self.regex):
#            line = line.replace(ESC+'[1;31m', '[:green]')
#            line = line.replace(ESC+'[m', '[:]')
            yield list(line.split('\0'))
        self.topRowIndex, self.cursorRowIndex = tmp


GitSheet.addCommand('g/', 'git-grep', 'rex=input("git grep: "); vd.push(GitGrep(rex, regex=rex, source=sheet))', 'find in all files in this repo'),
GitGrep.addCommand('Ctrl+O', 'sysopen-row', 'launchExternalEditorPath(Path(cursorRow[0]), linenum=cursorRow[1]); reload()', 'open this file in $EDITOR')
