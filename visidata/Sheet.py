import collections
import functools
import re

import visidata
from . import colors, options, status, error, date, anytype, WrongTypeStr, CalcErrorStr, vd, moveListItem
from .tui import draw_clip
from .Column import Column

base_commands = collections.OrderedDict()

class Sheet:
    def __init__(self, name, src=None):
        self.name = name
        self.filetype = None
        self.source = src
        self.rows = []
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorVisibleColIndex = 0  # index of cursor into self.visibleCols

        self.topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftVisibleColIndex = 0    # cursorVisibleColIndex of leftmost column

        # as computed during draw()
        self.rowLayout = {}      # [rowidx] -> y
        self.visibleColLayout = {}      # [vcolidx] -> (x, w)

        # all columns in display order
        self.columns = []
        self.nKeys = 0           # self.columns[:nKeys] are all pinned to the left and matched on join

        # current search term
        self.currentRegex = None
        self.currentRegexColumns = None

        self._selectedRows = {}   # id(row) -> row

        # specialized sheet keys
        self.commands = base_commands.copy()

    def __repr__(self):
        return self.name

    def isSelected(self, r):
        return id(r) in self._selectedRows

    def command(self, key, cmdstr, helpstr=''):
#        if key in self.commands:
#            status('overriding key %s' % key)
        self.commands[('', key)] = (cmdstr, helpstr)

    def exec_command(self, vdglobals, prefixes, key):
        cmdstr, _ = self.commands.get((prefixes, key))
        # handy globals for use by commands
        self.vd = vd()
        self.sheet = self
        exec(cmdstr, vdglobals, dict((name, getattr(self, name)) for name in dir(self)))


    def findColIdx(self, colname, columns=None):
        if columns is None:
            columns = self.columns
        cols = list(colidx for colidx, c in enumerate(columns) if c.name == colname)
        if not cols:
            error('no column named "%s"' % colname)
        elif len(cols) > 1:
            status('%d columns named "%s"' % (len(cols), colname))
        return cols[0]

    def clipdraw(self, y, x, s, attr, w):
        return draw_clip(self.scr, y, x, s, attr, w)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name.replace(' ', '_')

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
    def selectedRows(self):
        return [r for r in self.rows if id(r) in self._selectedRows]

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
        return 'row %s/%s (%s selected); %d/%d columns visible' % (self.cursorRowIndex, len(self.rows), len(self._selectedRows), self.nVisibleCols, self.nCols)

    @property
    def nRows(self):
        return len(self.rows)

    @property
    def nCols(self):
        return len(self.columns)

    @property
    def nVisibleCols(self):
        return len(self.visibleCols)

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
        if self.cursorColIndex >= self.nKeys: # if not a key, add it
            moveListItem(self.columns, self.cursorColIndex, self.nKeys)
            self.nKeys += 1
        else:  # otherwise move it after the last key
            self.nKeys -= 1
            moveListItem(self.columns, self.cursorColIndex, self.nKeys)

    def skipDown(self):
        pv = self.cursorValue
        for i in range(self.cursorRowIndex+1, len(self.rows)):
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
        status('selected %s/%s rows' % (len(self._selectedRows)-before, len(rows)))

    def unselect(self, rows):
        rows = list(rows)
        before = len(self._selectedRows)
        for r in rows:
            if id(r) in self._selectedRows:
                del self._selectedRows[id(r)]
        status('unselected %s/%s rows' % (before-len(self._selectedRows), len(rows)))

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

        if self.cursorVisibleColIndex <= 0:
            self.cursorVisibleColIndex = 0
        elif self.cursorVisibleColIndex >= self.nVisibleCols:
            self.cursorVisibleColIndex = self.nVisibleCols-1

        if self.topRowIndex <= 0:
            self.topRowIndex = 0
        elif self.topRowIndex > len(self.rows):
            self.topRowIndex = len(self.rows)-1

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

    def searchRegex(self, regex=None, columns=None, backward=False, moveCursor=False):
        'sets row index if moveCursor; otherwise returns list of row indexes'
        if regex:
            self.currentRegex = re.compile(regex, re.IGNORECASE)

        if not self.currentRegex:
            status('no regex')
            return []

        if columns:
            self.currentRegexColumns = columns

        if not self.currentRegexColumns:
            status('no columns given')
            return []

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
                    status('search wrapped')
                    return r
                matchingRowIndexes.append(r)

        status('%s matches for /%s/' % (len(matchingRowIndexes), self.currentRegex.pattern))

        return matchingRowIndexes

    def calcColLayout(self):
        self.visibleColLayout = {}
        x = 0
        for vcolidx in range(0, len(self.visibleCols)):
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
        typedict = {
                int: '#',
                str: '$',
                float: '%',
                date: '@',
                anytype: ' ',
            }
        T = typedict.get(col.type, '?')
        N = ' ' + (col.name or defaultColNames[vcolidx])  # save room at front for LeftMore
        if len(N) > colwidth-1:
            N = N[:colwidth-len(options.ch_Ellipsis)] + options.ch_Ellipsis
        self.clipdraw(0, x, N, hdrattr, colwidth)
        self.clipdraw(0, x+colwidth-len(T), T, hdrattr, len(T))

        if vcolidx == self.leftVisibleColIndex and vcolidx > self.nKeys:
            A = options.ch_LeftMore
            self.scr.addstr(0, x, A, colors[options.c_ColumnSep])

        C = options.ch_ColumnSep
        if x+colwidth+len(C) <= self.windowWidth:
            self.scr.addstr(0, x+colwidth, C, colors[options.c_ColumnSep])


    def draw(self, scr):
        numHeaderRows = 1
        self.scr = scr  # for clipdraw convenience
        scr.erase()  # clear screen before every re-draw

        self.windowHeight, self.windowWidth = scr.getmaxyx()
        sepchars = options.ch_ColumnSep
        if not self.columns:
            return status('no columns')

        self.rowLayout = {}
        self.calcColLayout()
        for vcolidx, colinfo in sorted(self.visibleColLayout.items()):
            x, colwidth = colinfo
            if x < self.windowWidth:  # only draw inside window
                self.drawColHeader(vcolidx)

                y = numHeaderRows
                for rowidx in range(0, self.nVisibleRows):
                    if self.topRowIndex + rowidx >= len(self.rows):
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
        if vcolidx is None:
            vcolidx = self.cursorVisibleColIndex
        x, w = self.visibleColLayout[vcolidx]
        y = self.rowLayout[self.cursorRowIndex]

        currentValue = self.cellValue(self.cursorRowIndex, vcolidx)
        r = vd().editText(y, x, w, value=currentValue, fillchar=options.ch_EditPadChar)
        return self.visibleCols[vcolidx].type(r)  # convert input to column type
