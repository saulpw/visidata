from . import anytype, vd, options, WrongTypeStr, CalcErrorStr

class Column:
    def __init__(self, name, type=anytype, func=lambda r: r, width=None):
        self.name = name
        self.func = func
        self.width = width
        self.type = type
        self.expr = None  # Python string expression if computed column
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
        try:
            v = self.func(row)
        except Exception as e:
            vd().exceptionCaught(status=False)
            raise

        try:
            return self.type(v)  # convert type on-the-fly
        except Exception as e:
            vd().exceptionCaught(status=False)
            return self.type()  # return a suitable value for this type

    def getDisplayValue(self, row, width=None):
        try:
            cellval = self.func(row)
        except Exception as e:
            vd().exceptionCaught(status=False)
            return CalcErrorStr(options.ch_FunctionError)

        if cellval is None:
            return options.ch_VisibleNone

        if isinstance(cellval, bytes):
            cellval = cellval.decode(options.encoding)

        try:
            cellval = self.deduceFmtstr() % self.type(cellval)  # convert type on-the-fly
            if width and self.type in (int, float): cellval = cellval.rjust(width-1)
        except Exception as e:
            vd().exceptionCaught(status=False)
            cellval = WrongTypeStr(str(cellval))

        return cellval

    def setValue(self, row, value):
        if hasattr(self.func, 'setter'):
            self.func.setter(row, value)
        else:
            error('column cannot be changed')

    def getMaxWidth(self, rows):
        if len(rows) == 0:
            return 0

        return max(max(len(self.getDisplayValue(r)) for r in rows), len(self.name))+2



class ColumnAttr(Column):
    def __init__(self, attrname, valtype):
        super().__init__(attrname, type=valtype, func=lambda_getattr(attrname))


### common column setups and helpers
def setter(r, k, v):  # needed for use in lambda
    r[k] = v

def lambda_colname(colname):
    func = lambda r: r[colname]
    func.setter = lambda r,v,b=colname: setter(r,b,v)
    return func

def lambda_col(b):
    func = lambda r,b=b: r[b]
    func.setter = lambda r,v,b=b: setter(r,b,v)
    return func

def lambda_getattr(b):
    func = lambda r: getattr(r,b)
    func.setter = lambda r,v,b=b: setattr(r,b,v)
    return func

def lambda_subrow_wrap(func, subrowidx):
    'wraps original func to be func(r[subrowidx])'
    subrow_func = lambda r,i=subrowidx,f=func: r[i] and f(r[i]) or None
    subrow_func.setter = lambda r,v,i=subrowidx,f=func: r[i] and f.setter(r[i], v) or None
    return subrow_func

class OnDemandDict:
    def __init__(self, sheet, row):
        self.row = row
        self.sheet = sheet
    def keys(self):
        return [c.name for c in self.sheet.columns]
    def __getitem__(self, colname):
        colidx = self.sheet.findColIdx(colname, self.sheet.columns)
        return self.sheet.columns[colidx].getValue(self.row)


def evalCol(sheet, col, row):
    return eval(col.expr, {}, OnDemandDict(sheet, row))

def ColumnExpr(sheet, expr):
    if expr:
        vc = Column(expr)
        vc.expr = expr
        vc.func = lambda r,newcol=vc,sheet=sheet: evalCol(sheet, newcol, r)
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
        vc.func = lambda r,newcol=vc,sheet=sheet: getTransformedValue(str(evalCol(sheet, newcol, r)), newcol.searchregex, newcol.replregex)
        return vc

def getPublicAttrs(obj):
    return [k for k in dir(obj) if not k.startswith('_') and not callable(getattr(obj, k))]

def PyobjColumns(exampleRow):
    'columns for each public attribute on an object'
    return [Column(k, type(getattr(exampleRow, k)), lambda_getattr(k)) for k in getPublicAttrs(exampleRow)]

def ArrayColumns(n):
    'columns that display r[0]..r[n]'
    return [Column('', anytype, lambda_col(colnum)) for colnum in range(n)]

def ArrayNamedColumns(columns):
    'columns is a list of column names, mapping to r[0]..r[n]'
    return [Column(colname, anytype, lambda_col(i)) for i, colname in enumerate(columns)]

def AttrColumns(colnames):
    'colnames is list of attribute names'
    return [Column(name, anytype, lambda_getattr(name)) for name in colnames]

