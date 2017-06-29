from visidata import *

command('D', 'vd.push(vd.editlog)', 'push the editlog')
command('KEY_BACKSPACE', 'vd.editlog.undo()', 'remove last action on editlog and replay')

def open_vd(p):
    vs = EditLog(p.name, p)
    vs.loader = lambda vs=vs: reload_tsv_sync(vs)
    return vs

class EditLog(Sheet):
    'Maintain log of commands for current session.'
    currentReplayRow = None  # must be global, to allow replay

    def __init__(self, name, *args):
        super().__init__(name, *args)

        self.columns = [
            ColumnItem('start_sheet', 0),
            ColumnItem('keystrokes', 1),
            ColumnItem('input', 2),
            ColumnItem('end_sheet', 3),
            ColumnItem('comment', 4),
        ]

        self.command('a', 'sheet.replayOne(cursorRow); status("replayed one row")', 'replay this editlog')
        self.command('ga', 'sheet.replay()', 'replay this editlog')

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
        '''Declare initial sheet before any undos can occur.

        This is done when source is initially opened.'''
        assert sheet is vd().sheets[0], (sheet.name, vd().sheets[0].name)
        if EditLog.currentReplayRow is None:
            self.currentActiveRow = [ sheet.name, keystrokes, args, None,
                    sheet.commands[keystrokes][1] ]
            self.rows.append(self.currentActiveRow)

    def afterExecSheet(self, vs, escaped):
        'Declare ending sheet for the most recent command.'
        if vs and self.currentActiveRow:
            if escaped:
                del self.rows[-1]
            else:
                self.currentActiveRow[3] = vs.name
                beforeName = self.currentActiveRow[0]
                afterName = self.currentActiveRow[3]

                # only record the sheet movement to/from the editlog
                if self.name in [beforeName, afterName]:
                    if beforeName == afterName:
                        del self.rows[-1]

            self.currentActiveRow = None

    def openHook(self, vs, src):
        if vs:
            self.rows.append([ None, 'o', src, vs.name, 'open file' ])
            self.sheetmap[vs.name] = vs

    def replayOne(self, r):
        'Replay the command in one given row.'
        beforeSheet, keystrokes, args, afterSheet = r[:4]

        EditLog.currentReplayRow = r
        if beforeSheet:
            vs = self.sheetmap[beforeSheet]
        else:
            vs = self

        escaped = vs.exec_command(None, vs.commands[keystrokes])

        sync()

        if afterSheet not in self.sheetmap:
            self.sheetmap[afterSheet] = vd().sheets[0]

        EditLog.currentReplayRow = None

    def replay(self):
        'Replay all commands in log.'
        self.sheetmap = {}

        for r in self.rows:
            self.replayOne(r)

        status('replayed entire %s' % self.name)

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
