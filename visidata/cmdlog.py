import threading

from visidata import *
import visidata

vd.option('replay_wait', 0.0, 'time to wait between replayed commands, in seconds', sheettype=None)
vd.option('disp_replay_play', '▶', 'status indicator for active replay')
vd.option('disp_replay_pause', '‖', 'status indicator for paused replay')
vd.option('color_status_replay', 'green', 'color of replay status indicator')
vd.option('replay_movement', False, 'insert movements during replay', sheettype=None)

# prefixes which should not be logged
nonLogged = '''forget exec-longname undo redo quit
show error errors statuses options threads jump
replay cancel save-cmdlog macro cmdlog-sheet menu repeat
go- search scroll prev next page start end zoom resize visibility sidebar
mouse suspend redraw no-op help syscopy sysopen profile toggle'''.split()

vd.option('rowkey_prefix', 'キ', 'string prefix for rowkey in the cmdlog', sheettype=None)
vd.option('cmdlog_histfile', '', 'file to autorecord each cmdlog action to', sheettype=None)

vd.activeCommand = UNLOADED

@VisiData.api
def open_vd(vd, p):
    return CommandLog(p.name, source=p, precious=True)

@VisiData.api
def open_vdj(vd, p):
    return CommandLogJsonl(p.name, source=p, precious=True)

VisiData.save_vd = VisiData.save_tsv


@VisiData.api
def save_vdj(vd, p, *vsheets):
    with p.open_text(mode='w', encoding=vsheets[0].options.encoding) as fp:
        fp.write("#!vd -p\n")
        for vs in vsheets:
            vs.write_jsonl(fp)


@VisiData.api
def checkVersion(vd, desired_version):
    if desired_version != visidata.__version_info__:
        vd.fail("version %s required" % desired_version)

@VisiData.api
def fnSuffix(vd, prefix):
    i = 0
    fn = prefix + '.vdj'
    while Path(fn).exists():
        i += 1
        fn = f'{prefix}-{i}.vdj'

    return fn

@BaseSheet.api
def inputLongname(sheet):
    longnames = set(k for (k, obj), v in vd.commands.iter(sheet))
    return vd.input("command name: ", completer=CompleteKey(sorted(longnames)), type='longname')

@BaseSheet.api
def exec_longname(sheet, longname):
    if not sheet.getCommand(longname):
        vd.warning(f'no command {longname}')
        return
    sheet.execCommand(longname)

def indexMatch(L, func):
    'returns the smallest i for which func(L[i]) is true'
    for i, x in enumerate(L):
        if func(x):
            return i

def keystr(k):
    return  options.rowkey_prefix+','.join(map(str, k))

@VisiData.api
def isLoggableCommand(vd, longname):
    for n in nonLogged:
        if longname.startswith(n):
            return False
    return True

def isLoggableSheet(sheet):
    return sheet is not vd.cmdlog and not isinstance(sheet, (OptionsSheet, ErrorSheet))


@Sheet.api
def moveToRow(vs, rowstr):
    'Move cursor to row given by *rowstr*, which can be either the row number or keystr.'
    rowidx = vs.getRowIndexFromStr(rowstr)
    if rowidx is None:
        return False

    if vs.options.replay_movement:
        while vs.cursorRowIndex != rowidx:
            vs.cursorRowIndex += 1 if (rowidx - vs.cursorRowIndex) > 0 else -1
            while not vd.delay(0.5):
                pass
    else:
        vs.cursorRowIndex = rowidx

    return True

@Sheet.api
def getRowIndexFromStr(vs, rowstr):
    index = indexMatch(vs.rows, lambda r,vs=vs,rowstr=rowstr: keystr(vs.rowkey(r)) == rowstr)
    if index is not None:
        return index

    try:
        return int(rowstr)
    except ValueError:
        return None

@Sheet.api
def moveToCol(vs, col):
    'Move cursor to column given by *col*, which can be either the column number or column name.'
    if isinstance(col, str):
        vcolidx = indexMatch(vs.visibleCols, lambda c,name=col: name == c.name)
    elif isinstance(col, int):
        vcolidx = col

    if vcolidx is None or vcolidx >= vs.nVisibleCols:
        return False

    if vs.options.replay_movement:
        while vs.cursorVisibleColIndex != vcolidx:
            vs.cursorVisibleColIndex += 1 if (vcolidx - vs.cursorVisibleColIndex) > 0 else -1
            while not vd.delay(0.5):
                pass
    else:
        vs.cursorVisibleColIndex = vcolidx

    return True


