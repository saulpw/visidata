from functools import wraps
import curses

import visidata

__all__ = ['ENTER', 'ALT', 'ESC', 'asyncthread', 'VisiData']


ENTER='Enter'
ALT=ESC='^['

import threading

# define @asyncthread for potentially long-running functions
#   when function is called, instead launches a thread
def asyncthread(func):
    'Function decorator, to make calls to `func()` spawn a separate thread if available.'
    @wraps(func)
    def _execAsync(*args, **kwargs):
        if args and isinstance(args[0], visidata.BaseSheet):  #1136: allow cancel of async methods on Sheet
            if 'sheet' not in kwargs:
                kwargs['sheet'] = args[0]
        return visidata.vd.execAsync(func, *args, **kwargs)
    return _execAsync


class VisiData(visidata.Extensible):
    allPrefixes = ['g', 'z', 'gz', 'Alt+', 'Alt+[']  # embig'g'en, 'z'mallify, Alt/Esc=User

    @classmethod
    def global_api(cls, func):
        'Make global func() and identical vd.func()'
        def _vdfunc(*args, **kwargs):
            return getattr(visidata.vd, func.__name__)(*args, **kwargs)
        visidata.vd.addGlobals({func.__name__: func})
        setattr(cls, func.__name__, func)
        return wraps(func)(_vdfunc)

    def __init__(self):
        self.sheets = []  # list of BaseSheet; all sheets on the sheet stack
        self.allSheets = []  # list of all non-precious sheets ever pushed
        self.lastErrors = []
        self.pendingKeys = []
        self.keystrokes = ''
        self.scrFull = None
        self._cmdlog = None
        self.currentReplay = None
        self.contexts = [self]  # objects whose attributes are in the fallback context for eval/exec.
        self.importingModule = None
        self.importedModules = []
        self.activeCommands = {}  # dict of thread ident -> CommandLogRow

    @property
    def cursesEnabled(self):
        return bool(self.scrFull)

    def sheetstack(self, pane=0):
        'Return list of sheets in given *pane*. pane=0 is the active pane.  pane=-1 is the inactive pane.'
        if pane == -1:
            return list(vs for vs in self.sheets if vs.pane and (vs.pane != self.activePane))
        else:
            return list(vs for vs in self.sheets if vs.pane == (pane or self.activePane))

    @property
    def stackedSheets(self):
        return list(vs for vs in self.sheets if vs.pane)

    @property
    def activeSheet(self):
        'Return top sheet on sheets stack, or cmdlog if no sheets.'
        for vs in self.sheets:
            if vs.pane and vs.pane == self.activePane:
                return vs

        for vs in self.sheets:
            if vs.pane and vs.pane != self.activePane:
                return vs

        return self._cmdlog

    @property
    def activeStack(self):
        return self.sheetstack() or self.sheetstack(-1)

    def __copy__(self):
        'Dummy method for Extensible.init()'
        pass

    def finalInit(self):
        'Initialize members specified in other modules with init()'
        pass

    @classmethod
    def init(cls, membername, initfunc, **kwargs):
        'Overload Extensible.init() to call finalInit instead of __init__'
        oldinit = cls.finalInit
        def newinit(self, *args, **kwargs):
            oldinit(self, *args, **kwargs)
            setattr(self, membername, initfunc())
        cls.finalInit = newinit
        super().init(membername, lambda: None, **kwargs)

    def clearCaches(self):
        'Invalidate internal caches between command inputs.'
        visidata.Extensible.clear_all_caches()

    def resetVisiData(self):
        self.clearCaches()  # we want vd to return a new VisiData object for each command
        vd = visidata.vd  # get the new vd
        vd.cmdlog.rows = []
        vd.sheets = []
        vd.allSheets = []
        return vd

    def get_wch(self, scr):
        try:
            return scr.get_wch()
        except AttributeError:  #192 some packages don't have wide chars
            k = scr.getch()
            if k == -1:  # mimic get_wch behavior
                raise curses.error('no char ready')
            return k

    def drainPendingKeys(self, scr):
        '''Call scr.get_wch() until no more keypresses are available.  Return True if any keypresses are pending.'''
        scr.timeout(0)
        try:
            while True:
                k = self.get_wch(scr)
                if k:
                    self.pendingKeys.append(k)
                else:
                    break
        except curses.error:
            pass
        finally:
            scr.timeout(self.curses_timeout)

        return bool(self.pendingKeys)

    def getkeystroke(self, scr, vs=None):
        'Get keystroke and display it on status bar.'
        self.drainPendingKeys(scr)
        k = None
        if self.pendingKeys:
            k = self.pendingKeys.pop(0)
        else:
            curses.reset_prog_mode()  #1347
            try:
                scr.refresh()
                k = self.get_wch(scr)
                vs = vs or self.activeSheet
                if vs:
                    self.drawRightStatus(vs._scr, vs) # continue to display progress %
            except curses.error:
                return ''  # curses timeout

        if isinstance(k, str):
            if ord(k) >= 32 and ord(k) != 127:  # 127 == DEL or ^?
                return k
            k = ord(k)

        keyname = curses.keyname(k).decode('utf-8')
        return self.prettykeys(keyname)

    @property
    def screenHeight(self):
        return self.scrFull.getmaxyx()[0] if self.scrFull else 25

    @property
    def screenWidth(self):
        return self.scrFull.getmaxyx()[1] if self.scrFull else 80

    @property
    def activeCommand(self):
        '''Returns the active command for the current thread.
            Returns a CommandLogRow, or None.
            Returns None when no command has ever been stored for the current thread.'''
        tid = threading.get_ident()
        if tid not in self.activeCommands:
            return None
        return self.activeCommands[tid]

    @activeCommand.setter
    def activeCommand(self, value):
        tid = threading.current_thread().ident
        if value is None and (tid in self.activeCommands):
            del self.activeCommands[tid]
        else:
            self.activeCommands[tid] = value
