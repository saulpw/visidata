#!/usr/bin/env python3
#
# Copyright 2017 Saul Pwanson  http://saul.pw/vdtui
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
__version__ = 'saul.pw/vdtui v1.1'
__author__ = 'Saul Pwanson <vdtui@saul.pw>'
__license__ = 'MIT'
__status__ = 'Production/Stable'

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

class EscapeException(BaseException):
    'Inherits from BaseException to avoid "except Exception" clauses.  Do not use a blanket "except:" or the task will be uncancelable.'
    pass

class ExpectedException(Exception):
    'an expected exception'
    pass

baseCommands = collections.OrderedDict()  # [cmd.name] -> Command
baseOptions = collections.OrderedDict()   # [opt.name] -> opt

class Command:
    def __init__(self, name, execstr, helpstr='', longname=None):
        self.name = name
        self.execstr = execstr
        self.helpstr = helpstr
        self.longname = longname

def globalCommand(keystrokes, execstr, helpstr='', longname=None):
    if isinstance(keystrokes, str):
        keystrokes = [keystrokes]

    if longname:
        cmd = Command(longname, execstr, helpstr, longname)
        baseCommands[longname] = cmd
        assert helpstr or (execstr in baseCommands), 'unknown longname ' + execstr
        helpstr = ''

    for ks in keystrokes:
        baseCommands[ks] = Command(ks, longname or execstr, helpstr, longname)

def option(name, default, helpstr=''):
    baseOptions[name] = [name, default, default, helpstr]
    globals()['options_'+name] = default


class OptionsObject:
    'minimalist options framework'
    def __init__(self, d):
        object.__setattr__(self, '_opts', d)

    def __getattr__(self, k):      # options.foo
        return self.__getitem__(k)

    def __setattr__(self, k, v):   # options.foo = v
        self.__setitem__(k, v)

    def __getitem__(self, k):      # options[k]
         name, value, default, helpstr = self._opts[k]
         return value

    def __setitem__(self, k, v):   # options[k] = v
        if k in self._opts:
            curval = self._opts[k][1]
            t = type(curval)
            if isinstance(v, str) and t is bool: # special case for bool options
                v = v and (v[0] not in "0fFnN")  # ''/0/false/no are false, everything else is true
            elif curval is not None:             # if None, do not apply type conversion
                v = t(v)
        else:
            status('setting unknown option %s' % k)
            option(k, v)

        self._opts[k][1] = v
        globals()['options_'+k] = v

options = OptionsObject(baseOptions)

alias = globalCommand
theme = option

option('encoding', 'utf-8', 'encoding passed to codecs.open')
option('encoding_errors', 'surrogateescape', 'encoding errors passed to codecs.open')

option('regex_flags', 'I', 'flags to pass to re.compile() [AILMSUX]')
option('default_width', 20, 'default column width')
option('wrap', False, 'wrap text to fit window width on TextSheet')

option('cmd_after_edit', 'j', 'command keystroke to execute after successful edit')
option('cmdlog_longname', False, 'Use command longname in cmdlog if available')

option('none_is_null', True, 'if Python None counts as null')
option('empty_is_null', False, 'if empty string counts as null')
option('false_is_null', False, 'if Python False counts as null')
option('zero_is_null', False, 'if integer 0 counts as null')


option('force_valid_colnames', False, 'clean column names to be valid Python identifiers')
option('debug', False, 'exit on error and display stacktrace')
option('curses_timeout', 100, 'curses timeout in ms')
theme('force_256_colors', False, 'use 256 colors even if curses reports fewer')
theme('use_default_colors', False, 'curses use default terminal colors')

disp_column_fill = ' ' # pad chars after column value
theme('disp_note_none', '⌀',  'visible contents of a cell whose value is None')
theme('disp_date_fmt','%Y-%m-%d', 'default fmtstr to strftime for date values')
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
theme('disp_error_val', '¿', 'displayed contents for computation exception')
theme('disp_ambig_width', 1, 'width to use for unicode chars marked ambiguous')

theme('color_default', 'normal', 'the default color')
theme('color_default_hdr', 'bold underline', 'color of the column headers')
theme('color_current_row', 'reverse', 'color of the cursor row')
theme('color_current_col', 'bold', 'color of the cursor column')
theme('color_current_hdr', 'reverse underline', 'color of the header for the cursor column')
theme('color_column_sep', '246 blue', 'color of column separators')
theme('color_key_col', '81 cyan', 'color of key columns')
theme('color_selected_row', '215 yellow', 'color of selected rows')

theme('color_status', 'bold', 'status line color')
theme('color_edit_cell', 'normal', 'cell color to use when editing cell')

theme('disp_pending', '', 'string to display in pending cells')
theme('note_pending', '⌛', 'note to display for pending cells')
theme('note_format_exc', '?', 'cell note for an exception during type conversion or formatting')
theme('note_getter_exc', '!', 'cell note for an exception during computation')

theme('color_note_pending', 'bold magenta', 'color of note in pending cells')
theme('color_note_type', '226 yellow', 'cell note for numeric types in anytype columns')
theme('color_format_exc', '48 bold green', 'color of formatting exception note')
theme('color_getter_exc', 'red bold', 'color of computation exception note')
theme('scroll_incr', 3, 'amount to scroll with scrollwheel')

ENTER='^J'
ESC='^['
globalCommand('KEY_RESIZE', '', 'no-op by default')
globalCommand('q',  'vd.sheets.pop(0)', 'quit current sheet', 'sheet-quit-current')
globalCommand('gq', 'vd.sheets.clear()', 'quit all sheets (clean exit)', 'sheet-quit-all')

globalCommand('^L', 'vd.scr.clear()', 'refresh screen')
globalCommand('^V', 'status(__version__)', 'show version information on status line', 'info-version')
globalCommand('^P', 'vd.push(TextSheet("statusHistory", vd.statusHistory, rowtype="statuses"))', 'open Status History', 'meta-status-history')

globalCommand('^E', 'vd.lastErrors and vd.push(TextSheet("last_error", vd.lastErrors[-1])) or status("no error")', 'view traceback for most recent error', 'info-errors-last')
globalCommand('^R', 'reload(); status("reloaded")', 'reload current sheet', 'sheet-reload')

globalCommand('^^', 'vd.sheets[1:] or error("no previous sheet"); vd.sheets[0], vd.sheets[1] = vd.sheets[1], vd.sheets[0]', 'jump to previous sheet (swap with current sheet)', 'view-go-sheet-swap')

globalCommand('g^E', 'vd.push(TextSheet("last_errors", sum(vd.lastErrors[-10:], [])))', 'view traceback for most recent errors', 'info-errors-all')

globalCommand('S', 'vd.push(SheetsSheet("sheets"))', 'open Sheets Sheet', 'meta-sheets')
globalCommand('O', 'vd.push(vd.optionsSheet)', 'open Options', 'meta-options')
globalCommand(['KEY_F(1)', 'z?'], 'vd.push(HelpSheet(name + "_commands", source=sheet))', 'view sheet of commands and keybindings', 'meta-commands')
globalCommand('^Z', 'suspend()', 'suspend VisiData process')

alias(ENTER, 'modify-edit-cell')  # ENTER is this by default
alias('delete-column-hide', 'schema-column-hide')
alias('h', 'view-go-left'),
alias('j', 'view-go-down'),
alias('k', 'view-go-up'),
alias('l', 'view-go-right'),
alias('gKEY_LEFT', 'view-go-far-left'),
alias('gKEY_RIGHT', 'view-go-far-right'),
alias('gKEY_UP', 'view-go-top'),
alias('gKEY_DOWN', 'view-go-bottom'),
alias('^F', 'view-go-page-down'),
alias('^B', 'view-go-page-up'),
alias(['gg', 'gk'], 'view-go-far-top'),
alias(['G', 'gj'], 'view-go-far-bottom'),
alias('gh', 'view-go-far-left'),
alias('gl', 'view-go-far-right'),

# VisiData uses Python native int, float, str, and adds simple date, currency, and anytype.
#
# A type T is used internally in these ways:
#    o = T(val)   # for interpreting raw value
#    o = T(str)   # for conversion from string (when setting)
#    o = T()      # for default value to be used when conversion fails
#
# The resulting object o must be orderable and convertible to a string for display and certain outputs (like csv).

