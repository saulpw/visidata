#!/usr/bin/env python3
#
# Copyright 2017-2018 Saul Pwanson  http://saul.pw/vdtui
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

'vdtui: a curses framework for columnar data'

# Just include this whole file in your project as-is.  If you do make
# modifications, please keep the base vdtui version and append your own id and
# version.
__version__ = '1.4'
__version_info__ = 'saul.pw/vdtui v' + __version__
__author__ = 'Saul Pwanson <vd@saul.pw>'
__license__ = 'MIT'
__status__ = 'Production/Stable'
__copyright__ = 'Copyright (c) 2016-2018 ' + __author__

from builtins import *
import sys
import os
import collections
from copy import copy, deepcopy
from contextlib import suppress
import curses
import datetime
import functools
import io
import itertools
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
        elif issubclass(obj, BaseSheet):
            v = obj.__name__
        else:
            return None

        self.allobjs[v] = obj
        return v

    def getobj(self, objname):
        'Inverse of objname(obj); returns obj if available'
        return self.allobjs.get(objname)

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
    def __init__(self, longname, execstr):
        self.longname = longname
        self.execstr = execstr
        self.helpstr = ''

def globalCommand(keystrokes, longname, execstr):
    commands.setdefault(longname, Command(longname, execstr))

    if keystrokes:
        assert not bindkeys._get(keystrokes), keystrokes
        bindkeys.setdefault(keystrokes, longname)

def bindkey(keystrokes, longname):
    bindkeys.setdefault(keystrokes, longname)

def bindkey_override(keystrokes, longname):
    bindkeys.set(keystrokes, longname)

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
                vd().callHook('set_option', k, v, obj)
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

def option(name, default, helpstr):
    return options.setdefault(name, default, helpstr)


theme = option
def replayableOption(optname, default, helpstr):
    option(optname, default, helpstr).replayable = True


replayableOption('encoding', 'utf-8', 'encoding passed to codecs.open')
replayableOption('encoding_errors', 'surrogateescape', 'encoding errors passed to codecs.open')

replayableOption('regex_flags', 'I', 'flags to pass to re.compile() [AILMSUX]')
replayableOption('default_width', 20, 'default column width')
option('wrap', False, 'wrap text to fit window width on TextSheet')

option('cmd_after_edit', 'go-down', 'command longname to execute after successful edit')
option('col_cache_size', 0, 'max number of cache entries in each cached column')
option('quitguard', False, 'confirm before quitting last sheet')

replayableOption('null_value', None, 'a value to be counted as null')

replayableOption('force_valid_colnames', False, 'clean column names to be valid Python identifiers')
option('debug', False, 'exit on error and display stacktrace')
option('curses_timeout', 100, 'curses timeout in ms')
theme('force_256_colors', False, 'use 256 colors even if curses reports fewer')
theme('use_default_colors', False, 'curses use default terminal colors')

disp_column_fill = ' ' # pad chars after column value
theme('disp_note_none', '⌀',  'visible contents of a cell whose value is None')
theme('disp_truncator', '…', 'indicator that the contents are only partially visible')
theme('disp_oddspace', '\u00b7', 'displayable character for odd whitespace')
theme('disp_unprintable', '.', 'substitute character for unprintables')
theme('disp_column_sep', '|', 'separator between columns')
theme('disp_keycol_sep', '\u2016', 'separator between key columns and rest of columns')
theme('disp_status_fmt', '{sheet.name}| ', 'status line prefix')
theme('disp_lstatus_max', 0, 'maximum length of left status line')
theme('disp_status_sep', ' | ', 'separator between statuses')
theme('disp_edit_fill', '_', 'edit field fill character')
theme('disp_more_left', '<', 'header note indicating more columns to the left')
theme('disp_more_right', '>', 'header note indicating more columns to the right')
theme('disp_error_val', '', 'displayed contents for computation exception')
theme('disp_ambig_width', 1, 'width to use for unicode chars marked ambiguous')

theme('color_default', 'normal', 'the default color')
theme('color_default_hdr', 'bold underline', 'color of the column headers')
theme('color_current_row', 'reverse', 'color of the cursor row')
theme('color_current_col', 'bold', 'color of the cursor column')
theme('color_current_hdr', 'bold reverse underline', 'color of the header for the cursor column')
theme('color_column_sep', '246 blue', 'color of column separators')
theme('color_key_col', '81 cyan', 'color of key columns')
theme('color_hidden_col', '8', 'color of hidden columns on metasheets')
theme('color_selected_row', '215 yellow', 'color of selected rows')

theme('color_keystrokes', 'white', 'color of input keystrokes on status line')
theme('color_status', 'bold', 'status line color')
theme('color_error', 'red', 'error message color')
theme('color_warning', 'yellow', 'warning message color')
theme('color_edit_cell', 'normal', 'cell color to use when editing cell')

theme('disp_pending', '', 'string to display in pending cells')
theme('note_pending', '⌛', 'note to display for pending cells')
theme('note_format_exc', '?', 'cell note for an exception during type conversion or formatting')
theme('note_getter_exc', '!', 'cell note for an exception during computation')
theme('note_type_exc', '!', 'cell note for an exception during computation')
theme('note_unknown_type', '', 'cell note for unknown types in anytype column')

theme('color_note_pending', 'bold magenta', 'color of note in pending cells')
theme('color_note_type', '226 yellow', 'cell note for numeric types in anytype columns')
theme('scroll_incr', 3, 'amount to scroll with scrollwheel')

ENTER='^J'
ESC='^['
globalCommand('KEY_RESIZE', 'no-op', '')
globalCommand('q', 'quit-sheet',  'vd.sheets[1:] or options.quitguard and confirm("quit last sheet? "); vd.sheets.pop(0)')
globalCommand('gq', 'quit-all', 'vd.sheets.clear()')

globalCommand('^L', 'redraw', 'vd.scr.clear()')
globalCommand('^^', 'prev-sheet', 'vd.sheets[1:] or fail("no previous sheet"); vd.sheets[0], vd.sheets[1] = vd.sheets[1], vd.sheets[0]')

globalCommand('^Z', 'suspend', 'suspend()')

globalCommand(' ', 'exec-longname', 'exec_keystrokes(input_longname(sheet))')

bindkey('KEY_RESIZE', 'redraw')

def input_longname(sheet):
    longnames = set(k for (k, obj), v in commands.iter(sheet))
    return input("command name: ", completer=CompleteKey(sorted(longnames)))


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
        return fmtstr.format(typedval)
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
vdtype(int, '#', '{:.0f}')
vdtype(float, '%', '{:.02f}')
vdtype(len, '♯', '{:.0f}')
vdtype(dict, '')
vdtype(list, '')

def isNumeric(col):
    return col.type in (int,len,float,currency,date)

###

