import threading

from visidata import *
import visidata

option('undo', True, 'enable undo/redo')
option('replay_wait', 0.0, 'time to wait between replayed commands, in seconds')
theme('disp_replay_play', '▶', 'status indicator for active replay')
theme('disp_replay_pause', '‖', 'status indicator for paused replay')
theme('color_status_replay', 'green', 'color of replay status indicator')
option('replay_movement', False, 'insert movements during replay')
option('visidata_dir', '~/.visidata/', 'directory to load and store macros')

globalCommand('gD', 'visidata-dir', 'p=Path(options.visidata_dir); vd.push(DirSheet(str(p), source=p))')
globalCommand('D', 'cmdlog', 'vd.push(vd.cmdlog)')
globalCommand('^D', 'save-cmdlog', 'saveSheets(inputPath("save to: ", value=fnSuffix(name)), vd.cmdlog)')
globalCommand('^U', 'pause-replay', 'CommandLog.togglePause()')
globalCommand('^I', 'advance-replay', '(CommandLog.currentReplay or fail("no replay to advance")).advance()')
globalCommand('^K', 'stop-replay', '(CommandLog.currentReplay or fail("no replay to cancel")).cancel()')

globalCommand(None, 'status', 'status(input("status: "))')
globalCommand('^V', 'show-version', 'status(__version_info__);')
globalCommand('z^V', 'check-version', 'checkVersion(input("require version: ", value=__version_info__))')

globalCommand('U', 'undo-last', 'vd.cmdlog.undo(sheet)')
globalCommand('R', 'redo-last', 'vd.cmdlog.redo(sheet)')

globalCommand(' ', 'exec-longname', 'exec_keystrokes(inputLongname(sheet))')


BaseSheet.init('undone', list)  # list of CommandLogRow for redo after undo

# prefixes which should not be logged
nonLogged = '''forget exec-longname undo redo
error status errors statuses options threads cmdlog
replay stop pause cancel advance save-cmdlog
go- search scroll prev next page go start end zoom resize
suspend redraw no-op help syscopy syspaste sysopen profile toggle'''.split()

option('rowkey_prefix', 'キ', 'string prefix for rowkey in the cmdlog')
option('cmdlog_histfile', '', 'file to autorecord each cmdlog action to')


def checkVersion(desired_version):
    if desired_version != visidata.__version_info__:
        fail("version %s required" % desired_version)

def fnSuffix(prefix):
    i = 0
    fn = prefix + '.vd'
    while Path(fn).exists():
        i += 1
        fn = f'{prefix}-{i}.vd'

    return fn

def inputLongname(sheet):
    longnames = set(k for (k, obj), v in commands.iter(sheet))
    return vd.input("command name: ", completer=CompleteKey(sorted(longnames)), type='longname')

def indexMatch(L, func):
    'returns the smallest i for which func(L[i]) is true'
    for i, x in enumerate(L):
        if func(x):
            return i

def keystr(k):
    return options.rowkey_prefix + ','.join(map(str, k))

def isLoggableSheet(sheet):
    return sheet is not vd.cmdlog and not isinstance(sheet, (OptionsSheet, ErrorSheet))

def isLoggableCommand(keystrokes, longname):
    for n in nonLogged:
        if longname.startswith(n):
            return False
    return True

def open_vd(p):
    return CommandLog(p.name, source=p)

Sheet.save_vd = Sheet.save_tsv

@Sheet.api
def moveToRow(vs, rowstr):
    rowidx = vs.getRowIndexFromStr(rowstr)
    if rowidx is None:
        return False

    if options.replay_movement:
        while vs.cursorRowIndex != rowidx:
            vs.cursorRowIndex += 1 if (rowidx - vs.cursorRowIndex) > 0 else -1
            while not self.delay(0.5):
                pass
    else:
        vs.cursorRowIndex = rowidx

    return True

@Sheet.api
def getRowIndexFromStr(vs, rowstr):
    try:
        return int(rowstr)
    except ValueError:
        index = indexMatch(vs.rows, lambda r,vs=vs,k=rowstr: keystr(vs.rowkey(r)).endswith(k))
        return index

@Sheet.api
def moveToCol(vs, colstr):
    try:
        vcolidx = int(colstr)
    except ValueError:
        vcolidx = indexMatch(vs.visibleCols, lambda c,name=colstr: name == c.name)

    if vcolidx is None:
        return False

    if options.replay_movement:
        while vs.cursorVisibleColIndex != vcolidx:
            vs.cursorVisibleColIndex += 1 if (vcolidx - vs.cursorVisibleColIndex) > 0 else -1
            while not self.delay(0.5):
                pass
    else:
        vs.cursorVisibleColIndex = vcolidx

    return True

