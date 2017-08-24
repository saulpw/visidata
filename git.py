import sh

from vdtui import *

git_commands = []

def git_all(*args, **kwargs):
    'Return entire output of git command.'
    try:
        out = sh.git(*args, _err_to_out=True, _decode_errors='replace', **kwargs)
    except sh.ErrorReturnCode as e:
        status('exit_code=%s' % e.exit_code)
        out = e.stdout

    return out


def git_lines(*args, **kwargs):
    'Generator of stdout lines from given git command'
    err = io.StringIO()
    try:
        for line in sh.git('--no-pager', _err=err, *args, _decode_errors='replace', _iter=True, _bg_exc=False, **kwargs):
            yield line[:-1]  # remove EOL
    except sh.ErrorReturnCode as e:
        status('exit_code=%s' % e.exit_code)

    errlines = err.getvalue().splitlines()
    if len(errlines) < 3:
        for line in errlines:
            status(line)
    else:
        vd().push(TextSheet('git ' + ' '.join(args), errlines))


def git_iter(sep, *args, **kwargs):
    'Generator of chunks of stdout from given git command, delineated by sep character'
    bufsize = 512
    err = io.StringIO()

    chunks = []
    try:
      for data in sh.git('--no-pager', *args, _decode_errors='replace', _out_bufsize=bufsize, _iter=True, _err=err, **kwargs):
        while True:
            i = data.find(sep)
            if i < 0:
                break
            chunks.append(data[:i])
            data = data[i+1:]
            yield ''.join(chunks)
            chunks.clear()

        chunks.append(data)
    except sh.ErrorReturnCode as e:
        status('exit_code=%s' % e.exit_code)

    r = ''.join(chunks)
    if r:
        yield r

    errlines = err.getvalue().splitlines()
    if len(errlines) < 3:
        for line in errlines:
            status(line)
    else:
        vd().push(TextSheet('git ' + ' '.join(args), errlines))


class GitFile:
    def __init__(self, f, gitsrc):
        self.path = f if isinstance(f, Path) else Path(f)
        self.filename = self.path.relpath(str(gitsrc) + '/')
        self.is_dir = self.path.is_dir()

    def __str__(self):
        return self.filename + (self.is_dir and '/' or '')


