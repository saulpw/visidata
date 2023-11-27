import math
import random
import os.path
from functools import singledispatch

from visidata import vd, Sheet, asyncthread, Progress, Column, VisiData, deduceType, anytype, getitemdef, ColumnsSheet


@Sheet.api
def getSampleRows(sheet):
    'Return list of sample rows, including the cursor row as the first row.'

    # do not include cursorRow in sample
    ret = sheet.rows[:sheet.cursorRowIndex] + sheet.rows[sheet.cursorRowIndex+1:]

    n = sheet.options.default_sample_size
    if n != 0 and n < sheet.nRows:
        vd.aside(f'sampling {n} rows')
        ret = random.sample(ret, n)

    return [sheet.cursorRow] + ret


@Sheet.api
def expandCols(sheet, cols, rows=None, depth=0):
    'expand all visible columns of containers to the given depth (0=fully)'
    ret = []
    if not rows:
        rows = sheet.getSampleRows()

    for col in cols:
        newcols = col.expand(rows)
        if depth != 1:  # countdown not yet complete, or negative (indefinite)
            ret.extend(sheet.expandCols(newcols, rows, depth-1))
    return ret

@singledispatch
def _createExpandedColumns(sampleValue, col, rows):
    '''By default, a column is not expandable. Supported container types for
    sampleValue trigger alternate, type-specific expansions.'''
    return []

@_createExpandedColumns.register(dict)
def _(sampleValue, col, vals):
    '''Build a set of columns to add, using the first occurrence of each key to
    determine column type'''
    newcols = {}

    for val in Progress(vals, 'expanding'):
        if not isinstance(val, dict):  # allow mixed-use columns
            continue
        colsToAdd = set(val).difference(newcols)
        colsToAdd and newcols.update({
            k: deduceType(v)
            for k, v in val.items()
            if k in colsToAdd
        })

    return [
        ExpandedColumn(col.sheet.options.fmt_expand_dict % (col.name, k), type=v, origCol=col, expr=k)
            for k, v in newcols.items()
    ]

def _createExpandedColumnsNamedTuple(col, val):
    return [
        ExpandedColumn(col.sheet.options.fmt_expand_dict % (col.name, k), type=colType, origCol=col, expr=i)
            for i, (k, colType) in enumerate(zip(val._fields, (deduceType(v) for v in val)))
    ]

@_createExpandedColumns.register(list)
@_createExpandedColumns.register(tuple)
def _(sampleValue, col, vals):
    '''Use the longest sequence to determine the number of columns we need to
    create, and their presumed types.  Ignore strings and exceptions. '''
    def lenNoExceptions(v):
        try:
            if isinstance(v, str):
                return 0
            return len(v)
        except Exception as e:
            return 0

    if hasattr(sampleValue, '_fields'):  # looks like a namedtuple
        return _createExpandedColumnsNamedTuple(col, vals[0])

    longestSeq = max(vals, key=lenNoExceptions)
    colTypes = [deduceType(v) for v in longestSeq]
    return [
        ExpandedColumn(col.sheet.options.fmt_expand_list % (col.name, k), type=colType, origCol=col, expr=k)
            for k, colType in enumerate(colTypes)
    ]


@Column.api
def expand(col, rows):
    isNull = col.sheet.isNullFunc()
    nonNulls = [
        col.getTypedValue(row)
        for row in rows
        if not isNull(col.getValue(row))
    ]

    if not nonNulls:
        return []

    # The type of the first non-null value for col determines if and how the
    # column can be expanded.
    expandedCols = _createExpandedColumns(nonNulls[0], col, nonNulls)

    idx = col.sheet.columns.index(col)

    for i, c in enumerate(expandedCols):
        col.sheet.addColumn(c, index=idx+i+1)
    if expandedCols:
        col.hide()
    return expandedCols


@VisiData.api
class ExpandedColumn(Column):
    def calcValue(self, row):
        return getitemdef(self.origCol.getValue(row), self.expr)

    def setValue(self, row, value):
        self.origCol.getValue(row)[self.expr] = value


