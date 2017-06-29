#!/usr/bin/env python3
#
# Copyright 2017 Saul Pwanson
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

'VisiData core functionality'

__version__ = 'saul.pw/VisiData v0.91'
__author__ = 'Saul Pwanson <vd@saul.pw>'
__license__ = 'MIT'
__status__ = 'Alpha'

from builtins import *
import sys
import os
import os.path
import copy
import collections
import functools
import itertools
import string
import re
import time
import curses
import datetime
import io
import random
import textwrap

class EscapeException(Exception):
    pass

baseCommands = collections.OrderedDict()
baseOptions = collections.OrderedDict()

def command(keystrokes, execstr, helpstr):
    if isinstance(keystrokes, str):
        keystrokes = [keystrokes]

    for ks in keystrokes:
        baseCommands[ks] = (ks, helpstr, execstr)

def option(name, default, helpstr=''):
    baseOptions[name] = [name, default, default, helpstr, type(default)]  # see OptionsObject
theme = option


option('debug', False, 'abort on error and display stacktrace')
option('readonly', False, 'disable saving')
option('filetype', '', 'specify file type')

option('headerlines', 1, 'parse first N rows of .csv/.tsv as column names')
option('encoding', 'utf-8', 'as passed to codecs.open')
option('encoding_errors', 'surrogateescape', 'as passed to codecs.open')

option('field_joiner', ' ', 'character used to join string fields')
option('sheetname_joiner', '~', 'string joining multiple sheet names')
option('curses_timeout', '100', 'curses timeout in ms')

option('default_width', 20, 'default column width')
option('regex_flags', 'I', 'flags to pass to re.compile() [AILMSUX]')
option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
option('num_colors', 0, 'force number of colors to use')
option('maxlen_col_hdr', 2, 'maximum length of column-header strings')

theme('disp_truncator', '…')
theme('disp_key_sep', '/')
theme('disp_format_exc', '?')
theme('disp_getter_exc', '!')
theme('disp_edit_fill', '_', 'edit field fill character')
theme('disp_more_left', '<', 'display cue in header indicating more columns to the left')
theme('disp_more_right', '>', 'display cue in header indicating more columns to the right')
theme('disp_column_sep', '|', 'chars between columns')
theme('disp_keycol_sep', '\u2016', 'chars between keys and rest of columns')

theme('disp_error_val', '¿', 'displayed contents when getter fails due to exception')
theme('disp_none', '',  'visible contents of a cell whose value was None')

theme('color_current_row', 'reverse')
theme('color_default', 'normal')
theme('color_selected_row', '215 yellow')
theme('color_format_exc', '48 bold yellow')
theme('color_getter_exc', 'red bold')
theme('color_current_col', 'bold')
theme('color_current_hdr', 'reverse underline')
theme('color_key_col', '81 cyan')
theme('color_default_hdr', 'bold underline')
theme('color_column_sep', '246 blue')
theme('disp_status_sep', ' | ', 'string separating multiple statuses')
theme('disp_unprintable', '.', 'a substitute character for unprintables')
theme('disp_column_fill', ' ', 'pad chars after column value')
theme('disp_oddspace', '\u00b7', 'displayable character for odd whitespace')
theme('color_status', 'bold', 'status line color')
theme('color_edit_cell', 'normal', 'edit cell color')
theme('disp_status_fmt', '{sheet.name}| ', 'status line prefix')
theme('unicode_ambiguous_width', 1, 'width to use for unicode chars marked ambiguous')

ENTER='^J'
ESC='^['

command('q',  'vd.sheets.pop(0)', 'quit the current sheet')

command(['h', 'KEY_LEFT'],  'cursorRight(-1)', 'go one column left')
command(['j', 'KEY_DOWN'],  'cursorDown(+1)', 'go one row down')
command(['k', 'KEY_UP'],    'cursorDown(-1)', 'go one row up')
command(['l', 'KEY_RIGHT'], 'cursorRight(+1)', 'go one column right')
command(['^F', 'KEY_NPAGE', 'kDOWN'], 'cursorDown(nVisibleRows); sheet.topRowIndex += nVisibleRows', 'scroll one page down')
command(['^B', 'KEY_PPAGE', 'kUP'], 'cursorDown(-nVisibleRows); sheet.topRowIndex -= nVisibleRows', 'scroll one page up')

command(['KEY_HOME', 'gg'],  'sheet.topRowIndex = sheet.cursorRowIndex = 0', 'go to top row')
command(['KEY_END', 'G'],   'sheet.cursorRowIndex = len(rows)-1', 'go to last row')

command('gq', 'vd.sheets.clear()', 'drop all sheets (clean exit)')

command('gh', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = nKeys', 'go to leftmost non-key column')
command('gk', 'sheet.cursorRowIndex = sheet.topRowIndex = 0', 'go to top row')
command('gj', 'sheet.cursorRowIndex = len(rows); sheet.topRowIndex = cursorRowIndex-nVisibleRows', 'go to bottom row')
command('gl', 'sheet.cursorVisibleColIndex = len(visibleCols)-1', 'go to rightmost column')

command('^G', 'status(statusLine)', 'show info for the current sheet')
command('^V', 'status(__version__)', 'show version information')

command('<', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorValue: col.getValue(row) != val, reverse=True) or status("no different value up this column")', 'move up to previous value in this column')
command('>', 'moveToNextRow(lambda row,sheet=sheet,col=cursorCol,val=cursorValue: col.getValue(row) != val) or status("no different value down this column")', 'move down to next value in this column')
command('{', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row), reverse=True) or status("no previous selected row")', 'move to previous selected row')
command('}', 'moveToNextRow(lambda row,sheet=sheet: sheet.isSelected(row)) or status("no next selected row")', 'move to next selected row')

command('_', 'cursorCol.toggleWidth(cursorCol.getMaxWidth(visibleRows))', 'toggle this column width between default_width and to fit visible values')
command('-', 'cursorCol.width = 0', 'hide this column')
command('^', 'cursorCol.name = editCell(cursorVisibleColIndex, -1)', 'rename this column')
command('+', 'cursorCol.aggregator = chooseOne(aggregators)', 'choose aggregator for this column')
command('!', 'cursorRight(toggleKeyColumn(cursorColIndex))', 'toggle this column as a key column')

command('g_', 'for c in visibleCols: c.width = c.getMaxWidth(visibleRows)', 'set width of all columns to fit visible cells')
command('g^', 'for c in visibleCols: c.name = c.getDisplayValue(cursorRow)', 'set names of all visible columns to this row')

command('[', 'rows.sort(key=lambda r,col=cursorCol: col.getValue(r))', 'sort by this column ascending')
command(']', 'rows.sort(key=lambda r,col=cursorCol: col.getValue(r), reverse=True)', 'sort by this column descending')
command('g[', 'rows.sort(key=lambda r,cols=keyCols: tuple(c.getValue(r) for c in cols))', 'sort by all key columns ascending')
command('g]', 'rows.sort(key=lambda r,cols=keyCols: tuple(c.getValue(r) for c in cols), reverse=True)', 'sort by all key columns descending')

command('^D', 'options.debug = not options.debug; status("debug " + ("ON" if options.debug else "OFF"))', 'toggle debug mode')

command('^E', 'vd.lastErrors and vd.push(TextSheet("last_error", vd.lastErrors[-1])) or status("no error")', 'open stack trace for most recent error')

command('^^', 'vd.sheets[0], vd.sheets[1] = vd.sheets[1], vd.sheets[0]', 'jump to previous sheet')
command('^I',  'moveListItem(vd.sheets, 0, len(vd.sheets))', 'cycle through sheet stack') # TAB
command('KEY_BTAB', 'moveListItem(vd.sheets, -1, 0)', 'reverse cycle through sheet stack')

command('g^E', 'vd.push(TextSheet("last_errors", "\\n\\n".join(vd.lastErrors)))', 'open most recent errors')

