'''
# vgit: VisiData wrapper for git

The syntax for vgit is the same as the syntax for git.
By default, will pass the command to git verbatim, as quickly as possible.
If vgit can provide an interactive interface for a particular subcommand,
it will open the sheet returned by vd.git_<subcommand>(path, args).
'''

import os
import sys


def vgit_cli():
    import visidata
    from visidata import vd, Path

    args = sys.argv[1:]
    flDebug = '--debug' in args
    if flDebug:
        args.remove('--debug')

    if not args:
        args = ['help']

    func = getattr(vd, 'git_'+args[0], None)
    if func:
        vd.loadConfigAndPlugins()
        vd.status(visidata.__version_info__)
        vd.domotd()
        if flDebug:
            vd.options.debug = True

        rc = 0
        try:
            p = Path('.')
            vs = func(p, args[1:])
            if vs:
                vd.run(vs)
        except BrokenPipeError:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno()) # handle broken pipe gracefully
        except visidata.ExpectedException as e:
            print(str(e))
        except Exception as e:
            rc = 1
            vd.exceptionCaught(e)
            if flDebug:
                raise

        sys.stderr.flush()
        sys.stdout.flush()
        os._exit(rc)  # cleanup can be expensive

    import subprocess
    return subprocess.run(['git', *args]).returncode
