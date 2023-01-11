import re
from visidata import *
from .git import GitSheet
from .diff import DifferSheet

vd.option('vgit_show_ignored', False, '')
vd.option('color_vgit_staged_mod', 'green', 'files staged with modifications')
vd.option('color_vgit_staged_del', 'red', 'files staged for deletion')
vd.option('color_vgit_staged_add', 'green', 'files staged for addition')
vd.option('color_vgit_unstaged_del', '88', 'files deleted but unstaged')
vd.option('color_vgit_untracked', '237 blue', 'ignored/untracked files')


# cached by GitStatus sheets
FileStatus = namedlist('FileStatus', 'status adds dels'.split())

class GitFile:
    def __init__(self, path, gitsrc):
        self.path = path
        self.filename = path.relative_to(gitsrc)
        self.is_dir = self.path.is_dir()

    def __str__(self):
        return str(self.filename) + (self.is_dir and '/' or '')


class GitStatus(GitSheet):
    rowtype = 'files'  # rowdef: GitFile
    colorizers = [
        CellColorizer(3, 'color_vgit_staged_mod',   lambda s,c,r,v: r and c and c.name == 'staged' and s.git_status(r).status[0] == 'M'), # staged mod
        CellColorizer(1, 'color_vgit_staged_del',     lambda s,c,r,v: r and c and c.name == 'staged' and s.git_status(r).status == 'D '), # staged delete
        RowColorizer(1, 'color_vgit_staged_add',  lambda s,c,r,v: r and s.git_status(r).status in ['A ', 'M ']), # staged add/mod
        RowColorizer(1, 'color_vgit_unstaged_del',       lambda s,c,r,v: r and s.git_status(r).status[1] == 'D'), # unstaged delete
        RowColorizer(1, 'color_vgit_untracked', lambda s,c,r,v: r and s.git_status(r).status == '!!'),  # ignored
        RowColorizer(1, 'color_vgit_untracked', lambda s,c,r,v: r and s.git_status(r).status == '??'),  # untracked
    ]
    columns = [
        Column('path', getter=lambda c,r: str(r)),
        Column('status', getter=lambda c,r: c.sheet.statusText(c.sheet.git_status(r)), width=8),
        Column('status_raw', getter=lambda c,r: c.sheet.git_status(r), width=0),
        Column('staged', getter=lambda c,r: c.sheet.git_status(r).dels),
        Column('unstaged', getter=lambda c,r: c.sheet.git_status(r).adds),
        Column('type', getter=lambda c,r: r.is_dir and '/' or r.path.suffix, width=0),
        Column('size', type=int, getter=lambda c,r: filesize(r.path)),
        Column('modtime', type=date, getter=lambda c,r: modtime(r.path)),
    ]
    nKeys = 1

    def __init__(self, p):
        super().__init__('/'.join(p.parts[-2:]), source=p)
        self.branch = ''
        self.remotediff = ''  # ahead/behind status

        self._cachedStatus = {}  # [filename] -> FileStatus(['!!' or '??' status, adds, dels])

    def statusText(self, st):
        vmod = {'A': 'add', 'D': 'rm', 'M': 'mod', 'T': 'chmod', '?': 'out', '!': 'ignored', 'U': 'unmerged'}
        x, y = st.status
        if st == '??': # untracked
            return 'new'
        elif st == '!!':  # ignored
            return 'ignored'
        elif x != ' ' and y == ' ': # staged
            return vmod.get(x, x)
        elif y != ' ': # unstaged
            return vmod.get(y, y)
        else:
            return ''

    @property
    def workdir(self):
        return str(self.source)

    def git_status(self, r):
        '''return tuple of (status, adds, dels).
        status like !! ??
        adds and dels are lists of additions and deletions.
        '''
        if not r:
            return None
        ret = self._cachedStatus.get(r.filename, None)
        if not ret:
            ret = FileStatus(["//", None, None])
            self._cachedStatus[r.filename] = ret

        return ret

    def ignored(self, fn):
        if options.vgit_show_ignored:
            return False

        if fn in self._cachedStatus:
            return self._cachedStatus[fn].status == '!!'

        return False


    def getBranchStatuses(self):
        ret = {}  # localbranchname -> "+5/-2"
        for branch_status in self.git_lines('for-each-ref', '--format=%(refname:short) %(upstream:short) %(upstream:track)', 'refs/heads'):
            m = re.search(r'''(\S+)\s*
                              (\S+)?\s*
                              (\[
                              (ahead.(\d+)),?\s*
                              (behind.(\d+))?
                              \])?''', branch_status, re.VERBOSE)
            if not m:
                status('unmatched branch status: ' + branch_status)
                continue

            localb, remoteb, _, _, nahead, _, nbehind = m.groups()
            if nahead:
                r = '+%s' % nahead
            else:
                r = ''
            if nbehind:
                if r:
                    r += '/'
                r += '-%s' % nbehind
            ret[localb] = r

        return ret

    @asyncthread
    def reload(self):
        files = [GitFile(p, self.source) for p in self.source.iterdir() if p.name not in ('.git')]  # files in working dir

        filenames = dict((gf.filename, gf) for gf in files)
        self.branch = self.git_all('rev-parse', '--abbrev-ref', 'HEAD').strip()
        self.remotediff = self.getBranchStatuses().get(self.branch, 'no branch')

        self.rows = []
        self._cachedStatus.clear()
        for fn in self.git_iter('ls-files', '-z'):
            self._cachedStatus[fn] = FileStatus(['  ', None, None])  # status, adds, dels

        for status_line in self.git_iter('status', '-z', '-unormal', '--ignored'):
            if status_line:
                if status_line[2:3] == ' ':
                    st, fn = status_line[:2], status_line[3:]
                else:
                    fn = status_line
                    st = '//'
                gf = GitFile(self.source.joinpath(fn), self.source)
                self._cachedStatus[gf.filename] = FileStatus([st, None, None])
                if gf.filename not in filenames:
                    if not self.ignored(gf.filename):
                        self.addRow(gf)

        for line in self.git_iter('diff-files', '--numstat', '-z'):
            if not line: continue
            adds, dels, fn = line.split('\t')
            if fn not in self._cachedStatus:
                self._cachedStatus[fn] = FileStatus(['##', None, None])
            cs = self._cachedStatus[fn]
            cs.adds = '+%s/-%s' % (adds, dels)

        for line in self.git_iter('diff-index', '--cached', '--numstat', '-z', 'HEAD'):
            if not line: continue
            adds, dels, fn = line.split('\t')
            if fn not in self._cachedStatus:
                self._cachedStatus[fn] = FileStatus(['$$', None, None])
            cs = self._cachedStatus[fn]
            cs.dels = '+%s/-%s' % (adds, dels)

        for fn, gf in filenames.items():
            if not self.ignored(gf.filename):
                self.addRow(gf)

        self.orderBy(None, self.columns[-1], reverse=True)

        self.recalc()  # erase column caches

