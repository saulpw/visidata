#
# Usage: $0 [<options>] [<input> ...]
#        $0 [<options>] --play <cmdlog> [--batch] [-w <waitsecs>] [-o <output>] [field=value ...]

__version__ = '3.4dev'
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

from visidata import vd, options, run, BaseSheet, Sheet, AttrDict, stacktrace
from visidata import Path, asyncthread
import visidata

vd.version_info = __version_info__

vd.option('config', vd.config_file, 'config file to exec in Python', sheettype=None)
vd.option('play', '', 'file.vdj to replay')
vd.option('batch', False, 'replay in batch mode (with no interface and all status sent to stdout)')
vd.option('output', None, 'save the final visible sheet to output at the end of replay', cli_only=True)
vd.option('output_cell', None, 'output the cursor cell display value at exit', cli_only=True)
vd.option('preplay', '', 'longnames to preplay before replay')
vd.option('imports', 'plugins', 'imports to preload before .visidatarc (command-line only)')
vd.option('nothing', False, 'no config, no plugins, nothing extra')
vd.option('interactive', False, 'run interactive mode after batch replay')
vd.option('s3_anon', False, 'run S3 in anonymous mode')

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
        # vdx format handles .vd (tsv), .vdj (json), and .vdx (minimal) lines
        vs = vd.openSource(src, filetype='vdx')
    else:
        vs = vd.openSource(src, filetype=src.ext or 'vdx')
    # add a row in place of the sheet creation command that undo() expects as the first command
    vs.cmdlog_sheet.addRow(vs.cmdlog_sheet.newRow(sheet=None, row='', keystrokes='', input='', longname='no-op', undofuncs=[]))
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
        stdout = open(os.dup(1), mode='w')  # for dumping to stdout from interface
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
vd.optalias('O', 'output_cell')
vd.optalias('w', 'replay_wait')
vd.optalias('d', 'delimiter')
vd.optalias('c', 'config')
vd.optalias('r', 'dir_depth', 100000)


@visidata.VisiData.api
def parsePos(vd, arg:str, inputs:'list[tuple[str, dict]]'=None):
    '''Return (startsheets:list, startcol:str, startrow:str) from *arg* like "+sheet:subsheet:col:row".
    The elements of *startsheets* are identifiers that pick out a sheet, either
    a) a string that is the name of a sheet or subsheet
    b) integers (which are indices of a row or column, or a sheet number).
    For example [1, 'sales', 3].
    Returns an empty list for *startsheets* when the starting pos applies to all sheets.
    Returns None for *startsheets* when the position expression did not specify a sheet.
    *inputs* is a list of (path, options) tuples.
    '''
    if arg == '': return None
    startsheets, startcol, startrow = None, None, None

    pos = []
    # convert any numeric index strings to ints
    for idx in arg.split(':'):
        if idx:
            if idx.isdigit() or (idx[0] == '-' and idx[1:].isdigit()):
                idx = int(idx)
        pos.append(idx)

    if len(pos) == 1:
        # -1 means the last sheet in the list of open sheets
        startsheets = [len(inputs) - 1] if inputs else None
        startrow = arg
    elif len(pos) == 2:
        startsheets = [len(inputs) - 1] if inputs else None
        startcol, startrow = pos
    else:
        # the first element of pos is the startsheet,
        # the later elements (if present) describe the branch to a subsheet
        startsheets = pos[:-2]
        if startsheets == ['']: startsheets = []
        startcol, startrow = pos[-2:]
    if startcol == '':  startcol = None
    if startrow == '':  startrow = None
    start_pos = (startsheets, startcol, startrow)

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
def moveToPos(vd, sources, sheet_desc, startcol, startrow):
    '''*sources* is a list of sheets, if it is empty, the currently active sheet is used'''
    if len(sources) == 0:
        sources = [vd.activeSheet]
    if sheet_desc is None:  #apply move to the last sheet
        sheet_descs = [[len(sources) - 1]]
    elif sheet_desc == [] or sheet_desc[0] == '': #apply move to all sheets
        # the list of moves must have each of its elements refer only to 1
        # sheet, so expand the "all sheets" sheet descriptor into individual sheets
        sheet_descs = [[i] + sheet_desc[1:] for i, sheet in enumerate(sources)]
    else:
        sheet_descs = [sheet_desc]
    if startcol is not None or startrow is not None:
        moves = []
        if startcol:
            moves += [(d, startcol, None) for d in sheet_descs]
        if startrow:
            moves += [(d, None, startrow) for d in sheet_descs]
    else:
        moves = [(d, None, None) for d in sheet_descs]
    vd.queue_move_to_pos(sources, moves)