command('^R', 'reload(); status("reloaded")', 'reload sheet from source')

command('/', 'moveRegex(regex=input("/", type="regex"), columns="cursorCol", backward=False)', 'search this column forward for regex')
command('?', 'moveRegex(regex=input("?", type="regex"), columns="cursorCol", backward=True)', 'search this column backward for regex')
command('n', 'moveRegex(reverse=False)', 'go to next match')
command('p', 'moveRegex(reverse=True)', 'go to previous match')

command('g/', 'moveRegex(regex=input("g/", type="regex"), backward=False, columns="visibleCols")', 'search regex forward in all visible columns')
command('g?', 'moveRegex(regex=input("g?", type="regex"), backward=True, columns="visibleCols")', 'search regex backward in all visible columns')

command('~', 'cursorCol.type = str', 'set column type to string')
command('@', 'cursorCol.type = date', 'set column type to ISO8601 datetime')
command('#', 'cursorCol.type = int', 'set column type to integer')
command('$', 'cursorCol.type = currency', 'set column type to currency')
command('%', 'cursorCol.type = float', 'set column type to float')

command('e', 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex)); sheet.cursorRowIndex += 1', 'edit this cell')
command('ge', 'cursorCol.setValues(selectedRows, input("set selected to: ", value=cursorValue))', 'edit this column for all selected rows')

command('c', 'searchColumnNameRegex(input("column name regex: ", "regex"))', 'go to visible column by regex of name')
command('r', 'sheet.cursorRowIndex = int(input("row number: "))', 'go to row number')

command('d', 'rows.pop(cursorRowIndex)', 'delete this row')
command('gd', 'deleteSelected()', 'delete all selected rows')

command('o', 'vd.push(openSource(input("open: ", "filename")))', 'open local file or url')
command('^S', 'saveSheet(sheet, input("save to: ", "filename", value=str(sheet.source)))', 'save this sheet to new file')

# slide rows/columns around
command('H', 'moveVisibleCol(cursorVisibleColIndex, max(cursorVisibleColIndex-1, 0)); sheet.cursorVisibleColIndex -= 1', 'move this column one left')
command('J', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, min(cursorRowIndex+1, nRows-1))', 'move this row one down')
command('K', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, max(cursorRowIndex-1, 0))', 'move this row one up')
command('L', 'moveVisibleCol(cursorVisibleColIndex, min(cursorVisibleColIndex+1, nVisibleCols-1)); sheet.cursorVisibleColIndex += 1', 'move this column one right')
command('gH', 'moveListItem(columns, cursorColIndex, nKeys)', 'move this column all the way to the left of the non-key columns')
command('gJ', 'moveListItem(rows, cursorRowIndex, nRows)', 'move this row all the way to the bottom')
command('gK', 'moveListItem(rows, cursorRowIndex, 0)', 'move this row all the way to the top')
command('gL', 'moveListItem(columns, cursorColIndex, nCols)', 'move this column all the way to the right')

command('O', 'vd.push(OptionsSheet("sheet options", baseOptions))', 'open Options for this sheet')

command(' ', 'toggle([cursorRow]); cursorDown(1)', 'toggle select of this row')
command('s', 'select([cursorRow]); cursorDown(1)', 'select this row')
command('u', 'unselect([cursorRow]); cursorDown(1)', 'unselect this row')

command('|', 'selectByIdx(searchRegex(regex=input("|", type="regex"), columns="cursorCol"))', 'select rows by regex matching this columns')
command('\\', 'unselectByIdx(searchRegex(regex=input("\\\\", type="regex"), columns="cursorCol"))', 'unselect rows by regex matching this columns')

command('g ', 'toggle(rows)', 'toggle select of all rows')
command('gs', 'select(rows)', 'select all rows')
command('gu', '_selectedRows.clear()', 'unselect all rows')

command('g|', 'selectByIdx(searchRegex(regex=input("g|", type="regex"), columns="visibleCols"))', 'select rows by regex matching any visible column')
command('g\\', 'unselectByIdx(searchRegex(regex=input("g\\\\", type="regex"), columns="visibleCols"))', 'unselect rows by regex matching any visible column')

command(',', 'select(gatherBy(lambda r,c=cursorCol,v=cursorValue: c.getValue(r) == v), progress=False)', 'select rows matching by this column')
command('g,', 'select(gatherBy(lambda r,v=cursorRow: r == v), progress=False)', 'select all rows that match this row')

command('"', 'vd.push(sheet.copy("_selected")).rows = list(sheet.selectedRows)', 'push duplicate sheet with only selected rows')
command('g"', 'vd.push(sheet.copy())', 'push duplicate sheet')
command('P', 'vd.push(copy("_sample")).rows = random.sample(rows, int(input("random population size: ")))', 'push duplicate sheet with a random sample of <N> rows')
command('V', 'vd.push(TextSheet("%s[%s].%s" % (name, cursorRowIndex, cursorCol.name), cursorValue))', 'view readonly contents of this cell in a new sheet')

command('`', 'vd.push(source if isinstance(source, Sheet) else None)', 'push source sheet')

# VisiData uses Python native int, float, str, and adds simple date, currency, and anytype.
#
# A type T is used internally in these ways:
#    o = T(str)   # for conversion from string
#    o = T()      # for default value to be used when conversion fails
#
# The resulting object o must be orderable and convertible to a string for display and certain outputs (like csv).

## minimalist 'any' type
def anytype(r=''):
    return str(r)
anytype.__name__ = ''

option('float_chars', '+-0123456789.eE_', 'valid numeric characters')
def currency(s):
    floatchars = options.float_chars
    if isinstance(s, str):
        while s[0] not in floatchars:
            s = s[1:]
        while s[-1] not in floatchars:
            s = s[:-1]
    return float(s)

class date:
    '`datetime` wrapper, constructing from time_t or with dateutil.parse'

    def __init__(self, s=None):
        if s is None:
            self.dt = datetime.datetime.now()
        elif isinstance(s, int) or isinstance(s, float):
            self.dt = datetime.datetime.fromtimestamp(s)
        elif isinstance(s, str):
            import dateutil.parser
            self.dt = dateutil.parser.parse(s)
        else:
            assert isinstance(s, datetime.datetime)
            self.dt = s

    def to_string(self, fmtstr=None):
        'Convert datetime object to string, in ISO 8601 format by default.'
        if not fmtstr:
            fmtstr = '%Y-%m-%d %H:%M:%S'
        return self.dt.strftime(fmtstr)

    def __getattr__(self, k):
        'Forward unknown attributes to inner datetime object'
        return getattr(self.dt, k)

    def __str__(self):
        return self.to_string()

    def __lt__(self, a):
        return self.dt < a.dt


typemap = {
    str: '~',
    date: '@',
    int: '#',
    currency: '$',
    float: '%',
    anytype: ' ',
}

windowWidth = 80
windowHeight = 25

def joinSheetnames(*sheetnames):
    'Concatenate sheet names using separator (`options.sheetname_joiner`).'
    return options.sheetname_joiner.join(str(x) for x in sheetnames)

def error(s):
    'Return custom exception as function, for use with `lambda` and `eval`.'
    raise Exception(s)

def status(s):
    'Return status property via function call.'
    return vd().status(s)

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


# VisiData singleton contains all sheets
@functools.lru_cache()
def vd():
    '''Instantiate and return singleton instance of VisiData class.

    Contains all sheets, and (as singleton) is unique instance..'''
    return VisiData()

def exceptionCaught(status=True):
    return vd().exceptionCaught(status)

def chooseOne(choices):
    '''Return `input` statement choices formatted with `/` as separator.

    Choices can be list/tuple or dict (if dict, its keys will be used).'''
    if isinstance(choices, dict):
        return choices[input('/'.join(choices.keys()) + ': ')]
    else:
        return input('/'.join(str(x) for x in choices) + ': ')

