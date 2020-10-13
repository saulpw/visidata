from functools import wraps
from unittest import mock
import curses

import visidata

__all__ = ['ENTER', 'ALT', 'ESC', 'asyncthread', 'VisiData', 'drawcache', 'drawcache_property']


ENTER='^J'
ALT=ESC='^['


# define @asyncthread for potentially long-running functions
#   when function is called, instead launches a thread
def asyncthread(func):
    'Function decorator, to make calls to `func()` spawn a separate thread if available.'
    @wraps(func)
    def _execAsync(*args, **kwargs):
        return visidata.vd.execAsync(func, *args, **kwargs)
    return _execAsync

# @drawcache is vd alias for @cache, since vd clears it every frame
drawcache = visidata.cache

def drawcache_property(func):
    return property(drawcache(func))


class VisiData(visidata.Extensible):
    allPrefixes = ['g', 'z', ESC]  # embig'g'en, 'z'mallify, ESC=Alt/Meta

    @classmethod
    def global_api(cls, func):
        'Make global func() and identical vd.func()'
        def _vdfunc(*args, **kwargs):
            return func(visidata.vd, *args, **kwargs)
        setattr(cls, func.__name__, func)
        return wraps(func)(_vdfunc)

    def __init__(self):
        self.sheets = []  # list of BaseSheet; all sheets on the sheet stack
        self.allSheets = []  # list of all non-precious sheets ever pushed
        self.lastErrors = []
        self.keystrokes = ''
        self.scrFull = mock.MagicMock(__bool__=mock.Mock(return_value=False))  # disable curses in batch mode
        self.cmdlog = None

    @drawcache_property
    def mousereg(self):
        return []

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

    def getkeystroke(self, scr, vs=None):
        'Get keystroke and display it on status bar.'
        k = None
        try:
            scr.refresh()
            k = scr.get_wch()
            vs = vs or self.sheets[0]
            self.drawRightStatus(vs._scr, vs) # continue to display progress %
        except curses.error:
            return ''  # curses timeout

        if isinstance(k, str):
            if ord(k) >= 32 and ord(k) != 127:  # 127 == DEL or ^?
                return k
            k = ord(k)
        return curses.keyname(k).decode('utf-8')

    def onMouse(self, scr, y, x, h, w, **kwargs):
        self.mousereg.append((scr, y, x, h, w, kwargs))

    def getMouse(self, _scr, _x, _y, button):
        for scr, y, x, h, w, kwargs in self.mousereg[::-1]:
            if scr == _scr and x <= _x < x+w and y <= _y < y+h and button in kwargs:
                return kwargs[button]

    @property
    def screenHeight(self):
        return self.scrFull.getmaxyx()[0] if self.scrFull else 25

    @property
    def screenWidth(self):
        return self.scrFull.getmaxyx()[1] if self.scrFull else 80
