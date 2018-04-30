import time
import operator
import threading

from visidata import *

option('replay_wait', 0.0, 'time to wait between replayed commands, in seconds')
option('disp_replay_play', '▶', 'status indicator for active replay')
option('disp_replay_pause', '‖', 'status indicator for paused replay')
option('replay_movement', False, 'insert movements during replay')
option('visidata_dir', '~/.visidata/', 'directory to load and store macros')

globalCommand('gD', 'p=Path(options.visidata_dir); vd.push(DirSheet(p.name, source=p))', 'open .visidata directory', 'meta-visidata-dir')
globalCommand('D', 'vd.push(vd.cmdlog)', 'open CommandLog', 'meta-cmdlog')
globalCommand('^D', 'saveSheets(inputFilename("save to: ", value=fnSuffix("cmdlog-{0}.vd") or "cmdlog.vd"), vd.cmdlog)', 'save CommandLog to new .vd file', 'meta-cmdlog-save')
globalCommand('^U', 'CommandLog.togglePause()', 'pause/resume replay', 'meta-replay-toggle')
globalCommand('^I', '(CommandLog.currentReplay or error("no replay to advance")).advance()', 'execute next row in replaying sheet', 'meta-replay-step')
globalCommand('^K', '(CommandLog.currentReplay or error("no replay to cancel")).cancel()', 'cancel current replay', 'meta-replay-cancel')

globalCommand('Q', 'vd.cmdlog.removeSheet(vd.sheets.pop(0))', 'quit current sheet and remove it from the cmdlog', 'sheet-quit-remove')

globalCommand('status', 'status(input("status: ", display=False))', 'show given status message')

# not necessary to log movements and scrollers
nonLogKeys = 'KEY_DOWN KEY_UP KEY_NPAGE KEY_PPAGE j k gj gk ^F ^B r < > { } / ? n N gg G g/ g?'.split()
nonLogKeys += 'KEY_LEFT KEY_RIGHT h l gh gl c'.split()
nonLogKeys += 'zk zj zt zz zb zh zl zKEY_LEFT zKEY_RIGHT'.split()
nonLogKeys += '^L ^C ^U ^K ^I ^D ^G KEY_RESIZE KEY_F(1) z? KEY_BACKSPACE'.split()
nonLogKeys += [' ']

option('rowkey_prefix', 'キ', 'string prefix for rowkey in the cmdlog')
option('cmdlog_histfile', '', 'file to autorecord each cmdlog action to')

def itemsetter(i):
    def g(obj, v):
        obj[i] = v
    return g

def namedlist(objname, fieldnames):
    class NamedListTemplate(list):
        __name__ = objname
        _fields = fieldnames
        def __init__(self, L=None):
            if L is None:
                L = [None for f in fieldnames]
            super().__init__(L)

    for i, attrname in enumerate(fieldnames):
        # create property getter/setter for each field
        setattr(NamedListTemplate, attrname, property(operator.itemgetter(i), itemsetter(i)))

    return NamedListTemplate

CommandLogRow = namedlist('CommandLogRow', 'sheet col row keystrokes input comment'.split())

def fnSuffix(template):
    for i in range(1, 1000):
        fn = template.format(i)
        if not Path(fn).exists():
            return fn

def getColVisibleIdxByFullName(sheet, name):
    for i, c in enumerate(sheet.visibleCols):
        if name == c.name:
            return i

def keystr(k):
    return  ','.join(map(str, k))

def getRowIdxByKey(sheet, k):
    for i, r in enumerate(sheet.rows):
        if keystr(sheet.rowkey(r)) == k:
            return i

def isLoggableSheet(sheet):
    return sheet is not vd().cmdlog and not isinstance(sheet, (OptionsSheet, ErrorSheet))

def isLoggableCommand(keystrokes):
    if keystrokes in nonLogKeys:
        return False
    if keystrokes.startswith('move-'):
        return False
    if keystrokes.startswith('BUTTON'):  # mouse click
        return False
    if keystrokes.startswith('REPORT'):  # scrollwheel/mouse position
        return False
    return True

