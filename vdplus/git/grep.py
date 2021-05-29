from visidata import Sheet, ColumnItem, asyncthread, globalCommand, ENTER
import vgit


class GitGrep(vgit.GitSheet):
    rowtype = 'results' # rowdef: list(file, line, line_contents)
    columns = [
        ColumnItem('filename', 0),
        ColumnItem('linenum', 1),
        ColumnItem('line', 2),
    ]
    @asyncthread
    def reload(self):
        tmp = (self.topRowIndex, self.cursorRowIndex)
        self.rows = []
        for line in self.git_lines('grep', '--no-color', '-z', '--line-number', '--ignore-case', self.regex):
            self.addRow(line.split('\0'))
        self.topRowIndex, self.cursorRowIndex = tmp

    def openRow(self, row):
        'open this match'
        vs=GitFileSheet(row[0])
        vs.cursorRowIndex=int(row[1])-1
        vs.reload()
        return vs


Sheet.unbindkey('g/')
globalCommand('g/', 'git-grep', 'rex=input("git grep: "); vd.push(GitGrep(rex, regex=rex, source=sheet))', 'find in all files in this repo'),

GitGrep.addCommand('^O', 'sysopen-row', 'launchExternalEditorPath(Path(cursorRow[0]), linenum=cursorRow[1]); reload()', 'open this file in $EDITOR')
