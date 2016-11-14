#!/usr/bin/python3

'VisiData: curses interface for exploration of tabular data'

__author__ = 'Saul Pwanson <vd@saul.pw>'
__version__ = 0.15

import string
import collections
import os.path

import curses
import codecs

vd = None    # toplevel VisiData, contains all sheets
scr = None   # toplevel curses screen
g_nextCmdIsGlobal = False  # 'g' prefix sets to True
g_winWidth = None
g_winHeight = None

Inverses = {}  # inverse colors

def gettext(k):
    _gettext = {
        'VisibleNone': '',
        'ColumnFiller': ' ',
        'Ellipsis': '…',
    }
    return _gettext[k]

def ctrl(ch):
    return ord(ch) & 31  # convert from 'a' to ^A keycode


# when done with 'g' prefix
global_commands = {
    ord('q'): 'vd.sheets = []',

    ord('h'): 'sheet.cursorColIndex = sheet.leftColIndex = 0',
    ord('k'): 'sheet.cursorRowIndex = sheet.topRowIndex = 0',
    ord('j'): 'sheet.cursorRowIndex = len(sheet.rows); sheet.topRowIndex = sheet.cursorRowIndex - sheet.nVisibleRows',
    ord('l'): 'sheet.cursorColIndex = sheet.leftColIndex = len(sheet.columns)',

    ord('E'): 'g_args.debug = True; raise VException(sheet.lastError)',
    ord('_'): 'for c in sheet.columns: c.width = getMaxWidth(c, sheet.visibleRows)',
}


base_commands = {
    ord('q'): 'del vd.sheets[0]',

    curses.KEY_LEFT:  'sheet.moveCursorRight(-1)',
    curses.KEY_DOWN:  'sheet.moveCursorDown(+1)',
    curses.KEY_UP:    'sheet.moveCursorDown(-1)',
    curses.KEY_RIGHT: 'sheet.moveCursorRight(+1)',
    curses.KEY_NPAGE: 'sheet.moveCursorDown(sheet.nVisibleRows); sheet.topRowIndex += sheet.nVisibleRows',
    curses.KEY_PPAGE: 'sheet.moveCursorDown(-sheet.nVisibleRows); sheet.topRowIndex -= sheet.nVisibleRows',
    curses.KEY_HOME:  'sheet.topRowIndex = sheet.cursorRowIndex = 0',
    curses.KEY_END:   'sheet.cursorRowIndex = len(sheet.rows)-1',

    ord('h'): 'sheet.moveCursorRight(-1)',
    ord('j'): 'sheet.moveCursorDown(+1)',
    ord('k'): 'sheet.moveCursorDown(-1)',
    ord('l'): 'sheet.moveCursorRight(+1)',
    ord('H'): 'sheet.cursorRowIndex = sheet.topRowIndex',
    ord('M'): 'sheet.cursorRowIndex = sheet.topRowIndex+sheet.nVisibleRows/2',
    ord('L'): 'sheet.cursorRowIndex = sheet.topRowIndex+sheet.nVisibleRows',

    ctrl('h'): 'sheet.leftColIndex -= 1',
    ctrl('j'): 'sheet.topRowIndex += 1',
    ctrl('k'): 'sheet.topRowIndex -= 1',
    ctrl('l'): 'sheet.leftColIndex += 1',

    ctrl('g'): 'vd.status("%s/%s   %s" % (sheet.cursorRowIndex, len(sheet.rows), sheet.name))',

    ord('E'): 'vd.pushSheet(createTextViewer("last_error", sheet.lastError))',
    ord('F'): 'vd.pushSheet(createFreqTable(sheet, sheet.cursorCol))',

    ord('_'): 'sheet.cursorCol.width = getMaxWidth(sheet.cursorCol, sheet.visibleRows)',
}


def createTextViewer(name, text):
    viewer = VSheet(name)
    viewer.rows = text.split('\n')
    viewer.columns = [ VColumn(name, None, lambda r: r) ]
    return viewer


def createFreqTable(sheet, col):
    values = collections.defaultdict(int)
    for r in sheet.rows:
        values[str(col.getValue(r))] += 1

    fqcolname = '%s_%s' % (sheet.name, col.name)
    freqtbl = VSheet('freq_' + fqcolname)
    freqtbl.rows = list(values.items())
    freqtbl.columns = [ VColumn(fqcolname, None, lambda_col(0)), VColumn('num_instances', None, lambda_col(1)) ]
    return freqtbl


class VException(Exception):
    pass

def exceptionCaught(sheet):
    import traceback
    sheet.lastError = traceback.format_exc().strip()
    vd.status(sheet.lastError.splitlines()[-1])
    if g_args.debug:
        raise


