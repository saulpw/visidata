#!/usr/bin/env python3

import sys
import random
import sh
from visidata import *

from .git import *
from .merge import GitMerge
from .blame import GitBlame, GitFileSheet
from .diff import *

__version__ = 'saul.pw/vgit v0.3pre'

option('vgit_show_ignored', False, '')

GitSheet.addCommand('x', 'git-exec', 'i = input("git ", type="git"); git(*i.split())', 'execute arbitrary git command')
GitSheet.addCommand('B', 'git-branches', 'vd.push(gitBranchesSheet)', 'push branches sheet')
GitSheet.addCommand('gO', 'git-options', 'vd.push(gitOptionsSheet)', 'push sheet of git options')
GitSheet.addCommand('', 'git-push', 'git("push")', 'git push')
GitSheet.addCommand('A', 'git-abort', 'abortWhatever()', 'abort the current in-progress action')

GitSheet.addCommand('H', 'git-log', 'vd.push(LogSheet(branch+"_log", ref=branch, source=sheet))', 'push log of current branch')
GitSheet.addCommand('T', 'git-stashes', 'vd.push(gitStashesSheet)', 'push stashes sheet')
GitSheet.addCommand('R', 'git-remotes', 'vd.push(gitRemotesSheet)', 'push remotes sheet')
GitSheet.addCommand('', 'git-stash-save', 'git("stash", "save")', 'stash uncommitted changes')
GitSheet.addCommand('', 'git-stash-pop', 'git("stash", "pop")', 'apply the most recent stashed change and drop it')


class GitStashes(GitSheet):
    columns = [
        ColumnItem('stashid', 0),
        ColumnItem('start_branch', 1),
        ColumnItem('sha1', 2),
        ColumnItem('msg', 3),
    ]

    def reload(self):
        self.rows = []
        for line in git_lines('stash', 'list'):
            stashid, ctx, rest = line[:-1].split(': ', 2)
            starting_branch = ctx[len('WIP on '):]
            sha1, msg = rest.split(' ', 1)
            self.rows.append([stashid, starting_branch, sha1, msg])

GitStashes.addCommand('a', 'git-stash-apply', 'git("stash", "apply", cursorRow[0])', 'apply this stashed change without removing'),
GitStashes.addCommand('', 'git-stash-pop-row', 'git("stash", "pop", cursorRow[0])', 'apply this stashed change and drop it'),
GitStashes.addCommand('d', 'git-stash-drop-row', 'git("stash", "drop", cursorRow[0])', 'drop this stashed change'),
GitStashes.addCommand('b', 'git-stash-branch', 'git("stash", "branch", input("create branch from stash named: "), cursorRow[0])', 'create branch from stash'),
GitStashes.addCommand(ENTER, 'dive-row', 'vd.push(HunksSheet(cursorRow[0]+"_diffs", "stash", "show", "--no-color", "--patch", cursorRow[0], source=sheet))', 'show this stashed change'),

class GitUndo:
    def __init__(self, *args):
        self.cmdargs = args
    def __enter__(self):
        return self
    def __exit__(self, exctype, exc, tb):
        out = git_all(*self.cmdargs)

def randomBranchName():
    return ''.join(string.ascii_lowercase[random.randint(0, 25)] for i in range(10))


# rowdef: (commit_hash, refnames, author, author_date, body, notes)
class LogSheet(GitSheet):
    # corresponding to rowdef
    GIT_LOG_FORMAT = ['%H', '%D', '%an <%ae>', '%ai', '%B', '%N']
    rowtype = 'commits'
    columns = [
            ColumnItem('commitid', 0, width=8),
            ColumnItem('refnames', 1, width=12),
            Column('message', getter=lambda c,r: r[4], setter=lambda c,r,v: c.sheet.git('commit', '--amend', '--no-edit', '--quiet', '--message', v), width=50),
            Column('author', getter=lambda c,r: r[2], setter=lambda c,r,v: c.sheet.git('commit', '--amend', '--no-edit', '--quiet', '--author', v)),
            Column('author_date', type=date, getter=lambda c,r:r[3], setter=lambda c,r,v: c.sheet.git('commit', '--amend', '--no-edit', '--quiet', '--date', v)),
            Column('notes', getter=lambda c,r: r[5], setter=lambda c,r,v: c.sheet.git('notes', 'add', '--force', '--message', v, r[0])),
    ]
