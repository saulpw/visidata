from functools import singledispatch

from visidata import *

option('visibility', 0, 'visibility level')
option('expand_col_scanrows', 1000, 'number of rows to check when expanding columns (0 = all)')


class PythonSheet(Sheet):
    def openRow(self, row):
        return load_pyobj("%s[%s]" % (self.name, self.keystr(row)), row)

def _getWraparoundSlice(seq, n, center):
    '''Return a slice of length n from a sequence, centered around a given index'''
    start = int(center - n / 2) % len(seq)
    end = (start + n) % len(seq)
    if start < end:
        return seq[start:end]
    return seq[start:] + seq[:end]

@asyncthread
def expand_cols_deep(sheet, cols, rows=None, depth=0):  # depth == 0 means drill all the way
    'expand all visible columns of containers to the given depth (0=fully)'
    ret = []
    if not rows:
        scanrows = options.expand_col_scanrows
        if scanrows == 0 or scanrows >= sheet.nRows:
            rows = sheet.rows
        else:
            rows = _getWraparoundSlice(sheet.rows, scanrows, sheet.cursorRowIndex)

    for col in cols:
        newcols = _addExpandedColumns(col, rows, sheet.columns.index(col))
        if depth != 1:  # countdown not yet complete, or negative (indefinite)
            ret.extend(expand_cols_deep.__wrapped__(sheet, newcols, rows, depth-1))
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
        ExpandedColumn('%s.%s' % (col.name, k), type=v, origCol=col, key=k)
            for k, v in newcols.items()
    ]

@_createExpandedColumns.register(list)
@_createExpandedColumns.register(tuple)
def _(sampleValue, col, vals):
    '''Use the longest sequence to determine the number of columns we need to
    create, and their presumed types'''
    longestSeq = max(vals, key=len)
    colTypes = [deduceType(v) for v in longestSeq]
    return [
        ExpandedColumn('%s[%s]' % (col.name, k), type=colType, origCol=col, key=k)
            for k, colType in enumerate(colTypes)
    ]

def _addExpandedColumns(col, rows, idx):
    isNull = isNullFunc()
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

    for i, c in enumerate(expandedCols):
        col.sheet.addColumn(c, idx+i+1)
    if expandedCols:
        col.hide()
    return expandedCols


def deduceType(v):
    if isinstance(v, (float, int)):
        return type(v)
    else:
        return anytype


class ExpandedColumn(Column):
    def calcValue(self, row):
        return getitemdef(self.origCol.getValue(row), self.key)

    def setValue(self, row, value):
        self.origCol.getValue(row)[self.key] = value


def closeColumn(sheet, col):
    if hasattr(col, 'origCol'):
        origCol = col.origCol
    else:
        fail('column has not been expanded')
    vd.addUndo(setattr, sheet, 'columns', sheet.columns)
    origCol.width = options.default_width
    cols = [c for c in sheet.columns if getattr(c, "origCol", None) is not origCol]
    sheet.columns = cols


#### generic list/dict/object browsing
def push_pyobj(name, pyobj):
    vs = load_pyobj(name, pyobj)
    if vs:
        return vd.push(vs)
    else:
        error("cannot push '%s' as pyobj" % type(pyobj).__name__)

def view(obj):
    run(load_pyobj(getattr(obj, '__name__', ''), obj))

@VisiData.global_api
def load_pyobj(vd, name, pyobj):
    'Return Sheet object of appropriate type for given sources in `args`.'
    if isinstance(pyobj, list) or isinstance(pyobj, tuple):
        if getattr(pyobj, '_fields', None):  # list of namedtuple
            return SheetNamedTuple(name, pyobj)
        else:
            return SheetList(name, pyobj)
    elif isinstance(pyobj, dict):
        return SheetDict(name, source=pyobj)
    elif isinstance(pyobj, str):
        return TextSheet(name, source=pyobj.splitlines())
    elif isinstance(pyobj, bytes):
        return TextSheet(name, source=pyobj.decode(options.encoding).splitlines())
    elif isinstance(pyobj, object):
        return PyobjSheet(name, source=pyobj)
    else:
        error("cannot load '%s' as pyobj" % type(pyobj).__name__)


def getPublicAttrs(obj):
    'Return all public attributes (not methods or `_`-prefixed) on object.'
    return [k for k in dir(obj) if not k.startswith('_') and not callable(getattr(obj, k))]

def PyobjColumns(obj):
    'Return columns for each public attribute on an object.'
    return [ColumnAttr(k, type=deduceType(getattr(obj, k))) for k in getPublicAttrs(obj)]

def AttrColumns(attrnames):
    'Return column names for all elements of list `attrnames`.'
    return [ColumnAttr(name) for name in attrnames]

def DictKeyColumns(d):
    'Return a list of Column objects from dictionary keys.'
    return [ColumnItem(k, k, type=deduceType(d[k])) for k in d.keys()]

def SheetList(name, src, **kwargs):
    'Creates a Sheet from a list of homogenous dicts or namedtuples.'

    if not src:
        status('no content in ' + name)
        return

    if isinstance(src[0], dict):
        return ListOfDictSheet(name, source=src, **kwargs)
    elif isinstance(src[0], tuple):
        if getattr(src[0], '_fields', None):  # looks like a namedtuple
            return ListOfNamedTupleSheet(name, source=src, **kwargs)

    # simple list
    return ListOfPyobjSheet(name, source=src, **kwargs)

class ListOfPyobjSheet(PythonSheet):
    rowtype = 'python objects'
    def reload(self):
        self.rows = self.source
        self.columns = []
        self.addColumn(Column(self.name,
                               getter=lambda col,row: row,
                               setter=lambda col,row,val: setitem(col.sheet.source, col.sheet.source.index(row), val)))

        for c in PyobjColumns(self.rows[0]):
            self.addColumn(c)

        if len(self.columns) > 1:
            self.columns[0].width = 0

