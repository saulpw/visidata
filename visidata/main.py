#
# Usage: $0 [<options>] [<input> ...]
#        $0 [<options>] --play <cmdlog> [--batch] [-w <waitsecs>] [-o <output>] [field=value ...]

__version__ = '2.0.1'
__version_info__ = 'saul.pw/VisiData v' + __version__

from copy import copy
import os
import io
import sys
import locale
import warnings

from visidata import vd, option, options, run, BaseSheet, AttrDict
from visidata import Path, saveSheets, domotd
import visidata

option('config', '~/.visidatarc', 'config file to exec in Python', sheettype=None)
option('play', '', '.vd file to replay')
option('batch', False, 'replay in batch mode (with no interface and all status sent to stdout)')
option('output', None, 'save the final visible sheet to output at the end of replay')
option('preplay', '', 'longnames to preplay before replay')
option('imports', 'plugins', 'imports to preload before .visidatarc (command-line only)')

# for --play
def eval_vd(logpath, *args, **kwargs):
    'Instantiate logpath with args/kwargs replaced and replay all commands.'
    log = logpath.read_text()
    if args or kwargs:
        log = log.format(*args, **kwargs)

    src = Path(logpath.given, fp=io.StringIO(log), filesize=len(log))
    vs = vd.openSource(src, filetype=src.ext)
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

        # close file descriptors for original stdin/stdout
        fin.close()
        fout.close()
    except Exception as e:
        print(e)
        stdin = sys.stdin
        stdout = sys.stdout

    return stdin, stdout

option_aliases = {}
def optalias(abbr, name):
    option_aliases[abbr] = name


optalias('f', 'filetype')
optalias('p', 'play')
optalias('b', 'batch')
optalias('P', 'preplay')
optalias('y', 'confirm_overwrite')
optalias('o', 'output')
optalias('w', 'replay_wait')
optalias('d', 'delimiter')
optalias('c', 'config')
optalias('r', 'dir_recurse')
optalias('force_valid_colnames', 'clean_names')  # deprecated


def main_vd():
    'Open the given sources using the VisiData interface.'
    locale.setlocale(locale.LC_ALL, '')
    warnings.showwarning = vd.warning

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

    i=1
    current_args = {}
    global_args = {}
    flGlobal = False
    optsdone = False

    while i < len(sys.argv):
        arg = sys.argv[i]
        if optsdone:
            # copied from final else: clause below
            inputs.append((arg, copy(current_args)))
            fmtargs.append(arg)
        elif arg in ['--']:
            optsdone = True
        elif arg in ['-v', '--version']:
            print(__version_info__)
            return 0
        elif arg == '-':
            inputs.append((stdinSource, copy(current_args)))
        elif arg in ['-h', '--help']:
            import curses
            curses.wrapper(lambda scr: vd.openManPage())
            return 0
        elif arg in ['-g', '--global']:
            flGlobal = not flGlobal  # can toggle within the same command
        elif arg[0] == '-':
            optname = arg.lstrip('-')
            optval = None
            try:
                optname, optval = optname.split('=', maxsplit=1)
                # convert to type
            except Exception:
                pass

            optname = optname.replace('-', '_')
            optname = option_aliases.get(optname, optname)

            if optval is None:
                opt = options._get(optname)
                if opt:
                    if type(opt.value) is bool:
                        optval = True
                    else:
                        if i >= len(sys.argv):
                            vd.error(f'"-{optname}" missing argument')

                        optval = sys.argv[i+1]
                        i += 1

            current_args[optname] = optval
            if flGlobal:
                global_args[optname] = optval

        elif arg.startswith('+'):  # position cursor at start
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

        elif current_args.get('play', None) and '=' in arg:
            # parse 'key=value' pairs for formatting cmdlog template in replay mode
            k, v = arg.split('=')
            fmtkwargs[k] = v
        else:
            inputs.append((arg, copy(current_args)))
            fmtargs.append(arg)

        i += 1

    args = AttrDict(current_args)

    vd.loadConfigAndPlugins(args)

    for k, v in global_args.items():
        options.set(k, v, obj='override')

    for k, v in current_args.items():
        opt = options._get(k)
        if opt and opt.sheettype is None:
            options.set(k, v, obj='override')

    # fetch motd and plugins *after* options parsing/setting
    visidata.PluginsSheet().reload()
    domotd()

    if args.batch:
        options.undo = False
        vd.status = lambda *args, **kwargs: print(*args, file=sys.stderr)  # ignore kwargs (like priority)
        vd.editline = lambda *args, **kwargs: ''
        vd.execAsync = lambda func, *args, **kwargs: func(*args, **kwargs) # disable async

    for cmd in (args.preplay or '').split():
        BaseSheet('').execCommand(cmd)

    if not args.play:
        if flPipedInput and not inputs:  # '|vd' without explicit '-'
            inputs.append((stdinSource, copy(current_args)))

    sources = []
    for p, opts in inputs:
        # filetype is a special option, bc it is needed to construct the specific sheet type
        if ('filetype' in current_args) and ('filetype' not in opts):
            opts['filetype'] = current_args['filetype']

        vs = vd.openSource(p, **opts)
        for k, v in current_args.items():  # apply final set of args to sheets specifically on cli, if not set otherwise #573
            if not vs.options.is_set(k, vs):
                vs.options[k] = v

        vd.cmdlog.openHook(vs, vs.source)
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
                startsheet = startsheets[0] or sources[-1]
                vs = vd.getSheet(startsheet)
                vd.sync(vs.ensureLoaded())
                vd.clearCaches()
                for startsheet in startsheets[1:]:
                    rowidx = vs.getRowIndexFromStr(options.rowkey_prefix + startsheet)
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

    saver_threads = [t for t in vd.unfinishedThreads if t.name.startswith('save_')]
    if saver_threads:
        print('finishing %d savers' % len(saver_threads))
        vd.sync(*saver_threads)

    vd._stdout.flush()

    return 0

def vd_cli():
    vd.status(__version_info__)
    rc = -1
    try:
        rc = main_vd()
    except visidata.ExpectedException as e:
        print('Error: ' + str(e))
    except FileNotFoundError as e:
        print(e)
        if options.debug:
            raise
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(rc)  # cleanup can be expensive with large datasets
