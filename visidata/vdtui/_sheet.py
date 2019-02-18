import collections
import functools
import threading
import re
from copy import copy

from visidata.vdtui import (Command, bindkeys, commands, options, theme, isNullFunc, error, Column,
TypedExceptionWrapper, regex_flags, getGlobals, LazyMapRow,
vd, exceptionCaught, status, catchapply, bindkey, typeIcon, clipdraw, BaseSheet, CursesAttr, colors, input, undoEditCell, undoEditCells, undoAttr)


__all__ = [ 'RowColorizer', 'CellColorizer', 'ColumnColorizer', 'Sheet' ]


disp_column_fill = ' ' # pad chars after column value

# higher precedence color overrides lower; all non-color attributes combine
# coloropt is the color option name (like 'color_error')
# func(sheet,col,row,value) should return a true value if coloropt should be applied
# if coloropt is None, func() should return a coloropt (or None) instead
RowColorizer = collections.namedtuple('RowColorizer', 'precedence coloropt func')
CellColorizer = collections.namedtuple('CellColorizer', 'precedence coloropt func')
ColumnColorizer = collections.namedtuple('ColumnColorizer', 'precedence coloropt func')

theme('color_default', 'normal', 'the default color')
theme('color_default_hdr', 'bold', 'color of the column headers')
theme('color_bottom_hdr', 'underline', 'color of the bottom header row')
theme('color_current_row', 'reverse', 'color of the cursor row')
theme('color_current_col', 'bold', 'color of the cursor column')
theme('color_current_hdr', 'bold reverse', 'color of the header for the cursor column')
theme('color_column_sep', '246 blue', 'color of column separators')
theme('color_key_col', '81 cyan', 'color of key columns')
theme('color_hidden_col', '8', 'color of hidden columns on metasheets')
theme('color_selected_row', '215 yellow', 'color of selected rows')


