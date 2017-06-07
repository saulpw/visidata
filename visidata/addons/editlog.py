from visidata import *

command('D', 'vd.push(vd.editlog)', 'push the editlog')
command('KEY_BACKSPACE', 'vd.editlog.undo()', 'remove last action on editlog and replay')

def open_vd(p):
    vs = EditLog(p.name, p)
    vs.loader = lambda vs=vs: reload_tsv_sync(vs)
    return vs

class EditLog(Sheet):
    """Maintain log of commands for current session."""
    current_replay_row = None  # must be global, to allow replay

    def __init__(self, name, *args):
        super().__init__(name, *args)

        self.columns = [
            ColumnItem('start_sheet', 0),
            ColumnItem('keystrokes', 1),
            ColumnItem('input', 2),
            ColumnItem('end_sheet', 3),
            ColumnItem('comment', 4),
        ]

        self.command('a', 'sheet.replay_one(cursorRow); status("replayed one row")', 'replay this editlog')
        self.command('ga', 'sheet.replay()', 'replay this editlog')

        self.sheetmap = {}
        self.current_exec_row = None

    def undo(self):
        """Delete last command, reload sources, and replay entire log."""
        if len(self.rows) < 2:
            error('no more to undo')

        deleted_row = self.rows[-2]   # the command to undo
        del self.rows[-2:]            # delete the previous command and the undo command

        vd().sheets = [self]

        self.sheetmap = {}
        for r in self.rows:
            self.replay_one(r)

        status('undid "%s"' % deleted_row[1])

    def before_exec_hook(self, sheet, keystrokes, args=''):
        """Declare initial sheet before any undos can occur.

        This is done when source is initially opened."""
        assert sheet is vd().sheets[0], (sheet.name, vd().sheets[0].name)
        if EditLog.current_replay_row is None:
            self.current_active_row = [ sheet.name, keystrokes, args, None,
                    sheet.commands[keystrokes][1] ]
            self.rows.append(self.current_active_row)

    def after_exec_sheet(self, vs, escaped):
        """Declare ending sheet for the most recent command."""
        if self.current_active_row:
            if escaped:
                del self.rows[-1]
            else:
                self.current_active_row[3] = vs.name
                before_name = self.current_active_row[0]
                after_name = self.current_active_row[3]

                # only record the sheet movement to/from the editlog
                if self.name in [before_name, after_name]:
                    if before_name == after_name:
                        del self.rows[-1]

            self.current_active_row = None

    def open_hook(self, vs, src):
        if vs:
            self.rows.append([ None, 'o', src, vs.name, 'open file' ])
            self.sheetmap[vs.name] = vs

    def replay_one(self, r):
        """Replay the command in one given row."""
        before_sheet, keystrokes, args, after_sheet = r[:4]

        EditLog.current_replay_row = r
        if before_sheet:
            vs = self.sheetmap[before_sheet]
        else:
            vs = self

        escaped = vs.exec_command(None, vs.commands[keystrokes])

        sync()

        if after_sheet not in self.sheetmap:
            self.sheetmap[after_sheet] = vd().sheets[0]

        EditLog.current_replay_row = None

    def replay(self):
        """Replay all commands in log."""
        self.sheetmap = {}

        for r in self.rows:
            self.replay_one(r)

        status('replayed entire %s' % self.name)

    def get_last_args(self):
        """Get last command, if any."""
        if EditLog.current_replay_row is not None:
            return EditLog.current_replay_row[2]
        else:
            return None

    def set_last_args(self, args):
        """Set args on any log but editlog (we don't log editlog commands)."""
        if vd().sheets[0] is not self:
            self.rows[-1][2] = args

vd().editlog = EditLog('__editlog__')

