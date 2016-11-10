#!/usr/bin/python3

'VisiData: curses tabular data exploration tool'

__author__ = 'saul.pw'
__version__ = 0.10

import curses
import codecs


class VException(Exception):
    pass


'''Movement Keys:
    hjkl    (or arrows) move cell cursor left/down/up/right (g to go all the way)
'''


Inverses = {}

class TsvFetcher:
    def __init__(self, fntsv):
        self.fp = codecs.open(fntsv, 'r')
        self.rowIndex = { }  # byte offsets of each line for random access
        lines = self.fp.read().splitlines()
        self.rows = dict((n, lines[n+1].split('\t')) for n in range(0, len(lines)-1))  # [rownum] -> [ field ... ]
        self.columnNames = lines[0].split('\t')

    def getColumnNames(self):
        return self.columnNames

    def getMaxWidth(self, colnum):
        maxvalwidth = max(len(row[colnum]) for row in self.rows.values())
        return max(maxvalwidth, len(self.columnNames[colnum]))

    def getRows(self, startrownum, endrownum):
        r = []
        for rownum in range(startrownum, endrownum+1):
            if rownum not in self.rows:
                self.rows[rownum] = self.fetchRow(rownum)
            r.append(self.rows[rownum])
        return r


class Visidata:
    def __init__(self):
        self.sheets = []

    def run(self, scr):
        return self.sheets[0].run(scr)

class VColumn:
    def __init__(self, name, width=None):
        self.name = name
        self.width = width or len(name)

class VSheet:
    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.rowIndex = 0  # absolute index of cursor into self.rows
        self.colIndex = 0  # absolute index of cursor into self.columns

        self.firstDisplayRow = 0  # rowIndex of topmost row
        self.firstDisplayCol = 0  # colIndex of leftmost column

        self.columns = [VColumn(name, fetcher.getMaxWidth(colnum)) for colnum, name in enumerate(fetcher.columnNames)]  # list of VColumn in display order
        self.commands = {
            ord('h'): 'self.moveCursor(0, -1)',
            ord('j'): 'self.moveCursor(+1, 0)',
            ord('k'): 'self.moveCursor(-1, 0)',
            ord('l'): 'self.moveCursor(0, +1)',
        }
        self.scr = None

    def moveCursor(self, dy, dx):
        y = self.rowIndex + dy
        x = self.colIndex + dx

        # check bounds
        if y < 0:
            y = 0
        elif y > self.winHeight:
            y = self.winHeight

        self.rowIndex = y
        self.colIndex = x

    def run(self, scr):
        self.scr = scr

        while True:
            try:
                self.draw()
            except Exception as e:
                self.lastError = [str(e)]
                self.error(self.lastError[0])

            curses.doupdate()

            ch = scr.getch()
            if ch == ord('q'):
                return "QUIT"
            elif ch in self.commands:
                exec(self.commands[ch])
            else:
                self.error('key "%s" (%d) unsupported' % (chr(ch), ch))

    def draw(self):
        scr = self.scr
        self.winHeight, self.winWidth = scr.getmaxyx()
        x = 0
        visibleRows = self.fetcher.getRows(self.firstDisplayRow, self.firstDisplayRow+self.winHeight-4)
        for colidx in range(self.firstDisplayCol, len(self.columns)):
            if colidx == self.colIndex:  # at this column
                attr = curses.A_REVERSE
            else:
                attr = curses.A_NORMAL
            col = self.columns[colidx]
            # always draw column header line on first row
            self.clipdraw(0, x, col.name, attr, col.width)

            y = 1
            for rowidx in range(0, len(visibleRows)):
                if rowidx == self.rowIndex:  # cursor at this row
                    attr = curses.A_UNDERLINE
                else:
                    attr = curses.A_NORMAL

                row = visibleRows[rowidx]
                self.clipdraw(y, x, row[colidx], attr, col.width)
                y += 1

            x += col.width+1
            if x > self.winWidth:
                break

    def clipdraw(self, y, x, s, attr=curses.A_NORMAL, w=None):
        if w is None:
            w = self.winWidth
        w = min(w, self.winWidth-x)
        if len(s) > w:
            self.scr.addstr(y, x, s[:w-3] + '...', attr)
        else:
            self.scr.addstr(y, x, s, attr)

    def status(self, s):
        self.clipdraw(self.winHeight-1, 0, s)
        self.scr.clrtoeol()

    def error(self, s):
        self.clipdraw(self.winHeight-2, 0, s)
        self.scr.clrtoeol()


def sheet_from_file(fn):
    if fn.endswith('.tsv'):
        fetcher = TsvFetcher(fn)
    else:
        raise VException('No parser available for %s' % fn)
    vs = VSheet(fetcher)
    return vs


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

    global g_args
    parser = argparse.ArgumentParser(description='Visidata ' + str(__version__) + ' by saul.pw')

    parser.add_argument('inputs', nargs='*', help='initial sheets')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False, help='abort on exception')
    g_args = parser.parse_args()

    vd = Visidata()
    vd.sheets = [sheet_from_file(fn) for fn in g_args.inputs] or sheet_from_file('.')

    wrapper(curses_main, vd)


def curses_main(scr, sheet):
    result = "DONTQUIT"
    while result and result != "QUIT":
        result = sheet.run(scr)

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


