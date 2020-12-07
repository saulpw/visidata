import collections
import itertools
from copy import copy
import textwrap

from visidata import VisiData, Extensible, globalCommand, ColumnAttr, ColumnItem, vd, ENTER, EscapeException, drawcache, drawcache_property, LazyChainMap, asyncthread, ExpectedException
from visidata import (options, theme, Column, option, namedlist, SettableColumn,
TypedExceptionWrapper, BaseSheet, UNLOADED,
vd, clipdraw, ColorAttr, update_attr, colors, undoAttrFunc)
import visidata


__all__ = ['RowColorizer', 'CellColorizer', 'ColumnColorizer', 'Sheet', 'TableSheet', 'IndexSheet', 'SheetsSheet', 'LazyComputeRow', 'SequenceSheet']


option('default_width', 20, 'default column width', replay=True)   # TODO: make not replay and remove from markdown saver
option('default_height', 10, 'default column height')
option('textwrap_cells', True, 'wordwrap text for multiline rows')

option('quitguard', False, 'confirm before quitting last sheet')
option('debug', False, 'exit on error and display stacktrace')
option('skip', 0, 'skip N rows before header', replay=True)
option('header', 1, 'parse first N rows as column names', replay=True)
theme('force_256_colors', False, 'use 256 colors even if curses reports fewer')
theme('use_default_colors', False, 'curses use default terminal colors')

theme('disp_note_none', '⌀',  'visible contents of a cell whose value is None')
theme('disp_truncator', '…', 'indicator that the contents are only partially visible')
theme('disp_oddspace', '\u00b7', 'displayable character for odd whitespace')
theme('disp_more_left', '<', 'header note indicating more columns to the left')
theme('disp_more_right', '>', 'header note indicating more columns to the right')
theme('disp_error_val', '', 'displayed contents for computation exception')
theme('disp_ambig_width', 1, 'width to use for unicode chars marked ambiguous')

theme('disp_pending', '', 'string to display in pending cells')
theme('note_pending', '⌛', 'note to display for pending cells')
theme('note_format_exc', '?', 'cell note for an exception during formatting')
theme('note_getter_exc', '!', 'cell note for an exception during computation')
theme('note_type_exc', '!', 'cell note for an exception during type conversion')

theme('color_note_pending', 'bold magenta', 'color of note in pending cells')
theme('color_note_type', '226 yellow', 'color of cell note for non-str types in anytype columns')
theme('color_note_row', '220 yellow', 'color of row note on left edge')
theme('scroll_incr', 3, 'amount to scroll with scrollwheel')
theme('disp_column_sep', '|', 'separator between columns')
theme('disp_keycol_sep', '║', 'separator between key columns and rest of columns')
theme('disp_rowtop_sep', '|', '') # ╷│┬╽⌜⌐▇
theme('disp_rowmid_sep', '⁝', '') # ┃┊│█
theme('disp_rowbot_sep', '⁝', '') # ┊┴╿⌞█⍿╵⎢┴⌊  ⋮⁝
theme('disp_rowend_sep', '║', '') # ┊┴╿⌞█⍿╵⎢┴⌊
theme('disp_keytop_sep', '║', '') # ╽╿┃╖╟
theme('disp_keymid_sep', '║', '') # ╽╿┃
theme('disp_keybot_sep', '║', '') # ╽╿┃╜‖
theme('disp_endtop_sep', '║', '') # ╽╿┃╖╢
theme('disp_endmid_sep', '║', '') # ╽╿┃
theme('disp_endbot_sep', '║', '') # ╽╿┃╜‖
theme('disp_selected_note', '•', '') #
theme('disp_sort_asc', '↑↟⇞⇡⇧⇑', 'characters for ascending sort') # ↑▲↟↥↾↿⇞⇡⇧⇈⤉⤒⥔⥘⥜⥠⍏˄ˆ
theme('disp_sort_desc', '↓↡⇟⇣⇩⇓', 'characters for descending sort') # ↓▼↡↧⇂⇃⇟⇣⇩⇊⤈⤓⥕⥙⥝⥡⍖˅ˇ
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
option('name_joiner', '_', 'string to join sheet or column names')
option('value_joiner', ' ', 'string to join display values')


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

class RecursiveExprException(Exception):
    pass

