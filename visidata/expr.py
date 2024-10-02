import time

from visidata import Progress, Sheet, Column, asyncthread, vd, Column


class ExprColumn(Column):
    'Column using *expr* to derive the value from each row.'
    def __init__(self, name, expr=None, **kwargs):
        super().__init__(name, **kwargs)
        self.expr = expr or name
        self.ncalcs = 0
        self.totaltime = 0
        self.maxtime = 0

    def calcValue(self, row):
        t0 = time.perf_counter()
        r = self.sheet.evalExpr(self.compiledExpr, row, col=self, curcol=self)
        t1 = time.perf_counter()
        self.ncalcs += 1
        self.maxtime = max(self.maxtime, t1-t0)
        self.totaltime += (t1-t0)
        return r

    def putValue(self, row, val):
        a = self.getDisplayValue(row)
        b = self.format(self.type(val))
        if a != b:
            vd.warning("Cannot change value of calculated column.  Use `'` to freeze column.")

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, expr):
        self.compiledExpr = compile(expr, '<expr>', 'eval') if expr else None
        self._expr = expr


class CompleteExpr:
    def __init__(self, sheet=None):
        self.varnames = []
        if sheet:
            self.varnames.extend(sorted(col.name for col in sheet.columns))
        self.varnames.extend(sorted(x for x in vd.getGlobals()))
        for c in vd.contexts:
            self.varnames.extend(sorted(x for x in dir(c)))

    def __call__(self, val, state):
        i = len(val)-1
        while val[i:].isidentifier() and i >= 0:
            i -= 1

        if i < 0:
            base = ''
            partial = val
        elif val[i] == '.':  # no completion of attributes
            return None
        else:
            base = val[:i+1]
            partial = val[i+1:]

        # Remove unmatching and duplicate completions
        varnames_dict = {x:None for x in self.varnames if x.startswith(partial)}
        varnames = list(varnames_dict.keys())

        if not varnames:
            return val

        return base + varnames[state%len(varnames)]


@Column.api
@asyncthread
def setValuesFromExpr(self, rows, expr, **kwargs):
    'Set values in this column for *rows* to the result of the Python expression *expr* applied to each row.'
    compiledExpr = compile(expr, '<expr>', 'eval')
    vd.addUndoSetValues([self], rows)
    nset = 0
    for row in Progress(rows, 'setting'):
        # Note: expressions that are only calculated once, do not need to pass column identity
        # they can reference their "previous selves" once without causing a recursive problem
        try:
            v = self.sheet.evalExpr(compiledExpr, row, **kwargs)
            self.setValue(row, v)
            nset += 1
        except Exception as e:
            vd.exceptionCaught(e)

    self.recalc()
    vd.status(f'set {nset} values = {expr}')


@Sheet.api
def inputExpr(self, prompt, *args, **kwargs):
    return vd.input(prompt, "expr", *args, completer=CompleteExpr(self), **kwargs)


Sheet.addCommand('=', 'addcol-expr', 'addColumnAtCursor(ExprColumn(inputExpr("new column expr="), col=cursorCol, curcol=cursorCol))', 'create new column from Python expression, with column names as variables')
Sheet.addCommand('g=', 'setcol-expr', 'cursorCol.setValuesFromExpr(someSelectedRows, inputExpr("set selected="), curcol=cursorCol)', 'set current column for selected rows to result of Python expression')
Sheet.addCommand('z=', 'setcell-expr', 'cursorCol.setValues([cursorRow], evalExpr(inputExpr("set expr="), row=cursorRow, curcol=cursorCol))', 'evaluate Python expression on current row and set current cell with result of Python expression')
Sheet.addCommand('gz=', 'setcol-iter', 'cursorCol.setValues(someSelectedRows, *list(itertools.islice(eval(input("set column= ", "expr", completer=CompleteExpr())), len(someSelectedRows))))', 'set current column for selected rows to the items in result of Python sequence expression')

Sheet.addCommand(None, 'show-expr', 'status(evalExpr(inputExpr("show expr="), row=cursorRow, curcol=cursorCol))', 'evaluate Python expression on current row and show result on status line')

vd.addGlobals(
    ExprColumn=ExprColumn,
    ColumnExpr=ExprColumn,
    CompleteExpr=CompleteExpr,
)

vd.addMenuItems('''
    Edit > Modify > current cell > Python expression > setcell-expr
    Edit > Modify > selected cells > Python sequence > setcol-expr
    Column > Add column > Python expr > addcol-expr
''')
