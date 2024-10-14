#
# Usage: $0 [<options>] [<input> ...]
#        $0 [<options>] --play <cmdlog> [--batch] [-w <waitsecs>] [-o <output>] [field=value ...]

__version__ = '3.1.1'
__version_info__ = 'saul.pw/VisiData v' + __version__

from copy import copy
import os
import io
import sys
import locale
import datetime
import functools
import signal
import warnings
import builtins  # to override print

from visidata import vd, options, run, BaseSheet, AttrDict
from visidata import Path
from visidata.settings import _get_config_file
import visidata

vd.version_info = __version_info__

vd.option('config', _get_config_file(), 'config file to exec in Python', sheettype=None)
vd.option('play', '', 'file.vdj to replay')
vd.option('batch', False, 'replay in batch mode (with no interface and all status sent to stdout)')
vd.option('output', None, 'save the final visible sheet to output at the end of replay')
vd.option('preplay', '', 'longnames to preplay before replay')
vd.option('imports', 'plugins', 'imports to preload before .visidatarc (command-line only)')
vd.option('nothing', False, 'no config, no plugins, nothing extra')
vd.option('interactive', False, 'run interactive mode after batch replay')

# for --play
def eval_vd(logpath, *args, **kwargs):
    'Instantiate logpath with args/kwargs replaced and replay all commands.'
    log = logpath.read_text()
    if args or kwargs:
        if logpath.ext in ['vdj', 'json', 'jsonl'] or logpath is vd.stdinSource:
            from string import Template
            log = Template(log).safe_substitute(**kwargs)
        else:
            log = log.format(*args, **kwargs)

    src = Path(logpath.given, fptext=io.StringIO(log), filesize=len(log))
    if logpath is vd.stdinSource:
        # replay from stdin only supports .vdj
        vs = vd.openSource(src, filetype='vdj')
    else:
        vs = vd.openSource(src, filetype=src.ext)
    vs.name += '_vd'
    vd.sync(vs.reload())
    vs.vd = vd
    return vs


def duptty():
    'Duplicate stdin/stdout for input/output and reopen tty as stdin/stdout.  Return (stdin, stdout).'
    try:
        fin = open('/dev/tty')
        fout = open('/dev/tty', mode='w')
        stdin = open(os.dup(0),
                     encoding=vd.options.getonly('encoding', 'global', 'utf-8'),
                     errors=vd.options.getonly('encoding_errors', 'global', 'surrogateescape'))  #2047
        stdout = open(os.dup(1))  # for dumping to stdout from interface
        os.dup2(fin.fileno(), 0)
        os.dup2(fout.fileno(), 1)

        # close file descriptors for original stdin/stdout
        fin.close()
        fout.close()
    except Exception as e:
        stdin = sys.stdin
        stdout = sys.stdout

    return stdin, stdout

vd.optalias('i', 'interactive')
vd.optalias('N', 'nothing')
vd.optalias('f', 'filetype')
vd.optalias('p', 'play')
vd.optalias('b', 'batch')
vd.optalias('P', 'preplay')
vd.optalias('o', 'output')
vd.optalias('w', 'replay_wait')
vd.optalias('d', 'delimiter')
vd.optalias('c', 'config')
vd.optalias('r', 'dir_depth', 100000)


@visidata.VisiData.api
def parsePos(vd, arg:str, inputs=None):
    'Return (startsheets:list, startrow:str, startcol:str) from *arg* like "+sheet:subsheet:col:row".  Empty sheetstr in startsheets means the starting pos applies to all sheets.'
    startsheets, startrow, startcol = [], None, None

    if ':' not in arg:
        return (None, arg, None)

    pos = arg.split(':')
    if len(pos) == 1:
        startsheet = [Path(inputs[-1]).base_stem] if inputs else None
        start_pos = (startsheet, pos[0], None)
    elif len(pos) == 2:
        startsheet = [Path(inputs[-1]).base_stem] if inputs else None
        startrow, startcol = pos
        start_pos = (None, startrow, startcol)
    else:  # if len(pos) >= 3:
        startsheets = pos[:-2]
        startrow, startcol = pos[-2:]
        start_pos = (startsheets, startrow, startcol)

    # index subsheets need to be loaded *after* the cursor indexing
    vd.options.set('load_lazy', True, obj=start_pos[0])

    return start_pos


