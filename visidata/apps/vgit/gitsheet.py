import io

from visidata import AttrDict, vd, Path, asyncthread, Sheet


class GitContext:
    def _git_args(self):
        'Return list of extra args to all git commands'

        worktree = self.gitPath
        if not worktree:
            return []

        return [
            '--git-dir', str(worktree.joinpath('.git')),
            '--work-tree', str(worktree),
        ]

    def git(self, *args, **kwargs):
        'For non-modifying commands; not logged except in debug mode'
        sh = vd.importExternal('sh')
        vd.debug('git ' + ' '.join(str(x) for x in args))
        return sh.git(*args, **kwargs)

    def loggit(self, *args, **kwargs):
        'Run git command with *args*, and post a status message.'
        import sh
        vd.warning('git ' + ' '.join(str(x) for x in args))
        return sh.git(*args, **kwargs)

    def git_all(self, *args, **kwargs):
        'Return entire output of git command.'
        sh = vd.importExternal('sh')
        try:
            cmd = self.git('--no-pager',
                      *self._git_args(),
                      *args,
                      _decode_errors='replace',
                      **kwargs)
            out = cmd.stdout
        except sh.ErrorReturnCode as e:
            vd.status('git '+' '.join(args), 'error=%s' % e.exit_code)
            out = e.stdout

        out = out.decode('utf-8')

        return out

    def git_lines(self, *args, **kwargs):
        'Generator of stdout lines from given git command'
        sh = vd.importExternal('sh')
        err = io.StringIO()
        try:
            for line in self.git('--no-pager',
                            *self._git_args(),
                            *args,
                            _decode_errors='replace',
                            _iter=True,
                            _bg_exc=False,
                            _err=err,
                            **kwargs):
                yield line[:-1]  # remove EOL

        except sh.ErrorReturnCode as e:
            vd.warning('git '+' '.join(map(str, args)), 'error=%s' % e.exit_code)

        errlines = err.getvalue().splitlines()
        if errlines:
            vd.warning('git stderr: ' + '\n'.join(errlines))

    def git_iter(self, *args, sep='\0', **kwargs):
        'Generator of chunks of stdout from given git command, delineated by sep character'
        sh = vd.importExternal('sh')
        err = io.StringIO()

        bufsize = 512
        chunks = []
        try:
          for data in self.git('--no-pager',
                          *self._git_args(),
                          *args,
                          _decode_errors='replace',
                          _out_bufsize=bufsize,
                          _iter=True,
                          _err=err,
                          **kwargs):
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
            vd.error('git '+' '.join(args), 'error=%s' % e.exit_code)

        if chunks:
            yield ''.join(chunks)

        errlines = err.getvalue().splitlines()
        if errlines:
            vd.warning('git stderr: ' + '\n'.join(errlines))

    @asyncthread
    def modifyGit(self, *args, **kwargs):
        'Run git command that modifies the repo'
        vd.warning('git ' + ' '.join(str(x) for x in args))
        ret = self.git_all(*args, **kwargs)
        vd.status(ret)

        if isinstance(self.source, GitSheet):
            self.source.reload()

        self.reload()

    @property
    def gitRootSheet(self):
        if isinstance(self.source, GitSheet):
            return self.source.gitRootSheet
        return self


class GitSheet(GitContext, Sheet):
    def git_exec(self, cmdstr):
        vd.push(TextSheet(cmdstr, source=sheet.git_lines(*cmdstr.split())))

@GitSheet.lazy_property
def gitPath(self):
    'Return Path of git root (nearest ancestor directory with a .git/)'
    def _getRepoPath(p):
        'Return path at p or above which has .git subdir'
        if p.joinpath('.git').exists():
            return p
        if str(p) in ['/','']:
            return None
        return _getRepoPath(p.resolve().parent)

    p = _getRepoPath(self.gitRootSheet.source)
    if p:
       return p/'.git'


@GitSheet.lazy_property
def branch(self):
    return self.rogit('rev-parse', '--abbrev-ref', 'HEAD').strip()


GitSheet.options.disp_note_none = ''
GitSheet.options.disp_status_fmt = '{sheet.progressStatus}‹{sheet.branchStatus}› {sheet.name}| '
GitSheet.addCommand('gi', 'git-exec', 'sheet.git_exec(input("gi", type="git"))')

GitSheet.addCommand('Alt+g', 'menu-git', 'pressMenu("Git")', '')

vd.addMenuItems('''
    Git > Execute command > git-exec
''')