def anytype(r=None):
    'minimalist "any" type'
    return r
anytype.__name__ = ''

floatchars='+-0123456789.'
def currency(s=''):
    'dirty float (strip non-numeric characters)'
    if isinstance(s, str):
        s = ''.join(ch for ch in s if ch in floatchars)
    return float(s) if s else float()

try:
    import dateutil.parser
except ImportError:
    pass


@functools.total_ordering
class date:
    'datetime wrapper, constructed from time_t or from str with dateutil.parse'

    def __init__(self, s=None):
        if s is None:
            self.dt = datetime.datetime.now()
        elif isinstance(s, int) or isinstance(s, float):
            self.dt = datetime.datetime.fromtimestamp(s)
        elif isinstance(s, str):
            self.dt = dateutil.parser.parse(s)
        elif isinstance(s, date):
            self.dt = s.dt
        else:
            assert isinstance(s, datetime.datetime), (type(s), s)
            self.dt = s

    def to_string(self, fmtstr=None):
        'Convert datetime object to string, using options.disp_date_fmt.'
        if not fmtstr:
            fmtstr = options.disp_date_fmt
        return self.dt.strftime(fmtstr)

    def __getattr__(self, k):
        'Forward unknown attributes to inner datetime object'
        return getattr(self.dt, k)

    def __str__(self):
        return self.to_string()
    def __hash__(self):
        return hash(self.dt)
    def __float__(self):
        return self.dt.timestamp()
    def __lt__(self, a):
        return self.dt < a.dt
    def __eq__(self, a):
        return self.dt == a.dt
    def __sub__(self, a):
        return self.dt - a.dt
    def __add__(self, a):
        return date(self.dt + a)

typemap = {
    None: 'Ø',
    str: '',
    date: '@',
    int: '#',
    len: '#',
    currency: '$',
    float: '%',
    anytype: '',
}

def joinSheetnames(*sheetnames):
    'Concatenate sheet names in a standard way'
    return '_'.join(str(x) for x in sheetnames)

def error(s):
    'Raise an expection.'
    status(s)
    raise ExpectedException(s)

def status(*args):
    'Return status property via function call.'
    return vd().status(*args)

def input(*args, **kwargs):
    return vd().input(*args, **kwargs)

def moveListItem(L, fromidx, toidx):
    "Move element within list `L` and return element's new index."
    r = L.pop(fromidx)
    L.insert(toidx, r)
    return toidx

def enumPivot(L, pivotIdx):
    '''Model Python `enumerate()` but starting midway through sequence `L`.

    Begin at index following `pivotIdx`, traverse through end.
    At sequence-end, begin at sequence-head, continuing through `pivotIdx`.'''
    rng = range(pivotIdx+1, len(L))
    rng2 = range(0, pivotIdx+1)
    for i in itertools.chain(rng, rng2):
        yield i, L[i]

def clean_to_id(s):  # [Nas Banov] https://stackoverflow.com/a/3305731
    return re.sub(r'\W|^(?=\d)', '_', str(s))

def middleTruncate(s, w):
    if len(s) <= w:
        return s
    return s[:w] + options.disp_truncator + s[-w:]

@functools.lru_cache()
def vd():
    'Return VisiData singleton, which contains all global context'
    return VisiData()

def exceptionCaught(e, **kwargs):
    return vd().exceptionCaught(e, **kwargs)

def stacktrace():
    return traceback.format_exc().strip().splitlines()

option('color_menu_prefix', 'green', 'color of accepted menu part')
option('color_menu_option', 'white', 'default menu color')
option('color_menu_cursor', 'bold reverse', 'color of menu cursor')
option('color_menu_help', 'bold', 'color of menu help text')
option('disp_menu_helpfmt', '{bindings} ⇨ {helpstr}', 'string between command keybindings and helpstr in menu') # ⇢ ⇒ → ↠
option('disp_menu_helpsep', ' | ', 'string between submenu options')

def cmdhelp(cmdname, sheet):
    cmd = sheet.getCommand(cmdname)
    if not cmd:
        return None

    helpstr = getattr(cmd, 'helpstr', '')
    helpstr = helpstr.replace("current cell", '[%s]' % clipstr(sheet.cursorDisplay, 10)[0])
    helpstr = helpstr.replace("current column", '[%s]' % sheet.cursorCol.name)
    selrowstr = "selected rows"
    if sheet._selectedRows:
        selrowstr = "%s selected rows" % len(sheet._selectedRows)
    else:
        if "selectedRows or rows" in cmd.execstr:
            selrowstr = "all %s rows" % len(sheet.rows)
        else:
            selrowstr = "[no rows selected]" # will have no effect
    helpstr = helpstr.replace("selected rows", selrowstr)
    helpstr = helpstr.replace("rows", '[%s]' % sheet.rowtype)

    # get all keybindings to cmdname
    bindings = set(cmd.name for cmd in sheet._commands.values() if sheet.getCommand(cmd.name).longname == cmdname and cmd.name != cmdname)
    bindings = ' '.join(bindings)
    return options.disp_menu_helpfmt.format(**locals())

def cmdsort(cmds):
    return list(cmds.keys())


