#!/usr/bin/env python3
#
# VisiData: a curses interface for exploring and arranging tabular data
#

__version__ = 'saul.pw/VisiData v0.41'
__author__ = 'Saul Pwanson <vd@saul.pw>'
__license__ = 'GPLv3'
__status__ = 'Development'

import sys
import os
import os.path
import copy
import collections
import functools
import itertools
import string
import re
import threading
import time
import curses
import datetime
import ctypes  # async exception
import io
import cProfile
import pstats
import random


class EscapeException(Exception):
    pass

base_commands = collections.OrderedDict()
base_options = collections.OrderedDict()

def command(keystrokes, execstr, helpstr):
    base_commands[keystrokes] = (keystrokes, helpstr, execstr)

def option(name, default, helpstr=''):
    base_options[name] = [name, default, default, helpstr]  # see OptionsObject
theme = option


option('debug', False, 'abort on error and display stacktrace')
option('readonly', False, 'disable saving')

option('headerlines', 1, 'parse first N rows of .csv/.tsv as column names')
option('encoding', 'utf-8', 'as passed to codecs.open')
option('encoding_errors', 'surrogateescape', 'as passed to codecs.open')

option('SubsheetSep', '~', 'string joining multiple sheet names')
option('cmdhistThreshold_ms', 1, 'minimum amount of time taken before adding command to cmdhist')
option('timeout_ms', '100', 'curses timeout in ms')
option('profile', True, 'profile async tasks')

theme('ch_Ellipsis', '…')
theme('ch_KeySep', '/')
theme('ch_WrongType', '~')
theme('ch_Error', '!')
theme('ch_Histogram', '*')
theme('ch_EditPadChar', '_')
theme('ch_LeftMore', '<')
theme('ch_RightMore', '>')
theme('ch_ColumnSep', '|', 'chars between columns')

theme('ch_FunctionError', '¿', 'when computation fails due to exception')
theme('ch_VisibleNone', '',  'visible contents of a cell whose value was None')

theme('c_CurRow', 'reverse')
theme('c_default', 'normal')
theme('c_SelectedRow', 'green')
theme('c_WrongType', 'magenta')
theme('c_Error', 'red')
theme('c_CurCol', 'bold')
theme('c_CurHdr', 'reverse')
theme('c_KeyCols', 'brown')
theme('c_Header', 'bold')
theme('c_ColumnSep', 'blue')
theme('ch_StatusSep', ' | ', 'string separating multiple statuses')
theme('ch_Unprintable', '.', 'a substitute character for unprintables')
theme('ch_ColumnFiller', ' ', 'pad chars after column value')
theme('ch_Newline', '\\n', 'displayable newline')
theme('c_StatusLine', 'bold', 'status line color')
theme('c_EditCell', 'normal', 'edit cell  line color')
theme('SheetNameFmt', '%s| ', 'status line prefix')
theme('ch_spinny', '◴◷◶◵', 'characters shown while commands are processing')

ENTER='^J'
ESC='^['

command('KEY_F(1)', 'vd.push(HelpSheet(name + "_commands", sheet.commands, base_commands))', 'open command help sheet')
command('q',  'vd.sheets.pop(0)', 'quit the current sheet')

command('KEY_LEFT',  'cursorRight(-1)', 'go one column left')
command('KEY_DOWN',  'cursorDown(+1)', 'go one row down')
command('KEY_UP',    'cursorDown(-1)', 'go one row up')
command('KEY_RIGHT', 'cursorRight(+1)', 'go one column right')
command('KEY_NPAGE', 'cursorDown(nVisibleRows); sheet.topRowIndex += nVisibleRows', 'scroll one page down')
command('KEY_PPAGE', 'cursorDown(-nVisibleRows); sheet.topRowIndex -= nVisibleRows', 'scroll one page up')
command('KEY_HOME',  'sheet.topRowIndex = sheet.cursorRowIndex = 0', 'go to top row')
command('KEY_END',   'sheet.cursorRowIndex = len(rows)-1', 'go to last row')

command('h', 'cursorRight(-1)', 'go one column left')
command('j', 'cursorDown(+1)', 'go one row down')
command('k', 'cursorDown(-1)', 'go one row up')
command('l', 'cursorRight(+1)', 'go one column right')

command('gq', 'vd.sheets.clear()', 'drop all sheets (clean exit)')