#    colorizers = [RowColorizer(5, 'cyan', lambda s,c,r,v: r and not s.inRemoteBranch(r[0]))]

    def amendPrevious(self, targethash):
        'amend targethash with current index, then rebase newer commits on top'

        prevBranch = self.git_all('rev-parse', '--symbolic-full-name', '--abbrev-ref', 'HEAD').strip()

        ret = self.git_all('commit', '-m', 'MERGE '+targethash) # commit index to viewed branch
        newChanges = self.git_all('rev-parse', 'HEAD').strip()

        ret += self.git_all('stash', 'save', '--keep-index') # stash everything else
        with GitUndo('stash', 'pop'):
            tmpBranch = randomBranchName()
            ret += self.git_all('checkout', '-b', tmpBranch) # create/switch to tmp branch
            with GitUndo('checkout', prevBranch), GitUndo('branch', '-D', tmpBranch):
                ret += self.git_all('reset', '--hard', targethash) # tmpbranch now at targethash
                ret += self.git_all('cherry-pick', '-n', newChanges)  # pick new change from original branch
                ret += self.git_all('commit', '--amend', '--no-edit')  # recommit to fix targethash (which will change)
                ret += self.git_all('rebase', '--onto', tmpBranch, 'HEAD@{1}', prevBranch)  # replay the rest

        return ret.splitlines()

    @functools.lru_cache()
    def inRemoteBranch(self, commitid):
        return git_all('branch', '-r', '--contains', commitid)

    @asyncthread
    def reload(self):
        self.rows = []
        lines = self.git_iter('log', '--no-color', '-z', '--pretty=format:%s' % '%x1f'.join(self.GIT_LOG_FORMAT), self.ref)
        for record in Progress(tuple(lines)):
            self.addRow(record.split('\x1f'))

LogSheet.addCommand(ENTER, 'dive-row', 'vd.push(getCommitSheet(cursorRow[0][:7], sheet, cursorRow[0]))', 'show this commit'),
#LogSheet.addCommand('', 'git-squash-selected', '', 'squash selected commits'),
LogSheet.addCommand('x', 'git-pick', 'git("cherry-pick", cursorRow[0])', 'cherry-pick this commit onto current branch'),
LogSheet.addCommand('gx', 'git-pick-selected', '', 'cherry-pick selected commits onto current branch'),
LogSheet.addCommand('C', 'git-commit-amend', 'confirm("amend this commit with the index? "); amendPrevious(cursorRow[0]); reload()', 'amend this commit with changes in the index'),
LogSheet.addCommand('r', 'git-reset-here', 'git("update-ref", "refs/heads/"+source, cursorRow[0])', 'reset this branch to this commit'),

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
        RowColorizer(10, 'underline', lambda s,c,r,v: r and r['current']),
#        RowColorizer(10, 'cyan', lambda s,c,r,v: r and not r['localbranch'].startswith('remotes/')),
    ]
    nKeys = 1

    @asyncthread
    def reload(self):
        self.rows = []
        branches_lines = git_lines('branch', '--list', '-vv', '--no-color', '--all')
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
            merge_base = git_all("show-branch", "--merge-base", row.localbranch, self.rootSheet.branch, _ok_code=[0,1]).strip()
            row.merge_name = git_all("name-rev", "--name-only", merge_base).strip() if merge_base else ''
            row.upstream = self.rootSheet.getBranchStatuses().get(row.localbranch)
            row.last_commit = git_all("show", "--no-patch", '--pretty=%ai', row.localbranch).strip()
            row.last_author = git_all("show", "--no-patch", '--pretty=%an', row.localbranch).strip()


GitBranches.addCommand('a', 'git-branch-create', 'git("branch", input("create branch: ", type="branch"))', 'create a new branch off the current checkout'),
GitBranches.addCommand('d', 'git-branch-delete', 'git("branch", "--delete", cursorRow.localbranch)', 'delete this branch'),
GitBranches.addCommand('e', 'git-branch-rename', 'git("branch", "-v", "--move", cursorRow.localbranch, editCell(0))', 'rename this branch'),
GitBranches.addCommand('c', 'git-checkout', 'git("checkout", cursorRow.localbranch)', 'checkout this branch'),
GitBranches.addCommand('m', 'git-branch-merge', 'git("merge", cursorRow.localbranch)', 'merge this branch into the current branch'),
GitBranches.addCommand(ENTER, 'dive-row', 'vd.push(LogSheet(cursorRow.localbranch+"_log", source=sheet, ref=cursorRow.localbranch))', 'push log of this branch'),