def regex_flags():
    'Return flags to pass to regex functions from options'
    return sum(getattr(re, f.upper()) for f in options.regex_flags)

def sync(f):
    'stub wrapper to wait for unfinished async tasks'
    pass

def async(func):
    'Function decorator to call in separate thread if async available.'
    def _execAsync(*args, **kwargs):
        return vd().execAsync(func, *args, **kwargs)
    return _execAsync

class VisiData:
    allPrefixes = 'gz'  # 'g'lobal, 'z'scroll

    def __init__(self):
        self.sheets = []
        self.statuses = [__version__]  # statuses shown until next action
        self.lastErrors = []
        self.searchContext = {}
        self.lastInputs = collections.defaultdict(collections.OrderedDict)  # [input_type] -> prevInputs
        self.keystrokes = ''
        self.inInput = False
        self.scr = None  # curses scr
        self.hooks = {}

    def status(self, s):
        'Add status message to be shown until next action.'
        s = str(s)
        self.statuses.append(s)
        return s

    def addHook(self, hookname, hookfunc):
        'Add hookfunc by hookname, to be called by corresponding `callHook`.'
        if hookname in self.hooks:
            hooklist = self.hooks[hookname]
        else:
            hooklist = []
            self.hooks[hookname] = hooklist

        hooklist.append(hookfunc)

    def callHook(self, hookname, *args, **kwargs):
        'Call all functions registered with `addHook` for the given hookname.'
        r = None
        for f in self.hooks.get(hookname, []):
            r = r or f(*args, **kwargs)
        return r

    def execAsync(self, func, *args, **kwargs):
        'Synchronous async caller stub, replaced if async available.'
        return func(*args, **kwargs)

    def editText(self, y, x, w, **kwargs):
        'Wrap global editText with `preedit` and `postedit` hooks.'
        v = self.callHook('preedit')
        if v is not None:
            return v
        v = editText(self.scr, y, x, w, **kwargs)
        if kwargs.get('display', True):
            self.status('"%s"' % v)
            self.callHook('postedit', v)
        return v

    def getkeystroke(self):
        'Get keystroke and display it on status bar.'
        k = None
        try:
            k = self.scr.get_wch()
            self.drawRightStatus()
        except Exception:
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

        status("ncols=%s" % len(columns))
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
        sheet.progressTotal = sheet.nRows
        sheet.progressMade = 0

        for r in rng:
            sheet.progressMade += 1
            c = findMatchingColumn(sheet, sheet.rows[r], columns, regex.search)
            if c:
                if moveCursor:
                    sheet.cursorRowIndex = r
                    sheet.cursorVisibleColIndex = sheet.visibleCols.index(c)
                    return
                else:
                    matchingRowIndexes += 1
                    yield r

        for r in rng2:
            sheet.progressMade += 1
            c = findMatchingColumn(sheet, sheet.rows[r], columns, regex.search)
            if c:
                if moveCursor:
                    sheet.cursorRowIndex = r
                    sheet.cursorVisibleColIndex = sheet.visibleCols.index(c)
                    status('search wrapped')   # the only reason for the duplicate code block
                    return
                else:
                    matchingRowIndexes += 1
                    yield r

        status('%s matches for /%s/' % (matchingRowIndexes, regex.pattern))

    def exceptionCaught(self, status=True):
        'Maintain list of most recent errors and return most recent one.'
        import traceback
        self.lastErrors.append(traceback.format_exc().strip())
        self.lastErrors = self.lastErrors[-10:]  # keep most recent
        if status:
            return self.status(self.lastErrors[-1].splitlines()[-1])
        if options.debug:
            raise

    def drawLeftStatus(self, vs):
        'Draw left side of status bar.'
        try:
            lstatus = self.leftStatus(vs)
            attr = colors[options.color_status]
            drawClip(self.scr, windowHeight-1, 0, lstatus, attr, windowWidth)
        except Exception as e:
            self.exceptionCaught()

    def drawRightStatus(self):
        'Draw right side of status bar.'
        try:
            rstatus = self.rightStatus()
            attr = colors[options.color_status]
            drawClip(self.scr, windowHeight-1, windowWidth-len(rstatus)-2, rstatus, attr)
            curses.doupdate()
        except Exception as e:
            self.exceptionCaught()

    def leftStatus(self, vs):
        'Compose left side of status bar from status messages.'
        s = options.disp_status_fmt.format(sheet=vs)
        s += options.disp_status_sep.join(self.statuses)
        return s

    def rightStatus(self):
        'Compose right side of status bar.'
        sheet = self.sheets[0]
        if sheet.progressMade == sheet.progressTotal:
            pctLoaded = 'rows'
        else:
            pctLoaded = ' %2d%%' % sheet.progressPct
        return '%s %9d %s' % (self.keystrokes, sheet.nRows, pctLoaded)

    def run(self, scr):
        'Manage execution of keystrokes and subsequent redrawing of screen.'
        global windowHeight, windowWidth, sheet
        windowHeight, windowWidth = scr.getmaxyx()
        scr.timeout(int(options.curses_timeout))
        self.scr = scr

        self.keystrokes = ''
        while True:
            if not self.sheets:
                # if no more sheets, exit
                return

            sheet = self.sheets[0]

            try:
                sheet.draw(scr)
            except Exception as e:
                self.exceptionCaught()

            self.drawLeftStatus(sheet)
            self.drawRightStatus()  # visible during this getkeystroke

            keystroke = self.getkeystroke()
            if keystroke:
                if self.keystrokes not in self.allPrefixes:
                    self.keystrokes = ''

                self.statuses.clear()
                self.keystrokes += keystroke
            self.drawRightStatus()  # visible for commands that wait for input

            if not keystroke:  # timeout instead of keypress
                pass
            elif keystroke == '^Q':
                return self.lastErrors and self.lastErrors[-1]
            elif keystroke == 'KEY_RESIZE':
                windowHeight, windowWidth = scr.getmaxyx()
            elif keystroke == 'KEY_MOUSE':
                try:
                    devid, x, y, z, bstate = curses.getmouse()
                    sheet.cursorRowIndex = sheet.topRowIndex+y-1
                except Exception:
                    self.exceptionCaught()
            elif self.keystrokes in sheet.commands:
                sheet.exec_command(g_globals, sheet.commands[self.keystrokes])
            elif keystroke in self.allPrefixes:
                pass
            else:
                status('no command for "%s"' % (self.keystrokes))

            self.callHook('predraw')
            sheet.checkCursor()

    def replace(self, vs):
        'Replace top sheet with the given sheet `vs`.'
        self.sheets.pop(0)
        return self.push(vs)

    def push(self, vs):
        'Move given sheet `vs` to index 0 of list `sheets`.'
        if vs:
            if vs in self.sheets:
                self.sheets.remove(vs)
                self.sheets.insert(0, vs)
            elif len(vs.rows) == 0:  # first time
                self.sheets.insert(0, vs)
                vs.reload()
            else:
                self.sheets.insert(0, vs)
            return vs
# end VisiData class

class LazyMap:
    'Wrap Python `dict` basic functionality.'
    def __init__(self, keys, getter, setter):
        self._keys = keys
        self._getter = getter
        self._setter = setter

    def keys(self):
        return self._keys

    def __getitem__(self, k):
        if k not in self._keys:
            raise KeyError(k)
        return self._getter(k)

    def __setitem__(self, k, v):
        self._keys.append(k)
        self._setter(k, v)

