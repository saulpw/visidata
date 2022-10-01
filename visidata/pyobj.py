from functools import singledispatch
from typing import Mapping
import inspect
import math

from visidata import *

vd.option('visibility', 0, 'visibility level')
vd.option('default_sample_size', 100, 'number of rows to sample for regex.split (0=all)', replay=True)
vd.option('fmt_expand_dict', '%s.%s', 'format str to use for names of columns expanded from dict (colname, key)') #1457
vd.option('fmt_expand_list', '%s[%s]', 'format str to use for names of columns expanded from list (colname, index)')


class PythonSheet(Sheet):
    def openRow(self, row):
        return PyobjSheet("%s[%s]" % (self.name, self.keystr(row)), source=row)


class InferColumnsSheet(Sheet):
    _rowtype = dict
    @asyncthread
    def reload(self):
        self.reloadCols()

        self.rows = []
        for r in self.iterload():
            self.addRow(r)

        # if an ordering has been specified, sort the sheet
        if self._ordering:
            vd.sync(self.sort())

    def reloadCols(self):
        self.columns = []
        self._knownKeys.clear()
        for c in type(self).columns:
            self.addColumn(deepcopy(c))

    def addColumn(self, *cols, index=None):
        for c in cols:
            self._knownKeys.add(c.expr or c.name)
        return super().addColumn(*cols, index=index)

    def addRow(self, row, index=None):
        ret = super().addRow(row, index=index)
        for k in row:
            if k not in self._knownKeys:
                self.addColumn(ColumnItem(k, type=deduceType(row[k])))

        return ret


InferColumnsSheet.init('_knownKeys', set, copy=True)  # set of row keys already seen
InferColumnsSheet.init('_ordering', list, copy=True)


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


@asyncthread
def expand_cols_deep(sheet, cols, rows=None, depth=0):  # depth == 0 means drill all the way
    'expand all visible columns of containers to the given depth (0=fully)'
    ret = []
    if not rows:
        rows = sheet.getSampleRows()

    for col in cols:
        newcols = col.expand(rows)
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


def deduceType(v):
    if isinstance(v, (float, int)):
        return type(v)
    else:
        return anytype


class ExpandedColumn(Column):
    def calcValue(self, row):
        return getitemdef(self.origCol.getValue(row), self.expr)

    def setValue(self, row, value):
        self.origCol.getValue(row)[self.expr] = value


def closeColumn(sheet, col):
    if hasattr(col, 'origCol'):
        origCol = col.origCol
    else:
        vd.fail('column has not been expanded')
    vd.addUndo(setattr, sheet, 'columns', sheet.columns)
    origCol.width = options.default_width
    cols = [c for c in sheet.columns if getattr(c, "origCol", None) is not origCol]
    sheet.columns = cols


#### generic list/dict/object browsing
@VisiData.global_api
def view(vd, obj):
    vd.run(PyobjSheet(getattr(obj, '__name__', ''), source=obj))



def getPublicAttrs(obj):
    'Return all public attributes (not methods or `_`-prefixed) on object.'
    return [k for k in dir(obj) if not k.startswith('_') and not callable(getattr(obj, k))]

def PyobjColumns(obj):
    'Return columns for each public attribute on an object.'
    return [ColumnAttr(k, type=deduceType(getattr(obj, k))) for k in getPublicAttrs(obj)]

def AttrColumns(attrnames):
    'Return column names for all elements of list `attrnames`.'
    return [ColumnAttr(name) for name in attrnames]


