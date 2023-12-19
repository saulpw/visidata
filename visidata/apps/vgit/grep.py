from visidata import vd, VisiData, Path, ColumnItem, ESC

from .gitsheet import GitSheet


@VisiData.api
def git_grep(vd, p, args):
    return GitGrep(args[0], regex=args[0], source=p)


class GitGrep(GitSheet):
    rowtype = 'results' # rowdef: list(file, line, line_contents)
    guide = '''
        # vgit grep
        Each row on this sheet is a line matching the regex pattern `{sheet.regex}` in the tracked files of the current directory.

        - `Ctrl+O` to open _{sheet.cursorRow[0]}:{sheet.cursorRow[1]}_ in the system editor; saved changes will be reflected automatically.
    '''
    columns = [
        ColumnItem('file', 0, help='filename of the match'),
        ColumnItem('line', 1, help='line number within file'),
        ColumnItem('text', 2, width=120, help='matching line of text'),
    ]
    nKeys = 2

    def iterload(self):
        tmp = (self.topRowIndex, self.cursorRowIndex)
        for line in self.git_lines('grep', '--no-color', '-z', '--line-number', '--ignore-case', self.regex):
#            line = line.replace(ESC+'[1;31m', '[:green]')
#            line = line.replace(ESC+'[m', '[/]')
            yield list(line.split('\0'))
        self.topRowIndex, self.cursorRowIndex = tmp


GitSheet.addCommand('g/', 'git-grep', 'rex=inputRegex("git grep: "); vd.push(GitGrep(rex, regex=rex, source=sheet))', 'find in all files in this repo')
GitGrep.addCommand('Ctrl+O', 'sysopen-row', 'launchExternalEditorPath(Path(cursorRow[0]), linenum=cursorRow[1]); reload()', 'open this file in $EDITOR')
GitGrep.bindkey('Enter', 'sysopen-row')
