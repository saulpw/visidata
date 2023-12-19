import functools

from visidata import vd, VisiData, Column, ItemColumn, date, RowColorizer, asyncthread, Progress, AttrDict

from .gitsheet import GitSheet


@VisiData.api
def git_log(vd, p, *args):
    return GitLogSheet('git-log', source=p, gitargs=args)

# rowdef: (commit_hash, refnames, author, author_date, body, notes)
class GitLogSheet(GitSheet):
    guide = '''
# git log {sheet.gitargstr}
{sheet.cursorRow.message}
    '''
    GIT_LOG_FORMAT = ['%H', '%D', '%an <%ae>', '%ai', '%B', '%N']
    rowtype = 'commits'  # rowdef: AttrDict
    defer = True
    savesToSource = True
    columns = [
        ItemColumn('commitid', width=8),
        ItemColumn('refnames', width=12),
        ItemColumn('message', type=str.strip, setter=lambda c,r,v: c.sheet.git('commit --amend --no-edit --quiet --message', v), width=50),
        ItemColumn('author', setter=lambda c,r,v: c.sheet.git('commit --amend --no-edit --quiet --author', v)),
        ItemColumn('author_date', type=date, setter=lambda c,r,v: c.sheet.git('commit --amend --no-edit --quiet --date', v)),
        ItemColumn('notes', setter=lambda c,r,v: c.sheet.git('notes add --force --message', v, r.commitid)),
    ]
    colorizers = [
            RowColorizer(5, 'color_vgit_unpushed', lambda s,c,r,v: r and not s.inRemoteBranch(r.commitid)),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @functools.lru_cache()
    def inRemoteBranch(self, commitid):
        return self.git_all('branch -r --contains', commitid, _ok_code=[0, 1])

    def iterload(self):
        lines = self.git_iter('log --no-color -z', '--pretty=format:' + '%x1f'.join(self.GIT_LOG_FORMAT), *self.gitargs)
        for record in Progress(tuple(lines)):
            r = record.split('\x1f')
            yield AttrDict(
                commitid=r[0],
                refnames=r[1],
                author=r[2],
                author_date=r[3],
                message=r[4],
                notes=r[5],
            )

    def openRow(self, row):
        'open this commit'
        return getCommitSheet(row[0][:7], self, row[0])

    @asyncthread
    def commit(self, path, adds, mods, dels):

        assert not adds
        assert not dels

        for row, rowmods in mods.values():
            for col, val in rowmods.values():
                vd.callNoExceptions(col.putValue, row, val)

        self.reload()
        self.resetDeferredCommit()


GitLogSheet.addCommand(None, 'delete-row', 'error("delete is not supported")')
GitLogSheet.addCommand(None, 'add-row', 'error("commits cannot be added")')
#GitLogSheet.addCommand('x', 'git-pick', 'git("cherry-pick", cursorRow.commitid)', 'cherry-pick this commit onto current branch')
#GitLogSheet.addCommand('r', 'git-reset-here', 'git("update-ref", "refs/heads/"+source, cursorRow[0])', 'reset this branch to this commit')

GitSheet.addCommand('', 'git-log', 'vd.push(git_log(gitRootPath, branch))', 'push log of current branch')

vd.addMenuItems('''
    Git > Open > log > git-log
''')
