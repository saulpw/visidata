import threading

from visidata import vd, UNLOADED, namedlist, vlen, asyncthread, globalCommand, date
from visidata import VisiData, BaseSheet, Sheet, ColumnAttr, VisiDataMetaSheet, JsonLinesSheet, TypedWrapper, AttrDict, Progress, ErrorSheet, CompleteKey, Path
import visidata

vd.option('replay_wait', 0.0, 'time to wait between replayed commands, in seconds', sheettype=None)
vd.theme_option('disp_replay_play', '▶', 'status indicator for active replay')
vd.theme_option('disp_replay_record', '⏺', 'status indicator for macro record')
vd.theme_option('color_status_replay', 'green', 'color of replay status indicator')

# prefixes which should not be logged
nonLogged = '''forget exec-longname undo redo quit
show error errors statuses options threads jump
replay cancel save-cmdlog macro cmdlog-sheet menu repeat reload-every
search scroll prev next page start end zoom visibility sidebar
mouse suspend redraw no-op help syscopy sysopen profile toggle'''.split()

vd.option('rowkey_prefix', 'キ', 'string prefix for rowkey in the cmdlog', sheettype=None)

vd._nextCommands = []  # list[str|CommandLogRow] for vd.queueCommand

CommandLogRow = namedlist('CommandLogRow', 'sheet col row longname input keystrokes comment undofuncs'.split())

@VisiData.api
def queueCommand(vd, longname, input=None, sheet=None, col=None, row=None):
    'Add command to queue of next commands to execute.'
    vd._nextCommands.append(CommandLogRow(longname=longname, input=input, sheet=sheet, col=col, row=row))


@VisiData.api
def open_vd(vd, p):
    return CommandLog(p.base_stem, source=p, precious=True)

@VisiData.api
def open_vdj(vd, p):
    return CommandLogJsonl(p.base_stem, source=p, precious=True)

VisiData.save_vd = VisiData.save_tsv


@VisiData.api
def save_vdj(vd, p, *vsheets):
    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
        fp.write("#!vd -p\n")
        for vs in vsheets:
            vs.write_jsonl(fp)


@VisiData.api
def checkVersion(vd, desired_version):
    if desired_version != visidata.__version_info__:
        vd.fail("version %s required" % desired_version)

@VisiData.api
def fnSuffix(vd, prefix:str):
    i = 0
    fn = prefix + '.vdj'
    while Path(fn).exists():
        i += 1
        fn = f'{prefix}-{i}.vdj'

    return fn

def indexMatch(L, func):
    'returns the smallest i for which func(L[i]) is true'
    for i, x in enumerate(L):
        if func(x):
            return i

@VisiData.api
def isLoggableCommand(vd, cmd):
    'Return whether command should be logged to the cmdlog, depending if it has a prefix in nonLogged, or was defined with replay=False.'
    if not cmd.replayable:
        return False

    for n in nonLogged:
        if cmd.longname.startswith(n):
            return False
    return True

def isLoggableSheet(sheet):
    return sheet is not vd.cmdlog and not isinstance(sheet, (vd.OptionsSheet, ErrorSheet))


@Sheet.api
def moveToRow(vs, rowstr):
    'Move cursor to row given by *rowstr*, which can be either the row number or keystr.'
    rowidx = vs.getRowIndexFromStr(rowstr)
    if rowidx is None:
        return False

    vs.cursorRowIndex = rowidx

    return True

@Sheet.api
def getRowIndexFromStr(vs, row):
    prefix = vd.options.rowkey_prefix
    index = None
    if isinstance(row, int):
        index = row
    elif isinstance(row, str) and row.startswith(prefix):
        rowk = row[len(prefix):]
        index = indexMatch(vs.rows, lambda r,vs=vs,rowk=rowk: rowk == ','.join(map(str, vs.rowkey(r))))
    else:
        try:
            index = int(row)
        except ValueError:
            vd.warning('invalid type for row index')

    return index


@Sheet.api
def moveToCol(vs, col):
    'Move cursor to column given by *col*, which can be either the column number or column name.'
    if isinstance(col, str):
        vcolidx = indexMatch(vs.visibleCols, lambda c,name=col: name == c.name)
    elif isinstance(col, int):
        vcolidx = col

    if vcolidx is None or vcolidx >= vs.nVisibleCols:
        return False

    vs.cursorVisibleColIndex = vcolidx

    return True


