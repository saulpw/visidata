# repo-wide sheets

import re

from visidata import *
from . import GitSheet, GitStatus, GitContext

__all__ = ['GitStashes', 'GitRemotes', 'GitLogSheet']

theme('color_vgit_unpushed', 'cyan', 'unpushed commits on log sheet')

# how to incorporate fetch/push/pull?
class GitRemotes(GitSheet):
    columns=[
            Column('remote', getter=lambda c,r: r[0], setter=lambda c,r,v: c.sheet.git('remote', 'rename', r[0], v)),
            Column('url', getter=lambda c,r: r[1], setter=lambda c,r,v: c.sheet.git('remote', 'set-url', r[0], v)),
            Column('type', getter=lambda c,r: r[2]),
    ]

    def reload(self):
        self.rows = []
        for line in self.git_lines('remote', '-v', 'show'):
            name, url, paren_type = line.split()
            self.addRow((name, url, paren_type[1:-1]))


class GitStashes(GitSheet):
    rowtype = 'stashes'  # rowdef: list(stashid, starting_branch, sha1, msg)
    columns = [
        ColumnItem('stashid', 0),
        ColumnItem('start_branch', 1),
        ColumnItem('sha1', 2),
        ColumnItem('msg', 3),
    ]

    @asyncthread
    def reload(self):
        self.rows = []
        for line in self.git_lines('stash', 'list'):
            stashid, ctx, rest = line[:-1].split(': ', 2)
            starting_branch = ctx[len('WIP on '):]
            sha1, msg = rest.split(' ', 1)
            self.addRow([stashid, starting_branch, sha1, msg])

    def openRow(self, row):
        'open this stashed change'
        return HunksSheet(row[0]+"_diffs", "stash", "show", "--no-color", "--patch", row[0], source=self)


# rowdef: (commit_hash, refnames, author, author_date, body, notes)
class GitLogSheet(GitSheet):
    # corresponding to rowdef
    GIT_LOG_FORMAT = ['%H', '%D', '%an <%ae>', '%ai', '%B', '%N']
    rowtype = 'commits'
    defermods = True
    savesToSource = True
    columns = [
            ColumnItem('commitid', 0, width=8),
            ColumnItem('refnames', 1, width=12),
            Column('message', height=3, getter=lambda c,r: r[4], setter=lambda c,r,v: c.sheet.git('commit', '--amend', '--no-edit', '--quiet', '--message', v), width=50),
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
        return self.git_all('branch', '-r', '--contains', commitid)

    @asyncthread
    def reload(self):
        self.rows = []
        lines = self.git_iter('log', '--no-color', '-z', '--pretty=format:%s' % '%x1f'.join(self.GIT_LOG_FORMAT), self.ref)
        for record in Progress(tuple(lines)):
            self.addRow(record.split('\x1f'))

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


@GitStatus.lazy_property
def gitStashesSheet(self):
    return GitStashes('stashes', source=self)

@GitStatus.lazy_property
def gitRemotesSheet(self):
    return GitRemotes('remotes', source=self)

BaseSheet.addCommand('B', 'git-branches', 'vd.push(getRootSheet(sheet).gitBranchesSheet)', 'push branches sheet')
BaseSheet.addCommand('T', 'git-stashes', 'vd.push(getRootSheet(sheet).gitStashesSheet)', 'push stashes sheet')
BaseSheet.addCommand('R', 'git-remotes', 'vd.push(getRootSheet(sheet).gitRemotesSheet)', 'push remotes sheet')
Sheet.unbindkey('T')
Sheet.unbindkey('L')
#unbindkey('gO')

BaseSheet.addCommand('L', 'git-log', 'vd.push(GitLogSheet(branch+"_log", ref=branch, source=sheet))', 'push log of current branch')

GitStashes.addCommand('a', 'git-stash-apply', 'git("stash", "apply", cursorRow[0])', 'apply this stashed change without removing'),
GitStashes.addCommand('', 'git-stash-pop-row', 'git("stash", "pop", cursorRow[0])', 'apply this stashed change and drop it'),
GitStashes.addCommand('d', 'git-stash-drop-row', 'git("stash", "drop", cursorRow[0])', 'drop this stashed change'),
GitStashes.addCommand('b', 'git-stash-branch', 'git("stash", "branch", input("create branch from stash named: "), cursorRow[0])', 'create branch from stash'),

GitRemotes.addCommand('d', 'git-remote-delete', 'git("remote", "rm", cursorRow[0])', 'delete remote'),
GitRemotes.addCommand('a', 'git-remote-add', 'git("remote", "add", input("new remote name: ", type="remote"), input("url: ", type="url"))', 'add new remote')

#GitLogSheet.addCommand('', 'git-squash-selected', '', 'squash selected commits'),
GitLogSheet.addCommand('x', 'git-pick', 'git("cherry-pick", cursorRow[0])', 'cherry-pick this commit onto current branch'),
GitLogSheet.addCommand('gx', 'git-pick-selected', '', 'cherry-pick selected commits onto current branch'),
GitLogSheet.addCommand(None, 'git-commit-amend', 'confirm("amend this commit with the index? "); amendPrevious(cursorRow[0]); reload()', 'amend this commit with changes in the index'),
GitLogSheet.addCommand('r', 'git-reset-here', 'git("update-ref", "refs/heads/"+source, cursorRow[0])', 'reset this branch to this commit'),