def choose(cmdtree, helpfunc=None, sheet=None):
    '''`cmdtree` is dict of str to nested dict or leaf. Returns leaf, or None, or raises Exception.
    helpfunc(cmdname, sheet) should return a helpstr for the given cmdname (composed from the cmdtree)'''
    vdobj = vd()
    scr = vdobj.scr
    sheet = sheet or vdobj.sheets[0]

    v = vd().callHook('preedit')
    if v and v[0]:
        for part in v[0].split('-'):
            if part+'-' in cmdtree:
                cmdtree = cmdtree[part+'-']
            else:
                cmdtree = cmdtree[part]
                break
        return cmdtree

    cmdpath = [[cmdtree, 0]]
    while cmdpath:
        curlevel = cmdpath[-1]
        curnode, curidx = curlevel

        if not isinstance(curnode, dict): # leaf node
            longname = ''.join(cmdsort(n)[i] for n,i in cmdpath[:-1])
            vd().callHook('postedit', longname)
            return curnode

        menuy = vdobj.windowHeight-1
        helpy = vdobj.windowHeight-2
        width = vdobj.windowWidth
        sheet.draw(scr)
        lstatus = vdobj.drawLeftStatus(scr, sheet)
        menux = len(lstatus)+2

        rstatus = vdobj.drawRightStatus(scr, sheet)
        scr.addstr(helpy, 0, ' '*width, 0)

        # curnode[cmdkeys[curidx]] is the entry (dict or leaf)
        cmdkeys = cmdsort(curnode) or error('nothing to choose from')

        # fix topmost cursor
        if curidx < 0: curidx = curlevel[1] = 0
        elif curidx >= len(cmdkeys): curidx = curlevel[1] = len(cmdkeys)-1

        maxitemwidth = max(len(x) for x in cmdkeys)+2
        menuwidth = width - menux - len(rstatus) - 2
        nVisibleItems = menuwidth//maxitemwidth
        nItems = len(cmdkeys)
        leftidx = 0
        if nItems > nVisibleItems:
            middleidx = nVisibleItems//2
            leftidx = max(curidx - middleidx, 0)

        scr.addstr(menuy, menux, ' '*menuwidth, 0)

        # draw the currently selected path on the left
        regattr = colors[options.color_menu_prefix]
        for cmdnode, cmdidx in cmdpath[:-1]:
            s = cmdsort(cmdnode)[cmdidx]
            _clipdraw(scr, helpy, menux, s, regattr, len(s))
            menux += len(s)

        # then the options under the latest node
        for i in range(leftidx, len(cmdkeys)):
            k = cmdkeys[i]
            k = ' '*((maxitemwidth-len(k))//2) + k
            attr = colors[options.color_menu_option]
            if i == curidx:
                attr, attrpre = colors.update(attr, 0, options.color_menu_cursor, 9)
                curx = menux

            _clipdraw(scr, menuy, menux, k, attr, maxitemwidth) # min(width-len(rstatus)-menux, len(k)))
            menux += maxitemwidth
            if menux > width-len(rstatus):
                break

        # display helpstr for cursor command
        curcmd = ''.join(cmdsort(n)[i] for n, i in cmdpath)
        if helpfunc:
            try:
                helpstr = helpfunc(curcmd, sheet)
            except Exception as e:
                helpstr = str(e)
            submenu = curnode[cmdkeys[curidx]]
            if not helpstr and isinstance(submenu, dict):
                helpstr = options.disp_menu_helpsep.join(cmdsort(submenu))
            if helpstr:
                helpx = max(width-len(helpstr)-2, 0)
                _clipdraw(scr, helpy, helpx, helpstr, colors[options.color_menu_help])
        else:
            helpstr = curnode[cmdkeys[curidx]].__doc__

        ch = vdobj.getkeystroke(scr, sheet)
        if not ch: continue
        elif ch in ['ESC', '^C', '^Q']:             raise EscapeException(ch)
        elif ch in ['k', '^A', 'KEY_HOME']:         curlevel[1] = 0
        elif ch in ['h', '^B', 'KEY_LEFT']:         curlevel[1] -= 1
        elif ch in ['j', '^E', 'KEY_END']:          curlevel[1] = len(cmdkeys)-1
        elif ch in ['l', '^F', 'KEY_RIGHT']:        curlevel[1] += 1
        elif ch in ['^I', ENTER, ' ', '-']:         cmdpath.append([curnode[cmdkeys[curidx]], 0]);
        elif ch in ['q', 'KEY_BACKSPACE']:          cmdpath = cmdpath[:-1];
        else:
            pass


def chooseOne(choices):
    'Return one of `choices` elements (if list) or values (if dict).'
    def choiceCompleter(v, i):
        opts = [x for x in choices if x.startswith(v)]
        return opts[i%len(opts)]

    if isinstance(choices, dict):
        return choices[input('/'.join(choices.keys()) + ': ', completer=choiceCompleter)]
    else:
        return input('/'.join(str(x) for x in choices) + ': ', completer=choiceCompleter)


def regex_flags():
    'Return flags to pass to regex functions from options'
    return sum(getattr(re, f.upper()) for f in options.regex_flags)

def moveRegex(sheet, *args, **kwargs):
    list(vd().searchRegex(sheet, *args, moveCursor=True, **kwargs))

def sync(expectedThreads=0):
    vd().sync(expectedThreads)

def async(func):
    'Function decorator, to make calls to `func()` spawn a separate thread if available.'
    def _execAsync(*args, **kwargs):
        return vd().execAsync(func, *args, **kwargs)
    return _execAsync

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

@async
def _async_deepcopy(vs, newlist, oldlist):
    for r in Progress(oldlist):
        newlist.append(deepcopy(r))

def async_deepcopy(vs, rowlist):
    ret = []
    _async_deepcopy(vs, ret, rowlist)
    return ret


class VisiData:
    allPrefixes = 'gz'  # embig'g'en, 'z'mallify

    def __init__(self):
        self.sheets = []  # list of BaseSheet
        self.statuses = []  # statuses shown until next action
        self.lastErrors = []
        self.searchContext = {}
        self.statusHistory = []
        self.lastInputs = collections.defaultdict(collections.OrderedDict)  # [input_type] -> prevInputs
        self.keystrokes = ''
        self.inInput = False
        self.prefixWaiting = False
        self.scr = None  # curses scr
        self.hooks = collections.defaultdict(list)  # [hookname] -> list(hooks)
        self.threads = [] # all long-running threads, including main and finished
        self.addThread(threading.current_thread(), endTime=0)
        self.addHook('rstatus', lambda sheet,self=self: (self.keystrokes, 'white'))
        self.addHook('rstatus', self.rightStatus)

    def status(self, *args):
        'Add status message to be shown until next action.'
        s = '; '.join(str(x) for x in args)
        self.statuses.append(s)
        self.statusHistory.insert(0, args[0] if len(args) == 1 else args)
        return s

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
            status('%s aborted' % t.name)
        except Exception as e:
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
                if not getattr(t, 'status', None):
                    t.status = 'ended'

    def sync(self, expectedThreads=0):
        'Wait for all but expectedThreads async threads to finish.'
        while len(self.unfinishedThreads) > expectedThreads:
            time.sleep(.3)
            self.checkForFinishedThreads()

    def refresh(self):
        Sheet.visibleCols.fget.cache_clear()

    def editText(self, y, x, w, **kwargs):
        'Wrap global editText with `preedit` and `postedit` hooks.'
        v = self.callHook('preedit')
        if not v or v[0] is None:
            with EnableCursor():
                v = editText(self.scr, y, x, w, **kwargs)
        else:
            v = v[0]

        if kwargs.get('display', True):
            self.status('"%s"' % v)
            self.callHook('postedit', v)
        return v

    def input(self, prompt, type='', defaultLast=False, **kwargs):
        'Get user input, with history of `type`, defaulting to last history item if no input and defaultLast is True.'
        if type:
            histlist = list(self.lastInputs[type].keys())
            ret = self._inputLine(prompt, history=histlist, **kwargs)
            if ret:
                self.lastInputs[type][ret] = ret
            elif defaultLast:
                histlist or error("no previous input")
                ret = histlist[-1]
        else:
            ret = self._inputLine(prompt, **kwargs)

        return ret

    def _inputLine(self, prompt, **kwargs):
        'Add prompt to bottom of screen and get line of input from user.'
        scr = self.scr
        if scr:
            scr.addstr(self.windowHeight-1, 0, prompt)
        self.inInput = True
        rstatus, _ = self.rightStatus(self.sheets[0])
        ret = self.editText(self.windowHeight-1, len(prompt), self.windowWidth-len(prompt)-len(rstatus), attr=colors[options.color_edit_cell], unprintablechar=options.disp_unprintable, **kwargs)
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


    # kwargs: regex=None, columns=None, backward=False
    def searchRegex(self, sheet, moveCursor=False, reverse=False, **kwargs):
        'Set row index if moveCursor, otherwise return list of row indexes.'
        def findMatchingColumn(sheet, row, columns, func):
            'Find column for which func matches the displayed value in this row'
            for c in columns:
                if func(c.getDisplayValue(row)):
                    return c

        self.searchContext.update(kwargs)

        regex = kwargs.get("regex")
        if regex:
            self.searchContext["regex"] = re.compile(regex, regex_flags()) or error('invalid regex: %s' % regex)

        regex = self.searchContext.get("regex") or error("no regex")

        columns = self.searchContext.get("columns")
        if columns == "cursorCol":
            columns = [sheet.cursorCol]
        elif columns == "visibleCols":
            columns = tuple(sheet.visibleCols)
        elif isinstance(columns, Column):
            columns = [columns]

        if not columns:
            error('bad columns')

        searchBackward = self.searchContext.get("backward")
        if reverse:
            searchBackward = not searchBackward

        if searchBackward:
            rng = range(sheet.cursorRowIndex-1, -1, -1)
            rng2 = range(sheet.nRows-1, sheet.cursorRowIndex-1, -1)
        else:
            rng = range(sheet.cursorRowIndex+1, sheet.nRows)
            rng2 = range(0, sheet.cursorRowIndex+1)

        matchingRowIndexes = 0

        with Progress(total=sheet.nRows) as prog:
            for r in itertools.chain(rng, rng2):
                prog.addProgress(1)
                c = findMatchingColumn(sheet, sheet.rows[r], columns, regex.search)
                if c:
                    if moveCursor:
                        sheet.cursorRowIndex = r
                        sheet.cursorVisibleColIndex = sheet.visibleCols.index(c)
                        if r in rng2:
                            status('search wrapped')
                        return
                    else:
                        matchingRowIndexes += 1
                        yield r

        status('%s matches for /%s/' % (matchingRowIndexes, regex.pattern))

    def exceptionCaught(self, exc=None, status=True):
        'Maintain list of most recent errors and return most recent one.'
        if isinstance(exc, ExpectedException):  # already reported, don't log
            return
        self.lastErrors.append(stacktrace())
        if status:
            return self.status(self.lastErrors[-1][-1])  # last line of latest error
        if options.debug:
            raise

    def drawLeftStatus(self, scr, vs):
        'Draw left side of status bar.'
        try:
            lstatus = self.leftStatus(vs)
            attr = colors[options.color_status]
            _clipdraw(scr, self.windowHeight-1, 0, lstatus, attr, self.windowWidth)
            return lstatus
        except Exception as e:
            self.exceptionCaught(e)

    def drawRightStatus(self, scr, vs):
        'Draw right side of status bar.'
        rightx = self.windowWidth-1

        ret = ''
        for rstatcolor in self.callHook('rstatus', vs):
            if rstatcolor:
                try:
                    rstatus, color = rstatcolor
                    rstatus = ' '+rstatus
                    rightx -= len(rstatus)
                    attr = colors[color]
                    _clipdraw(scr, self.windowHeight-1, rightx, rstatus, attr, len(rstatus))
                    ret += rstatus
                except Exception as e:
                    self.exceptionCaught(e)

        curses.doupdate()
        return ret

    def leftStatus(self, vs):
        'Compose left side of status bar and add status messages.'
        s = vs.leftStatus()
        maxwidth = options.disp_lstatus_max
        if maxwidth > 0:
            s = middleTruncate(s, maxwidth//2)
        s += options.disp_status_sep.join(self.statuses)
        return s

    def rightStatus(self, sheet):
        'Compose right side of status bar.'
        if sheet.currentThreads:
            status = '%9d  %2d%%' % (len(sheet), sheet.progressPct)
        else:
            status = '%9d %s' % (len(sheet), sheet.rowtype)
        return status, options.color_status

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

                self.statuses = []

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
            elif self.keystrokes in sheet._commands:
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
            try:
                sheet.checkCursor()
            except Exception as e:
                exceptionCaught(e)

    def replace(self, vs):
        'Replace top sheet with the given sheet `vs`.'
        self.sheets.pop(0)
        return self.push(vs)

    def remove(self, vs):
        if vs in self.sheets:
            self.sheets.remove(vs)
        else:
            error('sheet not on stack')

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
            return vs
# end VisiData class

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


class Colorizer:
    def __init__(self, colorizerType, precedence, colorfunc):
        self.type = colorizerType
        self.precedence = precedence
        self.func = colorfunc

class BaseSheet:
    rowtype=''
    def __init__(self, name, **kwargs):
        self.name = name

        # commands specific to this sheet
        sheetcmds = collections.OrderedDict()
        for cls in inspect.getmro(self.__class__)[::-1]:  # reverse of method-resolution-order
            for cmd in getattr(cls, 'commands', []):
                sheetcmds[cmd.name] = cmd
                if cmd.longname:
                    sheetcmds[cmd.longname] = cmd
        self._commands = collections.ChainMap(sheetcmds, baseCommands)

        # for progress bar
        self.progresses = []  # list of Progress objects

        # track all async threads from sheet
        self.currentThreads = []
        self.__dict__.update(kwargs)

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

    def getCommand(self, keystrokes, default=None):
        k = keystrokes
        cmd = None
        while k in self._commands:
            cmd = self._commands.get(k, default)
            k = cmd.execstr  # see if execstr is actually just an alias for another keystroke
        return cmd

    def exec_keystrokes(self, keystrokes, vdglobals=None):  # handle multiple commands concatenated?
        return self.exec_command(self.getCommand(keystrokes), vdglobals, keystrokes=keystrokes)

    def exec_command(self, cmd, args='', vdglobals=None, keystrokes=None):
        "Execute `cmd` tuple with `vdglobals` as globals and this sheet's attributes as locals.  Returns True if user cancelled."
        if not cmd:
            status('no command')
            return True

        escaped = False
        err = ''

        if vdglobals is None:
            vdglobals = getGlobals()

        self.sheet = self

        try:
            self.vd.callHook('preexec', self, cmd.name if options.cmdlog_longname else keystrokes)
            exec(cmd.execstr, vdglobals, LazyMap(self))
        except EscapeException as e:  # user aborted
            self.vd.status('aborted')
            escaped = True
        except Exception as e:
            err = self.vd.exceptionCaught(e)
            escaped = True

        try:
            self.vd.callHook('postexec', self.vd.sheets[0] if self.vd.sheets else None, escaped, err)
        except Exception:
            self.vd.exceptionCaught(e)

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

class Sheet(BaseSheet):
    commands = [
Command(' ', 'cmd=choose(mkmenu(*_commands.maps), cmdhelp, sheet); cmd and exec_command(cmd, keystrokes=cmd.longname)', 'start menu command'),
Command('KEY_LEFT',  'cursorRight(-1)', 'move one column left',  'view-go-left'),
Command('KEY_DOWN',  'cursorDown(+1)',  'move one row down',     'view-go-down'),
Command('KEY_UP',    'cursorDown(-1)',  'move one row up',       'view-go-up'),
Command('KEY_RIGHT', 'cursorRight(+1)', 'move one column right', 'view-go-right'),
Command('KEY_NPAGE', 'cursorDown(nVisibleRows); sheet.topRowIndex += nVisibleRows',  'move one page forward',  'view-go-page-down'),
Command('KEY_PPAGE', 'cursorDown(-nVisibleRows); sheet.topRowIndex -= nVisibleRows', 'move one page backward', 'view-go-page-up'),

Command('gh', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = 0', 'move all the way to the left', 'view-go-far-left'),
Command('KEY_HOME', 'sheet.cursorRowIndex = sheet.topRowIndex = 0', 'move all the way to the top', 'view-go-far-top'),
Command('KEY_END', 'sheet.cursorRowIndex = len(rows); sheet.topRowIndex = cursorRowIndex-nVisibleRows', 'move all the way to the bottom', 'view-go-far-bottom'),
Command('gl', 'sheet.leftVisibleColIndex = len(visibleCols)-1; pageLeft(); sheet.cursorVisibleColIndex = len(visibleCols)-1', 'move all the way to the right', 'view-go-far-right'),

Command('BUTTON1_PRESSED', 'sheet.cursorRowIndex=topRowIndex+mouseY-1', '', 'view-go-mouse-row'),
Command('BUTTON1_RELEASED', 'sheet.topRowIndex=cursorRowIndex-mouseY+1', '', 'view-scroll-mouse-row'),
Command('BUTTON4_PRESSED', 'cursorDown(options.scroll_incr); sheet.topRowIndex += options.scroll_incr', 'move scroll_incr forward', 'view-scroll-up'),
Command('REPORT_MOUSE_POSITION', 'cursorDown(-options.scroll_incr); sheet.topRowIndex -= options.scroll_incr', 'move scroll_incr backward', 'view-scroll-down'),

Command('^G', 'status(statusLine)', 'show cursor position and bounds of current sheet on status line', 'info-sheet'),

Command('<', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorValue: col.getValue(row) != val, reverse=True) or status("no different value up this column")', 'move up the current column to the next value', 'view-go-prev-value'),
Command('>', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorValue: col.getValue(row) != val) or status("no different value down this column")', 'move down the current column to the next value', 'view-go-next-value'),
Command('{', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row), reverse=True) or status("no previous selected row")', 'move up the current column to the previous selected row', 'view-go-prev-selected'),
Command('}', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row)) or status("no next selected row")', 'move down the current column to the next selected row', 'view-go-next-selected'),


Command('_', 'cursorCol.toggleWidth(cursorCol.getMaxWidth(visibleRows))', 'adjust width of current column to full', 'column-width-full'),
Command('z_', 'cursorCol.width = int(input("set width= ", value=cursorCol.width))', 'adjust current column width to given number', 'column-width-input'),

Command('-', 'cursorCol.width = 0', 'hide current column', 'column-hide'),
Command('z-', 'cursorCol.width = cursorCol.width//2', 'reduce width of current column by half', 'column-width-half'),

Command('!', 'toggleKeyColumn(cursorCol)', 'toggle current column as a key column', 'column-key-toggle'),
Command('z!', 'keyCols.remove(cursorCol)', 'unset current column as a key column', 'column-key-unset'),
Command('z~', 'cursorCol.type = anytype', 'set type of current column to anytype', 'column-type-any'),
Command('~', 'cursorCol.type = str', 'set type of current column to str', 'column-type-str'),
Command('@', 'cursorCol.type = date', 'set type of current column to date', 'column-type-date'),
Command('#', 'cursorCol.type = int', 'set type of current column to int', 'column-type-int'),
Command('$', 'cursorCol.type = currency', 'set type of current column to currency', 'column-type-currency'),
Command('%', 'cursorCol.type = float', 'set type of current column to float', 'column-type-float'),
Command('^', 'cursorCol.name = editCell(cursorVisibleColIndex, -1)', 'edit name of current column', 'column-name-input'),

Command('g_', 'for c in visibleCols: c.width = c.getMaxWidth(visibleRows)', 'adjust width of all visible columns to full', 'column-width-all-full'),

Command('[', 'orderBy(cursorCol)', 'sort ascending by current column', 'rows-sort-asc'),
Command(']', 'orderBy(cursorCol, reverse=True)', 'sort descending by current column', 'rows-sort-desc'),
Command('g[', 'orderBy(*keyCols)', 'sort ascending by all key columns', 'rows-sort-keys-asc'),
Command('g]', 'orderBy(*keyCols, reverse=True)', 'sort descending by all key columns', 'rows-sort-keys-desc'),

Command('z^E', 'vd.push(TextSheet("cell_error", getattr(cursorCell, "error", None) or error("no error this cell")))', 'view traceback for error in current cell'),


Command('^R', 'reload(); recalc(); status("reloaded")', 'reload current sheet'),
Command('z^R', 'cursorCol._cachedValues.clear()', 'clear cache for current column'),

Command('/', 'moveRegex(sheet, regex=input("/", type="regex", defaultLast=True), columns="cursorCol", backward=False)', 'search for regex forwards in current column', 'view-find-row-curcol-forward'),
Command('?', 'moveRegex(sheet, regex=input("?", type="regex", defaultLast=True), columns="cursorCol", backward=True)', 'search for regex backwards in current column', 'view-find-row-curcol-backward'),
Command('n', 'moveRegex(sheet, reverse=False)', 'move to next match from last search', 'view-find-forward-repeat'),
Command('N', 'moveRegex(sheet, reverse=True)', 'move to previous match from last search', 'view-find-backward-repeat'),

Command('g/', 'moveRegex(sheet, regex=input("g/", type="regex", defaultLast=True), backward=False, columns="visibleCols")', 'search for regex forwards over all visible columns', 'view-find-row-viscol-forward'),
Command('g?', 'moveRegex(sheet, regex=input("g?", type="regex", defaultLast=True), backward=True, columns="visibleCols")', 'search for regex backwards over all visible columns', 'view-find-row-viscol-backward'),

Command('e', 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex)); sheet.exec_keystrokes(options.cmd_after_edit)', 'edit contents of current cell', 'modify-edit-cell'),
Command('ge', 'cursorCol.setValues(selectedRows or rows, input("set selected to: ", value=cursorValue))', 'set contents of current column for selected rows to same input', 'modify-edit-column-selected'),
Command('zd', 'cursorCol.setValues([cursorRow], None)', 'set contents of current cell to None', 'modify-clear-cell'),
Command('gzd', 'cursorCol.setValues(selectedRows, None)', 'set contents of cells in current column to None for selected rows', 'modify-clear-column-selected'),
Command('KEY_DC', 'zd'),
Command('gKEY_DC', 'gzd'),

Command('t', 'toggle([cursorRow]); cursorDown(1)', 'toggle selection of current row', 'rows-toggle-current'),
Command('s', 'select([cursorRow]); cursorDown(1)', 'select current row', 'rows-select-current'),
Command('u', 'unselect([cursorRow]); cursorDown(1)', 'unselect current row', 'rows-unselect-current'),

Command('|', 'selectByIdx(vd.searchRegex(sheet, regex=input("|", type="regex", defaultLast=True), columns="cursorCol"))', 'select rows matching regex in current column', 'rows-select-regex'),
Command('\\', 'unselectByIdx(vd.searchRegex(sheet, regex=input("\\\\", type="regex", defaultLast=True), columns="cursorCol"))', 'unselect rows matching regex in current column', 'rows-unselect-regex'),

Command('gt', 'toggle(rows)', 'toggle selection of all rows', 'rows-toggle-all'),
Command('gs', 'select(rows)', 'select all rows', 'rows-select-all'),
Command('gu', '_selectedRows.clear()', 'unselect all rows', 'rows-unselect-all'),

Command('g|', 'selectByIdx(vd.searchRegex(sheet, regex=input("g|", type="regex", defaultLast=True), columns="visibleCols"))', 'select rows matching regex in any visible column', 'rows-select-regex-all'),
Command('g\\', 'unselectByIdx(vd.searchRegex(sheet, regex=input("g\\\\", type="regex", defaultLast=True), columns="visibleCols"))', 'unselect rows matching regex in any visible column', 'rows-unselect-regex-all'),

Command(',', 'select(gatherBy(lambda r,c=cursorCol,v=cursorValue: c.getValue(r) == v), progress=False)', 'select rows matching current cell in current column', 'rows-select-like-cell'),
Command('g,', 'select(gatherBy(lambda r,v=cursorRow: r == v), progress=False)', 'select rows matching current row in all visible columns', 'rows-select-like-row'),

Command('"', 'vs = copy(sheet); vs.name += "_selectedref"; vs.rows = list(selectedRows or rows); vs.select(selectedRows); vd.push(vs)', 'open duplicate sheet with only selected rows', 'sheet-duplicate-selected'),
Command('g"', 'vs = copy(sheet); vs.name += "_copy"; vs.rows = list(rows); vs.select(selectedRows); vd.push(vs)', 'open duplicate sheet with all rows', 'sheet-duplicate-all'),
Command('gz"', 'vs = deepcopy(sheet); vs.name += "_selectedcopy"; vs.rows = async_deepcopy(vs, selectedRows or rows); vd.push(vs); status("pushed sheet with async deepcopy of all rows")', 'open duplicate sheet with deepcopy of selected rows', 'sheet-duplicate-deepcopy'),

Command('=', 'addColumn(ColumnExpr(inputExpr("new column expr=")), index=cursorColIndex+1)', 'create new column from Python expression, with column names as variables', 'modify-add-column-expr'),
Command('g=', 'cursorCol.setValuesFromExpr(selectedRows or rows, inputExpr("set selected="))', 'set current column for selected rows to result of Python expression', 'modify-set-column-selected-expr'),

Command('V', 'vd.push(TextSheet("%s[%s].%s" % (name, cursorRowIndex, cursorCol.name), cursorDisplay.splitlines()))', 'view contents of current cell in a new sheet', 'sheet-open-cell'),

Command('C', 'vd.push(ColumnsSheet(sheet.name+"_columns", source=sheet))', 'open Columns Sheet', 'meta-columns-sheet'),
Command('gC', 'vd.push(ColumnsSheet("all_columns", source=vd.sheets))', 'open Columns Sheet with all columns from all sheets', 'meta-columns-all'),
Command('delete-column-really', 'columns.pop(cursorColIndex)', 'remove column permanently from the list of columns'),
    ]
    columns = []  # list of Column