@BaseSheet.api
def commandCursor(sheet, execstr):
    'Return (col, row) of cursor suitable for cmdlog replay of execstr.'
    colname, rowname = '', ''
    contains = lambda s, *substrs: any((a in s) for a in substrs)
    if contains(execstr, 'cursorTypedValue', 'cursorDisplay', 'cursorValue', 'cursorCell', 'cursorRow') and sheet.nRows > 0:
        rowname = sheet.cursorRowIndex

    if contains(execstr, 'cursorTypedValue', 'cursorDisplay', 'cursorValue', 'cursorCell', 'cursorCol', 'cursorVisibleCol', 'ColumnAtCursor'):
        if sheet.cursorCol:
            colname = sheet.cursorCol.name or sheet.visibleCols.index(sheet.cursorCol)
        else:
            colname = None
    return colname, rowname


# rowdef: namedlist (like TsvSheet)
class CommandLogBase:
    'Log of commands for current session.'
    rowtype = 'logged commands'
    precious = False
    _rowtype = CommandLogRow
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
                args = vd.sysclipValue().strip()


        comment = vd.currentReplayRow.comment if vd.currentReplayRow else cmd.helpstr
        vd.activeCommand = self.newRow(sheet=sheetname,
                                            col=colname,
                                            row=rowname,
                                            keystrokes=keystrokes,
                                            input=args,
                                            longname=cmd.longname,
                                            comment=comment,
                                            replayable=cmd.replayable,
                                            undofuncs=[])

    def afterExecSheet(self, sheet, escaped, err):
        'Records vd.activeCommand'
        if not vd.activeCommand:  # nothing to record
            return

        if escaped:
            vd.activeCommand = None
            return

        # remove user-aborted commands and simple movements (unless first command on the sheet, which created the sheet)
        if not sheet.cmdlog_sheet.rows or vd.isLoggableCommand(vd.activeCommand):
            if isLoggableSheet(sheet):      # don't record actions from cmdlog or other internal sheets on global cmdlog
                self.addRow(vd.activeCommand)  # add to global cmdlog
            sheet.cmdlog_sheet.addRow(vd.activeCommand)  # add to sheet-specific cmdlog

        vd.activeCommand = None

    def openHook(self, vs, src):
        while isinstance(src, BaseSheet):
            src = src.source
        r = self.newRow(keystrokes='o', input=str(src), longname='open-file', replayable=True)
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


@VisiData.api
def replay_cancel(vd):
    vd.currentReplayRow = None
    vd.currentReplay = None
    vd._nextCommands.clear()


@VisiData.api
def moveToReplayContext(vd, r, vs):
        'set the sheet/row/col to the values in the replay row'
        vs.ensureLoaded()
        vd.sync()
        vd.clearCaches()

        if r.row not in [None, '']:
            vs.moveToRow(r.row) or vd.error(f'no "{r.row}" row on {vs}')

        if r.col not in [None, '']:
            vs.moveToCol(r.col) or vd.error(f'no "{r.col}" column on {vs}')


@VisiData.api
def replayOne(vd, r):
        'Replay the command in one given row.'
        vd.currentReplayRow = r
        longname = getattr(r, 'longname', None)
        if longname is None and getattr(r, 'keystrokes', None) is None:
            vd.fail('failed to find command to replay')

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
                if vs in vd.sheets:  # if already on sheet stack, push to top
                    vd.push(vs)
            else:
                vs = vd.cmdlog

            try:
                vd.moveToReplayContext(r, vs)
                if r.comment:
                    vd.status(r.comment)

                # <=v1.2 used keystrokes in longname column; getCommand fetches both
                escaped = vs.execCommand(longname if longname else r.keystrokes, keystrokes=r.keystrokes)
            except Exception as e:
                vd.exceptionCaught(e)
                escaped = True

        vd.currentReplayRow = None

        if escaped:  # escape during replay aborts replay
            vd.warning('replay aborted during %s' % (longname or r.keystrokes))
        return escaped


@VisiData.api
class DisableAsync:
    def __enter__(self):
        vd.execAsync = vd.execSync

    def __exit__(self, exc_type, exc_val, tb):
        vd.execAsync = lambda *args, vd=vd, **kwargs: visidata.VisiData.execAsync(vd, *args, **kwargs)


