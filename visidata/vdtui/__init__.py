#!/usr/bin/env python3
#
# Copyright 2017-2018 Saul Pwanson  http://visidata.org

'vdtui: a curses framework for columnar data'

from builtins import *
import sys
import os
import collections
from collections import defaultdict
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
    def __init__(self, longname, execstr, helpstr='', undo=''):
        self.longname = longname
        self.execstr = execstr
        self.helpstr = helpstr
        self.undo = undo

def globalCommand(keystrokes, longname, execstr, **kwargs):
    commands.setdefault(longname, Command(longname, execstr, **kwargs))

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

def undoSelection(sheetstr):
    return undoAttrCopy('[%s]'%sheetstr, '_selectedRows')

undoBlocked = 'lambda: error("cannot undo")'
undoSheetRows = undoRows('sheet')
undoSheetCols = 'lambda sheet=sheet,oldcols=[copy(c) for c in columns]: setattr(sheet, "columns", oldcols)'
undoAddCols = undoAttrCopy('[sheet]', 'columns')
undoEditCell = undoSetValues('[cursorRow]', '[cursorCol]')
undoEditCells = undoSetValues('selectedRows or rows', '[cursorCol]')
undoSheetSelection = undoAttrCopy('[sheet]', '_selectedRows')

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

class AttrDict(dict):
    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v

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
                vd.callHook('set_option', k, v, obj)
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
replayableOption('encoding_errors', 'surrogateescape', 'encoding_errors passed to codecs.open')

replayableOption('regex_flags', 'I', 'flags to pass to re.compile() [AILMSUX]')
replayableOption('default_width', 20, 'default column width')
replayableOption('bulk_select_clear', False, 'clear selected rows before new bulk selections')

option('cmd_after_edit', 'go-down', 'command longname to execute after successful edit')
option('col_cache_size', 0, 'max number of cache entries in each cached column')
option('quitguard', False, 'confirm before quitting last sheet')

replayableOption('null_value', None, 'a value to be counted as null')

replayableOption('force_valid_colnames', False, 'clean column names to be valid Python identifiers')
option('debug', False, 'exit on error and display stacktrace')
curses_timeout = 100 # curses timeout in ms
timeouts_before_idle = 10
theme('force_256_colors', False, 'use 256 colors even if curses reports fewer')
theme('use_default_colors', False, 'curses use default terminal colors')

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
theme('note_format_exc', '?', 'cell note for an exception during formatting')
theme('note_getter_exc', '!', 'cell note for an exception during computation')
theme('note_type_exc', '!', 'cell note for an exception during type conversion')
theme('note_unknown_type', '', 'cell note for unknown types in anytype column')

theme('color_note_pending', 'bold magenta', 'color of note in pending cells')
theme('color_note_type', '226 yellow', 'cell note for numeric types in anytype columns')
theme('scroll_incr', 3, 'amount to scroll with scrollwheel')

ENTER='^J'
ESC='^['
globalCommand('KEY_RESIZE', 'no-op', '')
globalCommand('q', 'quit-sheet',  'vd.cmdlog.removeSheet(vd.quit())')
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
    return vd.status(*args, **kwargs)

def debug(*args, **kwargs):
    if options.debug:
        return vd.status(*args, **kwargs)

def input(*args, **kwargs):
    return vd.input(*args, **kwargs)

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
    return vd.exceptionCaught(e, **kwargs)

def stacktrace(e=None):
    if not e:
        return traceback.format_exc().strip().splitlines()
    return traceback.format_exception_only(type(e), e)

def chooseOne(choices):
    'Return one of `choices` elements (if list) or values (if dict).'
    ret = chooseMany(choices)
    if not ret:
        raise EscapeException()
    if len(ret) > 1:
        error('need only one choice')
    return ret[0]

def chooseMany(choices):
    'Return list of `choices` elements (if list) or values (if dict).'
    if isinstance(choices, dict):
        prompt = '/'.join(choices.keys())
        chosen = []
        for c in input(prompt+': ', completer=CompleteKey(choices)).split():
            poss = [choices[p] for p in choices if p.startswith(c)]
            if not poss:
                warning('invalid choice "%s"' % c)
            else:
                chosen.extend(poss)
    else:
        prompt = '/'.join(str(x) for x in choices)
        chosen = []
        for c in input(prompt+': ', completer=CompleteKey(choices)).split():
            poss = [p for p in choices if p.startswith(c)]
            if not poss:
                warning('invalid choice "%s"' % c)
            else:
                chosen.extend(poss)
    return chosen

def regex_flags():
    'Return flags to pass to regex functions from options'
    return sum(getattr(re, f.upper()) for f in options.regex_flags)


# define @asyncthread for potentially long-running functions
#   when function is called, instead launches a thread
def asyncthread(func):
    'Function decorator, to make calls to `func()` spawn a separate thread if available.'
    @functools.wraps(func)
    def _execAsync(*args, **kwargs):
        return vd.execAsync(func, *args, **kwargs)
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
                d[k] = vd.execAsync(_func, k, *args, **kwargs)
            return d.get(k)
        return _execAsync
    return _decorator


class Progress:
    def __init__(self, iterable=None, gerund="", total=None, sheet=None):
        self.iterable = iterable
        self.total = total if total is not None else len(iterable)
        self.sheet = sheet if sheet else getattr(threading.current_thread(), 'sheet', None)
        self.gerund = gerund
        self.made = 0

    def __enter__(self):
        if self.sheet:
            self.sheet.progresses.append(self)
        return self

    def addProgress(self, n):
        self.made += n
        return True

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
    for r in Progress(oldlist, 'copying'):
        newlist.append(deepcopy(r))

