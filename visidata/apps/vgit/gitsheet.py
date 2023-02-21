import io

from visidata import AttrDict, vd, Path, asyncthread, BaseSheet, Sheet

vd.option('vgit_logfile', '', 'file to log all git commands run by vgit')


GitCmd = AttrDict   # sheet, command, output

class GitContext:
    def _git_args(self):
        'Return list of extra args to all git commands'

        def _getRepoPath(p):
            'Return path at p or above which has .git subdir'
            if p.joinpath('.git').exists():
                return p
            if getattr(p, 'given', None) in ['/','']:
                return None
            return _getRepoPath(p.resolve().parent)

        worktree = _getRepoPath(self.gitRootSheet.source)  # Path
        if not worktree:
            return []

        return [
            '--git-dir', str(worktree.joinpath('.git')),
            '--work-tree', str(worktree),
        ]

    def maybeloggit(self, *args, **kwargs):
        import sh

        if self.options.vgit_logfile:
            cmdstr = 'git ' + ' '.join(args)
            with open(self.options.vgit_logfile, 'a') as fp:
                fp.write(cmdstr + '\n')

        return sh.git(*args, **kwargs)

    def loggit(self, *args, **kwargs):
        cmdstr = 'git ' + ' '.join(str(x) for x in args)
        gcmd = GitCmd(sheet=vd.sheet, command=cmdstr, output=None)

        gcmd.output = self.maybeloggit(*args, **kwargs)

        return gcmd.output

    def git_lines(self, *args, **kwargs):
        'Generator of stdout lines from given git command'
        import sh
        err = io.StringIO()
        git = self.loggit
        try:
            for line in git('--no-pager',
                            *self._git_args(),
                            *args,
                            _decode_errors='replace',
                            _iter=True,
                            _bg_exc=False,
                            _err=err,
                            **kwargs):
                yield line[:-1]  # remove EOL

        except sh.ErrorReturnCode as e:
            vd.error('git '+' '.join(args), 'error=%s' % e.exit_code)

        errlines = err.getvalue().splitlines()
        if errlines:
            vd.warning('git stderr: ' + '\n'.join(errlines))

    @asyncthread
    def modifyGit(self, *args, **kwargs):
        'Run git command that modifies the repo'
        for line in self.git_lines(*args, **kwargs):
            vd.status(line)

        if isinstance(self.source, GitSheet):
            self.source.reload()

        self.reload()

    @property
    def gitRootSheet(self):
        if isinstance(self.source, GitSheet):
            return self.source.gitRootSheet
        return self

    @property
    def gitPath(self):
        return Path('.git')  # XXX from git root


class GitSheet(GitContext, Sheet):
    def git_exec(self, cmdstr):
        vd.push(TextSheet(cmdstr, source=sheet.git_lines(*cmdstr.split())))


GitSheet.options.disp_note_none = ''
BaseSheet.addCommand('gi', 'git-exec', 'sheet.git_exec(input("gi", type="git"))')

GitSheet.addCommand('Alt+g', 'menu-git', 'pressMenu("Git")', '')

vd.addMenuItems('''
    Git > Execute command > git-exec
''')
