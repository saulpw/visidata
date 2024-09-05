from typing import Mapping
import inspect
import math
import numbers

from visidata import vd, asyncthread, ENTER, deduceType
from visidata import Sheet, Column, VisiData, ColumnItem, TableSheet, BaseSheet, Progress, ColumnAttr, SuspendCurses, TextSheet, setitem
import visidata

vd.option('visibility', 0, 'visibility level')
vd.option('default_sample_size', 100, 'number of rows to sample for regex.split (0=all)', replay=True)
vd.option('fmt_expand_dict', '%s.%s', 'format str to use for names of columns expanded from dict (colname, key)') #1457
vd.option('fmt_expand_list', '%s[%s]', 'format str to use for names of columns expanded from list (colname, index)')


class PythonSheet(Sheet):
    def openRow(self, row):
        return PyobjSheet("%s[%s]" % (self.name, self.rowname(row)), source=row)

class PythonAtomSheet(PythonSheet):
    '''a sheet to display one Python object that does not offer deeper inspection,
        like None, a bool, or an int/float'''
    rowtype = 'object'  #singular, because it should only ever hold one
    columns = [
        Column('value', getter=lambda col,row: row,
                        setter=lambda c,r,v: None)
    ]
    def loader(self):
        self.rows = [self.source]
        self.column('value').type = deduceType(self.source)

    def openRow(self, row):
        vd.fail('cannot dive deeper on this object')
    def openCell(self, col, row, rowidx=None):
        vd.fail('cannot dive deeper on this object')
    def openRowPyobj(self, rowidx):
        vd.fail('cannot dive deeper on this object')
    def openCellPyobj(self, col, rowidx):
        vd.fail('cannot dive deeper on this object')
    def newRow(self):
        vd.fail('adding rows to this sheet is not supported')

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
    'Creates a Sheet from a list of homogeneous dicts or namedtuples.'

    src = kwargs.get('source', None)
    if not src:
        vd.warning('no content in %s' % names)
        return Sheet(*names, **kwargs)

    if isinstance(src[0], Mapping):
        return ListOfDictSheet(*names, **kwargs)
    elif isinstance(src[0], tuple):
        if getattr(src[0], '_fields', None):  # looks like a namedtuple
            return ListOfNamedTupleSheet(*names, **kwargs)

    # simple list
    return ListOfPyobjSheet(*names, **kwargs)

class ListOfPyobjSheet(PythonSheet):
    rowtype = 'python objects'
    def loader(self):
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
        return PyobjSheet(f'{self.name}.{row[0]}', source=row[1])


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
        return PyobjSheet(f'{self.name}.{row}', source=self.source[row])


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
        if pyobj is None:
            return None
        elif isinstance(pyobj, numbers.Number):
            return PythonAtomSheet(*names, source=pyobj)
        elif isinstance(pyobj, (list, tuple)):
            if getattr(pyobj, '_fields', None):  # list of namedtuple
                return SheetNamedTuple(*names, **kwargs)
            else:
                return SheetList(*names, **kwargs)
        elif isinstance(pyobj, set):
            return ListOfPyobjSheet(*names, source=list(pyobj))
        elif isinstance(pyobj, Mapping):
            return SheetDict(*names, **kwargs)
        elif isinstance(pyobj, str):
            return TextSheet(*names, source=pyobj.splitlines())
        elif isinstance(pyobj, bytes):
            return TextSheet(*names, source=pyobj.decode(cls.options.encoding).splitlines())
        elif isinstance(pyobj, object):
            obj = super().__new__(cls)  #, *names, **kwargs)
            return obj
        else:
            vd.error("cannot load '%s' as pyobj" % type(pyobj).__name__)

    def reload(self):
        self.rows = []
        vislevel = self.options.visibility
        for r in dir(self.source):
            # reading these attributes can cause distracting fail() messages
            if r in ('onlySelectedRows', 'someSelectedRows'):
                vd.warning(f'skipping attribute: {r}')
                continue
            try:
                if vislevel <= 2 and r.startswith('__'): continue
                if vislevel <= 1 and r.startswith('_'): continue
                if vislevel <= 0 and callable(getattr(self.source, r)): continue
            except Exception:
                pass

            self.addRow(r)

    def openRow(self, row):
        'dive further into Python object'
        v = getattr(self.source, row)
        return PyobjSheet(self.name + "." + str(row), source=v() if callable(v) else v)


@TableSheet.api
def openRow(sheet, row, rowidx=None):
    'Return Sheet diving into *row*.'
    if row is None or sheet.nRows == 0: vd.fail('no row to dive into')
    if rowidx is None:
        k = sheet.rowname(row) or str(sheet.cursorRowIndex)
    else:
        k = rowidx

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
def openCell(sheet, col, row, rowidx=None):
    'Return Sheet diving into cell at *row* in *col*.'
    if col is None or row is None or sheet.nRows == 0: vd.fail('no cell to dive into')
    if rowidx is None:
        k = sheet.rowname(row) or str(sheet.cursorRowIndex)
    else:
        k = rowidx
    name = f'{sheet.name}[{k}].{col.name}'
    return PyobjSheet(name, source=col.getTypedValue(row))