@BaseSheet.api
def commandCursor(sheet, execstr):
    'Return (col, row) of cursor suitable for cmdlog replay of execstr.'
    colname, rowname = '', ''
    contains = lambda s, *substrs: any((a in s) for a in substrs)
    if contains(execstr, 'cursorTypedValue', 'cursorDisplay', 'cursorValue', 'cursorCell', 'cursorRow') and sheet.nRows > 0:
        k = sheet.rowkey(sheet.cursorRow)
        rowname = keystr(k) if k else sheet.cursorRowIndex

    if contains(execstr, 'cursorTypedValue', 'cursorDisplay', 'cursorValue', 'cursorCell', 'cursorCol', 'cursorVisibleCol', 'ColumnAtCursor'):
        colname = sheet.cursorCol.name or sheet.visibleCols.index(sheet.cursorCol)
    return colname, rowname


# rowdef: namedlist (like TsvSheet)
class CommandLogBase:
    'Log of commands for current session.'
    rowtype = 'logged commands'
    precious = False
    _rowtype = namedlist('CommandLogRow', 'sheet col row longname input keystrokes comment undofuncs'.split())
    columns = [
        ColumnAttr('sheet'),
        ColumnAttr('col'),
        ColumnAttr('row'),
        ColumnAttr('longname'),
        ColumnAttr('input'),
        ColumnAttr('keystrokes'),
        ColumnAttr('comment'),
        ColumnAttr('undo', 'undofuncs', type=vlen, width=0)
    ]

    filetype = 'vd'

    def newRow(self, **fields):
        return self._rowtype(**fields)

    def beforeExecHook(self, sheet, cmd, args, keystrokes):
        if vd.activeCommand:
            self.afterExecSheet(sheet, False, '')

        colname, rowname, sheetname = '', '', None
        if sheet and not (cmd.longname.startswith('open-') and not cmd.longname in ('open-row', 'open-cell')):
            sheetname = sheet.name

            colname, rowname = sheet.commandCursor(cmd.execstr)

            contains = lambda s, *substrs: any((a in s) for a in substrs)
            if contains(cmd.execstr, 'pasteFromClipboard'):
                args = vd.sysclip_value().strip()


        comment = vd.currentReplayRow.comment if vd.currentReplayRow else cmd.helpstr
        vd.activeCommand = self.newRow(sheet=sheetname,
                                            col=colname,
                                            row=str(rowname),
                                            keystrokes=keystrokes,
                                            input=args,
                                            longname=cmd.longname,
                                            comment=comment,
                                            undofuncs=[])

    def afterExecSheet(self, sheet, escaped, err):
        'Records vd.activeCommand'
        if not vd.activeCommand:  # nothing to record
            return

        if err:
            vd.activeCommand[-1] += ' [%s]' % err

        if escaped:
            vd.activeCommand = None
            return

        # remove user-aborted commands and simple movements (unless first command on the sheet, which created the sheet)
        if not sheet.cmdlog.rows or vd.isLoggableCommand(vd.activeCommand.longname):
            if isLoggableSheet(sheet):      # don't record actions from cmdlog or other internal sheets on global cmdlog
                self.addRow(vd.activeCommand)  # add to global cmdlog
            sheet.cmdlog_sheet.addRow(vd.activeCommand)  # add to sheet-specific cmdlog
            if options.cmdlog_histfile:
                name = date().strftime(options.cmdlog_histfile)
                p = Path(name)
                if not p.is_absolute():
                    p = Path(options.visidata_dir)/f'{name}.jsonl'
                if not getattr(vd, 'sessionlog', None):
                    vd.sessionlog = vd.loadInternalSheet(CommandLog, p)
                vd.sessionlog.append_tsv_row(vd.activeCommand)

        vd.activeCommand = None

    def openHook(self, vs, src):
        while isinstance(src, BaseSheet):
            src = src.source
        r = self.newRow(keystrokes='o', input=str(src), longname='open-file')
        vs.cmdlog_sheet.addRow(r)
        self.addRow(r)

class CommandLog(CommandLogBase, VisiDataMetaSheet):
    pass

class CommandLogJsonl(CommandLogBase, JsonLinesSheet):

    filetype = 'vdj'

    def newRow(self, **fields):
        return AttrDict(JsonLinesSheet.newRow(self, **fields))

    def iterload(self):
        for r in JsonLinesSheet.iterload(self):
            if isinstance(r, TypedWrapper):
                yield r
            else:
                yield AttrDict(r)


### replay

vd.paused = False
vd.currentReplay = None     # CommandLog replaying currently
vd.currentReplayRow = None  # must be global, to allow replay
vd.semaphore = threading.Semaphore(0)