class Sheet:
    'Base object for add-on inheritance.'
    def __init__(self, name, *sources, columns=None):
        self.name = name
        self.sources = sources

        self.rows = []           # list of opaque row objects
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorVisibleColIndex = 0  # index of cursor into self.visibleCols

        self.topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftVisibleColIndex = 0    # cursorVisibleColIndex of leftmost column
        self.rightVisibleColIndex = 0
        self.loader = None

        # as computed during draw()
        self.rowLayout = {}      # [rowidx] -> y
        self.visibleColLayout = {}      # [vcolidx] -> (x, w)

        # all columns in display order
        self.columns = columns or []        # list of Column objects
        self.nKeys = 0           # self.columns[:nKeys] are all pinned to the left and matched on join

        # commands specific to this sheet
        self.commands = collections.ChainMap(collections.OrderedDict(), baseCommands)

        self.filetype = None
        self._selectedRows = {}  # id(row) -> row

        # for progress bar
        self.progressMade = 0
        self.progressTotal = 0

        # only allow one async task per sheet
        self.currentTask = None

        self.colorizers = [ self.colorCursorCol, self.colorKeyCol, self.colorCursorRow, self.colorSelectedRow ]

    def genProgress(self, L, total=None):
        'Create generator (for for-loops), with `progressTotal` property.'
        self.progressTotal = total or len(L)
        self.progressMade = 0
        for i in L:
            self.progressMade += 1
            yield i

        self.progressMade = self.progressTotal

    @staticmethod
    def colorCursorCol(self, col, r, value):
        if col is self.cursorCol:
            if r is None:
                return options.color_current_hdr, 9
            else:
                return options.color_current_col, 9

    @staticmethod
    def colorKeyCol(self, col, r, value):
        if col in self.keyCols:
            return options.color_key_col, 7

    @staticmethod
    def colorCursorRow(self, col, r, value):
        if r and r is self.cursorRow:
            return options.color_current_row, 10

    @staticmethod
    def colorSelectedRow(self, col, r, value):
        if self.isSelected(r):
            return options.color_selected_row, 8


    def command(self, keystrokes, execstr, helpstr):
        'Populate command, help-string and execution string for keystrokes.'
        if isinstance(keystrokes, str):
            keystrokes = [keystrokes]

        for ks in keystrokes:
            self.commands[ks] = (ks, helpstr, execstr)

    def moveRegex(self, *args, **kwargs):
        'Wrap `VisiData.searchRegex`, with cursor additionally moved.'
        list(self.searchRegex(*args, moveCursor=True, **kwargs))

    def searchRegex(self, *args, **kwargs):
        'Wrap `VisiData.searchRegex`.'
        return self.vd.searchRegex(self, *args, **kwargs)

    def searchColumnNameRegex(self, colregex):
        'Select visible column matching `colregex`, if found.'
        for i, c in enumPivot(self.visibleCols, self.cursorVisibleColIndex):
            if re.search(colregex, c.name, regex_flags()):
                self.cursorVisibleColIndex = i
                return

    def reload(self):
        'Default reloader, wrapping `loader` method.'
        if self.loader:
            self.loader()
        else:
            status('no reloader')

    def copy(self, suffix="'"):
        'Wrap `deepcopy`, needed to avoid pass-by-reference pollution.'
        c = copy.copy(self)
        c.name += suffix
        c.topRowIndex = c.cursorRowIndex = 0
        c.columns = copy.deepcopy(self.columns)
        c._selectedRows = self._selectedRows.copy()
        c.colorizers = self.colorizers.copy()
        return c

    @async
    def deleteSelected(self):
        'Delete all selected rows.'
        oldrows = self.rows
        oldidx = self.cursorRowIndex
        ndeleted = 0

        row = None   # row to re-place cursor after
        while oldidx < len(oldrows):
            if not self.isSelected(oldrows[oldidx]):
                row = self.rows[oldidx]
                break
            oldidx += 1

        self.rows = []
        for r in self.genProgress(oldrows):
            if not self.isSelected(r):
                self.rows.append(r)
                if r is row:
                    self.cursorRowIndex = len(self.rows)-1
            else:
                ndeleted += 1

        nselected = len(self._selectedRows)
        self._selectedRows.clear()
        status('deleted %s rows' % ndeleted)
        if ndeleted != nselected:
            error('expected %s' % nselected)

    def __repr__(self):
        return self.name

    def exec_command(self, vdglobals, cmd):
        'Wrap execution of `cmd`, adding globals and `locs` dictionary.'
        escaped = False

        if vdglobals is None:
            vdglobals = g_globals
        # handy globals for use by commands
        keystrokes, _, execstr = cmd
        self.vd = vd()
        self.sheet = self
        locs = LazyMap(dir(self),
                lambda k,s=self: getattr(s, k),
                lambda k,v,s=self: setattr(s, k, v)
                )

        self.vd.callHook('preexec', self, keystrokes)

        try:
            exec(execstr, vdglobals, locs)
        except EscapeException as e:  # user aborted
            self.vd.status('EscapeException ' + ''.join(e.args[0:]))
            escaped = True
        except Exception:
            self.vd.exceptionCaught()

        self.vd.callHook('postexec', self.vd.sheets[0] if self.vd.sheets else None, escaped)

        return escaped

    def clipdraw(self, y, x, s, attr, w):
        'Wrap `drawClip`.'
        return drawClip(self.scr, y, x, s, attr, w)

    @property
    def name(self):
        'Wrap return of `_name`.'
        return self._name

    @name.setter
    def name(self, name):
        'Wrap setting of `_name`.'
        self._name = name.replace(' ', '_')

    @property
    def source(self):
        'Return first source, if any.'
        if not self.sources:
            return None
        else:
#            assert len(self.sources) == 1, len(self.sources)
            return self.sources[0]

    @property
    def progressPct(self):
        'Return percentage of rows completed.'
        if self.progressTotal != 0:
            return int(self.progressMade*100/self.progressTotal)

    @property
    def nVisibleRows(self):
        'Return number of visible rows, calculable from window height.'
        return windowHeight-2

    @property
    def cursorCol(self):
        'Return current Column object.'
        return self.visibleCols[self.cursorVisibleColIndex]

    @property
    def cursorRow(self):
        'Return current row.'
        return self.rows[self.cursorRowIndex]

    @property
    def visibleRows(self):  # onscreen rows
        'Return a list of rows currently visible onscreen.'
        return self.rows[self.topRowIndex:self.topRowIndex+self.nVisibleRows]

    @property
    def visibleCols(self):  # non-hidden cols
        'Return a list of unhidden Column objects.'
        return [c for c in self.columns if not c.hidden]

    @property
    def visibleColNames(self):
        'Return string of visible column-names.'
        return ' '.join(c.name for c in self.visibleCols)

    @property
    def cursorColIndex(self):
        'Return index of current column into Sheet.columns.'
        return self.columns.index(self.cursorCol)

    @property
    def keyCols(self):
        'Return list of key columns.'
        return self.columns[:self.nKeys]

    @property
    def nonKeyVisibleCols(self):
        'Return list of unhidden non-key columns.'
        return [c for c in self.columns[self.nKeys:] if not c.hidden]

    @property
    def keyColNames(self):
        'Return string of key column names.'
        return options.disp_key_sep.join(c.name for c in self.keyCols)

    @property
    def cursorValue(self):
        'Return cell contents at current row and column.'
        return self.cellValue(self.cursorRowIndex, self.cursorColIndex)

    @property
    def statusLine(self):
        'Return status-line element showing row and column stats.'
        rowinfo = 'row %d/%d (%d selected)' % (self.cursorRowIndex, self.nRows, len(self._selectedRows))
        colinfo = 'col %d/%d (%d visible)' % (self.cursorColIndex, self.nCols, len(self.visibleCols))
        return '%s  %s' % (rowinfo, colinfo)

    @property
    def nRows(self):
        'Return number of rows.'
        return len(self.rows)

    @property
    def nCols(self):
        'Return number of columns.'
        return len(self.columns)

    @property
    def nVisibleCols(self):
        'Return number of visible columns.'
        return len(self.visibleCols)