class Sheet(BaseSheet):
    'Base class for all tabular sheets.'
    _rowtype = lambda: collections.defaultdict(lambda: None)
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
        def allParents(cls):
            yield from cls.__bases__
            for b in cls.__bases__:
                yield from allParents(b)

        for b in [self] + list(allParents(self.__class__)):
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
        ret = super().__copy__()
        ret.rows = []                     # a fresh list without incurring any overhead
        ret.columns = [copy(c) for c in self.keyCols]
        ret.setKeys(ret.columns)
        ret.columns.extend(copy(c) for c in self.columns if c not in self.keyCols)
        ret.recalc()  # set .sheet on columns
        ret.topRowIndex = ret.cursorRowIndex = 0
        return ret

    def __deepcopy__(self, memo):
        'same as __copy__'
        ret = self.__copy__()
        memo[id(self)] = ret
        return ret

    def __repr__(self):
        return self.name

    def evalexpr(self, expr, row=None):
        return eval(expr, getGlobals(), LazyMapRow(self, row) if row is not None else None)

    @property
    def nVisibleRows(self):
        'Number of visible rows at the current window height.'
        return vd.windowHeight-self.nHeaderRows-self.nFooterRows

    @property
    @functools.lru_cache()  # cache for perf reasons on wide sheets.  cleared in vd.clear_caches()
    def nHeaderRows(self):
        vcols = self.visibleCols
        return max(len(col.name.split('\n')) for col in vcols) if vcols else 0

    @property
    def nFooterRows(self):
        'Number of lines reserved at the bottom, including status line.'
        return 1

    @property
    def cursorCol(self):
        'Current Column object.'
        vcols = self.visibleCols
        return vcols[min(self.cursorVisibleColIndex, len(vcols)-1)]

    @property
    def cursorRow(self):
        'The row object at the row cursor.'
        return self.rows[self.cursorRowIndex] if self.rows else None

    @property
    def visibleRows(self):  # onscreen rows
        'List of rows onscreen. '
        return self.rows[self.topRowIndex:self.topRowIndex+self.nVisibleRows]

    @property
    @functools.lru_cache()  # cache for perf reasons on wide sheets.  cleared in vd.clear_caches()
    def visibleCols(self):  # non-hidden cols
        'List of `Column` which are not hidden.'
        return self.keyCols + [c for c in self.columns if not c.hidden and not c.keycol]

    def visibleColAtX(self, x):
        for vcolidx, (colx, w) in self.visibleColLayout.items():
            if colx <= x <= colx+w:
                return vcolidx
        error('no visible column at x=%d' % x)

    @property
    @functools.lru_cache()  # cache for perf reasons on wide sheets.  cleared in vd.clear_caches()
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
        rowinfo = 'row %d/%d (%d selected)' % (self.cursorRowIndex, self.nRows, self.nSelected)
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
            Sheet.visibleCols.fget.cache_clear()
            return col

    def setColNames(self, rows):
        for c in self.visibleCols:
            c.name = '\n'.join(str(c.getDisplayValue(r)) for r in rows)

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
        return tuple(c.getTypedValue(row) for c in self.keyCols)

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
        y = self.cursorRowIndex - self.topRowIndex + self.nHeaderRows  # header

        # check bounds, scroll if necessary
        if y < self.nHeaderRows:
            self.topRowIndex = self.cursorRowIndex
        elif y > self.nHeaderRows+self.nVisibleRows-1:
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
                if cur_x+cur_w < vd.windowWidth:  # current columns fit entirely on screen
                    break
                self.leftVisibleColIndex += 1  # once within the bounds, walk over one column at a time

    def calcColLayout(self):
        'Set right-most visible column, based on calculation.'
        minColWidth = len(options.disp_more_left)+len(options.disp_more_right)
        sepColWidth = len(options.disp_column_sep)
        winWidth = vd.windowWidth
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

    def drawColHeader(self, scr, y, h, vcolidx):
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

        # AnameTC
        T = typeIcon(col.type)
        if T is None:  # still allow icon to be explicitly non-displayed ''
            T = '?'

        hdrs = col.name.split('\n')
        for i in range(h):
            name = ' '  # save room at front for LeftMore
            if h-i-1 < len(hdrs):
                name += hdrs[::-1][h-i-1]

            if len(name) > colwidth-1:
                name = name[:colwidth-len(options.disp_truncator)] + options.disp_truncator

            if i == h-1:
                hdrattr = hdrattr.update_attr(colors.color_bottom_hdr, 5)

            clipdraw(scr, y+i, x, name, hdrattr.attr, colwidth)
            vd.onMouse(scr, y+i, x, 1, colwidth, BUTTON3_RELEASED='rename-col')

            if C and x+colwidth+len(C) < vd.windowWidth:
                scr.addstr(y+i, x+colwidth, C, sepattr)

        clipdraw(scr, y+h-1, x+colwidth-len(T), T, hdrattr.attr, len(T))

        try:
            if vcolidx == self.leftVisibleColIndex and col not in self.keyCols and self.nonKeyVisibleCols.index(col) > 0:
                A = options.disp_more_left
                scr.addstr(y, x, A, sepattr)
        except ValueError:  # from .index
            pass

    def isVisibleIdxKey(self, vcolidx):
        'Return boolean: is given column index a key column?'
        return self.visibleCols[vcolidx] in self.keyCols

    def draw(self, scr):
        'Draw entire screen onto the `scr` curses object.'
        scr.erase()  # clear screen before every re-draw

        vd.clear_caches()

        if not self.columns:
            return

        color_current_row = CursesAttr(colors.color_current_row, 5)
        disp_column_sep = options.disp_column_sep

        rowattrs = {}  # [rowidx] -> attr
        colattrs = {}  # [colidx] -> attr
        isNull = isNullFunc()

        self.rowLayout = {}
        self.calcColLayout()

        numHeaderRows = self.nHeaderRows
        vcolidx = 0
        rows = list(self.rows[self.topRowIndex:self.topRowIndex+self.nVisibleRows])
        for vcolidx, colinfo in sorted(self.visibleColLayout.items()):
            x, colwidth = colinfo
            col = self.visibleCols[vcolidx]

            if x < vd.windowWidth:  # only draw inside window
              timer = threading.Timer(0.3, lambda col=col: status("setting %s async" % col.name) and col.setCache('async'))
              timer.start()
              try:
                headerRow = 0
                self.drawColHeader(scr, headerRow, numHeaderRows, vcolidx)

                y = headerRow + numHeaderRows
                for rowidx in range(0, min(len(rows), self.nVisibleRows)):
                    dispRowIdx = self.topRowIndex + rowidx
                    if dispRowIdx >= self.nRows:
                        break

                    self.rowLayout[dispRowIdx] = y

                    row = rows[rowidx]
                    cellval = col.getCell(row, colwidth-1)
                    try:
                        if isNull(cellval.value):
                            cellval.note = options.disp_note_none
                            cellval.notecolor = 'color_note_type'
                    except TypeError:
                        pass

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
                    vd.onMouse(scr, y, x, 1, colwidth, BUTTON3_RELEASED='edit-cell')

                    sepchars = disp_column_sep
                    if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
                        sepchars = options.disp_keycol_sep

                    if x+colwidth+len(sepchars) <= vd.windowWidth:
                       scr.addstr(y, x+colwidth, sepchars, sepattr.attr)

                    y += 1
              finally:
                    timer.cancel()

        if vcolidx+1 < self.nVisibleCols:
            scr.addstr(headerRow, vd.windowWidth-2, options.disp_more_right, colors.color_column_sep)

        catchapply(self.checkCursor)


Sheet.addCommand(None, 'go-left',  'cursorRight(-1)'),
Sheet.addCommand(None, 'go-down',  'cursorDown(+1)'),
Sheet.addCommand(None, 'go-up',    'cursorDown(-1)'),
Sheet.addCommand(None, 'go-right', 'cursorRight(+1)'),
Sheet.addCommand(None, 'next-page', 'cursorDown(nVisibleRows); sheet.topRowIndex += nVisibleRows'),
Sheet.addCommand(None, 'prev-page', 'cursorDown(-nVisibleRows); sheet.topRowIndex -= nVisibleRows'),

