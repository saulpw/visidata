import threading

from visidata import *
import visidata

option('replay_wait', 0.0, 'time to wait between replayed commands, in seconds')
theme('disp_replay_play', '▶', 'status indicator for active replay')
theme('disp_replay_pause', '‖', 'status indicator for paused replay')
theme('color_status_replay', 'green', 'color of replay status indicator')
option('replay_movement', False, 'insert movements during replay')
option('visidata_dir', '~/.visidata/', 'directory to load and store macros')

globalCommand('gD', 'visidata-dir', 'p=Path(options.visidata_dir); vd.push(DirSheet(str(p), source=p))')
globalCommand('D', 'cmdlog', 'vd.push(vd.cmdlog)')
globalCommand('^D', 'save-cmdlog', 'saveSheets(inputFilename("save to: ", value=fnSuffix("cmdlog-{0}.vd") or "cmdlog.vd"), vd.cmdlog)')
globalCommand('^U', 'pause-replay', 'CommandLog.togglePause()')
globalCommand('^I', 'advance-replay', '(CommandLog.currentReplay or fail("no replay to advance")).advance()')
globalCommand('^K', 'stop-replay', '(CommandLog.currentReplay or fail("no replay to cancel")).cancel()')

globalCommand('Q', 'forget-sheet', 'vd.cmdlog.removeSheet(vd.sheets.pop(0))')

globalCommand(None, 'status', 'status(input("status: "))')
globalCommand('^V', 'check-version', 'status(__version_info__); checkVersion(input("require version: ", value=__version_info__))')

# not necessary to log movements and scrollers
nonLogKeys = 'KEY_DOWN KEY_UP KEY_NPAGE KEY_PPAGE j k gj gk ^F ^B r < > { } / ? n N gg G g/ g? g_ _ z_'.split()
nonLogKeys += 'KEY_LEFT KEY_RIGHT h l gh gl c Q'.split()
nonLogKeys += 'zk zj zt zz zb zh zl zKEY_LEFT zKEY_RIGHT'.split()
nonLogKeys += '^^ ^Z ^A ^L ^C ^U ^K ^I ^D ^G KEY_RESIZE KEY_F(1) ^H KEY_BACKSPACE'.split()
nonLogKeys += [' ']

option('rowkey_prefix', 'キ', 'string prefix for rowkey in the cmdlog')
option('cmdlog_histfile', '', 'file to autorecord each cmdlog action to')


def checkVersion(desired_version):
    if desired_version != visidata.__version__:
        fail("version %s required" % desired_version)

def fnSuffix(template):
    for i in range(1, 1000):
        fn = template.format(i)
        if not Path(fn).exists():
            return fn

def indexMatch(L, func):
    'returns the smallest i for which func(L[i]) is true'
    for i, x in enumerate(L):
        if func(x):
            return i

def keystr(k):
    return options.rowkey_prefix + ','.join(map(str, k))

def isLoggableSheet(sheet):
    return sheet is not vd().cmdlog and not isinstance(sheet, (OptionsSheet, ErrorSheet))

def isLoggableCommand(keystrokes, longname):
    if keystrokes in nonLogKeys:
        return False
    if longname.startswith('go-'):
        return False
    if keystrokes.startswith('BUTTON'):  # mouse click
        return False
    if keystrokes.startswith('REPORT'):  # scrollwheel/mouse position
        return False
    return True

def open_vd(p):
    return CommandLog(p.name, source=p)

save_vd = save_tsv