@VisiData.api
def replay_pause(vd):
        if not vd.currentReplay:
            vd.fail('no replay to pause')
        else:
            if vd.paused:
                vd.replay_advance()
            vd.paused = not vd.paused
            vd.status('paused' if vd.paused else 'resumed')


@VisiData.api
def replay_advance(vd):
        vd.currentReplay or vd.fail("no replay to advance")
        vd.semaphore.release()


@VisiData.api
def replay_cancel(vd):
        vd.currentReplay or vd.fail("no replay to cancel")
        vd.currentReplayRow = None
        vd.currentReplay = None
        vd.semaphore.release()


@VisiData.api
def moveToReplayContext(vd, r, vs):
        'set the sheet/row/col to the values in the replay row'
        if r.row not in [None, '']:
            vs.moveToRow(r.row) or vd.error('no "%s" row' % r.row)

        if r.col not in [None, '']:
            vs.moveToCol(r.col) or vd.error('no "%s" column' % r.col)


@VisiData.api
def delay(vd, factor=1):
        'returns True if delay satisfied'
        acquired = vd.semaphore.acquire(timeout=options.replay_wait*factor if not vd.paused else None)
        return acquired or not vd.paused


@VisiData.api
def replayOne(vd, r):
        'Replay the command in one given row.'
        vd.currentReplayRow = r
        longname = getattr(r, 'longname', None)

        if r.sheet and longname not in ['set-option', 'unset-option']:
            vs = vd.getSheet(r.sheet) or vd.error('no sheet named %s' % r.sheet)
        else:
            vs = None

        if longname in ['set-option', 'unset-option']:
            try:
                context = vs if r.sheet and vs else vd
                option_scope = r.sheet or r.col or 'global'
                if option_scope == 'override': option_scope = 'global' # override is deprecated, is now global
                if longname == 'set-option':
                    context.options.set(r.row, r.input, option_scope)
                else:
                    context.options.unset(r.row, option_scope)

                escaped = False
            except Exception as e:
                vd.exceptionCaught(e)
                escaped = True
        else:
            vs = vs or vd.activeSheet
            if vs:
                vd.push(vs)
            else:
                vs = vd.cmdlog

            vd.moveToReplayContext(r, vs)

            if r.comment:
                vd.status(r.comment)

            vd.keystrokes = r.keystrokes
            # <=v1.2 used keystrokes in longname column; getCommand fetches both
            escaped = vs.execCommand(longname if longname else r.keystrokes, keystrokes=r.keystrokes)

        vd.currentReplayRow = None

        if escaped:  # escape during replay aborts replay
            vd.warning('replay aborted during %s' % (longname or r.keystrokes))
        return escaped


@VisiData.api
def replay_sync(vd, cmdlog, live=False):
        'Replay all commands in log.'
        cmdlog.cursorRowIndex = 0
        vd.currentReplay = cmdlog
        with Progress(total=len(cmdlog.rows)) as prog:
            while cmdlog.cursorRowIndex < len(cmdlog.rows):
                if vd.currentReplay is None:
                    vd.status('replay canceled')
                    return

                vd.statuses.clear()
                try:
                    if vd.replayOne(cmdlog.cursorRow):
                        vd.replay_cancel()
                        return True
                except Exception as e:
                    vd.replay_cancel()
                    vd.exceptionCaught(e)
                    vd.status('replay canceled')
                    return True

                cmdlog.cursorRowIndex += 1
                prog.addProgress(1)

                if vd.activeSheet:
                    vd.activeSheet.ensureLoaded()
                vd.sync()
                while not vd.delay():
                    pass

        vd.status('replay complete')
        vd.currentReplay = None


@VisiData.api
@asyncthread
def replay(vd, cmdlog):
        'Inject commands into live execution with interface.'
        for thread in vd.threads:
            if thread.name == 'replay':
                thread.noblock = True
        vd.replay_sync(cmdlog, live=True)


@VisiData.api
def getLastArgs(vd):
        'Get user input for the currently playing command.'
        if vd.currentReplayRow:
            return vd.currentReplayRow.input
        return None


@VisiData.api
def setLastArgs(vd, args):
        'Set user input on last command, if not already set.'
        # only set if not already set (second input usually confirmation)
        if (vd.activeCommand is not None) and (vd.activeCommand is not UNLOADED):
            if not vd.activeCommand.input:
                vd.activeCommand.input = args


@VisiData.property
def replayStatus(vd):
        x = options.disp_replay_pause if vd.paused else options.disp_replay_play
        return ' │ %s %s/%s' % (x, vd.currentReplay.cursorRowIndex, len(vd.currentReplay.rows))