## selection code
    def isSelected(self, r):
        'Return boolean: is current row selected?'
        return id(r) in self._selectedRows

    @async
    def toggle(self, rows):
        'Select any unselected rows.'
        for r in self.genProgress(rows, len(self.rows)):
            if not self.unselectRow(r):
                self.selectRow(r)

    def selectRow(self, row):
        'Select given row.'
        self._selectedRows[id(row)] = row

    def unselectRow(self, row):
        'Unselect given row, return True if selected; else return False.'
        if id(row) in self._selectedRows:
            del self._selectedRows[id(row)]
            return True
        else:
            return False

    @async
    def select(self, rows, status=True, progress=True):
        'Select given rows with option for progress-tracking.'
        before = len(self._selectedRows)
        for r in (self.genProgress(rows) if progress else rows):
            self.selectRow(r)
        if status:
            vd().status('selected %s%s rows' % (len(self._selectedRows)-before, ' more' if before > 0 else ''))

    @async
    def unselect(self, rows, status=True, progress=True):
        'Unselect given rows with option for progress-tracking.'
        before = len(self._selectedRows)
        for r in (self.genProgress(rows) if progress else rows):
            self.unselectRow(r)
        if status:
            vd().status('unselected %s/%s rows' % (before-len(self._selectedRows), before))

    def selectByIdx(self, rowIdxs):
        'Select given rows by index numbers.'
        self.select((self.rows[i] for i in rowIdxs), progress=False)

    def unselectByIdx(self, rowIdxs):
        'Unselect given rows by index numbers.'
        self.unselect((self.rows[i] for i in rowIdxs), progress=False)

    def gatherBy(self, func):
        'Yield each row matching the cursor value '
        for r in self.genProgress(self.rows):
            if func(r):
                yield r

    @property
    def selectedRows(self):
        'Return a list of selected rows in sheet order.'
        return [r for r in self.rows if id(r) in self._selectedRows]

## end selection code

    def moveVisibleCol(self, fromVisColIdx, toVisColIdx):
        'Move column to another position in sheet.'
        fromColIdx = self.columns.index(self.visibleCols[fromVisColIdx])
        toColIdx = self.columns.index(self.visibleCols[toVisColIdx])
        moveListItem(self.columns, fromColIdx, toColIdx)
        return toVisColIdx

    def cursorDown(self, n):
        "Increment cursor's row by `n`."
        self.cursorRowIndex += n

    def cursorRight(self, n):
        "Increment cursor's column by `n`."
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

    def cellValue(self, rownum, col):
        'Return cell value for given row number and Column object.'
        if not isinstance(col, Column):
            # assume it's the column number
            col = self.columns[col]
        return col.getValue(self.rows[rownum])

    def addColumn(self, col, index=None):
        'Insert column before current column or at given index.'
        if index is None:
            index = len(self.columns)
        if col:
            self.columns.insert(index, col)

    def toggleKeyColumn(self, colidx):
        'Toggle column at given index as key column.'
        if colidx >= self.nKeys: # if not a key, add it
            moveListItem(self.columns, colidx, self.nKeys)
            self.nKeys += 1
            return 1
        else:  # otherwise move it after the last key
            self.nKeys -= 1
            moveListItem(self.columns, colidx, self.nKeys)
            return 0

    def moveToNextRow(self, func, reverse=False):
        'Move cursor to next (prev if reverse) row for which func returns True.  Returns False if no row meets the criteria.'
        rng = range(self.cursorRowIndex-1, -1, -1) if reverse else range(self.cursorRowIndex+1, self.nRows)

        for i in rng:
            if func(self.rows[i]):
                self.cursorRowIndex = i
                return True

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
        elif self.topRowIndex > self.nRows-self.nVisibleRows:
            self.topRowIndex = self.nRows-self.nVisibleRows

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
                if cur_x+cur_w < windowWidth:  # current columns fit entirely on screen
                    break
                self.leftVisibleColIndex += 1

    def calcColLayout(self):
        'Set right-most visible column, based on calculation.'
        self.visibleColLayout = {}
        x = 0
        vcolidx = 0
        for vcolidx in range(0, self.nVisibleCols):
            col = self.visibleCols[vcolidx]
            if col.width is None and self.visibleRows:
                col.width = col.getMaxWidth(self.visibleRows)+len(options.disp_more_left)+len(options.disp_more_right)
            width = col.width if col.width is not None else col.getMaxWidth(self.visibleRows)  # handle delayed column width-finding
            if col in self.keyCols or vcolidx >= self.leftVisibleColIndex:  # visible columns
                self.visibleColLayout[vcolidx] = [x, min(width, windowWidth-x)]
                x += width+len(options.disp_column_sep)
            if x > windowWidth-1:
                break

        self.rightVisibleColIndex = vcolidx

    def colorize(self, col, row, value=None):
        'Returns curses attribute for the given col/row/value'
        rowattr = 0
        rowattrpre = 0

        for func in self.colorizers:
            ret = func(self, col, row, value)
            if ret:
                color, precedence = ret
                rowattr, rowattrpre = colors.update(rowattr, rowattrpre, color, precedence)

        return rowattr

    def drawColHeader(self, vcolidx):
        'Compose and draw column header for given vcolidx.'
        col = self.visibleCols[vcolidx]

        # hdrattr highlights whole column header
        # rowattr is for header separators
        rowattr = self.colorize(None, None) or colors[options.color_column_sep]
        hdrattr = self.colorize(col, None, None) or colors[options.color_default_hdr]

        C = options.disp_column_sep
        if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
            C = options.disp_keycol_sep

        x, colwidth = self.visibleColLayout[vcolidx]

        # ANameTC
        T = typemap.get(col.type, '?')
        N = ' ' + (col.name or defaultColNames[vcolidx])  # save room at front for LeftMore
        if len(N) > colwidth-1:
            N = N[:colwidth-len(options.disp_truncator)] + options.disp_truncator
        self.clipdraw(0, x, N, hdrattr, colwidth)
        self.clipdraw(0, x+colwidth-len(T), T, hdrattr, len(T))

        if vcolidx == self.leftVisibleColIndex and col not in self.keyCols and self.nonKeyVisibleCols.index(col) > 0:
            A = options.disp_more_left
            self.scr.addstr(0, x, A, rowattr)

        if C and x+colwidth+len(C) < windowWidth:
            self.scr.addstr(0, x+colwidth, C, rowattr)

    def isVisibleIdxKey(self, vcolidx):
        'Return boolean: is given column index a key column?'
        return self.visibleCols[vcolidx] in self.keyCols

    def draw(self, scr):
        'Draw entire screen onto the `scr` curses object.'
        global windowHeight, windowWidth
        numHeaderRows = 1
        self.scr = scr  # for clipdraw convenience
        scr.erase()  # clear screen before every re-draw

        windowHeight, windowWidth = scr.getmaxyx()
        if not self.columns:
            return

        self.rowLayout = {}
        self.calcColLayout()
        for vcolidx, colinfo in sorted(self.visibleColLayout.items()):
            x, colwidth = colinfo
            col = self.visibleCols[vcolidx]

            if x < windowWidth:  # only draw inside window
                self.drawColHeader(vcolidx)

                y = numHeaderRows
                for rowidx in range(0, self.nVisibleRows):
                    if self.topRowIndex + rowidx >= self.nRows:
                        break

                    self.rowLayout[self.topRowIndex+rowidx] = y

                    row = self.rows[self.topRowIndex + rowidx]
                    cellval = col.getDisplayValue(row, colwidth-1)

                    attr = self.colorize(col, row, cellval) or colors[options.color_default]
                    rowattr = self.colorize(None, row) or colors[options.color_column_sep]

                    self.clipdraw(y, x, options.disp_column_fill + cellval, attr, colwidth)

                    annotation = ''
                    if isinstance(cellval, CalcErrorStr):
                        annotation = options.disp_getter_exc
                        notecolor = colors[options.color_getter_exc]
                    elif isinstance(cellval, WrongTypeStr):
                        annotation = options.disp_format_exc
                        notecolor = colors[options.color_format_exc]

                    if annotation:
                        self.clipdraw(y, x+colwidth-len(annotation), annotation, notecolor, len(annotation))

                    sepchars = options.disp_column_sep
                    if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
                        sepchars = options.disp_keycol_sep

                    if x+colwidth+len(sepchars) <= windowWidth:
                       self.scr.addstr(y, x+colwidth, sepchars, rowattr)

                    y += 1

        if vcolidx+1 < self.nVisibleCols:
            self.scr.addstr(0, windowWidth-1, options.disp_more_right, colors[options.color_column_sep])

    def editCell(self, vcolidx=None, rowidx=None):
        '''Call `editText` on given cell after setting other parameters.

        Return row after editing cell.'''
        if options.readonly:
            status('readonly mode')
            return
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
            currentValue = self.cellValue(self.cursorRowIndex, col)

        r = vd().editText(y, x, w, value=currentValue, fillchar=options.disp_edit_fill)
        if rowidx >= 0:
            r = col.type(r)  # convert input to column type

        return r