#    commands = []  # list of Command
    colorizers = [ # list of Colorizer
        Colorizer('hdr', 0, lambda s,c,r,v: options.color_default_hdr),
        Colorizer('hdr', 9, lambda s,c,r,v: options.color_current_hdr if c is s.cursorCol else None),
        Colorizer('hdr', 8, lambda s,c,r,v: options.color_key_col if c in s.keyCols else None),
        Colorizer('col', 5, lambda s,c,r,v: options.color_current_col if c is s.cursorCol else None),
        Colorizer('col', 7, lambda s,c,r,v: options.color_key_col if c in s.keyCols else None),
        Colorizer('cell', 2, lambda s,c,r,v: options.color_default),
        Colorizer('row', 8, lambda s,c,r,v: options.color_selected_row if s.isSelected(r) else None),
    ]
    nKeys = 0  # initial keyCols = columns[:nKeys]
    rowtype = 'rows'

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
        self.recalc()

        self.keyCols = self.columns[:self.nKeys]  # initial list of key columns

        self._selectedRows = {}  # id(row) -> row

        self._colorizers = {'row': [], 'col': [], 'hdr': [], 'cell': []}

        for b in [self] + list(self.__class__.__bases__):
            for c in getattr(b, 'colorizers', []):
                self.addColorizer(c)

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
        self._colorizers[c.type].append(c)

    def colorizeRow(self, row):
        return self.colorize(['row'], None, row)

    def colorizeColumn(self, col):
        return self.colorize(['col'], col, None)

    def colorizeHdr(self, col):
        return self.colorize(['hdr'], col, None)

    def colorizeCell(self, col, row, value):
        return self.colorize(['col', 'row', 'cell'], col, row, value)

    def colorize(self, colorizerTypes, col, row, value=None):
        'Returns curses attribute for the given col/row/value'
        attr = 0
        attrpre = 0

        for colorizerType in colorizerTypes:
            for colorizer in sorted(self._colorizers[colorizerType], key=lambda x: x.precedence):
                color = colorizer.func(self, col, row, value)
                if color:
                    attr, attrpre = colors.update(attr, attrpre, color, colorizer.precedence)

        return attr

    def newRow(self):
        return list((None for c in self.columns))

    def addRow(self, row, index=None):
        if index is None:
            self.rows.append(row)
        else:
            self.rows.insert(index, row)
        return row

    def searchColumnNameRegex(self, colregex, moveCursor=False):
        'Select visible column matching `colregex`, if found.'
        for i, c in enumPivot(self.visibleCols, self.cursorVisibleColIndex):
            if re.search(colregex, c.name, regex_flags()):
                if moveCursor:
                    self.cursorVisibleColIndex = i
                return c

    def recalc(self):
        'Clear caches and set col.sheet to this sheet for all columns.'
        for c in self.columns:
            if c._cachedValues:
                c._cachedValues.clear()
            c.sheet = self
            c.name = c._name

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
        ret.columns = deepcopy(self.columns) # deepcopy columns even for shallow copy of sheet
        ret.keyCols = [ret.columns[i] for i, c in enumerate(self.columns) if c in self.keyCols]
        ret.recalc()  # set .sheet on columns
        ret._selectedRows = {}
        ret.topRowIndex = ret.cursorRowIndex = 0
        ret.progresses = []
        ret.currentThreads = []
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

        status('deleted %s rows' % ndeleted)
        return ndeleted

    @async
    def deleteSelected(self):
        'Delete all selected rows.'
        ndeleted = self.deleteBy(self.isSelected)
        nselected = len(self._selectedRows)
        self._selectedRows.clear()
        if ndeleted != nselected:
            error('expected %s' % nselected)

    @async
    def delete(self, rows):
        rowdict = {id(r): r for r in rows}
        ndeleted = self.deleteBy(lambda r,rowdict=rowdict: id(r) in rowdict)
        nrows = len(rows)
        if ndeleted != nrows:
            error('expected %s' % nrows)

    def __repr__(self):
        return self.name

    def evalexpr(self, expr, row):
        return eval(expr, getGlobals(), LazyMapRow(self, row))

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
    @functools.lru_cache()
    def visibleCols(self):  # non-hidden cols
        'List of `Column` which are not hidden.'
        return [c for c in self.keyCols if not c.hidden] + [c for c in self.columns if not c.hidden and c not in self.keyCols]

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

    @async
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

    @async
    def select(self, rows, status=True, progress=True):
        "Select given rows. Don't show progress if progress=False; don't show status if status=False."
        before = len(self._selectedRows)
        for r in (Progress(rows) if progress else rows):
            self.selectRow(r)
        if status:
            vd().status('selected %s%s rows' % (len(self._selectedRows)-before, ' more' if before > 0 else ''))

    @async
    def unselect(self, rows, status=True, progress=True):
        "Unselect given rows. Don't show progress if progress=False; don't show status if status=False."
        before = len(self._selectedRows)
        for r in (Progress(rows) if progress else rows):
            self.unselectRow(r)
        if status:
            vd().status('unselected %s/%s rows' % (before-len(self._selectedRows), before))

    def selectByIdx(self, rowIdxs):
        'Select given row indexes, without progress bar.'
        self.select((self.rows[i] for i in rowIdxs), progress=False)

    def unselectByIdx(self, rowIdxs):
        'Unselect given row indexes, without progress bar.'
        self.unselect((self.rows[i] for i in rowIdxs), progress=False)

    def gatherBy(self, func):
        'Generate only rows for which the given func returns True.'
        for r in Progress(self.rows):
            try:
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

    def moveVisibleCol(self, fromVisColIdx, toVisColIdx):
        'Move column to another position in sheet.'
        fromColIdx = self.columns.index(self.visibleCols[fromVisColIdx])
        toColIdx = self.columns.index(self.visibleCols[toVisColIdx])
        moveListItem(self.columns, fromColIdx, toColIdx)
        return toVisColIdx

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

    def toggleKeyColumn(self, col):
        'Toggle col as key column.'
        if col not in self.keyCols: # if not a key, add it
            self.keyCols.append(col)
            return 1
        else:
            self.keyCols.remove(col)
            return 0

    def rowkey(self, row):
        'returns a tuple of the key for the given row'
        return tuple(c.getValue(row) for c in self.keyCols)

    def moveToNextRow(self, func, reverse=False):
        'Move cursor to next (prev if reverse) row for which func returns True.  Returns False if no row meets the criteria.'
        rng = range(self.cursorRowIndex-1, -1, -1) if reverse else range(self.cursorRowIndex+1, self.nRows)

        for i in rng:
            try:
                if func(self.rows[i]):
                    self.cursorRowIndex = i
                    return True
            except Exception:
                pass

        return False

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
                if self.cursorVisibleColIndex < min(self.visibleColLayout.keys()):
                    self.leftVisibleColIndex -= 1
                    continue
                elif self.cursorVisibleColIndex > max(self.visibleColLayout.keys()):
                    self.leftVisibleColIndex += 1
                    continue

                cur_x, cur_w = self.visibleColLayout[self.cursorVisibleColIndex]
                if cur_x+cur_w < self.vd.windowWidth:  # current columns fit entirely on screen
                    break
                self.leftVisibleColIndex += 1

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
        sepattr = colors[options.color_column_sep]
        hdrattr = self.colorizeHdr(col)

        C = options.disp_column_sep
        if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
            C = options.disp_keycol_sep

        x, colwidth = self.visibleColLayout[vcolidx]

        # ANameTC
        T = typemap.get(col.type, '?')
        N = ' ' + col.name  # save room at front for LeftMore
        if len(N) > colwidth-1:
            N = N[:colwidth-len(options.disp_truncator)] + options.disp_truncator
        _clipdraw(scr, y, x, N, hdrattr, colwidth)
        _clipdraw(scr, y, x+colwidth-len(T), T, hdrattr, len(T))

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

        self.rowLayout = {}
        self.calcColLayout()
        vcolidx = 0
        for vcolidx, colinfo in sorted(self.visibleColLayout.items()):
            x, colwidth = colinfo
            col = self.visibleCols[vcolidx]

            if x < self.vd.windowWidth:  # only draw inside window
                headerRow = 0
                self.drawColHeader(scr, headerRow, vcolidx)

                y = headerRow + numHeaderRows
                rows = self.rows[self.topRowIndex:self.topRowIndex+self.nVisibleRows]
                for rowidx in range(0, self.nVisibleRows):
                    dispRowIdx = self.topRowIndex + rowidx
                    if dispRowIdx >= self.nRows:
                        break

                    self.rowLayout[dispRowIdx] = y

                    row = rows[rowidx]
                    cellval = col.getCell(row, colwidth-1)

                    attr = self.colorizeCell(col, row, cellval)
                    attrpre = 0
                    sepattr = self.colorizeRow(row)

                    # must apply current row here, because this colorization requires cursorRowIndex
                    if dispRowIdx == self.cursorRowIndex:
                        attr, attrpre = colors.update(attr, 0, options.color_current_row, 10)
                        sepattr, _ = colors.update(sepattr, 0, options.color_current_row, 10)

                    sepattr = sepattr or colors[options.color_column_sep]

                    note = getattr(cellval, 'note', None)
                    if note:
                        noteattr, _ = colors.update(attr, attrpre, cellval.notecolor, 8)
                        _clipdraw(scr, y, x+colwidth-len(note), note, noteattr, len(note))

                    _clipdraw(scr, y, x, disp_column_fill+cellval.display, attr, colwidth-(1 if note else 0))

                    sepchars = options.disp_column_sep
                    if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
                        sepchars = options.disp_keycol_sep

                    if x+colwidth+len(sepchars) <= self.vd.windowWidth:
                       scr.addstr(y, x+colwidth, sepchars, sepattr)

                    y += 1

        if vcolidx+1 < self.nVisibleCols:
            scr.addstr(headerRow, self.vd.windowWidth-2, options.disp_more_right, colors[options.color_column_sep])


    def editCell(self, vcolidx=None, rowidx=None):
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
            currentValue = col.getValue(self.rows[self.cursorRowIndex])

        r = self.vd.editText(y, x, w, value=currentValue, fillchar=options.disp_edit_fill, truncchar=options.disp_truncator)
        if rowidx >= 0:
            r = col.type(r)  # convert input to column type

        return r