def SheetList(*names, **kwargs):
    'Creates a Sheet from a list of homogenous dicts or namedtuples.'

    src = kwargs.get('source', None)
    if not src:
        vd.status('no content in %s' % names)
        return

    if isinstance(src[0], dict):
        return ListOfDictSheet(*names, **kwargs)
    elif isinstance(src[0], tuple):
        if getattr(src[0], '_fields', None):  # looks like a namedtuple
            return ListOfNamedTupleSheet(*names, **kwargs)

    # simple list
    return ListOfPyobjSheet(*names, **kwargs)

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
        self._knownKeys = set()
        for row in self.source:
            for k in row:
                if k not in self._knownKeys:
                    self.addColumn(ColumnItem(k, k, type=deduceType(row[k])))
                    self._knownKeys.add(k)
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

    def __init__(self, *names, **kwargs):
        super().__init__(*names, **kwargs)

    def reload(self):
        self.rows = list(zip(self.source._fields, self.source))

    def openRow(self, row):
        return PyobjSheet(self.name, row[0], source=row[1])


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
        return PyobjSheet(self.name, row, source=self.source[row])


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
    'Generic Sheet for any Python object.  Return specialized subclasses for lists of objects, namedtuples, and dicts.'
    rowtype = 'attributes'
    columns = [
        Column('attribute'),
        ColumnSourceAttr('value'),
        Column('signature', width=0, getter=lambda c,r: dict(inspect.signature(getattr(c.sheet.source, r)).parameters)),
        Column('docstring', getter=lambda c,r: docstring(c.sheet.source, r))
    ]
    nKeys = 1

    def __new__(cls, *names, **kwargs):
        'Return Sheet object of appropriate type for given sources in `args`.'
        pyobj=kwargs.get('source', object())
        if isinstance(pyobj, list) or isinstance(pyobj, tuple):
            if getattr(pyobj, '_fields', None):  # list of namedtuple
                return SheetNamedTuple(*names, **kwargs)
            else:
                return SheetList(*names, **kwargs)
        elif isinstance(pyobj, Mapping):
            return SheetDict(*names, **kwargs)
        elif isinstance(pyobj, str):
            return TextSheet(*names, source=pyobj.splitlines())
        elif isinstance(pyobj, bytes):
            return TextSheet(*names, source=pyobj.decode(options.encoding).splitlines())
        elif isinstance(pyobj, object):
            obj = super().__new__(cls)  #, *names, **kwargs)
            return obj
        else:
            vd.error("cannot load '%s' as pyobj" % type(pyobj).__name__)

    def reload(self):
        self.rows = []
        vislevel = self.options.visibility
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
        return PyobjSheet(self.name + "." + str(row), source=v() if callable(v) else v)


@TableSheet.api
def openRow(sheet, row):
    'Return Sheet diving into *row*.'
    k = sheet.keystr(row) or sheet.cursorRowIndex
    name = f'{sheet.name}[{k}]'
    return TableSheet(name,
                      rows=sheet.visibleCols,
                      sourceRow=sheet.cursorRow,
                      columns=[
                        Column('column', getter=lambda c,r: r.name),
                        Column('value', getter=lambda c,r: r.getTypedValue(c.sheet.sourceRow), setter=lambda c,r,v: r.setValue(c.sheet.sourceRow, v)),
                      ],
                      nKeys=1)

@TableSheet.api
def openCell(sheet, col, row):
    'Return Sheet diving into cell at *row* in *col*.'
    k = sheet.keystr(row) or [str(sheet.cursorRowIndex)]
    name = f'{sheet.name}[{k}].{col.name}'
    return PyobjSheet(name, source=col.getTypedValue(row))


@BaseSheet.api
def pyobj_expr(sheet):
    def launch_repl(v, i):
        import code
        with SuspendCurses():
            code.InteractiveConsole(locals=locals()).interact()
        return v, i
    expr = vd.input("eval: ", "expr", completer=visidata.CompleteExpr(), bindings={'^X': launch_repl})
    vd.push(PyobjSheet(expr, source=sheet.evalExpr(expr)))