@Sheet.api
@asyncthread
def openRows(sheet, rows):
    for r in Progress(rows):
        vd.push(sheet.openRow(r))

    vd.sync()

@Sheet.api
@asyncthread
def openCells(sheet, col, rows):
    for r in Progress(rows):
        vd.push(openCell(col, r))

    vd.sync()

@TableSheet.api
def openRowPyobj(sheet, rowidx):
    'Return Sheet of raw Python object of row.'
    if sheet.nRows == 0: vd.fail('no row to dive into')
    return PyobjSheet("%s[%s]" % (sheet.name, rowidx), source=sheet.rows[rowidx])

@TableSheet.api
def openCellPyobj(sheet, col, rowidx):
    'Return Sheet of raw Python object of cell.'
    if col is None or sheet.nRows == 0: vd.fail('no cell to dive into')
    name = f'{sheet.name}[{rowidx}].{col.name}'
    return PyobjSheet(name, source=col.getValue(sheet.rows[rowidx]))


@BaseSheet.api
def inputPythonExpr(sheet):
    def launch_repl(v, i):
        import code
        with SuspendCurses():
            code.InteractiveConsole(locals=locals()).interact()
        return v, i
    return vd.input("eval: ", "expr", completer=visidata.CompleteExpr(), bindings={'^X': launch_repl})

BaseSheet.addCommand('^X', 'pyobj-expr', 'expr=inputPythonExpr(); vd.push(PyobjSheet(expr, source=sheet.evalExpr(expr)))', 'evaluate Python expression and open result as Python object')
BaseSheet.addCommand('', 'exec-python', 'expr = input("exec: ", "expr", completer=CompleteExpr()); exec(expr, getGlobals(), LazyChainMap(sheet, *vd.contexts, locals=vd.getGlobals()))', 'execute Python statement with expression scope')
BaseSheet.addCommand('g^X', 'import-python', 'modname=input("import: ", type="import_python"); exec("import "+modname, getGlobals())', 'import Python module in the global scope')
BaseSheet.addCommand('z^X', 'pyobj-expr-row', 'expr = input("eval over current row: ", "expr", completer=CompleteExpr()); vd.push(PyobjSheet(expr, source=evalExpr(expr, row=cursorRow)))', 'evaluate Python expression, in context of current row, and open result as Python object')
BaseSheet.addCommand('', 'assert-expr', 'expr=inputPythonExpr(); assert sheet.evalExpr(expr), f"{expr} not true"', 'eval Python expression and assert result is truthy')
BaseSheet.addCommand('', 'assert-expr-row', 'expr=inputPythonExpr(); assert sheet.evalExpr(expr, row=cursorRow), f"{expr} not true"', 'eval Python expression in context of current row, and assert result is truthy')

Sheet.addCommand('^Y', 'pyobj-row', 'status(type(cursorRow).__name__); vd.push(openRowPyobj(cursorRowIndex))', 'open current row as Python object')
Sheet.addCommand('z^Y', 'pyobj-cell', 'status(type(cursorValue).__name__); vd.push(openCellPyobj(cursorCol, cursorRowIndex))', 'open current cell as Python object')
BaseSheet.addCommand('g^Y', 'pyobj-sheet', 'status(type(sheet).__name__); vd.push(PyobjSheet(sheet.name+"_sheet", source=sheet))', 'open current sheet as Python object')

Sheet.addCommand('', 'open-row-basic', 'vd.push(TableSheet.openRow(sheet, cursorRow))', 'dive into current row as basic table (ignoring subsheet dive)')
Sheet.addCommand(ENTER, 'open-row', 'vd.push(openRow(cursorRow)) if cursorRow else vd.fail("no row to open")', 'open current row with sheet-specific dive')
Sheet.addCommand('z'+ENTER, 'open-cell', 'vd.push(openCell(cursorCol, cursorRow))', 'open sheet with copies of rows referenced in current cell')
openRows
Sheet.addCommand('g'+ENTER, 'dive-selected', 'openRows(selectedRows)', 'open all selected rows')
Sheet.addCommand('gz'+ENTER, 'dive-selected-cells', 'openCells(cursorCol, selectedRows)', 'open all selected cells')

PyobjSheet.addCommand('v', 'visibility', 'sheet.options.visibility = 0 if sheet.options.visibility else 2; reload()', 'toggle show/hide for methods and hidden properties')
PyobjSheet.addCommand('gv', 'show-hidden', 'sheet.options.visibility = 2; reload()', 'show methods and hidden properties')
PyobjSheet.addCommand('zv', 'hide-hidden', 'sheet.options.visibility -= 1; reload()', 'hide methods and hidden properties')

vd.addGlobals({
    'PythonSheet': PythonSheet,
    'ListOfDictSheet': ListOfDictSheet,
    'SheetDict': SheetDict,
    'PyobjSheet': PyobjSheet,
    'view': view,
})

vd.addMenuItems('''
    View > Visibility > Methods and dunder attributes > show > show-hidden
    View > Visibility > Methods and dunder attributes > hide > hide-hidden
    Row > Dive into > open-row
    System > Python > import library > import-python
    System > Python > current sheet > pyobj-sheet
    System > Python > current row > pyobj-row
    System > Python > current cell > pyobj-cell
    System > Python > expression > pyobj-expr
    System > Python > exec() > exec-python
''')
