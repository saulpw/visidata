from visidata import *

command('^O', 'expr = input("eval: ", "expr"); push_pyobj(expr, eval(expr))', 'eval Python expression and open the result')
#command('^S', 'push_pyobj(sheet.name + "_pyobj", sheet)', 'push object for this sheet')

command('=', 'addColumn(ColumnExpr(sheet, input("new column expr=", "expr")), index=cursorColIndex+1)', 'add column by expr')
#command(':', 'addColumn(ColumnRegex(sheet, input("new column regex:", "regex")), index=cursorColIndex+1)', 'add column by regex')
#command(':', 'addColumn()', 'regex subst on current column')

#### generic list/dict/object browsing
def push_pyobj(name, pyobj, src=None):
    vs = open_pyobj(name, pyobj, src)
    if vs:
        return vd().push(vs)
    else:
        status('unknown type ' + type(pyobj))

def open_pyobj(name, pyobj, src=None):
    if isinstance(pyobj, list):
        return SheetList(name, pyobj)
    elif isinstance(pyobj, dict):
        return SheetDict(name, pyobj)
    elif isinstance(pyobj, object):
        return SheetObject(name, pyobj)
    else:
        status('unknown type ' + type(pyobj))

def getPublicAttrs(obj):
    return [k for k in dir(obj) if not k.startswith('_') and not callable(getattr(obj, k))]

def PyobjColumns(obj):
    'columns for each public attribute on an object'
    return [ColumnAttr(k, type(getattr(obj, k))) for k in getPublicAttrs(obj)]

def AttrColumns(attrnames):
    'attrnames is list of attribute names'
    return [ColumnAttr(name) for name in attrnames]


class SheetList(Sheet):
    def __init__(self, name, src, **kwargs):
        'columns is a list of strings naming attributes on the objects within the obj'
        super().__init__(name, src, **kwargs)
        assert isinstance(src, list), type(src)

    def reload(self):
        self.rows = self.source
        if self.columns:
            pass
        elif self.rows and isinstance(self.rows[0], dict):  # list of dict
            self.columns = DictKeyColumns(self.rows[0])
            self.nKeys = 1
        else:
            self.columns = [Column(self.name)]

        self.command('^J', 'push_pyobj("%s[%s]" % (name, cursorRowIndex), cursorRow).cursorRowIndex = cursorColIndex', 'dive into this row')

class SheetDict(Sheet):
    def reload(self):
        self.columns = [ColumnItem('key', 0)]
        self.rows = list(list(x) for x in self.source.items())
        if self.rows and isinstance(self.rows[0][1], list):
            self.columns.extend(DictKeyColumns(self.rows[0]))
            self.command('e', 'if cursorColIndex > 0: source[cursorRow[0]][cursorColIndex-1] = editCell(cursorColIndex); reload()', 'edit this value')
            self.command('^J', 'if cursorColIndex > 0: push_pyobj(join_sheetnames(name, cursorRow[0]), cursorRow[cursorColIndex-1])', 'dive into this value')
        else:
            self.columns.append(ColumnItem('value', 1))
            self.command('e', 'source[cursorRow[0]][1] = editCell(1); reload()', 'edit this value')
            self.command('^J', 'push_pyobj(join_sheetnames(name, cursorRow[0]), cursorRow[1])', 'dive into this value')



def ColumnSourceAttr(name, source):
    'For using the row as attribute name on the given source Python object'
    return Column(name, type=anytype,
        getter=lambda r,b=source: getattr(b,r),
        setter=lambda r,v,b=source: setattr(b,r,v))

class SheetObject(Sheet):
    def reload(self):
        self.rows = dir(self.source)
        self.columns = [
            Column(type(self.source).__name__ + '_attr'),
            ColumnSourceAttr('value', self.source)
        ]
        self.nKeys = 1
        self.command('^J', 'v = getattr(source, cursorRow); push_pyobj(join_sheetnames(name, cursorRow), v() if callable(v) else v)', 'dive into this value')
        self.command('e', 'setattr(source, cursorRow, editCell(1)); reload()', 'edit this value')

class LazyMapping:
    'calculates column values as needed'
    def __init__(self, sheet, row):
        self.row = row
        self.sheet = sheet

    def keys(self):
        return [c.name for c in self.sheet.columns]

    def __call__(self, col):
        return eval(col.expr, {}, self)

    def __getitem__(self, colname):
        colnames = [c.name for c in self.sheet.columns]
        if colname in colnames:
            colidx = colnames.index(colname)
            return self.sheet.columns[colidx].getValue(self.row)
        else:
            raise KeyError(colname)

    def __getattr__(self, colname):
        return self.__getitem__(colname)


def ColumnExpr(sheet, expr):
    if expr:
        vc = Column(expr)  # or default name?
        vc.expr = expr
        vc.getter = lambda r,c=vc,s=sheet: LazyMapping(s, r)(c)
        vc.setter = lambda r,c=vc,s=sheet: setattr(c, 'expr', v)
        return vc


def open_json(p):
    import json
    return load_pyobj(p.name, json.load(p.open_text()))
