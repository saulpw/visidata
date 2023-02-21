'''
# vgit: VisiData wrapper for git

The syntax for vgit is the same as the syntax for git.
By default, will pass the command to git verbatim, as quickly as possible.
If vgit can provide an interactive interface for a particular subcommand,
it will open the sheet returned by vd.git_<subcommand>().
'''

import sys


def vgit_cli():
    import visidata
    from visidata import vd, Path

    args = sys.argv[1:]

    if not args:
#        return vd.run(vd.git_help())
        return

    func = getattr(vd, 'git_'+args[0], None)
    if not func:
        import subprocess
        return subprocess.run(['git', *args]).returncode

    vd.loadConfigAndPlugins()
    vd.status(visidata.__version_info__)
    vd.domotd()

    vs = func(args[1:])
    return vd.run(vs)
