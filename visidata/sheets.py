import collections
import itertools
from copy import copy, deepcopy
import textwrap

from visidata import VisiData, Extensible, globalCommand, ColumnAttr, ColumnItem, vd, ENTER, EscapeException, drawcache, drawcache_property, LazyChainMap, asyncthread, ExpectedException
from visidata import (options, Column, namedlist, SettableColumn, AttrDict, DisplayWrapper,
TypedExceptionWrapper, BaseSheet, UNLOADED, wrapply,
clipdraw, clipdraw_chunks, ColorAttr, update_attr, colors, undoAttrFunc, vlen, dispwidth)
import visidata


vd.activePane = 1   # pane numbering starts at 1; pane 0 means active pane


vd.option('name_joiner', '_', 'string to join sheet or column names')
vd.option('value_joiner', ' ', 'string to join display values')
vd.option('max_rows', 1_000_000_000, 'number of rows to load from source')

vd.option('disp_wrap_max_lines', 3, 'max lines for multiline view')
vd.option('disp_wrap_break_long_words', False, 'break words longer than column width in multiline')
vd.option('disp_wrap_replace_whitespace', False, 'replace whitespace with spaces in multiline')
vd.option('disp_wrap_placeholder', '…', 'multiline string to indicate truncation')
vd.option('disp_multiline_focus', True, 'only multiline cursor row')
vd.option('color_aggregator', 'bold 255 white on 234 black', 'color of aggregator summary on bottom row')


@drawcache
def _splitcell(sheet, s, width=0, maxheight=1):
    height = max(maxheight, sheet.options.disp_wrap_max_lines or 0)
    if width <= 0 or height <= 0:
        return [s]

    wrap_kwargs = sheet.options.getall('disp_wrap_')
    wrap_kwargs['max_lines'] = height

    ret = []
    for attr, text in s:
        for line in textwrap.wrap(text, width=width, **wrap_kwargs):
            if len(ret) >= maxheight:
                ret[-1][0][1] += ' ' + line
                break
            else:
                ret.append([[attr, line]])
    return ret

disp_column_fill = ' ' # pad chars before column value

class Colorizer:
    '''higher precedence color overrides lower; all non-color attributes combine.
       coloropt is the color option name (like 'color_error').
       func(sheet,col,row,value) should return a true value if coloropt should be applied
       If coloropt is None, func() should return a coloropt (or None) instead'''

    def __init__(self, precedence:int, coloropt:str, func=lambda s,c,r,v: None):
        self.precedence = precedence
        self.coloropt = coloropt
        self._func = func

class RowColorizer(Colorizer):
    def func(self, s, c, r, v):
        return r is not None and self._func(s,c,r,v)

class ColumnColorizer(Colorizer):
    def func(self, s, c, r, v):
        return c is not None and self._func(s,c,r,v)

class CellColorizer(Colorizer):
    def func(self, s, c, r, v):
        return r is not None and c is not None and self._func(s,c,r,v)


class RecursiveExprException(Exception):
    pass

class LazyComputeRow:
    'Calculate column values as needed.'
    def __init__(self, sheet, row, col=None, **kwargs):
        self.row = row
        self.col = col
        self.sheet = sheet
        self.extra = AttrDict(kwargs) # extra bindings
        self._usedcols = set()

        self._lcm.clear()  # reset locals on lcm

    @property
    def _lcm(self):
        lcmobj = self.col or self.sheet
        if not hasattr(lcmobj, '_lcm'):
            lcmobj._lcm = LazyChainMap(self.sheet, self.col, self.extra, *vd.contexts)
        return lcmobj._lcm

    def __iter__(self):
        yield from self.sheet.availColnames
        yield from self._lcm.keys()
        yield 'row'
        yield 'sheet'
        yield 'col'

    def keys(self):
        return list(self.__iter__())

    def __str__(self):
        return str(self.as_dict())

    def as_dict(self):
        return {c.name:self[c.name] for c in self.sheet.visibleCols}

    def __getattr__(self, k):
        return self.__getitem__(k)

    def __getitem__(self, colid):
        try:
            i = self.sheet.availColnames.index(colid)
            c = self.sheet.availCols[i]
            if c is self.col:  # ignore current column
                j = self.sheet.availColnames[i+1:].index(colid)
                c = self.sheet.availCols[i+j+1]

        except ValueError:
            try:
                c = self._lcm[colid]
            except (KeyError, AttributeError) as e:
                if colid == 'sheet': return self.sheet
                elif colid == 'row': return self
                elif colid == '_row': return self.row
                elif colid == 'col': c = self.col
                else:
                    raise KeyError(colid) from e

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
        collections.defaultdict.__init__(self, lambda: None)
    def __bool__(self):
        return True