class LazyComputeRow:
    'Calculate column values as needed.'
    def __init__(self, sheet, row, col=None):
        self.row = row
        self.col = col
        self.sheet = sheet
        if not hasattr(self.sheet, '_lcm'):
            self.sheet._lcm = LazyChainMap(sheet, vd, col)
        else:
            self.sheet._lcm.clear()  # reset locals on lcm

        self._usedcols = set()
        self._keys = [c.name for c in self.sheet.columns]

    def keys(self):
        return self._keys + self.sheet._lcm.keys() + ['row', 'sheet', 'col']

    def __str__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {c.name:self[c.name] for c in self.sheet.visibleCols}

    def __getattr__(self, k):
        return self.__getitem__(k)

    def __getitem__(self, colid):
        try:
            i = self._keys.index(colid)
            c = self.sheet.columns[i]
            if c is self.col:
                j = self._keys[i+1:].index(colid)
                c = self.sheet.columns[i+j+1]

        except ValueError:
            try:
                c = self.sheet._lcm[colid]
            except (KeyError, AttributeError):
                if colid == 'sheet': return self.sheet
                elif colid == 'row': c = self.row
                elif colid == 'col': c = self.col
                else:
                    raise KeyError(colid)

        if not isinstance(c, Column):  # columns calc in the context of the row of the cell being calc'ed
            return c

        if c in self._usedcols:
            raise RecursiveExprException()

        self._usedcols.add(c)
        ret = c.getTypedValue(self.row)
        self._usedcols.remove(c)
        return ret

class BasicRow(collections.defaultdict):
    def __init__(self, *args):
        collections.defaultdict.__init__(self, lambda: None, *args)
    def __bool__(self):
        return True

