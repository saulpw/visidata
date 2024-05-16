from visidata import vd, Column, VisiData, ItemColumn, Path, AttrDict, BaseSheet, IndexSheet
from visidata import RowColorizer, CellColorizer
from visidata import filesize, modtime, date

from .gitsheet import GitSheet
#from .diff import DifferSheet

vd.option('vgit_show_ignored', False, 'show ignored files on git status')
vd.theme_option('color_git_staged_mod', 'green', 'color of files staged with modifications')
vd.theme_option('color_git_staged_add', 'green', 'color of files staged for addition')
vd.theme_option('color_git_staged_del', 'red', 'color of files staged for deletion')
vd.theme_option('color_git_unstaged_del', 'on 88', 'color of files deleted but unstaged')
vd.theme_option('color_git_untracked', '243 blue', 'color of ignored/untracked files')


@VisiData.api
def git_status(vd, p, args, **kwargs):
    vs = GitStatus('/'.join(p.parts[-2:]), source=p)
    if not vs.gitRootPath:
        return vd.git_repos(p, [])
    return vs

class GitFile:
    def __init__(self, path, gitsrc):
        self.path = path
        self.filename = path.relative_to(gitsrc)
        self.is_dir = self.path.is_dir()

    def __str__(self):
        return str(self.filename) + (self.is_dir and '/' or '')

class GitStatus(GitSheet):
    rowtype = 'files'  # rowdef: GitFile
    guide = '''
        # git status
        An overview of the local git checkout.

        - `Enter` to open diff of file (`git diff`)
        - `a` to stage changes in file (`git add`)
        - `r` to unstage changes in file (`git reset`)
        - `c` to revert all unstaged changes in file (`git checkout`)
        - `d` to stage the entire file for deletion (`git rm`)
        - `z Ctrl+S` to commit staged changes (`git commit`)
    '''

    columns = [
        Column('path', width=40, getter=lambda c,r: str(r)),
        Column('status', getter=lambda c,r: c.sheet.statusText(c.sheet.git_status(r)), width=8),
        Column('status_raw', getter=lambda c,r: c.sheet.git_status(r), width=0),
        Column('staged', getter=lambda c,r: c.sheet.git_status(r).dels),
        Column('unstaged', getter=lambda c,r: c.sheet.git_status(r).adds),
        Column('type', getter=lambda c,r: r.is_dir() and '/' or r.suffix, width=0),
        Column('size', type=int, getter=lambda c,r: filesize(r)),
        Column('modtime', type=date, getter=lambda c,r: modtime(r)),
    ]
    nKeys = 1

    colorizers = [
        CellColorizer(3, 'color_git_staged_mod',   lambda s,c,r,v: r and c and c.name == 'staged' and s.git_status(r).status[0] == 'M'), # staged mod
        CellColorizer(1, 'color_git_staged_del',     lambda s,c,r,v: r and c and c.name == 'staged' and s.git_status(r).status == 'D '), # staged delete
        RowColorizer(1, 'color_git_staged_add',  lambda s,c,r,v: r and s.git_status(r).status in ['A ', 'M ']), # staged add/mod
        RowColorizer(1, 'color_git_unstaged_del',       lambda s,c,r,v: r and s.git_status(r).status[1] == 'D'), # unstaged delete
        RowColorizer(3, 'color_git_untracked', lambda s,c,r,v: r and s.git_status(r).status == '!!'),  # ignored
        RowColorizer(1, 'color_git_untracked', lambda s,c,r,v: r and s.git_status(r).status == '??'),  # untracked
    ]

    def statusText(self, st):
        vmod = {'A': 'add', 'D': 'rm', 'M': 'mod', 'T': 'chmod', '?': '', '!': 'ignored', 'U': 'unmerged'}
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

        fn = str(r)
        ret = self._cachedStatus.get(fn, None)
        if not ret:
            ret = AttrDict(status='??')
            self._cachedStatus[fn] = ret

        return ret

    def ignored(self, fn):
        if self.options.vgit_show_ignored:
            return False

        if fn in self._cachedStatus:
            return self._cachedStatus[fn].status == '!!'

        return False

    @property
    def remotediff(self):
        return self.gitBranchStatuses.get(self.branch, 'no branch')

    def iterload(self):
        files = [GitFile(p, self.source) for p in self.source.iterdir() if p.stem not in ('.git')]  # files in working dir

        filenames = dict((gf.filename, gf) for gf in files)

        self._cachedStatus.clear()
        for fn in self.git_iter('ls-files', '-z'):
            self._cachedStatus[fn] = AttrDict(status='  ')

        for line in self.git_iter('status', '-z', '-unormal', '--ignored'):
            if not line: continue

            if line[2:3] == ' ':
                st, fn = line[:2], line[3:]
            else:
                fn = line
                st = '??'  # untracked file

            self._cachedStatus[fn] = AttrDict(status=st)
            if not self.ignored(fn):
                yield Path(fn)

        for line in self.git_iter('diff-files', '--numstat', '-z'):
            if not line: continue
            adds, dels, fn = line.split('\t')
            if fn not in self._cachedStatus:
                self._cachedStatus[fn] = AttrDict(status='##')
            cs = self._cachedStatus[fn]
            cs.adds = '+%s/-%s' % (adds, dels)

        for line in self.git_iter('diff-index', '--cached', '--numstat', '-z', 'HEAD'):
            if not line: continue
            adds, dels, fn = line.split('\t')
            if fn not in self._cachedStatus:
                self._cachedStatus[fn] = AttrDict(status='$$')
            cs = self._cachedStatus[fn]
            cs.dels = '+%s/-%s' % (adds, dels)

        self.orderBy(None, self.columns[-1], reverse=True)

        self.recalc()  # erase column caches

    def openRow(self, row):
        'Open unstaged diffs for this file, or dive into directory'
        if row.is_dir:
            return GitStatus(row.path)
        else:
            return DifferSheet(row, "HEAD", "index", "working", source=sheet)

    def openRows(self, rows):
        'Open unstaged hunks for selected rows'
        return getHunksSheet(sheet, *rows)