def getHunksSheet(parent, *files):
    return HunksSheet('hunks', 'diff',
                  '--diff-algorithm=' + options.git_diff_algo,
                  '--patch',
                  '--inter-hunk-context=2', '-U1',
                  '--no-color',
                  '--no-prefix', *[gf.filename for gf in files], source=parent)

def getStagedHunksSheet(parent, *files):
    return HunksSheet('staged_hunks', 'diff', '--cached',
                  '--diff-algorithm=' + options.git_diff_algo,
                  '--patch',
                  '--inter-hunk-context=2', '-U1',
                  '--no-color',
                  '--no-prefix', *[gf.filename for gf in files], source=parent)

def getCommitSheet(name, parent, *refids):
    return HunksSheet(name, 'show',
                  '--diff-algorithm=' + options.git_diff_algo,
                  '--patch',
                  '--inter-hunk-context=2', '-U1',
                  '--no-color',
                  '--no-prefix', *refids, source=parent)

# source is arguments to git()
class HunksSheet(GitSheet):
    columns = [
        ColumnItem('origfn', 0, width=0),
        ColumnItem('filename', 1),
        ColumnItem('context', 2),
        ColumnItem('leftlinenum', 3),
        ColumnItem('leftcount', 4),
        ColumnItem('rightlinenum', 5),
        ColumnItem('rightcount', 6),
    ]

    def __init__(self, name, *git_args, **kwargs):
        super().__init__(name, **kwargs)
        self.git_args = git_args

    def reload(self):
        def _parseStartCount(s):
            sc = s.split(',')
            if len(sc) == 2:
                return sc
            if len(sc) == 1:
                return sc[0], 1

        self.rows = []
        leftfn = ''
        rightfn = ''
        header_lines = None
        diff_started = False
        for line in git_lines(*self.git_args):
            if line.startswith('diff'):
                diff_started = True
                continue
            if not diff_started:
                continue

            if line.startswith('---'):
                header_lines = [line]  # new file
                leftfn = line[4:]
            elif line.startswith('+++'):
                header_lines.append(line)
                rightfn = line[4:]
            elif line.startswith('@@'):
                header_lines.append(line)
                _, linenums, context = line.split('@@')
                leftlinenums, rightlinenums = linenums.split()
                leftstart, leftcount = _parseStartCount(leftlinenums[1:])
                rightstart, rightcount = _parseStartCount(rightlinenums[1:])
                self.rows.append((leftfn, rightfn, context, int(leftstart), int(leftcount), int(rightstart), int(rightcount), header_lines))
                header_lines = header_lines[:2]  # keep file context
            elif line[0] in ' +-':
                self.rows[-1][-1].append(line)

HunksSheet.addCommand(ENTER, 'dive-row', 'vd.push(HunkViewer([cursorRow], source=sheet))', 'view the diff for this hunks'),
HunksSheet.addCommand('g^J', 'git-diff-selected', 'vd.push(HunkViewer(selectedRows or rows, source=sheet))', 'view the diffs for the selected hunks (or all hunks)'),
HunksSheet.addCommand('V', 'git-view-patch', 'vd.push(TextSheet("diff", "\\n".join(cursorRow[7])))', 'view the raw patch for this hunk'),
#HunksSheet.addCommand('gV', 'git-view-patch-selected', '', 'view the raw patch for selected/all hunks'),
HunksSheet.addCommand('a', 'git-apply-hunk', 'git_apply(cursorRow, "--cached")', 'apply this hunk to the index'),
#HunksSheet.addCommand('r', 'git-reverse-hunk', 'git_apply(cursorRow, "--reverse")', 'undo this hunk'),
#HunksSheet.bindkey('d', 'git-reverse-hunk')


