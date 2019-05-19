# Copyright 2017-2019 Saul Pwanson  http://visidata.org

'vdtui: a curses framework for columnar data'

from builtins import *
from unittest import mock
import sys
import os
import collections
from copy import copy, deepcopy
from contextlib import suppress
import curses
import datetime
from functools import wraps
import io
import itertools
import locale
import string
import re
import textwrap
import threading
import traceback
import time
import inspect
import weakref

class EscapeException(BaseException):
    'Inherits from BaseException to avoid "except Exception" clauses.  Do not use a blanket "except:" or the task will be uncancelable.'
    pass

class ExpectedException(Exception):
    'an expected exception'
    pass


vd = None  # will be filled in later



# undoers
def undoAttr(objs, attrname):
    'Returns a string that on eval() returns a closure that will set attrname on each obj to its former value as reference.'
    return '''lambda oldvals=[(o, getattr(o, "{attrname}")) for o in {objs}] : list(setattr(o, "{attrname}", v) for o, v in oldvals)'''.format(attrname=attrname, objs=objs)

def undoAttrCopy(objs, attrname):
    'Returns a string that on eval() returns a closure that will set attrname on each obj to its former value which is copied.'
    return '''lambda oldvals=[ (o, copy(getattr(o, "{attrname}"))) for o in {objs} ] : list(setattr(o, "{attrname}", v) for o, v in oldvals)'''.format(attrname=attrname, objs=objs)

def undoSetValues(rowstr='[cursorRow]', colstr='[cursorCol]'):
    return 'lambda oldvals=[(c, r, c.getValue(r)) for c,r in itertools.product({colstr}, {rowstr})]: list(c.setValue(r, v) for c, r, v in oldvals)'.format(rowstr=rowstr, colstr=colstr)

def undoRows(sheetstr):
    return undoAttrCopy('[%s]'%sheetstr, 'rows')

undoBlocked = 'lambda: error("cannot undo")'
undoSheetRows = undoRows('sheet')
undoSheetCols = 'lambda sheet=sheet,oldcols=[copy(c) for c in columns]: setattr(sheet, "columns", oldcols)'
undoAddCols = undoAttrCopy('[sheet]', 'columns')
undoEditCell = undoSetValues('[cursorRow]', '[cursorCol]')
undoEditCells = undoSetValues('selectedRows', '[cursorCol]')


curses_timeout = 100 # curses timeout in ms
timeouts_before_idle = 10
ENTER='^J'
ALT=ESC='^['
# _vdtype .typetype are e.g. int, float, str, and used internally in these ways:
#
#    o = typetype(val)   # for interpreting raw value
#    o = typetype(str)   # for conversion from string (when setting)
#    o = typetype()      # for default value to be used when conversion fails
#
# The resulting object o must be orderable and convertible to a string for display and certain outputs (like csv).
#
# .icon is a single character that appears in the notes field of cells and column headers.
# .formatter(fmtstr, typedvalue) returns a string of the formatted typedvalue according to fmtstr.
# .fmtstr is the default fmtstr passed to .formatter.

_vdtype = collections.namedtuple('type', 'typetype icon fmtstr formatter')

def anytype(r=None):
    'minimalist "any" passthrough type'
    return r
anytype.__name__ = ''

def _defaultFormatter(fmtstr, typedval):
    if fmtstr:
        return locale.format_string(fmtstr, typedval)
    return str(typedval)

def vdtype(typetype, icon='', fmtstr='', formatter=_defaultFormatter):
    t = _vdtype(typetype, icon, fmtstr, formatter)
    typemap[typetype] = t
    return t

# typemap [typetype] -> _vdtype
typemap = {}

def getType(typetype):
    return typemap.get(typetype) or _vdtype(anytype, None, '', _defaultFormatter)

vdtype(None, '∅')
vdtype(anytype, '', formatter=lambda _,v: str(v))
vdtype(str, '~', formatter=lambda _,v: v)
vdtype(int, '#', '%.0f')
vdtype(float, '%', '%.02f')
vdtype(dict, '')
vdtype(list, '')

def isNumeric(col):
    return col.type in (int,vlen,float,currency,date)

###