def async_deepcopy(vs, rowlist):
    ret = []
    _async_deepcopy(vs, ret, rowlist)
    return ret


class Extensible:
    @classmethod
    def init(cls, membername, initfunc):
        'Add `self.attr=T()` to cls.__init__.  Usage: cls.init("attr", T)'
        old = cls.__init__
        def new(self, *args, **kwargs):
            old(self, *args, **kwargs)
            setattr(self, membername, initfunc())
        cls.__init__ = new

    @classmethod
    def api(cls, func):
        setattr(cls, func.__name__, func)
        return func

    @classmethod
    def cached_property(cls, func):
        @property
        @functools.wraps(func)
        def get_if_not(self):
            name = '_' + func.__name__
            if not hasattr(self, name):
                setattr(self, name, func(self))
            return getattr(self, name)
        setattr(cls, func.__name__, get_if_not)
        return get_if_not

class VisiData(Extensible):
    allPrefixes = 'gz'  # embig'g'en, 'z'mallify

    def __call__(self):
        'Deprecated; use plain "vd"'
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
        self.mousereg = []
        self.threads = [] # all long-running threads, including main and finished
        self.addThread(threading.current_thread(), endTime=0)
        self.addHook('rstatus', lambda sheet,self=self: (self.keystrokes, 'color_keystrokes'))
        self.addHook('rstatus', self.rightStatus)

    def quit(self):
        if len(vd.sheets) == 1 and options.quitguard:
            confirm("quit last sheet? ")
        return vd.sheets.pop(0)

    @property
    def sheet(self):
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

    def sync(self, *joiningThreads):
        'Wait for joiningThreads to finish. If no joiningThreads specified, wait for all but current thread to finish.'
        joiningThreads = joiningThreads or (set(self.unfinishedThreads)-set([threading.current_thread()]))
        while any(t in self.unfinishedThreads for t in joiningThreads):
            for t in joiningThreads:
                try:
                    t.join()
                except RuntimeError:  # maybe thread hasn't started yet or has already joined
                    pass

    def refresh(self):
        Sheet.visibleCols.fget.cache_clear()
        Sheet.keyCols.fget.cache_clear()
        colors.colorcache.clear()
        self.mousereg.clear()

    def editText(self, y, x, w, record=True, **kwargs):
        'Wrap global editText with `preedit` and `postedit` hooks.'
        v = self.callHook('preedit') if record else None
        if not v or v[0] is None:
            with EnableCursor():
                v = editline(self.scr, y, x, w, **kwargs)
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

        try:
            lstatus = vs.leftStatus()
            maxwidth = options.disp_lstatus_max
            if maxwidth > 0:
                lstatus = middleTruncate(lstatus, maxwidth//2)

            y = self.windowHeight-1
            x = clipdraw(scr, y, 0, lstatus, attr)
            self.onMouse(scr, y, 0, 1, x,
                            BUTTON1_PRESSED='sheets',
                            BUTTON3_PRESSED='rename-sheet',
                            BUTTON3_CLICKED='rename-sheet')

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
            gerund = (' '+sheet.progresses[0].gerund) if sheet.progresses else ''
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
                self.keystrokes = ''.join(sorted(set(self.keystrokes)))  # prefix order/quantity does not matter
                self.prefixWaiting = True
            else:
                status('no command for "%s"' % (self.keystrokes))
                self.prefixWaiting = False

            self.checkForFinishedThreads()
            self.callHook('predraw')
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
                vs.creatingCommand = self.cmdlog.currentActiveRow

            self.sheets.insert(0, vs)

            if not vs.loaded:
                vs.reload()
                vs.recalc()  # set up Columns

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


class BaseSheet:
    _rowtype = object    # callable (no parms) that returns new empty item
    _coltype = None      # callable (no parms) that returns new settable view into that item
    rowtype = 'objects'  # one word, plural, describing the items
    precious = True      # False for a few discardable metasheets

    def __init__(self, name, **kwargs):
        self.name = name
        self.vd = vd

        # for progress bar
        self.progresses = []  # list of Progress objects

        # track all async threads from sheet
        self.currentThreads = []
        self.__dict__.update(kwargs)

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        else:
            return id(self) < id(other)

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

    def leftStatus(self):
        'Compose left side of status bar for this sheet (overridable).'
        return options.disp_status_fmt.format(sheet=self)

    def exec_keystrokes(self, keystrokes, vdglobals=None):
        return self.exec_command(self.getCommand(keystrokes), vdglobals, keystrokes=keystrokes)

    def exec_command(self, cmd, args='', vdglobals=None, keystrokes=None):
        "Execute `cmd` tuple with `vdglobals` as globals and this sheet's attributes as locals.  Returns True if user cancelled."
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
            self.vd = vd

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
        except Exception as e:
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

def wrapply(func, *args, **kwargs):
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
    except Exception as e:
        e.stacktrace = stacktrace()
        return TypedExceptionWrapper(func, *args, exception=e)


class DisplayWrapper:
    def __init__(self, value, **kwargs):
        self.value = value
        self.__dict__.update(kwargs)

    def __bool__(self):
        return self.value

###

def confirm(prompt):
    yn = input(prompt, value='no', record=False)[:1]
    if not yn or yn not in 'Yy':
        fail('disconfirmed')
    return True


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

from .cliptext import clipdraw, clipstr
from .editline import editline
from .column import *
from .color import colors, CursesAttr
from ._sheet import *
