#
# Usage: $0 [<options>] [<input> ...]
#        $0 [<options>] --play <cmdlog> [--batch] [-w <waitsecs>] [-o <output>] [field=value ...]

__version__ = '2.-3'
__version_info__ = 'saul.pw/VisiData v' + __version__

import os
import io
import sys
import locale

from visidata import vd, option, options, status, run, Sheet
from visidata import Path, openSource, saveSheets, setDiffSheet, domotd
import visidata

option('config', '~/.visidatarc', 'config file to exec in Python')
option('preplay', '', 'longnames to preplay before replay')

# for --play
def eval_vd(logpath, *args, **kwargs):
    'Instantiate logpath with args/kwargs replaced and replay all commands.'
    log = logpath.read_text()
    if args or kwargs:
        log = log.format(*args, **kwargs)

    src = Path(logpath.given, fp=io.StringIO(log), filesize=len(log))
    vs = openSource(src, filetype=src.ext)
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


def main_vd():
    'Open the given sources using the VisiData interface.'
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('inputs', nargs='*', help='initial sources')
    parser.add_argument('-f', dest='filetype', default='', help='uses loader for filetype instead of file extension')
    parser.add_argument('-y', dest='confirm_overwrite', default=None, action='store_false', help='overwrites existing files without confirmation')
    parser.add_argument('-p', '--play', dest='play', default=None, help='replays a saved .vd file within the interface')
    parser.add_argument('-P', dest='preplay', action='append', default=[], help='VisiData command to preplay before cmdlog replay')
    parser.add_argument('-b', '--batch', dest='batch', action='store_true', default=False, help='replays in batch mode (with no interface and all status sent to stdout)')
    parser.add_argument('-o', '--output', dest='output', default=None, help='saves the final visible sheet to output at the end of replay')
    parser.add_argument('-w', dest='replay_wait', default=0, help='time to wait between replayed commands, in seconds')
    parser.add_argument('-d', dest='delimiter', help='delimiter to use for tsv/usv filetype')
    parser.add_argument('--diff', dest='diff', default=None, help='show diffs from all sheets against this source')
    parser.add_argument('-v', '--version', action='version', version=__version_info__)

    args = vd.parseArgs(parser)

    # fetch motd and plugins *after* options parsing/setting
    visidata.PluginsSheet().reload()
    domotd()

    locale.setlocale(locale.LC_ALL, '')

    flPipedInput = not sys.stdin.isatty()
    flPipedOutput = not sys.stdout.isatty()

    vd._stdin, vd._stdout = duptty()  # always dup stdin/stdout

    stdinSource = Path('-', fp=vd._stdin)

    # parse args, including +sheetname:subsheet:4:3 starting at row:col on sheetname:subsheet[:...]
    start_positions = []  # (list_of_sheetstr, str, str)  # empty sheetstr means all sheets
    startsheets, startrow, startcol = [], None, None
    fmtargs = []
    fmtkwargs = {}
    inputs = []
    for arg in args.inputs:
        if arg.startswith('+'):  # position cursor at start
            if ':' in arg:
                pos = arg[1:].split(':')
                if len(pos) == 1:
                    startsheet = [Path(inputs[-1]).name] if inputs else None
                    start_positions.append((startsheet, pos[0], None))
                elif len(pos) == 2:
                    startsheet = [Path(inputs[-1]).name] if inputs else None
                    startrow, startcol = pos
                    start_positions.append((None, startrow, startcol))
                elif len(pos) >= 3:
                    startsheets = pos[:-2]
                    startrow, startcol = pos[-2:]
                    start_positions.append((startsheets, startrow, startcol))
            else:
                start_positions.append((None, arg[1:], None))

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
        vs.reload()
        setDiffSheet(vs)

    if args.batch:
        options.undo = False
        vd.status = lambda *args, **kwargs: print(*args, file=sys.stderr)  # ignore kwargs (like priority)
        vd.editline = lambda *args, **kwargs: ''
        vd.execAsync = lambda func, *args, **kwargs: func(*args, **kwargs) # disable async

    for cmd in args.preplay:
        Sheet('').exec_keystrokes(cmd)

    if not args.play:
        if flPipedInput and not inputs:  # '|vd' without explicit '-'
            inputs.append(stdinSource)

    sources = []
    for src in inputs:
        vs = openSource(src)
        vd.cmdlog.openHook(vs, src)
        sources.append(vs)

    vd.sheets.extend(sources)  # purposefully do not load everything

    if not vd.sheets and not args.play and not args.batch:
        vd.push(vd.vdmenu)

    if not args.play:
        if args.batch:
            vd.push(sources[0])
            sources[0].reload()

        for startsheets, startrow, startcol in start_positions:
            sheets = []  # sheets to apply startrow:startcol to
            if not startsheets:
                sheets = sources  # apply row/col to all sheets
            else:
                vs = vd.getSheet(startsheets[0]) or sources[-1]
                vd.sync(vs.ensureLoaded())
                vd.clearCaches()
                for startsheet in startsheets[1:]:
                    rowidx = vs.getRowIndexFromStr(startsheet)
                    if rowidx is None:
                        vs = None
                        vd.warning(f'no sheet "{startsheet}"')
                        break
                    vs = vs.rows[rowidx]
                    vd.sync(vs.ensureLoaded())
                    vd.clearCaches()
                if vs:
                    vd.push(vs)
                    sheets = [vs]

            if startrow:
                for vs in sheets:
                    if vs:
                        vs.moveToRow(startrow) or vd.warning(f'{vs} has no row "{startrow}"')

            if startcol:
                for vs in sheets:
                    if vs:
                        vs.moveToCol(startcol) or vd.warning(f'{vs} has no column "{startcol}"')

        if not args.batch:
            run(vd.sheets[0])
    else:
        if args.play == '-':
            vdfile = stdinSource
            vdfile.name = 'stdin.vd'
        else:
            vdfile = Path(args.play)

        vs = eval_vd(vdfile, *fmtargs, **fmtkwargs)
        vd.sync(vs.reload())
        if args.batch:
            if vd.replay_sync(vs):  # error
                return 1
        else:
            vd.replay(vs)
            run()

    if vd.sheets and (flPipedOutput or args.output):
        outpath = Path(args.output or '-')
        saveSheets(outpath, vd.sheets[0], confirm_overwrite=False)
        vd.sync()

    vd._stdout.flush()

    return 0

def vd_cli():
    status(__version_info__)
    rc = -1
    try:
        rc = main_vd()
    except visidata.ExpectedException as e:
        print('fail: ' + str(e))
    except FileNotFoundError as e:
        print(e)
        if options.debug:
            raise
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(rc)  # cleanup can be expensive with large datasets