class HunkViewer(GitSheet):
    def __init__(self, hunks, **kwargs):
        super().__init__('hunk', hunks=hunks, **kwargs)
        self.columns = [
            ColumnItem('1', 1, width=vd.windowWidth//2-1),
            ColumnItem('2', 2, width=vd.windowWidth//2-1),
        ]
        self.addColorizer(RowColorizer(4, None, HunkViewer.colorDiffRow))

    def reload(self):
        if not self.hunks:
            vd.remove(self)
            return

        fn, _, context, linenum, _, _, _, patchlines = self.hunks[0]
        self.name = '%s:%s' % (fn, linenum)
        self.rows = []
        nextDelIdx = None
        for line in patchlines[3:]:  # diff without the patch headers
            typech = line[0]
            line = line[1:]
            if typech == '-':
                self.rows.append([typech, line, None])
                if nextDelIdx is None:
                    nextDelIdx = len(self.rows)-1
            elif typech == '+':
                if nextDelIdx is not None:
                    if nextDelIdx < len(self.rows):
                        self.rows[nextDelIdx][2] = line
                        nextDelIdx += 1
                        continue

                self.rows.append([typech, None, line])
                nextDelIdx = None
            elif typech == ' ':
                self.rows.append([typech, line, line])
                nextDelIdx = None
            else:
                continue  # header

    def colorDiffRow(self, c, row, v):
        if row and row[1] != row[2]:
            if row[1] is None:
                return 'green'  # addition
            elif row[2] is None:
                return 'red'  # deletion
            else:
                return 'yellow'  # difference


HunkViewer.addCommand('2', 'git-apply-hunk', 'source.git_apply(hunks.pop(0), "--cached"); reload()', 'apply this hunk to the index and move to the next hunk'),
#HunkViewer.addCommand('1', 'git-remove-hunk', 'git_apply(hunks.pop(0), "--reverse")', 'remove this hunk from the diff'),
HunkViewer.addCommand(ENTER, 'git-skip-hunk', 'hunks.pop(0); reload()', 'move to the next hunk without applying this hunk'),
HunkViewer.addCommand('d', 'delete-line', 'source[7].pop(cursorRow[3]); reload()', 'delete a line from the patch'),


class GitGrep(GitSheet):
    rowtype = 'results' # list(file, line, line_contents)
    columns = [
        ColumnItem('filename', 0),
        ColumnItem('linenum', 1),
        ColumnItem('line', 2),
    ]
    def __init__(self, regex):
        super().__init__(regex, source=regex)

    def reload(self):
        self.rows = []
        for line in git_lines('grep', '--no-color', '-z', '--line-number', '--ignore-case', self.source):
            self.rows.append((line.split('\0')))

GitGrep.addCommand(ENTER, 'dive-row', 'vs=GitFileSheet(cursorRow[0]); vs.cursorRowIndex = int(cursorRow[1])-1; vd.push(vs).reload()', 'go to this match')
GitGrep.addCommand('^O', 'sysopen-row', 'launchExternalEditor(cursorRow[0], linenum=cursorRow[1]); reload()', 'open this file in $EDITOR')

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

GitOptions.addCommand('d', 'git-config-unset', 'git("config", "--unset", "--"+CONFIG_CONTEXTS[cursorColIndex], cursorRow[0])', 'unset this config value'),
GitOptions.addCommand('gd', 'git-config-unset-selected', 'for r in selectedRows: git("config", "--unset", "--"+CONFIG_CONTEXTS[cursorColIndex], r[0])', 'unset selected config values'),
#GitOptions.addCommand('e', 'i=(cursorVisibleColIndex or 1); visibleCols[i].setValues(sheet, [cursorRow], editCell(i)); sheet.cursorRowIndex += 1', 'edit this option'),
#GitOptions.addCommand('ge', 'i=(cursorVisibleColIndex or 1); visibleCols[i].setValues(sheet, selectedRows, input("set selected to: ", value=cursorValue))', 'edit this option for all selected rows'),
GitOptions.addCommand('a', 'git-config-add', 'git("config", "--add", "--"+CONFIG_CONTEXTS[cursorColIndex], input("option to add: "), "added")', 'add new option'),

# how to incorporate fetch/push/pull?
class GitRemotes(GitSheet):
    columns=[
            Column('remote', getter=lambda c,r: r[0], setter=lambda c,r,v: c.sheet.git('remote', 'rename', r[0], v)),
            Column('url', getter=lambda c,r: r[1], setter=lambda c,r,v: c.sheet.git('remote', 'set-url', r[0], v)),
            Column('type', getter=lambda c,r: r[2]),
    ]

    def reload(self):
        self.rows = []
        for line in git_lines('remote', '-v', 'show'):
            name, url, paren_type = line.split()
            self.rows.append((name, url, paren_type[1:-1]))

GitRemotes.addCommand('d', 'git-remote-delete', 'git("remote", "rm", cursorRow[0])', 'delete remote'),
GitRemotes.addCommand('a', 'git-remote-add', 'git("remote", "add", input("new remote name: ", type="remote"), input("url: ", type="url"))', 'add new remote')

# os.chdir(fn)
