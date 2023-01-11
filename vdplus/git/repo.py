# repo-wide sheets

import re

from visidata import *
from . import GitSheet, GitStatus, GitContext

__all__ = ['GitBranches', 'GitOptions', 'GitStashes', 'GitRemotes', 'GitLogSheet']

theme('color_vgit_unpushed', 'cyan', 'unpushed commits on log sheet')
theme('color_vgit_current_branch', 'underline', 'current branch on branches sheet')
theme('color_vgit_local_branch', 'cyan', 'color of non-remote branches')

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

class GitBranches(GitSheet):
    rowtype = 'branches'  # rowdef: AttrDict from regex (in reload below)
    columns = [
        Column('branch', getter=lambda c,r: remove_prefix(r['localbranch'], 'remotes/'), width=20),
#        Column('remote', getter=lambda c,r: r['localbranch'].startswith('remotes/') and '*' or '', width=3),
        ColumnItem('head_commitid', 'refid', width=0),
        ColumnItem('tracking', 'remotebranch'),
        ColumnItem('upstream'),
        ColumnItem('merge_base', 'merge_name', width=20),
        ColumnItem('extra', width=0),
        ColumnItem('head_commitmsg', 'msg', width=50),
        ColumnItem('last_commit', type=date),
        ColumnItem('last_author'),
    ]
    colorizers = [
        RowColorizer(10, 'color_vgit_current_branch', lambda s,c,r,v: r and r['current']),
        RowColorizer(10, 'color_vgit_local_branch', lambda s,c,r,v: r and not r['localbranch'].startswith('remotes/')),
    ]
    nKeys = 1

    @asyncthread
    def reload(self):
        self.rows = []
        branches_lines = self.git_lines('branch', '--list', '-vv', '--no-color', '--all')
        for line in branches_lines:
            if '->' in line:
                continue

            m = re.match(r'''(?P<current>\*?)\s+
                             (?P<localbranch>\S+)\s+
                             (?P<refid>\w+)\s+
                             (?:\[
                               (?P<remotebranch>[^\s\]:]+):?
                               \s*(?P<extra>.*?)
                             \])?
                             \s*(?P<msg>.*)''', line, re.VERBOSE)
            if m:
                row = AttrDict(m.groupdict())
                self.addRow(row)

        for row in Progress(self.rows):
            merge_base = self.git_all("show-branch", "--merge-base", row.localbranch, self.rootSheet.branch, _ok_code=[0,1]).strip()
            row.merge_name = self.git_all("name-rev", "--name-only", merge_base).strip() if merge_base else ''
            row.upstream = self.rootSheet.getBranchStatuses().get(row.localbranch)
            row.last_commit = self.git_all("show", "--no-patch", '--pretty=%ai', row.localbranch).strip()
            row.last_author = self.git_all("show", "--no-patch", '--pretty=%an', row.localbranch).strip()

    def openRow(self, row):
        return GitLogSheet(row.localbranch+"_log", source=self, ref=row.localbranch)


class GitOptions(GitSheet):
    CONFIG_CONTEXTS = ('local', 'local', 'global', 'system')
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.columns = [Column('option', getter=lambda c,r: r[0])]
        for i, ctx in enumerate(self.CONFIG_CONTEXTS[1:]):
            self.columns.append(Column(ctx, getter=lambda c,r, i=i: r[1][i], setter=self.config_setter(ctx)))

        self.nKeys = 1

    def config_setter(self, ctx):
        def setter(r, v):
            self.git('config', '--'+ctx, r[0], v)
        return setter

    def reload(self):
        opts = {}
        for i, ctx in enumerate(self.CONFIG_CONTEXTS[1:]):
            try:
                for line in self.git_iter('config', '--list', '--'+ctx, '-z'):
                    if line:
                        k, v = line.splitlines()
                        if k not in opts:
                            opts[k] = [None, None, None]
                        opts[k][i] = v
            except Exception:
                pass # exceptionCaught()

        self.rows = sorted(list(opts.items()))


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
def gitBranchesSheet(self):
    return GitBranches('branches', source=self)

@GitStatus.lazy_property
def gitOptionsSheet(self):
    return GitOptions('git-options', source=self)

@GitStatus.lazy_property
def gitStashesSheet(self):
    return GitStashes('stashes', source=self)

@GitStatus.lazy_property
def gitRemotesSheet(self):
    return GitRemotes('remotes', source=self)

