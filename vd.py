#!/usr/bin/python3

'VisiData: a curses interface for exploring and arranging tabular data'

__version__ = '0.28'
__author__ = 'Saul Pwanson <vd@saul.pw>'
__license__ = 'GPLv3'
__status__ = 'Development'

import os.path
import io
import datetime
import string
import collections
import functools
import codecs
import statistics
import curses
import curses.textpad
import re
import html.parser
import urllib.parse
import csv


default_options = {
    'csv_dialect': 'excel',
    'csv_delimiter': ',',
    'csv_quotechar': '"',

    'encoding': 'utf-8',
    'encoding_errors': 'surrogateescape',

    'VisibleNone': '',   # visible contents of a cell whose value was None
    'ColumnFiller': ' ',
    'ColumnSep': ' | ',  # chars between columns
    'Ellipsis': '…',
    'SubsheetSep': '~',
    'StatusSep': ' | ',
    'SheetNameFmt': '%s| ',  # before status line
    'FunctionError': '¿',    # when computation fails due to exception
    'HistogramChar': '*',

    # color scheme
    'c_default': 'normal',
    'c_Header': 'bold',
    'c_CurHdr': 'reverse',
    'c_CurRow': 'reverse',
    'c_CurCol': 'bold',
    'c_StatusLine': 'bold',
    'c_SelectedRow': 'green',
    'c_ColumnSep': 'blue',
    'c_EditCell': 'normal',
}

vd = None    # toplevel VisiData, contains all sheets
scr = None   # toplevel curses screen
sheet = None # current sheet

windowWidth = None
windowHeight = None

defaultColNames = string.ascii_uppercase

colors = {
    'bold': curses.A_BOLD,
    'reverse': curses.A_REVERSE,
    'normal': curses.A_NORMAL,
}

class attrdict(object):
    def __init__(self, d):
        self.__dict__ = d

options = attrdict(default_options)

class VException(Exception):
    pass

class ChangeCommandSet(VException):
    def __init__(self, commands, mode):
        self.commands = commands
        self.mode = mode

def ctrl(ch):
    return ord(ch) & 31  # convert from 'a' to ^A keycode

ENTER = ctrl('j')

