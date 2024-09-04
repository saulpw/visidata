from visidata import Progress, Sheet, Column, asyncthread, vd, ExprColumn


class CompleteExpr:
    def __init__(self, sheet=None):
        self.sheet = sheet
        self.varnames = []
        self.varnames.extend(sorted(col.name for col in self.sheet.columns))
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
def setValuesFromExpr(self, rows, expr):
    'Set values in this column for *rows* to the result of the Python expression *expr* applied to each row.'
    compiledExpr = compile(expr, '<expr>', 'eval')
    vd.addUndoSetValues([self], rows)
    for row in Progress(rows, 'setting'):
        # Note: expressions that are only calculated once, do not need to pass column identity
        # they can reference their "previous selves" once without causing a recursive problem
        v = vd.callNoExceptions(self.sheet.evalExpr, compiledExpr, row)
        vd.callNoExceptions(self.setValue, row, v)
    self.recalc()
    vd.status('set %d values = %s' % (len(rows), expr))


@Sheet.api
def inputExpr(self, prompt, *args, **kwargs):
    return vd.input(prompt, "expr", *args, completer=CompleteExpr(self), **kwargs)


Sheet.addCommand('=', 'addcol-expr', 'addColumnAtCursor(ExprColumn(inputExpr("new column expr="), curcol=cursorCol))', 'create new column from Python expression, with column names as variables')
Sheet.addCommand('g=', 'setcol-expr', 'cursorCol.setValuesFromExpr(someSelectedRows, inputExpr("set selected="))', 'set current column for selected rows to result of Python expression')
Sheet.addCommand('z=', 'setcell-expr', 'cursorCol.setValues([cursorRow], evalExpr(inputExpr("set expr="), cursorRow,))', 'evaluate Python expression on current row and set current cell with result of Python expression')
Sheet.addCommand('gz=', 'setcol-iter', 'cursorCol.setValues(someSelectedRows, *list(itertools.islice(eval(input("set column= ", "expr", completer=CompleteExpr())), len(someSelectedRows))))', 'set current column for selected rows to the items in result of Python sequence expression')

Sheet.addCommand(None, 'show-expr', 'status(evalExpr(inputExpr("show expr="), cursorRow))', 'evaluate Python expression on current row and show result on status line')

vd.addGlobals({'CompleteExpr': CompleteExpr})

vd.addMenuItems('''
    Edit > Modify > current cell > Python expression > setcell-expr
    Edit > Modify > selected cells > Python sequence > setcol-expr
    Column > Add column > Python expr > addcol-expr
''')