@visidata.VisiData.api
def outputProgressEvery(vd, sheet, seconds:float=0.5):
    import time
    t0 = time.time()

    while not vd.currentReplay:
        time.sleep(.1)

    while vd.currentReplay:
        t = time.time()
        print(f'\r[{t-t0:.1f}s] ', end='', file=sys.stderr)
        if sheet:
            print(f'{sheet.progressPct}  ', end='', file=sys.stderr)
        sys.stderr.flush()
        time.sleep(seconds)

@visidata.VisiData.api
def moveToPos(vd, sources, startsheets, startrow, startcol):
    sheets = []  # sheets to apply startrow:startcol to
    if not startsheets:
        sheets = sources  # apply row/col to all sheets
    else:
        startsheet = startsheets[0] or sources[-1]
        vs = vd.getSheet(startsheet)
        if not vs:
            vd.warning(f'no sheet "{startsheet}"')
            return

        vd.sync(vs.ensureLoaded())
        vd.clearCaches()
        for startsheet in startsheets[1:]:
            rowidx = vs.getRowIndexFromStr(vd.options.rowkey_prefix + startsheet)
            if rowidx is None:
                vd.warning(f'{vs.name} has no subsheet "{startsheet}"')
                vs = None
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
                if not vs.moveToCol(startcol):
                    if startcol.isdigit():
                        vs.moveToCol(int(startcol)) # handle indexing by column number
                    else:
                        vd.warning(f'{vs} has no column "{startcol}"')