def open_xlsx(fn):
    import openpyxl
    basename, ext = os.path.splitext(fn)
    workbook = openpyxl.load_workbook(fn, data_only=True, read_only=True)

    for sheetname in workbook.sheetnames:
        sheet = workbook.get_sheet_by_name(sheetname)
        vs = VSheet('%s:%s' % (basename, sheetname))

        defaultColNames = string.ascii_uppercase
        vs.columns = [VColumn(defaultColNames[colnum], None, lambda_col(colnum)) for colnum in range(0, sheet.max_column)]

        for row in sheet.iter_rows():
            vs.rows.append([cell.value for cell in row])

        yield vs


def open_tsv(fn):
    basename, ext = os.path.splitext(fn)
    fetcher = TsvFetcher(fn)
    vs = VSheet(basename)
    vs.rows = fetcher.getRows(0, 10000)
    vs.columns = [VColumn(name, None, lambda_col(colnum)) for colnum, name in enumerate(fetcher.columnNames)]  # list of VColumn in display order
    yield vs


class TsvFetcher:
    def __init__(self, fntsv):
        self.fp = codecs.open(fntsv, 'r')
        self.rowIndex = { }  # byte offsets of each line for random access
        lines = self.fp.read().splitlines()
        self.columnNames = lines[0].split('\t')
        self.rows = [L.split('\t') for L in lines[1:]]  # [rownum] -> [ field, ... ]

    def getColumnNames(self):
        return self.columnNames

    def getRows(self, startrownum, endrownum):
        return self.rows[startrownum:endrownum]


def getMaxWidth(col, rows):
    return max(max(len(col.getValue(r) or '') for r in rows), len(col.name))


class VisiData:
    def __init__(self):
        self.sheets = []
        self._status = 'saul.pw/visidata ' + str(__version__)

    def status(self, s):
        self._status = s

    def run(self):
        global g_nextCmdIsGlobal, g_winHeight, g_winWidth
        g_winHeight, g_winWidth = scr.getmaxyx()

        while True:
            if not self.sheets:
                # if no more sheets, exit
                return

            sheet = self.sheets[0]

            try:
                sheet.draw()
            except Exception as e:
                exceptionCaught(sheet)

            # draw status on last line
            if self._status:
                self.clipdraw(g_winHeight-1, 0, self._status)
                self._status = ''

            scr.move(g_winHeight-1, g_winWidth-2)
            curses.doupdate()

            ch = scr.getch()
            if ch == curses.KEY_RESIZE:
                g_winHeight, g_winWidth = scr.getmaxyx()
            elif g_nextCmdIsGlobal:
                if ch in global_commands:
                    try:
                        exec(global_commands[ch])
                    except Exception:
                        exceptionCaught(sheet)
                else:
                    self.status("no global version of command for key '%s' (%d)" % (chr(ch), ch))
                g_nextCmdIsGlobal = False
            elif ch == ord('g'):
                g_nextCmdIsGlobal = True
            elif ch in base_commands:
                try:
                    exec(base_commands[ch])
                except Exception:
                    exceptionCaught(sheet)
            else:
                self.status("no command for key '%s' (%d)" % (chr(ch), ch))

            sheet.checkCursor()

    def pushSheet(self, sheet):
        self.sheets.insert(0, sheet)

    def clipdraw(self, y, x, s, attr=curses.A_NORMAL, w=None):
        try:
            if w is None:
                w = g_winWidth
            w = min(w, g_winWidth-x)

            # convert to string just before drawing
            s = str(s)
            if len(s) > w:
                scr.addstr(y, x, s[:w-1] + gettext('Ellipsis'), attr)
            else:
                scr.addstr(y, x, s, attr)
                if len(s) < w:
                    scr.addstr(y, x+len(s), gettext('ColumnFiller')*(w-len(s)), attr)
        except Exception as e:
            self.status('clipdraw error: y=%s x=%s len(s)=%s w=%s' % (y, x, len(s), w))


class VColumn:
    def __init__(self, name, width=None, func=lambda r: r, eval_context=None):
        self.name = name
        self.width = width
        self.func = func

    def getValue(self, row):
        return self.func(row)


def lambda_col(b):
    return lambda r: r[b]