@Sheet.api
@asyncthread
def contract_cols(sheet, cols, depth=1):  # depth == 0 means contract all the way
    'Remove any columns in cols with .origCol, and also remove others in sheet.columns which share those .origCol.  The inverse of expand.'
    vd.addUndo(setattr, sheet, 'columns', sheet.columns)
    for i in range(depth or 10000):
        colsToClose = [c for c in cols if getattr(c, "origCol", None)]

        if not colsToClose:
            break

        origCols = set(c.origCol for c in colsToClose)
        for col in origCols:
            col.width = sheet.options.default_width

        sheet.columns = [col for col in sheet.columns if getattr(col, 'origCol', None) not in origCols]


@Sheet.api
@asyncthread
def expand_cols_deep(sheet, cols, rows=None, depth=0):  # depth == 0 means drill all the way
    return sheet.expandCols(cols, rows=rows, depth=depth)


@ColumnsSheet.api
def contract_source_cols(sheet, cols):
    prefix = os.path.commonprefix([c.name for c in cols])
    ret = ColumnGroup(prefix or 'group', prefix=prefix, sourceCols=cols)
    for c in cols:
        c.origCol = ret
    for vs in sheet.source:
        vd.addUndo(setattr, vs, 'columns', vs.columns)
        vs.columns[:] = [c for c in vs.columns if c not in cols]
    return ret


class ColumnGroup(Column):
    def calcValue(self, row):
        return {c.name[len(self.prefix):]:c.getValue(row) for c in self.sourceCols}

    def expand(self, rows):
        idx = self.sheet.columns.index(self)

        for i, c in enumerate(self.sourceCols):
            self.sheet.addColumn(c, index=idx+i+1)

        self.hide()

        return self.sourceCols


Sheet.addCommand('(', 'expand-col', 'expand_cols_deep([cursorCol], depth=1)', 'expand current column of containers one level')
Sheet.addCommand('g(', 'expand-cols', 'expand_cols_deep(visibleCols, depth=1)', 'expand all visible columns of containers one level')
Sheet.addCommand('z(', 'expand-col-depth', 'expand_cols_deep([cursorCol], depth=int(input("expand depth=", value=0)))', 'expand current column of containers to given depth (0=fully)')
Sheet.addCommand('gz(', 'expand-cols-depth', 'expand_cols_deep(visibleCols, depth=int(input("expand depth=", value=0)))', 'expand all visible columns of containers to given depth (0=fully)')

Sheet.addCommand(')', 'contract-col', 'contract_cols([cursorCol])', 'remove current column and siblings from sheet columns and unhide parent')
Sheet.addCommand('g)', 'contract-cols', 'contract_cols(visibleCols)', 'remove all child columns and unhide toplevel parents')
Sheet.addCommand('z)', 'contract-col-depth', 'contract_cols([cursorCol], depth=int(input("contract depth=", value=0)))', 'remove current column and siblings from sheet columns and unhide parent')
Sheet.addCommand('gz)', 'contract-cols-depth', 'contract_cols(visibleCols, depth=int(input("contract depth=", value=0)))', 'remove all child columns and unhide toplevel parents')

ColumnsSheet.addCommand(')', 'contract-source-cols', 'source[0].addColumn(contract_source_cols(someSelectedRows), index=cursorRowIndex)', 'contract selected columns into column group')  #1702


vd.addMenuItems('''
    Column > Expand > one level > expand-col
    Column > Expand > to depth N > expand-col-depth
    Column > Expand > all columns one level > expand-cols
    Column > Expand > all columns to depth > expand-cols-depth
    Column > Contract > one level > contract-col
    Column > Contract > N levels > contract-col-depth
    Column > Contract > all columns one level > contract-cols
    Column > Contract > all columns N levels > contract-cols-depth
    Column > Contract > selected columns on source sheet > contract-source-cols
''')