class WrongTypeStr(str):
    'Wrap `str` to indicate that type-conversion failed.'
    pass

class CalcErrorStr(str):
    'Wrap `str` (perhaps with error message), indicating `getValue` failed.'
    pass


def distinct(values):
    'Count unique elements in `values`.'
    return len(set(values))

def avg(values):
    'Calculate average or return None.'
    return float(sum(values))/len(values) if values else None

mean=avg

def count(values):
    'Count total number of elements or return None if 0.'
    return len([x for x in values if x is not None])

_sum = sum

def sum(values):
    "Wrap `_sum`, which is itself Python's built-in `sum`."
    return _sum(values)

avg.type = float
count.type = int
distinct.type = int
sum.type = None
#min.type = None
#max.type = None
aggregators = { '': None,
                'distinct': distinct,
                'sum': sum,
                'avg': avg,
                'mean': avg,
                'count': count, # (non-None)
                'min': min,
                'max': max
               }


class Column:
    '''Model spreadsheet-style "column".

    If `expr` is set, cell values will be computed by this object.'''

    def __init__(self, name, type=anytype, getter=lambda r: r, setter=None, width=None, fmtstr=None):
        self.name = name      # use property setter from the get-go to strip spaces
        self.type = type      # anytype/str/int/float/date/func
        self.getter = getter  # getter(r)
        self.setter = setter  # setter(r,v)
        self.width = width    # == 0 if hidden, None if auto-compute next time
        self.expr = None      # Python string expression if computed column
        self.aggregator = None # function to use on the list of column values when grouping
        self.fmtstr = fmtstr

    def copy(self):
        'Wrap `copy.copy`.'
        return copy.copy(self)

    @property
    def name(self):
        'Return `_name`.'
        return self._name

    @name.setter
    def name(self, name):
        'Set `_name`.'
        self._name = str(name).replace(' ', '_')

    @property
    def type(self):
        'Return `_type`.'
        return self._type

    @type.setter
    def type(self, t):
        'Set `_type`.'
        if isinstance(t, str):
            t = globals()[t]

        if t:
            assert callable(t)
            self._type = t
        else:
            self._type = anytype

    @property
    def aggregator(self):
        'Return `_aggregator`.'
        return self._aggregator

    @aggregator.setter
    def aggregator(self, aggfunc):
        'Set `_aggregator` to given `aggfunc` if it is callable.'
        if isinstance(aggfunc, str):
            if aggfunc:
                aggfunc = globals()[aggfunc]

        if aggfunc:
            assert callable(aggfunc)
            self._aggregator = aggfunc
        else:
            self._aggregator = None

    def format(self, cellval):
        'Format the type-name of given `cellval`.'

        if isinstance(cellval, (list, dict)):
            # complex objects can be arbitrarily large (like sheet.rows)
            return str(type(cellval))

        t = self.type
        val = t(cellval)
        if t is date:         return val.to_string(self.fmtstr)
        elif self.fmtstr is not None: return self.fmtstr.format(val)
        elif t is int:        return '{:d}'.format(val)
        elif t is float:      return '{:.02f}'.format(val)
        elif t is currency:   return '{:,.02f}'.format(val)
        else: return str(val)

    @property
    def hidden(self):
        "Set column width to zero, to 'hide' it."
        return self.width == 0

    def nEmpty(self, rows):
        'Count rows that are empty or contain None.'
        vals = self.values(rows)
        return sum(1 for v in vals if v == '' or v == None)

    def values(self, rows):
        'Return list of values of all rows.'
        return [self.getValue(r) for r in rows]

    def getValue(self, row):
        '''Return a properly-typed value, and also handle failures.

        Return a default value if the conversion fails; re-raise the
        exception if the getter fails.'''
        try:
            v = self.getter(row)
        except EscapeException:
            raise
        except Exception:
            exceptionCaught(status=False)
            return CalcErrorStr(self.type())

        try:
            return self.type(v)  # convert type on-the-fly
        except EscapeException:
            raise
        except Exception:
            exceptionCaught(status=False)
            return self.type()  # return a suitable value for this type

    def getDisplayValue(self, row, width=None):
        'Format cell value for display and return.'
        try:
            cellval = self.getter(row)
        except EscapeException:
            raise
        except Exception as e:
            exceptionCaught(status=False)
            return CalcErrorStr(options.disp_error_val)

        if cellval is None:
            return options.disp_none

        if isinstance(cellval, bytes):
            cellval = cellval.decode(options.encoding, options.encoding_errors)

        try:
            cellval = self.format(cellval)
            if width and self._type in (int, float, currency):
                cellval = cellval.rjust(width-1)
        except EscapeException:
            raise
        except Exception as e:
            exceptionCaught(status=False)
            cellval = WrongTypeStr(str(cellval))

        return cellval

    def setValues(self, rows, value):
        'Set given rows to `value`.'
        if not self.setter:
            error('column cannot be changed')
        value = self.type(value)
        for r in rows:
            self.setter(r, value)

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

def ColumnAttr(attrname, type=anytype, **kwargs):
    'Return Column object with `attrname` from current row Python object.'
    return Column(attrname, type=type,
            getter=lambda r,b=attrname: getattr(r,b),
            setter=lambda r,v,b=attrname: setattr(r,b,v),
            **kwargs)

def ColumnItem(attrname, itemkey, **kwargs):
    'Return Column object (with getitem/setitem) on the row Python object.'
    def setitem(r, i, v):  # function needed for use in lambda
        r[i] = v

    return Column(attrname,
            getter=lambda r,i=itemkey: r[i],
            setter=lambda r,v,i=itemkey,f=setitem: f(r,i,v),
            **kwargs)

def ArrayNamedColumns(columns):
    '''Return list of Column objects from named columns.

    Note: argument `columns` is a list of column names, Mapping to r[0]..r[n].'''
    return [ColumnItem(colname, i) for i, colname in enumerate(columns)]

def ArrayColumns(ncols):
    '''Return list of Column objects.

    Note: argument `ncols` is a count of columns,'''
    return [ColumnItem('', i, width=8) for i in range(ncols)]

def DictKeyColumns(d):
    'Return a list of Column objects from dictionary keys.'
    return [ColumnItem(k, k) for k in d]

def SubrowColumn(origcol, subrowidx, **kwargs):
    'Return Column object from sub-row.'
    return Column(origcol.name, origcol.type,
            getter=lambda r,i=subrowidx,f=origcol.getter: r[i] and f(r[i]) or None,
            setter=lambda r,v,i=subrowidx,f=origcol.setter: r[i] and f(r[i], v) or None,
            width=origcol.width,
            **kwargs)