command('gh', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = 0', 'go to leftmost column')
command('gk', 'sheet.cursorRowIndex = sheet.topRowIndex = 0', 'go to top row')
command('gj', 'sheet.cursorRowIndex = len(rows); sheet.topRowIndex = cursorRowIndex-nVisibleRows', 'go to bottom row')
command('gl', 'sheet.cursorVisibleColIndex = len(visibleCols)-1', 'go to rightmost column')

command('^G', 'status(statusLine)', 'show info for the current sheet')
command('^V', 'status(__version__)', 'show version information')

command('t', 'sheet.topRowIndex = cursorRowIndex', 'scroll cursor row to top of screen')
command('m', 'sheet.topRowIndex = cursorRowIndex-int(nVisibleRows/2)', 'scroll cursor row to middle of screen')
command('b', 'sheet.topRowIndex = cursorRowIndex-nVisibleRows+1', 'scroll cursor row to bottom of screen')

command('<', 'skipUp()', 'skip up this column to previous value')
command('>', 'skipDown()', 'skip down this column to next value')

command('_', 'cursorCol.width = cursorCol.getMaxWidth(visibleRows)', 'set this column width to fit visible cells')
command('-', 'cursorCol.width = 0', 'hide this column')
command('^', 'cursorCol.name = cursorCol.getDisplayValue(cursorRow)', 'set this column header to this cell value')
command('!', 'toggleKeyColumn(cursorColIndex); cursorRight(1)', 'toggle this column as a key column')

command('g_', 'for c in visibleCols: c.width = c.getMaxWidth(visibleRows)', 'set width of all columns to fit visible cells')
command('g^', 'for c in visibleCols: c.name = c.getDisplayValue(cursorRow)', 'set names of all visible columns to this row')

command('[', 'rows.sort(key=lambda r,col=cursorCol: col.getValue(r))', 'sort by this column ascending')
command(']', 'rows.sort(key=lambda r,col=cursorCol: col.getValue(r), reverse=True)', 'sort by this column descending')

command('^D', 'options.debug = not options.debug; status("debug " + ("ON" if options.debug else "OFF"))', 'toggle debug mode')

command('^E', 'vd.lastErrors and vd.push(TextSheet("last_error", vd.lastErrors[-1])) or status("no error")', 'open stack trace for most recent error')

command('^^', 'vd.sheets[0], vd.sheets[1] = vd.sheets[1], vd.sheets[0]', 'jump to previous sheet')
command('^I',  'moveListItem(vd.sheets, 0, len(vd.sheets))', 'cycle through sheet stack') # TAB
command('KEY_BTAB', 'moveListItem(vd.sheets, -1, 0)', 'reverse cycle through sheet stack')

command('g^E', 'vd.push(TextSheet("last_errors", "\\n\\n".join(vd.lastErrors)))', 'open most recent errors')

command('R', 'sheet.filetype = input("change type to: ", value=sheet.filetype)', 'set source type of this sheet')
command('^R', 'reload(); status("reloaded")', 'reload sheet from source')

command('/', 'searchRegex(input("/", type="regex"), columns=[cursorCol], moveCursor=True)', 'search this column forward for regex')
command('?', 'searchRegex(input("?", type="regex"), columns=[cursorCol], backward=True, moveCursor=True)', 'search this column backward for regex')
command('n', 'searchRegex(columns=[cursorCol], moveCursor=True)', 'go to next match')
command('p', 'searchRegex(columns=[cursorCol], backward=True, moveCursor=True)', 'go to previous match')

command('g/', 'searchRegex(input("g/", type="regex"), moveCursor=True, columns=visibleCols)', 'search regex forward in all visible columns')
command('g?', 'searchRegex(input("g?", type="regex"), backward=True, moveCursor=True, columns=visibleCols)', 'search regex backward in all visible columns')
command('gn', 'sheet.cursorRowIndex = max(searchRegex() or [cursorRowIndex])', 'go to first match')
command('gp', 'sheet.cursorRowIndex = min(searchRegex() or [cursorRowIndex])', 'go to last match')

command('@', 'cursorCol.type = date', 'set column type to ISO8601 datetime')
command('#', 'cursorCol.type = int', 'set column type to integer')
command('$', 'cursorCol.type = str', 'set column type to string')
command('%', 'cursorCol.type = float', 'set column type to float')
command('~', 'cursorCol.type = detectType(cursorValue)', 'autodetect type of column by its data')

command('^P', 'vd.status(vd.statusHistory[0])', 'show last status message again')
command('g^P', 'vd.push(TextSheet("statuses", vd.statusHistory))', 'open last 100 statuses')

command('e', 'cursorCol.setValue(cursorRow, editCell(cursorVisibleColIndex))', 'edit this cell')
command('c', 'searchColumnNameRegex(input("column name regex: ", "regex"))', 'go to visible column by regex of name')
command('r', 'sheet.cursorRowIndex = int(input("row number: "))', 'go to row number')

command('d', 'rows.pop(cursorRowIndex)', 'delete this row')
command('gd', 'sheet.rows = list(filter(lambda r,sheet=sheet: not sheet.isSelected(r), sheet.rows)); _selectedRows.clear()', 'delete all selected rows')

command('o', 'vd.push(openSource(input("open: ", "filename")))', 'open local file or url')
command('^S', 'saveSheet(sheet, input("save to: ", "filename"))', 'save this sheet to new file')

# slide rows/columns around
command('H', 'moveVisibleCol(cursorVisibleColIndex, max(cursorVisibleColIndex-1, 0)); sheet.cursorVisibleColIndex -= 1', 'move this column one left')
command('J', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, min(cursorRowIndex+1, nRows-1))', 'move this row one down')
command('K', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, max(cursorRowIndex-1, 0))', 'move this row one up')
command('L', 'moveVisibleCol(cursorVisibleColIndex, min(cursorVisibleColIndex+1, nVisibleCols-1)); sheet.cursorVisibleColIndex += 1', 'move this column one right')
command('gH', 'moveListItem(columns, cursorColIndex, nKeys)', 'move this column all the way to the left of the non-key columns')
command('gJ', 'moveListItem(rows, cursorRowIndex, nRows)', 'move this row all the way to the bottom')
command('gK', 'moveListItem(rows, cursorRowIndex, 0)', 'move this row all the way to the top')
command('gL', 'moveListItem(columns, cursorColIndex, nCols)', 'move this column all the way to the right')

command('O', 'vd.push(OptionsSheet("sheet options", base_options))', 'open Options for this sheet')

command(' ', 'toggle([cursorRow]); cursorDown(1)', 'toggle select of this row')
command('s', 'select([cursorRow]); cursorDown(1)', 'select this row')
command('u', 'unselect([cursorRow]); cursorDown(1)', 'unselect this row')

command('|', 'selectByIdx(searchRegex(input("|", type="regex"), columns=[cursorCol]))', 'select rows by regex matching this columns')
command('\\', 'unselectByIdx(searchRegex(input("\\\\", type="regex"), columns=[cursorCol]))', 'unselect rows by regex matching this columns')

command('g ', 'toggle(rows)', 'toggle select of all rows')
command('gs', 'select(rows)', 'select all rows')
command('gu', '_selectedRows.clear()', 'unselect all rows')

command('g|', 'selectByIdx(searchRegex(input("|", type="regex"), columns=visibleCols))', 'select rows by regex matching any visible column')
command('g\\', 'unselectByIdx(searchRegex(input("\\\\", type="regex"), columns=visibleCols))', 'unselect rows by regex matching any visible column')

command('X', 'vd.push(SheetDict("lastInputs", vd.lastInputs))', 'push last inputs sheet')

command(',', 'selectBy(lambda r,c=cursorCol,v=cursorValue: c.getValue(r) == v)', 'select rows matching by this column')
command('g,', 'selectBy(lambda r,v=cursorRow: r == v)', 'select all rows that match this row')

command('"', 'vd.push(vd.sheets[0].copy("_selected")).rows = list(vd.sheets[0]._selectedRows.values())', 'push duplicate sheet with only selected rows')
command('g"', 'vd.push(vd.sheets[0].copy())', 'push duplicate sheet')
command('P', 'vd.push(copy("_sample")).rows = random.sample(rows, int(input("random population size: ")))', 'push duplicate sheet with a random sample of <N> rows')


# VisiData uses Python native int, float, str, and adds a simple date and anytype.
#
# A type T is used internally in these ways:
#    o = T(str)   # for conversion from string
#    o = T()      # for default value to be used when conversion fails
#
# The resulting object o must be orderable and convertible to a string for display and certain outputs (like csv).

## minimalist 'any' type
anytype = lambda r='': str(r)
anytype.__name__ = ''

class date:
    'simple wrapper around datetime so it can be created from dateutil str or numeric input as time_t'
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

    def __str__(self):
        'always use ISO8601'
        return self.dt.strftime('%Y-%m-%d %H:%M:%S')

    def __lt__(self, a):
        return self.dt < a.dt


def detectType(v):
    'auto-detect types in this order of preference: int float date str'
    def tryType(T, v):
        try:
            v = T(v)
            return T
        except:
            return None

    return tryType(int, v) or tryType(float, v) or tryType(date, v) or str


typemap = {
    int: '#',
    str: '$',
    float: '%',
    date: '@',
    anytype: ' ',
}

windowWidth = None
windowHeight = None

def join_sheetnames(*sheetnames):
    return options.SubsheetSep.join(str(x) for x in sheetnames)

def error(s):
    'scripty sugar function to just raise, needed for lambda and eval'
    raise Exception(s)

def status(s):
    'scripty sugar function for status'
    return vd().status(s)

def moveListItem(L, fromidx, toidx):
    r = L.pop(fromidx)
    L.insert(toidx, r)
    return toidx

def enumPivot(L, pivotIdx):
    'like enumerate() but starts after pivotIdx and wraps around to end at pivotIdx'
    rng = range(pivotIdx+1, len(L))
    rng2 = range(0, pivotIdx+1)
    for i in itertools.chain(rng, rng2):
        yield i, L[i]


# VisiData singleton contains all sheets
@functools.lru_cache()
def vd():
    return VisiData()

def exceptionCaught(status=True):
    return vd().exceptionCaught(status)

# A .. Z AA AB ...
defaultColNames = list(itertools.chain(string.ascii_uppercase, [''.join(i) for i in itertools.product(string.ascii_uppercase, repeat=2)]))

class VisiData:
    allPrefixes = 'g'

    def __init__(self):
        self.sheets = []
        self.statusHistory = []
        self._status = [__version__]  # statuses shown until next action
        self.lastErrors = []
        self.lastRegex = None
        self.lastInputs = collections.defaultdict(collections.OrderedDict)  # [input_type] -> prevInputs
        self.cmdhistory = []  # list of [keystrokes, start_time, end_time, thread, notes]
        self.keystrokes = ''
        self.ticks = 0
        self.inInput = False
        self.tasks = []

    def status(self, s):
        strs = str(s)
        self._status.append(strs)
        self.statusHistory.insert(0, strs)
        del self.statusHistory[100:]  # keep most recent 100 only
        return s

    def editText(self, y, x, w, **kwargs):
        v = editText(self.scr, y, x, w, **kwargs)
        self.status('"%s"' % v)
        return v

    def getkeystroke(self):
        k = None
        if [t for t in self.tasks if t.thread.is_alive()]:
            self.ticks += 1
        else:
            self.ticks = 0
        try:
            k = self.scr.get_wch()
            self.drawRightStatus()
        except Exception:
            return ''  # curses timeout

        if isinstance(k, str):
            if ord(k) >= 32:
                return k
            k = ord(k)
        return curses.keyname(k).decode('utf-8')

    def searchRegex(self, sheet, regex=None, columns=[], backward=False, moveCursor=False):
        'sets row index if moveCursor; otherwise returns list of row indexes'

        def columnsMatch(sheet, row, columns, func):
            for c in columns:
                m = func(c.getDisplayValue(row))
                if m:
                    return True
            return False

        if regex:
            r = re.compile(regex, re.IGNORECASE)
            if r:
                self.lastRegex = r
            else:
                error('regex error')

        if not columns:
            error('no columns')

        if not self.lastRegex:
            error('no regex')

        if backward:
            rng = range(sheet.cursorRowIndex-1, -1, -1)
            rng2 = range(sheet.nRows-1, sheet.cursorRowIndex-1, -1)
        else:
            rng = range(sheet.cursorRowIndex+1, sheet.nRows)
            rng2 = range(0, sheet.cursorRowIndex+1)

        matchingRowIndexes = []

        for r in rng:
            if columnsMatch(sheet, sheet.rows[r], columns, self.lastRegex.search):
                if moveCursor:
                    sheet.cursorRowIndex = r
                    return r
                matchingRowIndexes.append(r)

        for r in rng2:
            if columnsMatch(sheet, sheet.rows[r], columns, self.lastRegex.search):
                if moveCursor:
                    sheet.cursorRowIndex = r
                    status('search wrapped')
                    return r
                matchingRowIndexes.append(r)

        status('%s matches for /%s/' % (len(matchingRowIndexes), self.lastRegex.pattern))

        return matchingRowIndexes

    def exceptionCaught(self, status=True):
        import traceback
        self.lastErrors.append(traceback.format_exc().strip())
        self.lastErrors = self.lastErrors[-10:]  # keep most recent
        if status:
            return self.status(self.lastErrors[-1].splitlines()[-1])
        if options.debug:
            raise

    def drawLeftStatus(self, vs):
        'draws sheet info on last line, including previous status messages, which are then cleared.'
        attr = colors[options.c_StatusLine]
        statusstr = options.SheetNameFmt % vs.name + options.ch_StatusSep.join(self._status)
        try:
            draw_clip(self.scr, windowHeight-1, 0, statusstr, attr, windowWidth)
        except Exception as e:
            self.exceptionCaught()

    def drawRightStatus(self):
        try:
            spinny = options.ch_spinny
            sheet = self.sheets[0]
            if sheet.progressMade == sheet.progressTotal:
                pctLoaded = 'rows'
            else:
                pctLoaded = ' %2d%%' % sheet.progressPct
            rstatus = '%s %9d %s' % (self.keystrokes, sheet.nRows, pctLoaded)
            draw_clip(self.scr, windowHeight-1, windowWidth-len(rstatus)-2, rstatus, colors[options.c_StatusLine])
            curses.doupdate()
        except Exception as e:
            self.exceptionCaught()

    def run(self, scr):
        global windowHeight, windowWidth, sheet
        windowHeight, windowWidth = scr.getmaxyx()
        scr.timeout(int(options.timeout_ms))
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

                self._status = []
                self.keystrokes += keystroke
            self.drawRightStatus()  # visible for commands that wait for input

            if keystroke in self.allPrefixes:
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
            else:
                sheet.exec_command(g_globals, self.keystrokes)

            for i, task in enumerate(self.tasks):
                if not task.endTime and not task.thread.is_alive():
                    task.endTime = time.process_time()
                    task.status += 'ended'

            sheet.checkCursor()

    def replace(self, vs):
        'replace top sheet with the given sheet vs'
        self.sheets.pop(0)
        return self.push(vs)

    def push(self, vs):
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
    def __init__(self, name, *sources, columns=None):
        self.name = name
        self.sources = sources

        self.rows = []           # list of opaque row objects
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorVisibleColIndex = 0  # index of cursor into self.visibleCols

        self.topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftVisibleColIndex = 0    # cursorVisibleColIndex of leftmost column

        # as computed during draw()
        self.rowLayout = {}      # [rowidx] -> y
        self.visibleColLayout = {}      # [vcolidx] -> (x, w)

        # all columns in display order
        self.columns = columns or []        # list of Column objects
        self.nKeys = 0           # self.columns[:nKeys] are all pinned to the left and matched on join

        # commands specific to this sheet
        self.commands = collections.OrderedDict()

        self.filetype = None
        self._selectedRows = {}  # id(row) -> row

        # for progress bar
        self.progressMade = 0
        self.progressTotal = 0

    def command(self, keystrokes, execstr, helpstr):
        self.commands[keystrokes] = (keystrokes, helpstr, execstr)

    def searchRegex(self, *args, **kwargs):
        return self.vd.searchRegex(self, *args, **kwargs)

    def searchColumnNameRegex(self, colregex):
        for i, c in enumPivot(self.visibleCols, self.cursorVisibleColIndex):
            if re.search(colregex, c.name):
                self.cursorVisibleColIndex = i
                return

    def reload(self):  # default reloader looks for .loader attr
        if self.loader:
            self.loader()
        else:
            status('no reloader')

    def copy(self, suffix="'"):
        c = copy.copy(self)
        c.name += suffix
        c.topRowIndex = c.cursorRowIndex = 0
        c.columns = copy.deepcopy(self.columns)
        return c

    def __repr__(self):
        return self.name

    def exec_command(self, vdglobals, keystrokes):
        cmd = self.commands.get(keystrokes)
        if not cmd:
            cmd = base_commands.get(keystrokes)
        if not cmd:
            status('no command for "%s"' % (keystrokes))
            return

        # handy globals for use by commands
        self.vd = vd()
        self.sheet = self
        locs = LazyMap(dir(self), lambda k,s=self: getattr(s, k), lambda k,v,s=self: setattr(s, k, v))
        _, _, execstr = cmd
        try:
            exec(execstr, vdglobals, locs)
        except EscapeException as e:  # user aborted
            self.vd.status('EscapeException ' + ''.join(e.args[0:]))
        except Exception:
            self.vd.exceptionCaught()
#            self.vd.status(sheet.commands[self.keystrokes].execstr)


    def clipdraw(self, y, x, s, attr, w):
        return draw_clip(self.scr, y, x, s, attr, w)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name.replace(' ', '_')

    @property
    def source(self):
        if not self.sources:
            return None
        else:
            assert len(self.sources) == 1, len(self.sources)
            return self.sources[0]

    @property
    def progressPct(self):
        return int(sheet.progressMade*100/sheet.progressTotal)

    @property
    def nVisibleRows(self):
        return self.windowHeight-2

    @property
    def cursorCol(self):
        return self.visibleCols[self.cursorVisibleColIndex]

    @property
    def cursorRow(self):
        return self.rows[self.cursorRowIndex]

    @property
    def visibleRows(self):  # onscreen rows
        return self.rows[self.topRowIndex:self.topRowIndex+self.nVisibleRows]

    @property
    def visibleCols(self):  # non-hidden cols
        return [c for c in self.columns if not c.hidden]

    @property
    def cursorColIndex(self):
        return self.columns.index(self.cursorCol)

    @property
    def keyCols(self):
        return self.columns[:self.nKeys]

    @property
    def keyColNames(self):
        return options.ch_KeySep.join(c.name for c in self.keyCols)

    @property
    def cursorValue(self):
        return self.cellValue(self.cursorRowIndex, self.cursorColIndex)

    @property
    def statusLine(self):
        return 'row %s/%s col %d/%d' % (self.cursorRowIndex, self.nRows, self.cursorColIndex, self.nCols)

    @property
    def nRows(self):
        return len(self.rows)

    @property
    def nCols(self):
        return len(self.columns)

    @property
    def nVisibleCols(self):
        return len(self.visibleCols)

## selection code
    def isSelected(self, r):
        return id(r) in self._selectedRows

    def toggle(self, rows):
        for r in rows:
            if id(r) in self._selectedRows:
                del self._selectedRows[id(r)]
            else:
                self._selectedRows[id(r)] = r

    def select(self, rows):
        rows = list(rows)
        before = len(self._selectedRows)
        self._selectedRows.update(dict((id(r), r) for r in rows))
        status('selected %s%s rows' % (len(self._selectedRows)-before, ' more' if before > 0 else ''))

    def unselect(self, rows):
        rows = list(rows)
        before = len(self._selectedRows)
        for r in rows:
            if id(r) in self._selectedRows:
                del self._selectedRows[id(r)]
        status('unselected %s/%s rows' % (before-len(self._selectedRows), len(rows)))

    def selectByIdx(self, rowIdxs):
        self.select(self.rows[i] for i in rowIdxs)

    def unselectByIdx(self, rowIdxs):
        self.unselect(self.rows[i] for i in rowIdxs)

    def selectBy(self, func):
        self.select(r for r in self.rows if func(r))

    @property
    def selectedRows(self):
        'returns a list of selected rows in sheet order'
        return [r for r in self.rows if id(r) in self._selectedRows]

## end selection code

    def moveVisibleCol(self, fromVisColIdx, toVisColIdx):
        fromColIdx = self.columns.index(self.visibleCols[fromVisColIdx])
        toColIdx = self.columns.index(self.visibleCols[toVisColIdx])
        moveListItem(self.columns, fromColIdx, toColIdx)
        return toVisColIdx

    def cursorDown(self, n):
        self.cursorRowIndex += n

    def cursorRight(self, n):
        self.cursorVisibleColIndex += n

    def cellValue(self, rownum, col):
        if not isinstance(col, Column):
            # assume it's the column number
            col = self.columns[col]
        return col.getValue(self.rows[rownum])

    def addColumn(self, col, index=None):
        if index is None:
            index = len(self.columns)
        if col:
            self.columns.insert(index, col)

    def toggleKeyColumn(self, colidx):
        if colidx >= self.nKeys: # if not a key, add it
            moveListItem(self.columns, colidx, self.nKeys)
            self.nKeys += 1
        else:  # otherwise move it after the last key
            self.nKeys -= 1
            moveListItem(self.columns, colidx, self.nKeys)

    def skipDown(self):
        pv = self.cursorValue
        for i in range(self.cursorRowIndex+1, self.nRows):
            if self.cellValue(i, self.cursorColIndex) != pv:
                self.cursorRowIndex = i
                return

        status('no different value down this column')

    def skipUp(self):
        pv = self.cursorValue
        for i in range(self.cursorRowIndex, -1, -1):
            if self.cellValue(i, self.cursorColIndex) != pv:
                self.cursorRowIndex = i
                return

        status('no different value up this column')

    def checkCursor(self):
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
        elif self.topRowIndex > self.nRows:
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
                if self.leftVisibleColIndex == self.cursorVisibleColIndex: # not much more we can do
                    break
                self.calcColLayout()
                if self.cursorVisibleColIndex < min(self.visibleColLayout.keys()):
                    self.leftVisibleColIndex -= 1
                    continue
                elif self.cursorVisibleColIndex > max(self.visibleColLayout.keys()):
                    self.leftVisibleColIndex += 1
                    continue

                cur_x, cur_w = self.visibleColLayout[self.cursorVisibleColIndex]
                left_x, left_w = self.visibleColLayout[self.leftVisibleColIndex]
                if cur_x+cur_w < self.windowWidth: # current columns fit entirely on screen
                    break
                self.leftVisibleColIndex += 1

    def calcColLayout(self):
        self.visibleColLayout = {}
        x = 0
        for vcolidx in range(0, self.nVisibleCols):
            col = self.visibleCols[vcolidx]
            if col.width is None:
                col.width = col.getMaxWidth(self.visibleRows)+len(options.ch_LeftMore)+len(options.ch_RightMore)
            if vcolidx < self.nKeys or vcolidx >= self.leftVisibleColIndex:  # visible columns
                self.visibleColLayout[vcolidx] = (x, min(col.width, self.windowWidth-x))
                x += col.width+len(options.ch_ColumnSep)
            if x > self.windowWidth-1:
                break

    def drawColHeader(self, vcolidx):
        # choose attribute to highlight column header
        if vcolidx == self.cursorVisibleColIndex:  # cursor is at this column
            hdrattr = colors[options.c_CurHdr]
        elif vcolidx < self.nKeys:
            hdrattr = colors[options.c_KeyCols]
        else:
            hdrattr = colors[options.c_Header]

        col = self.visibleCols[vcolidx]
        x, colwidth = self.visibleColLayout[vcolidx]

        # ANameTC
        T = typemap.get(col.type, '?')
        N = ' ' + (col.name or defaultColNames[vcolidx])  # save room at front for LeftMore
        if len(N) > colwidth-1:
            N = N[:colwidth-len(options.ch_Ellipsis)] + options.ch_Ellipsis
        self.clipdraw(0, x, N, hdrattr, colwidth)
        self.clipdraw(0, x+colwidth-len(T), T, hdrattr, len(T))

        if vcolidx == self.leftVisibleColIndex and vcolidx > self.nKeys:
            A = options.ch_LeftMore
            self.scr.addstr(0, x, A, colors[options.c_ColumnSep])

        C = options.ch_ColumnSep
        if x+colwidth+len(C) < self.windowWidth:
            self.scr.addstr(0, x+colwidth, C, colors[options.c_ColumnSep])


    def draw(self, scr):
        numHeaderRows = 1
        self.scr = scr  # for clipdraw convenience
        scr.erase()  # clear screen before every re-draw

        self.windowHeight, self.windowWidth = scr.getmaxyx()
        sepchars = options.ch_ColumnSep
        if not self.columns:
            return

        self.rowLayout = {}
        self.calcColLayout()
        for vcolidx, colinfo in sorted(self.visibleColLayout.items()):
            x, colwidth = colinfo
            if x < self.windowWidth:  # only draw inside window
                self.drawColHeader(vcolidx)

                y = numHeaderRows
                for rowidx in range(0, self.nVisibleRows):
                    if self.topRowIndex + rowidx >= self.nRows:
                        break

                    self.rowLayout[self.topRowIndex+rowidx] = y

                    row = self.rows[self.topRowIndex + rowidx]

                    if self.topRowIndex + rowidx == self.cursorRowIndex:  # cursor at this row
                        attr = colors[options.c_CurRow]
                    elif vcolidx < self.nKeys:
                        attr = colors[options.c_KeyCols]
                    else:
                        attr = colors[options.c_default]

                    if self.isSelected(row):
                        attr |= colors[options.c_SelectedRow]

                    if vcolidx == self.cursorVisibleColIndex:  # cursor is at this column
                        attr |= colors[options.c_CurCol]

                    cellval = self.visibleCols[vcolidx].getDisplayValue(row, colwidth-1)
                    self.clipdraw(y, x, options.ch_ColumnFiller + cellval, attr, colwidth)

                    if isinstance(cellval, CalcErrorStr):
                        self.clipdraw(y, x+colwidth-len(options.ch_Error), options.ch_Error, colors[options.c_Error], len(options.ch_Error))
                    elif isinstance(cellval, WrongTypeStr):
                        self.clipdraw(y, x+colwidth-len(options.ch_WrongType), options.ch_WrongType, colors[options.c_WrongType], len(options.ch_WrongType))

                    if x+colwidth+len(sepchars) <= self.windowWidth:
                       self.scr.addstr(y, x+colwidth, sepchars, attr or colors[options.c_ColumnSep])

                    y += 1

        if vcolidx+1 < self.nVisibleCols:
            self.scr.addstr(0, self.windowWidth-1, options.ch_RightMore, colors[options.c_ColumnSep])

    def editCell(self, vcolidx=None):
        if options.readonly:
            status('readonly mode')
            return
        if vcolidx is None:
            vcolidx = self.cursorVisibleColIndex
        x, w = self.visibleColLayout[vcolidx]
        y = self.rowLayout[self.cursorRowIndex]

        currentValue = self.cellValue(self.cursorRowIndex, vcolidx)
        r = vd().editText(y, x, w, value=currentValue, fillchar=options.ch_EditPadChar)
        return self.visibleCols[vcolidx].type(r)  # convert input to column type


class WrongTypeStr(str):
    'str wrapper with original str-ified contents to indicate that the type conversion failed'
    pass

class CalcErrorStr(str):
    'str wrapper (possibly with error message) to indicate that getValue failed'
    pass

class Column:
    def __init__(self, name, type=anytype, getter=lambda r: r, setter=None, width=None):
        self.name = name    # use property setter from the get-go to strip spaces
        self.type = type
        self.getter = getter
        self.setter = setter
        self.width = width  # == 0 if hidden, None if auto-compute next time
        self.expr = None    # Python string expression if computed column
        self.fmtstr = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = str(name).replace(' ', '_')

    def deduceFmtstr(self):
        if self.fmtstr is not None: return self.fmtstr
        elif self.type is int: return '%d'
        elif self.type is float: return '%.02f'
        else: return '%s'

    @property
    def hidden(self):
        return self.width == 0

    def nEmpty(self, rows):
        vals = self.values(rows)
        return sum(1 for v in vals if v == '' or v == None)

    def values(self, rows):
        return [self.getValue(r) for r in rows]

    def getValue(self, row):
        'returns a properly-typed value, or a default value if the conversion fails, or reraises the exception if the getter fails'
        try:
            v = self.getter(row)
        except Exception:
            exceptionCaught(status=False)
            return CalcErrorStr(self.type())

        try:
            return self.type(v)  # convert type on-the-fly
        except Exception:
            exceptionCaught(status=False)
            return self.type()  # return a suitable value for this type

    def getDisplayValue(self, row, width=None):
        try:
            cellval = self.getter(row)
        except Exception as e:
            exceptionCaught(status=False)
            return CalcErrorStr(options.ch_FunctionError)

        if cellval is None:
            return options.ch_VisibleNone

        if isinstance(cellval, bytes):
            cellval = cellval.decode(options.encoding)

        try:
            cellval = self.deduceFmtstr() % self.type(cellval)  # convert type on-the-fly
            if width and self.type in (int, float): cellval = cellval.rjust(width-1)
        except Exception as e:
            exceptionCaught(status=False)
            cellval = WrongTypeStr(str(cellval))

        return cellval

    def setValue(self, row, value):
        if self.setter:
            self.setter(row, value)
        else:
            error('column cannot be changed')

    def getMaxWidth(self, rows):
        w = 0
        if len(rows) > 0:
            w = max(max(len(self.getDisplayValue(r)) for r in rows), len(self.name))+2
        return max(w, len(self.name))


# ---- Column makers

def ColumnAttr(attrname, type=anytype):
    'a getattr/setattr column on the row Python object'
    return Column(attrname, type=type,
            getter=lambda r,b=attrname: getattr(r,b),
            setter=lambda r,v,b=attrname: setattr(r,b,v))

def ColumnItem(attrname, itemkey, **kwargs):
    'a getitem/setitem column on the row Python object'
    def setitem(r, i, v):  # function needed for use in lambda
        r[i] = v

    return Column(attrname,
            getter=lambda r,i=itemkey: r[i],
            setter=lambda r,v,i=itemkey,f=setitem: f(r,i,v),
            **kwargs)

def ArrayNamedColumns(columns):
    'columns is a list of column names, mapping to r[0]..r[n]'
    return [ColumnItem(colname, i) for i, colname in enumerate(columns)]

def ArrayColumns(ncols):
    'columns is a list of column names, mapping to r[0]..r[n]'
    return [ColumnItem('', i, width=8) for i in range(ncols)]

def DictKeyColumns(d):
    return [ColumnItem(k, k, type=detectType(d[k])) for k in d]

def SubrowColumn(origcol, subrowidx, **kwargs):
    return Column(origcol.name, origcol.type,
            getter=lambda r,i=subrowidx,f=origcol.getter: r[i] and f(r[i]) or None,
            setter=lambda r,v,i=subrowidx,f=origcol.setter: r[i] and f(r[i], v) or None,
            width=origcol.width,
            **kwargs)

###

def input(prompt, type='', **kwargs):
    if type:
        ret = _inputLine(prompt, history=list(vd().lastInputs[type].keys()), **kwargs)
        vd().lastInputs[type][ret] = ret
    else:
        return _inputLine(prompt, **kwargs)
    return ret

def _inputLine(prompt, **kwargs):
    'add a prompt to the bottom of the screen and get a line of input from the user'
    scr = vd().scr
    windowHeight, windowWidth = scr.getmaxyx()
    scr.addstr(windowHeight-1, 0, prompt)
    vd().inInput = True
    ret = vd().editText(windowHeight-1, len(prompt), windowWidth-len(prompt)-8, attr=colors[options.c_EditCell], unprintablechar=options.ch_Unprintable, **kwargs)
    vd().inInput = False
    return ret

def saveSheet(vs, fn):
    basename, ext = os.path.splitext(fn)
    funcname = 'save_' + ext[1:]
    if funcname not in g_globals:
        funcname = 'save_tsv'
    g_globals.get(funcname)(vs, fn)
    status('saved to ' + fn)


def draw_clip(scr, y, x, s, attr=curses.A_NORMAL, w=None):
    'Draw string s at (y,x)-(y,x+w), clipping with ellipsis char'
    s = s.replace('\n', options.ch_Newline)

    _, windowWidth = scr.getmaxyx()
    try:
        if w is None:
            w = windowWidth-1
        w = min(w, windowWidth-x-1)
        if w == 0:  # no room anyway
            return

        # convert to string just before drawing
        s = str(s)
        if len(s) > w:
            scr.addstr(y, x, s[:w-1] + options.ch_Ellipsis, attr)
        else:
            scr.addstr(y, x, s, attr)
            if len(s) < w:
                scr.addstr(y, x+len(s), options.ch_ColumnFiller*(w-len(s)), attr)
    except Exception as e:
        raise type(e)('%s [clip_draw y=%s x=%s len(s)=%s w=%s]' % (e, y, x, len(s), w)
                ).with_traceback(sys.exc_info()[2])


## Built-in sheets
class HelpSheet(Sheet):
    def reload(self):
        self.rows = []
        for i, src in enumerate(self.sources):
            self.rows.extend((i, v) for v in src.values())
        self.columns = [SubrowColumn(ColumnItem('keystrokes', 0), 1),
                        SubrowColumn(ColumnItem('action', 1), 1),
                        Column('with_g_prefix', str, lambda r,self=self: self.sources[r[0]].get('g' + r[1][0], (None,'-'))[1]),
                        SubrowColumn(ColumnItem('execstr', 2, width=0), 1)
                ]


## text viewer and dir browser
class TextSheet(Sheet):
    'views a string (one line per row) or a list of strings'
    def reload(self):
        self.columns = [Column(self.name, str)]
        if isinstance(self.source, list):
            self.rows = []
            for x in self.source:
                # copy so modifications don't change 'original'; also one iteration through generator
                self.rows.append(x)
        elif isinstance(self.source, str):
            self.rows = self.source.splitlines()
        else:
            error('unknown text type ' + str(type(self.source)))

class DirSheet(Sheet):
    'browses a directory, ENTER dives into the file'
    def reload(self):
        self.rows = [(p, p.stat()) for p in self.source.iterdir()]  #  if not p.name.startswith('.')]
        self.command('^J', 'vd.push(openSource(cursorRow[0]))', 'open file')  # path, filename
        self.columns = [Column('filename', str, lambda r: r[0].name),
                      Column('type', str, lambda r: r[0].is_dir() and '/' or r[0].suffix),
                      Column('size', int, lambda r: r[1].st_size),
                      Column('mtime', date, lambda r: r[1].st_mtime)]

#### options management
class OptionsObject:
    'simple class to get the option value from base_options'
    def __init__(self, d):
        self._opts = d
    def __getattr__(self, k):
        name, value, default, helpstr = self._opts[k]
        return value
    def __setitem__(self, k, v):
        if k not in self._opts:
            raise Exception('no such option "%s"' % k)
        self._opts[k][1] = v

options = OptionsObject(base_options)

class OptionsSheet(Sheet):
    def reload(self):
        self.rows = list(self.source.values())
        self.columns = ArrayNamedColumns('option value default description'.split())
        self.command('^J', 'cursorRow[1] = editCell(1)', 'edit this option')
        self.command('e', 'cursorRow[1] = editCell(1)', 'edit this option')


# define @async for potentially long-running functions
#   when function is called, instead launches a thread
#   adds a row to cmdhistory
#   ENTER on that row pushes a profile of the thread

class Task:
    def __init__(self, name):
        self.name = name
        self.startTime = time.process_time()
        self.endTime = None
        self.status = ''
        self.thread = None
        self.profileResults = None

    def start(self, func, *args, **kwargs):
        self.thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        self.thread.start()

    @property
    def elapsed_s(self):
        return (self.endTime or time.process_time())-self.startTime

#execThread(self.keystrokes, sheet.exec_command, g_globals, self.keystrokes, row)
def async(func):
    def execThread(*args, **kwargs):
        t = Task(func.__name__ + ' ' + ','.join(str(x) for x in args))
        if bool(options.profile):
            t.start(thread_profileCode, t, func, *args, **kwargs)
        else:
            t.start(try_func, t, func, *args, **kwargs)
        vd().tasks.append(t)
        return t
    return execThread

def try_func(task, func, *args, **kwargs):
    try:
        ret = func(*args, **kwargs)
        return ret
    except EscapeException as e:  # user aborted
        task.status += ' cancelled by user'
        status("%s cancelled" % task.name)
    except Exception as e:
        task.status += status('%s: %s' % (type(e).__name__, ' '.join(str(x) for x in e.args)))
        exceptionCaught()

def thread_profileCode(task, func, *args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    ret = try_func(task, func, *args, **kwargs)
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    task.profileResults = s.getvalue()
    return ret


# from https://gist.github.com/liuw/2407154
def ctype_async_raise(thread_obj, exception):
    def dict_find(D, value):
        for k, v in D.items():
            if v is value:
                return k

        raise ValueError("no such value in dict")

    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(dict_find(threading._active, thread_obj)),
                                               ctypes.py_object(exception))
    status('sent exception to %s' % thread_obj.name)

command('^C', 'ctype_async_raise(vd.tasks[-1].thread, EscapeException)', 'cancel most recent task')
command('^T', 'vd.push(TasksSheet("task_history", vd.tasks))', 'push task history sheet')

# each row is a Task object
class TasksSheet(Sheet):
    def reload(self):
        self.command('^C', 'ctype_async_raise(cursorRow.thread, EscapeException)', 'cancel this action')
        self.command(ENTER, 'vd.push(ProfileSheet(cursorRow))', 'push profile sheet for this action')
        self.columns = [
            ColumnAttr('name'),
            ColumnAttr('elapsed_s', type=float),
            ColumnAttr('status'),
        ]
        self.rows = vd().tasks

def ProfileSheet(task):
    return TextSheet(task.name + '_profile', task.profileResults)

#### enable external addons
def open_py(p):
    contents = p.read_text()
    exec(contents, g_globals)
    status('executed %s' % p)

def open_txt(p):
    fp = p.open_text()
    if '\t' in next(fp):
        return open_tsv(p)  # TSV often have .txt extension
    return TextSheet(p.name, fp)  # leaks file handle

def open_tsv(p):
    vs = Sheet(p.name, p)
    vs.loader = lambda vs=vs: load_tsv(vs)
    return vs

@async
def load_tsv(vs):
    'parses contents and populates vs'
    header_lines = int(options.headerlines)
    vs.rows = []

    with vs.source.open_text() as fp:
        i = 0
        while i < (header_lines or 1):
            L = next(fp)
            if L:
                vs.rows.append(L.split('\t'))
                i += 1

        if header_lines == 0:
            vs.columns = ArrayColumns(len(vs.rows[0]))
        else:
            # columns ideally reflect the max number of fields over all rows
            # but that's a lot of work for a large dataset
            vs.columns = ArrayNamedColumns('\\n'.join(x) for x in zip(*vs.rows[:header_lines]))
            vs.rows = vs.rows[header_lines:]

        vs.progressMade = 0
        vs.progressTotal = vs.source.filesize
        for L in fp:
            L = L[:-1]
            if L:
                vs.rows.append(L.split('\t'))
            vs.progressMade += len(L)

    vs.progressMade = 0
    vs.progressTotal = 0

    status('loaded')

    return vs

def save_tsv(vs, fn):
    with open(fn, 'w', encoding=options.encoding, errors=options.encoding_errors) as fp:
        colhdr = '\t'.join(col.name for col in vs.visibleCols) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)
        for r in vs.rows:
            fp.write('\t'.join(col.getDisplayValue(r) for col in vs.visibleCols) + '\n')

