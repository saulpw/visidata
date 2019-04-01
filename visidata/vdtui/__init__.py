# Copyright 2017-2018 Saul Pwanson  http://visidata.org

'vdtui: a curses framework for columnar data'

from builtins import *
from inspect import isclass
from unittest import mock
import sys
import os
import collections
from collections import defaultdict
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


# [settingname] -> { objname(Sheet-instance/Sheet-type/'override'/'global'): Option/Command/longname }
class SettingsMgr(collections.OrderedDict):
    def __init__(self):
        super().__init__()
        self.allobjs = {}

    def objname(self, obj):
        if isinstance(obj, str):
            v = obj
        elif obj is None:
            v = 'override'
        elif isinstance(obj, BaseSheet):
            v = obj.name
        elif isclass(obj) and issubclass(obj, BaseSheet):
            v = obj.__name__
        else:
            return None

        self.allobjs[v] = obj
        return v

    def getobj(self, objname):
        'Inverse of objname(obj); returns obj if available'
        return self.allobjs.get(objname)

    def unset(self, k, obj='global'):
        del self[k][self.objname(obj)]

    def set(self, k, v, obj='override'):
        'obj is a Sheet instance, or a Sheet [sub]class.  obj="override" means override all; obj="default" means last resort.'
        if k not in self:
            self[k] = dict()
        self[k][self.objname(obj)] = v
        return v

    def setdefault(self, k, v):
        return self.set(k, v, 'global')

    def _mappings(self, obj):
        if obj:
            mappings = [self.objname(obj)]
            mro = [self.objname(cls) for cls in inspect.getmro(type(obj))]
            mappings.extend(mro)
        else:
            mappings = []

        mappings += ['override', 'global']
        return mappings

    def _get(self, key, obj=None):
        d = self.get(key, None)
        if d:
            for m in self._mappings(obj or vd.sheet):
                v = d.get(m)
                if v:
                    return v

    def iter(self, obj=None):
        'Iterate through all keys considering context of obj. If obj is None, uses the context of the top sheet.'
        if obj is None and vd:
            obj = vd.sheet

        for o in self._mappings(obj):
            for k in self.keys():
                for o2 in self[k]:
                    if o == o2:
                        yield (k, o), self[k][o2]


class Command:
    def __init__(self, longname, execstr, helpstr='', undo=''):
        self.longname = longname
        self.execstr = execstr
        self.helpstr = helpstr
        self.undo = undo

def globalCommand(keystrokes, longname, execstr, helpstr='', **kwargs):
    commands.setdefault(longname, Command(longname, execstr, helpstr=helpstr, **kwargs))

    if keystrokes:
        assert not bindkeys._get(keystrokes), keystrokes
        bindkeys.setdefault(keystrokes, longname)

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

def bindkey(keystrokes, longname):
    bindkeys.setdefault(keystrokes, longname)

def bindkey_override(keystrokes, longname):
    bindkeys.set(keystrokes, longname)

def unbindkey(keystrokes):
    bindkeys.unset(keystrokes)

class Option:
    def __init__(self, name, value, helpstr=''):
        self.name = name
        self.value = value
        self.helpstr = helpstr
        self.replayable = False

    def __str__(self):
        return str(self.value)