BaseSheet.addCommand('B', 'git-branches', 'vd.push(getRootSheet(sheet).gitBranchesSheet)', 'push branches sheet')
BaseSheet.addCommand('gO', 'git-options', 'vd.push(getRootSheet(sheet).gitOptionsSheet)', 'push sheet of git options')
BaseSheet.addCommand('T', 'git-stashes', 'vd.push(getRootSheet(sheet).gitStashesSheet)', 'push stashes sheet')
BaseSheet.addCommand('R', 'git-remotes', 'vd.push(getRootSheet(sheet).gitRemotesSheet)', 'push remotes sheet')
Sheet.unbindkey('T')
Sheet.unbindkey('L')
#unbindkey('gO')

BaseSheet.addCommand('L', 'git-log', 'vd.push(GitLogSheet(branch+"_log", ref=branch, source=sheet))', 'push log of current branch')

GitBranches.addCommand('a', 'git-branch-create', 'git("branch", input("create branch: ", type="branch"))', 'create a new branch off the current checkout'),
GitBranches.addCommand('d', 'git-branch-delete', 'git("branch", "--delete", cursorRow.localbranch)', 'delete this branch'),
GitBranches.addCommand('e', 'git-branch-rename', 'git("branch", "-v", "--move", cursorRow.localbranch, editCell(0))', 'rename this branch'),
GitBranches.addCommand('c', 'git-checkout', 'git("checkout", cursorRow.localbranch)', 'checkout this branch'),
GitBranches.addCommand('m', 'git-branch-merge', 'git("merge", cursorRow.localbranch)', 'merge this branch into the current branch'),

GitStashes.addCommand('a', 'git-stash-apply', 'git("stash", "apply", cursorRow[0])', 'apply this stashed change without removing'),
GitStashes.addCommand('', 'git-stash-pop-row', 'git("stash", "pop", cursorRow[0])', 'apply this stashed change and drop it'),
GitStashes.addCommand('d', 'git-stash-drop-row', 'git("stash", "drop", cursorRow[0])', 'drop this stashed change'),
GitStashes.addCommand('b', 'git-stash-branch', 'git("stash", "branch", input("create branch from stash named: "), cursorRow[0])', 'create branch from stash'),

GitOptions.addCommand('d', 'git-config-unset', 'git("config", "--unset", "--"+CONFIG_CONTEXTS[cursorColIndex], cursorRow[0])', 'unset this config value'),
GitOptions.addCommand('gd', 'git-config-unset-selected', 'for r in selectedRows: git("config", "--unset", "--"+CONFIG_CONTEXTS[cursorColIndex], r[0])', 'unset selected config values'),
#GitOptions.addCommand('e', 'i=(cursorVisibleColIndex or 1); visibleCols[i].setValues(sheet, [cursorRow], editCell(i)); sheet.cursorRowIndex += 1', 'edit this option'),
#GitOptions.addCommand('ge', 'i=(cursorVisibleColIndex or 1); visibleCols[i].setValues(sheet, selectedRows, input("set selected to: ", value=cursorValue))', 'edit this option for all selected rows'),
GitOptions.addCommand('a', 'git-config-add', 'git("config", "--add", "--"+CONFIG_CONTEXTS[cursorColIndex], input("option to add: "), "added")', 'add new option'),

GitRemotes.addCommand('d', 'git-remote-delete', 'git("remote", "rm", cursorRow[0])', 'delete remote'),
GitRemotes.addCommand('a', 'git-remote-add', 'git("remote", "add", input("new remote name: ", type="remote"), input("url: ", type="url"))', 'add new remote')

#GitLogSheet.addCommand('', 'git-squash-selected', '', 'squash selected commits'),
GitLogSheet.addCommand('x', 'git-pick', 'git("cherry-pick", cursorRow[0])', 'cherry-pick this commit onto current branch'),
GitLogSheet.addCommand('gx', 'git-pick-selected', '', 'cherry-pick selected commits onto current branch'),
GitLogSheet.addCommand(None, 'git-commit-amend', 'confirm("amend this commit with the index? "); amendPrevious(cursorRow[0]); reload()', 'amend this commit with changes in the index'),
GitLogSheet.addCommand('r', 'git-reset-here', 'git("update-ref", "refs/heads/"+source, cursorRow[0])', 'reset this branch to this commit'),
