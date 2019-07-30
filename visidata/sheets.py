import collections
import functools
import threading
import re
from unittest import mock
from copy import copy
import textwrap

from visidata import VisiData, Extensible, globalCommand, ColumnAttr, ColumnItem, vd, ENTER, EscapeException, LazyMap
from visidata import (Command, bindkeys, commands, options, theme, isNullFunc, isNumeric, Column, option,
TypedExceptionWrapper, getGlobals, LazyMapRow, BaseSheet, UNLOADED,
vd, exceptionCaught, getType, clipdraw, ColorAttr, colors, undoEditCell, undoEditCells, undoAttr, undoBlocked)


__all__ = ['RowColorizer', 'CellColorizer', 'ColumnColorizer', 'Sheet', 'SheetsSheet']


option('default_width', 20, 'default column width', replay=True)   # TODO: make not replay and remove from markdown saver
option('textwrap_cells', True, 'wordwrap text for multiline rows')

option('cmd_after_edit', 'go-down', 'command longname to execute after successful edit')
option('quitguard', False, 'confirm before quitting last sheet')
option('debug', False, 'exit on error and display stacktrace')
theme('force_256_colors', False, 'use 256 colors even if curses reports fewer')
theme('use_default_colors', False, 'curses use default terminal colors')

theme('disp_note_none', '⌀',  'visible contents of a cell whose value is None')
theme('disp_truncator', '…', 'indicator that the contents are only partially visible')
theme('disp_oddspace', '\u00b7', 'displayable character for odd whitespace')
theme('disp_status_fmt', '{sheet.shortcut}〉{sheet.name}| ', 'status line prefix')
theme('disp_lstatus_max', 0, 'maximum length of left status line')
theme('disp_status_sep', ' | ', 'separator between statuses')
theme('disp_more_left', '<', 'header note indicating more columns to the left')
theme('disp_more_right', '>', 'header note indicating more columns to the right')
theme('disp_error_val', '', 'displayed contents for computation exception')
theme('disp_ambig_width', 1, 'width to use for unicode chars marked ambiguous')

theme('color_keystrokes', 'white', 'color of input keystrokes on status line')
theme('color_status', 'bold', 'status line color')
theme('color_error', 'red', 'error message color')
theme('color_warning', 'yellow', 'warning message color')

theme('disp_pending', '', 'string to display in pending cells')
theme('note_pending', '⌛', 'note to display for pending cells')
theme('note_format_exc', '?', 'cell note for an exception during formatting')
theme('note_getter_exc', '!', 'cell note for an exception during computation')
theme('note_type_exc', '!', 'cell note for an exception during type conversion')
theme('note_unknown_type', '', 'cell note for unknown types in anytype column')

theme('color_note_pending', 'bold magenta', 'color of note in pending cells')
theme('color_note_type', '226 yellow', 'cell note for numeric types in anytype columns')
theme('scroll_incr', 3, 'amount to scroll with scrollwheel')
theme('disp_column_sep', '╵', 'separator between columns')
theme('disp_keycol_sep', '║', 'separator between key columns and rest of columns')
theme('disp_rowtop_sep', '│', '') # ╷│┬╽⌜⌐▇
theme('disp_rowmid_sep', '│', '') # ┃┊│█
theme('disp_rowbot_sep', '╵', '') # ┊┴╿⌞█⍿╵⎢┴⌊
theme('disp_rowend_sep', '║', '') # ┊┴╿⌞█⍿╵⎢┴⌊
theme('disp_keytop_sep', '║', '') # ╽╿┃╖╟
theme('disp_keymid_sep', '║', '') # ╽╿┃
theme('disp_keybot_sep', '║', '') # ╽╿┃╜‖
theme('disp_endtop_sep', '║', '') # ╽╿┃╖╢
theme('disp_endmid_sep', '║', '') # ╽╿┃
theme('disp_endbot_sep', '║', '') # ╽╿┃╜‖

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


def splitcell(s, width=0):
    if width <= 0 or not options.textwrap_cells:
        return [s]

    ret = []
    for L in s.splitlines():
        ret.extend(textwrap.wrap(L, width=width, break_long_words=False, replace_whitespace=False))
    return ret

disp_column_fill = ' ' # pad chars after column value