base_commands = {
    # pop current sheet off the sheet stack
    ord('q'): 'vd.sheets.pop(0)',

    # standard movement with arrow keys
    curses.KEY_LEFT:  'sheet.moveCursorRight(-1)',
    curses.KEY_DOWN:  'sheet.moveCursorDown(+1)',
    curses.KEY_UP:    'sheet.moveCursorDown(-1)',
    curses.KEY_RIGHT: 'sheet.moveCursorRight(+1)',
    curses.KEY_NPAGE: 'sheet.moveCursorDown(sheet.nVisibleRows); sheet.topRowIndex += sheet.nVisibleRows',
    curses.KEY_PPAGE: 'sheet.moveCursorDown(-sheet.nVisibleRows); sheet.topRowIndex -= sheet.nVisibleRows',
    curses.KEY_HOME:  'sheet.topRowIndex = sheet.cursorRowIndex = 0',
    curses.KEY_END:   'sheet.cursorRowIndex = len(sheet.rows)-1',

    # move cursor with vi keys
    ord('h'): 'sheet.moveCursorRight(-1)',
    ord('j'): 'sheet.moveCursorDown(+1)',
    ord('k'): 'sheet.moveCursorDown(-1)',
    ord('l'): 'sheet.moveCursorRight(+1)',

    # reorder rows/columns with shift-movement
    ord('H'): 'sheet.cursorColIndex = moveListItem(sheet.columns, sheet.cursorColIndex, max(sheet.cursorColIndex-1, 0))',
    ord('J'): 'sheet.cursorRowIndex = moveListItem(sheet.rows, sheet.cursorRowIndex, min(sheet.cursorRowIndex+1, sheet.nRows-1))',
    ord('K'): 'sheet.cursorRowIndex = moveListItem(sheet.rows, sheet.cursorRowIndex, max(sheet.cursorRowIndex-1, 0))',
    ord('L'): 'sheet.cursorColIndex = moveListItem(sheet.columns, sheet.cursorColIndex, min(sheet.cursorColIndex+1, sheet.nCols))',

    # ^g/^p sheet status and status sheet
    ctrl('g'): 'vd.status(sheet.statusLine)',
    ctrl('p'): 'vd.status(vd.statusHistory[-1])',

    # t/m/b jumps to top/middle/bottom of screen
    ord('t'): 'sheet.topRowIndex = sheet.cursorRowIndex',
    ord('m'): 'sheet.topRowIndex = sheet.cursorRowIndex-int(sheet.nVisibleRows/2)',
    ord('b'): 'sheet.topRowIndex = sheet.cursorRowIndex-sheet.nVisibleRows+1',

    # </> skip up/down current column to next value
    ord('<'): 'sheet.skipUp()',
    ord('>'): 'sheet.skipDown()',

    # _ resets column width
    ord('_'): 'sheet.cursorCol.width = getMaxWidth(sheet.cursorCol, sheet.visibleRows)',

    # delete column
    ord('-'): 'sheet.columns.pop(sheet.cursorColIndex)',

    # retype as datetime/int/str/float
    ord('@'): 'sheet.convertType(sheet.cursorCol, datetime)',
    ord('#'): 'sheet.convertType(sheet.cursorCol, int)',
    ord('$'): 'sheet.convertType(sheet.cursorCol, str)',
    ord('%'): 'sheet.convertType(sheet.cursorCol, float)',

    # [/] sort asc/desc
    ord('['): 'sheet.rows = sorted(sheet.rows, key=sheet.cursorCol.getValue)',
    ord(']'): 'sheet.rows = sorted(sheet.rows, key=sheet.cursorCol.getValue, reverse=True)',

    # quit and print error sheet to terminal (in case error sheet itself is broken)
    ctrl('e'): 'g_args.debug = True; raise VException(vd.lastErrors[-1])',

    # other capital letters are new sheets
    ord('E'): 'if vd.lastErrors: createTextViewer("last_error", vd.lastErrors[-1])',
    ord('F'): 'createFreqTable(sheet, sheet.cursorCol)',

    # take this cell for header name
    ord('^'): 'sheet.cursorCol.name = sheet.cursorCol.getDisplayValue(sheet.cursorRow)',

    # delete current row
    ord('d'): 'sheet.rows.pop(sheet.cursorRowIndex)',

    # g = global mode
    ord('g'): 'raise ChangeCommandSet(global_commands, "g")',

    # meta sheets
    ord('S'): 'createListSheet("sheets", vd.sheets, "name nRows nCols cursorValue source".split())',
    ord('C'): 'createColumnSummary(sheet)',
    ord('O'): 'createDictSheet("options", options.__dict__)',

    # search this column via regex
    ord('/'): 'sheet.searchRegex(inputLine(prompt="/"), columns=[sheet.cursorCol], moveCursor=True)',
    ord('?'): 'sheet.searchRegex(inputLine(prompt="?"), columns=[sheet.cursorCol], backward=True, moveCursor=True)',
    ord('n'): 'sheet.searchRegex(columns=[sheet.cursorCol], moveCursor=True)',
    ord('p'): 'sheet.searchRegex(columns=[sheet.cursorCol], backward=True, moveCursor=True)',

    # select/unselect rows via regex
    ord(' '): 'sheet.toggle([sheet.cursorRow]); sheet.moveCursorDown(1)',
    ord('s'): 'sheet.select([sheet.cursorRow]); sheet.moveCursorDown(1)',
    ord('u'): 'sheet.unselect([sheet.cursorRow]); sheet.moveCursorDown(1)',

    ord('|'): 'sheet.select(sheet.rows[r] for r in sheet.searchRegex(inputLine(prompt="|"), columns=[sheet.cursorCol]))',
    ord('\\'): 'sheet.unselect(sheet.rows[r] for r in sheet.searchRegex(inputLine(prompt="\\\\"), columns=[sheet.cursorCol]))',

    # reload
    ord('R'): 'sheet.source.type = inputLine("change type to: ") or sheet.source.type',
    ctrl('r'): 'openSource(vd.sheets.pop(0).source); vd.status("reloaded")',

    # edit cell
    ord('e'): 'sheet.cursorCol.setValue(sheet.cursorRow, sheet.editCell(sheet.cursorColIndex) or sheet.cursorCol.getValue(sheet.cursorRow))',

    # save sheet
    ctrl('s'): 'saveSheet(sheet, inputLine("save to: "))',
}

sheet_specific_commands = {
    ('sheets', ENTER): 'vd.sheets.pop(0); moveListItem(vd.sheets, sheet.cursorRowIndex-1, 0)',
}