def combineColumns(cols):
    'Return Column object formed by joining fields in given columns.'
    return Column("+".join(c.name for c in cols),
                  getter=lambda r,cols=cols,ch=options.field_joiner: ch.join(filter(None, (c.getValue(r) for c in cols))))
###

def input(prompt, type='', **kwargs):
    'Compose input prompt.'
    if type:
        ret = _inputLine(prompt, history=list(vd().lastInputs[type].keys()), **kwargs)
        vd().lastInputs[type][ret] = ret
    else:
        ret = _inputLine(prompt, **kwargs)
    return ret

def _inputLine(prompt, **kwargs):
    'Add prompt to bottom of screen and get line of input from user.'
    global windowHeight, windowWidth

    scr = vd().scr
    if scr:
        windowHeight, windowWidth = scr.getmaxyx()
        scr.addstr(windowHeight-1, 0, prompt)
    vd().inInput = True
    ret = vd().editText(windowHeight-1, len(prompt), windowWidth-len(prompt)-8, attr=colors[options.color_edit_cell], unprintablechar=options.disp_unprintable, **kwargs)
    vd().inInput = False
    return ret

def saveSheet(vs, fn):
    'Save sheet `vs` with given filename `fn`.'
    assert vs.progressTotal == vs.progressMade, 'have to finish loading first'
    if Path(fn).exists():
        if options.confirm_overwrite:
            yn = input('%s already exists. overwrite? ' % fn, value='n')[:1]
            if not yn or yn not in 'Yy':
                error('overwrite disconfirmed')

    basename, ext = os.path.splitext(fn)
    funcname = 'save_' + ext[1:]
    if funcname not in g_globals:
        funcname = 'save_tsv'
    g_globals.get(funcname)(vs, fn)
    status('saving to ' + fn)


import unicodedata
def clipstr(s, dispw):
    '''Return clipped string and width in terminal display characters.

    Note: width may differ from len(s) if East Asian chars are 'fullwidth'.'''
    w = 0
    ret = ''
    ambig_width = options.unicode_ambiguous_width
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


def drawClip(scr, y, x, s, attr=curses.A_NORMAL, w=None):
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
        scr.addstr(y, x, options.disp_column_fill*w, attr)
        scr.addstr(y, x, s, attr)
    except Exception as e:
#        raise type(e)('%s [clip_draw y=%s x=%s dispw=%s w=%s]' % (e, y, x, dispw, w)
#                ).with_traceback(sys.exc_info()[2])
        pass


## Built-in sheets

## text viewer and dir browser
class TextSheet(Sheet):
    'Sheet displaying a string (one line per row) or a list of strings.'

    @async
    def reload(self):
        'Populate sheet via `reload` function.'
        self.rows = []
        self.columns = [Column(self.name, str, width=windowWidth)]
        if isinstance(self.source, list):
            for x in self.source:
                # copy so modifications don't change 'original'; also one iteration through generator
                self.addLine(x)
        elif isinstance(self.source, str):
            for L in self.source.splitlines():
                self.addLine(L)
        elif isinstance(self.source, io.IOBase):
            for L in self.source:
                self.addLine(L[:-1])
        elif isinstance(self.source, Path):
            for L in self.source.open_text():
                self.addLine(L[:-1])
        else:
            error('unknown text type ' + str(type(self.source)))

    def addLine(self, text):
        'Handle text re-wrapping.'
        self.rows.extend(textwrap.wrap(text, width=windowWidth-2))


class DirSheet(Sheet):
    'Sheet displaying directory, using ENTER to open a particular file.'

    def reload(self):
        'Populate sheet via `reload` function.'
        self.rows = [(p, p.stat()) for p in self.source.iterdir()]  #  if not p.name.startswith('.')]
        self.command(ENTER, 'vd.push(openSource(cursorRow[0]))', 'open file')  # path, filename
        self.columns = [Column('filename', str, lambda r: r[0].name + r[0].ext),
                      Column('type', str, lambda r: r[0].is_dir() and '/' or r[0].suffix),
                      Column('size', int, lambda r: r[1].st_size),
                      Column('mtime', date, lambda r: r[1].st_mtime)]

#### options management
class OptionsObject:
    'Get particular option value from `baseOptions`.'
    def __init__(self, d):
        self._opts = d
    def __getattr__(self, k):
        name, value, default, helpstr, option_type = self._opts[k]
        return option_type(value)
    def __setitem__(self, k, v):
        if k not in self._opts:
            raise Exception('no such option "%s"' % k)
        self._opts[k][1] = self._opts[k][4](v)

options = OptionsObject(baseOptions)

# Generator => A .. Z AA AB ...
defaultColNames = (''.join(j) for i in range(options.maxlen_col_hdr)
                             for j in itertools.product(string.ascii_uppercase,
                                   repeat=i+1)
                  )

class OptionsSheet(Sheet):
    'Sheet displaying user options.'

    def reload(self):
        'Populate sheet via `reload` function.'
        self.rows = list(self.source.values())
        self.columns = ArrayNamedColumns('option value default description'.split())
        self.command([ENTER, 'e'], 'cursorRow[1] = editCell(1)', 'edit this option')
        self.colorizers.append(self.colorOptionCell)
        self.nKeys = 1

    @staticmethod
    def colorOptionCell(sheet, col, row, value):
        if row and col and col.name in ['value', 'default'] and row[0].startswith('color_'):
            return col.getValue(row), 9


#### enable external addons
def open_vd(p):
    'Return a VisiData object with a sheet populated from a path `p`.'
    vs = open_tsv(p)
    vs.reload()
    return vd

def open_py(p):
    'Read and execute Python script at path `p`.'
    contents = p.read_text()
    exec(contents, g_globals)
    status('executed %s' % p)

def open_txt(p):
    'Create sheet from `.txt` file at path `p`, checking whether it is TSV.'
    with p.open_text() as fp:
        if '\t' in next(fp):
            return open_tsv(p)  # TSV often have .txt extension
        return TextSheet(p.name, p)

def getTsvHeaders(fp, nlines):
    'Return list of lists for use as headers, from paragraphs `fp`.'
    headers = []
    i = 0
    while i < nlines:
        L = next(fp)
        L = L[:-1]
        if L:
            headers.append(L.split('\t'))
            i += 1

    return headers

def open_tsv(p, vs=None):
    'Parse contents of Path `p` and populate columns.'

    if vs is None:
        vs = Sheet(p.name, p)
        vs.loader = lambda vs=vs: reload_tsv(vs)

    header_lines = int(options.headerlines)

    with vs.source.open_text() as fp:
        headers = getTsvHeaders(fp, header_lines or 1)  # get one data line if no headers

        if header_lines == 0:
            vs.columns = ArrayColumns(len(headers[0]))
        else:
            # columns ideally reflect the max number of fields over all rows
            # but that's a lot of work for a large dataset
            vs.columns = ArrayNamedColumns('\\n'.join(x) for x in zip(*headers[:header_lines]))

    return vs

@async
def reload_tsv(vs):
    'Asynchronous wrapper for `reload_tsv_sync`.'
    reload_tsv_sync(vs)

def reload_tsv_sync(vs):
    'Perform synchronous loading of TSV file, discarding header lines.'
    header_lines = int(options.headerlines)

    vs.rows = []
    with vs.source.open_text() as fp:
        getTsvHeaders(fp, header_lines)  # discard header lines

        vs.progressMade = 0
        vs.progressTotal = vs.source.filesize
        for L in fp:
            L = L[:-1]
            if L:
                vs.rows.append(L.split('\t'))
            vs.progressMade += len(L)

    vs.progressMade = 0
    vs.progressTotal = 0

    status('loaded %s' % vs.name)


@async
def save_tsv(vs, fn):
    'Write sheet to file `fn` as TSV, reporting progress on status bar.'
    with open(fn, 'w', encoding=options.encoding, errors=options.encoding_errors) as fp:
        colhdr = '\t'.join(col.name for col in vs.visibleCols) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)
        for r in vs.genProgress(vs.rows):
            fp.write('\t'.join(col.getDisplayValue(r) for col in vs.visibleCols) + '\n')
    status('%s save finished' % fn)