def sheet_from_description(vd, sources, sheet_desc):
    '''Return a Sheet to apply col/row to, given a list *sheet_desc* that refers to one specific sheet.
        The *sheet_desc* is either a Sheet, or a list of strings/ints similar to the return value of parsePos(),
        with the difference that *sheet_desc* will not ever be the empty list that denotes "all sheets".
        Return None if no matching sheet was found; if no match was found because sheets are loading,
        a subsequent call may return a matching sheet.
        Raise ValueError to indicate that a move failed, and should not be retried.'''
    if isinstance(sheet_desc, BaseSheet):
        vd.push(sheet_desc)
        return sheet_desc

    # descend the tree of subsheets
    for desc_lvl, subsheet in enumerate(sheet_desc):
        if desc_lvl == 0:
            vs = None
            #try subsheets as numbers first, then as names
            if isinstance(subsheet, int):
                try:
                    vs = sources[subsheet]
                except IndexError:
                    pass
            else:
                vs = vd.getSheet(subsheet)
            if not vs:
                raise ValueError(f'no sheet "{subsheet}"')
        else:
            if isinstance(subsheet, int):
                rowidx = subsheet
            else:
                rowidx = vs.getRowIndexFromStr(vd.options.rowkey_prefix + subsheet)
            try:
                if rowidx is None: raise IndexError
                vs_subsheet = vs.rows[rowidx]
            except IndexError:
                vd.warning(f'sheet {vs.name} has no subsheet `{subsheet}`')
                return None
            if not isinstance(vs_subsheet, BaseSheet):
                raise ValueError(f'row "{subsheet}" is not a sheet in {vs.name}')
            vs = vs_subsheet
        # if we have any more levels of subsheets to look at, load the current sheet fully
        if desc_lvl < len(sheet_desc) - 1:
            # Prevent the sheet from doing automatic ensureLoaded() on its subsheets when it
            # loads, so that we can call ensureLoaded() ourselves and sync() on it.
            vd.options.set('load_lazy', True, obj=vs)
            vd.sync(vs.ensureLoaded())
            vd.clearCaches()
    # Only push for subsheet navigation or sheets not already on the stack.
    # For single-level moves (cursor positioning on an existing source),
    # don't change the stack order -- just return the sheet for cursor moves.
    if len(sheet_desc) > 1 or vs not in vd.sheets:
        # use load=False to avoid calling afterLoad() early, before queue_move_to_pos
        # can replace the default afterLoad with a wrapped version
        vd.push(vs, load=False)
    return vs

@visidata.VisiData.api
def queue_move_to_pos(vd, sources, moves):
    for move in moves:
        sheet_desc = move[0]
        vs = sheet_from_description(vd, sources, sheet_desc)
        if not vs:
            continue
        if vs.rows is not visidata.basesheet.UNLOADED:
            attempt_move_to_pos(vd, sources, *move)
        else:
            if not hasattr(vs, '_startpos_moves'):
                vs._startpos_moves = []
            vs._startpos_moves.append((sources, move))
            if vd.options.batch:
                vd.sync(vs.ensureLoaded())

def attempt_move_to_pos(vd, sources, sheet_desc, startcol, startrow):
    '''Return True if the move succeeded in moving to the row and column, on the described sheet.
        Raise ValueError to indicate that a move failed, and should not be retried.'''
    vs = sheet_from_description(vd, sources, sheet_desc)
    if not vs:
        return False
    # switch the active sheet, for command line args like +s::
    if vs and startrow is None and startcol is None:
        vd.push(vs)
        return True

    # try cursor moves
    success = True
    if startrow is not None:
        if not vs.moveToRow(startrow):
            if vs.nRows > 0:    # avoid uninformative warnings early in startup
                vd.warning(f'{vs} has no row {startrow}:  nRows={len(vs.rows)}"')
            success = False

    if startcol is not None:
        if not vs.moveToCol(startcol):
            if vs.nRows > 0:
                vd.warning(f'{vs} has no column {startcol}')
            success = False
    return success

