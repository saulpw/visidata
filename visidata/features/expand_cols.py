import math
from functools import singledispatch

from visidata import vd, Sheet, asyncthread, Progress, Column, VisiData, deduceType, anytype, getitemdef


@Sheet.api
def getSampleRows(sheet):
    'Return list of sample rows centered around the cursor.'
    n = sheet.options.default_sample_size
    if n == 0 or n >= sheet.nRows:
        return sheet.rows

    vd.warning(f'sampling {n} rows')
    seq = sheet.rows
    start = math.ceil(sheet.cursorRowIndex - n / 2) % len(seq)
    end = (start + n) % len(seq)
    if start < end:
        return seq[start:end]
    return seq[start:] + seq[:end]

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
    create, and their presumed types'''
    def lenNoExceptions(v):
        try:
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
def closeColumn(sheet, col):
    if hasattr(col, 'origCol'):
        origCol = col.origCol
    else:
        vd.fail('column has not been expanded')
    vd.addUndo(setattr, sheet, 'columns', sheet.columns)
    origCol.width = sheet.options.default_width
    cols = [c for c in sheet.columns if getattr(c, "origCol", None) is not origCol]
    sheet.columns = cols


@Sheet.api
@asyncthread
def expand_cols_deep(sheet, cols, rows=None, depth=0):  # depth == 0 means drill all the way
    return sheet.expandCols(cols, rows=rows, depth=depth)


Sheet.addCommand('(', 'expand-col', 'expand_cols_deep([cursorCol], depth=1)', 'expand current column of containers one level')
Sheet.addCommand('g(', 'expand-cols', 'expand_cols_deep(visibleCols, depth=1)', 'expand all visible columns of containers one level')
Sheet.addCommand('z(', 'expand-col-depth', 'expand_cols_deep([cursorCol], depth=int(input("expand depth=", value=0)))', 'expand current column of containers to given depth (0=fully)')
Sheet.addCommand('gz(', 'expand-cols-depth', 'expand_cols_deep(visibleCols, depth=int(input("expand depth=", value=0)))', 'expand all visible columns of containers to given depth (0=fully)')

Sheet.addCommand(')', 'contract-col', 'closeColumn(cursorCol)', 'unexpand current column; restore original column and remove other columns at this level')

vd.addMenuItems('''
    Column > Expand > one level > expand-col
    Column > Expand > to depth > expand-col-depth
    Column > Expand > all columns one level > expand-cols
    Column > Expand > all columns to depth > expand-cols-depth
    Column > Contract > contract-col
''')