# rowdef: dict
class ListOfDictSheet(PythonSheet):
    rowtype = 'dicts'
    def reload(self):
        self.columns = []
        addedCols = set()
        for row in self.source:
            newCols = {k: v for k, v in row.items() if k not in addedCols}
            if not newCols:
                continue
            for c in DictKeyColumns(newCols):
                self.addColumn(c)
                addedCols.add(c.name)
        self.rows = self.source

# rowdef: namedtuple
class ListOfNamedTupleSheet(PythonSheet):
    rowtype = 'namedtuples'
    def reload(self):
        self.columns = []
        for i, k in enumerate(self.source[0]._fields):
            self.addColumn(ColumnItem(k, i))
        self.rows = self.source


# rowdef: PyObj
class SheetNamedTuple(PythonSheet):
    'a single namedtuple, with key and value columns'
    rowtype = 'values'
    columns = [ColumnItem('name', 0), ColumnItem('value', 1)]

    def __init__(self, name, src, **kwargs):
        super().__init__(name, source=src, **kwargs)

    def reload(self):
        self.rows = list(zip(self.source._fields, self.source))

    def openRow(self, row):
        return load_pyobj(joinSheetnames(self.name, row[0]), row[1])


# source is dict
class SheetDict(PythonSheet):
    rowtype = 'items'  # rowdef: keys
    columns = [
        Column('key'),
        Column('value', getter=lambda c,r: c.sheet.source[r],
                        setter=lambda c,r,v: setitem(c.sheet.source, r, v)),
    ]
    nKeys = 1
    def reload(self):
        self.rows = list(self.source.keys())

    def openRow(self, row):
        return load_pyobj(joinSheetnames(self.name, row), self.source[row])


class ColumnSourceAttr(Column):
    'Use row as attribute name on sheet source'
    def calcValue(self, attrname):
        return getattr(self.sheet.source, attrname)
    def setValue(self, attrname, value):
        return setattr(self.sheet.source, attrname, value)

def docstring(obj, attr):
    v = getattr(obj, attr)
    if callable(v):
        return v.__doc__
    return '<type %s>' % type(v).__name__

# rowdef: attrname
class PyobjSheet(PythonSheet):
    rowtype = 'attributes'
    columns = [
        Column('attribute'),
        ColumnSourceAttr('value'),
        Column('docstring', getter=lambda c,r: docstring(c.sheet.source, r))
    ]
    nKeys = 1

    def reload(self):
        self.rows = []
        vislevel = options.visibility
        for r in dir(self.source):
            try:
                if vislevel <= 2 and r.startswith('__'): continue
                if vislevel <= 1 and r.startswith('_'): continue
                if vislevel <= 0 and callable(getattr(self.source, r)): continue
                self.addRow(r)
            except Exception:
                pass

    def openRow(self, row):
        'dive further into Python object'
        v = getattr(self.source, row)
        return load_pyobj(self.name + "." + str(row), v() if callable(v) else v)


globalCommand('^X', 'pyobj-expr', 'expr = input("eval: ", "expr", completer=CompleteExpr()); push_pyobj(expr, evalexpr(expr, None))', 'evaluate Python expression and open result as Python object')
globalCommand('g^X', 'exec-python', 'expr = input("exec: ", "expr", completer=CompleteExpr()); exec(expr, getGlobals())', 'execute Python statement in the global scope')
globalCommand('z^X', 'pyobj-expr-row', 'expr = input("eval over current row: ", "expr", completer=CompleteExpr()); push_pyobj(expr, evalexpr(expr, cursorRow))', 'evaluate Python expression, in context of current row, and open result as Python object')

Sheet.addCommand('^Y', 'pyobj-row', 'status(type(cursorRow)); push_pyobj("%s[%s]" % (sheet.name, cursorRowIndex), cursorRow)', 'open current row as Python object')
Sheet.addCommand('z^Y', 'pyobj-cell', 'status(type(cursorValue)); push_pyobj("%s[%s].%s" % (sheet.name, cursorRowIndex, cursorCol.name), cursorValue)', 'open current cell as Python object')
globalCommand('g^Y', 'pyobj-sheet', 'status(type(sheet)); push_pyobj(sheet.name+"_sheet", sheet)', 'open current sheet as Python object')

Sheet.addCommand('(', 'expand-col', 'expand_cols_deep(sheet, [cursorCol], depth=0)', 'expand current column of containers fully')
Sheet.addCommand('g(', 'expand-cols', 'expand_cols_deep(sheet, visibleCols, depth=0)', 'expand all visible columns of containers fully')
Sheet.addCommand('z(', 'expand-col-depth', 'expand_cols_deep(sheet, [cursorCol], depth=int(input("expand depth=", value=1)))', 'expand current column of containers to given depth (0=fully)')
Sheet.addCommand('gz(', 'expand-cols-depth', 'expand_cols_deep(sheet, visibleCols, depth=int(input("expand depth=", value=1)))', 'expand all visible columns of containers to given depth (0=fully)')

Sheet.addCommand(')', 'contract-col', 'closeColumn(sheet, cursorCol)', 'unexpand current column; restore original column and remove other columns at this level')

PyobjSheet.addCommand('v', 'visibility', 'sheet.options.visibility = 0 if sheet.options.visibility else 2; reload()', 'toggle show/hide for methods and hidden properties')
PyobjSheet.addCommand('gv', 'show-hidden', 'sheet.options.visibility = 2; reload()', 'show methods and hidden properties')
PyobjSheet.addCommand('zv', 'hide-hidden', 'sheet.options.visibility -= 1; reload()', 'hide methods and hidden properties')
