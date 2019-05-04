from visidata import Sheet, Column, ColumnAttr, date, vlen, asyncthread, Path, ENTER
import vgit


class GitLinesColumn(Column):
    def __init__(self, name, cmd, *args, **kwargs):
        super().__init__(name, cache=True, **kwargs)
        cmdparts = cmd.split()
        if cmdparts[0] == 'git':
            cmdparts = cmdparts[1:]
        self.cmd = cmdparts + list(args)

    def calcValue(self, r):
        return list(vgit.git_lines('--git-dir', r.path.joinpath('.git').abspath(), *self.cmd))


class GitAllColumn(GitLinesColumn):
    def calcValue(self, r):
        return vgit.git_all('--git-dir', r.path.joinpath('.git').abspath(), *self.cmd).strip()



class GitOverview(Sheet):
    rowtype = 'repos'  # rowdef: GitRepo
    columns = [
        ColumnAttr('repo', 'path', type=str),
        GitLinesColumn('stashes', 'git stash list', type=vlen),
        GitLinesColumn('cached', 'git diff --cached', type=vlen),
        GitLinesColumn('branches', 'git branch --no-color', type=vlen),
        GitAllColumn('branch', 'git rev-parse --abbrev-ref HEAD'),
        Column('modtime', type=date, getter=lambda c,r: r.path.stat().st_mtime),
    ]
    nKeys = 1

    @asyncthread
    def reload(self):
        import glob
        import os.path
        self.rows = []
        for fn in glob.glob(os.path.join('**', '.git/'), recursive=True):
            if fn == '.git/':
                path = Path('.')
            else:
                path = Path(fn).parent.parent
            self.addRow(GitRepo([path]))


GitOverview.addCommand(ENTER, 'dive-row', 'vd.push(open_git(Path(cursorRow.path.abspath())))')
GitOverview.addCommand('z'+ENTER, 'dive-cell', 'view(cursorValue)')
