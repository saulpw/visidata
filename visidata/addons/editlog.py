from visidata import *
import time

option('piano', 0.0, '--play piano delay in seconds')

globalCommand('D', 'vd.push(vd.editlog)', 'push the editlog')
globalCommand('^D', 'saveSheet(vd.editlog, input("save to: ", "filename", value=fnSuffix("editlog-{0}.vd") or "editlog.vd"))', 'save editlog to new file')
#globalCommand('KEY_BACKSPACE', 'vd.editlog.undo()', 'remove last action on editlog and replay')

def fnSuffix(template):
    for i in range(1, 10):
        fn = template.format(i)
        if not Path(fn).exists():
            return fn

def open_vd(p):
    vs = EditLog(p.name, p)
    vs.loader = lambda vs=vs: reload_tsv_sync(vs)
    return vs

class EditLog(Sheet):
    'Log of commands for current session.'
    commands = [
        Command('^A', 'sheet.replayOne(cursorRow); status("replayed one row")', 'replay this row of the commandlog'),
        Command('g^A', 'sheet.replay()', 'replay this entire commandlog')
    ]

    currentReplayRow = None  # must be global, to allow replay

    def __init__(self, name, *args):
        super().__init__(name, *args)
        self.currentActiveRow = None

        self.columns = [
            ColumnItem('start_sheet', 0),
            ColumnItem('keystrokes', 1),
            ColumnItem('input', 2),
            ColumnItem('end_sheet', 3),
            ColumnItem('comment', 4),
        ]

        self.sheetmap = {}
        self.currentExecRow = None

    def undo(self):
        'Delete last command, reload sources, and replay entire log.'
        if len(self.rows) < 2:
            error('no more to undo')

        deletedRow = self.rows[-2]   # the command to undo
        del self.rows[-2:]            # delete the previous command and the undo command

        vd().sheets = [self]

        self.sheetmap = {}
        for r in self.rows:
            self.replayOne(r)

        status('undid "%s"' % deletedRow[1])

    def beforeExecHook(self, sheet, keystrokes, args=''):
        'Log keystrokes and args unless replaying.'
        assert not sheet or sheet is vd().sheets[0], (sheet.name, vd().sheets[0].name)
        if EditLog.currentReplayRow is None:
            self.currentActiveRow = [ sheet.name, keystrokes, args, '', sheet._commands[keystrokes][1] ]
            self.addRow(self.currentActiveRow)

    def afterExecSheet(self, vs, escaped):
        'Set end_sheet for the most recent command.'
        if vs and self.currentActiveRow:
            if escaped:  # remove user-aborted commands
                del self.rows[-1]
            else:
                self.currentActiveRow[3] = vs.name
                beforeName = self.currentActiveRow[0]
                afterName = self.currentActiveRow[3]

                # do not record actions on the editlog itself, only sheet movement to/from
                if self.name in [beforeName, afterName]:
                    if beforeName == afterName:
                        del self.rows[-1]

            self.currentActiveRow = None

    def openHook(self, vs, src):
        if vs:
            self.addRow([ '', 'o', src, vs.name, 'open file' ])
            self.sheetmap[vs.name] = vs

    def replayOne(self, r, expectedThreads=0):
        'Replay the command in one given row.'
        beforeSheet, keystrokes, args, afterSheet = r[:4]

        EditLog.currentReplayRow = r
        if beforeSheet:
            vs = self.sheetmap.get(beforeSheet)
            if not vs:
                matchingSheets = [x for x in vd().sheets if x.name == beforeSheet]
                if not matchingSheets:
                    error('no sheets named %s' % beforeSheet)
                vs = matchingSheets[0]
        else:
            vs = self

        vd().keystrokes = keystrokes
        escaped = vs.exec_keystrokes(keystrokes)

        sync(expectedThreads)

        if afterSheet not in self.sheetmap:
            self.sheetmap[afterSheet] = vd().sheets[0]

        EditLog.currentReplayRow = None

    def replay_sync(self, live=False):
        'Replay all commands in log.'
        self.sheetmap = {}

        for r in self.rows:
#            if live:
            time.sleep(options.piano)
            vd().statuses = []
            # sync should expect this thread if playing live
            self.replayOne(r, 1 if live else 0)

        status('replayed entire %s' % self.name)

    @async
    def replay(self):
        'Inject commands into live execution with interface'
        self.replay_sync(live=True)

    def getLastArgs(self):
        'Get last command, if any.'
        if EditLog.currentReplayRow is not None:
            return EditLog.currentReplayRow[2]
        else:
            return None

    def setLastArgs(self, args):
        "Set args on any log but editlog (we don't log editlog commands)."
        if vd().sheets[0] is not self:
            self.rows[-1][2] = args

vd().editlog = EditLog('__editlog__')
vd().addHook('preexec', vd().editlog.beforeExecHook)
vd().addHook('postexec', vd().editlog.afterExecSheet)
vd().addHook('preedit', vd().editlog.getLastArgs)
vd().addHook('postedit', vd().editlog.setLastArgs)