Sheet.addCommand(None, 'go-leftmost', 'sheet.cursorVisibleColIndex = sheet.leftVisibleColIndex = 0'),
Sheet.addCommand(None, 'go-top', 'sheet.cursorRowIndex = sheet.topRowIndex = 0'),
Sheet.addCommand(None, 'go-bottom', 'sheet.cursorRowIndex = len(rows); sheet.topRowIndex = cursorRowIndex-nVisibleRows'),
Sheet.addCommand(None, 'go-rightmost', 'sheet.leftVisibleColIndex = len(visibleCols)-1; pageLeft(); sheet.cursorVisibleColIndex = len(visibleCols)-1'),

Sheet.addCommand('BUTTON1_PRESSED', 'go-mouse', 'sheet.cursorRowIndex=topRowIndex+mouseY-1; sheet.cursorVisibleColIndex=visibleColAtX(mouseX)'),
Sheet.addCommand('BUTTON1_RELEASED', 'scroll-mouse', 'sheet.topRowIndex=cursorRowIndex-mouseY+1'),

Sheet.addCommand('BUTTON4_PRESSED', 'scroll-up', 'cursorDown(options.scroll_incr); sheet.topRowIndex += options.scroll_incr'),
Sheet.addCommand('REPORT_MOUSE_POSITION', 'scroll-down', 'cursorDown(-options.scroll_incr); sheet.topRowIndex -= options.scroll_incr'),

Sheet.bindkey('BUTTON1_CLICKED', 'go-mouse')
Sheet.bindkey('BUTTON3_PRESSED', 'go-mouse')

Sheet.addCommand('^G', 'show-cursor', 'status(statusLine)'),

Sheet.addCommand('_', 'resize-col-max', 'cursorCol.toggleWidth(cursorCol.getMaxWidth(visibleRows))'),
Sheet.addCommand('z_', 'resize-col', 'cursorCol.width = int(input("set width= ", value=cursorCol.width))'),

Sheet.addCommand('-', 'hide-col', 'cursorCol.hide()', undo=undoAttr('[cursorCol]', 'width'))
Sheet.addCommand('z-', 'resize-col-half', 'cursorCol.width = cursorCol.width//2'),
Sheet.addCommand('gv', 'unhide-cols', 'for c in columns: c.width = abs(c.width or 0) or c.getMaxWidth(visibleRows)', undo=undoAttr('[columns]', 'width'))

undoRestoreKey = undoAttr('[cursorCol]', 'keycol')

Sheet.addCommand('!', 'key-col', 'toggleKeys([cursorCol])', undo=undoRestoreKey),
Sheet.addCommand('z!', 'key-col-off', 'unsetKeys([cursorCol])', undo=undoRestoreKey),
Sheet.addCommand('g_', 'resize-cols-max', 'for c in visibleCols: c.width = c.getMaxWidth(visibleRows)'),

Sheet.addCommand('^R', 'reload-sheet', 'reload(); recalc(); status("reloaded")'),

Sheet.addCommand('e', 'edit-cell', 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex)); options.cmd_after_edit and sheet.exec_keystrokes(options.cmd_after_edit)', undo=undoEditCell)
Sheet.addCommand('ge', 'edit-cells', 'cursorCol.setValuesTyped(selectedRows or rows, input("set selected to: ", value=cursorDisplay))', undo=undoEditCells),

Sheet.addCommand('"', 'dup-selected', 'vs=copy(sheet); vs.name += "_selectedref"; vs.rows=tuple(); vs.reload=lambda vs=vs,rows=selectedRows or rows: setattr(vs, "rows", list(rows)); vd.push(vs)'),
Sheet.addCommand('g"', 'dup-rows', 'vs = copy(sheet); vs.name += "_copy"; vs.rows = list(rows); vs.select(selectedRows); vd.push(vs)'),
Sheet.addCommand('z"', 'dup-selected-deep', 'vs = deepcopy(sheet); vs.name += "_selecteddeepcopy"; vs.rows = async_deepcopy(vs, selectedRows or rows); vd.push(vs); status("pushed sheet with async deepcopy of selected rows")'),
Sheet.addCommand('gz"', 'dup-rows-deep', 'vs = deepcopy(sheet); vs.name += "_deepcopy"; vs.rows = async_deepcopy(vs, rows); vd.push(vs); status("pushed sheet with async deepcopy of all rows")'),

bindkey('KEY_LEFT', 'go-left')
bindkey('KEY_DOWN', 'go-down')
bindkey('KEY_UP', 'go-up')
bindkey('KEY_RIGHT', 'go-right')
bindkey('KEY_HOME', 'go-top')
bindkey('KEY_END', 'go-bottom')
bindkey('KEY_NPAGE', 'next-page')
bindkey('KEY_PPAGE', 'prev-page')

bindkey('gKEY_LEFT', 'go-leftmost'),
bindkey('gKEY_RIGHT', 'go-rightmost'),
bindkey('gKEY_UP', 'go-top'),
bindkey('gKEY_DOWN', 'go-bottom'),