@Sheet.after
def afterLoad(sheet):
    moves = getattr(sheet, '_startpos_moves', None)
    if not moves:
        return
    del sheet._startpos_moves
    for sources, move in moves:
        attempt_move_to_pos(vd, sources, *move)

def main_vd():
    'Open the given sources using the VisiData interface.'
    if '-v' in sys.argv or '--version' in sys.argv:
        print(vd.version_info)
        return 0
    if '-h' in sys.argv or '--help' in sys.argv:
        manpath = Path(vd.pkg_resources_files(visidata)) / 'man' / 'vd.txt'
        if manpath.exists():
            print(manpath.open().read())
        else:
            print('usage: vd [options] [input ...]')
            print('  see https://visidata.org/man for full reference')
        return 0
    vd.status(__version_info__)

    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error as e:
        vd.warning(e)

    if options.debug:
        warnings.showwarning = lambda msg, cat, fn, lineno, *args, **kwargs: vd.warning(f'{fn}:{lineno}: {msg}')
    else:
        warnings.showwarning = lambda msg, *args, **kwargs: vd.warning(msg)

    vd.printerr = lambda *args: builtins.print(*args, file=sys.stderr)

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
    sheet_moves = []
    fmtargs = []
    fmtkwargs = {}
    inputs = []

    i=1
    current_args = {}
    global_args = {}
    clionly_args = {}
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

            opt = vd.options._get(optname)
            if optval is None and opt:  # missing argument, determine type
                if type(opt.value) is bool:
                    optval = True
                else:
                    if i >= len(sys.argv)-1:
                        vd.error(f'`-{optname}` missing argument')

                    optval = sys.argv[i+1]
                    i += 1

            if opt and opt.cli_only:
                clionly_args[optname] = optval
            else:
                # batch and interactive are only meaningful when applied globally,
                # so exclude them from sheet-specific options. Those would
                # override any later change to vd.options.batch in global settings.
                if optname not in ('batch', 'interactive'):
                    current_args[optname] = optval
                if flGlobal:
                    global_args[optname] = optval
        elif arg.startswith('+'):  # position cursor at start
            parsed_pos = vd.parsePos(arg[1:], inputs=inputs)
            if parsed_pos:
                sheet_moves.append(parsed_pos)
        elif current_args.get('play', None) and '=' in arg:
            # parse 'key=value' pairs for formatting cmdlog template in replay mode
            k, v = arg.split('=', maxsplit=1)
            fmtkwargs[k] = v
        else:
            inputs.append((arg, copy(current_args)))
            fmtargs.append(arg)

        i += 1

    args = AttrDict(current_args)
    args.update(clionly_args)

    if args.profile:
        import threading
        import cProfile
        t = threading.current_thread()
        t.profile = cProfile.Profile()
        t.profile.enable()

    if not args.nothing:
        vd.loadConfigAndPlugins(args)

    for k, v in global_args.items():
        options.set(k, v, obj='global')

    vd._stdin, vd._stdout = duptty()  # always dup stdin/stdout
    vd.stdinSource.fptext = vd._stdin
    vd._stdin.close = vd.nop  #1759

    # fetch motd *after* options parsing/setting
    vd.domotd()

    if options.batch:
        if not vd.options.interactive:
            options.undo = False
            options.quitguard = False
        vd.execAsync = vd.execSync  # disable async

    for cmd in (args.preplay or '').split():
        BaseSheet('').execCommand(cmd)

    if not args.play:
        if flPipedInput and not inputs:  # '|vd' without explicit '-'
            inputs.append((vd.stdinSource, copy(current_args)))

    # filetype is consumed by openPath (stored on source path), not applied as a sheet option
    cli_filetype = current_args.pop('filetype', None)

    sources = []
    for p, opts in inputs:
        if cli_filetype and ('filetype' not in opts):
            opts['filetype'] = cli_filetype

        vs = vd.openSource(p, create=True, **opts) or vd.fail(f'could not open {p}')
        for k, v in current_args.items():  # apply final set of args to sheets specifically on cli, if not set otherwise #573
            if not vs.options.is_set(k, vs):
                vs.options[k] = v
            # source path is authoritative for format options  #2727
            if isinstance(vs.source, Path) and not vs.source.options.is_set(k, vs.source):
                vs.source.options.set(k, v, vs.source, cmdlog=False)

        # log source to cmdlog
        vd.cmdlog.openHook(vs, vs.source)
        sources.append(vs)

    for vs in reversed(sources):
        vd.push(vs, load=False) #1471, 1555

    if not vd.sheets and not args.play and not options.batch:
        if cli_filetype:
            newfunc = getattr(vd, 'new_' + cli_filetype, vd.getGlobals().get('new_' + cli_filetype))
            datestr = datetime.date.today().strftime('%Y-%m-%d')
            if newfunc:
                vd.status('creating blank %s' % cli_filetype)
                vd.push(newfunc(Path(datestr + '.' + cli_filetype)))
            else:
                vd.status('new_%s does not exist, creating new blank sheet' % cli_filetype)
                vd.push(vd.newSheet(datestr, 1))
        else:
            vd.push(vd.currentDirSheet)

            # log source to cmdlog
            vd.cmdlog.openHook(vd.currentDirSheet, vd.currentDirSheet.source)

    if not args.play:
        if options.batch:
            if sources:
                vd.push(sources[0])

        # process the moves in order of increasing length of sheet desc,
        # so that every sheet loads (and executes its moves in afterLoad)
        # before its subsheets require it to be loaded
        for move in sorted(sheet_moves, key=lambda m: ((len(m[0]) if m[0] is not None else 0),m[1],m[2])):
            vd.moveToPos(sources, *move)
        if sheet_moves:  #redo the last move in the argument list, to show the sheet
            vd.moveToPos(sources, *sheet_moves[-1])

        if not options.batch:
            run(vd.sheets[0])
    else:
        if args.play in ('-', '/dev/stdin'):  # /dev/stdin: post-duptty fd 0 is the tty, not the pipe
            if vd.stdinSource.fptext.isatty():
                vd.fail('replay commands must come by pipe, not by terminal')
            vdfile = vd.stdinSource
        else:
            vdfile = Path(args.play)

        vs = eval_vd(vdfile, *fmtargs, **fmtkwargs)
        if options.batch:
            if not args.debug and sys.stderr.isatty() and not os.environ.get('NO_COLOR'):
                vd.outputProgressThread = visidata.VisiData.execAsync(vd, vd.outputProgressEvery, vs, seconds=0.5, sheet=BaseSheet())  #1182
            vd.reloadMacros()
            if vd.replay_sync(vs):  # error
                return 1

            if vd.options.interactive:
                vd.options.batch = False  #2639
                vd.execAsync = lambda *args, vd=vd, **kwargs: visidata.VisiData.execAsync(vd, *args, **kwargs)
                run()
        else:
            vd.push(vs)
            for src in reversed(sources):
                vd.push(src, load=False)
            vd.replay(vs)
            run()

    if vd.stackedSheets and (flPipedOutput or args.output) and not args.output_cell:
        outpath = Path(args.output or '-')
        vd.saveSheets(outpath, vd.activeSheet, confirm_overwrite=False)

    if vd.stackedSheets and args.output_cell:
        outfile = vd._stdout if args.output_cell == '-' else open(args.output_cell, 'w')
        print(vd.activeSheet.cursorFullDisplay, file=outfile)

    saver_threads = [t for t in vd.unfinishedThreads if t.name.startswith('save_')]
    if saver_threads:
        if not options.batch:
            vd.printerr('finishing %d savers' % len(saver_threads))
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
        print(e, file=sys.stderr)
        if options.debug:
            raise
    except Exception as e:
        for l in stacktrace(): #show the stack trace without carets
            print(l, file=sys.stderr)

    sys.stderr.flush()
    sys.stdout.flush()

    vd.killLeftoverProcesses()

    if vd.options.profile:
        import threading
        threading.current_thread().profile.disable()
        threading.current_thread().profile.dump_stats('vd.pyprof')
    elif not vd.options.debug:
        os._exit(rc)  # cleanup can be expensive with large datasets

    sys.exit(rc)