class OptionsObject:
    'minimalist options framework'
    def __init__(self, mgr):
        object.__setattr__(self, '_opts', mgr)
        object.__setattr__(self, '_cache', {})

    def keys(self, obj=None):
        for k, d in self._opts.items():
            if obj is None or self._opts.objname(obj) in d:
                yield k

    def _get(self, k, obj=None):
        'Return Option object for k in context of obj. Cache result until any set().'
        opt = self._cache.get((k, obj), None)
        if opt is None:
            opt = self._opts._get(k, obj)
            self._cache[(k, obj or vd.sheet)] = opt
        return opt

    def _set(self, k, v, obj=None, helpstr=''):
        self._cache.clear()  # invalidate entire cache on any set()
        return self._opts.set(k, Option(k, v, helpstr), obj)

    def get(self, k, obj=None):
        return self._get(k, obj).value

    def getdefault(self, k):
        return self._get(k, 'global').value

    def set(self, k, v, obj='override'):
        opt = self._get(k)
        if opt:
            curval = opt.value
            t = type(curval)
            if v is None and curval is not None:
                v = t()           # empty value
            elif isinstance(v, str) and t is bool: # special case for bool options
                v = v and (v[0] not in "0fFnN")  # ''/0/false/no are false, everything else is true
            elif type(v) is t:    # if right type, no conversion
                pass
            elif curval is None:  # if None, do not apply type conversion
                pass
            else:
                v = t(v)

            if curval != v and self._get(k, 'global').replayable:
                if vd.cmdlog:  # options set on init aren't recorded
                    vd.cmdlog.set_option(k, v, obj)
        else:
            curval = None
            warning('setting unknown option %s' % k)

        return self._set(k, v, obj)

    def setdefault(self, k, v, helpstr):
        return self._set(k, v, 'global', helpstr=helpstr)

    def getall(self, kmatch):
        return {obj:opt for (k, obj), opt in self._opts.items() if k == kmatch}

    def __getattr__(self, k):      # options.foo
        return self.__getitem__(k)

    def __setattr__(self, k, v):   # options.foo = v
        self.__setitem__(k, v)

    def __getitem__(self, k):      # options[k]
        opt = self._get(k)
        if not opt:
            error('no option "%s"' % k)
        return opt.value

    def __setitem__(self, k, v):   # options[k] = v
        self.set(k, v)

    def __call__(self, prefix=''):
        return { optname[len(prefix):] : options[optname]
                    for optname in options.keys()
                        if optname.startswith(prefix) }


commands = SettingsMgr()
bindkeys = SettingsMgr()
_options = SettingsMgr()
options = OptionsObject(_options)

def option(name, default, helpstr, replay=False):
    opt = options.setdefault(name, default, helpstr)
    opt.replayable = replay
    return opt

theme = option
def replayableOption(optname, default, helpstr):
    option(optname, default, helpstr, replay=True)


replayableOption('encoding', 'utf-8', 'encoding passed to codecs.open')
replayableOption('encoding_errors', 'surrogateescape', 'encoding_errors passed to codecs.open')

replayableOption('regex_flags', 'I', 'flags to pass to re.compile() [AILMSUX]')
replayableOption('default_width', 20, 'default column width')

option('cmd_after_edit', 'go-down', 'command longname to execute after successful edit')
option('quitguard', False, 'confirm before quitting last sheet')

replayableOption('force_valid_colnames', False, 'clean column names to be valid Python identifiers')
option('debug', False, 'exit on error and display stacktrace')
curses_timeout = 100 # curses timeout in ms
timeouts_before_idle = 10
theme('force_256_colors', False, 'use 256 colors even if curses reports fewer')
theme('use_default_colors', False, 'curses use default terminal colors')

theme('disp_note_none', '⌀',  'visible contents of a cell whose value is None')
theme('disp_truncator', '…', 'indicator that the contents are only partially visible')
theme('disp_oddspace', '\u00b7', 'displayable character for odd whitespace')
theme('disp_column_sep', '|', 'separator between columns')
theme('disp_keycol_sep', '\u2016', 'separator between key columns and rest of columns')
theme('disp_status_fmt', '[{sheet.num}] {sheet.name}| ', 'status line prefix')
theme('disp_lstatus_max', 0, 'maximum length of left status line')
theme('disp_status_sep', ' | ', 'separator between statuses')
theme('disp_more_left', '<', 'header note indicating more columns to the left')
theme('disp_more_right', '>', 'header note indicating more columns to the right')
theme('disp_error_val', '', 'displayed contents for computation exception')
theme('disp_ambig_width', 1, 'width to use for unicode chars marked ambiguous')

theme('color_keystrokes', 'white', 'color of input keystrokes on status line')
theme('color_status', 'bold', 'status line color')
theme('color_error', 'red', 'error message color')
theme('color_warning', 'yellow', 'warning message color')