def isNullFunc():
    'Returns isNull function according to current options.'
    nullset = []
    if options.none_is_null:  nullset.append(None)
    if options.empty_is_null: nullset.append('')
    if options.false_is_null: nullset.append(False)
    if options.zero_is_null:  nullset.append(0)
    return lambda v,nullset=nullset: v in nullset


class Column:
    def __init__(self, name, type=anytype, cache=False, **kwargs):
        self.sheet = None     # owning Sheet, set in Sheet.addColumn
        self.name = name      # display visible name
        self.fmtstr = ''      # by default, use str()
        self.type = type      # anytype/str/int/float/date/func
        self.getter = lambda col, row: row
        self.setter = None    # setter(col,row,value)
        self.width = None     # == 0 if hidden, None if auto-compute next time

        self._cachedValues = collections.OrderedDict() if cache else None
        for k, v in kwargs.items():
            setattr(self, k, v)  # instead of __dict__.update(kwargs) to invoke property.setters

    def __copy__(self):
        cls = self.__class__
        ret = cls.__new__(cls)
        ret.__dict__.update(self.__dict__)
        if ret._cachedValues:
            ret._cachedValues = collections.OrderedDict()  # a fresh cache
        return ret

    def __deepcopy__(self, memo):
        return self.__copy__()  # no separate deepcopy

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
        if self._fmtstr:
            return self._fmtstr

        t = self.type
        if t is int:      return '{:d}'
        elif t is float:    return '{:.02f}'
        elif t is currency: return '{:,.02f}'

    @fmtstr.setter
    def fmtstr(self, v):
        self._fmtstr = v

    def format(self, cellval):
        'Return displayable string of `cellval` according to our `Column.type` and `Column.fmtstr`'
        if cellval is None:
            return None

        # complex objects can be arbitrarily large (like sheet.rows)
        #  this shortcut must be before self.type(cellval) (anytype will completely stringify)
        if isinstance(cellval, list):
            return '[%s]' % len(cellval)
        if isinstance(cellval, dict):
            return '{%s}' % len(cellval)

        t = self.type
        typedval = t(cellval)
        if t is date:         return typedval.to_string(self.fmtstr)
        elif self.fmtstr:     return self.fmtstr.format(typedval)
        else:                 return str(typedval)

    @property
    def hidden(self):
        'A column is hidden if its width == 0.'
        return self.width == 0

    def getValueRows(self, rows):
        'Generate (val, row) for the given `rows` at this Column, excluding errors and nulls.'
        f = isNullFunc()

        for r in rows:
            try:
                v = self.type(self.getValue(r))
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
        return self.type(self.getValue(row))

    def getTypedValueNoExceptions(self, row):
        '''Returns the properly-typed value for the given row at this column.
           Returns the type's default value if either the getter or the type conversion fails.'''
        try:
            return self.type(self.getValue(row))
        except Exception as e:
