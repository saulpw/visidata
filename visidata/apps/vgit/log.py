import functools

from visidata import vd, VisiData, Column, ItemColumn, date, RowColorizer, asyncthread, Progress

from .gitsheet import GitSheet


@VisiData.api
def git_log(vd, p, args):
    return GitLogSheet('git-log', source=p, gitargs=args)

# rowdef: (commit_hash, refnames, author, author_date, body, notes)
class GitLogSheet(GitSheet):
    help = '''


    '''
    # corresponding to rowdef
    GIT_LOG_FORMAT = ['%H', '%D', '%an <%ae>', '%ai', '%B', '%N']
    rowtype = 'commits'
    defer = True
    savesToSource = True
    columns = [
            ItemColumn('commitid', 0, width=8),
            ItemColumn('refnames', 1, width=12),
            Column('message', getter=lambda c,r: r[4], setter=lambda c,r,v: c.sheet.git('commit', '--amend', '--no-edit', '--quiet', '--message', v), width=50),
            Column('author', getter=lambda c,r: r[2], setter=lambda c,r,v: c.sheet.git('commit', '--amend', '--no-edit', '--quiet', '--author', v)),
            Column('author_date', type=date, getter=lambda c,r:r[3], setter=lambda c,r,v: c.sheet.git('commit', '--amend', '--no-edit', '--quiet', '--date', v)),
            Column('notes', getter=lambda c,r: r[5], setter=lambda c,r,v: c.sheet.git('notes', 'add', '--force', '--message', v, r[0])),
    ]
    colorizers = [
            RowColorizer(5, 'color_vgit_unpushed', lambda s,c,r,v: r and not s.inRemoteBranch(r[0])),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @functools.lru_cache()
    def inRemoteBranch(self, commitid):
        return self.git_all('branch -r --contains', commitid)

    def iterload(self):
        lines = self.git_iter('log --no-color -z', '--pretty=format:' + '%x1f'.join(self.GIT_LOG_FORMAT), *self.gitargs)
        for record in Progress(tuple(lines)):
            yield record.split('\x1f')

    def openRow(self, row):
        'open this commit'
        return getCommitSheet(row[0][:7], self, row[0])

    @asyncthread
    def commit(self, path, adds, mods, dels):

        assert not adds
        assert not dels

        for row, rowmods in mods.values():
            for col, val in rowmods.values():
                try:
                    col.putValue(row, val)
                except Exception as e:
                    vd.exceptionCaught(e)

        self.reload()
        self.resetDeferredCommit()


GitLogSheet.addCommand(None, 'delete-row', 'error("delete is not supported")')
GitLogSheet.addCommand(None, 'add-row', 'error("commits cannot be added")')


GitSheet.addCommand('', 'git-log', 'vd.push(git_log(self.gitRootPath, branch))', 'push log of current branch')

vd.addMenuItems('''
    Git > Open > log > git-log
''')