def main_vd():
    'Open the given sources using the VisiData interface.'
    if '-v' in sys.argv or '--version' in sys.argv:
        print(vd.version_info)
        return 0
    if '-h' in sys.argv or '--help' in sys.argv:
        print((Path(vd.pkg_resources_files(visidata)) / 'man' / 'vd.txt').open().read())
        return 0
    vd.status(__version_info__)

    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error as e:
        vd.warning(e)

    warnings.showwarning = vd.warning
    vd.printout = builtins.print

    flPipedInput = not sys.stdin.isatty()
    flPipedOutput = not sys.stdout.isatty()

    try:
        # workaround for bug in curses.wrapper #899
        # https://stackoverflow.com/questions/31440392/curses-wrapper-messing-up-terminal-after-background-foreground-sequence
        vd.tstp_signal = signal.getsignal(signal.SIGTSTP)
    except Exception:
        vd.tstp_signal = None

    vd.stdinSource = Path('-', fp=None)  # fp filled in below after options parsed for encoding

    # parse args, including +sheetname:subsheet:4:3 starting at row:col on sheetname:subsheet[:...]
    after_config = []
    fmtargs = []
    fmtkwargs = {}
    inputs = []

    i=1
    current_args = {}
    global_args = {}
    flGlobal = True
    optsdone = False

    while i < len(sys.argv):
        arg = sys.argv[i]
        if optsdone:
            # copied from final else: clause below
            inputs.append((arg, copy(current_args)))
            fmtargs.append(arg)
        elif arg in ['--']:
            optsdone = True
        elif arg == '-':
            if not flPipedInput:
                vd.fail('to use stdin as a data source, data must be piped into it')
            inputs.append((vd.stdinSource, copy(current_args)))
        elif arg in ['-g', '--global']:
            flGlobal = True
        elif arg in ['-n', '--nonglobal']:
            flGlobal = False
        elif arg.startswith('-'):
            optname = arg.lstrip('-')
            optval = None
            try:
                optname, optval = optname.split('=', maxsplit=1)
                # convert to type
            except Exception:
                pass

            optname = optname.replace('-', '_')
            optname, optval = vd._resolve_optalias(optname, optval)

            if optval is None:  # missing argument, maybe bool?
                opt = vd.options._get(optname)
                if opt:
                    if type(opt.value) is bool:
                        optval = True
                    else:
                        if i >= len(sys.argv)-1:
                            vd.error(f'"-{optname}" missing argument')

                        optval = sys.argv[i+1]
                        i += 1

            current_args[optname] = optval
            if flGlobal:
                global_args[optname] = optval
        elif arg.startswith('+'):  # position cursor at start
            after_config.append((vd.moveToPos, *vd.parsePos(arg[1:], inputs=inputs)))
        elif current_args.get('play', None) and '=' in arg:
            # parse 'key=value' pairs for formatting cmdlog template in replay mode
            k, v = arg.split('=', maxsplit=1)
            fmtkwargs[k] = v
        else:
            inputs.append((arg, copy(current_args)))
            fmtargs.append(arg)

        i += 1

    args = AttrDict(current_args)

    if not args.nothing:
        vd.loadConfigAndPlugins(args)

    for k, v in global_args.items():
        options.set(k, v, obj='global')

    vd._stdin, vd._stdout = duptty()  # always dup stdin/stdout
    vd.stdinSource.fptext = vd._stdin
    vd._stdin.close = vd.nop  #1759

    # fetch motd *after* options parsing/setting
    vd.domotd()

    if args.batch:
        if not vd.options.interactive:
            options.undo = False
            options.quitguard = False
        vd.execAsync = vd.execSync  # disable async

    for cmd in (args.preplay or '').split():
        BaseSheet('').execCommand(cmd)

    if not args.play:
        if flPipedInput and not inputs:  # '|vd' without explicit '-'
            inputs.append((vd.stdinSource, copy(current_args)))

    sources = []
    for p, opts in inputs:
        # filetype is a special option, bc it is needed to construct the specific sheet type
        if ('filetype' in current_args) and ('filetype' not in opts):
            opts['filetype'] = current_args['filetype']

        vs = vd.openSource(p, create=True, **opts) or vd.fail(f'could not open {p}')
        for k, v in current_args.items():  # apply final set of args to sheets specifically on cli, if not set otherwise #573
            if not vs.options.is_set(k, vs):
                vs.options[k] = v

        # log source to cmdlog
        vd.cmdlog.openHook(vs, vs.source)
        sources.append(vs)

    for vs in reversed(sources):
        vd.push(vs, load=False) #1471, 1555

    if not vd.sheets and not args.play and not args.batch:
        if 'filetype' in current_args:
            newfunc = getattr(vd, 'new_' + current_args['filetype'], vd.getGlobals().get('new_' + current_args['filetype']))
            datestr = datetime.date.today().strftime('%Y-%m-%d')
            if newfunc:
                vd.status('creating blank %s' % current_args['filetype'])
                vd.push(newfunc(Path(datestr + '.' + current_args['filetype'])))
            else:
                vd.status('new_%s does not exist, creating new blank sheet' % current_args['filetype'])
                vd.push(vd.newSheet(datestr, 1))
        else:
            vd.push(vd.currentDirSheet)

            # log source to cmdlog
            vd.cmdlog.openHook(vd.currentDirSheet, vd.currentDirSheet.source)

    if not args.play:
        if args.batch:
            if sources:
                vd.push(sources[0])

        for (f, *parms) in after_config:
            f(sources, *parms)

        if not args.batch:
            run(vd.sheets[0])
    else:
        if args.play == '-':
            vdfile = vd.stdinSource
        else:
            vdfile = Path(args.play)

        vs = eval_vd(vdfile, *fmtargs, **fmtkwargs)
        if args.batch:
            if not args.debug:
                vd.outputProgressThread = visidata.VisiData.execAsync(vd, vd.outputProgressEvery, vs, seconds=0.5, sheet=BaseSheet())  #1182
            vd.reloadMacros()
            if vd.replay_sync(vs):  # error
                return 1

            if vd.options.interactive:
                vd.execAsync = lambda *args, vd=vd, **kwargs: visidata.VisiData.execAsync(vd, *args, **kwargs)
                run()
        else:
            vd.replay(vs)
            run()

    if vd.stackedSheets and (flPipedOutput or args.output):
        outpath = Path(args.output or '-')
        vd.saveSheets(outpath, vd.activeSheet, confirm_overwrite=False)

    saver_threads = [t for t in vd.unfinishedThreads if t.name.startswith('save_')]
    if saver_threads:
        vd.printout('finishing %d savers' % len(saver_threads))
        vd.sync(*saver_threads)

    vd._stdout.flush()

    return 0

def vd_cli():
    rc = -1
    try:
        rc = main_vd()
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno()) # handle broken pipe gracefully
    except visidata.ExpectedException as e:
        if vd.options.debug:
            raise
    except FileNotFoundError as e:
        print(e)
        if options.debug:
            raise

    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(rc)  # cleanup can be expensive with large datasets
