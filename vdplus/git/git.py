import os.path
import sh
import io

from visidata import *
from visidata import namedlist


theme('disp_status_fmt', '{sheet.progressStatus}‹{sheet.branchStatus}› {sheet.name}| ', 'status line prefix')

class GitCmdLog(Sheet):
    rowtype = 'git commands'  # rowdef: GitCmd
    columns = [
        ColumnAttr('sheet'),
        ColumnAttr('command'),
        ColumnAttr('output.stdout'),
        ColumnAttr('output.stderr'),
    ]
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.rows = []


    def openRow(self, row):
        'open output of this command'
        return TextSheet(row[0], source=row[1])


@VisiData.lazy_property
def gitcmdlog(vd):
    return GitCmdLog('gitcmdlog')


def maybeloggit(*args, **kwargs):
    if options.vgit_logfile:
        cmdstr = 'git ' + ' '.join(args)
        with open(options.vgit_logfile, 'a') as fp:
            fp.write(cmdstr + '\n')

    return sh.git(*args, **kwargs)


def git_all(*args, git=loggit, **kwargs):
    'Return entire output of git command.'

    try:
        cmd = git('--no-pager', *args, _decode_errors='replace', **kwargs)
        out = cmd.stdout
    except sh.ErrorReturnCode as e:
        vd.status('git '+' '.join(args), 'error=%s' % e.exit_code)
        out = e.stdout

    out = out.decode('utf-8')

    return out


def git_lines(*args, git=loggit, **kwargs):
    'Generator of stdout lines from given git command'
    err = io.StringIO()
    try:
        for line in git('--no-pager', _err=err, *args, _decode_errors='replace', _iter=True, _bg_exc=False, **kwargs):
            yield line[:-1]  # remove EOL
    except sh.ErrorReturnCode as e:
        vd.status('git '+' '.join(args), 'error=%s' % e.exit_code)

    errlines = err.getvalue().splitlines()
    if len(errlines) < 3:
        for line in errlines:
            vd.status('stderr: '+line)
    else:
        vd.push(TextSheet('git ' + ' '.join(args), source=errlines))


def git_iter(*args, git=loggit, sep='\0', **kwargs):
    'Generator of chunks of stdout from given git command, delineated by sep character'
    bufsize = 512
    err = io.StringIO()

    chunks = []
    try:
      for data in git('--no-pager', *args, _decode_errors='replace', _out_bufsize=bufsize, _iter=True, _err=err, **kwargs):
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
        errlines = err.getvalue().splitlines()
        if len(errlines) < 3:
            for line in errlines:
                vd.status(line)
        else:
            vd.push(TextSheet('git ' + ' '.join(args), source=errlines))

        vd.error('git '+' '.join(args)+'error=%s' % e.exit_code)

    r = ''.join(chunks)
    if r:
        yield r

    errlines = err.getvalue().splitlines()
    if len(errlines) < 3:
        for line in errlines:
            vd.status(line)
    else:
        vd.push(TextSheet('git ' + ' '.join(args), source=errlines))


class GitUndo:
    def __init__(self, *args):
        self.cmdargs = args
    def __enter__(self):
        return self
    def __exit__(self, exctype, exc, tb):
        out = git_all(*self.cmdargs)


BaseSheet.addCommand('gD', 'git-output', 'vd.push(vd.gitcmdlog)', 'show output of git commands this session')