# higher precedence color overrides lower; all non-color attributes combine
# coloropt is the color option name (like 'color_error')
# func(sheet,col,row,value) should return a true value if coloropt should be applied
# if coloropt is None, func() should return a coloropt (or None) instead
RowColorizer = collections.namedtuple('RowColorizer', 'precedence coloropt func')
CellColorizer = collections.namedtuple('CellColorizer', 'precedence coloropt func')
ColumnColorizer = collections.namedtuple('ColumnColorizer', 'precedence coloropt func')



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
        RowColorizer(2, 'color_selected_row', lambda s,c,r,v: s.isSelected(r)),
        RowColorizer(1, 'color_error', lambda s,c,r,v: isinstance(r, (Exception, TypedExceptionWrapper))),
    ]
    nKeys = 0  # columns[:nKeys] are key columns

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.rows = UNLOADED      # list of opaque row objects (UNLOADED before first reload)
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorVisibleColIndex = 0  # index of cursor into self.visibleCols

        self.topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftVisibleColIndex = 0    # cursorVisibleColIndex of leftmost column
        self.rightVisibleColIndex = 0

        # as computed during draw()
        self.rowLayout = {}      # [rowidx] -> (y, w)
        self.visibleColLayout = {}      # [vcolidx] -> (x, w)

        # list of all columns in display order
        self.columns = kwargs.get('columns') or [copy(c) for c in self.columns] or [Column('')]
        self.recalc()  # set .sheet on columns and start caches

        self.setKeys(self.columns[:self.nKeys])  # initial list of key columns

        self.__dict__.update(kwargs)  # also done earlier in BaseSheet.__init__

    def __len__(self):
        return self.nRows

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

    def colorize(self, col, row, value=None) -> ColorAttr:
        'Returns ColorAttr for the given col/row/value'

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

    @property
    @functools.lru_cache()
    def colsByName(self):
        'Return dict of colname:col'
        # dict comprehension in reverse order so first column with the name is used
        return {col.name:col for col in self.columns[::-1]}

    def column(self, colname):
        'Return first column whose Column.name matches colname.'
        return self.colsByName.get(colname) or vd.fail('no column matching "%s"' % colname)

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
        ret.rows = UNLOADED
        ret.columns = [copy(c) for c in self.keyCols]
        ret.setKeys(ret.columns)
        ret.columns.extend(copy(c) for c in self.columns if c not in self.keyCols)
        ret.recalc()  # set .sheet on columns
        ret.topRowIndex = ret.cursorRowIndex = 0
        return ret

    @property
    def bottomRowIndex(self):
        return max(self.rowLayout.keys())

    def __deepcopy__(self, memo):
        'same as __copy__'
        ret = self.__copy__()
        memo[id(self)] = ret
        return ret

    def __repr__(self):
        return self.name

    def evalexpr(self, expr, row=None):
        return eval(expr, getGlobals(), LazyMapRow(self, row) if row is not None else None)

    def rowid(self, row):
        'Return a fast, unique, and stable hash of the given row object.  Must be fast.  Overrideable.'
        return id(row)

    @property
    def nVisibleRows(self):
        'Number of visible rows at the current window height.'
        return len(self.rowLayout) or (self.windowHeight-self.nHeaderRows-self.nFooterRows)

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
        return vcols[min(self.cursorVisibleColIndex, len(vcols)-1)] if vcols else None

    @property
    def cursorRow(self):
        'The row object at the row cursor.'
        return self.rows[self.cursorRowIndex] if self.nRows > 0 else None

    @property
    def visibleRows(self):  # onscreen rows
        'List of rows onscreen.'
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

    def visibleRowAtY(self, y):
        for rowidx, (rowy, h) in self.rowLayout.items():
            if rowy <= y <= rowy+h-1:
                return rowidx

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

    def addColumn(self, col, index=None):
        'Insert column at given index or after all columns.'
        if col:
            if index is None:
                index = len(self.columns)
            col.recalc(self)
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
        y = self.cursorRowIndex - self.topRowIndex + self.nHeaderRows

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
                if cur_x+cur_w < self.windowWidth:  # current columns fit entirely on screen
                    break
                self.leftVisibleColIndex += 1  # once within the bounds, walk over one column at a time

    def calcColLayout(self):
        'Set right-most visible column, based on calculation.'
        minColWidth = len(options.disp_more_left)+len(options.disp_more_right)
        sepColWidth = len(options.disp_column_sep)
        winWidth = self.windowWidth
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
        sepcattr = ColorAttr(colors.color_column_sep)

        hdrcattr = self.colorize(col, None)
        if vcolidx == self.cursorVisibleColIndex:
            hdrcattr = hdrcattr.update_attr(colors.color_current_hdr, 2)

        C = options.disp_column_sep
        if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
            C = options.disp_keycol_sep

        x, colwidth = self.visibleColLayout[vcolidx]

        # AnameTC
        T = getType(col.type).icon
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
                hdrcattr = hdrcattr.update_attr(colors.color_bottom_hdr, 5)

            clipdraw(scr, y+i, x, name, hdrcattr.attr, colwidth)
            vd.onMouse(scr, y+i, x, 1, colwidth, BUTTON3_RELEASED='rename-col')

            if C and x+colwidth+len(C) < self.windowWidth:
                scr.addstr(y+i, x+colwidth, C, sepcattr.attr)

        clipdraw(scr, y+h-1, x+colwidth-len(T), T, hdrcattr.attr, len(T))

        try:
            if vcolidx == self.leftVisibleColIndex and col not in self.keyCols and self.nonKeyVisibleCols.index(col) > 0:
                A = options.disp_more_left
                scr.addstr(y, x, A, sepcattr.attr)
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

        isNull = isNullFunc()

        self.rowLayout = {}  # [rowidx] -> (y, height)
        self.calcColLayout()

        numHeaderRows = self.nHeaderRows
        vcolidx = 0

        headerRow = 0
        for vcolidx, colinfo in sorted(self.visibleColLayout.items()):
            self.drawColHeader(scr, headerRow, numHeaderRows, vcolidx)

        y = headerRow + numHeaderRows

        rows = self.rows[self.topRowIndex:min(self.topRowIndex+self.nVisibleRows, self.nRows)]
        self.checkCursorNoExceptions()

        for rowidx, row in enumerate(rows):
            if y >= self.windowHeight-1:
                break

            rowcattr = self.colorize(None, row)

            y += self.drawRow(scr, row, self.topRowIndex+rowidx, y, rowcattr, maxheight=self.windowHeight-y, isNull=isNull)

        if vcolidx+1 < self.nVisibleCols:
            scr.addstr(headerRow, self.windowWidth-2, options.disp_more_right, colors.color_column_sep)

        scr.refresh()

    def drawRow(self, scr, row, rowidx, ybase, rowcattr: ColorAttr, maxheight, isNull=None):
            topsep = options.disp_rowtop_sep
            midsep = options.disp_rowmid_sep
            botsep = options.disp_rowbot_sep
            endsep = options.disp_rowend_sep
            keytopsep = options.disp_keytop_sep
            keymidsep = options.disp_keymid_sep
            keybotsep = options.disp_keybot_sep
            endtopsep = options.disp_endtop_sep
            endmidsep = options.disp_endmid_sep
            endbotsep = options.disp_endbot_sep

            colsep = options.disp_column_sep
            keysep = options.disp_keycol_sep

            # sepattr is the attr between cell/columns
            sepcattr = rowcattr.update_attr(colors.color_column_sep, newprec=1)

            # apply current row here instead of in a colorizer, because it needs to know dispRowIndex
            if rowidx == self.cursorRowIndex:
                color_current_row = ColorAttr(colors.color_current_row, 5)
                basecellcattr = rowcattr.update_attr(color_current_row)
                sepcattr = rowcattr
                sepcattr = sepcattr.update_attr(color_current_row)
            else:
                basecellcattr = rowcattr

            displines = {}  # [vcolidx] -> list of lines in that cell

            for vcolidx, (x, colwidth) in sorted(self.visibleColLayout.items()):
                if x < self.windowWidth:  # only draw inside window
                    vcols = self.visibleCols
                    if vcolidx >= len(vcols):
                        continue
                    col = vcols[vcolidx]
                    cellval = col.getCell(row)
                    if colwidth > 1 and isNumeric(col):
                        cellval.display = cellval.display.rjust(colwidth-2)

                    try:
                        if isNull(cellval.value):
                            cellval.note = options.disp_note_none
                            cellval.notecolor = 'color_note_type'
                    except (TypeError, ValueError):
                        pass

                    displines[vcolidx] = (col, cellval, splitcell(cellval.display, width=colwidth-2))

            heights = [0]
            for col, cellval, lines in displines.values():
                h = len(lines)   # of this cell
                heights.append(min(col.height, h))

            height = min(max(heights), maxheight) or 1  # display even empty rows

            self.rowLayout[rowidx] = (ybase, height)

            for vcolidx, (col, cellval, lines) in displines.items():
                    if vcolidx not in self.visibleColLayout:
                        continue
                    x, colwidth = self.visibleColLayout[vcolidx]

                    cattr = self.colorize(col, row, cellval)
                    cattr = cattr.update_attr(basecellcattr)

                    note = getattr(cellval, 'note', None)
                    if note:
                        notecattr = cattr.update_attr(colors.get_color(cellval.notecolor), 10)
                        clipdraw(scr, ybase, x+colwidth-len(note), note, notecattr.attr, len(note))

                    if len(lines) > height:
                        firstn = sum(len(i)+1 for i in lines[:height-1])
                        lines[height-1] = cellval.display[firstn:]
                        del lines[height:]
                    elif len(lines) < height:
                        lines.extend(['']*(height-len(lines)))

                    for i, line in enumerate(lines):
                        y = ybase+i

                        if vcolidx == self.rightVisibleColIndex:  # right edge of sheet
                            if len(lines) == 1:
                                sepchars = endsep
                            else:
                                if i == 0:
                                    sepchars = endtopsep
                                elif i == len(lines)-1:
                                    sepchars = endbotsep
                                else:
                                    sepchars = endmidsep
                        elif (self.keyCols and col is self.keyCols[-1]): # last keycol
                            if len(lines) == 1:
                                sepchars = keysep
                            else:
                                if i == 0:
                                    sepchars = keytopsep
                                elif i == len(lines)-1:
                                    sepchars = keybotsep
                                else:
                                    sepchars = keymidsep
                        else:
                            if len(lines) == 1:
                                sepchars = colsep
                            else:
                                if i == 0:
                                    sepchars = topsep
                                elif i == len(lines)-1:
                                    sepchars = botsep
                                else:
                                    sepchars = midsep

                        clipdraw(scr, y, x, disp_column_fill+line, cattr.attr, colwidth-(1 if note else 0))
                        vd.onMouse(scr, y, x, 1, colwidth, BUTTON3_RELEASED='edit-cell')

                        if x+colwidth+len(sepchars) <= self.windowWidth:
                            scr.addstr(y, x+colwidth, sepchars, sepcattr.attr)

            return height