class TableSheet(BaseSheet):
    'Base class for sheets with row objects and column views.'
    _rowtype = lambda: BasicRow()
    _coltype = SettableColumn

    rowtype = 'rows'
    guide = '# {sheet.help_title}\n'

    @property
    def help_title(self):
        if isinstance(self.source, visidata.Path):
            return 'Source Table'
        else:
            return 'Table Sheet'

    columns = []  # list of Column
    colorizers = [ # list of Colorizer
        CellColorizer(2, 'color_default_hdr', lambda s,c,r,v: r is None),
        ColumnColorizer(2, 'color_current_col', lambda s,c,r,v: c is s.cursorCol),
        ColumnColorizer(1, 'color_key_col', lambda s,c,r,v: c and c.keycol),
        CellColorizer(0, 'color_default', lambda s,c,r,v: True),
        RowColorizer(1, 'color_error', lambda s,c,r,v: isinstance(r, (Exception, TypedExceptionWrapper))),
        CellColorizer(3, 'color_current_cell', lambda s,c,r,v: c is s.cursorCol and r is s.cursorRow),
        ColumnColorizer(1, 'color_hidden_col', lambda s,c,r,v: c and c.hidden),
    ]
    nKeys = 0  # columns[:nKeys] are key columns
    _ordering = []  # list of (col:Column|str, reverse:bool)

    def __init__(self, *names, rows=UNLOADED, **kwargs):
        super().__init__(*names, rows=rows, **kwargs)
        self.cursorRowIndex = 0  # absolute index of cursor into self.rows
        self.cursorVisibleColIndex = 0  # index of cursor into self.visibleCols

        self._topRowIndex = 0     # cursorRowIndex of topmost row
        self.leftVisibleColIndex = 0    # cursorVisibleColIndex of leftmost column
        self.rightVisibleColIndex = 0

        # as computed during draw()
        self._rowLayout = {}      # [rowidx] -> (y, w)
        self._visibleColLayout = {}      # [vcolidx] -> (x, w)

        # list of all columns in display order
        self.initialCols = kwargs.pop('columns', None) or type(self).columns
        self.resetCols()

        self._ordering = list(type(self)._ordering)  #2254
        self._colorizers = self.classColorizers
        self.recalc()  # set .sheet on columns and start caches

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
        self._colorizers = sorted(self._colorizers, key=lambda x: x.precedence, reverse=True)

    def removeColorizer(self, c):
        'Remove Colorizer *c* from the list of colorizers for this sheet.'
        self._colorizers.remove(c)

    @property
    def classColorizers(self) -> list:
        'List of all colorizers from sheet class hierarchy in precedence order (highest precedence first)'
        # all colorizers must be in the same bucket
        # otherwise, precedence does not get applied properly
        _colorizers = set()

        for b in [self] + list(type(self).superclasses()):
            for c in getattr(b, 'colorizers', []):
                _colorizers.add(c)

        return sorted(_colorizers, key=lambda x: x.precedence, reverse=True)

    def _colorize(self, col, row, value=None) -> ColorAttr:
        'Return ColorAttr for the given colorizers/col/row/value'

        colorstack = []
        for colorizer in self._colorizers:
            try:
                r = colorizer.func(self, col, row, value)
                if r:
                    colorstack.append((colorizer.precedence, colorizer.coloropt if colorizer.coloropt else r))
            except Exception as e:
                vd.exceptionCaught(e)

        return colors.resolve_colors(tuple(colorstack))

    def addRow(self, row, index=None):
        'Insert *row* at *index*, or append at end of rows if *index* is None.'
        if index is None:
            self.rows.append(row)
        else:
            self.rows.insert(index, row)
            if self.cursorRowIndex and self.cursorRowIndex >= index:
                self.cursorRowIndex += 1
        return row

    def newRow(self):
        'Return new blank row compatible with this sheet.  Overridable.'
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
        'Load or reload rows and columns from ``self.source``.  Async.  Override resetCols() or loader() in subclass.'
        with visidata.ScopedSetattr(self, 'loading', True):
            self.resetCols()
            self.beforeLoad()
            try:
                self.loader()
                vd.debug(f'finished loading {self}')
            finally:
                self.afterLoad()

        self.recalc()

    def beforeLoad(self):
        pass

    def resetCols(self):
        'Reset columns to class settings'
        self.columns = []
        for c in self.initialCols:
            self.addColumn(deepcopy(c))
            if self.options.disp_expert < c.disp_expert:
                c.hide()

        self.setKeys(self.columns[:self.nKeys])

    def loader(self):
        'Reset rows and sync load ``source`` via iterload.  Overrideable.'
        self.rows = []
        try:
            with vd.Progress(gerund='loading', total=0):
                for i, r in enumerate(self.iterload()):
                    if self.precious and i > self.options.max_rows:
                        break
                    self.addRow(r)
        except FileNotFoundError:
            return  # let it be a blank sheet without error

    def iterload(self):
        'Generate rows from ``self.source``.  Override in subclass.'
        if False:
            yield vd.fail('no iterload for this loader yet')

    def afterLoad(self):
        'hook for after loading has finished.  Overrideable (be sure to call super).'
        # if an ordering has been specified, sort the sheet
        if self._ordering:
            vd.sync(self.sort())

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

        ret.columns = []

        col_mapping = {}
        for c in self.columns:
            new_col = copy(c)
            col_mapping[c] = new_col
            ret.addColumn(new_col)

        ret.setKeys([col_mapping[c] for c in self.columns if c.keycol])

        ret._ordering = []
        for sortcol,reverse in self._ordering:
            if isinstance(sortcol, str):
                ret._ordering.append((sortcol,reverse))
            else:
                ret._ordering.append((col_mapping[sortcol],reverse))

        ret.topRowIndex = ret.cursorRowIndex = 0
        return ret

    @property
    def bottomRowIndex(self):
        return self.topRowIndex+self.nScreenRows-1

    @bottomRowIndex.setter
    def bottomRowIndex(self, newidx):
        self._topRowIndex = newidx-self.nScreenRows+1

    @drawcache_property
    def rowHeight(self):
        cols = self.visibleCols
        return max(c.height for c in cols) if cols else 1

    def __deepcopy__(self, memo):
        'same as __copy__'
        ret = self.__copy__()
        memo[id(self)] = ret
        return ret

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<{type(self).__name__}: {self.name}>'

    @drawcache_property
    def currow(self):
        return LazyComputeRow(self, self.cursorRow, self.cursorCol)

    def evalExpr(self, expr:str, row=None, col=None, **kwargs):
        'eval() expr in the context of (row, col), with extra bindings in kwargs'
        if row is not None:
            # contexts are cached by sheet/rowid for duration of drawcycle
            contexts = vd._evalcontexts.setdefault((self, self.rowid(row), col), LazyComputeRow(self, row, col, **kwargs))
        else:
            contexts = dict(sheet=self)

        return eval(expr, vd.getGlobals(), contexts)

    def rowid(self, row):
        'Return a unique and stable hash of the *row* object.  Must be fast.  Overridable.'
        return id(row)

    @property
    def nScreenRows(self):
        'Number of visible rows at the current window height.'
        n = (self.windowHeight-self.nHeaderRows-self.nFooterRows)
        if self.options.disp_multiline_focus:  # focus multiline mode
            return n-self.rowHeight+1
        return n//self.rowHeight

    @drawcache_property
    def nHeaderRows(self):
        vcols = self.visibleCols
        return max(0, 1, *(len(col.name.split('\n')) for col in vcols))

    @property
    def nFooterRows(self):
        'Number of lines reserved at the bottom, including status line.'
        return len(self.allAggregators) + 1

    @property
    def cursorCol(self):
        'Current Column object.'
        vcols = self.availCols
        return vcols[min(self.cursorVisibleColIndex, len(vcols)-1)] if vcols else None

    @property
    def cursorRow(self):
        'The row object at the row cursor.'
        idx = self.cursorRowIndex
        return self.rows[idx] if self.nRows > idx else None

    @property
    def visibleRows(self):  # onscreen rows
        'List of rows onscreen.'
        return self.rows[self.topRowIndex:self.topRowIndex+self.nScreenRows]

    @drawcache_property
    def visibleCols(self):  # non-hidden cols
        'List of non-hidden columns in display order.'
        return (self.keyCols + [c for c in self.columns if not c.hidden and not c.keycol]) or [Column('', sheet=self)]

    @drawcache_property
    def keyCols(self):
        'List of visible key columns.'
        return sorted([c for c in self.columns if c.keycol and not c.hidden], key=lambda c:c.keycol)

    @drawcache_property
    def availCols(self):
        'List of all available columns, visible columns first.'
        return self.visibleCols + [c for c in self.columns if c.hidden]

    @drawcache_property
    def availColnames(self):
        'List of all available column names, visible columns first.'
        return [c.name for c in self.availCols]

    @property
    def cursorColIndex(self):
        'Index of current column into `Sheet.columns`. Linear search; prefer `cursorCol` or `cursorVisibleColIndex`.'
        try:
            return self.columns.index(self.cursorCol)
        except ValueError:
            return 0

    @property
    def nonKeyVisibleCols(self):
        'List of visible non-key columns.'
        return [c for c in self.columns if not c.hidden and c not in self.keyCols]

    @property
    def keyColNames(self):
        'String of key column names, for SheetsSheet convenience.'
        return ' '.join(c.name for c in self.keyCols)

    @keyColNames.setter
    def keyColNames(self, v):  #2122
        'Set key columns on this sheet to the space-separated list of column names.'
        newkeys = [self.column(colname) for colname in v.split()]
        self.unsetKeys(self.keyCols)
        self.setKeys(newkeys)

    @property
    def cursorCell(self):
        'Displayed value (DisplayWrapper) at current row and column.'
        return self.cursorCol.getCell(self.cursorRow)

    @property
    def cursorDisplay(self):
        'Displayed value (DisplayWrapper.text) at current row and column.'
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
        '''Insert all *cols* into columns at *index*, or append to end of columns if *index* is None.
           If *index* is None, columns are being added by loader, instead of by user.
           If added by user, mark sheet as modified.
           Columns added by loader share sheet's defer status.
           Columns added by user are not marked as deferred.
           Return first column.'''
        if not cols:
            vd.warning('no columns to add')
            return

        if index is not None:
            self.setModified()

        for i, col in enumerate(cols):
            col.name = self.maybeClean(col.name)
            col.defer = self.defer

            vd.addUndo(self.columns.remove, col)
            idx = len(self.columns) if index is None else index
            col.recalc(self)
            self.columns.insert(idx+i, col)

        # statements after addColumn in the same command may want to use these cached properties
        Sheet.keyCols.fget.cache_clear()
        Sheet.visibleCols.fget.cache_clear()
        Sheet.availCols.fget.cache_clear()
        Sheet.availColnames.fget.cache_clear()
        Sheet.colsByName.fget.cache_clear()

        return cols[0]

    def addColumnAtCursor(self, *cols):
        'Insert all *cols* into columns after cursor.  Return first column.'
        index = 0
        ccol = self.cursorCol
        if ccol and not ccol.keycol:
            index = self.columns.index(ccol)+1

        self.addColumn(*cols, index=index)
        firstnewcol = [c for c in cols if not c.hidden][0]
        self.cursorVisibleColIndex = self.visibleCols.index(firstnewcol)
        return firstnewcol

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

    def rowname(self, row):
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
        elif self.cursorVisibleColIndex >= len(self.availCols):
            self.cursorVisibleColIndex = len(self.availCols)-1

        if self.topRowIndex < 0:
            self.topRowIndex = 0
        elif self.topRowIndex > self.nRows-1:
            self.topRowIndex = self.nRows-1

        # check bounds, scroll if necessary
        if self.topRowIndex > self.cursorRowIndex:
            self.topRowIndex = self.cursorRowIndex
        elif self.bottomRowIndex < self.cursorRowIndex:
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
                    self.leftVisibleColIndex -= max((self.cursorVisibleColIndex - mincolidx)//2, 1)
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
        minColWidth = dispwidth(self.options.disp_more_left)+dispwidth(self.options.disp_more_right)+2
        sepColWidth = dispwidth(self.options.disp_column_sep)
        winWidth = self.windowWidth
        self._visibleColLayout = {}
        x = 0
        vcolidx = 0
        for vcolidx, col in enumerate(self.availCols):
            width = self.calcSingleColLayout(col, vcolidx, x, minColWidth)
            if width:
                x += width+sepColWidth
            if x > winWidth-1:
                break

        self.rightVisibleColIndex = vcolidx

    def calcSingleColLayout(self, col:Column, vcolidx:int, x:int=0, minColWidth:int=4):
            if col.width is None and len(self.visibleRows) > 0:
                vrows = self.visibleRows if self.nRows > 1000 else self.rows[:1000]  #1964
                # handle delayed column width-finding
                col.width = max(col.getMaxWidth(vrows), minColWidth)
                if vcolidx < self.nVisibleCols-1:  # let last column fill up the max width
                    col.width = min(col.width, self.options.default_width)

            width = col.width if col.width is not None else self.options.default_width

            # when cursor showing a hidden column
            if vcolidx >= self.nVisibleCols and vcolidx == self.cursorVisibleColIndex:
                width = self.options.default_width

            width = max(width, 1)
            if col in self.keyCols or vcolidx >= self.leftVisibleColIndex:  # visible columns
                self._visibleColLayout[vcolidx] = [x, min(width, self.windowWidth-x)]
                return width


    def drawColHeader(self, scr, y, h, vcolidx):
        'Compose and draw column header for given vcolidx.'
        col = self.availCols[vcolidx]

        # hdrattr highlights whole column header
        # sepattr is for header separators and indicators
        sepcattr = update_attr(colors.color_default, colors.get_color('color_column_sep'), 2)

        hdrcattr = self._colorize(col, None)
        if vcolidx == self.cursorVisibleColIndex:
            hdrcattr = update_attr(hdrcattr, colors.color_current_hdr, 2)

        C = self.options.disp_column_sep
        if (self.keyCols and col is self.keyCols[-1]) or vcolidx == self.nVisibleCols-1:
            C = self.options.disp_keycol_sep

        x, colwidth = self._visibleColLayout[vcolidx]

        # AnameTC
        T = vd.getType(col.type).icon
        if T is None:  # still allow icon to be explicitly non-displayed ''
            T = '?'

        hdrs = col.name.split('\n')
        for i in range(h):
            name = ''
            if colwidth > 2:
                name = ' '  # save room at front for LeftMore or sorted arrow

            if h-i-1 < len(hdrs):
                name += hdrs[::-1][h-i-1]

            if i == h-1:
                hdrcattr = update_attr(hdrcattr, colors.color_bottom_hdr, 5)

            if y+i < self.windowHeight:
                clipdraw(scr, y+i, x, name, hdrcattr, w=colwidth)
            vd.onMouse(scr, x, y+i, colwidth, 1, BUTTON3_RELEASED='rename-col')

            if C and x+colwidth+len(C) < self.windowWidth and y+i < self.windowHeight:
                scr.addstr(y+i, x+colwidth, C, sepcattr.attr)

        clipdraw(scr, y+h-1, min(x+colwidth, self.windowWidth-1)-dispwidth(T), T, hdrcattr)

        try:
            if vcolidx == self.leftVisibleColIndex and col not in self.keyCols and self.nonKeyVisibleCols.index(col) > 0:
                A = self.options.disp_more_left
                scr.addstr(y, x, A, sepcattr.attr)
        except ValueError:  # from .index
            pass

        try:
            A = ''
            for j, (sortcol, sortdir) in enumerate(self._ordering):
                if isinstance(sortcol, str):
                    sortcol = self.colsByName.get(sortcol)  # self.column will fail if sortcol was renamed
                if col is sortcol:
                    A = self.options.disp_sort_desc[j] if sortdir else self.options.disp_sort_asc[j]
                    scr.addstr(y+h-1, x, A, hdrcattr.attr)
                    break
        except IndexError:
            pass

    def isVisibleIdxKey(self, vcolidx):
        'Return boolean: is given column index a key column?'
        return self.visibleCols[vcolidx] in self.keyCols

    @drawcache_property
    def allAggregators(self):
        'Return dict of aggname -> list of cols with that aggregator.'
        allaggs = collections.defaultdict(list) # aggname -> list of cols with that aggregator
        for vcolidx, (x, colwidth) in sorted(self._visibleColLayout.items()):
            col = self.availCols[vcolidx]
            if not col.hidden:
                for aggr in col.aggregators:
                    allaggs[aggr.name].append(vcolidx)
        return allaggs

    def draw(self, scr):
        'Draw entire screen onto the `scr` curses object.'
        if not self.columns:
            return

        drawparams = {
            'isNull': self.isNullFunc(),

            'topsep': self.options.disp_rowtop_sep,
            'midsep': self.options.disp_rowmid_sep,
            'botsep': self.options.disp_rowbot_sep,
            'endsep': self.options.disp_rowend_sep,
            'keytopsep': self.options.disp_keytop_sep,
            'keymidsep': self.options.disp_keymid_sep,
            'keybotsep': self.options.disp_keybot_sep,
            'endtopsep': self.options.disp_endtop_sep,
            'endmidsep': self.options.disp_endmid_sep,
            'endbotsep': self.options.disp_endbot_sep,

            'colsep': self.options.disp_column_sep,
            'keysep': self.options.disp_keycol_sep,
            'selectednote': self.options.disp_selected_note,
            'disp_truncator': self.options.disp_truncator,
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
        vd.callNoExceptions(self.checkCursor)

        for rowidx, row in enumerate(rows):
            if y >= self.windowHeight-1:
                break

            rowcattr = self._colorize(None, row)

            y += self.drawRow(scr, row, self.topRowIndex+rowidx, y, rowcattr, maxheight=self.windowHeight-y-1, **drawparams)

        if vcolidx+1 < self.nVisibleCols:
            scr.addstr(headerRow, self.windowWidth-2, self.options.disp_more_right, colors.color_column_sep.attr)

        # draw bottom-row aggregators  #2209
        rightx, rightw = self._visibleColLayout[self.rightVisibleColIndex]
        rightx += rightw+1

        for aggrname, colidxs in self.allAggregators.items():
            clipdraw(scr, y, 0, ' '*rightx + f' {aggrname:9}', colors.color_aggregator, truncator='+')

            for vcolidx in colidxs:
                x, colwidth = self._visibleColLayout[vcolidx]
                col = self.availCols[vcolidx]

                if not col.hidden:
                    dw = DisplayWrapper('')
                    try:
                        agg = vd.aggregators[aggrname]
                        dw.value = col.aggregateTotal(agg)
                        dw.typedval = wrapply(agg.type or col.type, dw.value)
                        dw.text = col.format(dw.typedval)
                    except Exception as e:
                        dw.note = self.options.disp_note_typeexc
                        dw.notecolor = 'color_warning'
                        vd.exceptionCaught(e, status=False)
                    disps = [('', ' ')] + list(col.display(dw, width=colwidth))
                    clipdraw_chunks(scr, y, x, disps, colors.color_aggregator, w=colwidth)
            y += 1


    def calc_height(self, row, displines=None, isNull=None, maxheight=1):
            'render cell contents for row into displines'
            if displines is None:
                displines = {}  # [vcolidx] -> list of lines in that cell

            for vcolidx, (x, colwidth) in sorted(self._visibleColLayout.items()):
                if x < self.windowWidth:  # only draw inside window
                    vcols = self.availCols
                    if vcolidx >= self.nVisibleCols and vcolidx != self.cursorVisibleColIndex:
                        continue
                    col = vcols[vcolidx]
                    cellval = col.getCell(row)

                    cellval.display = col.display(cellval, colwidth)

                    try:
                        if isNull and isNull(cellval.value):
                            cellval.note = self.options.disp_note_none
                            cellval.notecolor = 'color_note_type'
                    except (TypeError, ValueError):
                        pass

                    if maxheight > 1:
                        lines = _splitcell(self, cellval.display, width=colwidth-2, maxheight=maxheight)
                    else:
                        lines = [cellval.display]
                    displines[vcolidx] = (col, cellval, lines)

            if len(displines) == 0:
                return 0
            return max(len(lines) for _, _, lines in displines.values())

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
                color_current_row = colors.get_color('color_current_row', 2)
                basecellcattr = sepcattr = update_attr(rowcattr, color_current_row)
            else:
                basecellcattr = rowcattr

            # calc_height renders cell contents into displines
            displines = {}  # [vcolidx] -> list of lines in that cell
            if options.disp_multiline_focus:
                height = self.rowHeight if rowidx == self.cursorRowIndex else 1
            else:
                height = min(self.rowHeight, maxheight) or 1  # display even empty rows

            self.calc_height(row, displines, maxheight=height)

            self._rowLayout[rowidx] = (ybase, height)

            if height > 1:
                colseps = [topsep] + [midsep]*(height-2) + [botsep]
                endseps = [endtopsep] + [endmidsep]*(height-2) + [endbotsep]
                keyseps = [keytopsep] + [keymidsep]*(height-2) + [keybotsep]
            else:
                colseps = [colsep]
                endseps = [endsep]
                keyseps = [keysep]

            for vcolidx, (col, cellval, lines) in displines.items():
                    if vcolidx not in self._visibleColLayout:
                        continue

                    if vcolidx == self.nVisibleCols-1:  # right edge of sheet
                        seps = endseps
                    elif (self.keyCols and col is self.keyCols[-1]): # last keycol
                        seps = keyseps
                    else:
                        seps = colseps

                    x, colwidth = self._visibleColLayout[vcolidx]
                    hoffset = col.hoffset
                    voffset = col.voffset

                    cattr = self._colorize(col, row, cellval)
                    cattr = update_attr(cattr, basecellcattr)

                    note = getattr(cellval, 'note', None)
                    notewidth = 1 if note else 0
                    if note:
                        notecattr = update_attr(cattr, colors.get_color(cellval.notecolor), 10)
                        clipdraw(scr, ybase, x+colwidth-notewidth, note, notecattr)

                    lines = lines[voffset:]

                    if len(lines) > height:
                        lines = lines[:height]
                    elif len(lines) < height:
                        lines.extend([[('', '')]]*(height-len(lines)))

                    for i, chunks in enumerate(lines):
                        y = ybase+i

                        sepchars = seps[i]

                        pre = disp_truncator if hoffset != 0 else disp_column_fill
                        prechunks = []
                        if colwidth > 2:
                            prechunks.append(('', pre))

                        for attr, text in chunks:
                            prechunks.append((attr, text[hoffset:]))

                        clipdraw_chunks(scr, y, x, prechunks, cattr, w=colwidth-notewidth)
                        vd.onMouse(scr, x, y, colwidth, 1, BUTTON3_RELEASED='edit-cell')

                        if sepchars and x+colwidth+dispwidth(sepchars) <= self.windowWidth:
                            scr.addstr(y, x+colwidth, sepchars, sepcattr.attr)

            for notefunc in vd.rowNoters:
                ch = notefunc(self, row)
                if ch:
                    clipdraw(scr, ybase, 0, ch, colors.color_note_row)
                    break

            return height

vd.rowNoters = [
    # f(sheet, row) -> character to be displayed on the left side of row
]

Sheet = TableSheet  # deprecated in 2.0 but still widely used internally


class SequenceSheet(Sheet):
    'Sheets with ``ColumnItem`` columns, and rows that are Python sequences (list, namedtuple, etc).'
    def setCols(self, headerrows):
        self.columns = []
        vd.clearCaches()  #1997
        for i, colnamelines in enumerate(itertools.zip_longest(*headerrows, fillvalue='')):
            colnamelines = ['' if c is None else c for c in colnamelines]
            self.addColumn(ColumnItem(''.join(map(str, colnamelines)), i))

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
        for i in range(self.options.getobj(optname, self)):
            try:
                yield next(it)
            except StopIteration:
                break

    def loader(self):
        'Skip first options.skip rows; set columns from next options.header rows.'

        itsource = self.iterload()

        # skip the first options.skip rows
        list(self.optlines(itsource, 'skip'))

        # use the next options.header rows as columns
        self.setCols(list(self.optlines(itsource, 'header')))

        self.rows = []
        # add the rest of the rows
        for i, r in enumerate(vd.Progress(itsource, gerund='loading', total=0)):
            if self.precious and i > self.options.max_rows:
                break
            self.addRow(r)


@VisiData.property
@drawcache
def _evalcontexts(vd):
    return {}

## VisiData sheet manipulation

@VisiData.api
def replace(vd, vs):
    'Replace top sheet with the given sheet `vs`.'
    vd.sheets.pop(0)
    return vd.push(vs)


@VisiData.api
def remove(vd, vs):
    'Remove *vs* from sheets stack, without asking for confirmation.'
    if vs in vd.sheets:
        vd.sheets.remove(vs)
        if vs in vd.allSheets:
            vd.allSheets.remove(vs)
            vd.allSheets.append(vs)
    else:
        vd.fail('sheet not on stack')


@VisiData.api
def push(vd, vs, pane=0, load=True):
    'Push Sheet *vs* onto ``vd.sheets`` stack for *pane* (0 for active pane, -1 for inactive pane).  Remove from other position if already on sheets stack.'
    if not isinstance(vs, BaseSheet):
        return  # return instead of raise, some commands need this

    if vs in vd.sheets:
        vd.sheets.remove(vs)

    vs.vd = vd
    if pane == -1:
        vs.pane = 2 if vd.activePane == 1 else 1
    elif pane == 0:
        if not vd.sheetstack(1): vd.activePane=vs.pane=1
        elif not vd.sheetstack(2) and vd.options.disp_splitwin_pct != 0: vd.activePane=vs.pane=2
        else: vs.pane = vd.activePane
    else:
        vs.pane = pane

    vd.sheets.insert(0, vs)

    if vs.precious and vs not in vd.allSheets:
        vd.allSheets.append(vs)

    if load:
        vs.ensureLoaded()
    if vd.activeCommand:
        vs.longname = vd.activeCommand.longname


@VisiData.api
def quit(vd, *sheets):
    'Remove *sheets* from sheets stack, asking for confirmation if needed.'

    for vs in sheets:
        vs.confirmQuit('quit')
        vs.pane = 0
        vd.remove(vs)
    if vd.activeCommand:
        vd.activeSheet.longname = vd.activeCommand.longname


@BaseSheet.api
def confirmQuit(vs, verb='quit'):
    if vs.options.quitguard and vs.precious and vs.hasBeenModified and not vd._nextCommands:
        vd.draw_all()
        vd.confirm(f'{verb} modified sheet "{vs.name}"? ')
    elif vs.options.getonly('quitguard', vs, False) and not vd._nextCommands:  # if this sheet is specifically guarded
        vd.draw_all()
        vd.confirm(f'{verb} guarded sheet "{vs.name}"? ')


@BaseSheet.api
def preloadHook(sheet):
    'Override to setup for reload().'
    sheet.confirmQuit('reload')

    sheet.hasBeenModified = False


@VisiData.api
def newSheet(vd, name, ncols, **kwargs):
    return Sheet(name, columns=[SettableColumn(width=vd.options.default_width) for i in range(ncols)], **kwargs)


@BaseSheet.api
def quitAndReleaseMemory(vs):
    'Release largest memory consumer refs on *vs* to free up memory.'
    if isinstance(vs.source, visidata.Path):
        vs.source.lines.clear() # clear cache of read lines

    if vs.precious: # only precious sheets have meaningful data
        vs.confirmQuit('quit')
        vs.rows.clear()
        vs.rows = UNLOADED
        vd.remove(vs)
        vd.allSheets.remove(vs)


@BaseSheet.api
def splitPane(sheet, pct=None):
    if vd.activeStack[1:]:
        undersheet = vd.activeStack[1]
        pane = 1 if undersheet.pane == 2 else 2
        vd.push(undersheet, pane=pane)
        vd.activePane = pane

    vd.options.disp_splitwin_pct = pct


@Sheet.api
def async_deepcopy(sheet, rowlist):
    @asyncthread
    def _async_deepcopy(newlist, oldlist):
        for r in vd.Progress(oldlist, 'copying'):
            newlist.append(deepcopy(r))

    ret = []
    _async_deepcopy(ret, rowlist)
    return ret



BaseSheet.init('pane', lambda: 1)


BaseSheet.addCommand('^R', 'reload-sheet', 'preloadHook(); reload()', 'Reload current sheet')
Sheet.addCommand('', 'show-cursor', 'status(statusLine)', 'show cursor position and bounds of current sheet on status line')

Sheet.addCommand('!', 'key-col', 'toggleKeys([cursorCol])', 'toggle current column as a key column')
Sheet.addCommand('z!', 'key-col-off', 'unsetKeys([cursorCol])', 'unset current column as a key column')

Sheet.addCommand('e', 'edit-cell', 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex)) if not (cursorRow is None) else fail("no rows to edit")', 'edit contents of current cell')
Sheet.addCommand('ge', 'setcol-input', 'cursorCol.setValuesTyped(selectedRows, input("set selected to: ", value=cursorDisplay))', 'set contents of current column for selected rows to same input')

Sheet.addCommand('"', 'dup-selected', 'vs=copy(sheet); vs.name += "_selectedref"; vs.reload=lambda vs=vs,rows=selectedRows: setattr(vs, "rows", list(rows)); vd.push(vs)', 'open a duplicate sheet with only the selected rows')
Sheet.addCommand('g"', 'dup-rows', 'vs=copy(sheet); vs.name+="_copy"; vs.rows=list(rows); status("copied "+vs.name); vs.select(selectedRows); vd.push(vs)', 'open a duplicate sheet with all rows')
Sheet.addCommand('z"', 'dup-selected-deep', 'vs = deepcopy(sheet); vs.name += "_selecteddeepcopy"; vs.rows = vs.async_deepcopy(selectedRows); vd.push(vs); status("pushed sheet with async deepcopy of selected rows")', 'open duplicate sheet with deepcopy of selected rows')
Sheet.addCommand('gz"', 'dup-rows-deep', 'vs = deepcopy(sheet); vs.name += "_deepcopy"; vs.rows = vs.async_deepcopy(rows); vd.push(vs); status("pushed sheet with async deepcopy of all rows")', 'open duplicate sheet with deepcopy of all rows')

Sheet.addCommand('z~', 'type-any', 'cursorCol.type = anytype', 'set type of current column to anytype')
Sheet.addCommand('~', 'type-string', 'cursorCol.type = str', 'set type of current column to str')
Sheet.addCommand('#', 'type-int', 'cursorCol.type = int', 'set type of current column to int')
Sheet.addCommand('z#', 'type-len', 'cursorCol.type = vlen', 'set type of current column to len')
Sheet.addCommand('%', 'type-float', 'cursorCol.type = float', 'set type of current column to float')
Sheet.addCommand('', 'type-floatlocale', 'cursorCol.type = floatlocale', 'set type of current column to float using system locale set in LC_NUMERIC')

BaseSheet.addCommand('q', 'quit-sheet',  'vd.quit(sheet)', 'quit current sheet')
BaseSheet.addCommand('Q', 'quit-sheet-free',  'quitAndReleaseMemory()', 'discard current sheet and free memory')
globalCommand('gq', 'quit-all', 'vd.quit(*vd.sheets)', 'quit all sheets (clean exit)')

BaseSheet.addCommand('Z', 'splitwin-half', 'splitPane(vd.options.disp_splitwin_pct or 50)', 'ensure split pane is set and push under sheet onto other pane')
BaseSheet.addCommand('gZ', 'splitwin-close', 'vd.options.disp_splitwin_pct = 0\nfor vs in vd.activeStack: vs.pane = 1', 'close split screen')
BaseSheet.addCommand('^I', 'splitwin-swap', 'vd.activePane = 1 if sheet.pane == 2 else 2', 'jump to inactive pane')
BaseSheet.addCommand('g^I', 'splitwin-swap-pane', 'vd.options.disp_splitwin_pct=-vd.options.disp_splitwin_pct', 'swap panes onscreen')
BaseSheet.addCommand('zZ', 'splitwin-input', 'vd.options.disp_splitwin_pct = input("% height for split window: ", value=vd.options.disp_splitwin_pct)', 'set split pane to specific size')

BaseSheet.addCommand('^L', 'redraw', 'sheet.refresh(); vd.redraw()', 'Refresh screen')
BaseSheet.addCommand(None, 'guard-sheet', 'options.set("quitguard", True, sheet); status("guarded")', 'Set quitguard on current sheet to confirm before quit')
BaseSheet.addCommand(None, 'guard-sheet-off', 'options.set("quitguard", False, sheet); status("unguarded")', 'Unset quitguard on current sheet to not confirm before quit')
BaseSheet.addCommand(None, 'open-source', 'vd.replace(source)', 'jump to the source of this sheet')

BaseSheet.bindkey('KEY_RESIZE', 'redraw')

BaseSheet.addCommand('A', 'open-new', 'vd.push(vd.newSheet("unnamed", 1))', 'Open new empty sheet')

BaseSheet.addCommand('`', 'open-source', 'vd.push(source)', 'open source sheet')
BaseSheet.addCommand(None, 'rename-sheet', 'sheet.name = input("rename sheet to: ", value=cleanName(sheet.name))', 'Rename current sheet')

Sheet.addCommand('', 'addcol-source', 'source.addColumn(copy(cursorCol)) if isinstance (source, BaseSheet) else error("source must be sheet")', 'add copy of current column to source sheet')  #988  frosencrantz


@Column.api
def formatter_enum(col, fmtdict):
    return lambda val, fmtdict=fmtdict,*args,**kwargs: fmtdict.__getitem__(val)

Sheet.addCommand('', 'setcol-formatter', 'cursorCol.formatter=input("set formatter to: ", value=cursorCol.formatter or "generic")', 'set formatter for current column (generic, json, python)')
Sheet.addCommand('', 'setcol-format-enum', 'cursorCol.fmtstr=input("format replacements (k=v): ", value=f"{cursorDisplay}=", i=len(cursorDisplay)+1); cursorCol.formatter="enum"', 'add secondary type translator to current column from input enum (space-separated)')


vd.addGlobals(
    RowColorizer=RowColorizer,
    CellColorizer=CellColorizer,
    ColumnColorizer=ColumnColorizer,
    RecursiveExprException=RecursiveExprException,
    LazyComputeRow=LazyComputeRow,
    Sheet=Sheet,
    TableSheet=TableSheet,
    SequenceSheet=SequenceSheet)

vd.addMenuItems('''
    File > New > open-new
    File > Rename > rename-sheet
    File > Guard > on > guard-sheet
    File > Guard > off > guard-sheet-off
    File > Duplicate > selected rows by ref > dup-selected
    File > Duplicate > all rows by ref > dup-rows
    File > Duplicate > selected rows deep > dup-selected-deep
    File > Duplicate > all rows deep > dup-rows-deep
    File > Reload > rows and columns > reload-sheet
    File > Quit > top sheet > quit-sheet
    File > Quit > all sheets > quit-all
    Edit > Modify > current cell > input > edit-cell
    Edit > Modify > selected cells > from input > setcol-input
    View > Sheets > stack > sheets-stack
    View > Sheets > all > sheets-all
    View > Other sheet > source sheet > open-source
    View > Split pane > in half > splitwin-half
    View > Split pane > in percent > splitwin-input
    View > Split pane > unsplit > splitwin-close
    View > Split pane > swap panes > splitwin-swap-pane
    View > Split pane > goto other pane > splitwin-swap
    View > Refresh screen > redraw
    Column > Type as > anytype > type-any
    Column > Type as > string > type-string
    Column > Type as > integer > type-int
    Column > Type as > float > type-float
    Column > Type as > locale float > type-floatlocale
    Column > Type as > length > type-len
    Column > Key > toggle current column > key-col
    Column > Key > unkey current column > key-col-off
''')