@GitStatus.lazy_property
def _cachedStatus(self):
    return {}  # [filename] -> AttrDict(status='xx', adds=, dels=)


GitStatus.addCommand('a', 'git-add', 'loggit("add", cursorRow.filename)', 'add this new file or modified file to staging')
#GitStatus.addCommand('m', 'git-mv', 'loggit("mv", cursorRow.filename, input("rename file to: ", value=cursorRow.filename))', 'rename this file')
GitStatus.addCommand('d', 'git-rm', 'loggit("rm", cursorRow.filename)', 'stage this file for deletion')
GitStatus.addCommand('r', 'git-reset', 'loggit("reset", "HEAD", cursorRow.filename)', 'reset/unstage this file')
GitStatus.addCommand('c', 'git-checkout', 'loggit("checkout", cursorRow.filename)', 'checkout this file')
GitStatus.addCommand('ga', 'git-add-selected', 'loggit("add", *[r for r in selectedRows])', 'add all selected files to staging')
GitStatus.addCommand('gd', 'git-rm-selected', 'loggit("rm", *[r for r in selectedRows])', 'delete all selected files')
GitStatus.addCommand(None, 'git-commit', 'loggit("commit", "-m", input("commit message: "))', 'commit changes')
GitStatus.addCommand(None, 'git-ignore-file', 'open(rootPath/".gitignore", "a").write(cursorRow.filename+"\\n"); reload()', 'add file to toplevel .gitignore')
GitStatus.addCommand(None, 'git-ignore-wildcard', 'open(rootPath/.gitignore, "a").write(input("add wildcard to .gitignore: "))', 'add input line to toplevel .gitignore')


#GitStatus.addCommand('z^J', 'diff-file-staged', 'vd.push(getStagedHunksSheet(sheet, cursorRow))', 'push staged diffs for this file')
#GitStatus.addCommand('gz^J', 'diff-selected-staged', 'vd.push(getStagedHunksSheet(sheet, *(selectedRows or rows)))', 'push staged diffs for selected files or all files')
#GitStatus.addCommand('^O', 'sysopen-row', 'launchExternalEditorPath(Path(cursorRow.path))', 'open this file in $EDITOR')


vd.addMenuItems('''
    Git > View staged changes > current file > diff-file-staged
    Git > View staged changes > selected files > staged changes > diff-selected-staged
    Git > Stage > current file > git-add
    Git > Stage > selected files > git-add-selected
    Git > Unstage > current file > git-reset
    Git > Unstage > selected files > git-reset-selected
    Git > Rename file > git-mv
    Git > Delete > file > git-rm
    Git > Delete > selected files > git-rm-selected
    Git > Ignore > file > ignore-file
    Git > Ignore > wildcard > ignore-wildcard
    Git > Commit staged changes > git-commit
    Git > Revert unstaged changes > current file > git-checkout
''')