# rowdef: namedlist (like TsvSheet)
class CommandLog(TsvSheet):
    'Log of commands for current session.'
    rowtype = 'logged commands'
    precious = False
    _rowtype = namedlist('CommandLogRow', 'sheet col row longname input keystrokes comment'.split())
    columns = [ColumnAttr(x) for x in _rowtype._fields]

    paused = False
    currentReplay = None     # CommandLog replaying currently
    currentReplayRow = None  # must be global, to allow replay
    semaphore = threading.Semaphore(0)
    filetype = 'vd'

    def __init__(self, name, source=None, **kwargs):
        super().__init__(name, source=source, **kwargs)
        self.currentActiveRow = None

    def newRow(self, **fields):
        return self._rowtype(**fields)

    def removeSheet(self, vs):
        'Remove all traces of sheets named vs.name from the cmdlog.'
        self.rows = [r for r in self.rows if r.sheet != vs.name]
        status('removed "%s" from cmdlog' % vs.name)

    def saveMacro(self, rows, ks):
        vs = copy(self)
        vs.rows = self.selectedRows
        macropath = Path(fnSuffix(options.visidata_dir+"macro-{0}.vd"))
        save_vd(macropath, vs)
        setMacro(ks, vs)
        append_tsv_row(vd().macrosheet, (ks, macropath.resolve()))

    def beforeExecHook(self, sheet, cmd, args, keystrokes):
        if not isLoggableSheet(sheet):
            return  # don't record editlog commands
        if self.currentActiveRow:
            self.afterExecSheet(sheet, False, '')

        sheetname, colname, rowname = '', '', ''
        if sheet and cmd.longname != 'open-file':
            contains = lambda s, *substrs: any((a in s) for a in substrs)
            sheetname = sheet.name
            if contains(cmd.execstr, 'cursorTypedValue', 'cursorDisplay', 'cursorValue', 'cursorCell', 'cursorRow') and sheet.rows:
                k = sheet.rowkey(sheet.cursorRow)
                rowname = keystr(k) if k else sheet.cursorRowIndex

            if contains(cmd.execstr, 'cursorTypedValue', 'cursorDisplay', 'cursorValue', 'cursorCell', 'cursorCol', 'cursorVisibleCol'):
                colname = sheet.cursorCol.name or sheet.visibleCols.index(sheet.cursorCol)

        comment = CommandLog.currentReplayRow.comment if CommandLog.currentReplayRow else cmd.helpstr
        self.currentActiveRow = self.newRow(sheet=sheetname, col=colname, row=rowname,
                                              keystrokes=keystrokes, input=args,
                                              longname=cmd.longname, comment=comment)

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
                    if not getattr(vd(), 'sessionlog', None):
                        vd().sessionlog = loadInternalSheet(CommandLog, Path(date().strftime(options.cmdlog_histfile)))
                    append_tsv_row(vd().sessionlog, self.currentActiveRow)

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
                rowidx = indexMatch(vs.rows, lambda r,vs=vs,k=r.row: keystr(vs.rowkey(r)) == k)

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
                vcolidx = indexMatch(vs.visibleCols, lambda c,name=r.col: name == c.name)

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

            vd().keystrokes = r.keystrokes
            # <=v1.2 used keystrokes in longname column; getCommand fetches both
            escaped = vs.exec_command(vs.getCommand(longname if longname else r.keystrokes), keystrokes=r.keystrokes)

        CommandLog.currentReplayRow = None

        if escaped:  # escape during replay aborts replay
            warning('replay aborted')
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

                vd().statuses.clear()
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

    def setOption(self, optname, optval, obj=None):
        objname = options._opts.objname(obj)
        self.addRow(self.newRow(col=objname, row=optname,
                    keystrokes='', input=str(optval),
                    longname='set-option'))

CommandLog.addCommand('x', 'replay-row', 'sheet.replayOne(cursorRow); status("replayed one row")')
CommandLog.addCommand('gx', 'replay-all', 'sheet.replay()')
CommandLog.addCommand('^C', 'stop-replay', 'sheet.cursorRowIndex = sheet.nRows')
CommandLog.addCommand('z^S', 'save-macro', 'sheet.saveMacro(selectedRows or fail("no rows selected"), input("save macro for keystroke: "))')
options.set('header', 1, CommandLog)  # .vd files always have a header row, regardless of options

vd().cmdlog = CommandLog('cmdlog')
vd().cmdlog.rows = []

vd().addHook('preexec', vd().cmdlog.beforeExecHook)
vd().addHook('postexec', vd().cmdlog.afterExecSheet)
vd().addHook('preedit', vd().cmdlog.getLastArgs)
vd().addHook('postedit', vd().cmdlog.setLastArgs)

vd().addHook('rstatus', lambda sheet: CommandLog.currentReplay and (CommandLog.currentReplay.replayStatus, 'color_status_replay'))
vd().addHook('set_option', vd().cmdlog.setOption)

def loadMacros():
    macrospath = Path(os.path.join(options.visidata_dir, 'macros.tsv'))
    macrosheet = loadInternalSheet(TsvSheet, macrospath, columns=(ColumnItem('command', 0), ColumnItem('filename', 1))) or error('error loading macros')

    for ks, fn in macrosheet.rows:
        vs = loadInternalSheet(CommandLog, Path(fn))
        setMacro(ks, vs)

    return macrosheet

def setMacro(ks, vs):
    bindkeys.set(ks, vs.name, 'override')
    commands.set(vs.name, vs, 'override')

vd().macrosheet = loadMacros()