GitStatus.addCommand('a', 'git-add', 'git("add", cursorRow.filename)', 'add this new file or modified file to staging'),
GitStatus.addCommand('m', 'git-mv', 'git("mv", cursorRow.filename, input("rename file to: ", value=cursorRow.filename))', 'rename this file'),
GitStatus.addCommand('d', 'git-rm', 'git("rm", cursorRow.filename)', 'stage this file for deletion'),
GitStatus.addCommand('r', 'git-reset', 'git("reset", "HEAD", cursorRow.filename)', 'reset/unstage this file'),
GitStatus.addCommand('c', 'git-checkout', 'git("checkout", cursorRow.filename)', 'checkout this file'),
GitStatus.addCommand('ga', 'git-add-selected', 'git("add", *[r.filename for r in selectedRows])', 'add all selected files to staging'),
GitStatus.addCommand('gd', 'git-rm-selected', 'git("rm", *[r.filename for r in selectedRows])', 'delete all selected files'),
GitStatus.addCommand(None, 'git-commit', 'git("commit", "-m", input("commit message: "))', 'commit changes'),
GitStatus.addCommand('V', 'open-file', 'vd.push(TextSheet(cursorRow.filename, source=Path(cursorRow.filename)))', 'open file'),
GitStatus.addCommand(None, 'ignore-file', 'open(workdir+"/.gitignore", "a").write(cursorRow.filename+"\\n"); reload()', 'add file to toplevel .gitignore'),
GitStatus.addCommand(None, 'ignore-wildcard', 'open(workdir+"/.gitignore", "a").write(input("add wildcard to .gitignore: "))', 'add input line to toplevel .gitignore'),


GitStatus.addCommand('z^J', 'diff-file-staged', 'vd.push(getStagedHunksSheet(sheet, cursorRow))', 'push staged diffs for this file'),
GitStatus.addCommand('gz^J', 'diff-selected-staged', 'vd.push(getStagedHunksSheet(sheet, *(selectedRows or rows)))', 'push staged diffs for selected files or all files'),

BaseSheet.addCommand('^[g', 'menu-git', 'pressMenu("Git")', 'open Git submenu')

vd.addMenuItem('Git', 'View staged changes', 'current file', 'diff-file-staged')
vd.addMenuItem('Git', 'View staged changes', 'selected files', 'staged changes', 'diff-selected-staged')
vd.addMenuItem('Git', 'Stage', 'current file', 'git-add')
vd.addMenuItem('Git', 'Stage', 'selected files', 'git-add-selected')
vd.addMenuItem('Git', 'Unstage', 'current file', 'git-reset')
vd.addMenuItem('Git', 'Unstage', 'selected files', 'git-reset-selected')
vd.addMenuItem('Git', 'Rename file', 'git-mv')
vd.addMenuItem('Git', 'Delete', 'file', 'git-rm')
vd.addMenuItem('Git', 'Delete', 'selected files', 'git-rm-selected')
vd.addMenuItem('Git', 'Ignore', 'file', 'ignore-file')
vd.addMenuItem('Git', 'Ignore', 'wildcard', 'ignore-wildcard')
vd.addMenuItem('Git', 'Commit staged changes', 'git-checkout')
vd.addMenuItem('Git', 'Revert unstaged changes', 'current file', 'git-checkout')

vd.addMenuItem('View', 'Revert unstaged changes', 'current file', 'git-checkout')


@GitStatus.api
def dive_rows(sheet, *gitfiles):
    if len(gitfiles) == 1:
        gf = gitfiles[0]
        if gf.is_dir:
            vs = GitStatus(gf.path)
        else:
            vs = DifferSheet(gf, "HEAD", "index", "working", source=sheet)
    else:
        vs = getHunksSheet(sheet, *gitfiles)
    vd.push(vs)

GitStatus.addCommand(ENTER, 'dive-row', 'sheet.dive_rows(cursorRow)', 'push unstaged diffs for this file or dive into directory'),
GitStatus.addCommand('g'+ENTER, 'dive-rows', 'sheet.dive_rows(*(selectedRows or rows))', 'push unstaged diffs for selected files or all files'),
GitStatus.addCommand('^O', 'sysopen-row', 'launchExternalEditorPath(Path(cursorRow.path))', 'open this file in $EDITOR')