### curses helpers

def editText(scr, y, x, w, attr=curses.A_NORMAL, value='', fillchar=' ', unprintablechar='.', completions=[], history=[]):
    def until(func):
        ret = None
        while not ret:
            ret = func()

        return ret

    def splice(v, i, s):  # splices s into the string v at i (v[i] = s[0])
        return v if i < 0 else v[:i] + s + v[i:]

    def clean(s):
        return ''.join(c if c.isprintable() else ('<%04X>' % ord(c)) for c in str(s))

    def delchar(s, i, remove=1):
        return s[:i] + s[i+remove:]

    def complete(v, comps, cidx):
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
        dispval = clean(v)
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
        elif ch == '^C' or ch == '^[':             raise EscapeException(ch)
        elif ch == '^D' or ch == 'KEY_DC':         v = delchar(v, i)
        elif ch == '^E' or ch == 'KEY_END':        i = len(v)
        elif ch == '^F' or ch == 'KEY_RIGHT':      i += 1
        elif ch in ('^H', 'KEY_BACKSPACE', '^?'):  i -= 1 if i > 0 else 0; v = delchar(v, i)
        elif ch == '^I':                           comps_idx += 1; v = complete(v[:i], completions, comps_idx)
        elif ch == 'KEY_BTAB':                     comps_idx -= 1; v = complete(v[:i], completions, comps_idx)
        elif ch == '^J':                           break  # ENTER
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