@VisiData.api
def replay_sync(vd, cmdlog):
    'Replay all commands in *cmdlog*.'
    with vd.DisableAsync():
        vd.sync()  #2352 let cmdlog finish loading
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

        vd.status('replay complete')
        vd.currentReplay = None


@VisiData.api
def replay(vd, cmdlog):
    'Inject commands into live execution with interface.'
    vd.push(cmdlog)
    vd._nextCommands.extend(cmdlog.rows)


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
        if vd.activeCommand:
            if not vd.activeCommand.input:
                vd.activeCommand.input = args


@VisiData.property
def replayStatus(vd):
    if vd.macroMode:
        return f'|[:error] {len(vd.macroMode)} {vd.options.disp_replay_record} [:]'

    if vd._nextCommands:
        return f'|[:status_replay] {len(vd._nextCommands)} {vd.options.disp_replay_play} [:]'

    return ''


@BaseSheet.property
def cmdlog(sheet):
    rows = sheet.cmdlog_sheet.rows
    if isinstance(sheet.source, BaseSheet):
        rows = sheet.source.cmdlog.rows + rows
    return CommandLogJsonl(sheet.name+'_cmdlog', source=sheet, rows=rows)


@BaseSheet.lazy_property
def cmdlog_sheet(sheet):
    c = CommandLogJsonl(sheet.name+'_cmdlog', source=sheet, rows=[])
    # copy over all existing globally set options
    # you only need to do this for the first BaseSheet in a tree
    if not isinstance(sheet.source, BaseSheet):
        for r in vd.cmdlog.rows:
            if r.sheet == 'global' and (r.longname == 'set-option') or (r.longname == 'unset-option'):
                c.addRow(r)
    return c


@BaseSheet.property
def shortcut(self):
    if self._shortcut:
        return self._shortcut
    try:
        return str(vd.allSheets.index(self)+1)
    except ValueError:
        pass

    try:
        return self.cmdlog_sheet.rows[0].keystrokes or ''  #2293
    except Exception:
        pass

    return ''


@VisiData.property
def cmdlog(vd):
    if not vd._cmdlog:
        vd._cmdlog = CommandLogJsonl('cmdlog', rows=[])  # no reload
        vd._cmdlog.resetCols()
        vd.beforeExecHooks.append(vd._cmdlog.beforeExecHook)
    return vd._cmdlog

@VisiData.property
def modifyCommand(vd):
    if vd.activeCommand and vd.isLoggableCommand(vd.activeCommand):
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
BaseSheet.addCommand('^D', 'save-cmdlog', 'saveSheets(inputPath("save cmdlog to: ", value=fnSuffix(name)), vd.cmdlog)', 'save CommandLog to filename.vdj file')
BaseSheet.bindkey('^N', 'no-op')
BaseSheet.addCommand('^K', 'replay-stop', 'vd.replay_cancel(); vd.warning("replay canceled")', 'cancel current replay')

globalCommand(None, 'show-status', 'status(input("status: "))', 'show given message on status line')
globalCommand('^V', 'show-version', 'status(__version_info__);', 'Show version and copyright information on status line')
globalCommand('z^V', 'check-version', 'checkVersion(input("require version: ", value=__version_info__))', 'check VisiData version against given version')

CommandLog.addCommand('x', 'replay-row', 'vd.replayOne(cursorRow); status("replayed one row")', 'replay command in current row')
CommandLog.addCommand('gx', 'replay-all', 'vd.replay(sheet)', 'replay contents of entire CommandLog')

CommandLogJsonl.addCommand('x', 'replay-row', 'vd.replayOne(cursorRow); status("replayed one row")', 'replay command in current row')
CommandLogJsonl.addCommand('gx', 'replay-all', 'vd.replay(sheet)', 'replay contents of entire CommandLog')

CommandLog.options.json_sort_keys = False
CommandLog.options.encoding = 'utf-8'
CommandLogJsonl.options.json_sort_keys = False
CommandLogJsonl.options.regex_skip = r'^(//|#).*'

vd.addGlobals(CommandLogBase=CommandLogBase, CommandLogRow=CommandLogRow)

vd.addMenuItems('''
            View > Command log > this sheet > cmdlog-sheet
    View > Command log > this sheet only > cmdlog-sheet-only
    View > Command log > all commands > cmdlog-all
    System > Execute longname > exec-longname
    Help > Version > show-version
''')