class VSheet:
    def __init__(self, name):
        self.name = name
        self.rows = []
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorColIndex = 0  # absolute index of cursor into self.columns
        self.pinnedRows = []

        self.topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftColIndex = 0    # cursorColIndex of leftmost column
        self.rightColIndex = 0   # cursorColIndex of rightmost column

        # all columns in display order
        self.columns = None

        self.lastError = 'No error'

    def __getattr__(self, k):
        if k == 'nVisibleRows':
            return g_winHeight-2
        elif k == 'cursorCol':
            return self.columns[self.cursorColIndex]
        elif k == 'visibleRows':
            return self.rows[self.topRowIndex:self.topRowIndex + g_winHeight-2]
        else:
            raise AttributeError(k)

    def moveCursorDown(self, n):
        self.cursorRowIndex += n

    def moveCursorRight(self, n):
        self.cursorColIndex += n

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
        elif y > g_winHeight-2:
            self.topRowIndex = self.cursorRowIndex-g_winHeight+3

        if x < 0:
            self.leftColIndex -= 1
        elif x > self.rightColIndex:
            self.leftColIndex += 1

    def draw(self):
        scr.erase()  # clear screen before every re-draw

        x = 0

        for colidx in range(self.leftColIndex, len(self.columns)):

            # draw header
            #   choose attribute to highlight column header
            if colidx == self.cursorColIndex:  # cursor is at this column
                attr = curses.A_BOLD
            else:
                attr = curses.A_NORMAL

            col = self.columns[colidx]

            # last column should use entire rest of screen width
            if colidx == len(self.columns)-1:
                colwidth = g_winWidth - x - 1
            else:
                colwidth = col.width or getMaxWidth(col, self.rows)

#            if self.drawColHeader:
            vd.clipdraw(0, x, col.name, attr, colwidth)

            y = 1
            for rowidx in range(0, g_winHeight-2):
                if self.topRowIndex + rowidx >= len(self.rows):
                    break

                if colidx == self.cursorColIndex:  # cursor is at this column
                    attr = curses.A_BOLD
                else:
                    attr = curses.A_NORMAL

                if self.topRowIndex + rowidx == self.cursorRowIndex:  # cursor at this row
                    attr = curses.A_REVERSE

                row = self.rows[self.topRowIndex + rowidx]
                cellval = self.columns[colidx].getValue(row)

                if cellval is None:
                    cellval = gettext('VisibleNone')

                vd.clipdraw(y, x, cellval, attr, colwidth)
                y += 1

            x += colwidth+1
            if x >= g_winWidth:
                self.rightColIndex = colidx
                break


def sheet_from_file(fqpn):
    fn, ext = os.path.splitext(fqpn)
    ext = ext[1:]  # remove leading '.'

    funcname = "open_" + ext
    if funcname not in globals():
        raise VException('%s: No parser available for %s' % (fqpn, ext))

    return globals()[funcname](fqpn)


nextColorPair = 1
def setupcolors(stdscr, f, *args):
    global RED, BLUE, GREEN, YELLOW, BROWN, CYAN, MAGENTA
    global RED_BG, BLUE_BG, GREEN_BG, BROWN_BG, CYAN_BG, MAGENTA_BG

    def makeColor(fg, bg):
        global nextColorPair
        if curses.has_colors():
            curses.init_pair(nextColorPair, fg, bg)
            c = curses.color_pair(nextColorPair)
            nextColorPair += 1
        else:
            c = curses.A_NORMAL

        return c

    if not Inverses:  # once-only
        curses.meta(1)  # allow "8-bit chars"

        RED = curses.A_BOLD | makeColor(curses.COLOR_RED, curses.COLOR_BLACK)
        BLUE = curses.A_BOLD | makeColor(curses.COLOR_BLUE, curses.COLOR_BLACK)
        GREEN = curses.A_BOLD | makeColor(curses.COLOR_GREEN, curses.COLOR_BLACK)
        BROWN = makeColor(curses.COLOR_YELLOW, curses.COLOR_BLACK)
        YELLOW = curses.A_BOLD | BROWN
        CYAN = makeColor(curses.COLOR_CYAN, curses.COLOR_BLACK)
        MAGENTA = makeColor(curses.COLOR_MAGENTA, curses.COLOR_BLACK)

        RED_BG = makeColor(curses.COLOR_WHITE, curses.COLOR_RED)
        BLUE_BG = makeColor(curses.COLOR_WHITE, curses.COLOR_BLUE)
        GREEN_BG = makeColor(curses.COLOR_BLACK, curses.COLOR_GREEN)
        BROWN_BG = makeColor(curses.COLOR_BLACK, curses.COLOR_YELLOW)
        CYAN_BG = makeColor(curses.COLOR_BLACK, curses.COLOR_CYAN)
        MAGENTA_BG = makeColor(curses.COLOR_BLACK, curses.COLOR_MAGENTA)

        Inverses[RED] = RED_BG
        Inverses[BLUE] = BLUE_BG
        Inverses[GREEN] = GREEN_BG
        Inverses[YELLOW] = BROWN_BG
        Inverses[CYAN] = CYAN_BG
        Inverses[MAGENTA] = MAGENTA_BG

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
        for vs in sheet_from_file(fn):
            vd.sheets.append(vs)

    ret = wrapper(curses_main)
    if ret:
        print(ret)


def curses_main(_scr):
    global scr
    scr = _scr

    # get control keys instead of signals
    curses.raw()

    try:
        return vd.run()
    except Exception as e:
        return 'Exception: ' + str(e)


def wrapper(f, *args):
    import curses
    return curses.wrapper(setupcolors, f, *args)


if __name__ == "__main__":
    terminal_main()
