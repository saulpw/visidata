#!/usr/bin/python3

'VisiData: curses tabular data exploration tool'

__author__ = 'saul.pw'
__version__ = 0.11

import os.path

import curses
import codecs

vd = None    # toplevel VisiData, contains all sheets
scr = None   # toplevel curses screen
g_nextCmdIsGlobal = False  # 'g' prefix sets to True
g_winWidth = None
g_winHeight = None

Inverses = {}  # inverse colors

'''Movement Keys:
    hjkl    (or arrows) move cell cursor left/down/up/right (g to go all the way)
'''
global_commands = {
            curses.KEY_LEFT:  'self.moveCursorRight(-1)',
            curses.KEY_DOWN:  'self.moveCursorDown(+1)',
            curses.KEY_UP:    'self.moveCursorDown(-1)',
            curses.KEY_RIGHT: 'self.moveCursorRight(+1)',
            curses.KEY_NPAGE: 'self.moveCursorDown(g_winHeight-1)',
            curses.KEY_PPAGE: 'self.moveCursorDown(-g_winHeight+1)',
            curses.KEY_HOME:  'self.topRowIndex = self.cursorRowIndex = 0',
            curses.KEY_END:   'self.cursorRowIndex = len(self.rows)-1',

            ord('h'): 'self.moveCursorRight(-1)',
            ord('j'): 'self.moveCursorDown(+1)',
            ord('k'): 'self.moveCursorDown(-1)',
            ord('l'): 'self.moveCursorRight(+1)',

            ord('E'): 'vd.lastError(self.lastError)',
        }


class VException(Exception):
    pass


def open_xlsx(fn):
    import openpyxl
    workbook = openpyxl.load_workbook(fn, data_only=True, read_only=True)

    for sheetname in workbook.sheetnames:
        sheet = workbook.get_sheet_by_name(sheetname)
        vs = VSheet()

        vs.columns = [VColumn('', None, lambda_slice(colnum, None)) for colnum in range(0, sheet.max_column)]

        for row in sheet.iter_rows():
            vs.rows.append([cell.value for cell in row])

        yield vs


def open_tsv(fn):
    fetcher = TsvFetcher(fn)
    vs = VSheet()
    vs.rows = fetcher.getRows(0, 10000)
    vs.columns = [VColumn(name, fetcher.getMaxWidth(colnum), lambda_slice(colnum, None)) for colnum, name in enumerate(fetcher.columnNames)]  # list of VColumn in display order
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

    def getMaxWidth(self, colnum):
        maxvalwidth = max(len(row[colnum]) for row in self.rows)
        return max(maxvalwidth, len(self.columnNames[colnum]))

    def getRows(self, startrownum, endrownum):
        return self.rows[startrownum:endrownum]


class Visidata:
    def __init__(self):
        self.sheets = []

    def run(self):
        return self.sheets[0].run()

    def status(self, s):
        self.clipdraw(g_winHeight-1, 0, s)
        scr.clrtoeol()

    def error(self, s):
        self.clipdraw(g_winHeight-2, 0, s)
        scr.clrtoeol()

    def clipdraw(self, y, x, s, attr=curses.A_NORMAL, w=None):
        if w is None:
            w = g_winWidth
        w = min(w, g_winWidth-x)

        # convert to string just before drawing
        s = str(s)
        if len(s) > w:
            scr.addstr(y, x, s[:w-1] + '…', attr)
        else:
            scr.addstr(y, x, s, attr)

    def lastError(self, errlines):
        if not errlines:
            self.status("No last error")
            return

        if g_nextCmdIsGlobal:
            g_args.debug = True
            raise Exception('\n'.join(errlines))

        errsheet = VSheet()
        errsheet.rows = [[L] for L in errlines]
        errsheet.columns = [ VColumn("error") ]
        errsheet.run()


class VColumn:
    def __init__(self, name, width=None, func=lambda r: r, eval_context=None):
        self.name = name
        self.width = width
        self.func = func

    def getValue(self, row):
        return self.func(row)


def lambda_slice(b,e):
    return lambda r: r[b:e]


class VSheet:
    def __init__(self):
        self.rows = []
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorColIndex = 0  # absolute index of cursor into self.columns

        self.topRowIndex = 0   # cursorRowIndex of topmost row
        self.leftColIndex = 0  # cursorColIndex of leftmost column

        # all columns in display order
        self.columns = None

        self.lastError = None

    def getMaxWidth(self, colnum):
        return max(len(row[colnum] or '') for row in self.rows)

    def moveCursorDown(self, n):
        self.cursorRowIndex += n

    def moveCursorRight(self, n):
        self.cursorColIndex += n

    def checkCursor(self):

        # keep cursor within actual available rowset
        if self.cursorRowIndex <= 0:
            self.cursorRowIndex = 0
        elif self.cursorRowIndex >= len(self.rows):
            # TODO: fetch more if available
            self.cursorRowIndex = len(self.rows)-1

        # (x,y) is relative cell within screen viewport
        x = self.cursorColIndex - self.leftColIndex
        y = self.cursorRowIndex - self.topRowIndex + 1  # header

        # check bounds
        if y > g_winHeight:
            y = g_winHeight

        if x < 0:
            x = 0