# rowdef: namedlist (like TsvSheet)
class CommandLog(TsvSheet):
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

    paused = False
    currentReplay = None     # CommandLog replaying currently
    currentReplayRow = None  # must be global, to allow replay
    semaphore = threading.Semaphore(0)
    filetype = 'vd'

    def __init__(self, name, source=None, **kwargs):
        super().__init__(name, source=source, **kwargs)
        options.set('delimiter', '\t', self)  # enforce standard delimiter for internal tsv
        options.set('row_delimiter', '\n', self)
        self.currentActiveRow = None

    def newRow(self, **fields):
        return self._rowtype(**fields)

    def removeSheet(self, vs):
        'Remove all traces of sheets named vs.name from the cmdlog if no other sheet on the cmdlog exists and refers to it.'
        newrows = []  # without vs.name
        for cmdlogrow in self.rows:
            if cmdlogrow.sheet != vs.name:
                if getattr(vs, 'creatingCommand', None) == cmdlogrow:
                    continue
                newrows.append(cmdlogrow)
                cmdsheet = vd.getSheet(cmdlogrow.sheet)
                if cmdsheet and vs in cmdsheet:
                    return  # a sheet still on the cmdlog sources from it

        self.rows = newrows
        debug('removed "%s" from cmdlog' % vs.name)

    def beforeExecHook(self, sheet, cmd, args, keystrokes):
        if not isLoggableSheet(sheet):
            return  # don't record editlog commands
        if self.currentActiveRow:
            self.afterExecSheet(sheet, False, '')

        sheetname, colname, rowname = '', '', ''
        if sheet and cmd.longname != 'open-file':
            contains = lambda s, *substrs: any((a in s) for a in substrs)
            sheetname = sheet.name
            if contains(cmd.execstr, 'cursorTypedValue', 'cursorDisplay', 'cursorValue', 'cursorCell', 'cursorRow') and sheet.nRows > 0:
                k = sheet.rowkey(sheet.cursorRow)
                rowname = keystr(k) if k else sheet.cursorRowIndex

            if contains(cmd.execstr, 'cursorTypedValue', 'cursorDisplay', 'cursorValue', 'cursorCell', 'cursorCol', 'cursorVisibleCol'):
                colname = sheet.cursorCol.name or sheet.visibleCols.index(sheet.cursorCol)

        comment = CommandLog.currentReplayRow.comment if CommandLog.currentReplayRow else cmd.helpstr
        self.currentActiveRow = self.newRow(sheet=sheetname,
                                            col=str(colname),
                                            row=str(rowname),
                                            keystrokes=keystrokes,
                                            input=args,
                                            longname=cmd.longname,
                                            comment=comment)

        if options.undo and cmd.undo:
            self.checkpoint(cmd, sheet, self.currentActiveRow)

    @asyncthread
    def checkpoint(self, cmd, sheet, cmdlogrow):
        cmdlogrow.undofuncs = [eval(cmd.undo, getGlobals(), LazyMap(sheet))]

    def onUndo(self, undofunc):
        'On undo of latest command, call undofunc()'
        self.currentActiveRow.undofuncs.append(undofunc)

    def afterExecSheet(self, sheet, escaped, err):
        'Records currentActiveRow'
        if not self.currentActiveRow:  # nothing to record
            return

        if err:
            self.currentActiveRow[-1] += ' [%s]' % err

        if isLoggableSheet(sheet):  # don't record jumps to cmdlog or other internal sheets
            # remove user-aborted commands and simple movements
            if not escaped and isLoggableCommand(self.currentActiveRow.keystrokes, self.currentActiveRow.longname):
                self.addRow(self.currentActiveRow)
                if options.cmdlog_histfile:
                    if not getattr(vd, 'sessionlog', None):
                        vd.sessionlog = loadInternalSheet(CommandLog, Path(date().strftime(options.cmdlog_histfile)))
                    append_tsv_row(vd.sessionlog, self.currentActiveRow)

        self.currentActiveRow = None

    def openHook(self, vs, src):
        self.addRow(self.newRow(keystrokes='o', input=src, longname='open-file'))

    @classmethod
    def togglePause(self):
        if not CommandLog.currentReplay:
            status('no replay to pause')
        else:
            if self.paused:
                CommandLog.currentReplay.advance()
            self.paused = not self.paused
            status('paused' if self.paused else 'resumed')

    def advance(self):
        CommandLog.semaphore.release()

    def cancel(self):
        CommandLog.currentReplayRow = None
        CommandLog.currentReplay = None
        self.advance()

    def moveToReplayContext(self, r):
        'set the sheet/row/col to the values in the replay row.  return sheet'
        if r.sheet:
            vs = vd.getSheet(r.sheet) or error('no sheet named %s' % r.sheet)
        else:
            return None

        if r.row:
            vs.moveToRow(r.row) or error('no "%s" row' % rowstr)

        if r.col:
            vs.moveToCol(r.col) or error('no "%s" column' % r.col)

        return vs

    def delay(self, factor=1):
        'returns True if delay satisfied'
        acquired = CommandLog.semaphore.acquire(timeout=options.replay_wait*factor if not self.paused else None)
        return acquired or not self.paused

    def replayOne(self, r):
        'Replay the command in one given row.'
        CommandLog.currentReplayRow = r

        longname = getattr(r, 'longname', None)
        if longname == 'set-option':
            try:
                options.set(r.row, r.input, options._opts.getobj(r.col))
                escaped = False
            except Exception as e:
                exceptionCaught(e)
                escaped = True
        else:
            vs = self.moveToReplayContext(r)
            if vs:
                vd.push(vs)
            else:
                vs = self  # any old sheet should do, row/column don't matter

            if r.comment:
                status(r.comment)

            vd.keystrokes = r.keystrokes
            # <=v1.2 used keystrokes in longname column; getCommand fetches both
            escaped = vs.exec_command(vs.getCommand(longname if longname else r.keystrokes), keystrokes=r.keystrokes)

        CommandLog.currentReplayRow = None

        if escaped:  # escape during replay aborts replay
            warning('replay aborted during %s' % (longname or r.keystrokes))
        return escaped

    def replay_sync(self, live=False):
        'Replay all commands in log.'
        self.cursorRowIndex = 0
        CommandLog.currentReplay = self
        with Progress(total=len(self.rows)) as prog:
            while self.cursorRowIndex < len(self.rows):
                if CommandLog.currentReplay is None:
                    status('replay canceled')
                    return

                vd.statuses.clear()
                try:
                    if self.replayOne(self.cursorRow):
                        self.cancel()
                        return True
                except Exception as e:
                    self.cancel()
                    exceptionCaught(e)
                    status('replay canceled')
                    return True

                self.cursorRowIndex += 1
                prog.addProgress(1)

                vd.sync()
                while not self.delay():
                    pass

        status('replay complete')
        CommandLog.currentReplay = None

    @asyncthread
    def replay(self):
        'Inject commands into live execution with interface.'
        self.replay_sync(live=True)

    def getLastArgs(self):
        'Get user input for the currently playing command.'
        if CommandLog.currentReplayRow:
            return CommandLog.currentReplayRow.input
        return None

    def setLastArgs(self, args):
        'Set user input on last command, if not already set.'
        # only set if not already set (second input usually confirmation)
        if self.currentActiveRow is not None:
            if not self.currentActiveRow.input:
                self.currentActiveRow.input = args

    @property
    def replayStatus(self):
        x = options.disp_replay_pause if self.paused else options.disp_replay_play
        return ' │ %s %s/%s' % (x, self.cursorRowIndex, len(self.rows))

    def set_option(self, optname, optval, obj=None):
        objname = options._opts.objname(obj)
        self.addRow(self.newRow(col=objname, row=optname,
                    keystrokes='', input=str(optval),
                    longname='set-option'))

    def undo(self, sheet):
        if not options.undo:
            fail("options.undo not enabled")

        for cmdlogrow in self.rows[::-1]:
            if cmdlogrow.undofuncs and str(cmdlogrow.sheet) == sheet.name:
                for undofunc in cmdlogrow.undofuncs:
                    undofunc()
                sheet.undone.append(cmdlogrow)
                self.rows.remove(cmdlogrow)
                vd.clear_caches()
                status("%s undone" % cmdlogrow.longname)
                return

        fail("nothing to undo on current sheet")

    def redo(self, sheet):
        sheet.undone or fail("nothing to redo")
        cmdlogrow = sheet.undone.pop()
        self.replayOne(cmdlogrow)
        status("%s redone" % cmdlogrow.longname)


CommandLog.addCommand('x', 'replay-row', 'sheet.replayOne(cursorRow); status("replayed one row")')
CommandLog.addCommand('gx', 'replay-all', 'sheet.replay()')
CommandLog.addCommand('^C', 'stop-replay', 'sheet.cursorRowIndex = sheet.nRows')
options.set('header', 1, CommandLog)  # .vd files always have a header row, regardless of options

def initCmdlog():
    vs = CommandLog('cmdlog')
    vs.rows = []
    return vs

VisiData.init('cmdlog', initCmdlog)