#            exceptionCaught(e, status=False)
            return self.type()

    def getValue(self, row):
        'Memoize calcValue with key id(row)'
        if self._cachedValues is None:
            return self.calcValue(row)

        k = id(row)
        if k in self._cachedValues:
            return self._cachedValues[k]

        ret = self.calcValue(row)
        self._cachedValues[k] = ret

        if len(self._cachedValues) > 256:  # max number of entries
            self._cachedValues.popitem(last=False)

        return ret

    def getCell(self, row, width=None):
        'Return DisplayWrapper for displayable cell value.'
        try:
            cellval = self.getValue(row)
        except Exception as e:
            return DisplayWrapper(None, error=stacktrace(),
                                display=options.disp_error_val,
                                note=options.note_getter_exc,
                                notecolor=options.color_getter_exc)

        if isinstance(cellval, threading.Thread):
            return DisplayWrapper(None,
                                display=options.disp_pending,
                                note=options.note_pending,
                                notecolor=options.color_note_pending)

        if isinstance(cellval, bytes):
            cellval = cellval.decode(options.encoding, options.encoding_errors)

        dw = DisplayWrapper(cellval)

        try:
            dispval = self.format(cellval)
            if dispval is None:
                dw.display = ''
                dw.note = options.disp_note_none
                dw.notecolor = options.color_note_type
                return dw

            if width and self.type in (int, float, currency, len):
                dispval = dispval.rjust(width-1)

            dw.display = dispval

            # annotate cells with raw value type in anytype columns
            if self.type is anytype and options.color_note_type:
                dw.note = typemap.get(type(cellval), None)
                dw.notecolor = options.color_note_type

        except Exception as e:  # type conversion or formatting failed
            dw.error = stacktrace()
            dw.display = str(cellval)
            dw.note = options.note_format_exc
            dw.notecolor = options.color_format_exc

        return dw

    def getDisplayValue(self, row):
        return self.getCell(row).display

    def setValue(self, row, value):
        'Set our column value for given row to `value`.'
        self.setter or error(self.name+' column cannot be changed')
        self.setter(self, row, value)

    def setValues(self, rows, value):
        'Set our column value for given list of rows to `value`.'
        value = self.type(value)
        for r in rows:
            self.setValue(r, value)
        status('set %d values = %s' % (len(rows), value))

    @async
    def setValuesFromExpr(self, rows, expr):
        compiledExpr = compile(expr, '<expr>', 'eval')
        for row in Progress(rows):
            self.setValue(row, self.sheet.evalexpr(compiledExpr, row))
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

