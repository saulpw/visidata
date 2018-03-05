from visidata import *

option('pyobj_show_hidden', False, 'show _private properties on pyobjs')
option('pyobj_show_methods', False, 'show methods on pyobjs')

globalCommand('^X', 'expr = input("eval: ", "expr", completer=CompleteExpr()); push_pyobj(expr, eval(expr))', 'evaluate Python expression and open result as Python object', 'python-eval-push')
globalCommand('g^X', 'expr = input("exec: ", "expr", completer=CompleteExpr()); exec(expr, getGlobals())', 'execute Python statement in the global scope', 'python-exec')
globalCommand('z^X', 'status(evalexpr(inputExpr("status="), cursorRow))', 'evaluate Python expression on current row and show result on status line', 'python-eval-status')

globalCommand('^Y', 'status(type(cursorRow)); push_pyobj("%s[%s]" % (sheet.name, cursorRowIndex), cursorRow)', 'open current row as Python object', 'python-push-row-object')
globalCommand('z^Y', 'status(type(cursorValue)); push_pyobj("%s[%s].%s" % (sheet.name, cursorRowIndex, cursorCol.name), cursorValue)', 'open current cell as Python object', 'python-push-cell-object')
globalCommand('g^Y', 'status(type(sheet)); push_pyobj(sheet.name+"_sheet", sheet)', 'open current sheet as Python object', 'python-push-sheet-object')

globalCommand('(', 'openColumn(cursorCol, cursorValue)', 'expand current column of lists or dict into multiple columns and hide the original column')
globalCommand(')', 'closeColumn(sheet, cursorCol)', 'unexpand current column; restore original column and remove other columns at this level')

# used as ENTER in several pyobj sheets
globalCommand('python-dive-row', 'push_pyobj("%s[%s]" % (name, cursorRowIndex), cursorRow).cursorRowIndex = cursorColIndex', 'dive further into Python object')


def deduceType(v):
    if isinstance(v, (float,int,str)):
        return type(v)
    else:
        return anytype


class ExpandedColumn(Column):
    def calcValue(self, row):
        return self.origCol.getValue(row)[self.key]

    def setValue(self, row, value):
        self.origCol.getValue(row)[self.key] = value

def openColumn(col, val):
    if isinstance(val, dict):
        for k in val:
            c = ExpandedColumn(col.name+'.'+k, type=deduceType(val[k]), origCol=col, key=k)
            col.sheet.addColumn(c, col.sheet.cursorColIndex+1)
            col.width = 0
    elif isinstance(val, (list, tuple)):
        for k in range(len(val)):
            c = ExpandedColumn('%s[%s]' % (col.name, k), type=deduceType(val[k]), origCol=col, key=k)
            col.sheet.addColumn(c, col.sheet.cursorColIndex+1)
            col.width = 0

def closeColumn(sheet, col):
    col.origCol.width = options.default_width
    cols = [c for c in sheet.columns if getattr(c, "origCol", None) is not getattr(col, "origCol", col)]
    sheet.columns = cols


#### generic list/dict/object browsing
def push_pyobj(name, pyobj):
    vs = load_pyobj(name, pyobj)
    if vs:
        return vd().push(vs)
    else:
        status('unknown type ' + type(pyobj))

def load_pyobj(name, pyobj):
    'Return Sheet object of appropriate type for given sources in `args`.'
    if isinstance(pyobj, list) or isinstance(pyobj, tuple):
        if getattr(pyobj, '_fields', None):  # list of namedtuple
            return SheetNamedTuple(name, pyobj)
        else:
            return SheetList(name, pyobj)
    elif isinstance(pyobj, dict):
        return SheetDict(name, pyobj)
    elif isinstance(pyobj, object):
        return SheetObject(name, pyobj)
    else:
        status('unknown type ' + type(pyobj))

def open_pyobj(path):
    'Provide wrapper for `load_pyobj`.'
    return load_pyobj(path.name, eval(path.read_text()))

def getPublicAttrs(obj):
    'Return all public attributes (not methods or `_`-prefixed) on object.'
    return [k for k in dir(obj) if not k.startswith('_') and not callable(getattr(obj, k))]

def PyobjColumns(obj):
    'Return columns for each public attribute on an object.'
    return [ColumnAttr(k, type(getattr(obj, k))) for k in getPublicAttrs(obj)]

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