class TableSheet(BaseSheet):
    'Base class for sheets with row objects and column views.'
    _rowtype = lambda: BasicRow()
    _coltype = SettableColumn

    rowtype = 'rows'

    columns = []  # list of Column
    colorizers = [ # list of Colorizer
        CellColorizer(2, 'color_default_hdr', lambda s,c,r,v: r is None),
        ColumnColorizer(2, 'color_current_col', lambda s,c,r,v: c is s.cursorCol),
        ColumnColorizer(1, 'color_key_col', lambda s,c,r,v: c and c.keycol),
        CellColorizer(0, 'color_default', lambda s,c,r,v: True),
        RowColorizer(2, 'color_selected_row', lambda s,c,r,v: s.isSelected(r)),
        RowColorizer(1, 'color_error', lambda s,c,r,v: isinstance(r, (Exception, TypedExceptionWrapper))),
    ]
    nKeys = 0  # columns[:nKeys] are key columns

    def __init__(self, *names, **kwargs):
        super().__init__(*names, **kwargs)
        self.rows = UNLOADED      # list of opaque row objects (UNLOADED before first reload)
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorVisibleColIndex = 0  # index of cursor into self.visibleCols

        self._topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftVisibleColIndex = 0    # cursorVisibleColIndex of leftmost column
        self.rightVisibleColIndex = 0

        # as computed during draw()
        self._rowLayout = {}      # [rowidx] -> (y, w)
        self._visibleColLayout = {}      # [vcolidx] -> (x, w)

        # list of all columns in display order
        self.columns = kwargs.get('columns') or [copy(c) for c in self.columns] or [Column('_')]
        self._colorizers = []
        self.recalc()  # set .sheet on columns and start caches

        self.setKeys(self.columns[:self.nKeys])  # initial list of key columns

        self.__dict__.update(kwargs)  # also done earlier in BaseSheet.__init__

    @property
    def topRowIndex(self):
        return self._topRowIndex

    @topRowIndex.setter
    def topRowIndex(self, v):
        self._topRowIndex = v
        self._rowLayout.clear()

    def addColorizer(self, c):
        'Add Colorizer *c* to the list of colorizers for this sheet.'
        self._colorizers.append(c)

    def removeColorizer(self, c):
        'Remove Colorizer *c* from the list of colorizers for this sheet.'
        self._colorizers.remove(c)

    @drawcache_property
    def allColorizers(self):
        # all colorizers must be in the same bucket
        # otherwise, precedence does not get applied properly
        _colorizers = set()
        def allParents(cls):
            yield from cls.__bases__
            for b in cls.__bases__:
                yield from allParents(b)

        for b in [self] + list(allParents(self.__class__)):
            for c in getattr(b, 'colorizers', []):
                _colorizers.add(c)

        _colorizers |= set(self._colorizers)
        return sorted(_colorizers, key=lambda x: x.precedence, reverse=True)

    def _colorize(self, col, row, value=None) -> ColorAttr:
        'Returns ColorAttr for the given colorizers/col/row/value'

        colorstack = []
        for colorizer in self.allColorizers:
            try:
                r = colorizer.func(self, col, row, value)
                if r:
                    colorstack.append(colorizer.coloropt if colorizer.coloropt else r)
            except Exception as e:
                vd.exceptionCaught(e)

        return colors.resolve_colors(tuple(colorstack))

    def addRow(self, row, index=None):
        'Insert *row* at *index*, or append at end of rows if *index* is None.'
        if index is None:
            self.rows.append(row)
        else:
            self.rows.insert(index, row)
        return row

    def newRow(self):
        'Return new blank row compatible with this sheet.  Overrideable.'
        return type(self)._rowtype()

    @drawcache_property
    def colsByName(self):
        'Return dict of colname:col'
        # dict comprehension in reverse order so first column with the name is used
        return {col.name:col for col in self.columns[::-1]}

    def column(self, colname):
        'Return first column whose name matches *colname*.'
        return self.colsByName.get(colname) or vd.fail('no column matching "%s"' % colname)

    def recalc(self):
        'Clear caches and set the ``sheet`` attribute on all columns.'
        for c in self.columns:
            c.recalc(self)

    @asyncthread
    def reload(self):
        'Load rows and/or columns from ``self.source``.  Async.  Override in subclass.'
        self.rows = []
        with vd.Progress(gerund='loading', total=0):
            for r in self.iterload():
                self.addRow(r)

        # if an ordering has been specified, sort the sheet
        if self._ordering:
            vd.sync(self.sort())

    def iterload(self):
        'Generate rows from ``self.source``.  Override in subclass.'
        if False:
            yield vd.fail('no iterload for this loader yet')

    def iterrows(self):
        if self.rows is UNLOADED:
            try:
                self.rows = []
                for row in self.iterload():
                    self.addRow(row)
                    yield row
                return
            except ExpectedException:
                vd.sync(self.reload())

        for row in vd.Progress(self.rows):
            yield row

    def __iter__(self):
        for row in self.iterrows():
            yield LazyComputeRow(self, row)


    def __copy__(self):
        'Copy sheet design but remain unloaded. Deepcopy columns so their attributes (width, type, name) may be adjusted independently of the original.'
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
        return max(self._rowLayout.keys()) if self._rowLayout else self.topRowIndex+self.nScreenRows

    @bottomRowIndex.setter
    def bottomRowIndex(self, newidx):
        'Set topRowIndex, by getting height of *newidx* row and going backwards until more than nScreenRows is allocated.'
        nrows = 0
        i = 0
        while nrows < self.nScreenRows and newidx-i >= 0:
            h = self.calc_height(self.rows[newidx-i])
            nrows += h
            i += 1

        self._topRowIndex = newidx-i+2

    def __deepcopy__(self, memo):
        'same as __copy__'
        ret = self.__copy__()
        memo[id(self)] = ret
        return ret

    def __repr__(self):
        return self.name

    def evalExpr(self, expr, row=None, col=None):
        if row:
            # contexts are cached by sheet/rowid for duration of drawcycle
            contexts = vd._evalcontexts.setdefault((self, self.rowid(row), col), LazyComputeRow(self, row, col=col))
        else:
            contexts = None

        return eval(expr, vd.getGlobals(), contexts)

    def rowid(self, row):
        'Return a unique and stable hash of the *row* object.  Must be fast.  Overrideable.'
        return id(row)

    @property
    def nScreenRows(self):
        'Number of visible rows at the current window height.'
        return self.windowHeight-self.nHeaderRows-self.nFooterRows

    @drawcache_property
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
        return self.rows[self.topRowIndex:self.topRowIndex+self.nScreenRows]

    @drawcache_property
    def visibleCols(self):  # non-hidden cols
        'List of non-hidden columns in display order.'
        return self.keyCols + [c for c in self.columns if not c.hidden and not c.keycol]

    def visibleColAtX(self, x):
        for vcolidx, (colx, w) in self._visibleColLayout.items():
            if colx <= x <= colx+w:
                return vcolidx

    def visibleRowAtY(self, y):
        for rowidx, (rowy, h) in self._rowLayout.items():
            if rowy <= y <= rowy+h-1:
                return rowidx

    @drawcache_property
    def keyCols(self):
        'List of visible key columns.'
        return sorted([c for c in self.columns if c.keycol and not c.hidden], key=lambda c:c.keycol)

    @property
    def cursorColIndex(self):
        'Index of current column into `Sheet.columns`. Linear search; prefer `cursorCol` or `cursorVisibleColIndex`.'
        return self.columns.index(self.cursorCol)

    @property
    def nonKeyVisibleCols(self):
        'List of visible non-key columns.'
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
        'Position of cursor and bounds of current sheet.'
        rowinfo = 'row %d (%d selected)' % (self.cursorRowIndex, self.nSelectedRows)
        colinfo = 'col %d (%d visible)' % (self.cursorVisibleColIndex, len(self.visibleCols))
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

    def addColumn(self, *cols, index=None):
        'Insert all *cols* into columns at *index*, or append to end of columns if *index* is None.  Return first column.'
        for i, col in enumerate(cols):
            vd.addUndo(self.columns.remove, col)
            if index is None:
                index = len(self.columns)
            col.recalc(self)
            self.columns.insert(index+i, col)
            Sheet.visibleCols.fget.cache_clear()

        return cols[0]

    def addColumnAtCursor(self, *cols):
        'Insert all *cols* into columns after cursor.  Return first column.'
        return self.addColumn(*cols, index=0 if self.cursorCol.keycol else self.columns.index(self.cursorCol)+1)

    def setColNames(self, rows):
        for c in self.visibleCols:
            c.name = '\n'.join(str(c.getDisplayValue(r)) for r in rows)

    def setKeys(self, cols):
        'Make all *cols* into key columns.'
        vd.addUndo(undoAttrFunc(cols, 'keycol'))
        lastkeycol = 0
        if self.keyCols:
            lastkeycol = max(c.keycol for c in self.keyCols)
        for col in cols:
            if not col.keycol:
                col.keycol = lastkeycol+1
                lastkeycol += 1
        # clears the keyCols cache
        visidata.Extensible.clear_all_caches()

    def unsetKeys(self, cols):
        'Make all *cols* non-key columns.'
        vd.addUndo(undoAttrFunc(cols, 'keycol'))
        for col in cols:
            col.keycol = 0

    def toggleKeys(self, cols):
        for col in cols:
            if col.keycol:
                self.unsetKeys([col])
            else:
                self.setKeys([col])

    def rowkey(self, row):
        'Return tuple of the key for *row*.'
        return tuple(c.getTypedValue(row) for c in self.keyCols)

    def keystr(self, row):
        'Return string of the key for *row*.'
        return ','.join(map(str, self.rowkey(row)))

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

        if self.topRowIndex < 0:
            self.topRowIndex = 0
        elif self.topRowIndex > self.nRows-1:
            self.topRowIndex = self.nRows-1

        # check bounds, scroll if necessary
        if self.topRowIndex > self.cursorRowIndex:
            self.topRowIndex = self.cursorRowIndex
        elif self.bottomRowIndex < self.cursorRowIndex:
            self.bottomRowIndex = self.cursorRowIndex
        elif self.bottomRowIndex == self.cursorRowIndex and self._rowLayout and self._rowLayout[self.bottomRowIndex][1] > 1:
            self.bottomRowIndex = self.cursorRowIndex

        if self.cursorCol and self.cursorCol.keycol:
            return

        if self.leftVisibleColIndex >= self.cursorVisibleColIndex:
            self.leftVisibleColIndex = self.cursorVisibleColIndex
        else:
            while True:
                if self.leftVisibleColIndex == self.cursorVisibleColIndex:  # not much more we can do
                    break
                self.calcColLayout()
                if not self._visibleColLayout:
                    break
                mincolidx, maxcolidx = min(self._visibleColLayout.keys()), max(self._visibleColLayout.keys())
                if self.cursorVisibleColIndex < mincolidx:
                    self.leftVisibleColIndex -= max((self.cursorVisibleColIndex - mincolid)//2, 1)
                    continue
                elif self.cursorVisibleColIndex > maxcolidx:
                    self.leftVisibleColIndex += max((maxcolidx - self.cursorVisibleColIndex)//2, 1)
                    continue

                cur_x, cur_w = self._visibleColLayout[self.cursorVisibleColIndex]
                if cur_x+cur_w < self.windowWidth:  # current columns fit entirely on screen
                    break
                self.leftVisibleColIndex += 1  # once within the bounds, walk over one column at a time

    def calcColLayout(self):
        'Set right-most visible column, based on calculation.'
        minColWidth = len(options.disp_more_left)+len(options.disp_more_right)+2
        sepColWidth = len(options.disp_column_sep)
        winWidth = self.windowWidth
        self._visibleColLayout = {}
        x = 0
        vcolidx = 0
        for vcolidx in range(0, self.nVisibleCols):
            col = self.visibleCols[vcolidx]
            if col.width is None and len(self.visibleRows) > 0:
                vrows = self.visibleRows if self.nRows > 1000 else self.rows
                # handle delayed column width-finding
                col.width = max(col.getMaxWidth(vrows), minColWidth)
                if vcolidx != self.nVisibleCols-1:  # let last column fill up the max width
                    col.width = min(col.width, options.default_width)
            width = col.width if col.width is not None else options.default_width
            if col in self.keyCols:
                width = max(width, 1)  # keycols must all be visible
            if col in self.keyCols or vcolidx >= self.leftVisibleColIndex:  # visible columns
                self._visibleColLayout[vcolidx] = [x, min(width, winWidth-x)]
                x += width+sepColWidth
            if x > winWidth-1:
                break

        self.rightVisibleColIndex = vcolidx

    def drawColHeader(self, scr, y, h, vcolidx):
        'Compose and draw column header for given vcolidx.'
        col = self.visibleCols[vcolidx]

        # hdrattr highlights whole column header
        # sepattr is for header separators and indicators
        sepcattr = colors.get_color('color_column_sep')

        hdrcattr = self._colorize(col, None)
        if vcolidx == self.cursorVisibleColIndex:
            hdrcattr = update_attr(hdrcattr, colors.color_current_hdr, 2)

        C = options.disp_column_sep
        if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.rightVisibleColIndex:
            C = options.disp_keycol_sep

        x, colwidth = self._visibleColLayout[vcolidx]

        # AnameTC
        T = vd.getType(col.type).icon
        if T is None:  # still allow icon to be explicitly non-displayed ''
            T = '?'

        hdrs = col.name.split('\n')
        for i in range(h):
            name = ' '  # save room at front for LeftMore or sorted arrow
            for j, (sortcol, sortdir) in enumerate(self._ordering):
                if col is sortcol:
                    try:
                        name = self.options.disp_sort_desc[j] if sortdir else self.options.disp_sort_asc[j]
                    except IndexError:
                        pass

            if h-i-1 < len(hdrs):
                name += hdrs[::-1][h-i-1]

            if len(name) > colwidth-1:
                name = name[:colwidth-len(options.disp_truncator)] + options.disp_truncator

            if i == h-1:
                hdrcattr = update_attr(hdrcattr, colors.color_bottom_hdr, 5)

            clipdraw(scr, y+i, x, name, hdrcattr.attr, colwidth)
            vd.onMouse(scr, y+i, x, 1, colwidth, BUTTON3_RELEASED='rename-col')

            if C and x+colwidth+len(C) < self.windowWidth and y+i < self.windowWidth:
                scr.addstr(y+i, x+colwidth, C, sepcattr.attr)

        clipdraw(scr, y+h-1, x+colwidth-len(T), T, hdrcattr.attr)

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
        vd.clearCaches()

        if not self.columns:
            if options.debug:
                self.addColumn(Column())
            else:
                return

        drawparams = {
            'isNull': self.isNullFunc(),

            'topsep': options.disp_rowtop_sep,
            'midsep': options.disp_rowmid_sep,
            'botsep': options.disp_rowbot_sep,
            'endsep': options.disp_rowend_sep,
            'keytopsep': options.disp_keytop_sep,
            'keymidsep': options.disp_keymid_sep,
            'keybotsep': options.disp_keybot_sep,
            'endtopsep': options.disp_endtop_sep,
            'endmidsep': options.disp_endmid_sep,
            'endbotsep': options.disp_endbot_sep,

            'colsep': options.disp_column_sep,
            'keysep': options.disp_keycol_sep,
            'selectednote': options.disp_selected_note,
            'disp_truncator': options.disp_truncator,
        }

        self._rowLayout = {}  # [rowidx] -> (y, height)
        self.calcColLayout()

        numHeaderRows = self.nHeaderRows
        vcolidx = 0

        headerRow = 0
        for vcolidx, colinfo in sorted(self._visibleColLayout.items()):
            self.drawColHeader(scr, headerRow, numHeaderRows, vcolidx)

        y = headerRow + numHeaderRows

        rows = self.rows[self.topRowIndex:min(self.topRowIndex+self.nScreenRows, self.nRows)]
        self.checkCursorNoExceptions()

        for rowidx, row in enumerate(rows):
            if y >= self.windowHeight-1:
                break

            rowcattr = self._colorize(None, row)

            y += self.drawRow(scr, row, self.topRowIndex+rowidx, y, rowcattr, maxheight=self.windowHeight-y-1, **drawparams)

        if vcolidx+1 < self.nVisibleCols:
            scr.addstr(headerRow, self.windowWidth-2, options.disp_more_right, colors.color_column_sep)

        scr.refresh()

    def calc_height(self, row, displines=None, isNull=None):
            if displines is None:
                displines = {}  # [vcolidx] -> list of lines in that cell

            for vcolidx, (x, colwidth) in sorted(self._visibleColLayout.items()):
                if x < self.windowWidth:  # only draw inside window
                    vcols = self.visibleCols
                    if vcolidx >= len(vcols):
                        continue
                    col = vcols[vcolidx]
                    cellval = col.getCell(row)
                    if colwidth > 1 and vd.isNumeric(col):
                        cellval.display = cellval.display.rjust(colwidth-2)

                    try:
                        if isNull and isNull(cellval.value):
                            cellval.note = options.disp_note_none
                            cellval.notecolor = 'color_note_type'
                    except (TypeError, ValueError):
                        pass

                    if col.voffset or col.height > 1:
                        lines = splitcell(cellval.display, width=colwidth-2)
                    else:
                        lines = [cellval.display]
                    displines[vcolidx] = (col, cellval, lines)

            heights = [0]
            for col, cellval, lines in displines.values():
                h = len(lines)   # of this cell
                heights.append(min(col.height, h))

            return max(heights)

    def drawRow(self, scr, row, rowidx, ybase, rowcattr: ColorAttr, maxheight,
            isNull='',
            topsep='',
            midsep='',
            botsep='',
            endsep='',
            keytopsep='',
            keymidsep='',
            keybotsep='',
            endtopsep='',
            endmidsep='',
            endbotsep='',
            colsep='',
            keysep='',
            selectednote='',
            disp_truncator=''
       ):
            # sepattr is the attr between cell/columns
            sepcattr = update_attr(rowcattr, colors.color_column_sep, 1)

            # apply current row here instead of in a colorizer, because it needs to know dispRowIndex
            if rowidx == self.cursorRowIndex:
                color_current_row = colors.get_color('color_current_row', 5)
                basecellcattr = sepcattr = update_attr(rowcattr, color_current_row)
            else:
                basecellcattr = rowcattr

            displines = {}  # [vcolidx] -> list of lines in that cell
            height = min(self.calc_height(row, displines), maxheight) or 1  # display even empty rows
            self._rowLayout[rowidx] = (ybase, height)

            for vcolidx, (col, cellval, lines) in displines.items():
                    if vcolidx not in self._visibleColLayout:
                        continue
                    x, colwidth = self._visibleColLayout[vcolidx]
                    hoffset = col.hoffset
                    voffset = col.voffset

                    cattr = self._colorize(col, row, cellval)
                    cattr = update_attr(cattr, basecellcattr)

                    note = getattr(cellval, 'note', None)
                    if note:
                        notecattr = update_attr(cattr, colors.get_color(cellval.notecolor), 10)
                        clipdraw(scr, ybase, x+colwidth-len(note), note, notecattr.attr)

                    if voffset >= 0:
                        if len(lines)-voffset > height:
                            # last line should always include as much as possible
                            firstn = sum(len(i)+1 for i in lines[:voffset+height-1])
                            lines = lines[:voffset+height]
                            lines[-1] = cellval.display[firstn:][:col.width]

                    lines = lines[voffset:]

                    if len(lines) > height:
                        lines = lines[:height]
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

                        pre = disp_truncator if hoffset != 0 else disp_column_fill
                        clipdraw(scr, y, x, (pre if colwidth > 2 else '')+line[hoffset:], cattr.attr, w=colwidth-(1 if note else 0))
                        vd.onMouse(scr, y, x, 1, colwidth, BUTTON3_RELEASED='edit-cell')

                        if x+colwidth+len(sepchars) <= self.windowWidth:
                            scr.addstr(y, x+colwidth, sepchars, sepcattr.attr)

            for notefunc in vd.rowNoters:
                ch = notefunc(self, row)
                if ch:
                    clipdraw(scr, ybase, 0, ch, colors.color_note_row)
                    break

            return height

vd.rowNoters = [
        lambda sheet, row: sheet.isSelected(row) and options.disp_selected_note,
]

Sheet = TableSheet  # deprecated in 2.0 but still widely used internally


class SequenceSheet(Sheet):
    'Sheets with ``ColumnItem`` columns, and rows that are Python sequences (list, namedtuple, etc).'
    def setCols(self, headerrows):
        self.columns = []
        for i, colnamelines in enumerate(itertools.zip_longest(*headerrows, fillvalue='')):
            colnamelines = ['' if c is None else c for c in colnamelines]
            self.addColumn(ColumnItem(''.join(colnamelines), i))

        self._rowtype = namedlist('tsvobj', [(c.name or '_') for c in self.columns])

    def newRow(self):
        return self._rowtype()

    def addRow(self, row, index=None):
        for i in range(len(self.columns), len(row)):  # no-op if already done
            self.addColumn(ColumnItem('', i))
            self._rowtype = namedlist('tsvobj', [(c.name or '_') for c in self.columns])
        if type(row) is not self._rowtype:
            row = self._rowtype(row)
        super().addRow(row, index=index)

    def optlines(self, it, optname):
        'Generate next options.<optname> elements from iterator with exceptions wrapped.'
        for i in range(options.getobj(optname, self)):
            try:
                yield next(it)
            except StopIteration:
                break

    @asyncthread
    def reload(self):
        'Skip first options.skip rows; set columns from next options.header rows.'

        itsource = self.iterload()

        # skip the first options.skip rows
        list(self.optlines(itsource, 'skip'))

        # use the next options.header rows as columns
        self.setCols(list(self.optlines(itsource, 'header')))

        self.rows = []
        # add the rest of the rows
        for r in vd.Progress(itsource, gerund='loading', total=0):
            self.addRow(r)

        # if an ordering has been specified, sort the sheet
        if self._ordering:
            vd.sync(self.sort())


class IndexSheet(Sheet):
    'Base class for tabular sheets with rows that are Sheets.'
    rowtype = 'sheets'  # rowdef: Sheet
    precious = False

    columns = [
        ColumnAttr('name'),
        ColumnAttr('rows', 'nRows', type=int),
        ColumnAttr('cols', 'nCols', type=int),
        ColumnAttr('keys', 'keyColNames'),
        ColumnAttr('source'),
    ]
    nKeys = 1

    def newRow(self):
        return Sheet('', columns=[ColumnItem('', 0)], rows=[])

    def openRow(self, row):
        return row  # rowdef is Sheet

    def getSheet(self, k):
        for vs in self.rows:
            if vs.name == k:
                return vs


class SheetsSheet(IndexSheet):
    columns = [
        ColumnAttr('name'),
        ColumnAttr('type', '__class__.__name__'),
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
    nKeys = 1
    def reload(self):
        self.rows = self.source

    def sort(self):
        self.rows[1:] = sorted(self.rows[1:], key=self.sortkey)

@VisiData.property
@drawcache
def _evalcontexts(vd):
    return {}

## VisiData sheet manipulation

@VisiData.global_api
def replace(vd, vs):
    'Replace top sheet with the given sheet `vs`.'
    vd.sheets.pop(0)
    return vd.push(vs)


@VisiData.global_api
def remove(vd, vs):
    'Remove *vs* from sheets stack, without asking for confirmation.'
    if vs in vd.sheets:
        vd.sheets.remove(vs)
        if vs in vd.allSheets:
            vd.allSheets.remove(vs)
            vd.allSheets.append(vs)
    else:
        vd.fail('sheet not on stack')


@VisiData.global_api
def push(vd, vs):
    'Push Sheet *vs* onto ``vd.sheets`` stack.  Remove from other position if already on sheets stack.'
    if not isinstance(vs, BaseSheet):
        return  # return instead of raise, some commands need this

    vs.vd = vd
    if vs in vd.sheets:
        vd.sheets.remove(vs)

    vd.sheets.insert(0, vs)

    if vs.precious and vs not in vd.allSheets:
        vd.allSheets.append(vs)

    vs.ensureLoaded()


@VisiData.lazy_property
def allSheetsSheet(vd):
    return SheetsSheet("sheets_all", source=vd.allSheets)

@VisiData.lazy_property
def sheetsSheet(vd):
    return SheetsSheet("sheets", source=vd.sheets)


@VisiData.api
def quit(vd, *sheets):
    'Remove *sheets* from sheets stack, asking for confirmation if options.quitguard set (either global or sheet-specific).'
    if len(vd.sheets) == len(sheets) and options.getonly('quitguard', 'override', False):
        vd.confirm("quit last sheet? ")
    for vs in sheets:
        if options.getonly('quitguard', vs, False):
            vd.draw_all()
            vd.confirm(f'quit guarded sheet "{vs.name}?" ')
        vd.remove(vs)


@BaseSheet.api
def preloadHook(sheet):
    'Override to setup for reload().'
    pass


@VisiData.api
def newSheet(vd, name, ncols, **kwargs):
    return Sheet(name, columns=[SettableColumn() for i in range(ncols)], **kwargs)


@Sheet.api
def updateColNames(sheet, rows, cols, overwrite=False):
    vd.addUndoColNames(cols)
    for c in cols:
        if not c._name or overwrite:
            c.name = "\n".join(c.getDisplayValue(r) for r in rows)


IndexSheet.class_options.header = 0
IndexSheet.class_options.skip = 0


globalCommand('S', 'sheets-stack', 'vd.push(vd.sheetsSheet)', 'open Sheets Stack: join or jump between the active sheets on the current stack')
globalCommand('gS', 'sheets-all', 'vd.push(vd.allSheetsSheet)', 'open Sheets Sheet: join or jump between all sheets from current session')

BaseSheet.addCommand('^R', 'reload-sheet', 'preloadHook(); vd.addUndoReload(rows, columns); reload(); recalc(); status("reloaded")', 'reload current sheet'),
Sheet.addCommand('^G', 'show-cursor', 'status(statusLine)', 'show cursor position and bounds of current sheet on status line'),

Sheet.addCommand('!', 'key-col', 'toggleKeys([cursorCol])', 'toggle current column as a key column')
Sheet.addCommand('z!', 'key-col-off', 'unsetKeys([cursorCol])', 'unset current column as a key column')

Sheet.addCommand('e', 'edit-cell', 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex)) if not (cursorRow is None) else fail("no rows to edit")', 'edit contents of current cell')
Sheet.addCommand('ge', 'setcol-input', 'cursorCol.setValuesTyped(selectedRows, input("set selected to: ", value=cursorDisplay))', 'set contents of current column for selected rows to same input')

Sheet.addCommand('"', 'dup-selected', 'vs=copy(sheet); vs.name += "_selectedref"; vs.reload=lambda vs=vs,rows=selectedRows: setattr(vs, "rows", list(rows)); vd.push(vs)', 'open duplicate sheet with only selected rows'),
Sheet.addCommand('g"', 'dup-rows', 'vs=copy(sheet); vs.name+="_copy"; vs.rows=list(rows); status("copied "+vs.name); vs.select(selectedRows); vd.push(vs)', 'open duplicate sheet with all rows'),
Sheet.addCommand('z"', 'dup-selected-deep', 'vs = deepcopy(sheet); vs.name += "_selecteddeepcopy"; vs.rows = async_deepcopy(vs, selectedRows); vd.push(vs); status("pushed sheet with async deepcopy of selected rows")', 'open duplicate sheet with deepcopy of selected rows'),
Sheet.addCommand('gz"', 'dup-rows-deep', 'vs = deepcopy(sheet); vs.name += "_deepcopy"; vs.rows = async_deepcopy(vs, rows); vd.push(vs); status("pushed sheet with async deepcopy of all rows")', 'open duplicate sheet with deepcopy of all rows'),

Sheet.addCommand('z~', 'type-any', 'cursorCol.type = anytype', 'set type of current column to anytype')
Sheet.addCommand('~', 'type-string', 'cursorCol.type = str', 'set type of current column to str')
Sheet.addCommand('@', 'type-date', 'cursorCol.type = date', 'set type of current column to date')
Sheet.addCommand('#', 'type-int', 'cursorCol.type = int', 'set type of current column to int')
Sheet.addCommand('z#', 'type-len', 'cursorCol.type = vlen', 'set type of current column to len')
Sheet.addCommand('$', 'type-currency', 'cursorCol.type = currency', 'set type of current column to currency')
Sheet.addCommand('%', 'type-float', 'cursorCol.type = float', 'set type of current column to float')
Sheet.addCommand('z%', 'type-floatsi', 'cursorCol.type = floatsi', 'set type of current column to SI float')

# when diving into a sheet, remove the index unless it is precious
IndexSheet.addCommand('g^R', 'reload-selected', 'for vs in selectedRows or rows: vs.reload()', 'reload all selected sheets')
SheetsSheet.addCommand('gC', 'columns-selected', 'vd.push(ColumnsSheet("all_columns", source=selectedRows))', 'open Columns Sheet with all visible columns from selected sheets')
SheetsSheet.addCommand('gI', 'describe-selected', 'vd.push(DescribeSheet("describe_all", source=selectedRows))', 'open Describe Sheet with all visble columns from selected sheets')
SheetsSheet.addCommand('z^C', 'cancel-row', 'cancelThread(*cursorRow.currentThreads)', 'abort async thread for current sheet')
SheetsSheet.addCommand('gz^C', 'cancel-rows', 'for vs in selectedRows: cancelThread(*vs.currentThreads)', 'abort async threads for selected sheets')
IndexSheet.addCommand('g^S', 'save-selected', 'vd.saveSheets(inputPath("save %d sheets to: " % nSelectedRows), *selectedRows, confirm_overwrite=options.confirm_overwrite)', 'save all selected sheets to given file or directory')
SheetsSheet.addCommand(ENTER, 'open-row', 'dest=cursorRow; vd.sheets.remove(sheet) if not sheet.precious else None; vd.push(openRow(dest))', 'open sheet referenced in current row')

BaseSheet.addCommand('q', 'quit-sheet',  'vd.quit(sheet)', 'quit current sheet')
globalCommand('gq', 'quit-all', 'vd.quit(*vd.sheets)', 'quit all sheets (clean exit)')

BaseSheet.addCommand('Z', 'splitwin-half', 'options.disp_splitwin_pct = 50', 'split screen in half, so that second sheet on stack is visible in a second pane')
BaseSheet.addCommand('gZ', 'splitwin-close', 'options.disp_splitwin_pct = 0', 'close an already split screen, current pane full screens')
BaseSheet.addCommand('^I', 'splitwin-swap', 'vd.push(vd.sheets[1]) if len(sheets) >=2 else fail("at least 2 sheets required for splitwin-swap"); options.disp_splitwin_pct = -options.disp_splitwin_pct', 'jump to other pane')
BaseSheet.addCommand('zZ', 'splitwin-input', 'options.disp_splitwin_pct = input("% height for split window: ", value=options.disp_splitwin_pct)', 'split screen and queries for height of second pane, second sheet on stack is visible in second pane')

BaseSheet.addCommand('^L', 'redraw', 'vd.redraw(); sheet.refresh()', 'refresh screen')
BaseSheet.addCommand(None, 'guard-sheet', 'options.set("quitguard", True, sheet); status("guarded")', 'guard current sheet from accidental quitting')
BaseSheet.addCommand(None, 'open-source', 'vd.push(source)', 'jump to the source of this sheet')

BaseSheet.bindkey('KEY_RESIZE', 'redraw')

BaseSheet.addCommand('A', 'open-new', 'vd.push(vd.newSheet("unnamed", 1))', 'open new blank sheet')

Sheet.addCommand('^', 'rename-col', 'vd.addUndoColNames([cursorCol]); cursorCol.name = editCell(cursorVisibleColIndex, -1)', 'edit name of current column')
Sheet.addCommand('z^', 'rename-col-selected', 'updateColNames(selectedRows or [cursorRow], [sheet.cursorCol], overwrite=True)', 'set name of current column to combined contents of current cell in selected rows (or current row)')
Sheet.addCommand('g^', 'rename-cols-row', 'updateColNames(selectedRows or [cursorRow], sheet.visibleCols)', 'set names of all unnamed visible columns to contents of selected rows (or current row)')
Sheet.addCommand('gz^', 'rename-cols-selected', 'updateColNames(selectedRows or [cursorRow], sheet.visibleCols, overwrite=True)', 'set names of all visible columns to combined contents of selected rows (or current row)')
BaseSheet.addCommand(None, 'rename-sheet', 'sheet.name = input("rename sheet to: ", value=sheet.name)', 'rename current sheet to input')
