#
# Usage: $0 [<options>] [<input> ...]
#        $0 [<options>] --play <cmdlog> [--batch] [-w <waitsecs>] [-o <output>] [field=value ...]

__version__ = '2.-1dev'
__version_info__ = 'saul.pw/VisiData v' + __version__

import os
import io
import sys
import locale

from visidata import vd, option, options, status, run
from visidata import loadConfigFile, addGlobals, getGlobals, globalCommand
from visidata import Path, PathFd, openSource, saveSheets, setDiffSheet, domotd

option('config', '~/.visidatarc', 'config file to exec in Python')

# for --play
def eval_vd(logpath, *args, **kwargs):
    'Instantiate logpath with args/kwargs replaced and replay all commands.'
    log = logpath.read_text()
    if args or kwargs:
        log = log.format(*args, **kwargs)

    src = PathFd(logpath.fqpn, io.StringIO(log), filesize=len(log))
    vs = openSource(src, filetype='vd')
    vs.name += '_vd'
    vd.push(vs)
    vs.vd = vd
    return vs


def duptty():
    'Duplicate stdin/stdout for input/output and reopen tty as stdin/stdout.  Return (stdin, stdout).'
    try:
        fin = open('/dev/tty')
        fout = open('/dev/tty', mode='w')
        stdin = open(os.dup(0))
        stdout = open(os.dup(1))  # for dumping to stdout from interface
        os.dup2(fin.fileno(), 0)
        os.dup2(fout.fileno(), 1)
    except Exception as e:
        print(e)
        stdin = sys.stdin
        stdout = sys.stdout

    return stdin, stdout


def main():
    'Open the given sources using the VisiData interface.'
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('inputs', nargs='*', help='initial sources')
    parser.add_argument('-f', dest='filetype', default='', help='uses loader for filetype instead of file extension')
    parser.add_argument('-y', dest='confirm_overwrite', default=None, action='store_false', help='overwrites existing files without confirmation')
    parser.add_argument('-p', '--play', dest='play', default=None, help='replays a saved .vd file within the interface')
    parser.add_argument('-b', '--batch', dest='batch', action='store_true', default=False, help='replays in batch mode (with no interface and all status sent to stdout)')
    parser.add_argument('-o', '--output', dest='output', default=None, help='saves the final visible sheet to output at the end of replay')
    parser.add_argument('-w', dest='replay_wait', default=0, help='time to wait between replayed commands, in seconds')
    parser.add_argument('-d', dest='delimiter', help='delimiter to use for tsv/usv filetype')
    parser.add_argument('--diff', dest='diff', default=None, help='show diffs from all sheets against this source')
    parser.add_argument('-v', '--version', action='version', version=__version_info__)

    args = vd.parseArgs(parser)

    # fetch motd after options parsing/setting
    domotd()

    locale.setlocale(locale.LC_ALL, '')

    flPipedInput = not sys.stdin.isatty()
    flPipedOutput = not sys.stdout.isatty()

    vd._stdin, vd._stdout = duptty()  # always dup stdin/stdout

    stdinSource = PathFd('-', vd._stdin)

    # parse args, including +4:3 starting row:col
    startrow, startcol = None, None
    fmtargs = []
    fmtkwargs = {}
    inputs = []
    for arg in args.inputs:
        if arg.startswith('+'):  # position cursor at start
            if ':' in arg:
                startrow, startcol = arg[1:].split(':')
            else:
                startrow = arg[1:]
        elif args.play and '=' in arg:
            # parse 'key=value' pairs for formatting cmdlog template in replay mode
            k, v = arg.split('=')
            fmtkwargs[k] = v
        elif arg == '-':
            inputs.append(stdinSource)
        else:
            inputs.append(arg)
            fmtargs.append(arg)

    if args.diff:
        vs = openSource(args.diff)
        vd.push(vs)
        setDiffSheet(vs)

    if args.batch:
        options.undo = False
        vd.status = lambda *args, **kwargs: print(*args, file=sys.stderr)  # ignore kwargs (like priority)
        vd.execAsync = lambda func, *args, **kwargs: func(*args, **kwargs) # disable async

    if not args.play:
        if flPipedInput and not inputs:  # '|vd' without explicit '-'
            inputs.append(stdinSource)

        if not inputs:
            inputs = ['.']

        sources = []
        for src in inputs:
            vs = openSource(src)
            vd.cmdlog.openHook(vs, src)
            sources.append(vs)
            if startrow is not None:
                vs.cursorRowIndex = int(startrow)-1
            if startcol is not None:
                vs.cursorVisibleColIndex = int(startcol)-1

        if args.batch:
            vd.sheets.extend(sources)
            sources[0].reload()
        else:
            run(*sources)
    else:
        if args.play == '-':
            vdfile = stdinSource  # PathFd
            vdfile.name = 'stdin.vd'
        else:
            vdfile = Path(args.play)

        vs = eval_vd(vdfile, *fmtargs, **fmtkwargs)
        if args.batch:
            if vs.replay_sync():  # error
                return 1
        else:
            vs.replay()
            run()

    if vd.sheets and (flPipedOutput or args.output):
        outpath = Path(args.output or '-')
        saveSheets(outpath, vd.sheets[0], confirm_overwrite=False)
        vd.sync()

    vd._stdout.flush()

    return 0

def vd_cli():
    status(__version_info__)
    rc = main()
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(rc)  # cleanup can be expensive with large datasets