# when used with 'g' prefix
global_commands = {
    # quit all sheets (and therefore exit)
    ord('q'): 'vd.sheets = []',

    # go all the way to the left/down/up/right
    ord('h'): 'sheet.cursorColIndex = sheet.leftColIndex = 0',
    ord('k'): 'sheet.cursorRowIndex = sheet.topRowIndex = 0',
    ord('j'): 'sheet.cursorRowIndex = len(sheet.rows); sheet.topRowIndex = sheet.cursorRowIndex-sheet.nVisibleRows',
    ord('l'): 'sheet.cursorColIndex = sheet.leftColIndex = len(sheet.columns)-1',

    # throw rows/columns all the way to the left/down/up/right (without moving cursor)
    ord('H'): 'moveListItem(sheet.columns, sheet.cursorColIndex, 0)',
    ord('J'): 'moveListItem(sheet.rows, sheet.cursorRowIndex, sheet.nRows)',
    ord('K'): 'moveListItem(sheet.rows, sheet.cursorRowIndex, 0)',
    ord('L'): 'moveListItem(sheet.columns, sheet.cursorColIndex, sheet.nCols)',

    # resize all columns (alternately: resize this column according to all rows)
    ord('_'): 'for c in sheet.columns: c.width = getMaxWidth(c, sheet.visibleRows)',

    # column header name change
    ord('^'): 'for c in sheet.columns: c.name = c.getDisplayValue(sheet.cursorRow)',

    # all previous errors sheet
    ord('E'): 'createTextViewer("last_error", "\\n\\n".join(vd.lastErrors))',

    # search all columns
    ord('/'): 'sheet.searchRegex(inputLine(prompt="/"), moveCursor=True)',
    ord('?'): 'sheet.searchRegex(inputLine(prompt="?"), backward=True, moveCursor=True)',

    # first/last match
    ord('n'): 'sheet.cursorRowIndex = max(sheet.searchRegex())',
    ord('p'): 'sheet.cursorRowIndex = min(sheet.searchRegex())',

    # toggle/select/unselect all rows
    ord(' '): 'sheet.toggle(sheet.rows)',
    ord('s'): 'sheet.selectedRows = sheet.rows.copy()',
    ord('u'): 'sheet.selectedRows = []',

    ord('|'): 'sheet.select(sheet.rows[r] for r in sheet.searchRegex(inputLine(prompt="|"), columns=sheet.columns))',
    ord('\\'): 'sheet.unselect(sheet.rows[r] for r in sheet.searchRegex(inputLine(prompt="\\\\"), columns=sheet.columns))',

    # delete all selected rows
    ord('d'): 'sheet.rows = [r for r in sheet.rows if r not in sheet.selectedRows]',  # maintain order

    # ^P open sheet with all previous messages
    ctrl('p'): 'createListSheet("statuses", vd.statusHistory[::-1])',
}

### VisiData core

def moveListItem(L, fromidx, toidx):
    r = L.pop(fromidx)
    L.insert(toidx, r)
    return toidx