def ColumnAttr(name, attr=None, **kwargs):
    'Column using getattr/setattr of given attr.'
    if attr is None:
        attr = name
    return Column(name,
            getter=lambda col,row,attr=attr: getattr(row, attr, None),
            setter=lambda col,row,val,attr=attr: setattr(row, attr, val),
            **kwargs)

def ColumnItem(name, key=None, **kwargs):
    'Column using getitem/setitem of given key.'
    if key is None:
        key = name
    return Column(name,
            getter=lambda col,row,key=key: row[key],
            setter=lambda col,row,val,key=key: setitem(row, key, val),
            **kwargs)

def ArrayNamedColumns(columns):
    'Return list of ColumnItems from given list of column names.'
    return [ColumnItem(colname, i) for i, colname in enumerate(columns)]

def ArrayColumns(ncols):
    'Return list of ColumnItems for given row length.'
    return [ColumnItem('', i, width=8) for i in range(ncols)]


class SubrowColumn(Column):
    def __init__(self, origcol, subrowidx, **kwargs):
        super().__init__(origcol.name, type=origcol.type, width=origcol.width, **kwargs)
        self.origcol = origcol
        self.subrowidx = subrowidx

    def getValue(self, row):
        subrow = row[self.subrowidx]
        if subrow is not None:
            return self.origcol.getValue(subrow)

    def setValue(self, row, value):
        subrow = row[self.subrowidx]
        if subrow is not None:
           self.origcol.setValue(subrow, value)


class DisplayWrapper:
    def __init__(self, value, **kwargs):
        self.value = value
        self.__dict__.update(kwargs)


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
        self.compiledExpr = compile(expr, '<expr>', 'eval')

###

def confirm(prompt):
    yn = input(prompt, value='n')[:1]
    if not yn or yn not in 'Yy':
        error('disconfirmed')

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
            ret += options.disp_oddspace
            w += len(options.disp_oddspace)
        else:
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
    commands = [
        Command('v', 'sheet.wrap = not getattr(sheet, "wrap", options.wrap); status("text%s wrapped" % ("" if wrap else " NOT")); reload()', 'toggle text wrap for this sheet')
    ]
    filetype = 'txt'

    def __init__(self, name, source, **kwargs):
        super().__init__(name, source=source, **kwargs)

    @async
    def reload(self):
        self.columns = [Column(self.name, getter=lambda col,row: row[1])]
        self.rows = []
        winWidth = vd().windowWidth
        for text in self.source:
            if getattr(self, 'wrap', options.wrap):
                startingLine = len(self.rows)
                for i, L in enumerate(textwrap.wrap(str(text), width=winWidth-2)):
                    self.addRow((startingLine+i, L))
            else:
                self.addRow((len(self.rows), text))