#        elif x >= len(self.visibleCols):
#            self.columns

    def run(self):
        global g_nextCmdIsGlobal, g_winHeight, g_winWidth
        while True:
            g_winHeight, g_winWidth = scr.getmaxyx()
            self.checkCursor()

            try:
                self.draw()
            except Exception as e:
                import traceback
                self.lastError = [x for x in traceback.format_exc().strip().split('\n')]
                vd.error(self.lastError[-1])
                if g_args.debug:
                    raise

            curses.doupdate()

            ch = scr.getch()
            if ch == ord('q'):
                return "QUIT"
            if ch == ord('g'):
                g_nextCmdIsGlobal = True
            elif ch in global_commands:
                exec(global_commands[ch])
                g_nextCmdIsGlobal = False
            else:
                self.error('key "%s" (%d) unsupported' % (chr(ch), ch))
                g_nextCmdIsGlobal = False

    def draw(self):
        scr.erase()  # clear screen before every re-draw

        x = 0
        visibleRows = self.rows[self.topRowIndex:self.topRowIndex+g_winHeight-4]
        for colidx in range(self.leftColIndex, len(self.columns)):
            if colidx == self.cursorColIndex:  # at this column
                attr = curses.A_REVERSE
            else:
                attr = curses.A_NORMAL

            col = self.columns[colidx]

            # last column should use entire rest of screen width
            if colidx == len(self.columns)-1:
                colwidth = g_winWidth - x
            else:
                colwidth = col.width or self.getMaxWidth(colidx)

            # always draw column header line on first row
            vd.clipdraw(0, x, col.name, attr, colwidth)

            y = 1
            for rowidx in range(0, len(visibleRows)):
                if rowidx == self.cursorRowIndex:  # cursor at this row
                    attr = curses.A_UNDERLINE
                else:
                    attr = curses.A_NORMAL

                row = visibleRows[rowidx]
                cellval = row[colidx]

                if cellval is None:
                    cellval = ''

                vd.clipdraw(y, x, cellval, attr, colwidth)
                y += 1

            x += colwidth+1
            if x > g_winWidth:
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
    'Parse arguments and initialize Visidata instance'
    import argparse

    global g_args, vd
    parser = argparse.ArgumentParser(description='Visidata ' + str(__version__) + ' by saul.pw')

    parser.add_argument('inputs', nargs='*', help='initial sheets')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False, help='abort on exception')
    g_args = parser.parse_args()

    vd = Visidata()
    inputs = g_args.inputs or ['.']

    for fn in inputs:
        for vs in sheet_from_file(fn):
            vd.sheets.append(vs)

    wrapper(curses_main)


def curses_main(_scr):
    global scr
    scr = _scr

    result = "DONTQUIT"
    while result and result != "QUIT":
        result = vd.run()

    return result


def wrapper(f, *args):
    import curses
    return curses.wrapper(setupcolors, f, *args)


if __name__ == "__main__":
    terminal_main()

notimplyet = '''
    ^HJKL    (or ctrl-arrows) move column/row left/down/up/right (changes data ordering) (g to 'throw' it all the way)
    ^F/^B   page forward/backward
            go to row number
    ^G      show sheet status line

    /       Search forward by regex
    ?       Search backward by regex
    n       Go to next search match in same direction

    s S     save current/every sheet to new file
    ^R      reload files (keep position)

Prefixes
    g       selects all columns or other global context for the next command only

Sheet setup and meta-sheets
    $       view sheet list
    ^       toggle to previous sheet

    %       column chooser
    -       Hide current column
    _       Expand current column to fit all column values on screen
    +       Expand all columns to fit all elements on screen
    =       Add derivative column from expression

    E       view last full error (e.g. stack trace)

    F       build frequency table for current column (g for all columns)

    SPACE   mark current row
    0       clear all marked items
    m       add regex to mark list
            add eval expression to mark list

    M       view mark list for this sheet
            mark all visible rows
            mark all rows
            hide marked rows
            only show marked rows
            mark all hidden rows and unhide

    D       remove marked rows (or current row?)
    T       transform column by expression

row filter (WHERE)
    |       filter by regex in this column (add to include list)
    \       ignore by regex in this column (add to exclude list)
    ,       filter the current column by its value in the current row
    *       Show all items (clear include/exclude lists)
    { }     Sort primarily by current column (asc/desc)
    [ ]     Toggle current column as additional sort key (asc/desc)
            Remove all sort keys (does not change current ordering)

aggregation (GROUP BY)
            group by current column locally (g to make global groups)
            ungroup current column (g to ungroup all columns)

    ^R      refresh current sheet from sources
'''