BaseSheet.addCommand('^X', 'pyobj-expr', 'pyobj_expr()', 'evaluate Python expression and open result as Python object')
BaseSheet.addCommand('', 'exec-python', 'expr = input("exec: ", "expr", completer=CompleteExpr()); exec(expr, getGlobals(), LazyChainMap(sheet, *vd.contexts, locals=vd.getGlobals()))', 'execute Python statement with expression scope')
BaseSheet.addCommand('g^X', 'import-python', 'modname=input("import: ", type="import_python"); exec("import "+modname, getGlobals())', 'import Python module in the global scope')
globalCommand('z^X', 'pyobj-expr-row', 'expr = input("eval over current row: ", "expr", completer=CompleteExpr()); vd.push(PyobjSheet(expr, source=evalExpr(expr, row=cursorRow)))', 'evaluate Python expression, in context of current row, and open result as Python object')

Sheet.addCommand('^Y', 'pyobj-row', 'status(type(cursorRow)); vd.push(PyobjSheet("%s[%s]" % (sheet.name, cursorRowIndex), source=cursorRow))', 'open current row as Python object')
Sheet.addCommand('z^Y', 'pyobj-cell', 'status(type(cursorValue)); vd.push(PyobjSheet("%s[%s].%s" % (sheet.name, cursorRowIndex, cursorCol.name), source=cursorValue))', 'open current cell as Python object')
globalCommand('g^Y', 'pyobj-sheet', 'status(type(sheet)); vd.push(PyobjSheet(sheet.name+"_sheet", source=sheet))', 'open current sheet as Python object')

Sheet.addCommand('(', 'expand-col', 'expand_cols_deep(sheet, [cursorCol], depth=1)', 'expand current column of containers one level')
Sheet.addCommand('g(', 'expand-cols', 'expand_cols_deep(sheet, visibleCols, depth=1)', 'expand all visible columns of containers one level')
Sheet.addCommand('z(', 'expand-col-depth', 'expand_cols_deep(sheet, [cursorCol], depth=int(input("expand depth=", value=1)))', 'expand current column of containers to given depth (0=fully)')
Sheet.addCommand('gz(', 'expand-cols-depth', 'expand_cols_deep(sheet, visibleCols, depth=int(input("expand depth=", value=1)))', 'expand all visible columns of containers to given depth (0=fully)')

Sheet.addCommand(')', 'contract-col', 'closeColumn(sheet, cursorCol)', 'unexpand current column; restore original column and remove other columns at this level')

Sheet.addCommand('', 'open-row-basic', 'vd.push(TableSheet.openRow(sheet, cursorRow))', 'open sheet with open sheet with copies of rows referenced in current row')
Sheet.addCommand(ENTER, 'open-row', 'vd.push(openRow(cursorRow))', 'open current row with sheet-specific dive')
Sheet.addCommand('z'+ENTER, 'open-cell', 'vd.push(openCell(cursorCol, cursorRow))', 'open sheet with copies of rows referenced in current cell')
Sheet.addCommand('g'+ENTER, 'dive-selected', 'for r in selectedRows: vd.push(openRow(r))', 'open sheet with copies of rows referenced in selected rows')
Sheet.addCommand('gz'+ENTER, 'dive-selected-cells', 'for r in selectedRows: vd.push(openCell(cursorCol, r))', 'open sheet with copies of rows referenced in selected rows')

PyobjSheet.addCommand('v', 'visibility', 'sheet.options.visibility = 0 if sheet.options.visibility else 2; reload()', 'toggle show/hide for methods and hidden properties')
PyobjSheet.addCommand('gv', 'show-hidden', 'sheet.options.visibility = 2; reload()', 'show methods and hidden properties')
PyobjSheet.addCommand('zv', 'hide-hidden', 'sheet.options.visibility -= 1; reload()', 'hide methods and hidden properties')

vd.addGlobals({
    'ExpandedColumn': ExpandedColumn,
    'PythonSheet': PythonSheet,
    'expand_cols_deep': expand_cols_deep,
    'deduceType': deduceType,
    'closeColumn': closeColumn,
    'ListOfDictSheet': ListOfDictSheet,
    'SheetDict': SheetDict,
    'InferColumnsSheet': InferColumnsSheet,
    'PyobjSheet': PyobjSheet,
    'view': view,
})