class SheetsSheet(Sheet):
    rowtype = 'sheets'
    precious = False
    defer = False
    columns = [
        ColumnAttr('name', width=30),
        ColumnAttr('shortcut'),
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
        ColumnAttr('nVisibleCols', type=int),
        ColumnAttr('cursorDisplay'),
        ColumnAttr('keyColNames'),
        ColumnAttr('source'),
        ColumnAttr('progressPct'),
#        ColumnAttr('threads', 'currentThreads', type=vlen),
    ]
    colorizers = [
        RowColorizer(1.5, 'color_hidden_col', lambda s,c,r,v: r and r not in vd.sheets),
    ]
    nKeys = 1

    def newRow(self):
        return Sheet('', columns=[ColumnItem('', 0)], rows=[])

    def reload(self):
        self.rows = self.source


## VisiData sheet manipulation

@VisiData.global_api
def replace(vd, vs):
    'Replace top sheet with the given sheet `vs`.'
    vd.sheets.pop(0)
    return vd.push(vs)


@VisiData.global_api
def remove(vd, vs):
    if vs in vd.sheets:
        vd.sheets.remove(vs)
        if vs in vd.allSheets:
            vd.allSheets.remove(vs)
            vd.allSheets.append(vs)
    else:
        vd.fail('sheet not on stack')