def iso8601(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def datestr(t):
    return iso8601(datetime.datetime.fromtimestamp(t))

def getMaxWidth(col, rows):
    if len(rows) == 0:
        return 0

    return min(max(max(len(col.getDisplayValue(r)) for r in rows), len(col.name)), int(windowWidth/2))


class VisiData:
    def __init__(self):
        self.sheets = []
        self._status = []
        self.statusHistory = []
        self.status('saul.pw/VisiData v' + __version__)
        self.lastErrors = []

    def status(self, s):
        self._status.append(s)
        self.statusHistory.append(s)
        self.statusHistory = self.statusHistory[-100:]  # keep most recent

    def exceptionCaught(self, status=True):
        import traceback
        self.lastErrors.append(traceback.format_exc().strip())
        self.lastErrors = self.lastErrors[-10:]  # keep most recent
        if status:
            self.status(self.lastErrors[-1].splitlines()[-1])
        if g_args.debug:
            raise

    def run(self):
        global sheet
        global windowHeight, windowWidth
        windowHeight, windowWidth = scr.getmaxyx()

        commands = base_commands
        while True:
            if not self.sheets:
                # if no more sheets, exit
                return

            sheet = self.sheets[0]
            if sheet.nRows == 0:
                self.status('no rows')

            try:
                sheet.draw()
            except Exception as e:
                self.exceptionCaught()

            # draw status on last line
            attr = colors[options.c_StatusLine]
            statusstr = options.SheetNameFmt % sheet.name + options.StatusSep.join(self._status)
            self.clipdraw(windowHeight-1, 0, statusstr, attr, windowWidth)
            self._status = []

            scr.move(windowHeight-1, windowWidth-2)
            curses.doupdate()

            ch = scr.getch()
            if ch == curses.KEY_RESIZE:
                windowHeight, windowWidth = scr.getmaxyx()
            elif ch == curses.KEY_MOUSE:
                try:
                    devid, x, y, z, bstate = curses.getmouse()
                    sheet.cursorRowIndex = sheet.topRowIndex+y-1
                except Exception:
                    self.exceptionCaught()
            elif ch in sheet.commands or ch in commands:
                cmdstr = sheet_specific_commands.get((sheet.name, ch)) or sheet.commands.get(ch) or commands.get(ch)
                try:
                    exec(cmdstr)

                    commands = base_commands
                except ChangeCommandSet as e:
                    # prefixes raise ChangeCommandSet exception instead
                    commands = e.commands
                    self.status(e.mode)
                except Exception:
                    commands = base_commands
                    self.exceptionCaught()
                    self.status(cmdstr)
            else:
                self.status('no command for key "%s" (%d) ' % (chr(ch), ch))

            sheet.checkCursor()

    def newSheet(self, name, src=None):
        if not src:
            src = VSource('internal', name)
        vs = VSheet(name, src)
        self.sheets.insert(0, vs)
        return vs

    def clipdraw(self, y, x, s, attr=curses.A_NORMAL, w=None):
        s = s.replace('\n', '\\n')
        try:
            if w is None:
                w = windowWidth-1
            w = min(w, windowWidth-x-1)

            # convert to string just before drawing
            s = str(s)
            if len(s) > w:
                scr.addstr(y, x, s[:w-1] + options.Ellipsis, attr)
            else:
                scr.addstr(y, x, s, attr)
                if len(s) < w:
                    scr.addstr(y, x+len(s), options.ColumnFiller*(w-len(s)), attr)
        except Exception as e:
            self.status('clipdraw error: y=%s x=%s len(s)=%s w=%s' % (y, x, len(s), w))
            self.exceptionCaught()
# end VisiData class

class VColumn:
    def __init__(self, name, func=lambda r: r, width=None):
        self.name = name
        self.func = func
        self.width = width

    def getValue(self, row):
        try:
            return self.func(row)
        except Exception as e:
            vd.exceptionCaught(status=False)
            return options.FunctionError

    def getDisplayValue(self, row):
        cellval = self.getValue(row)
        if cellval is None:
            cellval = options.VisibleNone
        return str(cellval).strip()

    def setValue(self, row, value):
        self.func.setter(row, value)

class VSource:
    def __init__(self, ref, name, contentType=None):
        self.ref = ref           # full reference (url/fqpn), for refetching
        self.name = name         # human-readable shorthand/mnemonic
        self.contents = None     # cached contents
        self.fp = None

        if contentType:
            self.type = contentType  # txt/json/csv etc to determine which File_* class to use
        elif isinstance(ref, str):
            fn, ext = os.path.splitext(self.ref)
            self.type = ext[1:]  # remove leading '.'
        elif isinstance(ref, object):
            self.type = 'pyobj'
        else:
            self.type = ''

    def __repr__(self):
        return self.ref

class VSheet:
    def __init__(self, name, src):
        self.source = src
        self.name = name
        self.rows = []
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorColIndex = 0  # absolute index of cursor into self.columns
        self.pinnedRows = []

        self.topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftColIndex = 0    # cursorColIndex of leftmost column
        self.rightColIndex = None   # cursorColIndex of rightmost column

        # as computed during draw()
        self.rowLayout = {} # [rowidx] -> y
        self.colLayout = {} # [colidx] -> (x, w)

        # all columns in display order
        self.columns = None

        # current search term
        self.currentRegex = None
        self.currentRegexColumns = None

        self.selectedRows = []

        # specialized sheet keys
        self.commands = {}

    @property
    def nVisibleRows(self):
        return windowHeight-2

    @property
    def cursorCol(self):
        return self.columns[self.cursorColIndex]

    @property
    def cursorRow(self):
        return self.rows[self.cursorRowIndex]

    @property
    def visibleRows(self):
        return self.rows[self.topRowIndex:self.topRowIndex+windowHeight-2]

    @property
    def cursorValue(self):
        return self.cellValue(self.cursorRowIndex, self.cursorColIndex)

    @property
    def statusLine(self):
        return 'row %s/%s' % (self.cursorRowIndex, len(self.rows))

    @property
    def nRows(self):
        return len(self.rows)

    @property
    def nCols(self):
        return len(self.columns)

    def moveCursorDown(self, n):
        self.cursorRowIndex += n

    def moveCursorRight(self, n):
        self.cursorColIndex += n

    def cellValue(self, rownum, col):
        if not isinstance(col, VColumn):
            # assume it's the column number
            col = self.columns[col]
        return col.getValue(self.rows[rownum])

    @functools.lru_cache()
    def columnValues(self, col):
        if not isinstance(col, VColumn):
            # assume it's the column number
            col = self.columns[col]
        return [col.getValue(r) for r in self.rows]

    def skipDown(self):
        pv = self.cursorValue
        for i in range(self.cursorRowIndex+1, len(self.rows)):
            if self.cellValue(i, self.cursorColIndex) != pv:
                self.cursorRowIndex = i
                return

        vd.status('no different value down this column')

    def skipUp(self):
        pv = self.cursorValue
        for i in range(self.cursorRowIndex, -1, -1):
            if self.cellValue(i, self.cursorColIndex) != pv:
                self.cursorRowIndex = i
                return

        vd.status('no different value up this column')

    def convertType(self, col, newType):
        nErrors = 0
        for r in self.rows:
            try:
                col.setValue(r, newType(col.getValue(r)))
            except Exception as e:
                col.setValue(r, None)
                nErrors += 1
        col.type = newType
        vd.status('converted %s to %s with %s exceptions' % (col.name, newType.__name__, nErrors))

    def toggle(self, rows):
        for r in rows:
            if r in self.selectedRows:
                self.selectedRows.remove(r)
            else:
                self.selectedRows.append(r)

    def select(self, rows):
        self.selectedRows.extend(rows)

    def unselect(self, rows):
        rows = list(rows)
        before = len(self.selectedRows)
        self.selectedRows = [r for r in self.selectedRows if r not in rows]
        vd.status('unselected %s rows' % (before-len(self.selectedRows)))

    def columnsMatch(self, row, columns, func):
        for c in columns:
            m = func(c.getDisplayValue(row))
            if m:
                return True
        return False

    def checkCursor(self):
        # keep cursor within actual available rowset
        if self.cursorRowIndex <= 0:
            self.cursorRowIndex = 0
        elif self.cursorRowIndex >= len(self.rows):
            self.cursorRowIndex = len(self.rows)-1

        if self.cursorColIndex <= 0:
            self.cursorColIndex = 0
        elif self.cursorColIndex >= len(self.columns):
            self.cursorColIndex = len(self.columns)-1

        if self.topRowIndex <= 0:
            self.topRowIndex = 0
        elif self.topRowIndex > len(self.rows):
            self.topRowIndex = len(self.rows)-1

        # (x,y) is relative cell within screen viewport
        x = self.cursorColIndex - self.leftColIndex
        y = self.cursorRowIndex - self.topRowIndex + 1  # header

        # check bounds, scroll if necessary
        if y < 1:
            self.topRowIndex = self.cursorRowIndex
        elif y > windowHeight-2:
            self.topRowIndex = self.cursorRowIndex-windowHeight+3

        if x < 0:
            self.leftColIndex -= 1
        elif self.rightColIndex and x > self.rightColIndex:
            self.leftColIndex += 1

    def searchRegex(self, regex=None, columns=None, backward=False, moveCursor=False):
        'sets row index if moveCursor; otherwise returns list of row indexes'
        if regex:
            self.currentRegex = re.compile(regex, re.IGNORECASE)

        if not self.currentRegex:
            vd.status('no regex')
            return []

        if columns:
            self.currentRegexColumns = columns

        if backward:
            rng = range(self.cursorRowIndex-1, -1, -1)
            rng2 = range(self.nRows-1, self.cursorRowIndex-1, -1)
        else:
            rng = range(self.cursorRowIndex+1, self.nRows)
            rng2 = range(0, self.cursorRowIndex+1)

        matchingRowIndexes = []

        for r in rng:
            if self.columnsMatch(self.rows[r], self.currentRegexColumns, self.currentRegex.search):
                if moveCursor:
                    self.cursorRowIndex = r
                    return r
                matchingRowIndexes.append(r)

        for r in rng2:
            if self.columnsMatch(self.rows[r], self.currentRegexColumns, self.currentRegex.search):
                if moveCursor:
                    self.cursorRowIndex = r
                    vd.status('search wrapped')
                    return r
                matchingRowIndexes.append(r)

        vd.status('%s matches for /%s/' % (len(matchingRowIndexes), self.currentRegex.pattern))

        return matchingRowIndexes

    def draw(self):
        scr.erase()  # clear screen before every re-draw
        sepchars = options.ColumnSep

        x = 0
        colidx = None

        self.colLayout = {}
        self.rowLayout = {}
        for colidx in range(self.leftColIndex, len(self.columns)):

            # draw header
            #   choose attribute to highlight column header
            if colidx == self.cursorColIndex:  # cursor is at this column
                attr = colors[options.c_CurHdr]
            else:
                attr = colors[options.c_Header]

            col = self.columns[colidx]
            col.width = col.width or getMaxWidth(col, self.visibleRows)
            colwidth = min(col.width, windowWidth-x)
            self.colLayout[colidx] = (x, colwidth)

            y = 0
            vd.clipdraw(y, x, col.name or defaultColNames[colidx], attr, colwidth)
            if x+colwidth+len(sepchars) <= windowWidth:
                scr.addstr(y, x+colwidth, sepchars, colors[options.c_ColumnSep])

            y += 1
            for rowidx in range(0, windowHeight-2):
                if self.topRowIndex + rowidx >= len(self.rows):
                    break

                self.rowLayout[self.topRowIndex+rowidx] = y

                row = self.rows[self.topRowIndex + rowidx]

                if self.topRowIndex + rowidx == self.cursorRowIndex:  # cursor at this row
                    attr = colors[options.c_CurRow]
                else:
                    attr = colors[options.c_default]

                if row in self.selectedRows:
                    attr |= colors[options.c_SelectedRow]

                if x+colwidth+len(sepchars) <= windowWidth:
                    scr.addstr(y, x+colwidth, sepchars, attr or colors[options.c_ColumnSep])

                if colidx == self.cursorColIndex:  # cursor is at this column
                    attr |= colors[options.c_CurCol]

                cellval = self.columns[colidx].getDisplayValue(row)
                vd.clipdraw(y, x, cellval, attr, colwidth)
                y += 1

            x += colwidth+len(sepchars)
            if x >= windowWidth:
                break

        self.rightColIndex = colidx

    def editCell(self, colnum=None):
        if colnum is None:
            colnum = self.cursorColIndex
        x, w = self.colLayout[colnum]
        y = self.rowLayout[self.cursorRowIndex]
        return editText(y, x, w)
# end VSheet class


### core sheet layouts
def setter(r, k, v):
    r[k] = v

def lambda_colname(colname):
    func = lambda r: r[colname]
    func.setter = lambda r,v,b=colname: setter(r,b,v)
    return func

def lambda_col(b):
    func = lambda r: r[b]
    func.setter = lambda r,v,b=b: setter(r,b,v)
    return func

def lambda_getattr(b):
    func = lambda r: getattr(r,b)
    func.setter = lambda r,v,b=b: setattr(r,b,v)
    return func


def getPublicAttrs(obj):
    return [k for k in dir(obj) if not k.startswith('_') and not callable(getattr(obj, k))]

def PyobjColumns(exampleRow):
    'columns for each public attribute on an object'
    return [VColumn(k, lambda_getattr(k)) for k in getPublicAttrs(exampleRow)]

def ArrayColumns(n):
    'columns that display r[0]..r[n]'
    return [VColumn('', lambda_col(colnum)) for colnum in range(n)]

def ArrayNamedColumns(columnstr):
    'columnstr is a string of n column names (separated by spaces), mapping to r[0]..r[n]'
    return [VColumn(colname, lambda_col(i)) for i, colname in enumerate(columnstr.split())]

def AttrColumns(colnames):
    'colnames is list of attribute names'
    return [VColumn(name, lambda_getattr(name)) for name in colnames]

def createTextViewer(name, text, src=None):
    viewer = vd.newSheet(name, src)
    viewer.rows = text.split('\n')
    viewer.columns = [ VColumn(name, lambda r: r) ]
    return viewer


def createPyObjSheet(name, pyobj, src=None):
    if isinstance(pyobj, list):
        return createListSheet(name, pyobj, src=src)
    elif isinstance(pyobj, dict):
        return createDictSheet(name, pyobj)
    elif isinstance(pyobj, object):
        return viewPyObj(pyobj)


def createListSheet(name, iterable, columns=None, src=None):
    'columns is a list of strings naming attributes on the objects within the iterable'
    vs = vd.newSheet(name, src)
    vs.rows = iterable

    if columns:
        vs.columns = AttrColumns(columns)
    elif isinstance(iterable[0], dict):  # list of dict
        vs.columns = [VColumn(k, lambda_colname(k)) for k in iterable[0].keys()]
    else:
        vs.columns = [VColumn(name)]

    # push sheet and set the new cursor row to the current cursor col
    vs.commands.update({
        ENTER: 'createPyObjSheet("%s[%s]" % (sheet.name, sheet.cursorRowIndex), sheet.cursorRow).cursorRowIndex = sheet.cursorColIndex',
    })
    return vs


def createDictSheet(name, mapping):
    vs = vd.newSheet(name, mapping)
    vs.rows = sorted(list(list(x) for x in mapping.items()))
    vs.columns = [
        VColumn('key', lambda_col(0)),
        VColumn('value', lambda_col(1))
    ]

    vs.commands.update({
        # pushes a sheet for the Pyobj in 'value', whatever that looks like
        ENTER: 'if sheet.cursorColIndex == 1: createPyObjSheet(sheet.name + options.SubsheetSep + sheet.cursorRow[0], sheet.cursorRow[1])',
        ord('e'): 'sheet.source[sheet.cursorRow[0]] = sheet.cursorRow[1] = sheet.editCell(1)',
    })
    return vs


def createFreqTable(sheet, col):
    values = collections.defaultdict(int)
    for r in sheet.rows:
        values[str(col.getValue(r))] += 1

    fqcolname = '%s_%s' % (sheet.name, col.name)
    freqtbl = vd.newSheet('freq_' + fqcolname)
    freqtbl.rows = sorted(values.items(), key=lambda r: r[1], reverse=True)  # sort by num reverse
    freqtbl.total = max(values.values())+1

    freqtbl.columns = [
        VColumn(fqcolname, lambda_col(0)),
        VColumn('num', lambda_col(1)),
        VColumn('histogram', lambda r,s=freqtbl: options.HistogramChar*int(r[1]*80/s.total), width=80)
    ]
    return freqtbl


def createColumnSummary(sheet):
    vs = vd.newSheet(sheet.name + '_columns', sheet)
    vs.rows = sheet.columns
    vs.columns = [
        VColumn('column', lambda_getattr('name')),
        VColumn('width',  lambda_getattr('width')),
        VColumn('type',   lambda_getattr('type')),
        VColumn('mode',   lambda c: statistics.mode(sheet.columnValues(c))),
        VColumn('min',    lambda c: min(sheet.columnValues(c))),
        VColumn('median', lambda c: statistics.median(sheet.columnValues(c))),
        VColumn('mean',   lambda c: statistics.mean(sheet.columnValues(c))),
        VColumn('max',    lambda c: max(sheet.columnValues(c))),
        VColumn('stddev', lambda c: statistics.stdev(sheet.columnValues(c))),
    ]
    vs.commands.update({
        ord('@'): 'sheet.source.convertType(sheet.cursorRow, datetime); sheet.moveCursorDown(+1)',
        ord('#'): 'sheet.source.convertType(sheet.cursorRow, int); sheet.moveCursorDown(+1)',
        ord('$'): 'sheet.source.convertType(sheet.cursorRow, str); sheet.moveCursorDown(+1)',
        ord('%'): 'sheet.source.convertType(sheet.cursorRow, float); sheet.moveCursorDown(+1)',
        })
    return vs

def viewPyObj(obj, src=None):
    if src is None:
        src = VSource(obj, str(obj))
    vs = vd.newSheet(type(obj), src)
    vs.rows = getPublicAttrs(obj)
    valfunc = lambda r,sheet=vs: getattr(sheet.source.ref, r)
    valfunc.setter = lambda r,v,sheet=vs: setattr(sheet.source.ref, r, v)
    vs.columns = [VColumn(type(obj).__name__ + '.attr'), VColumn('Value', valfunc)]
    return vs

MIMEToFileType = {
    'text/html': 'html',
}

### input source formats

def openSource(src):
    if isinstance(src.ref, str):
        if os.path.isdir(src.ref):
            return open_dir(src)

    funcname = 'open_' + src.type
    vs = globals().get(funcname, open_txt)(src)

    if '://' in src.ref:
        vs.commands.update({
            ord('A'): 'createDictSheet("headers:" + sheet.source.fp.geturl(), dict(sheet.source.fp.getheaders()))',
        })

    return vs

sourceCache = {}

def getContents(src):
    if not src.ref in sourceCache:
        sourceCache[src.ref] = getFile(src).read().decode(options.encoding, options.encoding_errors)

    return sourceCache[src.ref]

def getFile(src, mode='b'):  # mode may be 'b'
    if not src.fp:
        if hasattr(src.ref, 'read'):
            src.fp = src.ref
        elif isinstance(src.ref, str):
            if '://' in src.ref:
                import urllib.request
                import cgi
                resp = urllib.request.urlopen(src.ref)
                src.fp = resp
                src.ref = resp.geturl()   # replace with actual url retrieved (after following redirects)
                ctype, params = cgi.parse_header(resp.getheader('Content-Type'))
                src.type = MIMEToFileType.get(ctype, ctype.split('/')[-1])
            else:
                src.fp = open(src.ref, 'r' + mode)
        else:
            vd.status('unknown how to get file object from %s' % src)
            return None

    return src.fp

class hrefParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(self)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
           attrdict = dict(attrs)
           if 'href' in attrdict:
               self.hrefs.append(attrdict)

    def handle_data(self, data):
        if self.hrefs and 'linktext' not in self.hrefs[-1]:
            self.hrefs[-1]['linktext'] = data


def open_html(src):
    hp = hrefParser()
    hp.feed(getContents(src))
    vs = createListSheet(src.name + options.SubsheetSep + 'hrefs', hp.hrefs, PyobjColumns(hp.hrefs[0]), src=src)
    vs.commands.update({
        ENTER: 'openSource(VSource(urllib.parse.urljoin(sheet.source.ref, sheet.cursorRow["href"]), sheet.cursorRow["linktext"]))',
    })
    return vs


def open_zip(src):
    import zipfile
    if not src.fp:
        src.fp = zipfile.ZipFile(src.ref, 'r')

    vs = vd.newSheet(src.name, src)
    vs.rows = vs.source.fp.infolist()
    vs.columns = AttrColumns('filename file_size date_time'.split())
    vs.commands.update({
        ENTER: 'openSource(VSource(sheet.source.fp.open(sheet.cursorRow), sheet.cursorRow.filename))',
    })
    return vs


def open_txt(src):
    return createTextViewer(src.name, getContents(src), src)


def open_dir(src):
    vs = vd.newSheet(src.name, src)
    vs.rows = []
    for dirpath, dirnames, filenames in os.walk(src.ref):
        for fn in filenames:
            basename, ext = os.path.splitext(fn)
            path = os.path.join(dirpath, fn)
            st = os.stat(path)
            vs.rows.append((dirpath, fn, ext, st.st_size, datestr(st.st_mtime), path))

    vs.columns = ArrayNamedColumns('directory filename ext size mtime')
    vs.commands.update({
        ENTER: 'openSource(VSource(sheet.cursorRow[-1], sheet.cursorRow[1]))'  # path, filename
    })
    return vs



def open_csv(src):
    contents = getContents(src)

    if options.csv_dialect == 'sniff':
        headers = contents[:1024]
        dialect = csv.Sniffer().sniff(headers)
    else:
        dialect = options.csv_dialect

    rdr = csv.reader(io.StringIO(contents, newline=''), dialect=dialect, delimiter=options.csv_delimiter, quotechar=options.csv_quotechar)

    vs = vd.newSheet(src.name, src)
    vs.rows = [r for r in rdr]
    vs.columns = PyobjColumns(vs.rows[0]) or ArrayColumns(len(vs.rows[0]))
    return vs


def open_json(src):
    import json
    obj = json.loads(getContents(src))
    return createPyObjSheet(src.name, obj, src)


def open_tsv(src):
    contents = getContents(src)
    lines = contents.splitlines()

    vs = vd.newSheet(src.name, src)
    vs.rows = [L.split('\t') for L in lines[1:]]  # [rownum] -> [ field, ... ]
    vs.columns = [VColumn(name, lambda_col(colnum)) for colnum, name in enumerate(lines[0].split('\t'))]  # list of VColumn in display order
    return vs


def createHDF5Sheet(hobj, src):
    import h5py
    vs = vd.newSheet(hobj.name, src)

    if isinstance(hobj, h5py.Group):
        vs.rows = [ hobj[objname] for objname in hobj.keys() ]
        vs.columns = [
            VColumn(hobj.name, lambda r: r.name.split('/')[-1]),
            VColumn('type', lambda r: type(r).__name__),
            VColumn('nItems', lambda r: len(r)),
        ]

        vs.commands.update({
            ENTER: 'createHDF5Sheet(sheet.cursorRow, sheet.source)',
            ord('A'): 'createDictSheet(sheet.cursorRow.name + "_attrs", sheet.cursorRow.attrs)',
        })
    elif isinstance(hobj, h5py.Dataset):
        if len(hobj.shape) == 1:
            vs.rows = hobj[:]
            vs.columns = [VColumn(colname, lambda_colname(colname)) for colname in hobj.dtype.names]
        elif len(hobj.shape) == 2:  # matrix
            vs.rows = hobj[:]
            vs.columns = ArrayColumns(hobj.shape[1])
    return vs


def open_h5(src):
    import h5py
    if not src.fp:
        src.fp = h5py.File(src.ref, 'r')
    hs = createHDF5Sheet(src.fp, src)
    hs.name = src.name
    return hs

open_hdf5 = open_h5


def open_xlsx(src):
    import openpyxl

    fp = getFile(src, mode='b')

    workbook = openpyxl.load_workbook(fp, data_only=True, read_only=True)

    for sheetname in workbook.sheetnames:
        sheet = workbook.get_sheet_by_name(sheetname)
        vs = vd.newSheet(src.ref + options.SubsheetSep + sheetname, src)

        vs.columns = ArrayColumns(sheet.max_column)

        for row in sheet.iter_rows():
            vs.rows.append([cell.value for cell in row])

    return vs  # return the last one

### Sheet savers

def saveSheet(sheet, fn):
    basename, ext = os.path.splitext(fn)
    funcname = 'save_' + ext[1:]
    globals().get(funcname, save_tsv)(sheet, fn)
    vd.status('saved to ' + fn)

def save_tsv(sheet, fn):
    with open(fn, 'w', encoding=options.encoding, errors=options.encoding_errors) as fp:
        colhdr = '\t'.join(col.name for col in sheet.columns) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)
        for r in sheet.rows:
            fp.write('\t'.join(col.getDisplayValue(r) for col in sheet.columns) + '\n')