def open_vd(p):
    return CommandLog(p.name, source=p)

save_vd = save_tsv

# rowdef: CommandLogRow
class CommandLog(Sheet):
    'Log of commands for current session.'
    rowtype = 'logged commands'
    commands = [
        Command('x', 'sheet.replayOne(cursorRow); status("replayed one row")', 'replay command in current row', 'replay-row'),
        Command('gx', 'sheet.replay()', 'replay contents of entire CommandLog', 'replay-sheet'),
        Command('^C', 'sheet.cursorRowIndex = sheet.nRows', 'abort replay', 'replay-abort'),
        Command('z^S', 'sheet.saveMacro(selectedRows or error("no rows selected"), input("save macro for keystroke: "))', 'save macro', 'meta-macro-save'),
    ]
    columns = [ColumnAttr(x) for x in CommandLogRow._fields]

    paused = False
    currentReplay = None     # CommandLog replaying currently
    currentReplayRow = None  # must be global, to allow replay
    semaphore = threading.Semaphore(0)
    filetype = 'vd'

    def __init__(self, name, source=None, **kwargs):
        super().__init__(name, source=source, **kwargs)
        self.currentActiveRow = None

    def newRow(self):
        return CommandLogRow()

    @async
    def reload(self):
        reload_tsv_sync(self, header=1)  # .vd files always have a header row, regardless of options
        self.rows = [CommandLogRow(r) for r in self.rows]

    def removeSheet(self, vs):
        'Remove all traces of sheets named vs.name from the cmdlog.'
        self.rows = [r for r in self.rows if r.sheet != vs.name]
        status('removed "%s" from cmdlog' % vs.name)

    def saveMacro(self, rows, ks):
        vs = copy(self)
        vs.rows = self.selectedRows
        macropath = Path(fnSuffix(options.visidata_dir+"macro-{0}.vd"))
        save_vd(macropath, vs)
        vd().macros[ks] = vs
        append_tsv_row(vd().macrosheet, (ks, macropath.resolve()))

    def beforeExecHook(self, sheet, keystrokes, args=''):
        if not isLoggableSheet(sheet):
            return  # don't record editlog commands
        if self.currentActiveRow:
            self.afterExecSheet(sheet, False, '')

        cmd = sheet.getCommand(keystrokes)
        sheetname, colname, rowname = '', '', ''
        if sheet and keystrokes != 'o':
            contains = lambda s, *substrs: any((a in s) for a in substrs)
            sheetname = sheet.name
            if contains(cmd.execstr, 'cursorValue', 'cursorCell', 'cursorRow') and sheet.rows:
                k = sheet.rowkey(sheet.cursorRow)
                rowname = (options.rowkey_prefix + keystr(k)) if k else sheet.cursorRowIndex

            if contains(cmd.execstr, 'cursorValue', 'cursorCell', 'cursorCol', 'cursorVisibleCol'):
                colname = sheet.cursorCol.name or sheet.visibleCols.index(sheet.cursorCol)

        self.currentActiveRow = CommandLogRow([sheetname, colname, rowname, keystrokes, args, cmd.helpstr])

    def afterExecSheet(self, sheet, escaped, err):
        'Records currentActiveRow'
        if not self.currentActiveRow:  # nothing to record
            return

        if err:
            self.currentActiveRow[-1] += ' [%s]' % err

        if isLoggableSheet(sheet):  # don't record jumps to cmdlog or other internal sheets
            # remove user-aborted commands and simple movements
            if not escaped and isLoggableCommand(self.currentActiveRow.keystrokes):
                self.addRow(self.currentActiveRow)
                if options.cmdlog_histfile:
                    if not getattr(vd(), 'sessionlog', None):
                        vd().sessionlog = loadInternalSheet(CommandLog, Path(date().to_string(options.cmdlog_histfile)))
                    append_tsv_row(vd().sessionlog, self.currentActiveRow)

        self.currentActiveRow = None

    def openHook(self, vs, src):
        self.addRow(CommandLogRow(['', '', '', 'o', src, 'open file']))

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
        if not r.sheet:
#            assert not r.col and not r.row
            return self  # any old sheet should do, row/column don't matter

        try:
            sheetidx = int(r.sheet)
            vs = vd().sheets[sheetidx]
        except ValueError:
            vs = vd().getSheet(r.sheet) or error('no sheet named %s' % r.sheet)

        if r.row:
            try:
                rowidx = int(r.row)
            except ValueError:
                k = r.row[1:]  # trim rowkey_prefix
                rowidx = getRowIdxByKey(vs, k)

            if rowidx is None:
                error('no "%s" row' % r.row)

            if options.replay_movement:
                while vs.cursorRowIndex != rowidx:
                    vs.cursorRowIndex += 1 if (rowidx - vs.cursorRowIndex) > 0 else -1
                    while not self.delay(0.5):
                        pass
            else:
                vs.cursorRowIndex = rowidx

        if r.col:
            try:
                vcolidx = int(r.col)
            except ValueError:
                vcolidx = getColVisibleIdxByFullName(vs, r.col)

            if vcolidx is None:
                error('no "%s" column' % r.col)

            if options.replay_movement:
                while vs.cursorVisibleColIndex != vcolidx:
                    vs.cursorVisibleColIndex += 1 if (vcolidx - vs.cursorVisibleColIndex) > 0 else -1
                    while not self.delay(0.5):
                        pass

                assert vs.cursorVisibleColIndex == vcolidx
            else:
                vs.cursorVisibleColIndex = vcolidx
        return vs

    def delay(self, factor=1):
        'returns True if delay satisfied'
        acquired = CommandLog.semaphore.acquire(timeout=options.replay_wait*factor if not self.paused else None)
        return acquired or not self.paused

    def replayOne(self, r):
        'Replay the command in one given row.'
        CommandLog.currentReplayRow = r

        vs = self.moveToReplayContext(r)

        vd().keystrokes = r.keystrokes
        escaped = vs.exec_keystrokes(r.keystrokes)

        CommandLog.currentReplayRow = None

        if escaped:  # escape during replay aborts replay
            status('replay aborted')
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

                vd().statuses = []
                try:
                    if self.replayOne(self.cursorRow):
                        self.cancel()
                        return
                except Exception as e:
                    self.cancel()
                    exceptionCaught(e)
                    status('replay canceled')
                    return

                self.cursorRowIndex += 1
                prog.addProgress(1)

                sync(1 if live else 0)  # expect this thread also if playing live
                while not self.delay():
                    pass

        status('replay complete')
        CommandLog.currentReplay = None

    @async
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

    def setOption(self, optname, optval):
        self.addRow(CommandLogRow(['options', '', options.rowkey_prefix + optname, 'set-row-input', str(optval), 'set option']))


vd().cmdlog = CommandLog('cmdlog')
vd().cmdlog.rows = []  # so it can be added to immediately

vd().addHook('preexec', vd().cmdlog.beforeExecHook)
vd().addHook('postexec', vd().cmdlog.afterExecSheet)
vd().addHook('preedit', vd().cmdlog.getLastArgs)
vd().addHook('postedit', vd().cmdlog.setLastArgs)

vd().addHook('rstatus', lambda sheet: CommandLog.currentReplay and (CommandLog.currentReplay.replayStatus, 'green'))
vd().addHook('set_option', vd().cmdlog.setOption)

def loadMacros():
    macrospath = Path(os.path.join(options.visidata_dir, 'macros.tsv'))
    macrosheet = loadInternalSheet(TsvSheet, macrospath, columns=(ColumnItem('keystrokes', 0), ColumnItem('filename', 1))) or error('error loading macros')

    for ks, fn in macrosheet.rows:
        vd().macros[ks] = loadInternalSheet(CommandLog, Path(fn))

    return macrosheet

vd().macrosheet = loadMacros()