colors = collections.defaultdict(lambda: curses.A_NORMAL, {
    'bold': curses.A_BOLD,
    'reverse': curses.A_REVERSE,
    'normal': curses.A_NORMAL,
})


nextColorPair = 1
def setupcolors(stdscr, f, *args):
    def makeColor(fg, bg):
        global nextColorPair
        if curses.has_colors():
            curses.init_pair(nextColorPair, fg, bg)
            c = curses.color_pair(nextColorPair)
            nextColorPair += 1
        else:
            c = curses.A_NORMAL

        return c

    curses.raw()    # get control keys instead of signals
    curses.meta(1)  # allow "8-bit chars"
#    curses.mousemask(curses.ALL_MOUSE_EVENTS)  # enable mouse events

    colors['red'] = curses.A_BOLD | makeColor(curses.COLOR_RED, curses.COLOR_BLACK)
    colors['blue'] = curses.A_BOLD | makeColor(curses.COLOR_BLUE, curses.COLOR_BLACK)
    colors['green'] = curses.A_BOLD | makeColor(curses.COLOR_GREEN, curses.COLOR_BLACK)
    colors['brown'] = makeColor(curses.COLOR_YELLOW, curses.COLOR_BLACK)
    colors['yellow'] = curses.A_BOLD | colors['brown']
    colors['cyan'] = makeColor(curses.COLOR_CYAN, curses.COLOR_BLACK)
    colors['magenta'] = makeColor(curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    colors['red_bg'] = makeColor(curses.COLOR_WHITE, curses.COLOR_RED)
    colors['blue_bg'] = makeColor(curses.COLOR_WHITE, curses.COLOR_BLUE)
    colors['green_bg'] = makeColor(curses.COLOR_BLACK, curses.COLOR_GREEN)
    colors['brown_bg'] = colors['yellow_bg'] = makeColor(curses.COLOR_BLACK, curses.COLOR_YELLOW)
    colors['cyan_bg'] = makeColor(curses.COLOR_BLACK, curses.COLOR_CYAN)
    colors['magenta_bg'] = makeColor(curses.COLOR_BLACK, curses.COLOR_MAGENTA)

    return f(stdscr, *args)


def wrapper(f, *args):
    return curses.wrapper(setupcolors, f, *args)

### external interface

class Path:
    '''Modeled after pathlib.Path.'''
    def __init__(self, fqpn):
        self.fqpn = fqpn
        self.name = os.path.split(fqpn)[-1]
        self.suffix = os.path.splitext(self.name)[1][1:]

    def open_text(self):
        return open(self.resolve(), encoding=options.encoding, errors=options.encoding_errors)

    def read_text(self):
        with self.open_text() as fp:
            return fp.read()

    def read_bytes(self):
        with open(self.resolve(), 'rb') as fp:
            return fp.read()

    def is_dir(self):
        return os.path.isdir(self.resolve())

    def iterdir(self):
        return [self.parent] + [Path(os.path.join(self.fqpn, f)) for f in os.listdir(self.resolve())]

    def stat(self):
        return os.stat(self.resolve())

    def resolve(self):
        return os.path.expandvars(os.path.expanduser(self.fqpn))

    @property
    def parent(self):
        return Path(self.fqpn + "/..")

    @property
    def filesize(self):
        return self.stat().st_size

    def __str__(self):
        return self.fqpn


def openSource(p, filetype=None):
    'open a Path or a str (converts to Path or calls some TBD openUrl)'
    if isinstance(p, str):
        if '://' in p:
            vs = openUrl(p)
        else:
            return openSource(Path(p), filetype)  # convert to Path and recurse
    elif isinstance(p, Path):
        if filetype is None:
            filetype = p.suffix

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
    'main entry point to invoke curses mode'

    # reduce ESC timeout to 25ms. http://en.chys.info/2009/09/esdelay-ncurses/
    os.putenv('ESCDELAY', '25')

    ret = wrapper(curses_main, sheetlist)
    if ret:
        print(ret)

def curses_main(_scr, sheetlist=[]):
    for vs in sheetlist:
        vd().push(vs)  # first push does a reload
    return vd().run(_scr)

g_globals = globals()
def set_globals(g):
    global g_globals
    g_globals = g

if __name__ == '__main__':
    run(openSource(src) for src in sys.argv[1:])