def save_csv(sheet, fn):
    with open(fn, 'w', newline='', encoding=options.encoding, errors=options.encoding_errors) as fp:
        cw = csv.writer(fp, dialect=options.csv_dialect, delimiter=options.csv_delimiter, quotechar=options.csv_quotechar)
        colnames = [col.name for col in sheet.columns]
        if ''.join(colnames):
            cw.writerow(colnames)
        for r in sheet.rows:
            cw.writerow([col.getDisplayValue(r) for col in sheet.columns])

### curses, options, init

def editText(y, x, w, prompt=''):
    if not prompt:
        scr.addstr(y, x, '_' * w, colors[options.c_EditCell])
    else:
        scr.addstr(y, x, prompt) #'%-*s' % (windowWidth-1, prompt))
        x += len(prompt)
    curses.echo()
    inp = scr.getstr(y, x)
    curses.noecho()
    r = inp.decode('utf-8')
    vd.status('"%s"' % r)
    return r

def inputLine(prompt=''):
    'move to the bottom of the screen and get a line of input from the user'
    scr.move(windowHeight-1, 0)
    scr.clrtoeol()
    return editText(windowHeight-1, 0, windowWidth-1, prompt)


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

    curses.meta(1)  # allow "8-bit chars"

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


def terminal_main():
    'Parse arguments and initialize VisiData instance'
    import argparse

    global g_args, vd
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('inputs', nargs='*', help='initial sheets')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False, help='abort on exception')
    g_args = parser.parse_args()

    vd = VisiData()
    inputs = g_args.inputs or ['.']

    for fn in inputs:
        openSource(VSource(fn, fn))

    ret = wrapper(curses_main)
    if ret:
        print(ret)


def curses_main(_scr):
    global scr
    scr = _scr

    # get control keys instead of signals
    curses.raw()

    # enable mouse events
#    curses.mousemask(curses.ALL_MOUSE_EVENTS)

    try:
        return vd.run()
    except Exception as e:
        return 'Exception: ' + str(e)


def wrapper(f, *args):
    import curses
    return curses.wrapper(setupcolors, f, *args)


if __name__ == '__main__':
    terminal_main()