theme('disp_pending', '', 'string to display in pending cells')
theme('note_pending', '⌛', 'note to display for pending cells')
theme('note_format_exc', '?', 'cell note for an exception during formatting')
theme('note_getter_exc', '!', 'cell note for an exception during computation')
theme('note_type_exc', '!', 'cell note for an exception during type conversion')
theme('note_unknown_type', '', 'cell note for unknown types in anytype column')

theme('color_note_pending', 'bold magenta', 'color of note in pending cells')
theme('color_note_type', '226 yellow', 'cell note for numeric types in anytype columns')
theme('scroll_incr', 3, 'amount to scroll with scrollwheel')

ENTER='^J'
ALT=ESC='^['
globalCommand('KEY_RESIZE', 'no-op', '')
globalCommand('q', 'quit-sheet',  'vd.quit()')
globalCommand('gq', 'quit-all', 'vd.sheets.clear()')

globalCommand('^L', 'redraw', 'vd.scr.clear()')
globalCommand('^^', 'prev-sheet', 'vd.sheets[1:] or fail("no previous sheet"); vd.sheets[0], vd.sheets[1] = vd.sheets[1], vd.sheets[0]')

globalCommand('^Z', 'suspend', 'suspend()')

bindkey('KEY_RESIZE', 'redraw')

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
    return typemap.get(typetype) or _vdtype(anytype, '', '', _defaultFormatter)

def typeIcon(typetype):
    t = typemap.get(typetype, None)
    if t:
        return t.icon

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

    def __call__(self):
        'Deprecated; use plain "vd"'
        return self

    @classmethod
    def global_api(cls, func):
        'Make global func() and identical vd.func()'
        def _vdfunc(*args, **kwargs):
            return func(vd, *args, **kwargs)
        setattr(vd, func.__name__, _vdfunc)
        return wraps(func)(_vdfunc)

    def __init__(self):
        self.sheets = []  # list of BaseSheet; all sheets on the sheet stack
        self.allSheets = []  # list of all non-precious sheets ever pushed
        self.statuses = collections.OrderedDict()  # (priority, statusmsg) -> num_repeats; shown until next action
        self.statusHistory = []  # list of [priority, statusmsg, repeats] for all status messages ever
        self.lastErrors = []
        self.keystrokes = ''
        self.prefixWaiting = False
        self.scr = mock.MagicMock(__bool__=mock.Mock(return_value=False))  # disable curses in batch mode
        self.mousereg = []
        self.cmdlog = None  # CommandLog

    def quit(self):
        if len(vd.sheets) == 1 and options.quitguard:
            confirm("quit last sheet? ")
        return vd.sheets.pop(0)

    @property
    def sheet(self):
        'the top sheet on the stack'
        return self.sheets[0] if self.sheets else None

    @property
    def nSheets(self):
        return len(self.sheets)

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
        return self.scr.getmaxyx()[0] if self.scr else 25

    @property
    def windowWidth(self):
        return self.scr.getmaxyx()[1] if self.scr else 80

    def run(self, scr):
        'Manage execution of keystrokes and subsequent redrawing of screen.'
        scr.timeout(curses_timeout)
        with suppress(curses.error):
            curses.curs_set(0)

        self.scr = scr
        numTimeouts = 0

        self.keystrokes = ''
        while True:
            if not self.sheets:
                # if no more sheets, exit
                return

            sheet = self.sheets[0]
            threading.current_thread().sheet = sheet

            try:
                sheet.draw(scr)
            except Exception as e:
                self.exceptionCaught(e)

            self.drawLeftStatus(scr, sheet)
            self.drawRightStatus(scr, sheet)  # visible during this getkeystroke

            keystroke = self.getkeystroke(scr, sheet)

            if keystroke:  # wait until next keystroke to clear statuses and previous keystrokes
                numTimeouts = 0
                if not self.prefixWaiting:
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
                self.prefixWaiting = False
            elif keystroke in self.allPrefixes:
                self.prefixWaiting = True
            else:
                status('no command for "%s"' % (self.keystrokes))
                self.prefixWaiting = False

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

    def replace(self, vs):
        'Replace top sheet with the given sheet `vs`.'
        self.sheets.pop(0)
        return self.push(vs)

    def remove(self, vs):
        if vs in self.sheets:
            self.sheets.remove(vs)
        else:
            fail('sheet not on stack')

    def push(self, vs):
        'Move given sheet `vs` to index 0 of list `sheets`.'
        if vs:
            vs.vd = self
            if vs in self.sheets:
                self.sheets.remove(vs)
            else:
                vs.creatingCommand = self.cmdlog and self.cmdlog.currentActiveRow

            self.sheets.insert(0, vs)

            if not vs.loaded:
                vs.reload()
                vs.recalc()  # set up Columns

            if vs.precious and vs not in vs.vd.allSheets:
                vs.vd.allSheets.append(vs)
            return vs
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