class ColumnsSheet(Sheet):
    rowtype = 'columns'
    class ValueColumn(Column):
        'passthrough to the value on the source cursorRow'
        def calcValue(self, srcCol):
            return srcCol.getDisplayValue(srcCol.sheet.cursorRow)
        def setValue(self, srcCol, val):
            srcCol.setValue(self.sheet.source.cursorRow, val)

    columns = [
            ColumnAttr('sheet'),
            ColumnAttr('name', width=options.default_width),
            ColumnAttr('width', type=int),
            ColumnEnum('type', globals(), default=anytype),
            ColumnAttr('fmtstr'),
            ValueColumn('value', width=options.default_width)
    ]
    nKeys = 2
    colorizers = [
            Colorizer('row', 7, lambda self,c,r,v: options.color_key_col if r in r.sheet.keyCols else None),
    ]
    commands = []

    def reload(self):
        if isinstance(self.source, Sheet):
            self.rows = self.source.columns
            self.cursorRowIndex = self.source.cursorColIndex
            self.columns[0].width = 0  # hide 'sheet' column if only one sheet
        elif isinstance(self.source, list):  # lists of Columns
            self.rows = []
            for src in self.source:
                if src is not self:
                    self.rows.extend(src.columns)

class SheetsSheet(Sheet):
    rowtype = 'sheets'
    commands = [Command(ENTER, 'jumpTo(cursorRowIndex)', 'jump to sheet referenced in current row')]
    columns = [
        ColumnAttr('name'),
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
        ColumnAttr('nVisibleCols', type=int),
        ColumnAttr('cursorDisplay'),
        ColumnAttr('keyColNames'),
        ColumnAttr('source'),
    ]

    def reload(self):
        self.rows = vd().sheets

    def jumpTo(self, sheetnum):
        if sheetnum != 0:
            moveListItem(self.rows, sheetnum, 0)
            self.rows.pop(1)


class HelpSheet(Sheet):
    'Show all commands available to the source sheet.'
    rowtype = 'commands'

    class HelpColumn(Column):
        def calcValue(self, r):
            cmd = self.sheet.source.getCommand(self.prefix+r.name, None)
            return cmd.helpstr if cmd else '-'

    columns = [
        ColumnAttr('keystrokes', 'name'),
        ColumnAttr('helpstr'),
        HelpColumn('with_g_prefix', prefix='g'),
        HelpColumn('with_z_prefix', prefix='z'),
        ColumnAttr('execstr', width=0),
    ]
    nKeys = 1
    def reload(self):
        self.rows = []
        for src in self.source._commands.maps:
            self.rows.extend(src.values())


class OptionsSheet(Sheet):
    rowtype = 'options'
    commands = [
        Command(ENTER, 'editOption(cursorRow)', 'edit option'),
        Command('e', ENTER)
    ]
    columns = [ColumnItem('option', 0),
               Column('value', getter=lambda col,row: row[1], setter=lambda col,row,val: setattr(options, row[0], val)),
               ColumnItem('default', 2),
               ColumnItem('description', 3)]
    colorizers = []
    nKeys = 1

    def editOption(self, row):
        if isinstance(row[2], bool):
            self.source[row[0]] = not row[1]
        else:
            self.source[row[0]] = self.editCell(1)

    def reload(self):
        self.rows = list(self.source._opts.values())

vd().optionsSheet = OptionsSheet('options', source=options)

### Curses helpers

def clipdraw(scr, y, x, s, attr, w=None):
    'Draw string `s` at (y,x)-(y,x+w), clipping with ellipsis char.'
    _, windowWidth = scr.getmaxyx()
    dispw = 0
    try:
        if w is None:
            w = windowWidth-1
        w = min(w, windowWidth-x-1)
        if w == 0:  # no room anyway
            return

        # convert to string just before drawing
        s, dispw = clipstr(str(s), w)
        scr.addstr(y, x, disp_column_fill*w, attr)
        scr.addstr(y, x, s, attr)
    except Exception as e:
#        raise type(e)('%s [clip_draw y=%s x=%s dispw=%s w=%s]' % (e, y, x, dispw, w)
#                ).with_traceback(sys.exc_info()[2])
        pass

_clipdraw = clipdraw

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

def launchExternalEditor(v, linenum=0):
    editor = os.environ.get('EDITOR') or error('$EDITOR not set')

    import tempfile
    fd, fqpn = tempfile.mkstemp(text=True)
    with open(fd, 'w') as fp:
        fp.write(v)

    with SuspendCurses():
        cmd = '%s %s' % (editor, fqpn)
        if linenum:
            cmd += ' +%s' % linenum
        os.system(cmd)

    with open(fqpn, 'r') as fp:
        return fp.read()

def suspend():
    import signal
    with SuspendCurses():
        os.kill(os.getpid(), signal.SIGSTOP)

# history: earliest entry first
def editText(scr, y, x, w, attr=curses.A_NORMAL, value='', fillchar=' ', truncchar='-', unprintablechar='.', completer=lambda text,idx: None, history=[], display=True):
    'A better curses line editing widget.'
    ESC='^['
    ENTER='^J'

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
    i = 0           # index into v
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
            dispval += fillchar*(w-len(dispval))
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

        scr.addstr(y, x, dispval, attr)
        scr.move(y, x+dispi)
        ch = vd().getkeystroke(scr)
        if ch == '':                               continue
        elif ch == 'KEY_IC':                       insert_mode = not insert_mode
        elif ch == '^A' or ch == 'KEY_HOME':       i = 0
        elif ch == '^B' or ch == 'KEY_LEFT':       i -= 1
        elif ch == '^C' or ch == ESC:              raise EscapeException(ch)
        elif ch == '^D' or ch == 'KEY_DC':         v = delchar(v, i)
        elif ch == '^E' or ch == 'KEY_END':        i = len(v)
        elif ch == '^F' or ch == 'KEY_RIGHT':      i += 1
        elif ch in ('^H', 'KEY_BACKSPACE', '^?'):  i -= 1; v = delchar(v, i)
        elif ch == '^I':                           v, i = complete_state.complete(v, i, +1)
        elif ch == 'KEY_BTAB':                     v, i = complete_state.complete(v, i, -1)
        elif ch == ENTER:                          break
        elif ch == '^K':                           v = v[:i]  # ^Kill to end-of-line
        elif ch == '^O':                           v = launchExternalEditor(v)
        elif ch == '^R':                           v = str(value)  # ^Reload initial value
        elif ch == '^T':                           v = delchar(splice(v, i-2, v[i-1]), i)  # swap chars
        elif ch == '^U':                           v = v[i:]; i = 0  # clear to beginning
        elif ch == '^V':                           v = splice(v, i, until_get_wch()); i += 1  # literal character
        elif ch == '^W':                           j = rfind_nonword(v, 0, i-1); v = v[:j+1] + v[i:]; i = j+1
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
        color, prec = self.update(0, 0, colornamestr, 10)
        return color

    def update(self, attr, attr_prec, colornamestr, newcolor_prec):
        attr = attr or 0
        if isinstance(colornamestr, str):
            for colorname in colornamestr.split(' '):
                if colorname in self.color_attrs:
                    if newcolor_prec > attr_prec:
                        attr &= ~2047
                        attr |= self.color_attrs[colorname.lower()]
                        attr_prec = newcolor_prec
                elif colorname in self.attrs:
                    attr |= self.attrs[colorname.lower()]
        return attr, attr_prec


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

    status('<F1> or z? opens help')
    return vd().run(_scr)

def addGlobals(g):
    'importers can call `addGlobals(globals())` to have their globals accessible to execstrings'
    globals().update(g)

def getGlobals():
    return globals()

if __name__ == '__main__':
    run(*(TextSheet('contents', open(src)) for src in sys.argv[1:]))