class ListOfPyobjSheet(Sheet):
    rowtype = 'python objects'
    commands = [Command(ENTER, 'python-dive-row')]
    def reload(self):
        self.rows = self.source
        self.columns = [Column(self.name,
                               getter=lambda col,row: row,
                               setter=lambda col,row,val: setitem(col.sheet.source, col.sheet.source.index(row), val))]

# rowdef: dict
class ListOfDictSheet(Sheet):
    rowtype = 'dicts'
    commands = [Command(ENTER, 'python-dive-row')]
    def reload(self):
        self.columns = DictKeyColumns(self.source[0])
        self.rows = self.source

# rowdef: namedtuple
class ListOfNamedTupleSheet(Sheet):
    rowtype = 'namedtuples'
    commands = [Command(ENTER, 'python-dive-row')]
    def reload(self):
        self.columns = [ColumnItem(k, i) for i, k in enumerate(self.source[0]._fields)]
        self.rows = self.source


# rowdef: PyObj
class SheetNamedTuple(Sheet):
    rowtype = 'values'
    'a single namedtuple, with key and value columns'
    commands = [Command(ENTER, 'dive()', 'dive further into Python object', 'python-dive-row')]
    columns = [ColumnItem('name', 0), ColumnItem('value', 1)]

    def __init__(self, name, src, **kwargs):
        super().__init__(name, source=src, **kwargs)

    def reload(self):
        self.rows = list(zip(self.source._fields, self.source))

    def dive(self):
        push_pyobj(joinSheetnames(self.name, self.cursorRow[0]), self.cursorRow[1])


class SheetDict(Sheet):
    rowtype = 'items'
    commands = [
        Command('e', 'edit()', 'edit contents of current cell', 'modify-edit-cell'),
        Command(ENTER, 'dive()', 'dive further into Python object', 'python-dive-row')
    ]
    def __init__(self, name, src, **kwargs):
        super().__init__(name, source=src, **kwargs)

    def reload(self):
        self.columns = [ColumnItem('key', 0)]
        self.rows = list(list(x) for x in self.source.items())
        self.columns.append(ColumnItem('value', 1))

    def edit(self):
        self.source[self.cursorRow[0]][1] = self.editCell(1)
        self.cursorRowIndex += 1
        self.reload()

    def dive(self):
        push_pyobj(joinSheetnames(self.name, self.cursorRow[0]), self.cursorRow[1])

class ColumnSourceAttr(Column):
    'Use row as attribute name on sheet source'
    def calcValue(self, attrname):
        return getattr(self.sheet.source, attrname)
    def setValue(self, attrname, value):
        return setattr(self.sheet.source, attrname, value)

# rowdef: attrname
class SheetObject(Sheet):
    rowtype = 'attributes'
    commands = [
        Command(ENTER, 'v = getattr(source, cursorRow); push_pyobj(joinSheetnames(name, cursorRow), v() if callable(v) else v)', 'dive further into Python object'),
        Command('e', 'setattr(source, cursorRow, type(getattr(source, cursorRow))(editCell(1))); sheet.cursorRowIndex += 1; reload()', 'edit contents of current cell', 'modify-edit-cell'),
        Command('v', 'options.pyobj_show_hidden = not options.pyobj_show_hidden; reload()', 'toggle whether hidden properties are shown'),
        Command('gv', 'options.pyobj_show_hidden = options.pyobj_show_methods = True; reload()', 'show methods and hidden properties'),
        Command('zv', 'options.pyobj_show_hidden = options.pyobj_show_methods = False; reload()', 'hide methods and hidden properties'),
    ]
    def __init__(self, name, obj, **kwargs):
        super().__init__(name, source=obj, **kwargs)

    def reload(self):
        self.rows = []
        for r in dir(self.source):
            try:
                if options.pyobj_show_hidden or not r.startswith('_'):
                    self.addRow(r)
                elif options.pyobj_show_methods or not callable(getattr(self.source, r)):
                    self.addRow(r)
            except Exception:
                pass

        self.columns = [
            Column(type(self.source).__name__ + '_attr'),
            ColumnSourceAttr('value'),
            ColumnExpr('docstring', 'value.__doc__')
        ]
        self.recalc()

        self.keyCols = self.columns[0:1]