def catchapply(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        exceptionCaught(e)

def middleTruncate(s, w):
    if len(s) <= w:
        return s
    return s[:w] + options.disp_truncator + s[-w:]

def composeStatus(msgparts, n):
    msg = '; '.join(wrmap(str, msgparts))
    if n > 1:
        msg = '[%sx] %s' % (n, msg)
    return msg

def stacktrace(e=None):
    if not e:
        return traceback.format_exc().strip().splitlines()
    return traceback.format_exception_only(type(e), e)


def regex_flags():
    'Return flags to pass to regex functions from options'
    return sum(getattr(re, f.upper()) for f in options.regex_flags)


# define @asyncthread for potentially long-running functions
#   when function is called, instead launches a thread
def asyncthread(func):
    'Function decorator, to make calls to `func()` spawn a separate thread if available.'
    @wraps(func)
    def _execAsync(*args, **kwargs):
        return vd.execAsync(func, *args, **kwargs)
    return _execAsync


class Extensible:
    @classmethod
    def init(cls, membername, initfunc, **kwargs):
        'Add `self.attr=T()` to cls.__init__.  Usage: cls.init("attr", T[, copy=True])'
        oldinit = cls.__init__
        def newinit(self, *args, **kwargs):
            oldinit(self, *args, **kwargs)
            setattr(self, membername, initfunc())
        cls.__init__ = newinit

        oldcopy = cls.__copy__
        def newcopy(self, *args, **kwargs):
            ret = oldcopy(self, *args, **kwargs)
            setattr(ret, membername, getattr(self, membername) if kwargs.get('copy', False) else initfunc())
            return ret
        cls.__copy__ = newcopy

    @classmethod
    def api(cls, func):
        oldfunc = getattr(cls, func.__name__, None)
        if oldfunc:
            func = wraps(oldfunc)(func)
        setattr(cls, func.__name__, func)
        return func

    @classmethod
    def class_api(cls, func):
        name = func.__get__(None, dict).__func__.__name__
        oldfunc = getattr(cls, name, None)
        if oldfunc:
            func = wraps(oldfunc)(func)
        setattr(cls, name, func)
        return func

    @classmethod
    def property(cls, func):
        @property
        def dofunc(self):
            return func(self)
        setattr(cls, func.__name__, dofunc)
        return dofunc

    @classmethod
    def cached_property(cls, func):
        @property
        @wraps(func)
        def get_if_not(self):
            name = '_' + func.__name__
            if not hasattr(self, name):
                setattr(self, name, func(self))
            return getattr(self, name)
        setattr(cls, func.__name__, get_if_not)
        return get_if_not


class VisiData(Extensible):
    allPrefixes = ['g', 'z', ESC]  # embig'g'en, 'z'mallify, ESC=Alt/Meta

    @classmethod
    def global_api(cls, func):
        'Make global func() and identical vd.func()'
        def _vdfunc(*args, **kwargs):
            return func(vd, *args, **kwargs)
        setattr(cls, func.__name__, func)
        return wraps(func)(_vdfunc)

    def __init__(self):
        self.sheets = []  # list of BaseSheet; all sheets on the sheet stack
        self.allSheets = []  # list of all non-precious sheets ever pushed
        self.statuses = collections.OrderedDict()  # (priority, statusmsg) -> num_repeats; shown until next action
        self.statusHistory = []  # list of [priority, statusmsg, repeats] for all status messages ever
        self.lastErrors = []
        self.keystrokes = ''
        self._scr = mock.MagicMock(__bool__=mock.Mock(return_value=False))  # disable curses in batch mode
        self.mousereg = []
        self.cmdlog = None

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

    def quit(self):
        if len(vd.sheets) == 1 and options.quitguard:
            confirm("quit last sheet? ")
        return vd.sheets.pop(0)

    @property
    def sheet(self):
        'the top sheet on the stack'
        return self.sheets[0] if self.sheets else None

    def getSheet(self, sheetname):
        matchingSheets = [x for x in vd.sheets if x.name == sheetname]
        if matchingSheets:
            if len(matchingSheets) > 1:
                status('more than one sheet named "%s"' % sheetname)
            return matchingSheets[0]
        if sheetname == 'options':
            vs = self.optionsSheet
            vs.reload()
            vs.vd = vd
            return vs

    def clear_caches(self):
        'Invalidate internal caches between command inputs.'
        Sheet.visibleCols.fget.cache_clear()
        Sheet.keyCols.fget.cache_clear()
        Sheet.nHeaderRows.fget.cache_clear()
        Sheet.colsByName.fget.cache_clear()
        colors.colorcache.clear()
        self.mousereg.clear()

    def getkeystroke(self, scr, vs=None):
        'Get keystroke and display it on status bar.'
        k = None
        try:
            scr.refresh()
            k = scr.get_wch()
            self.drawRightStatus(scr, vs or self.sheets[0]) # continue to display progress %
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

    def drawLeftStatus(self, scr, vs):
        'Draw left side of status bar.'
        cattr = CursesAttr(colors.color_status)
        attr = cattr.attr
        error_attr = cattr.update_attr(colors.color_error, 1).attr
        warn_attr = cattr.update_attr(colors.color_warning, 2).attr
        sep = options.disp_status_sep

        x = 0
        y = self.windowHeight-1
        try:
            lstatus = vs.leftStatus()
            maxwidth = options.disp_lstatus_max
            if maxwidth > 0:
                lstatus = middleTruncate(lstatus, maxwidth//2)

            x = clipdraw(scr, y, 0, lstatus, attr)

            self.onMouse(scr, y, 0, 1, x,
                            BUTTON1_PRESSED='sheets',
                            BUTTON3_PRESSED='rename-sheet',
                            BUTTON3_CLICKED='rename-sheet')
        except Exception as e:
            self.exceptionCaught(e)

        one = False
        for (pri, msgparts), n in sorted(self.statuses.items(), key=lambda k: -k[0][0]):
            try:
                if x > self.windowWidth:
                    break
                if one:  # any messages already:
                    x += clipdraw(scr, y, x, sep, attr, self.windowWidth)
                one = True
                msg = composeStatus(msgparts, n)

                if pri == 3: msgattr = error_attr
                elif pri == 2: msgattr = warn_attr
                elif pri == 1: msgattr = warn_attr
                else: msgattr = attr
                x += clipdraw(scr, y, x, msg, msgattr, self.windowWidth)
            except Exception as e:
                self.exceptionCaught(e)

    def drawRightStatus(self, scr, vs):
        'Draw right side of status bar.  Return length displayed.'
        rightx = self.windowWidth-1

        ret = 0
        statcolors = [
            self.checkMemoryUsage(),
            self.rightStatus(vs),
            (self.keystrokes, 'color_keystrokes'),
        ]

        if self.cmdlog and self.cmdlog.currentReplay:
            statcolors.insert(0, (self.cmdlog.currentReplay.replayStatus, 'color_status_replay'))

        for rstatcolor in statcolors:
            if rstatcolor:
                try:
                    rstatus, coloropt = rstatcolor
                    rstatus = ' '+rstatus
                    attr = colors.get_color(coloropt).attr
                    statuslen = clipdraw(scr, self.windowHeight-1, rightx, rstatus, attr, rtl=True)
                    rightx -= statuslen
                    ret += statuslen
                except Exception as e:
                    self.exceptionCaught(e)

        if scr:
            curses.doupdate()
        return ret

    def rightStatus(self, sheet):
        'Compose right side of status bar.'
        gerund = sheet.processing
        if gerund:
            status = '%9d  %2d%%%s' % (len(sheet), sheet.progressPct, gerund)
        else:
            status = '%9d %s' % (len(sheet), sheet.rowtype)
        return status, 'color_status'

    @property
    def windowHeight(self):
        return self._scr.getmaxyx()[0] if self._scr else 25

    @property
    def windowWidth(self):
        return self._scr.getmaxyx()[1] if self._scr else 80

    def draw(self, scr, *sheets):
        'Redraw full screen.'
        for sheet in sheets:
            sheet._scr = scr
            try:
                sheet.draw(scr)
            except Exception as e:
                self.exceptionCaught(e)

        self.drawLeftStatus(scr, sheet)
        self.drawRightStatus(scr, sheet)  # visible during this getkeystroke

    def run(self, scr):
        'Manage execution of keystrokes and subsequent redrawing of screen.'
        scr.timeout(curses_timeout)
        with suppress(curses.error):
            curses.curs_set(0)

        self._scr = scr
        numTimeouts = 0
        prefixWaiting = False

        self.keystrokes = ''
        while True:
            if not self.sheets:
                # if no more sheets, exit
                return

            sheet = self.sheets[0]
            threading.current_thread().sheet = sheet

            self.draw(scr, sheet)

            keystroke = self.getkeystroke(scr, sheet)

            if keystroke:  # wait until next keystroke to clear statuses and previous keystrokes
                numTimeouts = 0
                if not prefixWaiting:
                    self.keystrokes = ''

                self.statuses.clear()

                if keystroke == 'KEY_MOUSE':
                    self.keystrokes = ''
                    clicktype = ''
                    try:
                        devid, x, y, z, bstate = curses.getmouse()
                        sheet.mouseX, sheet.mouseY = x, y
                        if bstate & curses.BUTTON_CTRL:
                            clicktype += "CTRL-"
                            bstate &= ~curses.BUTTON_CTRL
                        if bstate & curses.BUTTON_ALT:
                            clicktype += "ALT-"
                            bstate &= ~curses.BUTTON_ALT
                        if bstate & curses.BUTTON_SHIFT:
                            clicktype += "SHIFT-"
                            bstate &= ~curses.BUTTON_SHIFT

                        keystroke = clicktype + curses.mouseEvents.get(bstate, str(bstate))

                        f = self.getMouse(scr, x, y, keystroke)
                        if f:
                            if isinstance(f, str):
                                for cmd in f.split():
                                    sheet.exec_keystrokes(cmd)
                            else:
                                f(y, x, keystroke)

                            self.keystrokes = keystroke
                            keystroke = ''
                    except curses.error:
                        pass
                    except Exception as e:
                        exceptionCaught(e)

                self.keystrokes += keystroke

            self.drawRightStatus(scr, sheet)  # visible for commands that wait for input

            if not keystroke:  # timeout instead of keypress
                pass
            elif keystroke == '^Q':
                return self.lastErrors and '\n'.join(self.lastErrors[-1])
            elif bindkeys._get(self.keystrokes):
                sheet.exec_keystrokes(self.keystrokes)
                prefixWaiting = False
            elif keystroke in self.allPrefixes:
                prefixWaiting = True
            else:
                status('no command for "%s"' % (self.keystrokes))
                prefixWaiting = False

            self.checkForFinishedThreads()
            catchapply(sheet.checkCursor)

            # no idle redraw unless background threads are running
            time.sleep(0)  # yield to other threads which may not have started yet
            if vd.unfinishedThreads:
                scr.timeout(curses_timeout)
            else:
                numTimeouts += 1
                if numTimeouts > timeouts_before_idle:
                    scr.timeout(-1)
                else:
                    scr.timeout(curses_timeout)
# end VisiData class

vd = VisiData()

@VisiData.global_api
def status(self, *args, priority=0):
    'Add status message to be shown until next action.'
    k = (priority, args)
    self.statuses[k] = self.statuses.get(k, 0) + 1

    if self.statusHistory:
        prevpri, prevargs, prevn = self.statusHistory[-1]
        if prevpri == priority and prevargs == args:
            self.statusHistory[-1][2] += 1
            return True

    self.statusHistory.append([priority, args, 1])
    return True

@VisiData.global_api
def error(vd, s):
    'Log an error and raise an exception.'
    vd.status(s, priority=3)
    raise ExpectedException(s)

@VisiData.global_api
def fail(vd, s):
    vd.status(s, priority=2)
    raise ExpectedException(s)

@VisiData.global_api
def warning(vd, s):
    vd.status(s, priority=1)

@VisiData.global_api
def debug(vd, *args, **kwargs):
    if options.debug:
        return vd.status(*args, **kwargs)

@VisiData.global_api
def exceptionCaught(self, exc=None, **kwargs):
    'Maintain list of most recent errors and return most recent one.'
    if isinstance(exc, ExpectedException):  # already reported, don't log
        return
    self.lastErrors.append(stacktrace())
    if kwargs.get('status', True):
        status(self.lastErrors[-1][-1], priority=2)  # last line of latest error
    if options.debug:
        raise

###


def setupcolors(stdscr, f, *args):
    curses.raw()    # get control keys instead of signals
    curses.meta(1)  # allow "8-bit chars"
    curses.mousemask(-1) # even more than curses.ALL_MOUSE_EVENTS
    curses.mouseinterval(0) # very snappy but does not allow for [multi]click
    curses.mouseEvents = {}

    for k in dir(curses):
        if k.startswith('BUTTON') or k == 'REPORT_MOUSE_POSITION':
            curses.mouseEvents[getattr(curses, k)] = k

    return f(stdscr, *args)

def wrapper(f, *args):
    return curses.wrapper(setupcolors, f, *args)

### external interface

def run(*sheetlist):
    'Main entry point; launches vdtui with the given sheets already pushed (last one is visible)'

    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', '25')

    ret = wrapper(cursesMain, sheetlist)
    if ret:
        print(ret)

def cursesMain(_scr, sheetlist):
    'Populate VisiData object with sheets from a given list.'

    colors.setup()

    for vs in sheetlist:
        vd.push(vs)  # first push does a reload

    status('Ctrl+H opens help')
    return vd.run(_scr)

def loadConfigFile(fnrc, _globals=None):
    p = Path(fnrc)
    if p.exists():
        try:
            code = compile(open(p.resolve()).read(), p.resolve(), 'exec')
            exec(code, _globals or globals())
        except Exception as e:
            exceptionCaught(e)

def addGlobals(g):
    'importers can call `addGlobals(globals())` to have their globals accessible to execstrings'
    globals().update(g)

def getGlobals():
    return globals()