class GitSheet(Sheet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_args = []
        self.command('f', 'extra_args.append("--force"); status("--force next git command")', 'add --force to next git command')

    @async
    def git(self, *args, **kwargs):
        args = list(args) + self.extra_args
        self.extra_args.clear()

        git_commands.append('git ' + ' '.join(args))

        for line in git_lines(*args, **kwargs):
            status(line)

        gitStatusSheet.reload()

        if self.sources and isinstance(self.sources[0], GitSheet):
            self.sources[0].reload()

        self.reload()

    @staticmethod
    def inProgress():
        if Path('.git/rebase-merge').exists() or Path('.git/rebase-apply/rebasing').exists():
            return 'rebasing'
        elif Path('.git/rebase-apply').exists():
            return 'applying'
        elif Path('.git/CHERRY_PICK_HEAD').exists():
            return 'cherry-picking'
        elif Path('.git/MERGE_HEAD').exists():
            return 'merging'
        elif Path('.git/BISECT_LOG').exists():
            return 'bisecting'
        return ''


    def abortWhatever(self):
        inp = self.inProgress()
        if inp.startswith('cherry-pick'):
            self.git('cherry-pick', '--abort')
        elif inp.startswith('merg'):
            self.git('merge', '--abort')
        elif inp.startswith('bisect'):
            self.git('bisect', 'reset')
        elif inp.startswith('rebas') or inp.startswith('apply'):
            self.git('rebase', '--abort')  # or --quit?
        else:
            status('nothing to abort')

    def leftStatus(self):
        inp = self.inProgress()
        ret = ('[%s] ' % inp) if inp else ''
        ret += '‹%s%s› ' % (gitStatusSheet.branch, gitStatusSheet.remotediff)

        return ret + super().leftStatus()

    def git_apply(self, hunk, *args):
        self.git("apply", "-p0", "-", *args, _in="\n".join(hunk[7]) + "\n")
        status('applied hunk (lines %s-%s)' % (hunk[3], hunk[3]+hunk[4]))


# each row is a GitFile
class GitStatus(GitSheet):
    def __init__(self, p):
        super().__init__(p.relpath(''), p)
        self.branch = ''
        self.remotediff = ''  # ahead/behind status

        self.columns = [Column('path', getter=lambda r,s=self: str(r)),
                      Column('status', getter=lambda r,s=self: s.statusText(s.git_status(r)), width=8),
                      Column('staged', getter=lambda r,s=self: s.git_status(r)[2]),
                      Column('unstaged', getter=lambda r,s=self: s.git_status(r)[1]),
                      Column('type', getter=lambda r: r.is_dir and '/' or r.path.suffix, width=0),
                      Column('size', type=int, getter=lambda r: r.path.filesize),
                      Column('mtime', type=date, getter=lambda r: r.path.stat().st_mtime),
                    ]

        self.addColorizer('row', 3, GitStatus.rowColor)
        self.addColorizer('row', 6, lambda s,c,r,v: 'red underline' if 'U' in s.git_status(r)[0] else None)

        self.command('a', 'git("add", cursorRow.filename)', 'add this new file or modified file to staging')
        self.command('m', 'git("mv", cursorRow.filename, input("rename file to: ", value=cursorRow.filename))', 'rename this file')
        self.command('d', 'git("rm", cursorRow.filename)', 'stage this file for deletion')
        self.command('r', 'git("reset", "HEAD", cursorRow.filename)', 'reset/unstage this file')
        self.command('c', 'git("checkout", cursorRow.filename)', 'checkout this file')
        self.command('ga', 'git("add", *[r.filename for r in selectedRows])', 'add all selected files to staging')
        self.command('gd', 'git("rm", *[r.filename for r in selectedRows])', 'delete all selected files')
        self.command('C', 'git("commit", "-m", input("commit message: "))', 'commit changes')
        self.command('V', 'vd.push(TextSheet(cursorRow.filename, Path(cursorRow.filename)))', 'open file')
        self.command('i', 'open(workdir+"/.gitignore", "a").write(cursorRow.filename+"\\n"); reload()', 'add file to toplevel .gitignore')
        self.command('gi', 'open(workdir+"/.gitignore", "a").write(input("add wildcard to .gitignore: "))', 'add input line to toplevel .gitignore')  # path, filename

        self.command(ENTER, 'vd.push(getHunksSheet(sheet, cursorRow))', 'push unstaged diffs for this file')
        self.command('g^J', 'vd.push(getHunksSheet(sheet, *(selectedRows or rows)))', 'push unstaged diffs for selected files or all files')

        self.command('g/', 'vd.push(GitGrep(input("git grep: ")))', 'find in all files')

        self.command('z^J', 'vd.push(getStagedHunksSheet(sheet, cursorRow))', 'push staged diffs for this file')
        self.command(['zg^J', 'gz^J'], 'vd.push(getStagedHunksSheet(sheet, *(selectedRows or rows)))', 'push staged diffs for selected files or all files')

#        self.command('2', 'vd.push(GitMerge(cursorRow))', 'push merge for this file')
        self.command('L', 'vd.push(GitBlame(cursorRow))', 'push blame for this file')

        self._cachedStatus = {}

    def statusText(self, st):
        vmod = {'A': 'add', 'D': 'rm', 'M': 'mod', 'T': 'chmod', '?': 'out', '!': 'ignored', 'U': 'unmerged'}
        x, y = st[0]
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

    def rowColor(self, c, row, v):
        st = self.git_status(row)[0]
        x, y = st
        if st == '??': # untracked
            return 'yellow'
        elif st == '!!':  # ignored
            return '237 blue'
        elif x in 'AMD' and y == ' ': # staged add/mod/rm
            return 'green'
        elif y in 'AMD': # unstaged add/mod/rm
            return 'red'

        return 'white'

    def git_status(self, r):
        return self._cachedStatus.get(r.filename, ["//", None, None])

    def ignored(self, fn):
        if options.vgit_show_ignored:
            return False

        if fn in self._cachedStatus:
            return self._cachedStatus[fn][0] == '!!'

        return False


    @staticmethod
    def getBranchStatuses():
        ret = {}  # localbranchname -> "+5/-2"
        for branch_status in git_lines('for-each-ref', '--format=%(refname:short) %(upstream:short) %(upstream:track)', 'refs/heads'):
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

    @async
    def reload(self):
        files = [GitFile(p, self.source) for p in self.source.iterdir() if p.name not in ('.git', '..')]  # files in working dir

        filenames = dict((gf.filename, gf) for gf in files)

        self.branch = git_all('rev-parse', '--abbrev-ref', 'HEAD').strip()
        self.remotediff = self.getBranchStatuses().get(self.branch, 'no branch')

        self.rows = []
        self._cachedStatus.clear()
        for fn in git_iter('\0', 'ls-files', '-z'):
            self._cachedStatus[fn] = ['  ', None, None]  # status, adds, dels

        for status_line in git_iter('\0', 'status', '-z', '-unormal', '--ignored'):
            if status_line:
                st = status_line[:2]
                gf = GitFile(status_line[3:], self.source)
                self._cachedStatus[gf.filename] = [st, None, None]
                if gf.filename not in filenames:
                    if not self.ignored(gf.filename):
                        self.rows.append(gf)

        for line in git_iter('\0', 'diff-files', '--numstat', '-z'):
            if not line: continue
            adds, dels, fn = line.split('\t')
            if fn not in self._cachedStatus:
                self._cachedStatus[fn] = ['##', None, None]
            cs = self._cachedStatus[fn]
            cs[1] = '+%s/-%s' % (adds, dels)

        for line in git_iter('\0', 'diff-index', '--cached', '--numstat', '-z', 'HEAD'):
            if not line: continue
            adds, dels, fn = line.split('\t')
            if fn not in self._cachedStatus:
                self._cachedStatus[fn] = ['$$', None, None]
            cs = self._cachedStatus[fn]
            cs[2] = '+%s/-%s' % (adds, dels)

        self.rows.extend(gf for fn, gf in filenames.items() if not self.ignored(gf.filename))

        self.rows.sort(key=lambda r,col=self.columns[-1]: col.getValue(r), reverse=True)  # sort by -mtime

        self.recalc()  # erase column caches

gitStatusSheet = GitStatus(Path('.'))

addGlobals(globals())