class LazyMap:
    'provides a lazy mapping to obj attributes.  useful when some attributes are expensive properties.'
    def __init__(self, *objs):
        self.locals = {}
        self.objs = {} # [k] -> obj
        for obj in objs:
            for k in dir(obj):
                if k not in self.objs:
                    self.objs[k] = obj

    def keys(self):
        return list(self.objs.keys())  # sum(set(dir(obj)) for obj in self.objs))

    def clear(self):
        self.locals.clear()

    def __getitem__(self, k):
        obj = self.objs.get(k, None)
        if obj:
            return getattr(obj, k)
        return self.locals[k]

    def __setitem__(self, k, v):
        obj = self.objs.get(k, None)
        if obj:
            return setattr(obj, k, v)
        self.locals[k] = v

@asyncthread
def exec_shell(*args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err or out:
        lines = err.decode('utf8').splitlines() + out.decode('utf8').splitlines()
        vd.push(TextSheet(' '.join(args), lines))

class BaseSheet(Extensible):
    _rowtype = object    # callable (no parms) that returns new empty item
    _coltype = None      # callable (no parms) that returns new settable view into that item
    rowtype = 'objects'  # one word, plural, describing the items
    precious = True      # False for a few discardable metasheets

    def __init__(self, name, **kwargs):
        self.name = name
        self.source = None

        # track all async threads from sheet
        self.__dict__.update(kwargs)

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        else:
            return id(self) < id(other)

    def __copy__(self):
        cls = self.__class__
        ret = cls.__new__(cls)
        ret.__dict__.update(self.__dict__)
        ret.precious = True  # copies can be precious even if originals aren't
        return ret

    @classmethod
    def addCommand(cls, keystrokes, longname, execstr, helpstr='', **kwargs):
        commands.set(longname, Command(longname, execstr, helpstr=helpstr, **kwargs), cls)
        if keystrokes:
            bindkeys.set(keystrokes, longname, cls)

    @classmethod
    def bindkey(cls, keystrokes, longname):
        oldlongname = bindkeys._get(keystrokes, cls)
        if oldlongname:
            warning('%s was already bound to %s' % (keystrokes, oldlongname))
        bindkeys.set(keystrokes, longname, cls)

    @classmethod
    def unbindkey(cls, keystrokes):
        bindkeys.unset(keystrokes, cls)

    def getCommand(self, keystrokes_or_longname):
        longname = bindkeys._get(keystrokes_or_longname)
        try:
            if longname:
                return commands._get(longname) or fail('no command "%s"' % longname)
            else:
                return commands._get(keystrokes_or_longname) or fail('no binding for %s' % keystrokes_or_longname)
        except Exception:
            return None

    def __bool__(self):
        'an instantiated Sheet always tests true'
        return True

    def __len__(self):
        return 0

    def __contains__(self, vs):
        if self.source is vs:
            return True
        if isinstance(self.source, BaseSheet):
            return vs in self.source
        return False

    @property
    def loaded(self):
        return False

    @property
    def num(self):
        if self in vd.allSheets:
            return str(vd.allSheets.index(self)+1)

        if hasattr(self, 'creatingCommand') and self.creatingCommand:
            return self.creatingCommand.keystrokes

        return ''

    def leftStatus(self):
        'Compose left side of status bar for this sheet (overridable).'
        return options.disp_status_fmt.format(sheet=self, vd=vd)

    def exec_keystrokes(self, keystrokes, vdglobals=None):
        return self.exec_command(self.getCommand(keystrokes), vdglobals, keystrokes=keystrokes)

    def exec_command(self, cmd, args='', vdglobals=None, keystrokes=None):
        "Execute `cmd` tuple with `vdglobals` as globals and this sheet's attributes as locals.  Returns True if user cancelled."
        if not cmd:
            debug('no command "%s"' % keystrokes)
            return True

        if isinstance(cmd, CommandLog):
            cmd.replay()
            return False

        escaped = False
        err = ''

        if vdglobals is None:
            vdglobals = getGlobals()

        self.sheet = self

        try:
            if vd.cmdlog:
                vd.cmdlog.beforeExecHook(self, cmd, '', keystrokes)
            code = compile(cmd.execstr, cmd.longname, 'exec')
            debug(cmd.longname)
            exec(code, vdglobals, LazyMap(vd, self))
        except EscapeException as e:  # user aborted
            warning('aborted')
            escaped = True
        except ImportError as e:
            warning('%s not installed' % e.name)
            if confirm('run `pip3 install %s`? ' % e.name, exc=None):
                warning('installing %s' % e.name)
                exec_shell('pip3', 'install', e.name)
            escaped = True
        except Exception as e:
            debug(cmd.execstr)
            err = vd.exceptionCaught(e)
            escaped = True

        try:
            if vd.cmdlog:
                # sheet may have changed
                vd.cmdlog.afterExecSheet(vd.sheets[0] if vd.sheets else None, escaped, err)
        except Exception as e:
            vd.exceptionCaught(e)

        catchapply(self.checkCursor)

        vd.clear_caches()
        return escaped

    @property
    def name(self):
        return self._name or ''

    @name.setter
    def name(self, name):
        'Set name without spaces.'
        self._name = name.strip().replace(' ', '_')

    def recalc(self):
        'Clear any calculated value caches.'
        pass

    def draw(self, scr):
        error('no draw')

    def reload(self):
        error('no reload')

    def checkCursor(self):
        pass

    def newRow(self):
        return type(self)._rowtype()


BaseSheet.addCommand('^R', 'reload-sheet', 'reload(); status("reloaded")')


class DisplayWrapper:
    def __init__(self, value, **kwargs):
        self.value = value
        self.__dict__.update(kwargs)

    def __bool__(self):
        return self.value

###

# https://stackoverflow.com/questions/19833315/running-system-commands-in-python-using-curses-and-panel-and-come-back-to-previ
class SuspendCurses:
    'Context Manager to temporarily leave curses mode'
    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        newscr = curses.initscr()
        newscr.refresh()
        curses.doupdate()


def launchEditor(*args):
    editor = os.environ.get('EDITOR') or fail('$EDITOR not set')
    args = [editor] + list(args)
    with SuspendCurses():
        return subprocess.call(args)

def launchExternalEditor(v, linenum=0):
    import tempfile
    with tempfile.NamedTemporaryFile() as temp:
        with open(temp.name, 'w') as fp:
            fp.write(v)
        return launchExternalEditorPath(Path(temp.name))

def launchExternalEditorPath(path, linenum=0):
        fn = path.resolve()
        if linenum:
            launchEditor(fn, '+%s' % linenum)
        else:
            launchEditor(fn)

        with open(fn, 'r') as fp:
            try:
                r = fp.read()
                if r[:-1] == '\n':  # trim inevitable trailing newline
                    r = r[:-1]
                return r
            except Exception as e:
                exceptionCaught(e)
                return ''

        launchExternalEditor(Path(temp.name))

def suspend():
    import signal
    with SuspendCurses():
        os.kill(os.getpid(), signal.SIGSTOP)

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

from .helpers import *
from .cliptext import clipdraw, clipstr
from .color import colors, CursesAttr
from .wrappers import *
from .column import *
from ._sheet import *