### Curses helpers

def editText(scr, y, x, w, attr=curses.A_NORMAL, value='', fillchar=' ', unprintablechar='.', completions=[], history=[], display=True):
    'A better curses line editing widget.'

    def until(func):
        'Delay until function `func` returns non-zero.'
        ret = None
        while not ret:
            ret = func()

        return ret

    def splice(v, i, s):
        'Splice (insert) `s` into string `v` at `i`: (v[i] = s[0]).'
        return v if i < 0 else v[:i] + s + v[i:]

    def clean(s):
        'Escape Curses-unprintable characters.'
        return ''.join(c if c.isprintable() else ('<%04X>' % ord(c)) for c in str(s))

    def delchar(s, i, remove=1):
        'Delete `remove` characters from str `s` beginning at position `i`.'
        return s[:i] + s[i+remove:]

    def complete(v, comps, cidx):
        'Complete keystroke `v` based on list `comps` of completions.'
        if comps:
            for i in range(cidx, cidx + len(comps)):
                i %= len(comps)
                if comps[i].startswith(v):
                    return comps[i]
        # beep
        return v

    insert_mode = True
    first_action = True
    v = str(value)  # value under edit
    i = 0           # index into v
    comps_idx = 2
    hist_idx = 0

    while True:
        if display:
            dispval = clean(v)
        else:
            dispval = '*' * len(v)
        dispi = i
        if len(dispval) < w:
            dispval += fillchar*(w-len(dispval))
        elif i >= w:
            dispi = w-1
            dispval = dispval[i-w:]

        scr.addstr(y, x, dispval, attr)
        scr.move(y, x+dispi)
        ch = vd().getkeystroke()
        if ch == '':                               continue
        elif ch == 'KEY_IC':                       insert_mode = not insert_mode
        elif ch == '^A' or ch == 'KEY_HOME':       i = 0
        elif ch == '^B' or ch == 'KEY_LEFT':       i -= 1
        elif ch == '^C' or ch == ESC:             raise EscapeException(ch)
        elif ch == '^D' or ch == 'KEY_DC':         v = delchar(v, i)
        elif ch == '^E' or ch == 'KEY_END':        i = len(v)
        elif ch == '^F' or ch == 'KEY_RIGHT':      i += 1
        elif ch in ('^H', 'KEY_BACKSPACE', '^?'):  i -= 1 if i > 0 else 0; v = delchar(v, i)
        elif ch == '^I':                           comps_idx += 1; v = complete(v[:i], completions, comps_idx)
        elif ch == 'KEY_BTAB':                     comps_idx -= 1; v = complete(v[:i], completions, comps_idx)
        elif ch == ENTER:                          break
        elif ch == '^K':                           v = v[:i]  # ^Kill to end-of-line
        elif ch == '^R':                           v = str(value)  # ^Reload initial value
        elif ch == '^T':                           v = delchar(splice(v, i-2, v[i-1]), i)  # swap chars
        elif ch == '^U':                           v = v[i:]; i = 0  # clear to beginning
        elif ch == '^V':                           v = splice(v, i, until(scr.get_wch)); i += 1  # literal character
        elif history and ch == 'KEY_UP':           hist_idx += 1; v = history[hist_idx % len(history)]
        elif history and ch == 'KEY_DOWN':         hist_idx -= 1; v = history[hist_idx % len(history)]
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

    return v


class ColorMaker:
    def __init__(self):
        self.attrs = {}
        self.color_attrs = {}

    def setup(self):
        self.color_attrs['black'] = curses.color_pair(0)

        for c in range(0, int(options.num_colors) or curses.COLORS):
            curses.init_pair(c+1, c, curses.COLOR_BLACK)
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
#    curses.mousemask(curses.ALL_MOUSE_EVENTS)  # enable mouse events

    return f(stdscr, *args)

def wrapper(f, *args):
    'Wrap `curses.wrapper`.'
    return curses.wrapper(setupcolors, f, *args)

### external interface

class Path:
    'File and path-handling class, modeled on `pathlib.Path`.'

    def __init__(self, fqpn):
        'Initialize with file-queue path-name.'
        self.fqpn = fqpn
        fn = os.path.split(fqpn)[-1]
        self.name, self.ext = os.path.splitext(fn)
        self.suffix = self.ext[1:]

    def open_text(self, mode='r'):
        'Open file.'
        return open(self.resolve(), mode=mode, encoding=options.encoding, errors=options.encoding_errors)

    def read_text(self):
        'Open and read file.'
        with self.open_text() as fp:
            return fp.read()

    def read_bytes(self):
        'Open and read file of bytes.'
        with open(self.resolve(), 'rb') as fp:
            return fp.read()

    def is_dir(self):
        'Return boolean: is path directory?'
        return os.path.isdir(self.resolve())

    def exists(self):
        'Return boolean: does path exist?'
        return os.path.exists(self.resolve())

    def iterdir(self):
        'Return list of directory contents.'
        return [self.parent] + [Path(os.path.join(self.fqpn, f)) for f in os.listdir(self.resolve())]

    def stat(self):
        'Wrap `os.stat`.'
        return os.stat(self.resolve())

    def resolve(self):
        'Wrap `os.path.expanduser`.'
        return os.path.expandvars(os.path.expanduser(self.fqpn))

    @property
    def parent(self):
        'Return symbolic parent directory.'
        return Path(self.fqpn + "/..")

    @property
    def filesize(self):
        'Return file size.'
        return self.stat().st_size

    def __str__(self):
        return self.fqpn


class InternalSource(Path):
    'minimal Path interface to satisfy a tsv loader'
    def __init__(self, fqpn, contents):
        super().__init__(fqpn)
        self.contents = contents

    def read_text(self):
        return self.contents

    def open_text(self):
        return io.StringIO(self.contents)


def openSource(p, filetype=None):
    'open a Path or a str (converts to Path or calls some TBD openUrl)'
    if isinstance(p, str):
        if '://' in p:
            vs = openUrl(p)
        else:
            return openSource(Path(p), filetype)  # convert to Path and recurse
    elif isinstance(p, Path):
        if not filetype:
            filetype = options.filetype or p.suffix

        if os.path.isdir(p.resolve()):
            vs = DirSheet(p.name, p)
            filetype = 'dir'
        else:
            openfunc = 'open_' + filetype.lower()
            if openfunc not in g_globals:
                status('no %s function' % openfunc)
                filetype = 'txt'
                openfunc = 'open_txt'
            vs = g_globals[openfunc](p)
    else:  # some other object
        status('unknown object type %s' % type(p))
        vs = None

    if vs:
        status('opening %s as %s' % (p.name, filetype))
    return vs

def run(sheetlist=[]):
    'Invoke Curses mode. (This is the main entry point.)'

    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', '25')

    ret = wrapper(cursesMain, sheetlist)
    if ret:
        print(ret)

def cursesMain(_scr, sheetlist=[]):
    'Populate VisiData object with sheets from a given list.'

    for fnrc in ('.visidatarc', '$XDG_CONFIG_HOME/visidata/config', '~/.visidatarc'):
        p = Path(fnrc)
        if p.exists():
            exec(open(p.resolve()).read())
            break

    colors.setup()

    for vs in sheetlist:
        vd().push(vs)  # first push does a reload

    return vd().run(_scr)

g_globals = None
def setGlobals(g):
    'Assign given `g` to (expected) global dict `g_globals`.'
    global g_globals
    g_globals = g

def setGlobal(k, v):
    'Manually set global key-value pair in `g_globals`.'
    g_globals[k] = v

if __name__ == '__main__':
    run(openSource(src) for src in sys.argv[1:])
