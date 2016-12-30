import re
from . import exceptionCaught, options, error, theme, option
from .types import anytype

theme('ch_FunctionError', '¿', 'when computation fails due to exception')
theme('ch_VisibleNone', '',  'visible contents of a cell whose value was None')


class WrongTypeStr(str):
    'str wrapper with original str-ified contents to indicate that the type conversion failed'
    pass

class CalcErrorStr(str):
    'str wrapper (possibly with error message) to indicate that getValue failed'
    pass

class Column:
    def __init__(self, name, type=anytype, getter=lambda r: r, setter=None, width=None):
        self.name = name    # use property setter from the get-go to strip spaces
        self.type = type
        self.getter = getter
        self.setter = setter
        self.width = width  # <= 0 if hidden, None if auto-compute next time
        self.expr = None    # Python string expression if computed column
        self.fmtstr = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name.replace(' ', '_')

    def deduceFmtstr(self):
        if self.fmtstr is not None: return self.fmtstr
        elif self.type is int: return '%d'
        elif self.type is float: return '%.02f'
        else: return '%s'

    @property
    def hidden(self):
        return self.width == 0

    def nEmpty(self, rows):
        vals = self.values(rows)
        return sum(1 for v in vals if v == '' or v == None)

    def values(self, rows):
        return [self.getValue(r) for r in rows]

    def getValue(self, row):
        'returns a properly-typed value, or a default value if the conversion fails, or reraises the exception if the getter fails'
        try:
            v = self.getter(row)
        except Exception:
            exceptionCaught(status=False)
            raise

        try:
            return self.type(v)  # convert type on-the-fly
        except Exception:
            exceptionCaught(status=False)
            return self.type()  # return a suitable value for this type

    def getDisplayValue(self, row, width=None):
        try:
            cellval = self.getter(row)
        except Exception as e:
            exceptionCaught(status=False)
            return CalcErrorStr(options.ch_FunctionError)

        if cellval is None:
            return options.ch_VisibleNone

        if isinstance(cellval, bytes):
            cellval = cellval.decode(options.encoding)

        try:
            cellval = self.deduceFmtstr() % self.type(cellval)  # convert type on-the-fly
            if width and self.type in (int, float): cellval = cellval.rjust(width-1)
        except Exception as e:
            exceptionCaught(status=False)
            cellval = WrongTypeStr(str(cellval))

        return cellval

    def setValue(self, row, value):
        if self.setter:
            self.setter(row, value)
        else:
            error('column cannot be changed')

    def getMaxWidth(self, rows):
        if len(rows) == 0:
            return 0

        return max(max(len(self.getDisplayValue(r)) for r in rows), len(self.name))+2


# ---- Column makers

def ColumnAttr(attrname, type=anytype):
    'a getattr/setattr column on the row Python object'
    return Column(attrname, type=type,
            getter=lambda r,b=attrname: getattr(r,b),
            setter=lambda r,v,b=attrname: setattr(r,b,v))

def ColumnItem(attrname, itemkey, **kwargs):
    'a getitem/setitem column on the row Python object'
    def setitem(r, i, v):  # function needed for use in lambda
        r[i] = v

    return Column(attrname,
            getter=lambda r,i=itemkey: r[i],
            setter=lambda r,i=itemkey,f=setitem: f(r,i,v),
            **kwargs)

def ArrayNamedColumns(columns):
    'columns is a list of column names, mapping to r[0]..r[n]'
    return [ColumnItem(colname, i) for i, colname in enumerate(columns)]

def ArrayColumns(ncols):
    'columns is a list of column names, mapping to r[0]..r[n]'
    return [ColumnItem('', i) for i in range(ncols)]


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
        colidx = self.sheet.findColIdx(colname, self.sheet.columns)
        return self.sheet.columns[colidx].getValue(self.row)

    def __getattr__(self, colname):
        return self.__getitem__(colname)

def ColumnExpr(sheet, expr):
    if expr:
        vc = Column(expr)  # or default name?
        vc.expr = expr
        vc.getter = lambda r,c=vc,s=sheet: LazyMapping(s, r)(c)
        vc.setter = lambda r,c=vc,s=sheet: setattr(c, 'expr', v)
        return vc

def getTransformedValue(oldval, searchregex, replregex):
    m = re.search(searchregex, oldval)
    if not m:
        return None
    return m.expand(replregex)

def ColumnRegex(sheet, regex):
    if regex:
        vc = Column(regex)
        vc.expr, vc.searchregex, vc.replregex = regex.split('/')   # TODO: better syntax
        vc.getter = lambda r,c=vc,s=sheet: getTransformedValue(str(LazyMapping(s, r)(c)), newcol.searchregex, newcol.replregex)
        return vc