def catchapply(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        exceptionCaught(e)

def error(s):
    'Log an error and raise an exception.'
    status(s, priority=3)
    raise ExpectedException(s)

def fail(s):
    status(s, priority=2)
    raise ExpectedException(s)

def warning(s):
    status(s, priority=1)

def status(*args, **kwargs):
    return vd().status(*args, **kwargs)

def debug(*args, **kwargs):
    if options.debug:
        return vd().status(*args, **kwargs)

def input(*args, **kwargs):
    return vd().input(*args, **kwargs)

def rotate_range(n, idx, reverse=False):
    if reverse:
        rng = range(idx-1, -1, -1)
        rng2 = range(n-1, idx-1, -1)
    else:
        rng = range(idx+1, n)
        rng2 = range(0, idx+1)

    wrapped = False
    with Progress(total=n) as prog:
        for r in itertools.chain(rng, rng2):
            prog.addProgress(1)
            if not wrapped and r in rng2:
                status('search wrapped')
                wrapped = True
            yield r

def clean_to_id(s):  # [Nas Banov] https://stackoverflow.com/a/3305731
    return re.sub(r'\W|^(?=\d)', '_', str(s))

def middleTruncate(s, w):
    if len(s) <= w:
        return s
    return s[:w] + options.disp_truncator + s[-w:]

def composeStatus(msgparts, n):
    msg = '; '.join(wrmap(str, msgparts))
    if n > 1:
        msg = '[%sx] %s' % (n, msg)
    return msg

def exceptionCaught(e, **kwargs):
    return vd().exceptionCaught(e, **kwargs)

def stacktrace(e=None):
    if not e:
        return traceback.format_exc().strip().splitlines()
    return traceback.format_exception_only(type(e), e)

def chooseOne(choices):
    'Return one of `choices` elements (if list) or values (if dict).'
    ret = chooseMany(choices)
    assert len(ret) == 1, 'need one choice only'
    return ret[0]

def chooseMany(choices):
    'Return list of `choices` elements (if list) or values (if dict).'
    if isinstance(choices, dict):
        choosed = input('/'.join(choices.keys()) + ': ', completer=CompleteKey(choices)).split()
        return [choices[c] for c in choosed]
    else:
        return input('/'.join(str(x) for x in choices) + ': ', completer=CompleteKey(choices)).split()


def regex_flags():
    'Return flags to pass to regex functions from options'
    return sum(getattr(re, f.upper()) for f in options.regex_flags)

def sync(expectedThreads=0):
    vd().sync(expectedThreads)


# define @asyncthread for potentially long-running functions
#   when function is called, instead launches a thread
def asyncthread(func):
    'Function decorator, to make calls to `func()` spawn a separate thread if available.'
    @functools.wraps(func)
    def _execAsync(*args, **kwargs):
        return vd().execAsync(func, *args, **kwargs)
    return _execAsync


def asynccache(key=lambda *args, **kwargs: str(args)+str(kwargs)):
    def _decorator(func):
        'Function decorator, so first call to `func()` spawns a separate thread. Calls return the Thread until the wrapped function returns; subsequent calls return the cached return value.'
        d = {}  # per decoration cache
        def _func(k, *args, **kwargs):
            d[k] = func(*args, **kwargs)

        @functools.wraps(func)
        def _execAsync(*args, **kwargs):
            k = key(*args, **kwargs)
            if k not in d:
                d[k] = vd().execAsync(_func, k, *args, **kwargs)
            return d.get(k)
        return _execAsync
    return _decorator


class Progress:
    def __init__(self, iterable=None, total=None, sheet=None):
        self.iterable = iterable
        self.total = total if total is not None else len(iterable)
        self.sheet = sheet if sheet else getattr(threading.current_thread(), 'sheet', None)
        self.made = 0

    def __enter__(self):
        if self.sheet:
            self.sheet.progresses.append(self)
        return self

    def addProgress(self, n):
        self.made += n

    def __exit__(self, exc_type, exc_val, tb):
        if self.sheet:
            self.sheet.progresses.remove(self)

    def __iter__(self):
        with self as prog:
            for item in self.iterable:
                yield item
                self.made += 1

@asyncthread
def _async_deepcopy(vs, newlist, oldlist):
    for r in Progress(oldlist):
        newlist.append(deepcopy(r))

def async_deepcopy(vs, rowlist):
    ret = []
    _async_deepcopy(vs, ret, rowlist)
    return ret


class VisiData:
    allPrefixes = 'gz'  # embig'g'en, 'z'mallify

    def __call__(self):
        return self

    def __init__(self):
        self.sheets = []  # list of BaseSheet; all sheets on the sheet stack
        self.allSheets = weakref.WeakKeyDictionary()  # [BaseSheet] -> sheetname (all non-precious sheets ever pushed)
        self.statuses = collections.OrderedDict()  # (priority, statusmsg) -> num_repeats; shown until next action
        self.statusHistory = []  # list of [priority, statusmsg, repeats] for all status messages ever
        self.lastErrors = []
        self.lastInputs = collections.defaultdict(collections.OrderedDict)  # [input_type] -> prevInputs
        self.keystrokes = ''
        self.inInput = False
        self.prefixWaiting = False
        self.scr = None  # curses scr
        self.hooks = collections.defaultdict(list)  # [hookname] -> list(hooks)
        self.threads = [] # all long-running threads, including main and finished
        self.addThread(threading.current_thread(), endTime=0)
        self.addHook('rstatus', lambda sheet,self=self: (self.keystrokes, 'color_keystrokes'))
        self.addHook('rstatus', self.rightStatus)

    @property
    def sheet(self):
        return self.sheets[0] if self.sheets else None

    def getSheet(self, sheetname):
        matchingSheets = [x for x in vd().sheets if x.name == sheetname]
        if matchingSheets:
            if len(matchingSheets) > 1:
                status('more than one sheet named "%s"' % sheetname)
            return matchingSheets[0]
        if sheetname == 'options':
            vs = self.optionsSheet
            vs.reload()
            vs.vd = vd()
            return vs

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

    def addHook(self, hookname, hookfunc):
        'Add hookfunc by hookname, to be called by corresponding `callHook`.'
        self.hooks[hookname].insert(0, hookfunc)

    def callHook(self, hookname, *args, **kwargs):
        'Call all functions registered with `addHook` for the given hookname.'
        r = []
        for f in self.hooks[hookname]:
            try:
                r.append(f(*args, **kwargs))
            except Exception as e:
                exceptionCaught(e)
        return r

    def addThread(self, t, endTime=None):
        t.startTime = time.process_time()
        t.endTime = endTime
        t.status = ''
        t.profile = None
        t.exception = None
        self.threads.append(t)

    def execAsync(self, func, *args, **kwargs):
        'Execute `func(*args, **kwargs)` in a separate thread.'

        thread = threading.Thread(target=self.toplevelTryFunc, daemon=True, args=(func,)+args, kwargs=kwargs)
        self.addThread(thread)

        if self.sheets:
            currentSheet = self.sheets[0]
            currentSheet.currentThreads.append(thread)
        else:
            currentSheet = None

        thread.sheet = currentSheet
        thread.start()

        return thread

    @staticmethod
    def toplevelTryFunc(func, *args, **kwargs):
        'Thread entry-point for `func(*args, **kwargs)` with try/except wrapper'
        t = threading.current_thread()
        t.name = func.__name__
        ret = None
        try:
            ret = func(*args, **kwargs)
        except EscapeException as e:  # user aborted
            t.status += 'aborted by user'
            status('%s aborted' % t.name, priority=2)
        except Exception as e:
            t.exception = e
            exceptionCaught(e)

        if t.sheet:
            t.sheet.currentThreads.remove(t)
        return ret

    @property
    def unfinishedThreads(self):
        'A list of unfinished threads (those without a recorded `endTime`).'
        return [t for t in self.threads if getattr(t, 'endTime', None) is None]

    def checkForFinishedThreads(self):
        'Mark terminated threads with endTime.'
        for t in self.unfinishedThreads:
            if not t.is_alive():
                t.endTime = time.process_time()
                if getattr(t, 'status', None) is None:
                    t.status = 'ended'

    def sync(self, expectedThreads=0):
        'Wait for all but expectedThreads async threads to finish.'
        while len(self.unfinishedThreads) > expectedThreads:
            time.sleep(.3)
            self.checkForFinishedThreads()

    def refresh(self):
        Sheet.visibleCols.fget.cache_clear()
        Sheet.keyCols.fget.cache_clear()
        colors.colorcache.clear()

    def editText(self, y, x, w, record=True, **kwargs):
        'Wrap global editText with `preedit` and `postedit` hooks.'
        v = self.callHook('preedit') if record else None
        if not v or v[0] is None:
            with EnableCursor():
                v = editText(self.scr, y, x, w, **kwargs)
        else:
            v = v[0]

        if kwargs.get('display', True):
            status('"%s"' % v)
            self.callHook('postedit', v) if record else None
        return v

    def input(self, prompt, type='', defaultLast=False, **kwargs):
        'Get user input, with history of `type`, defaulting to last history item if no input and defaultLast is True.'
        if type:
            histlist = list(self.lastInputs[type].keys())
            ret = self._inputLine(prompt, history=histlist, **kwargs)
            if ret:
                self.lastInputs[type][ret] = ret
            elif defaultLast:
                histlist or fail("no previous input")
                ret = histlist[-1]
        else:
            ret = self._inputLine(prompt, **kwargs)

        return ret

    def _inputLine(self, prompt, **kwargs):
        'Add prompt to bottom of screen and get line of input from user.'
        self.inInput = True
        rstatuslen = self.drawRightStatus(self.scr, self.sheets[0])
        attr = 0
        promptlen = clipdraw(self.scr, self.windowHeight-1, 0, prompt, attr, w=self.windowWidth-rstatuslen-1)
        ret = self.editText(self.windowHeight-1, promptlen, self.windowWidth-promptlen-rstatuslen-2,
                            attr=colors.color_edit_cell,
                            unprintablechar=options.disp_unprintable,
                            truncchar=options.disp_truncator,
                            **kwargs)
        self.inInput = False
        return ret

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

    def exceptionCaught(self, exc=None, **kwargs):
        'Maintain list of most recent errors and return most recent one.'
        if isinstance(exc, ExpectedException):  # already reported, don't log
            return
        self.lastErrors.append(stacktrace())
        if kwargs.get('status', True):
            status(self.lastErrors[-1][-1], priority=2)  # last line of latest error
        if options.debug:
            raise

    def drawLeftStatus(self, scr, vs):
        'Draw left side of status bar.'
        cattr = CursesAttr(colors.color_status)
        attr = cattr.attr
        error_attr = cattr.update_attr(colors.color_error, 1).attr
        warn_attr = cattr.update_attr(colors.color_warning, 2).attr
        sep = options.disp_status_sep

        try:
            lstatus = vs.leftStatus()
            maxwidth = options.disp_lstatus_max
            if maxwidth > 0:
                lstatus = middleTruncate(lstatus, maxwidth//2)

            y = self.windowHeight-1
            x = clipdraw(scr, y, 0, lstatus, attr)
            one = False
            for (pri, msgparts), n in sorted(self.statuses.items(), key=lambda k: -k[0][0]):
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
        for rstatcolor in self.callHook('rstatus', vs):
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
        if sheet.currentThreads:
            status = '%9d  %2d%%' % (len(sheet), sheet.progressPct)
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
        global sheet
        scr.timeout(int(options.curses_timeout))
        with suppress(curses.error):
            curses.curs_set(0)

        self.scr = scr

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
                if not self.prefixWaiting:
                    self.keystrokes = ''

                self.statuses.clear()

                if keystroke == 'KEY_MOUSE':
                    try:
                        devid, x, y, z, bstate = curses.getmouse()
                        if bstate & curses.BUTTON_CTRL:
                            self.keystrokes += "CTRL-"
                            bstate &= ~curses.BUTTON_CTRL
                        if bstate & curses.BUTTON_ALT:
                            self.keystrokes += "ALT-"
                            bstate &= ~curses.BUTTON_ALT
                        if bstate & curses.BUTTON_SHIFT:
                            self.keystrokes += "SHIFT-"
                            bstate &= ~curses.BUTTON_SHIFT

                        keystroke = curses.mouseEvents.get(bstate, str(bstate))
                        sheet.mouseX, sheet.mouseY = x, y
                    except curses.error:
                        keystroke = ''

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
                self.keystrokes = ''.join(sorted(set(self.keystrokes)))  # prefix order/quantity does not matter
                self.prefixWaiting = True
            else:
                status('no command for "%s"' % (self.keystrokes))
                self.prefixWaiting = False

            self.checkForFinishedThreads()
            self.callHook('predraw')
            catchapply(sheet.checkCursor)

            # no idle redraw unless background threads are running
            scr.timeout(options.curses_timeout if vd.unfinishedThreads else -1)

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
                self.sheets.insert(0, vs)
            elif not vs.loaded:
                self.sheets.insert(0, vs)
                vs.reload()
                vs.recalc()  # set up Columns
            else:
                self.sheets.insert(0, vs)

            if vs.precious and vs not in vs.vd.allSheets:
                vs.vd.allSheets[vs] = vs.name
            return vs
# end VisiData class

vd = VisiData()

class LazyMap:
    'provides a lazy mapping to obj attributes.  useful when some attributes are expensive properties.'
    def __init__(self, obj):
        self.obj = obj

    def keys(self):
        return dir(self.obj)

    def __getitem__(self, k):
        if k not in dir(self.obj):
            raise KeyError(k)
        return getattr(self.obj, k)

    def __setitem__(self, k, v):
        setattr(self.obj, k, v)

class CompleteExpr:
    def __init__(self, sheet=None):
        self.sheet = sheet

    def __call__(self, val, state):
        i = len(val)-1
        while val[i:].isidentifier() and i >= 0:
            i -= 1

        if i < 0:
            base = ''
            partial = val
        elif val[i] == '.':  # no completion of attributes
            return None
        else:
            base = val[:i+1]
            partial = val[i+1:]

        varnames = []
        varnames.extend(sorted((base+col.name) for col in self.sheet.columns if col.name.startswith(partial)))
        varnames.extend(sorted((base+x) for x in globals() if x.startswith(partial)))
        return varnames[state%len(varnames)]

class CompleteKey:
    def __init__(self, items):
        self.items = items

    def __call__(self, val, state):
        opts = [x for x in self.items if x.startswith(val)]
        return opts[state%len(opts)]


# higher precedence color overrides lower; all non-color attributes combine
# coloropt is the color option name (like 'color_error')
# func(sheet,col,row,value) should return a true value if coloropt should be applied
# if coloropt is None, func() should return a coloropt (or None) instead
RowColorizer = collections.namedtuple('RowColorizer', 'precedence coloropt func')
CellColorizer = collections.namedtuple('CellColorizer', 'precedence coloropt func')
ColumnColorizer = collections.namedtuple('ColumnColorizer', 'precedence coloropt func')


class BaseSheet:
    _rowtype = object    # callable (no parms) that returns new empty item
    _coltype = None      # callable (no parms) that returns new settable view into that item
    rowtype = 'objects'  # one word, plural, describing the items
    precious = True      # False for a few discardable metasheets

    def __init__(self, name, **kwargs):
        self.name = name
        self.vd = vd()

        # for progress bar
        self.progresses = []  # list of Progress objects

        # track all async threads from sheet
        self.currentThreads = []
        self.__dict__.update(kwargs)


    @classmethod
    def addCommand(cls, keystrokes, longname, execstr):
        commands.set(longname, Command(longname, execstr), cls)
        if keystrokes:
            bindkeys.set(keystrokes, longname, cls)

    @classmethod
    def bindkey(cls, keystrokes, longname):
        oldlongname = bindkeys._get(keystrokes, cls)
        if oldlongname:
            warning('%s was already bound to %s' % (keystrokes, oldlongname))
        bindkeys.set(keystrokes, longname, cls)

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

    @property
    def loaded(self):
        return False

    def leftStatus(self):
        'Compose left side of status bar for this sheet (overridable).'
        return options.disp_status_fmt.format(sheet=self)

    def exec_keystrokes(self, keystrokes, vdglobals=None):
        return self.exec_command(self.getCommand(keystrokes), vdglobals, keystrokes=keystrokes)

    def exec_command(self, cmd, args='', vdglobals=None, keystrokes=None):
        "Execute `cmd` tuple with `vdglobals` as globals and this sheet's attributes as locals.  Returns True if user cancelled."
        global sheet
        sheet = vd.sheets[0]

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

        if not self.vd:
            self.vd = vd()

        self.sheet = self

        try:
            self.vd.callHook('preexec', self, cmd, '', keystrokes)
            exec(cmd.execstr, vdglobals, LazyMap(self))
        except EscapeException as e:  # user aborted
            status('aborted')
            escaped = True
        except Exception as e:
            debug(cmd.execstr)
            err = self.vd.exceptionCaught(e)
            escaped = True

        try:
            self.vd.callHook('postexec', self.vd.sheets[0] if self.vd.sheets else None, escaped, err)
        except Exception:
            self.vd.exceptionCaught(e)

        catchapply(self.checkCursor)

        self.vd.refresh()
        return escaped

    @property
    def name(self):
        return self._name or ''

    @name.setter
    def name(self, name):
        'Set name without spaces.'
        self._name = name.strip().replace(' ', '_')

    @property
    def progressMade(self):
        return sum(prog.made for prog in self.progresses)

    @property
    def progressTotal(self):
        return sum(prog.total for prog in self.progresses)

    @property
    def progressPct(self):
        'Percent complete as indicated by async actions.'
        if self.progressTotal != 0:
            return int(self.progressMade*100/self.progressTotal)
        return 0

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

class CursesAttr:
    def __init__(self, attr=0, precedence=-1):
        self.attributes = attr & ~curses.A_COLOR
        self.color = attr & curses.A_COLOR
        self.precedence = precedence

    def __str__(self):
        a = self.attr
        ret = set()
        for k in dir(curses):
            v = getattr(curses, k)
            if v == 0:
                pass
            elif k.startswith('A_'):
                if self.attributes & v == v:
                    ret.add(k)
            elif k.startswith('COLOR_'):
                if self.color == v:
                    ret.add(k)
        return (' '.join(k for k in ret) or str(self.color)) + ' %0X' % self.attr

    @property
    def attr(self):
        'the composed curses attr'
        return self.color | self.attributes

    def update_attr(self, newattr, newprec=None):
        if isinstance(newattr, int):
            newattr = CursesAttr(newattr)
        ret = copy(self)
        if newprec is None:
            newprec = newattr.precedence
        ret.attributes |= newattr.attributes
        if not ret.color or newprec > ret.precedence:
            if newattr.color:
                ret.color = newattr.color
            ret.precedence = newprec
        return ret


class Sheet(BaseSheet):
    'Base class for all tabular sheets.'
    _rowtype = lambda: defaultdict(lambda: None)
    rowtype = 'rows'

    columns = []  # list of Column
    colorizers = [ # list of Colorizer
        CellColorizer(2, 'color_default_hdr', lambda s,c,r,v: r is None),
        ColumnColorizer(2, 'color_current_col', lambda s,c,r,v: c is s.cursorCol),
        ColumnColorizer(1, 'color_key_col', lambda s,c,r,v: c in s.keyCols),
        CellColorizer(0, 'color_default', lambda s,c,r,v: True),
#        RowColorizer(-1, 'color_column_sep', lambda s,c,r,v: c is None),
        RowColorizer(2, 'color_selected_row', lambda s,c,r,v: s.isSelected(r)),
        RowColorizer(1, 'color_error', lambda s,c,r,v: isinstance(r, (Exception, TypedExceptionWrapper))),
    ]
    nKeys = 0  # columns[:nKeys] are key columns

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.rows = tuple()      # list of opaque row objects (tuple until first reload)
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorVisibleColIndex = 0  # index of cursor into self.visibleCols

        self.topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftVisibleColIndex = 0    # cursorVisibleColIndex of leftmost column
        self.rightVisibleColIndex = 0

        # as computed during draw()
        self.rowLayout = {}      # [rowidx] -> y
        self.visibleColLayout = {}      # [vcolidx] -> (x, w)

        # list of all columns in display order
        self.columns = kwargs.get('columns') or [copy(c) for c in self.columns] or [Column('')]
        self.recalc()  # set .sheet on columns and start caches

        self.setKeys(self.columns[:self.nKeys])  # initial list of key columns
        self._selectedRows = {}  # id(row) -> row

        self.__dict__.update(kwargs)  # also done earlier in BaseSheet.__init__

    def __len__(self):
        return self.nRows

    @property
    def loaded(self):
        if self.rows == tuple():
            self.rows = list()
            return False
        return True

    def addColorizer(self, c):
        self.colorizers.append(c)

    @functools.lru_cache()
    def getColorizers(self):
        _colorizers = set()
        for b in [self] + list(self.__class__.__bases__):
            for c in getattr(b, 'colorizers', []):
                _colorizers.add(c)
        return sorted(_colorizers, key=lambda x: x.precedence, reverse=True)

    def colorize(self, col, row, value=None):
        'Returns curses attribute for the given col/row/value'

#        colorstack = tuple(c.coloropt for c in self.getColorizers() if wrapply(c.func, self, col, row, value))

        colorstack = []
        for colorizer in self.getColorizers():
            try:
                r = colorizer.func(self, col, row, value)
                if r:
                    colorstack.append(colorizer.coloropt if colorizer.coloropt else r)
            except Exception as e:
                exceptionCaught(e)

        return colors.resolve_colors(tuple(colorstack))

    def addRow(self, row, index=None):
        if index is None:
            self.rows.append(row)
        else:
            self.rows.insert(index, row)
        return row

    def column(self, colregex):
        'Return first column whose Column.name matches colregex.'
        for c in self.columns:
            if re.search(colregex, c.name, regex_flags()):
                return c

    def recalc(self):
        'Clear caches and set col.sheet to this sheet for all columns.'
        for c in self.columns:
            c.recalc(self)

    def reload(self):
        'Loads rows and/or columns.  Override in subclass.'
        self.rows = []
        for r in self.iterload():
            self.addRow(r)

    def iterload(self):
        'Override this generator for loading, if columns can be predefined.'
        for row in []:
            yield row

    def __copy__(self):
        'copy sheet design (no rows).  deepcopy columns so their attributes (width, type, name) may be adjusted independently.'
        cls = self.__class__
        ret = cls.__new__(cls)
        ret.__dict__.update(self.__dict__)
        ret.rows = []                     # a fresh list without incurring any overhead
        ret.columns = [copy(c) for c in self.keyCols]
        ret.setKeys(ret.columns)
        ret.columns.extend(copy(c) for c in self.columns if c not in self.keyCols)
        ret.recalc()  # set .sheet on columns
        ret._selectedRows = {}
        ret.topRowIndex = ret.cursorRowIndex = 0
        ret.progresses = []
        ret.currentThreads = []
        ret.precious = True  # copies can be precious even if originals aren't
        return ret

    def __deepcopy__(self, memo):
        'same as __copy__'
        ret = self.__copy__()
        memo[id(self)] = ret
        return ret

    def deleteBy(self, func):
        'Delete rows for which func(row) is true.  Returns number of deleted rows.'
        oldrows = copy(self.rows)
        oldidx = self.cursorRowIndex
        ndeleted = 0

        row = None   # row to re-place cursor after
        while oldidx < len(oldrows):
            if not func(oldrows[oldidx]):
                row = self.rows[oldidx]
                break
            oldidx += 1

        self.rows.clear()
        for r in Progress(oldrows):
            if not func(r):
                self.rows.append(r)
                if r is row:
                    self.cursorRowIndex = len(self.rows)-1
            else:
                ndeleted += 1

        status('deleted %s %s' % (ndeleted, self.rowtype))
        return ndeleted

    @asyncthread
    def deleteSelected(self):
        'Delete all selected rows.'
        ndeleted = self.deleteBy(self.isSelected)
        nselected = len(self._selectedRows)
        self._selectedRows.clear()
        if ndeleted != nselected:
            error('expected %s' % nselected)

    @asyncthread
    def delete(self, rows):
        rowdict = {id(r): r for r in rows}
        ndeleted = self.deleteBy(lambda r,rowdict=rowdict: id(r) in rowdict)
        nrows = len(rows)
        if ndeleted != nrows:
            error('expected %s' % nrows)

    def __repr__(self):
        return self.name

    def evalexpr(self, expr, row=None):
        return eval(expr, getGlobals(), LazyMapRow(self, row) if row else None)

    def inputExpr(self, prompt, *args, **kwargs):
        return input(prompt, "expr", *args, completer=CompleteExpr(self), **kwargs)

    @property
    def nVisibleRows(self):
        'Number of visible rows at the current window height.'
        return self.vd.windowHeight-2

    @property
    def cursorCol(self):
        'Current Column object.'
        return self.visibleCols[self.cursorVisibleColIndex]

    @property
    def cursorRow(self):
        'The row object at the row cursor.'
        return self.rows[self.cursorRowIndex]

    @property
    def visibleRows(self):  # onscreen rows
        'List of rows onscreen. '
        return self.rows[self.topRowIndex:self.topRowIndex+self.nVisibleRows]

    @property
    @functools.lru_cache()  # cache for perf reasons on wide sheets.  cleared in .refresh()
    def visibleCols(self):  # non-hidden cols
        'List of `Column` which are not hidden.'
        return self.keyCols + [c for c in self.columns if not c.hidden and not c.keycol]

    @property
    @functools.lru_cache()  # cache for perf reasons on wide sheets.  cleared in .refresh()
    def keyCols(self):
        'Cached list of visible key columns (Columns with .key=True)'
        return [c for c in self.columns if c.keycol and not c.hidden]

    @property
    def cursorColIndex(self):
        'Index of current column into `columns`. Linear search; prefer `cursorCol` or `cursorVisibleColIndex`.'
        return self.columns.index(self.cursorCol)

    @property
    def nonKeyVisibleCols(self):
        'All columns which are not keysList of unhidden non-key columns.'
        return [c for c in self.columns if not c.hidden and c not in self.keyCols]

    @property
    def keyColNames(self):
        'String of key column names, for SheetsSheet convenience.'
        return ' '.join(c.name for c in self.keyCols)

    @property
    def cursorCell(self):
        'Displayed value (DisplayWrapper) at current row and column.'
        return self.cursorCol.getCell(self.cursorRow)

    @property
    def cursorDisplay(self):
        'Displayed value (DisplayWrapper.display) at current row and column.'
        return self.cursorCol.getDisplayValue(self.cursorRow)

    @property
    def cursorTypedValue(self):
        'Typed value at current row and column.'
        return self.cursorCol.getTypedValue(self.cursorRow)

    @property
    def cursorValue(self):
        'Raw value at current row and column.'
        return self.cursorCol.getValue(self.cursorRow)

    @property
    def statusLine(self):
        'String of row and column stats.'
        rowinfo = 'row %d/%d (%d selected)' % (self.cursorRowIndex, self.nRows, len(self._selectedRows))
        colinfo = 'col %d/%d (%d visible)' % (self.cursorColIndex, self.nCols, len(self.visibleCols))
        return '%s  %s' % (rowinfo, colinfo)

    @property
    def nRows(self):
        'Number of rows on this sheet.'
        return len(self.rows)

    @property
    def nCols(self):
        'Number of columns on this sheet.'
        return len(self.columns)

    @property
    def nVisibleCols(self):
        'Number of visible columns on this sheet.'
        return len(self.visibleCols)

## selection code
    def isSelected(self, row):
        'True if given row is selected. O(log n).'
        return id(row) in self._selectedRows

    @asyncthread
    def toggle(self, rows):
        'Toggle selection of given `rows`.'
        for r in Progress(rows, len(self.rows)):
            if not self.unselectRow(r):
                self.selectRow(r)

    def selectRow(self, row):
        'Select given row. O(log n)'
        self._selectedRows[id(row)] = row

    def unselectRow(self, row):
        'Unselect given row, return True if selected; else return False. O(log n)'
        if id(row) in self._selectedRows:
            del self._selectedRows[id(row)]
            return True
        else:
            return False

    @asyncthread
    def select(self, rows, status=True, progress=True):
        "Select given rows. Don't show progress if progress=False; don't show status if status=False."
        before = len(self._selectedRows)
        for r in (Progress(rows) if progress else rows):
            self.selectRow(r)
        if status:
            vd().status('selected %s%s %s' % (len(self._selectedRows)-before, ' more' if before > 0 else '', self.rowtype))

    @asyncthread
    def unselect(self, rows, status=True, progress=True):
        "Unselect given rows. Don't show progress if progress=False; don't show status if status=False."
        before = len(self._selectedRows)
        for r in (Progress(rows) if progress else rows):
            self.unselectRow(r)
        if status:
            vd().status('unselected %s/%s %s' % (before-len(self._selectedRows), before, self.rowtype))

    def selectByIdx(self, rowIdxs):
        'Select given row indexes, without progress bar.'
        self.select((self.rows[i] for i in rowIdxs), progress=False)

    def unselectByIdx(self, rowIdxs):
        'Unselect given row indexes, without progress bar.'
        self.unselect((self.rows[i] for i in rowIdxs), progress=False)

    def gatherBy(self, func):
        'Generate only rows for which the given func returns True.'
        for i in rotate_range(len(self.rows), self.cursorRowIndex):
            try:
                r = self.rows[i]
                if func(r):
                    yield r
            except Exception:
                pass

    def orderBy(self, *cols, **kwargs):
        try:
            self.rows.sort(key=lambda r,cols=cols: tuple(c.getTypedValueNoExceptions(r) for c in cols), **kwargs)
        except TypeError as e:
            status('sort incomplete due to TypeError; change column type')
            exceptionCaught(e, status=False)

    @property
    def selectedRows(self):
        'List of selected rows in sheet order. [O(nRows*log(nSelected))]'
        if len(self._selectedRows) <= 1:
            return list(self._selectedRows.values())
        return [r for r in self.rows if id(r) in self._selectedRows]

## end selection code

    def cursorDown(self, n=1):
        'Move cursor down `n` rows (or up if `n` is negative).'
        self.cursorRowIndex += n

    def cursorRight(self, n=1):
        'Move cursor right `n` visible columns (or left if `n` is negative).'
        self.cursorVisibleColIndex += n
        self.calcColLayout()

    def pageLeft(self):
        '''Redraw page one screen to the left.

        Note: keep the column cursor in the same general relative position:

         - if it is on the furthest right column, then it should stay on the
           furthest right column if possible

         - likewise on the left or in the middle

        So really both the `leftIndex` and the `cursorIndex` should move in
        tandem until things are correct.'''

        targetIdx = self.leftVisibleColIndex  # for rightmost column
        firstNonKeyVisibleColIndex = self.visibleCols.index(self.nonKeyVisibleCols[0])
        while self.rightVisibleColIndex != targetIdx and self.leftVisibleColIndex > firstNonKeyVisibleColIndex:
            self.cursorVisibleColIndex -= 1
            self.leftVisibleColIndex -= 1
            self.calcColLayout()  # recompute rightVisibleColIndex

        # in case that rightmost column is last column, try to squeeze maximum real estate from screen
        if self.rightVisibleColIndex == self.nVisibleCols-1:
            # try to move further left while right column is still full width
            while self.leftVisibleColIndex > 0:
                rightcol = self.visibleCols[self.rightVisibleColIndex]
                if rightcol.width > self.visibleColLayout[self.rightVisibleColIndex][1]:
                    # went too far
                    self.cursorVisibleColIndex += 1
                    self.leftVisibleColIndex += 1
                    break
                else:
                    self.cursorVisibleColIndex -= 1
                    self.leftVisibleColIndex -= 1
                    self.calcColLayout()  # recompute rightVisibleColIndex

    def addColumn(self, col, index=None):
        'Insert column at given index or after all columns.'
        if col:
            if index is None:
                index = len(self.columns)
            col.sheet = self
            self.columns.insert(index, col)
            return col

    def setKeys(self, cols):
        for col in cols:
            col.keycol = True

    def unsetKeys(self, cols):
        for col in cols:
            col.keycol = False

    def toggleKeys(self, cols):
        for col in cols:
            col.keycol = not col.keycol

    def rowkey(self, row):
        'returns a tuple of the key for the given row'
        return tuple(c.getTypedValueOrException(row) for c in self.keyCols)

    def checkCursor(self):
        'Keep cursor in bounds of data and screen.'
        # keep cursor within actual available rowset
        if self.nRows == 0 or self.cursorRowIndex <= 0:
            self.cursorRowIndex = 0
        elif self.cursorRowIndex >= self.nRows:
            self.cursorRowIndex = self.nRows-1

        if self.cursorVisibleColIndex <= 0:
            self.cursorVisibleColIndex = 0
        elif self.cursorVisibleColIndex >= self.nVisibleCols:
            self.cursorVisibleColIndex = self.nVisibleCols-1

        if self.topRowIndex <= 0:
            self.topRowIndex = 0
        elif self.topRowIndex > self.nRows-1:
            self.topRowIndex = self.nRows-1

        # (x,y) is relative cell within screen viewport
        x = self.cursorVisibleColIndex - self.leftVisibleColIndex
        y = self.cursorRowIndex - self.topRowIndex + 1  # header

        # check bounds, scroll if necessary
        if y < 1:
            self.topRowIndex = self.cursorRowIndex
        elif y > self.nVisibleRows:
            self.topRowIndex = self.cursorRowIndex-self.nVisibleRows+1

        if x <= 0:
            self.leftVisibleColIndex = self.cursorVisibleColIndex
        else:
            while True:
                if self.leftVisibleColIndex == self.cursorVisibleColIndex:  # not much more we can do
                    break
                self.calcColLayout()
                mincolidx, maxcolidx = min(self.visibleColLayout.keys()), max(self.visibleColLayout.keys())
                if self.cursorVisibleColIndex < mincolidx:
                    self.leftVisibleColIndex -= max((self.cursorVisibleColIndex - mincolid)//2, 1)
                    continue
                elif self.cursorVisibleColIndex > maxcolidx:
                    self.leftVisibleColIndex += max((maxcolidx - self.cursorVisibleColIndex)//2, 1)
                    continue

                cur_x, cur_w = self.visibleColLayout[self.cursorVisibleColIndex]
                if cur_x+cur_w < self.vd.windowWidth:  # current columns fit entirely on screen
                    break
                self.leftVisibleColIndex += 1  # once within the bounds, walk over one column at a time

    def calcColLayout(self):
        'Set right-most visible column, based on calculation.'
        minColWidth = len(options.disp_more_left)+len(options.disp_more_right)
        sepColWidth = len(options.disp_column_sep)
        winWidth = self.vd.windowWidth
        self.visibleColLayout = {}
        x = 0
        vcolidx = 0
        for vcolidx in range(0, self.nVisibleCols):
            col = self.visibleCols[vcolidx]
            if col.width is None and len(self.visibleRows) > 0:
                # handle delayed column width-finding
                col.width = col.getMaxWidth(self.visibleRows)+minColWidth
                if vcolidx != self.nVisibleCols-1:  # let last column fill up the max width
                    col.width = min(col.width, options.default_width)
            width = col.width if col.width is not None else options.default_width
            if col in self.keyCols:
                width = max(width, 1)  # keycols must all be visible
            if col in self.keyCols or vcolidx >= self.leftVisibleColIndex:  # visible columns
                self.visibleColLayout[vcolidx] = [x, min(width, winWidth-x)]
                x += width+sepColWidth
            if x > winWidth-1:
                break

        self.rightVisibleColIndex = vcolidx

    def drawColHeader(self, scr, y, vcolidx):
        'Compose and draw column header for given vcolidx.'
        col = self.visibleCols[vcolidx]

        # hdrattr highlights whole column header
        # sepattr is for header separators and indicators
        sepattr = colors.color_column_sep

        hdrattr = self.colorize(col, None)
        if vcolidx == self.cursorVisibleColIndex:
            hdrattr = hdrattr.update_attr(colors.color_current_hdr, 2)

        C = options.disp_column_sep
        if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
            C = options.disp_keycol_sep

        x, colwidth = self.visibleColLayout[vcolidx]

        # ANameTC
        T = getType(col.type).icon
        if T is None:  # still allow icon to be explicitly non-displayed ''
            T = '?'
        N = ' ' + col.name  # save room at front for LeftMore
        if len(N) > colwidth-1:
            N = N[:colwidth-len(options.disp_truncator)] + options.disp_truncator
        clipdraw(scr, y, x, N, hdrattr.attr, colwidth)
        clipdraw(scr, y, x+colwidth-len(T), T, hdrattr.attr, len(T))

        if vcolidx == self.leftVisibleColIndex and col not in self.keyCols and self.nonKeyVisibleCols.index(col) > 0:
            A = options.disp_more_left
            scr.addstr(y, x, A, sepattr)

        if C and x+colwidth+len(C) < self.vd.windowWidth:
            scr.addstr(y, x+colwidth, C, sepattr)

    def isVisibleIdxKey(self, vcolidx):
        'Return boolean: is given column index a key column?'
        return self.visibleCols[vcolidx] in self.keyCols

    def draw(self, scr):
        'Draw entire screen onto the `scr` curses object.'
        numHeaderRows = 1
        scr.erase()  # clear screen before every re-draw

        vd().refresh()

        if not self.columns:
            return

        color_current_row = CursesAttr(colors.color_current_row, 5)
        disp_column_sep = options.disp_column_sep

        rowattrs = {}  # [rowidx] -> attr
        colattrs = {}  # [colidx] -> attr
        self.rowLayout = {}
        self.calcColLayout()
        vcolidx = 0
        rows = list(self.rows[self.topRowIndex:self.topRowIndex+self.nVisibleRows])
        for vcolidx, colinfo in sorted(self.visibleColLayout.items()):
            x, colwidth = colinfo
            col = self.visibleCols[vcolidx]

            if x < self.vd.windowWidth:  # only draw inside window
                headerRow = 0
                self.drawColHeader(scr, headerRow, vcolidx)

                y = headerRow + numHeaderRows
                for rowidx in range(0, min(len(rows), self.nVisibleRows)):
                    dispRowIdx = self.topRowIndex + rowidx
                    if dispRowIdx >= self.nRows:
                        break

                    self.rowLayout[dispRowIdx] = y

                    row = rows[rowidx]
                    cellval = col.getCell(row, colwidth-1)
#
                    attr = self.colorize(col, row, cellval)

                    # sepattr is the attr between cell/columns
                    rowattr = rowattrs.get(rowidx)
                    if rowattr is None:
                        rowattr = rowattrs[rowidx] = self.colorize(None, row)
                    sepattr = rowattr

                    # must apply current row here, because this colorization requires cursorRowIndex
                    if dispRowIdx == self.cursorRowIndex:
                        attr = attr.update_attr(color_current_row)
                        sepattr = sepattr.update_attr(color_current_row)

                    note = getattr(cellval, 'note', None)
                    if note:
                        noteattr = attr.update_attr(colors.get_color(cellval.notecolor), 10)
                        clipdraw(scr, y, x+colwidth-len(note), note, noteattr.attr, len(note))

                    clipdraw(scr, y, x, disp_column_fill+cellval.display, attr.attr, colwidth-(1 if note else 0))

                    sepchars = disp_column_sep
                    if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
                        sepchars = options.disp_keycol_sep

                    if x+colwidth+len(sepchars) <= self.vd.windowWidth:
                       scr.addstr(y, x+colwidth, sepchars, sepattr.attr)

                    y += 1

        if vcolidx+1 < self.nVisibleCols:
            scr.addstr(headerRow, self.vd.windowWidth-2, options.disp_more_right, colors.color_column_sep)

        catchapply(self.checkCursor)

    def editCell(self, vcolidx=None, rowidx=None, **kwargs):
        'Call `editText` at its place on the screen.  Returns the new value, properly typed'

        if vcolidx is None:
            vcolidx = self.cursorVisibleColIndex
        x, w = self.visibleColLayout.get(vcolidx, (0, 0))

        col = self.visibleCols[vcolidx]
        if rowidx is None:
            rowidx = self.cursorRowIndex
        if rowidx < 0:  # header
            y = 0
            currentValue = col.name
        else:
            y = self.rowLayout.get(rowidx, 0)
            currentValue = col.getDisplayValue(self.rows[self.cursorRowIndex])

        editargs = dict(value=currentValue,
                        fillchar=options.disp_edit_fill,
                        truncchar=options.disp_truncator)
        editargs.update(kwargs)  # update with user-specified args
        r = self.vd.editText(y, x, w, **editargs)
        if rowidx >= 0:  # if not header
            r = col.type(r)  # convert input to column type, let exceptions be raised

        return r

Sheet.addCommand('KEY_LEFT', 'go-left',  'cursorRight(-1)'),
Sheet.addCommand('KEY_DOWN', 'go-down',  'cursorDown(+1)'),
Sheet.addCommand('KEY_UP', 'go-up',    'cursorDown(-1)'),
Sheet.addCommand('KEY_RIGHT', 'go-right', 'cursorRight(+1)'),
Sheet.addCommand('KEY_NPAGE', 'next-page', 'cursorDown(nVisibleRows); sheet.topRowIndex += nVisibleRows'),
Sheet.addCommand('KEY_PPAGE', 'prev-page', 'cursorDown(-nVisibleRows); sheet.topRowIndex -= nVisibleRows'),

Sheet.addCommand('gh', 'go-leftmost', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = 0'),
Sheet.addCommand('KEY_HOME', 'go-top', 'sheet.cursorRowIndex = sheet.topRowIndex = 0'),
Sheet.addCommand('KEY_END', 'go-bottom', 'sheet.cursorRowIndex = len(rows); sheet.topRowIndex = cursorRowIndex-nVisibleRows'),
Sheet.addCommand('gl', 'go-rightmost', 'sheet.leftVisibleColIndex = len(visibleCols)-1; pageLeft(); sheet.cursorVisibleColIndex = len(visibleCols)-1'),

Sheet.addCommand('BUTTON1_PRESSED', 'go-mouse', 'sheet.cursorRowIndex=topRowIndex+mouseY-1'),
Sheet.addCommand('BUTTON1_RELEASED', 'scroll-mouse', 'sheet.topRowIndex=cursorRowIndex-mouseY+1'),
Sheet.addCommand('BUTTON4_PRESSED', 'scroll-up', 'cursorDown(options.scroll_incr); sheet.topRowIndex += options.scroll_incr'),
Sheet.addCommand('REPORT_MOUSE_POSITION', 'scroll-down', 'cursorDown(-options.scroll_incr); sheet.topRowIndex -= options.scroll_incr'),

Sheet.addCommand('^G', 'show-cursor', 'status(statusLine)'),

Sheet.addCommand('_', 'resize-col-max', 'cursorCol.toggleWidth(cursorCol.getMaxWidth(visibleRows))'),
Sheet.addCommand('z_', 'resize-col', 'cursorCol.width = int(input("set width= ", value=cursorCol.width))'),

Sheet.addCommand('-', 'hide-col', 'cursorCol.hide()'),
Sheet.addCommand('z-', 'resize-col-half', 'cursorCol.width = cursorCol.width//2'),
Sheet.addCommand('gv', 'unhide-cols', 'for c in columns: c.width = abs(c.width or 0) or c.getMaxWidth(visibleRows)'),

Sheet.addCommand('!', 'key-col', 'toggleKeys([cursorCol])'),
Sheet.addCommand('z!', 'key-col-off', 'unsetKeys([cursorCol])'),
Sheet.addCommand('g_', 'resize-cols-max', 'for c in visibleCols: c.width = c.getMaxWidth(visibleRows)'),

Sheet.addCommand('[', 'sort-asc', 'orderBy(cursorCol)'),
Sheet.addCommand(']', 'sort-desc', 'orderBy(cursorCol, reverse=True)'),
Sheet.addCommand('g[', 'sort-keys-asc', 'orderBy(*keyCols)'),
Sheet.addCommand('g]', 'sort-keys-desc', 'orderBy(*keyCols, reverse=True)'),

Sheet.addCommand('^R', 'reload-sheet', 'reload(); recalc(); status("reloaded")'),

Sheet.addCommand('e', 'edit-cell', 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex)); options.cmd_after_edit and sheet.exec_keystrokes(options.cmd_after_edit)'),
Sheet.addCommand('ge', 'edit-cells', 'cursorCol.setValuesTyped(selectedRows or rows, input("set selected to: ", value=cursorDisplay))'),

Sheet.addCommand('"', 'dup-selected', 'vs=copy(sheet); vs.name += "_selectedref"; vs.rows=tuple(); vs.reload=lambda vs=vs,rows=selectedRows or rows: setattr(vs, "rows", list(rows)); vd.push(vs)'),
Sheet.addCommand('g"', 'dup-rows', 'vs = copy(sheet); vs.name += "_copy"; vs.rows = list(rows); vs.select(selectedRows); vd.push(vs)'),
Sheet.addCommand('z"', 'dup-selected-deep', 'vs = deepcopy(sheet); vs.name += "_selecteddeepcopy"; vs.rows = async_deepcopy(vs, selectedRows or rows); vd.push(vs); status("pushed sheet with async deepcopy of selected rows")'),
Sheet.addCommand('gz"', 'dup-rows-deep', 'vs = deepcopy(sheet); vs.name += "_deepcopy"; vs.rows = async_deepcopy(vs, rows); vd.push(vs); status("pushed sheet with async deepcopy of all rows")'),

Sheet.addCommand('=', 'addcol-expr', 'addColumn(ColumnExpr(inputExpr("new column expr=")), index=cursorColIndex+1)'),
Sheet.addCommand('g=', 'setcol-expr', 'cursorCol.setValuesFromExpr(selectedRows or rows, inputExpr("set selected="))'),

Sheet.addCommand('V', 'view-cell', 'vd.push(TextSheet("%s[%s].%s" % (name, cursorRowIndex, cursorCol.name), cursorDisplay.splitlines()))'),

Sheet.bindkey('gKEY_LEFT', 'go-leftmost'),
Sheet.bindkey('gKEY_RIGHT', 'go-rightmost'),
Sheet.bindkey('gKEY_UP', 'go-top'),
Sheet.bindkey('gKEY_DOWN', 'go-bottom'),


def isNullFunc():
    return lambda v,nulls=set([None, options.null_value]): v in nulls or isinstance(v, TypedWrapper)


@functools.total_ordering
class TypedWrapper:
    def __init__(self, func, *args):
        self.type = func
        self.args = args
        self.val = args[0] if args else None

    def __bool__(self):
        return False

    def __str__(self):
        return '%s(%s)' % (self.type.__name__, ','.join(str(x) for x in self.args))

    def __lt__(self, x):
        'maintain sortability; wrapped objects are always least'
        return True

    def __add__(self, x):
        return x

    def __radd__(self, x):
        return x

    def __hash__(self):
        return hash((self.type, str(self.val)))

    def __eq__(self, x):
        if isinstance(x, TypedWrapper):
            return self.type == x.type and self.val == x.val

class TypedExceptionWrapper(TypedWrapper):
    def __init__(self, func, *args, exception=None):
        TypedWrapper.__init__(self, func, *args)
        self.exception = exception
        self.stacktrace = stacktrace()
        self.forwarded = False

    def __str__(self):
        return str(self.exception)

    def __hash__(self):
        return hash((type(self.exception), ''.join(self.stacktrace[:-1])))

    def __eq__(self, x):
        if isinstance(x, TypedExceptionWrapper):
            return type(self.exception) is type(x.exception) and self.stacktrace[:-1] == x.stacktrace[:-1]

def forward(wr):
    if isinstance(wr, TypedExceptionWrapper):
        wr.forwarded = True
    return wr

def wrmap(func, iterable, *args):
    'Same as map(func, iterable, *args), but ignoring exceptions.'
    for it in iterable:
        try:
            yield func(it, *args)
        except Exception as e:
            pass

def wrapply(func, *args, exc_type=Exception, **kwargs):
    'Like apply(), but which wraps Exceptions and passes through Wrappers (if first arg)'
    val = args[0]
    if val is None:
        return TypedWrapper(func, None)
    elif isinstance(val, TypedExceptionWrapper):
        tew = copy(val)
        tew.forwarded = True
        return tew
    elif isinstance(val, TypedWrapper):
        return val
    elif isinstance(val, Exception):
        return TypedWrapper(func, *args)

    try:
        return func(*args, **kwargs)
    except exc_type as e:
        e.stacktrace = stacktrace()
        return TypedExceptionWrapper(func, *args, exception=e)


class Column:
    def __init__(self, name='', *, type=anytype, cache=False, **kwargs):
        self.sheet = None     # owning Sheet, set in Sheet.addColumn
        self.name = name      # display visible name
        self.fmtstr = ''      # by default, use str()
        self.type = type      # anytype/str/int/float/date/func
        self.getter = lambda col, row: row
        self.setter = lambda col, row, value: fail(col.name+' column cannot be changed')
        self.width = None     # == 0 if hidden, None if auto-compute next time
        self.keycol = False   # is a key column
        self.expr = None      # Column-type-dependent parameter

        self._cachedValues = collections.OrderedDict() if cache else None
        for k, v in kwargs.items():
            setattr(self, k, v)  # instead of __dict__.update(kwargs) to invoke property.setters

    def __copy__(self):
        cls = self.__class__
        ret = cls.__new__(cls)
        ret.__dict__.update(self.__dict__)
        ret.keycol = False   # column copies lose their key status
        if self._cachedValues is not None:
            ret._cachedValues = collections.OrderedDict()  # an unrelated cache for copied columns
        return ret

    def __deepcopy__(self, memo):
        return self.__copy__()  # no separate deepcopy

    def recalc(self, sheet=None):
        'reset column cache, attach to sheet, and reify name'
        if self._cachedValues:
            self._cachedValues.clear()
        if sheet:
            self.sheet = sheet
        self.name = self._name

    @property
    def name(self):
        return self._name or ''

    @name.setter
    def name(self, name):
        if isinstance(name, str):
            name = name.strip()
        if options.force_valid_colnames:
            name = clean_to_id(name)
        self._name = name

    @property
    def fmtstr(self):
        return self._fmtstr or getType(self.type).fmtstr

    @fmtstr.setter
    def fmtstr(self, v):
        self._fmtstr = v

    def format(self, typedval):
        'Return displayable string of `typedval` according to `Column.fmtstr`'
        if typedval is None:
            return None

        if isinstance(typedval, (list, tuple)):
            return '[%s]' % len(typedval)
        if isinstance(typedval, dict):
            return '{%s}' % len(typedval)
        if isinstance(typedval, bytes):
            typedval = typedval.decode(options.encoding, options.encoding_errors)

        return getType(self.type).formatter(self.fmtstr, typedval)

    def hide(self, hide=True):
        if hide:
            self.width = 0
        else:
            self.width = abs(self.width or self.getMaxWidth(self.sheet.visibleRows))

    @property
    def hidden(self):
        'A column is hidden if its width <= 0. (width==None means not-yet-autocomputed).'
        if self.width is None:
            return False
        return self.width <= 0

    def getValueRows(self, rows):
        'Generate (val, row) for the given `rows` at this Column, excluding errors and nulls.'
        f = isNullFunc()

        for r in Progress(rows):
            try:
                v = self.getTypedValue(r)
                if not f(v):
                    yield v, r
            except Exception:
                pass

    def getValues(self, rows):
        for v, r in self.getValueRows(rows):
            yield v

    def calcValue(self, row):
        return (self.getter)(self, row)

    def getTypedValue(self, row):
        'Returns the properly-typed value for the given row at this column.'
        return wrapply(self.type, wrapply(self.getValue, row))

    def getTypedValueOrException(self, row):
        'Returns the properly-typed value for the given row at this column, or an Exception object.'
        return wrapply(self.type, wrapply(self.getValue, row))

    def getTypedValueNoExceptions(self, row):
        '''Returns the properly-typed value for the given row at this column.
           Returns the type's default value if either the getter or the type conversion fails.'''
        return wrapply(self.type, wrapply(self.getValue, row))

    def getValue(self, row):
        'Memoize calcValue with key id(row)'
        if self._cachedValues is None:
            return self.calcValue(row)

        k = id(row)
        if k in self._cachedValues:
            return self._cachedValues[k]

        ret = self.calcValue(row)
        self._cachedValues[k] = ret

        cachesize = options.col_cache_size
        if cachesize > 0 and len(self._cachedValues) > cachesize:
            self._cachedValues.popitem(last=False)

        return ret

    def getCell(self, row, width=None):
        'Return DisplayWrapper for displayable cell value.'
        cellval = wrapply(self.getValue, row)
        typedval = wrapply(self.type, cellval)

        if isinstance(typedval, TypedWrapper):
            if isinstance(cellval, TypedExceptionWrapper):  # calc failed
                exc = cellval.exception
                if cellval.forwarded:
                    dispval = str(cellval)  # traceback.format_exception_only(type(exc), exc)[-1].strip()
                else:
                    dispval = options.disp_error_val
                return DisplayWrapper(cellval.val, error=exc.stacktrace,
                                        display=dispval,
                                        note=options.note_getter_exc,
                                        notecolor='color_error')
            elif typedval.val is None:  # early out for strict None
                return DisplayWrapper(None, display='',  # force empty display for None
                                            note=options.disp_note_none,
                                            notecolor='color_note_type')
            elif isinstance(typedval, TypedExceptionWrapper):  # calc succeeded, type failed
                return DisplayWrapper(typedval.val, display=str(cellval),
                                            error=typedval.exception.stacktrace,
                                            note=options.note_type_exc,
                                            notecolor='color_warning')
            else:
                return DisplayWrapper(typedval.val, display=str(typedval.val),
                                            note=options.note_type_exc,
                                            notecolor='color_warning')

        elif isinstance(typedval, threading.Thread):
            return DisplayWrapper(None,
                                display=options.disp_pending,
                                note=options.note_pending,
                                notecolor='color_note_pending')

        dw = DisplayWrapper(cellval)

        try:
            dw.display = self.format(typedval) or ''

            if width and isNumeric(self):
                dw.display = dw.display.rjust(width-1)

            # annotate cells with raw value type in anytype columns, except for strings
            if self.type is anytype and type(cellval) is not str:
                typedesc = typemap.get(type(cellval), None)
                dw.note = typedesc.icon if typedesc else options.note_unknown_type
                dw.notecolor = 'color_note_type'

        except Exception as e:  # formatting failure
            e.stacktrace = stacktrace()
            dw.error = e
            try:
                dw.display = str(cellval)
            except Exception as e:
                dw.display = str(e)
            dw.note = options.note_format_exc
            dw.notecolor = 'color_warning'

        return dw

    def getDisplayValue(self, row):
        return self.getCell(row).display

    def setValue(self, row, value):
        'Set our column value on row.  defaults to .setter; override in Column subclass. no type checking'
        return self.setter(self, row, value)

    def setValues(self, rows, *values):
        'Set our column value for given list of rows to `value`.'
        for r, v in zip(rows, itertools.cycle(values)):
            self.setValue(r, v)
        self.recalc()
        return status('set %d cells to %d values' % (len(rows), len(values)))

    def setValuesTyped(self, rows, *values):
        'Set values on this column for rows, coerced to the column type.  will stop on first exception in type().'
        for r, v in zip(rows, itertools.cycle(self.type(val) for val in values)):
            self.setValue(r, v)
        self.recalc()
        return status('set %d cells to %d values' % (len(rows), len(values)))

    @asyncthread
    def setValuesFromExpr(self, rows, expr):
        compiledExpr = compile(expr, '<expr>', 'eval')
        for row in Progress(rows):
            self.setValue(row, self.sheet.evalexpr(compiledExpr, row))
        self.recalc()
        status('set %d values = %s' % (len(rows), expr))

    def getMaxWidth(self, rows):
        'Return the maximum length of any cell in column or its header.'
        w = 0
        if len(rows) > 0:
            w = max(max(len(self.getDisplayValue(r)) for r in rows), len(self.name))+2
        return max(w, len(self.name))

    def toggleWidth(self, width):
        'Change column width to either given `width` or default value.'
        if self.width != width:
            self.width = width
        else:
            self.width = int(options.default_width)


# ---- Column makers

def setitem(r, i, v):  # function needed for use in lambda
    r[i] = v
    return True

def getattrdeep(obj, attr, *default):
    'Return dotted attr (like "a.b.c") from obj, or default if any of the components are missing.'
    attrs = attr.split('.')
    if default:
        getattr_default = lambda o,a,d=default[0]: getattr(o, a, d)
    else:
        getattr_default = lambda o,a: getattr(o, a)

    for a in attrs[:-1]:
        obj = getattr_default(obj, a)

    return getattr_default(obj, attrs[-1])

def setattrdeep(obj, attr, val):
    'Set dotted attr (like "a.b.c") on obj to val.'
    attrs = attr.split('.')

    for a in attrs[:-1]:
        obj = getattr(obj, a)
    setattr(obj, attrs[-1], val)


def ColumnAttr(name='', attr=None, **kwargs):
    'Column using getattr/setattr of given attr.'
    return Column(name,
                  expr=attr if attr is not None else name,
                  getter=lambda col,row: getattrdeep(row, col.expr),
                  setter=lambda col,row,val: setattrdeep(row, col.expr, val),
                  **kwargs)

def ColumnItem(name='', key=None, **kwargs):
    'Column using getitem/setitem of given key.'
    return Column(name,
            expr=key if key is not None else name,
            getter=lambda col,row: row[col.expr],
            setter=lambda col,row,val: setitem(row, col.expr, val),
            **kwargs)

def ArrayNamedColumns(columns):
    'Return list of ColumnItems from given list of column names.'
    return [ColumnItem(colname, i) for i, colname in enumerate(columns)]

def ArrayColumns(ncols):
    'Return list of ColumnItems for given row length.'
    return [ColumnItem('', i, width=8) for i in range(ncols)]


class SubrowColumn(Column):
    def __init__(self, name, origcol, subrowidx, **kwargs):
        super().__init__(name, type=origcol.type, width=origcol.width, **kwargs)
        self.origcol = origcol
        self.expr = subrowidx

    def getValue(self, row):
        subrow = row[self.expr]
        if subrow is not None:
            return self.origcol.getValue(subrow)

    def setValue(self, row, value):
        subrow = row[self.expr]
        if subrow is None:
            fail('no source row')
        self.origcol.setValue(subrow, value)

    def recalc(self, sheet=None):
        Column.recalc(self, sheet)
        self.origcol.recalc()  # reset cache but don't change sheet


class DisplayWrapper:
    def __init__(self, value, **kwargs):
        self.value = value
        self.__dict__.update(kwargs)

    def __bool__(self):
        return self.value


class ColumnEnum(Column):
    'types and aggregators. row.<name> should be kept to the values in the mapping m, and can be set by the a string key into the mapping.'
    def __init__(self, name, m, default=None):
        super().__init__(name)
        self.mapping = m
        self.default = default

    def getValue(self, row):
        v = getattr(row, self.name, None)
        return v.__name__ if v else None

    def setValue(self, row, value):
        if isinstance(value, str):  # first try to get the actual value from the mapping
            value = self.mapping.get(value, value)
        setattr(row, self.name, value or self.default)


class LazyMapRow:
    'Calculate column values as needed.'
    def __init__(self, sheet, row):
        self.row = row
        self.sheet = sheet
        self._keys = [c.name for c in self.sheet.columns]

    def keys(self):
        return self._keys

    def __getitem__(self, colid):
        try:
            i = self._keys.index(colid)
            return self.sheet.columns[i].getTypedValue(self.row)
        except ValueError:
            if colid in ['row', '__row__']:
                return self.row
            elif colid in ['sheet', '__sheet__']:
                return self.sheet
            raise KeyError(colid)


class ColumnExpr(Column):
    def __init__(self, name, expr=None):
        super().__init__(name)
        self.expr = expr or name

    def calcValue(self, row):
        return self.sheet.evalexpr(self.compiledExpr, row)

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, expr):
        self._expr = expr
        self.compiledExpr = compile(expr, '<expr>', 'eval') if expr else None

###

def confirm(prompt):
    yn = input(prompt, value='no', record=False)[:1]
    if not yn or yn not in 'Yy':
        fail('disconfirmed')
    return True


import unicodedata
@functools.lru_cache(maxsize=8192)
def clipstr(s, dispw):
    '''Return clipped string and width in terminal display characters.

    Note: width may differ from len(s) if East Asian chars are 'fullwidth'.'''
    w = 0
    ret = ''
    ambig_width = options.disp_ambig_width
    for c in s:
        if c != ' ' and unicodedata.category(c) in ('Cc', 'Zs', 'Zl'):  # control char, space, line sep
            c = options.disp_oddspace

        if c:
            c = c[0]  # multi-char disp_oddspace just uses the first char
            ret += c
            eaw = unicodedata.east_asian_width(c)
            if eaw == 'A':  # ambiguous
                w += ambig_width
            elif eaw in 'WF': # wide/full
                w += 2
            elif not unicodedata.combining(c):
                w += 1

        if w > dispw-len(options.disp_truncator)+1:
            ret = ret[:-2] + options.disp_truncator  # replace final char with ellipsis
            w += len(options.disp_truncator)
            break

    return ret, w


## text viewer and dir browser
# rowdef: (linenum, str)
class TextSheet(Sheet):
    'Displays any iterable source, with linewrap if wrap set in init kwargs or options.'
    rowtype = 'lines'
    filetype = 'txt'
    columns = [
        ColumnItem('linenum', 0, type=int, width=0),
        ColumnItem('text', 1),
    ]

    def __init__(self, name, source, **kwargs):
        super().__init__(name, source=source, **kwargs)

    @asyncthread
    def reload(self):
        self.rows = []
        winWidth = min(self.columns[1].width or 78, vd().windowWidth-2)
        wrap = options.wrap
        for startingLine, text in enumerate(self.source):
            if wrap and text:
                for i, L in enumerate(textwrap.wrap(str(text), width=winWidth)):
                    self.addRow([startingLine+i+1, L])
            else:
                self.addRow([startingLine+1, text])

TextSheet.addCommand('v', 'visibility', 'options.set("wrap", not options.wrap, sheet); reload(); status("text%s wrapped" % ("" if options.wrap else " NOT")); ')

### Curses helpers

def clipdraw(scr, y, x, s, attr, w=None, rtl=False):
    'Draw string `s` at (y,x)-(y,x+w), clipping with ellipsis char.  if rtl, draw inside (x-w, x).  Returns width drawn (max of w).'
    if not scr:
        return 0
    _, windowWidth = scr.getmaxyx()
    dispw = 0
    try:
        if w is None:
            w = windowWidth-1
        w = min(w, (x-1) if rtl else (windowWidth-x-1))
        if w <= 0:  # no room anyway
            return 0

        # convert to string just before drawing
        clipped, dispw = clipstr(str(s), w)
        if rtl:
            # clearing whole area (w) has negative display effects; clearing just dispw area is useless
#            scr.addstr(y, x-dispw-1, disp_column_fill*dispw, attr)
            scr.addstr(y, x-dispw-1, clipped, attr)
        else:
            scr.addstr(y, x, disp_column_fill*w, attr)  # clear whole area before displaying
            scr.addstr(y, x, clipped, attr)
    except Exception as e:
        pass
#        raise type(e)('%s [clip_draw y=%s x=%s dispw=%s w=%s clippedlen=%s]' % (e, y, x, dispw, w, len(clipped))
#                ).with_traceback(sys.exc_info()[2])

    return dispw


# https://stackoverflow.com/questions/19833315/running-system-commands-in-python-using-curses-and-panel-and-come-back-to-previ
class SuspendCurses:
    'Context Manager to temporarily leave curses mode'
    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        newscr = curses.initscr()
        newscr.refresh()
        curses.doupdate()

class EnableCursor:
    def __enter__(self):
        with suppress(curses.error):
            curses.mousemask(0)
            curses.curs_set(1)

    def __exit__(self, exc_type, exc_val, tb):
        with suppress(curses.error):
            curses.curs_set(0)
            curses.mousemask(-1)

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

        if linenum:
            launchEditor(temp.name, '+%s' % linenum)
        else:
            launchEditor(temp.name)

        with open(temp.name, 'r') as fp:
            r = fp.read()
            if r[-1] == '\n':  # trim inevitable trailing newline
                r = r[:-1]
            return r

def suspend():
    import signal
    with SuspendCurses():
        os.kill(os.getpid(), signal.SIGSTOP)

# history: earliest entry first
def editText(scr, y, x, w, i=0, attr=curses.A_NORMAL, value='', fillchar=' ', truncchar='-', unprintablechar='.', completer=lambda text,idx: None, history=[], display=True):
    'A better curses line editing widget.'
    ESC='^['
    ENTER='^J'
    TAB='^I'

    def until_get_wch():
        'Ignores get_wch timeouts'
        ret = None
        while not ret:
            try:
                ret = scr.get_wch()
            except curses.error:
                pass

        return ret

    def splice(v, i, s):
        'Insert `s` into string `v` at `i` (such that v[i] == s[0]).'
        return v if i < 0 else v[:i] + s + v[i:]

    def clean_printable(s):
        'Escape unprintable characters.'
        return ''.join(c if c.isprintable() else ('<%04X>' % ord(c)) for c in str(s))

    def delchar(s, i, remove=1):
        'Delete `remove` characters from str `s` beginning at position `i`.'
        return s if i < 0 else s[:i] + s[i+remove:]

    class CompleteState:
        def __init__(self, completer_func):
            self.comps_idx = -1
            self.completer_func = completer_func
            self.former_i = None
            self.just_completed = False

        def complete(self, v, i, state_incr):
            self.just_completed = True
            self.comps_idx += state_incr

            if self.former_i is None:
                self.former_i = i
            try:
                r = self.completer_func(v[:self.former_i], self.comps_idx)
            except Exception as e:
                # beep/flash; how to report exception?
                return v, i

            if not r:
                # beep/flash to indicate no matches?
                return v, i

            v = r + v[i:]
            return v, len(v)

        def reset(self):
            if self.just_completed:
                self.just_completed = False
            else:
                self.former_i = None
                self.comps_idx = -1

    class HistoryState:
        def __init__(self, history):
            self.history = history
            self.hist_idx = None
            self.prev_val = None

        def up(self, v, i):
            if self.hist_idx is None:
                self.hist_idx = len(self.history)
                self.prev_val = v
            if self.hist_idx > 0:
                self.hist_idx -= 1
                v = self.history[self.hist_idx]
            i = len(v)
            return v, i

        def down(self, v, i):
            if self.hist_idx is None:
                return v, i
            elif self.hist_idx < len(self.history)-1:
                self.hist_idx += 1
                v = self.history[self.hist_idx]
            else:
                v = self.prev_val
                self.hist_idx = None
            i = len(v)
            return v, i

    history_state = HistoryState(history)
    complete_state = CompleteState(completer)
    insert_mode = True
    first_action = True
    v = str(value)  # value under edit

    # i = 0  # index into v, initial value can be passed in as argument as of 1.2
    if i != 0:
        first_action = False

    left_truncchar = right_truncchar = truncchar

    def rfind_nonword(s, a, b):
        while not s[b].isalnum() and b >= a:  # first skip non-word chars
            b -= 1
        while s[b].isalnum() and b >= a:
            b -= 1
        return b

    while True:
        if display:
            dispval = clean_printable(v)
        else:
            dispval = '*' * len(v)

        dispi = i  # the onscreen offset within the field where v[i] is displayed
        if len(dispval) < w:  # entire value fits
            dispval += fillchar*(w-len(dispval)-1)
        elif i == len(dispval):  # cursor after value (will append)
            dispi = w-1
            dispval = left_truncchar + dispval[len(dispval)-w+2:] + fillchar
        elif i >= len(dispval)-w//2:  # cursor within halfwidth of end
            dispi = w-(len(dispval)-i)
            dispval = left_truncchar + dispval[len(dispval)-w+1:]
        elif i <= w//2:  # cursor within halfwidth of beginning
            dispval = dispval[:w-1] + right_truncchar
        else:
            dispi = w//2  # visual cursor stays right in the middle
            k = 1 if w%2==0 else 0  # odd widths have one character more
            dispval = left_truncchar + dispval[i-w//2+1:i+w//2-k] + right_truncchar

        prew = clipdraw(scr, y, x, dispval[:dispi], attr, w)
        clipdraw(scr, y, x+prew, dispval[dispi:], attr, w-prew+1)
        scr.move(y, x+prew)
        ch = vd().getkeystroke(scr)
        if ch == '':                               continue
        elif ch == 'KEY_IC':                       insert_mode = not insert_mode
        elif ch == '^A' or ch == 'KEY_HOME':       i = 0
        elif ch == '^B' or ch == 'KEY_LEFT':       i -= 1
        elif ch in ('^C', '^Q', ESC):              raise EscapeException(ch)
        elif ch == '^D' or ch == 'KEY_DC':         v = delchar(v, i)
        elif ch == '^E' or ch == 'KEY_END':        i = len(v)
        elif ch == '^F' or ch == 'KEY_RIGHT':      i += 1
        elif ch in ('^H', 'KEY_BACKSPACE', '^?'):  i -= 1; v = delchar(v, i)
        elif ch == TAB:                            v, i = complete_state.complete(v, i, +1)
        elif ch == 'KEY_BTAB':                     v, i = complete_state.complete(v, i, -1)
        elif ch == ENTER:                          break
        elif ch == '^K':                           v = v[:i]  # ^Kill to end-of-line
        elif ch == '^O':                           v = launchExternalEditor(v)
        elif ch == '^R':                           v = str(value)  # ^Reload initial value
        elif ch == '^T':                           v = delchar(splice(v, i-2, v[i-1]), i)  # swap chars
        elif ch == '^U':                           v = v[i:]; i = 0  # clear to beginning
        elif ch == '^V':                           v = splice(v, i, until_get_wch()); i += 1  # literal character
        elif ch == '^W':                           j = rfind_nonword(v, 0, i-1); v = v[:j+1] + v[i:]; i = j+1  # erase word
        elif ch == '^Z':                           v = suspend()
        elif history and ch == 'KEY_UP':           v, i = history_state.up(v, i)
        elif history and ch == 'KEY_DOWN':         v, i = history_state.down(v, i)
        elif ch.startswith('KEY_'):                pass
        else:
            if first_action:
                v = ''
            if insert_mode:
                v = splice(v, i, ch)
            else:
                v = v[:i] + ch + v[i+1:]

            i += 1

        if i < 0: i = 0
        if i > len(v): i = len(v)
        first_action = False
        complete_state.reset()

    return v


class ColorMaker:
    def __init__(self):
        self.attrs = {}
        self.color_attrs = {}
        self.colorcache = {}

    def setup(self):
        if options.use_default_colors:
            curses.use_default_colors()
            default_bg = -1
        else:
            default_bg = curses.COLOR_BLACK

        self.color_attrs['black'] = curses.color_pair(0)

        for c in range(0, options.force_256_colors and 256 or curses.COLORS):
            curses.init_pair(c+1, c, default_bg)
            self.color_attrs[str(c)] = curses.color_pair(c+1)

        for c in 'red green yellow blue magenta cyan white'.split():
            colornum = getattr(curses, 'COLOR_' + c.upper())
            self.color_attrs[c] = curses.color_pair(colornum+1)

        for a in 'normal blink bold dim reverse standout underline'.split():
            self.attrs[a] = getattr(curses, 'A_' + a.upper())

    def keys(self):
        return list(self.attrs.keys()) + list(self.color_attrs.keys())

    def __getitem__(self, colornamestr):
        return self._colornames_to_attr(colornamestr)

    def __getattr__(self, optname):
        'colors.color_foo returns colors[options.color_foo]'
        return self.get_color(optname).attr

    @functools.lru_cache()
    def resolve_colors(self, colorstack):
        'Returns the curses attribute for the colorstack, a list of color option names sorted highest-precedence color first.'
        attr = CursesAttr()
        for coloropt in colorstack:
            c = self.get_color(coloropt)
            attr = attr.update_attr(c)
        return attr

    def _colornames_to_attr(self, colornamestr, precedence=0):
        attr = CursesAttr(0, precedence)
        for colorname in colornamestr.split(' '):
            if colorname in self.color_attrs:
                if not attr.color:
                    attr.color = self.color_attrs[colorname.lower()]
            elif colorname in self.attrs:
                attr.attributes |= self.attrs[colorname.lower()]
        return attr

    def get_color(self, optname, precedence=0):
        'colors.color_foo returns colors[options.color_foo]'
        r = self.colorcache.get(optname, None)
        if r is None:
            coloropt = options._get(optname)
            colornamestr = coloropt.value if coloropt else optname
            r = self.colorcache[optname] = self._colornames_to_attr(colornamestr, precedence)
        return r

colors = ColorMaker()

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
        vd().push(vs)  # first push does a reload

    status('Ctrl+H opens help')
    return vd().run(_scr)

def addGlobals(g):
    'importers can call `addGlobals(globals())` to have their globals accessible to execstrings'
    globals().update(g)

def getGlobals():
    return globals()

if __name__ == '__main__':
    run(*(TextSheet('contents', open(src)) for src in sys.argv[1:]))