@VisiData.global_api
def push(vd, vs, sheets=None):
    'Move given sheet `vs` to index 0 of list `sheets`.'
    if sheets is None:
        sheets = vd.sheets

    if not isinstance(vs, BaseSheet):
        return  # return instead of raise, some commands
    else:
        vs.vd = vd
        if vs in sheets:
            sheets.remove(vs)
        else:
            vs.creatingCommand = vd.cmdlog and vd.cmdlog.currentActiveRow

        sheets.insert(0, vs)

        if vs.rows is UNLOADED:
            vs.rows = []  # prevent auto-reload from running twice
            vs.reload()
            vs.recalc()  # set up Columns

        if vs.precious and vs not in vd.allSheets:
            vd.allSheets.append(vs)
            vs.shortcut = len(vd.allSheets)
        elif hasattr(vs, 'creatingCommand') and vs.creatingCommand:
            vs.shortcut = vs.shortcut or vs.creatingCommand.keystrokes


@VisiData.cached_property
def sheetsSheet(vd):
    return SheetsSheet("sheets_all", source=vd.allSheets)


@VisiData.api
def quit(self):
    if len(vd.sheets) == 1 and options.quitguard:
        vd.confirm("quit last sheet? ")
    return vd.remove(vd.sheets[0])


undoRestoreKey = undoAttr('[cursorCol]', 'keycol')