@BaseSheet.property
def cmdlog(sheet):
    rows = sheet.cmdlog_sheet.rows
    if isinstance(sheet.source, BaseSheet):
        rows = sheet.source.cmdlog.rows + rows
    return CommandLogJsonl(sheet.name+'_cmdlog', source=sheet, rows=rows)


@BaseSheet.lazy_property
def cmdlog_sheet(sheet):
    return CommandLogJsonl(sheet.name+'_cmdlog', source=sheet, rows=[])


@BaseSheet.property
def shortcut(self):
    if self._shortcut:
        return self._shortcut
    try:
        return str(vd.allSheets.index(self)+1)
    except ValueError:
        pass

    try:
        return self.cmdlog_sheet.rows[0].keystrokes
    except Exception:
        pass

    return ''


@VisiData.property
def cmdlog(vd):
    if not vd._cmdlog:
        vd._cmdlog = CommandLogJsonl('cmdlog', rows=[])  # no reload
        vd._cmdlog.reloadCols()
        vd.beforeExecHooks.append(vd._cmdlog.beforeExecHook)
    return vd._cmdlog

@VisiData.property
def modifyCommand(vd):
    if vd.activeCommand is not None and vd.isLoggableCommand(vd.activeCommand.longname):
        return vd.activeCommand
    if not vd.cmdlog.rows:
        return None
    return vd.cmdlog.rows[-1]


@CommandLogJsonl.api
@asyncthread
def repeat_for_n(cmdlog, r, n=1):
    r.sheet = r.row = r.col = ""
    for i in range(n):
        vd.replayOne(r)

@CommandLogJsonl.api
@asyncthread
def repeat_for_selected(cmdlog, r):
    r.sheet = r.row = r.col = ""

    for idx, r in enumerate(vd.sheet.rows):
        if vd.sheet.isSelected(r):
            vd.sheet.cursorRowIndex = idx
            vd.replayOne(r)


BaseSheet.init('_shortcut')


globalCommand('gD', 'cmdlog-all', 'vd.push(vd.cmdlog)', 'open global CommandLog for all commands executed in current session')
globalCommand('D', 'cmdlog-sheet', 'vd.push(sheet.cmdlog)', "open current sheet's CommandLog with all other loose ends removed; includes commands from parent sheets")
globalCommand('zD', 'cmdlog-sheet-only', 'vd.push(sheet.cmdlog_sheet)', 'open CommandLog for current sheet with commands from parent sheets removed')
globalCommand('^D', 'save-cmdlog', 'saveSheets(inputPath("save cmdlog to: ", value=fnSuffix(name)), vd.cmdlog, confirm_overwrite=options.confirm_overwrite)', 'save CommandLog to filename.vd file')
globalCommand('^U', 'replay-pause', 'vd.replay_pause()', 'pause/resume replay')
globalCommand('^N', 'replay-advance', 'vd.replay_advance()', 'execute next row in replaying sheet')
globalCommand('^K', 'replay-stop', 'vd.replay_cancel()', 'cancel current replay')

globalCommand(None, 'show-status', 'status(input("status: "))', 'show given message on status line')
globalCommand('^V', 'show-version', 'status(__version_info__);', 'Show version and copyright information on status line')
globalCommand('z^V', 'check-version', 'checkVersion(input("require version: ", value=__version_info__))', 'check VisiData version against given version')

globalCommand(' ', 'exec-longname', 'exec_longname(inputLongname())', 'execute command by its longname')

CommandLog.addCommand('x', 'replay-row', 'vd.replayOne(cursorRow); status("replayed one row")', 'replay command in current row')
CommandLog.addCommand('gx', 'replay-all', 'vd.replay(sheet)', 'replay contents of entire CommandLog')
CommandLog.addCommand('^C', 'replay-stop', 'sheet.cursorRowIndex = sheet.nRows', 'abort replay')

CommandLogJsonl.addCommand('x', 'replay-row', 'vd.replayOne(cursorRow); status("replayed one row")', 'replay command in current row')
CommandLogJsonl.addCommand('gx', 'replay-all', 'vd.replay(sheet)', 'replay contents of entire CommandLog')
CommandLogJsonl.addCommand('^C', 'replay-stop', 'sheet.cursorRowIndex = sheet.nRows', 'abort replay')

CommandLog.options.json_sort_keys = False
CommandLog.options.encoding = 'utf-8'
CommandLogJsonl.options.json_sort_keys = False

vd.addGlobals({"CommandLogBase": CommandLogBase})
