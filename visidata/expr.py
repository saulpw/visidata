from visidata import Progress, Sheet, Column, asyncthread, vd, ExprColumn


class CompleteExpr:
    def __init__(self, sheet=None):
        self.sheet = sheet

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

        varnames = []
        varnames.extend(sorted((base+col.name) for col in self.sheet.columns if col.name.startswith(partial)))
        varnames.extend(sorted((base+x) for x in globals() if x.startswith(partial)))

        # Remove duplicate tabbing suggestions
        varnames_dict = {var:None for var in varnames}
        varnames = list(varnames_dict.keys())
        return varnames[state%len(varnames)]


@Column.api
@asyncthread
def setValuesFromExpr(self, rows, expr):
    'Set values in this column for *rows* to the result of the Python expression *expr* applied to each row.'
    compiledExpr = compile(expr, '<expr>', 'eval')
    vd.addUndoSetValues([self], rows)
    for row in Progress(rows, 'setting'):
        # Note: expressions that are only calculated once, do not need to pass column identity
        # they can reference their "previous selves" once without causing a recursive problem
        try:
            self.setValueSafe(row, self.sheet.evalExpr(compiledExpr, row))
        except Exception as e:
            vd.exceptionCaught(e)
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