globalCommand('zS', 'sheets-stack', 'vd.push(SheetsSheet("sheets", source=vd.sheets))')
globalCommand('S', 'sheets-all', 'vd.push(vd.sheetsSheet)')

BaseSheet.addCommand('^R', 'reload-sheet', 'reload(); recalc(); status("reloaded")'),
Sheet.addCommand('^G', 'show-cursor', 'status(statusLine)'),

Sheet.addCommand('!', 'key-col', 'toggleKeys([cursorCol])', undo=undoRestoreKey),
Sheet.addCommand('z!', 'key-col-off', 'unsetKeys([cursorCol])', undo=undoRestoreKey),

Sheet.addCommand('e', 'edit-cell', 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex)); options.cmd_after_edit and sheet.exec_keystrokes(options.cmd_after_edit)', undo=undoEditCell)
Sheet.addCommand('ge', 'setcol-input', 'cursorCol.setValuesTyped(selectedRows, input("set selected to: ", value=cursorDisplay))', undo=undoEditCells),

Sheet.addCommand('"', 'dup-selected', 'vs=copy(sheet); vs.name += "_selectedref"; vs.reload=lambda vs=vs,rows=selectedRows: setattr(vs, "rows", list(rows)); vd.push(vs)'),
Sheet.addCommand('g"', 'dup-rows', 'vs=copy(sheet); vs.name+="_copy"; vs.rows=list(rows); status("copied "+vs.name); vs.select(selectedRows); vd.push(vs)'),
Sheet.addCommand('z"', 'dup-selected-deep', 'vs = deepcopy(sheet); vs.name += "_selecteddeepcopy"; vs.rows = async_deepcopy(vs, selectedRows); vd.push(vs); status("pushed sheet with async deepcopy of selected rows")'),
Sheet.addCommand('gz"', 'dup-rows-deep', 'vs = deepcopy(sheet); vs.name += "_deepcopy"; vs.rows = async_deepcopy(vs, rows); vd.push(vs); status("pushed sheet with async deepcopy of all rows")'),

undoColType = undoAttr('[cursorCol]', 'type')

Sheet.addCommand('z~', 'type-any', 'cursorCol.type = anytype', undo=undoColType),
Sheet.addCommand('~', 'type-string', 'cursorCol.type = str', undo=undoColType),
Sheet.addCommand('@', 'type-date', 'cursorCol.type = date', undo=undoColType),
Sheet.addCommand('#', 'type-int', 'cursorCol.type = int', undo=undoColType),
Sheet.addCommand('z#', 'type-len', 'cursorCol.type = vlen', undo=undoColType),
Sheet.addCommand('$', 'type-currency', 'cursorCol.type = currency', undo=undoColType),
Sheet.addCommand('%', 'type-float', 'cursorCol.type = float', undo=undoColType),

SheetsSheet.addCommand(ENTER, 'open-row', 'dest=cursorRow; vd.sheets.remove(sheet) if not sheet.precious else None; vd.push(dest)')
SheetsSheet.addCommand('g'+ENTER, 'open-rows', 'for vs in selectedRows: vd.push(vs)')
SheetsSheet.addCommand('g^R', 'reload-selected', 'for vs in selectedRows or rows: vs.reload()')
SheetsSheet.addCommand('gC', 'columns-selected', 'vd.push(ColumnsSheet("all_columns", source=selectedRows))')
SheetsSheet.addCommand('gI', 'describe-selected', 'vd.push(DescribeSheet("describe_all", source=selectedRows))')
SheetsSheet.addCommand('z^C', 'cancel-row', 'cancelThread(*cursorRow.currentThreads)')
SheetsSheet.addCommand('gz^C', 'cancel-rows', 'for vs in selectedRows: cancelThread(*vs.currentThreads)')

globalCommand('q', 'quit-sheet',  'vd.quit()')
globalCommand('gq', 'quit-all', 'vd.sheets.clear()')

globalCommand('^L', 'redraw', 'sheet.refresh()')

BaseSheet.bindkey('KEY_RESIZE', 'redraw')
